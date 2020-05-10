from ATS_Rotations import Quaternion
from ATS_Rotations import GyroQuaternionCalibrationModel
from ATS_Rotations import SensorCalibration
import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty)
import sys, threading, time
import math
import socket
import json
import binascii

calibrate = False
streaming = False
calib_started = False
anim_frame = 1
calibration_count = 0
calibration_samples = 100

sensor_calibration = SensorCalibration()


def update_x_enum(self, context):
    # self = current scene in an EnumProperty callback!
    print('X setted to {}'.format(context.scene.custom_props.enum_axis_x))
    
def update_y_enum(self, context):
    # self = current scene in an EnumProperty callback!
    print('Y setted to {}'.format(context.scene.custom_props.enum_axis_y))
    
def update_z_enum(self, context):
    # self = current scene in an EnumProperty callback!
    print('Z setted to {}'.format(context.scene.custom_props.enum_axis_z))
    
def lock_x_changed(self, context):
    # self = current scene in an EnumProperty callback!
    print('X Stream lock setted to {}'.format(bool(context.scene.custom_props.axis_x_lock)))
    
def lock_y_changed(self, context):
    # self = current scene in an EnumProperty callback!
    print('Y Stream lock setted to {}'.format(bool(context.scene.custom_props.axis_y_lock)))
    
def lock_z_changed(self, context):
    # self = current scene in an EnumProperty callback!
    print('Z Stream lock setted to {}'.format(bool(context.scene.custom_props.axis_z_lock)))
    

 
class MyProperties(PropertyGroup):

    RotationQuat: FloatVectorProperty(
        name = "RotationQuat",
        default=(0.0, 0.0, 0.0),
        subtype = 'QUATERNION'
        # 'COLOR', 'TRANSLATION', 'DIRECTION', 'VELOCITY', 
        # 'ACCELERATION', 'MATRIX', 'EULER', 'QUATERNION', 
        # 'AXISANGLE', 'XYZ', 'COLOR_GAMMA', 'LAYER'
    )
        
    calibration_samples: IntProperty(
        name = "CalibrationSamples",
        default=100,
        min=100,
        max=1000
    )
        
    enum_axis_x: EnumProperty(
        name = "X Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("0", "X", "Set default"),
            ("1", "Y", "Switch X to Y Axis"),     
            ("2", "Z", "Switch X to Z Axis"),                 
        ],
        default="0",
        update=update_x_enum
    )

    enum_axis_y: EnumProperty(
        name = "Y Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("0", "X", "Switch Y to Z Axis"),
            ("1", "Y", "Set default"),     
            ("2", "Z", "Switch Y to Z Axis"),                 
        ],
        default="1",
        update=update_y_enum
    )

    enum_axis_z: EnumProperty(
        name = "Z Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("0", "X", "Switch Z to X Axis"),
            ("1", "Y", "Switch Z to Y Axis"),     
            ("2", "Z", "Set default"),                 
        ],
        default="2",
        update=update_z_enum
    )
    
    axis_x_lock: BoolProperty(
        name = "Lock/Unlock X Axis",
        description = "Lock/Unlock X Axis",
        default=False,
        update=lock_x_changed
    )
    
    axis_y_lock: BoolProperty(
        name = "Lock/Unlock Y Axis",
        description = "Lock/Unlock Y Axis",
        default=False,
        update=lock_y_changed
    )
  
    axis_z_lock: BoolProperty(
        name = "Lock/Unlock Z Axis",
        description = "Lock/Unlock Z Axis",
        default=False,
        update=lock_z_changed
    )
   
    axis_x_invert: BoolProperty(
        name = "Invert X Axis",
        description = "Invert X Axis",
        default=False
    )

    axis_y_invert: BoolProperty(
        name = "Invert Y Axis",
        description = "Invert Y Axis",
        default=False
    )    
    
    axis_z_invert: BoolProperty(
        name = "Invert Z Axis",
        description = "Invert Z Axis",
        default=False
    )
 

