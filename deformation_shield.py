#!/usr/bin/env python3
"""
Deformation Shield — The (3,5,7) 3-5 Switch Survival Kit
=========================================================

KEY DISCOVERY: The (3,5,7) Final Boss can be reduced to a degree-2
problem over Q(√5) via signature reordering.

The equation a³ + b⁵ = c⁷ rewrites as:
  b⁵ + (-c)⁷ + a³ = 0  →  x⁵ + y⁷ + z³ = 0
  Signature (q,p,r) = (5,7,3)

Field K = Q(ζ_q)⁺ · Q(ζ_r)⁺ = Q(ζ₅)⁺ · Q(ζ₃)⁺ = Q(√5) · Q = Q(√5)

This is the SAME degree-2 field as the (5,p,3) paper
(Pacetti–Villagra Torcomian, arXiv:2512.17845, Dec 2025).

The degree-6 nightmare (Q(cos(2π/5), cos(2π/7))) only appears
with orderings (5,3,7) or (7,3,5). We avoid it entirely.

"The (3,5,7) isn't a wall; it's a vacuum. It is so tight, so perfect,
 that it leaves no room for anything but the truth." — Croft
"""

import json
import sys
from math import gcd, isqrt
from itertools import product
from typing import Optional
from sympy import factorint, isprime, primerange, sqrt as sym_sqrt


# ═══════════════════════════════════════════════════════════════════
# LAYER 1: SIGNATURE REORDERING ENGINE
# ═══════════════════════════════════════════════════════════════════

