from pathlib import Path
import json, re, html, hashlib, csv
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
records=[]
for group in ['A','B','C']:
    records+=json.loads((ROOT/'literature'/group/'records.json').read_text())
for r in records:
    r['formal_counted']=r.get('eligible_formal_read',r.get('access_level')!='metadata_only')
    r['supplementary_preview']=r.get('material_type')=='publisher_intro_preview'
formal=[r for r in records if r['formal_counted']]
previews=[r for r in records if r['supplementary_preview']]
excluded=[r for r in records if not r['formal_counted'] and not r['supplementary_preview']]
assert len(formal)==45
pdfs=[r for r in formal if r.get('pdf_path')]
assert len(pdfs)==40
assert len(set((r.get('doi') or r['title']).lower() for r in records))==len(records)
for r in pdfs:
    p=Path(r['pdf_path']);assert p.read_bytes()[:5]==b'%PDF-'
    r['pdf_sha256_confirmed']=hashlib.sha256(p.read_bytes()).hexdigest()
def clean(s):return html.unescape(str(s)).strip()
def bib(r):
    venue=clean(r['venue'])
    if r['id'][0]!='A':
        parts=[]
        if r.get('volume'):parts.append(str(r['volume'])+('('+str(r['issue'])+')' if r.get('issue') else ''))
        if r.get('pages'):parts.append(str(r['pages']))
        elif r.get('article_number'):parts.append(str(r['article_number']))
        if parts:venue+=', '+', '.join(parts)
    link='https://doi.org/'+r['doi'] if r.get('doi') else r['url']
    author=', '.join(clean(a) for a in r['authors'])
    return f"[{r['id']}] {author}（{r['year']}）. *{clean(r['title'])}*. {venue}. [原始来源]({link})。"
def access(r):
    if r['supplementary_preview']:return '出版商首段预览；不计正式全文／摘要阅读'
    if r['access_level']=='metadata_only':return '仅书目信息；不计入实质性阅读'
    if r.get('pdf_path'):
        level=r['access_level']
        if 'preprint' in level:return '作者预印本PDF＋正式全文XML'
        if 'manuscript' in level:return '作者全文稿PDF'
        if 'early_view' in level:return '在线先行排版PDF'
        if r['id']=='C12':return '对应2007工作论文PDF；书目为2008正式论文'
        if r['id']=='A08':return '公共领域专著PDF；定向阅读相关章节'
        return 'PDF全文'
    return '真实摘要；未获得PDF'
def portable(r):
    q=dict(r)
    for k,v in list(q.items()):
        if isinstance(v,str) and v.startswith(str(ROOT)+'/'):q[k]=str(Path(v).relative_to(ROOT))
    return q
