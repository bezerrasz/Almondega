"""
Protocolo serial desktop <-> placa do professor. Python puro (sem Qt e sem pyserial).

A placa liga em espera a 9600 bps e só transmite depois de receber o comando de início.
Todo comando começa com '!' e termina em '\\n'.

Desktop -> placa              Placa -> desktop
  !S<baud>                 ->   >>> ACK: INICIANDO EM <baud> BPS <<<   (ainda a 9600; depois troca de velocidade)
  !1 | !L                  ->   >>> ACK: RELE LIGADO <<<
  !0 | !D                  ->   >>> ACK: RELE DESLIGADO <<<
  !T                       ->   >>> ACK: RELE ALTERNADO <<<
  !P | !STOP               ->   >>> ACK: CONVERSAO PAUSADA. RETORNANDO A 9600 BPS <<<
                                >>> ERR: BAUD INVALIDO ... <<<
                                $DAT,<A0>,<A1>,<rele>,<botao>*<CK>      (telemetria, ~200 por segundo)

CK = XOR dos caracteres entre '$' e '*', em hexadecimal com 2 dígitos.
A0 e A1 são leituras brutas do conversor A/D (0 a 1023). O relé ligado representa o disjuntor FECHADO.

Convenção adotada pela equipe (o firmware só entrega valores brutos):
  A0 = tensão   (0..1023  ->  0 a TENSAO_FUNDO_ESCALA_V)
  A1 = corrente (0..1023  ->  0 a CORRENTE_FUNDO_ESCALA_A)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

BAUDS_SUPORTADOS = (9600, 19200, 38400, 115200)
BAUD_INICIAL = 9600

ADC_MAXIMO = 1023
TENSAO_FUNDO_ESCALA_V = 250.0       # A0 = 1023  ->  250 V
CORRENTE_FUNDO_ESCALA_A = 40.0      # A1 = 1023  ->  40 A

_RE_INICIO = re.compile(r"ACK:\s*INICIANDO EM (\d+) BPS", re.IGNORECASE)


class PacoteInvalido(ValueError):
    pass


@dataclass(frozen=True)
class Mensagem:
    tipo: str              # "DATA" (telemetria), "ACK", "NAK" ou "INFO"
    campos: tuple[str, ...]


@dataclass(frozen=True)
class DadosTelemetria:
    adc_tensao: int
    adc_corrente: int
    tensao: float
    corrente: float
    disjuntor_fechado: bool
    botao_pressionado: bool


def checksum(texto: str) -> str:
    ck = 0
    for ch in texto:
        ck ^= ord(ch)
    return f"{ck:02X}"


def adc_para_tensao(adc: int) -> float:
    return adc * TENSAO_FUNDO_ESCALA_V / ADC_MAXIMO


def adc_para_corrente(adc: int) -> float:
    return adc * CORRENTE_FUNDO_ESCALA_A / ADC_MAXIMO


# ---------------- comandos (desktop -> placa) ----------------
def cmd_iniciar(baud: int) -> str:
    if baud not in BAUDS_SUPORTADOS:
        raise ValueError(f"baud {baud} não suportado")
    return f"!S{baud}"


def cmd_disjuntor(fechar: bool) -> str:
    """Disjuntor fechado = relé ligado (!1); aberto = relé desligado (!0)."""
    return "!1" if fechar else "!0"


def cmd_pausar() -> str:
    return "!P"


def sequencia_negociacao(baud_alvo: int) -> list[int]:
    """Velocidades a tentar, da preferida para a mais lenta (fallback)."""
    if baud_alvo not in BAUDS_SUPORTADOS:
        baud_alvo = BAUD_INICIAL
    return sorted((b for b in BAUDS_SUPORTADOS if b <= baud_alvo), reverse=True)


# ---------------- interpretação (placa -> desktop) ----------------
def interpretar_linha(linha: str) -> Mensagem:
    linha = linha.strip()
    if not linha:
        raise PacoteInvalido("linha vazia")

    if linha.startswith("$"):
        if "*" not in linha:
            raise PacoteInvalido("telemetria sem checksum")
        corpo, ck = linha[1:].rsplit("*", 1)
        if checksum(corpo) != ck.strip().upper():
            raise PacoteInvalido(f"checksum inválido em '{linha}'")
        partes = corpo.split(",")
        if partes[0] != "DAT" or len(partes) != 5:
            raise PacoteInvalido(f"telemetria com formato inesperado: '{linha}'")
        return Mensagem("DATA", tuple(partes[1:]))

    if linha.startswith(">>>"):
        texto = linha.strip(">< ").strip()
        m = _RE_INICIO.search(texto)
        if m:
            return Mensagem("ACK", ("INICIO", m.group(1)))
        maiusculo = texto.upper()
        if maiusculo.startswith("ACK:"):
            if "PAUSADA" in maiusculo:
                return Mensagem("ACK", ("PAUSA",))
            if "RELE LIGADO" in maiusculo:
                return Mensagem("ACK", ("RELE", "1"))
            if "RELE DESLIGADO" in maiusculo:
                return Mensagem("ACK", ("RELE", "0"))
            if "RELE ALTERNADO" in maiusculo:
                return Mensagem("ACK", ("RELE", "T"))
            return Mensagem("ACK", ("OUTRO", texto))
        if maiusculo.startswith("ERR:"):
            return Mensagem("NAK", (texto,))
        return Mensagem("INFO", (texto,))

    if set(linha) == {"="} or "PLACA EM ESPERA" in linha or linha.startswith("Envie !"):
        return Mensagem("INFO", (linha,))      # banner impresso ao ligar/reiniciar a placa

    raise PacoteInvalido(f"mensagem desconhecida '{linha}'")


def decodificar_telemetria(msg: Mensagem) -> DadosTelemetria:
    try:
        a0, a1, rele, botao = msg.campos
        adc_v, adc_i = int(a0), int(a1)
        if not (0 <= adc_v <= ADC_MAXIMO and 0 <= adc_i <= ADC_MAXIMO):
            raise ValueError("leitura A/D fora de 0..1023")
        if rele not in ("0", "1") or botao not in ("0", "1"):
            raise ValueError("relé/botão devem ser 0 ou 1")
    except (ValueError, TypeError) as e:
        raise PacoteInvalido(f"campos de telemetria inválidos: {msg.campos}") from e
    return DadosTelemetria(adc_v, adc_i, adc_para_tensao(adc_v), adc_para_corrente(adc_i),
                           rele == "1", botao == "1")
