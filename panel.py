"""
import bpy

class GenAIProperties(bpy.types.PropertyGroup):
    genai_question: bpy.props.StringProperty(
        name="Domanda AI",
        default=""
    )

    genai_response_text: bpy.props.StringProperty(
        name="Risposta AI",
        default=""
    )


class GENAI_PT_Panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.genai_props

        layout.prop(props, "genai_question", text="Domanda")
        layout.operator("genai.ask_operator", text="Chiedi a GenAI")

        layout.separator()
        layout.label(text="Risposta AI:")
        layout.prop(props, "genai_response_text", text="")

        layout.separator()
        layout.operator("genai.show_full_response", text="Apri risposta estesa")

classes = [GenAIProperties, GENAI_PT_Panel]

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"[WARNING] Classe già registrata: {cls.__name__}")

    if not hasattr(bpy.types.Scene, "genai_props"):
        bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            print(f"[WARNING] Impossibile deregistrare: {cls.__name__}")

    if hasattr(bpy.types.Scene, "genai_props"):
        del bpy.types.Scene.genai_props
"""

import bpy

class GenAIProperties(bpy.types.PropertyGroup):
    genai_question: bpy.props.StringProperty(
        name="Domanda AI",
        default=""
    )

    genai_response_text: bpy.props.StringProperty(
        name="Risposta AI",
        default=""
    )

class GENAI_PT_Panel(bpy.types.Panel):
    bl_label = "GenAI Assistant"
    bl_idname = "GENAI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GenAI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.genai_props

        layout.prop(props, "genai_question", text="Domanda")
        layout.operator("genai.ask_operator", text="Chiedi a GenAI")

        layout.separator()
        layout.label(text="Risposta AI:")
        # Visualizzazione multilinea con `text=""` (trucco per più righe)
        layout.prop(props, "genai_response_text", text="")

        layout.separator()
        layout.operator("genai.show_full_response", text="Apri risposta estesa")

classes = [GenAIProperties, GENAI_PT_Panel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.genai_props = bpy.props.PointerProperty(type=GenAIProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.genai_props
