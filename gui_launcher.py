import sys
import os

# Aggiunge il path del modulo Blender GenAI
sys.path.append(os.path.dirname(__file__))

from esterna_gui import avvia_gui_esternamente

if __name__ == "__main__":
    avvia_gui_esternamente()
