import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, PointerProperty)
import threading, time
import socket
import json

calibrate = False

def update_rot(self, context):
    global val
    bpy.context.object.rotation_mode = 'QUATERNION'
    bpy.context.object.rotation_quaternion  = val
    
class MyProperties(PropertyGroup):

    my_float_vector: FloatVectorProperty(
        name = "test",
        update=update_rot,
        description="Something",
        default=(0.0, 0.0, 0.0),
        subtype = 'QUATERNION'
        # 'COLOR', 'TRANSLATION', 'DIRECTION', 'VELOCITY', 
        # 'ACCELERATION', 'MATRIX', 'EULER', 'QUATERNION', 
        # 'AXISANGLE', 'XYZ', 'COLOR_GAMMA', 'LAYER'
        )

class SimpleOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
    
    def thread_update(self, context):
        UDP_IP_ADDRESS = "0.0.0.0"
        UDP_PORT_NO = 7755
        BUFFER_SIZE = 1024

        serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))

        while(True):
            global calibrate
            if calibrate:
                print('Calibration signal detected')
                calibrate = False
            else:
                data, addr = serverSock.recvfrom(BUFFER_SIZE)
                y = json.loads(data.decode('utf-8'))
                val = (float(y["qW"]), float(y["qX"]), float(y["qY"]), float(y["qZ"]))
                scene = bpy.context.scene
                scene['my_float_vector'] = val
                update_rot(self, context)
                scene.objects[0].active_object.rotation_mode = 'QUATERNION'
                scene.objects[0].active_object.rotation_quaternion  = val
                
                time.sleep(0.001) #update rate in seconds
    
    def execute(self, context):
        thread = threading.Thread(target=self.thread_update, args=[context])
        thread.start()
        return {'FINISHED'}

class CalibrateOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.calib_operator"
    bl_label = "Simple Object Operator"
    
    def execute(self, context):
        global calibrate
        calibrate = True
        return {'FINISHED'}

class OBPanel(bpy.types.Panel):
    bl_idname = "object.custom_panel"
    bl_label = "My Panels"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_context = "objectmode"  

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        layout.operator(SimpleOperator.bl_idname, text="Start Stream", icon="CONSOLE")
        layout.operator(CalibrateOperator.bl_idname, text="Calibrate", icon="CONSOLE")

classes = (
    MyProperties,
    SimpleOperator,
    CalibrateOperator,
    OBPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
