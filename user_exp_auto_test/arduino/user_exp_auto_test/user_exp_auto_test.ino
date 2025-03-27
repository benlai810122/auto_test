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
  if (Serial.available()>0)
  {
    
    char mode = Serial.read();
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
    }
    else if(mode =='2')
    {
      digitalWrite(buzzer_ping,HIGH);
      delay(2000);
      digitalWrite(buzzer_ping,LOW);
    }
    else if (mode =='3')
    {
      int counter = 0;
      while(counter<click_times)
      {
        mouse_click(myservo_mouse,0,22,500);
        counter++;
        delay(1000);
      }
      
    }
    else if (mode =='4')
    {
      for (int i = 0;i<sleep_time;i++)
        delay(1000);

      int counter = 0;
      while(counter<click_times)
      {
        mouse_click(myservo_mouse,0,22,500);
        counter++;
        delay(1000);
      }
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

  
  