class thread_with_trace(threading.Thread): 
  def __init__(self, *args, **keywords): 
    threading.Thread.__init__(self, *args, **keywords) 
    self.killed = False
  
  def start(self): 
    self.__run_backup = self.run 
    self.run = self.__run       
    threading.Thread.start(self) 
  
  def __run(self): 
    sys.settrace(self.globaltrace) 
    self.__run_backup() 
    self.run = self.__run_backup 
  
  def globaltrace(self, frame, event, arg): 
    if event == 'call': 
      return self.localtrace 
    else: 
      return None
  
  def localtrace(self, frame, event, arg): 
    if self.killed: 
      if event == 'line': 
        raise SystemExit() 
    return self.localtrace 
  
  def kill(self): 
    self.killed = True


def quat_multiply(q1 : Quaternion, q2 : Quaternion):
    qX = q1.qW * q2.qX + q1.qX * q2.qW + q1.qY * q2.qZ - q1.qZ * q2.qY
    qY = q1.qW * q2.qY + q1.qY * q2.qW + q1.qZ * q2.qX - q1.qX * q2.qZ
    qZ = q1.qW * q2.qZ + q1.qZ * q2.qW + q1.qX * q2.qY - q1.qY * q2.qX
    qW = q1.qW * q2.qW - q1.qX * q2.qX - q1.qY * q2.qY - q1.qZ * q2.qZ

    return Quaternion(q1.sensorName, qX, qY, qZ, qW)

