import datetime

class SistemaModel:
    def __init__(self):
        self.setpoint_tensao = 0.0
        self.setpoint_corrente = 0.0
        self.tensao_atual = 0.0
        self.corrente_atual = 0.0
        self.disjuntor_ligado = False
        
        self.lista_logs = []

    def registrar_log(self, tipo, mensagem):
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        novo_log = {
            "data": agora,
            "tipo": tipo,
            "mensagem": mensagem
        }
        self.lista_logs.append(novo_log)
        print(f"[{agora}] {tipo}: {mensagem}")

    def calcular_potencia(self):
        return self.tensao_atual * self.corrente_atual