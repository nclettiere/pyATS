import socket
import time
import json
try:
    from .ats_solver import *
except:
    from ats_solver import *

class ATS_SDK():
    def __init__(self, addr="", port=7755, time_out=3.0):
        self.connected = False

        self.addr = addr
        self.port = port
        self.port_connection = 11165

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.bind(("", 7755))

        self.last_rotation_quat = Quaternion("none", 0, 0, 0, 0)

    def get_raw_data(self):
        try:
            data, server = self.soc.recvfrom(1024)
            data = data.decode('utf-8')
            if data != None:
                return json.loads(data)
            else:
                return None
        except:
            return None

    def get_quaternion(self, axis_settings : dict):
        data = self.get_raw_data()
        if data != None:
            w = float(data["qW"])
            x = float(data["qX"])
            y = float(data["qY"])
            z = float(data["qZ"])

            ## Axis Tweaks (Inversions, Locks)
            if axis_settings['X_Tweak'] == 'X':
                x = x
            elif axis_settings['X_Tweak'] == 'Y':
                x = y
            else:
                x = z

            if axis_settings['Y_Tweak'] == 'X':
                y = x
            elif axis_settings['Y_Tweak'] == 'Y':
                y = y
            else:
                y = z

            if axis_settings['Z_Tweak'] == 'X':
                z = x
            elif axis_settings['Z_Tweak'] == 'Y':
                z = y
            else:
                z = z

            if axis_settings['X_Inversion']:
                x = x * -1
            if axis_settings['Y_Inversion']:
                y = y * -1
            if axis_settings['Z_Inversion']:
                z = z * -1      
        
            if axis_settings['X_Lock']:
                x = self.last_rotation_quat.qX
            if axis_settings['Y_Lock']:
                y = self.last_rotation_quat.qY
            if axis_settings['Z_Lock']:
                z = self.last_rotation_quat.qZ
            if axis_settings['X_Lock'] and axis_settings['Y_Lock'] and axis_settings['Z_Lock']:
                w = self.last_rotation_quat.qW

            return Quaternion(axis_settings["Name"], qX=x, qY=y, qZ=z, qW=w)

        else:
            return None