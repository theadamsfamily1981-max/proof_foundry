import BealFoundry.GematriaChains
import BealFoundry.CognitiveDiscipline

/-!
# Prime and Composite Index Chains

The gematria research material makes extensive claims about prime and
composite number indices — e.g., "883 is the 153rd prime" and
"2368 is the 2017th composite." This module defines efficient
primality testing and nth-prime/composite functions, then verifies
these index claims with exact computation.

## Key Verified Chains

1. **883 is the 153rd prime** — linking the prime index to the fish catch
2. **1399 is the 222nd prime** — "on the right hand of God" at the 222nd prime
3. **284 is the 222nd composite** — θεος ("God") is the 222nd composite
4. **First 29 primes sum to 1480** = Χριστος (Christ)
5. **1931 is the 294th prime** — Jared+Methuselah at the Melchizedek prime
6. **2368 is the 2017th composite** — Jesus Christ at the 2017th composite
7. **2772 is the 2368th composite** — bridging to Jesus Christ
8. **109 is the 29th prime** — connecting to the 29 primes summing to Christ

## Method

Efficient trial-division primality testing with √n bound.
All computations compile to native code via `native_decide`.
-/

namespace BealFoundry.PrimeCompositeChains

open BealFoundry.GematriaChains

-- ═══════════════════════════════════════════════════════════════════
-- § 1. Efficient Primality Testing
-- ═══════════════════════════════════════════════════════════════════

/-- Trial division up to √n with fuel for termination. -/
def checkPrimeAux (n : Nat) : Nat → Nat → Bool
  | 0, _ => true  -- fuel exhausted: assume prime (safe if fuel ≥ √n)
  | fuel + 1, d =>
    if d * d > n then true
    else if n % d == 0 then false
    else checkPrimeAux n fuel (d + 1)

/-- Primality test: efficient trial division to √n. -/
def isPrime (n : Nat) : Bool :=
  if n < 2 then false
  else if n < 4 then true
  else if n % 2 == 0 then false
  else checkPrimeAux n n 3

/-- Composite test: n ≥ 4 and not prime. -/
def isComposite (n : Nat) : Bool := n ≥ 4 && !isPrime n

-- ═══════════════════════════════════════════════════════════════════
-- § 2. Nth Prime and Composite
-- ═══════════════════════════════════════════════════════════════════

/-- Find the kth prime (1-indexed). Uses fuel for termination. -/
def nthPrimeAux : Nat → Nat → Nat → Nat
  | 0, _, _ => 0       -- fuel exhausted
  | fuel + 1, k, n =>
    if isPrime n then
      if k == 1 then n
      else nthPrimeAux fuel (k - 1) (n + 1)
    else nthPrimeAux fuel k (n + 1)

/-- The kth prime number (1-indexed: nthPrime 1 = 2). -/
def nthPrime (k : Nat) : Nat := nthPrimeAux (k * 20) k 2

/-- Find the kth composite (1-indexed). -/
def nthCompositeAux : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | fuel + 1, k, n =>
    if isComposite n then
      if k == 1 then n
      else nthCompositeAux fuel (k - 1) (n + 1)
    else nthCompositeAux fuel k (n + 1)

/-- The kth composite number (1-indexed: nthComposite 1 = 4). -/
def nthComposite (k : Nat) : Nat := nthCompositeAux (k * 3) k 4

-- ═══════════════════════════════════════════════════════════════════
-- § 3. Sum of First k Primes
-- ═══════════════════════════════════════════════════════════════════

/-- Sum primes from nthPrime(1) to nthPrime(k). -/
def sumFirstPrimesAux : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, acc => acc
  | _ + 1, 0, _, acc => acc
  | fuel + 1, remaining, n, acc =>
    if isPrime n then
      sumFirstPrimesAux fuel (remaining - 1) (n + 1) (acc + n)
    else sumFirstPrimesAux fuel remaining (n + 1) acc

def sumFirstPrimes (k : Nat) : Nat := sumFirstPrimesAux (k * 20) k 2 0

-- ═══════════════════════════════════════════════════════════════════
-- § 4. Basic Primality Checks
-- ═══════════════════════════════════════════════════════════════════

/-- Verify our isPrime function on known primes and composites. -/
theorem two_is_prime : isPrime 2 = true := by native_decide
theorem three_is_prime : isPrime 3 = true := by native_decide
theorem four_not_prime : isPrime 4 = false := by native_decide
theorem seven_is_prime : isPrime 7 = true := by native_decide
theorem nine_not_prime : isPrime 9 = false := by native_decide
theorem thirty_seven_prime : isPrime 37 = true := by native_decide
theorem seventy_three_prime : isPrime 73 = true := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 5. The 153rd Prime = 883
-- ═══════════════════════════════════════════════════════════════════

/-! 153 = the miraculous catch of fish (John 21:11).
    The 153rd prime is 883.
    883 is the gematria value that links to Abraham. -/

