import bpy    

class OBJECT_PT_HelloWorldPanel(bpy.types.Panel):
    bl_label = "Simple Custom Menu2"
    bl_idname = "OBJECT_MT_simple_custom_menus"
    bl_category = "ATS Linker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "mychosenObject")

def scene_mychosenobject_poll(self, object):
    return object.type == 'ARMATURE'

def register():
    bpy.types.Scene.mychosenObject = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=scene_mychosenobject_poll
    )


def unregister():
    del bpy.types.Scene.mychosenObject


if __name__ == "__main__":
    register()