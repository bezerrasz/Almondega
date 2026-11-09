"""Folha de estilo (tema escuro) aplicada à aplicação inteira."""

CORES_ESTADO = {
    "verde": "#1f9d55",
    "vermelho": "#d64545",
    "amarelo": "#d69e2e",
    "cinza": "#4a5568",
    "azul": "#3182ce",
}

QSS = """
QWidget { background-color: #1e2228; color: #e6e6e6; font-size: 10pt; }
QGroupBox {
    border: 1px solid #3a4049; border-radius: 6px; margin-top: 14px; padding: 8px 6px 6px 6px;
    font-weight: bold;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #f5a524; }
QLabel#lbl_titulo { font-size: 20pt; font-weight: 800; color: #f5a524; padding: 4px; }
QLabel#lbl_tensao, QLabel#lbl_corrente, QLabel#lbl_potencia {
    font-size: 17pt; font-weight: bold; color: #ffffff;
}
QLabel#lbl_estatisticas, QLabel#lbl_detalhe_conexao { color: #a0aec0; font-size: 9pt; }
QPushButton {
    background-color: #2d3748; border: 1px solid #4a5568; border-radius: 5px; padding: 6px 10px;
}
QPushButton:hover { background-color: #3b475c; }
QPushButton:disabled { color: #6b7280; background-color: #262b33; border-color: #333a44; }
QPushButton#btn_emergencia {
    background-color: #b91c1c; border: 1px solid #ef4444; font-weight: bold; font-size: 11pt; padding: 9px;
}
QPushButton#btn_emergencia:hover { background-color: #dc2626; }
QPushButton#btn_emergencia:disabled { background-color: #4b1f1f; color: #9b6b6b; }
QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QPlainTextEdit, QTableWidget {
    background-color: #12151a; border: 1px solid #3a4049; border-radius: 4px; padding: 3px;
}
QPlainTextEdit { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 9pt; }
QHeaderView::section { background-color: #2d3748; padding: 4px; border: none; }
QTableWidget { alternate-background-color: #1a1e24; gridline-color: #2d3748; }
QStatusBar { color: #a0aec0; }
"""


def estilo_indicador(cor: str) -> str:
    return (f"background-color: {CORES_ESTADO[cor]}; color: white; font-weight: bold;"
            "border-radius: 6px; padding: 8px; font-size: 12pt;")
