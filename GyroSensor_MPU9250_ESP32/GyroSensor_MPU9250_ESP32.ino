#include <Wire.h>
#include "I2Cdev.h"
#include "MPU9250_9Axis.h"
#include "EEPROM.h"
#include <WiFi.h>
#include "AsyncUDP.h"

#define EEPROMUtils
#define SettingsUtils
#define SerialPortHelper
#define WiFiHelper
#define UDPClient
#define ProtocolHelper
#define DataUtils

#define PB_PIN 15
#define led_gpio 2
bool searchConnection = true;

short int ledSignalStatus = 0;

MPU9250 mpu(0x68);

uint8_t mpuIntStatus;
uint16_t packetSize;
uint16_t fifoCount;
uint8_t fifoBuffer[64];
volatile bool mpuInterrupt = false;

Quaternion q;

unsigned long timing;
unsigned long gyroDataIntervalSend = 50;



void setup() 
{
  pinMode(PB_PIN, INPUT);
  ledcAttachPin(led_gpio, 0);
  ledcSetup(0, 4000, 8);
  
  Serial.begin(115200);
  EEPROM.begin(500);

  InitSettings();
    InitWiFi();
    UDPConnect();
    
    Wire.begin();
    Wire.setClock(400000);
  
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  xTaskCreate(EventsCheck, "EventsCheckTask", 1024, (void*)&ledSignalStatus, 1, NULL);

  while(searchConnection) {
    int Push_button_state = digitalRead(PB_PIN);
    if ( Push_button_state == HIGH ) {
      ledSignalStatus = 1;
    }
  }
    
  mpu.initialize();

  delay(1000);

  uint8_t devStatus = mpu.dmpInitialize();

    if (devStatus == 0) 
    {
        mpu.setDMPEnabled(true);
        mpuIntStatus = mpu.getIntStatus();
        packetSize = mpu.dmpGetFIFOPacketSize();
    }
}

void loop() 
{
}

void EventsCheck( void * parameter ) {
  int brightness = 0;    // how bright the LED is
  int fadeAmount = 5;
  
  while(true) {
    short int statusLed = *((short int*)parameter);
    
    switch(statusLed){
      case 0:
        ledcWrite(0, 0);
        break;
      case 1: {
        ledcWrite(0, brightness); // set the brightness of the LED

        // change the brightness for next time through the loop:
        brightness = brightness + fadeAmount;

        // reverse the direction of the fading at the ends of the fade:
        if (brightness <= 0 || brightness >= 255) {
          fadeAmount = -fadeAmount;

        unsigned short int code = UDPReadData();
    
        if(code == 0) {
          printf("Connection established!");
          statusLed = 2;
          searchConnection = false;
        }else {
          printf("Waiting for conncection.");
        }
        
        vTaskDelay(30);
        
        break;
      }
      case 2:
        ledcWrite(0, 255);
        break;
    }
    
    vTaskDelay(10);
  }
}


void dmpDataReady() 
{
    mpuInterrupt = true;
}
