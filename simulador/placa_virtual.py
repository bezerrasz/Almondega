"""
Simulador da placa do professor em porta serial virtual (mesmo protocolo do firmware real).

A placa liga em espera a 9600 bps e imprime um banner. Todo comando começa com '!':
    !S<baud>   inicia a telemetria nessa velocidade (9600/19200/38400/115200)
    !1 / !L    liga o relé  (disjuntor FECHADO)      !0 / !D   desliga o relé
    !T         alterna o relé
    !P / !STOP pausa a conversão e volta a 9600 bps
Telemetria:  $DAT,<A0>,<A1>,<rele>,<botao>*<CK>   (A0 = tensão, A1 = corrente, valores de 0 a 1023)

Uso (Windows com com0com criando o par COM10 <-> COM11):
    python simulador/placa_virtual.py COM11
    (no app desktop, escolha a COM10)

Uso (Linux):
    python tests/par_portas_virtuais.py        # mostra dois caminhos /dev/pts/X
    python simulador/placa_virtual.py /dev/pts/Y

Falhas que podem ser induzidas durante a demonstração (digite + Enter):
    p  -> pico de corrente por 6 s (dispara a proteção de sobrecorrente)
    t  -> sobretensão por 6 s
    c  -> envia 3 pacotes com checksum errado
    m  -> placa "trava" (para de responder) por 8 s
    b  -> aperta o botão físico (pino 11) por 0,5 s
    r  -> reinicia a placa (volta a 9600 / em espera, relé desligado)
    q  -> encerra o simulador
Opção --falhar-baud 115200 faz a placa não transmitir nessa velocidade,
para demonstrar o fallback de velocidade do desktop.
"""
import argparse
import math
import random
import sys
import threading
import time
from pathlib import Path

import serial

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models import protocolo  # noqa: E402  (mesma escala A/D do app)

BAUD_INICIAL = protocolo.BAUD_INICIAL
BAUDS_SUPORTADOS = protocolo.BAUDS_SUPORTADOS
INTERVALO_AMOSTRA = 0.005          # o timer do firmware dispara a cada 5 ms (200 amostras/s)


def checksum(texto: str) -> str:
    return protocolo.checksum(texto)


