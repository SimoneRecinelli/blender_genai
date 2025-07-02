"""
import bpy
from .utils import query_ollama_with_docs_async

class GENAI_OT_AskOperator(bpy.types.Operator):
    bl_idname = "genai.ask_operator"
    bl_label = "Chiedi a GenAI"

    def execute(self, context):
        props = context.scene.genai_props
        question = props.genai_question.strip()

        if not question:
            self.report({'WARNING'}, "Domanda vuota.")
            return {'CANCELLED'}

        # Salva domanda in cronologia
        user_msg = props.chat_history.add()
        user_msg.sender = 'USER'
        user_msg.message = question

        # ✅ Salva gli oggetti selezionati nel main thread
        selected_objects = list(bpy.context.selected_objects)

        def callback():
            print("[DEBUG] CALLBACK ESEGUITO")
            response = props.genai_response_text

            def strip_thinking_blocks(text):
                if "Thinking..." in text and "...done thinking." in text:
                    start = text.find("Thinking...")
                    end = text.find("...done thinking.") + len("...done thinking.")
                    return (text[:start] + text[end:]).strip()
                return text

            response = strip_thinking_blocks(response)

            # Aggiorna TextBlock
            if "MessaggioCompletoGenAI.txt" not in bpy.data.texts:
                text_block = bpy.data.texts.new("MessaggioCompletoGenAI.txt")
            else:
                text_block = bpy.data.texts["MessaggioCompletoGenAI.txt"]

            text_block.clear()
            text_block.write(response)

            # Aggiunge risposta alla chat
            ai_msg = props.chat_history.add()
            ai_msg.sender = 'AI'
            ai_msg.message = response

            # Reset domande/risposte
            props.genai_response = response
            props.genai_question = ""

            # ✅ Chiudi Text Editor se aperto e torna alla vista 3D
            for area in bpy.context.screen.areas:
                if area.type == 'TEXT_EDITOR':
                    area.type = 'VIEW_3D'

            # ✅ Messaggio di stato (evita self.report in thread secondari)
            props.genai_status = "Risposta aggiornata."

        # ✅ Passa anche gli oggetti selezionati
        query_ollama_with_docs_async(question, props, selected_objects, update_callback=callback)

        return {'FINISHED'}
    

class GENAI_OT_LoadImage(bpy.types.Operator):
    bl_idname = "genai.load_image"
    bl_label = "Carica un'immagine"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        props = context.scene.genai_props
        props.genai_image_path = self.filepath  # salva il path nell'oggetto scene
        self.report({'INFO'}, f"Immagine caricata: {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



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

        
"""


import bpy
from .utils import query_ollama_with_docs_async
import os


class GENAI_OT_AskOperator(bpy.types.Operator):
    bl_idname = "genai.ask_operator"
    bl_label = "Chiedi a GenAI"

    def execute(self, context):
        props = context.scene.genai_props
        question = props.genai_question.strip()

        if not question:
            self.report({'WARNING'}, "Domanda vuota.")
            return {'CANCELLED'}

        user_msg = props.chat_history.add()
        user_msg.sender = 'USER'
        user_msg.message = question

        selected_objects = list(bpy.context.selected_objects)

        def callback():
            response = props.genai_response_text

            def strip_thinking_blocks(text):
                if "Thinking..." in text and "...done thinking." in text:
                    start = text.find("Thinking...")
                    end = text.find("...done thinking.") + len("...done thinking.")
                    return (text[:start] + text[end:]).strip()
                return text

            response = strip_thinking_blocks(response)

            if "MessaggioCompletoGenAI.txt" not in bpy.data.texts:
                text_block = bpy.data.texts.new("MessaggioCompletoGenAI.txt")
            else:
                text_block = bpy.data.texts["MessaggioCompletoGenAI.txt"]

            text_block.clear()
            text_block.write(response)

            ai_msg = props.chat_history.add()
            ai_msg.sender = 'AI'
            ai_msg.message = response

            props.genai_response = response
            props.genai_question = ""

        query_ollama_with_docs_async(question, props, selected_objects, update_callback=callback)

        return {'FINISHED'}

class GENAI_OT_LoadImage(bpy.types.Operator):
    bl_idname = "genai.load_image"
    bl_label = "Carica un'immagine"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        props = context.scene.genai_props
        props.genai_image_path = self.filepath

        # Mostra conferma visiva e aggiorna stato nell'UI (opzionale)
        self.report({'INFO'}, f"✅ Immagine caricata correttamente.")
        props.genai_status = f"Immagine caricata: {os.path.basename(self.filepath)}"
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



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

classes = [GENAI_OT_AskOperator, GENAI_OT_LoadImage, GENAI_OT_ShowFullResponse]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
