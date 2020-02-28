import bpy
from bpy.props import StringProperty
import os.path
from os import path
import subprocess
import threading

rigName = ""

class ATS_Setup_Operator(bpy.types.Operator):
    bl_label = "ATS Configuration"
    bl_idname = "wm.ats_setup"
    bl_description = "Open ATS Link Configuration Panel"

    #@classmethod
    #def poll(cls, context):
    #    return path.exists("C:\\ATS_CONFIG\\cached\\ats_interface_configuration.dat")

    def execute(self, context):
        ats_config = OPEN_ATS_CONFIG()
        ats_config.start()
        ats_config.join()
        print(ats_config.stdout)

        self.report({'INFO'}, "Simple Operator executed.")

        return {'FINISHED'}

class BasicMenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_select_test"
    bl_label = "Select Module Port"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_all", text="COM 1")
        layout.operator("object.select_all", text="COM 2")
        layout.operator("object.select_random", text="WIFI 192.168.1.31")

class SimpleCustomMenu(bpy.types.Panel):
    bl_label = "Simple Custom Menu"
    bl_idname = "OBJECT_MT_simple_custom_menu"
    bl_category = "ATS Link"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        print('hello')

        layout.label(text="Open ATS Configuration", icon='ARROW_LEFTRIGHT')
        layout.operator("wm.ats_setup")
        layout.menu("OBJECT_MT_select_test", text="Select Module Port")
        layout.separator()
        layout.label(text="Setup Rig", icon='INFO')
        layout.prop(scene, "Rig", text="Select Rig")
        layout.operator("view3d.setup_rig")
        layout.separator()
        layout.label(text="Create New Animation", icon='DISCLOSURE_TRI_RIGHT')
        layout.operator("view3d.setup_rig", text="Start Animation")
        layout.operator("view3d.setup_rig", text="Stop Animation")

class OPEN_ATS_CONFIG(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def run(self):
        p = subprocess.Popen('C:\\Users\\Bloomberg\\source\\repos\\ATS Interface\\ATS Interface\\bin\\Release\\ATS Interface.exe'.split(),
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        self.stdout, self.stderr = p.communicate()

def scene_rig_poll(self, object):
    if self.objects.get(object.name) == None:
        bpy.data.objects.remove(object)
        return False
    else:
        rigName = object.name
        return True

def register():
    bpy.types.Scene.Rig = bpy.props.PointerProperty(
        type=bpy.types.Armature,
        poll=scene_rig_poll
    )

def unregister():
    del bpy.types.Scene.Rig

if __name__ == "__main__":
    register()