"""把 outputs/forum/论坛稿.md 排成投稿用 Word 与 PDF，并导出提交用中文摘要。

运行（仓库根目录）：python analysis/export_forum_documents.py
依赖：pandoc、LibreOffice（soffice）、python-docx；PDF 版使用 Noto CJK 字体。
投稿 Word 使用宋体／黑体／Times New Roman，PDF 另以 Noto CJK 排版，二者正文相同。
"""
from pathlib import Path
import copy, re, shutil, subprocess, tempfile
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

ROOT = Path(__file__).resolve().parents[1]
FORUM = ROOT/'outputs'/'forum'
SOURCE = FORUM/'论坛稿.md'
NAME = '词与世界论坛-英语-吴雨森、瞿唯艺'

def set_fonts(style, east, latin='Times New Roman', size=None, bold=None):
    style.font.name = latin
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts'); rpr.append(fonts)
    for attr in ['w:ascii','w:hAnsi','w:cs']:
        fonts.set(qn(attr), latin)
    fonts.set(qn('w:eastAsia'), east)
    if size: style.font.size = Pt(size)
    if bold is not None: style.font.bold = bold
    style.font.color.rgb = None

def border(el, edges):
    """给表格或单元格设置三线表所需的上下边框。"""
    pr = el.tblPr if el.tag.endswith('tbl') else el.get_or_add_tcPr()
    name = 'w:tblBorders' if el.tag.endswith('tbl') else 'w:tcBorders'
    box = pr.find(qn(name))
    if box is None:
        box = OxmlElement(name); pr.append(box)
    for edge in ['top','left','bottom','right','insideH','insideV']:
        node = box.find(qn('w:'+edge))
        if node is None:
            node = OxmlElement('w:'+edge); box.append(node)
        size = edges.get(edge)
        node.set(qn('w:val'), 'single' if size else 'nil')
        if size:
            node.set(qn('w:sz'), str(size)); node.set(qn('w:space'), '0'); node.set(qn('w:color'), '000000')

def display_width(text):
    return sum(2.2 if ord(ch) > 0x2e80 else 1 for ch in text)

def set_widths(table, total):
    """按各列最长内容（中文计2）分配列宽，避免短列挤压长列。"""
    longest = [max(display_width(c.text.strip()) for c in col.cells) for col in table.columns]
    weights = [max(8, min(w, 40)) + 4 for w in longest]
    widths = [int(total * w / sum(weights)) for w in weights]
    table.autofit = False
    grid = table._tbl.tblGrid.findall(qn('w:gridCol'))
    for i, w in enumerate(widths):
        if i < len(grid):
            grid[i].set(qn('w:w'), str(int(w / 635)))
        for cell in table.columns[i].cells:
            cell.width = w
    tblpr = table._tbl.tblPr
    layout = tblpr.find(qn('w:tblLayout'))
    if layout is None:
        layout = OxmlElement('w:tblLayout'); tblpr.append(layout)
    layout.set(qn('w:type'), 'fixed')
    tw = tblpr.find(qn('w:tblW'))
    if tw is None:
        tw = OxmlElement('w:tblW'); tblpr.append(tw)
    tw.set(qn('w:w'), str(int(total / 635))); tw.set(qn('w:type'), 'dxa')

def format_docx(path, serif, sans, kai):
    d = Document(path)
    for sec in d.sections:
        sec.page_height, sec.page_width = Cm(29.7), Cm(21)
        sec.top_margin = sec.bottom_margin = Cm(2.54)
        sec.left_margin = sec.right_margin = Cm(3.0)
    styles = {s.name: s for s in d.styles}
    for s in styles.values():
        if s.type == 1:
            set_fonts(s, serif)
    for name in ['Normal','Body Text','First Paragraph','Compact']:
        if name in styles:
            st = styles[name]; set_fonts(st, serif, size=12)
            pf = st.paragraph_format
            pf.line_spacing = 1.5 if name != 'Compact' else 1.0
            pf.space_before = Pt(0); pf.space_after = Pt(0)
            if name in ['Body Text','First Paragraph']:
                pf.first_line_indent = Pt(24)
    for name, size, east in [('Title',16,sans),('Subtitle',12,serif),('Author',12,kai),
                             ('Heading 1',15,sans),('Heading 2',14,sans),('Heading 3',12,sans)]:
        if name in styles:
            st = styles[name]; set_fonts(st, east, size=size, bold=name.startswith('Heading') or name=='Title')
            st.paragraph_format.space_before = Pt(12 if name.startswith('Heading') else 6)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.first_line_indent = Pt(0)
            if name in ['Title','Subtitle','Author']:
                st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                st.font.italic = False
    for name in ['Image Caption','Captioned Figure','Figure']:
        if name in styles:
            st = styles[name]; set_fonts(st, serif, size=10.5)
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.first_line_indent = Pt(0)
            st.font.italic = False
    in_refs = False
    for p in d.paragraphs:
        text = p.text.strip()
        if p.style.name.startswith('Heading'):
            in_refs = text == '参考文献'
            continue
        if p.style.name == 'Equation':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(3)
        if re.match(r'^表\d+　', text):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.keep_with_next = True
            for r in p.runs: r.font.size = Pt(10.5)
        if text.startswith('摘要：') or text.startswith('关键词：'):
            p.paragraph_format.first_line_indent = Pt(0)
            for r in p.runs: r.font.size = Pt(10.5)
        if in_refs:
            pf = p.paragraph_format
            pf.first_line_indent = Pt(-21); pf.left_indent = Pt(21); pf.line_spacing = 1.25
            for r in p.runs: r.font.size = Pt(10.5)
    for table in d.tables:
        table.alignment = 1
        set_widths(table, Cm(15))
        border(table._tbl, {'top':12,'bottom':12})
        for i, row in enumerate(table.rows):
            for cell in row.cells:
                if i == 0:
                    border(cell._tc, {'bottom':6})
                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent = Pt(0)
                    p.paragraph_format.line_spacing = 1.15
                    for r in p.runs: r.font.size = Pt(10.5)
    d.save(path)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp)/'raw.docx'
        subprocess.run(['pandoc', str(SOURCE), '-o', str(raw), '--resource-path', str(FORUM)], check=True, cwd=FORUM)
        word = FORUM/(NAME+'.docx')
        shutil.copy(raw, word)
        format_docx(word, '宋体', '黑体', '楷体')
        pdf_docx = Path(tmp)/(NAME+'.docx')
        shutil.copy(raw, pdf_docx)
        format_docx(pdf_docx, 'Noto Serif CJK SC', 'Noto Sans CJK SC', 'Noto Serif CJK SC')
        subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',tmp,str(pdf_docx)], check=True, capture_output=True)
        shutil.copy(Path(tmp)/(NAME+'.pdf'), FORUM/(NAME+'.pdf'))
    text = SOURCE.read_text()
    abstract = text.split('**摘要：** ')[1].split('\n\n')[0].strip()
    keywords = text.split('**关键词：** ')[1].split('\n\n')[0].strip()
    han = len(re.findall(r'[一-鿿]', abstract))
    (FORUM/'中文摘要_提交用.txt').write_text(f'{abstract}\n\n关键词：{keywords}\n')
    print(f'Word：{word.name}；PDF：{NAME}.pdf；摘要汉字数 {han}')

if __name__ == '__main__':
    main()
