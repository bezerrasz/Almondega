"""
Teste de integração (Linux/macOS): SerialWorker em QThread x simulador da placa.

    python tests/teste_serial_simulador.py            # negociação normal (115200)
    python tests/teste_serial_simulador.py --fallback # simula falha a 115200 e 38400
"""
import argparse
import sys
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "simulador"))
sys.path.insert(0, str(RAIZ / "tests"))

import serial  # noqa: E402
from PySide6.QtCore import QCoreApplication, QThread, QTimer  # noqa: E402

from par_portas_virtuais import abrir_par  # noqa: E402
from placa_virtual import PlacaVirtual  # noqa: E402
from workers import serial_worker as sw  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fallback", action="store_true")
    ap.add_argument("--segundos", type=float, default=8)
    args = ap.parse_args()

    sw.AGUARDAR_RESET_S = 0.2     # simulador não reinicia ao abrir a porta
    porta_app, porta_placa, parar_par = abrir_par()

    ser_placa = serial.Serial(porta_placa, 9600, timeout=0)
    placa = PlacaVirtual(ser_placa, [115200, 38400] if args.fallback else [])
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
    resultado = {"leituras": 0, "baud": None, "estados": [], "dj": []}

    thread.started.connect(worker.executar)
    worker.finalizado.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(app.quit)
    worker.estado_mudou.connect(lambda e, d: (resultado["estados"].append(e), print(f"[APP] {e}: {d}")))
    worker.log_protocolo.connect(lambda t: print(f"[APP]   {t}"))
    worker.velocidade_negociada.connect(lambda b: resultado.__setitem__("baud", b))
    worker.leitura_recebida.connect(lambda l: resultado.__setitem__("leituras", resultado["leituras"] + 1))
    worker.disjuntor_confirmado.connect(lambda f: resultado["dj"].append(f))
    worker.falha_comunicacao.connect(lambda t: print(f"[APP] FALHA: {t}"))

    QTimer.singleShot(int(args.segundos * 1000) - 2500, lambda: worker.enviar_comando("DJ,0"))
    QTimer.singleShot(int(args.segundos * 1000) - 1500, lambda: worker.enviar_comando("DJ,1"))
    QTimer.singleShot(int(args.segundos * 1000), lambda: worker.parar())
    QTimer.singleShot(int(args.segundos * 1000) + 15000, app.quit)   # segurança
    thread.start()
    app.exec()
    rodando.clear()
    parar_par.set()

    print("\nRESULTADO:", resultado["baud"], "bps |", resultado["leituras"], "leituras | DJ:",
          resultado["dj"], "| estados:", " > ".join(dict.fromkeys(resultado["estados"])))
    esperado = 19200 if args.fallback else 115200
    ok = resultado["baud"] == esperado and resultado["leituras"] > 3 and resultado["dj"] == [False, True]
    print("OK" if ok else "FALHOU")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
