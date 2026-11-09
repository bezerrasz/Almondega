/*
 * Smart Grid - Firmware da placa de medição (Entrega A1/5)
 *
 * Máquina de estados:
 *   AGUARDANDO_HS  -> placa a 9600 bps, em silêncio, esperando "HS,<baud>,<periodo_ms>"
 *   AGUARDANDO_SYNC-> respondeu "ACK,HS,..." e trocou para a nova velocidade;
 *                     espera "SYNC" por até 3 s (senão volta para 9600)
 *   TELEMETRIA     -> respondeu "ACK,SYNC" e envia "DATA,..." a cada periodo_ms
 *
 * Comandos aceitos em TELEMETRIA:
 *   DJ,0  abre o disjuntor (LED apagado, corrente = 0)
 *   DJ,1  fecha o disjuntor (LED aceso)
 *   PING  keepalive do desktop (sem resposta)
 *   STOP  encerra a telemetria e volta para 9600 / AGUARDANDO_HS
 * Um "HS" recebido em qualquer estado reinicia o handshake.
 * Sem nenhum byte do desktop por 5 s em TELEMETRIA -> volta para AGUARDANDO_HS.
 *
 * Pacote de telemetria:  DATA,<seq>,<tensao>,<corrente>,<dj>*<CK>
 *   CK = XOR de todos os caracteres entre o início da linha e o '*', em 2 dígitos hex.
 */

// ---------------- Configuração de hardware ----------------
const int  PINO_DISJUNTOR      = 13;   // LED representa o disjuntor (aceso = fechado)
const int  PINO_POT_CORRENTE   = A0;   // potenciômetro opcional para simular a carga
const bool USAR_POTENCIOMETRO  = false; // true: corrente = posição do pot (0-40 A)

// ---------------- Protocolo ----------------
const long BAUD_INICIAL          = 9600;
const unsigned long TIMEOUT_SYNC = 3000;  // ms esperando SYNC na nova velocidade
const unsigned long TIMEOUT_LINK = 5000;  // ms sem nada do desktop em TELEMETRIA

enum Estado { AGUARDANDO_HS, AGUARDANDO_SYNC, TELEMETRIA };
Estado estado = AGUARDANDO_HS;

long          baudAtual        = BAUD_INICIAL;
unsigned long periodoMs        = 1000;
unsigned long instanteEstado   = 0;   // quando entrou no estado atual
unsigned long ultimoRx         = 0;   // último byte vindo do desktop
unsigned long ultimoEnvio      = 0;
unsigned long sequencia        = 0;
bool          disjuntorFechado = true;

char buffer[48];
byte tamBuffer = 0;

// ---------------------------------------------------------
bool baudSuportado(long b) {
  return b == 9600 || b == 19200 || b == 38400 || b == 115200;
}

void trocarBaud(long novo) {
  Serial.flush();          // garante que a última resposta saiu na velocidade antiga
  Serial.end();
  Serial.begin(novo);
  baudAtual = novo;
  tamBuffer = 0;
}

void mudarEstado(Estado novo) {
  estado = novo;
  instanteEstado = millis();
}

void voltarParaEspera() {
  if (baudAtual != BAUD_INICIAL) trocarBaud(BAUD_INICIAL);
  sequencia = 0;
  mudarEstado(AGUARDANDO_HS);
}

void aplicarDisjuntor(bool fechado) {
  disjuntorFechado = fechado;
  digitalWrite(PINO_DISJUNTOR, fechado ? HIGH : LOW);
}

// ---------------- Medições simuladas ----------------
float medirTensao() {
  float t = millis() / 1000.0;
  return 220.0 + 2.5 * sin(t / 7.0) + random(-50, 51) / 100.0;
}

float medirCorrente() {
  if (!disjuntorFechado) return 0.0;
  if (USAR_POTENCIOMETRO) {
    return analogRead(PINO_POT_CORRENTE) * (40.0 / 1023.0);
  }
  float t = millis() / 1000.0;
  return 11.0 + 3.0 * sin(t / 10.0) + random(-30, 31) / 100.0;
}

