"""
DbWorker: dono exclusivo das operações no SQLite, vive numa QThread dedicada.

Diferente do SerialWorker, não tem laço bloqueante: usa o event loop da própria
thread. Cada pedido chega como sinal enfileirado (Qt.QueuedConnection automática,
porque o emissor está na thread da GUI) e é executado aqui, em segundo plano.
Quem fala SQL é o Model (EventoRepository e LeituraRepository); este worker só decide
em qual thread isso roda e devolve os resultados por sinal.
"""
from __future__ import annotations

import logging
import sqlite3

from PySide6.QtCore import QObject, QThread, Signal, Slot

from database.connection import Database
from models.repository import EventoRepository, LeituraRepository

log = logging.getLogger(__name__)

MAX_PONTOS_GRAFICO = 5000


def reduzir_pontos(itens: list, maximo: int) -> list:
    """Decimação simples para plotar consultas grandes sem pesar a interface."""
    if maximo <= 0 or len(itens) <= maximo:
        return itens
    passo = len(itens) / maximo
    return [itens[int(k * passo)] for k in range(maximo)]


class DbWorker(QObject):
    pronto = Signal()
    erro = Signal(str)
    historico_pronto = Signal(int, object, int)   # id do pedido, [(datetime, V, A, W)], total no banco
    eventos_prontos = Signal(int, object)         # id do pedido, linhas (data_hora, tipo, descricao)
    corte_concluido = Signal(bool, str)           # ok, motivo da falha (transação desfeita)
    encerrado = Signal()

    def __init__(self):
        super().__init__()
        self.leituras: LeituraRepository | None = None
        self._gravadas = 0

    @Slot()
    def iniciar(self):
        try:
            Database.init_db()                    # cria as tabelas se não existirem
            self.leituras = LeituraRepository()   # conexão própria desta thread
            log.info("SQLite aberto em %s (thread do banco)", Database.DB_PATH)
            self.pronto.emit()
        except sqlite3.Error as e:
            log.exception("falha ao abrir o banco")
            self.erro.emit(f"Não foi possível abrir o banco: {e}")

    # ---------------- gravações ----------------
    @Slot(object)
    def gravar_leitura(self, leitura):
        if not self.leituras:
            return
        try:
            self.leituras.inserir(leitura)
            self._gravadas += 1
        except sqlite3.Error as e:
            log.error("falha ao gravar leitura: %s", e)
            self.erro.emit(f"Falha ao gravar leitura: {e}")

    @Slot(str, str, float)
    def registrar_evento(self, tipo, mensagem, valor):
        try:
            EventoRepository.registrar_evento(tipo, mensagem, valor)
        except sqlite3.Error as e:
            log.error("falha ao gravar evento: %s", e)
            self.erro.emit(f"Falha ao gravar evento: {e}")

    @Slot(str, str, str, float)
    def registrar_chaveamento(self, novo_status, tipo, mensagem, valor):
        try:
            EventoRepository.registrar_chaveamento(novo_status, tipo, mensagem, valor)
        except sqlite3.Error as e:
            log.error("falha ao gravar chaveamento (rollback): %s", e)
            self.erro.emit(f"Falha ao gravar o chaveamento (transação desfeita): {e}")

    @Slot(str, str, float)
    def corte_emergencial(self, tipo, mensagem, valor):
        """Status do disjuntor + evento na mesma transação (ACID), como já era."""
        try:
            EventoRepository.executar_corte_emergencial(tipo, mensagem, valor, simular_falha=False)
            self.corte_concluido.emit(True, "")
        except Exception as e:      # rollback já feito pelo context manager da conexão
            log.error("falha no corte emergencial (rollback): %s", e)
            self.corte_concluido.emit(False, str(e))

    @Slot(float, float)
    def salvar_regras(self, limite_corrente, tensao_desarme):
        try:
            EventoRepository.salvar_regras(limite_corrente, tensao_desarme)
        except sqlite3.Error as e:
            log.error("falha ao salvar regras: %s", e)
            self.erro.emit(f"Falha ao salvar os limites no banco: {e}")

    # ---------------- consultas ----------------
    @Slot(int, object)
    def consultar_historico(self, pedido_id: int, filtro: dict):
        if not self.leituras:
            return
        try:
            if filtro.get("modo") == "ultimas":
                dados = self.leituras.consultar(ultimas=filtro["quantidade"])
            else:
                dados = self.leituras.consultar(inicio=filtro["inicio"], fim=filtro["fim"])
            self.historico_pronto.emit(pedido_id, reduzir_pontos(dados, MAX_PONTOS_GRAFICO), len(dados))
        except (sqlite3.Error, KeyError, ValueError) as e:
            log.error("falha na consulta de histórico: %s", e)
            self.erro.emit(f"Falha na consulta de histórico: {e}")
            self.historico_pronto.emit(pedido_id, [], 0)

    @Slot(int, object)
    def consultar_eventos(self, pedido_id: int, _filtro=None):
        try:
            linhas = EventoRepository.listar_todos()
            self.eventos_prontos.emit(pedido_id, linhas)
        except sqlite3.Error as e:
            self.erro.emit(f"Falha na consulta de eventos: {e}")
            self.eventos_prontos.emit(pedido_id, [])

    # ---------------- encerramento ----------------
    @Slot()
    def encerrar(self):
        """Fecha a conexão e encerra o event loop desta thread (cooperativo)."""
        try:
            if self.leituras:
                self.leituras.fechar()
                log.info("SQLite fechado (%d leituras gravadas nesta sessão)", self._gravadas)
        except sqlite3.Error as e:
            log.error("erro ao fechar banco: %s", e)
        finally:
            self.leituras = None
            self.encerrado.emit()
            QThread.currentThread().quit()
