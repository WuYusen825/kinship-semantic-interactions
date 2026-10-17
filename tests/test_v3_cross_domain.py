"""T6纯测试：精确覆盖、条件权重、分离、sandwich与置换。"""
import sys
from itertools import combinations, product
from pathlib import Path
import unittest

import numpy as np
from scipy.special import logsumexp
from statsmodels.discrete.conditional_models import ConditionalLogit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/v3"))
from cross_domain import (FiniteDescriptionLanguage, _fit_objective,
                          exact_stratum_permutation, fit_conditional,
                          holm_two, metric_languages, relative_metrics,
                          sandwich_inference, separation_diagnostic)
from domain_feasibility import domain_registry
from languages import minimum_dnf


class DescriptionTests(unittest.TestCase):
    def test_all_255_eight_cell_costs_match_frozen_T1(self):
        language = FiniteDescriptionLanguage(list(product((0,1), repeat=3)))
        for mask in range(1,256):
            self.assertEqual(language.minimum_dnf(mask), minimum_dnf(mask,"abs"))

    def test_parity_requires_every_minterm_in_four_dimensions(self):
        coordinates=list(product((0,1),repeat=4))
        language=FiniteDescriptionLanguage(coordinates)
        mask=sum(1<<i for i,row in enumerate(coordinates) if sum(row)%2)
        self.assertEqual(language.minimum_dnf(mask),32)
        self.assertEqual(language.minimum_dnf(language.universe),0)

    def test_q_advantage_and_cross_parallel_are_different(self):
        entries=domain_registry()["cousins16"]
        languages=metric_languages(entries,("s","p","c","r"))
        q=relative_metrics([row["s"]^row["r"] for row in entries],languages)
        cross=relative_metrics([row["p"]^row["c"] for row in entries],languages)
        self.assertEqual((q["dl_abs"],q["dl_rel_r"],q["delta_dl_r"]),(8,2,6))
        self.assertEqual(q["q_advantage_r"],1)
        self.assertTrue(cross["abs_nonconj"])
        self.assertEqual(cross["q_advantage_r"],0)
        self.assertEqual(cross["delta_dl_r"],0)

    def test_negative_advantage_is_preserved(self):
        entries=domain_registry()["cousins16"]
        languages=metric_languages(entries,("s","p","c","r"))
        metrics=relative_metrics([row["s"] for row in entries],languages)
        self.assertLess(metrics["delta_dl_r"],0)
        self.assertEqual(metrics["q_advantage_r"],0)
        self.assertEqual(metrics["delta_dl_s"],0)

    def test_dnf_allows_overlapping_terms(self):
        coordinates=list(product((0,1),repeat=3))
        language=FiniteDescriptionLanguage(coordinates)
        mask=sum(1<<i for i,(s,a,r) in enumerate(coordinates) if s==0 and (a==0 or r==0))
        self.assertEqual(language.minimum_dnf(mask),4)
        self.assertNotIn(mask,language.terms)


class ConditionalInferenceTests(unittest.TestCase):
    def test_conditioned_score_matches_enumerated_subsets(self):
        z=np.array([[0,0,1],[1,0,0],[0,1,0],[1,1,1]],dtype=float)
        y=np.array([1,0,0,1]); beta=np.array([.2,-.3,.4])
        model=ConditionalLogit(y,z,groups=np.array(["g"]*4))
        sufficient=np.array([z[list(indices)].sum(axis=0) for indices in combinations(range(4),2)])
        logits=sufficient@beta; probability=np.exp(logits-logsumexp(logits))
        expected_score=y@z-probability@sufficient
        expected_ll=(y@z)@beta-logsumexp(logits)
        np.testing.assert_allclose(model.score_grp(0,beta),expected_score,atol=1e-12)
        self.assertAlmostEqual(model.loglike_grp(0,beta),expected_ll)

    def test_per_family_average_controls_optimization(self):
        # 两个组的原始信息不同；传入LL/n后应等组优化，非按原始规模加权。
        def first(beta):
            return -.5*float((beta[0]-1)**2),np.array([1-beta[0]])
        def second(beta):
            return -.5*float((beta[0]-3)**2),np.array([3-beta[0]])
        result=_fit_objective([first,second],1)
        self.assertTrue(result["accepted"])
        self.assertAlmostEqual(result["parameters"][0],2,places=7)
        self.assertAlmostEqual(result["information"][0,0],1,places=6)

    def test_sandwich_invariant_to_common_weight_scale(self):
        beta=np.array([.3,.1,.2]); h=np.diag([2.,3.,4.])
        scores=np.array([[.2,.1,0],[-.1,-.2,.1],[-.1,.1,-.1]])
        first=sandwich_inference(beta,scores,h)
        second=sandwich_inference(beta,scores*7,h*7)
        np.testing.assert_allclose(first["covariance"],second["covariance"],atol=1e-14)
        self.assertEqual(first["df"],2)

    def test_box_lp_detects_complete_and_quasi_separation(self):
        self.assertTrue(separation_diagnostic([[1,0],[2,1]])["separated"])
        self.assertTrue(separation_diagnostic([[0,0],[1,0]])["separated"])
        self.assertFalse(separation_diagnostic([[1,0],[-1,0],[0,1],[0,-1]])["separated"])

    def test_no_outcome_variation_and_rank_failure_remain_NA(self):
        records=[{"family_group":"g","X":i,"Y":0,"k_sibling":2,"k_domain":2} for i in (0,1)]
        self.assertEqual(fit_conditional(records)["status"],"not_estimable_no_within_family_outcome_variation")
        records[1]["Y"]=1
        self.assertEqual(fit_conditional(records)["status"],"not_estimable_rank_deficient_controls_retained")


class PermutationTests(unittest.TestCase):
    def record(self,identifier,x,y,ks=2,kd=3,family="g"):
        return {"Language_ID":identifier,"family_group":family,"X":x,"Y":y,"k_sibling":ks,"k_domain":kd}

    def test_exact_strata_and_noninformative_not_p_one(self):
        records=[self.record("a",0,0,ks=2),self.record("b",1,1,ks=3)]
        result=exact_stratum_permutation(records,100)
        self.assertEqual(result["status"],"not_identifiable_no_informative_strata")
        self.assertIsNone(result["p_two_sided"])

    def test_balanced_two_case_swap_has_two_signed_statistics(self):
        records=[self.record("a",0,0),self.record("b",1,1)]
        first=exact_stratum_permutation(records,1000)
        second=exact_stratum_permutation(records,1000)
        self.assertEqual(first,second)
        self.assertEqual(first["unique_permutation_statistics"],2)
        self.assertEqual(first["statistic"],.5)
        self.assertEqual(first["p_two_sided"],1)

    def test_covariance_centers_within_each_exact_stratum(self):
        records=[self.record(str(i),x,y) for i,(x,y) in enumerate([(0,0),(0,0),(1,1),(1,1)])]
        result=exact_stratum_permutation(records,5000)
        self.assertAlmostEqual(result["statistic"],1)
        self.assertEqual(result["informative_systems"],4)
        self.assertEqual(sum(row["count"] for row in result["permutation_distribution"]),5000)
        self.assertTrue(.30<result["p_two_sided"]<.37)

    def test_holm_two_retains_missing_test_in_family(self):
        self.assertEqual(holm_two([.02,None]),[.04,None])
        self.assertEqual(holm_two([.02,.03]),[.04,.04])


if __name__=="__main__":
    unittest.main(verbosity=2)
