# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'serialport.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpinBox, QWidget)

class Ui_SerialDialog(object):
    def setupUi(self, SerialDialog):
        if not SerialDialog.objectName():
            SerialDialog.setObjectName(u"SerialDialog")
        SerialDialog.resize(541, 342)
        SerialDialog.setStyleSheet(u"/* Fundo escuro */\n"
"QDialog {\n"
"    background-color: #2b2b2b;\n"
"}\n"
"\n"
"/* R\u00f3tulos de texto */\n"
"QLabel {\n"
"    color: #ffffff;\n"
"    font-size: 16px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"/* Caixas de sele\u00e7\u00e3o e n\u00famero */\n"
"QComboBox, QSpinBox {\n"
"    background-color: #1e1e1e;\n"
"    color: #ffffff;\n"
"    padding: 5px;\n"
"    border-radius: 4px;\n"
"}\n"
"\n"
"QComboBox:focus, QSpinBox:focus {\n"
"    background-color: #3a3a3a;\n"
"}\n"
"\n"
"/* Bot\u00f5es */\n"
"QPushButton {\n"
"    background-color: #008cba;\n"
"    color: white;\n"
"    border-radius: 6px;\n"
"    padding: 8px;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #005f73;\n"
"}\n"
"\n"
"QPushButton:disabled {\n"
"    background-color: #555555;\n"
"    color: #888888;\n"
"}")
        self.lbl_titulo = QLabel(SerialDialog)
        self.lbl_titulo.setObjectName(u"lbl_titulo")
        self.lbl_titulo.setGeometry(QRect(70, 20, 391, 41))
        font = QFont()
        font.setFamilies([u"Sitka"])
        font.setBold(True)
        self.lbl_titulo.setFont(font)
        self.lbl_titulo.setTextFormat(Qt.TextFormat.AutoText)
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setWordWrap(False)
        self.lbl_status = QLabel(SerialDialog)
        self.lbl_status.setObjectName(u"lbl_status")
        self.lbl_status.setGeometry(QRect(370, 140, 141, 71))
        self.lbl_status.setStyleSheet(u"QLabel {\n"
"    background-color: #ff0000;\n"
"    color: #ffffff;\n"
"    font-weight: bold;\n"
"    font-size: 13px;\n"
"    border-radius: 15px;\n"
"    padding: 8px 15px;\n"
"}")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layoutWidget = QWidget(SerialDialog)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(30, 100, 251, 141))
        self.gridLayout = QGridLayout(self.layoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.lbl_com = QLabel(self.layoutWidget)
        self.lbl_com.setObjectName(u"lbl_com")
        font1 = QFont()
        font1.setFamilies([u"Yu Gothic UI"])
        font1.setBold(True)
        self.lbl_com.setFont(font1)

        self.gridLayout.addWidget(self.lbl_com, 0, 0, 1, 1)

        self.combo_porta = QComboBox(self.layoutWidget)
        self.combo_porta.setObjectName(u"combo_porta")

        self.gridLayout.addWidget(self.combo_porta, 0, 1, 1, 1)

        self.lbl_baudrate = QLabel(self.layoutWidget)
        self.lbl_baudrate.setObjectName(u"lbl_baudrate")
        self.lbl_baudrate.setFont(font1)

        self.gridLayout.addWidget(self.lbl_baudrate, 1, 0, 1, 1)

        self.combo_br = QComboBox(self.layoutWidget)
        self.combo_br.setObjectName(u"combo_br")

        self.gridLayout.addWidget(self.combo_br, 1, 1, 1, 1)

        self.lbl_timeout = QLabel(self.layoutWidget)
        self.lbl_timeout.setObjectName(u"lbl_timeout")
        self.lbl_timeout.setFont(font1)

        self.gridLayout.addWidget(self.lbl_timeout, 2, 0, 1, 1)

        self.spin_timeout = QSpinBox(self.layoutWidget)
        self.spin_timeout.setObjectName(u"spin_timeout")
        self.spin_timeout.setMinimumSize(QSize(80, 0))
        self.spin_timeout.setStyleSheet(u"QSpinBox {\n"
"    padding-right: 20px; /* Cria uma margem de prote\u00e7\u00e3o para o texto n\u00e3o encostar nas setas */\n"
"}")
        self.spin_timeout.setMinimum(1)

        self.gridLayout.addWidget(self.spin_timeout, 2, 1, 1, 1)

        self.layoutWidget1 = QWidget(SerialDialog)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(100, 260, 341, 71))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_conectar = QPushButton(self.layoutWidget1)
        self.btn_conectar.setObjectName(u"btn_conectar")

        self.horizontalLayout.addWidget(self.btn_conectar)

        self.btn_desconectar = QPushButton(self.layoutWidget1)
        self.btn_desconectar.setObjectName(u"btn_desconectar")

        self.horizontalLayout.addWidget(self.btn_desconectar)


        self.retranslateUi(SerialDialog)

        QMetaObject.connectSlotsByName(SerialDialog)
    # setupUi

    def retranslateUi(self, SerialDialog):
        SerialDialog.setWindowTitle(QCoreApplication.translate("SerialDialog", u"Comunica\u00e7\u00e3o Serial", None))
        self.lbl_titulo.setText(QCoreApplication.translate("SerialDialog", u"Configura\u00e7\u00e3o de Comunica\u00e7\u00e3o Serial", None))
        self.lbl_status.setText(QCoreApplication.translate("SerialDialog", u"<html><head/><body><p><span style=\" font-weight:700;\">DESCONECTADO</span></p></body></html>", None))
        self.lbl_com.setText(QCoreApplication.translate("SerialDialog", u"Porta COM:", None))
        self.lbl_baudrate.setText(QCoreApplication.translate("SerialDialog", u"Baud Rate:", None))
        self.lbl_timeout.setText(QCoreApplication.translate("SerialDialog", u"Timeout (s):", None))
        self.btn_conectar.setText(QCoreApplication.translate("SerialDialog", u"CONECTAR", None))
        self.btn_desconectar.setText(QCoreApplication.translate("SerialDialog", u"DESCONECTAR", None))
    # retranslateUi

