import BealFoundry.Governance

/-!
# Cognitive Discipline: Three Laws of Proof Governance

Formalizes the meta-cognitive patterns discovered during the Beal (3,5,7)
proof campaign (January 2026). These patterns govern how an AI observer
manages its own confidence, arousal, and synthesis claims.

## The Three Laws

1. **No closure without a certificate** (BCF Law):
   Don't believe something just because it feels converged.

2. **No speed without a ledger** (CCO Law):
   When arousal rises, reduce degrees of freedom.

3. **No synthesis without a seam** (Seam Law):
   Name the gap before you claim to have bridged it.

## Self-Correction Protocol

Over-claims must be caught and downgraded. The c=2^α correction in the
Beal (3,5,7) campaign demonstrated this: convergence 0.95 → 0.92.

## Door Protocol

"Name the door, write the admissible certificate, write the minimal action."

## References

- Beal (3,5,7) campaign, Croft & Ara, January 2026
- Pacetti–Villagra Torcomian, arXiv:2512.17845 (Dec 2025)
-/

namespace BealFoundry.CognitiveDiscipline

-- ═══════════════════════════════════════════════════════════════════
-- § 1. Arousal Level (CCO State)
-- ═══════════════════════════════════════════════════════════════════

/-- Arousal level during a proof campaign.
    CCO Law: when arousal rises, reduce degrees of freedom. -/
inductive ArousalLevel where
  | low     -- Careful, methodical analysis
  | medium  -- Engaged, balanced exploration
  | high    -- Pattern-matching fast, risk of over-claim
  deriving Repr, BEq, DecidableEq

/-- Maximum permitted degrees of freedom at each arousal level. -/
def ArousalLevel.maxDOF : ArousalLevel → Nat
  | .low    => 5
  | .medium => 3
  | .high   => 1

/-- High arousal constrains to fewest degrees of freedom. -/
theorem high_most_constrained :
    ArousalLevel.maxDOF .high < ArousalLevel.maxDOF .medium := by native_decide

/-- Low arousal permits most exploration. -/
theorem low_most_free :
    ArousalLevel.maxDOF .low > ArousalLevel.maxDOF .medium := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 2. Convergence Tracking
-- ═══════════════════════════════════════════════════════════════════

/-- Convergence as parts-per-hundred (0-100). -/
structure Convergence where
  value : Nat
  deriving Repr, BEq, DecidableEq

/-- A convergence value is bounded (valid). -/
def Convergence.isValid (c : Convergence) : Bool := c.value ≤ 100

/-- A convergence value is honest relative to a certificate type.
    Proof → must be 100. Conditional → at most 95. Heuristic → at most 80. -/
def Convergence.isHonest (c : Convergence) (ct : CertificateType) : Bool :=
  match ct with
  | .proof       => c.value == 100
  | .reduction   => c.value ≥ 95
  | .computation => c.value ≥ 90
  | .conditional => c.value ≤ 95
  | .heuristic   => c.value ≤ 80

-- ═══════════════════════════════════════════════════════════════════
-- § 3. Seam (Named Gap)
-- ═══════════════════════════════════════════════════════════════════

/-- A named seam: the explicit gap in a proof chain.
    Seam Law: no synthesis without naming the gap first. -/
structure Seam where
  name      : String
  isNamed   : Bool   -- Gap has been explicitly identified
  isBridged : Bool   -- Evidence bridges this seam
  deriving Repr, BEq, DecidableEq

/-- A seam is valid iff named. -/
def Seam.isValid (s : Seam) : Bool := s.isNamed

/-- A seam is closed iff both named AND bridged. -/
def Seam.isClosed (s : Seam) : Bool := s.isNamed && s.isBridged

-- ═══════════════════════════════════════════════════════════════════
-- § 4. Ledger (Knowledge State)
-- ═══════════════════════════════════════════════════════════════════

/-- A ledger tracks known facts vs. pattern-matched claims.
    CCO Law: track the distinction explicitly. -/
