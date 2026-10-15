"""核验本轮全文、TXT、引用范围与原冻结统计文件；不重拟合模型。"""
from pathlib import Path
import json,re,hashlib,subprocess,datetime
import fitz
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    record_paths=[ROOT/'literature'/g/'records.json' for g in 'ABC']
    additional=ROOT/'literature/D_colexification/records.json'
    if additional.exists():record_paths.append(additional)
    groups=sum([json.loads(p.read_text()) for p in record_paths],[])
    united=json.loads((ROOT/'outputs/文献登记表.json').read_text())
    assert {r['id']:r for r in groups}=={r['id']:r for r in united},'Grouped and unified records differ'
    formal=[r for r in groups if r.get('citation_status')=='included_fulltext']
    excluded=[r for r in groups if r.get('citation_status')=='excluded_no_fulltext']
    incomplete=[r for r in groups if r.get('citation_status')=='excluded_incomplete_pdf']
    baseline_ids=({f'A{i:02d}' for i in range(1,21)}-{'A02','A05'}
                  |{f'B{i:02d}' for i in range(1,17)}|{f'C{i:02d}' for i in range(1,13)})
    assert len(groups)==len({r['id'] for r in groups}),'Duplicate literature IDs'
    assert {r['id'] for r in incomplete}<={'C08'}
    assert {r['id'] for r in formal+incomplete if r['id'][0] in 'ABC'}==baseline_ids
    assert {r['id'] for r in excluded}=={'A02','A05'}
    for r in formal:
        assert r['formal_counted'] is True
        p=ROOT/r['pdf_path'];t=ROOT/r['txt_path']
        assert p.exists() and t.exists() and p.with_suffix('.txt')==t
        assert p.read_bytes()[:5]==b'%PDF-' and digest(p)==r['pdf_sha256']
        assert digest(t)==r['txt_sha256']
    uploads=json.loads((ROOT/'literature/uploaded_pdf_manifest.json').read_text())['files']
    assert len(uploads)==8
    for x in uploads:assert digest(ROOT/x['renamed_pdf'])==x['sha256']
    report=json.loads((ROOT/'literature/pdf_text_conversion_report.json').read_text())
    files=report['files'];actual_pdfs={str(p.relative_to(ROOT)) for p in (ROOT/'literature').rglob('*.pdf')}
    assert len(files)>=51 and {r['pdf'] for r in files}==actual_pdfs
    assert {str(p.relative_to(ROOT)) for p in (ROOT/'literature').rglob('*.txt')}=={r['txt'] for r in files}
    for r in files:
        p=ROOT/r['pdf'];t=ROOT/r['txt'];s=t.read_text()
        assert digest(p)==r['pdf_sha256'] and digest(t)==r['txt_sha256']
        with fitz.open(p) as doc:assert doc.page_count==r['pages']
        marks=re.findall(r'^===== PDF PAGE (\d+) / (\d+) \| .*? =====$',s,re.M)
        assert len(marks)==r['pages'] and [int(x[0]) for x in marks]==list(range(1,r['pages']+1))
        assert all(int(x[1])==r['pages'] for x in marks) and 'OCR_PENDING' not in s
    # 原研究计划及旧论文是保留的历史稿，不要求随S2新增文献改写。
    expected_ids=baseline_ids
    checked_docs=[];link_count=0
    docs=[ROOT/'README.md',ROOT/'CLAUDE.md',ROOT/'CLAUDE_TODO.md',ROOT/'CLAUDE_REVIEW_CHECKLIST.md',ROOT/'literature/README.md',ROOT/'literature/TXT索引.md']+list((ROOT/'outputs').glob('*.md'))
    for p in docs:
        s=p.read_text()
        if p.name in ['研究计划_完善版.md','论文_中文实证稿.md']:
            ids=set(re.findall(r'^\[([ABC]\d{2})\]',s,re.M));assert ids==expected_ids,(p.name,ids^expected_ids)
            assert not re.search(r'\[[^\]\n]*\b(?:A02|A05)\b[^\]\n]*\]',s)
            assert not re.search('<!--|回避型|思考过程',s)
        for target in re.findall(r'\]\(([^)]+)\)',s):
            if target.startswith(('https://','http://','#')):continue
            q=target.split('#',1)[0]
            if q and (p.parent/q).resolve()!=(ROOT/'outputs/本轮文献更新核验.json').resolve():
                assert (p.parent/q).exists(),(p,target)
            link_count+=1
        checked_docs.append(str(p.relative_to(ROOT)))
    baseline=json.loads((ROOT/'literature/update_baseline_hashes.json').read_text())
    for path,sha in baseline['files'].items():assert digest(ROOT/path)==sha,('Frozen analysis modified',path)
    low={r['pdf']:r['pages_still_low_text'] for r in files if r['pages_still_low_text']}
    result={'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formal_fulltext_references':len(formal),'excluded_no_fulltext':['A02','A05'],'excluded_incomplete_pdf':[r['id'] for r in incomplete],'publication_completeness_caveats':report.get('publication_completeness_caveats',{}),'uploaded_pdfs_verified':8,'source_pdf_files':len(files),'source_txt_files':len(files),'pdf_pages':report['total_pdf_pages'],'ocr_attempted_pages':report['ocr_attempted_pages'],'remaining_low_text_pages':low,'checked_markdown_documents':checked_docs,'checked_relative_links':link_count,'frozen_statistical_files_unchanged':list(baseline['files']),'statistical_models_rerun':False}
    (ROOT/'outputs/本轮文献更新核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['remaining_low_text_pages','checked_markdown_documents','frozen_statistical_files_unchanged']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
