"""
Gestão resiliente do config.json.

- Se o arquivo não existir (inclusive apagado com o app aberto) ele é recriado
  com valores padrão seguros na próxima leitura.
- Se estiver corrompido, é renomeado para config.json.corrompido e recriado.
- Campos ausentes ou com valores inválidos são substituídos pelo padrão.
- A gravação é atômica (arquivo temporário + os.replace), então uma queda no meio
  da escrita não deixa um JSON pela metade.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from models.caminhos import CONFIG_PATH
from models.protocolo import BAUDS_SUPORTADOS
from models.regras import Limites

log = logging.getLogger(__name__)


class ConfigManager:
    DEFAULT_CONFIG = {
        "porta_serial": "COM3",
        "baud_rate": 115200,          # velocidade alvo da negociação
        "taxa_amostragem_ms": 1000,   # período da telemetria pedido no handshake
        "limite_tensao_max": 240.0,
        "limite_tensao_min": 200.0,
        "limite_corrente_max": 30.0,
        "fator_potencia": 1.0,
        "reconexao_automatica": True,
        "pontos_grafico_tempo_real": 120,
    }

    # chave -> função que valida e devolve o valor normalizado (ou levanta ValueError)
    _VALIDADORES = {
        "porta_serial": lambda v: _texto_nao_vazio(v),
        "baud_rate": lambda v: _em(int(v), BAUDS_SUPORTADOS),
        "taxa_amostragem_ms": lambda v: _faixa(int(v), 200, 5000),
        "limite_tensao_max": lambda v: _faixa(float(v), 1.0, 1000.0),
        "limite_tensao_min": lambda v: _faixa(float(v), 0.0, 1000.0),
        "limite_corrente_max": lambda v: _faixa(float(v), 0.1, 500.0),
        "fator_potencia": lambda v: _faixa(float(v), 0.0, 1.0),
        "reconexao_automatica": lambda v: _booleano(v),
        "pontos_grafico_tempo_real": lambda v: _faixa(int(v), 10, 2000),
    }

    def __init__(self, caminho: str | Path = CONFIG_PATH):
        self.caminho = Path(caminho)
        self.carregar()

    # ------------------------------------------------------------------
    def carregar(self) -> dict:
        if not self.caminho.exists():
            log.warning("config.json ausente: recriando com valores padrão em %s", self.caminho)
            self._gravar(self.DEFAULT_CONFIG)
            return dict(self.DEFAULT_CONFIG)

        try:
            with open(self.caminho, "r", encoding="utf-8") as f:
                bruto = json.load(f)
            if not isinstance(bruto, dict):
                raise ValueError("raiz do JSON não é um objeto")
        except (OSError, ValueError) as e:   # JSONDecodeError herda de ValueError
            log.error("config.json corrompido (%s): recriando", e)
            self._guardar_corrompido()
            self._gravar(self.DEFAULT_CONFIG)
            return dict(self.DEFAULT_CONFIG)

        config, corrigido = self._normalizar(bruto)
        if corrigido:
            self._gravar(config)
        return config

    def salvar(self, novos_valores: dict) -> dict:
        """Mescla, valida e grava. Levanta ValueError se algum valor for inválido."""
        atual = self.carregar()
        for chave, valor in novos_valores.items():
            if chave not in self._VALIDADORES:
                raise ValueError(f"parâmetro desconhecido: {chave}")
            try:
                atual[chave] = self._VALIDADORES[chave](valor)
            except (TypeError, ValueError) as e:
                raise ValueError(f"valor inválido para {chave}: {valor!r}") from e
        if atual["limite_tensao_min"] >= atual["limite_tensao_max"]:
            raise ValueError("a tensão mínima deve ser menor que a tensão máxima")
        self._gravar(atual)
        return atual

    def limites(self) -> Limites:
        c = self.carregar()
        return Limites(c["limite_tensao_max"], c["limite_tensao_min"], c["limite_corrente_max"])

    # ------------------------------------------------------------------
    def _normalizar(self, bruto: dict) -> tuple[dict, bool]:
        config, corrigido = {}, False
        for chave, padrao in self.DEFAULT_CONFIG.items():
            if chave not in bruto:
                config[chave] = padrao
                corrigido = True
                continue
            try:
                config[chave] = self._VALIDADORES[chave](bruto[chave])
            except (TypeError, ValueError):
                log.warning("config.json: valor inválido em '%s' (%r); usando padrão", chave, bruto[chave])
                config[chave] = padrao
                corrigido = True
        if config["limite_tensao_min"] >= config["limite_tensao_max"]:
            config["limite_tensao_min"] = self.DEFAULT_CONFIG["limite_tensao_min"]
            config["limite_tensao_max"] = self.DEFAULT_CONFIG["limite_tensao_max"]
            corrigido = True
        return config, corrigido

    def _gravar(self, dados: dict):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".json.tmp")
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        os.replace(temporario, self.caminho)

    def _guardar_corrompido(self):
        try:
            os.replace(self.caminho, self.caminho.with_suffix(".json.corrompido"))
        except OSError:
            pass


# ---------------- validadores ----------------
def _faixa(v, minimo, maximo):
    if not (minimo <= v <= maximo):
        raise ValueError(f"{v} fora da faixa [{minimo}, {maximo}]")
    return v


def _em(v, opcoes):
    if v not in opcoes:
        raise ValueError(f"{v} não está em {opcoes}")
    return v


def _texto_nao_vazio(v):
    if not isinstance(v, str) or not v.strip():
        raise ValueError("texto vazio")
    return v.strip()


def _booleano(v):
    if isinstance(v, bool):
        return v
    raise ValueError("esperado true/false")
