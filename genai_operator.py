import bpy
from .utils import query_ollama_with_docs_async
from . import server
import os
import sys
import subprocess
import platform

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

        selected_objects = bpy.context.selected_objects.copy()

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

        # Messaggio nel pannello
        props.genai_status = f"Immagine caricata: {os.path.basename(self.filepath)}"

        # Funzione di reset
        def clear_status():
            props.genai_status = ""
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
            return None

        bpy.app.timers.register(clear_status, first_interval=10.0)

        self.report({'INFO'}, "Immagine caricata correttamente.")
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


class GENAI_OT_ShowExternalChat(bpy.types.Operator):
    bl_idname = "genai.show_external_chat"
    bl_label = "Apri Chat Esterna"

    def execute(self, context):
        try:
            from . import gui_launcher

            # Se la GUI è già attiva, manda un messaggio per portarsi in primo piano
            if gui_launcher.bring_window_to_front():
                self.report({'INFO'}, "🔁 Chat già attiva — riportata in primo piano.")
                return {'FINISHED'}

            # Altrimenti lanciamo la GUI come processo separato e indipendente
            script_path = os.path.join(os.path.dirname(__file__), "extern_gui.py")
            python_exe = sys.executable

            kwargs = {
                "args": [python_exe, script_path],
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }

            system = platform.system()
            if system == "Windows":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:  # macOS e Linux
                kwargs["start_new_session"] = True

            subprocess.Popen(**kwargs)

            self.report({'INFO'}, "✅ Chat esterna avviata.")
        except Exception as e:
            self.report({'ERROR'}, f"Errore apertura chat: {str(e)}")
        return {'FINISHED'}


classes = [
    GENAI_OT_AskOperator,
    GENAI_OT_LoadImage,
    GENAI_OT_ShowFullResponse,
    GENAI_OT_ShowExternalChat
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
