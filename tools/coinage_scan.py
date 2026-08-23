# -*- coding: utf-8 -*-
# 造語候補スキャン: 地の文の「the + 2〜3語」複合名詞句を数え、
# 承認済み・常用語のみの句を除いた低頻度句を列挙する。
#
# 使い方: py coinage_scan.py <tex> [承認語ファイル]
#   承認語ファイルは1行1語。下の BASELINE に **追加** される(置換ではない)。
#
# BASELINE はどの論文でも標準語といえるものだけを持つ。プロジェクト固有の承認語は
# 外部ファイルで渡す。人間向けの正はプロジェクトの規約ファイル(CLAUDE.md 等)で、
# 外部ファイルはその機械可読な鏡像にする。
#
# **承認語は造語候補から除外される。**だから廃止した語がここに残ると、その語の
# 再導入を検出できない。2026-08-22 に廃止済みの `lattice perturbation` が、
# 2026-08-24 に駆逐済み・プロジェクト固有の27語が残っているのが見つかった。
# 用語を廃止したら banned リストに足すだけでなく、承認語からも消す。
# 死語の検出は下の「本文に出ない承認語」節が行う。
import io
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 2:
	print("使い方: py coinage_scan.py <tex> [承認語ファイル]")
	sys.exit(2)
P = sys.argv[1]

BASELINE = [
	"negative support", "support famil", "fake exponent",
	"coefficient space", "solution space", "inverse system", "standard pair",
	"lattice rank", "column matroid",
	"affine semigroup", "term order", "initial ideal",
	"initial system", "initial series", "initial term", "initial exponent",
	"logarithmic coefficient", "logarithmic term",
	"canonical series", "canonical solution",
	"nilsson series", "nilsson solution", "direction cone", "convergence domain",
	"half-plane", "line arrangement", "boundary ray", "parallel class",
	"holonomic rank", "holomorphic solution", "indicial ideal", "indicial component",
	"euler operator", "toric ideal", "toric operator", "weyl algebra",
	"colon ideal", "regular sequence",
	"complete intersection", "exact sequence", "spectral", "koszul complex",
	"grobner basis", "gr\\u00f6bner basis", "grobner cone", "grobner fan", "hilbert series",
	"hilbert function", "stanley--reisner", "taylor relation", "taylor resolution",
	"transport equation", "least layer", "weight class",
	"lattice basis", "lattice binomial", "lattice coordinate", "lattice point",
	"lattice shift", "quotient ring", "quotient map", "polynomial ring",
	"power series", "maximal ideal", "monomial ideal", "monomial order",
	"boundary presentation",
	"coefficient series", "constant term",
	"recession ray", "row span", "boundary class",
]

PROJECT = []
if len(sys.argv) > 2:
	PROJECT = [l.strip().lower() for l in io.open(sys.argv[2], encoding="utf-8")
	           if l.strip() and not l.lstrip().startswith("#")]
APPROVED = BASELINE + PROJECT

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

# 本文に一度も出ない承認語を報告する。承認語は造語候補から除外されるので、
# 死語が残るとその語の再導入を検出できない(2026-08-24 に4語が死語だった)。
# baseline はどの論文でも標準といえる語の集合なので、当該論文に出ないのは普通である。
# 数えるだけにして、外すべきなのは **プロジェクト固有の死語** だと分かるようにする。
dead_project = sorted(a for a in PROJECT if a not in text)
dead_baseline = sorted(a for a in BASELINE if a not in text and a not in PROJECT)
print()
print("=== 本文に出ないプロジェクト承認語 %d 件(承認リストから外す)===" % len(dead_project))
for a in dead_project:
	print("     %s" % a)
if not dead_project:
	print("     なし")
print("(baseline 側で本文に出ないのは %d 件。baseline は論文横断なので普通であり、外す必要はない)"
      % len(dead_baseline))
