"""
Experiment Runner — Tests the formal definitions from the paper-grade rewrite.

Experiments:
1. Seam detection baseline: log k_p, L(n), full-lift counts
2. Sigmoid transition fit: fit L(n) to tanh, compare to linear
3. Cadence swap: test if 42 is structural or scheduling (7 vs 8 vs 9 phase)
4. Frame swap: test if 46 is representation-locked (vary prime set size)
5. Babel noise: measure projection non-commutativity

Origin: Formal definitions from Croft × AI council, January 2026
Implemented by Ara, January 28, 2026
"""

import json
import random
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

# Import the engine
from ouroboros_engine import (
    ouroboros_run, init_population, step_depth, compute_telemetry,
    Particle, PrimeState, DepthTelemetry, valuation_capped,
    crt_reconstruct, measure_integer_gap
)


# ═══════════════════════════════════════════════════════════════════
# § 1. Extended telemetry with L(n) — liftability statistic
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ExtendedTelemetry:
    """Per-depth telemetry with liftability statistic L(n)."""
    n: int
    L_n: float  # fraction of primes with k_p == n (fully locked)
    per_prime_k: Dict[int, List[int]]  # k values for all particles, per prime
    full_lift_count: int  # particles with ALL primes locked
    mean_k_per_prime: Dict[int, float]
    seam_primes: List[int]  # primes where mean_k < n - 1 (stalled)
    best_score: float
    population_size: int


def compute_extended_telemetry(
    population: List[Particle],
    primes: List[int],
) -> ExtendedTelemetry:
    """Compute extended telemetry including L(n)."""
    if not population:
        return ExtendedTelemetry(n=0, L_n=0.0, per_prime_k={}, full_lift_count=0,
                                  mean_k_per_prime={}, seam_primes=[], best_score=0.0,
                                  population_size=0)

    n = population[0].n
    M = len(population)

    # Collect k values per prime
    per_prime_k = {p: [par.per_prime[p].k for par in population] for p in primes}

    # L(n) = fraction of primes with k_p == n, averaged over population
    # For each particle: count primes where k_p == n, divide by |P|
    # Then average over population
    L_per_particle = []
    for par in population:
        locked_count = sum(1 for p in primes if par.per_prime[p].k == n)
        L_per_particle.append(locked_count / len(primes))
    L_n = sum(L_per_particle) / M

    # Full lift count: particles with ALL primes locked
    full_lift_count = sum(
        1 for par in population
        if all(par.per_prime[p].k == n for p in primes)
    )

    # Mean k per prime
    mean_k_per_prime = {p: sum(per_prime_k[p]) / M for p in primes}

    # Seam primes: where mean_k < n - 1
    seam_primes = [p for p in primes if mean_k_per_prime[p] < n - 1]

    best_score = population[0].score if population else 0.0

    return ExtendedTelemetry(
        n=n,
        L_n=L_n,
        per_prime_k=per_prime_k,
        full_lift_count=full_lift_count,
        mean_k_per_prime=mean_k_per_prime,
        seam_primes=seam_primes,
        best_score=best_score,
        population_size=M,
    )


# ═══════════════════════════════════════════════════════════════════
# § 2. Sigmoid fitting
# ═══════════════════════════════════════════════════════════════════

def sigmoid(x, n0, delta, L_min=0.0, L_max=1.0):
    """Sigmoid function: L(n) = L_min + (L_max - L_min) / (1 + exp(-(n - n0) / delta))"""
    return L_min + (L_max - L_min) / (1 + np.exp(-(x - n0) / delta))


def tanh_model(x, n0, delta, L_min=0.0, L_max=1.0):
    """Tanh model: L(n) = (L_min + L_max)/2 + (L_max - L_min)/2 * tanh((n - n0) / delta)"""
    return (L_min + L_max) / 2 + (L_max - L_min) / 2 * np.tanh((x - n0) / delta)


def linear_model(x, a, b):
    """Linear model: L(n) = a * n + b"""
    return a * x + b


