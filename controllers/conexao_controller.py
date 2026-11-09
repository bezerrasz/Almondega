"""Ciclo de vida da QThread serial (criação, encerramento cooperativo, deleteLater)."""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QThread, Signal

from workers.serial_worker import SerialWorker

log = logging.getLogger(__name__)


class ConexaoController(QObject):
    # sinais repassados do worker (já entregues na thread da GUI)
    estado_mudou = Signal(str, str)
    log_protocolo = Signal(str)
    velocidade_negociada = Signal(int)
    leitura_recebida = Signal(object)
    disjuntor_confirmado = Signal(bool)
    estatisticas = Signal(int, int, int)
    falha_comunicacao = Signal(str)
    conexao_encerrada = Signal()          # a thread terminou de verdade

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: SerialWorker | None = None
        self.link_ativo = False

    @property
    def ativo(self) -> bool:
        return self._thread is not None

    def conectar(self, porta: str, baud_alvo: int, periodo_ms: int,
                 fator_potencia: float, reconexao_automatica: bool):
        if self.ativo:
            return
        self._thread = QThread()
        self._thread.setObjectName("SerialThread")
        self._worker = SerialWorker(porta, baud_alvo, periodo_ms, fator_potencia, reconexao_automatica)
        self._worker.moveToThread(self._thread)

        w = self._worker
        self._thread.started.connect(w.executar)
        w.estado_mudou.connect(self._ao_mudar_estado)
        w.log_protocolo.connect(self.log_protocolo)
        w.velocidade_negociada.connect(self.velocidade_negociada)
        w.leitura_recebida.connect(self.leitura_recebida)
        w.disjuntor_confirmado.connect(self.disjuntor_confirmado)
        w.estatisticas.connect(self.estatisticas)
        w.falha_comunicacao.connect(self.falha_comunicacao)

        # encerramento cooperativo: o laço termina -> finalizado -> quit -> finished
        w.finalizado.connect(self._thread.quit)
        self._thread.finished.connect(w.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._ao_terminar_thread)

        log.info("iniciando SerialThread: %s alvo %d bps, %d ms", porta, baud_alvo, periodo_ms)
        self._thread.start()

    def desconectar(self):
        """Pede a parada. Chamada direta (thread-safe): o worker está ocupado no laço."""
        if self._worker is not None:
            self._worker.parar()

    def enviar_comando(self, comando: str) -> bool:
        if self._worker is None or not self.link_ativo:
            return False
        self._worker.enviar_comando(comando)
        return True

    def atualizar_fator_potencia(self, fp: float):
        if self._worker is not None:
            self._worker.fator_potencia = fp      # atribuição simples, atômica no Python

    def aguardar(self, ms: int) -> bool:
        return self._thread.wait(ms) if self._thread is not None else True

    # ------------------------------------------------------------------
    def _ao_mudar_estado(self, estado: str, detalhe: str):
        self.link_ativo = estado == "TELEMETRIA"
        self.estado_mudou.emit(estado, detalhe)

    def _ao_terminar_thread(self):
        log.info("SerialThread finalizada")
        self._thread = None
        self._worker = None
        self.link_ativo = False
        self.conexao_encerrada.emit()
