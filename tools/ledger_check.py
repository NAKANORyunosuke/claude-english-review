# -*- coding: utf-8 -*-
# 記号台帳と原稿の突き合わせ。
# 使い方: py ledger_check.py <file.tex> <ledger.md>
#
# 出すもの
#   1. 台帳にあるが原稿に無い記号  — 改名・削除したのに台帳を直し忘れた候補
#   2. 原稿にあるが台帳に無い記号  — 導入したのに台帳へ載せ忘れた候補
#
# 台帳が「廃止」「解消済み」「旧記号」と書いている行の記号は、原稿に無いのが正しい。
# その行の記号は 1 から除き、別枠で「廃止として記録済み」に数える。
#
# 完全な判定はできない。台帳は説明文の中にも記号を書くので、2 には局所的な
# ダミー変数が並ぶ。基準値を決めて、増えていないことを見る使い方を想定している。
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 3:
	print("usage: py ledger_check.py <file.tex> <ledger.md>")
	sys.exit(2)
TEX, LEDGER = sys.argv[1], sys.argv[2]

SKIP = set("""begin end section subsection label ref eqref cite pageref printbibliography
frac tfrac dfrac left right qquad quad text textrm mbox emph textcolor item hline
newcommand renewcommand documentclass usepackage maketitle sum prod int sqrt cdot cdots
ldots vdots dots ast circ colon mid mapsto longmapsto to longrightarrow rightarrow
backslash times oplus pm neq ne leq le geq ge equiv pmod bmod in notin subset subseteq
setminus cup cap langle rangle bigl bigr Bigl Bigr bigg Big big hspace vspace centering
tabular array pmatrix smallmatrix gathered aligned align gather equation substack
overline bar operatorname det ker exp log sin cos arg max min deg binom partial infty
forall exists iff implies thiswork nonumber notag par noindent caption matrix
mathit mathrm widehat overline Bigg ni bigcup bigcap prod_ sum_ e vt per
Transpose C R Q Z N Ps PGL GL SL Sp U rank Im Re pi cdotp phantomsection""".split())

PATS = [
	r"\\(?:mathcal|mathfrak|mathbb|widetilde|widehat|mathit)\s*\{[A-Za-z]\}",
	r"\\(?:hat|tilde|dot|bar)\s*\{?[A-Za-z]\}?",
	r"\\[A-Za-z]+",
	r"(?<![A-Za-z\\])[A-Za-z]_",
]


WRAP = "mathcal|mathfrak|mathbb|widetilde|widehat|mathit|hat|tilde|dot|bar|overline"


def normalize(text):
	"""\\mathcal I と \\mathcal{I} を同じ形に揃える。"""
	return re.sub(r"\\(" + WRAP + r")\s+([A-Za-z])(?![A-Za-z])", r"\\\1{\2}", text)


def symbols(text):
	"""基底記号の集合と出現回数を返す。"""
	text = normalize(text)
	c = collections.Counter()
	for p in PATS:
		for m in re.finditer(p, text):
			tok = re.sub(r"\s", "", m.group(0))
			if re.fullmatch(r"\\[A-Za-z]+", tok) and tok[1:] in SKIP:
				continue
			c[tok] += 1
	return c


src = io.open(TEX, encoding="utf-8").read().split("\n")
start = next((i for i, l in enumerate(src) if "\\begin{document}" in l), 0)
body = "\n".join(re.sub(r"(?<!\\)%.*$", "", s) for s in src[start:])
in_tex = symbols(body)

RETIRED = re.compile(r"廃止|解消済み|旧記号|旧 |使わない|不可")
# 他文書との比較表は、その文書の記号を並べるので対象外にする
OTHER = re.compile(r"比較|Chapter\s*1|Chapter\s*3|参考|平行概念")
led_live, led_dead = collections.Counter(), collections.Counter()
skip_section = False
for line in io.open(LEDGER, encoding="utf-8"):
	if line.lstrip().startswith("#"):
		skip_section = bool(OTHER.search(line))
		continue
	if skip_section or not line.lstrip().startswith("|"):
		continue
	c = symbols(line)
	if RETIRED.search(line):
		led_dead.update(c)
	else:
		led_live.update(c)

only_ledger = sorted(k for k in led_live if in_tex.get(k, 0) == 0 and k not in led_dead)
only_tex = sorted(k for k, n in in_tex.items() if n >= 2 and k not in led_live and k not in led_dead)

print("== 原稿の基底記号 %d / 台帳の現役 %d / 台帳が廃止と記録 %d"
      % (sum(1 for k, n in in_tex.items() if n >= 2), len(led_live), len(led_dead)))

print("\n== 台帳にあるが原稿に無い（改名・削除の反映漏れの候補） %d" % len(only_ledger))
for k in only_ledger:
	print("   %s" % k)

print("\n== 原稿にあるが台帳に無い（記載漏れの候補） %d" % len(only_tex))
for k in only_tex:
	print("   %-18s ×%d" % (k, in_tex[k]))
