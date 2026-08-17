from PySide6.QtWidgets import QDialog, QMessageBox
from ui.dashboard import Ui_Dialog
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import random
import datetime
from PySide6.QtCore import QTimer
from collections import deque
from controller.config_controller import ConfigController
from controller.serialport_controller import SerialPortController
from controller.historico_controller import HistoricoController
from models.sistema_model import SistemaModel

class DashboardController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("⚡ Smart Grid - Dashboard")

        #INICIALIZACAO DO SISTEMA
        self.model = SistemaModel()

        # CONFIG MANUAL DE TENSAO E CORRENTE
        self.model.tensao_atual = 220.0
        self.model.corrente_atual = 10.5
        self.atualizar_indicadores()

        # BOTAO DE EMERGENCIA / ALAVANCA 
        self.ui.btn_parar.clicked.connect(self.acionar_emergencia)

        self.ui.chk_simulador.toggled.connect(self.mudar_estado_alavanca)

        # CRIACAO DE GRAFICO
        self.tempo_x = deque(maxlen=60) 
        self.potencia_y = deque(maxlen=60)
        self.tempo_atual = 0
        
        self.preparar_grafico_realtime()
        self.timer_grafico = QTimer()
        self.timer_grafico.timeout.connect(self.atualizar_linha_grafico)
        self.timer_grafico.start(1000)

        # BOLINHA DE LIMITE
        self.ui.slider_limite.valueChanged.connect(self.mostrar_valor_bolinha)

        # LED DE STATUS
        self.ui.chk_simulador.toggled.connect(self.atualizar_status_led)

        # BOTOES QUE MUDAM AS TELAS
        self.ui.btn_config_limites.clicked.connect(self.abrir_tela_configuracao)
        self.ui.btn_tela_serial.clicked.connect(self.abrir_tela_serial)
        self.ui.btn_tela_historico.clicked.connect(self.abrir_tela_historico)

    # TELA 1
    def atualizar_indicadores(self):
        v = self.model.tensao_atual
        i = self.model.corrente_atual
        
        p = self.model.calcular_potencia()

        self.ui.lbl_tensao.setText(f"{v:.1f} V")
        self.ui.lbl_corrente.setText(f"{i:.1f} A")
        self.ui.lbl_potencia.setText(f"{p:.1f} W")

    def acionar_emergencia(self):
        self.ui.chk_simulador.setChecked(False)
        self.ui.lbl_status_disjuntor.setText("ABERTO")
        self.ui.lbl_status_disjuntor.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        QMessageBox.warning(self, "Alerta", "Corte emergencial acionado!")

        self.model.registrar_log("EMERGÊNCIA", "Botão de PARADA acionado pelo operador!")

    def mudar_estado_alavanca(self, estado):
            if estado == True:
                self.model.registrar_log("OPERAÇÃO", "Alavanca acionada: Sistema LIGADO.")
            else:
                self.model.registrar_log("OPERAÇÃO", "Alavanca recuada: Sistema DESLIGADO.")

    def preparar_grafico_realtime(self):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        self.linha, = self.ax.plot([], [], linestyle='-', color="#f5890f", linewidth=2)

        self.ax.set_title("Consumo em Tempo Real (Últimos 60s)")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Potência (W)")
        self.ax.set_ylim(0, 3500)
        self.ax.grid(True)
        self.fig.subplots_adjust(left=0.18, bottom=0.18, right=0.95, top=0.90)

        layout = QVBoxLayout(self.ui.widget_grafico)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def atualizar_linha_grafico(self):
        self.tempo_atual += 1
        
        if self.ui.chk_simulador.isChecked() == False:
            self.model.tensao_atual = 0.0
            self.model.corrente_atual = 0.0
        else:
            self.model.tensao_atual = random.uniform(218.0, 222.0)
            self.model.corrente_atual = random.uniform(8.0, 12.0)
            
            limite = self.model.setpoint_corrente
            
            if limite > 0 and self.model.corrente_atual > limite:
                texto_alerta = f"SOBRECARGA: Corrente {self.model.corrente_atual:.1f}A excedeu limite de {limite}A!"
                self.model.registrar_log("ALERTA CRÍTICO", texto_alerta)
                self.ui.chk_simulador.setChecked(False)
                self.acionar_emergencia()

        self.atualizar_indicadores()
        nova_potencia = self.model.calcular_potencia()
        
        self.tempo_x.append(self.tempo_atual)
        self.potencia_y.append(nova_potencia)
        self.linha.set_data(self.tempo_x, self.potencia_y)

        limite_esquerdo = max(0, self.tempo_atual - 60)
        limite_direito = max(60, self.tempo_atual)
        self.ax.set_xlim(limite_esquerdo, limite_direito)
        
        self.canvas.draw()

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

    # TELA 2
    def abrir_tela_configuracao(self):
        tela_config = ConfigController()
        
        if tela_config.exec() == QDialog.Accepted:
            nova_tensao = tela_config.limite_tensao
            nova_corrente = tela_config.limite_corrente
            
            self.model.setpoint_tensao = nova_tensao
            self.model.setpoint_corrente = nova_corrente
            
            texto_log = f"Setpoints atualizados: Tensão={nova_tensao}V | Corrente={nova_corrente}A"
            self.model.registrar_log("CONFIG", texto_log)

    # TELA 3
    def abrir_tela_serial(self):
        tela_serial = SerialPortController()
        tela_serial.enviar_log.connect(self.model.registrar_log)

        tela_serial.exec()

    # TELA 4
    def abrir_tela_historico(self):
        tela_logs = HistoricoController(self.model.lista_logs) 
        tela_logs.exec()

    