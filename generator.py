"""
BIOLOGIYA VEKTOR - HUJJAT GENERATORI (generator.py)
Matnlarni rasmiy Word (.docx) fayliga aylantirish.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_document(title: str, content: str, filename: str) -> str:
    doc = Document()

    # Sahifa chetki masofalari (A4 standarti)
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Bosh sarlavha (Header)
    header_p = doc.add_paragraph()
    header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = header_p.add_run(f"BIOLOGIYA VEKTOR | {title.upper()}\n")
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(16)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor(16, 185, 129) # Neon Green rang

    # Matnni qatorma-qator qayta ishlash
    lines = content.split('\n')
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        p = doc.add_paragraph()
        
        # Katta sarlavhalar
        if line_clean.startswith('# '):
            run = p.add_run(line_clean.replace('# ', ''))
            run.font.size = Pt(14)
            run.bold = True
            run.font.color.rgb = RGBColor(31, 41, 55)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
        
        # O'rta sarlavhalar
        elif line_clean.startswith('## '):
            run = p.add_run(line_clean.replace('## ', ''))
            run.font.size = Pt(12)
            run.bold = True
            run.font.color.rgb = RGBColor(75, 85, 99)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
        
        # Oddiy qatorlar
        else:
            run = p.add_run(line_clean)
            run.font.size = Pt(11)
            p.paragraph_format.space_after = Pt(3)

        run.font.name = 'Calibri'

    file_path = os.path.join(os.getcwd(), filename)
    doc.save(file_path)
    return file_path
