"""Regras de engenharia: validação de limites elétricos. Python puro."""
from __future__ import annotations

from dataclasses import dataclass

from models.entidades import LeituraTelemetria, TipoEvento


@dataclass(frozen=True)
class Limites:
    tensao_max: float
    tensao_min: float
    corrente_max: float


@dataclass(frozen=True)
class Violacao:
    tipo_evento: str
    grandeza: str
    valor: float
    limite: float
    exige_corte: bool

    @property
    def mensagem(self) -> str:
        unid = "V" if self.grandeza == "tensao" else "A"
        nomes = {
            TipoEvento.CORTE_SOBRECORRENTE: "Sobrecorrente",
            TipoEvento.CORTE_SOBRETENSAO: "Sobretensão",
            TipoEvento.ALERTA_SUBTENSAO: "Subtensão",
        }
        acao = "disjuntor aberto" if self.exige_corte else "apenas alerta"
        return (f"{nomes.get(self.tipo_evento, self.tipo_evento)}: {self.valor:.2f} {unid} "
                f"(limite {self.limite:.2f} {unid}) - {acao}")


def avaliar_limites(leitura: LeituraTelemetria, limites: Limites) -> list[Violacao]:
    violacoes = []
    if leitura.corrente > limites.corrente_max:
        violacoes.append(Violacao(TipoEvento.CORTE_SOBRECORRENTE, "corrente",
                                  leitura.corrente, limites.corrente_max, True))
    if leitura.tensao > limites.tensao_max:
        violacoes.append(Violacao(TipoEvento.CORTE_SOBRETENSAO, "tensao",
                                  leitura.tensao, limites.tensao_max, True))
    elif leitura.tensao < limites.tensao_min:
        violacoes.append(Violacao(TipoEvento.ALERTA_SUBTENSAO, "tensao",
                                  leitura.tensao, limites.tensao_min, False))
    return violacoes


class MonitorLimites:
    """
    Avalia cada leitura e só reporta uma violação quando ela COMEÇA
    (evita gravar o mesmo alarme a cada amostra enquanto a condição persiste).
    """

    def __init__(self, limites: Limites):
        self.limites = limites
        self._ativas: set[str] = set()

    def atualizar_limites(self, limites: Limites):
        self.limites = limites
        self._ativas.clear()

    def avaliar(self, leitura: LeituraTelemetria) -> list[Violacao]:
        atuais = avaliar_limites(leitura, self.limites)
        tipos_atuais = {v.tipo_evento for v in atuais}
        novas = [v for v in atuais if v.tipo_evento not in self._ativas]
        self._ativas = tipos_atuais
        return novas


def reduzir_pontos(itens: list, maximo: int) -> list:
    """Decimação simples para plotar consultas grandes sem pesar a interface."""
    if maximo <= 0 or len(itens) <= maximo:
        return itens
    passo = len(itens) / maximo
    return [itens[int(k * passo)] for k in range(maximo)]
