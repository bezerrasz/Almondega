import sys
from PySide6.QtWidgets import QApplication
from controller.dashboard_controller import DashboardController
from models import config_manager
import os
import json


def main():
    app = QApplication(sys.argv)

    # Inicializa o gerenciador de configuração
    # e carrega as configurações do arquivo JSON no momento da inicialização do aplicativo. 
    cfg = config_manager.ConfigManager() 
    
    window = DashboardController()
    window.show()

  
    sys.exit(app.exec())

if __name__ == "__main__":
    main()