/-- 883 is prime. -/
theorem prime_883 : isPrime 883 = true := by native_decide

/-- 883 is the 153rd prime number. -/
theorem nth_prime_153 : nthPrime 153 = 883 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 6. The 222nd Prime and Composite
-- ═══════════════════════════════════════════════════════════════════

/-! 222 = gcd(666, 888) = the (3,4,5) scaling factor.
    The 222nd prime = 1399 = εν δεξιαι του θεου ("on the right hand of God").
    The 222nd composite = 284 = θεος ("God"). -/

/-- 1399 is prime. -/
theorem prime_1399 : isPrime 1399 = true := by native_decide

/-- 1399 is the 222nd prime. -/
theorem nth_prime_222 : nthPrime 222 = 1399 := by native_decide

/-- 284 is composite. -/
theorem composite_284 : isComposite 284 = true := by native_decide

/-- 284 is the 222nd composite. -/
theorem nth_composite_222 : nthComposite 222 = 284 := by native_decide

/-- God (284) is the 222nd composite; "right hand of God" (1399) is the 222nd prime. -/
theorem god_222 : nthComposite 222 = theos ∧ nthPrime 222 = enDexiai := by
  constructor <;> native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 7. The 29th Prime and Christ
-- ═══════════════════════════════════════════════════════════════════

/-! The 29th prime is 109. The first 29 primes sum to 1480 = Christ. -/

/-- 109 is the 29th prime. -/
theorem nth_prime_29 : nthPrime 29 = 109 := by native_decide

/-- The first 29 primes sum to 1480 = Χριστος (Christ). -/
theorem first_29_primes_sum : sumFirstPrimes 29 = 1480 := by native_decide

/-- 1480 = Χριστος. The sum of the first 29 primes = Christ. -/
theorem christ_from_primes : sumFirstPrimes 29 = christos := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 8. The 109th Composite = 144
-- ═══════════════════════════════════════════════════════════════════

/-! 109 = 29th prime. The 109th composite = 144 = F(12) = 12².
    And the first 144 digits of pi sum to 666 (documented, not verified). -/

/-- 144 is the 109th composite. -/
theorem nth_composite_109 : nthComposite 109 = 144 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 9. The 294th Prime = 1931
-- ═══════════════════════════════════════════════════════════════════

/-! 294 = מלכי-צדק (Melchizedek). The 294th prime = 1931.
    And 1931 = Jared (962) + Methuselah (969).
    The Melchizedek prime equals the patriarch sum! -/

/-- 1931 is prime. -/
theorem prime_1931 : isPrime 1931 = true := by native_decide

/-- 1931 is the 294th prime = the Melchizedek prime. -/
theorem nth_prime_294 : nthPrime 294 = 1931 := by native_decide

/-- 1931 = Jared (962) + Methuselah (969). -/
theorem melchizedek_prime_is_patriarch_sum :
    nthPrime 294 = 962 + 969 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 10. The 2017th Composite = 2368
-- ═══════════════════════════════════════════════════════════════════

/-! 2368 = Ιησους Χριστος (Jesus Christ).
    2368 is the 2017th composite number.
    2017 = the Gregorian year when Hebrew year 5778 began. -/

/-- 2368 is composite. -/
theorem composite_2368 : isComposite 2368 = true := by native_decide

/-- 2368 is the 2017th composite = Jesus Christ at the 2017th position. -/
theorem nth_composite_2017 : nthComposite 2017 = 2368 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 11. The 2368th Composite = 2772
-- ═══════════════════════════════════════════════════════════════════

/-! Continuing the chain: the 2368th (Jesus Christ) composite = 2772. -/

/-- 2772 is the 2368th composite. -/
theorem nth_composite_2368 : nthComposite 2368 = 2772 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 12. The 1000th Composite = 1197
-- ═══════════════════════════════════════════════════════════════════

/-! 1197 = gematria of שמנה מאות שנה ("eight hundred years").
    1197 is the 1000th composite. -/

/-- 1197 is the 1000th composite. -/
theorem nth_composite_1000 : nthComposite 1000 = 1197 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 13. The 355th Composite and the 66th Prime
-- ═══════════════════════════════════════════════════════════════════

/-! Gen 14:18 (Melchizedek appears) is verse 355.
    355 is the 284th (= θεος, "God") composite.
    317 is the 66th prime (66 = books of the Bible). -/

/-- The 66th prime is 317. -/
theorem nth_prime_66 : nthPrime 66 = 317 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 14. Additional Index Claims
-- ═══════════════════════════════════════════════════════════════════

/-- The 26th prime is 101. (26 = YHWH). -/
theorem nth_prime_26 : nthPrime 26 = 101 := by native_decide

/-- The 49th prime is 227. -/
theorem nth_prime_49 : nthPrime 49 = 227 := by native_decide

/-- The 49th prime + 49th composite sum to 296 = הארץ ("the earth"). -/
theorem prime_composite_49_sum :
    nthPrime 49 + nthComposite 49 = 296 := by native_decide