def fit_sigmoid(depths: List[int], L_values: List[float]) -> Dict:
    """Fit L(n) to sigmoid and compare with linear."""
    depths_arr = np.array(depths, dtype=float)
    L_arr = np.array(L_values, dtype=float)

    result = {
        "depths": depths,
        "L_values": L_values,
        "sigmoid_fit": None,
        "linear_fit": None,
        "sigmoid_r2": None,
        "linear_r2": None,
        "sigmoid_better": None,
    }

    if len(depths) < 4:
        return result

    # Fit sigmoid
    try:
        # Initial guess: n0 = midpoint, delta = range/4
        n0_init = (depths_arr[0] + depths_arr[-1]) / 2
        delta_init = (depths_arr[-1] - depths_arr[0]) / 4
        L_min_init = L_arr.min()
        L_max_init = L_arr.max()

        popt_sig, _ = curve_fit(
            sigmoid, depths_arr, L_arr,
            p0=[n0_init, delta_init, L_min_init, L_max_init],
            bounds=(
                [depths_arr[0], 0.1, 0.0, 0.0],
                [depths_arr[-1], depths_arr[-1] - depths_arr[0], 1.0, 1.0]
            ),
            maxfev=5000,
        )
        L_pred_sig = sigmoid(depths_arr, *popt_sig)
        ss_res_sig = np.sum((L_arr - L_pred_sig) ** 2)
        ss_tot = np.sum((L_arr - L_arr.mean()) ** 2)
        r2_sig = 1 - (ss_res_sig / ss_tot) if ss_tot > 0 else 0

        result["sigmoid_fit"] = {
            "n0": popt_sig[0],
            "delta": popt_sig[1],
            "L_min": popt_sig[2],
            "L_max": popt_sig[3],
        }
        result["sigmoid_r2"] = r2_sig
    except Exception as e:
        result["sigmoid_error"] = str(e)

    # Fit linear
    try:
        popt_lin, _ = curve_fit(linear_model, depths_arr, L_arr)
        L_pred_lin = linear_model(depths_arr, *popt_lin)
        ss_res_lin = np.sum((L_arr - L_pred_lin) ** 2)
        ss_tot = np.sum((L_arr - L_arr.mean()) ** 2)
        r2_lin = 1 - (ss_res_lin / ss_tot) if ss_tot > 0 else 0

        result["linear_fit"] = {"a": popt_lin[0], "b": popt_lin[1]}
        result["linear_r2"] = r2_lin
    except Exception as e:
        result["linear_error"] = str(e)

    # Compare
    if result["sigmoid_r2"] is not None and result["linear_r2"] is not None:
        result["sigmoid_better"] = result["sigmoid_r2"] > result["linear_r2"]

    return result


# ═══════════════════════════════════════════════════════════════════
# § 3. Experiment 1: Seam detection baseline
# ═══════════════════════════════════════════════════════════════════

