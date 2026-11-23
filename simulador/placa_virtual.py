"""
Simulador da placa Smart Grid em porta serial virtual.

Implementa exatamente o mesmo protocolo do firmware (firmware/smartgrid_placa):
  AGUARDANDO_HS -> AGUARDANDO_SYNC -> TELEMETRIA

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
    r  -> reinicia a placa (volta a 9600 / aguardando handshake)
    q  -> encerra o simulador
Opção --falhar-baud 115200 faz a placa não entender o SYNC nessa velocidade,
para demonstrar o fallback de velocidade do desktop.
"""
import argparse
import math
import random
import sys
import threading
import time

import serial

BAUD_INICIAL = 9600
BAUDS_SUPORTADOS = (9600, 19200, 38400, 115200)
TIMEOUT_SYNC = 3.0
TIMEOUT_LINK = 5.0


def checksum(texto: str) -> str:
    ck = 0
    for ch in texto:
        ck ^= ord(ch)
    return f"{ck:02X}"


class PlacaVirtual:
    def __init__(self, porta: serial.Serial, falhar_bauds=()):
        self.porta = porta
        self.falhar_bauds = set(falhar_bauds)
        self.lock = threading.Lock()
        self.rodando = True
        self._reiniciar()

    # ---------------- estado ----------------
    def _reiniciar(self):
        self.estado = "AGUARDANDO_HS"
        self.baud = BAUD_INICIAL
        self.porta.baudrate = BAUD_INICIAL
        self.periodo = 1.0
        self.seq = 0
        self.disjuntor_fechado = True
        self.instante_estado = time.monotonic()
        self.ultimo_rx = time.monotonic()
        self.ultimo_envio = 0.0
        self.buffer = b""
        self.pico_ate = 0.0
        self.sobretensao_ate = 0.0
        self.travada_ate = 0.0
        self.corromper = 0
        self._log("placa iniciada: AGUARDANDO_HS a 9600 bps")

    def _mudar_estado(self, novo):
        self.estado = novo
        self.instante_estado = time.monotonic()
        self._log(f"estado -> {novo} ({self.baud} bps)")

    def _trocar_baud(self, novo):
        self.porta.flush()
        time.sleep(0.02)
        self.porta.baudrate = novo
        self.baud = novo
        self.buffer = b""

    def _voltar_espera(self):
        if self.baud != BAUD_INICIAL:
            self._trocar_baud(BAUD_INICIAL)
        self.seq = 0
        self._mudar_estado("AGUARDANDO_HS")

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
        self.buffer += self.porta.read(n)
        self.ultimo_rx = time.monotonic()
        while b"\n" in self.buffer:
            bruto, self.buffer = self.buffer.split(b"\n", 1)
            linha = bruto.decode("ascii", errors="replace").strip()
            if linha:
                self._processar(linha)

    # ---------------- medições ----------------
    def _tensao(self):
        t = time.monotonic()
        v = 220.0 + 2.5 * math.sin(t / 7.0) + random.uniform(-0.5, 0.5)
        if t < self.sobretensao_ate:
            v = 252.0 + random.uniform(-1, 1)
        return v

    def _corrente(self):
        if not self.disjuntor_fechado:
            return 0.0
        t = time.monotonic()
        i = 11.0 + 3.0 * math.sin(t / 10.0) + random.uniform(-0.3, 0.3)
        if t < self.pico_ate:
            i = 36.0 + random.uniform(-1, 1)
        return i

    def _enviar_telemetria(self):
        self.seq += 1
        corpo = (f"DATA,{self.seq},{self._tensao():.2f},{self._corrente():.2f},"
                 f"{1 if self.disjuntor_fechado else 0}")
        ck = checksum(corpo)
        if self.corromper > 0:
            self.corromper -= 1
            ck = "00" if ck != "00" else "FF"
        self._enviar(f"{corpo}*{ck}")

    # ---------------- protocolo ----------------
    def _processar(self, linha: str):
        if time.monotonic() < self.travada_ate:
            return
        if linha.startswith("HS,"):
            self._handshake(linha[3:])
            return

        if self.estado == "AGUARDANDO_HS":
            self._enviar("NAK,AGUARDANDO_HS")
        elif self.estado == "AGUARDANDO_SYNC":
            if linha == "SYNC":
                if self.baud in self.falhar_bauds:
                    self._log(f"(falha induzida) SYNC ilegível a {self.baud} bps")
                    return
                self._enviar("ACK,SYNC")
                self.ultimo_envio = time.monotonic()
                self._mudar_estado("TELEMETRIA")
        elif self.estado == "TELEMETRIA":
            if linha == "PING":
                pass
            elif linha in ("DJ,0", "DJ,1"):
                self.disjuntor_fechado = linha.endswith("1")
                self._enviar(f"ACK,{linha}")
                self._log("disjuntor " + ("FECHADO" if self.disjuntor_fechado else "ABERTO"))
            elif linha == "STOP":
                self._enviar("ACK,STOP")
                self._voltar_espera()
            elif linha == "SYNC":
                self._enviar("ACK,SYNC")
            else:
                self._enviar(f"NAK,CMD_INVALIDO:{linha}")

    def _handshake(self, args: str):
        partes = args.split(",")
        if len(partes) != 2:
            self._enviar("NAK,HS_FORMATO")
            return
        try:
            baud, periodo = int(partes[0]), int(partes[1])
        except ValueError:
            self._enviar("NAK,HS_FORMATO")
            return
        if baud not in BAUDS_SUPORTADOS:
            self._enviar("NAK,HS_BAUD")
            return
        if not 200 <= periodo <= 5000:
            self._enviar("NAK,HS_PERIODO")
            return
        self.periodo = periodo / 1000.0
        self._enviar(f"ACK,HS,{baud},{periodo}")
        self._log(f"handshake recebido: {baud} bps, período {periodo} ms")
        if baud != self.baud:
            self._trocar_baud(baud)
        self._mudar_estado("AGUARDANDO_SYNC")

    # ---------------- laço principal ----------------
    def passo(self):
        with self.lock:
            self._ler()
            agora = time.monotonic()
            if agora < self.travada_ate:
                return
            if self.estado == "AGUARDANDO_SYNC" and agora - self.instante_estado > TIMEOUT_SYNC:
                self._log("SYNC não chegou: voltando para 9600")
                self._voltar_espera()
            elif self.estado == "TELEMETRIA":
                if agora - self.ultimo_rx > TIMEOUT_LINK:
                    self._log("desktop em silêncio: voltando para espera")
                    self._voltar_espera()
                elif agora - self.ultimo_envio >= self.periodo:
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
    ap = argparse.ArgumentParser(description="Simulador da placa Smart Grid")
    ap.add_argument("porta", help="porta serial do lado da placa (ex.: COM11 ou /dev/pts/5)")
    ap.add_argument("--falhar-baud", type=int, nargs="*", default=[],
                    help="velocidades em que o SYNC 'não chega' (demonstra o fallback)")
    ap.add_argument("--sem-teclado", action="store_true", help="não lê comandos do stdin")
    args = ap.parse_args()

    with serial.Serial(args.porta, BAUD_INICIAL, timeout=0) as porta:
        placa = PlacaVirtual(porta, args.falhar_baud)
        if not args.sem_teclado:
            threading.Thread(target=ler_teclado, args=(placa,), daemon=True).start()
            print("Comandos: p=pico  t=sobretensão  c=checksum  m=trava  r=reinicia  q=sair")
        try:
            while placa.rodando:
                placa.passo()
                time.sleep(0.005)
        except KeyboardInterrupt:
            pass
        except serial.SerialException as e:
            print(f"Porta perdida: {e}")


if __name__ == "__main__":
    main()
