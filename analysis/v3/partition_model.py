"""Finite-support maximum-entropy models; no empirical data are read on import.

Identical feature patterns are combined with their multiplicities.  This is an
exact evaluation of the normalizer over every partition, not a sampled support.
"""
from __future__ import annotations

import os
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import linprog, minimize
from scipy.special import logsumexp, logit


@dataclass(frozen=True)
class FeatureSpace:
    """Coordinates standardized only against the complete theoretical support."""
    matrix: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    active_names: tuple[str, ...]
    dropped_names: tuple[str, ...]
    unique_matrix: np.ndarray
    multiplicities: np.ndarray
    pattern_index: np.ndarray
    rank: int

    @classmethod
    def from_raw(cls, raw_features: np.ndarray, feature_names: Sequence[str]) -> "FeatureSpace":
        raw = np.asarray(raw_features, dtype=float)
        names = tuple(feature_names)
        if raw.ndim != 2 or raw.shape[0] < 1 or raw.shape[1] != len(names):
            raise ValueError("Feature matrix and names do not describe a nonempty support")
        if len(set(names)) != len(names) or not np.isfinite(raw).all():
            raise ValueError("Features must be finite and names unique")
        mean, scale = raw.mean(axis=0), raw.std(axis=0)
        active = scale > 1e-12
        standardized = (raw[:, active] - mean[active]) / scale[active]
        unique, inverse, counts = np.unique(standardized, axis=0, return_inverse=True, return_counts=True)
        return cls(standardized, mean[active], scale[active],
                   tuple(n for n, a in zip(names, active) if a),
                   tuple(n for n, a in zip(names, active) if not a),
                   unique, counts.astype(float), inverse,
                   int(np.linalg.matrix_rank(standardized)) if standardized.shape[1] else 0)

    @property
    def n_support(self) -> int:
        return self.matrix.shape[0]

    @property
    def dimension(self) -> int:
        return self.matrix.shape[1]

    def metadata(self) -> dict:
        return {"active_names": list(self.active_names), "dropped_names": list(self.dropped_names),
                "mean": self.mean.tolist(), "scale": self.scale.tolist(),
                "support_size": self.n_support, "unique_feature_patterns": len(self.unique_matrix),
                "rank": self.rank, "parameters_identifiable": self.rank == self.dimension,
                "standardization": "complete_theoretical_support_population_sd"}


def objective_gradient(theta: np.ndarray, space: FeatureSpace,
                       target_mean: np.ndarray, alpha: float) -> tuple[float, np.ndarray]:
    """Weighted mean NLL + alpha*||theta||²/2, with an exact gradient."""
    theta = np.asarray(theta, dtype=float)
    target = np.asarray(target_mean, dtype=float)
    if theta.shape != (space.dimension,) or target.shape != theta.shape or alpha < 0:
        raise ValueError("Invalid parameter, moment, or penalty shape")
    linear = space.unique_matrix @ theta + np.log(space.multiplicities)
    log_z = logsumexp(linear)
    pattern_probability = np.exp(linear - log_z)
    value = log_z - theta @ target + alpha * (theta @ theta) / 2
    gradient = space.unique_matrix.T @ pattern_probability - target + alpha * theta
    return float(value), gradient