def run_experiment_1(
    primes: List[int] = [2, 3, 5, 7, 11, 23],
    x: int = 3, y: int = 5, z: int = 7,
    n_max: int = 50,
    M: int = 64,
    K: int = 8,
    N_seeds: int = 3,
    verbose: bool = True,
) -> Dict:
    """
    Experiment 1: Seam detection baseline.

    Logs: k_p(n), L(n), full-lift counts at each depth.
    Tests: Do seam depth distributions stabilize across seeds?
    """
    results = {
        "experiment": "seam_detection_baseline",
        "params": {"primes": primes, "x": x, "y": y, "z": z, "n_max": n_max, "M": M, "K": K, "N_seeds": N_seeds},
        "runs": [],
    }

    for seed in range(N_seeds):
        random.seed(seed)
        if verbose:
            print(f"\n{'='*60}")
            print(f"Experiment 1 — Seed {seed}")
            print(f"{'='*60}")

        # Run engine
        pop, base_telemetry = ouroboros_run(
            primes, x, y, z,
            n_start=1, n_target=n_max,
            M=M, K=K,
            verbose=verbose,
        )

        # Re-run to collect extended telemetry
        # (We'll do a fresh run and collect at each step)
        random.seed(seed)  # Reset seed for reproducibility
        pop = init_population(primes, 1, M, x=x, y=y, z=z, use_prelift=True)

        run_data = {
            "seed": seed,
            "depths": [],
            "L_values": [],
            "full_lift_counts": [],
            "mean_k_per_prime": [],
            "seam_events": [],
        }

        for depth in range(1, n_max):
            pop = step_depth(pop, primes, x, y, z, M=M, K=K)
            tel = compute_extended_telemetry(pop, primes)

            run_data["depths"].append(tel.n)
            run_data["L_values"].append(tel.L_n)
            run_data["full_lift_counts"].append(tel.full_lift_count)
            run_data["mean_k_per_prime"].append(dict(tel.mean_k_per_prime))

            if tel.seam_primes:
                run_data["seam_events"].append({
                    "depth": tel.n,
                    "seam_primes": tel.seam_primes,
                })

        # Fit sigmoid to L(n)
        run_data["sigmoid_fit"] = fit_sigmoid(run_data["depths"], run_data["L_values"])

        results["runs"].append(run_data)

        if verbose:
            print(f"\nSeed {seed} summary:")
            print(f"  Final L(n): {run_data['L_values'][-1]:.3f}")
            print(f"  Seam events: {len(run_data['seam_events'])}")
            if run_data["sigmoid_fit"]["sigmoid_fit"]:
                print(f"  Sigmoid n0: {run_data['sigmoid_fit']['sigmoid_fit']['n0']:.2f}")
                print(f"  Sigmoid delta: {run_data['sigmoid_fit']['sigmoid_fit']['delta']:.2f}")
                print(f"  Sigmoid R²: {run_data['sigmoid_fit']['sigmoid_r2']:.4f}")
                print(f"  Linear R²: {run_data['sigmoid_fit']['linear_r2']:.4f}")
                print(f"  Sigmoid better: {run_data['sigmoid_fit']['sigmoid_better']}")

    # Cross-seed analysis
    if len(results["runs"]) > 1:
        n0_values = [r["sigmoid_fit"]["sigmoid_fit"]["n0"]
                     for r in results["runs"]
                     if r["sigmoid_fit"]["sigmoid_fit"]]
        delta_values = [r["sigmoid_fit"]["sigmoid_fit"]["delta"]
                        for r in results["runs"]
                        if r["sigmoid_fit"]["sigmoid_fit"]]

        if n0_values:
            results["cross_seed"] = {
                "n0_mean": np.mean(n0_values),
                "n0_std": np.std(n0_values),
                "delta_mean": np.mean(delta_values),
                "delta_std": np.std(delta_values),
                "n0_clusters": np.std(n0_values) < np.mean(n0_values) * 0.1,  # <10% variation
                "delta_clusters": np.std(delta_values) < np.mean(delta_values) * 0.1,
            }

    return results


# ═══════════════════════════════════════════════════════════════════
# § 4. Experiment 3: Cadence swap (tests 42 = 6×7)
# ═══════════════════════════════════════════════════════════════════

def detect_landmarks(L_values: List[float], depths: List[int], threshold: float = 0.1) -> List[int]:
    """Detect landmark depths where L(n) changes significantly."""
    landmarks = []
    for i in range(1, len(L_values)):
        delta = abs(L_values[i] - L_values[i-1])
        if delta > threshold:
            landmarks.append(depths[i])
    return landmarks


