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
            