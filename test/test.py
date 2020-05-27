from test_ats_sdk import ATS_SDK
import time

SDK = ATS_SDK(False)

def main():
    print("Trying to connect ...")
    SDK.connect()
    time.sleep(10)
    for i in range(1000):
        dat = SDK.get_raw_data()
        print("Iter #{} => {}".format(i, dat))
    print("Loop test finished.")
    print("Disconnecting in 10 seconds")
    time.sleep(10)
    SDK.disconnect()
        
        
if __name__ == "__main__":
    main()
    
    