import bpy

class MAIN_UI_PANEL(bpy.types.Panel):
    bl_idname = "Test_PT_Panel"
    bl_label = "Nicolini ATS Addon"
    bl_category = "ATS Link"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("view3d.connect_arduino", text="Nicolini Time")
        layout.operator("view3d.setup_rig", text="Setup Rigged Model")
        layout.operator("view3d.auto_keyframe", text="Auto Keyframes")
