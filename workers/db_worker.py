"""
DbWorker: dono exclusivo da conexão SQLite, vive numa QThread dedicada.

Diferente do SerialWorker, não tem laço bloqueante: usa o event loop da própria
thread. Cada pedido chega como sinal enfileirado (Qt.QueuedConnection automática,
porque o emissor está na thread da GUI) e é executado aqui, em segundo plano.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from models.regras import reduzir_pontos
from models.repository import SmartGridRepository

log = logging.getLogger(__name__)

MAX_PONTOS_GRAFICO = 5000


class DbWorker(QObject):
    pronto = Signal()
    erro = Signal(str)
    historico_pronto = Signal(int, object, int)   # id do pedido, leituras, total no banco
    eventos_prontos = Signal(int, object)         # id do pedido, eventos
    evento_gravado = Signal(object)               # Evento
    encerrado = Signal()

    def __init__(self, caminho_db: str | Path):
        super().__init__()
        self.caminho_db = caminho_db
        self.repo: SmartGridRepository | None = None
        self._ultima_leitura_id: int | None = None
        self._gravadas = 0

    @Slot()
    def iniciar(self):
        try:
            self.repo = SmartGridRepository(self.caminho_db)
            self._ultima_leitura_id = self.repo.ultima_leitura_id()
            log.info("SQLite aberto em %s (thread do banco)", self.caminho_db)
            self.pronto.emit()
        except sqlite3.Error as e:
            log.exception("falha ao abrir o banco")
            self.erro.emit(f"Não foi possível abrir o banco: {e}")

    @Slot(object)
    def gravar_leitura(self, leitura):
        if not self.repo:
            return
        try:
            self._ultima_leitura_id = self.repo.inserir_leitura(leitura)
            self._gravadas += 1
        except sqlite3.Error as e:
            log.error("falha ao gravar leitura: %s", e)
            self.erro.emit(f"Falha ao gravar leitura: {e}")

    @Slot(object, object)
    def registrar_evento(self, evento, novo_status_disjuntor):
        if not self.repo:
            return
        try:
            self.repo.registrar_evento(evento, novo_status_disjuntor, self._ultima_leitura_id)
            self.evento_gravado.emit(evento)
        except sqlite3.Error as e:
            log.error("falha ao gravar evento (rollback): %s", e)
            self.erro.emit(f"Falha ao gravar evento (transação desfeita): {e}")

    @Slot(int, object)
    def consultar_historico(self, pedido_id: int, filtro: dict):
        if not self.repo:
            return
        try:
            if filtro.get("modo") == "ultimas":
                leituras = self.repo.consultar_leituras(ultimas=filtro["quantidade"])
            else:
                leituras = self.repo.consultar_leituras(filtro["inicio"], filtro["fim"])
            total = len(leituras)
            self.historico_pronto.emit(pedido_id, reduzir_pontos(leituras, MAX_PONTOS_GRAFICO), total)
        except (sqlite3.Error, KeyError, ValueError) as e:
            log.error("falha na consulta de histórico: %s", e)
            self.erro.emit(f"Falha na consulta de histórico: {e}")
            self.historico_pronto.emit(pedido_id, [], 0)

    @Slot(int, object)
    def consultar_eventos(self, pedido_id: int, filtro: dict):
        if not self.repo:
            return
        try:
            eventos = self.repo.consultar_eventos(filtro.get("inicio"), filtro.get("fim"))
            self.eventos_prontos.emit(pedido_id, eventos)
        except sqlite3.Error as e:
            self.erro.emit(f"Falha na consulta de eventos: {e}")
            self.eventos_prontos.emit(pedido_id, [])

    @Slot()
    def encerrar(self):
        """Fecha a conexão e encerra o event loop desta thread (cooperativo)."""
        try:
            if self.repo:
                self.repo.fechar()
                log.info("SQLite fechado (%d leituras gravadas nesta sessão)", self._gravadas)
        except sqlite3.Error as e:
            log.error("erro ao fechar banco: %s", e)
        finally:
            self.repo = None
            self.encerrado.emit()
            QThread.currentThread().quit()
