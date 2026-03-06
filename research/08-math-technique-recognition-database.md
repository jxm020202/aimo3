# Comprehensive math technique-recognition database for olympiad problem solving

**The core finding: across 100+ sources, approximately 85 distinct competition math techniques can be mapped to specific recognition triggers — pattern cues in problem statements that signal which approach to deploy.** This database synthesizes technique names, "if you see X, try Y" guidance, key theorem statements, and worked-example references from AoPS, Evan Chen's OTIS/EGMO materials, Yufei Zhao's MIT handouts, Brilliant.org, imomath.com, CP-Algorithms, Keith Conrad's UConn blurbs, and multiple olympiad textbooks. The techniques span six domains: geometry (22 techniques), number theory (9 techniques), algebra (13 techniques), functional equations (8 techniques), inequalities (14 techniques), and combinatorics (12 techniques), plus 7 cross-cutting meta-strategies. No large-scale dataset yet maps problems to techniques systematically — **CHAMP (270 problems, 54 concepts, 330 hints) is the only existing dataset with explicit technique labels**, making this compilation the most comprehensive technique-recognition reference currently available.

---

## GEOMETRY: 22 techniques from synthetic to projective

### Power of a Point and radical axes

**Power of a Point** is the workhorse of circle geometry. For any point P and circle ω, the quantity PA·PB is constant across all secants through P, equaling PO² − r². The recognition triggers are direct: **if two chords intersect, if a tangent meets a secant from the same external point, or if you need to prove four points concyclic**, Power of a Point applies. The converse — PA·PB = PC·PD implies concyclicity — is equally important. Sources: AoPS wiki, Yufei Zhao's Power of a Point handout (9 IMO-level problems including IMO 2000, USAMO 1998, IMO 1995).

**Radical axis** extends Power of a Point to multiple circles. The locus of points with equal power with respect to two circles forms a line perpendicular to the line of centers. The NYC Math Team's handout provides the sharpest recognition cue: **"If you ever want to prove that three strange lines are concurrent, the radical axis theorem will often help."** The radical center theorem (three pairwise radical axes concur) is the key result. A powerful trick: treat a point as a degenerate circle of radius zero, so the perpendicular bisector of a segment becomes a radical axis — this proves both the concurrency of altitudes and perpendicular bisectors. Sources: AoPS wiki (graded problem set at three difficulty levels), NYC Math Team PDF by Tovi Wen, EGMO Theorem 2.9.

### Barycentric coordinates for triangle-center problems

Every point P in the plane of triangle ABC can be written as P = (x : y : z) in homogeneous barycentric coordinates, with key points having clean expressions: centroid G = (1:1:1), incenter I = (a:b:c), symmedian K = (a²:b²:c²), and orthocenter H = (tan A : tan B : tan C). **Use barycentric coordinates when a problem is set in a triangle with many cevians or special points and a synthetic approach stalls** — particularly when the incenter or symmedian point is central, since these have the cleanest coordinates. Avoid when the circumcenter or orthocenter dominates, as their coordinates are messy. Key tools include the EFFT (perpendicularity condition), the circle equation a²yz + b²zx + c²xy + (x+y+z)(ux+vy+wz) = 0, and Conway's notation. The full 40-page Schindler–Chen handout provides seven worked olympiad solutions (USAMO 2001/2, USAMO 2008/2, ISL 2005 G5, among others) with commentary on "how one would invent the solution." Sources: Evan Chen bary-full.pdf (usefulness 5/5), EGMO Chapter 7.

### Inversion transforms tangent-circle nightmares into lines

Inversion about a circle centered at O with radius r maps each point P to P* on ray OP with OP·OP* = r². Lines through O map to themselves; **circles through O become lines; circles not through O become circles; and tangency is preserved**. The fundamental recognition cue, stated memorably by imomath.com: "Some pictures CRY to be inverted: there are many circles and lines through the same point A. Invert through A."

| Recognition trigger | Action |
|---|---|
| Many circles through one common point P | Invert at P — circles become lines |
| Tangent circles (internal or external) | Invert at tangent point — tangent circles become parallel lines |
| Mixtilinear/curvilinear incircles | Classic inversion setup at tangent point |
| Products PA·PB in metric relations | Distance formula A'B' = r²·AB/(OA·OB) handles these naturally |
| Incircle + excircle + circumcircle interactions | √bc inversion about vertex A (radius √(AB·AC)), which swaps B↔C and maps circumcircle to line BC |
| Collinearity ↔ concyclicity conversion needed | Inversion swaps these, so choose the easier direction |
| Feuerbach-type or Apollonius-type configurations | Classic inversion applications |

