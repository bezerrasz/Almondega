"""
SerialWorker: roda inteiro numa QThread dedicada.

Protocolo do firmware do professor (ver models/protocolo.py):
    a placa liga em espera a 9600 bps; "!S<baud>" -> ACK em texto -> a placa troca de velocidade
    e passa a mandar "$DAT,<A0>,<A1>,<rele>,<botao>*<CK>"; "!1"/"!0" comandam o relé (disjuntor);
    "!P" pausa a conversão e a placa volta a 9600.

Máquina de estados do lado desktop:
    ABRINDO -> HANDSHAKE (sempre a 9600) -> SINCRONIZANDO (nova velocidade, espera a 1ª telemetria)
            -> TELEMETRIA -> (falha) -> RECONECTANDO -> ABRINDO ...
    Qualquer estado + parar() -> ENCERRANDO -> DESCONECTADO

Toda leitura/escrita na porta acontece AQUI. A GUI só:
  - chama enviar_comando() e parar(), que são thread-safe (fila + Event);
  - recebe sinais, que o Qt entrega na thread principal (conexão enfileirada).
"""
from __future__ import annotations

import logging
import queue
import threading
import time

import serial
from PySide6.QtCore import QObject, Signal, Slot

from models import protocolo
from models.entidades import LeituraTelemetria

log = logging.getLogger(__name__)

AGUARDAR_RESET_S = 2.0       # Arduino reinicia ao abrir a porta (DTR)
TIMEOUT_RESPOSTA_S = 1.2     # espera por um ACK
TENTATIVAS_INICIO = 3
ESPERA_TELEMETRIA_S = 2.0    # após trocar de velocidade, tempo para chegar o 1º pacote válido
INTERVALO_RECONEXAO_S = 2.0


class FalhaHandshake(Exception):
    pass


class LinkPerdido(Exception):
    pass


class Cancelado(Exception):
    """parar() foi chamado no meio de uma etapa."""


