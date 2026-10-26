from PySide6.QtWidgets import QDialog
from ui.config_limites import Ui_Dialog
from PySide6.QtWidgets import QMessageBox
from models import config_manager
from database.connection import Database
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
        str_tensao = self.ui.spin_limite_tensao.text().replace(',', '.')
        str_corrente = self.ui.spin_limite_corrente.text().replace(',', '.')

        # str_tensao = "abc" # TESTE DE BLOQUEIO PARA CARACTERES NÃO NUMÉRICOS
        
        # VALIDAÇÃO A: Campo Vazio
        if not str_tensao.strip() or not str_corrente.strip():
            QMessageBox.warning(self, "Erro de Validação", "Nenhum dos limites pode ficar vazio!")
            return
            
        try:
            val_tensao = float(str_tensao)
            val_corrente = float(str_corrente)
            
            # VALIDAÇÃO B: Números negativos ou Zero
            if val_tensao <= 0 or val_corrente <= 0:
                QMessageBox.warning(self, "Erro de Validação", "Os limites devem ser valores maiores que zero!")
                return
                
            dados = self.cfg.carregar()
            dados["limite_tensao"] = val_tensao
            dados["limite_corrente"] = val_corrente
            self.cfg.salvar(dados) 
        
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO regras_limites (id, limite_corrente, tensao_desarme) 
                    VALUES (1, ?, ?)
                """, (val_corrente, val_tensao))
                conn.commit() 
            self.accept()
            
        except ValueError:
            # VALIDAÇÃO C: Usuário tentou colocar letras em campos matemáticos
            QMessageBox.warning(self, "Erro de Validação", "Por favor, insira apenas caracteres numéricos válidos!")