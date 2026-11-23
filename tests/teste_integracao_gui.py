"""
Teste de integração do app completo (DashboardController + threads + SQLite) contra o simulador.
Roda sem tela (QT_QPA_PLATFORM=offscreen) e numa pasta temporária: não mexe em data/.

    python tests/teste_integracao_gui.py        # Linux/macOS

Verifica o caminho inteiro: handshake -> telemetria -> gráfico em tempo real -> gravação no SQLite ->
alavanca virtual (relé) -> botão PARAR (corte emergencial ACID) -> tela de limites -> consulta de histórico
assíncrona -> tela de histórico de eventos -> config.json recriado -> encerramento cooperativo.
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
    sw.AGUARDAR_RESET_S = 0.2            # o simulador não reinicia ao abrir a porta
    pasta = Path(tempfile.mkdtemp())
    os.chdir(pasta)                      # data/config.json e data/smartgrid.db ficam aqui, não no projeto

    from controller.dashboard_controller import DashboardController
    from controller.config_controller import ConfigController
    from controller.historico_controller import HistoricoController

    avisos = []                          # as caixas de mensagem (modais) viram registros, para o teste não travar
    for nome in ("information", "warning", "critical"):
        setattr(QMessageBox, nome, staticmethod(lambda parent, titulo, texto, _n=nome: avisos.append((_n, titulo, texto))))

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
    janela = DashboardController()
    janela.show()

    r = {}
    u = janela.ui
    s = janela.tela_serial.ui

    def conectar():                         # o que o operador faz na tela Serial
        s.combo_porta.clear()
        s.combo_porta.addItem(porta_app)
        s.combo_br.setCurrentText("115200")
        s.spin_amostragem.setValue(250)
        s.btn_conectar.click()

    def checar_tempo_real():
        r["serial"] = s.lbl_status.text()
        r["velocidade"] = s.lbl_velocidade.text()
        r["log_handshake"] = s.txt_log_serial.toPlainText()
        r["pontos_rt"] = len(janela.tempo_x)
        r["medicao"] = u.lbl_tensao.text()
        r["disjuntor_inicial"] = u.lbl_status_disjuntor.text()

    def limites():                          # tela de limites: valida, grava config.json e regras_limites
        dialogo = ConfigController(janela.persistencia)
        dialogo.ui.spin_limite_tensao.setValue(230)
        dialogo.ui.spin_limite_corrente.setValue(25)
        dialogo.ui.btn_salvar.click()
        r["config_json"] = janela.cfg.carregar()
        r["limites_aceitos"] = (dialogo.limite_tensao, dialogo.limite_corrente)

    def historico_grafico():
        u.radio_historico.setChecked(True)
        u.radio_ultimas.setChecked(True)
        u.spin_ultimas.setValue(20)
        u.btn_consultar.click()

    def checar_historico_grafico():
        r["modo"] = janela.modo_historico
        r["pontos_hist"] = len(janela.ax.lines[0].get_xdata()) if janela.ax.lines else 0
        r["titulo_hist"] = janela.ax.get_title()

    def historico_eventos():
        dialogo = HistoricoController(janela.persistencia)
        r["dialogo_historico"] = dialogo
        dialogo.show()

    def checar_historico_eventos():
        r["linhas_eventos"] = r["dialogo_historico"].ui.tabela_logs.rowCount()
        r["dialogo_historico"].close()

    agenda = [
        (200, conectar),
        (4000, checar_tempo_real),
        (4200, u.chk_simulador.click),                                         # alavanca: fecha (!1)
        (5300, lambda: r.__setitem__("alavanca_fechou", u.lbl_status_disjuntor.text())),
        (5400, u.chk_simulador.click),                                         # alavanca: abre (!0)
        (6500, lambda: r.__setitem__("alavanca_abriu", u.lbl_status_disjuntor.text())),
        (6600, u.chk_simulador.click),                                         # alavanca: fecha de novo
        (7700, lambda: r.__setitem__("fechou_de_novo", u.lbl_status_disjuntor.text())),
        (7900, u.btn_parar.click),                                             # PARAR
        (9000, lambda: r.__setitem__("apos_parar", u.lbl_status_disjuntor.text())),
        (9200, limites),
        (9500, historico_grafico),
        (10500, checar_historico_grafico),
        (10600, historico_eventos),
        (12600, checar_historico_eventos),
        (12800, lambda: os.remove(pasta / "data" / "config.json")),
        (14800, lambda: r.__setitem__("config_recriado", (pasta / "data" / "config.json").exists())),
        (15200, janela.close),
        (40000, app.quit),
    ]
    for ms, acao in agenda:
        QTimer.singleShot(ms, acao)
    app.exec()
    rodando.clear()
    parar_par.set()

    con = sqlite3.connect(pasta / "data" / "smartgrid.db")
    leituras = con.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
    tipos = [linha[0] for linha in con.execute("SELECT tipo_evento FROM historico_eventos")]
    regras = con.execute("SELECT limite_corrente, tensao_desarme FROM regras_limites").fetchall()
    status = con.execute("SELECT status FROM dispositivos WHERE id = 1").fetchone()[0]
    con.close()

    verificacoes = {
        "handshake concluído (tela serial Conectado)": r.get("serial") == "Conectado",
        "velocidade negociada exibida (115200 bps)": "115200" in r.get("velocidade", ""),
        "log do handshake na tela serial (!S115200 a 9600 e ACK da placa)": all(
            x in r.get("log_handshake", "") for x in ("!S115200", "INICIANDO EM 115200")),
        "gráfico em tempo real recebeu pontos": r.get("pontos_rt", 0) > 5,
        "medições aparecem no dashboard": r.get("medicao", "").endswith(" V") and r.get("medicao") != "0.0 V",
        "disjuntor ABERTO ao conectar (a placa liga com o relé desligado)": r.get("disjuntor_inicial") == "ABERTO",
        "alavanca fecha o disjuntor (!1)": r.get("alavanca_fechou") == "FECHADO",
        "alavanca abre o disjuntor (!0)": r.get("alavanca_abriu") == "ABERTO",
        "alavanca fecha de novo": r.get("fechou_de_novo") == "FECHADO",
        "botão PARAR abre o disjuntor": r.get("apos_parar") == "ABERTO",
        "popup do corte emergencial (texto original)": any(
            "Corte emergencial acionado com sucesso e salvo no banco!" in a[2] for a in avisos),
        "leituras gravadas no SQLite": leituras > 5,
        "eventos EMERGÊNCIA, OPERAÇÃO, SERIAL e CONFIG gravados": {"EMERGÊNCIA", "OPERAÇÃO", "SERIAL", "CONFIG"} <= set(tipos),
        "chaveamento gravado uma vez só (3 eventos OPERAÇÃO)": tipos.count("OPERAÇÃO") == 3,
        "status do disjuntor no banco = ABERTO": status == "ABERTO",
        "limites gravados em config.json e regras_limites": regras == [(25.0, 230.0)]
                                                           and r.get("config_json", {}).get("limite_tensao") == 230.0
                                                           and r.get("limites_aceitos") == (230.0, 25.0),
        "histórico replotado no gráfico (modo consulta)": r.get("modo") is True and r.get("pontos_hist", 0) > 0,
        "tela de histórico de eventos carregada do banco": r.get("linhas_eventos", 0) >= 4,
        "config.json recriado após exclusão": r.get("config_recriado") is True,
        "janela fechou após encerrar as threads": not janela.isVisible(),
    }
    for nome, ok in verificacoes.items():
        print(("OK     " if ok else "FALHOU ") + nome)
    if not all(verificacoes.values()):
        print("detalhes:", r, "| eventos:", tipos, "| regras:", regras, "| status:", status, "| avisos:", avisos)
    sys.exit(0 if all(verificacoes.values()) else 1)


if __name__ == "__main__":
    main()
