"""T1的独立覆盖、DNF穷举、旧定义与分折／权重／日志检查。"""
from collections import Counter
from itertools import combinations,product
import csv
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/v3'))
import common
from languages import LANGUAGES,conjunction_terms,is_conjunctive,minimum_dnf,minimum_dnf_witness
from partitions import (blocks_to_rgs,canonical_rgs,enumerate_rgs,partition_catalogue,
                        partition_id_map,rgs_to_blocks,strict_direction_vector,validate_rgs)
from structural_enumeration import enumerate_partitions,is_conjunctive as old_conjunctive


def log_worker(directory,worker):
    common.RESULTS=Path(directory)
    common.git_commit=lambda:'parallel-test'
    for i in range(5):common.log_run('test',{'worker':worker,'i':i},{'ok':True},'passed')


def brute_subset_cost(target,language):
    """与DP不同：显式枚举全部允许项子集，核查小目标的真正最优。"""
    names=LANGUAGES[language];terms={}
    for assignment in product((-1,0,1),repeat=len(names)):
        mask=0
        for i in range(8):
            if all(v==-1 or common.FEATURES[f][i]==v for f,v in zip(names,assignment)):mask|=1<<i
        if mask and mask&~target==0:
            terms[mask]=min(terms.get(mask,99),sum(v!=-1 for v in assignment))
    items=list(terms.items());best=999
    for chosen in range(1,1<<len(items)):
        mask=0;cost=0
        for i,(extent,literals) in enumerate(items):
            if chosen>>i&1:mask|=extent;cost+=literals
        if mask==target:best=min(best,cost)
    return best


class PartitionInfrastructureTests(unittest.TestCase):
    def test_rgs_unique_lexicographic_and_bell_number(self):
        values=enumerate_rgs()
        self.assertEqual(len(values),4140)
        self.assertEqual(len(set(values)),4140)
        self.assertEqual(values,tuple(sorted(values)))
        self.assertEqual(values[0],(0,)*8)
        self.assertEqual(values[-1],tuple(range(8)))
        self.assertEqual([partition_id_map()[r] for r in values],list(range(4140)))

    def test_stirling_distribution_and_masks_match_old(self):
        counts=[[0]*9 for _ in range(9)];counts[0][0]=1
        for n in range(1,9):
            for k in range(1,9):counts[n][k]=k*counts[n-1][k]+counts[n-1][k-1]
        self.assertEqual(Counter(max(r)+1 for r in enumerate_rgs()),{k:counts[8][k] for k in range(1,9)})
        masks={rgs_to_blocks(r) for r in enumerate_rgs()}
        self.assertEqual(masks,set(enumerate_partitions()))
        for rgs in enumerate_rgs():self.assertEqual(blocks_to_rgs(rgs_to_blocks(rgs)),rgs)

    def test_invalid_rgs_and_empty_block_rejected(self):
        for rgs in [(1,)*8,(0,2,0,0,0,0,0,0),(0,)*7]:
            with self.assertRaises(ValueError):validate_rgs(rgs)
        with self.assertRaises(ValueError):blocks_to_rgs([0,255])
        with self.assertRaises(ValueError):minimum_dnf(0,'abs')

    def test_full_crosscheck_old_conjunction_and_strict_directions(self):
        for row in partition_catalogue():
            for language,features in LANGUAGES.items():
                self.assertEqual(is_conjunctive(row['blocks'],language),old_conjunctive(row['blocks'],features))
            self.assertEqual(tuple(row[p] for p in ['P2','P3','P4']),strict_direction_vector(row['labels']))
            self.assertLessEqual(sum(row[p]!=0 for p in ['P2','P3','P4']),1)

    def test_referent_and_relative_sex_examples(self):
        r=tuple(common.FEATURES['r']);q=tuple(common.FEATURES['q'])
        self.assertTrue(is_conjunctive(rgs_to_blocks(canonical_rgs(r)),'abs'))
        qblocks=rgs_to_blocks(canonical_rgs(q))
        self.assertFalse(is_conjunctive(qblocks,'abs'))
        self.assertTrue(is_conjunctive(qblocks,'rel_r'))
        self.assertTrue(is_conjunctive(qblocks,'rel_s'))
        for block in qblocks:
            self.assertEqual(minimum_dnf(block,'abs'),4)
            self.assertEqual(minimum_dnf(block,'rel_r'),1)


