import pathlib,json,re,html,hashlib
base=pathlib.Path('/workspace/kinship_research');notes=base/'notes/A';lit=base/'literature/A'
manual={
'A01':dict(title='Classificatory Systems of Relationship',authors=['Alfred Louis Kroeber'],year=1909,summary='区分代际、直旁系、同代年龄、所指性别、说话者性别、连接亲属性别、血亲与姻亲及连接亲属状态等八类亲属分类维度，并指出英语自身也大量合并关系。',relevance='提供基础维度清单，要求区分连接亲属性别与直旁系性；特征组合本身已有百余年研究传统。',claims=[('亲属分类具有代际、直旁系、相对年龄、所指性别、说话者性别与连接亲属性别等经典维度。','PDF第3—4页，原刊第78—79页：八项分类区分')]),
'A02':dict(title='Sibling Terminology and Cross-Sex Behavior',authors=['Sara Nerlove','A. Kimball Romney'],year=1967,summary='摘要提出兄弟姐妹称谓的类型学，并探讨强调跨性别关系的行为模式与区分同性、异性兄弟姐妹称谓之间的关联。',relevance='参照者与所指者的相同性别关系是既有类型学概念；可用作传统相对性别基准。',claims=[('该文摘要将同性／异性兄弟姐妹区分与跨性别关系行为相联系。','出版商原摘要，Crossref元数据')]),
'A03':dict(title='Componential Analysis and the Study of Meaning',authors=['Ward H. Goodenough'],year=1956,summary='出版商所展示的摘要性首段，以Truk亲属称谓为例讨论将成分分析从语言形式推广到文化形式与意义分析。',relevance='为区别语义特征描述与统计加性假设提供历史背景；当前可读首段未报告完整理论和实证细节。',claims=[('该文将亲属称谓的成分分析纳入经验意义研究。','出版商提供的摘要性首段，Crossref元数据')]),
'A04':dict(title='A Semantic Analysis of the Pawnee Kinship Usage',authors=['Floyd G. Lounsbury'],year=1956,summary='出版商提供的摘要性首段将语言的形式结构与文化人类学所研究的非语言刺激、反应和语境联系起来。',relevance='构成形式语义分析与文化语境研究的经典背景；本次摘要性首段不足以重建其Pawnee具体分析规则。',claims=[('该文开篇讨论形式语言研究与文化人类学之间的联系。','出版商提供的摘要性首段，Crossref元数据')]),
'A05':dict(title='Kin Term Patterns and Their Distribution',authors=['George Peter Murdock'],year=1970,summary='仅核实书目信息；本次未取得原文或原摘要，未作为已阅读证据计数。',relevance='经典数据来源；相关论断只能通过已读取后续文献明确标示转引。',claims=[]),
'A06':dict(title='Sibling Typology: Beyond Nerlove and Romney',authors=['David B. Kronenfeld'],year=1974,summary='摘要明确表明文章在Nerlove与Romney的合取性及标记性条件基础上推广类型学，并讨论这些条件的心理基础及其解释范围。',relevance='所选模型必须考虑传统合取性、标记性及相对性别结构，才能判断残余预测增益。',claims=[('兄弟姐妹称谓的合取性及标记性约束已有专门类型学分析。','出版商原摘要，Crossref元数据')]),
'A07':dict(title='Marking Theory and Kinship Analysis: Cross-cultural and Historical Applications',authors=['Per Hage'],year=2001,summary='摘要将Greenberg的亲属标记性理论用于跨文化分类、称谓演变次序和历史社会组织推断。',relevance='帮助将特征不对称与层级约束置于既有理论脉络，限制统计交互的原创性和因果解释范围。',claims=[('标记性理论用于亲属分类的跨文化规律与历史演变研究。','出版商原摘要，Crossref元数据；Sage网页摘要')]),
'A08':dict(title='Systems of Consanguinity and Affinity of the Human Family',authors=['Lewis Henry Morgan'],year=1871,venue='Smithsonian Contributions to Knowledge, Vol. 17, Smithsonian Institution',url='https://darwin-online.org.uk/converted/pdf/1871_Morgan_consanguinity_DlibD_A3203.pdf',summary='通过跨社会关系表及调查比较亲属称谓系统，使用描述式与分类式划分，奠定系统性比较亲属词汇的历史背景。',relevance='说明关系类别与称谓映射的比较并非新议题；采用其资料史贡献，同时结合后来维度化及本土逻辑研究。',claims=[('原著采用跨社会亲属关系调查表进行系统比较，并区分描述式与分类式体系。','PDF第28—30页，Preface；后附各体系关系表')]),
'A09':dict(title='Kinbank: A Global Database of Kinship Terminology',year=2023,summary='发布包含1,229种语言、210,903条数据的开放亲属称谓数据库，采用跨语言关系格网并保存数据来源，讨论类别覆盖及经典合并限制。',relevance='主数据来源；原文明确区分本土概念与外部关系编码，列出年龄、所指性别及参照者性别构成的八类兄弟姐妹关系格网。',claims=[('2023年论文报告1,229种语言与210,903条亲属称谓数据。','PDF第1及5页，Abstract及The Kinbank sample'),('相对性别的本土概念可对应参照者性别与所指性别的外部编码组合。','PDF第4页，emic/etic说明与Kayardild例子'),('兄弟姐妹领域的外部格网由所指性别、参照者性别及相对年龄构成八种类别。','PDF第5页，Nerlove与Romney八类别讨论'),('论文报告864种语言具有完整兄弟姐妹术语，并报告符合旁系性规律的观测合并。','PDF第8—9页，覆盖统计及law of collaterality')]),
'A10':dict(title='A Phylogenetic Analysis of the Evolution of Austronesian Sibling Terminologies',authors=['Fiona M. Jordan'],year=2011,summary='以南岛语系的语言谱系为背景，分别重建相对年龄与相对性别区分的祖先状态和转变过程，并研究异性兄弟姐妹称谓区分的扩展与收缩。',relevance='直接提供兄弟姐妹语义区分的历史研究先例，说明谱系依赖及语义与词形之间的区分；文中将年龄与性别的意义共演化检验列为后续工作。',claims=[('该文分别重建相对年龄和相对性别的历史，并研究相对性别区分的扩展。','PDF第8页，原刊第303页：The Present Study；第20页，原刊第315页Discussion'),('年龄与性别意义变化的共演化检验在本文讨论中作为后续研究方向提出。','PDF第21页，原刊第316页：meaning—meaning coevolution段落')]),
'A11':dict(title='No Universals in the Cultural Evolution of Kinship Terminology',authors=['Sam Passmore','Fiona M. Jordan'],year=2020,summary='在南岛、班图和犹他—阿兹特克三个语系与176个社会中检验亲属称谓演化及18项社会实践共演化理论，发现支持程度随语系和理论而变。',relevance='说明语言谱系、语系差异及社会制度的作用应纳入研究边界；现有数据未支持统一的称谓演化驱动解释。',claims=[('该文跨三个语系检验18项共演化理论，报告证据具有不一致及语系特定性。','PDF第1页，Abstract；全文Results和Discussion')]),
'A12':dict(title='Social Practice and Shared History, Not Social Scale, Structure Cross-Cultural Complexity in Kinship Systems',authors=['Péter Rácz','Sam Passmore','Fiona M. Jordan'],year=2020,summary='使用逾千个社会的全球民族志资料研究堂表亲称谓类型，发现婚姻规则与共同语言背景具有统计关联，并在模型中处理地理邻近及文化祖源。',relevance='支持将共同历史和社会实践纳入词汇分类研究；堂表亲总体类型的关联与兄弟姐妹类别对预测属于不同分析层级。',claims=[('全球样本中，婚姻规则与共享语言背景同堂表亲称谓类型存在统计关联。','PDF第2页，Abstract；正文结果')]),
'A13':dict(title='A Phylogenetic Comparative Study of Bantu Kinship Terminology Finds Limited Support for Its Co-Evolution with Social Organisation',authors=['Myrtille Guillon','Ruth Mace'],year=2016,summary='分析83个历史班图语群体，使用贝叶斯谱系比较研究堂表亲称谓与继嗣、婚后居住制度，报告对共演化假说的支持有限。',relevance='强调不能由词汇结构直接推出统一社会因果过程，并提供控制同源性的相关研究示例。',claims=[('83个班图语群体的谱系比较仅有限支持堂表亲称谓与社会组织共演化。','PDF第1页，Abstract')]),
'A14':dict(title='Human Kinship, from Conceptual Structure to Grammar',authors=['Doug Jones'],year=2010,summary='使用英语与Seneca例子，将亲属称谓的跨语言规律解释为概念结构和沟通约束的结合，并以普遍约束的不同排序形成变异。',relevance='是效率解释之前的重要形式理论；提示特征排序、结构约束与统计交互之间需要明确区别。',claims=[('该文以普遍约束的不同排序解释英语与Seneca亲属称谓差异。','PDF第1页，Abstract；正文约束分析')]),
'A15':dict(title='Kinship Theory: A Paradigm Shift',authors=['Dwight W. Read'],year=2007,venue='Ethnology, 46(4), 329–364',url='https://escholarship.org/uc/item/93c7072g',summary='提出亲属术语具有生成逻辑，将谱系追踪与亲属术语运算视为两个需要联系的概念系统，并讨论术语系统的结构转换。',relevance='说明外部关系格网的词形合并不穷尽本土亲属概念的生成结构；模型结果适用于记录层面的词汇分类。',claims=[('亲属术语体系可以作为具有生成规则的概念系统进行分析，并与谱系关系追踪区分。','PDF第2页，论文开篇摘要性段落；第20页，TWO CONCEPTUAL SYSTEMS')]),
'A16':dict(title='Kin Term Patterns and Language Families',authors=['Vladimir Pericliev'],year=2017,summary='利用亲属称谓模式计算区分语系，报告兄弟姐妹及涉及兄弟姐妹的亲属类别对语系归属具有较强指示作用。',relevance='为按语系分组验证提供亲属称谓领域的直接背景；不能把同一语系的语言当作完全独立重复。',claims=[('兄弟姐妹及兄弟姐妹子女、姻亲模式对语言语系归属具有较强指示作用。','PDF第1页，Abstract；第9—10页，计算结果讨论')]),
'A17':dict(title='Issues in the Classification of Kinship Terminologies: Toward a New Typology',authors=['David B. Kronenfeld'],year=2006,venue='Anthropos, 101(1), 203–219',url='https://escholarship.org/uc/item/99s7r1fz',summary='区分亲属术语的语义、语用和类型学分析层面，提出元类型学讨论，阐明词项、形态成分和可选修饰词可能承担相同关系区分。',relevance='直接解释严格词形相同标准与底层语义组织可能错位的问题，可用于设计词形匹配敏感性分析。',claims=[('英语以不同词项区分兄弟姐妹，西班牙语使用共同词干加性别后缀，Fanti可用通用性别修饰词。','PDF第15页，原刊第216页：English uses different lexemes段落'),('该文总结的是元类型学讨论，而非提出已经完成的单一新分类体系。','PDF第16页，原刊第217页：Conclusion')]),
'A18':dict(title='Kin Against Kin: Internal Co-selection and the Coherence of Kinship Typologies',year=2021,summary='通过Kinbank研究经典亲属类型的内部一致性，发现跨参照者与父母两代的类型预测有限，同时使用成对词形相似、聚类与降维展示亲属系统的连续变化。',relevance='是类别对与系统相依性方面最直接的前期工作；本研究应把贡献限定为传统相对性别之后的分组样本外增益。',claims=[('父母代和参照者代的经典类型并不高度一致，跨代类型预测有限。','PDF第1页，Abstract；第8—9页，Generational类型表与讨论'),('文章用受限Damerau–Levenshtein的OSA相似度衡量类别对，并以cugino/cugina说明形态性别差异。','PDF第13页，原刊第188页：Optimal String Alignment段落'),('兄弟姐妹相对年龄区分可与平行堂表亲相对年龄区分出现共同选择。','PDF第15页，原刊第190页，Interpreting the Kinship Space')]),
'A19':dict(title='Unthinkable Categories and the Fundamental Laws of Kinship',authors=['Per Hage'],year=1997,summary='摘要以认知语言学、图论及演化视角重新解释在经典分类中未观测到的亲属体系，并强调析取类别约束。',relevance='为传统合并限制提供理论背景；统计交互应与已有类别结构约束相对照。',claims=[('该文摘要以析取类别约束和图论视角讨论经典类型中的未实现体系。','出版商原摘要，Crossref元数据')]),
'A20':dict(title='Sibling Terminology and Cross-Sex Behavior: Data from the Southeastern Nuba Mountains',authors=['James C. Faris'],year=1969,summary='摘要报告东南Nuba兄弟姐妹称谓具有主要说话者性别成分且保持合取性，用该材料讨论Nerlove与Romney的部分假设。',relevance='为参照者性别的经验重要性提供经典例证，也说明传统类型学条件需要结合真实语言材料评价。',claims=[('东南Nuba材料的兄弟姐妹体系具有主要说话者性别成分且是合取性的。','出版商原摘要，Crossref元数据')])
}
records=[]
for id,m in manual.items():
 acq=json.loads((notes/(id+'_acquisition.json')).read_text())
 cp=notes/(id+'_crossref.json');cr=json.loads(cp.read_text()) if cp.exists() else {}
 authors=m.get('authors') or [' '.join([a.get('given',''),a.get('family','')]).strip() for a in cr.get('author',[])]
 abstract=html.unescape(re.sub('<[^>]+>',' ',cr.get('abstract',''))).strip();abstract=re.sub(r'\s+',' ',abstract)
 if not abstract:
  op=notes/('openalex_'+str(acq.get('doi')).replace('/','_')+'.json')
  if op.exists():
   oa=json.loads(op.read_text());idx=oa.get('abstract_inverted_index')
   if idx:
    pairs=sorted((pos,word) for word,positions in idx.items() for pos in positions);abstract=' '.join(word for pos,word in pairs)
    abstract_source='https://api.openalex.org/works/https://doi.org/'+acq['doi']
 else:abstract_source='https://api.crossref.org/works/'+str(acq['doi'])
 abstract_path=None
 if abstract:
  abstract_path=str(notes/(id+'_abstract.txt'))
  pathlib.Path(abstract_path).write_text('Source: '+abstract_source+'\nAccessed: 2026-10-14\n\n'+abstract+'\n',encoding='utf-8')
 access=acq['access_level']
 if access=='unavailable':access='abstract_only' if abstract else 'metadata_only'
 doi=acq.get('doi')
 if id=='A16':doi='10.11649/cs.1374'
 venue=m.get('venue')
 if not venue:
  venue=(cr.get('container-title') or [''])[0]
  if cr.get('volume'):venue+=', '+cr['volume']
  if cr.get('issue'):venue+='('+cr['issue']+')'
  if cr.get('page'):venue+=', '+cr['page']
 r=dict(id=id,title=m['title'],authors=authors,year=m['year'],venue=venue,doi=doi,url=m.get('url') or 'https://doi.org/'+str(doi),pdf_url=acq.get('pdf_url'),pdf_path=acq.get('pdf_path'),access_level=access,abstract_path=abstract_path,abstract_url=abstract_source if abstract else None,download_attempts=acq['download_attempts'],summary_zh=m['summary'],relevance_zh=m['relevance'],evidence_claims=[{'claim_zh':x,'locator':y} for x,y in m['claims']],notes=[],eligible_read=access in ['pdf_fulltext','html_fulltext','abstract_only'],retrieved_at='2026-10-14',fulltext_path=str(notes/(id+'_fulltext.txt')) if acq.get('pdf_path') else None)
 if cr:r['metadata_source']='https://api.crossref.org/works/'+str(doi)
 if id in ['A03','A04']:r['notes'].append('出版商把论文开篇段落放在摘要字段；仅据该可见首段引述，不把它当作全文研究结果摘要。')
 if id=='A05':r['notes'].append('原文与原摘要均未取得；不计入已阅读文献数。页码165–208由后续论文参考文献及HRAF核实。');r['venue']='Ethnology, 9(2), 165–208'
 if id=='A08':r['notes'].append('公共领域历史专著。所下载卷册封面及Smithsonian档案为1871；卷内目录记该单篇于1870年6月出版，常用引用年份1871。仅阅读与研究有关的前言及关系表，未宣称精读656页全书。')
 if id=='A12':r['notes'].append('2019年先行网络发表，2020年正式卷期12(2),744–765；本记录统一采用正式卷期年份2020。');r['venue']='Topics in Cognitive Science, 12(2), 744–765'
 if id=='A16':r['notes'].append('Crossref标题末词误录为familie；PDF原题与正文确认families。')
 if id=='A18':r['notes'].append('已读取正文；其类别对相似度及系统内部共同选择是本研究的直接对照文献。')
 if acq.get('pdf_path'):
  pdf=pathlib.Path(acq['pdf_path']);r['sha256']=hashlib.sha256(pdf.read_bytes()).hexdigest()
 records.append(r)
(notes/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
for r in records:print(r['id'],r['year'],r['access_level'],len(r['authors']),r['title'])
print('eligible',sum(r['eligible_read'] for r in records),'pdf',sum(r['access_level']=='pdf_fulltext' for r in records))
