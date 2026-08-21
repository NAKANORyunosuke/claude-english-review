# -*- coding: utf-8 -*-
# 記号の改名を JSON の指示書どおりに当てる。
# 使い方: py apply_renames.py <tex> <renames.json> [--apply]
#   既定は dry-run。--apply を付けたときだけ書き込む。
#
# なぜ要るか
#   記号の改名は「同じ文字列を全部置換」では済まない。同じ字が別の役で使われて
#   いるので範囲を切る必要があり、切り方を間違えると黙って壊れる。手でスクリプトを
#   書くと毎回同じ事故を起こすので、事故の型をここに畳んでおく。
#
# ここで防ぐ事故（すべて実際に起きたもの）
#   1. ヒアドキュメントに TeX を渡してバックスラッシュが壊れる
#      → 指示書は JSON ファイル。シェルを経由しない。
#   2. 期待ヒット数を数え違えて、一部だけ置換され旧記号が生き残る
#      → 事前アサート。1件でも合わなければ何も書かずに中止する。
#   3. 上付き・下付きの引数が1文字から複数文字になり括りが外れる
#      \sum_{i=1}^m を ^g_{\bw} にすると ^g と _{\bw} に割れる
#      → 置換後に ^X_{ / _X^{ の形を検出する。
#   4. 対象範囲に旧トークンが残っているのに気づかない
#      → residual に文字を挙げると、その範囲に独立トークンが無いことを確認する。
#   5. 事後アサートに新記号の個数を決め打ちして、その値のほうが間違っている
#      → 事後は「旧が消えたか」「壊れていないか」だけを見る。個数は書かせない。
#
# 指示書の形
#   {
#     "jobs": [
#       {"name": "N1 Phi_s -> Xi_s", "from": 1126, "to": 1146,
#        "old": "\\Phi_{\\mathfrak s}", "new": "\\Xi_{\\mathfrak s}", "count": 6},
#
#       {"name": "N7 alpha -> vartheta", "from": 2672, "to": 0,
#        "old": "\\alpha", "new": "\\vartheta", "count": 37, "macro": true},
#
#       {"name": "N9 residual", "from": 1811, "to": 1852,
#        "residual": "pqck"}
#     ]
#   }
#   from/to は 1-origin で両端を含む。to が 0 なら本文の末尾まで。
#   macro: true は直後に英字が続くマッチを除く（\alpha が \alphax に当たらない）。
#   residual だけの job は置換せず、その範囲に独立トークンが残っていないかを見る。
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SUPER_BROKEN = re.compile(r"\^[A-Za-z0-9]_\{|_[A-Za-z0-9]\^\{")


def token(ch):
	"""独立トークン。直前が英字・バックスラッシュ・アンダースコアなら別物の一部。"""
	return re.compile(r"(?<![A-Za-z\\_])" + re.escape(ch) + r"(?![A-Za-z_])")


def rows(lines, job):
	lo = int(job.get("from", 1))
	hi = int(job.get("to", 0)) or len(lines)
	return range(lo - 1, min(hi, len(lines)))


def finder(job):
	old = job["old"]
	if job.get("macro"):
		pat = re.compile(re.escape(old) + r"(?![A-Za-z])")
		return lambda s: len(pat.findall(s)), lambda s: pat.sub(job["new"].replace("\\", "\\\\"), s)
	return lambda s: s.count(old), lambda s: s.replace(old, job["new"])


def main(tex, spec, apply=False, db=None):
	src = io.open(tex, encoding="utf-8", newline="").read()
	nl = "\r\n" if "\r\n" in src else "\n"
	lines = src.split(nl)
	jobs = json.load(io.open(spec, encoding="utf-8"))["jobs"]

	print("== 事前アサート ==")
	bad = False
	for j in jobs:
		if "residual" in j and "old" not in j:
			continue
		count, _ = finder(j)
		got = sum(count(lines[i]) for i in rows(lines, j))
		want = j["count"]
		ok = got == want
		print("  %s %s: 期待%d 実際%d" % ("ok" if ok else "NG", j["name"], want, got))
		if not ok:
			bad = True
	if bad:
		print("\n中止: ヒット数が期待と違う。範囲か期待値のどちらかが誤っている。書き込んでいない。")
		return 1

	before = list(lines)
	for j in jobs:
		if "old" not in j:
			continue
		_, sub = finder(j)
		for i in rows(lines, j):
			lines[i] = sub(lines[i])
	out = nl.join(lines)

	print("\n== 事後アサート ==")
	ok_all = True

	def must(cond, msg):
		nonlocal ok_all
		print("  %s %s" % ("ok" if cond else "NG", msg))
		ok_all = ok_all and cond

	for j in jobs:
		if "old" not in j:
			continue
		count, _ = finder(j)
		left = sum(count(lines[i]) for i in rows(lines, j))
		must(left == 0, "%s: 範囲に旧記号の残存 0" % j["name"])

	for j in jobs:
		if "residual" not in j:
			continue
		hit = ["L%d:%s" % (i + 1, ch)
		       for i in rows(lines, j) for ch in j["residual"] if token(ch).search(lines[i])]
		must(not hit, "%s: 範囲に旧トークン %s の残存 0%s"
		     % (j["name"], j["residual"], "" if not hit else " -> " + ", ".join(hit[:8])))

	broken = [i + 1 for i, l in enumerate(lines)
	          if SUPER_BROKEN.search(l) and not SUPER_BROKEN.search(before[i])]
	must(not broken, "上付き・下付きの括りの破損 0%s"
	     % ("" if not broken else " -> L" + ", L".join(str(b) for b in broken)))
	must("\r" not in out.replace("\r\n", ""), "裸の CR 0")
	must(len(lines) == len(before), "行数不変")
	must(re.search(r"newcommand\{\\([A-Za-z]+)\}\{\\\1[^A-Za-z]", out) is None, "自己参照マクロ 0")

	if not ok_all:
		print("\n中止: 事後アサート失敗。書き込んでいない。")
		return 1
	if not apply:
		print("\ndry-run。--apply を付けると書き込む。")
		return 0
	io.open(tex, "w", encoding="utf-8", newline="").write(out)
	print("\n適用した。")
	if db:
		_retext_db(db, cfg)
	return 0


def _retext_db(dbp, cfg):
	"""指摘 DB のアンカーを改名に追随させる。

	改名は行数を変えないので行番号はずれない。ずれるのはアンカーの文面のほうで、
	放っておくと次の verify が、まだ片づいていない指摘を「消失」と報告する。
	"""
	import os
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	import finding_db
	pairs = [(j["old"], j["new"]) for j in cfg["jobs"] if "old" in j and "new" in j]
	print("\n-- 指摘 DB のアンカーを追随させる --")
	finding_db.cmd_retext(dbp, pairs)


if __name__ == "__main__":
	argv, a, db = sys.argv[1:], [], None
	i = 0
	while i < len(argv):
		if argv[i] == "--db" and i + 1 < len(argv):
			db, i = argv[i + 1], i + 2
			continue
		if not argv[i].startswith("--"):
			a.append(argv[i])
		i += 1
	if len(a) < 2:
		print("使い方: py apply_renames.py <tex> <renames.json> [--apply] [--db <findings.json>]")
		sys.exit(2)
	sys.exit(main(a[0], a[1], "--apply" in sys.argv, db))
