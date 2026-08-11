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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QSlider, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(746, 340)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(20, 60, 61, 21))
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(20, 90, 71, 21))
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(20, 120, 71, 21))
        self.lbl_corrente = QLabel(Dialog)
        self.lbl_corrente.setObjectName(u"lbl_corrente")
        self.lbl_corrente.setGeometry(QRect(150, 90, 61, 21))
        self.lbl_potencia = QLabel(Dialog)
        self.lbl_potencia.setObjectName(u"lbl_potencia")
        self.lbl_potencia.setGeometry(QRect(150, 120, 61, 21))
        self.lbl_tensao = QLabel(Dialog)
        self.lbl_tensao.setObjectName(u"lbl_tensao")
        self.lbl_tensao.setGeometry(QRect(150, 60, 61, 21))
        self.lbl_status_disjuntor = QLabel(Dialog)
        self.lbl_status_disjuntor.setObjectName(u"lbl_status_disjuntor")
        self.lbl_status_disjuntor.setGeometry(QRect(140, 210, 81, 41))
        self.lbl_status_disjuntor.setStyleSheet(u"background-color: green;\n"
"color: white;\n"
"font-weight: bold;\n"
"font-size: 14px;\n"
"padding: 5px;\n"
"border-radius: 5px;")
        self.btn_emergencia = QPushButton(Dialog)
        self.btn_emergencia.setObjectName(u"btn_emergencia")
        self.btn_emergencia.setGeometry(QRect(20, 200, 60, 60))
        self.btn_emergencia.setMinimumSize(QSize(60, 60))
        self.btn_emergencia.setMaximumSize(QSize(60, 60))
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
        self.horizontalSlider = QSlider(Dialog)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setGeometry(QRect(10, 300, 221, 16))
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)
        self.widget_grafico = QWidget(Dialog)
        self.widget_grafico.setObjectName(u"widget_grafico")
        self.widget_grafico.setGeometry(QRect(270, 20, 451, 291))
        self.lbl_potencia_2 = QLabel(Dialog)
        self.lbl_potencia_2.setObjectName(u"lbl_potencia_2")
        self.lbl_potencia_2.setGeometry(QRect(20, 270, 91, 21))
        font = QFont()
        font.setBold(True)
        self.lbl_potencia_2.setFont(font)
        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 170, 101, 21))
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(160, 170, 31, 21))
        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(60, 20, 91, 21))
        font1 = QFont()
        font1.setFamilies([u"Rockwell Extra Bold"])
        font1.setBold(True)
        self.label_6.setFont(font1)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Corrente (A):", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Pot\u00eancia (W):", None))
        self.lbl_corrente.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.lbl_potencia.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.lbl_tensao.setText(QCoreApplication.translate("Dialog", u"Tens\u00e3o (V):", None))
        self.lbl_status_disjuntor.setText(QCoreApplication.translate("Dialog", u"FECHADO", None))
        self.btn_emergencia.setText(QCoreApplication.translate("Dialog", u"PARAR", None))
        self.lbl_potencia_2.setText(QCoreApplication.translate("Dialog", u"Limite de Alerta", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Bot\u00e3o Emergencial", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Status", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"DASHBOARD", None))
    # retranslateUi

