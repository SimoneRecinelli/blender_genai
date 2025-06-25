import bpy
from .utils import query_ollama, get_model_context

class GENAI_OT_AskOperator(bpy.types.Operator):
    bl_idname = "genai.ask_operator"
    bl_label = "Chiedi a GenAI"

    def execute(self, context):
        props = context.scene.genai_props  # <- usa il PropertyGroup

        question = props.genai_question
        model_context = get_model_context()

        full_prompt = f"Sto lavorando su questo modello in Blender:\n{model_context}\n\nDomanda: {question}"
        response = query_ollama(full_prompt)

        props.genai_response_text = response

        # Scrive anche in un datablock testuale interno
        if "RispostaGenAI" not in bpy.data.texts:
            text_block = bpy.data.texts.new("RispostaGenAI")
        else:
            text_block = bpy.data.texts["RispostaGenAI"]
        text_block.clear()
        text_block.write(response)

        print("\n[DEBUG] Prompt:\n", full_prompt)
        print("[DEBUG] Risposta:\n", response)

        self.report({'INFO'}, "Risposta aggiornata e salvata nel Text Editor.")
        return {'FINISHED'}


class GENAI_OT_ShowFullResponse(bpy.types.Operator):
    bl_idname = "genai.show_full_response"
    bl_label = "Risposta completa GenAI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.genai_props
        layout.label(text="Risposta completa:")
        layout.prop(props, "genai_response_text", text="")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)


classes = [GENAI_OT_AskOperator, GENAI_OT_ShowFullResponse]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
