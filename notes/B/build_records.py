import pathlib,json,re,html
N=pathlib.Path('/workspace/kinship_research/notes/B');P=pathlib.Path('/workspace/kinship_research/literature/B');d=json.load(open(N/'downloads.json'))
annotations={
'B01':('通过可组合的亲属关系规则计算系统复杂度与交际信息量，发现真实亲属称谓系统接近简洁性—信息量的最优权衡，并解释若干传统分类约束。','为研究提供系统层面的效率背景。其规则语法已经包含语义组合；本研究的增量是指定类别对的样本外统计比较，不能把语义组合本身称为新发现。',[('真实亲属分类系统接近简洁性与信息量的权衡边界。','正文摘要；Science 336, 1049–1054；图2–4'),('复杂度通过生成亲属类别的语法/规则描述，而非三个差异变量的加性逻辑回归。','Methods/规则表示说明；正文第1049–1052页')]),
'B02':('使用1229种语言的Kinbank称谓，计算加权语义相似度与词形编辑相似度的相关，并优化六类特征权重。总体特征编码有层级，但语言之间存在差异。','最直接的加性特征权重先行研究。须说明本研究以完全共享词形为结果、比较样本外预测和相对性别基准；不是重做权重排序。',[('语义相似度采用六类特征相似值的加权求和。','第5832–5833页，表1与公式1'),('讨论部分已描述纳瓦霍语在女性连接亲属中进一步区分性别和相对年龄的条件性结构。','第5837页，Category structure vs category informativeness')]),
'B03':('研究731种语言的代际亲属类别预测关系，以对称条件熵及置换基准衡量系统结构；随后通过人工亲属称谓推广任务检验学习者对预测结构的偏好。','提供类别之间依赖和推广机制的直接证据。与本研究的区别是预测另一代类别体系，而不是同一兄弟姐妹空间中类别对共享词形的差异交互。',[('对称条件熵衡量父辈称谓与其子辈称谓之间的双向可预测性。','Study 1，Measuring Predictive Structure / Symmetric Conditional Entropy'),('731种语言各生成1000次置换以构建保持称谓数的语言特定基准。','Study 1，A Baseline With No Bias for Predictive Structure'),('实验显示学习者偏好预测结构，同时受到性别区分偏好的影响。','Study 3；Discussion；正式版本摘要')]),
'B04':('提出类别系统在特定变换下保持不变的对称性理论，预测不同语义域类别数量的奇偶分布；亲属子领域普遍偏好偶数类别。','最新直接相关研究，已经讨论兄弟姐妹的相对性别。因此相对性别必须成为基准，本研究不能把同/异性关系或类别数规律称为首次发现。',[('亲属分析明确使用所指者与参照者是否同性的相对性别特征。','正文第4页，siblings段落'),('兄弟姐妹分析使用12个Kinbank亲属类型，并去除mG、fG。','Methods，Kinship，第7页'),('正式发表日期为2026年1月14日，卷17，文章358。','出版社页面与Crossref published-online；论文页脚')]),
'B05':('综述亲属、颜色、生物分类、数词和空间关系等领域的跨语言语义变异，讨论效率原则如何解释大量未见的逻辑可能系统与重复出现的类别结构。','综述的总框架来源。适合将局部合并模型放入广义语义类型学，而不能把不同领域的指标直接混为一个模型。',[('效率框架兼顾认知资源与传达精度，并可联系语言变化及文化。','摘要；作者稿Introduction与Efficient communication章节')]),
'B06':('采用信息瓶颈原理描述词汇复杂度与信息准确度的权衡，发现多语言颜色称名达到近最优压缩，且允许软边界与不一致命名。','说明交际理论不要求硬划分。共享词形指标只是可观测操作量，应与心理类别和概率命名区分。',[('信息瓶颈最优系统允许软类别边界，并解释跨语言颜色命名差异。','PNAS 115, 7937–7942，摘要与Results')]),
'B07':('提出跨语义域的简洁性—信息量计算框架，依次讨论颜色、亲属和空间命名，解释普遍约束与跨语言差异如何并存。','提供从单域特征描述到通用交际约束的连接。作者稿中的亲属章节可用于核对规则复杂度与局部加性统计基准的差异。',[('框架同时应用于颜色、亲属和空间关系三个领域。','作者稿Introduction，Figure 1及各领域章节')]),
'B08':('将颜色称名建模为非均匀知觉空间的最优或近最优分割，解释普遍倾向并容纳语言间差异。','展示语义空间本身的几何结构会影响类别边界；兄弟姐妹差异空间的缺失组合和相对性别结构应先核查。',[('最优分割不假定所有颜色处在规则均匀空间。','PNAS 104, 1436–1441，摘要与模型说明')]),
'B09':('分析30种语言的数词系统，覆盖近似数词到递归计数系统，发现不同类型均能体现认知成本与表达准确性间的效率权衡。','显示共同原则可用不同表示和复杂度衡量落实；支持本研究明确区分规则复杂度与逻辑回归的预测损失。',[('样本为30种语言，系统覆盖近似数词、有限精确系统与递归系统。','Open Mind 4, 57–70，摘要与NUMERAL SYSTEMS')]),
'B10':('以对象、特征、关系为基本成分构造概念域，使用可组合表示语言建模，并在11类概念学习域中检验模型。','提醒亲属语义涉及关系而非仅内在特征；特征差异的统计交互不能自动解释为唯一认知表征。',[('概念表示将对象、特征和关系组合起来，并在11个领域检验。','Psychological Review 119, 685–722，摘要与总体模型说明')]),
'B11':('结合110种语言的世界颜色调查、自然图像颜色统计以及三组语言使用者的命名任务，提出颜色称名受实际交际用途影响。','提供交际需要的实证例子，但本研究缺少用途或频率测量，不能把预测增益直接解释为效率的因果证据。',[('分析110种语言WCS数据，并采集Tsimane、玻利维亚西班牙语与英语任务数据。','PNAS 114, 10785–10790，摘要与Methods')]),
'B12':('将学习的简洁性偏好与交际的信息量压力分开，通过贝叶斯迭代学习模型和实验发现：在没有交际任务时，学习者倾向较简单类别系统。','可用于讨论相关性不足以识别机制；亲属语料中的合并规律可能同时受到学习、使用和文化因素影响。',[('模型和实验比较学习者偏向简洁性还是信息量，结果支持简洁性解释。','Cognition 202, 104289；作者稿摘要、实验与General Discussion')]),
'B13':('区分语言专属机制与领域通用原则在语言中的特定效果，讨论简洁性等通用偏好如何在不同域产生不同结构。','为领域之间结果异同提供理论框架；祖辈、父母兄弟姐妹和兄弟姐妹不能机械共享同一组语义维度。',[('领域通用偏好可与具体表示结合产生领域特定结果。','Frontiers in Psychology 6, 1964；摘要与Discussion')]),
'B14':('以程序归纳建模亲属称谓概念习得，分析英语、Pukapuka、土耳其语、Yanomamö，并解释儿童的过度推广、使用不足及概念学习变化。','逻辑组合与关系操作已经得到明确建模。本文的局部交互分析只能提供词汇分类规律的量化检验，不能宣称首次提出亲属概念的组合语义。',[('表示语言包括亲属函数、集合并/交/差等可组合操作。','第770–775页，表示语言和Table 1'),('模型学习四种语言中的亲属称谓并解释儿童使用的发展模式。','第766页摘要；跨语言模拟章节'),('正式卷期为2022年29(3)，在线首发为2021年12月16日。','论文首页；Crossref published-print/published-online')]),
'B15':('将词形长度和语义范畴同时置于信息论通信框架，分析数、时态和证据性标记的系统及词形，实现形式与意义的联合效率解释。','与亲属称谓的词形—意义分析形成方法上的对话；区别二元共享词形、编辑相似度与表达长度三种结果指标。',[('理论同时解释语法特征系统取值与相应表达形式的相对长度。','PNAS 118(49), e2025993118，摘要与模型章节')]),
'B16':('重新分析颜色命名中的交际需要与知觉结构，显示一些暖色优势可由知觉结构解释，同时也发现超出知觉结构的交际需要信号。','展示对竞争基准进行比较的重要性；本研究应先纳入已有相对性别结构，才评估剩余交互是否有增益。',[('知觉结构可解释部分暖色优势，但信息论分析仍支持独立于知觉结构的交际需要。','Topics in Cognitive Science 11(1), 207–219，摘要与Conclusion')]),
}
versionnotes={
'B01':'作者主页提供的Science正式排版PDF，个人研究使用；文件含首页相邻论文尾段，已通过标题、作者、DOI核对目标论文。',
'B02':'出版社机构知识库正式会议论文PDF；PDF作者顺序为Hallam、Kirby、Jordan、Smith。没有将同名会议视频/演示记录DOI当作此论文DOI。',
'B03':'正式期刊PDF在出版社和机构库均403；已下载同题作者预印本，同时获取正式期刊全文XML核对731语言结果和摘要。期刊PDF未下载，明确列入未获得正式版本PDF清单。',
'B05':'作者提供的待刊稿，首页标To appear；以Crossref核对正式2018卷期页码。',
'B07':'作者预印本，首页注明personal use, not for redistribution；正式章页237–263。',
'B09':'已下载2020年三作者正式Open Mind PDF；最初获取的2014年两作者会议版本另存earlier_versions，不作为2020论文PDF或新增文献计数。',
'B10':'作者提供的Online First正式排版版本，首页卷期页码为占位值；正式书目信息按Crossref核对。',
'B12':'作者共享稿，经OSF API解析primary_file后下载；以正式Cognition DOI核对2020出版。',
'B13':'2016年1月12日发表，但DOI与卷号包含2015/6，年份以正式发表日期为准。',
'B14':'在线首发2021，但卷期版本2022，统一按卷期2022引用。',
'B16':'已获得带同一DOI的Topics in Cognitive Science Early View期刊排版PDF；统一按2019卷期引用。另存的2018会议版本不新增计数。',
}
records=[]
for i in range(1,17):
 id=f'B{i:02}';v=d[id]
 if id=='B02':
  m={'title':['Efficient communication drives the semantic structure of kinship terminology'],'author':[{'given':a,'family':b} for a,b in [('Maisy','Hallam'),('Simon','Kirby'),('Fiona','Jordan'),('Kenny','Smith')]],'container-title':['Proceedings of the Annual Meeting of the Cognitive Science Society'],'volume':'47','issue':'0','page':'5831-5837','published':{'date-parts':[[2025]]},'DOI':None};year=2025;u='https://escholarship.org/uc/item/1fg7b7hn'
 else:
  m=json.load(open(N/(id+'.json')))['message'];date=m.get('published-print',m.get('published-online',m['published']));year=date['date-parts'][0][0];u='https://doi.org/'+m['DOI']
 ab=m.get('abstract');absrc='https://api.crossref.org/works/'+m['DOI'] if ab else None
 if ab and (ab.lstrip().startswith('<jats:title>Significance') or id=='B01'): ab=None
 if id in ['B01','B02','B06','B11','B13','B15']:
  t=(N/(id+'_rawtext.txt')).read_text();bounds={'B01':('Languages vary in their systems','\nC\noncepts'),'B02':('Semantic distinctions are encoded variably','\nKeywords:'),'B06':('We derive a principled information-theoretic','\ninformation theory |'),'B11':('What determines how languages categorize colors?','\ncolor naming |'),'B13':('The extent to which the linguistic system','\nKeywords:'),'B15':('Previous work on grammatical marking suggests','\ncommunicative efficiency |')};a,b=bounds[id];start=t.find(a);end=t.find(b,start)
  if start>=0 and end>start:ab=t[start:end];absrc=v['pdf_url']
 if id=='B10':
  t=(N/(id+'_fulltext.txt')).read_text();a=t.find('Humans can learn');b=t.find('Keywords:',a);ab=t[a:b];absrc=v['pdf_url']
 if id=='B12':ab=json.load(open(N/'B12_osf.raw'))['data']['attributes']['description'];absrc='https://api.osf.io/v2/preprints/jkfyx/'
 if ab:
  ab=html.unescape(re.sub(r'<[^>]+>',' ',ab));ap=N/(id+'_abstract.txt');ap.write_text(ab.strip()+'\n');ap=str(ap)
 else:ap=None
 summary,relevance,claims=annotations[id]
 r={'id':id,'title':html.unescape(re.sub(r'\s+',' ',m['title'][0])).rstrip('.'),'authors':[html.unescape((a.get('given','')+' '+a.get('family','')).strip()) for a in m['author']],'year':year,'venue':html.unescape(m['container-title'][0]),'volume':m.get('volume'),'issue':m.get('issue'),'pages':m.get('page'),'article_number':m.get('article-number') or ('1964' if id=='B13' else None),'doi':m.get('DOI'),'url':u,'pdf_url':v['pdf_url'],'pdf_path':v['pdf_path'],'access_level':'fulltext_pdf','abstract_path':ap,'abstract_url':absrc,'download_attempts':v['download_attempts'],'summary_zh':summary,'relevance_zh':relevance,'evidence_claims':[{'claim_zh':c,'locator':l} for c,l in claims],'notes':versionnotes.get(id,'正式期刊排版PDF，标题、作者及DOI核对通过。'),'fulltext_path':str(N/(id+'_fulltext.txt')),'metadata_path':str(N/(id+'.json')) if id!='B02' else '论文PDF首页和标题页','read_scope':'已核对全文题名、作者、来源和摘要；对研究相关的方法、讨论及指定证据位置做定点阅读。'}
 if id=='B03':r.update({'access_level':'fulltext_author_preprint_pdf_and_version_of_record_xml','journal_pdf_unavailable':True,'formal_fulltext_path':str(N/'B03_europexml.raw'),'formal_fulltext_url':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12483572/fullTextXML'})
 elif id in ['B05','B07','B12']:r['access_level']='fulltext_author_manuscript_pdf'
 elif id in ['B10','B16']:r['access_level']='fulltext_early_view_pdf'
 records.append(r)
(P/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));(N/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('records',len(records),'PDFs',sum(pathlib.Path(r['pdf_path']).exists() for r in records),'abstracts',sum(bool(r['abstract_path']) for r in records))
for r in records:print(r['id'],r['year'],r['venue'],r['volume'],r['issue'],r['pages'],r['access_level'])
