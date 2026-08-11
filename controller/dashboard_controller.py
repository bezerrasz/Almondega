from PySide6.QtWidgets import QDialog, QMessageBox
from ui.dashboard import Ui_Dialog
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import random

class DashboardController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.lbl_tensao.setText("220 V")
        self.ui.lbl_corrente.setText("10.5 A")
        self.ui.lbl_potencia.setText("2310 W")

        self.ui.btn_emergencia.clicked.connect(self.acionar_emergencia)

        self.renderizar_grafico()
        self.ui.slider_limite.valueChanged.connect(self.mostrar_valor_bolinha)

        self.ui.chk_simulador.toggled.connect(self.atualizar_status_led)


    def acionar_emergencia(self):
        self.ui.chk_simulador.setChecked(False)
        self.ui.lbl_status_disjuntor.setText("ABERTO")
        self.ui.lbl_status_disjuntor.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        QMessageBox.warning(self, "Alerta", "Corte emergencial acionado!")
        

    def renderizar_grafico(self):

        fig, ax = plt.subplots()
        canvas = FigureCanvas(fig)

        horas = list(range(24))
        demanda_w = [random.randint(1000, 3000) for _ in range(24)]
        ax.plot(horas, demanda_w, marker='o', linestyle='-', color="#f5890f")

        ax.set_title("Curva de Demanda (Últimas 24h)")
        ax.set_xlabel("Hora do dia")
        ax.set_ylabel("Potência (W)")
        ax.grid(True)

        fig.subplots_adjust(left=0.18, bottom=0.18, right=0.95, top=0.90)

        layout = QVBoxLayout(self.ui.widget_grafico)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

    def mostrar_valor_bolinha(self, valor):
        posicao_mouse = QCursor.pos()
        
        QToolTip.showText(posicao_mouse, f"{valor} W", self.ui.slider_limite)
       
        self.limite_potencia = valor

    def atualizar_status_led(self, ligado):
        if ligado:
            self.ui.lbl_status_disjuntor.setText("FECHADO")
            self.ui.lbl_status_disjuntor.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
            )
        else:
            self.ui.lbl_status_disjuntor.setText("ABERTO")
            self.ui.lbl_status_disjuntor.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
            )