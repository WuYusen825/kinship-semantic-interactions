"""复现工具的实质核查：不能把统计变化当作可忽略元数据。"""
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis/v3'))
from run_all import child_environment, selected_stages
from verify_reproduction import Comparison, compare_roots


class ReproductionTests(unittest.TestCase):
    def test_bootstrap_requires_only_standard_library(self):
        script=Path(__file__).resolve().parents[1]/'analysis/v3/clean_reproduce.py'
        run=subprocess.run([sys.executable,'-S',str(script),'--help'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn('--prepare-only',run.stdout)
    def test_dependency_order_and_interval(self):
        names=[s.name for s in selected_stages()]
        self.assertLess(names.index('t1'),names.index('t2_cv'))
        self.assertLess(names.index('t5_strict'),names.index('t2_compare'))
        self.assertLess(names.index('t5_full'),names.index('t2_compare'))
        self.assertEqual([s.name for s in selected_stages('t5_strict','t2_compare')],['t5_strict','t5_full','t5_verify','t2_compare'])
        with self.assertRaises(ValueError):selected_stages('t7','t0')

    def test_child_threads_and_seed(self):
        env=child_environment()
        self.assertEqual(env['OPENBLAS_NUM_THREADS'],'1')
        self.assertEqual(env['PYTHONHASHSEED'],'20261016')

    def test_exact_counts_and_float_tolerance(self):
        compare=Comparison()
        compare.object({'count':625,'loss':.123456789},{'count':625,'loss':.1234567890001})
        self.assertEqual(compare.total_differences,0)
        compare.object({'count':625},{'count':626})
        self.assertEqual(compare.total_differences,1)
        compare.object({'loss':.5},{'loss':.50001})
        self.assertEqual(compare.total_differences,2)

    def test_only_named_metadata_separated(self):
        compare=Comparison()
        compare.object({'started_utc':'a','source_sha256':{'x':'old'},'seed':20261016,'replicates':5000},
                       {'started_utc':'b','source_sha256':{'x':'new'},'seed':20261016,'replicates':5000})
        self.assertEqual(compare.total_differences,0)
        self.assertEqual(len(compare.metadata_differences),2)
        compare.object({'replicates':5000},{'replicates':4999})
        self.assertEqual(compare.total_differences,1)

    def test_missing_keys_and_boolean_are_failures(self):
        compare=Comparison()
        compare.object({'passed':True,'count':625},{'passed':False})
        self.assertEqual(compare.total_differences,2)
        compare.scalar(True,1,'passed')
        self.assertEqual(compare.total_differences,3)

    def test_rgs_leading_zero_is_not_discarded(self):
        compare=Comparison()
        compare.csv_cell('00000000','0','rgs')
        compare.csv_cell('01010101','1010101','rgs')
        self.assertEqual(compare.total_differences,2)

    def test_historical_diagnostics_additions_must_match_planned_settings(self):
        compare=Comparison()
        location='results/t2/initial_solver/cv/diagnostics/attempts/0'
        compare.object({'iterations':11},{'iterations':11,'ftol':1e-12,'gtol':1e-8},location)
        self.assertEqual(compare.total_differences,0)
        compare.object({'iterations':11},{'iterations':11,'ftol':1e-9},location)
        self.assertEqual(compare.total_differences,1)

    def test_gzip_csv_and_row_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            first,second=Path(tmp)/'a.csv.gz',Path(tmp)/'b.csv.gz'
            for path,rows in [(first,[['rgs','loss'],['00000000','.5'],['01010101','.7']]),
                              (second,[['rgs','loss'],['00000000','.500000000001'],['01010101','.7']])]:
                with gzip.open(path,'wt',newline='') as h:csv.writer(h).writerows(rows)
            compare=Comparison()
            self.assertTrue(compare.file(first,second,'test.csv.gz'))
            with gzip.open(second,'wt',newline='') as h:csv.writer(h).writerows([['rgs','loss'],['01010101','.7'],['00000000','.5']])
            self.assertFalse(compare.file(first,second,'test.csv.gz'))

    def test_code_input_drift_cannot_be_hidden_by_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            first,second=Path(tmp)/'a',Path(tmp)/'b'
            for root in (first,second):
                (root/'analysis/v3').mkdir(parents=True)
                (root/'results/t1').mkdir(parents=True)
                (root/'analysis/v3/example.py').write_text('original')
                (root/'results/t1/summary.json').write_text(json.dumps({'count':4140}))
            same=compare_roots(first,second,require_all=False)
            self.assertTrue(same['passed'])
            (second/'analysis/v3/example.py').write_text('changed')
            different=compare_roots(first,second,require_all=False)
            self.assertFalse(different['passed'])
            self.assertEqual(len(different['source_differences']),1)

    def test_incomplete_results_cannot_pass_complete_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=compare_roots(root,root)
            self.assertFalse(result['passed'])
            self.assertEqual(len(result['absent_required_stages']),8)


if __name__=='__main__':unittest.main()
