from PySide6.QtWidgets import QDialog, QMessageBox
from ui.serialport import Ui_SerialDialog
from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QVBoxLayout


class SerialPortController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_SerialDialog()
        self.ui.setupUi(self)

        self.ui.combo_porta.addItems(["COM1", "COM2", "COM3", "COM4"])
        self.ui.combo_br.addItems(["9600", "19200", "38400", "57600", "115200"])

        self.ui.btn_conectar.clicked.connect(self.conectar)
        self.ui.btn_desconectar.clicked.connect(self.desconectar)

    def conectar(self):
        self.ui.combo_porta.setEnabled(False)
        self.ui.combo_br.setEnabled(False)
        self.ui.lbl_status.setText("Conectado")
        self.ui.lbl_status.setStyleSheet(
            "background-color: green; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        QMessageBox.information(self, "Dispositivo Conectado", "{} conectado com sucesso!".format(self.ui.combo_porta.currentText()))
        

    def desconectar(self):
        self.ui.combo_porta.setEnabled(True)
        self.ui.combo_br.setEnabled(True)   
        self.ui.lbl_status.setText("Desconectado")
        self.ui.lbl_status.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        QMessageBox.information(self, "Dispositivo Desconectado", "{} desconectado com sucesso!".format(self.ui.combo_porta.currentText()))

        

        