(OUT/'文献登记表.json').write_text(json.dumps([portable(r) for r in records],ensure_ascii=False,indent=2))
with (OUT/'文献登记表.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['编号','作者','年份','题名','来源','DOI','获取方式','PDF路径','摘要路径','计入45份'])
    w.writeheader()
    for r in records:
        q=portable(r);w.writerow({'编号':r['id'],'作者':'; '.join(r['authors']),'年份':r['year'],'题名':clean(r['title']),'来源':clean(r['venue']),'DOI':r.get('doi') or '', '获取方式':access(r),'PDF路径':q.get('pdf_path') or '', '摘要路径':q.get('abstract_path') or '', '计入45份':'是' if r['formal_counted'] else '否'})
bibliography='\n\n'.join(bib(r) for r in formal)+'\n\n### 补充历史资料：首段预览\n\n以下两项保留为历史脉络资料，未计入45份全文／真实摘要文献。\n\n'+'\n\n'.join(bib(r)+' '+access(r)+'。' for r in previews)
for name in ['研究计划_完善版.md','论文_中文实证稿.md']:
    p=OUT/name;s=p.read_text();s=s.replace('<!-- BIBLIOGRAPHY -->',bibliography)
    s=s.replace('Evans、Read及相关形式研究','Jones、Read及相关形式研究')
    s=s.replace('../analysis/seven_cells.png','../analysis/seven_cell_fit.png').replace('../analysis/sensitivity_gains.png','../analysis/robustness_gain.png')
    if name=='研究计划_完善版.md':
        s=s.replace('完成标准为：实质性相关的可核验文献不少于40份；','完成标准为：实质性相关的可核验文献不少于40份；')
        s=s.replace('## 参考文献','## 十四、本次执行记录\n\n本次已完成45份正式可计入的文献阅读，其中40份取得PDF全文（含作者稿、预印稿或对应工作论文），5份取得真实摘要；另保存2份历史首段预览和1份仅书目资料，不将其计入45份。文献下载状态和版本差异均有记录。\n\n数据协议在共享结果生成前固定；实际主分析包含939个完整语言记录系统、125个谱系组、26,292个类别对，全部135次拟合收敛。主设定完整交互相对原始加性增益0.004423，95%谱系区间[-0.000510, 0.008205]；相对经典加性增益0.001843，区间[-0.000604, 0.006120]。全部预设变体及独立复算已完成，结果见中文论文和执行报告。\n\n## 参考文献')
    p.write_text(s)
# 每份资料有可复查的书目、获取方式和有限论点。
lines=['# 文献综述与证据台账','', '检索与核验日期：2026年10月14日。本次采用围绕明确研究问题的定向文献综述与参考文献追踪；不是宣称穷尽全部数据库的系统综述。通过期刊、机构／作者存档、Crossref、OpenAlex与公开仓库核验资料。目标组别为经典亲属分类、亲属与一般语义理论、统计与数据方法。不同版本、补充材料和数据库网页不重复计作文献。','',
       '**正式计入45份：** 亲属文献17份、语义文献16份、方法文献12份。40份取得PDF，5份使用真实摘要；2份出版商首段预览及1份仅书目资料另列。全文下载并不表示逐页精读；每份资料按本研究相关章节／摘要定向阅读，下面记录可引用论点与定位。','',
       '| 组别 | 正式文献数 | PDF全文 | 真实摘要 | 补充首段 | 仅书目 |','|---|---:|---:|---:|---:|---:|','| A 亲属类型学与历史 | 17 | 12 | 5 | 2 | 1 |','| B 语义范畴与效率 | 16 | 16 | 0 | 0 | 0 |','| C 统计与数据方法 | 12 | 12 | 0 | 0 | 0 |','| 合计 | 45 | 40 | 5 | 2 | 1 |','']
for group,label in [('A','亲属分类、系统结构与历史'),('B','语义范畴、效率与学习'),('C','统计推断、验证与数据规范')]:
    lines+=['## '+label,'']
    for r in [x for x in records if x['id'].startswith(group)]:
        lines+=['### '+r['id']+' '+clean(r['title']),'',bib(r),'','**获取方式：** '+access(r)+'。']
        if r.get('pdf_path'):lines+=['','[打开所获PDF](../'+str(Path(r['pdf_path']).relative_to(ROOT))+')。']
        if r.get('abstract_path'):lines+=['','[核对所保存摘要／可见首段](../'+str(Path(r['abstract_path']).relative_to(ROOT))+')。摘要来源：['+('元数据或原始来源')+']('+r['abstract_url']+')。']
        lines+=['','**阅读摘要：** '+clean(r['summary_zh']),'','**研究关联：** '+clean(r['relevance_zh']),'']
        for claim in r.get('evidence_claims',[]):
            if isinstance(claim,dict):lines+=['- '+clean(claim.get('claim_zh',claim.get('claim','')))+'（定位：'+clean(claim.get('locator','资料所示位置'))+'）。']
            else:lines+=['- '+clean(claim)]
        notes=r.get('notes',[])
        if isinstance(notes,str):notes=[notes]
        if notes:lines+=['','**版本／核验说明：** '+'；'.join(clean(n) for n in notes)+'。']
        lines+=['']
# 合并每组主题综述，保留原有来源编号。
lines+=['## 主题综合','']
for group in ['A','B','C']:
    p=ROOT/'notes'/group/'review_zh.md'
    if p.exists():
        t=p.read_text();t=re.sub(r'^# ', '### ',t,flags=re.M);t=re.sub(r'^## ', '#### ',t,flags=re.M)
        if group=='A':t=t.replace('19份可计入已读文献','19份可按摘要字段／首段定向阅读；其中17份计入正式全文或真实摘要数量')
        lines+=[t,'']
(OUT/'文献综述与证据台账.md').write_text('\n'.join(lines))
# PDF未获取清单，摘要与正式版差异分别列示。
fail=['# PDF无法下载及版本替代清单','', '检索日期：2026年10月14日。共40项取得可核对题名的PDF；作者稿、预印本和工作论文按相同著作计一项，不另增文献。以下记录实际未取得的PDF，下载失败说明只针对本次访问，未据此判断资料在其他渠道不可获取。','',
      '## 一、未获得任何PDF：以真实摘要引用的5项','', '| 编号 | 文献 | 真实摘要来源 | 本次获取状态 |','|---|---|---|---|']
for r in formal:
    if r.get('pdf_path'):continue
    attempts=r['download_attempts'];last='；'.join(clean(a.get('status','')) for a in attempts[-3:])
    fail.append(f"| {r['id']} | {clean(r['title'])}（{r['year']}） | [核验摘要]({r['abstract_url']}) | {last.replace('|','/')} |")
fail+=['','以上资料仅用于摘要实际报告的研究目标、传统结构或总体发现；未从摘要编造详细方法、效应值或正文页码。各项原始摘要保存在资料包中。','',
       '## 二、补充历史资料：未获得全文和正式摘要','', '| 编号 | 文献 | 实际所获材料 | 纳入方式 |','|---|---|---|---|']
for r in previews+excluded:
    fail.append(f"| {r['id']} | {clean(r['title'])}（{r['year']}） | {access(r)} | {'历史脉络补充，未计入45份' if r['supplementary_preview'] else '仅供后续查找，未进入正式论文参考文献'} |")
fail+=['','Goodenough与Lounsbury条目中，出版商摘要字段提供的是论文开篇预览；本次明确按首段处理，不将其计为完整研究摘要。','',
       '## 三、正式排版PDF未取得，已取得替代全文','',
       '| 编号 | 正式论文 | 正式PDF尝试 | 实际使用版本 |','|---|---|---|---|',
       '| B03 | Hallam等（2025），Predictive Structure Emerges During the Generalisation of Kin Terms to New Referents | 出版社／机构入口403，PMC入口验证页面；完整尝试见登记表 | 作者预印本PDF、正式期刊全文XML及正式摘要；文中731语言及实验结论据正式全文 |',
       '| C12 | Cameron、Gelbach与Miller（2008），Bootstrap-Based Improvements for Inference with Clustered Errors | MIT正式版入口403；作者链接核查后发现旧链接指向其他题名，未计入 | 对应2007年NBER工作论文t0344；参考文献指向2008年正式发表版，并保留版本差异 |','',
       'B05、B07、B12为作者全文稿，B10、B16为在线先行排版；这些版本已取得完整PDF，逐项版本标识见登记表。数据库、会议早期稿和补充材料不重复计入文献数量。','',
       '## 四、逐项下载尝试','']
for r in records:
    if r.get('pdf_path') and r['id'] not in ['B03','C12']:continue
    fail+=['### '+r['id'],'',bib(r),'']
    for a in r['download_attempts']:
        fail+=['- ['+clean(a.get('url','来源'))+']('+a.get('url','')+')：'+clean(a.get('status','已记录'))+'。']
    fail+=['']
(OUT/'PDF无法下载清单.md').write_text('\n'.join(fail))
# 正文实测表。
r=json.loads((ROOT/'analysis/results.json').read_text());a=r['analyses'][0]
cell=['| 差异组合（所指／年龄／参照者） | 类别对数 | 实测共享率 | 原始加性预测 | 经典加性预测 | 交互预测 |','|---|---:|---:|---:|---:|---:|']
for x in r['seven_cells']:cell.append(f"| {x['pattern']} | {x['n_pairs']:,} | {100*x['share_rate']:.2f}% | {x['p_raw_additive_ridge']:.4f} | {x['p_classical_additive_ridge']:.4f} | {x['p_pairwise_ridge']:.4f} |")
main=['| 模型 | 可识别参数数 | 语言等权对数损失 | Brier分数 |','|---|---:|---:|---:|']
for m,n,label in [('raw_additive',4,'原始加性'),('classical_additive',5,'经典加性'),('pairwise',7,'完整两两交互')]:main.append(f"| {label} | {n} | {a['language_equal_logloss'][m]:.6f} | {a['language_equal_brier'][m]:.6f} |")
names={'primary':'主分析','coverage75':'至少75%覆盖','equal_sets':'词形集合完全相同','singleton_only':'每类仅一词形','single_source':'单一文献来源','C0.1':'C=0.1','C10':'C=10','unpenalized':'无惩罚'}
sens=['| 条件 | 语言数 | 原始增益 | 原始增益95%区间 | 经典剩余增益 | 剩余增益95%区间 |','|---|---:|---:|---|---:|---|']
for x in r['analyses']:
    if x['cv_grouping']!='family':continue
    c=x['comparisons'];dr=c['raw'];dc=c['classical']
    fmt=lambda t:f"[{t[0]:.6f}, {t[1]:.6f}]"
    sens.append(f"| {names[x['variant']]} | {x['languages']} | {dr['language_equal_gain']:.6f} | {fmt(dr['family_cluster_bootstrap_95ci'])} | {dc['language_equal_gain']:.6f} | {fmt(dc['family_cluster_bootstrap_95ci'])} |")
p=OUT/'论文_中文实证稿.md';s=p.read_text().replace('<!-- CELL_TABLE -->','\n'.join(cell)).replace('<!-- MAIN_TABLE -->','\n'.join(main)).replace('<!-- SENSITIVITY_TABLE -->','\n'.join(sens));p.write_text(s)
print(json.dumps({'formal_literature':len(formal),'pdfs':len(pdfs),'real_abstract_only':len(formal)-len(pdfs),'supplementary_previews':len(previews),'excluded_metadata':len(excluded)},ensure_ascii=False))
