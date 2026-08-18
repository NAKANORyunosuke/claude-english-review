# -*- coding: utf-8 -*-
# 定理環境・式・節の依存グラフと番号系列の点検。
# 使い方: py depgraph.py <file.tex> [<file.aux>]
#   .aux を省略すると同じベース名のものを探す。印字番号は再導出せず .aux から取る。
#   .aux が無い場合は番号を "?" として、依存関係の点検だけを行う。
#
# 出すもの
#   1. 印字番号の系列（定理系・式）— 欠番と重複の確認
#   2. 番号を消費するがラベルの無い環境 — 番号は振られるのに参照できない
#   3. 環境から離れた proof — 任意引数の \ref で結び直した対応と距離
#   4. 結果間の前方依存 — 自分より後ろの結果に依存しているもの
#   5. 入次数0 — どの結果からも引かれないもの（地の文からの参照回数を併記）
#
# 切り分けの注意
#   * 環境が「自分より後ろ」を引く参照の多くは、自分の内側の display を指しており
#     依存ではない。除外しないと偽陽性になる。
#   * 環境から離れた proof（\begin{proof}[Proof of \ref{...}]）を結び直さないと、
#     その証明が持つ辺が丸ごと落ちる。主定理の証明がこの形になりやすい。
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) < 2:
	print("usage: py depgraph.py <file.tex> [<file.aux>]")
	sys.exit(2)
TEX = sys.argv[1]
AUX = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(TEX)[0] + ".aux"

# 定理カウンタを共有する環境。プロジェクトに合わせて足す。
THM = "theorem|maintheorem|lemma|proposition|corollary|fact|remark|definition|conj|eg|note"
DISPLAY = "equation|align|gather|multline"

src = io.open(TEX, encoding="utf-8").read().split("\n")
start = next((i for i, l in enumerate(src) if "\\begin{document}" in l), 0)
body = [re.sub(r"(?<!\\)%.*$", "", s) for s in src]

printed = {}
if os.path.exists(AUX):
	aux = io.open(AUX, encoding="utf-8", errors="replace").read()
	for m in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}\{([^}]*)\}", aux):
		printed[m.group(1)] = m.group(2)

BEG = re.compile(r"\\begin\{(" + THM + r")\*?\}")
END = re.compile(r"\\end\{(" + THM + r")\*?\}")
DBEG = re.compile(r"\\begin\{(" + DISPLAY + r")\*?\}")
DEND = re.compile(r"\\end\{(" + DISPLAY + r")\*?\}")
PROOF_E = re.compile(r"\\end\{proof\}")
LAB = re.compile(r"\\label\{([^}]*)\}")
REF = re.compile(r"\\(?:eq)?ref\{([^}]*)\}")
SEC = re.compile(r"\\section\{([^}]*)\}")

nodes, label_line, kind_of = [], {}, {}


def add(ln, kind, lab, sec=None):
	if lab in label_line:
		return
	label_line[lab] = ln
	kind_of[lab] = kind
	nodes.append((ln, kind, lab, sec))


cur_sec = None
for i in range(start, len(body)):
	ms = SEC.search(body[i])
	if ms:
		cur_sec = ms.group(1)
	mb = BEG.search(body[i])
	if mb:
		for j in range(i, min(i + 4, len(body))):
			ml = LAB.search(body[j])
			if ml:
				add(i + 1, mb.group(1), ml.group(1), cur_sec)
				break
for i in range(start, len(body)):
	if DBEG.search(body[i]):
		for j in range(i, min(i + 40, len(body))):
			ml = LAB.search(body[j])
			if ml:
				add(j + 1, "eq", ml.group(1))
			if DEND.search(body[j]):
				break
for i in range(start, len(body)):
	ml = LAB.search(body[i])
	if ml:
		add(i + 1, "sec" if "sec:" in ml.group(1) else "other", ml.group(1))
nodes.sort()

