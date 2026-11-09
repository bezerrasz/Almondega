"""Mediação do diálogo de limites: View <-> ConfigManager (Model)."""
from PySide6.QtCore import QObject, Signal

from models.config_manager import ConfigManager
from views.limites_view import LimitesView


class LimitesController(QObject):
    limites_alterados = Signal(dict)

    def __init__(self, config: ConfigManager, parent_view):
        super().__init__()
        self.config = config
        self.view = LimitesView(parent_view)
        self.view.preencher(self.config.carregar())
        self.view.salvar_solicitado.connect(self._salvar)

    def executar(self):
        self.view.exec()

    def _salvar(self, valores: dict):
        try:
            novo = self.config.salvar(valores)     # a validação é do Model
        except ValueError as e:
            self.view.mostrar_erro(str(e))
            return
        except OSError as e:
            self.view.mostrar_erro(f"Não foi possível gravar o config.json: {e}")
            return
        self.limites_alterados.emit(novo)
        self.view.accept()
