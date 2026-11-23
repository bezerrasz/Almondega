import json
import os

 #Configuração padrão do arquivo JSON para armazenar inicialmente as configurações do sistema
class ConfigManager:
    DEFAULT_CONFIG = {
        "porta_serial" : "COM1",
        "baud_rate" : 9600,
        "limite_tensao" : 220.0,
        "limite_corrente" : 30.0,
        "taxa_amostragem_ms" : 1000,   # A1/5: período da telemetria pedido à placa no handshake
        "timeout_s" : 2                # A1/5: tempo de espera pelo ACK da placa
    }
    #Construtor da classe ConfigManager, que inicializa o gerenciador de configuração com o nome e diretório do arquivo JSON
    def __init__(self, filename: str = "data/config.json"):
        self.filename = filename
        self._carregar_ou_criar_config()



    def _carregar_ou_criar_config(self):
        #Verificar existência do arquvio de configuração e criar um novo se não existir
        if not os.path.exists(self.filename):
            self.salvar(self.DEFAULT_CONFIG)


    def existe(self) -> bool:
        return os.path.exists(self.filename)

    def caminho_pasta(self) -> str:
        return os.path.dirname(os.path.abspath(self.filename))

    def carregar(self) -> dict:
        #Carregar as configuração do JSON try/except para lidar com erros de leitura
        #A1/5: se o arquivo foi apagado (mesmo com o programa aberto) ele é recriado aqui
        self._carregar_ou_criar_config()
        try:
            with open(self.filename, "r", encoding = "utf-8") as f:
                config = json.load(f)
            if not isinstance(config, dict):
                raise ValueError("a raiz do JSON não é um objeto")
        except (FileNotFoundError, ValueError):     # JSONDecodeError herda de ValueError
            self.salvar(self.DEFAULT_CONFIG)        # arquivo corrompido: recria com os padrões
            return self.DEFAULT_CONFIG.copy()
        # completa chaves que faltam (config.json de versões anteriores)
        for chave, padrao in self.DEFAULT_CONFIG.items():
            config.setdefault(chave, padrao)
        return config

    def salvar(self, config_data : dict):
        #Salvar as configurações no arquivo JSON
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)
        with open(self.filename, "w", encoding = "utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
