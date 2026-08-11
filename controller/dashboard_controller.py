from PySide6.QtWidgets import QDialog, QMessageBox
from ui.dashboard import Ui_Dialog

class DashboardController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.lbl_tensao.setText("220 V")
        self.ui.lbl_corrente.setText("10.5 A")
        self.ui.lbl_potencia.setText("2310 W")

        self.ui.btn_emergencia.clicked.connect(self.acionar_emergencia)

    def acionar_emergencia(self):
        self.ui.lbl_status_disjuntor.setText("ABERTO")
        self.ui.lbl_status_disjuntor.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        QMessageBox.warning(self, "Alerta", "Corte emergencial acionado!")