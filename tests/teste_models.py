"""
Testes da camada Model (Python puro, rodam sem interface e sem placa).

    python -m unittest discover -s tests -p "teste_models.py" -v
"""
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import protocolo  # noqa: E402
from models.config_manager import ConfigManager  # noqa: E402
from models.entidades import Evento, LeituraTelemetria, TipoEvento  # noqa: E402
from models.regras import Limites, MonitorLimites, reduzir_pontos  # noqa: E402
from models.repository import SmartGridRepository  # noqa: E402


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


class TesteRegras(unittest.TestCase):
    def setUp(self):
        self.mon = MonitorLimites(Limites(tensao_max=240, tensao_min=200, corrente_max=30))

    def test_potencia(self):
        self.assertAlmostEqual(LeituraTelemetria.criar(220, 10, 0.9).potencia, 1980.0)

    def test_sobrecorrente_dispara_uma_vez(self):
        alta = LeituraTelemetria.criar(220, 35)
        self.assertEqual([v.tipo_evento for v in self.mon.avaliar(alta)], [TipoEvento.CORTE_SOBRECORRENTE])
        self.assertEqual(self.mon.avaliar(alta), [])                      # persiste: não repete
        self.mon.avaliar(LeituraTelemetria.criar(220, 0))                 # normalizou
        self.assertEqual(len(self.mon.avaliar(alta)), 1)                  # nova ocorrência

    def test_subtensao_so_alerta(self):
        v = self.mon.avaliar(LeituraTelemetria.criar(190, 10))[0]
        self.assertFalse(v.exige_corte)

    def test_reduzir_pontos(self):
        self.assertEqual(len(reduzir_pontos(list(range(10000)), 500)), 500)
        self.assertEqual(reduzir_pontos([1, 2], 500), [1, 2])


class TesteConfig(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.caminho = Path(self.dir.name) / "config.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_recria_se_apagado(self):
        cfg = ConfigManager(self.caminho)
        self.caminho.unlink()
        self.assertEqual(cfg.carregar(), ConfigManager.DEFAULT_CONFIG)
        self.assertTrue(self.caminho.exists())

    def test_corrompido(self):
        self.caminho.write_text("{ isso não é json", encoding="utf-8")
        self.assertEqual(ConfigManager(self.caminho).carregar(), ConfigManager.DEFAULT_CONFIG)
        self.assertTrue(self.caminho.with_suffix(".json.corrompido").exists())

    def test_valor_invalido_vira_padrao(self):
        self.caminho.write_text(json.dumps({"baud_rate": 57600, "limite_corrente_max": -5}), encoding="utf-8")
        c = ConfigManager(self.caminho).carregar()
        self.assertEqual(c["baud_rate"], 115200)
        self.assertEqual(c["limite_corrente_max"], 30.0)

    def test_salvar_rejeita_invalido(self):
        cfg = ConfigManager(self.caminho)
        with self.assertRaises(ValueError):
            cfg.salvar({"limite_tensao_min": 250, "limite_tensao_max": 240})
        with self.assertRaises(ValueError):
            cfg.salvar({"baud_rate": 57600})


class TesteRepositorio(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = SmartGridRepository(Path(self.dir.name) / "t.db")

    def tearDown(self):
        self.repo.fechar()
        self.dir.cleanup()

    def test_leituras_e_filtros(self):
        base = datetime(2026, 11, 9, 10, 0, 0)
        for k in range(100):
            self.repo.inserir_leitura(LeituraTelemetria.criar(220, 10, timestamp=base + timedelta(seconds=k)))
        self.assertEqual(len(self.repo.consultar_leituras(ultimas=10)), 10)
        intervalo = self.repo.consultar_leituras(base + timedelta(seconds=10), base + timedelta(seconds=19))
        self.assertEqual(len(intervalo), 10)
        self.assertLess(intervalo[0].timestamp, intervalo[-1].timestamp)

    def test_evento_atualiza_status_na_mesma_transacao(self):
        lid = self.repo.inserir_leitura(LeituraTelemetria.criar(220, 35))
        self.repo.registrar_evento(Evento(TipoEvento.CORTE_SOBRECORRENTE, "teste", 35), "ABERTO", lid)
        status = self.repo.conn.execute("SELECT status FROM dispositivos WHERE id=1").fetchone()[0]
        self.assertEqual(status, "ABERTO")
        self.assertEqual(self.repo.consultar_eventos()[0].tipo, TipoEvento.CORTE_SOBRECORRENTE)

    def test_rollback(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.registrar_evento(Evento(TipoEvento.CORTE_EMERGENCIAL, "x"), "STATUS_INVALIDO")
        self.assertEqual(self.repo.consultar_eventos(), [])   # nada gravado


if __name__ == "__main__":
    unittest.main(verbosity=2)