The **√bc inversion** deserves special mention: inversion about A with radius √(AB·AC), followed by reflection in the A-angle bisector, fixes the triangle while swapping B↔C and dramatically simplifying incenter/excircle configurations. Sources: Adam Kelly's inversion notes, Gunmay Handa's "Inversion on the Fly" (15 graded problems), imomath.com, EGMO Chapter 8.

### Cross ratios, harmonic bundles, and projective geometry

**Cross ratios** encode projective relationships: for four collinear points, (A,B;X,Y) = (XA/XB)÷(YA/YB). The critical special case is **harmonic bundles where the cross ratio equals −1**. These arise naturally from concurrent cevians (if AD, BE, CF concur and EF meets BC at X, then (X,D;B,C) = −1), from tangent lines to circles, and from angle bisector configurations.

| Recognition trigger | Action |
|---|---|
| Midpoints with parallel lines or points at infinity | Encode midpoint as harmonic bundle: (A,B;M,P∞) = −1 |
| Tangent lines from external point to circle | Tangent configuration automatically creates harmonic bundles |
| Concurrent cevians meeting opposite sides | Cevian feet + sideline intersection = harmonic bundle |
| Angle bisector + perpendicularity appearing together | Right angle + bisector = harmonic (any two of the three implies the third) |
| Symmedian or isogonal conjugate | Harmonic quadrilateral characterization on circumcircle |
| Only incidence relations matter (no metric data) | Pure projective problem — can apply projective transformations |

**Projective transformations** that preserve the circumcircle can send any convex cyclic quadrilateral to a rectangle, trivializing many problems. **Pascal's theorem** (hexagon inscribed in conic → three cross-intersection points collinear) and **Brianchon's theorem** (hexagon circumscribed about conic → three main diagonals concurrent) are the key projective tools. **Poles and polars** connect to Brocard's theorem: for cyclic ABCD, the diagonal triangle of the complete quadrilateral has the circumcenter as its orthocenter. Sources: Evan Chen's Cross Ratios MOP 2016 handout, Victor Rong's projective geometry PDF, Alexander Remorov's IMO Training 2010 notes, EGMO Chapter 9.

### Named olympiad lemmas as pattern-matching shortcuts

Evan Chen's "Lemmas in AoPS Geometry" catalogues recurring configurations that experienced contestants recognize instantly:

**Incenter/Excircle Lemma (Fact 5 / Trillium)**: In △ABC with incenter I and A-excircle I_A, the circumcircle of triangle BIC has its center at the arc midpoint L of minor arc BC. Recognition: any time incenter/excircle and circumcircle interact. **Shooting Lemma (Death Star Lemma)**: When a small circle is tangent to a chord AB of a big circle at K and internally tangent to the big circle at T, ray TK passes through the arc midpoint M of AB. Recognition: "If you see a small circle tangent to a chord of a big circle and internally tangent to the big circle." **Iran Lemma**: Connects the intouch triangle's tangent chord, angle bisectors, and side midpoints. Recognition: "If you see an incircle tangent point and a midpoint of a side." Additional named configurations include **Reim's Theorem** (shortcut for two circles intersecting the same pair of lines), **Miquel's Point** (circumcircles of a complete quadrilateral's four triangles concur), **Simson Line** (feet of perpendiculars from circumcircle point to triangle sides are collinear), and **Monge's Theorem** (three pairwise external tangent intersections of three circles are collinear). Sources: Evan Chen's Lemmas PDF, EGMO, AwesomeMath's "Lemmas in Olympiad Geometry" (18-chapter progressive structure from Power of a Point through Apollonian circles).

### Additional geometry techniques

**Isogonal conjugation** maps cevians to their reflections across angle bisectors. Use when angle bisector reflections or symmetric angle conditions appear. Key fact: the circumcenter and orthocenter are isogonal conjugates. **Homothety** maps figures to scaled copies — use when you see parallel lines, similar figures, or tangent circles (the tangent point is the center of homothety). **Complex numbers** on the unit circle work best when many points lie on the circumcircle and rotations/reflections play a role. **Directed angles** (angles mod 180°) eliminate configuration case-work in all angle-chasing arguments. Sources: AoPS wiki articles, EGMO Chapters 1–10, Yufei Zhao's "Cyclic Quadrilaterals — The Big Picture" and "Three Lemmas in Geometry."

---

## NUMBER THEORY: 9 core techniques from valuations to descent

### Lifting the Exponent Lemma trivializes power-difference divisibility

**LTE provides explicit formulas for ν_p(xⁿ ± yⁿ)** — the highest power of prime p dividing xⁿ ± yⁿ. For odd prime p with p ∤ x, p ∤ y, and p | (x−y): ν_p(xⁿ − yⁿ) = ν_p(x−y) + ν_p(n). The plus version requires p | (x+y) and n odd. The p = 2 case adds: ν_2(xⁿ − yⁿ) = ν_2(x−y) + ν_2(x+y) + ν_2(n) − 1 for odd x,y and even n.

