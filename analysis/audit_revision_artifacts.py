"""核查v2篇幅、DOCX统计与冻结文件；不运行统计估计。"""
from pathlib import Path
from zipfile import ZipFile
import datetime
import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FORUM = ROOT / 'outputs/forum'
NAME = '词与世界论坛-英语-吴雨森、瞿唯艺_v2'
MAINTENANCE = {
    'analysis/export_forum_documents.py': '计划授权指定输入与v2导出接口',
    'analysis/validate_literature_update.py': '新文献D组、完整性排除及动态数量核验',
    'analysis/package_deliverables.py': '资料包动态统计51完整来源、57源PDF，避免写死旧数量',
}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def odt_statistics(source, destination):
    destination.mkdir()
    subprocess.run(['soffice', '--headless', '--convert-to', 'odt',
                    '--outdir', str(destination), str(source)],
                   capture_output=True, check=True)
    with ZipFile(destination / (source.stem + '.odt')) as z:
        root = ET.fromstring(z.read('meta.xml'))
    node = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}document-statistic')
    assert node is not None
    return {k.rsplit('}', 1)[-1]: int(v) for k, v in node.attrib.items()}


def refresh_docx_stats(path, stats):
    """只更新Word扩展属性；内容、字体及排版XML保持原样。"""
    namespace = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
    mapping = {'Words': 'word-count', 'Characters': 'non-whitespace-character-count',
               'CharactersWithSpaces': 'character-count', 'Paragraphs': 'paragraph-count'}
    with ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    updated = []
    for info, data in items:
        if info.filename == 'docProps/app.xml':
            root = ET.fromstring(data)
            pages = root.find('{' + namespace + '}Pages')
            if pages is not None:
                root.remove(pages)  # 导入时ODT的缓存页数不等于实际排版页数。
            for tag, key in mapping.items():
                if key in stats:
                    node = root.find('{' + namespace + '}' + tag)
                    if node is None:
                        node = ET.SubElement(root, '{' + namespace + '}' + tag)
                    node.text = str(stats[key])
            data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        updated.append((info, data))
    temporary = path.with_suffix('.stats.docx')
    with ZipFile(temporary, 'w') as z:
        for info, data in updated:
            z.writestr(info, data)
    temporary.replace(path)


def main():
    source = FORUM / '论坛稿_v2.md'
    text = source.read_text()
    assert '【待' not in text and '待插入' not in text
    abstract = text.split('**摘要：** ', 1)[1].split('\n\n', 1)[0]
    body = text.split('## 一、', 1)[1].split('## 数据与代码', 1)[0]
    body = '## 一、' + body
    prose = '\n'.join(line for line in body.splitlines()
                      if not line.startswith(('|', '![', '#'))
                      and not re.match(r'^[图表]\d+', line))
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    refs = text.split('## 参考文献', 1)[1].strip()
    ref_lines = [s for s in refs.splitlines() if s.strip()]
    figures = len(re.findall(r'^!\[', body, re.M))
    tables = len(re.findall(r'^\|\s*:?-{3,}', body, re.M))
    assert 5400 <= han(body) <= 6600, han(body)
    assert 200 <= han(abstract) <= 300, han(abstract)
    assert figures <= 2 and tables <= 4
    with tempfile.TemporaryDirectory(prefix='kinship-v2-count-') as tmp:
        tmp = Path(tmp)
        md = tmp / '正文.md'
        md.write_text(body)
        body_docx = tmp / '正文.docx'
        subprocess.run(['pandoc', str(md), '-o', str(body_docx), '--resource-path', str(FORUM)],
                       check=True, capture_output=True, cwd=FORUM)
        body_stats = odt_statistics(body_docx, tmp / 'body_statistics')
        full_stats = odt_statistics(FORUM / (NAME + '.docx'), tmp / 'full_statistics')
    refresh_docx_stats(FORUM / (NAME + '.docx'), full_stats)
    with ZipFile(FORUM/(NAME+'.docx')) as z:
        xml = ET.fromstring(z.read('word/document.xml'))
    word_text = ''.join(n.text or '' for n in xml.iter(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    pdf_text = subprocess.check_output(['pdftotext', '-layout', str(FORUM/(NAME+'.pdf')), '-'], text=True)
    word_han = ''.join(re.findall(r'[一-鿿]', word_text))
    pdf_han = ''.join(re.findall(r'[一-鿿]', pdf_text))
    assert word_han == pdf_han, 'PDF与DOCX中文正文/标题/表格/图注顺序不一致'
    main_headings = ['一、引言','二、文献综述','三、数据与方法','四、结果','五、讨论','六、结论']
    assert all(h in pdf_text for h in main_headings)
    baseline = json.loads((ROOT/'notes/revision_baseline_verification.json').read_text())
    manifest = baseline['source_protection']['baseline_manifest_before']
    checks = []
    for rel, old in manifest.items():
        actual = digest(ROOT/rel)
        checks.append({'path': rel, 'baseline_sha256': old['sha256'], 'actual_sha256': actual,
                       'unchanged': actual == old['sha256'],
                       'maintenance_exception': MAINTENANCE.get(rel)})
    assert all(r['unchanged'] or r['maintenance_exception'] for r in checks)
    for rel in ['analysis/supplementary_s1', 'outputs/forum/论坛稿.md',
                'outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺.docx',
                'outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺.pdf',
                'outputs/论文_中文实证稿.md', 'outputs/论文_中文实证稿.docx',
                'outputs/论文_中文实证稿.pdf']:
        assert subprocess.check_output(['git','diff','d32e7d3','--',rel], cwd=ROOT) == b'', rel
    pdf_info = subprocess.check_output(['pdfinfo', str(FORUM/(NAME+'.pdf'))], text=True)
    pdf_pages = int(re.search(r'^Pages:\s+(\d+)', pdf_info, re.M).group(1))
    report = {
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'passed': True, 'manuscript_sha256': digest(source),
        'scope': '正文为第一节起至结论末；含节标题、表格、图题；排除摘要、数据代码说明、参考文献',
        'body_han_with_tables_captions_headings': han(body),
        'body_prose_han_excluding_tables_captions_headings': han(prose),
        'abstract_han': han(abstract), 'references': len(ref_lines),
        'figures': figures, 'tables': tables,
        'word_count_method': 'LibreOffice打开DOCX后转ODT读取刷新document-statistic；全稿统计写回DOCX的Word扩展属性。环境无Microsoft Word，未声称运行其专有计数器。',
        'body_word_compatible_statistics': body_stats, 'full_docx_statistics': full_stats,
        'actual_pdf_pages': pdf_pages,
        'docx_pdf_han_sequence_equal': True,
        'docx_pdf_han_characters': len(word_han),
        'all_six_main_headings_in_pdf': True,
        'pagination_note': 'ODT导入统计中的page-count为缓存值，不作实际页数使用，也不写回Word页数属性；实际页数由最终PDF读取。',
        'frozen_baseline_files': checks,
        'unchanged_count': sum(r['unchanged'] for r in checks),
        'maintenance_exceptions': MAINTENANCE,
        'artifacts_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                            [source, FORUM/(NAME+'.docx'), FORUM/(NAME+'.pdf'),
                             FORUM/'中文摘要_提交用_v2.txt']},
    }
    output = ROOT / 'notes/revision_artifact_check.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['frozen_baseline_files','artifacts_sha256']},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
