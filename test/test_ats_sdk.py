import socket
import time
import json
try:
    from .test_ats_solver import *
except:
    from test_ats_solver import *

class ATS_SDK():
    def __init__(self, auto_connect : bool, addr="", port=7755, time_out=3.0):
        self.connected = False

        self.addr = addr
        self.port = port
        self.port_connection = 11165

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.bind(("", 7755))

        self.IP_DISCOVERING = True
        self.DISCOVERED_IP = None
        self.CONNECTION_MESSAGE = b">-establish_connection"
        self.DISCONNECTION_MESSAGE = b">-disconnect_requested"

        self.last_rotation_quat = Quaternion("none", 0, 0, 0, 0)

        if auto_connect:
            self.connect()

    def connect(self):
        try:
            data, server = self.soc.recvfrom(1024)
            data = data.decode('utf-8')
            if data != None:
                json.loads(data)
                print("Already connected. Resuming.")
                self.connected = True
                return True
        except:
            print("")
            

        while self.IP_DISCOVERING:
            message, address = self.soc.recvfrom(1024)
            message = message.decode('utf-8')
            
            if message.startswith("ATS_IP:"):
                self.DISCOVERED_IP =  (address[0], self.port_connection)
                self.IP_DISCOVERING = False

        conn = False
        for pings in range(1000):
            self.soc.sendto(self.CONNECTION_MESSAGE, self.DISCOVERED_IP)

            data, server = self.soc.recvfrom(1024)
            data = data.decode('utf-8')

            if data == ">-connection_accepted":
                print("Connection Established Successfully")
                self.connected = True
                conn = True
        return conn

    def disconnect(self):
        for pings in range(20):
            self.soc.sendto(self.DISCONNECTION_MESSAGE, self.DISCOVERED_IP)
            data, server = self.soc.recvfrom(1024)
            data = data.decode('utf-8')

            if data == ">-disconnect_accepted":
                print("Disconnection Established Successfully")
                self.connected = False
                return True
        return False

    def get_raw_data(self):
        data, server = self.soc.recvfrom(1024)
        data = data.decode('utf-8')
        if data != None:
            try:
                return json.loads(data)
            except:
                return None
        else:
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

def quat_multiply(q1 : Quaternion, q2 : Quaternion):
    qX = q1.qW * q2.qX + q1.qX * q2.qW + q1.qY * q2.qZ - q1.qZ * q2.qY
    qY = q1.qW * q2.qY + q1.qY * q2.qW + q1.qZ * q2.qX - q1.qX * q2.qZ
    qZ = q1.qW * q2.qZ + q1.qZ * q2.qW + q1.qX * q2.qY - q1.qY * q2.qX
    qW = q1.qW * q2.qW - q1.qX * q2.qX - q1.qY * q2.qY - q1.qZ * q2.qZ

    return Quaternion(q1.sensorName, qX, qY, qZ, qW)
