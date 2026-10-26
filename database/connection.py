import sqlite3
import os
import logging

class Database:
    DB_PATH = os.path.join("data", "smartgrid.db")

    @classmethod
    def get_connection(cls):
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, timeout=5.0)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @classmethod
    def init_db(cls):
        with cls.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Tabela de Dispositivos / Atuadores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dispositivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('ABERTO', 'FECHADO')),
                    ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Tabela de Regras / Limites
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regras_limites (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    limite_corrente REAL NOT NULL,
                    tensao_desarme REAL NOT NULL
                );
            """)

            # 3. Tabela de Histórico de Eventos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tipo_evento TEXT NOT NULL,
                    valor_medido REAL,
                    descricao TEXT,
                    dispositivo_id INTEGER,
                    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos (id)
                );
            """)

            # Inserir o disjuntor padrão para garantir que exista
            cursor.execute("""
                INSERT OR IGNORE INTO dispositivos (id, tag, tipo, status)
                VALUES (1, 'DJ-PRINCIPAL', 'DISJUNTOR', 'FECHADO');
            """)
            
            conn.commit()
            
            # ADICIONE ESTA LINHA AQUI:
            logging.info("Conexão com SQLite estabelecida e esquema validado.")