"""
Testes da camada Model (Python puro, rodam sem interface e sem placa).

    python -m unittest discover -s tests -p "teste_models.py" -v
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.connection import Database  # noqa: E402
from models import protocolo  # noqa: E402
from models.config_manager import ConfigManager  # noqa: E402
from models.entidades import LeituraTelemetria  # noqa: E402
from models.repository import EventoRepository, LeituraRepository  # noqa: E402
from models.sistema_model import SistemaModel  # noqa: E402


class TesteProtocolo(unittest.TestCase):
    def test_data_valido(self):
        corpo = "DATA,7,220.10,10.50,1"
        msg = protocolo.interpretar_linha(f"{corpo}*{protocolo.checksum(corpo)}")
        d = protocolo.decodificar_telemetria(msg)
        self.assertEqual((d.seq, d.tensao, d.corrente, d.disjuntor_fechado), (7, 220.10, 10.50, True))

    def test_checksum_errado(self):
        with self.assertRaises(protocolo.PacoteInvalido):
            protocolo.interpretar_linha("DATA,7,220.10,10.50,1*00")

    def test_lixo(self):
        for linha in ("", "xyz", "DATA,1,2", "DATA,a,b,c,d*" + protocolo.checksum("DATA,a,b,c,d")):
            with self.assertRaises(protocolo.PacoteInvalido):
                protocolo.decodificar_telemetria(protocolo.interpretar_linha(linha))

    def test_sequencia_comeca_pela_alvo_e_termina_em_9600(self):
        self.assertEqual(protocolo.sequencia_negociacao(115200), [115200, 38400, 19200, 9600])
        self.assertEqual(protocolo.sequencia_negociacao(9600), [9600])
        self.assertEqual(protocolo.sequencia_negociacao(57600), [9600])   # não suportado


class TesteConfig(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.caminho = Path(self.dir.name) / "data" / "config.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_cria_se_nao_existe(self):
        cfg = ConfigManager(str(self.caminho))
        self.assertTrue(self.caminho.exists())
        self.assertEqual(cfg.carregar(), ConfigManager.DEFAULT_CONFIG)

    def test_recria_se_apagado_com_o_app_aberto(self):
        cfg = ConfigManager(str(self.caminho))
        self.caminho.unlink()
        self.assertEqual(cfg.carregar(), ConfigManager.DEFAULT_CONFIG)
        self.assertTrue(self.caminho.exists())

    def test_corrompido_e_recriado(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text("{ isso não é json", encoding="utf-8")
        self.assertEqual(ConfigManager(str(self.caminho)).carregar(), ConfigManager.DEFAULT_CONFIG)
        self.assertEqual(json.loads(self.caminho.read_text(encoding="utf-8")), ConfigManager.DEFAULT_CONFIG)

    def test_config_antigo_sem_as_chaves_novas_e_completado(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text(json.dumps({"porta_serial": "COM7", "baud_rate": 19200,
                                            "limite_tensao": 220.0, "limite_corrente": 30.0}), encoding="utf-8")
        c = ConfigManager(str(self.caminho)).carregar()
        self.assertEqual(c["porta_serial"], "COM7")
        self.assertEqual(c["taxa_amostragem_ms"], 1000)
        self.assertEqual(c["timeout_s"], 2)

    def test_salvar_e_ler(self):
        cfg = ConfigManager(str(self.caminho))
        dados = cfg.carregar()
        dados.update({"baud_rate": 115200, "limite_tensao": 230.0})
        cfg.salvar(dados)
        self.assertEqual(ConfigManager(str(self.caminho)).carregar()["baud_rate"], 115200)


class TesteSistemaModel(unittest.TestCase):
    def test_log_vai_para_o_callback_da_thread_do_banco(self):
        recebidos = []
        m = SistemaModel(persistir=lambda tipo, msg: recebidos.append((tipo, msg)))
        m.registrar_log("CONFIG", "teste")
        self.assertEqual(recebidos, [("CONFIG", "teste")])

    def test_potencia(self):
        m = SistemaModel()
        m.tensao_atual, m.corrente_atual = 220.0, 10.0
        self.assertEqual(m.calcular_potencia(), 2200.0)


class TesteBanco(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original = Database.DB_PATH
        Database.DB_PATH = str(Path(self.dir.name) / "t.db")
        Database.init_db()

    def tearDown(self):
        Database.DB_PATH = self.original
        self.dir.cleanup()

    def test_leituras_e_filtros(self):
        repo = LeituraRepository()
        base = datetime(2026, 11, 9, 10, 0, 0)
        for k in range(100):
            repo.inserir(LeituraTelemetria.criar(220, 10, timestamp=base + timedelta(seconds=k)))
        self.assertEqual(len(repo.consultar(ultimas=10)), 10)
        intervalo = repo.consultar(inicio=base + timedelta(seconds=10), fim=base + timedelta(seconds=19))
        self.assertEqual(len(intervalo), 10)
        self.assertLess(intervalo[0][0], intervalo[-1][0])
        self.assertEqual(repo.contar(), 100)
        repo.fechar()

    def _status(self):
        with Database.get_connection() as conn:
            return conn.execute("SELECT status FROM dispositivos WHERE id=1").fetchone()[0]

    def test_chaveamento_atualiza_status_e_evento_juntos(self):
        EventoRepository.registrar_chaveamento("ABERTO", "OPERAÇÃO", "Alavanca recuada", 5.0)
        self.assertEqual(self._status(), "ABERTO")
        self.assertEqual(EventoRepository.listar_todos()[0][1], "OPERAÇÃO")

    def test_corte_emergencial_faz_rollback_se_falhar(self):
        with self.assertRaises(RuntimeError):
            EventoRepository.executar_corte_emergencial("EMERGÊNCIA", "x", 1.0, simular_falha=True)
        self.assertEqual(self._status(), "FECHADO")          # o UPDATE foi desfeito
        self.assertEqual(EventoRepository.listar_todos(), [])  # e nenhum evento ficou

    def test_corte_emergencial_ok(self):
        EventoRepository.executar_corte_emergencial("EMERGÊNCIA", "parada", 12.0)
        self.assertEqual(self._status(), "ABERTO")
        self.assertEqual(len(EventoRepository.listar_todos()), 1)

    def test_regras_limites_insert_or_replace(self):
        EventoRepository.salvar_regras(30.0, 220.0)
        EventoRepository.salvar_regras(25.0, 230.0)
        with Database.get_connection() as conn:
            linhas = conn.execute("SELECT limite_corrente, tensao_desarme FROM regras_limites").fetchall()
        self.assertEqual(linhas, [(25.0, 230.0)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
