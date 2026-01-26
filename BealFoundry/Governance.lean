/-!
# Proof Governance Kernel

A type-theoretic framework for managing mathematical proof state.

## Key Concepts

- **Certificate**: A typed receipt for every claim transition
- **Lock**: Typed lock that prevents re-opening unless conditions are met
- **Domain**: Mathematical domain with state space, invariants, claims

## Main Theorem

`proven_lock_permanent`: A PROVEN lock admits no valid transition out.
-/

namespace BealFoundry

-- § 1. Certificate Types

/-- The evidence type for a mathematical claim. Ordered by strength. -/
inductive CertificateType where
  | proof        -- Complete, unconditional proof
  | reduction    -- Reduces to known result
  | computation  -- Verified by reproducible computation
  | conditional  -- Depends on unproved conjecture
  | heuristic    -- Numerical/probabilistic evidence only
  deriving Repr, BEq, DecidableEq

/-- Certificate strength ordering: proof > reduction > computation > conditional > heuristic -/
def CertificateType.strength : CertificateType → Nat
  | .proof       => 5
  | .reduction   => 4
  | .computation => 3
  | .conditional => 2
  | .heuristic   => 1

/-- A certificate is "hard" if it provides proof, reduction, or computation. -/
def CertificateType.isHard : CertificateType → Bool
  | .proof       => true
  | .reduction   => true
  | .computation => true
  | .conditional => false
  | .heuristic   => false

-- § 2. Lock Types

/-- The type of lock placed on a resolved domain. -/
inductive LockType where
  | proven      -- Permanent: unconditional proof exists
  | conditional -- Reopenable if the condition is resolved
  | heuristic   -- Reopenable with new tools or methods
  deriving Repr, BEq, DecidableEq

/-- Whether a lock type permits reopening. -/
def LockType.canReopen : LockType → Bool
  | .proven      => false
  | .conditional => true
  | .heuristic   => true

-- § 3. Domain State

/-- The lifecycle state of a mathematical domain. -/
inductive DomainState where
  | active                            -- Under investigation
  | dropped (cert : CertificateType)  -- Reduced to zero (with evidence)
  | locked (lt : LockType)            -- Resolved and locked
  | reactivated                       -- Reopened from conditional/heuristic lock
  deriving Repr, BEq

-- § 4. Lambda Kind

/-- The semantic kind of the criticality parameter λ. -/
inductive LambdaKind where
  | geometricCurvature     -- Orbifold Euler characteristic (Beal)
  | scalingCriticality     -- Sobolev/scaling exponent (Navier-Stokes)
  | spectralGapRisk        -- Gap in spectrum (Riemann, Yang-Mills)
  | diophantineComplexity  -- Density of solutions (P vs NP)
  | proofDependencyRisk    -- Certificate chain fragility
  | cognitiveLoad          -- Cognitive resource consumption
  deriving Repr, BEq, DecidableEq

-- § 5. Certificate Structure

/-- A certificate: typed receipt for a domain state transition. -/
structure Certificate where
  certType     : CertificateType
  reference    : String
  seam         : String
  verifier     : String := "unverified"
  blockingSeam : Option String := none
  requiredTool : Option String := none
  deriving Repr

/-- A certificate is hard iff its type is hard. -/
def Certificate.isHard (c : Certificate) : Bool :=
  c.certType.isHard

-- § 6. Domain Claim

/-- A mathematical claim within a domain. -/
structure DomainClaim where
  statement   : String
  status      : String
  certificate : Option Certificate := none
  openSeam    : Option String := none
  deriving Repr

-- § 7. Domain Registration

/-- A registered mathematical domain with full metadata. -/
structure Domain where
  name       : String
  lambdaKind : LambdaKind
  stateSpace : String
  invariants : List String
  stopRule   : String
  falsifier  : String
  state      : DomainState := .active
  claims     : List DomainClaim := []
  deriving Repr

-- § 8. State Transition Rules

/-- Valid transitions: which state changes are permitted. -/
inductive ValidTransition : DomainState → DomainState → Prop where
  | activeToDrop : (ct : CertificateType) →
      ValidTransition .active (.dropped ct)
  | dropToLock : (ct : CertificateType) → (lt : LockType) →
      ValidTransition (.dropped ct) (.locked lt)
  | lockToReactivate : (lt : LockType) → lt.canReopen = true →
      ValidTransition (.locked lt) .reactivated
  | reactivateToActive :
      ValidTransition .reactivated .active

/-- PROVEN locks cannot be reopened. -/
theorem proven_lock_permanent :
    ¬ ValidTransition (.locked .proven) .reactivated := by
  intro h
  cases h with
  | lockToReactivate lt hcan =>
    simp [LockType.canReopen] at hcan

/-- Conditional locks CAN be reopened. -/
theorem conditional_lock_reopenable :
    ValidTransition (.locked .conditional) .reactivated :=
  .lockToReactivate .conditional rfl

/-- Heuristic locks CAN be reopened. -/
theorem heuristic_lock_reopenable :
    ValidTransition (.locked .heuristic) .reactivated :=
  .lockToReactivate .heuristic rfl

-- § 9. Certificate Chain

/-- A certificate chain is a sequence of valid transitions. -/
inductive CertChain : DomainState → DomainState → Type where
  | single : {s1 s2 : DomainState} → ValidTransition s1 s2 → CertChain s1 s2
  | cons   : {s1 s2 s3 : DomainState} → ValidTransition s1 s2 → CertChain s2 s3 → CertChain s1 s3

-- § 10. Lock Permission

/-- When dropping a domain, the certificate type constrains the lock type.
    Hard certificates permit proven locks; soft ones do not. -/
def permittedLock (ct : CertificateType) : LockType → Prop
  | .proven      => ct.isHard = true
  | .conditional => ct = .conditional ∨ ct.isHard = true
  | .heuristic   => True

/-- A proof certificate permits a proven lock. -/
theorem proof_permits_proven : permittedLock .proof .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- A heuristic certificate does NOT permit a proven lock. -/
theorem heuristic_forbids_proven : ¬ permittedLock .heuristic .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- A conditional certificate does NOT permit a proven lock. -/
theorem conditional_forbids_proven : ¬ permittedLock .conditional .proven := by
  simp [permittedLock, CertificateType.isHard]

end BealFoundry
