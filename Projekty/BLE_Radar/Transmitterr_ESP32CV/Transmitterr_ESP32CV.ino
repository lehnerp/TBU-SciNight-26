/*
 * Samostatný BLE vysílač AirWave na ESP32; příjem: detektor + ../BLE_Scan.py.
 * Bez COM spojení s Pythonem; USB 115200 baud slouží diagnostice.
 * Knihovna: NimBLE-Arduino 2.x; ESP32 core, bez externích periferií.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <NimBLEDevice.h>
#include "esp_bt.h"
#include <math.h>

// ============================================================
// AIRWAVE // ORGANIC RF PRESENCE
// LaskaKit microESP-C3
//
// 3 vrstvy:
//   1. přirozený dech
//   2. pomalý pohyb / drift
//   3. jemný mikropohyb
//
// BLE advertising: 20 ms
// ============================================================


// ============================================================
// NASTAVENÍ
// ============================================================

#define UPDATE_MS 20

// Přibližná délka jednoho dechu.
// Každý nový dech dostane malou náhodnou odchylku.
#define BASE_BREATH_MS 4200

// Jak silně ovlivňuje výsledný signál dech
#define BREATH_WEIGHT 0.72f

// Jak silně ovlivňuje výsledný signál pohyb
#define MOVEMENT_WEIGHT 0.28f

// Síla velmi jemného mikropohybu
#define MICRO_AMOUNT 0.025f


// ============================================================
// BLE
// ============================================================

NimBLEAdvertising* adv;


// ============================================================
// RF ÚROVNĚ
// ============================================================
//
// slabý -> silný
//

const esp_power_level_t rfLevels[] = {

  ESP_PWR_LVL_N12,
  ESP_PWR_LVL_N9,
  ESP_PWR_LVL_N6,
  ESP_PWR_LVL_N3,
  ESP_PWR_LVL_N0,
  ESP_PWR_LVL_P3

};

const int RF_COUNT =
  sizeof(rfLevels)
  / sizeof(rfLevels[0]);


// ============================================================
// STAV DECHU
// ============================================================

unsigned long breathStart = 0;

unsigned long currentBreathMs =
  BASE_BREATH_MS;


// ============================================================
// STAV POHYBU
// ============================================================
//
// Pohyb nebudeme generovat jako jednu sinusovku.
//
// Místo toho se pomalu přesouváme mezi náhodnými cílovými
// hodnotami.
//

float movementCurrent = 0.5f;

float movementStartValue = 0.5f;

float movementTarget = 0.5f;

unsigned long movementStart = 0;

unsigned long movementDuration = 8000;


// ============================================================
// POMOCNÉ FUNKCE
// ============================================================

float clamp01(float value) {

  if (value < 0.0f) {
    return 0.0f;
  }

  if (value > 1.0f) {
    return 1.0f;
  }

  return value;
}


// ------------------------------------------------------------
// Smoothstep
// ------------------------------------------------------------

float smoothStep(float x) {

  x = clamp01(x);

  return
    x * x
    * (3.0f - 2.0f * x);
}


// ------------------------------------------------------------
// Jemnější smoothstep
// ------------------------------------------------------------

float smootherStep(float x) {

  x = clamp01(x);

  return
    x * x * x
    * (
        x
        * (
            x * 6.0f
            - 15.0f
          )
        + 10.0f
      );
}


// ------------------------------------------------------------
// Pomalý výdech
// ------------------------------------------------------------

float easeOut(float x) {

  x = clamp01(x);

  return
    1.0f
    - powf(
        1.0f - x,
        2.2f
      );
}


// ============================================================
// NOVÝ DECH
// ============================================================

void startNewBreath() {

  breathStart = millis();


  // ----------------------------------------------------------
  // Každý dech je trochu jiný.
  //
  // cca 3.7 až 4.8 sekundy
  // ----------------------------------------------------------

  currentBreathMs =
    BASE_BREATH_MS
    + random(
        -500,
        601
      );
}


// ============================================================
// NOVÝ CÍL POHYBU
// ============================================================

void startNewMovement() {

  movementStart = millis();

  movementStartValue =
    movementCurrent;


  // ----------------------------------------------------------
  // Nová cílová "pozice"
  //
  // 0 = slabší RF
  // 1 = silnější RF
  //
  // Nedovolujeme úplné extrémy pokaždé.
  // ----------------------------------------------------------

  movementTarget =
    random(
      15,
      86
    ) / 100.0f;


  // ----------------------------------------------------------
  // Jeden pomalý přesun trvá přibližně 6 až 14 sekund.
  // ----------------------------------------------------------

  movementDuration =
    random(
      6000,
      14001
    );
}


// ============================================================
// VÝPOČET DECHU
// ============================================================

float calculateBreath(
  unsigned long now
) {

  unsigned long elapsed =
    now - breathStart;


  // ----------------------------------------------------------
  // Nový dech
  // ----------------------------------------------------------

  if (
    elapsed >= currentBreathMs
  ) {

    startNewBreath();

    elapsed = 0;
  }


  float t =
    (float)elapsed
    / (float)currentBreathMs;


  float breath = 0.0f;


  // ----------------------------------------------------------
  // NÁDECH
  //
  // 0 -> 31 %
  // ----------------------------------------------------------

  if (t < 0.31f) {

    float x =
      t / 0.31f;

    breath =
      smootherStep(x);
  }


  // ----------------------------------------------------------
  // KRÁTKÝ VRCHOL
  //
  // 31 -> 38 %
  // ----------------------------------------------------------

  else if (t < 0.38f) {

    breath = 1.0f;
  }


  // ----------------------------------------------------------
  // VÝDECH
  //
  // 38 -> 88 %
  // ----------------------------------------------------------

  else if (t < 0.88f) {

    float x =
      (
        t - 0.38f
      )
      /
      (
        0.88f - 0.38f
      );

    breath =
      1.0f
      - easeOut(x);
  }


  // ----------------------------------------------------------
  // PAUZA
  //
  // 88 -> 100 %
  // ----------------------------------------------------------

  else {

    breath = 0.0f;
  }


  return clamp01(
    breath
  );
}


// ============================================================
// VÝPOČET POHYBU
// ============================================================

float calculateMovement(
  unsigned long now
) {

  unsigned long elapsed =
    now - movementStart;


  // ----------------------------------------------------------
  // Dosáhli jsme cíle.
  // Vyber nový.
  // ----------------------------------------------------------

  if (
    elapsed >= movementDuration
  ) {

    movementCurrent =
      movementTarget;

    startNewMovement();

    elapsed = 0;
  }


  float t =
    (float)elapsed
    / (float)movementDuration;


  // ----------------------------------------------------------
  // Velmi hladký přechod.
  // ----------------------------------------------------------

  float interpolation =
    smootherStep(t);


  movementCurrent =
    movementStartValue
    +
    (
      movementTarget
      - movementStartValue
    )
    * interpolation;


  return clamp01(
    movementCurrent
  );
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  Serial.begin(
    115200
  );

  delay(
    300
  );


  Serial.println(
    "AIRWAVE // ORGANIC RF PRESENCE"
  );


  // ==========================================================
  // RANDOM
  // ==========================================================

  randomSeed(
    micros()
  );


  // ==========================================================
  // BLE
  // ==========================================================

  NimBLEDevice::init(
    "AirWave"
  );


  adv =
    NimBLEDevice::getAdvertising();


  NimBLEAdvertisementData data;


  data.setName(
    "AirWave"
  );


  adv->setAdvertisementData(
    data
  );


  // ==========================================================
  // NON-CONNECTABLE BEACON
  // ==========================================================

  adv->setConnectableMode(
    BLE_GAP_CONN_MODE_NON
  );


  // ==========================================================
  // 20 ms ADVERTISING
  //
  // 32 * 0.625 ms = 20 ms
  // ==========================================================

  adv->setMinInterval(
    32
  );

  adv->setMaxInterval(
    32
  );


  adv->start();


  // ==========================================================
  // START
  // ==========================================================

  startNewBreath();


  movementCurrent =
    0.5f;

  movementStartValue =
    movementCurrent;

  movementTarget =
    0.65f;

  movementStart =
    millis();

  movementDuration =
    8000;


  Serial.println(
    "Advertising: 20 ms"
  );

  Serial.println(
    "Natural breath: ON"
  );

  Serial.println(
    "Movement drift: ON"
  );

  Serial.println(
    "Micro movement: ON"
  );
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  unsigned long now =
    millis();


  // ==========================================================
  // 1. DECH
  // ==========================================================

  float breath =
    calculateBreath(
      now
    );


  // ==========================================================
  // 2. POHYB
  // ==========================================================

  float movement =
    calculateMovement(
      now
    );


  // ==========================================================
  // 3. MIKROPOHYB
  // ==========================================================
  //
  // Dvě slabé frekvence místo jedné.
  //
  // Díky tomu není mikropohyb dokonale pravidelný.
  // ==========================================================

  float micro1 =
    sinf(
      now * 0.0023f
    );

  float micro2 =
    sinf(
      now * 0.0057f
      + 1.7f
    );


  float micro =
    (
      micro1 * 0.65f
      +
      micro2 * 0.35f
    )
    * MICRO_AMOUNT;


  // ==========================================================
  // SLOUČENÍ
  // ==========================================================

  float signal =
    breath
    * BREATH_WEIGHT
    +
    movement
    * MOVEMENT_WEIGHT
    +
    micro;


  signal =
    clamp01(
      signal
    );


  // ==========================================================
  // PŘEVOD NA RF LEVEL
  // ==========================================================

  int level =
    roundf(
      signal
      * (RF_COUNT - 1)
    );


  level = constrain(
    level,
    0,
    RF_COUNT - 1
  );


  // ==========================================================
  // TX POWER
  // ==========================================================

  esp_ble_tx_power_set(
    ESP_BLE_PWR_TYPE_ADV,
    rfLevels[level]
  );


  // ==========================================================
  // DEBUG
  // ==========================================================

  static int previousLevel = -1;


  if (
    level != previousLevel
  ) {

    previousLevel =
      level;


    Serial.print(
      "RF="
    );

    Serial.print(
      level
    );


    Serial.print(
      "  breath="
    );

    Serial.print(
      breath,
      2
    );


    Serial.print(
      "  movement="
    );

    Serial.print(
      movement,
      2
    );


    Serial.print(
      "  signal="
    );

    Serial.println(
      signal,
      2
    );
  }


  delay(
    UPDATE_MS
  );
}