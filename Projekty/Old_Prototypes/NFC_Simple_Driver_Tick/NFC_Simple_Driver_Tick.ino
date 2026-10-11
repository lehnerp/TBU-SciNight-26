/*
* RC522 < - > Arduino Uno
* SDA / SS < - > D10
* SCK < - > D13
* MOSI < - > D11
* MISO < - > D12
* IRQ < - > Not connected
* GND < - > GND
* RST < - > D9
* 3.3V < - > 3.3V
*/

#include <SPI.h>
#include <MFRC522.h>
#include <LedControl.h>

// ---------------- RFID ----------------
#define RFID_SS  10
#define RFID_RST 9

MFRC522 rfid(RFID_SS, RFID_RST);

// -------------- MATRIX ----------------
// DIN = D6
// CLK = D5
// CS  = D7
LedControl matrix = LedControl(6, 5, 7, 1);

// ---------- ALLOWED CARD ----------
byte allowedUID[4] = {0xA0, 0x5E, 0xE1, 0x28};

// ---------------- TICK -----------------
byte tick[8] = {
  B00000000,
  B00000001,
  B00000010,
  B00000100,
  B10001000,
  B01010000,
  B00100000,
  B00000000
};

// ------------------ X ------------------
byte cross[8] = {
  B10000001,
  B01000010,
  B00100100,
  B00011000,
  B00011000,
  B00100100,
  B01000010,
  B10000001
};

void setup() {
  Serial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  matrix.shutdown(0, false);
  matrix.setIntensity(0, 5);
  matrix.clearDisplay(0);

  Serial.println("Ready - scan card");
}

void showSymbol(byte image[8]) {

  matrix.clearDisplay(0);

  // Rotate image 90 degrees clockwise
  for (byte row = 0; row < 8; row++) {
    for (byte col = 0; col < 8; col++) {

      if (bitRead(image[row], 7 - col)) {

        byte newRow = col;
        byte newCol = 7 - row;

        matrix.setLed(0, newRow, newCol, true);
      }
    }
  }
}

bool cardAllowed() {
  if (rfid.uid.size != 4) {
    return false;
  }

  for (byte i = 0; i < 4; i++) {
    if (rfid.uid.uidByte[i] != allowedUID[i]) {
      return false;
    }
  }

  return true;
}

void loop() {

  // Wait for a new card
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Print UID
  Serial.print("Card UID: ");

  for (byte i = 0; i < rfid.uid.size; i++) {

    if (rfid.uid.uidByte[i] < 0x10) {
      Serial.print("0");
    }

    Serial.print(rfid.uid.uidByte[i], HEX);

    if (i < rfid.uid.size - 1) {
      Serial.print(":");
    }
  }

  Serial.println();

  // Show result
  if (cardAllowed()) {
    Serial.println("ACCESS GRANTED");
    showSymbol(tick);
  } else {
    Serial.println("ACCESS DENIED");
    showSymbol(cross);
  }

  // Keep symbol visible
  delay(2000);

  // CLEAR DISPLAY
  matrix.clearDisplay(0);

  // End communication
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  // Wait until the card is removed
  while (rfid.PICC_IsNewCardPresent()) {
    delay(100);
  }

  delay(300);
}
