# -*- coding: utf-8 -*-
# 記号を全数抽出して、初出行と定義行を突き合わせる。フェーズ B の中核。
# 使い方: py symbol_depgraph.py <tex> [最小出現回数]
#
# なぜ要るか
#   分割読み（フェーズ A）では、担当チャンクの外にある定義行が見えない。だから
#   「初出が定義より前にある記号」と「二重定義」は原理的に取りこぼす。全文で1回
#   やる必要がある。PLAYBOOK フェーズ B と templates/r-check-chunk.md 手順5。
#
#   手で記号を列挙してはいけない。記号として意識していない文字が表に載らず、
#   突き合わせの対象にすらならない。2026-08-22 の実測では、台帳の大域予約に
#   載っていない衝突が24件出た。
#
# 判定
#   未定義       定義の合図が見つからない
#   前方参照     初出が定義より前
#   定義候補複数  定義の合図が2箇所以上（二重定義の疑い）
#   正順         初出＝定義
#
# 出力は候補である。走る添字（i, j, k, a）は「定義される記号」ではないので、
# 単独文字の行は目視で落とす。残ったものを本文と照合してから報告する。
import io
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

STRUCT = set("""
left right frac begin end label ref eqref cite text mid middle bigl bigr Bigl Bigr
displaystyle mathrm mathbb mathcal mathsf mathfrak mathscr boldsymbol operatorname
widetilde overline underline hat tilde bar vec qquad quad notag nonumber substack
cases array bmatrix pmatrix aligned align equation lemma theorem proposition corollary
remark definition proof itemize enumerate item centering caption tabular figure table
small texorpdfstring newcommand def renewcommand hline par noindent emph big Big
""".split())

RELOP = set("""
in notin subseteq subsetneq supseteq subset supset leq geq ne neq to longrightarrow
mapsto longmapsto simeq cong equiv sim approx sum prod bigcup bigcap bigoplus coprod
cdot cdots ldots dots vdots ddots setminus cup cap sqcup times pm mp circ oplus otimes
Longrightarrow Longleftrightarrow implies iff forall exists varnothing emptyset
langle rangle lvert rvert lfloor rfloor lceil rceil triangle mathbin xrightarrow
colon perp parallel nparallel star ast prec succ preceq succeq geqslant leqslant
""".split())

OPS = set("""
rank dim deg gcd lcm Tor Ext Hom Ann Hilb coker ker im Span Supp Sing pr diag inw
nsupp gr Sol tp log exp min max lim int binom sqrt sup inf det tr Re Im ind coeff
rowspan GL Ker mov const last id ord
""".split())

NUMSYS = set("C Z N R Q".split())
EXCLUDE = STRUCT | RELOP | OPS | NUMSYS

MACRO = re.compile(r"\\([A-Za-z]+)")
LETTER = re.compile(r"(?<![A-Za-z\\])([A-Za-z])(?![A-Za-z])")

INLINE = [re.compile(r"\\\((.*?)\\\)", re.S), re.compile(r"\\\[(.*?)\\\]", re.S)]
DISPLAY_OPEN = re.compile(r"\\\[|\\begin\{(?:equation|align|aligned|array|cases|bmatrix|split|gather)\*?\}")
DISPLAY_CLOSE = re.compile(r"\\\]|\\end\{(?:equation|align|aligned|array|cases|bmatrix|split|gather)\*?\}")

# 導入儀式。合図が記号の直前 WINDOW 文字以内にあるときだけ定義とみなす。
# 行のどこかに合図があるだけで拾うと偽陽性だらけになる（\cN の定義候補が6行出た）。
WINDOW = 40
CUE = re.compile(
	r"\b(?:[Dd]efine|[Pp]ut|[Ss]et|[Ww]rite|[Ll]et|[Cc]hoose|[Aa]bbreviate|[Rr]etain|"
	r"[Ww]e call|[Dd]enote by|use the notation|[Tt]here (?:is|are)|"
	r"the existence of|[Ff]ix)\b"
)


def symbols_in(text):
	out = set()
	for m in MACRO.finditer(text):
		if m.group(1) not in EXCLUDE:
			out.add("\\" + m.group(1))
	for m in LETTER.finditer(MACRO.sub(" ", text)):
		if m.group(1) not in NUMSYS:
			out.add(m.group(1))
	return out


def occurrences(line, sym):
	if sym.startswith("\\"):
		return [m.start() for m in re.finditer(re.escape(sym) + r"(?![A-Za-z])", line)]
	masked = MACRO.sub(lambda m: " " * len(m.group(0)), line)
	return [m.start() for m in re.finditer(r"(?<![A-Za-z\\])" + re.escape(sym) + r"(?![A-Za-z])", masked)]


def main(path, min_count=2):
	lines = io.open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
	try:
		start = next(i for i, l in enumerate(lines) if "\\begin{document}" in l)
	except StopIteration:
		start = 0
	try:
		end = next(i for i, l in enumerate(lines) if "\\begin{thebibliography}" in l)
	except StopIteration:
		end = len(lines)

	first, count, depth = {}, defaultdict(int), 0
	for idx in range(start, end):
		raw = lines[idx]
		if raw.lstrip().startswith("%"):
			continue
		opens, closes = len(DISPLAY_OPEN.findall(raw)), len(DISPLAY_CLOSE.findall(raw))
		if depth > 0:
			chunks = [raw]                      # ディスプレイの内側は行全体が数式
		else:
			chunks = [c for p in INLINE for c in p.findall(raw)]
			if opens > closes:
				chunks.append(DISPLAY_OPEN.split(raw)[-1])
		depth = max(0, depth + opens - closes)
		for ch in chunks:
			for s in symbols_in(ch):
				count[s] += 1
				first.setdefault(s, idx + 1)

	defs = defaultdict(list)
	for idx in range(start, end):
		raw = lines[idx]
		if raw.lstrip().startswith("%"):
			continue
		cues = [m.end() for m in CUE.finditer(raw)]
		if not cues:
			continue
		for s in count:
			if any(0 <= pos - c <= WINDOW for pos in occurrences(raw, s) for c in cues):
				defs[s].append(idx + 1)

	out = []
	for s, c in count.items():
		if c < min_count:
			continue
		d = defs.get(s, [])
		if not d:
			verdict = "未定義"
		elif first[s] < d[0]:
			verdict = "前方参照"
		elif len(d) >= 2:
			verdict = "定義候補複数"
		else:
			verdict = "正順"
		out.append((verdict, s, c, first[s], d[:6]))

	order = {"未定義": 0, "前方参照": 1, "定義候補複数": 2, "正順": 3}
	out.sort(key=lambda r: (order[r[0]], -r[2]))

	print("対象 %s: 本文 L%d--L%d、出現%d回以上の基底記号 %d 個"
	      % (path, start + 1, end, min_count, len(out)))
	print("走る添字（単独文字）は定義される記号ではない。目視で落としてから報告する。\n")
	cur = None
	for verdict, s, c, fl, d in out:
		if verdict != cur:
			cur = verdict
			print("== %s ==" % verdict)
		print("  %-20s 出現%4d  初出L%-6d 定義候補 %s" % (s, c, fl, d if d else "-"))
	return 0


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("使い方: py symbol_depgraph.py <tex> [最小出現回数]")
		sys.exit(2)
	sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2))
