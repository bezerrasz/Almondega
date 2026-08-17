from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtCore import Signal 
from ui.serialport import Ui_SerialDialog

class SerialPortController(QDialog):
    
    enviar_log = Signal(str, str) 

    def __init__(self):
        super().__init__()
        self.ui = Ui_SerialDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("🔌 Conexão Serial")

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
        
        porta = self.ui.combo_porta.currentText()
        baud = self.ui.combo_br.currentText()
        
        self.enviar_log.emit("SERIAL", f"Conectado com sucesso à {porta} (Baud: {baud})")
        
        QMessageBox.information(self, "Dispositivo Conectado", f"{porta} conectado com sucesso!")
        

    def desconectar(self):
        self.ui.combo_porta.setEnabled(True)
        self.ui.combo_br.setEnabled(True)   
        self.ui.lbl_status.setText("Desconectado")
        self.ui.lbl_status.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        
        porta = self.ui.combo_porta.currentText()
        
        self.enviar_log.emit("SERIAL", f"Conexão encerrada com a {porta}")
        
        QMessageBox.information(self, "Dispositivo Desconectado", f"{porta} desconectado com sucesso!")