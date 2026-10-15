"""S2五种测量与字段级违例审查；不拟合模型，不改写冻结文件。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROTOCOL_COMMIT = '6ba7afba369d3d15446ea7571eabd2117b7e8c74'
PROTOCOL_SHA256 = '61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be'
CATEGORIES = ['meB','myB','meZ','myZ','feB','fyB','feZ','fyZ']
FIELD_REVIEW_NOTES={
 'akla1241':'逐行记录中manghod与igmánghod并存；注释空且同一来源。字符差别不构成误拼证据，不自行合并。',
 'anut1237':'原表按两种形式分布，八类均同一来源且无解释性注释；这里只违反三特征参照，不能称四特征主定义违例。',
 'area1240':'a加组合长音的规范编码会经NFC合成，原始Value与Form相同；这不证明其他不同拼写应合并。违例仅属三特征参照。',
 'auuu1241':'hei iue含空格，其他形式没有同一空格结构；没有注释说明词界或语义组成，故不标为已确认描述短语。',
 'awap1236':'八类单词形在不同参照者／年龄位置分布不一；来源一致、注释空，无法仅凭形式排除来源或编码问题。',
 'baca1243':'dantjanak jang toeana、dantjanak laki、dantjanak bini均含空格；没有注释证明其词素或修饰关系，保留机械空格线索。',
 'baff1241':'naʼ-yǎ与na-yǎʼ的符号位置不同；只记录原始字符串差异，不推断是异写、拼写错误或真实年龄区别。',
 'baro1253':'rok与sagok的八格记录同源、注释空；程序违例属于三特征参照，缺少原来源语境不能确认语义反例。',
 'bign1238':'tivalök nöngk含空格而tivalök不含；未有注释解释两者关系，不把形式包含关系自动标为形态或描述构式。',
 'blag1240':'-kaku与-edi的前导连字符保留；它们不等于单独的缺失标记“-”，不据连字符自动删除或切词。',
 'boun1245':'Comment直接写same-sex sibling与opposite-sex sibling，与相对性别记录有关；不能将缺少q的三特征参照违例误作主定义违例。',
 'buli1256':'teno taoeati与teno tawawai含空格；同一来源且无解释性注释，无法确认空格所对应的语言结构。',
 'buru1303':'kaka、wai、feta、naha按八类分布，来源统一而注释空；仅据该表不能解释差异来源。',
 'chek1238':'g加组合长音等字符按NFC处理；保留原始Value/Form和规范化后Form，未进行音系匹配或纠音。',
 'cher1273':'带组合变音和连字符的形式按原记录保留；NFC只改变规范编码，不把不同形式认作同词。',
 'chic1270':'较长形式中的字母与变音符号位置不同；没有注释允许纠错，故不凭外观接近修正原表。',
 'choc1276':'feB的a-näkʼ-fǐ与fyB的a-nakʼ-fǐ保留原差异；是否转写差异尚无字段证据，不能把去变音当作清洗。',
 'chok1245':'八类各有重复原始行，均标Inferred; NA，同源粗类背景也存在；这是明确的推断注释线索，但无法确定每格展开的具体依据。集合去重未增加词项。',
 'cogu1240':'部分注释说明unpossessed形式及same/opposite-sex；这些是来源已有说明，不把未给出的语境自动补入实际词形。',
 'copp1244':'八类来源为Damas_1975且注释空；保持全部字符串，无法依据未见异常认定原语义已获验证。',
 'umbu1257':'八行均为gibson_social_1952，Value=Form且注释空；P5不兼容是程序对该表的判定，原始语境与采集展开过程无法由这八行确认。',
 'urak1238':'ca、adi、kaka均为Hogan1988UrakLawo且注释空；没有字段直接解释参照者条件和词项范围，P5的真实语言解释仍未确认。',
 'yura1255':'pii、paa、pipi、dyama、yee、neshu均为Hirtzel2010且注释空；不因pii/pipi形式接近就合并或作叠音语义分析。'}
FIELD_REVIEW_NOTES.update({
 'dhuw1248':'八类均来自Keen2018，Value=Form而注释空；wäwa/yukuyuku/yapa的同形分布可复查，无法补推未记录的使用语境。',
 'fort1240':'toa-、tasi-、mane-、vavine-的尾连字符均原样保留；不把连接符自动解释为可删词缀，未见展开说明。',
 'imbo1238':'awahwa、abaqkawa、ayoqkawa、anahnowa、onanahwa的八类位置均同源且无注释；与其他语言形式相近不构成转写错误证据。',
 'jing1260':'phù带组合声调而naw不带；NFC正规化不删声调，单一来源KurabePC未附词项范围说明。',
 'lard1243':'meZ/myZ的Comment含bunjikarnan = honorific，记录形式仍为kuu；保留来源已有语体线索，不人工划分礼貌语义。',
 'luba1250':'myB/fyB的nkasa各有Jenniges与Yukawa两条来源记录，去重后仍为单词形；没有字段证明其他格应补入同义词。',
 'maba1278':'rimori tamoni与rimori mpinte含空格，其余有tenoe/remo；只记录完整形式和空格，不据外观作词素或描述构式标注。',
 'mand1446':'所有八类均来自Morgan1871，连字符与撇号保留；无注释说明异写或推广，不能把相似片段自行合并。',
 'nali1244':'meZ/myZ的dimafingu被Comment标为taboo，其余多为diagu；这是来源已有使用限制线索，不能据此单独改写称谓类别。',
 'nese1235':'tua-、tas-、jokhos-的尾连接符保留，来源Nese2006且注释空；不推断其必需词缀或补全形式。',
 'ngal1292':'meZ的来源注释明确建议标address term，并描述该用法；因此存在指称／称呼用法混合的字段线索，但不能单凭注释重标整个系统。',
 'nort2839':'taovjen与talang均来自rio2007a，注释空；保留八格分布，没有来源字段证明其由粗类复制。',
 'nort2961':'feZ/fyZ注释称女性说话者不按年龄区分女性同胞，而Form两格同为nimises；保留这项原文注释，不自动校正其他男性格。',
 'olal1237':'taling/maningeri均来自Lane1958且注释空；形式违例可定位，不能推断说话者条件是误录或心理机制。',
 'osag1243':'Morgan1871八格有数种带连接符与变音的形式；保持字符差别，没有记录支持音系归并。',
 'pawn1254':'a-täʼ-ke与a-täʼ-he等形式差异按原表保留；该系统四特征下违例而扩展六特征下并非同一结果，不能混称所有特征集均不合取。',
 'rovi1238':'tasi-na和vavene-na同源、注释空；仅凭共同后缀外观不做新增形态切分。',
 'sons1242':'keinapa、widi、meaŋa-i同源、注释空；保留各类形式，不据共同串推断另一个未记录类别。',
 'umpi1239':'全部八类Comment为Autofilled from CB Austkin data，确认存在上游自动填入注释；不能由此确定每格是粗类别展开或判断原语义错误。',
 'yomb1244':'女性／男性姐妹相关行有Inferred; NA注释，其他行注释空；确认推断标记存在，不把它直接判作已证实的粗类展开。'})


def normalize(value):
    return ' '.join(unicodedata.normalize('NFC',str(value)).split())


def protocol_gate():
    protocol = HERE/'protocol_s2.md'
    observed = hashlib.sha256(protocol.read_bytes()).hexdigest()
    if observed != PROTOCOL_SHA256:
        raise RuntimeError('最终协议SHA-256不符，停止测量。')
    committed = subprocess.check_output(['git','show',f'{PROTOCOL_COMMIT}:analysis/supplementary_s2/protocol_s2.md'],cwd=ROOT)
    if hashlib.sha256(committed).hexdigest()!=PROTOCOL_SHA256:
        raise RuntimeError('最终协议提交对象与约定校验值不符。')
    commit_unix=int(subprocess.check_output(['git','show','-s','--format=%ct',PROTOCOL_COMMIT],cwd=ROOT,text=True).strip())
    if Path(__file__).stat().st_mtime < commit_unix:
        raise RuntimeError('测量脚本时间早于最终协议提交。')
    return {'protocol_commit':PROTOCOL_COMMIT,'protocol_sha256':observed,
            'protocol_commit_time_utc':dt.datetime.fromtimestamp(commit_unix,dt.timezone.utc).isoformat()}


def load_measurement_data():
    """返回五定义配对表、逐系统元数据、按(Language_ID,类别)索引的形式集合。"""
    protocol_gate()
    pairs=pd.read_csv(ROOT/'analysis/pairs_primary.csv',keep_default_na=False,dtype={'pattern':str})
    cats=pd.read_csv(ROOT/'analysis/category_forms_primary.csv',keep_default_na=False)
    cats['formset']=cats.forms_json.map(lambda x:frozenset(json.loads(x)))
    forms=dict(zip(zip(cats.Language_ID,cats.Parameter_ID),cats.formset))
    keys=['Language_ID','Glottocode','Name','family_group','family_name','family_status','Macroarea']
    metadata=pairs[keys].drop_duplicates().reset_index(drop=True)
    if len(metadata)!=939 or metadata.Language_ID.nunique()!=939 or metadata.Glottocode.nunique()!=939:
        raise RuntimeError('主系统表不匹配939个唯一记录系统。')
    if pairs.family_group.nunique()!=125 or len(pairs)!=26292:
        raise RuntimeError('旧主样本规模不符。')
    metadata=metadata.rename(columns={'Macroarea':'Macroarea_original'})
    metadata['Macroarea_first']=metadata.Macroarea_original.map(lambda x:x.split(';')[0].strip())
    for lid in metadata.Language_ID:
        if any((lid,c) not in forms or not forms[(lid,c)] for c in CATEGORIES):
            raise RuntimeError('主样本存在缺少有效目标类别。')
    singleton={lid for lid in metadata.Language_ID if all(len(forms[(lid,c)])==1 for c in CATEGORIES)}
    spaced={lid for lid in metadata.Language_ID if any(' ' in f for c in CATEGORIES for f in forms[(lid,c)])}
    if len(singleton)!=625:raise RuntimeError('D3未重现625个系统。')
    if len(spaced)!=179:raise RuntimeError('D4未重现179个含空格系统。')
    tokens={key:frozenset(t for f in fs for t in f.split()) for key,fs in forms.items()}
    y1=[];y2=[];y5=[]
    for row in pairs.itertuples(index=False):
        fa=forms[(row.Language_ID,row.category_a)];fb=forms[(row.Language_ID,row.category_b)]
        y1.append(int(bool(fa&fb)));y2.append(int(fa==fb))
        y5.append(int(bool(tokens[(row.Language_ID,row.category_a)]&tokens[(row.Language_ID,row.category_b)])))
    if y1!=pairs.shared_form.tolist():raise RuntimeError('D1逐对未重现冻结结果。')
    if any(a>b for a,b in zip(y1,y5)):raise RuntimeError('D5机械切分不应删除D1正例。')
    pairs=pairs.merge(metadata[['Language_ID','Macroarea_original','Macroarea_first']],on='Language_ID',how='left',validate='many_to_one',sort=False)
    definitions={}
    for name,ys,subset in [('D1',y1,None),('D2',y2,None),('D3',y1,singleton),('D4',y1,set(metadata.Language_ID)-spaced),('D5',y5,None)]:
        frame=pairs.copy();frame['shared_form']=ys
        if subset is not None:frame=frame[frame.Language_ID.isin(subset)].copy()
        frame['definition']=name
        definitions[name]=frame.reset_index(drop=True)
    # 旧的两项严格定义也逐对核验，而非只核对规模。
    for name,old in [('D2','equal_sets'),('D3','singleton_only')]:
        before=pd.read_csv(ROOT/f'analysis/pairs_{old}.csv',dtype={'pattern':str})
        key=['Language_ID','category_a','category_b']
        joined=definitions[name].merge(before[key+['shared_form']],on=key,suffixes=('_new','_old'),validate='one_to_one')
        if len(joined)!=len(before) or len(joined)!=len(definitions[name]) or not joined.shared_form_new.eq(joined.shared_form_old).all():
            raise RuntimeError(name+'未逐对复现旧严格定义。')
    return definitions,metadata,forms


def measurement_results(definitions,metadata,forms):
    tokens={key:frozenset(t for f in fs for t in f.split()) for key,fs in forms.items()}
    by_language=metadata.set_index('Language_ID').to_dict('index')
    representation=[];repeated=[];adjacent_repeated=[];changed_categories=[]
    for (lid,cat),fs in sorted(forms.items()):
        if fs!=tokens[(lid,cat)]:changed_categories.append({'Language_ID':lid,'Glottocode':by_language[lid]['Glottocode'],'Parameter_ID':cat,'forms':sorted(fs),'tokens':sorted(tokens[(lid,cat)])})
        for form in sorted(fs):
            ts=form.split()
            entry={'Language_ID':lid,'Glottocode':by_language[lid]['Glottocode'],'Parameter_ID':cat,'form':form,'tokens':ts}
            if ts!=[form]:representation.append(entry)
            if len(set(ts))<len(ts):repeated.append(entry)
            if any(x==y for x,y in zip(ts,ts[1:])):adjacent_repeated.append(entry)
    rep_lids={x['Language_ID'] for x in repeated}
    adjacent_rep_lids={x['Language_ID'] for x in adjacent_repeated}
    repeated_keys={(x['Language_ID'],x['Parameter_ID']) for x in repeated}
    changed=[]
    for a,b in zip(definitions['D1'].itertuples(index=False),definitions['D5'].itertuples(index=False)):
        if a.shared_form==b.shared_form:continue
        fa=forms[(a.Language_ID,a.category_a)];fb=forms[(a.Language_ID,a.category_b)]
        ta=tokens[(a.Language_ID,a.category_a)];tb=tokens[(a.Language_ID,a.category_b)]
        changed.append({'Language_ID':a.Language_ID,'Glottocode':a.Glottocode,'family_group':a.family_group,
                        'Macroarea_original':a.Macroarea_original,'Macroarea_first':a.Macroarea_first,
                        'category_a':a.category_a,'category_b':a.category_b,'D1':int(a.shared_form),'D5':int(b.shared_form),
                        'forms_a':sorted(fa),'forms_b':sorted(fb),'tokens_a':sorted(ta),'tokens_b':sorted(tb),
                        'common_tokens':sorted(ta&tb),
                        'system_has_repeated_tokens':a.Language_ID in rep_lids,
                        'either_endpoint_has_repeated_tokens':(a.Language_ID,a.category_a) in repeated_keys or (a.Language_ID,a.category_b) in repeated_keys})
    changed_lids={r['Language_ID'] for r in changed}
    definition_counts={}
    baseline=definitions['D1'].set_index(['Language_ID','category_a','category_b']).shared_form
    for name,frame in definitions.items():
        compare=frame.shared_form.to_numpy()!=baseline.reindex(pd.MultiIndex.from_frame(frame[['Language_ID','category_a','category_b']])).to_numpy()
        definition_counts[name]={'systems':int(frame.Language_ID.nunique()),'genealogical_groups':int(frame.family_group.nunique()),
                                  'pairs':len(frame),'shared_pairs':int(frame.shared_form.sum()),
                                  'outcome_changes_from_D1_on_retained_pairs':int(compare.sum()),
                                  'systems_with_outcome_changes_from_D1':int(frame.loc[compare,'Language_ID'].nunique()),
                                  'systems_excluded_from_D1':int(939-frame.Language_ID.nunique()),
                                  'macroareas_first':frame[['Language_ID','Macroarea_first']].drop_duplicates().Macroarea_first.value_counts().to_dict()}
    multi=metadata[metadata.Macroarea_original.str.contains(';',regex=False)]
    missing=metadata[metadata.Macroarea_first.eq('')]
    cross=[]
    for group,frame in metadata.groupby('family_group'):
        areas=frame.loc[frame.Macroarea_first.ne(''),'Macroarea_first'].value_counts().to_dict()
        if len(areas)>1:cross.append({'family_group':group,'family_name':frame.family_name.iloc[0],'systems':len(frame),
                                    'systems_by_known_macroarea':areas,'systems_missing_macroarea':int(frame.Macroarea_first.eq('').sum())})
    old=json.loads((ROOT/'analysis/forum_descriptives.json').read_text())['multiword_forms']
    if len(representation)!=old['forms_with_space']:raise RuntimeError('形式拆分数未重现旧含空格计数。')
    examples=[]
    for lid in ['v_standardfrenchstan1290','v_standardspanishstan1288','v_mandarinchinamand1415']:
        if lid not in by_language:continue
        examples.append({'Language_ID':lid,'Name':by_language[lid]['Name'],'has_repeated_tokens':lid in rep_lids,
                         'form_occurrences_tokenized':sum(r['Language_ID']==lid for r in representation),
                         'D1_to_D5_pair_changes':sum(r['Language_ID']==lid for r in changed),
                         'changed_dyads':[r for r in changed if r['Language_ID']==lid]})
    return {
        'definitions':definition_counts,
        'checks':{'D1_exactly_reproduces_frozen_pair_outcomes':True,'D2_exactly_reproduces_frozen_equal_sets':True,
                  'D3_exactly_reproduces_frozen_singleton_pairs':True,'D3_systems_625':len(definitions['D3'].Language_ID.unique())==625,
                  'D4_excludes_179_systems':939-len(definitions['D4'].Language_ID.unique())==179,
                  'D5_never_changes_D1_shared_to_nonshared':True},
        'D4':{'excluded_systems':metadata[metadata.Language_ID.isin({lid for (lid,cat),fs in forms.items() if any(' ' in f for f in fs)})].to_dict('records')},
        'D5':{'interpretation':'机械空白词元共享；不等同词干、词素或语义共形。重复词元只是形式线索，不是新增的叠音语义标签。',
              'form_occurrences_before_tokenization':sum(len(forms[(lid,c)]) for lid in metadata.Language_ID for c in CATEGORIES),
              'form_occurrences_changed_by_tokenization':len(representation),
              'categories_with_formset_representation_changed':len(changed_categories),
              'systems_with_form_representation_changed':len({r['Language_ID'] for r in representation}),
              'dyad_outcome_changes':len(changed),'systems_with_dyad_outcome_changes':len(changed_lids),
              'new_shared_pairs':sum(r['D1']==0 and r['D5']==1 for r in changed),
              'lost_shared_pairs':sum(r['D1']==1 and r['D5']==0 for r in changed),
              'repeated_token_form_occurrences':len(repeated),'systems_with_repeated_token_forms':len(rep_lids),
              'repeated_token_systems_with_dyad_outcome_changes':len(rep_lids&changed_lids),
              'changed_dyads_in_repeated_token_systems':sum(r['system_has_repeated_tokens'] for r in changed),
              'changed_dyads_with_repeated_token_endpoint':sum(r['either_endpoint_has_repeated_tokens'] for r in changed),
              'repeated_token_impact_interpretation':'此处统计与重复词元记录并存的系统／端点变化，不是证明重复词元造成该变化的因果分解。',
              'adjacent_repeated_token_form_occurrences':len(adjacent_repeated),
              'systems_with_adjacent_repeated_token_forms':len(adjacent_rep_lids),
              'adjacent_repeated_token_systems_with_dyad_outcome_changes':len(adjacent_rep_lids&changed_lids),
              'adjacent_repetition_interpretation':'相邻相同词元是ge ge类叠写的机械线索；不等同经过语义标注的叠音类别。非相邻重复可来自异写并列表达。',
              'form_representation_changes':representation,'category_representation_changes':changed_categories,
              'repeated_token_records':repeated,'adjacent_repeated_token_records':adjacent_repeated,'outcome_change_records':changed,'forum_examples':examples},
        'geography':{'original_multivalue_systems':len(multi),'multivalue_records':multi.to_dict('records'),
                     'systems_with_first_value_different_from_original_string':int(metadata.Macroarea_first.ne(metadata.Macroarea_original).sum()),
                     'first_value_area_counts':metadata.Macroarea_first.value_counts().to_dict(),
                     'missing_macroarea_systems':len(missing),'missing_macroarea_records':missing.to_dict('records'),
                     'regional_validation_eligible_systems':int(metadata.Macroarea_first.ne('').sum()),
                     'nonmissing_macroarea_count':int(metadata.loc[metadata.Macroarea_first.ne(''),'Macroarea_first'].nunique()),
                     'families_spanning_multiple_first_macroareas':len(cross),'cross_macroarea_families':cross},
        'measurement_notes':['D1词形集合交集关系不保证传递性。','D2保留所有主系统，D3是单词形子样本。',
                             'D4去除空格形式不是去除已确认描述性短语。','D5可因mayor等修饰词共享增加阳性，不能称恢复亲属词干。']}


def split_sources(value):
    return [re.sub(r'\[[^\]]*\]','',s).strip() for s in value.split(';') if re.sub(r'\[[^\]]*\]','',s).strip()]


def build_violation_audit(metadata,posthoc_primary=False):
    violation_file=HERE/'s2_violations.csv'
    if not violation_file.exists():raise RuntimeError('尚无s2_violations.csv，不能声称已完成违例抽查。')
    violations=pd.read_csv(violation_file,keep_default_na=False)
    if not {'Language_ID','Glottocode'}.issubset(violations.columns):raise RuntimeError('违例文件缺少系统联结键。')
    primary_selected=violations[['Glottocode','Language_ID']].drop_duplicates().sort_values(['Glottocode','Language_ID']).head(20)
    eligible=violations
    if posthoc_primary:
        eligible=violations[violations.proposition.str.split(';').map(lambda xs:'P5' in xs or 'P1_A_four' in xs)]
    selected=eligible[['Glottocode','Language_ID']].drop_duplicates().sort_values(['Glottocode','Language_ID'])
    if not posthoc_primary:selected=selected.head(20)
    raw_all=pd.read_csv(ROOT/'data/kinbank/kinbank/cldf/forms.csv',keep_default_na=False)
    raw_all=raw_all[raw_all.Language_ID.isin(selected.Language_ID)].copy()
    raw=raw_all[raw_all.Parameter_ID.isin(CATEGORIES)].copy()
    context_codes=['mB','mZ','fB','fZ','mG','fG','meG','myG','feG','fyG']
    bibliography=(ROOT/'data/kinbank/kinbank/cldf/sources.bib').read_text()
    available_source_keys=set(re.findall(r'@[A-Za-z]+\s*\{\s*([^,\s]+)',bibliography))
    meta=metadata.set_index('Language_ID').to_dict('index');records=[]
    proposition_columns=[c for c in ['proposition','prediction','P','hypothesis','violation_type','reason','category','violation_reason'] if c in violations.columns]
    for index,key in enumerate(selected.itertuples(index=False),1):
        lid=key.Language_ID;rows=raw[raw.Language_ID.eq(lid)]
        if lid not in meta or set(rows.Parameter_ID)!=set(CATEGORIES):raise RuntimeError('违例系统没有完整可追踪的八类原始行。')
        fields=[];space=[];repeat=[];translation=[];source_missing=[];normalized=[];value_different=[];explicit_expansion=[];explicit_inference=[];explicit_autofill=[];explicit_transcription=[]
        source_set=set()
        for r in rows.itertuples(index=False):
            field={'ID':r.ID,'Parameter_ID':r.Parameter_ID,'Value':r.Value,'Form':r.Form,'Comment':r.Comment,'Source':r.Source,
                   'normalized_Form':normalize(r.Form),'parsed_sources':split_sources(r.Source)}
            fields.append(field);source_set.update(field['parsed_sources'])
            if ' ' in normalize(r.Form):space.append(r.ID)
            ts=normalize(r.Form).split()
            if len(set(ts))<len(ts):repeat.append(r.ID)
            if 'trad lit' in r.Comment.lower() or 'literal translation' in r.Comment.lower():translation.append(r.ID)
            if not field['parsed_sources']:source_missing.append(r.ID)
            if normalize(r.Form)!=r.Form:normalized.append(r.ID)
            if r.Value!=r.Form:value_different.append(r.ID)
            # 仅保存明确字面线索；不据此自动宣布展开或异写已经证实。
            if re.search(r'expand|copied|duplicat|not distinguished|not distinguish|no distinction',r.Comment,re.I):explicit_expansion.append({'ID':r.ID,'Comment':r.Comment})
            if re.search(r'inferred|inference|inferred from',r.Comment,re.I):explicit_inference.append({'ID':r.ID,'Comment':r.Comment})
            if re.search(r'autofilled|auto.?fill',r.Comment,re.I):explicit_autofill.append({'ID':r.ID,'Comment':r.Comment})
            if re.search(r'transcri|spell|orthograph|typo|variant',r.Comment,re.I):explicit_transcription.append({'ID':r.ID,'Comment':r.Comment})
        matched=violations[violations.Language_ID.eq(lid)]
        context=raw_all[raw_all.Language_ID.eq(lid)&raw_all.Parameter_ID.isin(context_codes)]
        context_rows=context[['ID','Parameter_ID','Value','Form','Comment','Source']].to_dict('records')
        raw_matches={c:sorted({normalize(x) for x in rows.loc[rows.Parameter_ID.eq(c),'Form'] if normalize(x) not in ['','?','-']}) for c in CATEGORIES}
        declared=pd.read_csv(ROOT/'analysis/category_forms_primary.csv',keep_default_na=False)
        expected={r.Parameter_ID:sorted(json.loads(r.forms_json)) for r in declared[declared.Language_ID.eq(lid)].itertuples(index=False)}
        if raw_matches!=expected:raise RuntimeError('抽查原始形式与主样本类别集合不一致。')
        propositions=sorted({p for value in matched.proposition for p in str(value).split(';') if p})
        primary_propositions=[p for p in propositions if p=='P1_A_four' or p in ['P2','P3','P4','P5']]
        record={'audit_order':index,'Language_ID':lid,'Glottocode':key.Glottocode,
                'family_group':meta[lid]['family_group'],'family_name':meta[lid]['family_name'],
                'Macroarea_original':meta[lid]['Macroarea_original'],'Macroarea_first':meta[lid]['Macroarea_first'],
                'violation_records':matched.to_dict('records'),'proposition_fields':proposition_columns,'raw_rows':fields,
                'propositions':propositions,'primary_definition_or_P2_P5_violations':primary_propositions,
                'reference_three_feature_only':all(p in ['P1_A_three','P1_B_three'] for p in propositions),
                'field_review_note':FIELD_REVIEW_NOTES.get(key.Glottocode,'原字段已列明；不作新增语义判定。'),
                'coarse_sibling_context_rows':context_rows,'raw_target_form_sets_match_partition_input':True,
                'candidate_explanations':{
                    'recorded_structural_violation':{'status':'程序判定的数据库形式违例','certainty':'对程序与已有字段的对应可核查；真实语言解释未确认','evidence':'对应s2_violations.csv的原始记录，见violation_records'},
                    'multiword_or_descriptive_form':{'status':'有空格形式线索' if space else '目标形式未见空格线索','certainty':'空格、重复词元与注释均为字段事实；是否描述短语无法一概判断','space_form_row_ids':space,'repeated_token_row_ids':repeat,'explicit_literal_translation_row_ids':translation},
                    'coarse_category_expansion':{'status':'有显式展开／推断／自动填入注释字面线索，待核对所指' if explicit_expansion or explicit_inference or explicit_autofill else '无法判断','certainty':'既有注释不足以逐条确认粗类展开；同形重复不是证明','comment_candidates':explicit_expansion,'inference_comment_candidates':explicit_inference,'autofill_comment_candidates':explicit_autofill},
                    'source_transcription_difference':{'status':'存在待核查字段差异' if len(source_set)>1 or source_missing or normalized or value_different or explicit_transcription else '未见所列字段线索，仍无法排除','certainty':'来源／编码差异是字段事实；是否同一词项的异写或误配无法判断','distinct_source_ids':sorted(source_set),'source_keys_not_resolved_in_bibliography':sorted(source_set-available_source_keys),'rows_without_source':source_missing,'rows_changed_by_NFC_whitespace':normalized,'rows_with_Value_not_equal_Form':value_different,'transcription_comment_candidates':explicit_transcription}},
                'overall_interpretation':'无法判断真实语义违例；仅确认数据库编码下的形式模式',
                'semantic_counterexample_confirmed':False,
                'review_scope':'核对所有目标八类的既有Value/Form/Comment/Source；不人工改词、不新增语义标签、不据此修改共享结果。'}
        records.append(record)
    summaries={
        'systems_with_space_form':sum(bool(r['candidate_explanations']['multiword_or_descriptive_form']['space_form_row_ids']) for r in records),
        'systems_with_repeated_token_form':sum(bool(r['candidate_explanations']['multiword_or_descriptive_form']['repeated_token_row_ids']) for r in records),
        'systems_with_Value_Form_difference':sum(bool(r['candidate_explanations']['source_transcription_difference']['rows_with_Value_not_equal_Form']) for r in records),
        'systems_with_NFC_whitespace_changes':sum(bool(r['candidate_explanations']['source_transcription_difference']['rows_changed_by_NFC_whitespace']) for r in records),
        'systems_with_missing_source':sum(bool(r['candidate_explanations']['source_transcription_difference']['rows_without_source']) for r in records),
        'systems_with_multiple_source_keys':sum(len(r['candidate_explanations']['source_transcription_difference']['distinct_source_ids'])>1 for r in records),
        'systems_with_unresolved_source_keys':sum(bool(r['candidate_explanations']['source_transcription_difference']['source_keys_not_resolved_in_bibliography']) for r in records),
        'systems_with_expansion_comment_candidates':sum(bool(r['candidate_explanations']['coarse_category_expansion']['comment_candidates']) for r in records),
        'systems_with_inference_comment_candidates':sum(bool(r['candidate_explanations']['coarse_category_expansion']['inference_comment_candidates']) for r in records),
        'systems_with_autofill_comment_candidates':sum(bool(r['candidate_explanations']['coarse_category_expansion']['autofill_comment_candidates']) for r in records),
        'systems_with_transcription_comment_candidates':sum(bool(r['candidate_explanations']['source_transcription_difference']['transcription_comment_candidates']) for r in records),
        'systems_with_coarse_sibling_context_rows':sum(bool(r['coarse_sibling_context_rows']) for r in records),
        'systems_with_raw_form_sets_verified':sum(r['raw_target_form_sets_match_partition_input'] for r in records),
        'systems_with_unresolved_semantic_interpretation':len(records),
        'systems_with_primary_four_feature_A_or_P2_P5_violation':sum(bool(r['primary_definition_or_P2_P5_violations']) for r in records),
        'systems_with_primary_four_feature_A_violation':sum('P1_A_four' in r['propositions'] for r in records),
        'systems_with_P5_violation':sum('P5' in r['propositions'] for r in records),
        'systems_with_both_primary_four_feature_A_and_P5_violation':sum('P1_A_four' in r['propositions'] and 'P5' in r['propositions'] for r in records),
        'systems_with_three_feature_reference_only':sum(r['reference_three_feature_only'] for r in records)}
    return {'selection_rule':'运行后补查全部四特征A不合取系统与全部P5明确不兼容对象，按Glottocode去重并排序；不替换固定前20。' if posthoc_primary else '全部违例按Glottocode、Language_ID升序的前20个不同系统；不足20检查全部。',
            'audit_role':'运行后补充质量核查' if posthoc_primary else '运行前指定的固定前20抽查',
            'available_distinct_violation_systems':int(eligible[['Glottocode','Language_ID']].drop_duplicates().shape[0]),
            'audited_distinct_systems':len(records),'target_at_least_20_reached':len(records)>=20,
            'all_available_reviewed_when_below_20':len(records)==len(eligible[['Glottocode','Language_ID']].drop_duplicates()) if len(records)<20 else None,
            'raw_field_rows_preserved':sum(len(r['raw_rows']) for r in records),
            'additional_coarse_context_rows_preserved':sum(len(r['coarse_sibling_context_rows']) for r in records),
            'semantic_counterexamples_confirmed':0,'all_cases_semantic_explanation_unresolved':True,
            'field_evidence_summary':summaries,
            'audit_records':records,'input_sha256':hashlib.sha256(violation_file.read_bytes()).hexdigest()}


def write_audit_markdown(audit):
    lines=['# S2违例原字段抽查','',
           f'按最终协议检查Glottocode顺序前{audit["audited_distinct_systems"]}个不同系统；可供抽查的违例系统共{audit["available_distinct_violation_systems"]}个。保留全部{audit["raw_field_rows_preserved"]}条八类相关原始记录，见`violation_audit.json`。',
           '', '四类候选解释允许并存。以下只记录程序形式违例、空格／注释线索、展开线索、来源／转写字段；仅凭这些字段不能确认真实语义违例。所有系统的语义总评均为“无法判断”，不是已确认的普遍律反例。',
           '', '汇总只描述这组按固定字典顺序取得的字段抽查，不能外推为全部违例的原因比例；全部八类原始形式集合都与分析输入逐项一致。',
           '', '| 序号 | Glottocode／系统 | 语系 | 空格行 | 重复词元行 | 无来源行 | 来源数 | Value/Form不同的行 | 总评 |',
           '|---:|---|---|---:|---:|---:|---:|---:|---|']
    for r in audit['audit_records']:
        m=r['candidate_explanations']['multiword_or_descriptive_form'];s=r['candidate_explanations']['source_transcription_difference']
        lines.append(f'| {r["audit_order"]} | {r["Glottocode"]}／{r["Language_ID"]} | {r["family_name"]} | {len(m["space_form_row_ids"])} | {len(m["repeated_token_row_ids"])} | {len(s["rows_without_source"])} | {len(s["distinct_source_ids"])} | {len(s["rows_with_Value_not_equal_Form"])} | 无法判断真实语义解释 |')
    lines+=['','## 各系统的全部原始字段','']
    if 'posthoc_primary_four_A_all_plus_P5' in audit:
        extra=audit['posthoc_primary_four_A_all_plus_P5']
        lines += [f'固定前20中，四特征主定义或P2–P5有关违例为{audit["field_evidence_summary"]["systems_with_primary_four_feature_A_or_P2_P5_violation"]}个，其余{audit["field_evidence_summary"]["systems_with_three_feature_reference_only"]}个仅属三特征参照。不能将后者改称主定义反例。',
                  '',f'结果生成后补查全部{extra["field_evidence_summary"]["systems_with_primary_four_feature_A_violation"]}个四特征A不合取系统及{extra["field_evidence_summary"]["systems_with_P5_violation"]}个P5明确不兼容系统，去重为{extra["audited_distinct_systems"]}个，保存{extra["raw_field_rows_preserved"]}条目标行；它们不替换预先固定的前20，另列为“运行后补充质量核查”。两组审查合计覆盖{audit["total_distinct_systems_with_existing_fields_reviewed"]}个不同系统。','']
    reviewed=audit['audit_records']+audit.get('posthoc_primary_four_A_all_plus_P5',{}).get('audit_records',[])
    for r in reviewed:
        lines+=[f'### {r["audit_order"]}. {r["Glottocode"]}：{r["Language_ID"]}','',
                f'谱系：{r["family_name"]}；区域：{r["Macroarea_original"]}。候选粗类展开解释：{r["candidate_explanations"]["coarse_category_expansion"]["status"]}；真实语义解释：无法判断。','',
                '所涉程序命题：'+', '.join(r['propositions'])+'。', '',
                '逐字段复核说明：'+r['field_review_note'],'',
                '| 记录ID | 类别 | Value | Form | Comment | Source |','|---|---|---|---|---|---|']
        for f in r['raw_rows']:
            lines.append('| '+' | '.join(str(f[x] or '〔空〕').replace('|','\\|').replace('\n','<br>') for x in ['ID','Parameter_ID','Value','Form','Comment','Source'])+' |')
        if r['coarse_sibling_context_rows']:
            lines+=['','相关粗类别／未区分所指者性别的背景行（不加入八类分析）：','',
                    '| 记录ID | 类别 | Value | Form | Comment | Source |','|---|---|---|---|---|---|']
            for f in r['coarse_sibling_context_rows']:
                lines.append('| '+' | '.join(str(f[x] or '〔空〕').replace('|','\\|').replace('\n','<br>') for x in ['ID','Parameter_ID','Value','Form','Comment','Source'])+' |')
        lines+=['']
    lines+=['抽查未修改任何原始记录或S2共享结果。空格与Value/Form差异可能来自书写方式或上游预处理；缺少相关线索也不能证明原语义数据无误。','']
    (HERE/'s2_violation_audit.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audit',action='store_true');args=parser.parse_args()
    start=dt.datetime.now(dt.timezone.utc).isoformat();gate=protocol_gate()
    definitions,metadata,forms=load_measurement_data()
    result=measurement_results(definitions,metadata,forms)
    result['provenance']={**gate,'started_utc':start,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'analysis/pairs_primary.csv',ROOT/'analysis/category_forms_primary.csv',ROOT/'data/kinbank/kinbank/cldf/forms.csv']}}
    (HERE/'measurement_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    summary={'definitions':result['definitions'],'D5_counts':{k:v for k,v in result['D5'].items() if not isinstance(v,(list,dict))},'geography':{k:v for k,v in result['geography'].items() if not isinstance(v,list)}}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if args.audit:
        audit=build_violation_audit(metadata)
        extra=build_violation_audit(metadata,posthoc_primary=True)
        for i,record in enumerate(extra['audit_records'],1):record['audit_order']='补充'+str(i)
        audit['posthoc_primary_four_A_all_plus_P5']=extra
        all_records=audit['audit_records']+extra['audit_records']
        audit['total_distinct_systems_with_existing_fields_reviewed']=len({r['Language_ID'] for r in all_records})
        audit['total_target_raw_rows_preserved']=len({f['ID'] for r in all_records for f in r['raw_rows']})
        audit['total_target_raw_rows_including_repeated_sections']=audit['raw_field_rows_preserved']+extra['raw_field_rows_preserved']
        audit['provenance']={**gate,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        (HERE/'violation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        write_audit_markdown(audit)
        print(json.dumps({'audited_systems':audit['audited_distinct_systems'],'raw_rows':audit['raw_field_rows_preserved'],'semantic_counterexamples_confirmed':0},ensure_ascii=False))


if __name__=='__main__':main()
