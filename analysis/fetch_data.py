"""下载锁定 commit 的必要公开数据；已有同名文件只校验，不覆盖。"""
from pathlib import Path
import hashlib,json,urllib.request

BASE=Path(__file__).resolve().parents[1]
PROV=json.loads((BASE/'analysis'/'provenance.json').read_text())
KIN=PROV['kinbank_commit'];GLOT=PROV['glottolog_commit']
TASKS=[
    ('kinbank/kinbank',KIN,'kinbank/cldf/forms.csv','data/kinbank/kinbank/cldf/forms.csv'),
    ('kinbank/kinbank',KIN,'kinbank/cldf/languages.csv','data/kinbank/kinbank/cldf/languages.csv'),
    ('kinbank/kinbank',KIN,'kinbank/cldf/parameters.csv','data/kinbank/kinbank/cldf/parameters.csv'),
    ('kinbank/kinbank',KIN,'kinbank/cldf/sources.bib','data/kinbank/kinbank/cldf/sources.bib'),
    ('kinbank/kinbank',KIN,'kinbank/cldf/cldf-metadata.json','data/kinbank/kinbank/cldf/cldf-metadata.json'),
    ('kinbank/kinbank',KIN,'kinbank/README.md','data/kinbank/kinbank/README.md'),
    ('kinbank/kinbank',KIN,'kinbank/FORMS.md','data/kinbank/kinbank/FORMS.md'),
    ('kinbank/kinbank',KIN,'LICENSE','data/kinbank/LICENSE'),
    ('glottolog/glottolog-cldf',GLOT,'cldf/languages.csv','data/glottolog_languages.csv'),
    ('glottolog/glottolog-cldf',GLOT,'cldf/cldf-metadata.json','data/glottolog_cldf-metadata.json'),
    ('glottolog/glottolog-cldf',GLOT,'README.md','data/glottolog_README.md'),
    ('glottolog/glottolog-cldf',GLOT,'LICENSE','data/glottolog_LICENSE')]

for repo,commit,remote,local in TASKS:
    dest=BASE/local
    if not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True)
        req=urllib.request.Request(f'https://raw.githubusercontent.com/{repo}/{commit}/{remote}',headers={'User-Agent':'KinshipResearch/1.0'})
        with urllib.request.urlopen(req,timeout=60) as response:payload=response.read()
        dest.write_bytes(payload)
    if local in PROV['data_sha256']:
        actual=hashlib.sha256(dest.read_bytes()).hexdigest()
        if actual!=PROV['data_sha256'][local]:raise RuntimeError(f'版本校验失败：{local}')
    print(f'已取得并核查 {local}')
