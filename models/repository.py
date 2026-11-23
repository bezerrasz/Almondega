from database.connection import Database
import datetime

class EventoRepository:
    
    @staticmethod
    def registrar_evento(tipo, mensagem, valor_medido=0.0, dispositivo_id=1):
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao, dispositivo_id)
                VALUES (?, ?, ?, ?, ?)
            """, (agora, tipo, valor_medido, mensagem, dispositivo_id))
            conn.commit()

    @staticmethod
    def listar_todos():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data_hora, tipo_evento, descricao 
                FROM historico_eventos 
                ORDER BY id DESC
            """)
            return cursor.fetchall()
        
    @staticmethod
    def executar_corte_emergencial(tipo_evento, mensagem, valor_medido, simular_falha=False):
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE dispositivos 
                SET status = 'ABERTO', ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE tag = 'DJ-PRINCIPAL'
            """)
            
            if simular_falha:
                raise RuntimeError("Conexão perdida no meio da operação!")
            
            cursor.execute("""
                INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao, dispositivo_id)
                VALUES (?, ?, ?, ?, 1)
            """, (agora, tipo_evento, valor_medido, mensagem))
            

    # ------------------------------------------------------------------
    # A1/5: acréscimos (o que está acima continua como era)
    # ------------------------------------------------------------------
    @staticmethod
    def registrar_chaveamento(novo_status, tipo_evento, mensagem, valor_medido=0.0):
        """
        Atuação de chaveamento (abrir/fechar o disjuntor): atualiza o status do
        dispositivo e grava o evento na MESMA transação (ACID: os dois ou nenhum).
        """
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE dispositivos
                SET status = ?, ultima_atualizacao = CURRENT_TIMESTAMP
                WHERE tag = 'DJ-PRINCIPAL'
            """, (novo_status,))
            cursor.execute("""
                INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao, dispositivo_id)
                VALUES (?, ?, ?, ?, 1)
            """, (agora, tipo_evento, valor_medido, mensagem))

    @staticmethod
    def salvar_regras(limite_corrente, tensao_desarme):
        """Grava os limites na tabela regras_limites (linha única, id = 1)."""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO regras_limites (id, limite_corrente, tensao_desarme)
                VALUES (1, ?, ?)
            """, (limite_corrente, tensao_desarme))
            conn.commit()


FORMATO_TS = "%Y-%m-%d %H:%M:%S.%f"


def _ts(dt):
    return dt.strftime(FORMATO_TS)[:-3]          # milissegundos


class LeituraRepository:
    """
    Histórico de telemetria (tabela leituras).

    Mantém UMA conexão aberta durante a vida da thread do banco (gravar uma leitura
    por amostra abrindo e fechando conexão seria desperdício). Por isso cada instância
    deve ser criada e usada somente dentro da thread do DbWorker.
    """

    def __init__(self):
        self.conn = Database.get_connection()

    def fechar(self):
        try:
            self.conn.commit()
        finally:
            self.conn.close()

    def inserir(self, leitura):
        with self.conn:      # transação: commit no sucesso, rollback em exceção
            cur = self.conn.execute("""
                INSERT INTO leituras (timestamp, seq, tensao, corrente, potencia,
                                      disjuntor_fechado, dispositivo_id)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (_ts(leitura.timestamp), leitura.seq, leitura.tensao, leitura.corrente,
                  leitura.potencia, int(leitura.disjuntor_fechado)))
            return cur.lastrowid

    def consultar(self, ultimas=None, inicio=None, fim=None):
        """Devolve (timestamp, tensao, corrente, potencia) em ordem cronológica."""
        if ultimas:
            linhas = self.conn.execute("""
                SELECT timestamp, tensao, corrente, potencia FROM (
                    SELECT id, timestamp, tensao, corrente, potencia
                    FROM leituras ORDER BY id DESC LIMIT ?
                ) ORDER BY id
            """, (int(ultimas),)).fetchall()
        else:
            linhas = self.conn.execute("""
                SELECT timestamp, tensao, corrente, potencia
                FROM leituras WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (_ts(inicio) if inicio else "0000-01-01 00:00:00.000",
                  _ts(fim) if fim else "9999-12-31 23:59:59.999")).fetchall()
        return [(datetime.datetime.strptime(t, FORMATO_TS), v, i, p) for t, v, i, p in linhas]

    def contar(self):
        return self.conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
