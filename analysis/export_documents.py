from pathlib import Path
import subprocess,concurrent.futures
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt,Cm
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
names=['研究计划_完善版','论文_中文实证稿','文献综述与证据台账','PDF无法下载清单']
def build(name):
    p=OUT/(name+'.md')
    cmds=[['pandoc',str(p),'-o',str(OUT/(name+'.pdf')),'--pdf-engine=xelatex','-V','mainfont=Noto Serif CJK SC','-V','sansfont=Noto Sans CJK SC','-V','monofont=Noto Sans Mono CJK SC','-V','geometry:margin=2cm','-V','fontsize=11pt','--include-in-header='+str(OUT/'pdf_header.tex')]]
    if name in names[:2]:cmds.append(['pandoc',str(p),'-o',str(OUT/(name+'.docx'))])
    for cmd in cmds:
        r=subprocess.run(cmd,cwd=OUT,capture_output=True,text=True)
        (OUT/(name+('.pdf' if '--pdf-engine=xelatex' in cmd else '.docx')+'_排版日志.txt')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(name+'\n'+r.stderr)
    text_export=subprocess.run(['pdftotext','-layout',str(OUT/(name+'.pdf')),str(OUT/(name+'.txt'))],capture_output=True,text=True)
    if text_export.returncode:raise RuntimeError(name+' TXT export failed: '+text_export.stderr)
    if name in names[:2]:
        path=OUT/(name+'.docx');d=Document(path)
        for style in d.styles:
            if style.type==1:
                style.font.name='Times New Roman'
                rpr=style.element.get_or_add_rPr();fonts=rpr.find(qn('w:rFonts'))
                if fonts is None:fonts=OxmlElement('w:rFonts');rpr.append(fonts)
                fonts.set(qn('w:eastAsia'),'黑体' if style.name.startswith('Heading') or style.name=='Title' else '宋体')
        d.styles['Normal'].font.size=Pt(11)
        for sec in d.sections:
            sec.page_height=Cm(29.7);sec.page_width=Cm(21);sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Cm(2)
        d.save(path)
    return name
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    for name in ex.map(build,names):print(name+'：排版完成',flush=True)
