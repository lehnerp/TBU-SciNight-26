/*
 * LCD + klávesnice na Mega; pár: ../KeyPad_code_driver.py.
 * USB 9600 baud: PIN:KEY, PIN:BACKSPACE, PIN:OK/WRONG/RESET.
 * Knihovny: LiquidCrystal_I2C, Keypad; PIN a klíč jsou níže.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

/*
 * LCD + KEYPAD -> Arduino Mega
 *
 * LCD VCC -> 5V
 * LCD GND -> GND
 * LCD SDA -> 20
 * LCD SCL -> 21
 *
 * Keypad R1 -> 2
 * Keypad R2 -> 3
 * Keypad R3 -> 4
 * Keypad R4 -> 5
 *
 * Keypad C1 -> 6
 * Keypad C2 -> 7
 * Keypad C3 -> 8
 * Keypad C4 -> 9
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>


// ============================================================
// LCD
// ============================================================

LiquidCrystal_I2C lcd(0x27, 16, 2);


// ============================================================
// KEYPAD
// ============================================================

const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {
  2, 3, 4, 5
};

byte colPins[COLS] = {
  6, 7, 8, 9
};

Keypad keypad = Keypad(
  makeKeymap(keys),
  rowPins,
  colPins,
  ROWS,
  COLS
);


// ============================================================
// PIN
// ============================================================

const String SECRET_PIN = "2012";
const String CIPHER_KEY = "TEST";

String enteredPIN = "";


// ============================================================
// CASOVANI OBRAZOVEK
// ============================================================

enum ScreenState {
  PIN_SCREEN,
  ACCESS_OK,
  SHOW_KEY,
  ACCESS_DENIED
};

ScreenState screenState = PIN_SCREEN;

unsigned long stateStarted = 0;


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();

  showPinScreen();

  Serial.println("KEYPAD:READY");
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  updateScreenTimer();

  char key = keypad.getKey();

  if (!key)
  {
    return;
  }


  // Pokud zrovna zobrazujeme vysledek,
  // klavesnici ignorujeme.

  if (screenState != PIN_SCREEN)
  {
    return;
  }


  // ==========================================================
  // CISLICE
  // ==========================================================

  if (key >= '0' && key <= '9')
  {
    if (enteredPIN.length() < 8)
    {
      enteredPIN += key;

      redrawStars();


      // -------------------------------------------------------
      // INFORMACE PRO PYTHON
      //
      // Napr.:
      // PIN:KEY:2:1
      // PIN:KEY:0:2
      //
      // posledni cislo = pocet zadanych znaku
      // -------------------------------------------------------

      Serial.print("PIN:KEY:");
      Serial.print(key);
      Serial.print(":");
      Serial.println(enteredPIN.length());
    }

    return;
  }


  // ==========================================================
  // * = SMAZAT POSLEDNI ZNAK
  // ==========================================================

  if (key == '*')
  {
    if (enteredPIN.length() > 0)
    {
      enteredPIN.remove(
        enteredPIN.length() - 1
      );

      redrawStars();


      Serial.print("PIN:BACKSPACE:");
      Serial.println(
        enteredPIN.length()
      );
    }

    return;
  }


  // ==========================================================
  // # = POTVRDIT
  // ==========================================================

  if (key == '#')
  {
    Serial.println("PIN:CONFIRM");

    checkPIN();

    return;
  }
}


// ============================================================
// PREKRESLENI HVEZDICEK
// ============================================================

void redrawStars()
{
  lcd.setCursor(0, 1);

  lcd.print(
    "                "
  );

  lcd.setCursor(0, 1);

  for (
    unsigned int i = 0;
    i < enteredPIN.length();
    i++
  )
  {
    lcd.print("*");
  }
}


// ============================================================
// KONTROLA PINU
// ============================================================

void checkPIN()
{
  lcd.clear();


  // ==========================================================
  // SPRAVNY PIN
  // ==========================================================

  if (enteredPIN == SECRET_PIN)
  {
    Serial.println("PIN:OK");

    lcd.setCursor(0, 0);
    lcd.print("Pristup POVOLEN");

    lcd.setCursor(0, 1);
    lcd.print("Overeno");

    screenState = ACCESS_OK;
    stateStarted = millis();

    return;
  }


  // ==========================================================
  // SPATNY PIN
  // ==========================================================

  Serial.println("PIN:WRONG");

  lcd.setCursor(0, 0);
  lcd.print("Pristup ZAMIT.");

  lcd.setCursor(0, 1);
  lcd.print("Spatny PIN");

  screenState = ACCESS_DENIED;
  stateStarted = millis();
}


// ============================================================
// CASOVANI LCD
// ============================================================

void updateScreenTimer()
{
  unsigned long now = millis();


  // ----------------------------------------------------------
  // SPRAVNY PIN
  // ----------------------------------------------------------

  if (screenState == ACCESS_OK)
  {
    if (now - stateStarted >= 1200)
    {
      lcd.clear();

      lcd.setCursor(0, 0);
      lcd.print("KLIC:");

      lcd.setCursor(0, 1);
      lcd.print(CIPHER_KEY);

      screenState = SHOW_KEY;
      stateStarted = now;
    }

    return;
  }


  // ----------------------------------------------------------
  // KLIC ZUSTANE 8 SEKUND
  // ----------------------------------------------------------

  if (screenState == SHOW_KEY)
  {
    if (now - stateStarted >= 8000)
    {
      enteredPIN = "";

      showPinScreen();

      Serial.println(
        "PIN:RESET"
      );
    }

    return;
  }


  // ----------------------------------------------------------
  // SPATNY PIN
  // ----------------------------------------------------------

  if (screenState == ACCESS_DENIED)
  {
    if (now - stateStarted >= 3000)
    {
      enteredPIN = "";

      showPinScreen();

      Serial.println(
        "PIN:RESET"
      );
    }
  }
}


// ============================================================
// UVODNI OBRAZOVKA
// ============================================================

void showPinScreen()
{
  screenState = PIN_SCREEN;

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Zadej PIN");

  lcd.setCursor(0, 1);

  redrawStars();
}