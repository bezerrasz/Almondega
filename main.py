import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from controller.dashboard_controller import DashboardController
from models.config_manager import ConfigManager
from database.connection import Database

def configurar_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=os.path.join("logs", "smartgrid.log"),
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8", 
        force=True
    )

def main():
    # 1. Configurações de infraestrutura (Logs, JSON e Banco SQLite)
    configurar_logging()
    ConfigManager()
    Database.init_db()

    # 2. Inicialização da Interface Gráfica
    app = QApplication(sys.argv)
    window = DashboardController()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()