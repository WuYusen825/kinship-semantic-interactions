from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT.parent/'亲属称谓研究_完整资料包.zip'
data_rel=[
 'data/kinbank/kinbank/cldf/forms.csv','data/kinbank/kinbank/cldf/languages.csv',
 'data/kinbank/kinbank/cldf/parameters.csv','data/kinbank/kinbank/cldf/sources.bib',
 'data/kinbank/kinbank/cldf/cldf-metadata.json','data/kinbank/kinbank/README.md',
 'data/kinbank/kinbank/FORMS.md','data/kinbank/LICENSE','data/glottolog_languages.csv',
 'data/glottolog_cldf-metadata.json','data/glottolog_README.md','data/glottolog_LICENSE','data/glottolog_commit.json']
files=[ROOT/n for n in ['README.md','original_research_plan.md','CLAUDE.md','CLAUDE_TODO.md','CLAUDE_REVIEW_CHECKLIST.md','CLAUDE_DECISIONS_V3.md','Makefile','CHANGELOG.md','.gitignore','.gitattributes']]+[ROOT/p for p in data_rel]
for p in (ROOT/'data/v3').rglob('*'):
 if p.is_file():files.append(p)
for folder in ['outputs','literature','analysis','notes','docs','results','tests']:
 for p in (ROOT/folder).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or p.name=='资料包文件清单.json':continue
  if '排版预览' in p.name or '排版日志' in p.name or '核验.png' in p.name:continue
  if folder=='notes' and p.suffix in ['.raw','.source']:continue
  files.append(p)
files=sorted(set(files))
assert all(p.exists() for p in files)
records=json.loads((ROOT/'outputs/文献登记表.json').read_text())
formal=sum(r.get('citation_status')=='included_fulltext' for r in records)
incomplete=[r['id'] for r in records if r.get('citation_status')=='excluded_incomplete_pdf']
pdf_count=sum(1 for _ in (ROOT/'literature').rglob('*.pdf'))
manifest={'资料包说明':f'{formal}项完整全文来源、{pdf_count}个源PDF及对应TXT；A02、A05无全文，'+(','.join(incomplete) or '无')+'为不完整副本，均不进入新版引用；早期版本和补充文件不重复计数。',
          '完整全文来源数':formal,'源PDF数':pdf_count,'不完整副本排除':incomplete,'files':[]}
for p in files:
 manifest['files'].append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
m=ROOT/'outputs/资料包文件清单.json';m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(m)
with zipfile.ZipFile(DEST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,arcname=str(Path('kinship_research')/p.relative_to(ROOT)))
with zipfile.ZipFile(DEST) as z:
 assert z.testzip() is None
 print(json.dumps({'archive':str(DEST),'files':len(z.namelist()),'size_mb':round(DEST.stat().st_size/1024**2,1),'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest()},ensure_ascii=False))
