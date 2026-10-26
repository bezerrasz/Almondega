import datetime
import logging
from models.repository import EventoRepository

class SistemaModel:
    def __init__(self):
        self.setpoint_tensao = 0.0
        self.setpoint_corrente = 0.0
        self.tensao_atual = 0.0
        self.corrente_atual = 0.0
        self.disjuntor_ligado = False

    def registrar_log(self, tipo, mensagem):
        # 1. Salva no banco de dados SQLite (Para aparecer na QTableWidget)
        EventoRepository.registrar_evento(tipo, mensagem)
        
        # 2. Avalia a severidade para o ficheiro de auditoria (smartgrid.log)
        texto_log = f"{tipo}: {mensagem}"
        tipo_upper = tipo.upper()
        
        if "ERRO" in tipo_upper or "EMERGÊNCIA" in tipo_upper or "ERROR" in tipo_upper:
            logging.error(texto_log)
        elif "ALERTA" in tipo_upper or "SOBRECARGA" in tipo_upper or "PICO" in tipo_upper:
            logging.warning(texto_log)
        else:
            logging.info(texto_log)

    def calcular_potencia(self):
        return self.tensao_atual * self.corrente_atual