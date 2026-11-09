# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'config_limites.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogLimites(object):
    def setupUi(self, DialogLimites):
        if not DialogLimites.objectName():
            DialogLimites.setObjectName(u"DialogLimites")
        DialogLimites.resize(420, 300)
        self.layout = QVBoxLayout(DialogLimites)
        self.layout.setObjectName(u"layout")
        self.grp_limites = QGroupBox(DialogLimites)
        self.grp_limites.setObjectName(u"grp_limites")
        self.form_limites = QFormLayout(self.grp_limites)
        self.form_limites.setObjectName(u"form_limites")
        self.lbl_vmax = QLabel(self.grp_limites)
        self.lbl_vmax.setObjectName(u"lbl_vmax")

        self.form_limites.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_vmax)

        self.spin_tensao_max = QDoubleSpinBox(self.grp_limites)
        self.spin_tensao_max.setObjectName(u"spin_tensao_max")
        self.spin_tensao_max.setDecimals(1)
        self.spin_tensao_max.setMinimum(1.000000000000000)
        self.spin_tensao_max.setMaximum(1000.000000000000000)

        self.form_limites.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spin_tensao_max)

        self.lbl_vmin = QLabel(self.grp_limites)
        self.lbl_vmin.setObjectName(u"lbl_vmin")

        self.form_limites.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_vmin)

        self.spin_tensao_min = QDoubleSpinBox(self.grp_limites)
        self.spin_tensao_min.setObjectName(u"spin_tensao_min")
        self.spin_tensao_min.setDecimals(1)
        self.spin_tensao_min.setMaximum(1000.000000000000000)

        self.form_limites.setWidget(1, QFormLayout.ItemRole.FieldRole, self.spin_tensao_min)

        self.lbl_imax = QLabel(self.grp_limites)
        self.lbl_imax.setObjectName(u"lbl_imax")

        self.form_limites.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lbl_imax)

        self.spin_corrente_max = QDoubleSpinBox(self.grp_limites)
        self.spin_corrente_max.setObjectName(u"spin_corrente_max")
        self.spin_corrente_max.setDecimals(2)
        self.spin_corrente_max.setMinimum(0.100000000000000)
        self.spin_corrente_max.setMaximum(500.000000000000000)

        self.form_limites.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spin_corrente_max)


        self.layout.addWidget(self.grp_limites)

        self.grp_outros = QGroupBox(DialogLimites)
        self.grp_outros.setObjectName(u"grp_outros")
        self.form_outros = QFormLayout(self.grp_outros)
        self.form_outros.setObjectName(u"form_outros")
        self.lbl_fp = QLabel(self.grp_outros)
        self.lbl_fp.setObjectName(u"lbl_fp")

        self.form_outros.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_fp)

        self.spin_fator_potencia = QDoubleSpinBox(self.grp_outros)
        self.spin_fator_potencia.setObjectName(u"spin_fator_potencia")
        self.spin_fator_potencia.setDecimals(2)
        self.spin_fator_potencia.setMaximum(1.000000000000000)
        self.spin_fator_potencia.setSingleStep(0.010000000000000)

        self.form_outros.setWidget(0, QFormLayout.ItemRole.FieldRole, self.spin_fator_potencia)

        self.chk_reconexao = QCheckBox(self.grp_outros)
        self.chk_reconexao.setObjectName(u"chk_reconexao")

        self.form_outros.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.chk_reconexao)


        self.layout.addWidget(self.grp_outros)

        self.botoes = QDialogButtonBox(DialogLimites)
        self.botoes.setObjectName(u"botoes")
        self.botoes.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.layout.addWidget(self.botoes)


        self.retranslateUi(DialogLimites)

        QMetaObject.connectSlotsByName(DialogLimites)
    # setupUi

    def retranslateUi(self, DialogLimites):
        DialogLimites.setWindowTitle(QCoreApplication.translate("DialogLimites", u"\u2699 Limites e par\u00e2metros", None))
        self.grp_limites.setTitle(QCoreApplication.translate("DialogLimites", u"Prote\u00e7\u00e3o (setpoints)", None))
        self.lbl_vmax.setText(QCoreApplication.translate("DialogLimites", u"Tens\u00e3o m\u00e1xima (corte)", None))
        self.spin_tensao_max.setSuffix(QCoreApplication.translate("DialogLimites", u" V", None))
        self.lbl_vmin.setText(QCoreApplication.translate("DialogLimites", u"Tens\u00e3o m\u00ednima (alerta)", None))
        self.spin_tensao_min.setSuffix(QCoreApplication.translate("DialogLimites", u" V", None))
        self.lbl_imax.setText(QCoreApplication.translate("DialogLimites", u"Corrente m\u00e1xima (corte)", None))
        self.spin_corrente_max.setSuffix(QCoreApplication.translate("DialogLimites", u" A", None))
        self.grp_outros.setTitle(QCoreApplication.translate("DialogLimites", u"Outros", None))
        self.lbl_fp.setText(QCoreApplication.translate("DialogLimites", u"Fator de pot\u00eancia", None))
        self.chk_reconexao.setText(QCoreApplication.translate("DialogLimites", u"Reconectar automaticamente se o link cair", None))
    # retranslateUi

