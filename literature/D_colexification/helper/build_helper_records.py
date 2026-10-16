from pathlib import Path
import json, subprocess, hashlib, datetime
root=Path('literature/D_colexification/helper')
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
conversion=[]
for p in sorted(root.glob('D*.pdf')):
    assert p.read_bytes().startswith(b'%PDF-')
    r=subprocess.run(['pdftotext','-layout',str(p),'-'],capture_output=True,text=True,check=True)
    pages=r.stdout.split('\f')
    if not pages[-1].strip():pages.pop()
    txt=p.with_suffix('.txt')
    header=f'# PDF全文文本（UTF-8）\n来源PDF：{p}\n原PDF SHA-256：{sha(p)}\n页码表示PDF文件页序，不自动等同于期刊印刷页码。Native为原文本层，OCR为扫描或低文字页识别；表格、音标、公式与OCR仍须对照PDF。\n\n'
    body='\n\n'.join(f'===== PDF PAGE {i:04d} / {len(pages):04d} | Native =====\n{s.strip(chr(10))}' for i,s in enumerate(pages,1))
    txt.write_text(header+body+'\n',encoding='utf-8')
    conversion.append({'pdf':str(p),'txt':str(txt),'pdf_sha256':sha(p),'txt_sha256':sha(txt),'pages':len(pages),'ocr_attempted_pages':[],'pages_still_low_text':[i for i,s in enumerate(pages,1) if len(s.strip())<80],'characters':sum(len(s) for s in pages),'page_methods':[{'page':i,'method':'Native','characters':len(s)} for i,s in enumerate(pages,1)],'quality_note':'已逐页提取原文本层；无须OCR。多栏排版、图表和统计符号应对照PDF；页面标记仅表示文件页序。'})
(root/'conversion_report.json').write_text(json.dumps(conversion,ensure_ascii=False,indent=2)+'\n')
all_attempts=[]
for name in ['initial_attempts.json','xu_attempts.json','further_attempts.json','publisher_pdf_attempts.json']:
    all_attempts.extend(json.loads((root/name).read_text()))
meta={}
for key in ['Jackson','Xu','Karjus']:
    meta[key]=json.loads((root/f'crossref_{key}.json').read_text())['message']
def base(key,id,file,version):
    m=meta[key]; c=next(x for x in conversion if Path(x['pdf']).name==file)
    return {'id':id,'title':m['title'][0],'authors_full':[a.get('given','')+' '+a.get('family','') for a in m['author']],'year':m['published']['date-parts'][0][0],'journal':m['container-title'][0],'volume':m.get('volume'),'issue':m.get('issue'),'pages':m.get('page'),'article_number':m.get('article-number'),'doi':m['DOI'],'doi_url':'https://doi.org/'+m['DOI'],'status':'已取得全文PDF及逐页TXT','citation_eligible':True,'pdf':c['pdf'],'txt':c['txt'],'pdf_pages':c['pages'],'pdf_sha256':c['pdf_sha256'],'txt_sha256':c['txt_sha256'],'pdf_version':version,'metadata_verified_at':'2026-10-15','metadata_source':'https://api.crossref.org/works/'+m['DOI'],'metadata_snapshot':str(root/f'crossref_{key}.json'),'conversion_report':str(root/'conversion_report.json'),'download_attempts':[a for a in all_attempts if key.lower() in (a.get('file','')+' '+a.get('url','')).lower()]}
