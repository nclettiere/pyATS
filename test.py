from ats_sdk import *

sdk = ATS_SDK(False, addr="255.255.255.255")

sdk.connect()
sdk.get_quaternion()
sdk.disconnect()