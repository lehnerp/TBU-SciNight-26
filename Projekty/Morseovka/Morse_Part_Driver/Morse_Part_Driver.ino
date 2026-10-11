/*
 * Světelná Morseovka na Mega 2560; pár: ../Morse_Driver.py.
 * USB 115200 baud: CLEAR, MORSE:, LETTER:, RESULT:text|morse.
 * Bez externích knihoven; IR D2–D6 a RGB D22–D36.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

// ============================================================
// SCIENCE FAIR – MORSEOVKA SVĚTLEM
// Arduino Mega 2560
//
// UTB = ..-  -  -...
// FAI = ..-. .-  ..
//
// 5x IR:
//   D2, D3, D4, D5, D6
//
// 5x KY-016:
//   RGB1 = 22,23,24
//   RGB2 = 25,26,27
//   RGB3 = 28,29,30
//   RGB4 = 31,32,33
//   RGB5 = 34,35,36
//
// KY-016 "-" -> GND
//
// Průběh:
// 1. IR pomalu, písmeno po písmenu
// 2. Celý výsledek + rychlé IR
// 3. Pauza
// 4. RGB pomalu, písmeno po písmenu
// 5. Celý výsledek + rychlé RGB
// ============================================================


// ============================================================
// PINY
// ============================================================

const byte IR[5] = {
  2, 3, 4, 5, 6
};

const byte RGB[5][3] = {
  {22, 23, 24},
  {25, 26, 27},
  {28, 29, 30},
  {31, 32, 33},
  {34, 35, 36}
};


// ============================================================
// POMALÁ MORSEOVKA
// ============================================================

const unsigned int TECKA = 300;
const unsigned int CARKA = 900;

const unsigned int MEZERA_ZNAK = 300;

const unsigned int ZOBRAZ_PISMENO = 1400;

const unsigned int PAUZA_PISMENO = 500;


// ============================================================
// RYCHLÁ MORSEOVKA
// ============================================================

const unsigned int FAST_TECKA = 120;
const unsigned int FAST_CARKA = 360;

const unsigned int FAST_MEZERA_ZNAK = 120;
const unsigned int FAST_MEZERA_PISMENO = 360;


// ============================================================
// VELKÉ PAUZY
// ============================================================

// Po rychlém finálním přehrání
const unsigned long ZOBRAZ_VYSLEDEK = 3000;

// IR -> RGB
const unsigned long PAUZA_IR_RGB = 5000;

// UTB -> FAI
const unsigned long PAUZA_ZPRAVA = 6000;

// Po FAI před opakováním
const unsigned long PAUZA_OPAKOVANI = 8000;


// ============================================================
// VŠECHNO VYPNOUT
// ============================================================

void vseVypnout() {

  for (byte i = 0; i < 5; i++) {

    digitalWrite(IR[i], LOW);

    digitalWrite(RGB[i][0], LOW);
    digitalWrite(RGB[i][1], LOW);
    digitalWrite(RGB[i][2], LOW);
  }
}


// ============================================================
// KOMUNIKACE S PYTHONEM
// ============================================================

void vycistitObrazovku() {

  Serial.println("CLEAR");
}


void zobrazMorse(String morse) {

  Serial.print("MORSE:");
  Serial.println(morse);
}


void zobrazPismeno(char pismeno) {

  Serial.print("LETTER:");
  Serial.println(pismeno);
}


void zobrazVysledek(String text, String morse) {

  Serial.print("RESULT:");
  Serial.print(text);
  Serial.print("|");
  Serial.println(morse);
}


// ============================================================
// POMALÝ IR IMPULZ
// ============================================================

void irImpulz(unsigned int delka) {

  for (byte i = 0; i < 5; i++) {
    digitalWrite(IR[i], HIGH);
  }

  delay(delka);

  for (byte i = 0; i < 5; i++) {
    digitalWrite(IR[i], LOW);
  }

  delay(MEZERA_ZNAK);
}


// ============================================================
// POMALÝ RGB IMPULZ
// ============================================================

void rgbImpulz(
  unsigned int delka,
  bool R,
  bool G,
  bool B
) {

  for (byte i = 0; i < 5; i++) {

    digitalWrite(RGB[i][0], R);
    digitalWrite(RGB[i][1], G);
    digitalWrite(RGB[i][2], B);
  }

  delay(delka);

  for (byte i = 0; i < 5; i++) {

    digitalWrite(RGB[i][0], LOW);
    digitalWrite(RGB[i][1], LOW);
    digitalWrite(RGB[i][2], LOW);
  }

  delay(MEZERA_ZNAK);
}


// ============================================================
// JEDNO PÍSMENO – IR
// ============================================================

void posliPismenoIR(
  const char* kod,
  char pismeno
) {

  String aktualni = "";

  for (int i = 0; kod[i] != '\0'; i++) {

    aktualni += kod[i];

    // Na obrazovce postupně:
    //
    // .
    // ..
    // ..-

    zobrazMorse(aktualni);

    if (kod[i] == '.') {
      irImpulz(TECKA);
    }
    else {
      irImpulz(CARKA);
    }
  }

  // Po dokončení Morseovky
  // zobraz písmeno

  zobrazPismeno(pismeno);

  delay(ZOBRAZ_PISMENO);

  vycistitObrazovku();

  delay(PAUZA_PISMENO);
}


// ============================================================
// JEDNO PÍSMENO – RGB
// ============================================================

void posliPismenoRGB(
  const char* kod,
  char pismeno,
  bool R,
  bool G,
  bool B
) {

  String aktualni = "";

  for (int i = 0; kod[i] != '\0'; i++) {

    aktualni += kod[i];

    zobrazMorse(aktualni);

    if (kod[i] == '.') {

      rgbImpulz(
        TECKA,
        R,G,B
      );
    }

    else {

      rgbImpulz(
        CARKA,
        R,G,B
      );
    }
  }

  zobrazPismeno(pismeno);

  delay(ZOBRAZ_PISMENO);

  vycistitObrazovku();

  delay(PAUZA_PISMENO);
}


// ============================================================
// RYCHLÝ IR ZNAK
// ============================================================

void rychlyIRZnak(char znak) {

  unsigned int delka;

  if (znak == '.') {
    delka = FAST_TECKA;
  }
  else {
    delka = FAST_CARKA;
  }


  // IR ON

  for (byte i = 0; i < 5; i++) {
    digitalWrite(IR[i], HIGH);
  }


  delay(delka);


  // IR OFF

  for (byte i = 0; i < 5; i++) {
    digitalWrite(IR[i], LOW);
  }


  delay(FAST_MEZERA_ZNAK);
}


// ============================================================
// RYCHLÉ IR PÍSMENO
// ============================================================

void rychleIRPismeno(const char* kod) {

  for (int i = 0; kod[i] != '\0'; i++) {

    rychlyIRZnak(
      kod[i]
    );
  }

  delay(
    FAST_MEZERA_PISMENO
  );
}


// ============================================================
// RYCHLÝ RGB ZNAK
// ============================================================

void rychlyRGBZnak(
  char znak,
  bool R,
  bool G,
  bool B
) {

  unsigned int delka;

  if (znak == '.') {
    delka = FAST_TECKA;
  }
  else {
    delka = FAST_CARKA;
  }


  // RGB ON

  for (byte i = 0; i < 5; i++) {

    digitalWrite(RGB[i][0], R);
    digitalWrite(RGB[i][1], G);
    digitalWrite(RGB[i][2], B);
  }


  delay(delka);


  // RGB OFF

  for (byte i = 0; i < 5; i++) {

    digitalWrite(RGB[i][0], LOW);
    digitalWrite(RGB[i][1], LOW);
    digitalWrite(RGB[i][2], LOW);
  }


  delay(FAST_MEZERA_ZNAK);
}


// ============================================================
// RYCHLÉ RGB PÍSMENO
// ============================================================

void rychleRGBPismeno(
  const char* kod,
  bool R,
  bool G,
  bool B
) {

  for (int i = 0; kod[i] != '\0'; i++) {

    rychlyRGBZnak(
      kod[i],
      R,G,B
    );
  }

  delay(
    FAST_MEZERA_PISMENO
  );
}


// ============================================================
// UTB – IR
// ============================================================

void UTB_IR() {

  vycistitObrazovku();


  // --------------------------------
  // U = ..-
  // --------------------------------

  posliPismenoIR(
    "..-",
    'U'
  );


  // --------------------------------
  // T = -
  // --------------------------------

  posliPismenoIR(
    "-",
    'T'
  );


  // --------------------------------
  // B = -...
  // --------------------------------

  posliPismenoIR(
    "-...",
    'B'
  );


  // ==================================================
  // CELÝ VÝSLEDEK
  // ==================================================

  zobrazVysledek(
    "UTB",
    "..-   -   -..."
  );


  // Rychlé přehrání celé zprávy

  rychleIRPismeno("..-");
  rychleIRPismeno("-");
  rychleIRPismeno("-...");


  delay(
    ZOBRAZ_VYSLEDEK
  );


  vycistitObrazovku();
}


// ============================================================
// UTB – RGB
// ============================================================

void UTB_RGB() {

  /*
     UTB = ORANŽOVÁ

     Kvůli nepřítomnosti PWM na D22-D36
     používáme stabilní kombinaci:

     R = ON
     G = ON
     B = OFF

     Bez softwarového PWM = žádné vibrování.
  */

  const bool R = HIGH;
  const bool G = HIGH;
  const bool B = LOW;


  vycistitObrazovku();


  // U
  posliPismenoRGB(
    "..-",
    'U',
    R,G,B
  );


  // T
  posliPismenoRGB(
    "-",
    'T',
    R,G,B
  );


  // B
  posliPismenoRGB(
    "-...",
    'B',
    R,G,B
  );


  // Celý výsledek

  zobrazVysledek(
    "UTB",
    "..-   -   -..."
  );


  // Rychlé přehrání

  rychleRGBPismeno(
    "..-",
    R,G,B
  );

  rychleRGBPismeno(
    "-",
    R,G,B
  );

  rychleRGBPismeno(
    "-...",
    R,G,B
  );


  delay(
    ZOBRAZ_VYSLEDEK
  );


  vycistitObrazovku();
}


