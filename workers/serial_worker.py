"""
SerialWorker: roda inteiro numa QThread dedicada.

Máquina de estados do lado desktop:
    ABRINDO -> HANDSHAKE (sempre a 9600) -> SINCRONIZANDO (nova velocidade)
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
TENTATIVAS_HS = 3
TENTATIVAS_SYNC = 2
ESPERA_VOLTA_9600_S = 3.3    # placa volta a 9600 após 3 s sem SYNC
INTERVALO_PING_S = 1.0
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
    disjuntor_confirmado = Signal(bool)      # ACK,DJ,x
    estatisticas = Signal(int, int, int)     # recebidos, inválidos, perdidos
    falha_comunicacao = Signal(str)
    finalizado = Signal()

    def __init__(self, porta: str, baud_alvo: int, periodo_ms: int,
                 fator_potencia: float = 1.0, reconexao_automatica: bool = True):
        super().__init__()
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
        self._ultimo_seq: int | None = None

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
        """Handshake sempre a 9600; tenta a velocidade alvo e cai para as menores."""
        for baud in protocolo.sequencia_negociacao(self.baud_alvo):
            if self._parar.is_set():
                raise Cancelado()

            self._estado("HANDSHAKE", f"9600 bps -> pedindo {baud} bps")
            ok = self._enviar_hs(baud)
            if self._parar.is_set():
                raise Cancelado()
            if not ok:
                raise FalhaHandshake("placa não respondeu ao HS a 9600 bps")

            if baud != protocolo.BAUD_INICIAL:
                self._ser.flush()
                time.sleep(0.05)
                self._ser.baudrate = baud           # troca sem fechar a porta (não reseta o Arduino)
                self._ser.reset_input_buffer()
                self._buffer = b""

            self._estado("SINCRONIZANDO", f"confirmando link a {baud} bps")
            ok = self._enviar_sync()
            if self._parar.is_set():
                raise Cancelado()
            if ok:
                self._estado("TELEMETRIA", f"link estabelecido a {baud} bps")
                return baud

            self._log(f"SYNC sem resposta a {baud} bps; voltando para 9600 e tentando velocidade menor")
            self._ser.baudrate = protocolo.BAUD_INICIAL
            if self._esperar(ESPERA_VOLTA_9600_S):
                raise Cancelado()
            self._ser.reset_input_buffer()
            self._buffer = b""
        raise FalhaHandshake("nenhuma velocidade foi confirmada")

    def _enviar_hs(self, baud: int) -> bool:
        cmd = protocolo.cmd_handshake(baud, self.periodo_ms)
        for tentativa in range(1, TENTATIVAS_HS + 1):
            self._escrever(cmd)
            msg = self._aguardar(lambda m: (m.tipo == "ACK" and m.campos[:1] == ("HS",))
                                 or (m.tipo == "NAK" and bool(m.campos) and m.campos[0].startswith("HS")))
            if msg and msg.tipo == "ACK" and len(msg.campos) >= 2 and msg.campos[1] == str(baud):
                return True
            if msg and msg.tipo == "NAK":
                raise FalhaHandshake(f"placa recusou o handshake: {','.join(msg.campos)}")
            self._log(f"sem ACK do HS (tentativa {tentativa}/{TENTATIVAS_HS})")
        return False

    def _enviar_sync(self) -> bool:
        for _ in range(TENTATIVAS_SYNC):
            self._escrever(protocolo.cmd_sync())
            msg = self._aguardar(lambda m: m.tipo == "ACK" and m.campos[:1] == ("SYNC",))
            if msg:
                return True
        return False

    def _laco_telemetria(self, baud: int):
        while not self._comandos.empty():      # descarta comandos antigos
            self._comandos.get_nowait()
        self._recebidos = self._invalidos = self._perdidos = 0
        self._ultimo_seq = None

        watchdog = max(3 * self.periodo_ms / 1000.0, 3.0)
        agora = time.monotonic()
        ultimo_dado = ultimo_ping = ultima_estat = agora

        while not self._parar.is_set():
            self._despachar_comandos()

            agora = time.monotonic()
            if agora - ultimo_ping >= INTERVALO_PING_S:
                self._escrever(protocolo.cmd_ping(), registrar=False)
                ultimo_ping = agora

            for linha in self._ler_linhas():
                if self._tratar_linha(linha):
                    ultimo_dado = time.monotonic()

            agora = time.monotonic()
            if agora - ultima_estat >= 1.0:
                self.estatisticas.emit(self._recebidos, self._invalidos, self._perdidos)
                ultima_estat = agora
            if agora - ultimo_dado > watchdog:
                raise LinkPerdido(f"nenhuma telemetria válida há {watchdog:.0f} s")

        # encerramento cooperativo: avisa a placa para voltar ao estado de espera
        self._estado("ENCERRANDO", "enviando STOP para a placa")
        try:
            self._escrever(protocolo.cmd_stop())
            self._aguardar(lambda m: m.tipo == "ACK" and m.campos[:1] == ("STOP",), timeout=0.5,
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
            if self._ultimo_seq is not None and d.seq > self._ultimo_seq + 1:
                self._perdidos += d.seq - self._ultimo_seq - 1
            self._ultimo_seq = d.seq
            self._recebidos += 1
            self.leitura_recebida.emit(LeituraTelemetria.criar(
                d.tensao, d.corrente, self.fator_potencia, d.seq, d.disjuntor_fechado))
            return True

        self._log(f"<- {linha}")
        if msg.tipo == "ACK" and msg.campos[:1] == ("DJ",) and len(msg.campos) >= 2:
            self.disjuntor_confirmado.emit(msg.campos[1] == "1")
        return False

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

    def _aguardar(self, predicado, timeout: float = TIMEOUT_RESPOSTA_S, respeitar_parada=True):
        limite = time.monotonic() + timeout
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
