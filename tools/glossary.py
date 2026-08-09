# -*- coding: utf-8 -*-
# 注意: 冒頭の定数(対象パス・承認/標準語リスト)はプロジェクトごとに書き換えて使う。
# 単語帳: 地の文の技術的名詞句(2〜3語)を全数抽出し、出典で分類する。
# 出力: 評価/glossary-2026-08-09.md
import io
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
P = r"D:\Workspace\TeX\Nagamine\paper-obstruction\paper-obstruction.tex"
OUT = r"D:\Workspace\TeX\Nagamine\評価\glossary-2026-08-09.md"
PRIOR = r"C:\Users\toppo\AppData\Local\Temp\claude\D--Workspace-TeX-Nagamine\d08b1097-5bc4-4001-90da-af937177ecfa\scratchpad\encheck\priorvocab.md"

APPROVED = ["distinguished collection", "lattice perturbation", "lattice-perturbation obstruction module",
	"moving integral set", "moving-binary", "support fiber", "support cell", "block-sum family",
	"shared-column family", "repeated-row family", "fake exponent", "negative support family",
	"negative support", "moving integral", "obstruction module", "fake-exponent sector"]

# 標準数学用語(教科書レベル)。部分一致で判定する。
STANDARD = """affine semigroup ambient ring apolar pairing artinian ring associated graded betti number
buchberger criterion canonical series chain complex circuit support cohen--macaulay column matroid
complete intersection convergence domain connected component convex cone coordinate ring
direct sum dual basis euler operator exact sequence exponential polynomial falling factorial
formal power series free module free resolution frobenius method generic weight graded module
grobner basis gr\u00f6bner basis grobner cone gr\u00f6bner cone grobner fan gr\u00f6bner fan half-plane half-space
hilbert function hilbert series holonomic rank holomorphic function homogeneous ideal hypergeometric series
hypergeometric system indicial ideal initial ideal initial form initial series initial term inverse system
koszul complex krull dimension lattice basis lattice point laurent polynomial leading monomial
lefschetz linear form linear functional local ring localization matroid maximal ideal minimal generator
minimal prime monomial curve monomial ideal monomial order nilsson series nilsson solution
parallel class polynomial ring power series primary ideal prime ideal quotient ring rational point
regular holonomic regular sequence relation lattice simplicial complex simply connected singular locus
solution space spectral sequence stanley--reisner standard monomial standard pair strongly convex
symmetric difference system of parameters taylor resolution tensor product term order toric ideal
torus translate uniform matroid unit ideal weyl algebra well-ordered zariski closure
recession ray dual cone row span integer kernel saturation homogeneous system boundary ray
trigonometric polynomial mean square identity theorem normal convergence absolute convergence
open set closed set interior closure boundary lattice rank""".split("\n")
STANDARD = set(w.strip() for chunk in STANDARD for w in [chunk] if w.strip())
STANDARD_FLAT = " ".join(STANDARD)

COMMON = set("""a an and of in on for with to by at as the this that these those there then than is are was were
be been being have has had do does did can could may might must shall should will would not no nor
first second third last next same other another such all every each both few many much more most
one two three four five six seven eight nine ten eleven twelve zero
new given fixed chosen following preceding above below right left open closed nonzero
nonempty finite infinite common corresponding resulting remaining displayed asserted stated smallest largest
least greatest lower upper least whole entire proper strict distinct unique only single
case cases part parts sense form forms way order number numbers set sets map maps
proof theorem lemma corollary proposition remark definition example section subsection paper
we our it its they their them he she his her which whose what when where how why if because since
so hence thus therefore moreover also even after before between among within outside inside
holds hold gives give given shows show proves prove denote denotes write writes let put define defines
suppose assume take choose consider obtain yield yields follows follow apply applies applied
belongs belong contains contain lies lie exists exist occurs occur equals equal
respectively precisely exactly namely called denoted defined obtained
element elements side sides hand term terms value values
""".split())

text_all = io.open(P, encoding="utf-8").read()
head, _, body0 = text_all.partition("\\begin{document}")
body0 = body0.split("\\begin{thebibliography}")[0]
lines = body0.split("\n")
off = head.count("\n") + 1  # begin{document} の行番号ベース

# \emph 定義語の抽出(語のみ。記号定義は除く)
emph_terms = set()
for m in re.finditer(r"\\emph\{([^{}\\]+)\}", body0):
	t = m.group(1).strip().lower()
	if re.fullmatch(r"[a-z][a-z\- ]+", t):
		emph_terms.add(t)

prior = set()
try:
	pv = io.open(PRIOR, encoding="utf-8").read().lower()
	for m in re.finditer(r"^- ([a-z][a-z\- ()]+?)(?:\s*\(|$)", pv, re.M):
		prior.add(m.group(1).strip())
except OSError:
	pass

occ = defaultdict(list)
for li, raw in enumerate(lines):
	s = raw
	s = re.sub(r"%.*", " ", s)
	s = re.sub(r"\\\((?:[^\\]|\\[^()])*?\\\)", " MATH ", s)
	s = re.sub(r"\\[A-Za-z]+(\[[^\]]*\])?(\{[^{}]*\})?", " ", s)
	words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", s.lower())
	for n in (2, 3):
		for i in range(len(words) - n + 1):
			g = words[i:i + n]
			if any(w in COMMON or w == "math" or len(w) < 3 for w in g):
				continue
			occ[" ".join(g)].append(off + li)

def canon(t):
	# 複数形の素朴な畳み込み
	ws = t.split()
	last = ws[-1]
	if last.endswith("ies"):
		alt = last[:-3] + "y"
	elif last.endswith("s") and not last.endswith("ss"):
		alt = last[:-1]
	else:
		return t
	alt_t = " ".join(ws[:-1] + [alt])
	return alt_t if alt_t in occ else t

merged = defaultdict(list)
for t, ls in occ.items():
	merged[canon(t)].extend(ls)

def classify(t):
	if any(a in t or t in a for a in APPROVED):
		return "承認済み"
	if t in emph_terms or any(t in e or e in t for e in emph_terms if len(e) > 6):
		return "emph定義"
	if t in STANDARD or any(t in s or s in t for s in STANDARD if len(s) > 8):
		return "標準"
	if t in prior or any(t in p or p in t for p in prior if len(p) > 8):
		return "先行研究"
	return "要審査"

buckets = defaultdict(list)
for t, ls in merged.items():
	if len(t) < 8:
		continue
	buckets[classify(t)].append((t, sorted(set(ls))))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
	f.write("# 単語帳(2026-08-09)paper-obstruction.tex の技術的名詞句全数\n\n")
	f.write("分類基準: 承認済み(CLAUDE.md)/ emph定義(本文で定義)/ 標準(教科書用語)/ 先行研究(OS25・DMM12 原文で確認)/ 要審査(統廃合候補)。\n\n")
	for b in ("要審査", "先行研究", "emph定義", "承認済み", "標準"):
		items = sorted(buckets[b], key=lambda x: (-len(x[1]), x[0]))
		f.write(f"\n## {b}({len(items)}語)\n\n")
		for t, ls in items:
			lstr = ",".join(f"L{x}" for x in ls[:6]) + ("..." if len(ls) > 6 else "")
			f.write(f"- **{t}** ×{len(ls)} ({lstr})\n")
print("emph定義語:", len(emph_terms), "/ 先行研究語彙:", len(prior))
for b in ("要審査", "先行研究", "emph定義", "承認済み", "標準"):
	print(b, len(buckets[b]))
print("wrote", OUT)
