# BealFoundry

**Lean 4 governance kernel for mathematical proof certification.**

A type-theoretic framework that manages the lifecycle of mathematical claims:
active (under investigation) → dropped (evidence attached) → locked (proven/conditional).

## Architecture

```
Governance.lean       — Core types: Certificate, Domain, LockType, DomainState
Lambda.lean           — Darmon-Granville regime classification (κ = 1/p + 1/q + 1/r)
Soundness.lean        — Soundness theorems: lifecycle safety, lock integrity
Observer.lean         — Observer contract: what an AI witness may/may not do
HDC.lean              — Hyperdimensional computing algebra + certificate bridge
NavierStokes.lean     — GAL proof structure with honest gap tracking
TensorGenerated.lean  — Auto-generated certificates from tensor fusion observer
UnifiedSolver.lean    — 455 Beal signatures (bound 1000, exponents 3-15)
```

## Key Properties (all Lean-verified)

- **No state skipping**: active → locked is forbidden; must pass through dropped
- **Hard certificate gate**: only computation/proof certificates support proven locks
- **Honest gap tracking**: NS certificate stays conditional until GAP_003 closes
- **Observer contract**: soft evidence cannot produce proven locks
- **Upgrade path**: when evidence strengthens, lock type upgrades automatically

## Build

```bash
lake build
```

Requires Lean 4 (see `lean-toolchain` for exact version).

## Status

- 8 modules, 500+ theorems, 1 intentional `sorry` (ABC conjecture placeholder)
- All build clean on Lean 4.14
- Beal search: 455 signatures checked at bound 1000, zero coprime counterexamples
- NS: conditional certificate (GAP_003 numerically closed, analytically open)

## References

- Darmon & Granville, "On the equations z^m = F(x,y) and Ax^p + By^q = Cz^r" (1995)
- Beale, Kato & Majda, "Remarks on the breakdown of smooth solutions for the 3-D Euler equations" (1984)
- Kanerva, "Hyperdimensional Computing: An Introduction to Computing in Distributed Representation" (2009)