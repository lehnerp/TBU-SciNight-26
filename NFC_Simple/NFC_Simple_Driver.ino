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

// RC522 pins for Arduino Uno
#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  // Small delay to let the reader initialize
  delay(100);
}

void loop() {

  // Check if a new card is present
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  // Read the card UID
  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Send UID to Python in format:
  // 53:A7:21:0D

  for (byte i = 0; i < rfid.uid.size; i++) {

    // Add leading zero if needed
    if (rfid.uid.uidByte[i] < 0x10) {
      Serial.print("0");
    }

    Serial.print(rfid.uid.uidByte[i], HEX);

    // Add ":" between bytes
    if (i < rfid.uid.size - 1) {
      Serial.print(":");
    }
  }

  // Finish the line
  Serial.println();

  // Stop communication with this card
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  // Prevent repeated scans immediately
  delay(1000);
}