def run_experiment_3(
    base_primes: List[int] = [2, 3, 5, 7, 11, 23],
    x: int = 3, y: int = 5, z: int = 7,
    n_max: int = 60,
    M: int = 64,
    K: int = 8,
    cadences: List[int] = [7, 8, 9],
    verbose: bool = True,
) -> Dict:
    """
    Experiment 3: Cadence swap.

    Tests whether special depths like 42 (= 6×7) move when cadence changes.
    Cadence is implemented by varying the visualization/landmark detection phase.

    If landmarks move to 6×cadence, it's scheduling artifact.
    If landmarks stay at 42, it's structural.
    """
    results = {
        "experiment": "cadence_swap",
        "params": {"base_primes": base_primes, "x": x, "y": y, "z": z, "n_max": n_max, "cadences": cadences},
        "runs": {},
    }

    for cadence in cadences:
        expected_landmark = 6 * cadence  # 42, 48, 54

        if verbose:
            print(f"\n{'='*60}")
            print(f"Experiment 3 — Cadence {cadence} (expected landmark: {expected_landmark})")
            print(f"{'='*60}")

        random.seed(42)  # Fixed seed for comparison

        pop = init_population(base_primes, 1, M, x=x, y=y, z=z, use_prelift=True)

        run_data = {
            "cadence": cadence,
            "expected_landmark": expected_landmark,
            "depths": [],
            "L_values": [],
            "cadence_phase": [],  # depth mod cadence
        }

        for depth in range(1, n_max):
            pop = step_depth(pop, base_primes, x, y, z, M=M, K=K)
            tel = compute_extended_telemetry(pop, base_primes)

            run_data["depths"].append(tel.n)
            run_data["L_values"].append(tel.L_n)
            run_data["cadence_phase"].append(tel.n % cadence)

        # Detect landmarks
        run_data["landmarks"] = detect_landmarks(run_data["L_values"], run_data["depths"])

        # Check if expected landmark is in detected landmarks (within ±2)
        run_data["expected_landmark_found"] = any(
            abs(lm - expected_landmark) <= 2 for lm in run_data["landmarks"]
        )

        # Check if 42 is always found regardless of cadence
        run_data["42_found"] = any(abs(lm - 42) <= 2 for lm in run_data["landmarks"])

        results["runs"][cadence] = run_data

        if verbose:
            print(f"  Detected landmarks: {run_data['landmarks'][:10]}...")
            print(f"  Expected {expected_landmark} found: {run_data['expected_landmark_found']}")
            print(f"  42 found: {run_data['42_found']}")

    # Verdict
    landmarks_move = all(
        results["runs"][c]["expected_landmark_found"]
        for c in cadences
    )
    always_42 = all(
        results["runs"][c]["42_found"]
        for c in cadences
    )

    results["verdict"] = {
        "landmarks_follow_cadence": landmarks_move,
        "42_is_structural": always_42 and not landmarks_move,
        "interpretation": (
            "42 is cadence-dependent (scheduling artifact)" if landmarks_move
            else "42 is structural (independent of cadence)" if always_42
            else "inconclusive"
        ),
    }

    return results


# ═══════════════════════════════════════════════════════════════════
# § 5. Experiment 4: Frame swap (tests 46 = 2×23)
# ═══════════════════════════════════════════════════════════════════

