import urllib.request,urllib.parse,json,os,subprocess,time,re
from concurrent.futures import ThreadPoolExecutor
base='/workspace/kinship_research'; os.makedirs(base+'/literature/A',exist_ok=True)
rows=[
('A01','10.2307/2843284',['https://zenodo.org/records/1679705/files/article.pdf']),
('A02','10.1525/aa.1967.69.2.02a00050',['https://anthrosource.onlinelibrary.wiley.com/doi/pdf/10.1525/aa.1967.69.2.02a00050']),
('A03','10.2307/410665',['https://www.cambridge.org/core/services/aop-cambridge-core/content/view/8B75EC4438C0D67F5EADC147B966FDBA/S009785075611812Xa.pdf/componential-analysis-and-the-study-of-meaning.pdf','https://www.jstor.org/stable/pdf/410665.pdf']),
('A04','10.2307/410664',['https://www.jstor.org/stable/pdf/410664.pdf']),
('A05','10.2307/3772782',['https://www.jstor.org/stable/pdf/3772782.pdf']),
('A06','10.1525/ae.1974.1.3.02a00060',['https://anthrosource.onlinelibrary.wiley.com/doi/pdf/10.1525/ae.1974.1.3.02a00060']),
('A08',None,['https://darwin-online.org.uk/converted/pdf/1871_Morgan_consanguinity_DlibD_A3203.pdf']),
('A09','10.1371/journal.pone.0283218',['https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0283218&type=printable']),
('A10','10.3378/027.083.0209',['https://pure.mpg.de/rest/items/item_417669_11/component/file_958629/content']),
('A11','10.1017/ehs.2020.41',['https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0BF406C9CFC182F9142749FDD0442471/S2513843X20000419a.pdf/div-class-title-no-universals-in-the-cultural-evolution-of-kinship-terminology-div.pdf']),
('A12','10.1111/tops.12430',['https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/tops.12430']),
('A13','10.1371/journal.pone.0147920',['https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0147920&type=printable','https://discovery.ucl.ac.uk/1477055/7/Mace_journal.pone.0147920.PDF']),
('A14','10.1017/S0140525X10000890',['https://cpb-us-w2.wpmucdn.com/web.sas.upenn.edu/dist/0/236/files/2017/04/jones-bbs-kinship_origins-2bxhvg5.pdf']),
('A15',None,['https://escholarship.org/content/qt93c7072g/qt93c7072g.pdf']),
('A16',None,['https://journals.ispan.edu.pl/index.php/cs-ec/article/download/cs.1374/3059/8060'])]
def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 Academic literature retrieval'})
 with urllib.request.urlopen(req,timeout=45) as f:return f.read(),f.status,f.headers.get('Content-Type'),f.url
def f(row):
 id,doi,urls=row; r={'id':id,'doi':doi,'download_attempts':[],'access_level':'unavailable','pdf_path':None,'pdf_url':None}
 if doi:
  try:
   cr=json.loads(get('https://api.crossref.org/works/'+urllib.parse.quote(doi,safe=''))[0])['message']
   open(base+'/notes/A/'+id+'_crossref.json','w').write(json.dumps(cr,ensure_ascii=False,indent=2))
  except Exception as e:r['crossref_error']=str(e)
 for u in urls:
  try:
   d,status,ct,final=get(u); a={'url':u,'status':status,'content_type':ct,'bytes':len(d),'final_url':final,'pdf_magic':d[:5]==b'%PDF-'}
   if d[:5]==b'%PDF-':
    p=base+'/literature/A/'+id+'.pdf';open(p,'wb').write(d)
    info=subprocess.run(['pdfinfo',p],capture_output=True,text=True);a['pdfinfo']=info.stdout;a['pdfinfo_status']=info.returncode
    if info.returncode==0:
     subprocess.run(['pdftotext','-layout',p,base+'/notes/A/'+id+'_fulltext.txt'])
     r.update({'pdf_path':p,'pdf_url':u,'access_level':'pdf_fulltext'});r['download_attempts'].append(a);break
   r['download_attempts'].append(a)
  except Exception as e:r['download_attempts'].append({'url':u,'status':'failed','error':str(e)})
 open(base+'/notes/A/'+id+'_acquisition.json','w').write(json.dumps(r,ensure_ascii=False,indent=2))
 return {k:r[k] for k in ['id','access_level','pdf_path','download_attempts']}
for r in ThreadPoolExecutor(6).map(f,rows):print(json.dumps(r,ensure_ascii=False))