class DescriptionCostTests(unittest.TestCase):
    def test_tautology_singletons_and_overlap(self):
        for language in LANGUAGES:
            self.assertEqual(minimum_dnf(255,language),0)
            for i in range(8):self.assertEqual(minimum_dnf(1<<i,language),3)
        self.assertEqual(minimum_dnf((1<<0)|(1<<1)|(1<<2),'abs'),4)

    def test_exact_optimum_with_independent_subset_enumeration(self):
        for language in LANGUAGES:
            for size in [1,2,3]:
                for atoms in combinations(range(8),size):
                    target=sum(1<<i for i in atoms)
                    self.assertEqual(minimum_dnf(target,language),brute_subset_cost(target,language),(language,target))

    def test_all_witnesses_cover_target_with_exact_cost(self):
        for language in LANGUAGES:
            for mask in range(1,256):
                proof=minimum_dnf_witness(mask,language);coverage=0
                for term in proof:
                    coverage|=sum(1<<i for i in range(8) if all(common.FEATURES[f][i]==v for f,v in term))
                self.assertEqual(coverage,mask)
                self.assertEqual(sum(map(len,proof)),minimum_dnf(mask,language))


class DataAndExecutionTests(unittest.TestCase):
    def test_parquet_roundtrip_matches_csv_and_native_masks(self):
        path=common.RESULTS/'t1'
        if not (path/'partitions.parquet').exists():
            self.skipTest('统一环境尚未安装Parquet依赖，CSV/JSON检查独立完成。')
        csv_table=pd.read_csv(path/'partitions.csv',dtype={'rgs':str})
        parquet=pd.read_parquet(path/'partitions.parquet')
        pd.testing.assert_frame_equal(csv_table,parquet[csv_table.columns])
        for column in ['blocks','labels','s2_labels','shape']:
            expected=csv_table[column+'_json'].map(json.loads)
            self.assertEqual([list(x) for x in parquet[column]],expected.tolist())

    def test_mappings_reproduce_T0_and_fixed_folds(self):
        table=common.load_partition_table();base=common.load_base_data();meta=base['systems'].set_index('Language_ID')
        for sample,n in [('strict',625),('equal_sets',939),('components',939)]:
            mapping=common.load_system_mapping(sample)
            self.assertEqual(len(mapping),n)
            self.assertTrue(mapping.partition_id.isin(table.partition_id).all())
            for mode in ['family','language']:
                expected=mapping.Language_ID.map(meta['fold_'+mode])
                np.testing.assert_array_equal(mapping['fold_'+mode],expected)
            self.assertTrue(mapping.groupby('family_group').fold_family.nunique().eq(1).all())
        strict=common.load_system_mapping('strict').merge(table,on='partition_id')
        self.assertEqual((~strict.conj_abs).sum(),163)
        self.assertEqual((~strict.conj_all).sum(),22)
        self.assertEqual(strict.family_group.nunique(),108)

    def test_three_partition_definitions_have_different_meanings(self):
        from build_t1 import connected_labels
        sets=[frozenset({'x'}),frozenset({'x','y'}),frozenset({'y'})]+[frozenset({str(i)}) for i in range(3,8)]
        equality=canonical_rgs(sets);connected=connected_labels(sets)
        self.assertNotEqual(equality[0],equality[1]);self.assertNotEqual(equality[0],equality[2])
        self.assertEqual(connected[0],connected[1]);self.assertEqual(connected[0],connected[2])

    def test_weights_distinguish_families_and_keep_language_unweighted_identity(self):
        frame=pd.DataFrame({'family_group':['a','a','b']})
        np.testing.assert_allclose(common.system_weights(frame,'family'),[.25,.25,.5])
        np.testing.assert_array_equal(common.system_weights(frame,'language'),common.system_weights(frame,'unweighted'))
        self.assertAlmostEqual(common.system_weights(frame,'family').sum(),1)

    def test_plan_gate_rejects_missing_and_changed_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            with patch.object(common,'PLAN_LOCK_PATH',path/'missing.json'):
                with self.assertRaises(RuntimeError):common.verify_analysis_plan(require_t1=False)
            (path/'plan.md').write_text('changed')
            (path/'lock.json').write_text('{"commit":"bad","sha256":"wrong"}')
            with patch.object(common,'PLAN_LOCK_PATH',path/'lock.json'),patch.object(common,'PLAN_PATH',path/'plan.md'):
                with self.assertRaises(RuntimeError):common.verify_analysis_plan(require_t1=False)

    def test_concurrent_log_append_preserves_every_row(self):
        with tempfile.TemporaryDirectory() as directory:
            context=multiprocessing.get_context('spawn')
            jobs=[context.Process(target=log_worker,args=(directory,i)) for i in range(4)]
            for job in jobs:job.start()
            for job in jobs:job.join(20);self.assertEqual(job.exitcode,0)
            with (Path(directory)/'run_log.csv').open(encoding='utf-8',newline='') as handle:rows=list(csv.DictReader(handle))
            self.assertEqual(len(rows),20)
            self.assertTrue(all(r['commit']=='parallel-test' for r in rows))


if __name__=='__main__':unittest.main()
