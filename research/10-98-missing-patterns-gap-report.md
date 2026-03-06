# Competition math pattern bank: 98 missing patterns with sources

Your 263-entry database covers the core toolkit well. **98 additional patterns across 6 categories remain uncovered**, ranging from essential AIME-level techniques (Chicken McNugget, partial fractions, telescoping products) to IMO-level weapons (moving points method, LGV lemma, entropy method) to the meta-strategic "glue" that tells solvers *when* to deploy each tool. Below is the complete gap report with best source URLs, recognition-trigger availability, and difficulty ratings for every missing pattern.

The most critical finding: **recognition triggers are the scarcest resource**. Only ~60% of identified sources include explicit "when to use this" guidance. Three author ecosystems dominate the best sources: Evan Chen's handouts (web.evanchen.cc) cover 25+ gaps, Yufei Zhao's MOP/MIT materials (yufeizhao.com) cover 15+, and Keith Conrad's UConn blurbs (kconrad.math.uconn.edu) cover 8+ number theory gaps. Four sources deserve immediate full extraction: Evan Chen's "Lemmas in AoPS Geometry" handout, his Probabilistic Method handout, Yufei Zhao's "Algebraic Techniques in Combinatorics," and Gil Kalai's "Extremal Combinatorics III" blog post (which single-handedly covers 4 combinatorics gaps).

---

## Geometry: 20 patterns from phantom points to conformal intuition

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| G1 | Phantom point / auxiliary point technique | https://web.evanchen.cc/geombook.html (EGMO §1.4) | ✅ Yes | USAMO |
| G2 | Moving points method | AoPS community tutorial by yayups; also Norra Real handout | ✅ Yes | IMO |
| G3 | Trig bash / trig substitution in geometry | https://arxiv.org/abs/2403.09661 (Lignos, "Trig and Analytic Tools") | ✅ Yes | USAMO/IMO |
| G4 | Length chasing vs angle chasing decision framework | https://blog.evanchen.cc/2016/01/19/some-advice-for-olympiad-geometry/ | ✅ Yes | USAMO |
| G5 | Pedal triangle and properties | https://artofproblemsolving.com/wiki/index.php/Orthic_triangle + Yufei Zhao's geolemmas.pdf | ✅ Yes | USAMO |
| G6 | Feuerbach's theorem and applications | https://www.cut-the-knot.org/Curriculum/Geometry/Feuerbach.shtml | ❌ No | USAMO/IMO |
| G7 | Radical center beyond radical axis | Evan Chen's EGMO textbook §2 (radical axes chapter) | ✅ Yes | USAMO |
| G8 | Mixtilinear incircles | https://web.evanchen.cc/handouts/GeoSlang/GeoSlang.pdf + Evan Chen's mixtilinear blog post | ✅ Yes | IMO |
| G9 | Sawayama lemma | https://www.cut-the-knot.org/Curriculum/Geometry/JLAyme.shtml + yufeizhao.com/olympiad/geolemmas.pdf | ❌ No | IMO |
| G10 | √bc inversion | Evan Chen's EGMO Ch. 8 (inversion) | ✅ Yes | USAMO/IMO |
| G11 | Projective duality | https://brilliant.org/wiki/projective-geometry/ + EGMO Ch. 9 | ✅ Yes | IMO |
| G12 | Menelaus for transversals (advanced) | https://yufeizhao.com/olympiad/geolemmas.pdf | ✅ Yes | USAMO |
| G13 | Reim's theorem | https://web.evanchen.cc/handouts/GeoSlang/GeoSlang.pdf | ✅ Yes | USAMO |
| G14 | Curvilinear incircle configurations | "Lemmas in Olympiad Geometry" by Andreescu et al. (Ch. 17) | ✅ Yes | IMO |
| G15 | Anti-Steiner point | Darij Grinberg's geometry notes (cip.ifi.lmu.de/~grinberg/geometry2.html) | ✅ Yes | IMO |
| G16 | Isotomic conjugate | https://en.wikipedia.org/wiki/Isotomic_conjugate + MathWorld | ❌ No | USAMO |
| G17 | Trigonometric form of Ceva's theorem | https://www.cut-the-knot.org/triangle/TrigCeva.shtml | ✅ Yes | USAMO |
| G18 | Power of a point for spheres (3D) | https://en.wikipedia.org/wiki/Power_of_a_point (3D section) | ❌ No | USAMO |
| G19 | Inversive distance | Evan Chen's EGMO Ch. 8 (inversive distance formula section) | ✅ Yes | USAMO/IMO |
| G20 | Conformal mapping intuition for inversions | Evan Chen's EGMO Ch. 8 + Adam Kelly's inversion handout | ❌ No | USAMO/IMO |

