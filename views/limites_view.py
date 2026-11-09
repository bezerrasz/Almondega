"""View do diálogo de limites: só exibe valores e repassa o que o operador digitou."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox

from ui.ui_config_limites import Ui_DialogLimites


class LimitesView(QDialog):
    salvar_solicitado = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DialogLimites()
        self.ui.setupUi(self)
        self.ui.botoes.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self._emitir)
        self.ui.botoes.rejected.connect(self.reject)

    def preencher(self, config: dict):
        self.ui.spin_tensao_max.setValue(config["limite_tensao_max"])
        self.ui.spin_tensao_min.setValue(config["limite_tensao_min"])
        self.ui.spin_corrente_max.setValue(config["limite_corrente_max"])
        self.ui.spin_fator_potencia.setValue(config["fator_potencia"])
        self.ui.chk_reconexao.setChecked(config["reconexao_automatica"])

    def _emitir(self):
        self.salvar_solicitado.emit({
            "limite_tensao_max": self.ui.spin_tensao_max.value(),
            "limite_tensao_min": self.ui.spin_tensao_min.value(),
            "limite_corrente_max": self.ui.spin_corrente_max.value(),
            "fator_potencia": self.ui.spin_fator_potencia.value(),
            "reconexao_automatica": self.ui.chk_reconexao.isChecked(),
        })

    def mostrar_erro(self, mensagem: str):
        QMessageBox.warning(self, "Valor inválido", mensagem)
