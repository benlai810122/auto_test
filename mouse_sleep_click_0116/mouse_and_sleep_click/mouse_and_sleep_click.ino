/* Sweep
 by BARRAGAN <http://barraganstudio.com>
 This example code is in the public domain.

 modified 8 Nov 2013
 by Scott Fitzgerald
 https://www.arduino.cc/en/Tutorial/LibraryExamples/Sweep
*/

#include <Servo.h>
Servo myservo;  // create Servo object to control a servo
long ms_sleep_array[] = {0,180,360,1800};
int delay_time_array[] = {2000,3000,4000,5000};
int os_wakeup = 120;
int click_freg = 5;


void setup() {
  Serial.begin(115200);
  myservo.attach(3);  // attaches the servo on pin 3 to the Servo object
  randomSeed(analogRead(0));
}

void loop() {

  int click_times = os_wakeup/click_freg;
  if (Serial.available()>0)
  {
    char mode = Serial.read();
    {
      mode = mode - '0';
      //if mode == 0 , mouse keep clicking randomly
      if(mode == 0)
      {
         while(1)
        {
          int index = random(4);
          int delay_time = delay_time_array[index];
          mouse_click();
          delay(delay_time);
          Serial.write("c");
        }
      }
      //if mode == other(1~3), mouse only click when os wake up
      else
      {
        while(1)
        {
          for(int i = 0; i<click_times;i++)
          {
            mouse_click();
            delay(click_freg*1000);
          }
          Serial.write('0');
          for(int n = 0;n<ms_sleep_array[mode];n++)
          {
            delay(1000);
          }
        }

      }
      
    }
  }
}
void mouse_click()
{
      myservo.write(0);
      delay(100);
      myservo.write(20);
      delay(100);
}
  
  