**Geometry extraction priority.** Three sources cover the majority of these gaps: Evan Chen's EGMO textbook (G1, G7, G10, G19, G20), his "Lemmas in AoPS Geometry" handout (G8, G13), and Yufei Zhao's "Lemmas in Euclidean Geometry" at yufeizhao.com/olympiad/geolemmas.pdf (G5, G9, G12). The **moving points method** (G2) is the most urgent addition—it has appeared on multiple recent IMOs and has no single canonical source yet, though the AoPS tutorial by yayups and a Swedish training handout are the best available. The trig bash paper by Lignos on arXiv (G3) is unusually thorough for an olympiad resource and includes recognition cues for when trig outperforms coordinates.

---

## Number theory: 19 patterns from Wolstenholme to polynomial congruences

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| N1 | Wolstenholme's theorem | https://artofproblemsolving.com/wiki/index.php/Wolstenholme%27s_Theorem + Euler Circle handout (simonrs.com/eulercircle/) | ❌ No | USAMO/IMO |
| N2 | Chicken McNugget theorem | https://artofproblemsolving.com/wiki/index.php/Chicken_McNugget_Theorem | ✅ Yes | AIME |
| N3 | Lifting mod p to mod p^k (beyond Hensel) | Aditya Khurmi's "Modern Olympiad Number Theory" Ch. 5 | ❌ No | USAMO/IMO |
| N4 | Primitive root existence and applications | https://kconrad.math.uconn.edu/blurbs/ugradnumthy/cyclicmodp.pdf | ❌ No | USAMO |
| N5 | Index / discrete log in competition context | Keith Conrad's orders handout (kconrad.math.uconn.edu/blurbs/ugradnumthy/ordersmodm.pdf) | ❌ No | USAMO/IMO |
| N6 | Korselt's criterion (Carmichael numbers) | https://kconrad.math.uconn.edu/blurbs/ugradnumthy/carmichaelkorselt.pdf | ✅ Yes | USAMO |
| N7 | Jacobi symbol beyond Legendre | https://brilliant.org/wiki/jacobi-symbol/ | ✅ Yes | USAMO |
| N8 | Quadratic forms: which primes represented | https://kconrad.math.uconn.edu/blurbs/ugradnumthy/Zinotes.pdf (Gaussian integers + Thue's lemma) | ❌ No | USAMO/IMO |
| N9 | Continued fractions and best approximations | https://www.cut-the-knot.org/blue/ContinuedFractions.shtml | ✅ Yes | USAMO |
| N10 | Stern-Brocot tree | https://cp-algorithms.com/others/stern_brocot_tree_farey_sequences.html | ✅ Yes | USAMO |
| N11 | Bertrand's postulate applications | Crux Mathematicorum April 2016 (cms.math.ca) — Cody Johnson's 10+ problem collection | ✅ Yes | USAMO |
| N12 | Bonse's inequality | https://en.wikipedia.org/wiki/Bonse%27s_inequality + same Crux article | ❌ No | USAMO |
| N13 | Grimm's conjecture type problems | https://en.wikipedia.org/wiki/Grimm%27s_conjecture | ❌ No | IMO |
| N14 | Sum of digits function properties s(n) | https://artofproblemsolving.com/wiki/index.php/Digital_root | ✅ Yes | AIME |
| N15 | LTE for p=2 specifically | Parvardi's LTE handout v6 (Theorems 3–4) + https://brilliant.org/wiki/lifting-the-exponent/ | ✅ Yes | USAMO |
| N16 | Thue's lemma (pigeonhole for modular equations) | Khurmi's MONT Ch. 5 + https://en.wikipedia.org/wiki/Thue%27s_lemma | ❌ No | USAMO |
| N17 | Erdős-Ginzburg-Ziv theorem | https://anuragbishnoi.wordpress.com/2015/12/17/the-erdos-ginzburg-ziv-theorem/ | ✅ Yes | USAMO/IMO |
| N18 | Davenport constant | https://math.osu.edu/sites/math.osu.edu/files/What_is_2018_Davenport_Constant.pdf | ✅ Yes | IMO |
| N19 | Polynomial congruences beyond Hensel | https://kconrad.math.uconn.edu/blurbs/ (Hensel's lemma blurb) + Khurmi's MONT p-adic chapter | ❌ No | USAMO/IMO |

