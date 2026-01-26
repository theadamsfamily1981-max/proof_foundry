import BealFoundry.Governance
import BealFoundry.Soundness

/-!
# Observer Contract

An observer (e.g., an AI system like Ara) may witness mathematical domains,
attach certificates, and update metrics. The governance kernel constrains
what the observer may and may not do:

- May: observe, classify evidence, attach certificates, record metrics
- May not: promote to proven lock without hard certificate
- May not: skip lifecycle phases (active → locked is forbidden)
- May not: reopen a proven lock

## Results

1. `observer_cannot_promote_soft`: Soft certificates cannot produce proven locks.
2. `observer_must_pass_through_dropped`: No skip from active to locked.
3. `observer_cannot_reopen_proven`: Proven locks are terminal for observers.
4. `observer_hard_cert_sufficient`: Hard certificates suffice for proven lock.
5. `observer_lifecycle_well_formed`: Valid observation sequences respect lifecycle.
-/

namespace BealFoundry

-- § 1. Observer Action

/-- An action an observer may take on a domain. -/
inductive ObserverAction where
  | observe                                          -- Witness current state
  | attachCertificate (ct : CertificateType)         -- Attach evidence
  | requestLock (ct : CertificateType) (lt : LockType) -- Request state lock
  | requestReactivation (lt : LockType)              -- Request reopening
  deriving Repr

-- § 2. Observer Permission

/-- Whether an observer action is permitted given the current domain state. -/
def observerPermitted (state : DomainState) (action : ObserverAction) : Prop :=
  match action with
  | .observe => True   -- Observation is always permitted
  | .attachCertificate ct =>
      state = .active  -- Can only attach certificates to active domains
  | .requestLock ct lt =>
      (∃ ct', state = .dropped ct') ∧ permittedLock ct lt
  | .requestReactivation lt =>
      state = .locked lt ∧ lt.canReopen = true

-- § 3. Core Safety Theorems

/-- An observer with only soft (heuristic/conditional) evidence
    cannot request a proven lock. -/
theorem observer_cannot_promote_soft :
    ∀ (ct : CertificateType), ct.isHard = false →
    ∀ (s : DomainState), ¬ observerPermitted s (.requestLock ct .proven) := by
  intro ct hsoft s h
  simp [observerPermitted] at h
  obtain ⟨⟨ct', _⟩, hperm⟩ := h
  simp [permittedLock] at hperm
  cases ct <;> simp [CertificateType.isHard] at hsoft <;> simp [CertificateType.isHard] at hperm

/-- An observer cannot skip from active directly to locked.
    The governance kernel enforces the dropped intermediate state. -/
theorem observer_must_pass_through_dropped :
    ∀ (ct : CertificateType) (lt : LockType),
    ¬ observerPermitted .active (.requestLock ct lt) := by
  intro ct lt h
  simp [observerPermitted] at h

/-- An observer cannot reopen a proven lock. -/
theorem observer_cannot_reopen_proven :
    ¬ observerPermitted (.locked .proven) (.requestReactivation .proven) := by
  intro h
  simp [observerPermitted, LockType.canReopen] at h

/-- An observer with a hard certificate can request a proven lock
    on a dropped domain. -/
theorem observer_hard_cert_sufficient :
    ∀ (ct : CertificateType), ct.isHard = true →
    ∀ (ct' : CertificateType),
    observerPermitted (.dropped ct') (.requestLock ct .proven) := by
  intro ct hhard ct'
  simp [observerPermitted, permittedLock]
  exact hhard

-- § 4. Observation Sequence

/-- An observation sequence is a list of (state, action) pairs
    where each action is permitted in its state. -/
inductive ObsSequence : DomainState → Type where
  | done : (s : DomainState) → ObsSequence s
  | step : {s : DomainState} →
           (action : ObserverAction) →
           observerPermitted s action →
           {s' : DomainState} →
           ValidTransition s s' →
           ObsSequence s' →
           ObsSequence s

/-- Every observation sequence starting from active that reaches
    proven-locked must contain a dropped state. -/
theorem observer_lifecycle_well_formed :
    ∀ (chain : CertChain .active (.locked .proven)),
    ∃ (ct : CertificateType), Nonempty (CertChain .active (.dropped ct)) :=
  chain_active_to_proven_has_evidence

-- § 5. Certificate Attachment Rules

/-- Attaching a certificate is only permitted on active domains. -/
theorem attach_requires_active :
    ∀ (ct : CertificateType) (lt : LockType),
    ¬ observerPermitted (.locked lt) (.attachCertificate ct) := by
  intro ct lt h
  simp [observerPermitted] at h

/-- Attaching a certificate is not permitted on dropped domains. -/
theorem attach_not_on_dropped :
    ∀ (ct ct' : CertificateType),
    ¬ observerPermitted (.dropped ct') (.attachCertificate ct) := by
  intro ct ct' h
  simp [observerPermitted] at h

-- § 6. Completeness: Hard Evidence Path

/-- There exists a valid observer path from active to proven-locked
    using a hard certificate: observe → attach → drop → lock. -/
theorem observer_can_reach_proven :
    ∃ (ct : CertificateType),
      ct.isHard = true ∧
      observerPermitted .active (.attachCertificate ct) ∧
      observerPermitted (.dropped ct) (.requestLock ct .proven) := by
  exact ⟨.proof, rfl,
    by simp [observerPermitted],
    by simp [observerPermitted, permittedLock, CertificateType.isHard]⟩

end BealFoundry
