"""
Brain Geometry Empirical Tests
==============================

Three tests to validate whether the HDC brain's Beal regime structure
is a real geometric property or an encoding artifact.

Test 1: Invariance under re-encoding
Test 2: Perturbation continuity
Test 3: Task relevance (regime classification)

These produce computational certificates, not proofs.
"""

import numpy as np
import json
import sys
import os

# Add Ara to path
sys.path.insert(0, '/home/croft/user/Ara')

# === HDC Configuration ===
D = 16384  # Hypervector dimension (matches Ara brain)
SEED_BASE = 42


def encode_signature(p, q, r, seed=SEED_BASE):
    """Encode a Beal signature (p, q, r) as a bipolar hypervector.

    Method: Each component gets a random base vector (seeded deterministically),
    then they are bound together via elementwise multiplication (XOR analog).
    The curvature κ = 1/p + 1/q + 1/r is encoded as a level-coded vector.
    """
    rng = np.random.RandomState(seed)

    # Base vectors for each position
    v_p = np.sign(rng.randn(D)).astype(np.int8)
    v_q = np.sign(rng.randn(D)).astype(np.int8)
    v_r = np.sign(rng.randn(D)).astype(np.int8)
    v_k = np.sign(rng.randn(D)).astype(np.int8)  # curvature base

    # Value encoding: circular shift by value
    def shift_encode(base, value):
        return np.roll(base, int(value * 100) % D)

    h_p = shift_encode(v_p, p)
    h_q = shift_encode(v_q, q)
    h_r = shift_encode(v_r, r)

    kappa = 1.0/p + 1.0/q + 1.0/r
    h_k = shift_encode(v_k, kappa)

    # Bind all four: elementwise multiplication
    h = h_p * h_q * h_r * h_k
    return h.astype(np.float64)


