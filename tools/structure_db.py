# -*- coding: utf-8 -*-
# 各行が何をしている行かを分類し、環境グループと位置(行・ページ・節)を持たせて、
# 構造の欠陥を機械的に拾う。
#
# 使い方
#   py structure_db.py <tex> [<aux>] [--json out.json]
#
# なぜ要るか
#   台帳の決定3(「定理環境には仮定と主張だけを置く」)は 2026-08-15 から明文化されているが、
#   2026-08-22 の点検でまた2件見つかった(P1 と S1)。規則があっても人が読まないと守られない。
#   これらは「グループ×種別」の組で機械判定できる型なので、規則ではなく検査で止める。
#
# 拾う型(すべて 2026-08-22 の実点検で出たもの)
#   P1  定理環境の主張の中で記号を定義している
#   S1  定理の主張が命令文で始まる / 環境の中で記号を定義している
#   S2  証明の末尾に、その証明が属する主張に無い条件付きの主張がある
#
#   前方参照(S6)はここでは見ない。ラベルの前後関係は depgraph.py、記号の定義位置は
#   symbol_depgraph.py が持っている。同じ判定を3つに分けて書かない。
#
# 較正の記録(2026-08-22、paper-obstruction-arxiv.tex 3495行)
#   素朴に書いたら 60 件出た。うち実害があるのは 4 件だった。効いた絞り込みは3つある。
#   1. `Let X be ...` は仮定であって定義ではない(規範の明文)。混ぜると定理の仮定が全部挙がる。
#   2. `set` は名詞で出る。`open set \(\Omega\)` を定義と読むと存在主張が定義に化ける。
#   3. 主張とその証明は同じ視野。分けると、補題で定義し直後の証明で使うだけの記号が挙がる。
#   検出を足すより、この3つのような「規則の言い換えでしかない一致」を落とすほうが効く。
#
# 位置の三層
#   行   — 編集で腐る。DB では参考値。
#   節   — 「同じ紙面で両方の役が同時に見えるか」の判定に使う。記号の維持/解消を分ける
#          基準として Codex が繰り返し使ったもの。
#   ページ — 前方参照の重さを測る。同じページなら読者は目を戻せるが、10ページ前を
#          参照させるのは実害がある。行だけだとこの差が出ない。
import io
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

THM_ENVS = {"theorem", "proposition", "lemma", "corollary", "conjecture", "fact"}
BODY_ENVS = THM_ENVS | {"definition", "example", "remark", "proof", "algorithm"}
DISPLAY_ENVS = {"equation", "align", "aligned", "array", "cases", "bmatrix", "split", "gather"}

BEGIN = re.compile(r"\\begin\{([a-z*]+)\}")
END = re.compile(r"\\end\{([a-z*]+)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")
SEC = re.compile(r"\\(sub)?section\{")
NEWLABEL = re.compile(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}")

# 導入儀式。記号の直前に来たときだけ定義とみなす(行のどこかにあるだけでは拾わない)。
# `Let X be ...` と `Choose ...` は**仮定の宣言**であって定義ではない。規範も
# 「"Let X be …" は補題内の仮定用」と定める。ここを混ぜると定理の仮定が全部
# 「定理環境の中の定義」として誤検出される(実データで60件中の大半がこれだった)。
CUE = re.compile(r"\b(?:[Dd]efine|[Pp]ut|[Ss]et|[Ww]rite|[Dd]enote by|[Ww]e call|"
                 r"use the notation|[Aa]bbreviate)\b")
# `set` は圧倒的に名詞で出る。`the set \(E\)` や `open set \(\Omega\)` を定義と読むと、
# 存在主張がまるごと「定理環境の中の定義」に化ける(実データで20件中5件がこれだった)。
# 動詞の `set` は文頭か `we set` の形でしか現れないので、その位置だけを合図とみなす。
def _is_cue(s, m):
	if m.group(0).lower() != "set":
		return True
	before = s[:m.start()].rstrip()
	return before == "" or before.lower().endswith("we")
HYP = re.compile(r"^\s*(?:Let\b|Suppose\b|Assume\b|Choose\b|Retain\b|Fix\b|With\b|For\b|If\b)")
SYM = re.compile(r"\\\((\\[A-Za-z]+|[A-Za-z])")
IMPERATIVE = re.compile(r"^\s*(?:Decompose|Filter|Take|Consider|Fix|Choose|Apply|Substitute|"
                        r"Use|Write|Put|Set|Define|Group|Order|Partition|Assume)\b")
CONDITIONAL = re.compile(r"^\s*If\b.*\bthen\b")


def classify(line, in_display):
	s = line.strip()
	if not s:
		return "blank"
	if s.startswith("%"):
		return "comment"
	if BEGIN.search(s) and not in_display:
		return "env-begin"
	if END.search(s):
		return "env-end"
	if s.startswith("\\label{"):
		return "label"
	if in_display:
		return "display"
	# 仮定の宣言が先。`Let \(F_1\supseteq\cdots\) be a filtration` は定義ではない。
	if HYP.match(s):
		return "hypothesis"
	# 定義: 合図の直後(40字以内)に \( で始まる記号がある
	for m in CUE.finditer(s):
		if not _is_cue(s, m):
			continue
		for k in SYM.finditer(s):
			if 0 <= k.start() - m.end() <= 40:
				return "definition"
	if IMPERATIVE.match(s):
		return "imperative"
	if CONDITIONAL.match(s):
		return "conditional"
	return "prose"


