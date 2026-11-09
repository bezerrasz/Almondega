"""View do histórico de eventos (atuações do disjuntor, cortes, falhas, conexões)."""
from PySide6.QtCore import QDateTime, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidgetItem

from ui.ui_tela_historico import Ui_DialogEventos

CORES = {"CORTE": "#7f1d1d", "ALERTA": "#78350f", "FALHA": "#4c1d95"}


class EventosView(QDialog):
    filtro_solicitado = Signal(object, object)   # datetime início, datetime fim

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DialogEventos()
        self.ui.setupUi(self)
        t = self.ui.tabela_eventos
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["Data/hora", "Tipo", "Dispositivo", "Valor", "Descrição"])
        h = t.horizontalHeader()
        for col in range(4):
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        agora = QDateTime.currentDateTime()
        self.ui.dt_fim.setDateTime(agora.addSecs(3600))
        self.ui.dt_inicio.setDateTime(agora.addDays(-7))

        self.ui.btn_filtrar.clicked.connect(self._emitir_filtro)
        self.ui.botoes.rejected.connect(self.reject)

    def _emitir_filtro(self):
        self.filtro_solicitado.emit(self.ui.dt_inicio.dateTime().toPython(),
                                    self.ui.dt_fim.dateTime().toPython())

    def solicitar_carga_inicial(self):
        self._emitir_filtro()

    def indicar_carregando(self):
        self.ui.btn_filtrar.setEnabled(False)
        self.ui.lbl_total.setText("Consultando banco...")

    def mostrar_eventos(self, eventos):
        t = self.ui.tabela_eventos
        t.setRowCount(len(eventos))
        for linha, ev in enumerate(eventos):
            valor = "" if ev.valor_medido is None else f"{ev.valor_medido:.2f}"
            celulas = [ev.timestamp.strftime("%d/%m/%Y %H:%M:%S"), ev.tipo, ev.dispositivo_tag,
                       valor, ev.descricao]
            cor = next((QColor(c) for chave, c in CORES.items() if ev.tipo.startswith(chave)), None)
            for col, texto in enumerate(celulas):
                item = QTableWidgetItem(texto)
                if cor:
                    item.setBackground(cor)
                t.setItem(linha, col, item)
        self.ui.btn_filtrar.setEnabled(True)
        self.ui.lbl_total.setText(f"{len(eventos)} evento(s)")
