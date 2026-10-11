/*
 * BLE detektor na ESP32-C3; pár: ../BLE_Scan.py přes USB.
 * 460800 baud: BLE,MAC,RSSI,JMENO; detekuje také vysílač AirWave.
 * Knihovna: NimBLE-Arduino 2.x; ESP32 core.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <NimBLEDevice.h>

// ============================================================
// AIRWAVE // BLE DETEKTOR
// ESP32-C3 / LaskaKit microESP-C3
//
// Serial:
// 460800 baud
//
// Formát:
// BLE,MAC,RSSI,JMENO
//
// například:
// BLE,C2:A1:7A:00:00:01,-54,AirWave
// BLE,61:29:AB:31:12:88,-77,-
// ============================================================


class AirWaveScanCallbacks : public NimBLEScanCallbacks {

  void onResult(
    const NimBLEAdvertisedDevice* device
  ) override {

    // --------------------------------------------------------
    // RSSI
    // --------------------------------------------------------

    int rssi = device->getRSSI();


    // --------------------------------------------------------
    // VÝSTUP
    // --------------------------------------------------------

    Serial.print("BLE,");


    // MAC
    Serial.print(
      device
        ->getAddress()
        .toString()
        .c_str()
    );

    Serial.print(",");


    // RSSI
    Serial.print(rssi);

    Serial.print(",");


    // JMÉNO
    if (device->haveName()) {

      Serial.print(
        device
          ->getName()
          .c_str()
      );

    } else {

      Serial.print("-");
    }


    Serial.println();
  }
};


AirWaveScanCallbacks scanCallbacks;


// ============================================================
// SETUP
// ============================================================

void setup() {

  // Vyšší rychlost sériové linky.
  //
  // Důležité v prostředí s velkým množstvím BLE paketů.

  Serial.begin(460800);

  delay(500);

  Serial.println(
    "AIRWAVE_DETECTOR_START"
  );


  // ==========================================================
  // BLE
  // ==========================================================

  NimBLEDevice::init("");


  NimBLEScan* scan =
    NimBLEDevice::getScan();


  // ==========================================================
  // CALLBACK
  // ==========================================================

  scan->setScanCallbacks(
    &scanCallbacks,
    false
  );


  // ==========================================================
  // AKTIVNÍ SKENOVÁNÍ
  // ==========================================================
  //
  // Active scan může získat také scan-response.
  //
  // Některá zařízení mají jméno právě tam.
  // ==========================================================

  scan->setActiveScan(true);


  // ==========================================================
  // SCAN INTERVAL / WINDOW
  // ==========================================================
  //
  // Window = interval
  //
  // Cílem je vysoký scan duty-cycle.
  // ==========================================================

  scan->setInterval(45);
  scan->setWindow(45);


  // ==========================================================
  // SPUŠTĚNÍ
  // ==========================================================

  scan->start(
    0,
    false
  );


  Serial.println(
    "AIRWAVE_DETECTOR_READY"
  );
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  // NimBLE běží asynchronně.

  delay(1);
}