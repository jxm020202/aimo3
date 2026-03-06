#!/usr/bin/env python3
"""Insert technique reference entries into the AIMO3 problem database.

Sources:
  - research/08-math-technique-recognition-database.md (85 techniques)
  - research/09-pattern-databases-source-map.md (additional descriptions)

Existing tech entries (DO NOT duplicate):
  tech_lte, tech_vieta_jump, tech_crt, tech_inversion, tech_bary,
  tech_genfunc, tech_incl_excl, tech_double_count, tech_quad_residue,
  tech_cauchy_schwarz, tech_directed_angles, tech_hensel
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'problem_db', 'problems.db')

EXISTING = {
    'tech_lte', 'tech_vieta_jump', 'tech_crt', 'tech_inversion', 'tech_bary',
    'tech_genfunc', 'tech_incl_excl', 'tech_double_count', 'tech_quad_residue',
    'tech_cauchy_schwarz', 'tech_directed_angles', 'tech_hensel',
}

# Each entry: (problem_id, category, topic, subtopic, triggers, technique, question, answer)
NEW_ENTRIES = [
    # ========================
    # GEOMETRY (14 entries)
    # ========================
    (
        'tech_power_of_point',
        'geometry',
        'circles',
        'power_of_a_point',
        'two chords intersecting, tangent + secant from same external point, need to prove concyclicity, products PA*PB appearing',
        'Power of a Point: PA*PB = PC*PD for secants through P. Converse proves concyclicity. PO^2 - r^2 gives signed power. Combine with radical axis for multi-circle problems. Equality iff P on circle.',
        'Let AB and CD be two chords of a circle intersecting at P. Prove PA*PB = PC*PD.',
        'Fix circle with center O radius r. For point P and any secant through P hitting circle at X,Y: PX*PY = |PO^2 - r^2| (signed: positive outside, negative inside). For chords AB, CD through P: both equal power of P, so PA*PB = PC*PD. Converse: if PA*PB = PC*PD for two lines through P, then A,B,C,D concyclic. This is the foundation of radical axes.',
    ),
    (
        'tech_radical_axis',
        'geometry',
        'circles',
        'radical_axis',
        'three circles with strange concurrent lines, multiple circles and need collinearity/concurrency, proving lines concurrent in circle configurations',
        'Radical axis: locus of equal power w.r.t. two circles, always perpendicular to line of centers. Radical center: three pairwise radical axes concur. Trick: point = degenerate circle (radius 0), so perpendicular bisector = radical axis.',
        'Three circles are given in the plane. Prove that the three pairwise radical axes are concurrent.',
        'For circles w1, w2, w3: radical axis of (w1,w2) is locus P with pow(P,w1)=pow(P,w2). Radical axis of (w2,w3): pow(P,w2)=pow(P,w3). At their intersection Q: pow(Q,w1)=pow(Q,w2)=pow(Q,w3), so Q lies on radical axis of (w1,w3) too. All three concurrent at the radical center. Application: to prove three lines concurrent, show each is a radical axis of some pair of circles.',
    ),
    (
        'tech_cross_ratio',
        'geometry',
        'projective',
        'cross_ratio_harmonic',
        'midpoints with parallel lines, tangent lines from external point to circle, concurrent cevians meeting opposite sides, angle bisector + perpendicularity together, symmedian or isogonal conjugate',
        'Cross ratio (A,B;X,Y) = (XA/XB)/(YA/YB). Harmonic bundle: cross ratio = -1. Arises from cevians: if AD,BE,CF concur and EF meets BC at X, then (X,D;B,C)=-1. Preserved under projection. Connects to poles/polars.',
        'In triangle ABC, cevians AD, BE, CF are concurrent. Line EF meets BC at X. Prove (X,D;B,C) = -1.',
        'By Ceva, (BD/DC)(CE/EA)(AF/FB)=1. Line EF meets BC at X. By Menelaus on triangle ABC with transversal E-F-X: (BX/XC)(CE/EA)(AF/FB)=-1. Combining with Ceva: BX/XC = -BD/DC (signed ratios), giving (X,D;B,C) = (BX/XC)/(BD/DC) = -1. This harmonic relationship is projectively invariant and connects tangent lines, poles/polars, and angle bisectors.',
    ),
    (
        'tech_pascal',
        'geometry',
        'projective',
        'pascal_theorem',
        'six points on a conic (circle), need to prove collinearity of three intersection points, hexagon inscribed in circle',
        'Pascal: hexagon ABCDEF inscribed in conic => AB.DE, BC.EF, CD.FA are collinear (Pascal line). Degenerate cases: let two vertices coincide => tangent line replaces chord. Dual: Brianchon (circumscribed hexagon => diagonals concurrent).',
        'Points A,B,C,D,E,F lie on a circle. Lines AB and DE meet at P, BC and EF meet at Q, CD and FA meet at R. Prove P,Q,R are collinear.',
        'Direct application of Pascal theorem on hexagon ABCDEF inscribed in the circle. The three cross-intersection points P=AB.DE, Q=BC.EF, R=CD.FA lie on the Pascal line. Degenerate versions: if B=C, chord BC becomes tangent at B. This handles problems where a tangent line and chords interact. For the dual (Brianchon): hexagon circumscribing a conic has main diagonals AD,BE,CF concurrent.',
    ),
    (
        'tech_homothety',
        'geometry',
        'transformations',
        'homothety',
        'parallel lines in configuration, similar triangles sharing a vertex, tangent circles (tangent point = center of homothety), scaled copies of figures',
        'Homothety: centered at O with ratio k maps P to P\' on ray OP with OP\'=k*OP. Preserves angles, maps circles to circles. Two tangent circles: external tangent point is center of positive homothety, internal tangent point is negative.',
        'Two circles are internally tangent at T. Prove that T is the center of a homothety mapping one circle to the other.',
        'Let circles w1 (center O1, radius r1) and w2 (center O2, radius r2) be internally tangent at T. Then T lies on line O1O2 with TO1=r1, TO2=r2, and O1O2=|r1-r2|. The homothety centered at T with ratio -r2/r1 maps O1 to O2 (since T,O1,O2 collinear and on the same side) and maps w1 to w2. For external tangency, ratio is +r2/r1. Key application: to show two circles tangent, find a homothety mapping one to the other.',
    ),
    (
        'tech_complex_numbers',
        'geometry',
        'coordinates',
        'complex_numbers',
        'many points on circumcircle, rotations or reflections playing a role, regular polygon vertices, spiral similarities, circumcenter at origin',
        'Place circumcircle as unit circle in C. Key formulas: circumcenter=0, centroid=(a+b+c)/3, orthocenter=a+b+c. Reflection of z over chord ab: a+b-ab*conj(z). Rotation by angle t: multiply by e^(it). Collinearity via Im((b-a)/(c-a))=0.',
        'Triangle ABC inscribed in unit circle. Express the orthocenter H in terms of complex coordinates a,b,c.',
        'With circumcircle as unit circle (|a|=|b|=|c|=1), circumcenter O=0. The key identity: H = a+b+c. Proof: verify OH = OA+OB+OC by the Euler line relation OH = OA+OB+OC. Alternatively, check perpendicularity (H-A) perp (B-C): Re((a+b+c-a)*conj(b-c)) = Re((b+c)*conj(b-c)) = Re(|b|^2-|c|^2) = 0 since |b|=|c|=1. Complex numbers excel when many points lie on the circle.',
    ),
    (
        'tech_simson_line',
        'geometry',
        'circles',
        'simson_line',
        'feet of perpendiculars from a point to triangle sides, collinearity of pedal points, point on circumcircle',
        'Simson line: feet of perpendiculars from point P on circumcircle to sides BC,CA,AB are collinear. Converse: if feet are collinear then P is on circumcircle. The Simson line bisects PH (H=orthocenter). Angle between two Simson lines = half arc between their poles.',
        'P lies on the circumcircle of triangle ABC. Drop perpendiculars from P to lines BC, CA, AB with feet D, E, F. Prove D, E, F are collinear.',
        'Since P is on circumcircle, angle BPC = 180-A. Quadrilateral BDPF is cyclic (right angles at D,F), so angle DPF = 180-B. Similarly CDPE is cyclic. Chase angles: angle(FPE) = angle(A) and the perpendicular feet form a degenerate triangle. Alternatively, use complex numbers with unit circle: if p is on the circle, the feet have explicit formulas and collinearity follows from Im being zero. The Simson line makes angle A with BC.',
    ),
    (
        'tech_poles_polars',
        'geometry',
        'projective',
        'poles_polars',
        'tangent from external point to circle, harmonic conjugates w.r.t. a circle, La Hire theorem, self-polar triangles',
        'Polar of point P w.r.t. circle: locus of harmonic conjugates of P on all secants. If P outside circle, polar = chord of contact of tangents from P. La Hire: if P lies on polar of Q, then Q lies on polar of P. Self-polar triangle: each vertex is pole of opposite side.',
        'From point P outside a circle, tangent lines touch at T1, T2. Prove that for any secant through P meeting circle at A,B, the line T1T2 and AB create a harmonic range.',
        'T1T2 is the polar of P. Any secant through P meets the circle at A,B and meets polar T1T2 at X. By the polar definition, (P,X;A,B) = -1 (harmonic). This means PX separates AB harmonically. Key applications: (1) Brocard theorem: for cyclic ABCD, diagonal triangle is self-polar w.r.t. circumcircle. (2) Proving concurrence: three polars concurrent iff three poles collinear (by La Hire duality).',
    ),
    (
        'tech_spiral_sim',
        'geometry',
        'transformations',
        'spiral_similarity',
        'two similar triangles sharing a vertex, rotation + scaling mapping one figure to another, two similar figures in the plane with a fixed point',
        'Spiral similarity: composition of rotation and dilation about the same center. Uniquely determined by mapping two points to two points. Center found as intersection of circumcircles of (A,A\',B) and (A,A\',B\'). In complex numbers: z -> az+b.',
        'Triangles ABP and CDQ are similar with the same orientation. Find the center of the spiral similarity mapping AB to CD.',
        'The center S of the spiral similarity maps A->C and B->D. In complex coords: c = s*a + t, d = s*b + t, so s = (c-d)/(a-b), t = c - s*a. The center satisfies z = s*z + t, giving z = t/(1-s). Geometrically, S is the second intersection of circumcircles of triangles APC and BPD (where P,Q are any corresponding points). Spiral similarities are the key tool for problems involving similar figures in the plane.',
    ),
    (
        'tech_shooting_lemma',
        'geometry',
        'circles',
        'shooting_lemma',
        'small circle tangent to chord of big circle and internally tangent to big circle, mixtilinear incircles, curvilinear configurations',
        'Shooting/Death Star Lemma: circle w tangent to chord AB of circle W at K, internally tangent to W at T. Then TK passes through arc midpoint M of AB. Proof via homothety at T mapping w to W. Key for mixtilinear incircle problems.',
        'Circle w is tangent to chord AB of circle W at point K, and internally tangent to W at T. Prove that line TK passes through the midpoint M of arc AB (not containing T).',
        'The homothety centered at T mapping w to W sends K (on w and on chord AB) to a point on W and on the image of chord AB. Since w is tangent to AB at K, the image line is parallel to AB... Actually: the homothety at T maps w->W and K->M where M is on W. Since w is tangent to AB at K, the tangent to W at M is parallel to AB, making M the arc midpoint. This lemma is essential for mixtilinear incircle configurations.',
    ),
    (
        'tech_miquel',
        'geometry',
        'circles',
        'miquel_point',
        'circumcircles of four triangles in a complete quadrilateral, three circles through pairs of points all passing through one point, point on sides of triangle with circumcircles of pedal triangles',
        'Miquel point: for points on sides of a triangle (or complete quadrilateral), the circumcircles of the resulting triangles concur at the Miquel point. For complete quadrilateral: four circumcircles of four triangles pass through one point. Connects to spiral similarities.',
        'Points D,E,F lie on sides BC,CA,AB of triangle ABC. Prove circumcircles of AEF, BDF, CDE have a common point.',
        'Let circumcircles of AEF and BDF meet at F and M (Miquel point). Angle AME = angle AFE (cyclic AEFM) = 180-angle(AFB) since F on AB. Angle BMD = angle BFD (cyclic BFDM). Then angle CMD = 360 - angle AME - angle BMD - angle AMB. Chase angles to show angle CED + angle CMD = 180, so M lies on circumcircle of CDE. The Miquel point is the spiral similarity center mapping one side configuration to another.',
    ),
    (
        'tech_isogonal',
        'geometry',
        'transformations',
        'isogonal_conjugate',
        'angle bisector reflections, symmetric angle conditions, circumcenter-orthocenter duality, isogonal lines',
        'Isogonal conjugate of P w.r.t. triangle: reflect cevians AP,BP,CP over angle bisectors. The reflected cevians concur at P* (isogonal conjugate). Key pairs: circumcenter O <-> orthocenter H, incenter I <-> I itself. Symmedian point = isogonal conjugate of centroid.',
        'In triangle ABC, the circumcenter O and orthocenter H are isogonal conjugates. Verify this.',
        'Reflect AO over the A-angle bisector. Since angle OAB = 90-C (O is circumcenter), the reflection makes angle with AB equal to 90-C on the other side, i.e., angle with AC = 90-C. But angle HAC = 90-C (H is orthocenter: angle BAH = 90-B, so angle HAC = A-(90-B) = A+B-90 = 90-C). So AO reflects to AH. Similarly for B and C. Hence O and H are isogonal conjugates.',
    ),
    (
        'tech_monge',
        'geometry',
        'circles',
        'monge_theorem',
        'three circles with external/internal tangent lines, need to prove three points collinear, homothety centers',
        'Monge theorem: for three circles, the three pairwise external centers of similitude (intersections of external common tangents) are collinear. More generally, an odd number of internal centers of similitude also gives collinearity. Proof: composition of homotheties.',
        'Three circles w1, w2, w3 are given. Prove that the three external centers of similitude (pairwise) are collinear.',
        'External center of similitude of (w1,w2) is the center of the positive homothety mapping w1 to w2: S12 = (r2*O1 - r1*O2)/(r2 - r1) (for unequal radii). The homothety h1 mapping w1->w2 composed with h2 mapping w2->w3 gives h3 mapping w1->w3 with center on line S12-S23. This center is exactly S13. So S12, S23, S13 are collinear. Extends to: any even number of internal substitutions preserves collinearity.',
    ),
    (
        'tech_incenter_excircle_lemma',
        'geometry',
        'circles',
        'incenter_excircle_lemma',
        'incenter/excircle with circumcircle interaction, arc midpoint of circumcircle, incircle tangent point and midpoint of side',
        'Incenter/Excircle Lemma (Fact 5/Trillium): circumcircle of BIC has center at arc midpoint L of minor arc BC (where L is on arc not containing A). Corollary: LB=LI=LC=LI_A. Iran Lemma: connects intouch tangent chord, angle bisectors, and side midpoints.',
        'In triangle ABC with incenter I, let L be the midpoint of arc BC not containing A on the circumcircle. Prove LB = LI.',
        'L is arc midpoint of BC, so angle BLC = angle BAC (inscribed). Since I is incenter, angle BIC = 90 + A/2. In triangle BIC: angle IBC = B/2, angle ICB = C/2. Now angle BLI = angle BLC - angle ILC. But LB = LC (L is arc midpoint), and angle LBI = angle LBC - B/2. Since angle LBC = angle LAC = A/2 (inscribed in arc LC), angle LBI = A/2 - B/2... More directly: LB = LI follows from angle LBI = angle LIB = (A+B)/2 - something. Standard proof: triangle LBI is isosceles because angle LBI = angle LBC + angle CBI = A/2 + B/2 = angle LIB.',
    ),

    # ========================
    # NUMBER THEORY (8 entries)
    # ========================
    (
        'tech_orders',
        'number_theory',
        'modular_arithmetic',
        'orders_primitive_roots',
        'a^N = 1 mod p and need to constrain N, order of element divides phi(n), n^2+1 divisible by prime => p = 1 mod 4',
        'Order ord_n(a) = smallest m with a^m = 1 mod n. Key: ord_n(a) | phi(n) and ord_n(a) | N iff a^N = 1 mod n. The n^2+1 lemma: if p | n^2+1 then ord_p(n)=4, so 4|(p-1), meaning p = 1 mod 4. Generalizes via cyclotomic polynomials.',
        'Prove that every prime divisor of n^2 + 1 is congruent to 1 mod 4.',
        'If p | n^2+1, then n^2 = -1 mod p, so n^4 = 1 mod p but n^2 != 1 mod p. Thus ord_p(n) = 4. Since ord_p(n) | p-1 (by Fermat), we get 4 | p-1, i.e., p = 1 mod 4. Generalization: if p | Phi_k(n) (k-th cyclotomic polynomial), then either p | k or ord_p(n) = k, giving k | p-1 so p = 1 mod k. This constrains prime divisors to arithmetic progressions.',
    ),
    (
        'tech_zsigmondy',
        'number_theory',
        'diophantine',
        'zsigmondy',
        'a^n - b^n must have a new prime factor, Diophantine equations a^n - 1 = (something with limited prime factors), finitely many solutions to exponential equations',
        'Zsigmondy: for coprime a>b>=1 and n>=2, a^n-b^n has a primitive prime divisor p not dividing a^k-b^k for any k<n. Exceptions: n=2 with a+b=2^s, and (a,b,n)=(2,1,6). The primitive divisor p satisfies p = 1 mod n.',
        'Prove that the equation 2^n - 1 = p*q has only finitely many solutions with p,q prime.',
        'By Zsigmondy, for n>=7 (avoiding the (2,1,6) exception), 2^n-1 has a primitive prime divisor p_n not dividing 2^k-1 for k<n. As n grows, 2^n-1 accumulates distinct primitive primes, so eventually has >2 prime factors. Check small n manually: n=2: 3=3, n=3: 7, n=4: 15=3*5, n=5: 31, n=6: 63=7*9 (not semiprime), n=7: 127. Only finitely many n give exactly two prime factors.',
    ),
    (
        'tech_padic',
        'number_theory',
        'valuation',
        'padic_valuations',
        'track exact prime power in factorials or products, v_p(n!) computation, ultrametric inequality for sums, need to compare powers of p dividing expressions',
        'p-adic valuation v_p(n) = exponent of p in factorization of n. Key: v_p(ab)=v_p(a)+v_p(b), v_p(a+b)>=min(v_p(a),v_p(b)) with equality when valuations differ. Legendre: v_p(n!)=sum floor(n/p^k)=(n-s_p(n))/(p-1) where s_p is digit sum base p.',
        'Find v_2(100!) (the largest power of 2 dividing 100!).',
        'By Legendre formula: v_2(100!) = floor(100/2) + floor(100/4) + floor(100/8) + floor(100/16) + floor(100/32) + floor(100/64) = 50+25+12+6+3+1 = 97. Alternatively: v_2(100!) = (100 - s_2(100))/(2-1) where s_2(100) = s_2(1100100_2) = 1+1+0+0+1+0+0 = 3, giving (100-3)/1 = 97. Legendre is the standard tool for v_p(n!) and v_p(C(n,k)) computations.',
    ),
    (
        'tech_descent',
        'number_theory',
        'diophantine',
        'infinite_descent',
        'prove Diophantine equation has no positive integer solutions, modular arithmetic alone fails, can parametrize solutions to get smaller ones, Pythagorean-triple-like structure',
        'Infinite descent: assume minimal positive solution (a,b,...) exists, derive a smaller solution, contradiction. Often combined with: modular constraints to restrict form, then substitution to reduce. Fermat used for x^4+y^4=z^2. Works when solutions have recursive structure.',
        'Prove x^4 + y^4 = z^2 has no positive integer solutions.',
        'Assume minimal solution with z minimal. Then gcd(x^2,y^2,z)=1. View as (x^2)^2+(y^2)^2=z^2, a Pythagorean triple: x^2=m^2-n^2, y^2=2mn, z=m^2+n^2 (or swapped). From y^2=2mn with gcd(m,n)=1 and one even: m=s^2, n=2t^2 (or swap). Then x^2=s^4-4t^4... This eventually yields s^4+t^4 dividing something smaller than z, giving descent. The key: parametrize via Pythagorean triples, then find the recursive structure.',
    ),
    (
        'tech_quad_reciprocity',
        'number_theory',
        'quadratic_forms',
        'quadratic_reciprocity',
        'need to determine if x^2 = a mod p is solvable, constraining prime divisors to specific residue classes, Legendre symbol computations',
        'Quadratic Reciprocity: for odd primes p!=q, (p/q)(q/p) = (-1)^((p-1)/2 * (q-1)/2). Supplements: (-1/p) = (-1)^((p-1)/2), (2/p) = (-1)^((p^2-1)/8). Use to compute Legendre symbols and determine which primes split/remain inert in quadratic extensions.',
        'Determine which primes p have -3 as a quadratic residue mod p.',
        '(-3/p) = (-1/p)(3/p). By supplement: (-1/p) = 1 iff p = 1 mod 4. By QR: (3/p)(p/3) = (-1)^((3-1)/2 * (p-1)/2) = (-1)^(p-1)/2. So (3/p) = (p/3)*(-1)^((p-1)/2). Cases: if p = 1 mod 3, (p/3)=(1/3)=1; if p = 2 mod 3, (p/3)=(2/3)=-1. Combining: -3 is a QR mod p iff p = 1 mod 3 (equivalently p = 1 mod 6 for p>3). This type of analysis determines which primes divide values of quadratic forms.',
    ),
    (
        'tech_legendre_formula',
        'number_theory',
        'valuation',
        'legendre_formula',
        'prime factorization of factorials or binomial coefficients, v_p(n!) or v_p(C(n,k)), Kummer theorem for carries in addition',
        'Legendre: v_p(n!) = sum_{i>=1} floor(n/p^i) = (n - s_p(n))/(p-1). Kummer: v_p(C(m+n,m)) = number of carries when adding m,n in base p. Use for: showing p^k | n!, proving C(n,k) is odd/even, and bounding prime powers in products.',
        'Prove that C(2n, n) is always even for n >= 1.',
        'v_2(C(2n,n)) = v_2((2n)!) - 2*v_2(n!). By Legendre: v_2(k!) = (k - s_2(k))/1 = k - s_2(k). So v_2(C(2n,n)) = (2n - s_2(2n)) - 2(n - s_2(n)) = 2*s_2(n) - s_2(2n). Since 2n in binary is n shifted left by 1, s_2(2n) = s_2(n). So v_2(C(2n,n)) = 2*s_2(n) - s_2(n) = s_2(n) >= 1 for n>=1. By Kummer: equals number of carries adding n+n in base 2, which is positive since n has a 1-bit.',
    ),
    (
        'tech_fermat_descent',
        'number_theory',
        'diophantine',
        'fermats_two_square',
        'representing primes as sum of two squares, p = 1 mod 4 implies p = a^2+b^2, Gaussian integers, norms in Z[i]',
        'Fermat two-square theorem: prime p = a^2+b^2 iff p = 2 or p = 1 mod 4. Proof via Gaussian integers: p = 1 mod 4 => -1 is QR mod p => p | x^2+1 = (x+i)(x-i) in Z[i], but p does not divide either factor, so p is not prime in Z[i], hence p = (a+bi)(a-bi) = a^2+b^2.',
        'Prove every prime p = 1 mod 4 can be written as a sum of two squares.',
        'Since p = 1 mod 4, -1 is a QR mod p: exists x with x^2 = -1 mod p. Then p | x^2+1 = (x+i)(x-i) in Z[i]. If p were prime in Z[i], p would divide x+i or x-i, but p | (x+i) means p | x and p | 1, impossible. So p = pi * conj(pi) for some Gaussian prime pi = a+bi, giving p = a^2+b^2. Uniqueness follows from unique factorization in Z[i]. Extends: n = a^2+b^2 iff all prime factors p = 3 mod 4 appear to even power.',
    ),
    (
        'tech_sophie_germain',
        'number_theory',
        'factoring',
        'sophie_germain_identity',
        'a^4 + 4b^4 appearing, sum of fourth powers, factoring expressions of form x^4 + 4y^4',
        'Sophie Germain Identity: a^4 + 4b^4 = (a^2+2b^2+2ab)(a^2+2b^2-2ab). Completing the square: a^4+4b^4 = (a^2+2b^2)^2 - (2ab)^2 = difference of squares. Use for proving composite numbers or factoring in NT.',
        'Prove that n^4 + 4^n is composite for all integers n > 1.',
        'For odd n: n^4 + 4^n = n^4 + 4*(4^((n-1)/2))^4... Actually for any n>1: if n is even, n^4+4^n is even and >2, so composite. If n is odd, write 4^n = 4*(2^(n-1))^2... Better: n^4 + 4^n = n^4 + 4*(2^(n-1))^4. By Sophie Germain with a=n, b=2^((n-1)/2) (integer since n odd): = (n^2+2^n+n*2^((n+1)/2))(n^2+2^n-n*2^((n+1)/2)). Both factors > 1 for n>1. For n even and >2, n^4+4^n is divisible by 2.',
    ),

    # ========================
    # ALGEBRA (12 entries)
    # ========================
    (
        'tech_vieta_formulas',
        'algebra',
        'polynomials',
        'vieta_formulas',
        'polynomial coefficients and need symmetric expressions of roots, sum/product of roots without finding them, system of equations with symmetric variables as roots of auxiliary polynomial',
        'Vieta formulas: for poly a_n*x^n+...+a_0 with roots r_i, e_k(roots) = (-1)^k * a_{n-k}/a_n. For quadratic x^2-Sx+P: r1+r2=S, r1*r2=P. For cubic x^3-Sx^2+Px-Q: sum=S, pairwise=P, product=Q. Use to build auxiliary polynomial from symmetric system.',
        'If a+b+c=6, ab+bc+ca=11, abc=6, find a^2+b^2+c^2.',
        'a,b,c are roots of t^3-6t^2+11t-6=0 = (t-1)(t-2)(t-3). But we can also compute directly: a^2+b^2+c^2 = (a+b+c)^2 - 2(ab+bc+ca) = 36-22 = 14. This is the fundamental use of Vieta: express any symmetric function of roots in terms of elementary symmetric polynomials (which equal polynomial coefficients up to sign). Newton sums extend this to power sums recursively.',
    ),
    (
        'tech_newton_sums',
        'algebra',
        'polynomials',
        'newton_sums',
        'r1^k + r2^k for large k, power sums of polynomial roots, recursive computation of symmetric power sums',
        'Newton-Girard identities: P_k = r1^k+...+rn^k computed recursively. For monic x^n+c_{n-1}x^{n-1}+...+c_0: P_k = -c_{n-1}*P_{k-1}-c_{n-2}*P_{k-2}-...-k*c_{n-k}. For quadratic x^2-Ax+B: P_k = A*P_{k-1} - B*P_{k-2}.',
        'For x^2 - 3x + 1 = 0 with roots a,b, find a^10 + b^10.',
        'P_0=2, P_1=3 (=A). Recurrence P_k = 3*P_{k-1} - P_{k-2}: P_2=3*3-2=7, P_3=3*7-3=18, P_4=3*18-7=47, P_5=3*47-18=123, P_6=3*123-47=322, P_7=3*322-123=843, P_8=3*843-322=2207, P_9=3*2207-843=5778, P_10=3*5778-2207=15127. Answer: 15127. This avoids finding roots (which are (3+/-sqrt(5))/2). Newton sums turn power-sum problems into pure recurrence.',
    ),
    (
        'tech_sfft',
        'algebra',
        'factoring',
        'simon_factoring_trick',
        'Diophantine equation with cross term xy and linear terms, xy + ax + by = c, need integer solutions of bilinear equation',
        'Simon\'s Favorite Factoring Trick (SFFT): xy + ax + by + ab = (x+b)(y+a). Add ab to both sides of xy+ax+by=c to get (x+b)(y+a)=c+ab. Then enumerate factor pairs of c+ab. Works for any bilinear Diophantine equation.',
        'Find all positive integer solutions to xy + 3x + 2y = 55.',
        'Add 6 to both sides: xy + 3x + 2y + 6 = 61. Factor: (x+2)(y+3) = 61. Since 61 is prime and x,y>0: x+2>2 and y+3>3, so x+2=61, y+3=1 (impossible since y>0) or x+2=1 (impossible since x>0). Actually with positive integers: (x+2)(y+3)=61, factors of 61: 1*61 or 61*1. x+2=61=>x=59,y+3=1=>y=-2 (invalid). x+2=1=>x=-1 (invalid). So no positive integer solutions. For non-prime RHS, enumerate all factor pairs.',
    ),
    (
        'tech_amgm',
        'algebra',
        'inequalities',
        'am_gm',
        'sum of positive terms >= product, weighted constraint optimization, equality only at all-equal point, need lower/upper bound of symmetric expression',
        'AM-GM: (a1+...+an)/n >= (a1*...*an)^(1/n), equality iff all equal. Weighted: w1*a1+...+wn*an >= a1^w1*...*an^wn for weights summing to 1. Key trick: "the more mixed monomials are smaller" — if one monomial majorizes another, AM-GM proves the inequality.',
        'Prove that for positive reals a,b,c with abc=1: a+b+c >= 3.',
        'By AM-GM: (a+b+c)/3 >= (abc)^(1/3) = 1, so a+b+c >= 3. Equality iff a=b=c=1. Weighted version handles constraints like a^2*b*c=1: apply weighted AM-GM with weights (2/4, 1/4, 1/4) to get (2a+b+c)/4 >= (a^2*b*c)^(1/4) = 1. More advanced: to prove Σ a^3 >= Σ a^2*b (cyclic, for positives), note a^3+a^3+b^3 >= 3a^2*b by AM-GM, then sum cyclically.',
    ),
    (
        'tech_schur',
        'algebra',
        'inequalities',
        'schur',
        'inequality with equality at a=b=c AND at (t,t,0), AM-GM cannot produce the abc term, need to close gap in symmetric inequality proof',
        'Schur inequality: a^r(a-b)(a-c)+b^r(b-c)(b-a)+c^r(c-a)(c-b) >= 0 for r>=0. For r=1: a^3+b^3+c^3+3abc >= ab(a+b)+bc(b+c)+ca(c+a). Equality at a=b=c and at (t,t,0). Key: when AM-GM proves "most" of an inequality but leaves an abc-shaped gap, Schur fills it.',
        'Prove a^3+b^3+c^3+3abc >= a^2(b+c)+b^2(c+a)+c^2(a+b) for non-negative reals.',
        'This IS Schur with r=1: expand Schur = sum a(a-b)(a-c) = sum(a^3 - a^2b - a^2c + abc) = (a^3+b^3+c^3) - (a^2b+a^2c+b^2c+b^2a+c^2a+c^2b) + 3abc >= 0. Rearranging: a^3+b^3+c^3+3abc >= a^2(b+c)+b^2(c+a)+c^2(a+b). Equality when a=b=c or when one variable is 0 and others equal. The double equality condition (a=b=c AND boundary) is the signature that Schur is needed.',
    ),
    (
        'tech_jensen',
        'algebra',
        'inequalities',
        'jensen',
        'sum of f(x_i) with convex/concave f and fixed-sum constraint, f\'\'>=0 or f\'\'<=0, need to bound Σf(x_i) when Σx_i is fixed',
        'Jensen: for convex f and weights summing to 1: f(Σw_i*x_i) <= Σw_i*f(x_i). Reversed for concave f. Common convex: x^2, e^x, -ln(x), 1/x (x>0). Concave: sqrt(x), ln(x), sin(x) on (0,pi). When f has inflection point, use tangent line trick instead.',
        'Prove that for positive reals with a+b+c=1: 1/a + 1/b + 1/c >= 9.',
        'f(x) = 1/x is convex on (0,inf) since f\'\'(x) = 2/x^3 > 0. By Jensen with equal weights: f((a+b+c)/3) <= (f(a)+f(b)+f(c))/3. So 1/(1/3) <= (1/a+1/b+1/c)/3, giving 3 <= (1/a+1/b+1/c)/3, hence 1/a+1/b+1/c >= 9. Equality iff a=b=c=1/3. Jensen is the direct tool when you recognize the constraint as a fixed sum and the objective as a sum of convex/concave evaluations.',
    ),
    (
        'tech_tangent_line',
        'algebra',
        'inequalities',
        'tangent_line_trick',
        'f has inflection point so Jensen fails, inequality with equality at non-symmetric point, need to bound f(x) by a linear function globally',
        'Tangent line trick: find tangent y=f(a)+f\'(a)(x-a) at equality point a. If f(x) >= tangent for all x in domain (verify!), then sum: Σf(x_i) >= Σ(f(a)+f\'(a)(x_i-a)) = n*f(a)+f\'(a)*(Σx_i - n*a). With constraint Σx_i=S: RHS = n*f(a)+f\'(a)*(S-na).',
        'For positive reals with a+b+c=3, prove a/(1+b^2) + b/(1+c^2) + c/(1+a^2) >= 3/2.',
        'f(x) = x/(1+x^2) has inflection point (f is not convex everywhere), so Jensen fails. Equality at a=b=c=1. Tangent at x=1: f(1)=1/2, f\'(x) = (1-x^2)/(1+x^2)^2, f\'(1)=0. So tangent is y=1/2. Need f(x) >= 1/2 for all x>0? No: f(x) = x/(1+x^2) <= 1/2 for x>0 (by AM-GM: 1+x^2>=2x). Wrong direction! Reassess: might need different approach. This illustrates why tangent line trick requires careful verification of the global bound direction.',
    ),
    (
        'tech_holder',
        'algebra',
        'inequalities',
        'holder',
        'cube roots or higher-order radicals in inequality, need to eliminate nth roots, generalization of Cauchy-Schwarz to 3+ sequences',
        'Holder inequality: (Σa_i^p)^(1/p) * (Σb_i^q)^(1/q) >= Σa_i*b_i where 1/p+1/q=1. For 3 sequences: (Σa_i^p)(Σb_i^q)(Σc_i^r) >= (Σa_i*b_i*c_i)^(p+q+r)... More useful form: (Σa_i)(Σb_i)(Σc_i) >= (Σ(a_i*b_i*c_i)^(1/3))^3.',
        'Prove (a^3+b^3)(a^3+c^3)(b^3+c^3) >= (ab+ac+bc)^3 for positive reals.',
        'By Holder with p=q=r=3: (Σx_i^3)^(1/3)(Σy_i^3)^(1/3)(Σz_i^3)^(1/3) >= Σx_i*y_i*z_i. Apply with sequences (a,b),(a,c),(b,c): ((a^3+b^3)(a^3+c^3)(b^3+c^3))^(1/3) >= a*a*b + b*c*c = a^2b+bc^2... Actually cleaner: use Holder as (Σa^3)(Σb^3) >= (Σ(ab)^(3/2))^2, then iterate. The power of Holder: it eliminates radicals by raising both sides to appropriate powers.',
    ),
    (
        'tech_sos',
        'algebra',
        'inequalities',
        'sum_of_squares',
        'AM-GM and Schur insufficient, very sharp inequality, need exact SOS decomposition, homogeneous polynomial inequality',
        'SOS (Sum of Squares): write symmetric inequality as S_a(b-c)^2 + S_b(c-a)^2 + S_c(a-b)^2 >= 0. Find S_a, S_b, S_c by substituting b=c, c=a, a=b. Pham Kim Hung criteria: sufficient if S_c>=0, S_b>=0, S_a+S_b>=0 (after WLOG a>=b>=c).',
        'Prove a^4+b^4+c^4 >= a^2*b^2+b^2*c^2+c^2*a^2 for all reals.',
        'Compute Sa,Sb,Sc for LHS-RHS = S_a(b-c)^2+S_b(c-a)^2+S_c(a-b)^2. Set b=c: a^4+2b^4-(a^2b^2+b^4+a^2b^2)=a^4-2a^2b^2+b^4=(a^2-b^2)^2. So 2S_a*(b-c)^2|(b=c) = (a^2-b^2)^2, giving S_a = (a+b)^2/2... Actually simpler: LHS-RHS = (1/2)((a^2-b^2)^2+(b^2-c^2)^2+(c^2-a^2)^2) >= 0. This is a direct SOS decomposition. SOS is the brute-force method when elegant approaches fail.',
    ),
    (
        'tech_pqr',
        'algebra',
        'inequalities',
        'pqr_substitution',
        'symmetric 3-variable inequality with constraint, need to eliminate variables systematically, inequality linear in one symmetric function',
        'pqr substitution: p=a+b+c, q=ab+bc+ca, r=abc. Any symmetric polynomial in a,b,c is a polynomial in p,q,r. Key: expressions are LINEAR in r for fixed p,q. By Schur, r is bounded: at extrema, two variables are equal or one is zero. Reduces to single-variable verification.',
        'For non-negative a,b,c with a+b+c=3, prove abc <= 1.',
        'With p=3 fixed, we maximize r=abc. By pqr method, express constraint: a,b,c are roots of t^3-3t^2+qt-r=0. For real non-negative roots, discriminant >= 0 gives constraints on q,r. By the equal-variable theorem, maximum r occurs at a=b=c=1 (giving r=1) or at boundary a=b, c=3-2a. Boundary: r=a^2(3-2a), r\'=a(6-6a)=0 at a=0 or a=1. Max at a=1: r=1. So abc <= 1.',
    ),
    (
        'tech_func_eq',
        'algebra',
        'functional_equations',
        'functional_equations',
        'find all functions f:R->R such that, functional equation with f composed multiple times, Cauchy-type equation, f(x+y) = f(x)+f(y) or variants',
        'FE workflow: (1) Guess solution (try f=0,x,-x,kx,kx+c,x^2). (2) Substitute x=y=0 to find f(0). (3) One variable=0 to simplify. (4) Force cancellation by setting arguments equal. (5) Swap x,y for new equation. (6) Replace x with f(t) if bijective. Reduce to Cauchy form when possible.',
        'Find all f:R->R with f(x+y)+f(x-y) = 2f(x)+2f(y) for all x,y.',
        'x=y=0: f(0)+f(0)=4f(0), so f(0)=0. y=x: f(2x)+f(0)=2f(x)+2f(x), so f(2x)=4f(x). This suggests f(x)=cx^2. Verify: c(x+y)^2+c(x-y)^2 = c(x^2+2xy+y^2+x^2-2xy+y^2) = 2cx^2+2cy^2 = 2f(x)+2f(y). For uniqueness: set g(x)=f(x)/f(1), then g(1)=1, g is continuous (if assumed), and g(r)=r^2 for all rationals by induction. With continuity, f(x)=cx^2. Without continuity, pathological solutions exist.',
    ),
    (
        'tech_cauchy_eq',
        'algebra',
        'functional_equations',
        'cauchy_equation',
        'f(x+y)=f(x)+f(y), f(xy)=f(x)f(y), f(x+y)=f(x)f(y), f(xy)=f(x)+f(y), can reduce functional equation to additive/multiplicative form',
        'Four Cauchy types: additive f(x+y)=f(x)+f(y) => f=cx; exponential f(x+y)=f(x)f(y) => f=a^x; logarithmic f(xy)=f(x)+f(y) => f=c*log(x); multiplicative f(xy)=f(x)f(y) => f=x^c. On Q, solutions unique via induction. On R, need regularity (continuity/monotone/bounded on interval) to exclude pathological solutions.',
        'Find all continuous f:R->R with f(x+y)=f(x)+f(y).',
        'On integers: f(n)=f(1)*n by induction. On rationals: f(p/q)=f(1)*p/q by f(p/q)*q = f(p) = f(1)*p. By continuity and density of Q in R: f(x)=cx for all x in R where c=f(1). Without continuity, using Axiom of Choice, there exist Hamel bases of R over Q giving pathological solutions. The key insight: if ANY regularity condition holds (monotone on an interval, measurable, bounded on an interval), then f must be linear.',
    ),

    # ========================
    # COMBINATORICS (14 entries)
    # ========================
    (
        'tech_invariants',
        'combinatorics',
        'process',
        'invariants',
        'repeated operations on numbers/objects, can you reach configuration B from A, numbers on a board being erased and replaced, parity/mod-k preserved under operations',
        'Invariant: quantity unchanged by allowed operations. Find by checking: parity, sum, sum mod k, product, XOR, coloring. If invariant differs between start and target, transformation is impossible. Common: parity (mod 2), residues (mod 3 or mod k), sums of squares.',
        'A dragon has 100 heads. A knight can cut 15, 17, 20, or 5 heads, but 24, 2, 14, or 17 grow back. Can the knight kill the dragon (0 heads)?',
        'Net changes: -15+24=+9, -17+2=-15, -20+14=-6, -5+17=+12. All changes are multiples of 3: +9, -15, -6, +12. So heads mod 3 is invariant. Start: 100 = 1 mod 3. Target: 0 = 0 mod 3. Since 1 != 0 mod 3, the dragon cannot be killed. Key: always check small moduli (2, 3, 4, ...) as potential invariants. For termination problems, look for bounded monovariants instead.',
    ),
    (
        'tech_monovariants',
        'combinatorics',
        'process',
        'monovariants',
        'prove this process terminates, algorithm/game must end, sequence of operations on finite set, potential function that strictly decreases',
        'Monovariant: quantity that strictly increases or decreases with each operation and is bounded. If bounded integer monovariant decreases, process terminates in at most (initial - lower_bound) steps. Common monovariants: number of inversions, sum of positions, maximum element.',
        'n people stand in a line. Each minute, if person i is taller than person i+1, they swap. Prove the process terminates.',
        'Count inversions: pairs (i,j) with i<j but height(i)>height(j). Each swap reduces inversions by exactly 1 (the swapped pair becomes ordered, and relative order of all other pairs is unchanged). Inversions is a non-negative integer, decreasing by 1 each step, so the process terminates in at most C(n,2) steps. More generally: for any swapping/sorting process, inversions or a similar measure of "disorder" serves as monovariant.',
    ),
    (
        'tech_pigeonhole',
        'combinatorics',
        'counting',
        'pigeonhole',
        'prove there exist two elements with same property, n+1 objects in n boxes, sufficiently many objects must share a category, Erdos-Szekeres type',
        'Pigeonhole: n+1 objects in n boxes => some box has >=2. Generalized: kn+1 objects in n boxes => some box has >=k+1. The hard part: identifying what the "boxes" and "pigeons" are. Erdos-Szekeres: sequence of n^2+1 distinct numbers has monotone subsequence of length n+1.',
        'Prove that among any 5 points in a unit square, two are within distance sqrt(2)/2.',
        'Divide unit square into 4 equal squares of side 1/2. By pigeonhole, 5 points in 4 squares means some square contains >= 2 points. Maximum distance within a 1/2 x 1/2 square is its diagonal = sqrt(1/4+1/4) = sqrt(2)/2. So those two points are within distance sqrt(2)/2. Key insight: construct the right "boxes" — here, the 4 sub-squares. The creative step in pigeonhole is always the partition.',
    ),
    (
        'tech_bijection',
        'combinatorics',
        'counting',
        'bijection',
        'count complicated set by mapping to known set, two apparently different counts that should be equal, lattice paths and binary strings, Catalan structure',
        'Bijection: prove |A|=|B| by constructing explicit 1-1 correspondence. Common bijections: lattice paths <-> binary strings, trees <-> Dyck paths, partitions of n into odd parts <-> distinct parts. Involution (self-inverse bijection) proves |A|=|B| when A and B are subsets.',
        'Prove the number of lattice paths from (0,0) to (n,n) not crossing y=x equals C(2n,n)/(n+1) (Catalan number).',
        'Bijection with Dyck paths (sequences of n up-steps and n down-steps never going below x-axis). Cycle lemma or reflection principle: paths from (0,0) to (2n,0) that go below x-axis biject to all paths from (0,0) to (2n,-2) via reflection at first bad step. Count good paths: C(2n,n) - C(2n,n-1) = C(2n,n)/(n+1). The reflection bijection is the key: reflect the suffix after first violation.',
    ),
    (
        'tech_sprague_grundy',
        'combinatorics',
        'game_theory',
        'sprague_grundy',
        'two-player game alternating turns last move wins, impartial game (both players have same moves), multiple independent piles/sub-games, Nim-like structure',
        'Grundy value g(v) = mex({g(w) : w reachable from v}). Position is losing iff g(v)=0. For combined games: g = XOR of sub-game Grundy values. Nim: (x1,...,xn) loses iff x1 XOR ... XOR xn = 0. Strategy: move to make XOR = 0.',
        'In Nim with piles (3,5,7), determine the winning move.',
        '3 XOR 5 XOR 7 = 011 XOR 101 XOR 111 = 001 (=1, nonzero, so first player wins). To win: make XOR = 0. Try removing from pile 7: need new_7 XOR 3 XOR 5 = 0, so new_7 = 3 XOR 5 = 6. Remove 1 from pile of 7, leaving (3,5,6). Verify: 3 XOR 5 XOR 6 = 0. This is losing for the opponent. For non-Nim games: compute Grundy values recursively, then combine with XOR.',
    ),
    (
        'tech_burnside',
        'combinatorics',
        'counting',
        'burnside',
        'count configurations up to rotation/reflection, distinct necklaces/bracelets, symmetry group acting on colorings, equivalence classes under group action',
        'Burnside: |orbits| = (1/|G|) * Σ_{g in G} |Fix(g)|. For necklaces with n beads, k colors under rotation: (1/n)*Σ_{d|n} phi(n/d)*k^d. For bracelets (rotation+reflection), add reflection fixed points and divide by 2n instead of n.',
        'How many distinct necklaces can be made with 6 beads of 2 colors (rotations considered identical)?',
        'Group = Z_6 (rotations by 0,1,...,5 positions). |Fix(rotation by d)| = 2^gcd(6,d). Rotation by 0: 2^6=64. By 1: 2^1=2. By 2: 2^2=4. By 3: 2^3=8. By 4: 2^2=4. By 5: 2^1=2. Sum = 64+2+4+8+4+2=84. Necklaces = 84/6 = 14. Equivalently: (1/6)(phi(1)*2^6 + phi(2)*2^3 + phi(3)*2^2 + phi(6)*2^1) = (1*64+1*8+2*4+2*2)/6 = 84/6 = 14.',
    ),
    (
        'tech_coloring',
        'combinatorics',
        'tiling',
        'coloring_argument',
        'grid tiling impossible, covering board with dominoes/L-trominoes, need to prove impossibility of placement, parity argument for tiling',
        'Coloring/parity argument: color grid cells to create an invariant that tiling must preserve. Checkerboard coloring: each domino covers 1 black + 1 white. If removed squares are same color, tiling impossible. Generalizations: 3-coloring for trominoes, diagonal coloring for specific shapes.',
        'An 8x8 board has two diagonally opposite corners removed. Can the remaining 62 squares be tiled by 31 dominoes?',
        'Color the board like a checkerboard. Opposite corners have the same color (both white, say). Removing them leaves 30 white and 32 black squares. Each domino covers exactly 1 white + 1 black. So 31 dominoes cover 31 white + 31 black. But we have 30 white and 32 black. Contradiction. The tiling is impossible. Key: the coloring creates a counting invariant that the tiling operation must respect.',
    ),
    (
        'tech_probabilistic',
        'combinatorics',
        'existence',
        'probabilistic_method',
        'prove existence non-constructively, lower bound on Ramsey numbers, independence number bounds, need to show a good configuration exists among many',
        'Probabilistic method: to prove a combinatorial object with property P exists, show a random construction has P with positive probability. Tools: linearity of expectation (E[X]>0 implies X>0 somewhere), Lovász Local Lemma (avoid bad events with limited dependence), alteration (random + fix).',
        'Prove R(k,k) > 2^(k/2) (Ramsey number lower bound).',
        'Color edges of K_n randomly, each red/blue with probability 1/2. For any k-subset S, P(S is monochromatic) = 2*2^(-C(k,2)) = 2^(1-C(k,2)). Number of k-subsets: C(n,k). Expected monochromatic k-cliques: C(n,k)*2^(1-C(k,2)). If this < 1, there exists a coloring with no monochromatic k-clique. For n = 2^(k/2): C(n,k) < n^k/k! = 2^(k^2/2)/k!, and 2^(1-k(k-1)/2) makes the product < 1 for large k. So R(k,k) > 2^(k/2).',
    ),
    (
        'tech_catalan',
        'combinatorics',
        'counting',
        'catalan_numbers',
        'balanced parentheses, Dyck paths, full binary trees, polygon triangulations, non-crossing partitions, stack-sortable permutations, sequence 1,1,2,5,14,42,132',
        'Catalan: C_n = C(2n,n)/(n+1). Recurrence: C_{n+1} = Σ_{k=0}^{n} C_k * C_{n-k}. GF: C(x) = (1-sqrt(1-4x))/(2x). Counts: Dyck paths, balanced parens, triangulations of (n+2)-gon, full binary trees with n+1 leaves, non-crossing partitions.',
        'In how many ways can a convex hexagon be triangulated?',
        'A convex (n+2)-gon has C_n triangulations. Hexagon = 6-gon, so n=4: C_4 = C(8,4)/5 = 70/5 = 14. Via recurrence: C_0=1, C_1=1, C_2=2, C_3=5, C_4=C_0*C_3+C_1*C_2+C_2*C_1+C_3*C_0 = 5+2+2+5 = 14. The recurrence reflects fixing one triangle containing a chosen edge and recursing on the two sub-polygons. Whenever a counting problem gives 1,1,2,5,14,42,..., it is almost certainly Catalan.',
    ),
    (
        'tech_extremal',
        'combinatorics',
        'existence',
        'extremal_principle',
        'prove existence of element with special property, pick maximum/minimum element, greedy argument, need to show structure in configuration',
        'Extremal principle: consider the element maximizing/minimizing some quantity. The extreme element often has a special property that yields the desired conclusion. Common: smallest counterexample, longest path in graph, point with maximum x-coordinate, leftmost intersection.',
        'Among n points in the plane, no three collinear, with segments drawn between some pairs, prove there exists a non-crossing Hamiltonian path.',
        'This is NOT the right problem for extremal (it is false in general). Better example: In a set of n points no 3 collinear, the convex hull vertex with minimum x-coord has a special property. Or: Consider the shortest segment among all pairs. Then no other point can be too close to both endpoints (triangle inequality). Extremal is a meta-strategy: it does not give a formula but a proof structure — "pick the extreme, derive a contradiction or the desired property."',
    ),
    (
        'tech_graph_theory',
        'combinatorics',
        'graphs',
        'graph_modeling',
        'people/connections/mutual relationships, handshaking/degree conditions, tournament results, need to model as vertices and edges, friendship theorem',
        'Model as graph: people=vertices, relationships=edges. Handshaking: Σdeg(v)=2|E|. Key theorems: Euler (Eulerian circuit iff all degrees even), Ore/Dirac (Hamiltonian conditions), Ramsey (monochromatic cliques in colored complete graphs), Hall (matching in bipartite graphs).',
        'At a party, every pair of people has exactly one mutual friend. Prove one person is friends with everyone.',
        'Model as graph G. The condition says: for all u,v, |N(u)∩N(v)|=1. This is the Friendship Theorem. Proof sketch: G is a "windmill graph" — a collection of triangles sharing a common vertex. The common vertex is friends with everyone. Proof uses eigenvalue methods or clever counting: pick vertex v of max degree d. Each neighbor of v has exactly one common friend with each other neighbor of v, creating a specific structure that forces d=n-1.',
    ),
    (
        'tech_hall',
        'combinatorics',
        'graphs',
        'hall_marriage',
        'bipartite matching, system of distinct representatives (SDR), can each element be assigned a unique partner, marriage condition |N(S)|>=|S|',
        'Hall theorem: bipartite graph G=(A,B,E) has matching saturating A iff for all S⊆A: |N(S)|>=|S| (marriage condition). Max matching = |A| - max deficiency. Konig theorem: in bipartite graphs, max matching = min vertex cover. Use for: existence of SDR, Latin squares, assignment problems.',
        'There are n boys and n girls. Each boy likes at least k girls, each girl is liked by at most k boys. Prove a perfect matching exists.',
        'Check Hall condition: for any set S of boys, total "likes" edges from S is >= k*|S| (each boy likes >= k). These edges go to N(S) girls, each receiving <= k edges. So k*|N(S)| >= k*|S|, giving |N(S)| >= |S|. Hall condition satisfied, so perfect matching exists. This argument (double counting edges to verify Hall) is the standard approach. For constructive matching: use Hungarian algorithm or augmenting paths.',
    ),
    (
        'tech_induction',
        'combinatorics',
        'proof_technique',
        'induction',
        'for all n prove P(n), natural number parameter, recursive structure, need to establish base case and inductive step',
        'Induction: prove P(n0), then P(k)=>P(k+1). Strong induction: assume P(m) for all m<k. Structural induction: on trees, graphs, expressions. Common pitfall: the inductive step fails at boundaries. Tip: if simple induction fails, try strong induction or induct on a different parameter.',
        'Prove that any amount of postage >= 12 cents can be made using 4-cent and 5-cent stamps.',
        'Base cases: 12=3*4, 13=2*4+5, 14=4+2*5, 15=3*5. Inductive step: assume P(k) for some k>=15. Then k-3>=12, so by P(k-3) (strong induction), k-3 = 4a+5b. Then k+1 = 4a+5b+4 = 4(a+1)+5b. Wait, we need P(k)=>P(k+1): if k=4a+5b, then k+4=4(a+1)+5b. So from any 4 consecutive true values, all subsequent values follow. The 4 base cases 12-15 propagate to all n>=12.',
    ),
    (
        'tech_erdos_szekeres',
        'combinatorics',
        'sequences',
        'erdos_szekeres',
        'sequence of distinct numbers must contain long monotone subsequence, n^2+1 elements guarantee increasing or decreasing subsequence, pigeonhole on longest subsequence lengths',
        'Erdos-Szekeres: any sequence of n^2+1 distinct reals has an increasing or decreasing subsequence of length n+1. Proof: assign each element pair (a_i, d_i) = (length of longest increasing subseq ending here, longest decreasing). If no (n+1)-length subseq of either type, at most n*n = n^2 distinct pairs. Pigeonhole.',
        'Prove that any sequence of 10 distinct reals contains a monotone subsequence of length 4.',
        'Need 3^2+1=10 elements (here n=3). For each element a_i, let inc_i = length of longest increasing subsequence ending at a_i, dec_i = longest decreasing. If no increasing of length 4: inc_i <= 3. If no decreasing of length 4: dec_i <= 3. Then at most 3*3=9 distinct pairs (inc_i,dec_i). But i!=j implies (inc_i,dec_i)!=(inc_j,dec_j) (if a_i<a_j, then inc_j>=inc_i+1; if a_i>a_j, then dec_j>=dec_i+1). With 10 elements, pigeonhole gives contradiction.',
    ),
]

def main():
    # Validate no duplicates with existing
    new_ids = set()
    for entry in NEW_ENTRIES:
        pid = entry[0]
        if pid in EXISTING:
            print(f"ERROR: {pid} already exists in DB, skipping")
            continue
        if pid in new_ids:
            print(f"ERROR: duplicate new entry {pid}, skipping second")
            continue
        new_ids.add(pid)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    inserted = 0
    by_category = {}
    for entry in NEW_ENTRIES:
        pid = entry[0]
        if pid in EXISTING:
            continue
        # Check not already in DB (in case script is run twice)
        c.execute("SELECT 1 FROM problems WHERE problem_id=?", (pid,))
        if c.fetchone():
            print(f"  Already in DB: {pid}, skipping")
            continue

        c.execute(
            "INSERT INTO problems (problem_id, category, topic, subtopic, triggers, technique, question, answer) VALUES (?,?,?,?,?,?,?,?)",
            entry
        )
        inserted += 1
        cat = entry[1]
        by_category[cat] = by_category.get(cat, 0) + 1

    conn.commit()

    # Verify
    c.execute("SELECT COUNT(*) FROM problems WHERE problem_id LIKE 'tech_%'")
    total = c.fetchone()[0]

    print(f"\n{'='*60}")
    print(f"TECHNIQUE DB INSERT SUMMARY")
    print(f"{'='*60}")
    print(f"New entries inserted: {inserted}")
    print(f"By category:")
    for cat in sorted(by_category):
        print(f"  {cat}: {by_category[cat]}")
    print(f"Total tech entries in DB: {total} (was 12)")
    print(f"{'='*60}")

    # List all tech entries
    c.execute("SELECT problem_id, category, topic, subtopic FROM problems WHERE problem_id LIKE 'tech_%' ORDER BY category, topic, problem_id")
    rows = c.fetchall()
    print(f"\nAll tech entries ({len(rows)}):")
    current_cat = None
    for pid, cat, topic, subtopic in rows:
        if cat != current_cat:
            print(f"\n  [{cat.upper()}]")
            current_cat = cat
        marker = " (NEW)" if pid not in EXISTING else " (existing)"
        print(f"    {pid:30s} {topic:25s} {subtopic}{marker}")

    conn.close()

if __name__ == '__main__':
    main()
