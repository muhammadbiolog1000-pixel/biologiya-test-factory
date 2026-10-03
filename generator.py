import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

FONT_NAME = "CMU Serif"

def build_student_docx(tests: list, filepath: str):
    """O'quvchi uchun Word hujjati (Javoblarsiz)"""
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title = doc.add_paragraph()
    r = title.add_run("BIOLOGIYA — SINOV TESTLARI (O'QUVCHI UCHUN)")
    r.font.name = FONT_NAME
    r.font.size = Pt(14)
    r.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    for idx, t in enumerate(tests, 1):
        p_q = doc.add_paragraph()
        run_num = p_q.add_run(f"{idx}. ")
        run_num.font.name = FONT_NAME
        run_num.font.size = Pt(10.5)
        run_num.bold = True
        
        run_shart = p_q.add_run(t.get("shart", ""))
        run_shart.font.name = FONT_NAME
        run_shart.font.size = Pt(10.5)

        for h in t.get("hukmlar", []):
            p_h = doc.add_paragraph()
            p_h.paragraph_format.left_indent = Inches(0.2)
            rh = p_h.add_run(h)
            rh.font.name = FONT_NAME
            rh.font.size = Pt(10)

        for harf in ["A", "B", "C", "D"]:
            var_text = t.get("variantlar", {}).get(harf, "")
            if var_text:
                pv = doc.add_paragraph()
                pv.paragraph_format.left_indent = Inches(0.3)
                r_let = pv.add_run(f"{harf}) ")
                r_let.font.name = FONT_NAME
                r_let.font.size = Pt(10)
                r_let.bold = False

                r_val = pv.add_run(var_text)
                r_val.font.name = FONT_NAME
                r_val.font.size = Pt(10)
                r_val.italic = True
        doc.add_paragraph()

    doc.save(filepath)

def build_teacher_docx(tests: list, filepath: str):
    """O'qituvchi uchun to'liq tahliliy Word hujjati"""
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title = doc.add_paragraph()
    r = title.add_run("BIOLOGIYA — EKSPERTIZA VA METODIK TAHLIL (O'QITUVCHI UCHUN)")
    r.font.name = FONT_NAME
    r.font.size = Pt(14)
    r.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    for idx, t in enumerate(tests, 1):
        p_q = doc.add_paragraph()
        run_num = p_q.add_run(f"{idx}. ")
        run_num.font.name = FONT_NAME
        run_num.font.size = Pt(10.5)
        run_num.bold = True
        
        run_shart = p_q.add_run(t.get("shart", ""))
        run_shart.font.name = FONT_NAME
        run_shart.font.size = Pt(10.5)

        for h in t.get("hukmlar", []):
            p_h = doc.add_paragraph()
            p_h.paragraph_format.left_indent = Inches(0.2)
            rh = p_h.add_run(h)
            rh.font.name = FONT_NAME
            rh.font.size = Pt(10)

        for harf in ["A", "B", "C", "D"]:
            var_text = t.get("variantlar", {}).get(harf, "")
            if var_text:
                pv = doc.add_paragraph()
                pv.paragraph_format.left_indent = Inches(0.3)
                r_let = pv.add_run(f"{harf}) ")
                r_let.font.name = FONT_NAME
                r_let.font.size = Pt(10)

                r_val = pv.add_run(var_text)
                r_val.font.name = FONT_NAME
                r_val.font.size = Pt(10)
                r_val.italic = True

        # Tahlil va kalit qismi
        p_ans = doc.add_paragraph()
        p_ans.paragraph_format.left_indent = Inches(0.2)
        r_ans = p_ans.add_run(f"To'g'ri javob: {t.get('kalit', '')}\n")
        r_ans.font.name = FONT_NAME
        r_ans.font.size = Pt(10)
        r_ans.bold = True
        r_ans.font.color.rgb = RGBColor(0, 100, 0)

        tahlil = t.get("tahlil", {})
        asos = tahlil.get("ilmiy_asos", "")
        dist = tahlil.get("distraktorlar_mantiqi", "")
        
        r_tahlil = p_ans.add_run(f"Ilmiy tahlil: {asos}\nDistraktorlar mantiqi: {dist}")
        r_tahlil.font.name = FONT_NAME
        r_tahlil.font.size = Pt(9.5)
        r_tahlil.font.color.rgb = RGBColor(70, 70, 70)
        
        doc.add_paragraph()

    doc.save(filepath)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.drawRightString(A4[0] - 40, 25, f"{self._pageNumber} / {page_count}")

def build_pdf_document(tests: list, filepath: str, is_teacher: bool = False):
    """PDF formatini yaratish"""
    doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=35, rightMargin=35, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name="TStyle", fontSize=13, fontName="Helvetica-Bold", alignment=1, spaceAfter=15)
    q_style = ParagraphStyle(name="QStyle", fontSize=10, fontName="Helvetica-Bold", spaceAfter=4)
    h_style = ParagraphStyle(name="HStyle", fontSize=9.5, fontName="Helvetica", leftIndent=12, spaceAfter=2)
    v_style = ParagraphStyle(name="VStyle", fontSize=9.5, fontName="Helvetica-Oblique", leftIndent=18, spaceAfter=2)
    a_style = ParagraphStyle(name="AStyle", fontSize=9, fontName="Helvetica", leftIndent=12, spaceBefore=4, spaceAfter=10)

    story = []
    title_text = "BIOLOGIYA — EKSPERTIZA VA METODIK TAHLIL" if is_teacher else "BIOLOGIYA — SINOV TESTLARI"
    story.append(Paragraph(title_text, title_style))

    for idx, t in enumerate(tests, 1):
        shart_matn = f"{idx}. {t.get('shart', '')}"
        story.append(Paragraph(shart_matn, q_style))

        for h in t.get("hukmlar", []):
            story.append(Paragraph(h, h_style))

        for harf in ["A", "B", "C", "D"]:
            var_text = t.get("variantlar", {}).get(harf, "")
            if var_text:
                v_html = f"<b>{harf})</b> <i>{var_text}</i>"
                story.append(Paragraph(v_html, v_style))

        if is_teacher:
            kalit = t.get("kalit", "")
            tahlil = t.get("tahlil", {})
            asos = tahlil.get("ilmiy_asos", "")
            ans_html = f"<b>To'g'ri javob: {kalit}</b><br/><i>Tahlil:</i> {asos}"
            story.append(Paragraph(ans_html, a_style))

        story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)