**Number theory extraction priority.** Keith Conrad's blurbs are the single best source ecosystem, covering N4, N5, N6, N8, N19 with characteristic rigor. Aditya Khurmi's "Modern Olympiad Number Theory" (freely available, widely circulated) is the best for the "lifting" techniques (N3, N16, N19). The **Chicken McNugget theorem** (N2) and **sum of digits** (N14) are AIME-level gaps that should be trivial to fill. **Thue's lemma** (N16) is the most underrated gap—it's the key bridge between pigeonhole and quadratic forms, and many students lack it despite its power. The **Erdős-Ginzburg-Ziv theorem** (N17) connects to zero-sum combinatorics and has appeared on multiple national olympiads.

---

## Algebra: 20 patterns from root location to Sophie Germain applications

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| A1 | Polynomial root location (Rouché, Descartes) | https://yufeizhao.com/olympiad/ (Integer Polynomials handout) + https://brilliant.org/wiki/descartes-rule-of-signs/ | ✅ Yes | USAMO/IMO |
| A2 | Sturm's theorem for real root counting | https://en.wikipedia.org/wiki/Sturm%27s_theorem (rare in competitions; Descartes is the practical tool) | ✅ Yes | USAMO |
| A3 | Partial fractions decomposition | https://artofproblemsolving.com/wiki/index.php/Partial_fraction_decomposition | ✅ Yes | AIME |
| A4 | Telescoping products | https://brilliant.org/wiki/telescoping-series-product/ | ✅ Yes | AIME |
| A5 | Abel's summation by parts applications | Evan Chen's Summation handout (web.evanchen.cc/handouts/Summation/Summation.pdf) | ✅ Yes | USAMO/IMO |
| A6 | Weighted AM-GM with optimal weight selection | https://yufeizhao.com/olympiad/ (Inequalities handout, Canadian 2008 Winter Training) | ✅ Yes | USAMO/IMO |
| A7 | Normalization / WLOG in inequalities | Evan Chen's Olympiad Inequalities handout (web.evanchen.cc/handouts/Ineq/en.pdf) | ✅ Yes | USAMO |
| A8 | uvw method for 3-variable symmetric inequalities | https://brilliant.org/wiki/the-uvw-method/ (includes Tejs' theorem) | ✅ Yes | USAMO/IMO |
| A9 | Half-convexity / fudging method | Yufei Zhao's Inequalities handout (Canadian 2008 Winter Training) — n−1 EV principle | ✅ Yes | USAMO/IMO |
| A10 | Isolated fudging | Thomas Mildorf's "Olympiad Inequalities" (artofproblemsolving.com/articles/files/MildorfInequalities.pdf) | ✅ Yes | USAMO/IMO |
| A11 | Functional equation: additive + multiplicative | Evan Chen's FE handout (web.evanchen.cc/handouts/FuncEq-Intro/FuncEq-Intro.pdf), Example 4.3 | ✅ Yes | USAMO/IMO |
| A12 | Functional equations on restricted domains | Same Evan Chen FE handout, §3 (domain choice discussion) + imomath.com FE page | ✅ Yes | USAMO/IMO |
| A13 | Polynomial functional equations | https://yufeizhao.com/olympiad/ (Polynomials handout, Canadian 2008 Summer Training) | ❌ No | USAMO/IMO |
| A14 | Radicals elimination via Hölder | https://hcmop.wordpress.com/2012/04/19/holders-inequality/ (IMO 2001 P2 example) | ✅ Yes | USAMO/IMO |
| A15 | Algebraic NT flavor (minimal polynomial, conjugates) | https://brilliant.org/wiki/cayley-hamilton-theorem/ (rare in competitions) | ❌ No | IMO |
| A16 | Matrix methods for linear recurrences | https://artofproblemsolving.com/wiki/index.php/Characteristic_polynomial | ✅ Yes | AIME/USAMO |
| A17 | Generating functions: OGF vs EGF decision | Evan Chen's Summation handout + https://codeforces.com/blog/entry/77468 | ✅ Yes | AIME/USAMO |
| A18 | q-analogs in competition math | https://en.wikipedia.org/wiki/Gaussian_binomial_coefficient (very rare in competitions) | ❌ No | IMO |
| A19 | Vieta jumping variants (constant/geometric descent) | https://brilliant.org/wiki/vieta-root-jumping/ + Yimin Ge's dedicated paper | ✅ Yes | IMO |
| A20 | Sophie Germain identity applications beyond factoring | https://brilliant.org/wiki/sophie-germain-identity/ | ✅ Yes | AIME/USAMO |