// ============================================================
// FAI – IR
// ============================================================

void FAI_IR() {

  vycistitObrazovku();


  // F = ..-.

  posliPismenoIR(
    "..-.",
    'F'
  );


  // A = .-

  posliPismenoIR(
    ".-",
    'A'
  );


  // I = ..

  posliPismenoIR(
    "..",
    'I'
  );


  // Celý výsledek

  zobrazVysledek(
    "FAI",
    "..-.   .-   .."
  );


  // Rychlé přehrání

  rychleIRPismeno("..-.");
  rychleIRPismeno(".-");
  rychleIRPismeno("..");


  delay(
    ZOBRAZ_VYSLEDEK
  );


  vycistitObrazovku();
}


// ============================================================
// FAI – RGB
// ============================================================

void FAI_RGB() {

  /*
     FAI = ŽLUTÁ / ZLATÁ

     Požadovaná barva byla RGB(255,205,0).

     Bez PWM používáme stabilní:
     R = ON
     G = ON
     B = OFF
  */

  const bool R = HIGH;
  const bool G = HIGH;
  const bool B = LOW;


  vycistitObrazovku();


  // F
  posliPismenoRGB(
    "..-.",
    'F',
    R,G,B
  );


  // A
  posliPismenoRGB(
    ".-",
    'A',
    R,G,B
  );


  // I
  posliPismenoRGB(
    "..",
    'I',
    R,G,B
  );


  // Celý výsledek

  zobrazVysledek(
    "FAI",
    "..-.   .-   .."
  );


  // Rychlé přehrání

  rychleRGBPismeno(
    "..-.",
    R,G,B
  );

  rychleRGBPismeno(
    ".-",
    R,G,B
  );

  rychleRGBPismeno(
    "..",
    R,G,B
  );


  delay(
    ZOBRAZ_VYSLEDEK
  );


  vycistitObrazovku();
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  Serial.begin(115200);


  // IR

  for (byte i = 0; i < 5; i++) {

    pinMode(
      IR[i],
      OUTPUT
    );

    digitalWrite(
      IR[i],
      LOW
    );
  }


  // RGB

  for (byte i = 0; i < 5; i++) {

    pinMode(
      RGB[i][0],
      OUTPUT
    );

    pinMode(
      RGB[i][1],
      OUTPUT
    );

    pinMode(
      RGB[i][2],
      OUTPUT
    );
  }


  vseVypnout();


  // Čas na spuštění Python aplikace

  delay(2000);
}


// ============================================================
// HLAVNÍ PROGRAM
// ============================================================

void loop() {

  // ==================================================
  // 1. UTB – NEVIDITELNÉ IR
  // ==================================================

  UTB_IR();


  // Delší pauza

  delay(
    PAUZA_IR_RGB
  );


  // ==================================================
  // 2. UTB – VIDITELNÉ RGB
  // ==================================================

  UTB_RGB();


  // Pauza před FAI

  delay(
    PAUZA_ZPRAVA
  );


  // ==================================================
  // 3. FAI – NEVIDITELNÉ IR
  // ==================================================

  FAI_IR();


  // Delší pauza

  delay(
    PAUZA_IR_RGB
  );


  // ==================================================
  // 4. FAI – VIDITELNÉ RGB
  // ==================================================

  FAI_RGB();


  // Dlouhá pauza před novým kolem

  delay(
    PAUZA_OPAKOVANI
  );
}