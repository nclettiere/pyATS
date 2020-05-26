import bpy

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
        customprops = scene.ats_props
        
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
        
        if bpy.context.scene.ats_props.axis_x_lock == True:
            icon_lock_x = "LOCKED"
            text_lock_x = "Locked"
        else:
            icon_lock_x = "UNLOCKED"
            text_lock_x = "Unlocked"
            
        if bpy.context.scene.ats_props.axis_y_lock == True:
            icon_lock_y = "LOCKED"
            text_lock_y = "Locked"
        else:
            icon_lock_y = "UNLOCKED"
            text_lock_y = "Unlocked"
            
        if bpy.context.scene.ats_props.axis_z_lock == True:
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