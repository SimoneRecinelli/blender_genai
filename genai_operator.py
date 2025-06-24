import bpy
from .utils import query_ollama, get_model_context

class GENAI_OT_AskOperator(bpy.types.Operator):
    bl_idname = "genai.ask_operator"
    bl_label = "Chiedi a GenAI"
    
    def execute(self, context):
        question = context.scene.genai_question
        model_context = get_model_context()

        # Costruzione del prompt
        full_prompt = f"Sto lavorando su questo modello in Blender:\n{model_context}\n\nDomanda: {question}"
        response = query_ollama(full_prompt)

        context.scene.genai_response = response
        self.report({'INFO'}, "Risposta aggiornata!")
        print("Prompt completo inviato a Ollama:\n", full_prompt)
        print("Risposta GenAI:", response)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(GENAI_OT_AskOperator)

def unregister():
    bpy.utils.unregister_class(GENAI_OT_AskOperator)

