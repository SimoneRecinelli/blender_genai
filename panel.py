import bpy

class GENAI_PT_panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        layout.operator("genai.ask_question")

def register():
    bpy.utils.register_class(GENAI_PT_panel)

def unregister():
    bpy.utils.unregister_class(GENAI_PT_panel)
