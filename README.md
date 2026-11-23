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

---

# Entrega A1/5 - Comunicação serial real, threads e persistência

A interface e o código das etapas anteriores foram mantidos (`controller/`, `ui/`, `models/`, `database/`).
A A1/5 acrescentou a comunicação com a placa (Arduino ou simulador), duas threads de trabalho e a persistência das leituras.

## 👥 Equipe
* Daniel Bezerra Freire - 411358
* Bruno Felipe Kuhnen - 414110
* Yago Colon Marques - 417703

## 🚀 Como executar
```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install PySide6 matplotlib pyserial
python main.py
```
**Com Arduino:** grave o firmware do professor (`firmware/firmware_professor/firmware_professor.ino`, cópia sem alterações), feche o Monitor Serial da IDE,
abra **Serial** no app, escolha a COM da placa e clique em *Conectar*.
O relé (pino 12) representa o disjuntor: ligado = FECHADO. A placa liga com o relé desligado, então o disjuntor aparece ABERTO até a *Alavanca Virtual* ser marcada.
O potenciômetro em **A0** é a tensão e o de **A1** é a corrente (0 a 250 V e 0 a 40 A; escala em `models/protocolo.py`).

**Com o simulador (sem hardware):**
* Windows: instale o [com0com](https://com0com.sourceforge.net/) e crie o par `COM10 <-> COM11`.
  Rode `python simulador/placa_virtual.py COM11` e conecte o app na `COM10`.
* Linux/macOS: `python tests/par_portas_virtuais.py` mostra dois caminhos `/dev/pts/X`. Use um no simulador e o outro no app.

**Testes** (Linux/macOS; no Windows os de serial precisam do com0com):
```bash
python tests/teste_models.py                     # Model: protocolo, config.json, repositório SQLite (16 testes)
python tests/teste_serial_simulador.py           # SerialWorker x simulador: handshake a 115200
python tests/teste_serial_simulador.py --fallback --segundos 30   # falha a 115200/38400 -> cai para 19200
python tests/teste_integracao_gui.py             # app completo: telas + 2 threads + SQLite + gráfico + config.json
python tests/teste_corte_automatico.py           # pico de corrente -> SOBRECARGA -> corte emergencial ACID
python tests/teste_falhas.py                     # cabo puxado e placa travada: reconecta e refaz o handshake
```

## ➕ O que a A1/5 acrescentou ao que já existia
| Onde | O que mudou |
|---|---|
| `workers/serial_worker.py` (novo) | laço da **SerialThread**: handshake, telemetria, comandos, watchdog e reconexão |
| `workers/db_worker.py` (novo) | **DatabaseThread**: grava leituras/eventos e responde às consultas |
| `controller/conexao_controller.py`, `persistencia_controller.py` (novos) | criam e encerram as duas QThreads (`quit` + `deleteLater`) |
| `controller/dashboard_controller.py` | o gerador aleatório saiu: os valores vêm da placa; alavanca e PARAR comandam o relé/disjuntor (`!1`/`!0` + ACK); modo histórico do gráfico; encerramento cooperativo |
| `controller/serialport_controller.py` | **Conectar/Desconectar** agora abrem a porta de verdade; portas reais na lista; amostragem e timeout salvos no `config.json` |
| `controller/config_controller.py`, `historico_controller.py` | o banco é acessado pela DatabaseThread (mesmas validações, telas e filtro de antes) |
| `models/protocolo.py`, `portas_seriais.py`, `entidades.py` (novos) | pacotes e checksum, lista de portas, leitura de telemetria |
| `models/config_manager.py` | recria o `config.json` se for apagado/corrompido, mesmo com o app aberto; chaves novas `taxa_amostragem_ms` e `timeout_s` |
| `models/repository.py`, `database/connection.py` | tabela `leituras` (histórico de V, I e P) e gravação de chaveamento + status na mesma transação |
| `models/sistema_model.py` | o log de auditoria é entregue à DatabaseThread, em vez de gravar na thread da tela |
| `ui/dashboard.ui`, `ui/serialport.ui` | seletor Tempo real/Histórico com filtro; campo Amostragem, velocidade e log do handshake |

O limite de **corrente** (config.json) e o **slider de Limite de Alerta** (potência) continuam sendo as regras de proteção:
ao violar uma delas, o app envia `!0` (desliga o relé) e, quando a placa confirma, grava o corte emergencial (ACID).

## 🧵 Threads

```
 GUI (MainThread)                SerialThread                      DatabaseThread
 ─────────────────               ─────────────────                 ──────────────────
 Dashboard (QDialog) ◄── sinais ──── SerialWorker.executar()           DbWorker (event loop)
 DashboardController             laço: read(timeout 0,1 s)         conexão SQLite própria
   │  enviar_comando() ─ fila ─►  escreve comandos da fila          gravar_leitura()
   │  parar() ──── Event ──────►  sai do laço, envia !P            registrar_evento()
   └─ sinais enfileirados ────────────────────────────────────────► consultar_historico()
                                                                    consultar_eventos()
```

* A GUI **nunca** chama `read`/`readline` nem acessa o banco. O maior atraso medido no event loop da GUI
  durante o teste completo foi de cerca de 150 ms (desenho do matplotlib).
* `SerialWorker` tem laço bloqueante, então a GUI conversa com ele por estruturas thread-safe
  (`queue.Queue` para comandos e `threading.Event` para a parada), e não por slots.
* `DbWorker` usa o event loop da própria thread: cada pedido é um sinal enfileirado (QueuedConnection automática).
  A conexão SQLite é criada **dentro** da thread do banco.
* **Encerramento cooperativo:** ao fechar a janela, o `closeEvent` é ignorado e o encerramento começa.
  A serial para primeiro (envia `!P` à placa) e depois o banco grava o que está na fila e fecha a conexão.
  Só então a janela fecha. Em cada thread: `finalizado → thread.quit()`, `thread.finished → worker.deleteLater()`
  e `thread.finished → thread.deleteLater()`.

## 🔌 Protocolo serial e handshake

Protocolo do firmware do professor. Comandos começam com `!` e terminam em `\n`.

| Desktop → placa | Placa → desktop | Quando |
|---|---|---|
| `!S<baud>` | `>>> ACK: INICIANDO EM <baud> BPS <<<` | **sempre enviado a 9600 bps**; é o primeiro pacote do link. A placa responde a 9600 e só então troca de velocidade |
| | `$DAT,<A0>,<A1>,<relé>,<botão>*<CK>` | telemetria contínua (~200 pacotes/s; CK = XOR dos caracteres entre `$` e `*`, em hex) |
| `!1` / `!0` | `>>> ACK: RELE LIGADO <<<` / `>>> ACK: RELE DESLIGADO <<<` | fechar / abrir o disjuntor |
| `!P` | `>>> ACK: CONVERSAO PAUSADA. RETORNANDO A 9600 BPS <<<` | a placa volta a 9600 e fica em espera |
| velocidade inválida | `>>> ERR: BAUD INVALIDO ... <<<` | |

**Máquina de estados da placa:** em espera a 9600 bps (imprime um banner e não transmite leituras) → telemetria na velocidade pedida → `!P` volta à espera.

**Negociação no desktop:** abre a porta a 9600, espera o reset do Arduino (2 s), envia `!S<baud>` com a velocidade alvo do `config.json`
e, recebido o ACK, troca a velocidade sem fechar a porta (fechar resetaria o Arduino). Em seguida espera o primeiro `$DAT` válido.
Se ele não chegar, envia `!P`, volta a 9600 e tenta a próxima velocidade menor (115200 → 38400 → 19200 → 9600).

**Conversão e amostragem:** A0 e A1 são valores brutos do conversor (0 a 1023). O app converte A0 em tensão (0 a 250 V) e A1 em corrente (0 a 40 A);
as constantes `TENSAO_FUNDO_ESCALA_V` e `CORRENTE_FUNDO_ESCALA_A` ficam em `models/protocolo.py`. Relé desligado (disjuntor aberto) = sem carga, e a corrente exibida é 0.
O firmware amostra a cada 5 ms e não aceita período; o campo *Amostragem (ms)* do app define quantas leituras por segundo vão para o gráfico e para o banco
(uma mudança no relé é mostrada na hora). O botão físico (pino 11) funciona como o PARAR da tela: na subida (solto → apertado, 2 pacotes seguidos) o app envia `!0`, espera o ACK e grava o corte de emergência (ACID). Se já estiver apertado ao conectar, não dispara; se o disjuntor já estiver aberto, só registra no log.

## 💾 Persistência
* **config.json** (`data/`): porta, velocidade alvo, limites de tensão e corrente, amostragem (ms) e timeout (s).
  Se o arquivo for apagado (até com o app aberto, via `QFileSystemWatcher`) ou corrompido, é recriado com valores padrão.
* **smartgrid.db:** `dispositivos`, `regras_limites` e `historico_eventos` (como já eram) e a nova tabela
  **`leituras`** (timestamp com ms, tensão, corrente, potência e estado do disjuntor).

## 📈 Gráfico em dois modos
* **Tempo real:** cada amostra da SerialThread entra na curva (últimos 60 s).
* **Histórico:** escolha *Consulta de histórico* e filtre por últimas N leituras ou por intervalo de data/hora.
  A consulta roda na DatabaseThread; o resultado volta por sinal e a curva é replotada com eixo de data/hora.

## 🛡️ Tolerância a falhas (para a bancada)

| Falha induzida | Como provocar | Reação do sistema |
|---|---|---|
| Cabo desconectado | puxar o USB | `SerialException` capturada na SerialThread, alerta + evento, tentativa de reconexão a cada 2 s e novo handshake quando a placa volta |
| Placa travada / reiniciada | simulador `m` ou `r`, botão reset do Arduino | watchdog (3× período, mínimo de 3 s) detecta a falta de telemetria, reconecta e refaz o handshake; a placa reiniciada volta com o relé desligado |
| Pacote corrompido | simulador `c` | checksum rejeita o pacote, que entra no contador "inválidos" |
| Botão físico de emergência | botão no pino 11 (ou `b` no simulador) | mesmo fluxo do PARAR: `!0`, ACK, corte gravado, popup |
| Sobrecorrente | simulador `p`, ou potenciômetro A1 | o app envia `!0`, a placa confirma e o corte é gravado (ACID) |
| Velocidade alta falha | `--falhar-baud 115200` no simulador | fallback para a próxima velocidade |
| Placa não confirma o comando | | sem ACK em 2 s, grava um evento `ERROR` e alerta |
| config.json apagado/corrompido | apagar/editar o arquivo | recriado na hora |

## 🎤 Roteiro sugerido da demonstração
1. Abrir o app e mostrar o console: banco aberto na DatabaseThread.
2. Botão **Serial**: escolher porta/velocidade e **Conectar**. O log mostra `!S115200` a 9600, o `ACK`, a troca de velocidade e a telemetria.
3. Arrastar a janela e abrir os diálogos durante a telemetria: nada trava.
4. **Alavanca Virtual** fecha/abre o disjuntor (`!1`/`!0` + ACK) e grava o evento. Girar o potenciômetro A1 (ou `p` no simulador) além do limite de corrente: corte automático.
5. **PARAR** (na tela ou o botão físico da protoboard): corte emergencial salvo no banco (popup de confirmação).
6. **Limites**: alterar e salvar. **Histórico**: eventos por data.
7. Modo *Consulta de histórico*: últimas 500 leituras e depois um intervalo.
8. Apagar o `config.json` com o app aberto: é recriado.
9. Puxar o cabo USB: alerta e tentativas de reconexão. Recolocar: o handshake é refeito sozinho.
10. Fechar o app e mostrar no log o encerramento ordenado das threads.
