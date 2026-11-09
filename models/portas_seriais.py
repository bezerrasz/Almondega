"""Enumeração das portas seriais do sistema (equivalente ao script 1 - listagem)."""
import serial.tools.list_ports


def listar_portas() -> list[tuple[str, str]]:
    try:
        return [(p.device, p.description or "") for p in serial.tools.list_ports.comports()]
    except Exception:
        return []
