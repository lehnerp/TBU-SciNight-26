/*
* Module <-> Pin <-> Arduino Mega
* LCD <-> VCC <-> 5V
* LCD <-> GND <-> GND
* LCD <-> SDA <-> 20
* LCD <-> SCL <-> 21
* Keypad <-> R1 <-> 2
* Keypad <-> R2 <-> 3
* Keypad <-> R3 <-> 4
* Keypad <-> R4 <-> 5
* Keypad <-> C1 <-> 6
* Keypad <-> C2	 <-> 7
* Keypad <-> C3 <-> 8
* Keypad <-> C4 <-> 9
*/
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

// --------------------
// KEYPAD
// --------------------

const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {2, 3, 4, 5};
byte colPins[COLS] = {6, 7, 8, 9};

Keypad keypad = Keypad(
  makeKeymap(keys),
  rowPins,
  colPins,
  ROWS,
  COLS
);

// --------------------
// SECRET SETTINGS
// --------------------

const String SECRET_PIN = "1234";
const String CIPHER_KEY = "TESTER";

String enteredPIN = "";

void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();

  showPinScreen();
}

void loop() {

  char key = keypad.getKey();

  if (!key)
    return;

  // --------------------
  // NUMBER PRESSED
  // --------------------

  if (key >= '0' && key <= '9') {

    if (enteredPIN.length() < 8) {

      enteredPIN += key;

      lcd.setCursor(0, 1);

      // Display stars instead of PIN
      for (int i = 0; i < enteredPIN.length(); i++) {
        lcd.print("*");
      }

    }
  }

  // --------------------
  // * = BACKSPACE
  // --------------------

  else if (key == '*') {

    if (enteredPIN.length() > 0) {

      enteredPIN.remove(enteredPIN.length() - 1);

      lcd.setCursor(0, 1);
      lcd.print("                ");

      lcd.setCursor(0, 1);

      for (int i = 0; i < enteredPIN.length(); i++) {
        lcd.print("*");
      }
    }
  }

  // --------------------
  // # = CONFIRM
  // --------------------

  else if (key == '#') {

    checkPIN();

  }
}

// ========================================
// CHECK PIN
// ========================================

void checkPIN() {

  lcd.clear();

  if (enteredPIN == SECRET_PIN) {

    lcd.setCursor(0, 0);
    lcd.print("Pristup POVOLEN");

    delay(1200);

    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("KLIC:");

    lcd.setCursor(0, 1);
    lcd.print(CIPHER_KEY);

    // Keep the key visible
    delay(8000);

  }

  else {

    lcd.setCursor(0, 0);
    lcd.print("Pristup ZAMITNUT");

    lcd.setCursor(0, 1);
    lcd.print("Spatny PIN");

    delay(2000);

  }

  enteredPIN = "";

  showPinScreen();
}

// ========================================
// PIN SCREEN
// ========================================

void showPinScreen() {

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Zadej PIN");

  lcd.setCursor(0, 1);

}
