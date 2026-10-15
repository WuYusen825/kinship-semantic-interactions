import urllib.request,pathlib,json,concurrent.futures,subprocess,re,hashlib
P=pathlib.Path('literature/D_colexification')
us={'D01':['https://marama.huma-num.fr/data/AlexFrancois_2008_Colexification_SemanticMaps_published.pdf','https://shs.hal.science/halshs-00526845/document'],'D02':['https://www.nature.com/articles/s41597-019-0341-x.pdf'],'D03':['https://www.sciencedirect.com/science/article/pii/S0010027722001676/pdf']}
def f(kv):
 id,urls=kv;att=[]
 for u in urls:
  try:
   r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30);b=r.read()
   if not b.startswith(b'%PDF-'):att.append({'url':u,'status':str(r.status)+' not PDF '+str(len(b))});continue
   m=json.load(open(P/(id+'_crossref.json')));author=m['author'][0]['family'];title=re.sub('[^A-Za-z0-9]+','_',m['title'][0]).strip('_');year=2008 if id=='D01' else 2020 if id=='D02' else 2022;p=P/f'{id}_{author}_{year}_{title}.pdf';p.write_bytes(b);raw=subprocess.check_output(['pdftotext','-layout',str(p),'-']).decode();pages=raw.split('\f');pages=pages[:-1] if not pages[-1].strip() else pages;t=p.with_suffix('.txt');t.write_text('# PDF全文文本（UTF-8）\n来源PDF：'+str(p)+'\n原PDF SHA-256：'+hashlib.sha256(b).hexdigest()+'\n页码表示PDF文件页序，不自动等同于印刷页码。\n\n'+'\n\n'.join(f'===== PDF PAGE {i:04} / {len(pages):04} | Native =====\n'+txt for i,txt in enumerate(pages,1)));att.append({'url':u,'status':'downloaded; %PDF- validated; '+str(len(b))+' bytes'});return id,{'pdf_path':str(p),'text_path':str(t),'pdf_url':u,'pdf_pages':len(pages),'sha256':hashlib.sha256(b).hexdigest(),'download_attempts':att}
  except Exception as e:att.append({'url':u,'status':str(e)})
 return id,{'download_attempts':att,'access_level':'excluded_no_fulltext'}
x=dict(concurrent.futures.ThreadPoolExecutor(3).map(f,us.items()));(P/'downloads_d01_d03.json').write_text(json.dumps(x,ensure_ascii=False,indent=2));print(json.dumps(x,ensure_ascii=False,indent=2))
