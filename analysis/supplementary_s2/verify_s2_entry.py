"""S2协议及冻结C=1复现门；只写S2目录。"""
from pathlib import Path
import datetime, hashlib, importlib.util, json, subprocess
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROTOCOL_COMMIT = '6ba7afba369d3d15446ea7571eabd2117b7e8c74'
PROTOCOL_SHA = '61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be'

def verify_protocol():
    p = HERE/'protocol_s2.md'
    assert hashlib.sha256(p.read_bytes()).hexdigest() == PROTOCOL_SHA
    committed = subprocess.check_output(['git','show',f'{PROTOCOL_COMMIT}:analysis/supplementary_s2/protocol_s2.md'], cwd=ROOT)
    assert hashlib.sha256(committed).hexdigest() == PROTOCOL_SHA
    msg = subprocess.check_output(['git','show','-s','--format=%s',PROTOCOL_COMMIT], cwd=ROOT).decode()
    assert 'pre-run protocol' in msg
    return {'protocol_commit':PROTOCOL_COMMIT,'protocol_sha256':PROTOCOL_SHA}

def reproduce_frozen():
    meta=verify_protocol()
    # 只读复用S1的精确衔接参数化，不改S1源文件或其输出。
    spec=importlib.util.spec_from_file_location('frozen_s1_reproduction',HERE.parent/'supplementary_s1/run_s1.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    frame=pd.read_csv(HERE.parent/'pairs_primary.csv',dtype={'pattern':str})
    frozen=json.loads((HERE.parent/'results.json').read_text())
    primary=next(r for r in frozen['analyses'] if r['variant']=='primary' and r['cv_grouping']=='family')
    mapping={'M0':'raw_additive','M1':'classical_additive','M2':'pairwise'}
    values={}; errors={}; folds=[]
    for model,key in mapping.items():
        pred=np.zeros(len(frame))
        for k,(itr,ite) in enumerate(GroupKFold(5).split(frame,groups=frame.family_group)):
            pred[ite]=mod.fit_predict(frame.iloc[itr],frame.iloc[ite],model,1)
            if model=='M0':folds.append({'fold':k,'test_systems':int(frame.iloc[ite].Glottocode.nunique())})
        values[model]=float(mod.language_equal_loss(frame,pred))
        errors[model]=abs(values[model]-primary['language_equal_logloss'][key])
    assert max(errors.values())<=1e-9,errors
    meta.update(verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,language_equal_C1_losses=values,max_absolute_error=max(errors.values()),tolerance=1e-9,folds=folds)
    (HERE/'s2_baseline_reproduction.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    return meta

if __name__=='__main__':
    print(json.dumps(reproduce_frozen(),ensure_ascii=False,indent=2))