class PlacaVirtual:
    def __init__(self, porta: serial.Serial, falhar_bauds=(), rele_inicial: bool = False):
        self.porta = porta
        self.falhar_bauds = set(falhar_bauds)
        self.rele_inicial = rele_inicial
        self.lock = threading.Lock()
        self.rodando = True
        self._reiniciar()

    # ---------------- estado ----------------
    def _reiniciar(self):
        self.conversao = False
        self.baud = BAUD_INICIAL
        self.porta.baudrate = BAUD_INICIAL
        self.rele = self.rele_inicial
        self.botao = False
        self.botao_ate = 0.0
        self.ultimo_envio = 0.0
        self.cmd = ""
        self.gravando = False
        self.pico_ate = 0.0
        self.sobretensao_ate = 0.0
        self.travada_ate = 0.0
        self.corromper = 0
        self._log("placa iniciada: EM ESPERA a 9600 bps")
        self._banner()

    def _banner(self):
        for linha in ("", "=" * 40, "PLACA EM ESPERA (9600 baud)",
                      "Envie !S115200 para iniciar nessa taxa",
                      "Envie !P para pausar e voltar para 9600", "=" * 40):
            self._enviar(linha)

    def _trocar_baud(self, novo):
        self.porta.flush()
        time.sleep(0.02)
        self.porta.baudrate = novo
        self.baud = novo

    # ---------------- E/S ----------------
    @staticmethod
    def _log(msg):
        print(f"[PLACA {time.strftime('%H:%M:%S')}] {msg}", flush=True)

    def _enviar(self, linha: str):
        self.porta.write((linha + "\r\n").encode("ascii"))

    def _ler(self):
        n = self.porta.in_waiting
        if not n:
            return
        for byte in self.porta.read(n):
            c = chr(byte)
            if self.estava_travada():
                continue
            if c == "!":
                self.gravando = True
                self.cmd = ""
            elif self.gravando:
                if c in "\r\n":
                    if self.cmd:
                        self._processar(self.cmd)
                    self.gravando = False
                    self.cmd = ""
                elif c != " " and len(self.cmd) < 15:
                    self.cmd += c

    def estava_travada(self) -> bool:
        return time.monotonic() < self.travada_ate

    # ---------------- medições (valores brutos do conversor A/D) ----------------
    def _adc_tensao(self):
        t = time.monotonic()
        v = 220.0 + 2.5 * math.sin(t / 7.0) + random.uniform(-0.5, 0.5)
        if t < self.sobretensao_ate:
            v = 245.0 + random.uniform(-1, 1)
        return self._para_adc(v, protocolo.TENSAO_FUNDO_ESCALA_V)

    def _adc_corrente(self):
        t = time.monotonic()
        i = 11.0 + 3.0 * math.sin(t / 10.0) + random.uniform(-0.3, 0.3)
        if t < self.pico_ate:
            i = 36.0 + random.uniform(-1, 1)
        return self._para_adc(i, protocolo.CORRENTE_FUNDO_ESCALA_A)

    @staticmethod
    def _para_adc(valor, fundo_escala):
        return max(0, min(protocolo.ADC_MAXIMO, round(valor / fundo_escala * protocolo.ADC_MAXIMO)))

    def _enviar_telemetria(self):
        self.botao = time.monotonic() < self.botao_ate
        corpo = f"DAT,{self._adc_tensao()},{self._adc_corrente()},{1 if self.rele else 0},{1 if self.botao else 0}"
        ck = checksum(corpo)
        if self.corromper > 0:
            self.corromper -= 1
            ck = "00" if ck != "00" else "FF"
        self._enviar(f"${corpo}*{ck}")

    # ---------------- protocolo ----------------
    def _processar(self, cmd: str):
        if cmd[0] in "Ss":
            try:
                baud = int(cmd[1:]) if cmd[1:] else 115200
            except ValueError:
                baud = 0
            if baud in BAUDS_SUPORTADOS:
                self._enviar(f">>> ACK: INICIANDO EM {baud} BPS <<<")
                self._log(f"início da telemetria a {baud} bps")
                if baud != BAUD_INICIAL:
                    self._trocar_baud(baud)
                self.conversao = True
                self.ultimo_envio = 0.0
            else:
                self._enviar(">>> ERR: BAUD INVALIDO. Use 9600, 19200, 38400 ou 115200 <<<")
        elif cmd.upper() in ("P", "STOP"):
            self.conversao = False
            self._enviar("")
            self._enviar(">>> ACK: CONVERSAO PAUSADA. RETORNANDO A 9600 BPS <<<")
            self._trocar_baud(BAUD_INICIAL)
            self._log("conversão pausada: volta a 9600 bps")
        elif cmd == "1" or cmd.upper() == "L":
            self.rele = True
            self._enviar(">>> ACK: RELE LIGADO <<<")
            self._log("relé LIGADO (disjuntor FECHADO)")
        elif cmd == "0" or cmd.upper() == "D":
            self.rele = False
            self._enviar(">>> ACK: RELE DESLIGADO <<<")
            self._log("relé DESLIGADO (disjuntor ABERTO)")
        elif cmd.upper() == "T":
            self.rele = not self.rele
            self._enviar(">>> ACK: RELE ALTERNADO <<<")

    # ---------------- laço principal ----------------
    def passo(self):
        with self.lock:
            self._ler()
            agora = time.monotonic()
            if self.estava_travada() or not self.conversao or self.baud in self.falhar_bauds:
                return
            # a 9600 bps um pacote de ~24 bytes leva ~25 ms: a linha serial limita a taxa
            intervalo = max(INTERVALO_AMOSTRA, 24 * 10 / self.baud)
            if agora - self.ultimo_envio >= intervalo:
                self.ultimo_envio = agora
                self._enviar_telemetria()

    def comando_operador(self, cmd: str):
        with self.lock:
            agora = time.monotonic()
            if cmd == "p":
                self.pico_ate = agora + 6
                self._log("falha induzida: pico de corrente")
            elif cmd == "t":
                self.sobretensao_ate = agora + 6
                self._log("falha induzida: sobretensão")
            elif cmd == "c":
                self.corromper = 3
                self._log("falha induzida: 3 pacotes corrompidos")
            elif cmd == "m":
                self.travada_ate = agora + 8
                self._log("falha induzida: placa travada por 8 s")
            elif cmd == "b":
                self.botao_ate = agora + 0.5
                self._log("botão físico apertado")
            elif cmd == "r":
                self._log("reinício da placa")
                self._reiniciar()
            elif cmd == "q":
                self.rodando = False


def ler_teclado(placa: PlacaVirtual):
    for linha in sys.stdin:
        placa.comando_operador(linha.strip().lower())
        if not placa.rodando:
            break


def main():
    ap = argparse.ArgumentParser(description="Simulador da placa Smart Grid (firmware do professor)")
    ap.add_argument("porta", help="porta serial do lado da placa (ex.: COM11 ou /dev/pts/5)")
    ap.add_argument("--falhar-baud", type=int, nargs="*", default=[],
                    help="velocidades em que a placa 'não transmite' (demonstra o fallback)")
    ap.add_argument("--rele-ligado", action="store_true", help="começa com o relé ligado (o firmware real começa desligado)")
    ap.add_argument("--sem-teclado", action="store_true", help="não lê comandos do stdin")
    args = ap.parse_args()

    with serial.Serial(args.porta, BAUD_INICIAL, timeout=0) as porta:
        placa = PlacaVirtual(porta, args.falhar_baud, args.rele_ligado)
        if not args.sem_teclado:
            threading.Thread(target=ler_teclado, args=(placa,), daemon=True).start()
            print("Comandos: p=pico  t=sobretensão  c=checksum  m=trava  r=reinicia  q=sair")
        try:
            while placa.rodando:
                placa.passo()
                time.sleep(0.002)
        except KeyboardInterrupt:
            pass
        except serial.SerialException as e:
            print(f"Porta perdida: {e}")


if __name__ == "__main__":
    main()
