import bpy
from .utils import query_ollama_with_docs, get_model_context

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

        response = query_ollama_with_docs(question, props=props)

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
