import socket
import time
import json

from ats_solver import *

class ATS_SDK():
    def __init__(self, auto_connect : bool, addr="0.0.0.0", port=7755, time_out=3.0):
        self.connected = False

        self.addr = addr
        self.port = port

        self.port_connection = 11153
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(time_out)

        self.last_rotation_quat = Quaternion("none", 0, 0, 0, 0)

        if auto_connect:
            self.connect()

    def connect(self):
        for pings in range(20):
            message = b'>-establish_connection'
            addr = (self.addr, self.port_connection)

            start = time.time()
            self.client_socket.sendto(message, addr)
            try:
                data, server = self.client_socket.recvfrom(1024)

                # Successful connection
                if data.decode('utf-8') == ">-connection_accepted":
                    self.connected = True

                    end = time.time()
                    elapsed = end - start
                    print(f'{data} {pings} {elapsed}')
                    
                    return True
            except socket.timeout:
                print('REQUEST TIMED OUT')
        return False

    def disconnect(self):
        for pings in range(20):
            message = b'>-disconnection_requested'
            addr = (self.addr, self.port_connection)

            start = time.time()
            self.client_socket.sendto(message, addr)
            try:
                data, server = self.client_socket.recvfrom(1024)

                # Successful connection
                if data.decode('utf-8') == ">-disconnection_accepted":
                    self.connected = True

                    end = time.time()
                    elapsed = end - start
                    print(f'{data} {pings} {elapsed}')
                    return True
            except socket.timeout:
                print('REQUEST TIMED OUT')
        
        return False

    def get_raw_data(self):
        if self.connected:
            data, server = self.client_socket.recvfrom(1024)
            data = json.loads(data.decode('utf-8'))

            return data
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
                w = last_rotation_quat.qW

            return Quaternion(axis_settings["Name"], qX=x, qY=y, qZ=z, qW=w)

        else:
            return None
