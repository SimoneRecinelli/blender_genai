import bpy

class GENAI_PT_Panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "genai_question")
        layout.operator("genai.ask_operator", text="Chiedi a GenAI")
        
        layout.separator()
        layout.label(text="Risposta AI:")
        layout.label(text=context.scene.genai_response)  # mostro la risposta come testo non editabile


def register():
    bpy.utils.register_class(GENAI_PT_Panel)
    bpy.types.Scene.genai_question = bpy.props.StringProperty(name="Domanda AI", default="")
    bpy.types.Scene.genai_response = bpy.props.StringProperty(name="Risposta AI", default="")  # <-- serve questa

def unregister():
    bpy.utils.unregister_class(GENAI_PT_Panel)
    del bpy.types.Scene.genai_question
    del bpy.types.Scene.genai_response  # <-- e questa


