// ArrayOfLedArrays - see https://github.com/FastLED/FastLED/wiki/Multiple-Controller-Examples for more info on
// using multiple controllers.  In this example, we're going to set up three NEOPIXEL strips on three
// different pins, each strip getting its own CRGB array to be played with, only this time they're going
// to be all parts of an array of arrays.

#include <FastLED.h>

#define NUM_STRIPS 3
#define NUM_LEDS_PER_STRIP 30

#define LED_LEFT_PIN 6
#define LED_RIGHT_PIN 7
#define LED_EXT_PIN 11

#define LIGHT_SOURCE_PIN1 3
#define LIGHT_SOURCE_PIN2 5

#define LIGHT_INTENSITY 50  //0-255 range

CRGB leds[NUM_STRIPS][NUM_LEDS_PER_STRIP];
int led_left_indx = 0;
int led_right_indx = 1;
int led_ext_indx = 2;


int blinkState = 0;
int tmp_state = 0;
// For mirroring strips, all the "special" stuff happens just in setup.  We
// just addLeds multiple times, once for each strip

void setup() {
  //Setup Serial Communication Port
  Serial.begin(115200);
  //Serial.begin(921600);

  //Setup LIGHT SOURCE PWM PINS

  pinMode(LIGHT_SOURCE_PIN1, OUTPUT);
  pinMode(LIGHT_SOURCE_PIN2, OUTPUT);

  //Setup LEDs
  FastLED.addLeds<NEOPIXEL, 6>(leds[0], NUM_LEDS_PER_STRIP);
  FastLED.addLeds<NEOPIXEL, 7>(leds[1], NUM_LEDS_PER_STRIP);
  FastLED.addLeds<NEOPIXEL, 11>(leds[2], NUM_LEDS_PER_STRIP);


  analogWrite(LIGHT_SOURCE_PIN1, LIGHT_INTENSITY);
  analogWrite(LIGHT_SOURCE_PIN2, LIGHT_INTENSITY);

  Serial.println("Starting");
  control_external_leds(1);
}

void signal_reward_leds() {
  for (int i = 0; i < NUM_LEDS_PER_STRIP; i++) {
    leds[0][i] =  CRGB::White;
    leds[1][i] =  CRGB::White;
    FastLED.show();
    delay(10);
    // Now turn the LED off, then pause
    leds[0][i] = CRGB::Black;
    leds[1][i] = CRGB::Black;
    FastLED.show();
  }
}

void control_external_leds(int state) {
  //Turn on EXTERNAL LEDs
  if (state == 1) {
    for (int i = 0; i < NUM_LEDS_PER_STRIP; i++) {
      leds[2][i] = CRGB(0, 128, 0); // change external LED color
      FastLED.show();
    }
  } else {  //Turn off external LEDs
    for (int i = 0; i < NUM_LEDS_PER_STRIP; i++) {
      leds[2][i] = CRGB::Black;
      FastLED.show();
    }
  }
  delay(10);
}



void loop() {

  String val = "";
  if (Serial.available()) {
    val = Serial.readString();
    //Serial.println(val);
  }
  // This outer loop will go over each strip, one at a time

  if (val == "reward") {
    signal_reward_leds();
    Serial.println("EXEC");
    Serial.flush();
  } else if (val == "external:ON") {
    control_external_leds(1);
    Serial.println("EXEC");
    Serial.flush();
    blinkState = 0;
  } else if (val == "external:OFF") {
    control_external_leds(0);
    Serial.println("EXEC");
    Serial.flush();
    blinkState = 0;
  }else if (val == "external:BLINK"){
    blinkState = 1;
    if(blinkState){
      for (int ii = 0; ii < 10; ii++){
        control_external_leds(tmp_state);
        if(tmp_state == 1){
          tmp_state = 0;
          delay(100);
        }else{
          tmp_state = 1;
          delay(100);
        }
      }
      Serial.println("EXEC");
      Serial.flush();
      blinkState = 0;
    }
  }else if (val == "lights:ON"){
    analogWrite(LIGHT_SOURCE_PIN1, LIGHT_INTENSITY);
    analogWrite(LIGHT_SOURCE_PIN2, LIGHT_INTENSITY);
    Serial.println("EXEC");
    Serial.flush();
  }else if (val == "lights:OFF"){
    analogWrite(LIGHT_SOURCE_PIN1, 0);
    analogWrite(LIGHT_SOURCE_PIN2, 0);
    Serial.println("EXEC");
    Serial.flush();
  }
  delay(1);
}
