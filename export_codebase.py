import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT_DIR = os.path.abspath("src")  # Change this to your code root
OUTPUT_FILE = "codebase_export.pdf"
EXCLUDE_DIRS = {'__pycache__', 'venv', 'rasa_env', '.git', 'node_modules'}

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=10)
pdf.set_font("Courier", size=8)  # Monospaced font, smaller size

def add_code_to_pdf(file_path):
    pdf.add_page()
    pdf.set_font("Courier", style='B', size=10)
    pdf.cell(0, 10, f"File: {os.path.relpath(file_path, ROOT_DIR)}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Courier", size=8)
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            try:
                pdf.multi_cell(0, 4, line.rstrip('\n'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            except Exception:
                pdf.multi_cell(0, 4, "[LINE TOO LONG TO DISPLAY]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Walk through files and add to PDF
for foldername, subfolders, filenames in os.walk(ROOT_DIR):
    # Skip excluded directories
    if any(excluded in foldername for excluded in EXCLUDE_DIRS):
        continue
    for filename in filenames:
        if filename.endswith(".py") or filename.endswith(".yml"):  # Only include .py and .yml files
            full_path = os.path.join(foldername, filename)
            add_code_to_pdf(full_path)

pdf.output(OUTPUT_FILE)
print(f"\n✅ Codebase exported to: {OUTPUT_FILE}")
