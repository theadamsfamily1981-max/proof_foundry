import BealFoundry.Governance

/-!
# Soundness of the Proof Governance Kernel

Main theorems establishing that the certificate discipline is sound.

## Results

1. `proven_is_terminal`: PROVEN lock admits no transitions.
2. `safety_heuristic_not_proven`: Heuristic cannot produce proven lock.
3. `strength_gap`: Hard certificates are strictly stronger than soft.
4. `chain_active_to_proven_has_evidence`: Path to proven lock requires evidence.
-/

namespace BealFoundry

-- § 1. Core Safety Properties

/-- Heuristic evidence cannot produce a proven lock. -/
theorem safety_heuristic_not_proven :
    ¬ permittedLock .heuristic .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- Conditional evidence cannot produce a proven lock. -/
theorem safety_conditional_not_proven :
    ¬ permittedLock .conditional .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- Proof evidence CAN produce a proven lock. -/
theorem safety_proof_permits_proven :
    permittedLock .proof .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- Reduction evidence CAN produce a proven lock. -/
theorem safety_reduction_permits_proven :
    permittedLock .reduction .proven := by
  simp [permittedLock, CertificateType.isHard]

/-- Computation evidence CAN produce a proven lock. -/
theorem safety_computation_permits_proven :
    permittedLock .computation .proven := by
  simp [permittedLock, CertificateType.isHard]

-- § 2. Proven is Terminal

/-- A proven lock is terminal: there is no valid transition out of it. -/
theorem proven_is_terminal :
    ∀ (s : DomainState), ¬ ValidTransition (.locked .proven) s := by
  intro s h
  cases h with
  | lockToReactivate lt hcan =>
    simp [LockType.canReopen] at hcan

-- § 3. State Machine Properties

/-- Reactivation always returns to active. -/
theorem reactivation_returns_to_active :
    ∀ (s : DomainState), ValidTransition .reactivated s → s = .active := by
  intro s h
  cases h with
  | reactivateToActive => rfl

/-- Cannot skip from active directly to locked. -/
theorem no_skip_active_to_locked :
    ∀ (lt : LockType), ¬ ValidTransition .active (.locked lt) := by
  intro lt h
  cases h

/-- Cannot go backwards from dropped to active. -/
theorem no_backwards_drop_to_active :
    ∀ (ct : CertificateType), ¬ ValidTransition (.dropped ct) .active := by
  intro ct h
  cases h

-- § 4. Certificate Chain Soundness

/-- A chain from active to proven-locked must pass through dropped.
    This ensures every proven lock has evidence backing it. -/
theorem chain_active_to_proven_has_evidence :
    CertChain .active (.locked .proven) →
    ∃ (ct : CertificateType), Nonempty (CertChain .active (.dropped ct)) := by
  intro chain
  cases chain with
  | single h => cases h
  | cons h₁ rest =>
    cases h₁ with
    | activeToDrop ct => exact ⟨ct, ⟨.single (.activeToDrop ct)⟩⟩

-- § 5. Strength Classification

/-- All hard certificate types have strength ≥ 3. -/
theorem hard_implies_strength_ge_3 :
    ∀ (ct : CertificateType), ct.isHard = true → ct.strength ≥ 3 := by
  intro ct h
  cases ct <;> simp [CertificateType.isHard] at h <;> simp [CertificateType.strength] <;> omega

/-- All soft certificate types have strength ≤ 2. -/
theorem soft_implies_strength_le_2 :
    ∀ (ct : CertificateType), ct.isHard = false → ct.strength ≤ 2 := by
  intro ct h
  cases ct <;> simp [CertificateType.isHard] at h <;> simp [CertificateType.strength] <;> omega

/-- The strength gap: hard certificates are strictly stronger than soft ones. -/
theorem strength_gap :
    ∀ (ct₁ ct₂ : CertificateType),
    ct₁.isHard = true → ct₂.isHard = false →
    ct₁.strength > ct₂.strength := by
  intro ct₁ ct₂ h₁ h₂
  have hge := hard_implies_strength_ge_3 ct₁ h₁
  have hle := soft_implies_strength_le_2 ct₂ h₂
  omega

end BealFoundry
