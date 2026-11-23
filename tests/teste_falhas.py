"""
Falhas induzidas na SerialThread (bancada): cabo puxado e placa travada.
O worker deve avisar, reconectar sozinho e refazer o handshake.

    python tests/teste_falhas.py        # Linux/macOS (~25 s)
"""
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for p in (RAIZ, RAIZ / "simulador", RAIZ / "tests"):
    sys.path.insert(0, str(p))

import serial  # noqa: E402
from PySide6.QtCore import QCoreApplication, QThread, QTimer  # noqa: E402

from par_portas_virtuais import abrir_par  # noqa: E402
from placa_virtual import PlacaVirtual  # noqa: E402
from workers import serial_worker as sw  # noqa: E402


def main():
    sw.AGUARDAR_RESET_S = 0.2
    sw.INTERVALO_RECONEXAO_S = 1.0
    porta_app, porta_placa, parar_par = abrir_par()
    placa = PlacaVirtual(serial.Serial(porta_placa, 9600, timeout=0))
    rodando = threading.Event()
    rodando.set()

    def laco_placa():
        while rodando.is_set():
            placa.passo()
            time.sleep(0.005)
    threading.Thread(target=laco_placa, daemon=True).start()

    app = QCoreApplication(sys.argv)
    thread = QThread()
    worker = sw.SerialWorker(porta_app, 115200, 250)
    worker.moveToThread(thread)
    estados, falhas = [], []

    thread.started.connect(worker.executar)
    worker.finalizado.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(app.quit)
    worker.estado_mudou.connect(lambda e, d: estados.append(e))
    worker.falha_comunicacao.connect(lambda t: falhas.append(t))

    def puxar_cabo():
        def quebrado(*a, **k):
            raise serial.SerialException("device disconnected")
        worker._ser.read = quebrado      # o pyserial levanta SerialException ao perder o USB

    def travar_placa():
        placa.travada_ate = time.monotonic() + 8   # placa muda por 8 s (watchdog = 3 s)

    QTimer.singleShot(3000, puxar_cabo)
    QTimer.singleShot(9000, travar_placa)
    QTimer.singleShot(26000, lambda: worker.parar())   # lambda: chamada direta, não enfileirada na thread do worker
    QTimer.singleShot(40000, app.quit)
    thread.start()
    app.exec()
    terminou = thread.wait(3000)         # a thread encerra sozinha depois de parar()
    rodando.clear()
    parar_par.set()

    verificacoes = {
        "cabo puxado detectado": any("indisponível" in f for f in falhas),
        "placa travada detectada pelo watchdog": any("Link perdido" in f for f in falhas),
        "handshake refeito após as falhas (3 links)": estados.count("TELEMETRIA") >= 3,
        "thread terminou de forma cooperativa (parar -> !P -> finished)": terminou and "ENCERRANDO" in estados,
    }
    for nome, ok in verificacoes.items():
        print(("OK     " if ok else "FALHOU ") + nome)
    sys.exit(0 if all(verificacoes.values()) else 1)


if __name__ == "__main__":
    main()
