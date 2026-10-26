import datetime
from PySide6.QtWidgets import QDialog, QTableWidgetItem, QHeaderView
from PySide6.QtCore import QDate 
from ui.tela_historico import Ui_Dialog
from models.repository import EventoRepository 

class HistoricoController(QDialog):
    def __init__(self): 
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Histórico de Eventos")
        
        self.ui.data_filtro.setDate(QDate.currentDate())
        
        self.ui.tabela_logs.setColumnCount(3)
        self.ui.tabela_logs.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Mensagem"])
        header = self.ui.tabela_logs.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.ui.btn_fechar.clicked.connect(self.accept)
        self.ui.btn_filtrar.clicked.connect(self.filtrar_por_data) 

        # PREENCHE A TABELA DIRETO DO BANCO DE DADOS
        self.logs_completos = EventoRepository.listar_todos()
        self.preencher_tabela(self.logs_completos)

    def preencher_tabela(self, lista_para_mostrar):
        self.ui.tabela_logs.setRowCount(0)
        
        for log in lista_para_mostrar:
            linha_atual = self.ui.tabela_logs.rowCount()
            self.ui.tabela_logs.insertRow(linha_atual)
            
            self.ui.tabela_logs.setItem(linha_atual, 0, QTableWidgetItem(str(log[0])))
            self.ui.tabela_logs.setItem(linha_atual, 1, QTableWidgetItem(str(log[1])))
            self.ui.tabela_logs.setItem(linha_atual, 2, QTableWidgetItem(str(log[2])))

    def filtrar_por_data(self):
        data_escolhida = self.ui.data_filtro.date().toString("dd/MM/yyyy")
        logs_filtrados = []
        
        for log in self.logs_completos:
            data_do_log = str(log[0])[:10]  
            
            if data_do_log == data_escolhida:
                logs_filtrados.append(log)
                
        self.preencher_tabela(logs_filtrados)