Recognition triggers: **if you see xⁿ − yⁿ or xⁿ + yⁿ and need the exact power of a prime dividing it, LTE is the tool**. Common problem types include exponential Diophantine equations (aⁿ + bⁿ = cᵏ) and "find the largest power of p dividing..." questions. Critical condition often forgotten: p must NOT divide x or y. Example: IMO 2000 P5 uses LTE to analyze ν_3(2ⁿ + 1). Sources: AoPS wiki, Amir Hossein Parvardi's LTE v6 PDF, Carl Joshua Quines' handout, Brilliant.org.

### Hensel's Lemma lifts solutions through prime powers

If a polynomial f(x) has a simple root r modulo prime p (meaning f(r) ≡ 0 mod p and f'(r) ≢ 0 mod p), then this root lifts uniquely to all higher powers pᵏ. **The lifting formula is exactly Newton's method: s ≡ r − f(r)/f'(r) (mod p^(k+1)).** Use when solving polynomial congruences mod pᵏ for large k — first solve mod p, then lift. The derivative condition (simple root) is crucial: when f'(r) ≡ 0 mod p, the standard lemma fails. Sources: AoPS wiki, Keith Conrad's UConn blurb (rigorous treatment), Brilliant.org.

### Vieta Jumping is descent via quadratic root-swapping

Given a solution (a,b) to a symmetric quadratic relation, fix one variable and use Vieta's formulas to find the other root of the resulting quadratic — producing a "smaller" solution that creates an impossible descent. **The signature trigger: a relation that is quadratic in one variable when the other is fixed**, particularly when asked to prove divisibility or that an expression is a perfect square. The most famous application is **IMO 1988 P6**: prove (a² + b²)/(ab + 1) is a perfect square. Vieta jumping problems can often ONLY be solved by Vieta jumping. Sources: Brilliant.org wiki, Wikipedia.

### Orders, primitive roots, and the n²+1 lemma

The order of a modulo n, ord_n(a), is the smallest positive m with aᵐ ≡ 1 mod n. **If you see aᴺ ≡ 1 (mod p) and need to constrain N, the fundamental fact is ord_p(a) | N.** The powerful **n² + 1 lemma** follows: for odd prime p, if p | n² + 1, then ord_p(n) = 4, so 4 | (p−1), meaning p ≡ 1 mod 4. This generalizes via cyclotomic polynomials: if p | Φ_n(a), then either p | n or p ≡ 1 mod n. Evan Chen calls this "one of the most important techniques in number theory." Sources: Evan Chen's "Orders Modulo a Prime" handout, Justin Stevens' Olympiad Number Theory PDF.

### Zsigmondy's theorem guarantees new prime factors

For coprime a > b ≥ 1 and n ≥ 2, **aⁿ − bⁿ always has a "primitive" prime divisor not dividing aᵏ − bᵏ for any k < n**, with only two exceptions: n = 2 with a + b a power of 2, and (a,b,n) = (2,1,6). Use when proving Diophantine equations of the form aⁿ − 1 = (something with limited prime factors) have only finitely many solutions. Connection to orders: the primitive divisor p satisfies n | (p−1), so p ≡ 1 mod n. Sources: AoPS wiki, Wikipedia, IMO Shortlist applications.

### Additional number theory techniques

**p-adic valuations** (ν_p) form the language underlying LTE, Hensel, and much of olympiad NT. Key properties: ν_p(ab) = ν_p(a) + ν_p(b), and ν_p(a+b) ≥ min(ν_p(a), ν_p(b)) with equality when the valuations differ. **Legendre's formula** gives ν_p(n!) = (n − s_p(n))/(p−1). **Infinite descent** proves non-existence by showing any solution implies a smaller one — use when modular arithmetic alone fails and you can parametrize solutions (e.g., via Pythagorean triples) to get structural descent. Fermat used it to prove x⁴ + y⁴ = z² has no positive integer solutions. **Quadratic reciprocity** and the Legendre symbol characterize when x² ≡ a mod p is solvable — use when you need to constrain prime divisors of polynomial expressions to specific residue classes. **Chinese Remainder Theorem** decomposes problems mod composite n into independent problems mod each prime power — use whenever moduli are coprime. Sources: Keith Conrad's QR intro and Pythagorean Triples blurbs, Brilliant.org wikis, AoPS wiki.

---

## ALGEBRA: polynomials and symmetric functions

### Vieta's formulas connect coefficients to roots without solving

For polynomial aₙxⁿ + ... + a₀ with roots r₁,...,rₙ, the k-th elementary symmetric polynomial of the roots equals (−1)ᵏ aₙ₋ₖ/aₙ. **Use when a problem gives polynomial coefficients and asks about symmetric expressions of roots**, or when a system of equations has variables appearing symmetrically that can be identified as roots of an auxiliary polynomial. The system a+b+c = S, ab+bc+ca = P, abc = Q means a,b,c are roots of t³ − St² + Pt − Q = 0. Sources: AoPS wiki, Brilliant.org, David Altizio's handout.

### Newton's sums compute high power sums recursively

**Newton-Girard identities give Pₖ = r₁ᵏ + ... + rₙᵏ from polynomial coefficients without finding roots.** For a monic quadratic x² − Ax + B, the recurrence is Pᵢ = A·Pᵢ₋₁ − B·Pᵢ₋₂. The signature recognition trigger: **"find r₁ᵏ + r₂ᵏ for large k"** — this screams Newton's sums. Example: for x² − 2x + 6 with roots a,b, computing a¹⁰ + b¹⁰ iteratively gives 7552 without ever finding a or b. The identities also provide the key link: any symmetric polynomial is expressible via elementary symmetric polynomials (the Fundamental Theorem of Symmetric Polynomials). Sources: AoPS wiki, Brilliant.org (worked AMC/AIME examples).

### Key algebraic factoring tricks

**Sophie Germain Identity**: a⁴ + 4b⁴ = (a² + 2b² + 2ab)(a² + 2b² − 2ab). Trigger: sum of a fourth power and 4× a fourth power. **Simon's Favorite Factoring Trick**: xy + ax + by + ab = (x+b)(y+a). Trigger: Diophantine equation with cross term xy and linear terms — add a constant to both sides to factor. **Difference/sum of powers**: xⁿ − yⁿ = (x−y)(xⁿ⁻¹ + xⁿ⁻²y + ... + yⁿ⁻¹). Trigger: factoring power expressions for divisibility. Sources: AoPS wiki.

---

## FUNCTIONAL EQUATIONS: the substitution-driven art

### The standard workflow and key substitutions

Evan Chen's approach to functional equations (from his FuncEq-Intro handout): **first guess the answer** (try f(x) = 0, x, −x, kx, kx+c, x²), then verify, then prove uniqueness. The proof proceeds through systematic substitutions:

**Step 1 — x = y = 0**: almost always gives f(0). **Step 2 — one variable = 0**: simplifies the equation using the known f(0). **Step 3 — forced cancellation**: if you see two compound arguments, set them equal to kill a term. Chen's memorable phrasing: "DURR WE WANT STUFF TO CANCEL." **Step 4 — symmetry substitution**: swap x↔y to generate a new equation, then combine with the original. **Step 5 — the fff trick**: replace x with f(t) when f is known bijective, potentially "unwrapping" nested applications. **Step 6 — prove injectivity/surjectivity**: if you derive f(expression₁) = f(expression₂) and need the expressions equal, you need injectivity first. For surjectivity, fix one variable and vary the other to show f covers its codomain.

### Cauchy's equation and its four variants

**f(x+y) = f(x) + f(y) has the unique continuous solution f(x) = cx**, but pathological discontinuous solutions exist (via Hamel basis). The four Cauchy variants and their solutions under regularity conditions:

| Equation | Continuous solution |
|---|---|
| f(x+y) = f(x) + f(y) | f(x) = cx (additive) |
| f(x+y) = f(x)·f(y) | f(x) = aˣ (exponential) |
| f(xy) = f(x) + f(y) | f(x) = c·log(x) (logarithmic) |
| f(xy) = f(x)·f(y) | f(x) = xᶜ (multiplicative) |

**The key recognition trigger: if you can REDUCE your functional equation to any Cauchy form, do so and invoke the theorem.** For domain ℚ, solutions are unique via induction (f(1)→f(n)→f(1/n)→f(p/q)). For domain ℝ, you need an additional regularity condition — continuity, monotonicity, or boundedness on any interval — to eliminate pathological solutions. The additive + multiplicative system (both f(x+y) = f(x)+f(y) AND f(xy) = f(x)f(y)) forces f(x) = x or f(x) = 0, because f(t²) = f(t)² ≥ 0 gives boundedness below. Sources: Evan Chen FuncEq-Intro PDF, imomath.com (Marko Radovanović's 12-method taxonomy), the book "Functional Equations and How To Solve Them."

### IMOmath's 12-method functional equation taxonomy

Radovanović's comprehensive classification: (1) substituting values for variables, (2) mathematical induction over ℤ→ℚ, (3) investigating injectivity/surjectivity, (4) finding fixed points, (5) Cauchy equation reduction, (6) assuming polynomial form and solving for degree, (7) bounding/contradiction, (8) recurrence relations, (9) analyzing the set where f equals claimed solution, (10) function substitution (g(x) = f(x)−c), (11) odd/even decomposition, (12) Cauchy variants. Sources: imomath.com functional equations pages (solved problems + theory).

---

## INEQUALITIES: a 14-technique hierarchy with a decision flowchart

### The AM-GM to Cauchy-Schwarz pipeline

**AM-GM** (arithmetic mean ≥ geometric mean) is the starting point: for non-negative reals, (a₁+...+aₙ)/n ≥ ⁿ√(a₁...aₙ). The weighted version with ω₁a₁+...+ωₙaₙ ≥ a₁^ω₁...aₙ^ωₙ handles asymmetric situations. Evan Chen's key insight: **"The more 'mixed' polynomials are smaller"** — if one symmetric monomial dominates another in majorization order, AM-GM suffices. Use AM-GM for "weak" inequalities where equality holds only at a = b = c.

**Cauchy-Schwarz** in Titu/Engel form — Σ(xᵢ²/yᵢ) ≥ (Σxᵢ)²/(Σyᵢ) — has the sharpest recognition trigger in all of inequality theory: **if you see fractions with squared numerators, apply Titu's lemma immediately**. Standard Cauchy (Σaᵢ²)(Σbᵢ²) ≥ (Σaᵢbᵢ)² works better when two natural "paired" sequences exist. **Hölder's inequality** generalizes Cauchy to eliminate nth roots: use when cube roots or higher-order radicals appear in the inequality. Chen: "Cauchy and Hölder have at least two uses: eliminating radicals and eliminating fractions."

### Schur's inequality fills the abc gap

**Schur's inequality**: aʳ(a−b)(a−c) + bʳ(b−c)(b−a) + cʳ(c−a)(c−b) ≥ 0. For r = 1 this gives a³+b³+c³+3abc ≥ a²(b+c)+b²(c+a)+c²(a+b). The critical recognition trigger: **equality at a = b = c AND at (a,b,0)**. When AM-GM/Muirhead cannot produce the abc term needed to close an inequality, Schur fills the gap. Mildorf's "dumbassing" approach: expand, apply AM-GM to most terms, then use Schur for the leftover.

### Jensen, tangent line trick, and the convexity ladder

**Jensen's inequality** applies when you have Σf(xᵢ) with a fixed-sum constraint and f is convex (f'' ≥ 0): the sum is minimized when all variables equal. Common convex functions: x², eˣ, −ln(x), 1/x for x > 0. Concave: √x, ln(x), sin(x) on (0,π). When f is NOT globally convex — having an inflection point — **Jensen fails, and the tangent line trick takes over**: find the tangent to f at the equality point, verify f(x) ≥ tangent line everywhere in the domain, then sum. The **n−1 EV (Equal Value) principle** handles the even harder case: if f has exactly one inflection point, extrema of Σf(xᵢ) occur when n−1 variables are equal, reducing to a single-variable problem.

### SOS, Muirhead, and the pqr/uvw substitution

**SOS (Sum of Squares)**: write any 3-variable polynomial inequality as Sₐ(b−c)² + S_b(c−a)² + S_c(a−b)² ≥ 0. **Use when AM-GM and Schur are insufficient** — SOS provides finer control. Chen: "The whole point of SOS is so you can use AM-GM backwards." After the SOS factoring, Pham Kim Hung's criteria determine non-negativity without further work.

**Muirhead's inequality** states that (x₁,...,xₙ) majorizing (y₁,...,yₙ) implies Σ_sym a₁^x₁...aₙ^xₙ ≥ Σ_sym a₁^y₁...aₙ^yₙ. Critical warning from Chen: **Muirhead applies to SYMMETRIC sums only, not cyclic sums.** Best used as a checking tool to verify that an AM-GM proof exists, then write the AM-GM explicitly. Mildorf: "Muirhead is not favorably regarded in olympiad solutions."

**The pqr/uvw substitution** (p = a+b+c, q = ab+bc+ca, r = abc) converts any symmetric polynomial inequality in 3 variables into an expression that is **linear in r for fixed p,q**. By Schur's constraint, extrema occur when two variables are equal or one is zero — reducing to a single-variable problem.

### The master inequality decision flowchart

This hierarchy, synthesized from Mildorf and Chen, should be applied in order:

1. Is it homogeneous? If not, homogenize first (multiply by appropriate powers of symmetric expressions)
2. Equality only at a = b = c? → AM-GM, Cauchy-Schwarz, or Jensen likely suffice
3. Equality at a = b = c AND at (t,t,0)? → **Schur is needed**
4. Fractions with squared numerators? → **Cauchy-Schwarz (Titu form)**
5. Radicals present? → **Hölder** or Power Mean to eliminate them
6. Sum of f(xᵢ) with convex f? → **Jensen**
7. f has an inflection point? → **Tangent line trick** or n−1 EV
8. Very sharp, standard methods fail? → **SOS method**
9. Symmetric in 3 variables? → **pqr/uvw substitution**

Sources: Evan Chen's "Brief Introduction to Olympiad Inequalities," Thomas Mildorf's "Olympiad Inequalities," David Arthur's SOS lecture (Canada 2009), Yufei Zhao's Winter Camp 2008, Brilliant.org, imomath.com.

---

## COMBINATORICS: 12 techniques from invariants to the probabilistic method

### Invariants and monovariants detect impossibility and termination

An invariant is a quantity unchanged by allowed operations; a monovariant changes monotonically. Recognition triggers: **"Can you reach configuration B from A?"** → find an invariant that differs between A and B. **"Prove this process terminates"** → find a bounded monovariant. **"Numbers on a board being erased and replaced"** → check parity, sum, sum of squares, or product as potential invariants. Good invariant candidates include parity (mod 2), residues (mod k), sums of squares (for replacement operations), colorings (for grid problems), and products (for multiplication operations). Classic example: a dragon with 100 heads, knight can cut 15/17/20/5 heads (growing back 24/2/14/17); all changes ≡ 0 mod 3, but 100 ≡ 1 mod 3 ≠ 0, so the dragon can never die. Sources: Brilliant.org wiki, Yufei Zhao's Winter Camp 2008, Evan Chen's OTIS "Process" unit.

### Double counting, bijections, and pigeonhole

**Double counting** proves A = B by counting one set two ways. Use whenever you need to prove an identity or relate two combinatorial quantities. The handshaking lemma (Σdeg(v) = 2|E|) is the simplest instance. **Bijections** establish |A| = |B| by constructing a one-to-one correspondence — use when counting a complicated set by mapping it to a known one (e.g., lattice paths ↔ binary strings). **Pigeonhole**: n+1 objects into n boxes forces a collision. Trigger: "prove there exist two elements with the same property" among sufficiently many objects. The **Erdős-Szekeres theorem** (any sequence of n²+1 distinct numbers has an increasing or decreasing subsequence of length n+1) is a powerful pigeonhole application. Sources: AoPS wiki, Yufei Zhao's bijections and counting handouts.

### Generating functions encode sequences algebraically

**Ordinary generating functions (OGF)** encode {aₙ} as A(x) = Σaₙxⁿ; **exponential generating functions (EGF)** encode as Â(x) = Σaₙxⁿ/n!. The decision rule: **use OGF for unlabeled/unordered structures** (partitions, multisets, compositions) and **EGF for labeled/ordered structures** (permutations, derangements, labeled set partitions). OGF multiplication merges unlabeled classes; EGF multiplication interleaves labeled classes.

Triggers: "solve a linear recurrence" → OGF. "Count ways to distribute identical objects" → OGF product. "Count partitions" → Π1/(1−xᵏ). "Convolution sum cₙ = Σaₖbₙ₋ₖ" → coefficient of xⁿ in A(x)·B(x). "Catalan recurrence cₙ = Σcₖcₙ₋₁₋ₖ" → C(x) satisfying xC(x)² − C(x) + 1 = 0. Key closed forms: Fibonacci F(x) = x/(1−x−x²), Catalan C(x) = (1−√(1−4x))/(2x), derangements D̂(x) = e⁻ˣ/(1−x). Sources: imomath.com (OGF and advanced GF pages), Yufei Zhao's AwesomeMath 2007, Codeforces blog.

### Game theory through Sprague-Grundy

Every position in an impartial game has a **Grundy value** g(v) = mex({g(w) : w a follower of v}), where mex is the minimum excludant. **For combined independent sub-games, the overall Grundy value is the XOR of individual values.** Bouton's theorem for Nim: position (x₁,...,xₙ) is losing iff x₁ ⊕ ... ⊕ xₙ = 0. Trigger: **"two-player game, alternating turns, last move wins"** → compute Grundy values. **"Multiple independent piles or sub-games"** → XOR the Grundy values. Sources: CP-Algorithms, Brilliant.org wiki.

### Burnside, extremal principle, probabilistic method, and Catalan numbers

**Burnside's lemma** counts distinct objects under symmetry: |orbits| = (1/|G|)Σ|Fix(g)|. Trigger: **"count configurations up to rotation/reflection."** For necklaces with n beads and k colors: (1/n)Σ_{d|n} φ(n/d)·kᵈ. **The extremal principle** — consider the element maximizing or minimizing some quantity — is universally applicable for existence proofs. **The probabilistic method** proves existence by showing a random construction has the desired property with positive probability; use for lower bounds on Ramsey numbers, independence numbers, and other combinatorial quantities where explicit construction is hard. Erdős's 1947 proof that R(k,k) > 2^(k/2) is the paradigmatic example.

**Catalan numbers** Cₙ = (1/(n+1))C(2n,n) appear whenever you see balanced parentheses, Dyck paths, full binary trees, polygon triangulations, non-crossing partitions, or stack-sortable permutations. First values: 1, 1, 2, 5, 14, 42, 132. **If a counting problem gives these values, it's almost certainly Catalan** — verify using the recurrence Cₙ₊₁ = Σ CₖCₙ₋ₖ. Sources: CP-Algorithms, AoPS wiki, Brilliant.org.

---

## META-STRATEGIES: the seven cross-cutting approaches

Every major olympiad textbook identifies the same set of universal meta-strategies that cut across all four competition subjects. Engel organizes his 14-chapter book around them; Zeitz structures problem-solving as Strategy→Tactics→Tools; Chen's OTIS program weaves them throughout.

**The Invariance Principle** (Engel Ch1, OTIS "Process"): "If there is repetition, look for what does not change." **The Extremal Principle** (Engel Ch3, OTIS "Local"): "Pick an object that maximizes or minimizes some function." **Pigeonhole** (Engel Ch4, OTIS "Global"): more objects than containers forces collisions. **Induction** (Engel Ch8): natural number parameters with n→n+1 stepping. **Coloring/Parity** (Engel Ch2): tiling, covering, impossibility. **Symmetry** (Zeitz): impose or exploit it. **Contradiction** (universal): assume the negation, derive impossibility.

Chen's OTIS program adds two key **combinatorial dichotomies**: **Rigid vs. Free** (few degrees of freedom → discover structure; many degrees → invent/construct) and **Global vs. Local** (aggregate counting/expectation/pigeonhole vs. greedy algorithms/perturbation). These provide strategic orientation before technique selection.

Zeitz's most distinctive contribution is the **"crux move" concept** from mountaineering: the single key obstacle whose resolution clears the path. His emphasis on **wishful thinking** ("what if the problem was already solved? work backwards") and **psychological factors** (confidence, concentration, courage) addresses the metacognitive layer above technique selection.

---

## Existing structured datasets and their technique-recognition gaps

**The critical finding: no large-scale dataset systematically maps competition math problems to solving techniques.** The landscape:

| Dataset | Size | Topic labels | Technique labels |
|---|---|---|---|
| NuminaMath-1.5 | 900k | Domain-level (problem_type) | None |
| NuminaMath-CoT | 860k | Source only | None |
| MATH (Hendrycks) | 12.5k | 7 subjects × 5 difficulty levels | None |
| **CHAMP** | **270** | **5 categories** | **54 concepts + 330 hints** |
| AutoMathKG | KG | 3 entity types | Partial (tactic edges) |
| Math-KG | KG | 2 entity types | None (concept relations only) |

**CHAMP is the only dataset with explicit technique annotations**, providing 54 unique "concepts" (general theorems like AM-GM, Vieta's) and 330 unique "hints" (problem-specific strategies) for its 270 problems. Its key finding: providing technique hints improves LLM performance more than providing concept names. **AutoMathKG** from 2025 provides the most promising architecture — a Problem→Theorem→Definition knowledge graph with LLM-identified tactic labels on edges, auto-updated from ProofWiki and arXiv.

The most efficient path to building a comprehensive technique-recognition dataset: use CHAMP's taxonomy as the seed (expanding from 54 to ~85 concepts using this database), annotate the MATH dataset's 12.5k problems as the initial target, then scale via LLM extraction from NuminaMath-1.5's 900k CoT solutions, organized in AutoMathKG's graph structure.

---

## The complete recognition lookup table

This master table distills the entire database into a single decision resource, organized by the pattern you observe in a problem:

| If you see in the problem... | Try this technique | Domain |
|---|---|---|
| Two chords intersecting or tangent + secant from same point | Power of a Point | Geometry |
| Three circles, need to prove lines concurrent | Radical Axis Theorem | Geometry |
| Triangle with many cevians/special points, synthetic fails | Barycentric Coordinates | Geometry |
| Many circles through one point | Inversion at that point | Geometry |
| Tangent circles (internal or external) | Inversion at tangent point | Geometry |
| Incircle + circumcircle interaction | √bc Inversion or Incenter/Excircle Lemma | Geometry |
| Small circle tangent to chord of big circle | Shooting/Death Star Lemma | Geometry |
| Concurrent cevians + sideline intersection | Harmonic bundle (cross ratio = −1) | Geometry |
| Six points on a conic | Pascal's Theorem | Geometry |
| Only incidence relations (no metric data) | Projective Transformation | Geometry |
| Angle bisector + perpendicularity together | Harmonic bundle | Geometry |
| Tangent from external point to circle | Poles and Polars | Geometry |
| xⁿ − yⁿ or xⁿ + yⁿ, need highest prime power | Lifting the Exponent (LTE) | Number Theory |
| f(x) ≡ 0 mod pᵏ for large k | Hensel's Lemma (lift from mod p) | Number Theory |
| Symmetric quadratic in two variables, prove perfect square | Vieta Jumping | Number Theory |
| aᴺ ≡ 1 mod p, need to constrain N | Orders and Primitive Roots | Number Theory |
| aⁿ − bⁿ must have a new prime factor | Zsigmondy's Theorem | Number Theory |
| Prove Diophantine equation has no solutions | Infinite Descent | Number Theory |
| Need to constrain prime divisors of n²+k to residue class | Quadratic Reciprocity | Number Theory |
| Composite modulus, pairwise coprime | Chinese Remainder Theorem | Number Theory |
| Track exact prime power in any expression | p-adic Valuations | Number Theory |
| Sum/product of roots without finding them | Vieta's Formulas | Algebra |
| r₁ᵏ + r₂ᵏ for large k | Newton's Sums (recursive) | Algebra |
| Symmetric expression given elementary symmetric values | Fundamental Theorem of Symmetric Polynomials | Algebra |
| Diophantine with cross term xy + ax + by | Simon's Favorite Factoring Trick | Algebra |
| a⁴ + 4b⁴ | Sophie Germain Identity | Algebra |
| "Find all functions f:ℝ→ℝ such that..." | Functional Equation substitution chain | Func. Eq. |
| f(x+y) = f(x) + f(y) or any Cauchy variant | Cauchy's Equation (identify variant) | Func. Eq. |
| f(f(x)) = x derived from FE | Involution → f is bijective | Func. Eq. |
| FE domain is ℚ | Induction: ℤ⁺ → ℤ → ℚ | Func. Eq. |
| FE domain ℝ, need f linear | Prove regularity + Cauchy | Func. Eq. |
| Sum of positive terms ≥ product | AM-GM | Inequalities |
| Fractions with squared numerators: Σ(xᵢ²/yᵢ) | Cauchy-Schwarz (Titu/Engel form) | Inequalities |
| Equality at a=b=c AND at (t,t,0) | Schur's Inequality | Inequalities |
| Σf(xᵢ) with convex f and fixed-sum constraint | Jensen's Inequality | Inequalities |
| Radicals (cube roots, nth roots) in inequality | Hölder's Inequality | Inequalities |
| f not globally convex (has inflection point) | Tangent Line Trick or n−1 EV | Inequalities |
| AM-GM and Schur insufficient, very sharp | SOS (Sum of Squares) method | Inequalities |
| Symmetric 3-variable inequality with constraint | pqr/uvw substitution | Inequalities |
| Process with repeated operations; "can you reach X?" | Invariants | Combinatorics |
| "Prove this process terminates" | Monovariants | Combinatorics |
| "Prove quantity A = quantity B" (combinatorial) | Double Counting | Combinatorics |
| "Prove two with same property must exist" | Pigeonhole Principle | Combinatorics |
| People/connections/mutual relationships | Graph Theory (model as graph) | Combinatorics |
| Solve linear recurrence or count structured sequences | Generating Functions | Combinatorics |
| Two-player impartial game, last move wins | Sprague-Grundy (compute Grundy values, XOR) | Combinatorics |
| Count configurations up to rotation/reflection | Burnside's Lemma / Pólya Enumeration | Combinatorics |
| Prove existence (non-constructive) | Probabilistic Method | Combinatorics |
| Grid tiling impossible? | Coloring Argument | Combinatorics |
| Count matches 1,1,2,5,14,42... | Catalan Numbers | Combinatorics |
| "For all n..." with natural number parameter | Mathematical Induction | Meta-strategy |

## Conclusion

This database captures a critical insight confirmed across every source: **technique recognition is the bottleneck in olympiad problem-solving, not technique execution**. Chen's OTIS program, Engel's strategies framework, and Zeitz's hierarchy all converge on the same point — the hard part is seeing which tool fits. The 85 techniques documented here, mapped to their recognition triggers, represent the most comprehensive such compilation available. Three actionable findings emerge that are not obvious from any single source. First, the techniques form a natural hierarchy — meta-strategies (invariance, extremal, pigeonhole) are universal, while subject techniques are domain-specific instantiations of these same principles (infinite descent IS the invariance principle applied to number theory; SOS IS the extremal principle applied to inequalities). Second, the "if you see X, try Y" mappings are far more reliable in some domains than others — inequality technique selection is nearly algorithmic (follow the flowchart), while geometry technique selection remains deeply dependent on pattern experience (as imomath admits: "the answer comes with experience and cannot be put on paper"). Third, the CHAMP dataset's finding that technique hints help LLMs more than concept names suggests that a retrieval-augmented system pairing problems with this recognition database could substantially improve automated mathematical reasoning.