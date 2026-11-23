"""Entidades de domínio. Python puro: nenhuma dependência de Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def calcular_potencia_ativa(tensao: float, corrente: float, fator_potencia: float = 1.0) -> float:
    """P = V · I · FP (W). Com FP = 1 é o mesmo cálculo que o SistemaModel já fazia (V · I)."""
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