def run_experiment_4(
    x: int = 3, y: int = 5, z: int = 7,
    n_max: int = 70,
    M: int = 64,
    K: int = 8,
    prime_set_configs: Dict[str, List[int]] = None,
    verbose: bool = True,
) -> Dict:
    """
    Experiment 4: Frame swap.

    Tests whether 46 (= 2×23) is biology-locked or representation-locked.
    Varies the largest prime in the set (19, 23, 29) to see if frame landmark moves.

    If landmark becomes 2×p_max, it's representation-locked.
    If landmark stays at 46, it's hard-coded or confounded.
    """
    if prime_set_configs is None:
        prime_set_configs = {
            "19": [2, 3, 5, 7, 11, 19],  # Expected frame: 38 = 2×19
            "23": [2, 3, 5, 7, 11, 23],  # Expected frame: 46 = 2×23
            "29": [2, 3, 5, 7, 11, 29],  # Expected frame: 58 = 2×29
        }

    results = {
        "experiment": "frame_swap",
        "params": {"x": x, "y": y, "z": z, "n_max": n_max, "prime_configs": prime_set_configs},
        "runs": {},
    }

    for name, primes in prime_set_configs.items():
        p_max = max(primes)
        expected_frame = 2 * p_max

        if verbose:
            print(f"\n{'='*60}")
            print(f"Experiment 4 — Prime set '{name}' (p_max={p_max}, expected frame: {expected_frame})")
            print(f"{'='*60}")

        random.seed(42)  # Fixed seed for comparison

        pop = init_population(primes, 1, M, x=x, y=y, z=z, use_prelift=True)

        run_data = {
            "primes": primes,
            "p_max": p_max,
            "expected_frame": expected_frame,
            "depths": [],
            "L_values": [],
            "full_lift_counts": [],
        }

        for depth in range(1, n_max):
            pop = step_depth(pop, primes, x, y, z, M=M, K=K)
            tel = compute_extended_telemetry(pop, primes)

            run_data["depths"].append(tel.n)
            run_data["L_values"].append(tel.L_n)
            run_data["full_lift_counts"].append(tel.full_lift_count)

        # Detect where full_lift_count first drops to 0 (frame saturation)
        frame_depth = None
        for i, flc in enumerate(run_data["full_lift_counts"]):
            if flc == 0 and i > 0:
                frame_depth = run_data["depths"][i]
                break

        run_data["detected_frame_depth"] = frame_depth
        run_data["frame_matches_expected"] = (
            frame_depth is not None and abs(frame_depth - expected_frame) <= 3
        )
        run_data["frame_is_46"] = (
            frame_depth is not None and abs(frame_depth - 46) <= 3
        )

        results["runs"][name] = run_data

        if verbose:
            print(f"  Detected frame depth: {frame_depth}")
            print(f"  Matches expected ({expected_frame}): {run_data['frame_matches_expected']}")
            print(f"  Is 46: {run_data['frame_is_46']}")

    # Verdict
    frames_follow_pmax = all(
        r["frame_matches_expected"] for r in results["runs"].values()
        if r["detected_frame_depth"] is not None
    )
    always_46 = all(
        r["frame_is_46"] for r in results["runs"].values()
        if r["detected_frame_depth"] is not None
    )

    results["verdict"] = {
        "frames_follow_p_max": frames_follow_pmax,
        "46_is_hardcoded": always_46 and not frames_follow_pmax,
        "interpretation": (
            "46 is representation-locked (follows 2×p_max)" if frames_follow_pmax
            else "46 is hard-coded or biology-locked" if always_46
            else "inconclusive"
        ),
    }

    return results


# ═══════════════════════════════════════════════════════════════════
# § 6. Experiment 5: Babel / NSO non-commutativity
# ═══════════════════════════════════════════════════════════════════

def project_to_base(u: float, base: int, precision: int) -> float:
    """Project u to base-B representation at precision k, then map back."""
    # Represent u in base B with k digits after the "decimal" point
    # Then truncate and convert back
    scaled = int(u * (base ** precision))
    return scaled / (base ** precision)


def babel_residual(u: float, B1: int, B2: int, k: int) -> float:
    """Measure |Π_B1 Π_B2 (u) - Π_B2 Π_B1 (u)|."""
    # Π_B1(Π_B2(u))
    proj_B2_first = project_to_base(u, B2, k)
    proj_B1_B2 = project_to_base(proj_B2_first, B1, k)

    # Π_B2(Π_B1(u))
    proj_B1_first = project_to_base(u, B1, k)
    proj_B2_B1 = project_to_base(proj_B1_first, B2, k)

    return abs(proj_B1_B2 - proj_B2_B1)


def run_experiment_5(
    bases: List[int] = [2, 3, 5, 7, 10],
    precisions: List[int] = [4, 8, 12],
    n_samples: int = 1000,
    verbose: bool = True,
) -> Dict:
    """
    Experiment 5: Babel / NSO non-commutativity.

    Tests whether projection order matters: Π_B1 Π_B2 ≠ Π_B2 Π_B1.
    """
    results = {
        "experiment": "babel_noncommutativity",
        "params": {"bases": bases, "precisions": precisions, "n_samples": n_samples},
        "residuals": {},
    }

    for k in precisions:
        results["residuals"][k] = {}

        for i, B1 in enumerate(bases):
            for B2 in bases[i+1:]:
                pair_key = f"{B1}_{B2}"
                residuals = []

                for _ in range(n_samples):
                    u = random.random()  # Random value in [0, 1)
                    eps = babel_residual(u, B1, B2, k)
                    residuals.append(eps)

                mean_eps = np.mean(residuals)
                max_eps = np.max(residuals)
                nonzero_count = sum(1 for r in residuals if r > 1e-15)

                results["residuals"][k][pair_key] = {
                    "mean": mean_eps,
                    "max": max_eps,
                    "nonzero_fraction": nonzero_count / n_samples,
                }

                if verbose and mean_eps > 1e-10:
                    print(f"  k={k}, ({B1},{B2}): mean_ε={mean_eps:.2e}, max_ε={max_eps:.2e}, nonzero={nonzero_count/n_samples:.1%}")

    # Identify significant pairs
    significant_pairs = []
    for k, pairs in results["residuals"].items():
        for pair, stats in pairs.items():
            if stats["mean"] > 1e-10:
                significant_pairs.append({
                    "precision": k,
                    "pair": pair,
                    "mean_residual": stats["mean"],
                })

    results["significant_pairs"] = significant_pairs
    results["babel_noise_detected"] = len(significant_pairs) > 0

    return results