def thread_update():
    global calibrate
    global calib_started
    global sensor_calibration
    global anim_frame
    global calibration_count
    global streaming
    
    UDP_IP_ADDRESS = "0.0.0.0"
    UDP_PORT_NO = 7755
    BUFFER_SIZE = 1024

    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    
    scene = bpy.context.scene
    
    ob = bpy.data.objects[bpy.context.scene.arma]
    pbone = ob.pose.bones["Head"]
    
    last_rotation_quat = pbone.rotation_quaternion
    
    while(streaming):
        try:
            data, addr = serverSock.recvfrom(BUFFER_SIZE)
            data = json.loads(data.decode('utf-8'))
            
            w = float(data["qW"])
            x = float(data["qX"])
            y = float(data["qY"])
            z = float(data["qZ"])
    
            #print(type(bpy.context.scene.custom_props.enum_axis_x))
            
            if bpy.context.scene.custom_props.enum_axis_x == '0':
                x = float(data["qX"])
            elif bpy.context.scene.custom_props.enum_axis_x == '1':
                x = float(data["qY"])
            else:
                x = float(data["qZ"])
                
            if bpy.context.scene.custom_props.enum_axis_y == '0':
                y = float(data["qX"])
            elif bpy.context.scene.custom_props.enum_axis_y == '1':
                y = float(data["qY"])
            else:
                y = float(data["qZ"])
                
            if bpy.context.scene.custom_props.enum_axis_z == '0':
                z = float(data["qX"])
            elif bpy.context.scene.custom_props.enum_axis_z == '1':
                z = float(data["qY"])
            else:
                z = float(data["qZ"])
            
    
    
            if bpy.context.scene.custom_props.axis_x_invert == True:
                x = x * -1
                print('Inversion signal for X Axis applied')
            
            if bpy.context.scene.custom_props.axis_y_invert == True:
                y = y * -1
                print('Inversion signal for X Axis applied')
            
            if bpy.context.scene.custom_props.axis_z_invert == True:
                z = z * -1
                print('Inversion signal for X Axis applied')
                
                
                
                
            if bpy.context.scene.custom_props.axis_x_lock == True and bpy.context.scene.custom_props.axis_y_lock == True and bpy.context.scene.custom_props.axis_z_lock == True:
                w = last_rotation_quat[0]
                print('Lock signal for W Axis applied')        
            
            if bpy.context.scene.custom_props.axis_x_lock == True:
                x = last_rotation_quat[1]
                print('Lock signal for X Axis applied')
            
            if bpy.context.scene.custom_props.axis_y_lock == True:
                y = last_rotation_quat[2]
                print('Lock signal for Y Axis applied')
            
            if bpy.context.scene.custom_props.axis_z_lock == True:
                z = last_rotation_quat[3]
                print('Lock signal for Z Axis applied')
                
            if bpy.context.scene.custom_props.axis_x_lock == True and bpy.context.scene.custom_props.axis_y_lock == True and bpy.context.scene.custom_props.axis_z_lock == True:
                w = last_rotation_quat[0]
                print('Lock signal for W Axis applied')
            
            
            rotation_quat = (w, x, y, z)
            last_rotation_quat = rotation_quat
    
            #bpy.ops.transform.rotate(value=float(z), orient_axis='Z')
    
            #scene['RotationQuat'] = rotation_quat
            #bpy.context.scene.objects[bpy.context.scene.arma].select_get()
            #bpy.scene.objects[0].rotation_mode = 'QUATERNION'
            #bpy.scene.objects[0].rotation_quaternion  = rotation_quat
            
            # Set rotation mode to Euler XYZ, easier to understand
            # than default quaternions
            # select axis in ['X','Y','Z']  <--bone local
            pbone.rotation_mode = 'QUATERNION'
            print(int(bpy.context.scene.custom_props.calibration_samples))
            print(calibration_count)
            q = Quaternion('GyroSensor00', qX=x, qY=y, qZ=z, qW=w)
            sensor_calibration.push(q)
            
            gyroQuaternionInverse = q.inverse()
    
            gyroQuaternionCalibrationResult = sensor_calibration.get_calib_result('GyroSensor00')
    
            if gyroQuaternionCalibrationResult != None:
                gyroQuaternion = quat_multiply(gyroQuaternionInverse, gyroQuaternionCalibrationResult)
    
                MESSAGE = gyroQuaternion.toJSON().encode()
                serverSock.sendto(MESSAGE, ("192.168.1.47", 8855))
    
                quat = (gyroQuaternion.qW, gyroQuaternion.qX, gyroQuaternion.qY, gyroQuaternion.qZ)
                
                pbone.rotation_quaternion = quat
                calibration_count = calibration_count + 1
                print('yes?')
            else:
                print('result none')
                calibration_count = calibration_count + 1
            
            #insert a keyframe
            pbone.keyframe_insert(data_path="rotation_quaternion", frame=anim_frame)
            #scene.objects[0].transform.rotate(value=float(z), orient_axis='Z')
            
            anim_frame += 1
            
            time.sleep(0.001) #update rate in seconds
        except:
            print("meep")

thread = None


class SimpleOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        return not calibrate
        
    def execute(self, context):
        global streaming
        global thread
        global anim_frame
        if not streaming:
            streaming = True
            thread = thread_with_trace(target = thread_update) 
            thread.start() 
            if thread.isAlive(): 
                print('thread started')
        else:
            streaming = False
            thread.kill() 
            thread.join() 
            if not thread.isAlive(): 
                print('thread killed') 
                anim_frame = 1
                
        return {'FINISHED'}

class CalibrateOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.calib_operator"
    bl_label = "Simple Object Operator"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        return not calibrate
    
    def execute(self, context):
        global calibrate
        global sensor_calibration
        #calibrate = True
        sensor_calibration = SensorCalibration()
        self.report({'PROPERTY'}, "Calibration has started, please wait.")
        return {'FINISHED'}

