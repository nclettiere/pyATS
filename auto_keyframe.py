import bpy
import mathutils
import subprocess
import threading
import time
                    
class AUTO_KEYFRAME(bpy.types.Operator) :
    bl_idname = "view3d.auto_keyframe"
    bl_label = "Auto Keyframes"
    bl_name = "Auto Keyframe"
    bl_description = "Start recording an animation"

    def execute(self, context):
        myclass = MyClass()
        myclass.start()
        myclass.join()
        print(myclass.stdout)

        return {'FINISHED'}
    
    def call_interface():
        print('executed!')
        #popen = subprocess.Popen(['C:\\Users\\Bloomberg\\Desktop\\ATS\\ATS Interface\\bin\\Release\\ATS Interface.exe'], stdout=subprocess.PIPE, universal_newlines=True)
        #for stdout_line in iter(popen.stdout.readline, ""):
        #    yield stdout_line 
        #popen.stdout.close()
        #return_code = popen.wait()
        #if return_code:
        #    raise subprocess.CalledProcessError(return_code, cmd)
        
        

class MyClass(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def run(self):
        p = subprocess.Popen('C:\\Users\\Bloomberg\\Desktop\\ATS\\ATS Interface\\bin\\Release\\ATS Interface.exe'.split(),
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        self.stdout, self.stderr = p.communicate()
