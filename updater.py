from ATS_Rotations import *
from ATS_Rotations import Quaternion
from ATS_Rotations import QuaternionCalibrationModel
from ATS_Rotations import SensorCalibration
from preset_manager import PresetManager
import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty)
import sys, threading, time
import math
import socket
import json

calibrate = False
streaming = False
calib_started = False
animating = False
last_quat = None
anim_frame = 0
last_anim_frame = 0
calibration_count = 0
calibration_samples = 100

PRESETS = PresetManager()

preset_dict = PRESETS.load_user_presets() or None

sensor_calibration = SensorCalibration()

def get_enums(self, context):
    global PRESETS
    return PRESETS.get_enums()

## TODO : Multisensor support
def preset_changed(self, context):
    global PRESETS
    selected_preset = str(context.scene.custom_props.enum_presets)

    X = "X"
    Y = "Y"
    Z = "Z"

    if selected_preset != "None":
        preset = PRESETS.get_preset_name(selected_preset)

        X = str(preset['X'])
        Y = str(preset['Y'])
        Z = str(preset['Z'])

        bpy.context.scene.custom_props.enum_axis_x = X
        bpy.context.scene.custom_props.enum_axis_y = Y
        bpy.context.scene.custom_props.enum_axis_z = Z
    
        bpy.context.scene.custom_props.axis_x_invert = bool(preset["Xinverted"])
        bpy.context.scene.custom_props.axis_y_invert = bool(preset["Yinverted"])
        bpy.context.scene.custom_props.axis_z_invert = bool(preset["Zinverted"])
            
        bpy.context.scene.custom_props.axis_x_lock = bool(preset["Xlocked"])
        bpy.context.scene.custom_props.axis_y_lock = bool(preset["Ylocked"])
        bpy.context.scene.custom_props.axis_z_lock = bool(preset["Zlocked"])

    else:
        bpy.context.scene.custom_props.enum_axis_x = X
        bpy.context.scene.custom_props.enum_axis_y = Y
        bpy.context.scene.custom_props.enum_axis_z = Z
        bpy.context.scene.custom_props.axis_x_invert = False
        bpy.context.scene.custom_props.axis_y_invert = False
        bpy.context.scene.custom_props.axis_z_invert = False
        bpy.context.scene.custom_props.axis_x_lock = False
        bpy.context.scene.custom_props.axis_y_lock = False
        bpy.context.scene.custom_props.axis_z_lock = False

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

    frame_start: IntProperty(
        name="Animation Frame Start",
        description = "Set animation frame start",
        default=0,
        min=0
    )

    frame_end: IntProperty(
        name="Animation Frame End",
        description = "Set animation frame end (0 for no end)",
        default=0,
        min=0
    )

    replace_current_keyframes: BoolProperty(
        name = "Replace Keyframes",
        description = "If set to true, all keyframes will be deleted",
        default=True
    )

    start_in_last_keyframe: BoolProperty(
        name = "Start in Last Keyframe",
        description = "If set to true, the animation will start at the last keyframe.",
        default=False,
    )
        
    enum_axis_x: EnumProperty(
        name = "X Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("X", "X", "Set default"),
            ("Y", "Y", "Switch X to Y Axis"),     
            ("Z", "Z", "Switch X to Z Axis"),                 
        ],
        default="X"
    )

    enum_axis_y: EnumProperty(
        name = "Y Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("X", "X", "Switch Y to Z Axis"),
            ("Y", "Y", "Set default"),     
            ("Z", "Z", "Switch Y to Z Axis"),                 
        ],
        default="Y"
    )

    enum_axis_z: EnumProperty(
        name = "Z Axis Tweaks",
        description = "Change Axis Direction",
        items = [
            ("X", "X", "Switch Z to X Axis"),
            ("Y", "Y", "Switch Z to Y Axis"),     
            ("Z", "Z", "Set default"),                 
        ],
        default="Z"
    )
    
    axis_x_lock: BoolProperty(
        name = "Lock/Unlock X Axis",
        description = "Lock/Unlock X Axis",
        default=False
    )
    
    axis_y_lock: BoolProperty(
        name = "Lock/Unlock Y Axis",
        description = "Lock/Unlock Y Axis",
        default=False
    )
  
    axis_z_lock: BoolProperty(
        name = "Lock/Unlock Z Axis",
        description = "Lock/Unlock Z Axis",
        default=False
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

    enum_presets: EnumProperty(
        name = "Axis Presets",
        description = "Change Axis Preset",
        items = get_enums,
        default=None,
        update=preset_changed
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
    global last_anim_frame
    global calibration_count
    global streaming
    global last_quat
    global animating
    
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
        data, addr = serverSock.recvfrom(BUFFER_SIZE)
        data = json.loads(data.decode('utf-8'))
        
        w = float(data["qW"])
        x = float(data["qX"])
        y = float(data["qY"])
        z = float(data["qZ"])
    
        #print(type(bpy.context.scene.custom_props.enum_axis_x))
        
        if bpy.context.scene.custom_props.enum_axis_x == 'X':
            x = float(data["qX"])
        elif bpy.context.scene.custom_props.enum_axis_x == 'Y':
            x = float(data["qY"])
        else:
            x = float(data["qZ"])
            
        if bpy.context.scene.custom_props.enum_axis_y == 'X':
            y = float(data["qX"])
        elif bpy.context.scene.custom_props.enum_axis_y == 'Y':
            y = float(data["qY"])
        else:
            y = float(data["qZ"])
            
        if bpy.context.scene.custom_props.enum_axis_z == 'X':
            z = float(data["qX"])
        elif bpy.context.scene.custom_props.enum_axis_z == 'Y':
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
       
        pbone.rotation_mode = 'QUATERNION'

        q = Quaternion('GyroSensor00', qX=x, qY=y, qZ=z, qW=w)
        sensor_calibration.push(q)

        gyroQuaternionInverse = q.inverse()

        gyroQuaternionCalibrationResult = sensor_calibration.get_calib_result('GyroSensor00')

        if gyroQuaternionCalibrationResult != None:
            gyroQuaternion = quat_multiply(gyroQuaternionInverse, gyroQuaternionCalibrationResult)

            MESSAGE = gyroQuaternion.toJSON().encode()
            serverSock.sendto(MESSAGE, ("192.168.1.47", 8855))

            quat = (gyroQuaternion.qW, gyroQuaternion.qX, gyroQuaternion.qY, gyroQuaternion.qZ)
            
            # interpolate with last quaternion
            if last_quat != None:
                new_quat = interpolate_angles(last_quat, gyroQuaternion, amount=0.5)
                
                quat = (new_quat.qW, new_quat.qX, new_quat.qY, new_quat.qZ)
                
                pbone.rotation_quaternion = quat
            else:
                pbone.rotation_quaternion = quat
                
            last_quat = gyroQuaternion
        if animating and bpy.context.scene.custom_props.frame_end == 0:
            #insert a keyframe
            pbone.keyframe_insert(data_path="rotation_quaternion", frame=anim_frame)
            last_anim_frame = anim_frame
            anim_frame += 1
            if bpy.context.scene.custom_props.start_in_last_keyframe:
                bpy.context.scene.custom_props.frame_start = anim_frame
        elif animating and anim_frame <= bpy.context.scene.custom_props.frame_end:
            #insert a keyframe
            pbone.keyframe_insert(data_path="rotation_quaternion", frame=anim_frame)
            last_anim_frame = anim_frame
            anim_frame += 1
            if bpy.context.scene.custom_props.start_in_last_keyframe:
                bpy.context.scene.custom_props.frame_start = anim_frame
        else:
            animating = False

        time.sleep(0.001) #update rate in seconds

thread = None


class SimpleOperator(Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        global animating
        global streaming

        if streaming and bpy.context.screen.is_animation_playing:
            animating = False
            thread.kill() 
            thread.join() 
            if not thread.isAlive(): 
                print('animation playing, thread killed') 
                anim_frame = 1

        return not calibrate and not animating and not bpy.context.screen.is_animation_playing
        
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


class AnimateOperator(Operator):
    bl_idname = "object.animate"
    bl_label = "Animate Model"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        global streaming
        return not calibrate and streaming
    
    def execute(self, context):
        global animating
        global anim_frame

        if not bpy.context.scene.custom_props.start_in_last_keyframe:
            anim_frame =  bpy.context.scene.custom_props.frame_start

        try:
            if not animating and bpy.context.scene.custom_props.replace_current_keyframes:
                bpy.context.active_object.animation_data_clear()
        except Exception as e:
            print('Failed: '+ str(e))

        animating = not animating

        #self.report({'INFO'}, "Calibration has started, please wait.")
        return {'FINISHED'}


class SavePreset(Operator):
    bl_idname = "object.save_preset"
    bl_label = "Save Current Preset For The Selected Bone"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        return not calibrate
    
    def execute(self, context):
        global PRESETS
        global presets_enum

        sel_bone = bpy.context.active_pose_bone.name

        preset = {
            "name" : sel_bone,

            "X" : bpy.context.scene.custom_props.enum_axis_x,
            "Xinverted" : bpy.context.scene.custom_props.axis_x_invert,
            "Xlocked" : bpy.context.scene.custom_props.axis_x_lock,

            "Y" : bpy.context.scene.custom_props.enum_axis_y,
            "Yinverted" : bpy.context.scene.custom_props.axis_y_invert,
            "Ylocked" : bpy.context.scene.custom_props.axis_y_lock,

            "Z" : bpy.context.scene.custom_props.enum_axis_z,
            "Zinverted" : bpy.context.scene.custom_props.axis_z_invert,
            "Zlocked" : bpy.context.scene.custom_props.axis_z_lock
        }

        PRESETS.add_preset(preset)

        bpy.context.scene.custom_props.enum_presets = sel_bone

        return {'FINISHED'}

class RemovePreset(Operator):
    bl_idname = "object.remove_preset"
    bl_label = "Remove Current Preset"
    
    @classmethod
    def poll(cls, context):
        global calibrate
        selected_preset = str(context.scene.custom_props.enum_presets)
        return not calibrate and selected_preset != 'None' and selected_preset != ''
    
    def execute(self, context):
        global PRESETS
        global presets_enum

        selected_preset = str(context.scene.custom_props.enum_presets)
        PRESETS.remove_preset(selected_preset)

        bpy.context.scene.custom_props.enum_presets = 'None'

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
         
        if calibrate:
           layout.enabled = False 
        else:
            layout.enabled = True 

        if animating:
            icon_anim = "PAUSE"
            text_anim = "Stop Animation"
        else:
            icon_anim = "PLAY"
            text_anim = "Start Animation"
         
        box = layout.box()
        box.label(text="General")
        col = box.column()
        col.operator(SimpleOperator.bl_idname, text=text, icon=icon)
        col.prop(customprops, "calibration_samples", text="Calib. Samples")
        col.operator(CalibrateOperator.bl_idname, text="Calibrate", icon="SNAP_FACE_CENTER")
        col.separator()
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

        col.separator()

        row = col.row(align=True)
        row.prop(customprops, "enum_presets")
        row.operator(SavePreset.bl_idname, text="", icon='FILE')
        row.operator(RemovePreset.bl_idname, text="", icon='CANCEL')
        
        
        box = layout.box()
        col = box.column()
        col.label(text="Animation")
        col.operator(AnimateOperator.bl_idname, text=text_anim, icon=icon_anim)
        
        col.separator()

        row = col.row(align=True)
        row.prop(customprops, "frame_start", text="Start", expand=False, slider=False)
        row.prop(customprops, "frame_end", text="End", expand=False, slider=False)
        
        col.separator()

        col.prop(customprops, "start_in_last_keyframe", expand=True)
        col.prop(customprops, "replace_current_keyframes", expand=False)

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
    AnimateOperator,
    SavePreset,
    RemovePreset,
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