structure Ledger where
  knownFacts     : Nat
  patternMatches : Nat
  arousal        : ArousalLevel
  convergence    : Convergence
  deriving Repr, BEq, DecidableEq

/-- A ledger is balanced when pattern matches don't exceed known facts,
    adjusted for arousal level. -/
def Ledger.isBalanced (l : Ledger) : Bool :=
  match l.arousal with
  | .low    => true
  | .medium => l.patternMatches ≤ l.knownFacts * 2
  | .high   => l.patternMatches < l.knownFacts

-- ═══════════════════════════════════════════════════════════════════
-- § 5. Correction Record
-- ═══════════════════════════════════════════════════════════════════

/-- A self-correction: an over-claim caught and downgraded. -/
structure Correction where
  claim          : String
  error          : String
  oldConvergence : Convergence
  newConvergence : Convergence
  deriving Repr, BEq, DecidableEq

/-- A correction is genuine if convergence strictly decreased. -/
def Correction.isGenuine (c : Correction) : Bool :=
  c.newConvergence.value < c.oldConvergence.value

-- ═══════════════════════════════════════════════════════════════════
-- § 6. Door Protocol
-- ═══════════════════════════════════════════════════════════════════

/-- A door: the single point of entry for closing a proof gap.
    "Name the door, write the admissible certificate, write the minimal action." -/
structure Door where
  name          : String
  seam          : Seam
  certificate   : Certificate
  ledger        : Ledger
  minimalAction : String
  corrections   : List Correction
  deriving Repr

-- ═══════════════════════════════════════════════════════════════════
-- § 7. The Three Laws (Boolean Predicates on Door)
-- ═══════════════════════════════════════════════════════════════════

/-- BCF Law: No closure without a certificate.
    Convergence must be honest relative to certificate type. -/
def hasBCFDiscipline (d : Door) : Bool :=
  d.ledger.convergence.isHonest d.certificate.certType

/-- CCO Law: No speed without a ledger.
    Ledger must be balanced for the current arousal level. -/
def hasCCODiscipline (d : Door) : Bool :=
  d.ledger.isBalanced

/-- Seam Law: No synthesis without a seam.
    The seam must be validly named. -/
def hasSeamDiscipline (d : Door) : Bool :=
  d.seam.isValid

/-- A door is cognitively disciplined iff ALL THREE laws hold. -/
def cognitivelyDisciplined (d : Door) : Bool :=
  hasBCFDiscipline d && hasCCODiscipline d && hasSeamDiscipline d

-- ═══════════════════════════════════════════════════════════════════
-- § 8. The Three Laws (Theorems)
-- ═══════════════════════════════════════════════════════════════════

/-- Law 1: Heuristic cert with convergence > 80 fails BCF. -/
theorem bcf_law :
    ∀ (d : Door), d.certificate.certType = .heuristic →
    d.ledger.convergence.value > 80 →
    hasBCFDiscipline d = false := by
  intro d htype hconv
  unfold hasBCFDiscipline Convergence.isHonest
  rw [htype]; simp; omega

/-- Law 2: High arousal with patterns ≥ known fails CCO. -/
theorem cco_law :
    ∀ (d : Door), d.ledger.arousal = .high →
    d.ledger.patternMatches ≥ d.ledger.knownFacts →
    hasCCODiscipline d = false := by
  intro d harousal hpats
  unfold hasCCODiscipline Ledger.isBalanced
  rw [harousal]; simp; omega

/-- Law 3: Unnamed seam fails seam discipline. -/
theorem seam_law :
    ∀ (d : Door), d.seam.isNamed = false →
    hasSeamDiscipline d = false := by
  intro d h; unfold hasSeamDiscipline Seam.isValid; exact h

