bl_info = {
    "name": "Voxelize",
    "author": "Jonathan Lampel",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Object",
    "description": "Converts any object into a voxel mesh",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}


import bpy
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    PropertyGroup,
)
from bpy.props import (IntProperty)

class OBJECT_OT_voxelize(Operator):
    bl_label = "Voxelize"
    bl_idname = "object.voxelize"
    bl_description = "Converts any object into a voxel mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}
    
    voxelizeResolution: bpy.props.IntProperty(
        name = "Voxel Resolution",
        default = 6,
        min = 1,
        max = 15,
        description = "Octree Depth used in the Remesh Modifier",
    )
    
    @classmethod
    def poll(cls, context):
        return context.object.select_get() and context.object.type == 'MESH' or context.object.type == 'CURVE'
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        #set source and create target
        sourceName = bpy.context.object.name
        source = bpy.data.objects[sourceName]

        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = sourceName + "_Voxelized"
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        bpy.ops.object.convert(target='MESH')

        source.hide_render = True
        source.hide_viewport = True


        targetName = bpy.context.object.name
        target = bpy.data.objects[targetName]

        #turn the target object into blocks
        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].mode = 'BLOCKS'
        bpy.context.object.modifiers["Remesh"].octree_depth = self.voxelizeResolution
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.ops.object.modifier_apply(modifier="Remesh")

        #transfer UV's to target
        bpy.ops.object.modifier_add(type='DATA_TRANSFER')
        bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
        bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}
        bpy.context.object.modifiers["DataTransfer"].loop_mapping = 'POLYINTERP_NEAREST'
        bpy.context.object.modifiers["DataTransfer"].object = source
        bpy.ops.object.datalayout_transfer(modifier="DataTransfer")
        bpy.ops.object.modifier_apply(modifier="DataTransfer")

        #reduce faces to single color
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.area.ui_type = 'UV'
        bpy.context.scene.tool_settings.use_uv_select_sync = False
        bpy.context.space_data.uv_editor.sticky_select_mode = 'DISABLED'
        bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
        bpy.context.space_data.pivot_point = 'INDIVIDUAL_ORIGINS'

        count = 0
        while count < 100:
            bpy.ops.mesh.select_random(ratio = (count+1)/100, seed = count)
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.transform.resize(value=(0.001, 0.001, 0.001))
            bpy.ops.mesh.hide(unselected=False)
            count +=1 
            
        #return to previous context
        bpy.context.area.ui_type = 'VIEW_3D'
        bpy.ops.mesh.reveal()
        bpy.ops.object.editmode_toggle()
        
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_voxelize.bl_idname)
    
def register():
    bpy.utils.register_class(OBJECT_OT_voxelize)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_voxelize)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    
if __name__ == "__main__":
    register()
    