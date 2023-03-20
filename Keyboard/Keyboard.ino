#include "DigiKeyboard.h"

void setup() {

}

int sensorValue = 0;

void loop() {
  sensorValue = analogRead(1);
  
  if(sensorValue>=1000){
    DigiKeyboard.print(" ");                   
    DigiKeyboard.delay(1000);
                        
    }
    
}  

            




























                                

 
