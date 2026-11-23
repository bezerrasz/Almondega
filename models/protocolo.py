"""
Protocolo serial desktop <-> placa. Python puro (sem Qt e sem pyserial).

Desktop -> placa                Placa -> desktop
  HS,<baud>,<periodo_ms>   ->     ACK,HS,<baud>,<periodo_ms>   (sempre a 9600 bps)
  SYNC                     ->     ACK,SYNC                     (já na nova velocidade)
  DJ,0 | DJ,1              ->     ACK,DJ,0 | ACK,DJ,1
  PING                            (sem resposta, keepalive)
  STOP                     ->     ACK,STOP
                                  DATA,<seq>,<V>,<I>,<dj>*<CK>
                                  NAK,<motivo>
CK = XOR dos caracteres antes do '*', em hexadecimal com 2 dígitos.
"""
from __future__ import annotations

from dataclasses import dataclass

BAUDS_SUPORTADOS = (9600, 19200, 38400, 115200)
BAUD_INICIAL = 9600


class PacoteInvalido(ValueError):
    pass


@dataclass(frozen=True)
class Mensagem:
    tipo: str              # "DATA", "ACK" ou "NAK"
    campos: tuple[str, ...]


@dataclass(frozen=True)
class DadosTelemetria:
    seq: int
    tensao: float
    corrente: float
    disjuntor_fechado: bool


def checksum(texto: str) -> str:
    ck = 0
    for ch in texto:
        ck ^= ord(ch)
    return f"{ck:02X}"


def cmd_handshake(baud: int, periodo_ms: int) -> str:
    if baud not in BAUDS_SUPORTADOS:
        raise ValueError(f"baud {baud} não suportado")
    return f"HS,{baud},{periodo_ms}"


def cmd_sync() -> str:
    return "SYNC"


def cmd_disjuntor(fechar: bool) -> str:
    return f"DJ,{1 if fechar else 0}"


def cmd_ping() -> str:
    return "PING"


def cmd_stop() -> str:
    return "STOP"


def sequencia_negociacao(baud_alvo: int) -> list[int]:
    """Velocidades a tentar, da preferida para a mais lenta (fallback)."""
    if baud_alvo not in BAUDS_SUPORTADOS:
        baud_alvo = BAUD_INICIAL
    return sorted((b for b in BAUDS_SUPORTADOS if b <= baud_alvo), reverse=True)


def interpretar_linha(linha: str) -> Mensagem:
    linha = linha.strip()
    if not linha:
        raise PacoteInvalido("linha vazia")

    if linha.startswith("DATA,"):
        if "*" not in linha:
            raise PacoteInvalido("DATA sem checksum")
        corpo, ck = linha.rsplit("*", 1)
        if checksum(corpo) != ck.strip().upper():
            raise PacoteInvalido(f"checksum inválido em '{linha}'")
        campos = tuple(corpo.split(",")[1:])
        if len(campos) != 4:
            raise PacoteInvalido(f"DATA com {len(campos)} campos")
        return Mensagem("DATA", campos)

    tipo, *resto = linha.split(",")
    if tipo in ("ACK", "NAK"):
        return Mensagem(tipo, tuple(resto))
    raise PacoteInvalido(f"mensagem desconhecida '{linha}'")


def decodificar_telemetria(msg: Mensagem) -> DadosTelemetria:
    try:
        seq, v, i, dj = msg.campos
        return DadosTelemetria(int(seq), float(v), float(i), dj.strip() == "1")
    except (ValueError, TypeError) as e:
        raise PacoteInvalido(f"campos de DATA inválidos: {msg.campos}") from e
