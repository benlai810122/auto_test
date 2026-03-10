/* Sweep
 by BARRAGAN <http://barraganstudio.com>
 This example code is in the public domain.

 modified 8 Nov 2013
 by Scott Fitzgerald
 https://www.arduino.cc/en/Tutorial/LibraryExamples/Sweep
*/

#include <Servo.h>
Servo myservo_mic_power;  // create Servo object to control a servo
Servo myservo_mouse;
Servo myservo_keyboard; 
const int buzzer_ping = 2;
const int servo_ping_1 = 3;
const int sound_ping = 4;
const int servo_ping_2 = 5;
const int servo_ping_3 = 6;

const char CMD_SERVO_HEADSET_POWER = '0';
const char CMD_SOUND_DETECTER = '1';
const char CMD_BUZZER = '2';
const char CMD_MOUSE_CLICKING = '3';
const char CMD_MOUSE_DELAY_CLICKING = '4';
const char CMD_MOUSE_RANDOM_CLICKING = '5';
const char CMD_KEYBOARD_CLICKING = '6';
const char CMD_KEYBOARD_RANDOM_CLICKING = '7';


int click_times = 5;
int random_click_times = 10;
int sleep_time = 60;

const int bufferSize = 64;      // Adjust as needed
char inputBuffer[bufferSize] = {'\0'};   // Store incoming data
int delay_time_array[] = {2000,3000,4000,5000};
int index = 0;

void setup() {

  pinMode(sound_ping, INPUT);
  pinMode(buzzer_ping, OUTPUT);
  myservo_mic_power.attach(servo_ping_1);  // attaches the servo on pin 3 to the Servo object
  myservo_mouse.attach(servo_ping_2);
  myservo_keyboard.attach(servo_ping_3);
  myservo_mic_power.write(0);
  myservo_mouse.write(0);
  myservo_keyboard.write(0);
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
  //CMD_servo (for headset power control)
  if (mode == CMD_SERVO_HEADSET_POWER)
  {
    mouse_click(myservo_mic_power,0,51,1000);
  }
  //CMD_voice_detect (for headset input test)
  else if (mode == CMD_SOUND_DETECTER)
  {
    int detected_time = 1000;
    int ping_states = 0 ;
    while(detected_time>0)
    {
      ping_states = ping_states | digitalRead(sound_ping);
      delay(10);
      detected_time--;
    }
    Serial.write(ping_states+0x30);
  }
  //CMD_buzzer (for headset output test)
  else if(mode == CMD_BUZZER)
  {
    digitalWrite(buzzer_ping,HIGH);
    delay(5000);
    digitalWrite(buzzer_ping,LOW);
  }
  //CMD_mouse_clicking (for mouse function test)
  else if (mode == CMD_MOUSE_CLICKING)
  {
    int counter = 0;
    while(counter<click_times)
    {
      mouse_click(myservo_mouse,0,52,500);
      counter++;
      delay(1000);
    }
  }
  //CMD_mouse_delay_clicking (for MS power states)
  else if (mode == CMD_MOUSE_DELAY_CLICKING)
  {
    int index_s = 2;
    String sleep_time_s = "";
    while (inputBuffer[index_s] != '\0')
    {
      sleep_time_s = sleep_time_s+inputBuffer[index_s];
      index_s++;
    }
    //Serial.print(sleep_time_s);
    sleep_time = sleep_time_s.toInt();
    int counter = 0;
    
    for(int i = 0;i < sleep_time; i++ )
      delay(1000);

    while(counter<click_times)
    {
      mouse_click(myservo_mouse,0,52,500);
      counter++;
      delay(1000);
    }
  }
  //CMD_mouse_random_clicking (for mouse random clicking test)
  else if (mode == CMD_MOUSE_RANDOM_CLICKING)
  {
    int counter = 0;
    while(counter<random_click_times)
    {
      mouse_click(myservo_mouse,0,52,500);
      counter++;
      int index = random(4);
      int delay_time = delay_time_array[index];
      delay(delay_time);
    }
    Serial.write("c");
  }
//CMD_keyboard_clicking (for mouse function test)
  else if (mode == CMD_KEYBOARD_CLICKING)
  {
    int counter = 0;
    while(counter<click_times)
    {
      mouse_click(myservo_keyboard,0,52,500);
      counter++;
      delay(1000);
    }
  }
  //CMD_keyboard_random_clicking (for keyboard random clicking test)
  else if (mode == CMD_KEYBOARD_RANDOM_CLICKING)
  {
    int counter = 0;
    while(counter<random_click_times)
    {
      mouse_click(myservo_keyboard,0,50,500);
      counter++;
      int index = random(4);
      int delay_time = delay_time_array[index];
      delay(delay_time);
    }
    Serial.write("c");
  }
  // for test
  else if (mode =='f')
  {
    Serial.write("c");
  }

}

void mouse_click(Servo myservo, int start, int end, int delay_time)
{
  myservo.write(end);
  delay(delay_time);
  myservo.write(start);
  delay(delay_time);
}

  
  