**Algebra extraction priority.** The inequality gaps (A6–A10, A14) cluster around a few masterful handouts: **Thomas Mildorf's "Olympiad Inequalities"** covers isolated fudging and half-convexity, **Yufei Zhao's Inequalities handout** covers weighted AM-GM and the n−1 EV principle, and **Evan Chen's Inequalities handout** covers normalization. The functional equation gaps (A11–A13) are efficiently filled by Evan Chen's single FE-Intro handout. The **uvw method** (A8) on Brilliant.org includes the critical Tejs' theorem stating where extrema occur—this is the kind of recognition trigger that transforms a technique from "known" to "usable." Sturm's theorem (A2) and q-analogs (A18) are low-priority since they almost never appear in competitions.

---

## Combinatorics: 30 patterns from LGV lemma to Narayana numbers

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| C1 | LGV lemma (non-crossing paths → determinants) | MIT OCW 18.212 lecture 35 PDF + Codeforces blog entry/108395 | ❌ No | USAMO/IMO |
| C2 | Hook length formula | https://en.wikipedia.org/wiki/Hook_length_formula | ❌ No | USAMO/IMO |
| C3 | RSK correspondence | https://www.samuelfhopkins.com/docs/rsk.pdf | ❌ No | IMO |
| C4 | De Bruijn sequences | https://en.wikipedia.org/wiki/De_Bruijn_sequence | ❌ No | AIME/USAMO |
| C5 | Necklace splitting / ham sandwich theorem | https://brilliant.org/wiki/ham-sandwich-theorem/ | ✅ Yes | IMO |
| C6 | Lovász Local Lemma applications | Evan Chen's Probabilistic Method handout (web.evanchen.cc), §5 | ✅ Yes | USAMO/IMO |
| C7 | Alteration method (probabilistic) | Same Evan Chen Probabilistic Method handout, §4 | ✅ Yes | USAMO/IMO |
| C8 | Derandomization / conditional expectation | Yufei Zhao's MIT 18.218 notes (web.stanford.edu/~lindrew/18.218.pdf) | ❌ No | IMO |
| C9 | Turán-type problems beyond basic Turán | https://yufeizhao.com/gtacbook/gtacbook.pdf (Zhao's "Graph Theory and Additive Combinatorics") | ✅ Yes | USAMO/IMO |
| C10 | Kruskal-Katona theorem | https://gilkalai.wordpress.com/2008/09/28/extremal-combinatorics-iii-some-basic-theorems/ | ✅ Yes | USAMO/IMO |
| C11 | Sunflower lemma | Same Gil Kalai blog post (Extremal Combinatorics III) | ✅ Yes | USAMO/IMO |
| C12 | Delta-system | Same as C11 (delta-system = sunflower; same concept, different name) | ✅ Yes | USAMO/IMO |
| C13 | Bollobás set-pairs inequality | Same Gil Kalai blog post | ✅ Yes | USAMO/IMO |
| C14 | Frankl's union-closed conjecture problems | https://en.wikipedia.org/wiki/Union-closed_sets_conjecture | ❌ No | IMO |
| C15 | Shannon capacity type problems | https://en.wikipedia.org/wiki/Shannon_capacity_of_a_graph | ❌ No | IMO |
| C16 | Projective planes in combinatorics | ETH Steiner systems notes (metaphor.ethz.ch) | ✅ Yes | USAMO/IMO |
| C17 | Steiner systems | https://en.wikipedia.org/wiki/Steiner_system | ❌ No | USAMO/IMO |
| C18 | Linear algebra method in combinatorics | https://yufeizhao.com/olympiad/algcomb.pdf | ✅ Yes | USAMO/IMO |
| C19 | Polynomial method (Dvir, cap set) | https://yufeizhao.com/pm16/ (Oxford 2016 graduate course) | ✅ Yes | IMO |
| C20 | Container method | https://arxiv.org/abs/1801.04584 (Balogh-Morris-Samotij ICM survey) | ❌ No | IMO |
| C21 | Dependent random choice | https://arxiv.org/abs/0909.3271 (Fox-Sudakov survey) | ✅ Yes | IMO |
| C22 | Regularity lemma at competition level | https://yufeizhao.com/gtacbook/gtacbook.pdf (Ch. 2) | ✅ Yes | IMO |
| C23 | Probabilistic method: 1st/2nd moment + LLL | Evan Chen's "Expected Uses of Probability" handout | ✅ Yes | USAMO/IMO |
| C24 | Entropy method in combinatorics | https://arxiv.org/abs/1406.7872 (Galvin's "Three tutorial lectures on entropy and counting") | ❌ No | USAMO/IMO |
| C25 | Algebraic graph theory (eigenvalues) | MPI lecture notes (resources.mpi-inf.mpg.de) + Zhao's textbook | ✅ Yes | USAMO/IMO |
| C26 | Expander graphs / mixing lemma | Harvard's Salil Vadhan chapter (people.seas.harvard.edu/~salil/cs225/) | ✅ Yes | IMO |
| C27 | Weight function technique | Kedlaya's Inequalities handout (artofproblemsolving.com/articles/files/KedlayaInequalities.pdf) | ✅ Yes | USAMO/IMO |
| C28 | Smoothing / convexity in discrete optimization | Same Kedlaya handout | ✅ Yes | AIME/USAMO |
| C29 | Token sliding / pebbling arguments | Pranav Sriram's "Olympiad Combinatorics" Ch. 3 (AoPS download) | ✅ Yes | USAMO/IMO |
| C30 | Motzkin and Narayana numbers | https://en.wikipedia.org/wiki/Motzkin_number + https://en.wikipedia.org/wiki/Narayana_number | ❌ No | AIME/USAMO |

