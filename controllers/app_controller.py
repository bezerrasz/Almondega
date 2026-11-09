"""
Controller principal: liga a View aos Models e coordena as duas QThreads.

Fluxo de uma amostra:
  SerialThread decodifica DATA -> sinal leitura_recebida -> (thread GUI) AppController
     -> View: indicadores + curva em tempo real
     -> PersistenciaController -> (DatabaseThread) INSERT em leituras
     -> MonitorLimites (Model) -> se violou: comando DJ,0 + evento de corte
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer

from controllers.conexao_controller import ConexaoController
from controllers.eventos_controller import EventosController
from controllers.limites_controller import LimitesController
from controllers.persistencia_controller import PersistenciaController
from models import protocolo
from models.caminhos import DB_PATH
from models.config_manager import ConfigManager
from models.entidades import Disjuntor, Evento, LeituraTelemetria, TipoEvento
from models.portas_seriais import listar_portas
from models.regras import MonitorLimites
from views.dashboard_view import DashboardView

log = logging.getLogger(__name__)

TIMEOUT_ACK_DJ_MS = 2000
TIMEOUT_ENCERRAMENTO_MS = 6000


class AppController(QObject):
    def __init__(self, view: DashboardView, config: ConfigManager, caminho_db=DB_PATH):
        super().__init__()
        self.view = view
        self.config = config
        cfg = config.carregar()

        self.disjuntor = Disjuntor()
        self.monitor = MonitorLimites(config.limites())
        self.conexao = ConexaoController(self)
        self.persistencia = PersistenciaController(caminho_db, self)

        self._modo = "tempo_real"
        self._pedido_historico = None
        self._ultima_leitura: LeituraTelemetria | None = None
        self._comando_pendente: tuple[bool, Evento] | None = None
        self._teve_link = False
        self._desconexao_pelo_operador = False
        self._encerrando = False

        self._timer_ack = QTimer(self)
        self._timer_ack.setSingleShot(True)
        self._timer_ack.timeout.connect(self._ack_expirou)

        # recria o config.json no instante em que ele for apagado
        self._observador_config = QFileSystemWatcher([str(config.caminho.parent)], self)
        self._observador_config.directoryChanged.connect(self._verificar_config)

        self._ligar_view()
        self._ligar_conexao()
        self._ligar_persistencia()

        # estado inicial da tela a partir do config.json
        self.view.definir_velocidades(protocolo.BAUDS_SUPORTADOS, cfg["baud_rate"])
        self.view.definir_periodo(cfg["taxa_amostragem_ms"])
        self.view.definir_capacidade_grafico(cfg["pontos_grafico_tempo_real"])
        self._aplicar_limites_na_view()
        self._atualizar_portas()

        self.persistencia.iniciar()

    # ------------------------------------------------------------------ ligações
    def _ligar_view(self):
        v = self.view
        v.conectar_solicitado.connect(self._conectar)
        v.desconectar_solicitado.connect(self._desconectar)
        v.atualizar_portas_solicitado.connect(self._atualizar_portas)
        v.disjuntor_solicitado.connect(self._chaveamento_manual)
        v.emergencia_solicitada.connect(self._corte_emergencial)
        v.abrir_limites_solicitado.connect(self._abrir_limites)
        v.abrir_eventos_solicitado.connect(self._abrir_eventos)
        v.modo_grafico_alterado.connect(self._mudar_modo)
        v.consulta_historico_solicitada.connect(self._consultar_historico)
        v.fechamento_solicitado.connect(self.encerrar)

    def _ligar_conexao(self):
        c = self.conexao
        c.estado_mudou.connect(self._ao_mudar_estado)
        c.log_protocolo.connect(lambda t: self.view.escrever_console(f"[serial] {t}"))
        c.velocidade_negociada.connect(self._ao_negociar)
        c.leitura_recebida.connect(self._ao_receber_leitura)
        c.disjuntor_confirmado.connect(self._ao_confirmar_disjuntor)
        c.estatisticas.connect(self.view.mostrar_estatisticas)
        c.falha_comunicacao.connect(self._ao_falhar_comunicacao)

    def _ligar_persistencia(self):
        p = self.persistencia
        p.pronto.connect(lambda: self.view.escrever_console("[banco] SQLite pronto (thread dedicada)"))
        p.historico_pronto.connect(self._ao_receber_historico)
        p.evento_gravado.connect(lambda e: self.view.escrever_console(f"[evento] {e.tipo}: {e.descricao}"))
        p.erro.connect(self._ao_erro_banco)

    # ------------------------------------------------------------------ conexão
    def _atualizar_portas(self):
        self.view.definir_portas(listar_portas(), self.config.carregar()["porta_serial"])

    def _conectar(self, porta: str, baud: int, periodo_ms: int):
        if not porta:
            self.view.mostrar_alerta("Conexão", "Informe a porta serial.")
            return
        try:
            cfg = self.config.salvar({"porta_serial": porta, "baud_rate": baud,
                                      "taxa_amostragem_ms": periodo_ms})
        except (ValueError, OSError) as e:
            self.view.mostrar_alerta("Configuração inválida", str(e))
            return
        self._desconexao_pelo_operador = False
        self.view.escrever_console(f"[serial] conectando em {porta}: início obrigatório a 9600 bps, "
                                   f"alvo {baud} bps, amostragem {periodo_ms} ms")
        self.conexao.conectar(porta, baud, periodo_ms, cfg["fator_potencia"], cfg["reconexao_automatica"])

    def _desconectar(self):
        self._desconexao_pelo_operador = True
        self.conexao.desconectar()

    def _ao_mudar_estado(self, estado: str, detalhe: str):
        self.view.mostrar_estado_conexao(estado, detalhe)
        link = estado == "TELEMETRIA"
        self.view.habilitar_comandos(link)

        if link:
            self._teve_link = True
            self.view.limpar_medicoes()
            self.persistencia.registrar_evento(Evento(TipoEvento.CONEXAO, f"Handshake concluído: {detalhe}"))
            return

        self.view.mostrar_disjuntor(None)
        if estado == "DESCONECTADO" and self._teve_link:
            self._teve_link = False
            motivo = "pelo operador" if self._desconexao_pelo_operador else "comunicação encerrada"
            self.persistencia.registrar_evento(Evento(TipoEvento.DESCONEXAO, f"Link encerrado {motivo}"))

    def _ao_negociar(self, baud: int):
        self.view.mostrar_status(f"Velocidade negociada: {baud} bps", 8000)

    def _ao_falhar_comunicacao(self, mensagem: str):
        self.view.escrever_console(f"[serial] FALHA: {mensagem}")
        if self._teve_link:            # só alerta/grava na queda do link, não a cada nova tentativa
            self._teve_link = False
            self.view.limpar_medicoes()
            self.persistencia.registrar_evento(Evento(TipoEvento.FALHA_COMUNICACAO, mensagem))
            if not self._encerrando:
                self.view.mostrar_alerta("Falha de comunicação",
                                         f"{mensagem}\n\nO sistema tentará reconectar automaticamente "
                                         "(se habilitado nos parâmetros).", critico=True)

    # ------------------------------------------------------------------ telemetria
    def _ao_receber_leitura(self, leitura: LeituraTelemetria):
        self._ultima_leitura = leitura
        self.view.mostrar_medicoes(leitura.tensao, leitura.corrente, leitura.potencia)
        self.view.adicionar_ponto_tempo_real(leitura.timestamp, leitura.tensao,
                                             leitura.corrente, leitura.potencia)
        self.persistencia.gravar_leitura(leitura)

        self.disjuntor.atualizar(leitura.disjuntor_fechado)
        self.view.mostrar_disjuntor(self.disjuntor.fechado)

        for violacao in self.monitor.avaliar(leitura):
            evento = Evento(violacao.tipo_evento, violacao.mensagem, violacao.valor)
            if violacao.exige_corte and self.disjuntor.fechado:
                self._comandar_disjuntor(False, evento)
                self.view.mostrar_alerta("Proteção atuou", violacao.mensagem, critico=True)
            else:
                self.persistencia.registrar_evento(evento)
                self.view.mostrar_status(violacao.mensagem, 10000)

    # ------------------------------------------------------------------ disjuntor
    def _chaveamento_manual(self, fechar: bool):
        tipo = TipoEvento.FECHAMENTO_MANUAL if fechar else TipoEvento.ABERTURA_MANUAL
        texto = "Operador fechou o disjuntor" if fechar else "Operador abriu o disjuntor"
        self._comandar_disjuntor(fechar, Evento(tipo, texto, self._corrente_atual()))

    def _corte_emergencial(self):
        self._comandar_disjuntor(False, Evento(TipoEvento.CORTE_EMERGENCIAL,
                                               "Corte emergencial acionado pelo operador",
                                               self._corrente_atual()))

    def _comandar_disjuntor(self, fechar: bool, evento: Evento):
        if not self.conexao.enviar_comando(protocolo.cmd_disjuntor(fechar)):
            self.view.mostrar_alerta("Disjuntor", "Sem link com a placa: comando não enviado.")
            return
        self._comando_pendente = (fechar, evento)
        self._timer_ack.start(TIMEOUT_ACK_DJ_MS)

    def _ao_confirmar_disjuntor(self, fechado: bool):
        self.disjuntor.atualizar(fechado)
        self.view.mostrar_disjuntor(fechado)
        if self._comando_pendente and self._comando_pendente[0] == fechado:
            _, evento = self._comando_pendente
            self._comando_pendente = None
            self._timer_ack.stop()
            # evento + status do dispositivo gravados na mesma transação
            self.persistencia.registrar_evento(evento, self.disjuntor.estado_texto)

    def _ack_expirou(self):
        if not self._comando_pendente:
            return
        fechar, evento = self._comando_pendente
        self._comando_pendente = None
        texto = f"Placa não confirmou o comando ({evento.tipo}) em {TIMEOUT_ACK_DJ_MS} ms"
        self.persistencia.registrar_evento(Evento(TipoEvento.FALHA_COMUNICACAO, texto))
        self.view.mostrar_alerta("Disjuntor", texto, critico=True)

    def _corrente_atual(self):
        return self._ultima_leitura.corrente if self._ultima_leitura else None

    # ------------------------------------------------------------------ gráfico
    def _mudar_modo(self, modo: str):
        self._modo = modo
        self.view.definir_modo(modo)
        if modo == "historico":
            self.view.mostrar_status("Modo histórico: a telemetria continua sendo gravada em segundo plano")

    def _consultar_historico(self, filtro: dict):
        if filtro["modo"] == "intervalo" and filtro["inicio"] >= filtro["fim"]:
            self.view.mostrar_alerta("Filtro inválido", "O início do intervalo deve ser anterior ao fim.")
            return
        self.view.indicar_consulta_em_andamento(True)
        self._filtro_atual = filtro
        self._pedido_historico = self.persistencia.consultar_historico(filtro)

    def _ao_receber_historico(self, pedido: int, leituras: list, total: int):
        if pedido != self._pedido_historico:
            return        # resposta de uma consulta antiga
        self.view.indicar_consulta_em_andamento(False)
        f = self._filtro_atual
        if f["modo"] == "ultimas":
            titulo = f"Histórico: últimas {f['quantidade']} leituras"
        else:
            titulo = f"Histórico: {f['inicio']:%d/%m %H:%M:%S} a {f['fim']:%d/%m %H:%M:%S}"
        if total > len(leituras):
            titulo += f" ({len(leituras)} de {total} pontos)"
        else:
            titulo += f" ({total} pontos)"
        self.view.mostrar_historico([l.timestamp for l in leituras], [l.tensao for l in leituras],
                                    [l.corrente for l in leituras], [l.potencia for l in leituras], titulo)

    # ------------------------------------------------------------------ diálogos
    def _abrir_limites(self):
        dialogo = LimitesController(self.config, self.view)
        dialogo.limites_alterados.connect(self._ao_alterar_limites)
        dialogo.executar()

    def _verificar_config(self, _pasta: str):
        if self.config.caminho.exists():
            return
        cfg = self.config.carregar()          # recria com os padrões seguros
        self.monitor.atualizar_limites(self.config.limites())
        self.conexao.atualizar_fator_potencia(cfg["fator_potencia"])
        self._aplicar_limites_na_view()
        if not self.conexao.ativo:
            self.view.definir_velocidades(protocolo.BAUDS_SUPORTADOS, cfg["baud_rate"])
            self.view.definir_periodo(cfg["taxa_amostragem_ms"])
        texto = "config.json foi excluído e recriado com valores padrão seguros"
        self.view.escrever_console(f"[config] {texto}")
        self.view.mostrar_status(texto, 10000)
        self.persistencia.registrar_evento(Evento(TipoEvento.CONFIG, texto))

    def _ao_alterar_limites(self, cfg: dict):
        self.monitor.atualizar_limites(self.config.limites())
        self.conexao.atualizar_fator_potencia(cfg["fator_potencia"])
        self._aplicar_limites_na_view()
        texto = (f"Limites: V {cfg['limite_tensao_min']}-{cfg['limite_tensao_max']} V, "
                 f"I máx {cfg['limite_corrente_max']} A, FP {cfg['fator_potencia']}")
        self.persistencia.registrar_evento(Evento(TipoEvento.CONFIG, texto))

    def _aplicar_limites_na_view(self):
        lim = self.config.limites()
        self.view.definir_limites_grafico({
            "tensao": (lim.tensao_min, lim.tensao_max),
            "corrente": (None, lim.corrente_max),
        })

    def _abrir_eventos(self):
        EventosController(self.persistencia, self.view).executar()

    def _ao_erro_banco(self, mensagem: str):
        log.error(mensagem)
        self.view.escrever_console(f"[banco] ERRO: {mensagem}")
        self.view.mostrar_status(mensagem, 10000)

    # ------------------------------------------------------------------ encerramento
    def encerrar(self):
        """Serial para primeiro (envia STOP), depois o banco grava o que falta e fecha."""
        if self._encerrando:
            return
        self._encerrando = True
        self._desconexao_pelo_operador = True
        log.info("encerrando aplicação")
        QTimer.singleShot(TIMEOUT_ENCERRAMENTO_MS, self._forcar_fechamento)
        if self.conexao.ativo:
            self.conexao.conexao_encerrada.connect(self._encerrar_banco)
            self.conexao.desconectar()
        else:
            self._encerrar_banco()

    def _encerrar_banco(self):
        self.persistencia.finalizado.connect(self.view.permitir_fechamento)
        self.persistencia.encerrar()

    def _forcar_fechamento(self):
        log.warning("encerramento demorou; aguardando threads por mais 1 s")
        self.conexao.desconectar()
        self.conexao.aguardar(1000)
        self.persistencia.encerrar()
        self.persistencia.aguardar(1000)
        self.view.permitir_fechamento()
