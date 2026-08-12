from PySide6.QtWidgets import QDialog
from ui.config_limites import Ui_Dialog

class ConfigController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        self.limite_tensao = 0
        self.limite_corrente = 0.0
        
        self.ui.btn_salvar.clicked.connect(self.salvar_e_fechar)
        
    def salvar_e_fechar(self):

        self.limite_tensao = self.ui.spin_limite_tensao.value()
        self.limite_corrente = self.ui.spin_limite_corrente.value()
        
        self.accept() 