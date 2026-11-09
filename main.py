"""Ponto de entrada: infraestrutura (log + config) e montagem View/Controller."""
import logging
import sys
import threading

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from controllers.app_controller import AppController
from models.caminhos import LOG_DIR
from models.config_manager import ConfigManager
from views.dashboard_view import DashboardView
from views.estilo import QSS


class FiltroNomeThread(logging.Filter):
    """Mostra no log o nome da QThread (GUI, SerialThread, DatabaseThread)."""
    def filter(self, record):
        nome = QThread.currentThread().objectName()
        record.threadName = nome or ("GUI" if record.threadName == "MainThread" else record.threadName)
        return True


def configurar_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [logging.FileHandler(LOG_DIR / "smartgrid.log", encoding="utf-8"), logging.StreamHandler()]
    for h in handlers:
        h.addFilter(FiltroNomeThread())
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s %(threadName)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def registrar_excecoes_nao_tratadas():
    def handler(tipo, valor, tb):
        logging.critical("exceção não tratada", exc_info=(tipo, valor, tb))
    sys.excepthook = handler
    threading.excepthook = lambda args: handler(args.exc_type, args.exc_value, args.exc_traceback)


def main():
    configurar_logging()
    registrar_excecoes_nao_tratadas()

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)

    config = ConfigManager()          # recria data/config.json se não existir
    view = DashboardView()
    controller = AppController(view, config)  # noqa: F841 (mantém a referência viva)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
