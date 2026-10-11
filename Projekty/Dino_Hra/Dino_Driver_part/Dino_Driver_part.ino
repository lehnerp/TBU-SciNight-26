/*
 * Dino hra na třech NeoPixel maticích 8x8; pár: ../DinoRun_Driver.py.
 * USB 9600 baud: START/RESTART, JUMP, RESET; výstup GAME:*.
 * Knihovna: Adafruit NeoPixel; data D2/D3/D4.
 * Zapojení a požadavky: ../README.md tohoto stanoviště.
 */

#include <Adafruit_NeoPixel.h>

// ============================================================
// DINO RUNNER - COLORFUL FIREWORKS VERSION
//
// Matrix 1 = D2
// Matrix 2 = D3
// Matrix 3 = D4
//
// Each matrix = 8x8
// Logical display = 24x8
//
// WIN = 5 obstacles
// SUCCESS = colorful fireworks across all 3 panels
// ============================================================


// ============================================================
// DISPLAY
// ============================================================

#define MATRIX_WIDTH 8
#define MATRIX_HEIGHT 8
#define MATRIX_PIXELS 64

#define SCREEN_WIDTH 24
#define SCREEN_HEIGHT 8

#define MATRIX1_PIN 2
#define MATRIX2_PIN 3
#define MATRIX3_PIN 4

#define MATRIX_BRIGHTNESS 20


// ============================================================
// MATRICES
// ============================================================

Adafruit_NeoPixel matrix1(
  MATRIX_PIXELS,
  MATRIX1_PIN,
  NEO_GRB + NEO_KHZ800
);

Adafruit_NeoPixel matrix2(
  MATRIX_PIXELS,
  MATRIX2_PIN,
  NEO_GRB + NEO_KHZ800
);

Adafruit_NeoPixel matrix3(
  MATRIX_PIXELS,
  MATRIX3_PIN,
  NEO_GRB + NEO_KHZ800
);


// ============================================================
// COLORS
// ============================================================

uint32_t COLOR_DINO;
uint32_t COLOR_GROUND;
uint32_t COLOR_CACTUS;
uint32_t COLOR_EYE;
uint32_t COLOR_GAMEOVER;

uint32_t COLOR_RED;
uint32_t COLOR_GREEN;
uint32_t COLOR_BLUE;
uint32_t COLOR_YELLOW;
uint32_t COLOR_CYAN;
uint32_t COLOR_MAGENTA;
uint32_t COLOR_ORANGE;
uint32_t COLOR_WHITE;


// ============================================================
// GAME STATE
// ============================================================

enum GameState
{
  WAITING,
  PLAYING,
  GAME_OVER,
  WIN
};

GameState gameState = WAITING;


// ============================================================
// DINO
// ============================================================

const int DINO_X = 3;
const float GROUND_Y = 5.0;

float dinoY = GROUND_Y;
float velocityY = 0.0;

bool onGround = true;


// ============================================================
// PHYSICS
// ============================================================

const float GRAVITY = 0.16;
const float JUMP_POWER = -2.15;


// ============================================================
// OBSTACLE
// ============================================================

float obstacleX = 23.0;

int obstacleHeight = 2;

bool obstacleScored = false;


// ============================================================
// SCORE
// ============================================================

int score = 0;

const int WIN_SCORE = 5;


// ============================================================
// SPEED
// ============================================================

float gameSpeed = 0.22;

const float START_SPEED = 0.22;
const float MAX_SPEED = 0.55;


// ============================================================
// TIMING
// ============================================================

unsigned long lastFrame = 0;

const unsigned long FRAME_TIME = 45;

unsigned long gameOverStart = 0;
unsigned long winStart = 0;

const unsigned long RESULT_TIME = 3000;


// ============================================================
// SERIAL
// ============================================================

String command = "";


// ============================================================
// MATRIX MAPPING
//
// IMPORTANT:
// DO NOT CHANGE THIS.
//
// This is the existing orientation that makes the Dino
// appear correctly.
// ============================================================

