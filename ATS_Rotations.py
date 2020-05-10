import numpy as np
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

    def normalize_axis(self, angle : float):
        angle = self.Fmod(angle, 360)
        if (angle < 0.0):
            angle += 360.0
        if (angle > 180.0):
            angle -= 360.0

        return angle
    
    def Fmod(self, X : float, Y : float): 
        if (np.absolute(Y) <= 1e-8):
            return 0

        Quotient = float((int(X / Y)))
        IntPortion = Y * Quotient

        if (np.absolute(IntPortion) > np.absolute(X)):
            IntPortion = X

        Result = X - IntPortion
        return Result
    

    ## TODO def quat_to_euler(self, quat : Quaternion):

class GyroQuaternionCalibrationModel:
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
