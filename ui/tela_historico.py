# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tela_historico.ui'
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
from PySide6.QtWidgets import (QApplication, QDateEdit, QDialog, QHBoxLayout,
    QHeaderView, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(615, 300)
        Dialog.setStyleSheet(u"/* Fundo da janela */\n"
"QDialog {\n"
"    background-color: #2b2b2b;\n"
"}\n"
"\n"
"/* Estilo da Tabela */\n"
"QTableWidget {\n"
"    background-color: #1e1e1e;\n"
"    color: #ffffff;\n"
"    gridline-color: #444444; /* Cor da linha divis\u00f3ria */\n"
"    border: 1px solid #555555;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"/* Estilo do Cabe\u00e7alho da Tabela (Onde ficam os t\u00edtulos das colunas) */\n"
"QHeaderView::section {\n"
"    background-color: #333333;\n"
"    color: #ffffff;\n"
"    font-weight: bold;\n"
"    border: 1px solid #444444;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"/* Estilo do Bot\u00e3o Fechar */\n"
"QPushButton {\n"
"    background-color: #555555; \n"
"    color: white;\n"
"    border-radius: 5px;\n"
"    padding: 8px;\n"
"    font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #777777; \n"
"}")
        self.widget = QWidget(Dialog)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(9, 9, 601, 272))
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.data_filtro = QDateEdit(self.widget)
        self.data_filtro.setObjectName(u"data_filtro")
        self.data_filtro.setCalendarPopup(True)

        self.horizontalLayout.addWidget(self.data_filtro)

        self.btn_filtrar = QPushButton(self.widget)
        self.btn_filtrar.setObjectName(u"btn_filtrar")

        self.horizontalLayout.addWidget(self.btn_filtrar)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tabela_logs = QTableWidget(self.widget)
        self.tabela_logs.setObjectName(u"tabela_logs")
        self.tabela_logs.setStyleSheet(u"")

        self.verticalLayout.addWidget(self.tabela_logs)

        self.btn_fechar = QPushButton(self.widget)
        self.btn_fechar.setObjectName(u"btn_fechar")

        self.verticalLayout.addWidget(self.btn_fechar)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.btn_filtrar.setText(QCoreApplication.translate("Dialog", u"Filtrar", None))
        self.btn_fechar.setText(QCoreApplication.translate("Dialog", u"Fechar", None))
    # retranslateUi

