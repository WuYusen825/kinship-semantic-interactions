import urllib.request,json,pathlib,concurrent.futures,subprocess
N=pathlib.Path('/workspace/kinship_research/notes/B');P=pathlib.Path('/workspace/kinship_research/literature/B');d=json.load(open(N/'downloads.json'))
us={
'B03':['https://cdn.ncbi.nlm.nih.gov/pmc/blobs/333e/12483572/1738a61207d7/opmi-09-1431.pdf','https://pmc.ncbi.nlm.nih.gov/articles/PMC12483572/pdf/opmi-09-1431.pdf'],
'B09':['https://cdn.ncbi.nlm.nih.gov/pmc/blobs/62d5/8412190/c88af03076fd/opmi-04-57.pdf'],
'B11':['https://dspace.mit.edu/bitstreams/d8a3dc13-3924-4b1d-8790-94ef85c75314/download'],
'B12':['https://osf.io/download/atuwf/','https://files.osf.io/v1/resources/jkfyx_v1/providers/osfstorage/5b3927de82299e000e19c403'],
'B16':['https://escholarship.org/content/qt8p67769q/qt8p67769q.pdf'],
}
def f(kv):
 id,urls=kv; v=d[id]
 for u in urls:
  try:
   r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30);b=r.read()
   if b[:5]!=b'%PDF-':v['download_attempts'].append({'url':u,'status':str(r.status)+'; not PDF '+str(len(b))});continue
   p=P/(id+'.pdf');p.write_bytes(b);t=N/(id+'_fulltext.txt');subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
   v.update({'pdf_url':u,'pdf_path':str(p),'first_text':t.read_text(errors='ignore')[:800]});v['download_attempts'].append({'url':u,'status':'downloaded; %PDF- validated; '+str(len(b))+' bytes'});return id,v
  except Exception as e:v['download_attempts'].append({'url':u,'status':str(e)})
 return id,v
for id,v in concurrent.futures.ThreadPoolExecutor(5).map(f,us.items()):d[id]=v;print(id,v)
(N/'downloads.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