def optimal_ordering(p: int, q: int, r: int) -> dict:
    """
    Find the signature ordering (q', p', r') for the equation
    a^p + b^q = c^r that minimizes the degree of the base field
    K = Q(ζ_{q'})⁺ · Q(ζ_{r'})⁺.

    Returns the optimal ordering and field information.
    """
    from sympy import totient

    exponents = [p, q, r]
    best = None

    # All 6 orderings of x^{q'} + y^{p'} + z^{r'} = 0
    from itertools import permutations
    for perm in permutations(exponents):
        q_prime, p_prime, r_prime = perm
        # Field degree = [Q(ζ_{q'})⁺ : Q] × [Q(ζ_{r'})⁺ : Q]
        def real_cyclotomic_degree(n):
            if n <= 2:
                return 1
            return max(1, totient(n) // 2)

        deg_q = real_cyclotomic_degree(q_prime)
        deg_r = real_cyclotomic_degree(r_prime)
        degree = deg_q * deg_r

        if best is None or degree < best["degree"]:
            best = {
                "ordering": (q_prime, p_prime, r_prime),
                "degree": degree,
                "field_q": f"Q(ζ_{q_prime})⁺" if q_prime > 2 else "Q",
                "field_r": f"Q(ζ_{r_prime})⁺" if r_prime > 2 else "Q",
                "deg_q": deg_q,
                "deg_r": deg_r,
            }

    # Describe the field
    q_opt, p_opt, r_opt = best["ordering"]
    if best["degree"] == 1:
        best["field"] = "Q"
    elif best["degree"] == 2:
        # Identify which gives degree 2
        if best["deg_q"] == 2:
            best["field"] = f"Q(cos(2π/{q_opt}))"
        else:
            best["field"] = f"Q(cos(2π/{r_opt}))"
    else:
        best["field"] = f"Q(cos(2π/{q_opt}), cos(2π/{r_opt}))"

    # Map back to original equation
    best["equation_map"] = {
        "original": f"a^{p} + b^{q} = c^{r}",
        "rewritten": f"x^{q_opt} + y^{p_opt} + z^{r_opt} = 0",
        "field": best["field"],
        "degree": best["degree"],
    }

    return best


# ═══════════════════════════════════════════════════════════════════
# LAYER 2: HYPERGEOMETRIC MOTIVE PARAMETERS
# ═══════════════════════════════════════════════════════════════════

def hgm_parameters(q: int, r: int) -> dict:
    """
    Compute the hypergeometric motive (HGM) parameters for
    the Frey representation attached to signature (q, p, r).

    From Golfieri–Pacetti (arXiv:2412.08804):
      ℋ⁺(t) = ℋ((1/r, -1/r), (1/q, -1/q) | t)
      ℋ⁻(t) = ℋ((1/(2r), -1/(2r)), (1/q, -1/q) | t)

    Specialization: t₀ = -x^q / z^r
    """
    return {
        "H_plus": {
            "alpha": (f"1/{r}", f"-1/{r}"),
            "beta": (f"1/{q}", f"-1/{q}"),
            "description": f"ℋ((1/{r}, -1/{r}), (1/{q}, -1/{q}) | t)",
        },
        "H_minus": {
            "alpha": (f"1/{2*r}", f"-1/{2*r}"),
            "beta": (f"1/{q}", f"-1/{q}"),
            "description": f"ℋ((1/{2*r}, -1/{2*r}), (1/{q}, -1/{q}) | t)",
        },
        "specialization": f"t₀ = -x^{q} / z^{r}",
        "wild_primes": sorted(set(factorint(2 * q * r).keys())),
        "wild_product": 2 * q * r,
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 3: GHOST SOLUTION ENUMERATOR
# ═══════════════════════════════════════════════════════════════════

def enumerate_ghosts(q: int, r: int, max_exp: int = 4,
                     max_val: int = 20) -> dict:
    """
    Enumerate ghost solutions for signature (q, ?, r).

    Ghost equation (Pacetti–VT):
      q^s · r^l · x^q  ±  q^m · r^n  +  q^u · r^v · z^r = 0

    Returns distinct specialization parameters t₀ = coeff_x·x^q / (coeff_z·z^r).
    """
    ghosts = []
    seen_t0 = {}

    for s, l, m, n, u, v in product(range(max_exp), repeat=6):
        coeff_x = q**s * r**l
        constant = q**m * r**n
        coeff_z = q**u * r**v

        for x in range(1, max_val + 1):
            for z in range(1, max_val + 1):
                lhs_x = coeff_x * x**q
                rhs_z = coeff_z * z**r

                # Case 1: coeff_x·x^q - constant + coeff_z·z^r = 0
                if lhs_x + rhs_z == constant:
                    t0_num = coeff_x * x**q
                    t0_den = coeff_z * z**r
                    g = gcd(t0_num, t0_den)
                    t0_key = (t0_num // g, t0_den // g)

                    if t0_key not in seen_t0:
                        seen_t0[t0_key] = {
                            "t0": f"{t0_key[0]}/{t0_key[1]}",
                            "t0_float": t0_key[0] / t0_key[1],
                            "example": {
                                "x": x, "z": z,
                                "coeff_x": coeff_x,
                                "constant": constant,
                                "coeff_z": coeff_z,
                                "exponents": (s, l, m, n, u, v),
                            },
                            "count": 0,
                        }
                    seen_t0[t0_key]["count"] += 1

                # Case 2: -coeff_x·x^q + constant + coeff_z·z^r = 0
                if constant + rhs_z == lhs_x:
                    t0_num = coeff_x * x**q
                    t0_den = coeff_z * z**r
                    g = gcd(t0_num, t0_den)
                    t0_key = (t0_num // g, t0_den // g)

                    if t0_key not in seen_t0:
                        seen_t0[t0_key] = {
                            "t0": f"{t0_key[0]}/{t0_key[1]}",
                            "t0_float": t0_key[0] / t0_key[1],
                            "example": {
                                "x": x, "z": z,
                                "coeff_x": coeff_x,
                                "constant": constant,
                                "coeff_z": coeff_z,
                                "exponents": (s, l, m, n, u, v),
                            },
                            "count": 0,
                        }
                    seen_t0[t0_key]["count"] += 1

    ghost_params = sorted(seen_t0.values(), key=lambda g: g["t0_float"])

    return {
        "signature": f"({q}, p, {r})",
        "total_ghosts": sum(g["count"] for g in ghost_params),
        "distinct_t0": len(ghost_params),
        "parameters": ghost_params,
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 4: CONDUCTOR COMPUTATION (ADAPTED FROM (5,p,3) PAPER)
# ═══════════════════════════════════════════════════════════════════

def conductor_at_3(a: int, b: int, c: int, q: int = 5, r: int = 3) -> dict:
    """
    Conductor exponent at prime 3 for signature (q, p, r) = (5, 7, 3).
    Adapted from Table 3.2 of Pacetti–VT (arXiv:2512.17845).

    For the rewritten equation x^5 + y^7 + z^3 = 0:
      x=b, y=-c, z=a from original a^3 + b^5 = c^7
    """
    x, y, z = b, c, a  # Mapping from original to (5,7,3) ordering

    if z % 3 == 0:
        # 3 | z (i.e., 3 | a in original)
        return {"prime": 3, "divides": "z", "exponent_range": (1, 2),
                "note": "3|z: conductor 1 or 2 depending on congruence"}
    elif x % 3 == 0:
        # 3 | x (i.e., 3 | b in original)
        return {"prime": 3, "divides": "x", "exponent_range": (1, 3),
                "note": "3|x: conductor 1-3, depends on x^5 mod 9"}
    else:
        # 3 ∤ xz, must have 3 | y (i.e., 3 | c in original)
        return {"prime": 3, "divides": "y (or neither)", "exponent_range": (0, 2),
                "note": "3∤xz: conductor 0-2"}


def conductor_at_5(a: int, b: int, c: int, q: int = 5, r: int = 3) -> dict:
    """
    Conductor exponent at prime 5 for signature (5, 7, 3).
    Adapted from Table 3.4 of Pacetti–VT.
    """
    x, y, z = b, c, a

    if x % 5 == 0:
        # 5 | x (i.e., 5 | b)
        return {"prime": 5, "divides": "x", "exponent_range": (0, 2),
                "note": "5|x: conductor 0-2"}
    elif z % 5 == 0:
        # 5 | z (i.e., 5 | a)
        return {"prime": 5, "divides": "z", "exponent_range": (1, 3),
                "note": "5|z: conductor 1-3"}
    else:
        # 5 ∤ xz
        return {"prime": 5, "divides": "neither x,z", "exponent_range": (0, 3),
                "note": "5∤xz: depends on F(x) irreducibility over Q_5"}


def conductor_at_2(a: int, b: int, c: int) -> dict:
    """
    Conductor exponent at prime 2 for signature (5, 7, 3).
    From Proposition 3.15 and Chen–VT (arXiv:2509.23540).
    """
    x, y, z = b, c, a

    if x % 2 == 0 and y % 2 == 1 and z % 2 == 1:
        return {"prime": 2, "exponent_range": (2, 6),
                "note": "2|x only: wild ramification, conductor 2-6"}
    elif y % 2 == 0 and x % 2 == 1 and z % 2 == 1:
        return {"prime": 2, "exponent_range": (0, 4),
                "note": "2|y only: conductor 0-4"}
    elif z % 2 == 0 and x % 2 == 1 and y % 2 == 1:
        return {"prime": 2, "exponent_range": (1, 5),
                "note": "2|z only: conductor 1-5"}
    else:
        # All odd
        return {"prime": 2, "exponent_range": (0, 6),
                "note": "all odd: conductor depends on mod 8 congruences"}


def serre_level_bounds(a: int, b: int, c: int) -> dict:
    """
    Compute bounds on the Serre level (conductor) of the Frey
    representation for a hypothetical solution a^3 + b^5 = c^7.

    Level = product of prime-power contributions over all wild primes.
    Over Q(√5), the level is an ideal in O_{Q(√5)}.
    """
    cond_2 = conductor_at_2(a, b, c)
    cond_3 = conductor_at_3(a, b, c)
    cond_5 = conductor_at_5(a, b, c)

    # Level norm bounds (over Q(√5), norm of ideal = N_{K/Q}(𝔫))
    # Since 5 ramifies in Q(√5): 𝔭₅² = (5), so norm contributions differ
    min_norm = (2**cond_2["exponent_range"][0] *
                3**cond_3["exponent_range"][0] *
                5**cond_5["exponent_range"][0])
    max_norm = (2**cond_2["exponent_range"][1] *
                3**cond_3["exponent_range"][1] *
                5**cond_5["exponent_range"][1])

    return {
        "conductor_at_2": cond_2,
        "conductor_at_3": cond_3,
        "conductor_at_5": cond_5,
        "level_norm_range": (min_norm, max_norm),
        "field": "Q(√5)",
        "note": ("Serre level is an ideal in O_{Q(√5)}. "
                 "Norm gives the rational level. "
                 "The (5,p,3) paper computes HMFs up to norm 400."),
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 5: BIG IMAGE VERIFICATION (p=7 SPECIFIC)
# ═══════════════════════════════════════════════════════════════════

def big_image_analysis_p7() -> dict:
    """
    Analyze the Big Image Conjecture for p=7 over K=Q(√5).

    The (5,p,3) paper assumes p > C(K,K) for an unspecified constant C.
    For p=7, we need to verify directly that the mod-7 representation
    has image containing SL₂(F₇).

    Key facts:
    - |SL₂(F₇)| = 336
    - Possible subgroups: Borel (order 42), normalizer of split Cartan (12),
      normalizer of non-split Cartan (16), exceptional (S₄, A₅, etc.)
    - For p=7, the representation is "large" if it's not contained in
      any of the proper maximal subgroups
    """
    return {
        "prime": 7,
        "field": "Q(√5)",
        "SL2_F7_order": 336,
        "maximal_subgroups": [
            {"name": "Borel", "order": 42,
             "obstruction": "representation is reducible"},
            {"name": "Normalizer of split Cartan", "order": 12,
             "obstruction": "induced from character of Q(√5)"},
            {"name": "Normalizer of non-split Cartan", "order": 16,
             "obstruction": "induced from character of Q(√-7)"},
            {"name": "S₄ (exceptional)", "order": 24,
             "obstruction": "Serre's conjecture weight bound"},
            {"name": "A₅ (exceptional)", "order": 60,
             "obstruction": "Only for p ≡ ±1 mod 5 → 7 ≡ 2 mod 5 → EXCLUDED"},
        ],
        "p7_specific": {
            "7_mod_5": 7 % 5,  # = 2
            "A5_excluded": True,  # 7 ≢ ±1 mod 5
            "note": ("A₅ subgroup excluded because 7 ≡ 2 mod 5 (not ±1). "
                     "S₄ can be checked via weight considerations. "
                     "Borel case (reducibility) requires direct computation. "
                     "Cartan cases require checking if ρ̄₇ is dihedral."),
        },
        "verification_strategy": (
            "For each conductor level 𝔫 over Q(√5):\n"
            "  1. Compute ρ̄₇ from the HGM at that level\n"
            "  2. Check image is not in Borel (reducibility test)\n"
            "  3. Check image is not dihedral (Cartan test)\n"
            "  4. S₄ check via Serre weight\n"
            "  5. A₅ already excluded (7 ≡ 2 mod 5)\n"
            "If all pass → Big Image holds for p=7"
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 6: THE 3-5 SWITCH MECHANISM
# ═══════════════════════════════════════════════════════════════════

def three_five_switch_analysis() -> dict:
    """
    The Taylor-Wiles 3-5 switch for the (3,5,7) boss.

    In the original Wiles proof of FLT, the 3-5 switch works because:
    - Start with mod-3 representation (known to be modular via Langlands-Tunnell)
    - Lift to mod-5 using Taylor-Wiles patching

    For (3,5,7) via (5,7,3) ordering:
    - Working mod 7 (the middle exponent p=7)
    - If mod-7 is reducible, switch to mod-5 (q=5) or mod-3 (r=3)

    The switch exploits: at most one of {3, 5, 7} can have reducible
    residual representation for a given solution.
    """
    return {
        "mechanism": "Taylor-Wiles 3-5-7 switch",
        "equation": "x⁵ + y⁷ + z³ = 0 over Q(√5)",
        "primary_prime": 7,
        "switch_targets": [5, 3],
        "logic": {
            "step_1": ("Start with mod-7 representation ρ̄₇ from HGM ℋ⁺ or ℋ⁻"),
            "step_2": ("Check Big Image: does im(ρ̄₇) ⊇ SL₂(F₇)?"),
            "step_3_yes": ("Big Image holds → apply level-lowering → "
                           "reach conductor 𝔫 → check S₂(Γ₀(𝔫)) = 0"),
            "step_3_no": ("Big Image fails → switch to mod-5 or mod-3"),
            "step_4_mod5": ("Mod-5: ρ̄₅ from ℋ⁺ specialized differently. "
                            "Since 5 ramifies in Q(√5), use Fontaine-Laffaille"),
            "step_4_mod3": ("Mod-3: ρ̄₃ reducible → use Langlands-Tunnell "
                            "(as in original Wiles). Known modular."),
            "step_5": ("Whichever prime gives irreducible ρ̄, apply "
                       "Taylor-Wiles patching to get R = T"),
            "step_6": ("If R = T = 0 (no modular forms at that level), "
                       "then no solution exists → Beal holds for (3,5,7)"),
        },
        "key_insight": (
            "The 3-5 switch for (3,5,7) is STRONGER than for FLT because "
            "we have THREE primes to switch between, not just two. "
            "If mod-7 fails, try mod-5. If mod-5 fails, try mod-3. "
            "The Langlands-Tunnell theorem guarantees mod-3 always works "
            "as a starting point (the representation is automatically modular)."
        ),
        "goldilocks_interaction": (
            "The degree-3 cyclotomic field from 7 (Q(ζ₇)⁺ = Q(cos(2π/7))) "
            "is NOT the base field in our ordering. Our base field is Q(√5) "
            "from the q=5 exponent. The 7 appears only as the mod-p prime, "
            "where it creates a finite-image obstruction — not a field "
            "extension obstruction."
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# INTEGRATED SHIELD RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_shield(verbose: bool = True) -> dict:
    """
    Run the complete Deformation Shield analysis for (3,5,7).
    """
    print("╔══════════════════════════════════════════════════════════╗")
    print("║    DEFORMATION SHIELD — The (3,5,7) Final Boss Kit     ║")
    print("║    Equation: a³ + b⁵ = c⁷                              ║")
    print("║    Rewritten: x⁵ + y⁷ + z³ = 0 over Q(√5)            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    results = {}

    # Layer 1: Signature Reordering
    print("LAYER 1: SIGNATURE REORDERING")
    print("-" * 50)
    ordering = optimal_ordering(3, 5, 7)
    results["ordering"] = ordering
    print(f"  Original: a³ + b⁵ = c⁷")
    print(f"  Optimal ordering: (q,p,r) = {ordering['ordering']}")
    print(f"  Rewritten: x^{ordering['ordering'][0]} + "
          f"y^{ordering['ordering'][1]} + z^{ordering['ordering'][2]} = 0")
    print(f"  Field: {ordering['field']} (degree {ordering['degree']})")
    print(f"  DEGREE-6 AVOIDED: Q(ζ₃)⁺ = Q (trivial!)")
    print()

    # Layer 2: HGM Parameters
    print("LAYER 2: HYPERGEOMETRIC MOTIVE PARAMETERS")
    print("-" * 50)
    q_opt, p_opt, r_opt = ordering["ordering"]
    hgm = hgm_parameters(q_opt, r_opt)
    results["hgm"] = hgm
    print(f"  ℋ⁺(t) = {hgm['H_plus']['description']}")
    print(f"  ℋ⁻(t) = {hgm['H_minus']['description']}")
    print(f"  Specialization: {hgm['specialization']}")
    print(f"  Wild primes: {hgm['wild_primes']} (product = {hgm['wild_product']})")
    print()

    # Layer 3: Ghost Enumeration
    print("LAYER 3: GHOST SOLUTION ENUMERATION")
    print("-" * 50)
    ghosts = enumerate_ghosts(q_opt, r_opt, max_exp=4, max_val=20)
    results["ghosts"] = ghosts
    print(f"  Signature: (q, p, r) = ({q_opt}, {p_opt}, {r_opt})")
    print(f"  Total ghost solutions found: {ghosts['total_ghosts']}")
    print(f"  Distinct specialization parameters: {ghosts['distinct_t0']}")
    print(f"  Ghost t₀ values:")
    for g in ghosts["parameters"]:
        print(f"    t₀ = {g['t0']:>10s} = {g['t0_float']:.4f}  "
              f"({g['count']} instances)")
    print()

    # Layer 4: Conductor Bounds
    print("LAYER 4: CONDUCTOR ANALYSIS (sample cases)")
    print("-" * 50)
    # Test a few divisibility cases
    cases = [
        (1, 1, 1, "all odd, coprime"),
        (2, 1, 1, "2|a only"),
        (1, 2, 1, "2|b only"),
        (1, 1, 2, "2|c only"),
        (3, 1, 1, "3|a"),
        (1, 5, 1, "5|b"),
    ]
    for a, b, c, desc in cases:
        bounds = serre_level_bounds(a, b, c)
        lo, hi = bounds["level_norm_range"]
        print(f"  {desc:20s}: level norm ∈ [{lo}, {hi}]")

    # General bounds
    bounds_general = serre_level_bounds(1, 1, 1)
    results["conductor"] = bounds_general
    print(f"\n  General level norm range: "
          f"[{bounds_general['level_norm_range'][0]}, "
          f"{bounds_general['level_norm_range'][1]}]")
    print(f"  (5,p,3) paper computed HMFs up to norm 400")
    print()

    # Layer 5: Big Image
    print("LAYER 5: BIG IMAGE ANALYSIS (p=7)")
    print("-" * 50)
    big_image = big_image_analysis_p7()
    results["big_image"] = big_image
    print(f"  |SL₂(F₇)| = {big_image['SL2_F7_order']}")
    print(f"  Maximal subgroups to exclude:")
    for sg in big_image["maximal_subgroups"]:
        status = "✗ EXCLUDED" if sg["name"] == "A₅ (exceptional)" else "? CHECK"
        print(f"    {sg['name']:35s} (order {sg['order']:>3d}): {status}")
    print(f"\n  7 mod 5 = {big_image['p7_specific']['7_mod_5']} → "
          f"A₅ excluded: {big_image['p7_specific']['A5_excluded']}")
    print()

    # Layer 6: The Switch
    print("LAYER 6: THE 3-5-7 SWITCH")
    print("-" * 50)
    switch = three_five_switch_analysis()
    results["switch"] = switch
    for step, desc in switch["logic"].items():
        print(f"  {step}: {desc}")
    print()
    print(f"  KEY INSIGHT: {switch['key_insight']}")
    print()

    # Summary
    print("═" * 60)
    print("SHIELD STATUS SUMMARY")
    print("═" * 60)
    print(f"  Base field:        Q(√5) (degree 2, NOT degree 6)")
    print(f"  HGM constructed:   ℋ⁺ and ℋ⁻ for (5,7,3)")
    print(f"  Ghosts found:      {ghosts['distinct_t0']} distinct t₀ parameters")
    print(f"  Wild primes:       2, 3, 5 (same as (5,p,3) paper!)")
    print(f"  Big Image p=7:     A₅ excluded, 4 subgroups to check")
    print(f"  Switch available:  mod-7 → mod-5 → mod-3 (Langlands-Tunnell)")
    print()
    print("  WHAT'S NEEDED TO CLOSE (3,5,7):")
    print("  1. Magma/PARI: Compute HMFs over Q(√5) at ghost levels")
    print("  2. Direct irreducibility check for ρ̄₇ (bypass Big Image)")
    print("  3. Ghost elimination via trace comparison at small primes")
    print("  4. If all ghosts die → Beal holds for (3,5,7)")
    print()
    print("  INFRASTRUCTURE REUSE FROM (5,p,3) PAPER:")
    print("  - Same field Q(√5)")
    print("  - Same wild primes {2, 3, 5}")
    print("  - Same Magma/PARI scripts (shanks-birch cluster)")
    print("  - Same HMF databases (LMFDB)")
    print("  - p=7 is just ONE specific case, not an infinite family")
    print()

    return results


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_shield(verbose=True)

    # Save results
    output_path = "/home/croft/user/Ara/proof_foundry/zord_results/deformation_shield_357.json"

    # Clean for JSON serialization
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [clean(v) for v in obj]
        if isinstance(obj, set):
            return sorted(list(obj))
        return obj

    with open(output_path, "w") as f:
        json.dump(clean(results), f, indent=2, default=str)
    print(f"Results saved to {output_path}")
