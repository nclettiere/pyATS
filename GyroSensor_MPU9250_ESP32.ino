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
#define ProtocolHelper
#define DataUtils

// GPIOS 
#define GPIO_ConnectionLED 1

MPU9250 mpu(0x68);

uint8_t mpuIntStatus;
uint16_t packetSize;
uint16_t fifoCount;
uint8_t fifoBuffer[64];
volatile bool mpuInterrupt = false;

int ConnectionLEDBrightness = 0;
int ConnectionLEDFadeAmount = 5;

Quaternion q;

bool connection = false;


unsigned long timing;
unsigned long gyroDataIntervalSend = 50;

AsyncUDP udpClient;

void UDPConnect()
{
    String mocapServer = ReadStringEEPROM(3);
    String mocapServerPort = ReadStringEEPROM(4);

    IPAddress ipAddress = IPAddress();
    ipAddress.fromString(mocapServer);

    int port = mocapServerPort.toInt();
    
    udpClient.connect(ipAddress, port);   
}

AsyncUDP UDPGetClient()
{
    return udpClient;
}

void UDPSendData(String message)
{
    String mocapServerPort = ReadStringEEPROM(4);
    int port = mocapServerPort.toInt();

    char charBuffer[1024];
    message.toCharArray(charBuffer, 1024);

    if (udpClient.connected())
        udpClient.broadcastTo(charBuffer, port);
    else
        UDPConnect();
}


bool re = false;
bool UDPEstablishConnection()
{
    if(udpClient.listen(11165)) {
        Serial.print("UDP Listening on IP: ");
        Serial.println(WiFi.localIP());
        udpClient.onPacket([re](AsyncUDPPacket packet) {
            char* tmpStr = (char*) malloc(packet.length() + 1);
            memcpy(tmpStr, packet.data(), packet.length());
            tmpStr[packet.length()] = '\0'; // ensure null termination
            String testString = String(tmpStr);
            Serial.println(testString);
            if(testString == ">-establish_connection") {
                re = true;
                //reply to the client
              packet.printf(">-connection-established");
            }else {
              re = false;
            }
            free(tmpStr); // Strign(char*) creates a copy so we can delete our one

            return;
        });
    }

    return re;
}

bool close_conn = false;
bool UDPListenForClose()
{
    if(udpClient.listen(11165)) {
        Serial.print("UDP Listening on IP: ");
        Serial.println(WiFi.localIP());
        udpClient.onPacket([close_conn](AsyncUDPPacket packet) {
            char* tmpStr = (char*) malloc(packet.length() + 1);
            memcpy(tmpStr, packet.data(), packet.length());
            tmpStr[packet.length()] = '\0'; // ensure null termination
            String testString = String(tmpStr);
            Serial.println(testString);
            if(testString == ">-close_connection") {
                close_conn = true;
                //reply to the client
              packet.printf(">-connection_closed");
            }
            free(tmpStr); // Strign(char*) creates a copy so we can delete our one
        });
    }

    return close_conn;
}


void setup() 
{
    Serial.begin(115200);
    EEPROM.begin(500);

    //pinMode(GPIO_ConnectionLED, OUTPUT);

    InitSettings();
    InitWiFi();
    UDPConnect();

    Wire.begin();
    Wire.setClock(400000);

    ledcAttachPin(GPIO_ConnectionLED, 0);
    ledcSetup(0, 5000, 8);

    while(!connection) {
        if(UDPEstablishConnection()){
            Serial.println("Data Received\n");
            ledcWrite(0, 255);
            connection = true;
        }else {
          ledcWrite(0, ConnectionLEDBrightness);

          ConnectionLEDBrightness = ConnectionLEDBrightness + ConnectionLEDFadeAmount;

          if(ConnectionLEDBrightness <= 0 || ConnectionLEDBrightness >= 255) {
            ConnectionLEDFadeAmount = -ConnectionLEDFadeAmount;
          }
        }
    }

    Serial.println("Connection established.");
    
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

    if(UDPListenForClose()) {
        ESP.restart();
    }
    
}

   

void dmpDataReady() 
{
    mpuInterrupt = true;
}
