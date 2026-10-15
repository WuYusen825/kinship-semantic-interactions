"""仅作数据结构审计；不生成或检查共享词形结果。"""
from pathlib import Path
import hashlib, json, unicodedata
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / 'data' / 'kinbank' / 'kinbank' / 'cldf'
OUT = BASE / 'analysis'
CATEGORIES = ['meB','myB','meZ','myZ','feB','fyB','feZ','fyZ']

def norm(value):
    return ' '.join(unicodedata.normalize('NFC', str(value)).split())

def load_data():
    forms = pd.read_csv(RAW / 'forms.csv', keep_default_na=False)
    langs = pd.read_csv(RAW / 'languages.csv', keep_default_na=False)
    glot = pd.read_csv(BASE / 'data' / 'glottolog_languages.csv', keep_default_na=False)
    gm = glot.set_index('ID')
    def family(gc):
        if gc not in gm.index:
            return '', '', 'unmatched'
        row = gm.loc[gc]
        fid = row.Family_ID
        if fid:
            return fid, str(gm.loc[fid, 'Name']) if fid in gm.index else fid, 'family'
        root = row.Language_ID or gc
        is_isolate = row.Is_Isolate == 'true'
        if root in gm.index:
            is_isolate = is_isolate or gm.loc[root, 'Is_Isolate'] == 'true'
        if is_isolate:
            return 'isolate:' + root, str(gm.loc[root,'Name']) if root in gm.index else root, 'isolate'
        return '', '', 'unclassified'
    vals = langs.Glottocode.map(family)
    langs[['family_group','family_name','family_status']] = pd.DataFrame(vals.tolist(), index=langs.index)
    sibling = forms[forms.Parameter_ID.isin(CATEGORIES)].copy()
    sibling['normalized_form'] = sibling.Form.map(norm)
    sibling['valid_form'] = ~sibling.normalized_form.isin(['','?','-'])
    valid = sibling[sibling.valid_form]
    coverage = valid.groupby('Language_ID').Parameter_ID.nunique().rename('n_categories')
    langs = langs.join(coverage, on='ID')
    langs['n_categories'] = langs.n_categories.fillna(0).astype(int)
    available = langs[langs.n_categories > 0].copy()
    # 仅按已有类别覆盖选一个资料来源；并列时用稳定的ID字典顺序。
    selected = available.sort_values(['Glottocode','n_categories','ID'], ascending=[True,False,True]).drop_duplicates('Glottocode')
    selected = selected[selected.Glottocode != ''].copy()
    return forms, sibling, valid, available, selected, glot

def matrix(patterns, model):
    d = np.array(patterns,dtype=float)
    if model == 'raw_additive':
        cols = d
    elif model == 'classical_additive':
        cols = np.c_[d, np.logical_xor(d[:,0],d[:,2]).astype(float)]
    elif model == 'pairwise':
        cols = np.c_[d, d[:,0]*d[:,1], d[:,0]*d[:,2], d[:,1]*d[:,2]]
    else:
        raise ValueError(model)
    return cols

def main():
    forms, sibling, valid, available, selected, glot = load_data()
    selected.to_csv(OUT/'selected_languages_structural.csv',index=False)
    patterns = [(a,b,c) for a in (0,1) for b in (0,1) for c in (0,1) if a+b+c]
    ranks = {k: int(np.linalg.matrix_rank(np.c_[np.ones(7),matrix(patterns,k)])) for k in ['raw_additive','classical_additive','pairwise']}
    audit = {
        'forms_records':len(forms), 'language_ids_total': int(pd.read_csv(RAW/'languages.csv').shape[0]),
        'parameters_total': int(pd.read_csv(RAW/'parameters.csv').shape[0]),
        'sibling_records':len(sibling), 'sibling_valid_records':len(valid),
        'sibling_language_ids':len(available),'sibling_glottocodes_selected':len(selected),
        'duplicate_source_ids_removed':len(available)-len(selected),
        'coverage_before_dedup':available.n_categories.value_counts().sort_index().to_dict(),
        'coverage_after_dedup':selected.n_categories.value_counts().sort_index().to_dict(),
        'selected_family_status':selected.family_status.value_counts().to_dict(),
        'original_missing_family_ids':int((available.Family=='').sum()),
        'original_missing_family_selected':int((selected.Family=='').sum()),
        'normalization_changed_records':int((sibling.Form!=sibling.normalized_form).sum()),
        'invalid_form_records':int((~sibling.valid_form).sum()),
        'target_categories':CATEGORIES, 'model_design_ranks':ranks,
        'rank_two_dimensions_additive':int(np.linalg.matrix_rank([[1,0,1],[1,1,0],[1,1,1]])),
        'rank_two_dimensions_with_interaction':int(np.linalg.matrix_rank([[1,0,1,0],[1,1,0,0],[1,1,1,1]])),
        'sha256':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [RAW/'forms.csv',RAW/'languages.csv',RAW/'parameters.csv',BASE/'data'/'glottolog_languages.csv']},
    }
    (OUT/'structural_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print(json.dumps(audit,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
