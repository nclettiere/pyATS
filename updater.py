import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty)
import sys, threading, time
import socket
import json

calibrate = False
streaming = False
calibration_samples = 100

def update_rot(self, context):
    global val
    bpy.context.active_object.rotation_mode = 'QUATERNION'
    bpy.context.active_object.rotation_quaternion  = val

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
        update=update_rot,
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
        name = "Lock/Unlock X Axis Stream",
        description = "Lock/Unlock X Axis Stream",
        default=False,
        update=lock_x_changed
    )
    
    axis_y_lock: BoolProperty(
        name = "Lock/Unlock Y Axis Stream",
        description = "Lock/Unlock Y Axis Stream",
        default=False,
        update=lock_y_changed
    )
  
    axis_z_lock: BoolProperty(
        name = "Lock/Unlock Z Axis Stream",
        description = "Lock/Unlock Z Axis Stream",
        default=False,
        update=lock_z_changed
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
  
  
def thread_update():
    UDP_IP_ADDRESS = "0.0.0.0"
    UDP_PORT_NO = 7755
    BUFFER_SIZE = 1024

    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    
    scene = bpy.context.scene
    last_rotation_quat = scene.objects[0].rotation_quaternion
    
    while(True):
        global calibrate
        if calibrate:
            print('Calibration signal detected')
            calibrate = False
        else:
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
            #update_rot(self, context)
            scene.objects[0].rotation_mode = 'QUATERNION'
            scene.objects[0].rotation_quaternion  = rotation_quat
            #scene.objects[0].transform.rotate(value=float(z), orient_axis='Z')
            
            time.sleep(0.001) #update rate in seconds
            

thread = None

class SimpleOperator(Operator):
    """Print object name in Console"""
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
        
    def execute(self, context):
        global streaming
        global thread
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
    bl_idname = "object.ats_panel"
    bl_label = "ATS"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "ATS Linker"
    bl_context = "objectmode"  

    def draw(self, context):
        scene = context.scene
        ob = context.object
        layout = self.layout
        customprops = scene.custom_props
        
        global streaming
        text="Start Stream"
        icon="TRIA_RIGHT"
        if streaming:
            text="Stop Stream"
            icon="PAUSE"
        else:
            text="Start Stream"
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
            
        box = layout.box()
        box.label(text="General")
        col = box.column()
        col.operator(SimpleOperator.bl_idname, text=text, icon=icon)
        col.prop(customprops, "calibration_samples", text="Calib. Samples")
        col.operator(CalibrateOperator.bl_idname, text="Calibrate", icon="SNAP_FACE_CENTER")
        
        box = layout.box()
        col = box.column()
        col.label(text="Axis Tweaks")
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_x", text="X is")
        row.prop(customprops, "axis_x_lock", text=text_lock_x, icon=icon_lock_x)
        
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_y", text="Y is")
        row.prop(customprops, "axis_y_lock", text=text_lock_y, icon=icon_lock_y)
        
        row = col.row(align=True)
        row.prop(customprops, "enum_axis_z", text="Z is")
        row.prop(customprops, "axis_z_lock", text=text_lock_z, icon=icon_lock_z)

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

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
