#include <FastLED.h>

#define LED_PIN 5
#define NUM_LEDS 133
#define CHIPSET WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS 255

CRGB leds[NUM_LEDS];

String incomingLine = "";

void setup() {
  Serial.begin(115200);

  FastLED.addLeds<CHIPSET, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      processLine(incomingLine);
      incomingLine = "";
    } else {
      incomingLine += c;
    }
  }
}

void processLine(String line) {
  int ledIndex = 0;
  int startPos = 0;

  while (startPos < line.length() && ledIndex < NUM_LEDS) {
    int endPos = line.indexOf(';', startPos);

    if (endPos == -1) {
      endPos = line.length();
    }

    String triplet = line.substring(startPos, endPos);

    int firstComma = triplet.indexOf(',');
    int secondComma = triplet.indexOf(',', firstComma + 1);

    if (firstComma != -1 && secondComma != -1) {
      int r = triplet.substring(0, firstComma).toInt();
      int g = triplet.substring(firstComma + 1, secondComma).toInt();
      int b = triplet.substring(secondComma + 1).toInt();

      leds[ledIndex] = CRGB(r, g, b);
    }

    ledIndex++;
    startPos = endPos + 1;
  }

  FastLED.show();
}
