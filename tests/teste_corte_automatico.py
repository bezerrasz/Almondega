"""
Corte automático: pico de corrente induzido no simulador -> SOBRECARGA -> DJ,0 -> ACK -> corte emergencial ACID.
Roda sem tela e em pasta temporária.

    python tests/teste_corte_automatico.py
"""
import os
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for p in (RAIZ, RAIZ / "simulador", RAIZ / "tests"):
    sys.path.insert(0, str(p))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import serial  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from par_portas_virtuais import abrir_par  # noqa: E402
from placa_virtual import PlacaVirtual  # noqa: E402
from workers import serial_worker as sw  # noqa: E402


def main():
    sw.AGUARDAR_RESET_S = 0.2
    pasta = Path(tempfile.mkdtemp())
    os.chdir(pasta)
    from controller.dashboard_controller import DashboardController

    avisos = []
    for nome in ("information", "warning", "critical"):
        setattr(QMessageBox, nome, staticmethod(lambda parent, titulo, texto, _n=nome: avisos.append((_n, texto))))

    porta_app, porta_placa, parar_par = abrir_par()
    placa = PlacaVirtual(serial.Serial(porta_placa, 9600, timeout=0))
    rodando = threading.Event()
    rodando.set()

    def laco():
        while rodando.is_set():
            placa.passo()
            time.sleep(0.005)
    threading.Thread(target=laco, daemon=True).start()

    app = QApplication(sys.argv)
    janela = DashboardController()
    janela.show()
    s = janela.tela_serial.ui
    r = {}

    def conectar():
        s.combo_porta.clear()
        s.combo_porta.addItem(porta_app)
        s.combo_br.setCurrentText("115200")
        s.spin_amostragem.setValue(250)
        s.btn_conectar.click()

    QTimer.singleShot(200, conectar)
    QTimer.singleShot(3000, lambda: placa.comando_operador("p"))          # pico de corrente
    QTimer.singleShot(7500, lambda: r.__setitem__("status", janela.ui.lbl_status_disjuntor.text()))
    QTimer.singleShot(7600, lambda: r.__setitem__("corrente", janela.ui.lbl_corrente.text()))
    QTimer.singleShot(8000, janela.close)
    QTimer.singleShot(30000, app.quit)
    app.exec()
    rodando.clear()
    parar_par.set()

    con = sqlite3.connect(pasta / "data" / "smartgrid.db")
    eventos = con.execute("SELECT tipo_evento, descricao FROM historico_eventos").fetchall()
    status = con.execute("SELECT status FROM dispositivos WHERE id = 1").fetchone()[0]
    con.close()
    tipos = [e[0] for e in eventos]

    verificacoes = {
        "alerta SOBRECARGA gravado (ALERTA CRÍTICO)": any(t == "ALERTA CRÍTICO" and "SOBRECARGA" in d for t, d in eventos),
        "corte emergencial gravado uma única vez (sem repetir a cada amostra)": tipos.count("ALERTA CRÍTICO") == 1,
        "disjuntor ABERTO na tela": r.get("status") == "ABERTO",
        "status ABERTO no banco": status == "ABERTO",
        "popup do corte emergencial com o motivo": any("Corte emergencial acionado" in t and "SOBRECARGA" in t for _, t in avisos),
    }
    for nome, ok in verificacoes.items():
        print(("OK     " if ok else "FALHOU ") + nome)
    if not all(verificacoes.values()):
        print("detalhes:", r, eventos, avisos)
    sys.exit(0 if all(verificacoes.values()) else 1)


if __name__ == "__main__":
    main()