def cosine_sim(a, b):
    """Cosine similarity between two vectors."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def classify_regime(p, q, r):
    """Ground truth regime classification."""
    kappa = 1.0/p + 1.0/q + 1.0/r
    if kappa > 1.0:
        return 'spherical'
    elif abs(kappa - 1.0) < 0.01:
        return 'euclidean'
    else:
        return 'hyperbolic'


# === Test Signatures ===
SIGNATURES = {
    'spherical': [(1, 2, 3), (1, 2, 4), (1, 2, 5), (1, 3, 4), (2, 2, 2)],
    'hyperbolic': [(3, 5, 7), (3, 3, 4), (4, 5, 6), (3, 4, 5), (5, 5, 5)],
    'transitional': [(2, 3, 6), (2, 4, 4), (2, 3, 7), (2, 4, 5), (3, 3, 3)],
}


def test_1_invariance():
    """Test 1: Invariance under re-encoding.

    Encode the same signature set with different random seeds.
    If structure is real, nearest-neighbor relationships should be
    stable up to permutation and noise.
    """
    print("=" * 60)
    print("TEST 1: Invariance Under Re-encoding")
    print("=" * 60)

    all_sigs = []
    for regime, sigs in SIGNATURES.items():
        for s in sigs:
            all_sigs.append((s, regime))

    seeds = [42, 137, 256, 999, 7777]
    neighbor_stability = []

    for trial_i, (seed_a, seed_b) in enumerate(zip(seeds[:-1], seeds[1:])):
        # Encode all signatures with seed_a
        vecs_a = [encode_signature(*s, seed=seed_a) for s, _ in all_sigs]
        # Encode all signatures with seed_b
        vecs_b = [encode_signature(*s, seed=seed_b) for s, _ in all_sigs]

        # Find nearest neighbor for each sig under both encodings
        nn_a = []
        nn_b = []
        for i in range(len(all_sigs)):
            sims_a = [cosine_sim(vecs_a[i], vecs_a[j]) if i != j else -2 for j in range(len(all_sigs))]
            sims_b = [cosine_sim(vecs_b[i], vecs_b[j]) if i != j else -2 for j in range(len(all_sigs))]
            nn_a.append(np.argmax(sims_a))
            nn_b.append(np.argmax(sims_b))

        # Check if nearest neighbors are the same
        matches = sum(1 for a, b in zip(nn_a, nn_b) if a == b)
        stability = matches / len(all_sigs)
        neighbor_stability.append(stability)
        print(f"  Trial {trial_i+1} (seed {seed_a} vs {seed_b}): "
              f"NN stability = {stability:.2%} ({matches}/{len(all_sigs)})")

    avg_stability = np.mean(neighbor_stability)
    print(f"\n  Average NN stability: {avg_stability:.2%}")
    print(f"  VERDICT: {'PASS - Real structure' if avg_stability > 0.5 else 'FAIL - Encoding artifact'}")

    return {
        'test': 'invariance_under_reencoding',
        'trials': len(neighbor_stability),
        'stability_scores': [float(s) for s in neighbor_stability],
        'average_stability': float(avg_stability),
        'pass': avg_stability > 0.5
    }


def test_2_perturbation():
    """Test 2: Perturbation continuity.

    Slightly perturb the signature representation (add monotone transform
    of kappa, add redundant features). Real structure should be stable.
    """
    print("\n" + "=" * 60)
    print("TEST 2: Perturbation Continuity")
    print("=" * 60)

    all_sigs = []
    for regime, sigs in SIGNATURES.items():
        for s in sigs:
            all_sigs.append((s, regime))

    # Baseline encoding
    vecs_base = [encode_signature(*s) for s, _ in all_sigs]

    # Compute baseline intra-class and inter-class similarities
    def class_sims(vecs, labels):
        intra = []
        inter = []
        for i in range(len(vecs)):
            for j in range(i+1, len(vecs)):
                sim = cosine_sim(vecs[i], vecs[j])
                if labels[i] == labels[j]:
                    intra.append(sim)
                else:
                    inter.append(sim)
        return np.mean(intra) if intra else 0, np.mean(inter) if inter else 0

    labels = [regime for _, regime in all_sigs]
    base_intra, base_inter = class_sims(vecs_base, labels)
    base_gap = base_intra - base_inter

    print(f"  Baseline: intra={base_intra:.4f}, inter={base_inter:.4f}, gap={base_gap:.4f}")

    # Perturbation 1: Replace kappa with kappa^2 (monotone transform)
    def encode_perturbed_1(p, q, r, seed=SEED_BASE):
        rng = np.random.RandomState(seed)
        v_p = np.sign(rng.randn(D)).astype(np.int8)
        v_q = np.sign(rng.randn(D)).astype(np.int8)
        v_r = np.sign(rng.randn(D)).astype(np.int8)
        v_k = np.sign(rng.randn(D)).astype(np.int8)

        def shift_encode(base, value):
            return np.roll(base, int(value * 100) % D)

        h_p = shift_encode(v_p, p)
        h_q = shift_encode(v_q, q)
        h_r = shift_encode(v_r, r)
        kappa = (1.0/p + 1.0/q + 1.0/r) ** 2  # Squared kappa
        h_k = shift_encode(v_k, kappa)
        h = h_p * h_q * h_r * h_k
        return h.astype(np.float64)

    vecs_p1 = [encode_perturbed_1(*s) for s, _ in all_sigs]
    p1_intra, p1_inter = class_sims(vecs_p1, labels)
    p1_gap = p1_intra - p1_inter
    print(f"  Perturb 1 (κ²): intra={p1_intra:.4f}, inter={p1_inter:.4f}, gap={p1_gap:.4f}")

    # Perturbation 2: Add redundant feature chi = 1 - kappa
    def encode_perturbed_2(p, q, r, seed=SEED_BASE):
        rng = np.random.RandomState(seed)
        v_p = np.sign(rng.randn(D)).astype(np.int8)
        v_q = np.sign(rng.randn(D)).astype(np.int8)
        v_r = np.sign(rng.randn(D)).astype(np.int8)
        v_k = np.sign(rng.randn(D)).astype(np.int8)
        v_chi = np.sign(rng.randn(D)).astype(np.int8)  # Extra feature

        def shift_encode(base, value):
            return np.roll(base, int(value * 100) % D)

        h_p = shift_encode(v_p, p)
        h_q = shift_encode(v_q, q)
        h_r = shift_encode(v_r, r)
        kappa = 1.0/p + 1.0/q + 1.0/r
        h_k = shift_encode(v_k, kappa)
        h_chi = shift_encode(v_chi, 1.0 - kappa)  # Redundant
        h = h_p * h_q * h_r * h_k * h_chi
        return h.astype(np.float64)

    vecs_p2 = [encode_perturbed_2(*s) for s, _ in all_sigs]
    p2_intra, p2_inter = class_sims(vecs_p2, labels)
    p2_gap = p2_intra - p2_inter
    print(f"  Perturb 2 (χ=1-κ): intra={p2_intra:.4f}, inter={p2_inter:.4f}, gap={p2_gap:.4f}")

    # Stability = gap preserved under perturbation
    gap_preserved_1 = abs(p1_gap - base_gap) / max(abs(base_gap), 1e-8) < 0.5
    gap_preserved_2 = abs(p2_gap - base_gap) / max(abs(base_gap), 1e-8) < 0.5

    print(f"\n  Gap stability (perturb 1): {abs(p1_gap - base_gap) / max(abs(base_gap), 1e-8):.2%} change")
    print(f"  Gap stability (perturb 2): {abs(p2_gap - base_gap) / max(abs(base_gap), 1e-8):.2%} change")
    print(f"  VERDICT: {'PASS' if gap_preserved_1 and gap_preserved_2 else 'PARTIAL' if gap_preserved_1 or gap_preserved_2 else 'FAIL'}")

    return {
        'test': 'perturbation_continuity',
        'baseline_gap': float(base_gap),
        'perturb1_gap': float(p1_gap),
        'perturb2_gap': float(p2_gap),
        'gap_change_1': float(abs(p1_gap - base_gap) / max(abs(base_gap), 1e-8)),
        'gap_change_2': float(abs(p2_gap - base_gap) / max(abs(base_gap), 1e-8)),
        'pass_1': bool(gap_preserved_1),
        'pass_2': bool(gap_preserved_2),
    }


def test_3_task_relevance():
    """Test 3: Task relevance.

    Define task: classify spherical/transitional/hyperbolic.
    Compare HDC representation vs simple numeric features.
    If HDC helps, should see gains vs baseline.
    """
    print("\n" + "=" * 60)
    print("TEST 3: Task Relevance (Regime Classification)")
    print("=" * 60)

    # Build larger test set
    test_sigs = []
    for p in range(1, 8):
        for q in range(p, 8):
            for r in range(q, 8):
                if p >= 1 and q >= 1 and r >= 1:
                    regime = classify_regime(p, q, r)
                    test_sigs.append(((p, q, r), regime))

    print(f"  Generated {len(test_sigs)} test signatures")

    # Count regimes
    regime_counts = {}
    for _, regime in test_sigs:
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
    print(f"  Regime distribution: {regime_counts}")

    # Method 1: HDC prototype classification
    # Build prototype for each regime
    regimes = ['spherical', 'euclidean', 'hyperbolic']
    prototypes = {}
    for regime in regimes:
        regime_sigs = [s for s, r in test_sigs if r == regime]
        if not regime_sigs:
            continue
        vecs = [encode_signature(*s) for s in regime_sigs]
        proto = np.mean(vecs, axis=0)  # Bundle = superposition
        prototypes[regime] = proto

    # Classify by nearest prototype
    hdc_correct = 0
    for (s, true_regime) in test_sigs:
        v = encode_signature(*s)
        best_regime = max(prototypes.keys(), key=lambda r: cosine_sim(v, prototypes[r]))
        if best_regime == true_regime:
            hdc_correct += 1

    hdc_accuracy = hdc_correct / len(test_sigs)
    print(f"\n  HDC prototype accuracy: {hdc_accuracy:.2%} ({hdc_correct}/{len(test_sigs)})")

    # Method 2: Simple numeric baseline (classify by kappa threshold)
    baseline_correct = 0
    for (p, q, r), true_regime in test_sigs:
        kappa = 1.0/p + 1.0/q + 1.0/r
        if kappa > 1.0:
            pred = 'spherical'
        elif abs(kappa - 1.0) < 0.01:
            pred = 'euclidean'
        else:
            pred = 'hyperbolic'
        if pred == true_regime:
            baseline_correct += 1

    baseline_accuracy = baseline_correct / len(test_sigs)
    print(f"  Numeric baseline accuracy: {baseline_accuracy:.2%} ({baseline_correct}/{len(test_sigs)})")

    gain = hdc_accuracy - baseline_accuracy
    print(f"\n  HDC gain over baseline: {gain:+.2%}")
    print(f"  VERDICT: {'PASS - HDC adds value' if gain >= 0 else 'NEUTRAL - Baseline sufficient for this task'}")

    return {
        'test': 'task_relevance',
        'n_signatures': len(test_sigs),
        'regime_distribution': regime_counts,
        'hdc_accuracy': float(hdc_accuracy),
        'baseline_accuracy': float(baseline_accuracy),
        'gain': float(gain),
        'pass': gain >= 0
    }


if __name__ == '__main__':
    print("Brain Geometry Empirical Tests")
    print("Computational certificates for HDC Beal regime structure")
    print()

    results = {}
    results['test_1'] = test_1_invariance()
    results['test_2'] = test_2_perturbation()
    results['test_3'] = test_3_task_relevance()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = all([
        results['test_1']['pass'],
        results['test_2'].get('pass_1', False) or results['test_2'].get('pass_2', False),
        results['test_3']['pass']
    ])

    for key, val in results.items():
        test_name = val['test']
        passed = val.get('pass', val.get('pass_1', False))
        print(f"  {test_name}: {'PASS' if passed else 'FAIL/PARTIAL'}")

    print(f"\n  Overall: {'REAL STRUCTURE' if all_pass else 'NEEDS INVESTIGATION'}")

    # Save as computational certificate
    outpath = '/home/croft/user/Ara/proof_foundry/tests/brain_geometry_certificate.json'
    def make_serializable(obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [make_serializable(v) for v in obj]
        return obj
    with open(outpath, 'w') as f:
        json.dump(make_serializable(results), f, indent=2)
    print(f"\n  Certificate saved to: {outpath}")
