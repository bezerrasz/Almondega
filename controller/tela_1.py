from PySide6.QtWidgets import QDialog
from ui.tela_2 import Ui_Dialog


class TelaCadastroController(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Instancia e carrega a interface compilada pelo Qt
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Popula as opções do ComboBox dinamicamente via Controller
        self.ui.cmb_categoria.clear()
        self.ui.cmb_categoria.addItems(["Selecione...", "Software", "Hardware", "Redes"])
        # Conecta o clique do botão ao método accept() nativo do QDialog
        self.ui.btn_ok.clicked.connect(self.accept)

    # Método público para ler os dados da popup sem alterar a UI gerada.
    def get_dados(self) -> dict:
        dicionario = {
            "nome": self.ui.txt_nome.text().strip(),
            "categoria": self.ui.cmb_categoria.currentText()
        }

        return dicionario