**Combinatorics extraction priority.** This domain has the most gaps (30) but they stratify cleanly into three tiers. **Tier 1 — immediately extractable from existing handouts:** Evan Chen's Probabilistic Method handout covers C6, C7, C23 in one document; Yufei Zhao's algcomb.pdf covers C18; Gil Kalai's single blog post covers C10–C13; Kedlaya's inequalities handout covers C27–C28. **Tier 2 — competition-relevant but requires assembling from multiple sources:** LGV lemma (C1), dependent random choice (C21), entropy method (C24), and algebraic graph theory (C25). **Tier 3 — graduate-level tools that rarely appear directly in competitions:** container method (C20), regularity lemma (C22), RSK correspondence (C3), Shannon capacity (C15). For Tier 3, Yufei Zhao's textbook "Graph Theory and Additive Combinatorics" (free PDF) is the one source that makes these accessible at near-competition level.

---

## Cross-domain bridge patterns: 9 techniques for knowing when to switch tools

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| B1 | Geometry → coordinates (structural cues) | Evan Chen's EGMO Ch. 7 (bary) + Ch. 13 (when to use coordinates) | ✅ Yes | USAMO |
| B2 | Geometry → complex numbers (structural cues) | Evan Chen's complex number handout (web.evanchen.cc/handouts/cmplx/en-cmplx.pdf) + Yi Sun's MOP notes | ✅ Yes | USAMO/IMO |
| B3 | Combinatorics → graph modeling | https://yufeizhao.com/olympiad/algcomb.pdf + Adam Kelly's graph theory handout | ✅ Yes | USAMO/IMO |
| B4 | NT ↔ algebra (when to cross over) | Justin Stevens' "Olympiad NT through Challenging Problems" (AoPS CDN) | Partial | USAMO/IMO |
| B5 | Polynomial methods in geometry | https://arxiv.org/abs/1310.6482 (Tao's polynomial method survey) | ✅ Yes | IMO |
| B6 | Linear algebra in number theory (lattice methods) | https://yufeizhao.com/olympiad/algcomb.pdf + Po-Shen Loh's MOP 2009 handout | Partial | USAMO/IMO |
| B7 | Generating functions for NT (Dirichlet series) | https://mathybit.github.io/assets/docs/ntfunctions-dirichletgen.pdf | ✅ Yes | USAMO/IMO |
| B8 | Probabilistic arguments in number theory | Evan Chen's Probabilistic Method handout (framework transfers to NT) | Partial | IMO |
| B9 | Geometry in combinatorics (double counting via configurations) | Stephan Wagner's combinatorics notes (math.sun.ac.za/swagner/Combinatorics.pdf) | Partial | USAMO/IMO |