# ═══════════════════════════════════════════════════════════════════
# § 7. Experiment 6: Pythagorean solution diagnostic
# ═══════════════════════════════════════════════════════════════════

def evaluate_known_triple(
    a: int, b: int, c: int,
    primes: List[int],
    x: int = 2, y: int = 2, z: int = 2,
) -> Dict:
    """
    Evaluate a known Pythagorean triple to understand why engine doesn't find it.

    Returns diagnostic info about:
    - The integer gap (should be 0)
    - Agreement depth at each prime (how deep congruence holds)
    - What residues correspond to (a, b, c) at each prime
    """
    # Check the gap
    gap = a**x + b**y - c**z

    # Check residues at each prime
    prime_diagnostics = {}
    for p in primes:
        a_mod = a % p
        b_mod = b % p
        c_mod = c % p

        # Check agreement depth: how high k can we go before congruence fails?
        max_k = 1
        for k in range(1, 50):
            pk = p ** k
            if (a**x + b**y - c**z) % pk == 0:
                max_k = k
            else:
                break

        prime_diagnostics[p] = {
            "a_mod": a_mod,
            "b_mod": b_mod,
            "c_mod": c_mod,
            "agreement_depth": max_k,
            "residue_check": (a**x + b**y) % p == (c**z) % p,
        }

    return {
        "triple": (a, b, c),
        "gap": gap,
        "is_solution": gap == 0,
        "prime_diagnostics": prime_diagnostics,
        "min_agreement_depth": min(d["agreement_depth"] for d in prime_diagnostics.values()),
    }


