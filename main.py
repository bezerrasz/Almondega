import sys
import os
import logging
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from controller.dashboard_controller import DashboardController
from models.config_manager import ConfigManager

class FiltroNomeThread(logging.Filter):
    # A1/5: mostra no log em qual thread cada mensagem foi gerada (GUI, SerialThread, DatabaseThread)
    def filter(self, record):
        nome = QThread.currentThread().objectName()
        record.threadName = nome or ("GUI" if record.threadName == "MainThread" else record.threadName)
        return True

def configurar_logging():
    os.makedirs("logs", exist_ok=True)
    handlers = [logging.FileHandler(os.path.join("logs", "smartgrid.log"), encoding="utf-8"),
                logging.StreamHandler()]
    for h in handlers:
        h.addFilter(FiltroNomeThread())
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s %(threadName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True
    )

def main():
    # 1. Configurações de infraestrutura (Logs e JSON). O banco SQLite agora é aberto pela DatabaseThread.
    configurar_logging()
    ConfigManager()

    # 2. Inicialização da Interface Gráfica
    app = QApplication(sys.argv)
    window = DashboardController()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