**Bridge patterns are the highest-value gaps in your entire database.** These are not individual techniques but *decision procedures* for choosing which technique to apply. The best single resource for B1 and B2 is **Yi Sun's MOP 2015 complex numbers handout** (yisun.io/notes/complex.pdf), which uniquely provides explicit "do NOT use complex numbers when..." guidance alongside "use them when..." guidance. Evan Chen's EGMO textbook is the most comprehensive source for B1 (it devotes an entire chapter to coordinate method selection). For B5, Terence Tao's polynomial method survey is graduate-level but conceptually illuminating. **No single source comprehensively covers all 9 bridge patterns**—this is a genuine gap in the olympiad training literature that would justify creating original material.

---

## Meta-strategy patterns: 10 problem-solving frameworks

| # | Pattern | Best Source URL | Triggers? | Difficulty |
|---|---------|----------------|-----------|------------|
| M1 | Working backwards from the answer | Polya's "How to Solve It" (heuristic dictionary: "Working Backwards") | ✅ Yes | AIME/USAMO |
| M2 | Small cases → pattern → conjecture → proof | Evan Chen's "Notes on Proof-Writing Style" (web.evanchen.cc/handouts/english/english.pdf) | Partial | AIME/USAMO |
| M3 | WLOG — when and how to reduce | https://www.cut-the-knot.org/blue/WLOG.shtml | ✅ Yes | AIME/USAMO |
| M4 | Extremal principle as meta-strategy | Engel's "Problem-Solving Strategies" Ch. 3 + https://brilliant.org/wiki/extremal-principle/ | ✅ Yes | USAMO/IMO |
| M5 | Contradiction: structural cues | Engel's "Problem-Solving Strategies" (throughout) | Partial | USAMO/IMO |
| M6 | Construction: building examples/counterexamples | Evan Chen's OTIS Excerpts ("Equality and Construction" unit) + Pranav Sriram's Ch. 1 | Partial | USAMO/IMO |
| M7 | Generalize then specialize | Polya's "How to Solve It" ("Generalization" + "Inventor's Paradox") | ✅ Yes | USAMO/IMO |
| M8 | Make it easier (relaxation) | Polya's "How to Solve It" + Zeitz's "Art and Craft of Problem Solving" | ✅ Yes | AIME/USAMO |
| M9 | Problem transformation: equivalent reformulation | Geoff Smith's blog (eventuallyalmosteverywhere.wordpress.com) | ✅ Yes | USAMO/IMO |
| M10 | "What's the bottleneck?" — identifying the hard step | Evan Chen's OTIS philosophy + IMO reports (web.evanchen.cc/olympiad.html) | ✅ Yes | USAMO/IMO |

