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

#define GPIO_ConnectionLED 1
int ConnectionLEDBrightness = 0;
int ConnectionLEDFadeAmount = 5;

TaskHandle_t Task1;

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
    Serial.begin(115200);
    EEPROM.begin(500);

    ledcAttachPin(GPIO_ConnectionLED, 0);
    ledcSetup(0, 5000, 8);

    xTaskCreatePinnedToCore(
      Task1code, /* Function to implement the task */
      "Task1", /* Name of the task */
      10000,  /* Stack size in words */
      NULL,  /* Task input parameter */
      0,  /* Priority of the task */
      &Task1,  /* Task handle. */
      0); /* Core where the task should run */

    InitSettings();
    InitWiFi();
    UDPConnect();
    
    Wire.begin();
    Wire.setClock(400000);
    
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
    mpuInterrupt = false;

    mpuIntStatus = mpu.getIntStatus();

    fifoCount = mpu.getFIFOCount();

    if ((mpuIntStatus & 0x10) || fifoCount == 1024) 
    {
        mpu.resetFIFO();
    } 
    else if (mpuIntStatus & 0x02) 
    {
        while (fifoCount < packetSize) 
            fifoCount = mpu.getFIFOCount();

        mpu.getFIFOBytes(fifoBuffer, packetSize);

        fifoCount -= packetSize;

        mpu.dmpGetQuaternion(&q, fifoBuffer);

        if (millis() - timing > gyroDataIntervalSend)
        {
            timing = millis();
            String sensorName = ReadStringEEPROM(2);
            String gyroDataJSONString = GetGyroDataJSONString(sensorName, q.x, q.y, q.z, q.w);
            UDPSendData(gyroDataJSONString);
        }
    }

    SerialPortReceive();
}

Void Task1code( void * parameter) {
  for(;;) {
    ledcWrite(0, ConnectionLEDBrightness);

    ConnectionLEDBrightness = ConnectionLEDBrightness + ConnectionLEDFadeAmount;

    if(ConnectionLEDBrightness <= 0 || ConnectionLEDBrightness >= 255) {
      ConnectionLEDFadeAmount = -ConnectionLEDFadeAmount;
    }
  }
}

void dmpDataReady() 
{
    mpuInterrupt = true;
}