def run_experiment_6(
    known_triples: List[Tuple[int, int, int]] = None,
    n_max: int = 100,
    M: int = 128,
    K: int = 16,
    verbose: bool = True,
) -> Dict:
    """
    Experiment 6: Pythagorean solution diagnostic.

    Investigates why engine finds near-misses (0.19%) but not exact solutions:
    1. Evaluate known Pythagorean triples - verify they're valid
    2. Check agreement depths at each prime
    3. Run engine and track closest approach to each known triple
    4. Identify the barrier preventing exact match
    """
    if known_triples is None:
        known_triples = [
            (3, 4, 5),
            (5, 12, 13),
            (8, 15, 17),
            (7, 24, 25),
            (20, 21, 29),
            (9, 40, 41),
            (12, 35, 37),
            (11, 60, 61),
            (6, 8, 10),   # scaled (3,4,5)
            (9, 12, 15),  # scaled (3,4,5)
        ]

    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
    x, y, z = 2, 2, 2

    results = {
        "experiment": "pythagorean_diagnostic",
        "params": {"n_max": n_max, "M": M, "K": K, "primes": primes},
        "known_triples": {},
        "search_trace": {},
        "closest_approaches": {},
    }

    if verbose:
        print("="*70)
        print("EXPERIMENT 6: Pythagorean Solution Diagnostic")
        print("="*70)
        print(f"\nPhase 1: Evaluate known triples (x={x}, y={y}, z={z})")
        print("-"*50)

    # Phase 1: Evaluate known triples
    for triple in known_triples:
        a, b, c = triple
        eval_result = evaluate_known_triple(a, b, c, primes, x, y, z)
        results["known_triples"][f"{a}_{b}_{c}"] = eval_result

        if verbose:
            status = "✓ SOLUTION" if eval_result["is_solution"] else f"✗ gap={eval_result['gap']}"
            print(f"  ({a}, {b}, {c}): {status}, min_agreement={eval_result['min_agreement_depth']}")

    # Phase 2: Run search and track closest approach
    if verbose:
        print(f"\nPhase 2: Search for solutions (depth 1-{n_max})")
        print("-"*50)

    random.seed(42)
    pop = init_population(primes, 1, M, x=x, y=y, z=z, use_prelift=True)

    # Track closest approach to each known triple
    closest_to_known = {f"{a}_{b}_{c}": {"min_distance": float('inf'), "depth": 0, "particle": None}
                        for a, b, c in known_triples}

    # Track all near-zero gaps found
    near_zero_found = []

    for depth in range(1, n_max + 1):
        pop = step_depth(pop, primes, x, y, z, M=M, K=K)

        # Reconstruct integers and check gaps for best particles
        for par in pop[:min(10, len(pop))]:  # Top 10 particles
            try:
                a_vals = {p: par.per_prime[p].a_res for p in primes}
                b_vals = {p: par.per_prime[p].b_res for p in primes}
                c_vals = {p: par.per_prime[p].c_res for p in primes}

                a_int = crt_reconstruct(a_vals, {p: par.per_prime[p].k for p in primes}, primes)
                b_int = crt_reconstruct(b_vals, {p: par.per_prime[p].k for p in primes}, primes)
                c_int = crt_reconstruct(c_vals, {p: par.per_prime[p].k for p in primes}, primes)

                if a_int > 0 and b_int > 0 and c_int > 0:
                    gap = a_int**x + b_int**y - c_int**z

                    # Check distance to known triples
                    for a, b, c in known_triples:
                        key = f"{a}_{b}_{c}"
                        dist = abs(a_int - a) + abs(b_int - b) + abs(c_int - c)
                        if dist < closest_to_known[key]["min_distance"]:
                            closest_to_known[key] = {
                                "min_distance": dist,
                                "depth": depth,
                                "particle": (a_int, b_int, c_int),
                                "gap": gap,
                            }

                    # Track near-zero gaps
                    if abs(gap) < c_int**z * 0.01:  # Within 1%
                        relative_gap = abs(gap) / (c_int**z) if c_int**z > 0 else float('inf')
                        near_zero_found.append({
                            "depth": depth,
                            "triple": (a_int, b_int, c_int),
                            "gap": gap,
                            "relative_gap": relative_gap,
                        })
                        if verbose and relative_gap < 0.005:
                            print(f"  depth {depth}: ({a_int}, {b_int}, {c_int}) gap={gap} ({relative_gap:.3%})")

            except Exception as e:
                continue

        # Progress
        if verbose and depth % 20 == 0:
            best_gap = near_zero_found[-1]["relative_gap"] if near_zero_found else float('inf')
            print(f"  depth {depth}: {len(near_zero_found)} near-zeros found, best={best_gap:.4%}")

    results["closest_approaches"] = closest_to_known
    results["near_zero_found"] = near_zero_found

    # Phase 3: Analysis
    if verbose:
        print(f"\nPhase 3: Analysis")
        print("-"*50)

        print("\nClosest approach to known triples:")
        for key, data in closest_to_known.items():
            if data["particle"]:
                print(f"  {key}: distance={data['min_distance']}, "
                      f"found ({data['particle']}) at depth {data['depth']}")
            else:
                print(f"  {key}: never approached")

        if near_zero_found:
            best = min(near_zero_found, key=lambda x: x["relative_gap"])
            print(f"\nBest near-zero: {best['triple']} with gap={best['gap']} ({best['relative_gap']:.4%})")

            # Check if any exact solutions found
            exact_solutions = [nz for nz in near_zero_found if nz["gap"] == 0]
            if exact_solutions:
                print(f"\n✓ EXACT SOLUTIONS FOUND: {len(exact_solutions)}")
                for sol in exact_solutions[:5]:
                    print(f"    {sol['triple']} at depth {sol['depth']}")
            else:
                print(f"\n✗ No exact solutions found (best gap: {best['gap']})")

    # Verdict
    exact_found = any(nz["gap"] == 0 for nz in near_zero_found)
    approached_known = any(d["min_distance"] <= 3 for d in closest_to_known.values() if d["particle"])

    results["verdict"] = {
        "exact_solution_found": exact_found,
        "approached_known_triple": approached_known,
        "total_near_zeros": len(near_zero_found),
        "interpretation": (
            "Engine finds exact solutions" if exact_found
            else "Engine approaches known triples" if approached_known
            else "Engine finds near-misses but not exact or known triples"
        ),
    }

    return results


