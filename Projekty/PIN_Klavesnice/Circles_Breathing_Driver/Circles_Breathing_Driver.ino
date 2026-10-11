/*
 * Tři NeoPixel kruhy po 12 LED; pár: ../KeyPad_code_driver.py.
 * USB 9600 baud: STEP:1/2/3, SUCCESS, ERROR, RESET.
 * Knihovna: Adafruit NeoPixel; data D2/D3/D4.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <Adafruit_NeoPixel.h>

// ============================================================
// HARDWARE
// ============================================================

#define LED_COUNT 12

#define RING1_PIN 2
#define RING2_PIN 3
#define RING3_PIN 4

Adafruit_NeoPixel ring1(
  LED_COUNT,
  RING1_PIN,
  NEO_GRB + NEO_KHZ800
);

Adafruit_NeoPixel ring2(
  LED_COUNT,
  RING2_PIN,
  NEO_GRB + NEO_KHZ800
);

Adafruit_NeoPixel ring3(
  LED_COUNT,
  RING3_PIN,
  NEO_GRB + NEO_KHZ800
);


// ============================================================
// SERIAL
// ============================================================

String command = "";


// ============================================================
// STATES
// ============================================================

enum AnimationMode
{
  IDLE,
  ENTERING,
  SUCCESS,
  ERROR
};

AnimationMode mode = IDLE;


// ============================================================
// TIMING
// ============================================================

unsigned long lastAnimation = 0;


// ============================================================
// ENTERING ANIMATION
// ============================================================

int animationPixel = 0;
int activeRing = 0;


// ============================================================
// ERROR
// ============================================================

bool flashState = false;


// ============================================================
// IDLE WHITE BREATHING
// ============================================================

int breathBrightness = 3;
int breathDirection = 1;

// Slow breathing
const unsigned long BREATH_SPEED = 80;

const int BREATH_MIN = 3;
const int BREATH_MAX = 30;


// ============================================================
// COLORS
//
// Intentionally DIM.
// PC screen is the dominant visual indicator.
// ============================================================

uint32_t COLOR_INPUT;
uint32_t COLOR_GREEN;
uint32_t COLOR_RED;


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(9600);

  ring1.begin();
  ring2.begin();
  ring3.begin();

  // Keep global brightness available.
  // Individual RGB values below control actual intensity.

  ring1.setBrightness(100);
  ring2.setBrightness(100);
  ring3.setBrightness(100);


  // Dim blue
  COLOR_INPUT =
    ring1.Color(
      0,
      25,
      40
    );


  // Dim green
  COLOR_GREEN =
    ring1.Color(
      0,
      45,
      0
    );


  // Dim red
  COLOR_RED =
    ring1.Color(
      50,
      0,
      0
    );


  clearAll();

  mode = IDLE;

  Serial.println("NEOPIXEL:READY");
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  readSerial();

  updateAnimation();
}


// ============================================================
// SERIAL READER
// ============================================================

void readSerial()
{
  while (Serial.available())
  {
    char c = Serial.read();


    if (c == '\n')
    {
      command.trim();

      if (command.length() > 0)
      {
        processCommand(command);
      }

      command = "";

      continue;
    }


    if (c == '\r')
    {
      continue;
    }


    if (command.length() < 50)
    {
      command += c;
    }
  }
}


// ============================================================
// COMMAND PROCESSOR
// ============================================================

void processCommand(String cmd)
{
  cmd.trim();


  // ==========================================================
  // RESET
  // ==========================================================

  if (cmd == "RESET")
  {
    clearAll();

    mode = IDLE;

    activeRing = 0;
    animationPixel = 0;

    breathBrightness = BREATH_MIN;
    breathDirection = 1;

    lastAnimation = millis();

    Serial.println("NEOPIXEL:RESET");

    return;
  }


  // ==========================================================
  // STEP
  //
  // STEP:1
  // STEP:2
  // STEP:3
  // ==========================================================

  if (cmd.startsWith("STEP:"))
  {
    activeRing =
      cmd.substring(5).toInt();


    if (activeRing < 1)
    {
      activeRing = 1;
    }


    if (activeRing > 3)
    {
      activeRing = 3;
    }


    mode = ENTERING;

    animationPixel = 0;

    clearAll();

    lastAnimation = millis();

    return;
  }


  // ==========================================================
  // SUCCESS
  // ==========================================================

  if (cmd == "SUCCESS")
  {
    mode = SUCCESS;

    animationPixel = 0;

    clearAll();

    lastAnimation = millis();

    return;
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (cmd == "ERROR")
  {
    mode = ERROR;

    animationPixel = 0;

    flashState = false;

    clearAll();

    lastAnimation = millis();

    return;
  }
}


// ============================================================
// GET RING
// ============================================================

Adafruit_NeoPixel* getRing(int number)
{
  if (number == 1)
  {
    return &ring1;
  }

  if (number == 2)
  {
    return &ring2;
  }

  return &ring3;
}


// ============================================================
// CLEAR ALL
// ============================================================

void clearAll()
{
  ring1.clear();
  ring2.clear();
  ring3.clear();

  ring1.show();
  ring2.show();
  ring3.show();
}


// ============================================================
// FILL RING
// ============================================================

void fillRing(
  Adafruit_NeoPixel &ring,
  uint32_t color
)
{
  for (int i = 0; i < LED_COUNT; i++)
  {
    ring.setPixelColor(
      i,
      color
    );
  }

  ring.show();
}


// ============================================================
// FILL ALL
// ============================================================

void fillAll(uint32_t color)
{
  fillRing(
    ring1,
    color
  );

  fillRing(
    ring2,
    color
  );

  fillRing(
    ring3,
    color
  );
}


// ============================================================
// IDLE BREATHING
// ============================================================

void updateBreathing()
{
  unsigned long now = millis();


  if (
    now - lastAnimation <
    BREATH_SPEED
  )
  {
    return;
  }


  lastAnimation = now;


  breathBrightness +=
    breathDirection;


  if (
    breathBrightness >=
    BREATH_MAX
  )
  {
    breathBrightness =
      BREATH_MAX;

    breathDirection = -1;
  }


  if (
    breathBrightness <=
    BREATH_MIN
  )
  {
    breathBrightness =
      BREATH_MIN;

    breathDirection = 1;
  }


  uint32_t white =
    ring1.Color(
      breathBrightness,
      breathBrightness,
      breathBrightness
    );


  for (int i = 0; i < LED_COUNT; i++)
  {
    ring1.setPixelColor(
      i,
      white
    );

    ring2.setPixelColor(
      i,
      white
    );

    ring3.setPixelColor(
      i,
      white
    );
  }


  ring1.show();
  ring2.show();
  ring3.show();
}


// ============================================================
// MAIN ANIMATION
// ============================================================

void updateAnimation()
{
  unsigned long now = millis();


  // ==========================================================
  // IDLE
  // ==========================================================

  if (mode == IDLE)
  {
    updateBreathing();

    return;
  }


  // ==========================================================
  // ENTERING PIN
  // ==========================================================

  if (mode == ENTERING)
  {
    // Slower rotation

    if (
      now - lastAnimation <
      100
    )
    {
      return;
    }


    lastAnimation = now;


    Adafruit_NeoPixel* ring =
      getRing(activeRing);


    ring->clear();


    // --------------------------------------------------------
    // MAIN BLUE PIXEL
    // --------------------------------------------------------

    ring->setPixelColor(
      animationPixel,
      COLOR_INPUT
    );


    // --------------------------------------------------------
    // TRAIL 1
    // --------------------------------------------------------

    int previous1 =
      animationPixel - 1;


    if (previous1 < 0)
    {
      previous1 += LED_COUNT;
    }


    ring->setPixelColor(
      previous1,
      ring->Color(
        0,
        10,
        16
      )
    );


    // --------------------------------------------------------
    // TRAIL 2
    // --------------------------------------------------------

    int previous2 =
      animationPixel - 2;


    if (previous2 < 0)
    {
      previous2 += LED_COUNT;
    }


    ring->setPixelColor(
      previous2,
      ring->Color(
        0,
        3,
        6
      )
    );


    ring->show();


    animationPixel++;


    if (
      animationPixel >=
      LED_COUNT
    )
    {
      animationPixel = 0;
    }


    return;
  }


  // ==========================================================
  // SUCCESS
  //
  // Ring 1 -> Ring 2 -> Ring 3
  // progressively turns green.
  // ==========================================================

  if (mode == SUCCESS)
  {
    if (
      now - lastAnimation <
      90
    )
    {
      return;
    }


    lastAnimation = now;


    // RING 1

    if (
      animationPixel <
      LED_COUNT
    )
    {
      ring1.setPixelColor(
        animationPixel,
        COLOR_GREEN
      );

      ring1.show();
    }


    // RING 2

    else if (
      animationPixel <
      LED_COUNT * 2
    )
    {
      int pixel =
        animationPixel -
        LED_COUNT;


      ring2.setPixelColor(
        pixel,
        COLOR_GREEN
      );

      ring2.show();
    }


    // RING 3

    else if (
      animationPixel <
      LED_COUNT * 3
    )
    {
      int pixel =
        animationPixel -
        (LED_COUNT * 2);


      ring3.setPixelColor(
        pixel,
        COLOR_GREEN
      );

      ring3.show();
    }


    // FINISHED

    else
    {
      fillAll(
        COLOR_GREEN
      );

      // Stay green until RESET.

      return;
    }


    animationPixel++;

    return;
  }


  // ==========================================================
  // ERROR
  //
  // Physical LEDs intentionally less aggressive than PC.
  // ==========================================================

  if (mode == ERROR)
  {
    if (
      now - lastAnimation <
      300
    )
    {
      return;
    }


    lastAnimation = now;

    flashState =
      !flashState;


    if (flashState)
    {
      fillAll(
        COLOR_RED
      );
    }
    else
    {
      clearAll();
    }


    return;
  }
}