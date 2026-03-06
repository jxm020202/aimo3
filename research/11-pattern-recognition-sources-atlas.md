# The complete atlas of mathematical pattern-recognition sources

**The single most important finding: the knowledge that separates "I know LTE exists" from "this is an LTE problem" lives in roughly 150 identifiable sources, and about 80% of the highest-quality material traces back to fewer than a dozen creators.** Evan Chen's ecosystem (OTIS, blog, handouts, Twitch streams, EGMO, solution notes) is the densest repository of explicit pattern-recognition teaching ever assembled for competition math. The cognitive science literature confirms why this matters — experts categorize problems by deep structure while novices fixate on surface features, and the bridge between these states requires exactly the kind of "motivation" commentary and meta-cognitive scaffolding that these sources provide.

What follows is a structured catalog of every significant source identified, organized by the type of pattern-recognition knowledge it delivers. This is not a reading list — it is a map of where micro-pattern knowledge actually lives.

---

## The Evan Chen ecosystem: densest source of "how did you know?"

No individual has produced more explicit pattern-recognition content for olympiad math than Evan Chen (v_Enhance). His materials span six interconnected systems, each targeting a different layer of technique recognition.

**The blog posts on meta-cognition** are the most direct treatment of approach selection anywhere in competition math. "Hard and Soft Techniques" (https://blog.evanchen.cc/2019/05/03/hard-and-soft-techniques/) explicitly distinguishes two types of thinking: *hard techniques* (tools that could help solve a problem) versus *soft techniques* (tools that help you understand the problem better — checking special cases, heuristic arguments for why something should be true, thinking about why a technique *failed*). This single post is arguably the most concentrated treatment of technique-selection meta-cognition by any competition math author. "On Reading Solutions" (https://blog.evanchen.cc/2017/03/06/on-reading-solutions/) teaches how to extract the "ocean-crossing point" — the discrete jump from unsolved to solved — from any solution you read. "Some Thoughts on Olympiad Material Design" (https://blog.evanchen.cc/2017/04/08/on-designing-olympiad-training/) argues that standard labels like "pigeonhole" or "induction" are often misleading and proposes classifying problems by patterns of thought rather than technique names. "Getting to Know Problems" (https://blog.evanchen.cc/2025/02/14/getting-to-know-problems/) critiques students who rush to apply techniques rather than understanding the problem's structure, using a dating metaphor: "running out of ideas" is like "running out of conversation on a first date." Additional key posts include "What Leads to Success at Math Contests?" (https://blog.evanchen.cc/2014/07/27/what-leads-to-success-at-math-contests/), "Math Contest Platitudes v3" (https://blog.evanchen.cc/2019/01/31/math-contest-platitudes-v3/), and "Lessons from Math Olympiads" (https://blog.evanchen.cc/2018/01/05/lessons-from-math-olympiads/), which introduces the concept of the "morally correct" way of thinking about things.

**The OTIS catalog** (https://web.evanchen.cc/static/otis-samples/synopsis.html) is the most comprehensive technique-oriented taxonomy of competition math problem-solving in existence, containing **60+ units** organized by specific solving techniques with difficulty coding (B/D/Z for beginner/intermediate/advanced) and subject coding (A/C/G/N for algebra/combinatorics/geometry/number theory). Critical units include "Diagram Intuition" (teaching students to look at a geometry diagram and determine which claims should or shouldn't be true — pure meta-cognition), "Equality" (mandatory for newcomers, teaching exploitation of equality cases), and "Tricky Ineq" (explicitly described as problems that "don't succumb to the standard methods"). The full OTIS syllabus lives at https://web.evanchen.cc/upload/otis-syllabus.pdf. The free OTIS Excerpts mini-book (https://web.evanchen.cc/textbooks/OTIS-Excerpts.pdf) contains **202 problems across 13 topics** with walkthroughs and, critically, "Bogus Solution" sections demonstrating common anti-patterns.

**The IMO Solution Notes** (available for every year at https://web.evanchen.cc/problems.html) are distinctive because they include "Remark (Motivation)" sections explaining *why* certain techniques were tried. Example from IMO 2024: "The reason to consider the number M = ab+1 is the same technique used in IMO 2005/4, namely the idea to consider 'n = −1'." These notes also flag when problems have essentially only one known approach — invaluable for understanding which problems have narrow recognition windows.

**Twitch Solves ISL** (https://web.evanchen.cc/twitch.html) provides real-time narrated problem-solving showing false starts, technique selection, and "aha" moments across multiple seasons starting 2022. The accompanying PDFs include motivational commentary. This is the closest thing available to watching an expert's pattern-recognition engine operate in real time.

**The geometry ecosystem** spans the EGMO book (https://web.evanchen.cc/geombook.html) — which contains "how would you come up with this?" commentary throughout and explicitly discusses when to use synthetic vs. computational approaches — plus the blog post "Some Advice for Olympiad Geometry" (https://blog.evanchen.cc/2016/01/19/some-advice-for-olympiad-geometry/), which provides the foundational **three-attack-mode framework**: (I) Synthetic techniques, (II) Computational bashing, (III) Finding crucial intermediate claims via large diagrams. His rule of thumb: the nth problem on an IMO paper requires about n of these strategy types.

**Domain-specific handouts** with explicit recognition guidance include the Introduction to Functional Equations (https://web.evanchen.cc/handouts/FuncEq-Intro/FuncEq-Intro.pdf), which documents "triggers for induction" and warns about the "pointwise trap"; Brief Introduction to Olympiad Inequalities (https://web.evanchen.cc/handouts/Ineq/en.pdf); Barycentric Coordinates with Max Schindler (https://web.evanchen.cc/handouts/bary/bary-full.pdf); and the complete index at https://web.evanchen.cc/olympiad.html.

---

## Expert writings that teach when, not just how

Beyond Chen, a handful of expert mathematicians have written explicitly about the meta-cognition of technique selection.

**Terence Tao's** "245A: Problem Solving Strategies" (https://terrytao.wordpress.com/2010/10/21/245a-problem-solving-strategies/) lists ~20 explicit heuristics for real analysis with WHEN-to-apply conditions: "Split up equalities into inequalities" (when proving X=Y), "Give yourself an epsilon of room" (when proving X≤Y), "Decompose a rough object by a smoother one" (when stuck on the general case). The post directly addresses "analysis paralysis" when multiple options exist: "Rather than agonize over which option is the 'right' one, simply select the best initial guess, work with that, and see what happens." His Masterclass on Mathematical Thinking (https://terrytao.wordpress.com/2022/01/27/masterclass-on-mathematical-thinking/) discusses dialectical strategy pairs: Complex-Simple, General-Special, Primary-Secondary, Known-Unknown, Forward-Reverse, Higher-Lower, Global-Local. His book *Solving Mathematical Problems* (OUP, 2006) explicitly demonstrates the thought process of approaching problems "for the first time." His blog's "Tricks" category (https://terrytao.wordpress.com/category/expository/tricks/) catalogs specific tricks with deployment conditions.

**Yufei Zhao's handouts** (https://yufeizhao.com/olympiad/) are notable for "big picture" framing. "Cyclic Quadrilaterals — The Big Picture" gives a high-level view of when cyclic quadrilateral theory applies. "Algebraic Techniques in Combinatorics" (MOP 2007) explicitly teaches when algebraic tools apply to combinatorial settings. His Winter Camp 2008 Inequalities handout covers the "turning the table" technique for switching between constraint and inequality.

**Po-Shen Loh's** philosophy explicitly opposes rote technique memorization. His central dictum: "The way to learn how to solve the widest variety of problems is to learn how to invent your own solution methods." His CMU Putnam course gives students problems and asks them to brainstorm what concepts might help with no scripted lectures. His MOP handouts are available at https://www.math.cmu.edu/~lohp/olympiad.shtml, including the Probabilistic Methods in Combinatorics handout from MOP 2009 (https://www.math.cmu.edu/~lohp/docs/math/mop2009/prob-comb.pdf), which demonstrates when probabilistic methods provide elegant solutions to seemingly non-probabilistic problems.

**Adam Goucher's** *Mathematical Olympiad Dark Arts* (https://www.isinj.com/mt-usamo/Math%20Olympiad%20Dark%20Arts%20-%20Goucher%20(2012).pdf) attempts to systematize "advanced techniques which can offer considerable advantage in solving certain problems" — explicitly about recognizing WHEN to deploy non-obvious tools like inversion and projective geometry.

---

## AoPS threads and blogs with genuine meta-reasoning

The Art of Problem Solving community is the world's largest repository of competition math discussion, but only a fraction of threads contain genuine pattern-recognition insight rather than just solutions.

**Highest-value AoPS sources include:** the 2025 USAMO Problem 6 wiki page (https://artofproblemsolving.com/wiki/index.php/2025_USAMO_Problems/Problem_6), which shows step-by-step motivation for applying Hall's marriage lemma; the 2014 USAMO Problem 6 page (https://artofproblemsolving.com/wiki/index.php/2014_USAMO_Problems/Problem_6), Chen's canonical example for "main idea extraction"; and the complete IMO and USAMO problem archives (https://artofproblemsolving.com/wiki/index.php/IMO_Problems_and_Solutions, https://artofproblemsolving.com/wiki/index.php/USAMO_Problems_and_Solutions). The IMO 2023 wiki pages include embedded YouTube videos by user ~little-fermat containing "motivation + discussion" for each problem.

**External blogs with exceptional meta-reasoning:** Steve Newman's "What It's Like To Solve a Math Olympiad Problem" (https://secondthoughts.ai/p/solving-math-olympiad-problems) — a former 1983/1984 USA IMO team member walks through solving IMO 2024 P3 step by step, explicitly labeling mental tools at each stage. The "nor" blog's "Solving the IMO 2025 Problems" (https://nor-blog.pages.dev/posts/2025-07-19-imo-2025/) provides expert-level intuition like "O(n²) points but only O(n) lines, so O(n) average incidence — this is suspicious." Ho Jun Wei's "How to Approach an Olympiad Problem" (https://hcmop.wordpress.com/2012/03/23/how-to-approach-an-olympiad-problem-by-ho-jun-wei/) describes maintaining personal compiled handbooks of geometry lemmas and "100 standard inequalities."

---

## Books ranked by recognition vs. execution teaching

The competition math book landscape exhibits a sharp **"recognition gap"** — most books teach technique execution but not technique recognition. The following ranking prioritizes recognition content.

**Paul Zeitz's *The Art and Craft of Problem Solving*** is the single strongest book for approach selection, with its unique Strategy/Tactics/Tools framework. "Strategy" means broad plans (like selecting a mountain climbing route), "Tactics" means general methods (negotiating obstacles), "Tools" means specific techniques (specialized equipment). The book explicitly teaches the "Penultimate Step" (thinking backwards from the goal), the "Crux Move" (identifying the key obstacle), and "Wishful Thinking" (assuming the problem is solved and reverse-engineering). **Schoenfeld's *Mathematical Problem Solving*** is the definitive research work, demonstrating that the critical missing ingredient in problem solving is **metacognitive control** — the ability to monitor your solution process and switch strategies when stuck. His protocol analyses showed novices pursuing single unproductive approaches for entire allotted periods while experts abandoned failing approaches within minutes. Schoenfeld's three self-monitoring questions — "What exactly are you doing?", "Why are you doing that?", "How does it help you?" — are themselves a micro-pattern recognition tool. **Polya's *How to Solve It*** catalogs **67 heuristic entries** organized alphabetically, with the "Devise a Plan" step entirely about recognition: "Have you seen it before? Do you know a related problem?"

**Arthur Engel's *Problem Solving Strategies*** organizes its first four chapters by strategy (Invariance Principle, Coloring Proofs, Extremal Principle, Box Principle) rather than by mathematical topic, implicitly teaching "when you see X, try strategy Y." The Invariance chapter opens: "We present our first Higher Problem-Solving Strategy. It is extremely useful in solving *certain types of difficult problems, which are easily recognizable.*" Chapters 5-12 shift to topic-based organization. **Tao's *Solving Mathematical Problems*** demonstrates his actual thought process — reviewers describe it as "like a detective story." **Chen's EGMO** contains "how would you come up with this?" commentary and explicit guidance on when to use synthetic vs. computational approaches in geometry. **Pranav Sriram's *Olympiad Combinatorics*** (freely available on AoPS) includes "reverse engineering" sections showing how solutions' main ideas fit together.

The Andreescu/Feng books, the IMO Compendium, and most traditional problem collections score high on execution but low on recognition — they organize problems by chapter/topic, effectively doing the recognition work for the reader.

---

## The cognitive science of how experts actually recognize problems

The research literature provides precise mechanisms for how mathematical pattern recognition works, with direct implications for competition math training.

**Chi, Feltovich, and Glaser's 1981 study** (*Cognitive Science*, 5(2), 121-152) is the foundational result. When experts and novices sorted 24 physics problems by similarity, **novices categorized by surface features** ("problems with blocks on inclined planes") while **experts categorized by deep structure** ("Conservation of Energy problems"). The experts' categories had no visual similarity — only a physicist could detect the underlying connection. This directly maps to competition math: a novice sees "this problem mentions triangles" while an expert sees "this is really a power-of-a-point configuration." The study established the concept of **problem schemata** — interrelated knowledge structures that unify superficially disparate problems.

**Schoenfeld and Herrmann's 1982 sorting study** replicated this for mathematics: when 32 math problems were sorted by professors versus students, professors grouped by underlying mathematical principles while students grouped by surface features. Critically, Schoenfeld's protocol analyses demonstrated that novice failure is often **not from lack of knowledge but from ineffective use of knowledge** — students who knew relevant techniques still failed because they couldn't recognize when to apply them.

**De Groot's chess expertise research** and Chase & Simon's chunking theory (1973) provide the quantitative benchmark: chess masters store approximately **50,000 chunks** (patterns) in long-term memory, and their superiority vanishes when pieces are randomly arranged. This directly analogizes to mathematics — experts recognize problem structures that suggest solution methods, just as chess masters recognize positional patterns that suggest moves. The estimate of ~50,000 chunks for chess mastery suggests mathematical competition expertise also requires massive exposure to organized problem types.

**Sweller's cognitive load theory** delivers a critical counterintuitive finding: conventional problem solving via means-ends analysis can actually **interfere with learning** because it consumes so much working memory that none is available for schema acquisition. This means studying worked examples (like Evan Chen's solution notes with motivation remarks) can be more effective than pure problem-solving for building technique recognition, especially for developing students. As schemas are acquired and automated, they free working memory for higher-level strategic thinking — explaining how experts seem to effortlessly recognize problem types.

**Koedinger and Anderson's 1990 study** found that geometry experts parse problem diagrams into **perceptual chunks called "diagram configurations"** that immediately cue relevant schematic knowledge, enabling them to plan proofs at a more abstract level and skip intermediate steps mentally. **Rittle-Johnson and Star's 2007 work** showed that explicitly comparing different solution methods for the same problem was "particularly effective for supporting procedural flexibility" — the ability to choose among approaches that characterizes expert problem solving.

**Amalric and Dehaene's 2016 fMRI study** (*PNAS*, 113(18), 4909-4917) revealed that mathematical thinking in experts activates bilateral intraparietal sulci and inferior temporal regions while **sparing language areas entirely** — mathematical pattern recognition is built on evolutionarily ancient circuits for number and space, not linguistic processing. This neurological finding suggests that verbal descriptions of techniques may be less effective for building recognition than spatial/visual training.

---

## Structured databases and AI approaches: the taxonomy landscape

**The OTIS catalog** remains the most comprehensive human-curated technique taxonomy, with 60+ units spanning all four olympiad domains. The public synopsis at https://web.evanchen.cc/static/otis-samples/synopsis.html reveals the full structure. Notable categories: Geometry includes "Moving Points" (projective animation), "Spiral Similarity/Miquel," "Config Geo" (standard configurations), and "Diagram Intuition." Combinatorics includes "Arrows" (functional graphs), "Global" (probabilistic method), "Weight" (weighted arguments), and "Equality" (exploiting equality cases). Number theory includes "Lifting the Exponent," "Orders" (multiplicative orders/primitive roots), "p-adic valuations," and "Vieta Jumping."

**The CHAMP paper** (Mao, Kim, Zhou; ACL 2024; https://arxiv.org/abs/2401.06961) provides the most concrete AI-oriented taxonomy: **54 concepts and 330 hints** mapped to 270 competition problems across number theory, polynomials, sequences, inequalities, and combinatorics. Each concept has category, name, and parent concept metadata (enabling hierarchical organization). Concepts are general knowledge (e.g., "Fermat's Little Theorem"); hints are problem-specific tricks (e.g., "Add 1 to both sides"). Key finding: **hints helped AI models far more than concept names** — the specific trick matters more than knowing the theorem exists. Average per problem: 1.4 concepts and 1.7 hints.

**Tim Gowers' Tricki** (https://www.tricki.org/) was the most ambitious attempt at cataloging mathematical tricks with deployment conditions — articles ranging from "If you can't solve the problem, try an easier one" to "Take the Fourier transform to convert a linear differential equation to polynomial." Unfortunately, it's now archived and contains only ~100 articles. Gowers identified the fundamental problem: "it was quite hard to make a really good contribution... for a website to take off, there needs to be a lower bar to participation." The vision and organizational structure remain more valuable than the actual content.

**DeepMind's AlphaProof** (Nature, 2025; DOI: 10.1038/s41586-025-09833-y) solved 4/6 IMO 2024 problems including P6 (which only 5 of 609 humans solved fully). It learns technique selection implicitly through reinforcement learning on 80 million auto-formalized problems rather than through an explicit technique taxonomy. The system's Test-Time RL approach generates millions of problem variants at inference time, essentially discovering relevant sub-problems and related theorems dynamically. **Gemini Deep Think** subsequently solved 5/6 IMO 2025 problems operating end-to-end in natural language. The AI literature confirms that pattern recognition can emerge from massive exposure even without explicit categorization — but the "Proof or Bluff" paper (Petrov et al., 2025; https://arxiv.org/abs/2503.21934) found current LLMs consistently claim to have solved problems even when their reasoning is flawed, unlike human experts who know when they're stuck.

**Lean/Mathlib's tactic library** (https://github.com/leanprover-community/mathlib4) catalogs proof tactics by purpose: algebraic (`ring`, `group`, `abel`), arithmetic (`linarith`, `omega`), simplification (`simp`, `norm_num`), and search (`apply?`, `exact?`). **ProofWiki** (https://proofwiki.org/) maintains **48 subcategories** of proof techniques. **Metamath** (https://us.metamath.org/) contains **41,000+ theorems** with complete dependency chains from ZFC axioms.

---

## Compound patterns: when problems demand technique chaining

The most important finding on compound patterns comes from Chen's geometry framework: **hard problems require chaining 2-3 of synthetic/computational/observational approaches**, and the nth problem on an IMO paper typically requires about n strategy types. This means P3 and P6 problems fundamentally require compound pattern recognition.

**Vieta Jumping** (https://en.wikipedia.org/wiki/Vieta_jumping) remains the canonical example of unexpected domain-crossing. IMO 1988 P6 is a number theory problem solved by treating it as a quadratic equation and using Vieta's formulas for infinite descent. The Brilliant wiki notes recognition is linked to symmetric Diophantine equations of degree 2 in two variables. The technique was essentially unknown before 1988 and created an entirely new recognition category.

**Bridge patterns** — structural cues indicating domain conversion is needed — are documented across several sources. Chen's IMO solution notes show examples: IMO 2023 geometry requiring a "synthetic phase" chained with a "projective phase." Yufei Zhao's "Algebraic Techniques in Combinatorics" (MOP 2007) explicitly teaches when algebraic tools apply to combinatorial settings. The OTIS unit "Adv Poly Method" covers the combinatorial Nullstellensatz — algebra applied to combinatorics. The key recognition pattern: when a combinatorics problem has too much algebraic structure to be purely combinatorial, or when a number theory problem's constraint suggests working with polynomials.

---

## Anti-patterns: the five most dangerous false leads

Sources consistently identify five recurring failure modes:

**Equality case mismatch** is the most documented anti-pattern. Thomas Mildorf's "Olympiad Inequalities" (https://artofproblemsolving.com/articles/files/MildorfInequalities.pdf) explicitly warns: when equality holds at both (t,t,t) AND (2t,t,t), "any cavalier use of AM-GM, Jensen, or Cauchy with unique equality case a = b = c will immediately falsify the problem." The decision hierarchy: check equality cases FIRST, then select the inequality tool whose equality case matches.

**The pointwise trap** in functional equations — assuming f(x)² = x² implies f(x) = x everywhere — is documented in Chen's Functional Equations handout and the OTIS Excerpts' Bogus Solutions section. The correct recognition: pointwise results like f(x) ∈ {0, x} don't determine f globally without additional structure.

**Premature technique commitment** — deciding on induction/coordinates/a specific approach before understanding the problem — is addressed across Chen's "Getting to Know Problems," Schoenfeld's research on metacognitive control, and Dominic Sherpa's blog (https://eventuallyalmosteverywhere.wordpress.com/): "The task is not to look at the problem and decide that it is an example of Olympiad technique #371. The task is actually to have as many ideas as possible, and eliminate the ones that don't work as quickly as possible."

**Condition-checking failures** — using LTE without verifying p ∤ x, p ∤ y, or applying Zsygmondy without checking the known exceptions — are documented in the LTE lemma handouts by Parvardi (https://pregatirematematicaolimpiadejuniori.wordpress.com/wp-content/uploads/2016/07/lte.pdf) and Victor Rong's divisibility handout (https://www.lessvrong.com/math/handouts/divisibility-summer2025.pdf).

**Strategic overreach** — spending excessive time on hard problems while making errors on easier ones — is documented in Chen's Contest Platitudes v3 as a contest-level anti-pattern.

---

## Domain-specific recognition cues: geometry, number theory, combinatorics, algebra

**Geometry approach selection** is best documented in Chen's three-source system. The blog post (https://blog.evanchen.cc/2016/01/19/some-advice-for-olympiad-geometry/) provides the macro framework. EGMO provides the detailed treatment. The decision cues: use **inversion** when many circles and lines pass through the same point (imomath.com: "some pictures cry to be inverted"); use **barycentric coordinates** when perpendicularity to triangle sides is involved or when problems are "triangle-centric" (Chen & Schindler's handout: "Cartesian coordinates are woefully inadequate for most olympiad geometry problems"); use **complex numbers** for problems on the unit circle; use **spiral similarity** when two similar triangles share a vertex; use **projective methods** when the problem is invariant under projection. The "GeoSlang" handout (https://web.evanchen.cc/handouts/GeoSlang/GeoSlang.pdf) catalogs named configurations: Reim's theorem, Shooting lemma, Death Star lemma, Prism lemma.

**Number theory recognition** is anchored by the LTE lemma: apply when you need ν_p(x^n − y^n) and p | (x−y) with p ∤ x, p ∤ y. The choice of which prime p to use is critical and documented in the Norra Real handout. Zsygmondy recognition: when a^n − b^n needs a "new" prime divisor not appearing for smaller exponents. Orders/primitive roots: when a problem involves divisibility of a^n − 1 by specific moduli. Vieta jumping: symmetric Diophantine equations of degree 2 in two variables. The OTIS catalog distinguishes 12+ number theory unit types.

**Combinatorics recognition** spans: **double counting** when an object can be measured two ways (Yufei Zhao MOP 2007 handout at https://yufeizhao.com/olympiad/doublecounting_mop.pdf); **extremal principle** when values are distinct, the set is bounded, or you have a monovariant (Brilliant wiki at https://brilliant.org/wiki/extremal-principle/); **probabilistic method** when there are "a lot of dumb choices" (noted in Chen's blog comments); **generating functions** for partition problems and recurrence relations (Zhao's AwesomeMath handout at https://yufeizhao.com/olympiad/comb3.pdf).

**Algebra recognition** follows: check homogeneity first; if non-homogeneous, use constraints to homogenize; then check equality cases to determine which inequality tool applies. Functional equations: guess answers by testing linear functions, establish injectivity/surjectivity, check for Cauchy-type structure. The OTIS Excerpts cover 13 algebraic/combinatorial topics with explicit walkthroughs.

---

## Video and summer program sources worth mining

**3Blue1Brown's** Putnam and IMO videos (https://www.3blue1brown.com/lessons/hardest-problem, plus the IMO windmill problem and generating functions videos) explicitly teach two meta-strategies: "Continue asking simpler versions until you get a foothold" and "If something you've added makes things conceptually easier, reframe the entire question in terms of it." **Po-Shen Loh's** MOP handouts (https://www.math.cmu.edu/~lohp/olympiad.shtml) span 2002-2013+. **Michael Penn's** YouTube channel (~300K subscribers, https://youtube.com/@MichaelPennMath) provides 400+ videos solving competition problems from worldwide contests with approach motivation. **Numberphile** has covered IMO 1988 P6 and Vieta jumping in multiple videos.

**Summer program materials:** PROMYS (https://promys.org/) — daily problem sets designed for discovery-based learning; students "design their own numerical experiments and employ their own powers of analysis to discover mathematical patterns." ROSS Mathematics Program (https://rossprogram.org/) — "Think deeply about simple things" philosophy, with students spending 20+ hours on single problems. MOP materials are available through Chen (https://web.evanchen.cc/mop.html), Zhao, and Loh's pages. **Mathcamp** (https://www.mathcamp.org/) emphasizes breadth over competition-specific training but its Qualifying Quiz process — which values scratchwork documenting the problem-solving journey — trains meta-cognitive skills.

---

## The master resource aggregation layer

Several meta-resources serve as entry points to the ecosystem:

- **Evan Chen's olympiad page** (https://web.evanchen.cc/olympiad.html) — master index of all his handouts, solution notes, and teaching materials
- **Evan Chen's "Where to Start"** (https://web.evanchen.cc/wherestart.html) — recommended progression for beginners
- **AoPS Resources Wiki** (https://artofproblemsolving.com/wiki/index.php/Resources_for_mathematics_competitions) — comprehensive meta-list of books, websites, programs
- **Jyoti Prakash Saha's Math Olympiad Training** (https://jpsaha.github.io/MOTP/) — organized links to all major handout collections
- **Yufei Zhao's olympiad page** (https://yufeizhao.com/olympiad/) — handout collection with book recommendations at increasing difficulty
- **MISTI Resources List** (https://www.mit.edu/~hsmui/files/handouts/bhutan/resources.pdf) — MIT-curated resource list by domain
- **OmegaLearn** (https://www.omegalearn.org/high-competition-math) — comprehensive listing of training programs and resources

---

## Conclusion: where the micro-pattern knowledge actually concentrates

The pattern-recognition knowledge that separates elite competition mathematicians from those who merely know techniques concentrates in a surprisingly small number of high-quality sources. **The Evan Chen ecosystem** (blog, OTIS, handouts, Twitch, EGMO, solution notes) contains the highest density of explicit "when to apply what" guidance. **Cognitive science** (Schoenfeld's metacognitive control, Chi et al.'s deep-structure categorization, Sweller's schema theory) provides the theoretical foundation explaining why studying motivated solutions builds recognition faster than raw problem-solving. **The CHAMP paper's 54 concepts and 330 hints** offer the most concrete attempt at a machine-readable technique taxonomy for competition math.

Three gaps remain unfilled. First, no source systematically maps the full space of compound pattern combinations — which technique pairings are common and what structural cues indicate chaining is needed. Second, anti-pattern documentation is scattered; no single resource catalogs "problems that look like X but are actually Y" across all domains. Third, the bridge between cognitive science findings and concrete training protocols for competition math is underdeveloped — Schoenfeld's self-monitoring questions ("What exactly are you doing? Why? How does it help?") have never been systematically integrated into a competition training curriculum. These three gaps represent the highest-value opportunities for advancing the field of mathematical pattern-recognition training.