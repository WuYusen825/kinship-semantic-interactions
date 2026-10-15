import urllib.request,json,pathlib,concurrent.futures,subprocess
P=pathlib.Path('/workspace/kinship_research/literature/B'); N=pathlib.Path('/workspace/kinship_research/notes/B')
urls={
'B01':['https://www.charleskemp.com/papers/kempr_kinshipcategoriesacrosslanguagesreflectgeneralcommunicativeprinciples.pdf'],
'B02':['https://escholarship.org/content/qt1fg7b7hn/qt1fg7b7hn.pdf'],
'B03':['https://www.research.ed.ac.uk/files/560907672/HallamEtalOM2025PredictiveStructure.pdf','https://direct.mit.edu/opmi/article-pdf/doi/10.1162/OPMI.a.27/2555700/opmi.a.27.pdf'],
'B04':['https://www.nature.com/articles/s41467-025-67463-4.pdf'],
'B05':['https://www.charleskemp.com/papers/kempxr_semantictypologyandefficientcommunication.pdf'],
'B06':['https://www.charleskemp.com/papers/zaslavskykrt_efficientcompressionincolornaminganditsevolution.pdf'],
'B07':['https://lclab.berkeley.edu/papers/EC-chapter-2014.pdf'],
'B08':['https://lclab.berkeley.edu/papers/regier-kay-khetarpal-PNAS-2007.pdf'],
'B09':['https://escholarship.org/content/qt27j6p2x9/qt27j6p2x9.pdf'],
'B10':['https://www.charleskemp.com/papers/kemp_exploringtheconceptualuniverse.pdf'],
'B11':['https://www.pnas.org/content/pnas/114/40/10785.full.pdf','https://www.pnas.org/doi/pdf/10.1073/pnas.1619666114'],
'B12':['https://www.research.ed.ac.uk/files/148862213/Carr_Smith_Culbertson_Kirby.pdf','https://psyarxiv.com/jkfyx/download'],
'B13':['https://www.frontiersin.org/articles/10.3389/fpsyg.2015.01964/pdf','https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.01964/pdf'],
'B14':['https://link.springer.com/content/pdf/10.3758/s13423-021-02017-5.pdf'],
'B15':['https://escholarship.org/content/qt9zx351pm/qt9zx351pm.pdf','https://www.pnas.org/doi/pdf/10.1073/pnas.2025993118'],
'B16':['https://arxiv.org/pdf/1805.06165','https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/tops.12395'],
}
def f(kv):
 id,us=kv; attempts=[]
 for u in us:
  try:
   r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=35);b=r.read()
   if b[:5]!=b'%PDF-': attempts.append({'url':u,'status':str(r.status)+'; not PDF '+str(len(b))});continue
   p=P/(id+'.pdf');p.write_bytes(b);t=N/(id+'_fulltext.txt');subprocess.run(['pdftotext','-layout',str(p),str(t)],check=True)
   attempts.append({'url':u,'status':'downloaded; %PDF- validated; '+str(len(b))+' bytes'})
   return id,{'pdf_url':u,'pdf_path':str(p),'download_attempts':attempts,'first_text':t.read_text(errors='ignore')[:900]}
  except Exception as e:attempts.append({'url':u,'status':str(e)})
 return id,{'pdf_url':None,'pdf_path':None,'download_attempts':attempts}
results=dict(concurrent.futures.ThreadPoolExecutor(8).map(f,urls.items()));(N/'downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
for k,v in results.items():print(k,v)
