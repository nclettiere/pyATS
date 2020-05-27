import bpy
import sys, threading, time
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty)

try:
    from . ats_preset_manager import PresetManager
    from . ats_sdk import ATS_SDK
    from . ats_solver import SensorCalibration
    from . ats_solver import QuatSolver
except:
    from ats_preset_manager import PresetManager
    from ats_sdk import ATS_SDK
    from ats_solver import SensorCalibration
    from ats_solver import QuatSolver

calib_started = False
animating = False
last_quat = None
anim_frame = 0
last_anim_frame = 0
calibration_count = 0
calibration_samples = 100

SDK = ATS_SDK(False)

PRESETS = PresetManager()
preset_dict = PRESETS.load_user_presets() or None
sensor_calibration = SensorCalibration()

connection_thread = None

class ConnectionManager(Operator):
    bl_idname = "object.connection_manager"
    bl_label = "Connection Manager"
    
    @classmethod
    def poll(cls, context):

        if bpy.context.scene.ats_props.streaming and bpy.context.screen.is_animation_playing:
            bpy.context.scene.ats_props.animating = False
            connection_thread.kill() 
            connection_thread.join() 
            if not connection_thread.isAlive(): 
                print('animation playing, connection_thread killed') 
                anim_frame = 1

        return not bpy.context.scene.ats_props.calibrate and not bpy.context.scene.ats_props.animating and not bpy.context.screen.is_animation_playing
        
    def execute(self, context):
        global connection_thread
        global anim_frame
        if not bpy.context.scene.ats_props.streaming:
            bpy.context.scene.ats_props.streaming = True
            connection_thread = thread_with_trace(target = thread_update) 
            connection_thread.start() 
            if connection_thread.isAlive(): 
                print('thread started')
        else:
            bpy.context.scene.ats_props.streaming = False
            connection_thread.kill() 
            connection_thread.join() 
            ## Disconnect when streaming signal is false
            disconnected = False
            while not disconnected:
                disconnected = SDK.disconnect()
                print("Disconnectiong ...")
            if not connection_thread.isAlive(): 
                print('thread killed') 
                anim_frame = 1
                
        return {'FINISHED'}

class CalibrateOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.calib_operator"
    bl_label = "Simple Object Operator"
    
    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.ats_props.calibrate
    
    def execute(self, context):
        global sensor_calibration
        #bpy.context.scene.ats_props.calibrate = True
        sensor_calibration = SensorCalibration()
        self.report({'PROPERTY'}, "Calibration has started, please wait.")
        return {'FINISHED'}


class AnimateOperator(Operator):
    bl_idname = "object.animate"
    bl_label = "Animate Model"
    
    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.ats_props.calibrate and bpy.context.scene.ats_props.streaming
    
    def execute(self, context):
        global anim_frame

        if not bpy.context.scene.ats_props.start_in_last_keyframe:
            anim_frame =  bpy.context.scene.ats_props.frame_start

        try:
            if not bpy.context.scene.ats_props.animating and bpy.context.scene.ats_props.replace_current_keyframes:
                bpy.context.active_object.animation_data_clear()
        except Exception as e:
            print('Failed: '+ str(e))

        bpy.context.scene.ats_props.animating = not bpy.context.scene.ats_props.animating

        #self.report({'INFO'}, "Calibration has started, please wait.")
        return {'FINISHED'}


class SavePreset(Operator):
    bl_idname = "object.save_preset"
    bl_label = "Save Current Preset For The Selected Bone"
    
    @classmethod
    def poll(cls, context):
        return not bpy.context.scene.ats_props.calibrate
    
    def execute(self, context):
        global PRESETS
        global presets_enum

        sel_bone = bpy.context.active_pose_bone.name

        preset = {
            "name" : sel_bone,

            "X" : bpy.context.scene.ats_props.enum_axis_x,
            "Xinverted" : bpy.context.scene.ats_props.axis_x_invert,
            "Xlocked" : bpy.context.scene.ats_props.axis_x_lock,

            "Y" : bpy.context.scene.ats_props.enum_axis_y,
            "Yinverted" : bpy.context.scene.ats_props.axis_y_invert,
            "Ylocked" : bpy.context.scene.ats_props.axis_y_lock,

            "Z" : bpy.context.scene.ats_props.enum_axis_z,
            "Zinverted" : bpy.context.scene.ats_props.axis_z_invert,
            "Zlocked" : bpy.context.scene.ats_props.axis_z_lock
        }

        PRESETS.add_preset(preset)

        bpy.context.scene.ats_props.enum_presets = sel_bone

        return {'FINISHED'}

class RemovePreset(Operator):
    bl_idname = "object.remove_preset"
    bl_label = "Remove Current Preset"
    
    @classmethod
    def poll(cls, context):
        selected_preset = str(context.scene.ats_props.enum_presets)
        return not bpy.context.scene.ats_props.calibrate and selected_preset != 'None' and selected_preset != ''
    
    def execute(self, context):
        global PRESETS
        global presets_enum

        selected_preset = str(context.scene.ats_props.enum_presets)
        PRESETS.remove_preset(selected_preset)

        bpy.context.scene.ats_props.enum_presets = 'None'

        return {'FINISHED'}


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

