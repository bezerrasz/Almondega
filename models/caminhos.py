"""Caminhos absolutos do projeto (independem da pasta de onde o app é executado)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "smartgrid.db"
