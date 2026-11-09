"""
View principal. Regras desta camada:
  - só desenha e captura ações do operador (emitindo sinais);
  - não calcula nada de engenharia, não acessa banco, não acessa porta serial;
  - recebe tudo pronto do controller através dos métodos mostrar_*/definir_*.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QMainWindow, QMessageBox, QVBoxLayout

from ui.ui_dashboard import Ui_MainWindow
from views.estilo import estilo_indicador
from views.grafico import GRANDEZAS, GraficoWidget

COR_POR_ESTADO = {
    "TELEMETRIA": "verde",
    "ABRINDO": "amarelo", "HANDSHAKE": "amarelo", "SINCRONIZANDO": "amarelo",
    "RECONECTANDO": "amarelo", "ENCERRANDO": "amarelo",
    "DESCONECTADO": "vermelho",
}
MAX_LINHAS_CONSOLE = 500


class DashboardView(QMainWindow):
    conectar_solicitado = Signal(str, int, int)        # porta, baud alvo, período (ms)
    desconectar_solicitado = Signal()
    atualizar_portas_solicitado = Signal()
    disjuntor_solicitado = Signal(bool)                 # True = fechar
    emergencia_solicitada = Signal()
    abrir_limites_solicitado = Signal()
    abrir_eventos_solicitado = Signal()
    modo_grafico_alterado = Signal(str)                 # "tempo_real" | "historico"
    consulta_historico_solicitada = Signal(dict)
    fechamento_solicitado = Signal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._pode_fechar = False
        self._fechamento_pedido = False

        self.grafico = GraficoWidget(self.ui.widget_grafico)
        lay = QVBoxLayout(self.ui.widget_grafico)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.grafico)

        for chave, (nome, unid, _) in GRANDEZAS.items():
            self.ui.combo_grandeza.addItem(f"{nome} ({unid})", chave)

        agora = QDateTime.currentDateTime()
        self.ui.dt_fim.setDateTime(agora)
        self.ui.dt_inicio.setDateTime(agora.addSecs(-3600))

        self._conectar_widgets()
        self.mostrar_estado_conexao("DESCONECTADO", "selecione a porta e clique em Conectar")
        self.mostrar_disjuntor(None)
        self.definir_modo("tempo_real")
        self.habilitar_comandos(False)

    def _conectar_widgets(self):
        u = self.ui
        u.btn_conectar.clicked.connect(lambda: self.conectar_solicitado.emit(
            u.combo_porta.currentData() or u.combo_porta.currentText().strip(),
            int(u.combo_baud.currentData()), u.spin_periodo.value()))
        u.btn_desconectar.clicked.connect(self.desconectar_solicitado)
        u.btn_atualizar_portas.clicked.connect(self.atualizar_portas_solicitado)
        u.btn_fechar_dj.clicked.connect(lambda: self.disjuntor_solicitado.emit(True))
        u.btn_abrir_dj.clicked.connect(lambda: self.disjuntor_solicitado.emit(False))
        u.btn_emergencia.clicked.connect(self.emergencia_solicitada)
        u.btn_config_limites.clicked.connect(self.abrir_limites_solicitado)
        u.btn_eventos.clicked.connect(self.abrir_eventos_solicitado)
        u.radio_tempo_real.toggled.connect(
            lambda marcado: self.modo_grafico_alterado.emit("tempo_real" if marcado else "historico"))
        u.combo_grandeza.currentIndexChanged.connect(
            lambda _: self.grafico.definir_grandeza(u.combo_grandeza.currentData()))
        u.btn_consultar.clicked.connect(self._emitir_consulta)

    def _emitir_consulta(self):
        u = self.ui
        if u.radio_ultimas.isChecked():
            filtro = {"modo": "ultimas", "quantidade": u.spin_ultimas.value()}
        else:
            filtro = {"modo": "intervalo",
                      "inicio": u.dt_inicio.dateTime().toPython(),
                      "fim": u.dt_fim.dateTime().toPython()}
        self.consulta_historico_solicitada.emit(filtro)

    # ---------------- conexão ----------------
    def definir_portas(self, portas: list[tuple[str, str]], preferida: str):
        combo = self.ui.combo_porta
        combo.blockSignals(True)
        combo.clear()
        for dispositivo, descricao in portas:
            combo.addItem(f"{dispositivo} - {descricao}", dispositivo)
        indice = combo.findData(preferida)
        if indice >= 0:
            combo.setCurrentIndex(indice)
        else:
            combo.setEditText(preferida)
        combo.blockSignals(False)

    def definir_velocidades(self, velocidades, alvo: int):
        combo = self.ui.combo_baud
        combo.clear()
        for b in velocidades:
            combo.addItem(f"{b} bps", b)
        combo.setCurrentIndex(max(0, combo.findData(alvo)))

    def definir_periodo(self, periodo_ms: int):
        self.ui.spin_periodo.setValue(periodo_ms)

    def mostrar_estado_conexao(self, estado: str, detalhe: str = ""):
        u = self.ui
        u.lbl_status_conexao.setText(estado)
        u.lbl_status_conexao.setStyleSheet(estilo_indicador(COR_POR_ESTADO.get(estado, "cinza")))
        u.lbl_detalhe_conexao.setText(detalhe or "-")
        ativo = estado != "DESCONECTADO"
        u.btn_conectar.setEnabled(not ativo)
        u.btn_desconectar.setEnabled(ativo and estado != "ENCERRANDO")
        for w in (u.combo_porta, u.combo_baud, u.spin_periodo, u.btn_atualizar_portas):
            w.setEnabled(not ativo)
        self.statusBar().showMessage(f"Serial: {estado} {('- ' + detalhe) if detalhe else ''}")

    def mostrar_estatisticas(self, ok: int, invalidos: int, perdidos: int):
        self.ui.lbl_estatisticas.setText(f"Pacotes: {ok} ok · {invalidos} inválidos · {perdidos} perdidos")

    # ---------------- medições e disjuntor ----------------
    def mostrar_medicoes(self, tensao: float, corrente: float, potencia: float):
        self.ui.lbl_tensao.setText(f"{tensao:.2f} V")
        self.ui.lbl_corrente.setText(f"{corrente:.2f} A")
        self.ui.lbl_potencia.setText(f"{potencia:.1f} W")

    def limpar_medicoes(self):
        for lbl, unid in ((self.ui.lbl_tensao, "V"), (self.ui.lbl_corrente, "A"), (self.ui.lbl_potencia, "W")):
            lbl.setText(f"--- {unid}")

    def mostrar_disjuntor(self, fechado: bool | None):
        lbl = self.ui.lbl_status_disjuntor
        if fechado is None:
            lbl.setText("SEM LINK")
            lbl.setStyleSheet(estilo_indicador("cinza"))
        else:
            lbl.setText("FECHADO (energizado)" if fechado else "ABERTO (desenergizado)")
            lbl.setStyleSheet(estilo_indicador("verde" if fechado else "vermelho"))

    def habilitar_comandos(self, habilitar: bool):
        for w in (self.ui.btn_fechar_dj, self.ui.btn_abrir_dj, self.ui.btn_emergencia):
            w.setEnabled(habilitar)

    # ---------------- gráfico ----------------
    def definir_modo(self, modo: str):
        historico = modo == "historico"
        self.ui.grp_filtro.setEnabled(historico)
        self.ui.radio_historico.blockSignals(True)
        self.ui.radio_tempo_real.blockSignals(True)
        self.ui.radio_historico.setChecked(historico)
        self.ui.radio_tempo_real.setChecked(not historico)
        self.ui.radio_historico.blockSignals(False)
        self.ui.radio_tempo_real.blockSignals(False)
        self.grafico.definir_modo(modo)

    def definir_capacidade_grafico(self, pontos: int):
        self.grafico.definir_capacidade_tempo_real(pontos)

    def definir_limites_grafico(self, limites: dict):
        self.grafico.definir_limites(limites)

    def adicionar_ponto_tempo_real(self, t: datetime, tensao: float, corrente: float, potencia: float):
        self.grafico.adicionar_ponto(t, tensao, corrente, potencia)

    def mostrar_historico(self, t, tensao, corrente, potencia, titulo: str):
        self.grafico.carregar_historico(t, tensao, corrente, potencia, titulo)

    def indicar_consulta_em_andamento(self, em_andamento: bool):
        self.ui.btn_consultar.setEnabled(not em_andamento)
        self.ui.btn_consultar.setText("Consultando..." if em_andamento else "Consultar")

    # ---------------- mensagens ----------------
    def escrever_console(self, texto: str):
        console = self.ui.txt_console
        console.appendPlainText(f"{datetime.now():%H:%M:%S}  {texto}")
        if console.blockCount() > MAX_LINHAS_CONSOLE:
            cursor = console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        console.verticalScrollBar().setValue(console.verticalScrollBar().maximum())

    def mostrar_alerta(self, titulo: str, mensagem: str, critico: bool = False):
        """Caixa NÃO modal: a telemetria e o gráfico continuam atualizando por trás."""
        caixa = QMessageBox(QMessageBox.Icon.Critical if critico else QMessageBox.Icon.Warning,
                            titulo, mensagem, QMessageBox.StandardButton.Ok, self)
        caixa.setModal(False)
        caixa.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        caixa.show()
        self.statusBar().showMessage(mensagem, 10000)

    def mostrar_status(self, texto: str, ms: int = 5000):
        self.statusBar().showMessage(texto, ms)

    # ---------------- fechamento cooperativo ----------------
    def permitir_fechamento(self):
        self._pode_fechar = True
        self.close()

    def closeEvent(self, evento):
        if self._pode_fechar:
            evento.accept()
            return
        evento.ignore()                      # espera as threads terminarem
        if not self._fechamento_pedido:
            self._fechamento_pedido = True
            self.setEnabled(False)
            self.statusBar().showMessage("Encerrando threads de comunicação e banco...")
            self.fechamento_solicitado.emit()
