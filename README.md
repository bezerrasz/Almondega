# ⚡ Smart Grid - Supervisório (Entrega A1/5)

Software desktop em Python/PySide6 para supervisionar uma placa de medição (Arduino ou simulador):
handshake com negociação de velocidade, telemetria em tempo real, proteção automática por limites,
comando do disjuntor, persistência em SQLite, configurações em JSON e gráfico com consulta de histórico.
O padrão é MVC com três threads (GUI, serial e banco).

## 👥 Equipe
* Daniel Bezerra Freire - 411358
* Bruno Felipe Kuhnen - 414110
* Yago Colon Marques - 417703

---

## 🚀 Como executar

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Com Arduino:** grave `firmware/smartgrid_placa/smartgrid_placa.ino`, escolha a COM da placa e clique em *Conectar*.
O LED do pino 13 representa o disjuntor (aceso = fechado). Com `USAR_POTENCIOMETRO = true`, um potenciômetro
em A0 controla a corrente (0 a 40 A); girar até o fim faz a proteção de sobrecorrente atuar.

**Com o simulador (sem hardware):**
* Windows: instale o [com0com](https://com0com.sourceforge.net/) e crie o par `COM10 <-> COM11`.
  Rode `python simulador/placa_virtual.py COM11` e conecte o app na `COM10`.
* Linux/macOS: `python tests/par_portas_virtuais.py` mostra dois caminhos `/dev/pts/X`. Use um no simulador e o outro no app.

**Testes:**
```bash
python tests/teste_models.py                     # Model: protocolo, regras, JSON, SQLite (15 testes)
python tests/teste_serial_simulador.py           # SerialWorker x simulador (Linux/macOS)
python tests/teste_serial_simulador.py --fallback
```

---

## 🏗️ Arquitetura MVC

```
main.py                     infraestrutura (log, config) e montagem View + Controller
models/      (sem Qt)       entidades.py   LeituraTelemetria, Disjuntor, Evento, cálculo de potência
                            regras.py      Limites, MonitorLimites (violação só no início), decimação
                            protocolo.py   montagem/validação de pacotes, checksum, ordem de negociação
                            config_manager.py   config.json resiliente (recria, valida, grava atômico)
                            repository.py  SQLite: esquema, migração da A1/1, leituras, eventos, consultas
views/       (só desenho)   dashboard_view.py, grafico.py, limites_view.py, eventos_view.py
ui/                         arquivos do Qt Designer (.ui) e o código gerado (pyside6-uic)
controllers/ (orquestração) app_controller.py, conexao_controller.py, persistencia_controller.py,
                            limites_controller.py, eventos_controller.py
workers/     (QThreads)     serial_worker.py, db_worker.py
firmware/                   código da placa (Arduino)
simulador/                  placa virtual com o mesmo protocolo e falhas induzidas
```

Regras seguidas (e conferíveis com `grep`):
* **Model** não importa PySide6. Valida limites, calcula potência e acessa SQLite e JSON.
* **View** só emite sinais (`conectar_solicitado`, `disjuntor_solicitado`, `consulta_historico_solicitada`...)
  e expõe métodos `mostrar_*`. Não importa `serial`, `sqlite3` nem nada de `models`.
* **Controller** liga os sinais da View aos Models, cria e encerra as threads e repassa os dados prontos para a tela.

## 🧵 Threads

```
 GUI (MainThread)                SerialThread                      DatabaseThread
 ─────────────────               ─────────────────                 ──────────────────
 DashboardView   ◄── sinais ──── SerialWorker.executar()           DbWorker (event loop)
 AppController                   laço: read(timeout 0,1 s)         conexão SQLite própria
   │  enviar_comando() ─ fila ─►  escreve comandos da fila          gravar_leitura()
   │  parar() ──── Event ──────►  sai do laço, envia STOP           registrar_evento()
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
  A serial para primeiro (envia `STOP` à placa) e depois o banco grava o que está na fila e fecha a conexão.
  Só então a janela fecha. Em cada thread: `finalizado → thread.quit()`, `thread.finished → worker.deleteLater()`
  e `thread.finished → thread.deleteLater()`.

## 🔌 Protocolo serial e handshake

Linhas ASCII terminadas em `\n`.

| Desktop → placa | Placa → desktop | Quando |
|---|---|---|
| `HS,<baud>,<periodo_ms>` | `ACK,HS,<baud>,<periodo_ms>` | **sempre a 9600 bps**; é o primeiro pacote do link |
| `SYNC` | `ACK,SYNC` | já na nova velocidade; libera a telemetria |
| | `DATA,<seq>,<V>,<I>,<dj>*<CK>` | a cada `periodo_ms` (CK = XOR dos caracteres, em hex) |
| `DJ,0` / `DJ,1` | `ACK,DJ,0` / `ACK,DJ,1` | abrir / fechar o disjuntor |
| `PING` | (nada) | keepalive a cada 1 s |
| `STOP` | `ACK,STOP` | placa volta a 9600 e ao estado de espera |
| qualquer coisa errada | `NAK,<motivo>` | |

**Máquina de estados da placa:** `AGUARDANDO_HS` (9600 bps, em silêncio) → `AGUARDANDO_SYNC` (nova velocidade;
volta a 9600 se o SYNC não chegar em 3 s) → `TELEMETRIA` (volta à espera após 5 s sem nada do desktop).

**Negociação no desktop:** abre a porta a 9600, espera o reset do Arduino (2 s), envia o `HS` com a velocidade
alvo do `config.json` e, recebido o ACK, troca a velocidade sem fechar a porta (fechar resetaria o Arduino).
Se o `SYNC` não for confirmado, volta a 9600 e tenta a próxima velocidade menor (115200 → 38400 → 19200 → 9600).

## 💾 Persistência

* **config.json:** porta, velocidade alvo, amostragem, limites de tensão (mín/máx) e de corrente, fator de potência
  e reconexão automática. Se o arquivo for apagado (até com o app aberto, via `QFileSystemWatcher`), é recriado
  com valores padrão seguros. Se estiver corrompido, vira `config.json.corrompido` e é recriado. Valores inválidos
  voltam ao padrão. A gravação é atômica.
* **smartgrid.db:**
  * `leituras` (timestamp, seq, tensão, corrente, potência, estado do disjuntor, FK do dispositivo)
  * `historico_eventos` (FK `dispositivo_id` + FK `leitura_id` da amostra que motivou o evento)
  * `dispositivos` (status do disjuntor)

  Atuação do disjuntor = evento + status do dispositivo na **mesma transação**.
  Bancos da A1/1 são migrados automaticamente (datas `dd/mm/aaaa` passam para ISO).

## 📈 Gráfico em dois modos
* **Tempo real:** cada amostra da SerialThread entra na curva na hora (potência, tensão ou corrente),
  com as linhas de limite desenhadas.
* **Histórico:** filtro "últimas N leituras" ou "intervalo de data/hora". A consulta roda na DatabaseThread,
  o resultado volta por sinal e a curva é replotada. Consultas grandes são reduzidas a 5000 pontos.
  Enquanto isso, a telemetria continua sendo gravada.

## 🛡️ Tolerância a falhas (para a bancada)

| Falha induzida | Como provocar | Reação do sistema |
|---|---|---|
| Cabo desconectado | puxar o USB | `SerialException` capturada na SerialThread, alerta + evento, tentativa de reconexão a cada 2 s e novo handshake quando a placa volta |
| Placa travada / reiniciada | simulador `m` ou `r`, botão reset do Arduino | watchdog (3× período, mínimo de 3 s) detecta a falta de telemetria, reconecta e refaz o handshake |
| Pacote corrompido | simulador `c` | checksum rejeita o pacote, que entra no contador "inválidos" |
| Sobrecorrente / sobretensão | simulador `p` / `t`, ou potenciômetro | `MonitorLimites` envia `DJ,0` e grava o evento de corte com a leitura vinculada |
| Velocidade alta falha | `--falhar-baud 115200` no simulador | fallback para a próxima velocidade |
| Placa não confirma o comando | | sem ACK em 2 s, grava `FALHA_COMUNICACAO` e alerta |
| config.json apagado/corrompido | apagar/editar o arquivo | recriado na hora |

## 🎤 Roteiro sugerido da demonstração
1. Abrir o app e mostrar o console: banco aberto na DatabaseThread.
2. Conectar e mostrar no console `HS` a 9600, `ACK`, troca para 115200, `SYNC` e o início da telemetria.
3. Arrastar a janela e abrir diálogos durante a telemetria: nada trava.
4. Induzir um pico (`p` ou potenciômetro): corte automático, evento na tela de Eventos.
5. Corte emergencial, depois religar.
6. Modo histórico: últimas 500 leituras e depois um intervalo de horário.
7. Apagar o `config.json` com o app aberto: é recriado.
8. Puxar o cabo USB: alerta, tentativas de reconexão. Recolocar: o handshake é refeito sozinho.
9. Fechar o app e mostrar no log o encerramento ordenado das threads.
