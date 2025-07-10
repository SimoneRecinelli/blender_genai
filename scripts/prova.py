import fitz

pdf_path = "/Users/diegosantarelli/Library/Application Support/Blender/4.4/scripts/addons/blender_genai/Blender_doc.pdf"
doc = fitz.open(pdf_path)

print(doc[0].get_text())
