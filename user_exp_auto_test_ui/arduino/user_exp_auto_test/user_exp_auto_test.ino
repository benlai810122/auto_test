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
int buzzer_ping = 2;
int servo_ping_1 = 3;
int servo_ping_2 = 5;
int sound_ping = 4;
int click_times = 5;
int sleep_time = 60;

const int bufferSize = 64;      // Adjust as needed
char inputBuffer[bufferSize] = {'\0'};   // Store incoming data
int index = 0;

void setup() {
  Serial.begin(115200);
  myservo_mic_power.attach(servo_ping_1);  // attaches the servo on pin 3 to the Servo object
  myservo_mouse.attach(servo_ping_2);
  pinMode(sound_ping, INPUT);
  pinMode(buzzer_ping, OUTPUT);
  myservo_mic_power.write(0);
  myservo_mouse.write(0);
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
  if (mode == '0')
  {
    mouse_click(myservo_mic_power,0,51,1000);
  }
  else if (mode =='1')
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
  else if(mode =='2')
  {
    digitalWrite(buzzer_ping,HIGH);
    delay(5000);
    digitalWrite(buzzer_ping,LOW);
  }
  else if (mode =='3')
  {
    int counter = 0;
    while(counter<click_times)
    {
      mouse_click(myservo_mouse,0,52,500);
      counter++;
      delay(1000);
    }
  }
  else if (mode =='4')
  {
    int index_s = 2;
    String sleep_time_s = "";
    while (inputBuffer[index_s] != '\0')
    {
      sleep_time_s = sleep_time_s+inputBuffer[index_s];
      index_s++;
    }
    Serial.print(sleep_time_s);
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
}

void mouse_click(Servo myservo, int start, int end, int delay_time)
{
  myservo.write(end);
  delay(delay_time);
  myservo.write(start);
  delay(delay_time);
}

  
  