r4=base('Jackson','D04','D04_Jackson_2019.pdf','正式期刊排版，ANU机构库合法公开副本')
r4.update({'citation':'Jackson, J. C., Watts, J., Henry, T. R., List, J.-M., Forkel, R., Mucha, P. J., Greenhill, S. J., Gray, R. D., & Lindquist, K. A. (2019). Emotion semantics show both cultural variation and universal structure. Science, 366(6472), 1517–1522. https://doi.org/10.1126/science.aaw8160',
'landing_page':'https://openresearch-repository.anu.edu.au/items/3bf3f8f5-4f56-4bc2-9537-022817f61f19',
'pdf_download_url':'https://openresearch-repository.anu.edu.au/bitstreams/51e9da84-0297-470f-beb0-c58eeec2c575/download',
'abstract_zh':'研究以2474种语言的情绪概念共词化网络比较语义组织。不同语系呈现明显差异，语系的地理接近与网络结构相似有关；情绪效价和生理激活程度又体现较广泛的组织作用。这为同时讨论跨语言共享约束与历史、文化差异提供实例。',
'abstract_source':'PDF第1页；原文摘要。',
'page_number_note':'期刊书目页码为1517–1522。此副本PDF共6页：第1–5页正文页脚为1 of 5至5 of 5，第6页是期刊书目信息。未据此推定每一文件页对应的连续印刷页码；定位采用PDF文件页及正文自标页。',
'evidence':[{'claim_zh':'共词化测量两个不同概念是否由同一词形表达；它可作为语义组织的线索。','pdf_pages':[2],'printed_page_label':'正文2 of 5','location':'正文关于colexification的界定及Fig.1。'}, {'claim_zh':'本文使用2474种语言的资料，比较情绪共词化网络及语系之间的结构。','pdf_pages':[1,2],'printed_page_label':'正文1–2 of 5','location':'摘要、样本与网络构造。'}, {'claim_zh':'语系地理距离与情绪网络相似性有关，支持研究中考虑谱系和地域结构。','pdf_pages':[3],'printed_page_label':'正文3 of 5','location':'Fig.3及其邻近结果。'}, {'claim_zh':'效价与激活维度具有较高模型解释作用；此处为情绪领域模型比较。','pdf_pages':[4,5],'printed_page_label':'正文4–5 of 5','location':'Fig.4、删去维度的AIC比较及讨论。'}],
'proposition_links':{'P1':'提供共词化网络测量及跨语言结构比较背景；未检验亲属类别合取比例。','P2':'未直接检验年龄条件下年长侧的性别二级区分。','P3':'未直接检验性别条件下男性侧的年龄二级区分。','P4':'未直接检验相对性别条件下同性侧的年龄二级区分。','P5':'未直接检验参照者性别的三级位置。','P6':'地理接近与网络结构关联为分组外推设计提供动机；本文未比较本研究的显式条件结构模型和加性模型。'},
'limits_zh':'情绪概念共词化不是亲属语义特征层级的直接证据；同词形网络也不能自动视为概念同一或完整类别划分。地理相关不能单独识别接触的因果机制。'})
r5=base('Xu','D05','D05_Xu_2020_author_preprint.pdf','作者公开稿；首页标注To appear in Cognition，不能标作已下载出版社最终PDF')
r5.update({'citation':'Xu, Y., Duong, K., Malt, B. C., Jiang, S., & Srinivasan, M. (2020). Conceptual relations predict colexification across languages. Cognition, 201, 104280. https://doi.org/10.1016/j.cognition.2020.104280',
'landing_page':'https://www.cs.utoronto.ca/~yangxu/papers.html',
'pdf_download_url':'https://www.cs.toronto.edu/~yangxu/xu_et_al_2020_colexification_preprint.pdf',
'abstract_zh':'研究将246种语言的共词化资料与独立的概念联想、语料相似性等指标相联系。结果表明，跨语言更常共词化的概念通常具有更强的联想关系，支持概念关联与认知经济解释。概念联想和语义相似性在研究中分别操作化，不能混同。',
'abstract_source':'作者公开稿PDF第2页；原文摘要。',
'page_number_note':'正式期刊以文章号104280定位，无期号。已取得作者公开稿29页，其页眉页码1–29与PDF文件页序一致；下列定位均为作者稿页，不得改写成出版社最终版页码。',
'evidence':[{'claim_zh':'共词化按两个意义共享相同词形操作化，包含多义和同音同形的可能性。','pdf_pages':[9],'printed_page_label':'作者稿第9页','location':'§2.1 Cross-linguistic data of colexification。'}, {'claim_zh':'样本为246种语言、41个语系；以分层自助法评估语系、气候、地域不均衡。','pdf_pages':[9,10],'printed_page_label':'作者稿第9–10页','location':'§2.1。'}, {'claim_zh':'概念联想和word2vec余弦相似性是不同预测指标；另考虑词频等变量。','pdf_pages':[11,12],'printed_page_label':'作者稿第11–12页','location':'§2.2 Predictors of colexification frequency。'}, {'claim_zh':'存在性分类采用十折验证；讨论将联想关系视为解释共词化频率的重要变量。','pdf_pages':[15,16,22],'printed_page_label':'作者稿第15–16、22页','location':'§3结果与§4讨论。'}],
'proposition_links':{'P1':'支持将同词形共享定义为可检验结果变量，并提醒同音、多义与参考概念选择的影响；未检验类别合取比例。','P2':'未直接检验亲属年长侧性别区分。','P3':'未直接检验亲属男性侧年龄区分。','P4':'未直接检验亲属同性侧年龄区分。','P5':'未直接检验参照者性别的层级位置。','P6':'提供独立语义预测指标和验证比较的先例；其概念对十折验证不等于本研究未见谱系、未见地域外推检验。'},
'limits_zh':'概念关联指标主要来自英语；本文指出参考概念和单词标签的限制。联想关系的证据不能直接当作某一亲属特征交互的证据。',
'version_availability_note':'出版社网页和最终PDF端点本次返回403；已合法取得作者公开全文，不属于无法取得任何全文的文献。',
'citation_mismatch_note':'Hallam 2025正文关于一般词汇共词化的句子标为Xu, Liu, & Regier (2020)，参考文献却列数词系统论文（本库B09）。该引文不能作为本篇的准确书目来源；本篇依据独立作者主页、Crossref和出版社资料核实。'})
r6=base('Karjus','D06','D06_Karjus_2021.pdf','正式期刊开放版，塔林大学文化数据分析项目公开副本；首页含CC BY-NC-ND许可')
r6.update({'citation':'Karjus, A., Blythe, R. A., Kirby, S., Wang, T., & Smith, K. (2021). Conceptual similarity and communicative need shape colexification: An experimental study. Cognitive Science, 45(9), e13035. https://doi.org/10.1111/cogs.13035',
'landing_page':'https://onlinelibrary.wiley.com/doi/10.1111/cogs.13035',
'pdf_download_url':'https://cudan.tlu.ee/pub/2021_CogSci_Karjus-et-al_Conceptual-Similarity.pdf',
'license_url':'http://creativecommons.org/licenses/by-nc-nd/4.0/',
'abstract_zh':'四个人工语言交流实验考察概念相似性与区分需求如何影响共词化。一般条件下，参与者较常让相似概念共享信号；当交流频繁要求区分这些概念时，该倾向减弱。结果为区分相似性偏好和交际需求作用提供实验依据。',
'abstract_source':'PDF第1页；原文摘要。',
'page_number_note':'正式期刊用文章号e13035定位。PDF30页的正文自标页码为1 of 30至30 of 30，与文件页序一致。',
'evidence':[{'claim_zh':'共词化是不同意义共享词形的描述性关系，不以已判明多义或同音为前提。','pdf_pages':[2],'printed_page_label':'2 of 30','location':'§1 Introduction。'}, {'claim_zh':'刺激选择将语义相似性与联想关系区分，使用高相似、低联想的目标词对。','pdf_pages':[5,6],'printed_page_label':'5–6 of 30','location':'§2.2 Meanings及Fig.2。'}, {'claim_zh':'目标条件增加相似目标意义相互成为候选时的区分需求；其操纵不是简单提高概念自身总频率。','pdf_pages':[7,20],'printed_page_label':'7、20 of 30','location':'§2.4交际需求操纵、§7.1讨论。'}, {'claim_zh':'四实验支持相似性偏好随交际区分需求变化；外推仍受小词表与人工情境限制。','pdf_pages':[4,19,23],'printed_page_label':'4、19、23 of 30','location':'实验概述、§7 General discussion、§8 Conclusions。'}],
'proposition_links':{'P1':'为共词化取舍和交际基准提供实验背景；未检验亲属严格划分中的合取比例。','P2':'未直接检验年长侧性别二级区分。','P3':'未直接检验男性侧年龄二级区分。','P4':'未直接检验同性侧年龄二级区分。','P5':'未直接检验参照者性别只出现于三级。','P6':'说明相似性与交际需求应作为可区分的解释；其交互概念不等于本研究特定亲属语义条件结构，未报告本研究的跨谱系或跨地域模型增益。'},
'limits_zh':'人工交流情境及小词表的机制性证据不提供自然语言中P2–P5的方向证据。不可把文中的相似性×交际需求关系当作本研究已经执行的亲属模型。'})
records=[r4,r5,r6]
(root/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'id':r['id'],'title':r['title'],'pages':r['pdf_pages'],'version':r['pdf_version']} for r in records],ensure_ascii=False,indent=2))
