import bpy
import mathutils

class SETUP_RIG(bpy.types.Operator) :
    bl_idname = "view3d.setup_rig"
    bl_label = "Setup Rig"
    bl_name = "Setup Rig"
    bl_description = "Setup a rigged model to animate"

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'ARMATURE')

    def execute(self, context):
        # BONES TO MODIFY
        # root
        # head
        # hand_ik.L & hand_ik.R
        # upper_arm_ik.L & upper_arm_ik.R
        # shoulder.L & shoulder.R
        # chest
        # torso
        # hips
        # thigh_ik.L & thigh_ik.R
        # foot_ik.L & foot_ik.R

        default_bones = ["root",
                         "head", 
                         "hand_ik.L", "hand_ik.R", 
                         "upper_arm_ik.L", "upper_arm_ik.R",
                         "shoulder.L", "shoulder.R",
                         "chest", 
                         "torso",
                         "hips",
                         "thigh_ik.L", "thigh_ik.R",
                         "foot_ik.L","foot_ik.R"]

        objectType = bpy.context.object.type

        if objectType == "ARMATURE":
            ob = bpy.context.object
            armature = ob.data

            scene = bpy.context.scene

            bpy.ops.object.select_all(action='DESELECT')

            last_selected_object = ""

            # clear scene
            for empty in scene.objects:
                if empty.type == 'EMPTY' and empty.name.startswith("E_"):
                    empty.select_set(True)
                else: 
                    empty.select_set(False)

            bpy.ops.object.delete()

            # create empty objects
            bpy.ops.object.mode_set(mode='OBJECT')
            for bone in armature.bones:
                if bone.name in default_bones:
                    new_name = "E_" + bone.name
                    vector_location = [bone.head_local.x, bone.head_local.y - 2.0, bone.head_local.z]

                    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(vector_location))
                    bpy.ops.transform.resize(value=(5.0, 5.0, 5.0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                    for obj in bpy.context.selected_objects:
                        obj.name = new_name
                        obj.empty_display_size = 4
                        obj.empty_display_type = 'ARROWS'

                        # constraint to root empty
                        if new_name != "E_root":
                            bpy.ops.object.constraint_add(type='COPY_LOCATION')
                            bpy.context.object.constraints["Copy Location"].target = bpy.data.objects["E_root"]
                            bpy.context.object.constraints["Copy Location"].use_offset = True

                        obj.select_set(False)
                        last_selected_object = new_name


            # set bones contraints
            bpy.context.active_object.select_set(False)
            bpy.context.scene.objects[last_selected_object].select_set(False)
            bpy.context.scene.objects["rig"].select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.mode_set(mode='POSE')

            # try to remove old constraints
            for bone in armature.bones:
                cons = bpy.context.object.pose.bones[bone.name].constraints
                if bone != None:
                    cl = len(cons)
                if cl > 0:
                    # Remove existing constraints.
                    for c in cons:
                        if c.type == "COPY_LOCATION" or c.type == "COPY_ROTATION":
                            cons.remove(c)

            for bone in armature.bones:
                if bone.name in default_bones:
                    bpy.data.objects['rig'].data.bones.active = bone
                    bone.select = True
                    try:
                        bpy.ops.pose.constraint_add(type='COPY_LOCATION')
                        bpy.ops.pose.constraint_add(type='COPY_ROTATION')
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Location"].target = bpy.data.objects["E_"+bone.name]
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Rotation"].target = bpy.data.objects["E_"+bone.name]
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Rotation"].mix_mode = 'ADD'
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Rotation"].invert_x = True
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Rotation"].invert_y = True
                        bpy.context.object.pose.bones[bone.name].constraints["Copy Rotation"].invert_z = True

                    except:
                        print('this bone do not accept contraints')
                    bone.select = False
        else:
            self.report({'ERROR'}, 'Error, select a rigify rig to continue.')
        return {'FINISHED'}