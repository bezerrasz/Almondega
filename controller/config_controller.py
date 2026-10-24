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
        self.cfg = config_manager.ConfigManager()
        self.limite_tensao = self.cfg.carregar().get("limite_tensao")
        self.limite_corrente = self.cfg.carregar().get("limite_corrente")

        self.ui.spin_limite_tensao.setValue(self.limite_tensao)
        self.ui.spin_limite_corrente.setValue(self.limite_corrente)

        
        self.ui.btn_salvar.clicked.connect(self.salvar_e_fechar)
        
    def salvar_e_fechar(self):
    # Salvar os limites atualizados no arquivo de configuração JSON
        dados = self.cfg.carregar()

        dados["limite_tensao"] = self.ui.spin_limite_tensao.value()
        dados["limite_corrente"] = self.ui.spin_limite_corrente.value()
        self.cfg.salvar(dados)

        self.accept() 