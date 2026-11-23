"""
Teste de integração do app completo (View + Controller + threads + SQLite) contra o simulador.
Roda sem tela (QT_QPA_PLATFORM=offscreen) e usa pasta temporária: não mexe em data/.

    python tests/teste_integracao_gui.py        # Linux/macOS

Verifica: handshake -> telemetria -> gráfico em tempo real -> gravação no SQLite ->
corte emergencial (evento) -> consulta de histórico assíncrona -> config.json recriado ->
encerramento cooperativo das duas QThreads.
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
from PySide6.QtWidgets import QApplication  # noqa: E402

from controllers.app_controller import AppController  # noqa: E402
from models.config_manager import ConfigManager  # noqa: E402
from par_portas_virtuais import abrir_par  # noqa: E402
from placa_virtual import PlacaVirtual  # noqa: E402
from views.dashboard_view import DashboardView  # noqa: E402
from workers import serial_worker as sw  # noqa: E402


def main():
    sw.AGUARDAR_RESET_S = 0.2            # o simulador não reinicia ao abrir a porta
    pasta = Path(tempfile.mkdtemp())
    porta_app, porta_placa, parar_par = abrir_par()
    placa = PlacaVirtual(serial.Serial(porta_placa, 9600, timeout=0))
    rodando = threading.Event()
    rodando.set()

    def laco_placa():
        while rodando.is_set():
            placa.passo()
            time.sleep(0.005)
    threading.Thread(target=laco_placa, daemon=True).start()

    app = QApplication(sys.argv)
    config = ConfigManager(pasta / "config.json")
    view = DashboardView()
    controller = AppController(view, config, pasta / "smartgrid.db")  # noqa: F841
    view.show()

    r = {}
    u = view.ui

    def conectar():
        u.combo_porta.clear()
        u.combo_porta.addItem(porta_app, porta_app)
        u.combo_baud.setCurrentIndex(u.combo_baud.findData(115200))
        u.spin_periodo.setValue(250)
        u.btn_conectar.click()

    def checar_tempo_real():
        r["estado"] = u.lbl_status_conexao.text()
        r["pontos_rt"] = len(view.grafico._rt["t"])

    def consultar_historico():
        u.radio_historico.setChecked(True)
        u.radio_ultimas.setChecked(True)
        u.spin_ultimas.setValue(20)
        u.btn_consultar.click()

    def checar_historico():
        r["modo"] = view.grafico.modo
        r["pontos_hist"] = len(view.grafico._hist["t"])

    QTimer.singleShot(200, conectar)
    QTimer.singleShot(4000, checar_tempo_real)
    QTimer.singleShot(4200, u.btn_emergencia.click)
    QTimer.singleShot(5000, consultar_historico)
    QTimer.singleShot(6000, checar_historico)
    QTimer.singleShot(6200, lambda: os.remove(pasta / "config.json"))
    QTimer.singleShot(7200, lambda: r.__setitem__("config_recriado", (pasta / "config.json").exists()))
    QTimer.singleShot(7500, view.close)
    QTimer.singleShot(25000, app.quit)
    app.exec()
    rodando.clear()
    parar_par.set()

    con = sqlite3.connect(pasta / "smartgrid.db")
    leituras = con.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
    eventos = {linha[0] for linha in con.execute("SELECT tipo_evento FROM historico_eventos")}
    con.close()

    verificacoes = {
        "handshake concluído (TELEMETRIA)": r.get("estado") == "TELEMETRIA",
        "gráfico em tempo real recebeu pontos": r.get("pontos_rt", 0) > 5,
        "leituras gravadas no SQLite": leituras > 5,
        "corte emergencial virou evento": "CORTE_EMERGENCIAL" in eventos,
        "evento de conexão gravado": "CONEXAO" in eventos,
        "histórico replotado no gráfico": r.get("modo") == "historico" and r.get("pontos_hist", 0) > 0,
        "config.json recriado após exclusão": r.get("config_recriado") is True,
        "janela fechou após encerrar as threads": not view.isVisible(),
    }
    for nome, ok in verificacoes.items():
        print(("OK     " if ok else "FALHOU ") + nome)
    sys.exit(0 if all(verificacoes.values()) else 1)


if __name__ == "__main__":
    main()