def finite_mle_check(space: FeatureSpace, target_mean: np.ndarray) -> dict:
    """Maximize a common minimum mass on every unique feature pattern.

    Writing each pattern mass as u_j+t avoids a large inequality matrix.  An
    optimizer solution at t=0 is on a face of the convex hull and has no finite
    ordinary MLE.  The frozen plan supplies the numerical positivity threshold.
    """
    target = np.asarray(target_mean, dtype=float)
    if target.shape != (space.dimension,) or not np.isfinite(target).all():
        raise ValueError("Invalid target feature moment")
    m = len(space.unique_matrix)
    threshold = 1e-9 / m
    if space.dimension == 0:
        return {"finite_mle": True, "minimum_pattern_weight": 1.0 / m,
                "threshold": threshold, "lp_success": True, "lp_status": 0,
                "unique_patterns": m, "message": "zero-dimensional support"}
    equality = np.vstack((np.ones(m), space.unique_matrix.T))
    equality = np.column_stack((equality, equality.sum(axis=1)))
    rhs = np.r_[1.0, target]
    objective = np.r_[np.zeros(m), -1.0]
    result = linprog(objective, A_eq=equality, b_eq=rhs, bounds=(0.0, None),
                     method="highs", options={"primal_feasibility_tolerance": 1e-9,
                                               "dual_feasibility_tolerance": 1e-9})
    value = float(result.x[-1]) if result.success and result.x is not None else None
    residual = float(np.max(np.abs(equality @ result.x - rhs))) if value is not None else None
    finite = bool(result.success and value is not None and value > threshold
                  and residual is not None and residual <= 1e-9)
    return {"finite_mle": finite, "minimum_pattern_weight": value,
            "threshold": threshold, "lp_success": bool(result.success),
            "lp_status": int(result.status), "unique_patterns": m,
            "max_equality_residual": residual, "message": str(result.message)}


@dataclass
class FitResult:
    theta: np.ndarray
    raw_coefficients: dict[str, float]
    probabilities: np.ndarray
    log_probabilities: np.ndarray
    converged: bool
    gradient_max: float
    normalization_error: float
    alpha: float
    objective: float
    diagnostics: dict


def _failed(space: FeatureSpace, alpha: float, diagnostics: dict) -> FitResult:
    return FitResult(np.full(space.dimension, np.nan),
                     {name: float("nan") for name in space.active_names},
                     np.full(space.n_support, np.nan), np.full(space.n_support, np.nan),
                     False, float("nan"), float("nan"), alpha, float("nan"), diagnostics)


def fit_maxent(space: FeatureSpace, partition_ids: np.ndarray,
               weights: np.ndarray | None = None, alpha: float = 0.0,
               maxiter: int = 2000, retry_maxiter: int = 10000,
               precision_retry: bool = False) -> FitResult:
    ids = np.asarray(partition_ids, dtype=int)
    if ids.ndim != 1 or not len(ids) or ids.min() < 0 or ids.max() >= space.n_support:
        raise ValueError("Invalid observed partition indices")
    weights = np.ones(len(ids), dtype=float) if weights is None else np.asarray(weights, dtype=float)
    if weights.shape != ids.shape or not np.isfinite(weights).all() or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Weights must be finite, nonnegative and have positive sum")
    if not np.isfinite(alpha) or alpha < 0:
        raise ValueError("Penalty must be finite and nonnegative")
    weights = weights / weights.sum()
    target = weights @ space.matrix[ids]
    diagnostics = {"target_mean": target.tolist(), "alpha": float(alpha),
                   "weighted_mean_objective": True, "feature_space": space.metadata(), "attempts": []}
    if alpha == 0:
        diagnostics["finite_mle"] = finite_mle_check(space, target)
        if not diagnostics["finite_mle"]["finite_mle"]:
            diagnostics["status"] = "nonfinite_mle_boundary"
            return _failed(space, alpha, diagnostics)
    if space.dimension == 0:
        log_p = np.full(space.n_support, -np.log(space.n_support))
        probabilities = np.exp(log_p)
        diagnostics["status"] = "analytic_uniform"
        return FitResult(np.empty(0), {}, probabilities, log_p, True, 0.0,
                         float(abs(probabilities.sum() - 1)), alpha, float(np.log(space.n_support)), diagnostics)
    initial = np.zeros(space.dimension)
    attempts = [(maxiter, 1e-12), (retry_maxiter, 1e-12)]
    if precision_retry:
        attempts.append((10000, 1e-15))
    for limit, ftol in dict.fromkeys(attempts):
        result = minimize(objective_gradient, initial.copy(), args=(space, target, alpha),
                          method="L-BFGS-B", jac=True,
                          options={"maxiter": int(limit), "ftol": ftol, "gtol": 1e-8, "maxls": 50})
        theta = np.asarray(result.x)
        value, gradient = objective_gradient(theta, space, target, alpha)
        grad_max = float(np.max(np.abs(gradient)))
        linear = space.matrix @ theta
        log_p = linear - logsumexp(linear)
        probabilities = np.exp(log_p)
        error = float(abs(probabilities.sum() - 1.0))
        finite = bool(np.isfinite(theta).all() and np.isfinite(value) and np.isfinite(grad_max)
                      and np.isfinite(log_p).all() and np.isfinite(probabilities).all())
        converged = bool(result.success and finite and grad_max <= 1e-6 and error < 1e-9)
        diagnostics["attempts"].append({"maxiter": int(limit), "ftol": ftol, "gtol": 1e-8,
                                        "solver_success": bool(result.success),
                                        "solver_status": int(result.status), "message": str(result.message),
                                        "iterations": int(result.nit), "objective": float(value),
                                        "gradient_max": grad_max, "normalization_error": error,
                                        "converged": converged})
        if converged:
            diagnostics["status"] = "converged"
            return FitResult(theta, {name: float(v) for name, v in zip(space.active_names, theta / space.scale)},
                             probabilities, log_p, True, grad_max, error, float(alpha), value, diagnostics)
    diagnostics["status"] = "optimizer_failed"
    return _failed(space, float(alpha), diagnostics)


