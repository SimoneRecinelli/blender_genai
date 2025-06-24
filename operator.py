import bpy
from .utils import query_llava

class GENAI_OT_AskQuestion(bpy.types.Operator):
    bl_idname = "genai.ask_question"
    bl_label = "Chiedi all'AI"

    def execute(self, context):
        risposta = query_llava("Come faccio un bevel in Blender?")
        self.report({'INFO'}, risposta[:200])  # Messaggio breve
        return {'FINISHED'}

def register():
    bpy.utils.register_class(GENAI_OT_AskQuestion)

def unregister():
    bpy.utils.unregister_class(GENAI_OT_AskQuestion)
