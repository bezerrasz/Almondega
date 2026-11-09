# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tela_historico.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDateTimeEdit,
    QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_DialogEventos(object):
    def setupUi(self, DialogEventos):
        if not DialogEventos.objectName():
            DialogEventos.setObjectName(u"DialogEventos")
        DialogEventos.resize(860, 460)
        self.layout = QVBoxLayout(DialogEventos)
        self.layout.setObjectName(u"layout")
        self.layout_filtro = QHBoxLayout()
        self.layout_filtro.setObjectName(u"layout_filtro")
        self.lbl_de = QLabel(DialogEventos)
        self.lbl_de.setObjectName(u"lbl_de")

        self.layout_filtro.addWidget(self.lbl_de)

        self.dt_inicio = QDateTimeEdit(DialogEventos)
        self.dt_inicio.setObjectName(u"dt_inicio")
        self.dt_inicio.setCalendarPopup(True)

        self.layout_filtro.addWidget(self.dt_inicio)

        self.lbl_ate = QLabel(DialogEventos)
        self.lbl_ate.setObjectName(u"lbl_ate")

        self.layout_filtro.addWidget(self.lbl_ate)

        self.dt_fim = QDateTimeEdit(DialogEventos)
        self.dt_fim.setObjectName(u"dt_fim")
        self.dt_fim.setCalendarPopup(True)

        self.layout_filtro.addWidget(self.dt_fim)

        self.btn_filtrar = QPushButton(DialogEventos)
        self.btn_filtrar.setObjectName(u"btn_filtrar")

        self.layout_filtro.addWidget(self.btn_filtrar)

        self.espaco = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout_filtro.addItem(self.espaco)

        self.lbl_total = QLabel(DialogEventos)
        self.lbl_total.setObjectName(u"lbl_total")

        self.layout_filtro.addWidget(self.lbl_total)


        self.layout.addLayout(self.layout_filtro)

        self.tabela_eventos = QTableWidget(DialogEventos)
        self.tabela_eventos.setObjectName(u"tabela_eventos")
        self.tabela_eventos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_eventos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_eventos.setAlternatingRowColors(True)

        self.layout.addWidget(self.tabela_eventos)

        self.botoes = QDialogButtonBox(DialogEventos)
        self.botoes.setObjectName(u"botoes")
        self.botoes.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.layout.addWidget(self.botoes)


        self.retranslateUi(DialogEventos)

        QMetaObject.connectSlotsByName(DialogEventos)
    # setupUi

    def retranslateUi(self, DialogEventos):
        DialogEventos.setWindowTitle(QCoreApplication.translate("DialogEventos", u"\U0001f4cb Hist\U000000f3rico de eventos", None))
        self.lbl_de.setText(QCoreApplication.translate("DialogEventos", u"De", None))
        self.dt_inicio.setDisplayFormat(QCoreApplication.translate("DialogEventos", u"dd/MM/yyyy HH:mm", None))
        self.lbl_ate.setText(QCoreApplication.translate("DialogEventos", u"at\u00e9", None))
        self.dt_fim.setDisplayFormat(QCoreApplication.translate("DialogEventos", u"dd/MM/yyyy HH:mm", None))
        self.btn_filtrar.setText(QCoreApplication.translate("DialogEventos", u"Filtrar", None))
        self.lbl_total.setText("")
    # retranslateUi

