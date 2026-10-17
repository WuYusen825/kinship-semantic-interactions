"""把 outputs/forum/论坛稿.md 排成投稿用 Word 与 PDF，并导出提交用中文摘要。

运行（仓库根目录）：python analysis/export_forum_documents.py
依赖：pandoc、LibreOffice（soffice）、python-docx；PDF 版使用 Noto CJK 字体。
投稿 Word 使用宋体／黑体／Times New Roman，PDF 另以 Noto CJK 排版，二者正文相同。
--format-profile 可读取用户模板的字体、行距及书目悬挂缩进；PDF字体替代另行说明。
"""
from pathlib import Path
import argparse, copy, hashlib, json, re, shutil, subprocess, tempfile
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm
from docx.text.run import Run

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
    # Pandoc模板的主题字体会覆盖显式东亚字体，导致LibreOffice漏掉中文标题。
    for attr in list(fonts.attrib):
        if 'theme' in attr.lower():
            del fonts.attrib[attr]
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

def apply_format_profile(document, profile, pdf_preview=False):
    """仅覆盖字体、行距与书目悬挂缩进；模板未授权更改页面或章节。"""
    substitutions = profile['pdf_font_substitutions'] if pdf_preview else {}

    def font(target, role):
        east = substitutions.get(role['east_asia'], role['east_asia'])
        latin = substitutions.get(role['latin'], role['latin'])
        target.font.name = latin
        target.font.size = Pt(role['size_pt'])
        if role['bold'] is not None:
            target.font.bold = role['bold']
        rpr = target._element.get_or_add_rPr()
        fonts = rpr.find(qn('w:rFonts'))
        if fonts is None:
            fonts = OxmlElement('w:rFonts'); rpr.append(fonts)
        for attr in list(fonts.attrib):
            if 'theme' in attr.lower():
                del fonts.attrib[attr]
        for attr in ['w:ascii', 'w:hAnsi', 'w:cs']:
            fonts.set(qn(attr), latin)
        fonts.set(qn('w:eastAsia'), east)

    roles = profile['roles']
    style_roles = {'Title':'title', 'Subtitle':'subtitle', 'Author':'author',
                   'Image Caption':'caption', 'Captioned Figure':'caption', 'Figure':'caption'}
    for style in document.styles:
        if style.type != 1:
            continue
        key = 'heading' if style.name.startswith('Heading') else style_roles.get(style.name, 'body')
        font(style, roles[key])
        style.paragraph_format.line_spacing = profile['line_spacing']
    in_refs = False
    for p in document.paragraphs:
        text = p.text.strip()
        if p.style.name.startswith('Heading'):
            in_refs = text == '参考文献'
            key = 'heading'
        elif in_refs:
            key = 'references'
            indent = profile['reference_hanging_indent_pt']
            p.paragraph_format.left_indent = Pt(indent)
            p.paragraph_format.first_line_indent = Pt(-indent)
        elif text.startswith('摘要：'):
            key = 'abstract'
            # 模板只有“摘要”二字加粗，冒号不加粗；不改动源文件提取标记。
            for run in list(p.runs):
                if run.text == '摘要：':
                    run.text = '摘要'
                    colon = copy.deepcopy(run._r)
                    colon_run = Run(colon, p)
                    colon_run.text = '：'; colon_run.bold = False
                    run._r.addnext(colon)
        elif text.startswith('关键词：'):
            key = 'keywords'
        elif re.match(r'^表\d+　', text):
            key = 'caption'
        else:
            key = style_roles.get(p.style.name, 'body')
        p.paragraph_format.line_spacing = profile['line_spacing']
        # 包含超链接内部的run；只改字体，不丢失参考文献斜体和页码上标。
        for element in p._p.iter(qn('w:r')):
            font(Run(element, p), roles[key])
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing = profile['line_spacing']
                    for element in p._p.iter(qn('w:r')):
                        font(Run(element, p), roles['table'])


def format_docx(path, serif, sans, kai, page_numbers=False, profile=None, pdf_preview=False):
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
    if profile:
        apply_format_profile(d, profile, pdf_preview)
    if page_numbers:
        for section in d.sections:
            paragraph = section.footer.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Pt(0)
            run = paragraph.add_run()
            run.font.name = 'Liberation Serif' if profile and pdf_preview else 'Times New Roman'
            run.font.size = Pt(9)
            if profile:
                paragraph.paragraph_format.line_spacing = profile['line_spacing']
            field = OxmlElement('w:fldSimple')
            field.set(qn('w:instr'), 'PAGE')
            value = OxmlElement('w:t')
            value.text = '1'
            run._r.append(value)
            field.append(run._r)
            paragraph._p.append(field)
    d.save(path)

def main():
    parser = argparse.ArgumentParser(description='导出指定论坛稿，保留旧稿产物。')
    parser.add_argument('--input', type=Path, default=SOURCE)
    parser.add_argument('--suffix', default=None, help='输出文件后缀，v2 输入默认使用 _v2。')
    parser.add_argument('--name', default=None, help='指定导出文件名，不含扩展名。')
    parser.add_argument('--abstract-name', default=None, help='指定摘要TXT文件名，不含扩展名。')
    parser.add_argument('--page-numbers', action='store_true', help='在页脚居中添加页码。')
    parser.add_argument('--format-profile', type=Path, help='仅应用用户模板的字体、行距与引用格式规则。')
    args = parser.parse_args()
    profile = json.loads(args.format_profile.read_text()) if args.format_profile else None
    if profile:
        template = ROOT / profile['template_path']
        if hashlib.sha256(template.read_bytes()).hexdigest() != profile['template_sha256']:
            raise ValueError('模板SHA不匹配，请先重新核对格式规则。')
    source = args.input.resolve()
    suffix = args.suffix if args.suffix is not None else ('_v2' if source.stem.endswith('_v2') else '')
    name = args.name or NAME + suffix
    destination = source.parent
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp)/'raw.docx'
        subprocess.run(['pandoc', str(source), '-o', str(raw), '--resource-path', str(destination)], check=True, cwd=destination)
        word = destination/(name+'.docx')
        shutil.copy(raw, word)
        format_docx(word, '宋体', '黑体', '楷体', args.page_numbers, profile)
        pdf_docx = Path(tmp)/(name+'.docx')
        shutil.copy(raw, pdf_docx)
        format_docx(pdf_docx, 'Noto Serif CJK SC', 'Noto Sans CJK SC', 'Noto Serif CJK SC', args.page_numbers, profile, pdf_preview=True)
        subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',tmp,str(pdf_docx)], check=True, capture_output=True)
        shutil.copy(Path(tmp)/(name+'.pdf'), destination/(name+'.pdf'))
    subprocess.run(['pdftotext', '-layout', str(destination/(name+'.pdf')),
                    str(destination/(name+'.txt'))], check=True)
    text = source.read_text()
    abstract = text.split('**摘要：** ')[1].split('\n\n')[0].strip()
    keywords = text.split('**关键词：** ')[1].split('\n\n')[0].strip()
    han = len(re.findall(r'[一-鿿]', abstract))
    abstract_name = args.abstract_name or '中文摘要_提交用'+suffix
    (destination/(abstract_name+'.txt')).write_text(f'{abstract}\n\n关键词：{keywords}\n')
    print(f'Word：{word.name}；PDF：{name}.pdf；摘要汉字数 {han}')

if __name__ == '__main__':
    main()