def thread_update():
    global calib_started
    global sensor_calibration
    global anim_frame
    global last_anim_frame
    global calibration_count
    global last_quat
    
    scene = bpy.context.scene
    
    ob = bpy.data.objects[bpy.context.scene.arma]
    pbone = ob.pose.bones["Head"]
    
    last_rotation_quat = pbone.rotation_quaternion
    
    ## Establish connection and enter the main loop

    connected = False
    while not connected:
        connected = SDK.connect()

    while(bpy.context.scene.ats_props.streaming):

        axis_settings = {
            "Name": "GyroSensor00",

            "X_Tweak": bpy.context.scene.ats_props.enum_axis_x,
            "Y_Tweak": bpy.context.scene.ats_props.enum_axis_y,
            "Z_Tweak": bpy.context.scene.ats_props.enum_axis_z,

            "X_Inversion": bpy.context.scene.ats_props.axis_x_invert,
            "Y_Inversion": bpy.context.scene.ats_props.axis_y_invert,
            "Z_Inversion": bpy.context.scene.ats_props.axis_z_invert,

            "X_Lock": bpy.context.scene.ats_props.axis_x_lock,
            "Y_Lock": bpy.context.scene.ats_props.axis_y_lock,
            "Z_Lock": bpy.context.scene.ats_props.axis_z_lock,
        }

        q = SDK.get_quaternion(axis_settings)

        if q == None:
            print("Noooone!")
            continue

        sensor_calibration.push(q)

        gyroQuaternionInverse = q.inverse()
        gyroQuaternionCalibrationResult = sensor_calibration.get_calib_result(axis_settings["Name"])

        if gyroQuaternionCalibrationResult != None:
            gyroQuaternion = QuatSolver().quat_multiply(gyroQuaternionInverse, gyroQuaternionCalibrationResult)

            #MESSAGE = gyroQuaternion.toJSON().encode()
            #serverSock.sendto(MESSAGE, ("192.168.1.47", 8855))

            quat = (gyroQuaternion.qW, gyroQuaternion.qX, gyroQuaternion.qY, gyroQuaternion.qZ)
            
            # interpolate with last quaternion
            if last_quat != None:
                new_quat = QuatSolver().interpolate_angles(last_quat, gyroQuaternion, amount=0.5)
                
                quat = (new_quat.qW, new_quat.qX, new_quat.qY, new_quat.qZ)

                pbone.rotation_mode = 'QUATERNION'
                pbone.rotation_quaternion = quat
            else:
                pbone.rotation_quaternion = quat
                
            last_quat = gyroQuaternion
        if bpy.context.scene.ats_props.animating and bpy.context.scene.ats_props.frame_end == 0:
            #insert a keyframe
            pbone.keyframe_insert(data_path="rotation_quaternion", frame=anim_frame)
            last_anim_frame = anim_frame
            anim_frame += 1
            if bpy.context.scene.ats_props.start_in_last_keyframe:
                bpy.context.scene.ats_props.frame_start = anim_frame
        elif bpy.context.scene.ats_props.animating and anim_frame <= bpy.context.scene.ats_props.frame_end:
            #insert a keyframe
            pbone.keyframe_insert(data_path="rotation_quaternion", frame=anim_frame)
            last_anim_frame = anim_frame
            anim_frame += 1
            if bpy.context.scene.ats_props.start_in_last_keyframe:
                bpy.context.scene.ats_props.frame_start = anim_frame
        else:
            bpy.context.scene.ats_props.animating = False

        time.sleep(0.001) #update rate in seconds

def get_enums(self, context):
    global PRESETS
    return PRESETS.get_enums()

## TODO : Multisensor support
def preset_changed(self, context):
    global PRESETS
    selected_preset = str(context.scene.ats_props.enum_presets)

    X = "X"
    Y = "Y"
    Z = "Z"

    if selected_preset != "None":
        preset = PRESETS.get_preset_name(selected_preset)

        X = str(preset['X'])
        Y = str(preset['Y'])
        Z = str(preset['Z'])

        bpy.context.scene.ats_props.enum_axis_x = X
        bpy.context.scene.ats_props.enum_axis_y = Y
        bpy.context.scene.ats_props.enum_axis_z = Z
    
        bpy.context.scene.ats_props.axis_x_invert = bool(preset["Xinverted"])
        bpy.context.scene.ats_props.axis_y_invert = bool(preset["Yinverted"])
        bpy.context.scene.ats_props.axis_z_invert = bool(preset["Zinverted"])
            
        bpy.context.scene.ats_props.axis_x_lock = bool(preset["Xlocked"])
        bpy.context.scene.ats_props.axis_y_lock = bool(preset["Ylocked"])
        bpy.context.scene.ats_props.axis_z_lock = bool(preset["Zlocked"])

    else:
        bpy.context.scene.ats_props.enum_axis_x = X
        bpy.context.scene.ats_props.enum_axis_y = Y
        bpy.context.scene.ats_props.enum_axis_z = Z
        bpy.context.scene.ats_props.axis_x_invert = False
        bpy.context.scene.ats_props.axis_y_invert = False
        bpy.context.scene.ats_props.axis_z_invert = False
        bpy.context.scene.ats_props.axis_x_lock = False
        bpy.context.scene.ats_props.axis_y_lock = False
        bpy.context.scene.ats_props.axis_z_lock = False

class ATS_Properties(PropertyGroup):
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

    streaming: BoolProperty(
        name = "ATS Streaming",
        description = "Get ATS isStreaming value",
        default=False
    )

    calibrate: BoolProperty(
        name = "ATS Calibrate",
        description = "Calibrate ATS System",
        default=False
    )

    animating: BoolProperty(
        name = "ATS animating",
        description = "animating ATS System",
        default=False
    )
