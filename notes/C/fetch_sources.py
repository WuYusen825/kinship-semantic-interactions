import json, re, urllib.request, urllib.parse, concurrent.futures, pathlib, subprocess

ROOT=pathlib.Path('/workspace/kinship_research')
OUT=ROOT/'literature/C'
NOTES=ROOT/'notes/C'
DOIS={
'C01':'10.1016/j.jml.2007.11.007',
'C02':'10.1016/j.jml.2012.11.001',
'C03':'10.18637/jss.v067.i01',
'C04':'10.1111/ecog.02881',
'C05':'10.1214/08-AOAS191',
'C06':'10.1093/biomet/80.1.27',
'C07':'10.1111/j.2517-6161.1995.tb02031.x',
'C08':'10.1086/204317',
'C09':'10.1038/nature09923',
'C10':'10.1371/journal.pone.0158391',
'C11':'10.1038/sdata.2018.205',
'C12':'10.1162/rest.90.3.414',
}
PDFS={
'C01':['https://pmc.ncbi.nlm.nih.gov/articles/PMC2613284/pdf/nihms81944.pdf'],
'C02':['https://pmc.ncbi.nlm.nih.gov/articles/PMC3881361/pdf/nihms-524979.pdf'],
'C03':['https://www.jstatsoft.org/article/view/v067i01/v67i01.pdf'],
'C04':['https://www.wsl.ch/fileadmin/user_upload/WSL/Mitarbeitende/wohlgemu/Roberts_et_al_2017_Ecography.pdf'],
'C05':['https://www.stat.columbia.edu/~gelman/research/published/priors.pdf'],
'C06':[],
'C07':['https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_hochberg1995.pdf'],
'C08':[],
'C09':['https://www.mpi.nl/publications/escidoc-63501/fulltext'],
'C10':['https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0158391&type=printable'],
'C11':['https://www.nature.com/articles/sdata2018205.pdf'],
'C12':['https://cameron.econ.ucdavis.edu/research/Cameron_Gelbach_Miller_2008.pdf'],
}

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 academic-literature-retrieval/1.0'})
    with urllib.request.urlopen(req,timeout=35) as r:
        return r.read(),r.status,r.geturl(),dict(r.headers)

def process(item):
    ident,doi=item
    rec={'id':ident,'doi':doi,'download_attempts':[]}
    try:
        raw,_,_,_=get('https://api.crossref.org/works/'+urllib.parse.quote(doi,safe=''))
        (NOTES/f'{ident}_crossref.json').write_bytes(raw)
        m=json.loads(raw)['message']
        rec.update(title=m['title'][0],authors=[a.get('given','')+' '+a.get('family','') for a in m.get('author',[])],year=m.get('published-print',m.get('published',{}))['date-parts'][0][0],venue=m.get('container-title',[''])[0],url=m['URL'],volume=m.get('volume'),issue=m.get('issue'),pages=m.get('page'))
        abstract=m.get('abstract','')
        if abstract:
            p=NOTES/f'{ident}_abstract.txt'
            p.write_text(re.sub('<[^>]+>','',abstract),encoding='utf8')
            rec['abstract_path']=str(p)
            rec['abstract_url']='https://api.crossref.org/works/'+doi
    except Exception as e:rec['metadata_error']=str(e)
    try:
        raw,_,_,_=get('https://api.openalex.org/works/https://doi.org/'+doi)
        (NOTES/f'{ident}_openalex.json').write_bytes(raw)
        oa=json.loads(raw)
        urls=PDFS[ident]+[a['pdf_url'] for a in oa.get('locations',[]) if a.get('pdf_url')]
        rec['candidate_urls']=list(dict.fromkeys(urls))
        if not rec.get('abstract_path') and oa.get('abstract_inverted_index'):
            idx=oa['abstract_inverted_index']; words={i:w for w,inds in idx.items() for i in inds}
            p=NOTES/f'{ident}_abstract.txt';p.write_text(' '.join(words[i] for i in sorted(words)),encoding='utf8')
            rec['abstract_path']=str(p);rec['abstract_url']=oa.get('primary_location',{}).get('landing_page_url') or oa['doi']
            rec['abstract_provenance']='OpenAlex abstract index; original source verification pending'
    except Exception as e:rec['openalex_error']=str(e);rec['candidate_urls']=PDFS[ident]
    for url in rec['candidate_urls'][:5]:
        try:
            raw,status,final,headers=get(url)
            if raw[:5]!=b'%PDF-':
                rec['download_attempts'].append({'url':url,'status':f'HTTP {status}; not PDF; {headers.get("Content-Type", "unknown")}'});continue
            path=OUT/f'{ident}.pdf';path.write_bytes(raw)
            txt=NOTES/f'{ident}_fulltext.txt'
            p=subprocess.run(['pdftotext','-layout',str(path),str(txt)],capture_output=True,text=True)
            rec['download_attempts'].append({'url':url,'status':f'HTTP {status}; valid PDF; {len(raw)} bytes; pdftotext exit {p.returncode}'})
            rec.update(pdf_url=final,pdf_path=str(path),access_level='full_text_pdf',fulltext_path=str(txt))
            break
        except Exception as e:rec['download_attempts'].append({'url':url,'status':str(e)})
    if not rec.get('pdf_path'):rec.update(pdf_url=None,pdf_path=None,access_level='abstract_only' if rec.get('abstract_path') else 'metadata_only')
    return rec

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results=list(ex.map(process,DOIS.items()))
    (OUT/'records_initial.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps([{k:r.get(k) for k in ['id','title','authors','year','access_level','abstract_path','candidate_urls','download_attempts']} for r in results],ensure_ascii=False,indent=2))