def page_map(tex_lines, aux):
	"""ラベルの印字ページを .aux から取り、行→ページを直近のラベルで埋める。"""
	pages = {}
	if aux and os.path.exists(aux):
		for line in io.open(aux, encoding="utf-8", errors="replace"):
			m = NEWLABEL.match(line.strip())
			if m:
				pages[m.group(1)] = m.group(3)
	at = {}
	for i, l in enumerate(tex_lines):
		m = LABEL.search(l)
		if m and m.group(1) in pages:
			at[i] = pages[m.group(1)]
	out, cur = {}, None
	for i in range(len(tex_lines)):
		if i in at:
			cur = at[i]
		out[i] = cur
	return out


def build(tex, aux):
	lines = io.open(tex, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
	pg = page_map(lines, aux)
	rows, groups, stack, depth = [], [], [], 0
	section = subsection = None
	last_thm = None
	for i, l in enumerate(lines):
		s = l.strip()
		if SEC.search(s):
			if s.startswith("\\subsection"):
				subsection = s
			else:
				section, subsection = s, None
		opens = [m.group(1).rstrip("*") for m in BEGIN.finditer(s)]
		closes = [m.group(1).rstrip("*") for m in END.finditer(s)]
		was = depth
		depth += sum(1 for e in opens if e in DISPLAY_ENVS) - sum(1 for e in closes if e in DISPLAY_ENVS)
		depth = max(0, depth)
		if s.startswith("\\[") or s == "\\[":
			depth += 1
		if s.startswith("\\]") or s == "\\]":
			depth = max(0, depth - 1)

		for e in opens:
			if e in BODY_ENVS:
				lab = None
				for j in range(i, min(i + 3, len(lines))):
					m = LABEL.search(lines[j])
					if m:
						lab = m.group(1)
						break
				# 直前の定理環境に proof を結び付ける
				owner = last_thm if e == "proof" else lab
				g = {"id": len(groups), "env": e, "label": lab, "owner": owner,
				     "start": i + 1, "end": None}
				groups.append(g)
				stack.append(g)
				if e in THM_ENVS:
					last_thm = lab

		kind = classify(l, was > 0 or depth > 0)
		g = stack[-1] if stack else None
		rows.append({
			"line": i + 1, "kind": kind,
			"env": g["env"] if g else None,
			"group": (g["label"] or g["owner"]) if g else None,
			"gid": g["id"] if g else None,
			"page": pg.get(i),
			"section": section, "subsection": subsection,
			"text": s[:110],
		})
		for e in closes:
			if e in BODY_ENVS and stack:
				stack.pop()["end"] = i + 1
	for g in groups:
		if g["end"] is None:
			g["end"] = len(lines)
	return rows, groups, lines


# 名前ではないマクロ。これらが行に載っていても「定義された記号」ではない。
NOT_A_NAME = set("""left right big Big bigg Bigg quad qquad text mathrm mathsf mathbb mathcal
mathfrak operatorname begin end label ref eqref cite emph textbf textit
sum prod int bigoplus bigcup bigcap oplus otimes cup cap setminus subseteq supseteq
subset supset in notin leq geq neq to mapsto colon cdot cdots ldots dots vdots
frac binom sqrt overline widetilde widehat tilde hat bar circ
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda
mu nu xi pi varpi rho sigma tau upsilon phi varphi chi psi omega
Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
forall exists and or not implies iff langle rangle lvert rvert lVert rVert
min max sup inf lim deg dim ker coker image rank ord""".split())
MACRO = re.compile(r"\\([A-Za-z]+)")


MATH = re.compile(r"\\\((.+?)\\\)")
BY = re.compile(r"\bby\b|\bto be\b|\bto denote\b")
# 頭の記号。`\mathsf T` や `\phi_{\min}` のように、字体マクロと直後の添字までを一体で見る。
HEAD = re.compile(r"^\s*(\\math[a-z]+\s*\{[A-Za-z0-9]+\}|\\math[a-z]+\s+[A-Za-z0-9]"
                  r"|\\[A-Za-z]+|[A-Za-z])((?:_\{[^{}]*\}|_[A-Za-z0-9])?)")


def defined_symbols(s):
	"""定義されている記号だけを拾う。

	行に載っている記号を全部拾ってはいけない。`Put \\(\\cS_{\\bw}(\\Omega)=\\Sigma(\\cV)\\)`
	の \\bw も \\cV も**既に定義済みの記号を使っているだけ**であり、この行が定義するのは
	\\cS だけである。合図の直後の等式の左辺の頭だけを見る。
	"""
	out = []
	for m in CUE.finditer(s):
		if not _is_cue(s, m):
			continue
		rest = s[m.end():]
		# 列挙形 `Define \(a\), \(b\), and \(c\) by ...` は by の手前までが定義対象。
		cut = BY.search(rest)
		zone = rest[:cut.start()] if cut else rest
		gs = MATH.findall(zone)
		if not gs:
			continue
		if not cut:
			gs = gs[:1]
		for gtext in gs:
			lhs = re.split(r"=|\\colon|:", gtext, maxsplit=1)[0]
			h = HEAD.match(lhs)
			if not h:
				continue
			name = (h.group(1) + h.group(2)).strip()
			base = MACRO.match(name)
			# 添字も字体指定も付かない裸のギリシャ文字等は、その場限りの記号とみなす。
			if base and base.group(1) in NOT_A_NAME and not h.group(2) and not name.startswith("\\math"):
				continue
			out.append(name)
	return out


def escapes(sym, lines, start, end):
	"""環境の外でその記号が使われている回数。

	裸の1文字は数えない。`p` は原稿のどこにでも出るので、外で使われているかを
	文字列一致で測れない。
	"""
	if not sym.startswith("\\"):
		return 0
	pat = re.compile(re.escape(sym) + r"(?![A-Za-z])")
	n = 0
	for i, l in enumerate(lines):
		if start <= i + 1 <= end:
			continue
		n += len(pat.findall(l))
	return n


def audit(rows, groups, lines):
	found = []
	gmap = {g["id"]: g for g in groups}
	# 主張とその証明は同じ視野である。証明の中でその記号を使うのは逸脱ではない。
	# これを分けると `\phi_{\min}` のように、補題で定義して直後の証明で使うだけの
	# 記号まで「環境の外へ出る」と報告してしまう。
	scope_end = {}
	for g in groups:
		e = g["end"]
		if g["label"]:
			for p in groups:
				if p["env"] == "proof" and p["owner"] == g["label"] and p["end"] > e:
					e = p["end"]
		scope_end[g["id"]] = e
	for r in rows:
		if r["env"] not in THM_ENVS:
			continue
		if r["kind"] not in ("definition", "imperative"):
			continue
		what = ("定理環境の中で記号を定義している(決定3)" if r["kind"] == "definition"
		        else "定理の主張が命令文で始まる(決定3)")
		g = gmap.get(r["gid"])
		# 記号が環境の外へ出るなら実害がある。読者はその定義を定理の中まで探しに行けない。
		# 2026-08-22 の P1(\fT_{\cN} を定理の主張で定義し、後の節で使っていた)がこの型。
		out = []
		if g:
			for sym in set(defined_symbols(lines[r["line"] - 1])):
				if escapes(sym, lines, g["start"], scope_end[g["id"]]):
					out.append(sym)
		r = dict(r, escaped=sorted(out))
		found.append((what + ("  [環境の外で使う記号: %s]" % " ".join(sorted(out)) if out else ""), r))
	# 証明の末尾が条件付きの主張
	by_group = defaultdict(list)
	for r in rows:
		if r["env"] == "proof":
			by_group[(r["group"], r["env"])].append(r)
	for _k, rs in by_group.items():
		body = [r for r in rs if r["kind"] not in ("blank", "comment", "env-begin", "env-end", "label")]
		if body and body[-1]["kind"] == "conditional":
			found.append(("証明の末尾が条件付きの主張(その主張に無いなら Remark へ)", body[-1]))
	return found


if __name__ == "__main__":
	# `--json out.json` の値を positional から外す。外さないと出力先が aux として
	# 読まれ、ページ欄が黙って全部 null になる。
	argv, a, out_json = sys.argv[1:], [], None
	i = 0
	while i < len(argv):
		if argv[i] == "--json" and i + 1 < len(argv):
			out_json = argv[i + 1]
			i += 2
			continue
		a.append(argv[i])
		i += 1
	if not a:
		print("usage: py structure_db.py <tex> [<aux>] [--json out.json]")
		sys.exit(2)
	tex = a[0]
	aux = a[1] if len(a) > 1 else os.path.splitext(tex)[0] + ".aux"
	rows, groups, lines = build(tex, aux)

	if out_json:
		io.open(out_json, "w", encoding="utf-8").write(
			json.dumps({"rows": rows, "groups": groups}, ensure_ascii=False, indent=1))
		print("行の分類を書き出した: %s (%d 行, 環境 %d 個)" % (out_json, len(rows), len(groups)))

	kinds = defaultdict(int)
	for r in rows:
		kinds[r["kind"]] += 1
	print("== 行の分類 ==")
	for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
		print("  %-12s %d" % (k, v))

	hits = audit(rows, groups, lines)
	# 記号が環境の外へ出るものを先に出す。局所で閉じている定義は読者に実害が無い。
	hits.sort(key=lambda mr: (not mr[1].get("escaped"), mr[1]["line"]))
	heavy = sum(1 for _m, r in hits if r.get("escaped"))
	print("\n== 構造の欠陥 %d 件(うち記号が環境の外へ出るもの %d 件) ==" % (len(hits), heavy))
	for msg, r in hits:
		print("  L%-5d p%-4s %-14s %s" % (r["line"], r["page"] or "?", r["env"], msg))
		print("        %s" % r["text"])
	sys.exit(1 if hits else 0)
