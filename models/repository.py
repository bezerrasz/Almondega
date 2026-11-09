"""
Persistência SQLite (smartgrid.db).

Esta classe NÃO é thread-safe de propósito: cada instância é criada e usada
somente dentro da thread do DbWorker, que é dona da conexão.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from models.caminhos import DB_PATH
from models.entidades import Evento, LeituraTelemetria

FORMATO_TS = "%Y-%m-%d %H:%M:%S.%f"


def _ts(dt: datetime) -> str:
    return dt.strftime(FORMATO_TS)[:-3]   # milissegundos


def _limite_inf(dt: datetime | None) -> str:
    return _ts(dt) if dt else "0000-01-01 00:00:00.000"


def _limite_sup(dt: datetime | None) -> str:
    return _ts(dt) if dt else "9999-12-31 23:59:59.999"


def _dt(texto: str) -> datetime:
    for fmt in (FORMATO_TS, "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    raise ValueError(f"timestamp inválido: {texto}")


class SmartGridRepository:
    def __init__(self, caminho: str | Path = DB_PATH):
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(caminho), timeout=5.0)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")   # leitura não bloqueia escrita
        self._ids_dispositivo: dict[str, int] = {}
        self.inicializar_esquema()

    def fechar(self):
        try:
            self.conn.commit()
        finally:
            self.conn.close()

    # ------------------------------------------------------------------
    def inicializar_esquema(self):
        with self.conn:   # transação: commit no sucesso, rollback em exceção
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS dispositivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('ABERTO', 'FECHADO')),
                    ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )""")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    seq INTEGER,
                    tensao REAL NOT NULL,
                    corrente REAL NOT NULL,
                    potencia REAL NOT NULL,
                    disjuntor_fechado INTEGER NOT NULL,
                    dispositivo_id INTEGER NOT NULL REFERENCES dispositivos(id)
                )""")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_leituras_ts ON leituras(timestamp)")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS historico_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo_evento TEXT NOT NULL,
                    valor_medido REAL,
                    descricao TEXT,
                    dispositivo_id INTEGER,
                    leitura_id INTEGER REFERENCES leituras(id),
                    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos (id)
                )""")
            self._migrar_versao_anterior()
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_eventos_ts ON historico_eventos(data_hora)")
            self.conn.execute("""
                INSERT OR IGNORE INTO dispositivos (id, tag, tipo, status)
                VALUES (1, 'DJ-PRINCIPAL', 'DISJUNTOR', 'FECHADO')""")

    def _migrar_versao_anterior(self):
        """Bancos da A1/1: sem coluna leitura_id e datas em dd/mm/aaaa."""
        colunas = {r[1] for r in self.conn.execute("PRAGMA table_info(historico_eventos)")}
        if "leitura_id" not in colunas:
            self.conn.execute("ALTER TABLE historico_eventos ADD COLUMN leitura_id INTEGER REFERENCES leituras(id)")
        self.conn.execute("""
            UPDATE historico_eventos
               SET data_hora = substr(data_hora, 7, 4) || '-' || substr(data_hora, 4, 2) || '-' ||
                               substr(data_hora, 1, 2) || substr(data_hora, 11)
             WHERE data_hora LIKE '__/__/____%'""")

    def _id_dispositivo(self, tag: str) -> int:
        if tag not in self._ids_dispositivo:
            linha = self.conn.execute("SELECT id FROM dispositivos WHERE tag = ?", (tag,)).fetchone()
            if linha is None:
                cur = self.conn.execute(
                    "INSERT INTO dispositivos (tag, tipo, status) VALUES (?, 'DISJUNTOR', 'FECHADO')", (tag,))
                self._ids_dispositivo[tag] = cur.lastrowid
            else:
                self._ids_dispositivo[tag] = linha[0]
        return self._ids_dispositivo[tag]

    # ------------------------------------------------------------------
    def inserir_leitura(self, leitura: LeituraTelemetria, tag: str = "DJ-PRINCIPAL") -> int:
        with self.conn:
            cur = self.conn.execute(
                """INSERT INTO leituras (timestamp, seq, tensao, corrente, potencia,
                                         disjuntor_fechado, dispositivo_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (_ts(leitura.timestamp), leitura.seq, leitura.tensao, leitura.corrente,
                 leitura.potencia, int(leitura.disjuntor_fechado), self._id_dispositivo(tag)))
            return cur.lastrowid

    def ultima_leitura_id(self) -> int | None:
        linha = self.conn.execute("SELECT MAX(id) FROM leituras").fetchone()
        return linha[0] if linha else None

    def registrar_evento(self, evento: Evento, novo_status_disjuntor: str | None = None,
                         leitura_id: int | None = None) -> int:
        """
        Grava o evento e, se for um chaveamento, atualiza o status do disjuntor
        na MESMA transação (ACID: ou grava os dois, ou nenhum).
        """
        disp_id = self._id_dispositivo(evento.dispositivo_tag)
        with self.conn:
            if novo_status_disjuntor is not None:
                self.conn.execute(
                    "UPDATE dispositivos SET status = ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = ?",
                    (novo_status_disjuntor, disp_id))
            cur = self.conn.execute(
                """INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao,
                                                  dispositivo_id, leitura_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (_ts(evento.timestamp), evento.tipo, evento.valor_medido, evento.descricao,
                 disp_id, leitura_id))
            return cur.lastrowid

    # ------------------------------------------------------------------
    def consultar_leituras(self, inicio: datetime | None = None, fim: datetime | None = None,
                           ultimas: int | None = None) -> list[LeituraTelemetria]:
        if ultimas:
            linhas = self.conn.execute(
                """SELECT * FROM (
                       SELECT timestamp, seq, tensao, corrente, potencia, disjuntor_fechado
                         FROM leituras ORDER BY id DESC LIMIT ?
                   ) ORDER BY timestamp""", (int(ultimas),)).fetchall()
        else:
            linhas = self.conn.execute(
                """SELECT timestamp, seq, tensao, corrente, potencia, disjuntor_fechado
                     FROM leituras WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp""",
                (_limite_inf(inicio), _limite_sup(fim))).fetchall()
        return [LeituraTelemetria(tensao=v, corrente=i, potencia=p, timestamp=_dt(ts),
                                  seq=seq or 0, disjuntor_fechado=bool(dj))
                for ts, seq, v, i, p, dj in linhas]

    def consultar_eventos(self, inicio: datetime | None = None, fim: datetime | None = None,
                          limite: int = 2000) -> list[Evento]:
        linhas = self.conn.execute(
            """SELECT e.data_hora, e.tipo_evento, e.descricao, e.valor_medido, COALESCE(d.tag, '-')
                 FROM historico_eventos e LEFT JOIN dispositivos d ON d.id = e.dispositivo_id
                WHERE e.data_hora BETWEEN ? AND ?
                ORDER BY e.data_hora DESC LIMIT ?""",
            (_limite_inf(inicio), _limite_sup(fim), limite)).fetchall()
        eventos = []
        for ts, tipo, desc, valor, tag in linhas:
            try:
                quando = _dt(ts)
            except (ValueError, TypeError):
                continue
            eventos.append(Evento(tipo=tipo, descricao=desc or "", valor_medido=valor,
                                  timestamp=quando, dispositivo_tag=tag))
        return eventos
