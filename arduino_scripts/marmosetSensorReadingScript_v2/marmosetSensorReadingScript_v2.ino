/*
Orhun Caner Eren  & Simon Steffens @NTGroup - INI- ETH Zurich

Marmoset Setup External Sensor reading script 
*/

// defines pins numbers
const int lickPin = D12;

const int photoresistor_analog = A0;
//const int photoresistor_digital= D17;

// defines variables
long duration;
int distance;
int lickState;
int photoresistor_state;

//Distance sensor interrupt parameters
const int trigPinLeft = D14;
const int echoPinLeft = D13;

volatile unsigned long t_distance_left;
volatile unsigned long pulseStartTimeLeft = 0;
volatile unsigned long pulseEndTimeLeft = 0;
volatile int pulseStateLeft = 0; //0 before trig sequence, //1: echo started //2: echo finished


const int trigPinRight = D11; //Change this to a suitable pin
const int echoPinRight = D10; // Change this to a suitable pin
const int SERIAL_DELAY = 100;

volatile unsigned long t_distance_right;
volatile unsigned long pulseStartTimeRight = 0;
volatile unsigned long pulseEndTimeRight = 0;

volatile unsigned long unique_id = 0; // package id

volatile int pulseStateRight = 0; //0 before trig sequence, //1: echo started //2: echo finished


void setup() {
  pinMode(trigPinLeft, OUTPUT); // Sets the trigPinLeft as an Output
  pinMode(echoPinLeft, INPUT); // Sets the echoPinLeft as an Input 
  attachInterrupt(digitalPinToInterrupt(echoPinLeft), pulseEndHandlerLeft, CHANGE);

  pinMode(trigPinRight, OUTPUT); // Sets the trigPinLeft as an Output
  pinMode(echoPinRight, INPUT); // Sets the echoPinLeft as an Input 
  attachInterrupt(digitalPinToInterrupt(echoPinRight), pulseEndHandlerRight, CHANGE);


  pinMode(lickPin, INPUT);
  pinMode(photoresistor_analog, INPUT);
  Serial.begin(921600); // Starts the serial communication
  //Serial.println("comm begin");
}

void handleLeftDistanceSensor(){
  //Handle the distance sensor
  if(pulseStateLeft == 0){ //state 0 means ready to send a new pulse
    // Clears the trigPinLeft
    digitalWrite(trigPinLeft, LOW);
    delayMicroseconds(2);
    // Sets the trigPinLeft on HIGH state for 10 micro seconds
    digitalWrite(trigPinLeft, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPinLeft, LOW);

  }

  else if(pulseStateLeft == 1){
    unsigned long timeoutCheck = micros();
    long timeout_duration = timeoutCheck - pulseStartTimeLeft;
    if (timeout_duration > 1000000){
      pulseStateLeft = 0;
    }
    
  }
 
  else if (pulseStateLeft == 2){
    unsigned long pulseDuration = pulseEndTimeLeft - pulseStartTimeLeft;
    distance = pulseDuration * 0.034 / 2;
    //delay(1);
    Serial.print("id:distanceSensorLeft_uniqueId:");
    Serial.print(unique_id);
    Serial.print("_value:");
    Serial.print(distance);
    Serial.print("_t:");
    Serial.print(t_distance_left);
    Serial.println();
    Serial.flush();
    unique_id +=1;
    pulseStateLeft = 0;
    delayMicroseconds(SERIAL_DELAY);
    //delay(1);
  }
}


void handleRightDistanceSensor(){
  //Handle the distance sensor
  if(pulseStateRight == 0){ //state 0 means ready to send a new pulse
    // Clears the trigPinLeft
    digitalWrite(trigPinRight, LOW);
    delayMicroseconds(2);
    // Sets the trigPinLeft on HIGH state for 10 micro seconds
    digitalWrite(trigPinRight, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPinRight, LOW);

  }

  else if(pulseStateRight == 1){
    unsigned long timeoutCheck = micros();
    long timeout_duration = timeoutCheck - pulseStartTimeRight;
    if (timeout_duration > 1000000){
      pulseStateRight = 0;
    }
    
  }
 
  else if (pulseStateRight == 2){
    unsigned long pulseDuration = pulseEndTimeLeft - pulseStartTimeRight;
    distance = pulseDuration * 0.034 / 2;
    
    Serial.print("id:distanceSensorRight_uniqueId:");
    Serial.print(unique_id);
    Serial.print("_value:");
    Serial.print(distance);
    Serial.print("_t:");
    Serial.print(t_distance_right);
    Serial.println();
    Serial.flush();
    unique_id +=1;
    pulseStateRight = 0;
    delayMicroseconds(SERIAL_DELAY);
    //delay(1);
  }


}

void loop() {

  handleLeftDistanceSensor();
  handleRightDistanceSensor();

    //delay(500);// remove this for actual setup
  //Read Touch sensor response
  lickState = !digitalRead(lickPin);
  unsigned long t_lick = millis();
  Serial.print("id:lickSensor_uniqueId:");
  Serial.print(unique_id);
  Serial.print("_value:");
  Serial.print(lickState);
  Serial.print("_t:");
  Serial.print(t_lick);
  Serial.println();
  Serial.flush();
  delayMicroseconds(SERIAL_DELAY);
  unique_id +=1;
  
  //delay(1);
    
  photoresistor_state = analogRead(photoresistor_analog);
  unsigned long t_photoresistor = millis();
  Serial.print("id:photoResistor_uniqueId:");
  Serial.print(unique_id);
  Serial.print("_value:");
  Serial.print(photoresistor_state);
  Serial.print("_t:");
  Serial.print(t_photoresistor);
  Serial.println();
  Serial.flush();
  unique_id +=1;
  delayMicroseconds(SERIAL_DELAY);
  //delay(1);
}

void pulseEndHandlerLeft() {
  if (digitalRead(echoPinLeft) == HIGH) {
    pulseStartTimeLeft = micros();
    pulseStateLeft = 1; //1 means pulse sent waiting for echo
  } else {
    pulseEndTimeLeft = micros();
    pulseStateLeft = 2; //echo received ready to transmit new one.
    t_distance_left = millis(); // device timestamp for distance sensor
  }
}

void pulseEndHandlerRight(){
  if (digitalRead(echoPinRight) == HIGH) {
    pulseStartTimeRight = micros();
    pulseStateRight = 1; //1 means pulse sent waiting for echo
  } else {
    pulseEndTimeRight = micros();
    pulseStateRight = 2; //echo received ready to transmit new one.
    t_distance_right = millis(); // device timestamp for distance sensor
  }

}