int xyToPixel(int x, int y)
{
  if (
    x < 0 ||
    x >= MATRIX_WIDTH ||
    y < 0 ||
    y >= MATRIX_HEIGHT
  )
  {
    return -1;
  }


  if (y % 2 == 0)
  {
    return
      y * MATRIX_WIDTH +
      x;
  }


  return
    y * MATRIX_WIDTH +
    (MATRIX_WIDTH - 1 - x);
}


// ============================================================
// LOGICAL 24x8 PIXEL
// ============================================================

void setGamePixel(
  int x,
  int y,
  uint32_t color
)
{
  if (
    x < 0 ||
    x >= SCREEN_WIDTH ||
    y < 0 ||
    y >= SCREEN_HEIGHT
  )
  {
    return;
  }


  int localX;
  int pixel;


  // ==========================================================
  // MATRIX 1 - D2
  // X = 0...7
  // ==========================================================

  if (x < 8)
  {
    localX = x;


    pixel =
      xyToPixel(
        localX,
        y
      );


    if (pixel >= 0)
    {
      matrix1.setPixelColor(
        pixel,
        color
      );
    }


    return;
  }


  // ==========================================================
  // MATRIX 2 - D3
  // X = 8...15
  // ==========================================================

  if (x < 16)
  {
    localX =
      x - 8;


    pixel =
      xyToPixel(
        localX,
        y
      );


    if (pixel >= 0)
    {
      matrix2.setPixelColor(
        pixel,
        color
      );
    }


    return;
  }


  // ==========================================================
  // MATRIX 3 - D4
  // X = 16...23
  // ==========================================================

  localX =
    x - 16;


  pixel =
    xyToPixel(
      localX,
      y
    );


  if (pixel >= 0)
  {
    matrix3.setPixelColor(
      pixel,
      color
    );
  }
}


// ============================================================
// DISPLAY HELPERS
// ============================================================

void clearDisplay()
{
  matrix1.clear();
  matrix2.clear();
  matrix3.clear();
}