edges, span, unlabeled = [], {}, []
i = start
while i < len(body):
	mb = BEG.search(body[i])
	if not mb:
		i += 1
		continue
	lab = None
	for j in range(i, min(i + 4, len(body))):
		ml = LAB.search(body[j])
		if ml:
			lab = ml.group(1)
			break
	depth, j = 1, i + 1
	while j < len(body) and depth > 0:
		if BEG.search(body[j]):
			depth += 1
		if END.search(body[j]):
			depth -= 1
		j += 1
	end = j
	k = end
	while k < len(body) and body[k].strip() == "":
		k += 1
	if k < len(body) and re.search(r"\\begin\{proof\}", body[k]):
		while k < len(body) and not PROOF_E.search(body[k]):
			k += 1
		end = k + 1
	if lab:
		span[lab] = (i + 1, end)
		for j in range(i, min(end, len(body))):
			for r in REF.findall(body[j]):
				if r != lab:
					edges.append((lab, r))
	else:
		unlabeled.append((i + 1, mb.group(1)))
	i = end

detached = []
i = start
while i < len(body):
	m = re.search(r"\\begin\{proof\}\[([^\]]*)\]", body[i])
	if m and not any(a <= i + 1 <= b for a, b in span.values()):
		owner = REF.findall(m.group(1))
		j = i
		while j < len(body) and not PROOF_E.search(body[j]):
			j += 1
		if owner:
			o = owner[0]
			detached.append((i + 1, o, label_line.get(o, 0)))
			for k in range(i, min(j + 1, len(body))):
				for r in REF.findall(body[k]):
					if r != o:
						edges.append((o, r))
		i = j + 1
		continue
	i += 1

allrefs = collections.Counter()
for i in range(start, len(body)):
	for r in REF.findall(body[i]):
		allrefs[r] += 1

env_n = sum(1 for n in nodes if n[1] not in ("eq", "sec", "other"))
print("== ノード %d (環境 %d / 式 %d / 節 %d) / 辺 %d"
      % (len(nodes), env_n,
         sum(1 for n in nodes if n[1] == "eq"),
         sum(1 for n in nodes if n[1] == "sec"), len(edges)))

for title, want in (("定理系の番号系列", False), ("式番号の系列", True)):
	print("\n== " + title)
	for ln, kind, lab, sec in nodes:
		if (kind == "eq") != want or kind in ("sec", "other"):
			continue
		print("   L%-5d %-13s %-26s -> %s" % (ln, kind, lab, printed.get(lab, "?")))

print("\n== 番号を消費するがラベルの無い環境")
if not unlabeled:
	print("   なし")
for ln, name in unlabeled:
	print("   L%-5d %s" % (ln, name))

print("\n== 環境から離れた proof")
if not detached:
	print("   なし")
for ln, o, oln in detached:
	print("   L%-5d は %s (L%d) の証明。距離 %d 行" % (ln, o, oln, ln - oln))


def inside(u, v):
	a, b = span.get(u, (0, 0))
	return a <= label_line.get(v, 0) <= b


fwd = sorted({(u, v) for u, v in edges
              if label_line.get(v, 0) > label_line.get(u, 0) and not inside(u, v)},
             key=lambda e: label_line.get(e[0], 0))
print("\n== 結果間の前方依存（自分より後ろの結果に依存している）")
if not fwd:
	print("   なし")
for u, v in fwd:
	print("   L%-5d %-26s -> %-26s (L%d)" % (label_line[u], u, v, label_line.get(v, 0)))
print("   参考: 自分の内側の display を引く参照 %d 件（依存ではない）"
      % len({(u, v) for u, v in edges if inside(u, v)}))

indeg = collections.Counter(v for u, v in edges)
print("\n== 入次数0（どの結果からも引かれない）")
for ln, kind, lab, sec in nodes:
	if indeg[lab] == 0:
		print("   L%-5d %-13s %-26s 地の文からの参照 %d 回" % (ln, kind, lab, allrefs[lab]))
