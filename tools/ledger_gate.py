# -*- coding: utf-8 -*-
# 記号を変えたのに台帳を直していないコミットを止めるゲート。
# 使い方: py ledger_gate.py <file.tex> <ledger.md> [<base-rev>]
#   base-rev の既定は HEAD。作業ツリーと base-rev の原稿から記号集合を作り、
#   差があるのに台帳が base-rev から変わっていなければ 1 を返す。
#
# ledger_check.py との違い
#   ledger_check.py は台帳と原稿を突き合わせて「今ある乖離」を出す。台帳の説明文にも
#   記号が現れるので偽陽性が残り、基準値と比べる使い方になる。
#   こちらは原稿の記号集合の「変化」だけを見るので偽陽性がほとんど無い。記号を触って
#   いないコミットでは何も言わない。新しい乖離を作らせないのが役目。
#
# 記号の粒度
#   添字が英字のものは添字ごと区別する（\gamma_D と \gamma は別、r_l と r は別）。
#   数字の添字はまとめる（\mathfrak a_1 も \mathfrak a_6 も \mathfrak a_#）。
#   改名は「消えた記号」と「増えた記号」の対として出る。
import io
import re
import subprocess
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 3:
	print("usage: py ledger_gate.py <file.tex> <ledger.md> [<base-rev>]")
	sys.exit(2)
TEX, LEDGER = sys.argv[1], sys.argv[2]
BASE = sys.argv[3] if len(sys.argv) > 3 else "HEAD"

SKIP = set("""begin end section subsection label ref eqref cite pageref printbibliography
frac tfrac dfrac left right qquad quad text textrm mbox emph textcolor item hline
newcommand renewcommand documentclass usepackage maketitle sum prod int sqrt cdot cdots
ldots vdots dots ast circ colon mid mapsto longmapsto to longrightarrow rightarrow
backslash times oplus pm neq ne leq le geq ge equiv pmod bmod in notin subset subseteq
setminus cup cap langle rangle bigl bigr Bigl Bigr bigg Big big hspace vspace centering
tabular array pmatrix smallmatrix gathered aligned align gather equation substack
operatorname det ker exp log sin cos arg max min deg binom partial infty forall exists
iff implies thiswork nonumber notag par noindent caption matrix mathit mathrm Bigg ni
Transpose C R Q Z N Ps PGL GL SL Sp U rank Im Re pi cdotp phantomsection""".split())

WRAP = "mathcal|mathfrak|mathbb|widetilde|widehat|hat|tilde|dot|bar|overline"
SYM = (r"(?:\\(?:" + WRAP + r")\{[A-Za-z]\}|\\[A-Za-z]+|(?<![A-Za-z\\])[A-Za-z])")
TOK = re.compile(SYM + r"(?:_(?:\{[A-Za-z0-9,+\\-]{1,6}\}|[A-Za-z0-9]))?")


def run(args):
	return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def symbols(text):
	text = re.sub(r"(?<!\\)%.*$", "", text, flags=re.M)
	i = text.find("\\begin{document}")
	if i >= 0:
		text = text[i:]
	text = re.sub(r"\\(" + WRAP + r")\s+([A-Za-z])(?![A-Za-z])", r"\\\1{\2}", text)
	out = collections.Counter()
	for m in TOK.finditer(text):
		tok = m.group(0)
		head = re.match(r"\\([A-Za-z]+)", tok)
		if head and head.group(1) in SKIP:
			continue
		tok = re.sub(r"_\{?[0-9]+\}?$", "_#", tok)
		out[tok] += 1
	return out


base_tex = run(["git", "show", "%s:%s" % (BASE, TEX)])
if base_tex.returncode != 0:
	print("base の原稿を読めない: %s:%s" % (BASE, TEX))
	sys.exit(2)
now = symbols(io.open(TEX, encoding="utf-8").read())
old = symbols(base_tex.stdout)

added = sorted(k for k in now if k not in old)
removed = sorted(k for k in old if k not in now)
ledger_touched = run(["git", "diff", "--quiet", BASE, "--", LEDGER]).returncode != 0

if not added and not removed:
	print("記号集合に変化なし。台帳の更新は不要。")
	sys.exit(0)

print("== 記号集合が変わった（対 %s）" % BASE)
if added:
	print("\n   増えた %d" % len(added))
	for k in added:
		print("      %-20s ×%d" % (k, now[k]))
if removed:
	print("\n   消えた %d" % len(removed))
	for k in removed:
		print("      %-20s (旧 ×%d)" % (k, old[k]))

print("\n== 台帳 %s: %s" % (LEDGER, "更新あり" if ledger_touched else "**更新なし**"))
if ledger_touched:
	print("\nOK: 記号を変えて台帳も更新している。")
	sys.exit(0)
print("""
NG: 記号集合が変わったのに台帳が更新されていない。
    改名なら「消えた」と「増えた」の対を台帳に反映し、旧記号は廃止として理由付きで残す。
    追加なら台帳に行を足す。削除なら該当行を廃止として印を付ける。""")
sys.exit(1)
