# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'config_limites.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QDoubleSpinBox, QLabel,
    QPushButton, QSizePolicy, QSpinBox, QSplitter,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)
        Dialog.setStyleSheet(u"/* Pinta o fundo da janela de cinza escuro */\n"
"QDialog {\n"
"    background-color: #2b2b2b;\n"
"}\n"
"\n"
"/* Pinta todos os textos de branco e deixa em negrito */\n"
"QLabel {\n"
"    color: #ffffff;\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"/* Estiliza as caixinhas preservando as setinhas nativas (Sem bordas e sem padding!) */\n"
"QSpinBox, QDoubleSpinBox {\n"
"    background-color: #1e1e1e;\n"
"    color: #ffffff;\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"/* Quando voc\u00ea clica na caixinha para digitar (Foco), clareia o fundo em vez de criar borda */\n"
"QSpinBox:focus, QDoubleSpinBox:focus {\n"
"    background-color: #3a3a3a; \n"
"}\n"
"\n"
"/* Estiliza o bot\u00e3o de Salvar */\n"
"QPushButton {\n"
"    background-color: #00aa00; \n"
"    color: white;\n"
"    border-radius: 8px;\n"
"    padding: 10px;\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"/* Quando passa o mouse por cima do bot\u00e3o, ele fica com um verde mais claro */\n"
"QPushButton:hover {\n"
""
                        "    background-color: #00cc00; \n"
"}")
        self.btn_salvar = QPushButton(Dialog)
        self.btn_salvar.setObjectName(u"btn_salvar")
        self.btn_salvar.setGeometry(QRect(130, 250, 121, 31))
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(90, 30, 221, 16))
        font = QFont()
        font.setFamilies([u"Gill Sans"])
        font.setBold(True)
        self.label_3.setFont(font)
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setGeometry(QRect(90, 160, 212, 58))
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.label_2 = QLabel(self.splitter)
        self.label_2.setObjectName(u"label_2")
        self.splitter.addWidget(self.label_2)
        self.spin_limite_corrente = QDoubleSpinBox(self.splitter)
        self.spin_limite_corrente.setObjectName(u"spin_limite_corrente")
        self.spin_limite_corrente.setMaximum(100.000000000000000)
        self.splitter.addWidget(self.spin_limite_corrente)
        self.splitter_2 = QSplitter(Dialog)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setGeometry(QRect(100, 80, 198, 58))
        self.splitter_2.setOrientation(Qt.Orientation.Vertical)
        self.label = QLabel(self.splitter_2)
        self.label.setObjectName(u"label")
        self.splitter_2.addWidget(self.label)
        self.spin_limite_tensao = QSpinBox(self.splitter_2)
        self.spin_limite_tensao.setObjectName(u"spin_limite_tensao")
        self.spin_limite_tensao.setMaximum(500)
        self.splitter_2.addWidget(self.spin_limite_tensao)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.btn_salvar.setText(QCoreApplication.translate("Dialog", u"Salvar e Fechar", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Configura\u00e7\u00e3o de Limites", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Limite M\u00e1ximo de Corrente (A):", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Limite M\u00e1ximo de Tens\u00e3o (V):", None))
    # retranslateUi

