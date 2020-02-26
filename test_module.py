import bpy

class TEST_MODULE(bpy.types.Operator) :
    bl_idname = "view3d.connect_arduino"
    bl_label = "Connect ATS Module"
    bl_name = "ATS Linker"
    bl_description = "Connect with the ATS hardware module"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
        return {'FINISHED'}