# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDateTimeEdit, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPlainTextEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QSpinBox, QStatusBar,
    QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1240, 780)
        self.central = QWidget(MainWindow)
        self.central.setObjectName(u"central")
        self.layout_principal = QHBoxLayout(self.central)
        self.layout_principal.setSpacing(12)
        self.layout_principal.setObjectName(u"layout_principal")
        self.painel_esquerdo = QWidget(self.central)
        self.painel_esquerdo.setObjectName(u"painel_esquerdo")
        self.painel_esquerdo.setMinimumSize(QSize(320, 0))
        self.painel_esquerdo.setMaximumSize(QSize(340, 16777215))
        self.layout_esquerdo = QVBoxLayout(self.painel_esquerdo)
        self.layout_esquerdo.setObjectName(u"layout_esquerdo")
        self.layout_esquerdo.setContentsMargins(0, 0, 0, 0)
        self.lbl_titulo = QLabel(self.painel_esquerdo)
        self.lbl_titulo.setObjectName(u"lbl_titulo")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_esquerdo.addWidget(self.lbl_titulo)

        self.grp_conexao = QGroupBox(self.painel_esquerdo)
        self.grp_conexao.setObjectName(u"grp_conexao")
        self.grid_conexao = QGridLayout(self.grp_conexao)
        self.grid_conexao.setObjectName(u"grid_conexao")
        self.lbl_porta = QLabel(self.grp_conexao)
        self.lbl_porta.setObjectName(u"lbl_porta")

        self.grid_conexao.addWidget(self.lbl_porta, 0, 0, 1, 1)

        self.combo_porta = QComboBox(self.grp_conexao)
        self.combo_porta.setObjectName(u"combo_porta")
        self.combo_porta.setEditable(True)

        self.grid_conexao.addWidget(self.combo_porta, 0, 1, 1, 1)

        self.btn_atualizar_portas = QToolButton(self.grp_conexao)
        self.btn_atualizar_portas.setObjectName(u"btn_atualizar_portas")

        self.grid_conexao.addWidget(self.btn_atualizar_portas, 0, 2, 1, 1)

        self.lbl_baud = QLabel(self.grp_conexao)
        self.lbl_baud.setObjectName(u"lbl_baud")

        self.grid_conexao.addWidget(self.lbl_baud, 1, 0, 1, 1)

        self.combo_baud = QComboBox(self.grp_conexao)
        self.combo_baud.setObjectName(u"combo_baud")

        self.grid_conexao.addWidget(self.combo_baud, 1, 1, 1, 2)

        self.lbl_periodo = QLabel(self.grp_conexao)
        self.lbl_periodo.setObjectName(u"lbl_periodo")

        self.grid_conexao.addWidget(self.lbl_periodo, 2, 0, 1, 1)

        self.spin_periodo = QSpinBox(self.grp_conexao)
        self.spin_periodo.setObjectName(u"spin_periodo")
        self.spin_periodo.setMinimum(200)
        self.spin_periodo.setMaximum(5000)
        self.spin_periodo.setSingleStep(100)
        self.spin_periodo.setValue(1000)

        self.grid_conexao.addWidget(self.spin_periodo, 2, 1, 1, 2)

        self.layout_botoes_conexao = QHBoxLayout()
        self.layout_botoes_conexao.setObjectName(u"layout_botoes_conexao")
        self.btn_conectar = QPushButton(self.grp_conexao)
        self.btn_conectar.setObjectName(u"btn_conectar")

        self.layout_botoes_conexao.addWidget(self.btn_conectar)

        self.btn_desconectar = QPushButton(self.grp_conexao)
        self.btn_desconectar.setObjectName(u"btn_desconectar")

        self.layout_botoes_conexao.addWidget(self.btn_desconectar)


        self.grid_conexao.addLayout(self.layout_botoes_conexao, 3, 0, 1, 3)

        self.lbl_status_conexao = QLabel(self.grp_conexao)
        self.lbl_status_conexao.setObjectName(u"lbl_status_conexao")
        self.lbl_status_conexao.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.grid_conexao.addWidget(self.lbl_status_conexao, 4, 0, 1, 3)

        self.lbl_detalhe_conexao = QLabel(self.grp_conexao)
        self.lbl_detalhe_conexao.setObjectName(u"lbl_detalhe_conexao")
        self.lbl_detalhe_conexao.setWordWrap(True)

        self.grid_conexao.addWidget(self.lbl_detalhe_conexao, 5, 0, 1, 3)

        self.lbl_estatisticas = QLabel(self.grp_conexao)
        self.lbl_estatisticas.setObjectName(u"lbl_estatisticas")

        self.grid_conexao.addWidget(self.lbl_estatisticas, 6, 0, 1, 3)


        self.layout_esquerdo.addWidget(self.grp_conexao)

        self.grp_medicoes = QGroupBox(self.painel_esquerdo)
        self.grp_medicoes.setObjectName(u"grp_medicoes")
        self.form_medicoes = QFormLayout(self.grp_medicoes)
        self.form_medicoes.setObjectName(u"form_medicoes")
        self.lbl_t_tensao = QLabel(self.grp_medicoes)
        self.lbl_t_tensao.setObjectName(u"lbl_t_tensao")

        self.form_medicoes.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_t_tensao)

        self.lbl_tensao = QLabel(self.grp_medicoes)
        self.lbl_tensao.setObjectName(u"lbl_tensao")

        self.form_medicoes.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lbl_tensao)

        self.lbl_t_corrente = QLabel(self.grp_medicoes)
        self.lbl_t_corrente.setObjectName(u"lbl_t_corrente")

        self.form_medicoes.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_t_corrente)

        self.lbl_corrente = QLabel(self.grp_medicoes)
        self.lbl_corrente.setObjectName(u"lbl_corrente")

        self.form_medicoes.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lbl_corrente)

        self.lbl_t_potencia = QLabel(self.grp_medicoes)
        self.lbl_t_potencia.setObjectName(u"lbl_t_potencia")

        self.form_medicoes.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lbl_t_potencia)

        self.lbl_potencia = QLabel(self.grp_medicoes)
        self.lbl_potencia.setObjectName(u"lbl_potencia")

        self.form_medicoes.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lbl_potencia)


        self.layout_esquerdo.addWidget(self.grp_medicoes)

        self.grp_disjuntor = QGroupBox(self.painel_esquerdo)
        self.grp_disjuntor.setObjectName(u"grp_disjuntor")
        self.layout_disjuntor = QVBoxLayout(self.grp_disjuntor)
        self.layout_disjuntor.setObjectName(u"layout_disjuntor")
        self.lbl_status_disjuntor = QLabel(self.grp_disjuntor)
        self.lbl_status_disjuntor.setObjectName(u"lbl_status_disjuntor")
        self.lbl_status_disjuntor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_disjuntor.addWidget(self.lbl_status_disjuntor)

        self.layout_botoes_dj = QHBoxLayout()
        self.layout_botoes_dj.setObjectName(u"layout_botoes_dj")
        self.btn_fechar_dj = QPushButton(self.grp_disjuntor)
        self.btn_fechar_dj.setObjectName(u"btn_fechar_dj")

        self.layout_botoes_dj.addWidget(self.btn_fechar_dj)

        self.btn_abrir_dj = QPushButton(self.grp_disjuntor)
        self.btn_abrir_dj.setObjectName(u"btn_abrir_dj")

        self.layout_botoes_dj.addWidget(self.btn_abrir_dj)


        self.layout_disjuntor.addLayout(self.layout_botoes_dj)

        self.btn_emergencia = QPushButton(self.grp_disjuntor)
        self.btn_emergencia.setObjectName(u"btn_emergencia")

        self.layout_disjuntor.addWidget(self.btn_emergencia)


        self.layout_esquerdo.addWidget(self.grp_disjuntor)

        self.layout_telas = QHBoxLayout()
        self.layout_telas.setObjectName(u"layout_telas")
        self.btn_config_limites = QPushButton(self.painel_esquerdo)
        self.btn_config_limites.setObjectName(u"btn_config_limites")

        self.layout_telas.addWidget(self.btn_config_limites)

        self.btn_eventos = QPushButton(self.painel_esquerdo)
        self.btn_eventos.setObjectName(u"btn_eventos")

        self.layout_telas.addWidget(self.btn_eventos)


        self.layout_esquerdo.addLayout(self.layout_telas)

        self.espaco_esquerdo = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_esquerdo.addItem(self.espaco_esquerdo)


        self.layout_principal.addWidget(self.painel_esquerdo)

        self.layout_direito = QVBoxLayout()
        self.layout_direito.setObjectName(u"layout_direito")
        self.layout_modo = QHBoxLayout()
        self.layout_modo.setObjectName(u"layout_modo")
        self.lbl_modo = QLabel(self.central)
        self.lbl_modo.setObjectName(u"lbl_modo")

        self.layout_modo.addWidget(self.lbl_modo)

        self.radio_tempo_real = QRadioButton(self.central)
        self.radio_tempo_real.setObjectName(u"radio_tempo_real")
        self.radio_tempo_real.setChecked(True)

        self.layout_modo.addWidget(self.radio_tempo_real)

        self.radio_historico = QRadioButton(self.central)
        self.radio_historico.setObjectName(u"radio_historico")

        self.layout_modo.addWidget(self.radio_historico)

        self.espaco_modo = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_modo.addItem(self.espaco_modo)

        self.lbl_grandeza = QLabel(self.central)
        self.lbl_grandeza.setObjectName(u"lbl_grandeza")

        self.layout_modo.addWidget(self.lbl_grandeza)

        self.combo_grandeza = QComboBox(self.central)
        self.combo_grandeza.setObjectName(u"combo_grandeza")

        self.layout_modo.addWidget(self.combo_grandeza)


        self.layout_direito.addLayout(self.layout_modo)

        self.grp_filtro = QGroupBox(self.central)
        self.grp_filtro.setObjectName(u"grp_filtro")
        self.layout_filtro = QHBoxLayout(self.grp_filtro)
        self.layout_filtro.setObjectName(u"layout_filtro")
        self.radio_ultimas = QRadioButton(self.grp_filtro)
        self.radio_ultimas.setObjectName(u"radio_ultimas")
        self.radio_ultimas.setChecked(True)

        self.layout_filtro.addWidget(self.radio_ultimas)

        self.spin_ultimas = QSpinBox(self.grp_filtro)
        self.spin_ultimas.setObjectName(u"spin_ultimas")
        self.spin_ultimas.setMinimum(1)
        self.spin_ultimas.setMaximum(1000000)
        self.spin_ultimas.setValue(500)

        self.layout_filtro.addWidget(self.spin_ultimas)

        self.radio_intervalo = QRadioButton(self.grp_filtro)
        self.radio_intervalo.setObjectName(u"radio_intervalo")

        self.layout_filtro.addWidget(self.radio_intervalo)

        self.dt_inicio = QDateTimeEdit(self.grp_filtro)
        self.dt_inicio.setObjectName(u"dt_inicio")
        self.dt_inicio.setCalendarPopup(True)

        self.layout_filtro.addWidget(self.dt_inicio)

        self.lbl_ate = QLabel(self.grp_filtro)
        self.lbl_ate.setObjectName(u"lbl_ate")

        self.layout_filtro.addWidget(self.lbl_ate)

        self.dt_fim = QDateTimeEdit(self.grp_filtro)
        self.dt_fim.setObjectName(u"dt_fim")
        self.dt_fim.setCalendarPopup(True)

        self.layout_filtro.addWidget(self.dt_fim)

        self.btn_consultar = QPushButton(self.grp_filtro)
        self.btn_consultar.setObjectName(u"btn_consultar")

        self.layout_filtro.addWidget(self.btn_consultar)


        self.layout_direito.addWidget(self.grp_filtro)

        self.widget_grafico = QWidget(self.central)
        self.widget_grafico.setObjectName(u"widget_grafico")
        self.widget_grafico.setMinimumSize(QSize(500, 320))

        self.layout_direito.addWidget(self.widget_grafico)

        self.txt_console = QPlainTextEdit(self.central)
        self.txt_console.setObjectName(u"txt_console")
        self.txt_console.setMaximumSize(QSize(16777215, 170))
        self.txt_console.setReadOnly(True)

        self.layout_direito.addWidget(self.txt_console)

        self.layout_direito.setStretch(2, 1)

        self.layout_principal.addLayout(self.layout_direito)

        self.layout_principal.setStretch(1, 1)
        MainWindow.setCentralWidget(self.central)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Smart Grid - Supervis\u00f3rio", None))
        self.lbl_titulo.setObjectName(QCoreApplication.translate("MainWindow", u"lbl_titulo", None))
        self.lbl_titulo.setText(QCoreApplication.translate("MainWindow", u"\u26a1 SMART GRID", None))
        self.grp_conexao.setTitle(QCoreApplication.translate("MainWindow", u"Conex\u00e3o serial", None))
        self.lbl_porta.setText(QCoreApplication.translate("MainWindow", u"Porta", None))
