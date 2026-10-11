/*
 * TFT ST7789 + OLED SH1106 na Mega; pár: ../NFC_code_Driver.py.
 * USB 9600 baud: KEY:krok:kód, WRONG, UNLOCKED, RESET.
 * Knihovny: Adafruit GFX, ST7735/ST7789, SH110X, BusIO.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <SPI.h>
#include <Wire.h>

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <Adafruit_SH110X.h>


// ============================================================
// ST7789 240x240
// ============================================================
//
// Mega:
// MOSI -> 51
// SCK  -> 52
// DC   -> 9
// RST  -> 8
// CS   -> neni
//

#define TFT_DC   9
#define TFT_RST  8
#define TFT_CS  -1

Adafruit_ST7789 tft(
  TFT_CS,
  TFT_DC,
  TFT_RST
);


// ============================================================
// SH1106 128x64
// ============================================================
//
// I2C adresa: 0x3C
// Mega:
// SDA -> 20
// SCL -> 21
//

#define OLED_WIDTH   128
#define OLED_HEIGHT   64
#define OLED_ADDRESS 0x3C

Adafruit_SH1106G oled(
  OLED_WIDTH,
  OLED_HEIGHT,
  &Wire,
  -1
);


// ============================================================
// SERIAL
// ============================================================

String prikaz = "";


// ============================================================
// VYCENTROVANY TEXT NA TFT
// ============================================================

void tftStred(
  const char* text,
  int y,
  int velikost,
  uint16_t barva
)
{
  int16_t x1;
  int16_t y1;
  uint16_t w;
  uint16_t h;

  tft.setTextSize(velikost);
  tft.setTextColor(barva);
  tft.setTextWrap(false);

  tft.getTextBounds(
    text,
    0,
    y,
    &x1,
    &y1,
    &w,
    &h
  );

  tft.setCursor(
    (240 - w) / 2,
    y
  );

  tft.print(text);
}


// ============================================================
// VYCENTROVANY TEXT NA OLED
// ============================================================

void oledStred(
  const char* text,
  int y,
  int velikost
)
{
  int16_t x1;
  int16_t y1;
  uint16_t w;
  uint16_t h;

  oled.setTextSize(velikost);
  oled.setTextColor(SH110X_WHITE);

  oled.getTextBounds(
    text,
    0,
    y,
    &x1,
    &y1,
    &w,
    &h
  );

  oled.setCursor(
    (128 - w) / 2,
    y
  );

  oled.print(text);
}


// ============================================================
// ZELENA FAJFKA
// ============================================================

void kresliFajfku()
{
  tft.drawCircle(
    120,
    87,
    42,
    ST77XX_GREEN
  );

  tft.drawCircle(
    120,
    87,
    41,
    ST77XX_GREEN
  );

  for (int i = -2; i <= 2; i++)
  {
    tft.drawLine(
      94,
      87 + i,
      112,
      105 + i,
      ST77XX_GREEN
    );

    tft.drawLine(
      112,
      105 + i,
      149,
      66 + i,
      ST77XX_GREEN
    );
  }
}


// ============================================================
// CERVENY KRIZEK
// ============================================================

void kresliKrizek()
{
  tft.drawCircle(
    120,
    87,
    42,
    ST77XX_RED
  );

  for (int i = -2; i <= 2; i++)
  {
    tft.drawLine(
      98 + i,
      65,
      142 + i,
      109,
      ST77XX_RED
    );

    tft.drawLine(
      142 + i,
      65,
      98 + i,
      109,
      ST77XX_RED
    );
  }
}


// ============================================================
// POSTUP 0/3 - 3/3
// ============================================================

void kresliPostup(int krok)
{
  int pozice[3] = {
    65,
    120,
    175
  };

  int y = 214;

  tft.drawFastHLine(
    65,
    y,
    110,
    0x8410
  );

  for (int i = 0; i < 3; i++)
  {
    if (i < krok)
    {
      tft.fillCircle(
        pozice[i],
        y,
        8,
        ST77XX_GREEN
      );
    }
    else
    {
      tft.fillCircle(
        pozice[i],
        y,
        8,
        ST77XX_BLACK
      );

      tft.drawCircle(
        pozice[i],
        y,
        8,
        0x8410
      );
    }
  }
}


// ============================================================
// OLED - CAST KODU
// ============================================================

void zobrazKodOLED(
  const char* kod,
  int krok
)
{
  oled.clearDisplay();

  oledStred(
    "PRISTUPOVY KOD",
    0,
    1
  );

  oled.drawLine(
    0,
    12,
    127,
    12,
    SH110X_WHITE
  );

  // Velky kod
  oledStred(
    kod,
    21,
    3
  );

  char postup[10];

  sprintf(
    postup,
    "%d / 3",
    krok
  );

  oledStred(
    postup,
    53,
    1
  );

  oled.display();
}


// ============================================================
// UVODNI OBRAZOVKA
// ============================================================

void zobrazStart()
{
  // ----------------------------------------------------------
  // TFT
  // ----------------------------------------------------------

  tft.fillScreen(ST77XX_BLACK);

  tft.fillRect(
    0,
    0,
    240,
    42,
    0x0010
  );

  tftStred(
    "MOJO",
    13,
    2,
    ST77XX_WHITE
  );

  // Grafika RFID karty
  tft.drawRoundRect(
    55,
    60,
    130,
    80,
    10,
    ST77XX_CYAN
  );

  tft.drawRoundRect(
    58,
    63,
    124,
    74,
    8,
    ST77XX_CYAN
  );

  tft.fillRoundRect(
    72,
    87,
    30,
    22,
    4,
    ST77XX_CYAN
  );

  tft.drawCircle(
    135,
    100,
    10,
    ST77XX_CYAN
  );

  tft.drawCircle(
    135,
    100,
    20,
    ST77XX_CYAN
  );

  tftStred(
    "PRILOZ KARTU",
    158,
    2,
    ST77XX_WHITE
  );

  tftStred(
    "ZACNI SEKVENCI",
    187,
    1,
    ST77XX_YELLOW
  );

  kresliPostup(0);


  // ----------------------------------------------------------
  // OLED
  // ----------------------------------------------------------

  zobrazKodOLED(
    "____",
    0
  );
}


// ============================================================
// SPRAVNY KROK
// ============================================================

void zobrazSpravne(
  int krok,
  const char* kod
)
{
  // ----------------------------------------------------------
  // TFT
  // ----------------------------------------------------------

  tft.fillScreen(
    ST77XX_BLACK
  );

  kresliFajfku();

  tftStred(
    "SPRAVNE",
    145,
    3,
    ST77XX_GREEN
  );

  char postup[10];

  sprintf(
    postup,
    "%d / 3",
    krok
  );

  tftStred(
    postup,
    182,
    2,
    ST77XX_WHITE
  );

  kresliPostup(
    krok
  );


  // ----------------------------------------------------------
  // OLED
  //
  // Zobrazeny kod zustava na displeji.
  // ----------------------------------------------------------

  zobrazKodOLED(
    kod,
    krok
  );
}


// ============================================================
// SPATNA KARTA / PORADI
// ============================================================

void zobrazSpatne()
{
  // ----------------------------------------------------------
  // TFT
  // ----------------------------------------------------------

  tft.fillScreen(
    ST77XX_BLACK
  );

  tft.drawRoundRect(
    8,
    8,
    224,
    224,
    12,
    ST77XX_RED
  );

  kresliKrizek();

  tftStred(
    "SPATNE",
    145,
    3,
    ST77XX_RED
  );

  tftStred(
    "PORADI",
    182,
    2,
    ST77XX_WHITE
  );


  // ----------------------------------------------------------
  // OLED
  // ----------------------------------------------------------

  oled.clearDisplay();

  oledStred(
    "SPATNE PORADI",
    5,
    1
  );

  oledStred(
    "X",
    20,
    4
  );

  oledStred(
    "RESET...",
    53,
    1
  );

  oled.display();
}


// ============================================================
// HOTOVO / ODEMCENO
// ============================================================

void zobrazOdemceno()
{
  // ----------------------------------------------------------
  // TFT
  // ----------------------------------------------------------

  tft.fillScreen(
    ST77XX_BLACK
  );

  tft.drawRoundRect(
    8,
    8,
    224,
    224,
    12,
    ST77XX_GREEN
  );

  kresliFajfku();

  tftStred(
    "ODEMCENO",
    145,
    3,
    ST77XX_GREEN
  );

  tftStred(
    "2012",
    185,
    3,
    ST77XX_WHITE
  );

  kresliPostup(3);


  // ----------------------------------------------------------
  // OLED
  // ----------------------------------------------------------

  oled.clearDisplay();

  oledStred(
    "PRISTUPOVY KOD",
    0,
    1
  );

  oled.drawLine(
    0,
    12,
    127,
    12,
    SH110X_WHITE
  );

  oledStred(
    "2012",
    20,
    3
  );

  oledStred(
    "ODEMCENO",
    53,
    1
  );

  oled.display();
}


// ============================================================
// ZPRACOVANI PRIKAZU Z PYTHONU
// ============================================================

void zpracujPrikaz(String cmd)
{
  cmd.trim();

  if (cmd == "RESET")
  {
    zobrazStart();

    Serial.println(
      "DISPLAY:RESET"
    );

    return;
  }


  if (cmd == "KEY:1:2___")
  {
    zobrazSpravne(
      1,
      "2___"
    );

    Serial.println(
      "DISPLAY:KROK1"
    );

    return;
  }


  if (cmd == "KEY:2:20__")
  {
    zobrazSpravne(
      2,
      "20__"
    );

    Serial.println(
      "DISPLAY:KROK2"
    );

    return;
  }


  if (cmd == "KEY:3:2012")
  {
    zobrazSpravne(
      3,
      "2012"
    );

    Serial.println(
      "DISPLAY:KROK3"
    );

    return;
  }


  if (cmd == "WRONG")
  {
    zobrazSpatne();

    Serial.println(
      "DISPLAY:SPATNE"
    );

    return;
  }


  if (cmd == "UNLOCKED")
  {
    zobrazOdemceno();

    Serial.println(
      "DISPLAY:ODEMCENO"
    );

    return;
  }


  Serial.print(
    "DISPLAY:NEZNAMY:"
  );

  Serial.println(
    cmd
  );
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(9600);

  Wire.begin();


  // ----------------------------------------------------------
  // SH1106
  // ----------------------------------------------------------

  if (!oled.begin(OLED_ADDRESS, true))
  {
    Serial.println(
      "OLED:CHYBA"
    );
  }
  else
  {
    Serial.println(
      "OLED:OK"
    );
  }


  // ----------------------------------------------------------
  // ST7789
  //
  // Overene nastaveni tveho M130T.
  // ----------------------------------------------------------

  tft.init(
    240,
    240,
    SPI_MODE3
  );

  tft.setSPISpeed(
    1000000
  );

  tft.setRotation(
    2
  );


  zobrazStart();

  Serial.println(
    "DISPLAY:READY"
  );
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  while (Serial.available())
  {
    char c = Serial.read();

    if (c == '\n')
    {
      if (prikaz.length() > 0)
      {
        zpracujPrikaz(
          prikaz
        );
      }

      prikaz = "";

      continue;
    }

    if (c == '\r')
    {
      continue;
    }

    if (prikaz.length() < 100)
    {
      prikaz += c;
    }
  }
}