"""根据当前全文登记表幂等更新书目、证据台账及排除清单，不修改统计结果。"""
from pathlib import Path
import json,re,html,csv,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
def clean(s):return html.unescape(str(s)).strip()
def fullpath(s):return ROOT/str(s)
def bib(r):
    venue=clean(r['venue'])
    if not r['id'].startswith('A'):
        v=str(r.get('volume') or '')
        if r.get('issue'):v+='('+str(r['issue'])+')'
        rest=[v] if v else []
        loc=r.get('pages') or r.get('article_number')
        if loc:rest.append(str(loc))
        if rest:venue+=', '+', '.join(rest)
    url='https://doi.org/'+r['doi'] if r.get('doi') else r['url']
    return f"[{r['id']}] {', '.join(clean(a) for a in r['authors'])}（{r['year']}）. *{clean(r['title'])}*. {venue}. [原始来源]({url})。"
def access(r):
    if r.get('citation_status')=='excluded_no_fulltext':return '未取得全文，排除引用'
    if r.get('pdf_source')=='user_uploaded':return '用户提供的正式PDF全文'
    level=r.get('access_level','')
    if 'manuscript' in level:return '作者全文稿PDF'
    if 'early_view' in level:return '在线先行排版PDF'
    if r['id']=='A08':return '公共领域专著PDF；定向阅读相关章节'
    return 'PDF全文'
