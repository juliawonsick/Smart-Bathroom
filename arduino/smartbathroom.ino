#ifdef __INTELLISENSE__
  #include <stdint.h>
  #define HIGH   1
  #define LOW    0
  #define INPUT  0
  #define OUTPUT 1
  inline void          pinMode(uint8_t, uint8_t) {}
  inline void          digitalWrite(uint8_t, uint8_t) {}
  inline int           digitalRead(uint8_t) { return 0; }
  inline void          delay(unsigned long) {}
  inline unsigned long millis() { return 0; }
  inline void          tone(uint8_t, unsigned int, unsigned long = 0) {}
  inline void          noTone(uint8_t) {}
  struct _Serial {
    void begin(unsigned long) {}
    template<typename T> void print(T) {}
    template<typename T> void println(T) {}
  } Serial;
#endif

// ==========================================
// SMART BATHROOM
// ==========================================

// ---------- BOTÕES ----------

// Feminino
const int btnFemPH    = 13;
const int btnFemSab   = 12;
const int btnResetFem = 11;

// Masculino
const int btnResetMasc = 4;
const int btnMascSab   = 3;
const int btnMascPH    = 2;

// ---------- LEDS ----------

// Feminino
const int ledFemPH  = 10;
const int ledFemSab = 9;

// Masculino
const int ledMascSab = 5;
const int ledMascPH  = 6;

// ---------- BUZZERS ----------

const int buzzerFem  = 8;
const int buzzerMasc = 7;

// ---------- ESTADOS ----------

bool estadoFemPH  = false;
bool estadoFemSab = false;

bool estadoMascSab = false;
bool estadoMascPH  = false;

int ultimaQtdFem  = 0;
int ultimaQtdMasc = 0;

// ---------- SERIAL JSON ----------

void enviarAlerta(const char* bath, const char* item) {
  Serial.print("{\"event\":\"alert\",\"bathroom\":\"");
  Serial.print(bath);
  Serial.print("\",\"item\":\"");
  Serial.print(item);
  Serial.println("\"}");
}

void enviarResolucao(const char* bath) {
  Serial.print("{\"event\":\"resolve\",\"bathroom\":\"");
  Serial.print(bath);
  Serial.println("\"}");
}

// ==========================================
// BUZZER FEMININO
// ==========================================

void verificarBuzzerFem() {

  int qtd = estadoFemPH + estadoFemSab;

  if (ultimaQtdFem == 0 && qtd == 1) {

    for (int i = 0; i < 3; i++) {

      tone(buzzerFem, 1000);
      delay(3000);

      noTone(buzzerFem);

      if (i < 2) {
        delay(3000);
      }
    }
  }

  else if (ultimaQtdFem == 1 && qtd == 2) {

    tone(buzzerFem, 1500);
    delay(5000);
    noTone(buzzerFem);
  }

  ultimaQtdFem = qtd;
}

// ==========================================
// BUZZER MASCULINO
// ==========================================

void verificarBuzzerMasc() {

  int qtd = estadoMascSab + estadoMascPH;

  if (ultimaQtdMasc == 0 && qtd == 1) {

    for (int i = 0; i < 3; i++) {

      tone(buzzerMasc, 1000);
      delay(3000);

      noTone(buzzerMasc);

      if (i < 2) {
        delay(3000);
      }
    }
  }

  else if (ultimaQtdMasc == 1 && qtd == 2) {

    tone(buzzerMasc, 1500);
    delay(5000);
    noTone(buzzerMasc);
  }

  ultimaQtdMasc = qtd;
}

// ==========================================
// SETUP
// ==========================================

void setup() {

  Serial.begin(9600);

  pinMode(btnFemPH, INPUT);
  pinMode(btnFemSab, INPUT);
  pinMode(btnResetFem, INPUT);

  pinMode(btnResetMasc, INPUT);
  pinMode(btnMascSab, INPUT);
  pinMode(btnMascPH, INPUT);

  pinMode(ledFemPH, OUTPUT);
  pinMode(ledFemSab, OUTPUT);

  pinMode(ledMascSab, OUTPUT);
  pinMode(ledMascPH, OUTPUT);

  pinMode(buzzerFem, OUTPUT);
  pinMode(buzzerMasc, OUTPUT);

  digitalWrite(ledFemPH, LOW);
  digitalWrite(ledFemSab, LOW);

  digitalWrite(ledMascSab, LOW);
  digitalWrite(ledMascPH, LOW);

  noTone(buzzerFem);
  noTone(buzzerMasc);
}

// ==========================================
// LOOP
// ==========================================

void loop() {

  bool mudouFem  = false;
  bool mudouMasc = false;

  // ---------- FEMININO ----------

  if (digitalRead(btnFemPH) == HIGH && !estadoFemPH) {
    estadoFemPH = true;
    mudouFem = true;
    enviarAlerta("fem", "ph");
  }

  if (digitalRead(btnFemSab) == HIGH && !estadoFemSab) {
    estadoFemSab = true;
    mudouFem = true;
    enviarAlerta("fem", "sab");
  }

  if (digitalRead(btnResetFem) == HIGH) {

    bool tinhaAlgo = estadoFemPH || estadoFemSab;

    estadoFemPH  = false;
    estadoFemSab = false;
    ultimaQtdFem = 0;

    noTone(buzzerFem);

    if (tinhaAlgo) enviarResolucao("fem");
  }

  // ---------- MASCULINO ----------

  if (digitalRead(btnMascSab) == HIGH && !estadoMascSab) {
    estadoMascSab = true;
    mudouMasc = true;
    enviarAlerta("masc", "sab");
  }

  if (digitalRead(btnMascPH) == HIGH && !estadoMascPH) {
    estadoMascPH = true;
    mudouMasc = true;
    enviarAlerta("masc", "ph");
  }

  if (digitalRead(btnResetMasc) == HIGH) {

    bool tinhaAlgo = estadoMascSab || estadoMascPH;

    estadoMascSab = false;
    estadoMascPH  = false;
    ultimaQtdMasc = 0;

    noTone(buzzerMasc);

    if (tinhaAlgo) enviarResolucao("masc");
  }

  // ---------- LEDS ----------

  digitalWrite(ledFemPH,   estadoFemPH);
  digitalWrite(ledFemSab,  estadoFemSab);

  digitalWrite(ledMascSab, estadoMascSab);
  digitalWrite(ledMascPH,  estadoMascPH);

  // ---------- BUZZERS ----------

  if (mudouFem)  verificarBuzzerFem();
  if (mudouMasc) verificarBuzzerMasc();

  delay(50);
}
