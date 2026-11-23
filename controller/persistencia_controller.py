"""Ciclo de vida da QThread de banco e fachada assíncrona para os pedidos."""
from __future__ import annotations

import itertools
import logging

from PySide6.QtCore import QObject, QThread, Signal

from workers.db_worker import DbWorker

log = logging.getLogger(__name__)


class PersistenciaController(QObject):
    # pedidos -> worker (emitidos na GUI, executados na thread do banco)
    _pedir_leitura = Signal(object)
    _pedir_evento = Signal(str, str, float)
    _pedir_chaveamento = Signal(str, str, str, float)
    _pedir_corte = Signal(str, str, float)
    _pedir_regras = Signal(float, float)
    _pedir_historico = Signal(int, object)
    _pedir_eventos = Signal(int, object)
    _pedir_encerramento = Signal()

    # respostas -> controllers
    pronto = Signal()
    historico_pronto = Signal(int, object, int)
    eventos_prontos = Signal(int, object)
    corte_concluido = Signal(bool, str)
    erro = Signal(str)
    finalizado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ids = itertools.count(1)
        self._thread: QThread | None = None
        self._worker: DbWorker | None = None

    @property
    def ativo(self) -> bool:
        return self._thread is not None

    def iniciar(self):
        self._thread = QThread()
        self._thread.setObjectName("DatabaseThread")
        self._worker = DbWorker()
        self._worker.moveToThread(self._thread)
        w = self._worker

        self._thread.started.connect(w.iniciar)
        self._pedir_leitura.connect(w.gravar_leitura)
        self._pedir_evento.connect(w.registrar_evento)
        self._pedir_chaveamento.connect(w.registrar_chaveamento)
        self._pedir_corte.connect(w.corte_emergencial)
        self._pedir_regras.connect(w.salvar_regras)
        self._pedir_historico.connect(w.consultar_historico)
        self._pedir_eventos.connect(w.consultar_eventos)
        self._pedir_encerramento.connect(w.encerrar)

        w.pronto.connect(self.pronto)
        w.historico_pronto.connect(self.historico_pronto)
        w.eventos_prontos.connect(self.eventos_prontos)
        w.corte_concluido.connect(self.corte_concluido)
        w.erro.connect(self.erro)

        self._thread.finished.connect(w.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._ao_terminar_thread)
        self._thread.start()

    # ---------------- API assíncrona ----------------
    def gravar_leitura(self, leitura):
        self._pedir_leitura.emit(leitura)

    def registrar_evento(self, tipo: str, mensagem: str, valor: float = 0.0):
        self._pedir_evento.emit(tipo, mensagem, float(valor or 0.0))

    def registrar_chaveamento(self, novo_status: str, tipo: str, mensagem: str, valor: float = 0.0):
        self._pedir_chaveamento.emit(novo_status, tipo, mensagem, float(valor or 0.0))

    def corte_emergencial(self, tipo: str, mensagem: str, valor: float = 0.0):
        self._pedir_corte.emit(tipo, mensagem, float(valor or 0.0))

    def salvar_regras(self, limite_corrente: float, tensao_desarme: float):
        self._pedir_regras.emit(float(limite_corrente), float(tensao_desarme))

    def consultar_historico(self, filtro: dict) -> int:
        pedido = next(self._ids)
        self._pedir_historico.emit(pedido, filtro)
        return pedido

    def consultar_eventos(self) -> int:
        pedido = next(self._ids)
        self._pedir_eventos.emit(pedido, None)
        return pedido

    def encerrar(self):
        """Enfileira o encerramento DEPOIS dos pedidos pendentes (ordem garantida)."""
        if self.ativo:
            self._pedir_encerramento.emit()
        else:
            self.finalizado.emit()

    def aguardar(self, ms: int) -> bool:
        return self._thread.wait(ms) if self._thread is not None else True

    def _ao_terminar_thread(self):
        log.info("DatabaseThread finalizada")
        self._thread = None
        self._worker = None
        self.finalizado.emit()
