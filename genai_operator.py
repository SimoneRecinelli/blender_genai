import bpy
import os
from .utils import query_ollama_with_docs, get_model_context, costruisci_blender_docs

class GENAI_OT_BuildDocs(bpy.types.Operator):
    bl_idname = "genai.build_docs"
    bl_label = "Genera documento Blender RAG"
    bl_description = "Estrae il contenuto della documentazione HTML di Blender per l'AI"

    def execute(self, context):
        try:
            # Cartella contenente i file HTML della documentazione
            cartella_docs = "/Users/andreamarini/Desktop/blender_genai/blender_manual_v440_en.html"

            # File di output salvato fuori dalla cartella HTML
            output_txt = "/Users/andreamarini/Desktop/blender_genai/blender_docs.txt"

            costruisci_blender_docs(cartella_docs, output_txt)
            self.report({'INFO'}, f"Documentazione salvata in: {output_txt}")
        except Exception as e:
            self.report({'ERROR'}, f"Errore nella generazione: {e}")
        return {'FINISHED'}


class GENAI_OT_AskOperator(bpy.types.Operator):
    bl_idname = "genai.ask_operator"
    bl_label = "Chiedi a GenAI"

    def execute(self, context):
        props = context.scene.genai_props
        question = props.genai_question

        path_to_docs = "/Users/andreamarini/Desktop/blender_genai/blender_docs.txt"

        response = query_ollama_with_docs(question, path_to_docs)
        props.genai_response_text = response

        # Scrive nel Text Editor interno
        if "RispostaGenAI" not in bpy.data.texts:
            text_block = bpy.data.texts.new("RispostaGenAI")
        else:
            text_block = bpy.data.texts["RispostaGenAI"]
        text_block.clear()
        text_block.write(response)

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


# Registrazione classi
classes = [GENAI_OT_BuildDocs, GENAI_OT_AskOperator, GENAI_OT_ShowFullResponse]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
