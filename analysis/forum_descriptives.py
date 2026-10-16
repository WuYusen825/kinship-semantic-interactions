"""论坛稿使用的事后描述统计：只读冻结输出，不重新拟合模型，不属于冻结协议。

运行：python analysis/forum_descriptives.py
输入：pairs_primary.csv、category_forms_primary.csv、selected_languages_structural.csv、results.json
输出：forum_descriptives.json
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, json

OUT = Path(__file__).resolve().parent
CATEGORIES = ['meB','myB','meZ','myZ','feB','fyB','feZ','fyZ']
CELLS = ['001','010','011','100','101','110','111']
# 论坛六语种及作为对照的普通话，按 Kinbank 语言资料 ID 选取
FORUM_LANGUAGES = {
    'p_englishstan1293':'英语','v_standardfrenchstan1290':'法语','p_germanstan1295':'德语',
    'v_japanesenucl1643':'日语','p_russianruss1263a':'俄语','v_standardspanishstan1288':'西班牙语',
    'v_mandarinchinamand1415':'普通话'}

def shared_iff(rule):
    """把“共享当且仅当 rule(Dr,Da,De)”转成七单元共享计数签名（每单元4对）。"""
    return tuple((c, 4 if rule(*map(int, c)) else 0) for c in CELLS)

NAMED_TYPES = {
    shared_iff(lambda r,a,e: True):'不作区分：一个词形覆盖全部八类',
    shared_iff(lambda r,a,e: r==0):'只区分所指者性别（英语型）',
    shared_iff(lambda r,a,e: r==0 and a==0):'区分所指者性别与相对年龄（日语、普通话型）',
    shared_iff(lambda r,a,e: a==0):'只区分相对年龄',
    shared_iff(lambda r,a,e: (r^e)==0):'只区分同性／异性兄弟姐妹',
    shared_iff(lambda r,a,e: False):'八类各不相同',
}

def main():
    pairs = defaultdict(list)
    with (OUT/'pairs_primary.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            pairs[row['Language_ID']].append(row)
    forms = defaultdict(dict)
    with (OUT/'category_forms_primary.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['Language_ID'] in pairs:
                forms[row['Language_ID']][row['Parameter_ID']] = json.loads(row['forms_json'])
    names = {}
    with (OUT/'selected_languages_structural.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            names[row['ID']] = (row['Name'], row['family_name'])

    signatures = {}
    for lang, rows in pairs.items():
        counts = Counter({c:0 for c in CELLS})
        for row in rows:
            counts[row['pattern']] += int(row['shared_form'])
        signatures[lang] = tuple((c, counts[c]) for c in CELLS)
    n = len(signatures)
    dist = Counter(signatures.values())
    cell_determined = sum(all(v in (0,4) for _,v in s) for s in signatures.values())
    type_rows = [{'type':label,'signature':dict(sig),'languages':dist.get(sig,0),'share':dist.get(sig,0)/n}
                 for sig,label in NAMED_TYPES.items()]

    # 七单元内部的次级区分：同一差异单元的四个具体类别对共享情况不同
    # A：所指者性别只在一个年龄段区分（001全共享，100与101各共享2对）
    # B：相对年龄只在一种所指者性别内区分（001全共享，010与011各共享2对）
    sig_a = (('001',4),('010',0),('011',0),('100',2),('101',2),('110',0),('111',0))
    sig_b = (('001',4),('010',2),('011',2),('100',0),('101',0),('110',0),('111',0))
    secondary = Counter()
    secondary_families = defaultdict(Counter)
    for lang, rows in pairs.items():
        if signatures[lang] == sig_a:
            ages = {r['category_a'][1] for r in rows if r['pattern']=='100' and r['shared_form']=='1'}
            key = {'y':'sex_distinguished_for_elder_only','e':'sex_distinguished_for_younger_only'}.get(''.join(ages),'mixed')
        elif signatures[lang] == sig_b:
            sexes = {r['category_a'][2] for r in rows if r['pattern']=='010' and r['shared_form']=='1'}
            key = {'Z':'age_distinguished_for_brothers_only','B':'age_distinguished_for_sisters_only'}.get(''.join(sexes),'mixed')
        else:
            continue
        secondary[key] += 1
        secondary_families[key][names[lang][1]] += 1

    forum = []
    for lang, zh in FORUM_LANGUAGES.items():
        sig = signatures[lang]
        forum.append({'language':zh,'Language_ID':lang,'Name':names[lang][0],'family':names[lang][1],
                      'forms':{c:forms[lang][c] for c in CATEGORIES},
                      'shared_pairs_by_cell':dict(sig),'type':NAMED_TYPES.get(sig,'其他')})

    all_forms = [f for lang in pairs for c in CATEGORIES for f in forms[lang].get(c,[])]
    multi_langs = {lang for lang in pairs for c in CATEGORIES for f in forms[lang].get(c,[]) if ' ' in f.strip()}

    primary = next(a for a in json.loads((OUT/'results.json').read_text())['analyses']
                   if a['variant']=='primary' and a['cv_grouping']=='family')
    cr = primary['comparisons']['classical_over_raw']

    result = {
        'note':'事后描述统计，读取冻结输出生成；不重新拟合模型，不改变 results.json。',
        'languages':n,
        'distinct_28_pair_vectors':len({tuple(int(r['shared_form']) for r in sorted(rows,key=lambda r:(r['category_a'],r['category_b']))) for rows in pairs.values()}),
        'distinct_seven_cell_signatures':len(dist),
        'cell_determined_languages':cell_determined,
        'cell_determined_share':cell_determined/n,
        'named_types':type_rows,
        'secondary_distinctions':{k:{'languages':v,'families':len(secondary_families[k]),
                                     'top_families':secondary_families[k].most_common(3)} for k,v in secondary.items()},
        'forum_languages':forum,
        'multiword_forms':{'forms_total':len(all_forms),'forms_with_space':sum(' ' in f.strip() for f in all_forms),
                           'systems_with_space_form':len(multi_langs)},
        'classical_over_raw_primary':{'gain':cr['language_equal_gain'],'ci95':cr['family_cluster_bootstrap_95ci'],
                                      'families_positive':cr['families_with_positive_gain'],
                                      'families_negative':cr['families_with_negative_gain'],
                                      'gain_excluding_largest_family':cr['gain_excluding_largest_family_fixed_predictions'],
                                      'share_of_raw_to_pairwise_gain':cr['language_equal_gain']/primary['comparisons']['raw']['language_equal_gain']},
    }
    (OUT/'forum_descriptives.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k:result[k] for k in ['languages','distinct_28_pair_vectors','distinct_seven_cell_signatures','cell_determined_languages','multiword_forms']}, ensure_ascii=False))
    for t in type_rows: print(t['languages'], f"{t['share']:.1%}", t['type'])
    for f in forum: print(f['language'], f['type'])

if __name__ == '__main__':
    main()