/-- Corollary: unnamed seam prevents cognitive discipline. -/
theorem unnamed_not_disciplined :
    ∀ (d : Door), d.seam.isNamed = false →
    cognitivelyDisciplined d = false := by
  intro d h
  unfold cognitivelyDisciplined
  have := seam_law d h
  simp [hasSeamDiscipline, Seam.isValid] at this
  simp [hasBCFDiscipline, hasCCODiscipline, hasSeamDiscipline, Seam.isValid, h]

-- ═══════════════════════════════════════════════════════════════════
-- § 9. Governance Bridge
-- ═══════════════════════════════════════════════════════════════════

/-- Disciplined lock permission: cognitive discipline AND governance permission. -/
def disciplinedLockPermitted (d : Door) (lt : LockType) : Prop :=
  cognitivelyDisciplined d = true ∧ permittedLock d.certificate.certType lt

/-- Undisciplined doors cannot get any lock. -/
theorem undisciplined_no_lock :
    ∀ (d : Door) (lt : LockType),
    cognitivelyDisciplined d = false →
    ¬ disciplinedLockPermitted d lt := by
  intro d lt hfail ⟨hdisc, _⟩
  rw [hfail] at hdisc; exact absurd hdisc (by decide)

/-- A disciplined door with hard cert can get proven lock. -/
theorem disciplined_hard_proven :
    ∀ (d : Door),
    cognitivelyDisciplined d = true →
    d.certificate.certType.isHard = true →
    disciplinedLockPermitted d .proven := by
  intro d hdisc hhard
  exact ⟨hdisc, by simp [permittedLock, hhard]⟩

/-- A disciplined door with conditional cert cannot get proven lock. -/
theorem disciplined_conditional_no_proven :
    ∀ (d : Door),
    d.certificate.certType = .conditional →
    ¬ disciplinedLockPermitted d .proven := by
  intro d hcond ⟨_, hperm⟩
  simp [permittedLock, hcond, CertificateType.isHard] at hperm

-- ═══════════════════════════════════════════════════════════════════
-- § 10. Self-Correction Soundness
-- ═══════════════════════════════════════════════════════════════════

/-- Genuine corrections are non-trivial: old ≠ new. -/
theorem genuine_means_different :
    ∀ (c : Correction), c.isGenuine = true →
    c.oldConvergence.value ≠ c.newConvergence.value := by
  intro c h; simp [Correction.isGenuine] at h; omega

/-- A correction is consistent with a convergence value. -/
def Correction.consistentWith (c : Correction) (cv : Convergence) : Bool :=
  c.newConvergence.value == cv.value

-- ═══════════════════════════════════════════════════════════════════
-- § 11. Concrete: The c=2^α Self-Correction
-- ═══════════════════════════════════════════════════════════════════

/-- The c=2^α self-correction: S_allowed is infinite, not finite.
    Q-Spin blocks 70.7% of primes, but 29.3% remain allowed.
    Baker requires FINITE S, which Q-Spin alone does not give. -/
def c_eq_2alpha_correction : Correction where
  claim          := "Q-Spin reduces c to 2^α (finite S-unit equation)"
  error          := "S_allowed is INFINITE (29.3% density). Baker blocked."
  oldConvergence := ⟨95⟩
  newConvergence := ⟨92⟩

/-- The correction is genuine: convergence decreased. -/
theorem correction_genuine :
    c_eq_2alpha_correction.isGenuine = true := by native_decide

/-- Convergence dropped by exactly 3 points. -/
theorem correction_delta :
    c_eq_2alpha_correction.oldConvergence.value -
    c_eq_2alpha_correction.newConvergence.value = 3 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 12. Concrete: The Beal (3,5,7) Door
-- ═══════════════════════════════════════════════════════════════════

/-- The seam: ghost trace elimination at p=7. -/
def beal357Seam : Seam where
  name    := "Door A: Pacetti-VT EliminationExponents for p=7 on ghosts 24.a⊗χ±2 over Q(√5)"
  isNamed := true
  isBridged := false

