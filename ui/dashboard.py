# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFormLayout,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSlider, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(849, 449)
        self.layoutWidget = QWidget(Dialog)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 20, 295, 361))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setSpacing(15)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.layoutWidget)
        self.label_6.setObjectName(u"label_6")
        font = QFont()
        font.setFamilies([u"Rockwell Extra Bold"])
        font.setPointSize(28)
        font.setBold(True)
        self.label_6.setFont(font)
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label_6)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.lbl_tensao = QLabel(self.layoutWidget)
        self.lbl_tensao.setObjectName(u"lbl_tensao")
        font2 = QFont()
        font2.setPointSize(13)
        self.lbl_tensao.setFont(font2)
        self.lbl_tensao.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lbl_tensao)

        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")
        font3 = QFont()
        font3.setPointSize(11)
        font3.setBold(True)
        self.label_2.setFont(font3)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.lbl_corrente = QLabel(self.layoutWidget)
        self.lbl_corrente.setObjectName(u"lbl_corrente")
        self.lbl_corrente.setFont(font2)
        self.lbl_corrente.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lbl_corrente)

        self.label_3 = QLabel(self.layoutWidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font3)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.lbl_potencia = QLabel(self.layoutWidget)
        self.lbl_potencia.setObjectName(u"lbl_potencia")
        self.lbl_potencia.setFont(font2)
        self.lbl_potencia.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lbl_potencia)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.lbl_status_disjuntor = QLabel(self.layoutWidget)
        self.lbl_status_disjuntor.setObjectName(u"lbl_status_disjuntor")
        self.lbl_status_disjuntor.setStyleSheet(u"background-color: green;\n"
"color: white;\n"
"font-weight: bold;\n"
"font-size: 14px;\n"
"padding: 5px;\n"
"border-radius: 5px;")
        self.lbl_status_disjuntor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.lbl_status_disjuntor, 2, 1, 1, 1)

        self.label_5 = QLabel(self.layoutWidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font3)

        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)

        self.chk_simulador = QCheckBox(self.layoutWidget)
        self.chk_simulador.setObjectName(u"chk_simulador")
        font4 = QFont()
        font4.setBold(True)
        self.chk_simulador.setFont(font4)
        self.chk_simulador.setChecked(True)

        self.gridLayout.addWidget(self.chk_simulador, 9, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.label_4 = QLabel(self.layoutWidget)
        self.label_4.setObjectName(u"label_4")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setFont(font1)
        self.label_4.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_4, 0, 1, 1, 1)

        self.btn_emergencia = QPushButton(self.layoutWidget)
        self.btn_emergencia.setObjectName(u"btn_emergencia")
        self.btn_emergencia.setMinimumSize(QSize(60, 60))
        self.btn_emergencia.setMaximumSize(QSize(60, 60))
        self.btn_emergencia.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btn_emergencia.setStyleSheet(u"QPushButton {\n"
"    background-color: #e74c3c;\n"
"    color: white;\n"
"    font-weight: bold;\n"
"    font-size: 12px;\n"
"    border-radius: 30px; \n"
"    border: 4px solid #c0392b;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #c0392b;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #781f16;\n"
"    border: 4px solid #4a110a;\n"
"}")
        self.btn_emergencia.setAutoDefault(False)

        self.gridLayout.addWidget(self.btn_emergencia, 2, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.lbl_potencia_2 = QLabel(self.layoutWidget)
        self.lbl_potencia_2.setObjectName(u"lbl_potencia_2")
        self.lbl_potencia_2.setFont(font4)

        self.gridLayout.addWidget(self.lbl_potencia_2, 9, 0, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.slider_limite = QSlider(self.layoutWidget)
        self.slider_limite.setObjectName(u"slider_limite")
        self.slider_limite.setMinimum(1000)
        self.slider_limite.setMaximum(4000)
        self.slider_limite.setOrientation(Qt.Orientation.Horizontal)
        self.slider_limite.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_limite.setTickInterval(500)

        self.verticalLayout.addWidget(self.slider_limite)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_7 = QLabel(self.layoutWidget)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout.addWidget(self.label_7)

        self.label_8 = QLabel(self.layoutWidget)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label_8)

        self.label_9 = QLabel(self.layoutWidget)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.label_9)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.widget_grafico = QWidget(Dialog)
        self.widget_grafico.setObjectName(u"widget_grafico")
        self.widget_grafico.setGeometry(QRect(320, 20, 511, 411))
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.widget_grafico.sizePolicy().hasHeightForWidth())
        self.widget_grafico.setSizePolicy(sizePolicy1)
        self.widget = QWidget(Dialog)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(10, 400, 291, 28))
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.btn_tela_serial = QPushButton(self.widget)
        self.btn_tela_serial.setObjectName(u"btn_tela_serial")

        self.horizontalLayout_2.addWidget(self.btn_tela_serial, 0, Qt.AlignmentFlag.AlignLeft)

        self.btn_config_limites = QPushButton(self.widget)
        self.btn_config_limites.setObjectName(u"btn_config_limites")

        self.horizontalLayout_2.addWidget(self.btn_config_limites, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btn_tela_historico = QPushButton(self.widget)
        self.btn_tela_historico.setObjectName(u"btn_tela_historico")

        self.horizontalLayout_2.addWidget(self.btn_tela_historico, 0, Qt.AlignmentFlag.AlignRight)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"DASHBOARD", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.lbl_tensao.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Corrente (A):", None))
        self.lbl_corrente.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Pot\u00eancia (W):", None))
        self.lbl_potencia.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.lbl_status_disjuntor.setText(QCoreApplication.translate("Dialog", u"FECHADO", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Bot\u00e3o Emergencial", None))
        self.chk_simulador.setText(QCoreApplication.translate("Dialog", u"Alavanca Virtual", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Status", None))
        self.btn_emergencia.setText(QCoreApplication.translate("Dialog", u"PARAR", None))
        self.lbl_potencia_2.setText(QCoreApplication.translate("Dialog", u"Limite de Alerta", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"1000", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"2500", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"4000", None))
        self.btn_tela_serial.setText(QCoreApplication.translate("Dialog", u"Serial", None))
        self.btn_config_limites.setText(QCoreApplication.translate("Dialog", u"Limites", None))
        self.btn_tela_historico.setText(QCoreApplication.translate("Dialog", u"Hist\u00f3rico", None))
    # retranslateUi

