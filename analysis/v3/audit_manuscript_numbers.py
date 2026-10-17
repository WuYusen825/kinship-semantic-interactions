#!/usr/bin/env python3
"""第三版逐处数字核验：复用冻结检查器，结果只允许绑定带生产来源的汇总叶。"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))
import check_manuscript_numbers as base

base.DEFAULT_MANUSCRIPT = 'outputs/论文_中文第三版.md'
base.DEFAULT_CLAIMS = 'notes/v3/manuscript_number_claims.json'
base.DEFAULT_REPORT = 'notes/v3/number_check.json'
base.RESULT_FILES = set(base.RESULT_FILES) | {'results/summary.json'}
# 长整数小数不能被SHA分支抢先截成“整数部分”和“小数部分”。只调整本版导入实例，
# 冻结旧检查器文件及旧报告均不变；真正SHA仍由含a-f的十六进制字符串识别。
base.NUMBER_RE = re.compile(base.NUMBER_RE.pattern.replace(
    r'(?=[0-9a-fA-F]*\d)[0-9a-fA-F]{7,64}',
    r'(?=[0-9a-fA-F]*\d)(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{7,64}'))
_calculate = base.calculate
_run_check = base.run_check


def calculate(claim, root, cache):
    calculation = claim.get('calculation') or {}
    if calculation.get('operation') == 'count_items':
        if not claim.get('calculation_reason') or len(calculation.get('operands', [])) != 1:
            raise ValueError('列表计数必须有唯一精确来源及明确理由')
        value = base.read_json_source(calculation['operands'][0], root, cache, True)
        if not isinstance(value, (list, dict)):
            raise ValueError('列表计数来源不是列表或字典')
        return Decimal(len(value))
    return _calculate(claim, root, cache)


def run_check(manuscript, mapping, root):
    report = _run_check(manuscript, mapping, root)
    provenance = []
    summary_path = root / 'results/summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    numeric_index = {(a, p): v for a, p, v in summary.get('numeric_index', [])}
    for claim in mapping.get('claims', []):
        if claim.get('kind') != 'result':
            continue
        sources = [claim['source']] if claim.get('source') else (claim.get('calculation') or {}).get('operands', [])
        for source in sources:
            try:
                if source['file'] != 'results/summary.json':
                    raise ValueError('第三版实测数值只允许results/summary.json，不能引用旧稿或首轮求解')
                parts = source['pointer'].split('/')
                if len(parts) < 5 or parts[1] != 'artifacts' or parts[3] != 'data':
                    raise ValueError('必须绑定/artifacts/所属任务/data具体指标，不接受numeric_index或同值搜索')
                artifact = parts[2]
                record = summary['artifacts'][artifact]
                value = base.pointer_get(summary, source['pointer'])
                relative_pointer = '/' + '/'.join(parts[4:])
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if (artifact, relative_pointer) not in numeric_index or numeric_index[artifact, relative_pointer] != value:
                        raise ValueError('指定指标未与汇总逐叶来源索引一致')
                elif (claim.get('calculation') or {}).get('operation') != 'count_items':
                    raise ValueError('非标量来源仅允许明确的列表计数')
                for key in ['source_file', 'producer_script', 'producer_function']:
                    if not record.get(key):
                        raise ValueError('结果缺少来源文件、脚本或函数')
                provenance.append({'occurrence_id': claim['occurrence_id'], 'pointer': source['pointer'],
                                   **{k: record[k] for k in ['source_file', 'producer_script', 'producer_function']}})
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                report['mismatches'].append({'type': 'v3_provenance_failed', 'occurrence_id': claim['occurrence_id'], 'detail': str(exc)})
    report['result_provenance'] = provenance
    report['claim_counts'] = {kind: sum(c.get('kind') == kind for c in mapping.get('claims', []))
                              for kind in ['result', 'whitelist', 'unresolved']}
    report['passed'] = report['passed'] and not report['mismatches']
    report['status'] = 'passed' if report['passed'] else 'failed'
    return report


base.calculate = calculate
base.run_check = run_check

def v3_self_test():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'results').mkdir()
        (root / 'analysis').mkdir()
        summary = {'artifacts': {'partition_models': {'source_file': 'results/t2/t2_results.json',
                    'producer_script': 'analysis/v3/run_t2.py', 'producer_function': 'run_cv',
                    'data': {'loss': 0.123456}}},
                   'numeric_index': [['partition_models', '/loss', 0.123456]]}
        (root / 'results/summary.json').write_text(json.dumps(summary))
        (root / 'analysis/results.json').write_text(json.dumps({'same_value': 0.123456}))
        manuscript = root / 'manuscript.md'
        manuscript.write_text('指定损失0.1235。\n')
        mapping = base.synchronize(manuscript, {}, root)
        claim = mapping['claims'][0]
        claim.update(kind='result', label='具有指定语义角色的损失', metric='log_loss',
                     format={'kind': 'fixed', 'places': 4},
                     source={'file': 'results/summary.json', 'pointer': '/artifacts/partition_models/data/loss'})
        assert run_check(manuscript, mapping, root)['passed']
        claim['source']['pointer'] = '/numeric_index/0/2'
        assert not run_check(manuscript, mapping, root)['passed']
        claim['source'] = {'file': 'analysis/results.json', 'pointer': '/same_value'}
        assert not run_check(manuscript, mapping, root)['passed']
        claim['source'] = {'file': 'results/summary.json', 'pointer': '/artifacts/partition_models/data/loss'}
        summary['artifacts']['partition_models']['producer_function'] = ''
        (root / 'results/summary.json').write_text(json.dumps(summary))
        assert not run_check(manuscript, mapping, root)['passed']
        assert [o['token'] for o in base.extract_numbers('上限37397057.50。')] == ['37397057.50']
    print('v3_self_test_passed=true：指定artifact、禁止索引/旧稿同值、生产函数及长小数提取通过')

if __name__ == '__main__':
    # 原检查器自测使用独立临时仓库，因而不套用本版来源位置限制。
    if '--self-test' in sys.argv:
        v3_self_test()
        base.run_check = _run_check
    raise SystemExit(base.main())
