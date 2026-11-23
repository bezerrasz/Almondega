from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtCore import Signal 
from models import config_manager
from models.portas_seriais import listar_portas
from models.protocolo import BAUDS_SUPORTADOS
from ui.serialport import Ui_SerialDialog
import os
import json

class SerialPortController(QDialog):
    
    enviar_log = Signal(str, str) 

    def __init__(self, conexao):
        super().__init__()
        self.conexao = conexao      # A1/5: a porta é aberta pela SerialThread (ConexaoController)
        self.teve_link = False
        self.ui = Ui_SerialDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("🔌 Conexão Serial")

        self.atualizar_portas()
        self.ui.combo_porta.setStyleSheet(
            "background-color: black; color: white; font-weight: regular; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )
        
        self.ui.combo_br.addItems([str(b) for b in BAUDS_SUPORTADOS])    # 9600, 19200, 38400, 115200
        self.ui.combo_br.setStyleSheet(
            "background-color: black; color: white; font-weight: regular; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )

        self.ui.btn_conectar.clicked.connect(self.conectar)
        self.ui.btn_desconectar.clicked.connect(self.desconectar)

    # cONFIGURAÇÃO INICIAL DA PORTA SERIAL COM BASE NO ARQUIVO DE CONFIGURAÇÃO jSON 
        self.cfg = config_manager.ConfigManager()

        self.ui.combo_porta.setCurrentText(self.cfg.carregar().get("porta_serial"))
        self.ui.combo_br.setCurrentText(str(self.cfg.carregar().get("baud_rate")))
        self.ui.spin_amostragem.setValue(self.cfg.carregar().get("taxa_amostragem_ms"))
        self.ui.spin_timeout.setValue(self.cfg.carregar().get("timeout_s"))

        #Nas duas linhas abaixo, o sinal de mudança das comboxes é conectado a função de autosave_config, 
        # que salva automaticamente as configurações de porta serial e baud rate no arquivo JSON sempre que o usuário altera essas opções na interface gráfica.

        self.ui.combo_porta.currentIndexChanged.connect(self.autosave_config)
        self.ui.combo_br.currentIndexChanged.connect(self.autosave_config)
        self.ui.spin_amostragem.valueChanged.connect(self.autosave_config)
        self.ui.spin_timeout.valueChanged.connect(self.autosave_config)

        # A1/5: estado real da conexão e log do handshake vêm da SerialThread
        self.conexao.estado_mudou.connect(self.ao_mudar_estado)
        self.conexao.log_protocolo.connect(self.ui.txt_log_serial.appendPlainText)
        self.conexao.velocidade_negociada.connect(
            lambda baud: self.ui.lbl_velocidade.setText(f"Velocidade: {baud} bps"))
        self.ao_mudar_estado("DESCONECTADO", "")

    def atualizar_portas(self):
        #Lista as portas seriais que existem de verdade no computador (mantém a porta do config.json)
        if self.conexao.ativo:
            return
        atual = self.ui.combo_porta.currentText() or self.cfg_porta()
        self.ui.combo_porta.blockSignals(True)
        self.ui.combo_porta.clear()
        for dispositivo, _descricao in listar_portas():
            self.ui.combo_porta.addItem(dispositivo)
        if atual and self.ui.combo_porta.findText(atual) < 0:
            self.ui.combo_porta.addItem(atual)
        self.ui.combo_porta.setCurrentText(atual)
        self.ui.combo_porta.blockSignals(False)

    def cfg_porta(self):
        return config_manager.ConfigManager().carregar().get("porta_serial")

    def autosave_config(self):
        #Função de salvamento automático para as configurações deixadas pelo usuário na conexão serial

        if not self.ui.combo_porta.currentText():
            return
        dados = self.cfg.carregar()
        dados["porta_serial"] = self.ui.combo_porta.currentText()
        dados["baud_rate"] = int(self.ui.combo_br.currentText())
        dados["taxa_amostragem_ms"] = self.ui.spin_amostragem.value()
        dados["timeout_s"] = self.ui.spin_timeout.value()

        self.cfg.salvar(dados)


    def conectar(self):
        porta = self.ui.combo_porta.currentText()
        baud = int(self.ui.combo_br.currentText())
        if not porta:
            QMessageBox.warning(self, "Conexão", "Informe a porta serial.")
            return

        self.autosave_config()
        self.ui.txt_log_serial.appendPlainText(
            f"conectando em {porta}: início obrigatório a 9600 bps, alvo {baud} bps, "
            f"amostragem {self.ui.spin_amostragem.value()} ms")
        # A1/5: quem abre a porta e faz o handshake é a SerialThread; o status só muda quando a placa responde
        self.conexao.conectar(porta, baud, self.ui.spin_amostragem.value(), 1.0, True,
                              float(self.ui.spin_timeout.value()))

    def desconectar(self):
        self.conexao.desconectar()

    def ao_mudar_estado(self, estado, detalhe):
        #Atualiza a tela com o estado REAL da conexão (vindo da SerialThread)
        porta = self.ui.combo_porta.currentText()
        em_andamento = estado in ("ABRINDO", "HANDSHAKE", "SINCRONIZANDO", "RECONECTANDO", "ENCERRANDO")

        if estado == "TELEMETRIA":
            self.ui.lbl_status.setText("Conectado")
            cor = "green"
        elif em_andamento:
            self.ui.lbl_status.setText("Conectando...")
            cor = "#d98e04"
        else:
            self.ui.lbl_status.setText("Desconectado")
            self.ui.lbl_velocidade.setText("Velocidade: -")
            cor = "red"
        self.ui.lbl_status.setStyleSheet(
            f"background-color: {cor}; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
        )

        ativo = estado != "DESCONECTADO"
        for w in (self.ui.combo_porta, self.ui.combo_br, self.ui.spin_amostragem, self.ui.spin_timeout):
            w.setEnabled(not ativo)
        self.ui.btn_conectar.setEnabled(not ativo)
        self.ui.btn_desconectar.setEnabled(ativo and estado != "ENCERRANDO")

        if estado == "TELEMETRIA" and not self.teve_link:
            self.teve_link = True
            self.enviar_log.emit("SERIAL", f"Conectado com sucesso à {porta} ({detalhe})")
            if self.isVisible():
                QMessageBox.information(self, "Dispositivo Conectado", "{} conectado com sucesso!".format(porta))
        elif estado == "DESCONECTADO" and self.teve_link:
            self.teve_link = False
            self.enviar_log.emit("SERIAL", f"Conexão encerrada com a {porta}")
            if self.isVisible():
                QMessageBox.information(self, "Dispositivo Desconectado", "{} desconectado com sucesso!".format(porta))

    def exec(self):
        self.atualizar_portas()
        return super().exec()