class SerialWorker(QObject):
    estado_mudou = Signal(str, str)          # estado, detalhe
    log_protocolo = Signal(str)              # linha para o console da interface
    velocidade_negociada = Signal(int)
    leitura_recebida = Signal(object)        # LeituraTelemetria
    disjuntor_confirmado = Signal(bool)      # ACK do relé: ligado (True) / desligado (False)
    botao_emergencia = Signal()              # botão físico (pino 11) foi apertado (borda de subida)
    estatisticas = Signal(int, int, int)     # recebidos, inválidos, perdidos
    falha_comunicacao = Signal(str)
    finalizado = Signal()

    def __init__(self, porta: str, baud_alvo: int, periodo_ms: int,
                 fator_potencia: float = 1.0, reconexao_automatica: bool = True,
                 timeout_resposta_s: float = TIMEOUT_RESPOSTA_S):
        super().__init__()
        self.timeout_resposta = timeout_resposta_s     # "Timeout (s)" da tela serial
        self.porta = porta
        self.baud_alvo = baud_alvo
        self.periodo_ms = periodo_ms
        self.fator_potencia = fator_potencia
        self.reconexao_automatica = reconexao_automatica

        self._parar = threading.Event()
        self._comandos: queue.Queue[str] = queue.Queue()
        self._ser: serial.Serial | None = None
        self._buffer = b""
        self._recebidos = self._invalidos = self._perdidos = 0
        self._seq = 0                              # contador de leituras emitidas (o firmware não numera)
        self._ultima_emissao = 0.0
        self._ultimo_rele: bool | None = None
        self._ultimo_botao: bool | None = None   # None = ainda não viu nenhum pacote
        self._botao_consecutivos = 0

    # ---------------- API thread-safe (chamada pela GUI) ----------------
    def parar(self):
        self._parar.set()

    def enviar_comando(self, comando: str):
        self._comandos.put(comando)

    # ---------------- laço principal (thread serial) ----------------
    @Slot()
    def executar(self):
        try:
            while not self._parar.is_set():
                try:
                    self._abrir_porta()
                    baud = self._negociar()
                    self.velocidade_negociada.emit(baud)
                    self._laco_telemetria(baud)
                except serial.SerialException as e:
                    self._falha(f"Porta serial indisponível ou desconectada: {e}")
                except OSError as e:
                    self._falha(f"Erro de E/S na porta: {e}")
                except FalhaHandshake as e:
                    self._falha(f"Handshake falhou: {e}")
                except LinkPerdido as e:
                    self._falha(f"Link perdido: {e}")
                except Cancelado:
                    pass
                except Exception as e:
                    # qualquer erro imprevisto vira queda de link: registra e reconecta,
                    # em vez de matar a thread e deixar o operador sem comunicação
                    log.exception("erro inesperado na comunicação serial")
                    self._falha(f"Erro inesperado: {e}")
                finally:
                    self._fechar_porta()

                if self._parar.is_set() or not self.reconexao_automatica:
                    break
                self._estado("RECONECTANDO", f"nova tentativa em {INTERVALO_RECONEXAO_S:.0f} s")
                self._esperar(INTERVALO_RECONEXAO_S)
        except Exception as e:   # nunca deixa a thread morrer sem avisar
            log.exception("erro inesperado no SerialWorker")
            self.falha_comunicacao.emit(f"Erro inesperado: {e}")
        finally:
            self._fechar_porta()
            self._estado("DESCONECTADO", "comunicação encerrada")
            self.finalizado.emit()

    # ---------------- etapas ----------------
    def _abrir_porta(self):
        self._estado("ABRINDO", f"{self.porta} a {protocolo.BAUD_INICIAL} bps")
        self._ser = serial.Serial(self.porta, protocolo.BAUD_INICIAL,
                                  timeout=0.1, write_timeout=1.0)
        self._buffer = b""
        self._log(f"porta {self.porta} aberta a 9600 bps; aguardando reset da placa")
        if self._esperar(AGUARDAR_RESET_S):
            raise Cancelado()
        self._ser.reset_input_buffer()

    def _negociar(self) -> int:
        """Handshake sempre a 9600 ("!S<baud>"); tenta a velocidade alvo e cai para as menores."""
        for baud in protocolo.sequencia_negociacao(self.baud_alvo):
            if self._parar.is_set():
                raise Cancelado()

            self._estado("HANDSHAKE", f"9600 bps -> pedindo {baud} bps")
            ok = self._enviar_inicio(baud)
            if self._parar.is_set():
                raise Cancelado()
            if not ok:
                raise FalhaHandshake("placa não respondeu ao !S a 9600 bps")

            if baud != protocolo.BAUD_INICIAL:
                # a placa responde o ACK a 9600 e só depois troca; nada é transmitido no intervalo
                self._ser.baudrate = baud           # troca sem fechar a porta (não reseta o Arduino)
                self._ser.reset_input_buffer()
                self._buffer = b""

            self._estado("SINCRONIZANDO", f"aguardando telemetria a {baud} bps")
            if self._aguardar(lambda m: m.tipo == "DATA", timeout=max(self.timeout_resposta, ESPERA_TELEMETRIA_S)):
                self._estado("TELEMETRIA", f"link estabelecido a {baud} bps")
                return baud
            if self._parar.is_set():
                raise Cancelado()

            self._log(f"sem telemetria a {baud} bps; pausando a placa e tentando velocidade menor")
            self._voltar_para_9600()
        raise FalhaHandshake("nenhuma velocidade foi confirmada")

    def _enviar_inicio(self, baud: int) -> bool:
        cmd = protocolo.cmd_iniciar(baud)
        for tentativa in range(1, TENTATIVAS_INICIO + 1):
            self._escrever(cmd)
            msg = self._aguardar(lambda m: (m.tipo == "ACK" and m.campos[:1] == ("INICIO",)) or m.tipo == "NAK")
            if msg and msg.tipo == "ACK" and msg.campos[1] == str(baud):
                return True
            if msg and msg.tipo == "NAK":
                raise FalhaHandshake(f"placa recusou o início: {msg.campos[0]}")
            self._log(f"sem ACK do início (tentativa {tentativa}/{TENTATIVAS_INICIO})")
        return False

    def _voltar_para_9600(self):
        """!P na velocidade atual: a placa responde o ACK e volta a 9600, em espera."""
        self._escrever(protocolo.cmd_pausar())
        self._aguardar(lambda m: m.tipo == "ACK" and m.campos[:1] == ("PAUSA",), timeout=0.8)
        self._ser.baudrate = protocolo.BAUD_INICIAL
        self._ser.reset_input_buffer()
        self._buffer = b""

    def _laco_telemetria(self, baud: int):
        while not self._comandos.empty():      # descarta comandos antigos
            self._comandos.get_nowait()
        self._recebidos = self._invalidos = self._perdidos = 0
        self._seq = 0
        self._ultima_emissao = 0.0
        self._ultimo_rele = None
        self._ultimo_botao = None
        self._botao_consecutivos = 0

        watchdog = max(3 * self.periodo_ms / 1000.0, 3.0)
        agora = time.monotonic()
        ultimo_dado = ultima_estat = agora

        while not self._parar.is_set():
            self._despachar_comandos()

            for linha in self._ler_linhas():
                if self._tratar_linha(linha):
                    ultimo_dado = time.monotonic()

            agora = time.monotonic()
            if agora - ultima_estat >= 1.0:
                self.estatisticas.emit(self._recebidos, self._invalidos, self._perdidos)
                ultima_estat = agora
            if agora - ultimo_dado > watchdog:
                raise LinkPerdido(f"nenhuma telemetria válida há {watchdog:.0f} s")

        # encerramento cooperativo: pausa a placa (ela volta a 9600 e fica em espera)
        self._estado("ENCERRANDO", "enviando !P para a placa")
        try:
            self._escrever(protocolo.cmd_pausar())
            self._aguardar(lambda m: m.tipo == "ACK" and m.campos[:1] == ("PAUSA",), timeout=0.5,
                           respeitar_parada=False)
        except (serial.SerialException, OSError):
            pass

    def _tratar_linha(self, linha: str) -> bool:
        """Devolve True se a linha era uma telemetria válida."""
        try:
            msg = protocolo.interpretar_linha(linha)
        except protocolo.PacoteInvalido as e:
            self._invalidos += 1
            self._log(f"pacote descartado: {e}")
            return False

        if msg.tipo == "DATA":
            try:
                d = protocolo.decodificar_telemetria(msg)
            except protocolo.PacoteInvalido as e:
                self._invalidos += 1
                self._log(f"pacote descartado: {e}")
                return False
            self._recebidos += 1
            self._verificar_botao(d.botao_pressionado)      # em TODO pacote (não passa pela decimação)
            self._emitir_leitura(d)
            return True

        self._log(f"<- {linha}")
        if msg.tipo == "ACK" and msg.campos[:1] == ("RELE",) and msg.campos[1] in ("0", "1"):
            self.disjuntor_confirmado.emit(msg.campos[1] == "1")
        return False

    def _verificar_botao(self, pressionado: bool):
        """Botão físico de emergência: dispara só na SUBIDA (solto -> apertado), com 2 pacotes
        seguidos em 1 como antirruído. Se já estiver apertado no 1º pacote, não dispara."""
        if self._ultimo_botao is None:
            self._ultimo_botao = pressionado
            self._botao_consecutivos = 2 if pressionado else 0
            return
        if not pressionado:
            self._ultimo_botao = False
            self._botao_consecutivos = 0
            return
        self._botao_consecutivos += 1
        if not self._ultimo_botao and self._botao_consecutivos >= 2:
            self._ultimo_botao = True
            self._log("botão físico de emergência apertado")
            self.botao_emergencia.emit()

    def _emitir_leitura(self, d: protocolo.DadosTelemetria):
        """A placa manda ~200 pacotes/s; o app emite uma leitura por período de amostragem.
        Uma mudança no relé (disjuntor) é emitida na hora, sem esperar o período."""
        agora = time.monotonic()
        mudou_rele = self._ultimo_rele is not None and d.disjuntor_fechado != self._ultimo_rele
        self._ultimo_rele = d.disjuntor_fechado
        if not mudou_rele and agora - self._ultima_emissao < self.periodo_ms / 1000.0:
            return
        self._ultima_emissao = agora
        self._seq += 1
        # disjuntor aberto = sem carga: o potenciômetro de corrente continua girando, mas a corrente é 0
        corrente = d.corrente if d.disjuntor_fechado else 0.0
        self.leitura_recebida.emit(LeituraTelemetria.criar(
            d.tensao, corrente, self.fator_potencia, self._seq, d.disjuntor_fechado))

    # ---------------- utilitários de E/S ----------------
    def _despachar_comandos(self):
        while True:
            try:
                cmd = self._comandos.get_nowait()
            except queue.Empty:
                return
            self._escrever(cmd)

    def _escrever(self, cmd: str, registrar: bool = True):
        self._ser.write((cmd + "\n").encode("ascii"))
        if registrar:
            self._log(f"-> {cmd}")

    def _ler_linhas(self) -> list[str]:
        # read() espera no máximo `timeout` (0,1 s): a thread nunca fica presa
        dados = self._ser.read(self._ser.in_waiting or 1)
        if not dados:
            return []
        self._buffer += dados
        if len(self._buffer) > 4096:            # lixo sem '\n' (ex.: baud errado)
            self._buffer = self._buffer[-256:]
        linhas = []
        while b"\n" in self._buffer:
            bruto, self._buffer = self._buffer.split(b"\n", 1)
            texto = bruto.decode("ascii", errors="replace").strip()
            if texto:
                linhas.append(texto)
        return linhas

    def _aguardar(self, predicado, timeout: float | None = None, respeitar_parada=True):
        limite = time.monotonic() + (self.timeout_resposta if timeout is None else timeout)
        while time.monotonic() < limite:
            if respeitar_parada and self._parar.is_set():
                return None
            for linha in self._ler_linhas():
                try:
                    msg = protocolo.interpretar_linha(linha)
                except protocolo.PacoteInvalido:
                    continue
                if msg.tipo != "DATA":
                    self._log(f"<- {linha}")
                if predicado(msg):
                    return msg
        return None

    def _esperar(self, segundos: float) -> bool:
        """Espera interrompível. Devolve True se parar() foi chamado."""
        return self._parar.wait(segundos)

    def _fechar_porta(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def _estado(self, estado: str, detalhe: str = ""):
        log.info("serial: %s %s", estado, detalhe)
        self.estado_mudou.emit(estado, detalhe)

    def _log(self, texto: str):
        self.log_protocolo.emit(texto)

    def _falha(self, texto: str):
        log.error(texto)
        self.falha_comunicacao.emit(texto)