def main():
    records=[]
    for g in 'ABC':records+=json.loads((ROOT/'literature'/g/'records.json').read_text())
    formal=[r for r in records if r.get('citation_status')=='included_fulltext']
    excluded=[r for r in records if r not in formal]
    assert len(formal)>=40
    for r in formal:
        p=fullpath(r['pdf_path']);assert p.read_bytes()[:5]==b'%PDF-'
        assert fullpath(r['txt_path']).exists()
        r['pdf_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        r['formal_counted']=True
    for r in excluded:r['formal_counted']=False
    (OUT/'文献登记表.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    with (OUT/'文献登记表.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['编号','作者','年份','题名','来源','DOI','获取方式','PDF路径','TXT路径','纳入正式引用']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in records:w.writerow(dict(zip(fields,[r['id'],'; '.join(r['authors']),r['year'],clean(r['title']),clean(r['venue']),r.get('doi') or '',access(r),r.get('pdf_path') or '',r.get('txt_path') or '', '是' if r['formal_counted'] else '否'])))
    bibliography='\n\n'.join(bib(r) for r in formal)
    for name in ['研究计划_完善版.md','论文_中文实证稿.md']:
        p=OUT/name;body=p.read_text().split('\n## 参考文献')[0].rstrip()
        p.write_text(body+'\n\n## 参考文献\n\n当前正式参考文献仅包含已取得全文的'+str(len(formal))+'项独立著作，编号与登记表一致。\n\n'+bibliography+'\n')
    lines=['# 文献综述与证据台账','','更新日期：2026年10月15日。本轮按用户要求只引用已经取得全文的文献。当前正式文献'+str(len(formal))+'项，均保存PDF和同名TXT；其余2项只进入排除记录。早期稿和补充材料不重复计数。定向阅读范围与证据位置逐项列出，全文文件齐备不表示已经逐页精读。','','| 组别 | 正式引用 | 主要PDF全文 | 仅摘要引用 |','|---|---:|---:|---:|']
    for g,label in [('A','亲属分类与历史'),('B','语义范畴与效率'),('C','统计与数据方法')]:
        n=sum(r['id'].startswith(g) for r in formal);lines.append(f'| {g} {label} | {n} | {n} | 0 |')
    lines+=['', '全部源PDF的逐页文本、历史版本与补充文件见[TXT索引](../literature/TXT索引.md)。低文本页的OCR状态见[转换报告](../literature/pdf_text_conversion_report.json)。','']
    for g,label in [('A','亲属分类、系统结构与历史'),('B','语义范畴、效率与学习'),('C','统计推断、验证与数据规范')]:
        lines+=['## '+label,'']
        for r in [r for r in formal if r['id'].startswith(g)]:
            lines+=['### '+r['id']+' '+clean(r['title']),'',bib(r),'','**当前来源：** '+access(r)+'。','','[PDF](../'+r['pdf_path']+')｜[TXT](../'+r['txt_path']+')','','**定向阅读摘要：** '+clean(r['summary_zh']),'','**研究关联：** '+clean(r['relevance_zh']),'']
            for e in r.get('evidence_claims',[]):
                if isinstance(e,dict):lines.append('- '+clean(e.get('claim_zh',e.get('claim','')))+'（'+clean(e.get('locator','正文对应段落'))+'）。')
                else:lines.append('- '+clean(e))
            notes=r.get('notes',[])
            if isinstance(notes,str):notes=[notes]
            if notes:lines+=['','**版本说明：** '+'；'.join(notes)+'。']
            lines+=['']
    lines+=['## 全文补充后的理论关系','','Goodenough的替代概念模型讨论[A03]、Lounsbury的显性／隐性特征表达[A04]，使特征编码和词形分段之间的区别具有直接原文依据。Kronenfeld[A06]分别讨论八类别位置、相对性别特征、合取性与重叠词项；Faris[A20]说明条件性性别区分及多义分析如何改变初看之下的分类结构。Hage的标记性和类别结构研究[A07、A19]提供进一步的先行约束。它们支持把本研究定位为明确的预测基准比较，而非首次发现语义组合。','','Hallam等正式版[B03]及Cameron等正式版[C12]已经由用户提供。相应先前版本仅保留为历史材料；当前页码引用以正式版为准。C12的bootstrap-t及OLS结论不自动证明本项目固定折外预测百分位区间的性质。','','## 排除记录','','以下项目未取得全文，已从计划、论文和正式参考文献中移除；仅为防止误纳入而保留编号。','','| 编号 | 资料名称 | 当前处理 |','|---|---|---|']
    for r in excluded:lines.append(f"| {r['id']} | {r['authors'][0]}（{r['year']}），{clean(r['title'])} | 未取得全文，不引用 |")
    (OUT/'文献综述与证据台账.md').write_text('\n'.join(lines)+'\n')
    manifest=json.loads((ROOT/'literature/uploaded_pdf_manifest.json').read_text())
    fail=['# 全文补充、版本更新与未纳入引用清单','','更新日期：2026年10月15日。正式引用仅纳入46项已取得全文的文献。以下两项仍缺少全文，已排除引用；不再以摘要或书目替代正式引用。','','## 仍未取得全文：不引用','','| 编号 | 资料 | 处理 |','|---|---|---|']
    for r in excluded:fail.append(f"| {r['id']} | {r['authors'][0]}（{r['year']}），{clean(r['title'])} | 未取得全文；排除计划、论文及正式参考文献 |")
    fail+=['','## 本轮8份用户提供PDF','','| 编号 | 原文件名 | 规范化文件 | 当前状态 |','|---|---|---|---|']
    lookup={r['id']:r for r in formal}
    for m in manifest['files']:
        r=lookup[m['id']];fail.append(f"| {m['id']} | {m['original_filename']} | [PDF](../{r['pdf_path']})｜[TXT](../{r['txt_path']}) | 正式全文已补齐 |")
    fail+=['','Goodenough、Lounsbury已由首段预览升级为正式全文；Kronenfeld、Hage两篇及Faris已由摘要升级为全文。Hallam的Open Mind论文和Cameron等论文已取得正式期刊版，旧预印稿与NBER工作论文保留在earlier_versions，不重复计数。','','## 全文与版本原则','','作者全文稿和在线先行排版仍按已取得全文记录，其具体版本见登记表。引用原题和正式书目，证据页码指向实际所读版本。未取得全文的两项资料不会出现在正式引用中；它们的旧摘要和原始元数据只属于历史检索记录。','','全部PDF均有对应TXT；OCR和低文字页的质量状态见[转换报告](../literature/pdf_text_conversion_report.json)。']
    (OUT/'PDF无法下载清单.md').write_text('\n'.join(fail)+'\n')
    lib=['# 文献库与全文入口','','正式引用46项独立著作；未取得全文的A02、A05不引用。命名采用“编号_第一作者_年份_题名”；各主要PDF同目录有同名TXT。5个早期版本或补充PDF不额外计作文献。','','[全部51个源PDF及TXT索引](TXT索引.md)｜[结构化登记表](../outputs/文献登记表.json)｜[补充与排除清单](../outputs/PDF无法下载清单.md)','','| 编号 | 文献 | PDF | TXT |','|---|---|---|---|']
    for r in formal:lib.append(f"| {r['id']} | {r['authors'][0]}（{r['year']}），{clean(r['title'])} | [PDF]({Path(r['pdf_path']).relative_to('literature').as_posix()}) | [TXT]({Path(r['txt_path']).relative_to('literature').as_posix()}) |")
    (ROOT/'literature/README.md').write_text('\n'.join(lib)+'\n')
    print(json.dumps({'formal_fulltext_references':len(formal),'excluded_no_fulltext':[r['id'] for r in excluded],'source_pdf_files':len(list((ROOT/'literature').rglob('*.pdf')))},ensure_ascii=False))
if __name__=='__main__':main()
