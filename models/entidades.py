"""Entidades de domínio. Python puro: nenhuma dependência de Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def calcular_potencia_ativa(tensao: float, corrente: float, fator_potencia: float = 1.0) -> float:
    """P = V · I · FP (W)."""
    return tensao * corrente * fator_potencia


@dataclass(frozen=True)
class LeituraTelemetria:
    tensao: float
    corrente: float
    potencia: float
    timestamp: datetime = field(default_factory=datetime.now)
    seq: int = 0
    disjuntor_fechado: bool = True

    @classmethod
    def criar(cls, tensao: float, corrente: float, fator_potencia: float = 1.0,
              seq: int = 0, disjuntor_fechado: bool = True,
              timestamp: datetime | None = None) -> "LeituraTelemetria":
        return cls(
            tensao=tensao,
            corrente=corrente,
            potencia=calcular_potencia_ativa(tensao, corrente, fator_potencia),
            timestamp=timestamp or datetime.now(),
            seq=seq,
            disjuntor_fechado=disjuntor_fechado,
        )


class TipoEvento:
    ABERTURA_MANUAL = "ABERTURA_MANUAL"
    FECHAMENTO_MANUAL = "FECHAMENTO_MANUAL"
    CORTE_EMERGENCIAL = "CORTE_EMERGENCIAL"
    CORTE_SOBRECORRENTE = "CORTE_SOBRECORRENTE"
    CORTE_SOBRETENSAO = "CORTE_SOBRETENSAO"
    ALERTA_SUBTENSAO = "ALERTA_SUBTENSAO"
    CONEXAO = "CONEXAO"
    DESCONEXAO = "DESCONEXAO"
    FALHA_COMUNICACAO = "FALHA_COMUNICACAO"
    CONFIG = "CONFIG"


@dataclass(frozen=True)
class Evento:
    tipo: str
    descricao: str
    valor_medido: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    dispositivo_tag: str = "DJ-PRINCIPAL"


class Disjuntor:
    """Estado do disjuntor principal (espelho do estado reportado pela placa)."""

    def __init__(self, tag: str = "DJ-PRINCIPAL", fechado: bool = True):
        self.tag = tag
        self.fechado = fechado

    @property
    def estado_texto(self) -> str:
        return "FECHADO" if self.fechado else "ABERTO"

    def atualizar(self, fechado: bool) -> bool:
        """Atualiza o estado; devolve True se houve mudança."""
        mudou = fechado != self.fechado
        self.fechado = fechado
        return mudou
