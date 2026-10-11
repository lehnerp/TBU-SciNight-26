/*
 * RFID + TFT/QR na Mega 2560; pár: ../RFID_code_Driver.py.
 * USB 115200 baud: RFID_OK, NOT_OK, TASK_DONE (po zobrazení QR).
 * Knihovny: Adafruit GFX, ST7735/ST7789, QRCode; SPI je součást jádra.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <qrcode.h>
#include <avr/pgmspace.h>


// ======================================================
// NASTAVENI
// ======================================================

const char* DEVICE_ID = "RFID01";

// SEM DEJ ID SPRAVNE KARTY
const char* SPRAVNA_KARTA = "4C00411FB3A1";

// OBSAH QR KODU
const char QR_TEXT[] = "https://example.com";


// ======================================================
// CASY
// ======================================================

// Spravna karta bude zobrazena 3 sekundy
const unsigned long CAS_SPRAVNE_KARTY = 3000;

// Spatna karta bude zobrazena 3 sekundy
const unsigned long CAS_SPATNE_KARTY = 3000;

// Po teto dobe bez RFID dat povazujeme kartu za odebranou
const unsigned long CAS_ODEBRANI = 1200;


// ======================================================
// TFT ST7789 240x240
//
// MEGA 2560:
//
// GND       -> GND
// VCC       -> 3.3V
// SCL/SCK   -> 52
// SDA/MOSI  -> 51
// RES       -> 8
// DC        -> 9
// BLK       -> 3.3V
// ======================================================

#define TFT_DC   9
#define TFT_RST  8
#define TFT_CS  -1

Adafruit_ST7789 tft(TFT_CS, TFT_DC, TFT_RST);


// ======================================================
// RFID RDM6300
//
// VCC -> 5V
// GND -> GND
// TX  -> MEGA pin 19 / RX1
// ======================================================

#define RFID Serial1

char rfidBuffer[20];

byte rfidIndex = 0;

bool prijimam = false;


// ======================================================
// STAV SYSTEMU
// ======================================================

String posledniKarta = "";

unsigned long posledniCas = 0;


// ------------------------------------------------------
// SPRAVNA KARTA / QR
// ------------------------------------------------------

bool ukolSplnen = false;

bool spravnaKartaZobrazena = false;

unsigned long casSpravneKarty = 0;


// ------------------------------------------------------
// SPATNA KARTA
// ------------------------------------------------------

bool spatnaKartaZobrazena = false;

unsigned long casSpatneKarty = 0;


// ======================================================
// FAI LOGO 32x32
// ======================================================

const uint32_t PROGMEM faiLogo[32] =
{
  0x03FFF800UL,
  0x07FFE000UL,
  0x07FF0000UL,
  0x07F800E0UL,
  0x07C007E0UL,
  0x06003FE0UL,
  0x0001FFE0UL,
  0x0007FFE0UL,

  0x063FFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,

  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,
  0x07FFFFE0UL,

  0x07FFFFE0UL,
  0x07FFFFC0UL,
  0x07FFFF00UL,
  0x07FFF800UL,
  0x07FFC000UL,
  0x07FE0000UL,
  0x03F80000UL,
  0x01C00000UL
};


// ======================================================
// TEXT NA STRED
// ======================================================

void textStred(
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


// ======================================================
// RFID IKONA
// ======================================================

void ikonaKarty()
{
  uint16_t barva = ST77XX_CYAN;

  // Karta
  tft.drawRoundRect(
    65,
    65,
    110,
    72,
    8,
    barva
  );

  tft.drawRoundRect(
    68,
    68,
    104,
    66,
    6,
    barva
  );

  // Cip
  tft.fillRoundRect(
    82,
    90,
    25,
    20,
    3,
    barva
  );

  // RFID vlny
  tft.drawCircle(
    135,
    103,
    7,
    barva
  );

  tft.drawCircle(
    135,
    103,
    15,
    barva
  );

  tft.drawCircle(
    135,
    103,
    23,
    barva
  );
}


// ======================================================
// UVODNI OBRAZOVKA
// ======================================================

void zobrazCekani()
{
  tft.fillScreen(ST77XX_BLACK);

  // Horni lista
  tft.fillRect(
    0,
    0,
    240,
    42,
    0x0010
  );

  textStred(
    "RFID UKOL",
    13,
    2,
    ST77XX_WHITE
  );

  ikonaKarty();

  textStred(
    "PRILOZ KARTU",
    158,
    2,
    ST77XX_WHITE
  );

  textStred(
    "CEKAM...",
    190,
    1,
    ST77XX_YELLOW
  );

  tft.drawFastHLine(
    15,
    215,
    210,
    0x8410
  );

  textStred(
    "SYSTEM PRIPRAVEN",
    222,
    1,
    0x8410
  );
}


// ======================================================
// SPRAVNA KARTA
// ======================================================

void zobrazSpravnou()
{
  tft.fillScreen(ST77XX_BLACK);

  // Zeleny ramecek
  tft.drawRoundRect(
    10,
    10,
    220,
    220,
    12,
    ST77XX_GREEN
  );

  tft.drawRoundRect(
    13,
    13,
    214,
    214,
    10,
    ST77XX_GREEN
  );

  // Zeleny kruh
  tft.drawCircle(
    120,
    78,
    38,
    ST77XX_GREEN
  );

  tft.drawCircle(
    120,
    78,
    37,
    ST77XX_GREEN
  );

  // Fajfka
  for (int i = -2; i <= 2; i++)
  {
    tft.drawLine(
      96,
      78 + i,
      113,
      95 + i,
      ST77XX_GREEN
    );

    tft.drawLine(
      113,
      95 + i,
      146,
      61 + i,
      ST77XX_GREEN
    );
  }

  textStred(
    "SPRAVNA",
    137,
    3,
    ST77XX_WHITE
  );

  textStred(
    "KARTA",
    174,
    3,
    ST77XX_GREEN
  );

  textStred(
    "GENERUJI QR...",
    215,
    1,
    ST77XX_WHITE
  );
}


// ======================================================
// SPATNA KARTA
// ======================================================

void zobrazSpatnou()
{
  tft.fillScreen(ST77XX_BLACK);

  // Cerveny ramecek
  tft.drawRoundRect(
    10,
    10,
    220,
    220,
    12,
    ST77XX_RED
  );

  tft.drawRoundRect(
    13,
    13,
    214,
    214,
    10,
    ST77XX_RED
  );

  // Cerveny kruh
  tft.drawCircle(
    120,
    78,
    38,
    ST77XX_RED
  );

  tft.drawCircle(
    120,
    78,
    37,
    ST77XX_RED
  );

  // X
  for (int i = -2; i <= 2; i++)
  {
    tft.drawLine(
      101 + i,
      59,
      139 + i,
      97,
      ST77XX_RED
    );

    tft.drawLine(
      139 + i,
      59,
      101 + i,
      97,
      ST77XX_RED
    );
  }

  textStred(
    "SPATNA",
    137,
    3,
    ST77XX_WHITE
  );

  textStred(
    "KARTA",
    174,
    3,
    ST77XX_RED
  );

  textStred(
    "ZKUS TO ZNOVU",
    215,
    1,
    ST77XX_WHITE
  );
}


// ======================================================
// FAI LOGO
// ======================================================

void drawFAILogo(
  int centerX,
  int centerY
)
{
  int startX = centerX - 16;
  int startY = centerY - 16;

  // FAI zluta #FECB00
  uint16_t faiYellow =
    tft.color565(
      254,
      203,
      0
    );

  // Bila ochranna plocha pod logem
  tft.fillRect(
    startX - 3,
    startY - 3,
    38,
    38,
    ST77XX_WHITE
  );

  // Logo
  for (int y = 0; y < 32; y++)
  {
    uint32_t row =
      pgm_read_dword(
        &faiLogo[y]
      );

    for (int x = 0; x < 32; x++)
    {
      if (
        row &
        (0x80000000UL >> x)
      )
      {
        tft.drawPixel(
          startX + x,
          startY + y,
          faiYellow
        );
      }
    }
  }
}


// ======================================================
// QR KOD
// ======================================================

void drawQRCode(
  const char* text
)
{
  QRCode qrcode;

  const uint8_t QR_VERSION = 5;

  uint8_t qrcodeData[
    qrcode_getBufferSize(
      QR_VERSION
    )
  ];

  // HIGH error correction
  qrcode_initText(
    &qrcode,
    qrcodeData,
    QR_VERSION,
    ECC_HIGH,
    text
  );

  const int SCALE = 5;
  const int QUIET = 4;

  int totalModules =
    qrcode.size +
    (QUIET * 2);

  int totalPixels =
    totalModules *
    SCALE;

  int startX =
    (240 - totalPixels) / 2;

  int startY =
    (240 - totalPixels) / 2;

  // Bile pozadi
  tft.fillScreen(
    ST77XX_WHITE
  );

  // QR
  for (
    uint8_t y = 0;
    y < qrcode.size;
    y++
  )
  {
    for (
      uint8_t x = 0;
      x < qrcode.size;
      x++
    )
    {
      if (
        qrcode_getModule(
          &qrcode,
          x,
          y
        )
      )
      {
        int px =
          startX +
          ((x + QUIET) * SCALE);

        int py =
          startY +
          ((y + QUIET) * SCALE);

        tft.fillRect(
          px,
          py,
          SCALE,
          SCALE,
          ST77XX_BLACK
        );
      }
    }
  }

  // FAI logo doprostred
  drawFAILogo(
    120,
    120
  );
}


// ======================================================
// START SPRAVNE KARTY
// ======================================================

void spravnaKarta()
{
  // Pokud uz je QR / ukol splnen,
  // dalsi SPRAVNOU kartu ignorujeme.
  if (ukolSplnen)
  {
    return;
  }

  // Od teto chvile je ukol splnen
  ukolSplnen = true;

  // Vypnout pripadny stav spatne karty
  spatnaKartaZobrazena = false;

  // Zapnout 3s stav spravne karty
  spravnaKartaZobrazena = true;

  casSpravneKarty = millis();

  // Nejdrive zobraz SPRAVNA KARTA
  zobrazSpravnou();


  // ======================================================
  // FIX: SPRAVNA KARTA -> RFID_OK
  // ======================================================

  Serial.println("RFID_OK");


  // Informace pro PC
  Serial.print("ID:");
  Serial.print(DEVICE_ID);
  Serial.println(";STATUS:DONE");
}


// ======================================================
// SPATNA KARTA / RESET PROCESU
// ======================================================

void spatnaKarta()
{
  // ====================================================
  // TOTO FUNGUJE I KDYZ JE ZOBRAZEN QR
  //
  // Spatna karta zrusi splneny ukol
  // a spusti proces znovu.
  // ====================================================

  ukolSplnen = false;

  spravnaKartaZobrazena = false;

  spatnaKartaZobrazena = true;

  casSpatneKarty = millis();

  zobrazSpatnou();


  // ======================================================
  // FIX: SPATNA KARTA -> NOT_OK
  // ======================================================

  Serial.println("NOT_OK");


  // Informace pro PC
  Serial.print("ID:");
  Serial.print(DEVICE_ID);
  Serial.println(";STATUS:WRONG");
}


// ======================================================
// ZPRACOVANI RFID KARTY
// ======================================================

void zpracujKartu()
{
  String karta =
    String(rfidBuffer);

  unsigned long ted =
    millis();


  // ====================================================
  // STEJNA KARTA JE STALE PRILOZENA
  //
  // RDM6300 ji posila porad dokola.
  // Nechceme opakovane prekreslovani.
  // ====================================================

  if (
    karta ==
    posledniKarta
  )
  {
    posledniCas = ted;

    return;
  }


  // ====================================================
  // NOVA KARTA
  // ====================================================

  posledniKarta = karta;

  posledniCas = ted;


  // Diagnostika
  Serial.print("RFID:");
  Serial.println(karta);


  // ====================================================
  // JE TO SPRAVNA KARTA?
  // ====================================================

  if (
    karta ==
    SPRAVNA_KARTA
  )
  {
    spravnaKarta();

    return;
  }


  // ====================================================
  // JINAK JE SPATNA
  //
  // POZOR:
  // Toto se provede i kdyz je zobrazen QR.
  // ====================================================

  spatnaKarta();
}


// ======================================================
// SETUP
// ======================================================

void setup()
{
  // USB -> PC
  Serial.begin(
    115200
  );


  // RDM6300
  RFID.begin(
    9600
  );


  // TFT
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


  // Uvodni obrazovka
  zobrazCekani();


  // Stanice pripravena
  Serial.print("ID:");
  Serial.print(DEVICE_ID);
  Serial.println(";STATUS:READY");
}


// ======================================================
// LOOP
// ======================================================

void loop()
{
  // ====================================================
  // CTENI RDM6300
  // ====================================================

  while (
    RFID.available()
  )
  {
    byte znak =
      RFID.read();


    // ==================================================
    // STX 0x02
    // ZACATEK RFID PAKETU
    // ==================================================

    if (znak == 0x02)
    {
      prijimam = true;

      rfidIndex = 0;

      continue;
    }


    // Pokud nejsme uvnitr paketu
    if (!prijimam)
    {
      continue;
    }


    // ==================================================
    // ETX 0x03
    // KONEC RFID PAKETU
    // ==================================================

    if (znak == 0x03)
    {
      rfidBuffer[
        rfidIndex
      ] = '\0';

      prijimam = false;


      if (rfidIndex > 0)
      {
        zpracujKartu();
      }

      continue;
    }


    // ==================================================
    // UKLADANI RFID DAT
    // ==================================================

    if (
      rfidIndex <
      sizeof(rfidBuffer) - 1
    )
    {
      rfidBuffer[
        rfidIndex
      ] = (char)znak;

      rfidIndex++;
    }
  }


  // ====================================================
  // DETEKCE ODEBRANI KARTY
  // ====================================================

  if (
    posledniKarta.length() > 0 &&
    millis() - posledniCas >
      CAS_ODEBRANI
  )
  {
    posledniKarta = "";
  }


  // ====================================================
  // SPRAVNA KARTA
  // PO 3 SEKUNDACH ZOBRAZ QR
  // ====================================================

  if (
    spravnaKartaZobrazena &&
    ukolSplnen &&
    millis() - casSpravneKarty >=
      CAS_SPRAVNE_KARTY
  )
  {
    spravnaKartaZobrazena = false;

    // Zobraz QR
    drawQRCode(
      QR_TEXT
    );

    // Python spustí dokončení úkolu až po zobrazení QR.
    Serial.println("TASK_DONE");

    // QR zustane zobrazen,
    // dokud neprijde SPATNA karta.
  }


  // ====================================================
  // SPATNA KARTA
  // PO 3 SEKUNDACH ZACNI ZNOVU
  // ====================================================

  if (
    spatnaKartaZobrazena &&
    millis() - casSpatneKarty >=
      CAS_SPATNE_KARTY
  )
  {
    // Reset stavu procesu
    spatnaKartaZobrazena = false;

    spravnaKartaZobrazena = false;

    ukolSplnen = false;

    posledniKarta = "";


    // Zpet na zacatek
    zobrazCekani();


    // RFID_OK REMOVED FROM HERE


    // Informace pro PC
    Serial.print("ID:");
    Serial.print(DEVICE_ID);
    Serial.println(";STATUS:READY");
  }
}