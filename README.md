# ⚡ Smart Grid - Dashboard (Entrega A1/1)

Interface gráfica em Python (PySide6) para monitoramento de telemetria de uma Smart Grid. Esta etapa inicial foca apenas na construção visual, navegação e organização do código no padrão MVC (sem conexão física com hardware ainda).

## 👥 Equipe
* Daniel Bezerra Freire - 411358
* Bruno Felipe Kuhnen - 414110

## 🏗️ Estrutura do Projeto
* `.venv/`: Ambiente virtual do Python, utilizado para isolar as dependências e bibliotecas do projeto (PySide6 e Matplotlib).
* `/ui`: Telas desenhadas no Qt Designer e seus arquivos `.py` gerados automaticamente.
* `/controllers`: Classes responsáveis por controlar a interface, gerenciar eventos e integrar as múltiplas janelas.
* `/models`: Banco de dados em memória e regras de negócio do sistema (ex: cálculos matemáticos e armazenamento de logs).
* `main.py`: Arquivo inicial e enxuto, funcionando apenas como ponto de partida da aplicação.

## 🚀 Funcionalidades Implementadas
* Dashboard responsivo com indicadores de Tensão, Corrente e cálculo de Potência.
* Gráfico de consumo pré-carregado simulando curva de demanda.
* Indicador visual do status do disjuntor (Aberto/Fechado).
* Janela modal para configuração de limites (Setpoints).
* Sistema de auditoria e logs (QTableWidget) com filtro por data (QDateEdit).
* Interface de configuração para comunicação serial.