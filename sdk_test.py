from ats_sdk import ATS_SDK
import time

SDK = ATS_SDK(False)

SDK.connect()
print("Connected!")
print("Getting raw data ...")
time.sleep(10)
for i in range(20):
    print(SDK.get_raw_data())
print("Disconnecting in 15 seconds ...")
time.sleep(15)
SDK.disconnect()
print("Disconnected!")