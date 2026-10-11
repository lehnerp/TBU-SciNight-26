/*
 * RC522 + MAX7219 na Uno; pár: ../NFC_code_Driver.py.
 * USB 9600 baud: CARD:UID; přijímá OK, WRONG, RESET.
 * Knihovny: MFRC522, LedControl; SPI je součást jádra.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <SPI.h>
#include <MFRC522.h>
#include <LedControl.h>

// ============================================================
// RC522
// ============================================================
//
// SDA / SS -> D10
// SCK      -> D13
// MOSI     -> D11
// MISO     -> D12
// RST      -> D9
// 3.3V     -> 3.3V
//

#define RFID_SS  10
#define RFID_RST 9

MFRC522 rfid(RFID_SS, RFID_RST);


// ============================================================
// MAX7219 8x8
// ============================================================
//
// DIN -> D6
// CLK -> D5
// CS  -> D7
//

LedControl matrix = LedControl(6, 5, 7, 1);


// ============================================================
// SYMBOLY
// ============================================================

byte usmev[8] = {
  B00111100,
  B01000010,
  B10100101,
  B10000001,
  B10100101,
  B10011001,
  B01000010,
  B00111100
};

byte smutek[8] = {
  B00111100,
  B01000010,
  B10100101,
  B10000001,
  B10011001,
  B10100101,
  B01000010,
  B00111100
};


// ============================================================
// SERIOVY PRIKAZ Z PYTHONU
// ============================================================

String prikaz = "";


// ============================================================
// ZOBRAZENI SYMBOLU
// ============================================================

void zobrazSymbol(byte obrazek[8])
{
  matrix.clearDisplay(0);

  for (byte radek = 0; radek < 8; radek++)
  {
    for (byte sloupec = 0; sloupec < 8; sloupec++)
    {
      if (bitRead(obrazek[radek], 7 - sloupec))
      {
        // Otoceni o 90 stupnu doprava
        byte novyRadek = sloupec;
        byte novySloupec = 7 - radek;

        matrix.setLed(
          0,
          novyRadek,
          novySloupec,
          true
        );
      }
    }
  }
}


// ============================================================
// ZPRACOVANI PRIKAZU Z PYTHONU
// ============================================================

void zpracujPrikaz(String cmd)
{
  cmd.trim();

  if (cmd == "OK")
  {
    zobrazSymbol(usmev);

    delay(2000);

    matrix.clearDisplay(0);

    return;
  }

  if (cmd == "WRONG")
  {
    zobrazSymbol(smutek);

    delay(2000);

    matrix.clearDisplay(0);

    return;
  }

  if (cmd == "RESET")
  {
    matrix.clearDisplay(0);

    return;
  }
}


// ============================================================
// CTENI PRIKAZU Z PC
// ============================================================

void ctiPython()
{
  while (Serial.available())
  {
    char c = Serial.read();

    if (c == '\n')
    {
      if (prikaz.length() > 0)
      {
        zpracujPrikaz(prikaz);
      }

      prikaz = "";
      continue;
    }

    if (c == '\r')
    {
      continue;
    }

    if (prikaz.length() < 50)
    {
      prikaz += c;
    }
  }
}


// ============================================================
// ODESLANI UID DO PYTHONU
// ============================================================

void odesliUID()
{
  Serial.print("CARD:");

  for (byte i = 0; i < rfid.uid.size; i++)
  {
    if (rfid.uid.uidByte[i] < 0x10)
    {
      Serial.print("0");
    }

    Serial.print(
      rfid.uid.uidByte[i],
      HEX
    );
  }

  Serial.println();
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  matrix.shutdown(0, false);
  matrix.setIntensity(0, 5);
  matrix.clearDisplay(0);

  Serial.println("RC522:READY");
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  // Nejdrive prijmeme pripadnou odpoved z Pythonu
  ctiPython();

  // Cekame na kartu
  if (!rfid.PICC_IsNewCardPresent())
  {
    return;
  }

  if (!rfid.PICC_ReadCardSerial())
  {
    return;
  }

  // Arduino pouze posle UID.
  // O spravnosti rozhoduje Python.
  odesliUID();

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(500);
}