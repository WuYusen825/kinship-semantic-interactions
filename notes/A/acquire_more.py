import sys,json,os,urllib.parse
sys.path.insert(0,'/workspace/kinship_research/notes/A')
ns={};s=open('/workspace/kinship_research/notes/A/acquire.py').read();exec(s[:s.index('for r in ThreadPoolExecutor')],ns)
f=ns['f']
for row in [('A07','10.1177/146349960100100203',['https://journals.sagepub.com/doi/pdf/10.1177/146349960100100203?download=true']),('A12','10.1111/tops.12430',['https://research-information.bris.ac.uk/ws/portalfiles/portal/202655238/Full_text_PDF_final_published_version_.pdf']),('A17',None,['https://escholarship.org/content/qt99s7r1fz/qt99s7r1fz.pdf'])]:
 oldp='/workspace/kinship_research/notes/A/'+row[0]+'_acquisition.json';old=json.load(open(oldp)) if os.path.exists(oldp) else None
 r=f(row)
 if old:
  new=json.load(open(oldp));new['download_attempts']=old['download_attempts']+new['download_attempts'];open(oldp,'w').write(json.dumps(new,ensure_ascii=False,indent=2))
 print(json.dumps(r,ensure_ascii=False))