/-- The certificate: conditional (GAP_B open). -/
def beal357Cert : Certificate where
  certType     := .conditional
  reference    := "Deformation Shield via (5,p,3) paper (arXiv:2512.17845)"
  seam         := "GAP_B: ghost trace elimination for 3|a at p=7"
  verifier     := "Pacetti-VT framework"
  blockingSeam := some "Door A: Magma trace elimination for p=7"

/-- The ledger: 5 known facts, 2 pattern matches, medium arousal, convergence 92. -/
def beal357Ledger : Ledger where
  knownFacts     := 5
  patternMatches := 2
  arousal        := .medium
  convergence    := ⟨92⟩

/-- The Beal (3,5,7) door. -/
def beal357Door : Door where
  name          := "Close GAP_B: eliminate ghost traces for 3|a at p=7"
  seam          := beal357Seam
  certificate   := beal357Cert
  ledger        := beal357Ledger
  minimalAction := "Run EliminationExponents(7, [24.a⊗χ₂, 24.a⊗χ₋₂], Q(√5)) in Magma"
  corrections   := [c_eq_2alpha_correction]

/-- The (3,5,7) door has BCF discipline: 92 ≤ 95 for conditional. -/
theorem beal357_bcf : hasBCFDiscipline beal357Door = true := by native_decide

/-- The (3,5,7) door has CCO discipline: 2 ≤ 5×2 at medium. -/
theorem beal357_cco : hasCCODiscipline beal357Door = true := by native_decide

/-- The (3,5,7) door has seam discipline: seam is named. -/
theorem beal357_seam : hasSeamDiscipline beal357Door = true := by native_decide

/-- MAIN: The Beal (3,5,7) door is cognitively disciplined. -/
theorem beal357_disciplined :
    cognitivelyDisciplined beal357Door = true := by native_decide

/-- The correction is consistent with the ledger. -/
theorem beal357_correction_consistent :
    c_eq_2alpha_correction.consistentWith beal357Ledger.convergence = true := by
  native_decide

/-- Can get conditional lock (disciplined + conditional cert). -/
theorem beal357_conditional_lock :
    disciplinedLockPermitted beal357Door .conditional := by
  constructor
  · exact beal357_disciplined
  · simp [beal357Door, beal357Cert, permittedLock]

/-- Cannot get proven lock (conditional cert). -/
theorem beal357_no_proven :
    ¬ disciplinedLockPermitted beal357Door .proven :=
  disciplined_conditional_no_proven beal357Door rfl

-- ═══════════════════════════════════════════════════════════════════
-- § 13. Negative Example: Undisciplined Door
-- ═══════════════════════════════════════════════════════════════════

/-- A door with no named seam, heuristic cert, high arousal. -/
def undisciplinedDoor : Door where
  name          := "Close some gap (unspecified)"
  seam          := { name := "", isNamed := false, isBridged := false }
  certificate   := { certType := .heuristic, reference := "gut feeling", seam := "none" }
  ledger        := { knownFacts := 1, patternMatches := 5, arousal := .high, convergence := ⟨50⟩ }
  minimalAction := "unclear"
  corrections   := []

/-- Fails seam discipline. -/
theorem undisciplined_fails_seam :
    hasSeamDiscipline undisciplinedDoor = false := by native_decide

/-- Fails CCO discipline (high arousal, 5 patterns ≥ 1 known). -/
theorem undisciplined_fails_cco :
    hasCCODiscipline undisciplinedDoor = false := by native_decide

/-- NOT cognitively disciplined. -/
theorem undisciplined_not_disciplined :
    cognitivelyDisciplined undisciplinedDoor = false := by native_decide

/-- Therefore: no lock of any kind. -/
theorem undisciplined_no_lock_any :
    ∀ (lt : LockType), ¬ disciplinedLockPermitted undisciplinedDoor lt :=
  fun lt => undisciplined_no_lock undisciplinedDoor lt undisciplined_not_disciplined

end BealFoundry.CognitiveDiscipline
