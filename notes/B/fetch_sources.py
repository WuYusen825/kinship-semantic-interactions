import urllib.request,urllib.parse,json,concurrent.futures,pathlib,time,re
P=pathlib.Path('/workspace/kinship_research/notes/B')
urls={
 'B01':'https://api.crossref.org/works/10.1126/science.1218811',
 'B02':'https://escholarship.org/uc/item/1fg7b7hn',
 'B03':'https://api.crossref.org/works/10.1162/opmi.a.27',
 'B04':'https://api.crossref.org/works/10.1038/s41467-025-67463-4',
 'B05':'https://api.crossref.org/works/10.1146/annurev-linguistics-011817-045406',
 'B06':'https://api.crossref.org/works/10.1073/pnas.1800521115',
 'B07':'https://api.crossref.org/works/10.1002/9781118346136.ch11',
 'B08':'https://api.crossref.org/works/10.1073/pnas.0610341104',
 'B09':'https://api.crossref.org/works/10.1162/opmi_a_00034',
 'B10':'https://api.crossref.org/works/10.1037/a0029347',
 'B11':'https://api.crossref.org/works/10.1073/pnas.1619666114',
 'B12':'https://api.crossref.org/works/10.1016/j.cognition.2020.104289',
 'B13':'https://api.crossref.org/works/10.3389/fpsyg.2015.01964',
 'B14':'https://api.crossref.org/works/10.3758/s13423-021-02017-5',
 'B15':'https://api.crossref.org/works/10.1073/pnas.2025993118',
 'B16':'https://api.crossref.org/works/10.1111/tops.12441',
 'kemp_author':'https://charleskemp.com/publications/',
 'regier_author':'https://lclab.berkeley.edu/pubs/',
 'B03_pmc':'https://pmc.ncbi.nlm.nih.gov/articles/PMC12483572/',
 'B04_publisher':'https://www.nature.com/articles/s41467-025-67463-4',
}
def fetch(t):
 id,u=t
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30); b=r.read(); out=P/(id+('.json' if 'api.crossref' in u else '.html')); out.write_bytes(b)
  if 'api.crossref' in u:
   x=json.loads(b)['message'];return id,x.get('title'),x.get('published'),x.get('author'),x.get('link'),bool(x.get('abstract'))
  return id,r.status,len(b)
 except Exception as e:return id,str(e)
for x in concurrent.futures.ThreadPoolExecutor(8).map(fetch,urls.items()):print(x)
