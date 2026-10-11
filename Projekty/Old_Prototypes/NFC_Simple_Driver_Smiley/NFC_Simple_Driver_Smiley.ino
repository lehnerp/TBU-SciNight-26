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

// ---------------- SMILEY ----------------
byte smiley[8] = {
  B00111100,
  B01000010,
  B10100101,
  B10000001,
  B10100101,
  B10011001,
  B01000010,
  B00111100
};

// ---------------- CRY / SAD ----------------
byte cry[8] = {
  B00111100,
  B01000010,
  B10100101,
  B10000001,
  B10011001,
  B10100101,
  B01000010,
  B00111100
};

void setup() {
  Serial.begin(9600);

  // Start RFID
  SPI.begin();
  rfid.PCD_Init();

  // Start matrix
  matrix.shutdown(0, false);
  matrix.setIntensity(0, 5);
  matrix.clearDisplay(0);

  Serial.println("Ready - scan card");
}


// Show image ROTATED 90 degrees clockwise
void showSymbol(byte image[8]) {

  matrix.clearDisplay(0);

  for (byte row = 0; row < 8; row++) {

    for (byte col = 0; col < 8; col++) {

      // Read original pixel
      if (bitRead(image[row], 7 - col)) {

        // Rotate 90 degrees clockwise
        byte newRow = col;
        byte newCol = 7 - row;

        matrix.setLed(0, newRow, newCol, true);
      }
    }
  }
}


// Check allowed UID
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

  // Wait for RFID card
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


  // Check access
  if (cardAllowed()) {

    Serial.println("ACCESS GRANTED");

    // :)
    showSymbol(smiley);

  } else {

    Serial.println("ACCESS DENIED");

    // :(
    showSymbol(cry);
  }


  // Show for 2 seconds
  delay(2000);

  // Blank display
  matrix.clearDisplay(0);


  // Stop RFID communication
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(1000);
}