void enviarTelemetria() {
  char sTensao[10], sCorrente[10], linha[64];
  dtostrf(medirTensao(), 1, 2, sTensao);
  dtostrf(medirCorrente(), 1, 2, sCorrente);
  snprintf(linha, sizeof(linha), "DATA,%lu,%s,%s,%d",
           ++sequencia, sTensao, sCorrente, disjuntorFechado ? 1 : 0);

  byte ck = 0;
  for (char *p = linha; *p; p++) ck ^= (byte)*p;

  char sufixo[6];
  snprintf(sufixo, sizeof(sufixo), "*%02X", ck);
  Serial.print(linha);
  Serial.println(sufixo);
}

// ---------------- Tratamento de comandos ----------------
void tratarHandshake(char *args) {
  // args = "<baud>,<periodo>"
  char *sBaud = strtok(args, ",");
  char *sPer  = strtok(NULL, ",");
  if (!sBaud || !sPer) { Serial.println("NAK,HS_FORMATO"); return; }

  long novoBaud = atol(sBaud);
  long novoPer  = atol(sPer);
  if (!baudSuportado(novoBaud))     { Serial.println("NAK,HS_BAUD");    return; }
  if (novoPer < 200 || novoPer > 5000) { Serial.println("NAK,HS_PERIODO"); return; }

  periodoMs = novoPer;
  Serial.print("ACK,HS,");
  Serial.print(novoBaud);
  Serial.print(",");
  Serial.println(periodoMs);

  if (novoBaud != baudAtual) trocarBaud(novoBaud);
  mudarEstado(AGUARDANDO_SYNC);
}

void processarLinha(char *linha) {
  if (strncmp(linha, "HS,", 3) == 0) {         // aceito em qualquer estado
    tratarHandshake(linha + 3);
    return;
  }

  switch (estado) {
    case AGUARDANDO_HS:
      Serial.println("NAK,AGUARDANDO_HS");
      break;

    case AGUARDANDO_SYNC:
      if (strcmp(linha, "SYNC") == 0) {
        Serial.println("ACK,SYNC");
        ultimoEnvio = millis();
        mudarEstado(TELEMETRIA);
      }
      break;

    case TELEMETRIA:
      if (strcmp(linha, "PING") == 0) {
        // keepalive: nada a responder
      } else if (strcmp(linha, "DJ,0") == 0) {
        aplicarDisjuntor(false);
        Serial.println("ACK,DJ,0");
      } else if (strcmp(linha, "DJ,1") == 0) {
        aplicarDisjuntor(true);
        Serial.println("ACK,DJ,1");
      } else if (strcmp(linha, "STOP") == 0) {
        Serial.println("ACK,STOP");
        voltarParaEspera();
      } else if (strcmp(linha, "SYNC") == 0) {
        Serial.println("ACK,SYNC");            // SYNC repetido: só confirma
      } else {
        Serial.print("NAK,CMD_INVALIDO:");
        Serial.println(linha);
      }
      break;
  }
}

// Leitura não bloqueante: monta a linha byte a byte
void lerSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    ultimoRx = millis();
    if (c == '\r') continue;
    if (c == '\n') {
      buffer[tamBuffer] = '\0';
      if (tamBuffer > 0) processarLinha(buffer);
      tamBuffer = 0;
    } else if (tamBuffer < sizeof(buffer) - 1) {
      buffer[tamBuffer++] = c;
    } else {
      tamBuffer = 0;   // linha longa demais: descarta
    }
  }
}

// ---------------------------------------------------------
void setup() {
  pinMode(PINO_DISJUNTOR, OUTPUT);
  aplicarDisjuntor(true);
  randomSeed(analogRead(A5));
  Serial.begin(BAUD_INICIAL);
  mudarEstado(AGUARDANDO_HS);   // em silêncio até o desktop iniciar o link
}

void loop() {
  lerSerial();
  unsigned long agora = millis();

  if (estado == AGUARDANDO_SYNC && agora - instanteEstado > TIMEOUT_SYNC) {
    voltarParaEspera();         // SYNC não chegou: a velocidade nova falhou
  }

  if (estado == TELEMETRIA) {
    if (agora - ultimoRx > TIMEOUT_LINK) {
      voltarParaEspera();       // desktop sumiu
      return;
    }
    if (agora - ultimoEnvio >= periodoMs) {
      ultimoEnvio = agora;
      enviarTelemetria();
    }
  }
}
