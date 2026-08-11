from PySide6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem
from ui.Ui_tela_principal import Ui_MainWindow
# Importa o controller da popup para instanciação
from controller.tela_cadastro_controller import TelaCadastroController


class TelaPrincipalController(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Instancia e carrega a interface principal compilada
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Configura a QTableWidget via Controller
        self.ui.tbl_dados.setColumnCount(2)
        self.ui.tbl_dados.setHorizontalHeaderLabels(["Item", "Categoria"])
        
        # Conecta o botão de abertura da popup
        self.ui.btn_abrir.clicked.connect(self.abrir_janela)

    def abrir_janela(self):
        popup = TelaCadastroController(parent=self)

        if popup.exec() == QDialog.Accepted:
            dados = popup.get_dados()

            linha = self.ui.tbl_dados.rowCount()
            self.ui.tbl_dados.insertRow(linha)

            self.ui.tbl_dados.setItem(linha, 0, QTableWidgetItem(dados["nome"]))
            self.ui.tbl_dados.setItem(linha, 1, QTableWidgetItem(dados["categoria"]))