def pair_probabilities(probabilities: np.ndarray, same_block_matrix: np.ndarray) -> np.ndarray:
    p = np.asarray(probabilities, dtype=float)
    indicators = np.asarray(same_block_matrix, dtype=float)
    if p.ndim != 1 or indicators.ndim != 2 or len(p) != len(indicators):
        raise ValueError("Partition probabilities and pair indicators disagree")
    if not np.isfinite(p).all() or np.any(p < 0) or abs(p.sum() - 1) >= 1e-9:
        raise ValueError("A converged normalized partition distribution is required")
    if not np.isin(indicators, [0.0, 1.0]).all():
        raise ValueError("Sharing indicators must be binary")
    return p @ indicators


def seven_cell_rates(pair_probs: np.ndarray, cell_codes: Sequence[str]) -> dict[str, float]:
    p = np.asarray(pair_probs, dtype=float)
    codes = np.asarray(cell_codes).astype(str)
    if p.shape != codes.shape or p.ndim != 1 or not np.isfinite(p).all():
        raise ValueError("Pair probabilities and difference cells disagree")
    return {code: float(p[codes == code].mean()) for code in sorted(set(codes))}


def m2_logit_contrasts(seven_rates: np.ndarray, design_matrix: np.ndarray,
                       names: Sequence[str]) -> dict:
    rates = np.asarray(seven_rates, dtype=float)
    design = np.asarray(design_matrix, dtype=float)
    if rates.ndim != 1 or design.shape != (len(rates), len(names)):
        raise ValueError("Difference-cell rates and M2 design disagree")
    if not np.isfinite(rates).all() or np.any(rates <= 0) or np.any(rates >= 1):
        raise ValueError("Finite logits require all probabilities strictly between zero and one")
    if np.linalg.matrix_rank(design) != len(names):
        raise ValueError("M2 contrast design must have full column rank")
    logits = logit(rates)
    coefficients = np.linalg.lstsq(design, logits, rcond=None)[0]
    residuals = logits - design @ coefficients
    return {"coefficients": {name: float(v) for name, v in zip(names, coefficients)},
            "residuals": residuals.tolist(), "max_abs_residual": float(np.max(np.abs(residuals))),
            "interpretation": "saturated projection residual is only a numerical check"}
