import numpy as np

class Quaternion:
    def __init__(self, sensor_name, qX=0.0, qY=0.0, qZ=0.0, qW=0.0):
        self.sensorName = sensor_name
        self.qX=qX
        self.qY=qY
        self.qZ=qZ
        self.qW=qW

    def inverse(self, quat : Quaternion):
        quaternion2 =  Quaternion(quat.sensorName, 0, 0, 0, -1)
        num2 = (quat.qX * quat.qX) + (quat.qY * quat.qY) + (quat.qZ * quat.qZ) + (quat.qW * quat.qW)
        num = (1.0 / num2)

        quaternion2.qX = -quat.qX * num
        quaternion2.qY = -quat.qY * num
        quaternion2.qZ = -quat.qZ * num
        quaternion2.qW = quat.qW * num

        return quaternion2

    def multiply(self, q1 : Quaternion, q2 : Quaternion):
        qX = q1.qW * q2.qX + q1.qX * q2.qW + q1.qY * q2.qZ - q1.qZ * q2.qY
        qY = q1.qW * q2.qY + q1.qY * q2.qW + q1.qZ * q2.qX - q1.qX * q2.qZ
        qZ = q1.qW * q2.qZ + q1.qZ * q2.qW + q1.qX * q2.qY - q1.qY * q2.qX
        qW = q1.qW * q2.qW - q1.qX * q2.qX - q1.qY * q2.qY - q1.qZ * q2.qZ
        return Quaternion(q1.sensorName, qX, qY, qZ, qW)

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