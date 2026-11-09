"""Mediação da tela de eventos: a consulta vai para a thread do banco e volta por sinal."""
from PySide6.QtCore import QObject

from views.eventos_view import EventosView


class EventosController(QObject):
    def __init__(self, persistencia, parent_view):
        super().__init__()
        self.persistencia = persistencia
        self._pedido = None
        self.view = EventosView(parent_view)
        self.view.filtro_solicitado.connect(self._filtrar)
        self.persistencia.eventos_prontos.connect(self._ao_receber)

    def executar(self):
        self.view.solicitar_carga_inicial()
        self.view.exec()
        self.persistencia.eventos_prontos.disconnect(self._ao_receber)

    def _filtrar(self, inicio, fim):
        if inicio >= fim:
            inicio, fim = fim, inicio
        self.view.indicar_carregando()
        self._pedido = self.persistencia.consultar_eventos({"inicio": inicio, "fim": fim})

    def _ao_receber(self, pedido, eventos):
        if pedido == self._pedido:
            self.view.mostrar_eventos(eventos)