#if QT_CONFIG(tooltip)
        self.btn_atualizar_portas.setToolTip(QCoreApplication.translate("MainWindow", u"Atualizar lista de portas", None))
#endif // QT_CONFIG(tooltip)
        self.btn_atualizar_portas.setText(QCoreApplication.translate("MainWindow", u"\u27f3", None))
        self.lbl_baud.setText(QCoreApplication.translate("MainWindow", u"Velocidade alvo", None))
        self.lbl_periodo.setText(QCoreApplication.translate("MainWindow", u"Amostragem", None))
        self.spin_periodo.setSuffix(QCoreApplication.translate("MainWindow", u" ms", None))
        self.btn_conectar.setText(QCoreApplication.translate("MainWindow", u"Conectar", None))
        self.btn_desconectar.setText(QCoreApplication.translate("MainWindow", u"Desconectar", None))
        self.lbl_status_conexao.setText(QCoreApplication.translate("MainWindow", u"DESCONECTADO", None))
        self.lbl_detalhe_conexao.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.lbl_estatisticas.setText(QCoreApplication.translate("MainWindow", u"Pacotes: 0 ok \u00b7 0 inv\u00e1lidos \u00b7 0 perdidos", None))
        self.grp_medicoes.setTitle(QCoreApplication.translate("MainWindow", u"Medi\u00e7\u00f5es", None))
        self.lbl_t_tensao.setText(QCoreApplication.translate("MainWindow", u"Tens\u00e3o", None))
        self.lbl_tensao.setText(QCoreApplication.translate("MainWindow", u"--- V", None))
        self.lbl_t_corrente.setText(QCoreApplication.translate("MainWindow", u"Corrente", None))
        self.lbl_corrente.setText(QCoreApplication.translate("MainWindow", u"--- A", None))
        self.lbl_t_potencia.setText(QCoreApplication.translate("MainWindow", u"Pot\u00eancia ativa", None))
        self.lbl_potencia.setText(QCoreApplication.translate("MainWindow", u"--- W", None))
        self.grp_disjuntor.setTitle(QCoreApplication.translate("MainWindow", u"Disjuntor DJ-PRINCIPAL", None))
        self.lbl_status_disjuntor.setText(QCoreApplication.translate("MainWindow", u"DESCONHECIDO", None))
        self.btn_fechar_dj.setText(QCoreApplication.translate("MainWindow", u"Fechar (ligar)", None))
        self.btn_abrir_dj.setText(QCoreApplication.translate("MainWindow", u"Abrir (desligar)", None))
        self.btn_emergencia.setText(QCoreApplication.translate("MainWindow", u"\u26d4 CORTE EMERGENCIAL", None))
        self.btn_config_limites.setText(QCoreApplication.translate("MainWindow", u"\u2699 Limites", None))
        self.btn_eventos.setText(QCoreApplication.translate("MainWindow", u"\U0001f4cb Eventos", None))
        self.lbl_modo.setText(QCoreApplication.translate("MainWindow", u"Modo do gr\u00e1fico:", None))
        self.radio_tempo_real.setText(QCoreApplication.translate("MainWindow", u"Tempo real", None))
        self.radio_historico.setText(QCoreApplication.translate("MainWindow", u"Consulta de hist\u00f3rico", None))
        self.lbl_grandeza.setText(QCoreApplication.translate("MainWindow", u"Grandeza:", None))
        self.grp_filtro.setTitle(QCoreApplication.translate("MainWindow", u"Filtro do hist\u00f3rico (SQLite)", None))
        self.radio_ultimas.setText(QCoreApplication.translate("MainWindow", u"\u00daltimas", None))
        self.spin_ultimas.setSuffix(QCoreApplication.translate("MainWindow", u" leituras", None))
        self.radio_intervalo.setText(QCoreApplication.translate("MainWindow", u"De", None))
        self.dt_inicio.setDisplayFormat(QCoreApplication.translate("MainWindow", u"dd/MM/yyyy HH:mm:ss", None))
        self.lbl_ate.setText(QCoreApplication.translate("MainWindow", u"at\u00e9", None))
        self.dt_fim.setDisplayFormat(QCoreApplication.translate("MainWindow", u"dd/MM/yyyy HH:mm:ss", None))
        self.btn_consultar.setText(QCoreApplication.translate("MainWindow", u"Consultar", None))
        self.txt_console.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Console de protocolo e eventos", None))
    # retranslateUi