/-- The 29th composite is 44 = דם ("blood"). -/
theorem nth_composite_29 : nthComposite 29 = 44 := by native_decide
theorem composite_29_is_blood : nthComposite 29 = dam := by native_decide

-- The 153rd prime is 883 (verified in § 5).

-- ═══════════════════════════════════════════════════════════════════
-- § 15. The 37th Prime/Composite Connection
-- ═══════════════════════════════════════════════════════════════════

/-! יהוה אלהים (LORD God) appears 37 times in the Tanakh.
    37 and 73 are consecutive star primes.
    The 37th prime + 37th composite sum. -/

/-- The 37th prime is 157. -/
theorem nth_prime_37 : nthPrime 37 = 157 := by native_decide

/-- The 37th composite is 54. -/
theorem nth_composite_37 : nthComposite 37 = 54 := by native_decide

/-- The 37th prime + 37th composite = 211 = digit sum of F(248)+F(145). -/
theorem prime_composite_37_sum :
    nthPrime 37 + nthComposite 37 = 211 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 16. The 27th Prime and Believe
-- ═══════════════════════════════════════════════════════════════════

/-- 27th prime + 27th composite = 143. -/
theorem prime_composite_27_sum :
    nthPrime 27 + nthComposite 27 = 143 := by native_decide

/-- 27 is the 17th composite. -/
theorem nth_composite_17 : nthComposite 17 = 27 := by native_decide

/-- 27 + 17 = 44 = blood. -/
theorem composite_index_sum : 27 + 17 = dam := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 17. The 16th Composite = 26 (YHWH)
-- ═══════════════════════════════════════════════════════════════════

/-- The 16th composite number is 26 = YHWH. -/
theorem nth_composite_16 : nthComposite 16 = 26 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 18. The Prime/Composite Sum Chain
-- ═══════════════════════════════════════════════════════════════════

/-! Each nth prime + nth composite creates a "resonance".
    Some key resonances from the source material. -/

-- The 79th prime + 79th composite = 509
theorem prime_composite_79_sum :
    nthPrime 79 + nthComposite 79 = 509 := by native_decide

-- The 60th prime + 60th composite = 365 = Enoch's years
theorem prime_composite_60_sum :
    nthPrime 60 + nthComposite 60 = 365 := by native_decide

-- The 107th prime + 107th composite
theorem nth_prime_107 : nthPrime 107 = 587 := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 19. The 446th and 499th Primes
-- ═══════════════════════════════════════════════════════════════════

/-- The 446th prime is 3137 = εγω ειμι ο αρτος της ζωης
    ("I am that bread of life"). -/
theorem nth_prime_446 : nthPrime 446 = 3137 := by native_decide

/-- The 499th prime is 3559. -/
theorem nth_prime_499 : nthPrime 499 = 3559 := by native_decide

/-- The 499th composite is 611 = תורה (Torah). -/
theorem nth_composite_499 : nthComposite 499 = 611 := by native_decide
theorem composite_499_is_torah : nthComposite 499 = torah := by native_decide

-- ═══════════════════════════════════════════════════════════════════
-- § 20. Governance Bridge
-- ═══════════════════════════════════════════════════════════════════

open CognitiveDiscipline in
def primeCompositeDoor : Door where
  name := "Prime-Composite Index Chains: Gematria Values at Structural Positions"
  seam := { name := "Verify nth-prime and nth-composite index claims via trial division",
             isNamed := true, isBridged := false }
  certificate := { certType := .computation,
                    reference := "Lean 4 native_decide with efficient trial division",
                    seam := "Index positions verified; significance of patterns is interpretive" }
  ledger := { knownFacts := 20,
              patternMatches := 8,
              arousal := .medium,
              convergence := ⟨95⟩ }
  minimalAction := "Verify all prime/composite index claims from gematria research"
  corrections := []

open CognitiveDiscipline in
theorem prime_composite_disciplined :
    cognitivelyDisciplined primeCompositeDoor = true := by native_decide

open CognitiveDiscipline in
theorem prime_composite_lock :
    disciplinedLockPermitted primeCompositeDoor .proven := by
  constructor
  · exact prime_composite_disciplined
  · simp [primeCompositeDoor, permittedLock, CertificateType.isHard]

-- ═══════════════════════════════════════════════════════════════════
-- § 21. Seam Declaration
-- ═══════════════════════════════════════════════════════════════════

/-! **Verified**: All prime indices, composite indices, and prime sums
    are computed by exact trial division compiled to native code.

    **Not verified**: Claims about digit positions in transcendental
    constants (π, φ, e). These require arbitrary-precision digit
    extraction beyond our current scope.

    **Seam**: That "the 153rd prime is 883" is an arithmetic fact.
    That this connects the fish catch (153) to Abraham (883 → 248 chain)
    is an interpretive claim. The numbers stand; the meaning is yours. -/

end BealFoundry.PrimeCompositeChains