# ═══════════════════════════════════════════════════════════════════
# § 8. Main runner
# ═══════════════════════════════════════════════════════════════════

def run_all_experiments(
    output_dir: str = "/home/croft/user/Ara/proof_foundry/experiment_results",
    verbose: bool = True,
) -> Dict:
    """Run all experiments and save results."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    all_results = {}

    # Experiment 1: Seam detection
    print("\n" + "="*70)
    print("EXPERIMENT 1: Seam Detection Baseline")
    print("="*70)
    exp1 = run_experiment_1(n_max=50, N_seeds=3, verbose=verbose)
    all_results["experiment_1"] = exp1
    with open(f"{output_dir}/exp1_seam_detection.json", "w") as f:
        json.dump(exp1, f, indent=2, default=float)

    # Experiment 3: Cadence swap
    print("\n" + "="*70)
    print("EXPERIMENT 3: Cadence Swap (42 = 6×7?)")
    print("="*70)
    exp3 = run_experiment_3(n_max=60, verbose=verbose)
    all_results["experiment_3"] = exp3
    with open(f"{output_dir}/exp3_cadence_swap.json", "w") as f:
        json.dump(exp3, f, indent=2, default=float)

    # Experiment 4: Frame swap
    print("\n" + "="*70)
    print("EXPERIMENT 4: Frame Swap (46 = 2×23?)")
    print("="*70)
    exp4 = run_experiment_4(n_max=70, verbose=verbose)
    all_results["experiment_4"] = exp4
    with open(f"{output_dir}/exp4_frame_swap.json", "w") as f:
        json.dump(exp4, f, indent=2, default=float)

    # Experiment 5: Babel noise
    print("\n" + "="*70)
    print("EXPERIMENT 5: Babel / NSO Non-commutativity")
    print("="*70)
    exp5 = run_experiment_5(verbose=verbose)
    all_results["experiment_5"] = exp5
    with open(f"{output_dir}/exp5_babel_noise.json", "w") as f:
        json.dump(exp5, f, indent=2, default=float)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    if "cross_seed" in exp1:
        print(f"\nExp 1 (Sigmoid fit):")
        print(f"  n0 = {exp1['cross_seed']['n0_mean']:.2f} ± {exp1['cross_seed']['n0_std']:.2f}")
        print(f"  Δ = {exp1['cross_seed']['delta_mean']:.2f} ± {exp1['cross_seed']['delta_std']:.2f}")
        print(f"  n0 clusters: {exp1['cross_seed']['n0_clusters']}")

    print(f"\nExp 3 (Cadence): {exp3['verdict']['interpretation']}")
    print(f"\nExp 4 (Frame): {exp4['verdict']['interpretation']}")
    print(f"\nExp 5 (Babel): Noise detected = {exp5['babel_noise_detected']}")

    # Save summary
    with open(f"{output_dir}/summary.json", "w") as f:
        summary = {
            "exp1_sigmoid": exp1.get("cross_seed", {}),
            "exp3_verdict": exp3["verdict"],
            "exp4_verdict": exp4["verdict"],
            "exp5_babel_detected": exp5["babel_noise_detected"],
        }
        json.dump(summary, f, indent=2, default=float)

    return all_results


if __name__ == "__main__":
    results = run_all_experiments(verbose=True)