class OBPanel(bpy.types.Panel):
    bl_idname = "object.ats_panel"
    bl_label = "ATS"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "ATS Linker"
    bl_context = "posemode"  

    def draw(self, context):
        scene = context.scene
        ob = context.object
        layout = self.layout
        customprops = scene.custom_props
        
        global streaming
        text="Start Stream"
        icon="TRIA_RIGHT"
        if streaming:
            text="Disconnect"
            icon="PAUSE"
        else:
            text="Connect"
            icon="TRIA_RIGHT"
            
        icon_lock_x = "UNLOCKED"
        icon_lock_y = "UNLOCKED"
        icon_lock_z = "UNLOCKED"
        text_lock_x = "Unlocked"
        text_lock_y = "Unlocked"
        text_lock_z = "Unlocked"
        
        if bpy.context.scene.custom_props.axis_x_lock == True:
            icon_lock_x = "LOCKED"
            text_lock_x = "Locked"
        else:
            icon_lock_x = "UNLOCKED"
            text_lock_x = "Unlocked"
            
        if bpy.context.scene.custom_props.axis_y_lock == True:
            icon_lock_y = "LOCKED"
            text_lock_y = "Locked"
        else:
            icon_lock_y = "UNLOCKED"
            text_lock_y = "Unlocked"
            
        if bpy.context.scene.custom_props.axis_z_lock == True:
            icon_lock_z = "LOCKED"
            text_lock_z = "Locked"
        else:
            icon_lock_z = "UNLOCKED"
            text_lock_z = "Unlocked"
            
        view = context.space_data
        overlay = view.overlay
         
        if calibrate:
           layout.enabled = False 
        else:
            layout.enabled = True 
         
        box = layout.box()
        box.label(text="General")
        col = box.column()
        col.operator(SimpleOperator.bl_idname, text=text, icon=icon)
        col.prop(customprops, "calibration_samples", text="Calib. Samples")
        col.operator(CalibrateOperator.bl_idname, text="Calibrate", icon="SNAP_FACE_CENTER")
        col.prop(scene, "arma", icon="ARMATURE_DATA", text="Rig")
        
        box = layout.box()
        col = box.column()
        col.label(text="Axis Tweaks")
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_x", text="X is")
        row.prop(customprops, "axis_x_invert", text="", toggle=1, icon='NORMALS_VERTEX')
        row.prop(customprops, "axis_x_lock", text=text_lock_x, icon=icon_lock_x)
        
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_y", text="Y is")
        row.prop(customprops, "axis_y_invert", text="", toggle=1, icon='NORMALS_VERTEX')
        row.prop(customprops, "axis_y_lock", text=text_lock_y, icon=icon_lock_y)
        
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_z", text="Z is")
        row.prop(customprops, "axis_z_invert", text="", toggle=1, icon='NORMALS_VERTEX')
        row.prop(customprops, "axis_z_lock", text=text_lock_z, icon=icon_lock_z)
        
        box = layout.box()
        col = box.column()
        col.label(text="Animation")
        row = col.row(align=True)
        col.operator(SimpleOperator.bl_idname, text="Start Animation", icon=icon)

def arma_items(self, context):
    obs = []
    for ob in context.scene.objects:
        if ob.type == 'ARMATURE':
            obs.append((ob.name, ob.name, ""))
    return obs

def arma_upd(self, context):
    self.arma_coll.clear()
    for ob in context.scene.objects:
        if ob.type == 'ARMATURE':
            item = self.arma_coll.add()
            item.name = ob.name

def bone_items(self, context):
    arma = context.scene.objects.get(self.arma)
    if arma is None:
        return
    return [(bone.name, bone.name, "") for bone in arma.data.bones]

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

    bpy.types.Scene.custom_props = PointerProperty(type=MyProperties)
    bpy.types.Scene.arma = bpy.props.EnumProperty(items=arma_items, update=arma_upd)
    bpy.types.Scene.bone = bpy.props.EnumProperty(items=bone_items)
    bpy.types.Scene.arma_coll  = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.arma_name = bpy.props.StringProperty()
    bpy.types.Scene.bone_name = bpy.props.StringProperty()

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
