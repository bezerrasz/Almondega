import logging
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QToolTip
from PySide6.QtGui import QCursor
from PySide6.QtCore import QTimer, QFileSystemWatcher, QDateTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from ui.dashboard import Ui_Dialog
from controller.config_controller import ConfigController
from controller.serialport_controller import SerialPortController
from controller.historico_controller import HistoricoController
from controller.conexao_controller import ConexaoController
from controller.persistencia_controller import PersistenciaController
from models import protocolo
from models.config_manager import ConfigManager
from models.sistema_model import SistemaModel

log = logging.getLogger(__name__)

TIMEOUT_ACK_DJ_MS = 2000
TIMEOUT_ENCERRAMENTO_MS = 6000

class DashboardController(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("⚡ Smart Grid - Dashboard")

        # A1/5: AS DUAS THREADS DE TRABALHO (banco e serial). A tela nunca fala direto com nenhum dos dois.
        self.persistencia = PersistenciaController(self)
        self.conexao = ConexaoController(self)
        self.cfg = ConfigManager()

        #INICIALIZACAO DO SISTEMA
        # (o log de auditoria passa a ser gravado pela thread do banco)
        self.model = SistemaModel(persistir=self.persistencia.registrar_evento)
        self.model.setpoint_tensao = self.cfg.carregar().get("limite_tensao")
        self.model.setpoint_corrente = self.cfg.carregar().get("limite_corrente")

        # SEM LINK COM A PLACA AINDA: NADA MEDIDO
        self.model.tensao_atual = 0.0
        self.model.corrente_atual = 0.0
        self.atualizar_indicadores()

        # ESTADO DA COMUNICACAO / DO DISJUNTOR (A1/5)
        self.ultima_leitura = None
        self.disjuntor_fechado = None        # None = sem link; True/False = estado real informado pela placa
        self.corte_pendente = None           # mensagem do corte aguardando o ACK da placa
        self.alavanca_pendente = None        # True = fechar, False = abrir
        self.motivo_corte_automatico = None
        self.sincronizando = False
        self.teve_link = False
        self.encerrando = False
        self.modo_historico = False
        self.pedido_historico = None
        self.filtro_historico = {}

        # BOTAO DE EMERGENCIA / ALAVANCA 
        self.ui.btn_parar.clicked.connect(self.acionar_emergencia)

        self.ui.chk_simulador.toggled.connect(self.mudar_estado_alavanca)

        # CRIACAO DE GRAFICO
        # (A1/5: cada amostra da SerialThread entra na curva; x = segundos desde a primeira amostra)
        self.tempo_x = deque()
        self.potencia_y = deque()
        self.tempo_inicial = None
        self.grafico_sujo = False
        
        self.preparar_grafico_realtime()
        self.timer_grafico = QTimer()
        self.timer_grafico.timeout.connect(self.atualizar_linha_grafico)
        self.timer_grafico.start(250)

        # A1/5: MODO DO GRAFICO (TEMPO REAL x HISTORICO) E FILTRO DA CONSULTA
        self.ui.radio_historico.toggled.connect(self.mudar_modo_grafico)
        self.ui.radio_ultimas.toggled.connect(self.mudar_tipo_filtro)
        self.ui.btn_consultar.clicked.connect(self.consultar_historico)
        agora = QDateTime.currentDateTime()
        self.ui.dt_fim.setDateTime(agora)
        self.ui.dt_inicio.setDateTime(agora.addSecs(-3600))
        self.mudar_tipo_filtro()

        # BOLINHA DE LIMITE
        valor_maximo_slider = self.ui.slider_limite.maximum()
        self.ui.slider_limite.setValue(valor_maximo_slider)
        self.limite_potencia = valor_maximo_slider
        self.ui.slider_limite.valueChanged.connect(self.mostrar_valor_bolinha)

        # LED DE STATUS
        # (A1/5: o LED agora mostra o estado REAL do disjuntor, informado pela placa -> mostrar_disjuntor)
        self.mostrar_disjuntor(None)

        # BOTOES QUE MUDAM AS TELAS
        self.ui.btn_config_limites.clicked.connect(self.abrir_tela_configuracao)
        self.ui.btn_tela_serial.clicked.connect(self.abrir_tela_serial)
        self.ui.btn_tela_historico.clicked.connect(self.abrir_tela_historico)

        # A1/5: TELA SERIAL (uma só, reaproveitada) E SINAIS DAS THREADS
        self.tela_serial = SerialPortController(self.conexao)
        self.tela_serial.enviar_log.connect(self.model.registrar_log)

        self.timer_ack = QTimer(self)
        self.timer_ack.setSingleShot(True)
        self.timer_ack.timeout.connect(self.ack_expirou)

        self.conexao.estado_mudou.connect(self.ao_mudar_estado)
        self.conexao.leitura_recebida.connect(self.ao_receber_leitura)
        self.conexao.disjuntor_confirmado.connect(self.ao_confirmar_disjuntor)
        self.conexao.falha_comunicacao.connect(self.ao_falhar_comunicacao)
        self.persistencia.historico_pronto.connect(self.ao_receber_historico)
        self.persistencia.corte_concluido.connect(self.ao_concluir_corte)
        self.persistencia.erro.connect(lambda msg: QMessageBox.critical(self, "Banco de dados", msg))

        # recria o config.json no instante em que ele for apagado (mesmo com o app aberto)
        self.observador_config = QFileSystemWatcher([self.cfg.caminho_pasta()], self)
        self.observador_config.directoryChanged.connect(self.verificar_config)

        self.persistencia.iniciar()      # abre o banco na DatabaseThread

    # TELA 1

    #ATUALIZAO VALORES DE TENSAO E CORRENTE E CALCULO DE POTENCIA
    def atualizar_indicadores(self):
        v = self.model.tensao_atual
        i = self.model.corrente_atual
        
        p = self.model.calcular_potencia()

        self.ui.lbl_tensao.setText(f"{v:.1f} V")
        self.ui.lbl_corrente.setText(f"{i:.1f} A")
        self.ui.lbl_potencia.setText(f"{p:.1f} W")

    # ATIVACAO BOTAO DE EMERGENCIA
    # A1/5: o botão PARAR manda DJ,0 à placa; o corte só é gravado no banco (ACID) depois do ACK dela
    def acionar_emergencia(self):
        self.executar_corte(None)

    def executar_corte(self, motivo_automatico):
        if not self.conexao.enviar_comando(protocolo.cmd_disjuntor(False)):
            QMessageBox.warning(self, "Disjuntor", "Sem link com a placa: comando não enviado.")
            return
        self.motivo_corte_automatico = motivo_automatico
        self.corte_pendente = ("Botão de PARADA acionado pelo operador!" if motivo_automatico is None
                               else f"Corte automático: {motivo_automatico}")
        self.timer_ack.start(TIMEOUT_ACK_DJ_MS)

    # SIMULA UMA ALAVANCA DE LIGA E DESLIGA DO SISTEMA
    # A1/5: a alavanca agora comanda o disjuntor de verdade (DJ,1 / DJ,0); o estado exibido vem do ACK da placa
    def mudar_estado_alavanca(self, estado):
        if self.sincronizando:      # a alavanca foi movida pelo programa (acompanhando a placa), não pelo operador
            return
        if not self.conexao.enviar_comando(protocolo.cmd_disjuntor(bool(estado))):
            QMessageBox.warning(self, "Disjuntor", "Sem link com a placa: comando não enviado.")
            self.mostrar_disjuntor(self.disjuntor_fechado)
            return
        self.alavanca_pendente = bool(estado)
        self.timer_ack.start(TIMEOUT_ACK_DJ_MS)

    # GRAFICO COM VALORES SIMULADOS 
    def preparar_grafico_realtime(self):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        self.linha, = self.ax.plot([], [], linestyle='-', color="#f5890f", linewidth=2)

        self.ax.set_title("Consumo em Tempo Real (Últimos 60s)")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Potência (W)")
        self.ax.set_ylim(0, 3500)
        self.ax.grid(True)
        self.fig.subplots_adjust(left=0.18, bottom=0.18, right=0.95, top=0.90)

        layout = QVBoxLayout(self.ui.widget_grafico)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def atualizar_linha_grafico(self):
        #Redesenha a curva em tempo real (as amostras entram em adicionar_ponto)
        if not self.grafico_sujo or self.modo_historico or not self.tempo_x:
            return
        self.grafico_sujo = False
        tempo_atual = self.tempo_x[-1]
        self.linha.set_data(self.tempo_x, self.potencia_y)

        limite_esquerdo = max(0, tempo_atual - 60)
        limite_direito = max(60, tempo_atual)
        self.ax.set_xlim(limite_esquerdo, limite_direito)
        self.ax.set_ylim(0, max(3500, max(self.potencia_y) * 1.1))

        self.canvas.draw()

    def adicionar_ponto(self, instante, potencia):
        if self.tempo_inicial is None:
            self.tempo_inicial = instante
        t = (instante - self.tempo_inicial).total_seconds()
        self.tempo_x.append(t)
        self.potencia_y.append(potencia)
        while self.tempo_x and self.tempo_x[0] < t - 60:     # descarta o que saiu da janela de 60 s
            self.tempo_x.popleft()
            self.potencia_y.popleft()
        self.grafico_sujo = True

    # A1/5: MODO HISTORICO DO GRAFICO
    def mudar_modo_grafico(self, historico):
        self.modo_historico = historico
        self.ui.grp_historico.setEnabled(historico)
        if not historico:
            self.restaurar_tempo_real()

    def mudar_tipo_filtro(self, *_):
        ultimas = self.ui.radio_ultimas.isChecked()
        self.ui.spin_ultimas.setEnabled(ultimas)
        self.ui.dt_inicio.setEnabled(not ultimas)
        self.ui.dt_fim.setEnabled(not ultimas)

    def consultar_historico(self):
        if self.ui.radio_ultimas.isChecked():
            filtro = {"modo": "ultimas", "quantidade": self.ui.spin_ultimas.value()}
        else:
            filtro = {"modo": "intervalo",
                      "inicio": self.ui.dt_inicio.dateTime().toPython(),
                      "fim": self.ui.dt_fim.dateTime().toPython()}
            if filtro["inicio"] >= filtro["fim"]:
                QMessageBox.warning(self, "Filtro inválido", "O início do intervalo deve ser anterior ao fim.")
                return
        self.ui.btn_consultar.setEnabled(False)
        self.filtro_historico = filtro
        # a consulta roda na DatabaseThread; o resultado volta pelo sinal historico_pronto
        self.pedido_historico = self.persistencia.consultar_historico(filtro)

    def ao_receber_historico(self, pedido, dados, total):
        if pedido != self.pedido_historico:
            return        # resposta de uma consulta antiga
        self.ui.btn_consultar.setEnabled(True)
        f = self.filtro_historico
        if f["modo"] == "ultimas":
            titulo = f"Histórico: últimas {f['quantidade']} leituras"
        else:
            titulo = f"Histórico: {f['inicio']:%d/%m %H:%M:%S} a {f['fim']:%d/%m %H:%M:%S}"
        titulo += f" ({len(dados)} de {total} pontos)" if total > len(dados) else f" ({total} pontos)"
        self.desenhar_historico([d[0] for d in dados], [d[3] for d in dados], titulo)

    def desenhar_historico(self, instantes, potencias, titulo):
        if not self.modo_historico:
            return
        self.ax.clear()
        self.ax.plot(instantes, potencias, linestyle='-', color="#f5890f", linewidth=2)
        self.ax.set_title(titulo)
        self.ax.set_xlabel("Data/hora")
        self.ax.set_ylabel("Potência (W)")
        self.ax.set_ylim(0, max([3500] + [p * 1.1 for p in potencias]))
        self.ax.grid(True)
        self.ax.xaxis.set_major_formatter(DateFormatter("%d/%m %H:%M:%S"))
        for rotulo in self.ax.get_xticklabels():
            rotulo.set_rotation(20)
            rotulo.set_ha("right")
        self.canvas.draw()

    def restaurar_tempo_real(self):
        self.ax.clear()
        self.linha, = self.ax.plot(list(self.tempo_x), list(self.potencia_y), linestyle='-', color="#f5890f", linewidth=2)
        self.ax.set_title("Consumo em Tempo Real (Últimos 60s)")
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Potência (W)")
        self.ax.set_ylim(0, 3500)
        self.ax.grid(True)
        self.grafico_sujo = True
        self.atualizar_linha_grafico()
        self.canvas.draw()

    # BOLINHA PARA LIMITE DE VALORES QUE ACOMPANHA O MOUSE
    def mostrar_valor_bolinha(self, valor):
        posicao_mouse = QCursor.pos()
        
        QToolTip.showText(posicao_mouse, f"{valor} W", self.ui.slider_limite)
       
        self.limite_potencia = valor

    # FAZER UMA SIMULACAO DE UM LED FUNCIONANDO
    def atualizar_status_led(self, ligado):
        if ligado:
            self.ui.lbl_status_disjuntor.setText("FECHADO")
            self.ui.lbl_status_disjuntor.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
            )
        else:
            self.ui.lbl_status_disjuntor.setText("ABERTO")
            self.ui.lbl_status_disjuntor.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
            )

    # A1/5: ESTADO REAL DO DISJUNTOR (None = sem link com a placa)
    def mostrar_disjuntor(self, fechado):
        self.disjuntor_fechado = fechado
        if fechado is None:
            self.ui.lbl_status_disjuntor.setText("SEM LINK")
            self.ui.lbl_status_disjuntor.setStyleSheet(
                "background-color: #555555; color: white; font-weight: bold; border-radius: 20px; qproperty-alignment: AlignCenter;"
            )
            return
        self.sincronizando = True          # a alavanca acompanha o estado real sem disparar comando
        self.ui.chk_simulador.setChecked(fechado)
        self.sincronizando = False
        self.atualizar_status_led(fechado)

    # A1/5: EVENTOS DA SERIAL THREAD
    def ao_mudar_estado(self, estado, detalhe):
        link = estado == "TELEMETRIA"
        self.ui.chk_simulador.setEnabled(link)
        self.ui.btn_parar.setEnabled(link)
        if link:
            self.teve_link = True
            return
        self.mostrar_disjuntor(None)
        self.model.tensao_atual = 0.0
        self.model.corrente_atual = 0.0
        self.atualizar_indicadores()

    def ao_falhar_comunicacao(self, mensagem):
        log.error("falha de comunicação: %s", mensagem)
        if self.teve_link:            # só alerta e grava na queda do link, não a cada nova tentativa
            self.teve_link = False
            self.corte_pendente = self.alavanca_pendente = None
            self.timer_ack.stop()
            self.model.registrar_log("ERROR", mensagem)
            if not self.encerrando:
                QMessageBox.critical(self, "Falha de comunicação",
                                     f"{mensagem}\n\nO sistema tentará reconectar automaticamente.")

    def ao_receber_leitura(self, leitura):
        self.ultima_leitura = leitura
        self.model.tensao_atual = leitura.tensao
        self.model.corrente_atual = leitura.corrente
        self.atualizar_indicadores()
        self.adicionar_ponto(leitura.timestamp, leitura.potencia)
        self.persistencia.gravar_leitura(leitura)          # grava na DatabaseThread

        if self.disjuntor_fechado != leitura.disjuntor_fechado:
            self.mostrar_disjuntor(leitura.disjuntor_fechado)

        # LIMITES (as mesmas regras de antes: corrente do config.json e potência do slider)
        if not self.disjuntor_fechado or self.corte_pendente is not None:
            return
        limite = self.model.setpoint_corrente
        nova_potencia = self.model.calcular_potencia()
        if limite > 0 and self.model.corrente_atual > limite:
            texto_alerta = f"SOBRECARGA: Corrente {self.model.corrente_atual:.1f}A excedeu limite de {limite}A!"
            self.model.registrar_log("ALERTA CRÍTICO", texto_alerta)
            self.executar_corte(texto_alerta)
        elif self.limite_potencia > 0 and nova_potencia > self.limite_potencia:
            texto_alerta = f"PICO DE CONSUMO: Potência {nova_potencia:.1f}W excedeu o limite do Slider ({self.limite_potencia}W)!"
            self.model.registrar_log("ALERTA DE CONSUMO", texto_alerta)
            self.executar_corte(texto_alerta)

    def ao_confirmar_disjuntor(self, fechado):
        #ACK da placa a um DJ,0 / DJ,1
        self.mostrar_disjuntor(fechado)
        corrente = self.ultima_leitura.corrente if self.ultima_leitura else 0.0

        if self.corte_pendente is not None and not fechado:
            mensagem, self.corte_pendente = self.corte_pendente, None
            self.timer_ack.stop()
            # status do disjuntor + evento na mesma transação (ACID), executada na DatabaseThread
            self.persistencia.corte_emergencial("EMERGÊNCIA", mensagem, corrente)
        elif self.alavanca_pendente is not None and self.alavanca_pendente == fechado:
            self.alavanca_pendente = None
            self.timer_ack.stop()
            texto = "Alavanca acionada: Sistema LIGADO." if fechado else "Alavanca recuada: Sistema DESLIGADO."
            self.persistencia.registrar_chaveamento("FECHADO" if fechado else "ABERTO", "OPERAÇÃO", texto, corrente)
            log.info("OPERAÇÃO: %s", texto)

    def ao_concluir_corte(self, ok, motivo):
        #Resposta da DatabaseThread ao corte emergencial
        if ok:
            extra = f"\n\n{self.motivo_corte_automatico}" if self.motivo_corte_automatico else ""
            QMessageBox.warning(self, "Alerta", "Corte emergencial acionado com sucesso e salvo no banco!" + extra)
            self.model.registrar_log("EMERGÊNCIA", "Corte concluído e persistido via ACID.")
        else:
            QMessageBox.critical(self, "Falha Transacional", f"Ocorreu um erro crítico! ROLLBACK executado no banco.\nMotivo: {motivo}")
            self.model.registrar_log("ERROR", f"Falha na operação de corte emergencial. Rollback executado: {motivo}")
        self.motivo_corte_automatico = None

    def ack_expirou(self):
        if self.corte_pendente is None and self.alavanca_pendente is None:
            return
        pendente = "corte emergencial" if self.corte_pendente is not None else "chaveamento"
        self.corte_pendente = self.alavanca_pendente = None
        texto = f"Placa não confirmou o comando ({pendente}) em {TIMEOUT_ACK_DJ_MS} ms"
        self.model.registrar_log("ERROR", texto)
        self.mostrar_disjuntor(self.disjuntor_fechado)       # volta a tela ao estado real
        QMessageBox.critical(self, "Disjuntor", texto)

    def verificar_config(self, _pasta):
        if self.cfg.existe():
            return
        dados = self.cfg.carregar()            # recria com os valores padrão seguros
        self.model.setpoint_tensao = dados.get("limite_tensao")
        self.model.setpoint_corrente = dados.get("limite_corrente")
        self.model.registrar_log("CONFIG", "config.json foi excluído e recriado com valores padrão seguros")
        QMessageBox.information(self, "Configuração", "O config.json foi excluído e recriado com valores padrão seguros.")

    # TELA 2
    def abrir_tela_configuracao(self):
        tela_config = ConfigController(self.persistencia)
        
        if tela_config.exec() == QDialog.Accepted:
            nova_tensao = tela_config.limite_tensao
            nova_corrente = tela_config.limite_corrente
            
            self.model.setpoint_tensao = nova_tensao
            self.model.setpoint_corrente = nova_corrente
            
            texto_log = f"Setpoints atualizados: Tensão={nova_tensao}V | Corrente={nova_corrente}A"
            self.model.registrar_log("CONFIG", texto_log)

    # TELA 3
    def abrir_tela_serial(self):
        self.tela_serial.exec()

    # TELA 4
    def abrir_tela_historico(self):
        tela_logs = HistoricoController(self.persistencia)   
        tela_logs.exec()

    # A1/5: ENCERRAMENTO COOPERATIVO
    # Fechar a janela não mata as threads: a serial para primeiro (envia STOP à placa), depois o banco
    # grava o que falta e fecha a conexão. Só então a janela fecha de verdade.
    def closeEvent(self, event):
        if getattr(self, "fechamento_liberado", False):
            event.accept()
            return
        event.ignore()
        self.encerrar()

    def reject(self):          # ESC também passa pelo encerramento ordenado
        self.close()

    def encerrar(self):
        if self.encerrando:
            return
        self.encerrando = True
        log.info("encerrando aplicação")
        self.timer_grafico.stop()
        QTimer.singleShot(TIMEOUT_ENCERRAMENTO_MS, self.forcar_fechamento)
        if self.conexao.ativo:
            self.conexao.conexao_encerrada.connect(self.encerrar_banco)
            self.conexao.desconectar()
        else:
            self.encerrar_banco()

    def encerrar_banco(self):
        self.persistencia.finalizado.connect(self.liberar_fechamento)
        self.persistencia.encerrar()

    def liberar_fechamento(self):
        self.fechamento_liberado = True
        self.close()

    def forcar_fechamento(self):
        if getattr(self, "fechamento_liberado", False):
            return
        log.warning("encerramento demorou; aguardando as threads por mais 1 s")
        self.conexao.desconectar()
        self.conexao.aguardar(1000)
        self.persistencia.encerrar()
        self.persistencia.aguardar(1000)
        self.liberar_fechamento()

