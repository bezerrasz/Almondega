# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tela_cadastro.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(330, 154)
        self.lbl_instrucao = QLabel(Dialog)
        self.lbl_instrucao.setObjectName(u"lbl_instrucao")
        self.lbl_instrucao.setGeometry(QRect(10, 10, 311, 20))
        self.txt_nome = QLineEdit(Dialog)
        self.txt_nome.setObjectName(u"txt_nome")
        self.txt_nome.setGeometry(QRect(10, 40, 301, 26))
        self.btn_ok = QPushButton(Dialog)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setGeometry(QRect(230, 120, 81, 26))
        self.cmb_categoria = QComboBox(Dialog)
        self.cmb_categoria.setObjectName(u"cmb_categoria")
        self.cmb_categoria.setGeometry(QRect(10, 80, 301, 26))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Formul\u00e1rio de Cadastro", None))
        self.lbl_instrucao.setText(QCoreApplication.translate("Dialog", u"Digite as informa\u00e7\u00f5es:", None))
        self.btn_ok.setText(QCoreApplication.translate("Dialog", u"OK", None))
    # retranslateUi

