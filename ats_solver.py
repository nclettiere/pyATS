import numpy as np
import math
from pyquaternion import Quaternion as pyQuaternion
import json

class Quaternion:
    def __init__(self, sensor_name, qX=0.0, qY=0.0, qZ=0.0, qW=0.0):
        self.type = "gyroData"
        self.sensorName = sensor_name
        self.qX=qX
        self.qY=qY
        self.qZ=qZ
        self.qW=qW

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    def inverse(self):
        quaternion2 =  Quaternion(self.sensorName, 0, 0, 0, -1)
        num2 = (self.qX * self.qX) + (self.qY * self.qY) + (self.qZ * self.qZ) + (self.qW * self.qW)
        num = (1.0 / num2)

        quaternion2.qX = -self.qX * num
        quaternion2.qY = -self.qY * num
        quaternion2.qZ = -self.qZ * num
        quaternion2.qW = self.qW * num

        return quaternion2
        
    def get_array(self):
        return [self.qW, self.qX, self.qY, self.qZ]


def Fmod(X : float, Y : float): 
    if (np.absolute(Y) <= 1e-8):
        return 0

    Quotient = float((int(X / Y)))
    IntPortion = Y * Quotient

    if (np.absolute(IntPortion) > np.absolute(X)):
        IntPortion = X

    Result = X - IntPortion
    return Result
       

def normalize_axis(angle : float):
    angle = Fmod(angle, 360)
    if (angle < 0.0):
        angle += 360.0
    if (angle > 180.0):
        angle -= 360.0

    return angle
    
        
def quat_to_euler(quat):

    euler = [0.0, 0.0, 0.0]

    X = quat.qX
    Y = quat.qY
    Z = quat.qZ
    W = quat.qW

    SingularityTest = Z * X - W * Y
    YawY = 2.0 * (W * Z + X * Y)
    YawX = (1.0 - 2.0 * (Y * Y + Z * Z))

    RAD_TO_DEG = float(((180) / np.pi))

    if (SingularityTest < -0.4999995):
    
        euler[0] = -90.0
        euler[1] = float(math.atan2(YawY, YawX)) * RAD_TO_DEG
        euler[2] = normalize_axis((float)(-euler.Y - (2.0 * math.atan2(X, W) * RAD_TO_DEG)))
    
    elif (SingularityTest > 0.4999995):
        euler[0] = 90.0
        euler[1] = float(math.atan2(YawY, YawX)) * RAD_TO_DEG
        euler[2] = normalize_axis(float(euler.Y - (2.0 * math.atan2(X, W) * RAD_TO_DEG)))   
    else:
        euler[0] = float(math.asin(2.0 * (SingularityTest))) * RAD_TO_DEG
        euler[1] = float(math.atan2(YawY, YawX)) * RAD_TO_DEG
        euler[2] = float(math.atan2(-2.0 * (W * X + Y * Z), (1.0 - 2.0 * (X * X + Y * Y)))) * RAD_TO_DEG
    

    return euler
    

def interpolate_angles(q1 : Quaternion, q2 : Quaternion, amount=0.5):
    from scipy.spatial.transform import Slerp
    
    qn1 = pyQuaternion(x=q1.qX, y=q1.qY, z=q1.qZ, w=q1.qW)
    qn2 = pyQuaternion(x=q2.qX, y=q2.qY, z=q2.qZ, w=q2.qW)
    
    qnew = pyQuaternion.slerp(qn1, qn2, amount=amount)
    
    print("{} {} {} {}".format(qnew.x, qnew.y, qnew.z, qnew.w))

    return Quaternion(q2.sensorName, qX=qnew.x, qY=qnew.y, qZ=qnew.z, qW=qnew.w)


def quat_multiply(q1 : Quaternion, q2 : Quaternion):
    qX = q1.qW * q2.qX + q1.qX * q2.qW + q1.qY * q2.qZ - q1.qZ * q2.qY
    qY = q1.qW * q2.qY + q1.qY * q2.qW + q1.qZ * q2.qX - q1.qX * q2.qZ
    qZ = q1.qW * q2.qZ + q1.qZ * q2.qW + q1.qX * q2.qY - q1.qY * q2.qX
    qW = q1.qW * q2.qW - q1.qX * q2.qX - q1.qY * q2.qY - q1.qZ * q2.qZ

    return Quaternion(q1.sensorName, qX, qY, qZ, qW)

class QuaternionCalibrationModel:
    def __init__(self, GyroQuaternion : Quaternion, CalibrationCount=0, CalibrationComplete=False):
        self.GyroQuaternion = GyroQuaternion
        self.CalibrationCount = CalibrationCount
        self.CalibrationComplete = CalibrationComplete

class SensorCalibration:
    def __init__(self):
        self.calibration_dictionaty = {}
    
    def push(self, quat : Quaternion):
        if not any(quat.sensorName in c for c in self.calibration_dictionaty):
            self.calibration_dictionaty.update({quat.sensorName : Quaternion(quat.sensorName, quat.qX, quat.qY, quat.qZ, quat.qW)})

    def get_calib_result(self, sensor_name : str):
        return self.calibration_dictionaty[next(f for f in self.calibration_dictionaty if f == sensor_name)]
        