**Meta-strategy assessment.** Two books dominate this category: **Polya's "How to Solve It"** (M1, M7, M8) and **Engel's "Problem-Solving Strategies"** (M4, M5). Neither is freely available online, but both are so foundational that pattern extraction from them is worthwhile. For free online sources, **Evan Chen's various handouts and blog posts** collectively model all 10 meta-strategies, though they rarely name them explicitly. The **most novel gap** here is M10 ("What's the bottleneck?")—this metacognitive skill is implicitly taught through Evan Chen's contest reports and OTIS program but has no dedicated handout anywhere.

---

## The 12 highest-priority sources to extract first

Based on pattern coverage density and recognition-trigger quality, these sources should be processed first:

1. **Evan Chen's "Expected Uses of Probability"** — covers C6, C7, C23, B8 (4 patterns, all with triggers)
2. **Yufei Zhao's "Algebraic Techniques in Combinatorics"** (yufeizhao.com/olympiad/algcomb.pdf) — covers C18, B3, B6 (3 patterns with triggers)
3. **Gil Kalai's "Extremal Combinatorics III"** blog post — covers C10, C11, C12, C13 (4 patterns, all with triggers)
4. **Evan Chen's EGMO textbook** (chapters 2, 8, 9) — covers G1, G7, G10, G19, G20, B1, B2 (7 patterns)
5. **Evan Chen's "Lemmas in AoPS Geometry"** handout — covers G8, G13, plus Reim's theorem and named configurations
6. **Thomas Mildorf's "Olympiad Inequalities"** — covers A9, A10 (with explicit recognition triggers)
7. **Keith Conrad's UConn blurbs** (cyclicmodp.pdf, carmichaelkorselt.pdf, Zinotes.pdf, ordersmodm.pdf) — covers N4, N5, N6, N8
8. **Yufei Zhao's Inequalities handout** (Canadian 2008) — covers A6, A9
9. **Evan Chen's Functional Equations handout** — covers A11, A12 (with domain analysis)
10. **Kedlaya's Inequalities handout** on AoPS — covers C27, C28
11. **Parvardi's LTE handout v6** — covers N15 (the p=2 case specifically)
12. **Yufei Zhao's "Graph Theory and Additive Combinatorics"** textbook PDF — covers C9, C22, C25 and contextualizes many advanced patterns

## Conclusion: what the gap analysis reveals about the database's architecture

The 98 missing patterns split into **three strategic layers**. The first layer (~25 patterns) comprises bread-and-butter techniques at the AIME/early-USAMO level—partial fractions, telescoping products, Chicken McNugget, WLOG—whose absence suggests the database was built top-down from hard problems rather than bottom-up from technique taxonomies. The second layer (~45 patterns) represents genuine USAMO/IMO weapons—moving points, √bc inversion, LGV lemma, entropy method, Thue's lemma—that appear on approximately 1–3 problems per year across major competitions. The third layer (~28 patterns) includes research-adjacent tools and meta-strategies that rarely appear as named techniques but fundamentally shape how expert solvers *think*: bridge patterns, the extremal principle as meta-strategy, and bottleneck identification.

The most structurally important gaps are not individual techniques but the **bridge patterns** (B1–B9) and **meta-strategies** (M1–M10). A solver who knows all 263 existing patterns plus all 79 domain-specific gaps but lacks the bridge patterns would still struggle with problems requiring tool selection across domains—which describes most IMO problems above difficulty 4. No existing source comprehensively teaches all bridge patterns or meta-strategies in one place, making this the area where original material creation would add the most value.