void showDisplay()
{
  matrix1.show();
  matrix2.show();
  matrix3.show();
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(9600);


  matrix1.begin();
  matrix2.begin();
  matrix3.begin();


  matrix1.setBrightness(
    MATRIX_BRIGHTNESS
  );

  matrix2.setBrightness(
    MATRIX_BRIGHTNESS
  );

  matrix3.setBrightness(
    MATRIX_BRIGHTNESS
  );


  // ==========================================================
  // GAME COLORS
  // ==========================================================

  COLOR_DINO =
    matrix1.Color(
      0,
      200,
      80
    );


  COLOR_GROUND =
    matrix1.Color(
      35,
      35,
      35
    );


  COLOR_CACTUS =
    matrix1.Color(
      180,
      90,
      0
    );


  COLOR_EYE =
    matrix1.Color(
      200,
      200,
      200
    );


  COLOR_GAMEOVER =
    matrix1.Color(
      220,
      0,
      0
    );


  // ==========================================================
  // FIREWORK COLORS
  // ==========================================================

  COLOR_RED =
    matrix1.Color(
      255,
      0,
      0
    );


  COLOR_GREEN =
    matrix1.Color(
      0,
      255,
      50
    );


  COLOR_BLUE =
    matrix1.Color(
      0,
      80,
      255
    );


  COLOR_YELLOW =
    matrix1.Color(
      255,
      180,
      0
    );


  COLOR_CYAN =
    matrix1.Color(
      0,
      220,
      255
    );


  COLOR_MAGENTA =
    matrix1.Color(
      255,
      0,
      180
    );


  COLOR_ORANGE =
    matrix1.Color(
      255,
      70,
      0
    );


  COLOR_WHITE =
    matrix1.Color(
      255,
      255,
      255
    );


  randomSeed(
    analogRead(A0)
  );


  clearDisplay();
  showDisplay();


  gameState =
    WAITING;


  Serial.println(
    "GAME:READY"
  );
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop()
{
  readSerial();


  unsigned long now =
    millis();


  if (
    now - lastFrame <
    FRAME_TIME
  )
  {
    return;
  }


  lastFrame =
    now;


  switch (gameState)
  {
    case WAITING:

      updateWaiting();

      break;


    case PLAYING:

      updateGame();

      break;


    case GAME_OVER:

      updateGameOver();

      break;


    case WIN:

      updateWin();

      break;
  }
}


// ============================================================
// SERIAL INPUT
// ============================================================

void readSerial()
{
  while (
    Serial.available()
  )
  {
    char c =
      Serial.read();


    if (c == '\n')
    {
      command.trim();


      if (
        command.length() > 0
      )
      {
        processCommand(
          command
        );
      }


      command = "";

      continue;
    }


    if (c == '\r')
    {
      continue;
    }


    if (
      command.length() < 40
    )
    {
      command += c;
    }
  }
}


// ============================================================
// COMMANDS
// ============================================================

void processCommand(
  String cmd
)
{
  cmd.trim();


  // ==========================================================
  // RESET
  // ==========================================================

  if (
    cmd == "RESET"
  )
  {
    returnToIdle();


    Serial.println(
      "GAME:RESET"
    );


    return;
  }


  // ==========================================================
  // RESULT ANIMATION CANNOT BE INTERRUPTED
  // ==========================================================

  if (
    gameState == GAME_OVER ||
    gameState == WIN
  )
  {
    return;
  }


  // ==========================================================
  // START / RESTART
  // ==========================================================

  if (
    cmd == "START" ||
    cmd == "RESTART"
  )
  {
    startGame();

    return;
  }


  // ==========================================================
  // JUMP
  // ==========================================================

  if (
    cmd == "JUMP"
  )
  {
    // First SPACE starts game and jumps

    if (
      gameState == WAITING
    )
    {
      startGame();

      jump();

      return;
    }


    if (
      gameState == PLAYING
    )
    {
      jump();

      return;
    }
  }
}


// ============================================================
// START GAME
// ============================================================

void startGame()
{
  score =
    0;


  dinoY =
    GROUND_Y;


  velocityY =
    0.0;


  onGround =
    true;


  // First obstacle starts farther away

  obstacleX =
    25.0;


  obstacleHeight =
    random(
      1,
      3
    );


  obstacleScored =
    false;


  gameSpeed =
    START_SPEED;


  gameState =
    PLAYING;


  clearDisplay();
  showDisplay();


  Serial.println(
    "GAME:START"
  );
}


// ============================================================
// RETURN TO IDLE
// ============================================================

void returnToIdle()
{
  gameState =
    WAITING;


  score =
    0;


  dinoY =
    GROUND_Y;


  velocityY =
    0.0;


  onGround =
    true;


  obstacleX =
    23.0;


  obstacleHeight =
    2;


  obstacleScored =
    false;


  gameSpeed =
    START_SPEED;


  clearDisplay();
  showDisplay();


  Serial.println(
    "GAME:READY"
  );
}


// ============================================================
// JUMP
// ============================================================

void jump()
{
  // No double jump

  if (!onGround)
  {
    return;
  }


  velocityY =
    JUMP_POWER;


  onGround =
    false;


  Serial.println(
    "GAME:JUMP"
  );
}


// ============================================================
// WAITING
// ============================================================

void updateWaiting()
{
  dinoY =
    GROUND_Y;


  velocityY =
    0.0;


  onGround =
    true;


  clearDisplay();


  drawGround();

  drawDino();


  showDisplay();
}


// ============================================================
// GAME
// ============================================================

void updateGame()
{
  // ==========================================================
  // DINO PHYSICS
  // ==========================================================

  velocityY +=
    GRAVITY;


  dinoY +=
    velocityY;


  // ==========================================================
  // LANDING
  // ==========================================================

  if (
    dinoY >=
    GROUND_Y
  )
  {
    dinoY =
      GROUND_Y;


    velocityY =
      0.0;


    onGround =
      true;
  }


  // ==========================================================
  // MOVE CACTUS
  // ==========================================================

  obstacleX -=
    gameSpeed;


  // ==========================================================
  // COLLISION
  // ==========================================================

  if (
    checkCollision()
  )
  {
    gameState =
      GAME_OVER;


    gameOverStart =
      millis();


    Serial.print(
      "GAME:OVER:"
    );


    Serial.println(
      score
    );


    return;
  }


  // ==========================================================
  // SCORE
  // ==========================================================

  if (
    !obstacleScored &&
    obstacleX <
    DINO_X - 1
  )
  {
    obstacleScored =
      true;


    score++;


    Serial.print(
      "GAME:SCORE:"
    );


    Serial.println(
      score
    );


    // ========================================================
    // SPEED UP
    // ========================================================

    gameSpeed +=
      0.025;


    if (
      gameSpeed >
      MAX_SPEED
    )
    {
      gameSpeed =
        MAX_SPEED;
    }


    // ========================================================
    // WIN
    // ========================================================

    if (
      score >=
      WIN_SCORE
    )
    {
      gameState =
        WIN;


      winStart =
        millis();


      Serial.println(
        "GAME:WIN"
      );


      return;
    }
  }


  // ==========================================================
  // NEXT CACTUS
  // ==========================================================

  if (
    obstacleX <
    -2
  )
  {
    obstacleX =
      23 +
      random(
        4,
        10
      );


    obstacleHeight =
      random(
        1,
        3
      );


    obstacleScored =
      false;
  }


  drawGame();
}


// ============================================================
// COLLISION
// ============================================================

bool checkCollision()
{
  int cactusX =
    round(
      obstacleX
    );


  bool horizontalCollision =
    (
      cactusX >=
      DINO_X
    )
    &&
    (
      cactusX <=
      DINO_X + 1
    );


  if (
    !horizontalCollision
  )
  {
    return false;
  }


  int dinoBottom =
    round(
      dinoY
    ) + 1;


  int cactusTop =
    7 -
    obstacleHeight;


  if (
    dinoBottom >=
    cactusTop
  )
  {
    return true;
  }


  return false;
}


// ============================================================
// DRAW GAME
// ============================================================

void drawGame()
{
  clearDisplay();


  drawGround();

  drawDino();

  drawObstacle();


  showDisplay();
}


// ============================================================
// MOVING GROUND
// ============================================================

void drawGround()
{
  int movement =
    (
      millis() / 150
    ) % 3;


  for (
    int x = 0;
    x < SCREEN_WIDTH;
    x++
  )
  {
    if (
      (
        x + movement
      ) % 3 == 0
    )
    {
      setGamePixel(
        x,
        7,
        COLOR_GROUND
      );
    }
  }
}


// ============================================================
// ORIGINAL DINO
// ============================================================

void drawDino()
{
  int y =
    round(
      dinoY
    );


  // Body

  setGamePixel(
    DINO_X,
    y,
    COLOR_DINO
  );


  setGamePixel(
    DINO_X + 1,
    y,
    COLOR_DINO
  );


  // Head

  setGamePixel(
    DINO_X + 1,
    y - 1,
    COLOR_DINO
  );


  // Tail

  setGamePixel(
    DINO_X - 1,
    y,
    COLOR_DINO
  );


  // Leg

  setGamePixel(
    DINO_X,
    y + 1,
    COLOR_DINO
  );


  // Eye

  setGamePixel(
    DINO_X + 1,
    y - 1,
    COLOR_EYE
  );
}


// ============================================================
// CACTUS
// ============================================================

void drawObstacle()
{
  int x =
    round(
      obstacleX
    );


  for (
    int i = 0;
    i < obstacleHeight;
    i++
  )
  {
    setGamePixel(
      x,
      6 - i,
      COLOR_CACTUS
    );
  }


  if (
    obstacleHeight >= 2
  )
  {
    setGamePixel(
      x + 1,
      6,
      COLOR_CACTUS
    );
  }
}


// ============================================================
// GAME OVER
//
// 0 - 1 second = red flashing
// 1 - 3 seconds = red X
// ============================================================

void updateGameOver()
{
  unsigned long elapsed =
    millis() -
    gameOverStart;


  // ==========================================================
  // RED FLASH
  // ==========================================================

  if (
    elapsed < 1000
  )
  {
    bool flash =
      (
        (
          elapsed / 120
        ) % 2
      );


    clearDisplay();


    if (flash)
    {
      for (
        int x = 0;
        x < SCREEN_WIDTH;
        x++
      )
      {
        for (
          int y = 0;
          y < SCREEN_HEIGHT;
          y++
        )
        {
          if (
            (
              x + y
            ) % 2 == 0
          )
          {
            setGamePixel(
              x,
              y,
              COLOR_GAMEOVER
            );
          }
        }
      }
    }


    showDisplay();

    return;
  }


  // ==========================================================
  // RED X
  // ==========================================================

  if (
    elapsed <
    RESULT_TIME
  )
  {
    clearDisplay();


    for (
      int i = 1;
      i < 7;
      i++
    )
    {
      setGamePixel(
        8 + i,
        i,
        COLOR_GAMEOVER
      );


      setGamePixel(
        15 - i,
        i,
        COLOR_GAMEOVER
      );
    }


    showDisplay();

    return;
  }


  returnToIdle();
}


// ============================================================
// DRAW A SMALL FIREWORK
//
// stage 0 = ignition
// stage 1 = small burst
// stage 2 = large burst
// stage 3 = outer sparks
// ============================================================

void drawFirework(
  int cx,
  int cy,
  int stage,
  uint32_t color
)
{
  // ==========================================================
  // STAGE 0
  // ==========================================================

  if (stage == 0)
  {
    setGamePixel(
      cx,
      cy,
      COLOR_WHITE
    );

    return;
  }


  // ==========================================================
  // STAGE 1
  //
  //    *
  //   ***
  //    *
  // ==========================================================

  if (stage == 1)
  {
    setGamePixel(
      cx,
      cy,
      COLOR_WHITE
    );


    setGamePixel(
      cx - 1,
      cy,
      color
    );


    setGamePixel(
      cx + 1,
      cy,
      color
    );


    setGamePixel(
      cx,
      cy - 1,
      color
    );


    setGamePixel(
      cx,
      cy + 1,
      color
    );


    return;
  }


  // ==========================================================
  // STAGE 2
  //
  // Expanded explosion
  // ==========================================================

  if (stage == 2)
  {
    setGamePixel(
      cx - 2,
      cy,
      color
    );


    setGamePixel(
      cx + 2,
      cy,
      color
    );


    setGamePixel(
      cx,
      cy - 2,
      color
    );


    setGamePixel(
      cx,
      cy + 2,
      color
    );


    setGamePixel(
      cx - 1,
      cy - 1,
      color
    );


    setGamePixel(
      cx + 1,
      cy - 1,
      color
    );


    setGamePixel(
      cx - 1,
      cy + 1,
      color
    );


    setGamePixel(
      cx + 1,
      cy + 1,
      color
    );


    return;
  }


  // ==========================================================
  // STAGE 3
  //
  // Outer scattered sparks
  // ==========================================================

  if (stage == 3)
  {
    setGamePixel(
      cx - 2,
      cy - 1,
      color
    );


    setGamePixel(
      cx + 2,
      cy - 1,
      color
    );


    setGamePixel(
      cx - 2,
      cy + 1,
      color
    );


    setGamePixel(
      cx + 2,
      cy + 1,
      color
    );


    setGamePixel(
      cx - 1,
      cy - 2,
      color
    );


    setGamePixel(
      cx + 1,
      cy - 2,
      color
    );


    setGamePixel(
      cx - 1,
      cy + 2,
      color
    );


    setGamePixel(
      cx + 1,
      cy + 2,
      color
    );
  }
}


// ============================================================
// COLORFUL FIREWORK SUCCESS ANIMATION
//
// Total = 3 seconds
//
// Fireworks appear across all three matrices.
// ============================================================

void updateWin()
{
  unsigned long elapsed =
    millis() -
    winStart;


  // ==========================================================
  // FINISHED
  // ==========================================================

  if (
    elapsed >=
    RESULT_TIME
  )
  {
    returnToIdle();

    return;
  }


  clearDisplay();


  // ==========================================================
  // FIREWORK 1
  // LEFT MATRIX
  // MAGENTA
  // ==========================================================

  if (
    elapsed < 900
  )
  {
    int stage =
      (
        elapsed / 180
      ) % 4;


    drawFirework(
      4,
      3,
      stage,
      COLOR_MAGENTA
    );
  }


  // ==========================================================
  // FIREWORK 2
  // CENTER MATRIX
  // CYAN
  // ==========================================================

  if (
    elapsed >= 350 &&
    elapsed < 1250
  )
  {
    int stage =
      (
        (elapsed - 350) /
        180
      ) % 4;


    drawFirework(
      11,
      4,
      stage,
      COLOR_CYAN
    );
  }


  // ==========================================================
  // FIREWORK 3
  // RIGHT MATRIX
  // YELLOW
  // ==========================================================

  if (
    elapsed >= 700 &&
    elapsed < 1600
  )
  {
    int stage =
      (
        (elapsed - 700) /
        180
      ) % 4;


    drawFirework(
      19,
      3,
      stage,
      COLOR_YELLOW
    );
  }


  // ==========================================================
  // FIREWORK 4
  // LEFT/CENTER BORDER
  // ORANGE
  // ==========================================================

  if (
    elapsed >= 1150 &&
    elapsed < 2050
  )
  {
    int stage =
      (
        (elapsed - 1150) /
        180
      ) % 4;


    drawFirework(
      7,
      4,
      stage,
      COLOR_ORANGE
    );
  }


  // ==========================================================
  // FIREWORK 5
  // CENTER/RIGHT BORDER
  // BLUE
  // ==========================================================

  if (
    elapsed >= 1450 &&
    elapsed < 2350
  )
  {
    int stage =
      (
        (elapsed - 1450) /
        180
      ) % 4;


    drawFirework(
      16,
      3,
      stage,
      COLOR_BLUE
    );
  }


  // ==========================================================
  // FIREWORK 6
  // CENTER
  // GREEN
  // ==========================================================

  if (
    elapsed >= 1750 &&
    elapsed < 2650
  )
  {
    int stage =
      (
        (elapsed - 1750) /
        180
      ) % 4;


    drawFirework(
      12,
      3,
      stage,
      COLOR_GREEN
    );
  }


  // ==========================================================
  // FINAL COLORFUL SPARKLES
  // 2.2 - 3.0 seconds
  // ==========================================================

  if (
    elapsed >= 2200
  )
  {
    bool flash =
      (
        (
          elapsed / 100
        ) % 2
      );


    if (flash)
    {
      setGamePixel(
        1,
        1,
        COLOR_RED
      );

      setGamePixel(
        3,
        5,
        COLOR_YELLOW
      );

      setGamePixel(
        5,
        2,
        COLOR_CYAN
      );

      setGamePixel(
        7,
        6,
        COLOR_MAGENTA
      );


      setGamePixel(
        9,
        2,
        COLOR_ORANGE
      );

      setGamePixel(
        11,
        5,
        COLOR_BLUE
      );

      setGamePixel(
        13,
        1,
        COLOR_GREEN
      );

      setGamePixel(
        15,
        6,
        COLOR_YELLOW
      );


      setGamePixel(
        17,
        2,
        COLOR_MAGENTA
      );

      setGamePixel(
        19,
        5,
        COLOR_CYAN
      );

      setGamePixel(
        21,
        1,
        COLOR_ORANGE
      );

      setGamePixel(
        23,
        4,
        COLOR_GREEN
      );
    }
    else
    {
      setGamePixel(
        2,
        3,
        COLOR_BLUE
      );

      setGamePixel(
        4,
        1,
        COLOR_GREEN
      );

      setGamePixel(
        6,
        5,
        COLOR_RED
      );


      setGamePixel(
        8,
        6,
        COLOR_YELLOW
      );

      setGamePixel(
        10,
        3,
        COLOR_MAGENTA
      );

      setGamePixel(
        12,
        1,
        COLOR_YELLOW
      );

      setGamePixel(
        14,
        5,
        COLOR_CYAN
      );


      setGamePixel(
        16,
        1,
        COLOR_GREEN
      );

      setGamePixel(
        18,
        4,
        COLOR_ORANGE
      );

      setGamePixel(
        20,
        2,
        COLOR_BLUE
      );

      setGamePixel(
        22,
        6,
        COLOR_MAGENTA
      );
    }
  }


  showDisplay();
}