from PySide6.QtWidgets import QDialog
from ui.config_limites import Ui_Dialog
from models import config_manager
import json
import os

class ConfigController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("⚙️ Configurar Limites (Setpoints)")

        # Carregar os limites atuais do arquivo de configuração JSON
        cfg = config_manager.ConfigManager()
        self.limite_tensao = cfg.carregar().get("limite_tensao")
        self.limite_corrente = cfg.carregar().get("limite_corrente")

        self.ui.spin_limite_tensao.setValue(self.limite_tensao)
        self.ui.spin_limite_corrente.setValue(self.limite_corrente)
        
        
        self.ui.btn_salvar.clicked.connect(self.salvar_e_fechar)
        
    def salvar_e_fechar(self):

        self.limite_tensao = self.ui.spin_limite_tensao.value()
        self.limite_corrente = self.ui.spin_limite_corrente.value()
        
        self.accept() 