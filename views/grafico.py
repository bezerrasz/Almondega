"""Widget do gráfico principal (matplotlib embutido no Qt). Somente desenho."""
from __future__ import annotations

from collections import deque

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

GRANDEZAS = {
    "potencia": ("Potência ativa", "W", "#f5a524"),
    "tensao": ("Tensão", "V", "#63b3ed"),
    "corrente": ("Corrente", "A", "#68d391"),
}


class GraficoWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None, pontos_tempo_real: int = 120):
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor="#1e2228", layout="constrained")
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)

        self.grandeza = "potencia"
        self.modo = "tempo_real"
        self._rt = {k: deque(maxlen=pontos_tempo_real) for k in ("t", "tensao", "corrente", "potencia")}
        self._hist = {k: [] for k in ("t", "tensao", "corrente", "potencia")}
        self._titulo_hist = ""
        self._limites: dict[str, tuple[float | None, float | None]] = {}
        self._linha, = self.ax.plot([], [], linewidth=1.8)
        self._redesenhar_completo()

    # ---------------- API usada pela View ----------------
    def definir_capacidade_tempo_real(self, pontos: int):
        for k, d in self._rt.items():
            self._rt[k] = deque(d, maxlen=pontos)

    def definir_grandeza(self, grandeza: str):
        self.grandeza = grandeza
        self._redesenhar_completo()

    def definir_modo(self, modo: str):
        self.modo = modo
        self._redesenhar_completo()

    def definir_limites(self, limites: dict):
        self._limites = limites
        self._redesenhar_completo()

    def adicionar_ponto(self, t, tensao, corrente, potencia):
        for k, v in (("t", t), ("tensao", tensao), ("corrente", corrente), ("potencia", potencia)):
            self._rt[k].append(v)
        if self.modo == "tempo_real":
            self._atualizar_linha(self._rt)

    def limpar_tempo_real(self):
        for d in self._rt.values():
            d.clear()
        if self.modo == "tempo_real":
            self._redesenhar_completo()

    def carregar_historico(self, t, tensao, corrente, potencia, titulo: str):
        self._hist = {"t": list(t), "tensao": list(tensao), "corrente": list(corrente),
                      "potencia": list(potencia)}
        self._titulo_hist = titulo
        self._redesenhar_completo()

    # ---------------- desenho ----------------
    def _dados(self):
        return self._rt if self.modo == "tempo_real" else self._hist

    def _redesenhar_completo(self):
        nome, unid, cor = GRANDEZAS[self.grandeza]
        ax = self.ax
        ax.clear()
        ax.set_facecolor("#12151a")
        for lado in ax.spines.values():
            lado.set_color("#3a4049")
        ax.tick_params(colors="#a0aec0", labelsize=9)
        ax.grid(True, color="#2d3748", linewidth=0.6)
        ax.set_ylabel(f"{nome} ({unid})", color="#e6e6e6", fontsize=10)
        localizador = AutoDateLocator(minticks=3, maxticks=8)
        ax.xaxis.set_major_locator(localizador)
        ax.xaxis.set_major_formatter(ConciseDateFormatter(
            localizador,
            formats=["%Y", "%b", "%d/%m", "%H:%M", "%H:%M", "%H:%M:%S"],
            zero_formats=["", "%Y", "%b", "%d/%m", "%H:%M", "%H:%M:%S"],
            show_offset=False))
        titulo = "Monitoramento em tempo real" if self.modo == "tempo_real" else (self._titulo_hist or "Histórico")
        ax.set_title(titulo, color="#e6e6e6", fontsize=11)

        lim_inf, lim_sup = self._limites.get(self.grandeza, (None, None))
        for valor, rotulo in ((lim_sup, "máx"), (lim_inf, "mín")):
            if valor is not None:
                ax.axhline(valor, color="#d64545", linestyle="--", linewidth=1)
                ax.annotate(f"{rotulo} {valor:g} {unid}", xy=(1, valor), xycoords=("axes fraction", "data"),
                            xytext=(-4, 3), textcoords="offset points", ha="right",
                            color="#f87171", fontsize=8)

        self._linha, = ax.plot([], [], color=cor, linewidth=1.8 if self.modo == "tempo_real" else 1.2)
        dados = self._dados()
        if self.modo == "historico" and not dados["t"]:
            ax.text(0.5, 0.5, "Sem leituras para o filtro escolhido", transform=ax.transAxes,
                    ha="center", va="center", color="#a0aec0")
        self._atualizar_linha(dados)

    def _atualizar_linha(self, dados):
        t, y = list(dados["t"]), list(dados[self.grandeza])
        self._linha.set_data(t, y)
        if t:
            if len(t) > 1:
                self.ax.set_xlim(t[0], t[-1])
            minimo, maximo = min(y), max(y)
            lim_inf, lim_sup = self._limites.get(self.grandeza, (None, None))
            if lim_sup is not None:
                maximo = max(maximo, lim_sup)
            if lim_inf is not None and self.grandeza == "tensao":
                minimo = min(minimo, lim_inf)
            folga = max((maximo - minimo) * 0.1, 1.0)
            self.ax.set_ylim(max(0, minimo - folga) if minimo >= 0 else minimo - folga, maximo + folga)
        self.draw_idle()
