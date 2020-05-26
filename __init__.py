# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "ATS Linker",
    "author" : "Nicolas Cabrera Lettiere",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Motion Tracking"
}

import bpy
from bpy.types import (Panel, Operator, PropertyGroup)
from bpy.props import (FloatVectorProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty)

from . import auto_load
from . ats_operators import ConnectionManager
from . ats_operators import CalibrateOperator
from . ats_operators import AnimateOperator
from . ats_operators import SavePreset
from . ats_operators import RemovePreset
from . ats_operators import ATS_Properties

from . ats_ui import ATS_Linker_Panel

auto_load.init()

classes = (
    ATS_Properties,
    ConnectionManager,
    CalibrateOperator,
    AnimateOperator,
    SavePreset,
    RemovePreset,
    ATS_Linker_Panel
)

register, unregister = bpy.utils.register_classes_factory(classes)

bpy.types.Scene.ats_props = PointerProperty(type=ATS_Properties)
bpy.types.Scene.arma = bpy.props.EnumProperty(items=arma_items, update=arma_upd)
bpy.types.Scene.bone = bpy.props.EnumProperty(items=bone_items)
bpy.types.Scene.arma_coll  = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
bpy.types.Scene.arma_name = bpy.props.StringProperty()
bpy.types.Scene.bone_name = bpy.props.StringProperty()