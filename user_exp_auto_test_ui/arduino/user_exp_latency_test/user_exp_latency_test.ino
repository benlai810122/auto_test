
const int SOLENOID_MOUSE_PIN = 9;   // for mouse latency PWM PIN
const int SOLENOID_KEYBOARD_PIN = 10;   // for keyboard latency PWM PIN
const unsigned long PRESS_MS = 100;  // Solenoid ON time (20~35 ms typical)
const unsigned long PRESS_STRENG = 145;  // Solenoid ON time (20~35 ms typical)
const unsigned long CONTINUE_PRESS_MS = 500;  // Solenoid ON time (20~35 ms typical)

const char MOUSE_LATENCY_SINGLE_CMD = 'a';
const char KEYBOARD_LATENCY_SINGLE_CMD = 'b';
const char MOUSE_LATENCY_WITH_KEYBOARD_CMD = 'c';
const char KEYBOARD_LATENCY_WITH_MOUSE_CMD = 'd';

int click_times = 5;
int random_click_times = 10;
int sleep_time = 60;

const int bufferSize = 64;      // Adjust as needed
char inputBuffer[bufferSize] = {'\0'};   // Store incoming data
int delay_time_array[] = {2000,3000,4000,5000};
int index = 0;

void setup() {
  pinMode(SOLENOID_MOUSE_PIN, OUTPUT);
  pinMode(SOLENOID_KEYBOARD_PIN, OUTPUT);
  digitalWrite(SOLENOID_MOUSE_PIN, LOW);  // Ensure OFF at startup
  digitalWrite(SOLENOID_KEYBOARD_PIN, LOW);  // Ensure OFF at startup
  Serial.begin(115200);
}

void loop() {

  while (Serial.available() > 0)
  {
    char received = Serial.read();
    // Check for newline or buffer overflow
    if (received == '\n' || index >= bufferSize - 1) {
      inputBuffer[index] = '\0'; // Null-terminate string
      //Serial.print("Received: ");
      //Serial.println(inputBuffer);
      test_start();
      index = 0; // Reset index for next input
    } else {
      inputBuffer[index++] = received;
    }
  }
}

void test_start()
{
  int mode = inputBuffer[0];
  //CMD_mouse_latency (for mouse latency test)
  if (mode == MOUSE_LATENCY_SINGLE_CMD)
  {
    pulse_solenoid(SOLENOID_MOUSE_PIN,PRESS_MS,PRESS_STRENG);
  }
  //CMD_keyboard_latency (for keyboard latency test)
  else if (mode == KEYBOARD_LATENCY_SINGLE_CMD)
  {
    pulse_solenoid(SOLENOID_KEYBOARD_PIN,PRESS_MS,PRESS_STRENG);
  }
  //MOUSE LATENCY TEST WITH KEYBOARD
  else if (mode == MOUSE_LATENCY_WITH_KEYBOARD_CMD)
  {
    analogWrite(SOLENOID_KEYBOARD_PIN, PRESS_STRENG);
    delay(CONTINUE_PRESS_MS);
    pulse_solenoid(SOLENOID_MOUSE_PIN,PRESS_MS,PRESS_STRENG);
    delay(CONTINUE_PRESS_MS);
    analogWrite(SOLENOID_KEYBOARD_PIN, 0); 
  }
  //KEYBOARD LATENCY TEST WITH MOUSE
  else if (mode == KEYBOARD_LATENCY_WITH_MOUSE_CMD)
  {
    analogWrite(SOLENOID_MOUSE_PIN, PRESS_STRENG);
    delay(CONTINUE_PRESS_MS);
    pulse_solenoid(SOLENOID_KEYBOARD_PIN,PRESS_MS,PRESS_STRENG);
    delay(CONTINUE_PRESS_MS);
    analogWrite(SOLENOID_MOUSE_PIN, 0); 
  }
  //for test
  else if (mode =='f')
  {
    for(int i = 0;i < 10; i++ )
    {
      pulse_solenoid(SOLENOID_MOUSE_PIN,PRESS_MS,PRESS_STRENG);
      delay(40);
      pulse_solenoid(SOLENOID_KEYBOARD_PIN,PRESS_MS,PRESS_STRENG);
      delay(400);
      Serial.println("PULSE_Ttt");
    }
  }

}

void pulse_solenoid(uint8_t pin , unsigned long press_ms, unsigned long press_streng) {
  analogWrite(pin, press_streng);   // ~50% duty PWM
  delay(press_ms);
  analogWrite(pin, 0);     // OFF
}


  
  