# -*- coding: utf-8 -*-
# 注意: 冒頭の定数(対象パス・承認/標準語リスト)はプロジェクトごとに書き換えて使う。
# 造語候補スキャン: 地の文の「the + 2〜3語」複合名詞句を数え、
# 承認済み・常用語のみの句を除いた低頻度句を列挙する。
import io
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
P = r"D:\Workspace\TeX\Nagamine\paper-obstruction\paper-obstruction.tex"

APPROVED = [
	"distinguished collection", "lattice perturbation", "obstruction module",
	"moving integral set", "negative support", "support famil", "fake exponent",
	"block-sum famil", "shared-column famil", "repeated-row famil", "support fiber",
	"support cell", "boundary monomial", "support monomial", "comparison ideal",
	"coefficient space", "solution space", "inverse system", "standard pair",
	"lattice rank", "column matroid", "gale row", "gale linear", "gale matrix",
	"relation lattice", "affine semigroup", "term order", "initial ideal",
	"initial system", "initial series", "initial term", "initial exponent",
	"leading monomial", "logarithmic coefficient", "logarithmic term", "logarithm polynomial",
	"canonical series", "canonical formal", "canonical lift", "canonical solution",
	"nilsson series", "nilsson solution", "direction cone", "convergence domain",
	"half-plane", "line arrangement", "sector label", "boundary ray", "parallel class",
	"holonomic rank", "holomorphic solution", "indicial ideal", "indicial component",
	"euler operator", "toric ideal", "toric operator", "weyl algebra",
	"colon ideal", "polynomial model", "boundary matrix", "regular sequence",
	"complete intersection", "exact sequence", "spectral", "koszul complex",
	"grobner basis", "gr\\u00f6bner basis", "grobner cone", "grobner fan", "hilbert series",
	"hilbert function", "stanley--reisner", "taylor relation", "taylor resolution",
	"transport equation", "least layer", "weight class", "circuit support",
	"lattice basis", "lattice binomial", "lattice coordinate", "lattice point",
	"lattice shift", "quotient ring", "quotient map", "polynomial ring",
	"power series", "maximal ideal", "monomial ideal", "monomial order",
	"boundary presentation", "ambient realization", "ambient perturbation",
	"intrinsic perturbation", "coefficient series", "constant term",
	"recession ray", "row span", "base exponent", "boundary class",
]
COMMON = set("""a an and of in on for with to by at the this that these those is are was be been
first second third last next same other two three four five one only such all every each
new given fixed chosen following preceding above below right left open closed nonzero zero
nonempty finite infinite common corresponding resulting remaining displayed asserted stated
proof theorem lemma corollary proposition remark definition example section subsection
case cases part parts sense form way order number numbers set sets map maps
""".split())

text = io.open(P, encoding="utf-8").read().split("\\begin{document}", 1)[1]
text = text.split("\\begin{thebibliography}")[0]
# 数式・コマンドを除去して地の文だけにする
text = re.sub(r"\\\((?:[^\\]|\\[^()])*?\\\)", " MATH ", text)
text = re.sub(r"\\\[(?:.|\n)*?\\\]", " MATH ", text)
text = re.sub(r"\\begin\{(equation|align|aligned|array|cases|bmatrix|split)\*?\}(?:.|\n)*?\\end\{\1\*?\}", " MATH ", text)
text = re.sub(r"\\[A-Za-z]+(\[[^\]]*\])?(\{[^{}]*\})*", " ", text)
text = text.lower()

words = re.findall(r"[a-z][a-z\-]+", text)
cand = Counter()
for n in (2, 3):
	for i in range(len(words) - n):
		if words[i] != "the":
			continue
		gram = words[i + 1:i + 1 + n]
		if any(w in COMMON or w == "math" for w in gram):
			continue
		if len(gram[-1]) < 4:
			continue
		phrase = " ".join(gram)
		if any(a in phrase for a in APPROVED):
			continue
		cand[phrase] += 1

print("=== 「the + 複合名詞句」で承認外・低頻度(3回以下)===")
for ph, c in sorted(cand.items(), key=lambda t: (t[1], t[0])):
	if c <= 3:
		print(f"{c:3d}  the {ph}")
