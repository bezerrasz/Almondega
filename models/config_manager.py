import json
import os

class ConfigManager:
    DEFAULT_CONFIG = {
        "porta_serial" : "COM1",
        "baud_rate" : 9600,
        "limite_tensao" : 220.0,
        "limite_corrente" : 30.0
    }

    def __init__(self, filename: str = "data/config.json"):
        self.filename = filename
        self._carregar_ou_criar_config()



    def _carregar_ou_criar_config(self):
        "Verificar existência do arquvio de configuração e criar um novo se não existir"
        if not os.path.exists(self.filename):
            self.salvar(self.DEFAULT_CONFIG)


    def carregar(self) -> dict:
        "Carregar as configuração do JSON try/except para lidar com erros de leitura"
        try:
            with open(self.filename, "r", encoding = "utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_CONFIG.copy()

    def salvar(self, config_data : dict):
        "Salvar as configurações no arquivo JSON"
        with open(self.filename, "w", encoding = "utf-8") as f:
            json.dump(config_data, f, ident=4, ensure_ascii=False)
