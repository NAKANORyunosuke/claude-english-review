# -*- coding: utf-8 -*-
# 指摘の位置を保つ。行番号は腐るので、アンカー(原稿の実文)を正とする。
#
# 使い方
#   py finding_db.py init   <review-dir> <tex> [db.json]   報告書から DB を作る
#   py finding_db.py verify <db.json> <tex>                アンカーを引き直して照合する
#   py finding_db.py shift  <db.json> <at> <del> <add>     1回の編集を反映する
#   py finding_db.py sync   <db.json> <tex> <since-commit> git 履歴から復旧する
#   py finding_db.py status <db.json> <since-commit>       コミットの applied: を状態へ反映
#
# なぜ要るか
#   点検1回で数十件の指摘が出る。原稿を1行足すだけで以降の行番号がずれ、次に触るときに
#   全件を数え直すことになる。2026-08-22 の回では、記号を当てたあとに英文の37件を扱う
#   ところで「行番号がずれたので内容で特定し直す」を4回やった。
#
# 位置の保ち方(3層)
#   1. shift  — 編集のたびに (行, 削除数, 追加数) を反映する。検索が要らず軽い。
#   2. verify — 原稿のハッシュが記録と違えば、アンカーで引き直して同期する。
#               外部の編集(IDE、他セッション、人の手直し)はここで拾う。
#   3. sync   — git 履歴の hunk から shift をまとめて再生する。1 の記録が途切れた区間を
#               埋める。人が別環境で直した回の復旧はこれ。
#
# アンカーが見つからない件は「対象の文が既に無い」という情報である。消さずに残す。
#   2026-08-22 の S4 は、別の指摘(N9)を当てた副作用で対象自体が消滅した。行番号だけで
#   追っていると、その行を指し続けたまま気づけない。
#
# DB は対象リポジトリの findings_dir に置いてコミットする。
#   scratchpad やセッション固有の場所に置くと、複数の環境で作業したときに共有されない。
#   衝突を恐れなくてよい。この DB は**完全に再生成できる**からである。状態は報告書の
#   裁定表が正、アンカーは init が原稿から引き直す。マージで揉めたら init で作り直す。
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROW = re.compile(r"^\|\s*([A-Z]+[0-9]+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
ANCHOR_LEN = 72
# 報告書ではないもの。裁定表の形をしていても指摘ではない。
SKIP = {"HANDOVER.md", "PROCESS-DEFECTS.md"}


def sha(path):
	import hashlib
	return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def lines_of(path):
	return io.open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")


def first_line_number(cell):
	"""報告書の行欄から最初の行番号を拾う。'1126--1146' や '641 ほか' に対応。"""
	m = re.search(r"\d+", cell or "")
	return int(m.group(0)) if m else None


def make_anchor(line):
	"""行そのものをアンカーにする。インデントは落とす。

	短い行や環境の境界はアンカーにならない。原稿には `\\begin{equation}` や空行が
	何十個もあり、部分一致で拾うと1つの指摘が何十箇所にも当たる。一意に引けない
	ものは None にして、行番号だけで持つほうが誤りが少ない。
	"""
	s = line.strip()
	if len(s) < 25:
		return None
	if s.startswith("\\begin{") or s.startswith("\\end{") or s.startswith("\\label{"):
		return None
	# 数式だけの行はアンカーにならない。同じ式が何度も出るし、記号を改名すると変わる。
	# 地の文の語が3つ以上ある行だけを使う。
	prose = re.sub(r"\\[A-Za-z]+", " ", s)
	if len(re.findall(r"(?<![A-Za-z])[A-Za-z]{3,}(?![A-Za-z])", prose)) < 3:
		return None
	return s


def cmd_init(review_dir, tex, out):
	tl = lines_of(tex)
	db = {"tex": os.path.abspath(tex), "sha": sha(tex), "findings": []}
	for fn in sorted(f for f in os.listdir(review_dir) if f.endswith(".md") and f not in SKIP):
		seen = False
		for raw in io.open(os.path.join(review_dir, fn), encoding="utf-8"):
			m = ROW.match(raw)
			if not m:
				continue
			key, state, where = m.group(1), m.group(2), m.group(3)
			if key in ("件",):
				continue
			seen = True
			n = first_line_number(where)
			anchor = make_anchor(tl[n - 1]) if n and 0 < n <= len(tl) else None
			db["findings"].append({
				"report": fn[:-3], "key": key, "state": state.strip(),
				"line": n, "anchor": anchor,
			})
		if not seen:
			print("  (裁定表なし) %s" % fn)
	io.open(out, "w", encoding="utf-8").write(json.dumps(db, ensure_ascii=False, indent=1))
	live = sum(1 for f in db["findings"] if f["anchor"])
	print("DB を作った: %s" % out)
	print("  件数 %d、アンカーを取れたもの %d" % (len(db["findings"]), live))
	return 0


def load(dbp):
	return json.load(io.open(dbp, encoding="utf-8"))


def save(dbp, db):
	io.open(dbp, "w", encoding="utf-8").write(json.dumps(db, ensure_ascii=False, indent=1))


def cmd_verify(dbp, tex):
	db, tl = load(dbp), lines_of(tex)
	cur = sha(tex)
	if cur == db.get("sha"):
		print("原稿は記録と同じ(SHA-256 一致)。行番号はそのまま使える。")
	else:
		print("原稿が記録と違う。アンカーで引き直す。")
	moved = lost = ok = 0
	for f in db["findings"]:
		a = f.get("anchor")
		if not a:
			continue
		hits = [i + 1 for i, l in enumerate(tl) if l.strip() == a]
		if len(hits) == 1:
			if hits[0] != f.get("line"):
				print("  移動 %-4s %-34s L%s -> L%d" % (f["key"], f["report"][:34], f.get("line"), hits[0]))
				f["line"] = hits[0]
				moved += 1
			else:
				ok += 1
		elif not hits:
			print("  消失 %-4s %-34s L%s  (対象の文が無い。既に直したか、指摘が古い)"
			      % (f["key"], f["report"][:34], f.get("line")))
			f["stale"] = True
			lost += 1
		else:
			print("  多重 %-4s %-34s アンカーが%d箇所に一致。アンカーを長くする" % (f["key"], f["report"][:34], len(hits)))
	db["sha"] = cur
	save(dbp, db)
	print("\n一致 %d / 移動 %d / 消失 %d" % (ok, moved, lost))
	return 1 if lost else 0


def cmd_shift(dbp, at, deleted, added):
	db = load(dbp)
	delta = added - deleted
	n = 0
	for f in db["findings"]:
		if f.get("line") and f["line"] > at:
			f["line"] += delta
			n += 1
	save(dbp, db)
	print("L%d で %+d 行。%d 件の行番号をずらした。" % (at, delta, n))
	return 0


def cmd_sync(dbp, tex, since):
	"""git 履歴の hunk から shift をまとめて再生する。"""
	rel = os.path.relpath(os.path.abspath(tex), _repo_root(tex))
	diff = subprocess.run(["git", "diff", "-U0", since, "--", rel],
	                      cwd=_repo_root(tex), capture_output=True, text=True, encoding="utf-8")
	db = load(dbp)
	edits = []
	for line in diff.stdout.split("\n"):
		m = HUNK.match(line)
		if m:
			a, b = int(m.group(1)), int(m.group(2) or 1)
			d = int(m.group(4) or 1)
			edits.append((a, b, d))
	# 後ろの hunk から当てると前の行番号がずれない
	for a, b, d in sorted(edits, reverse=True):
		for f in db["findings"]:
			if f.get("line") and f["line"] > a:
				f["line"] += d - b
	save(dbp, db)
	print("%s 以降の hunk %d 個を反映した。" % (since, len(edits)))
	print("このあと verify を走らせて、アンカーとの食い違いを確かめること。")
	return 0


def cmd_status(dbp, since):
	"""コミット本文の applied: 行を読んで状態を更新する(PLAYBOOK のコミット規約)。"""
	root = os.path.dirname(os.path.abspath(dbp))
	log = subprocess.run(["git", "log", "--format=%h%x00%B%x01", "%s..HEAD" % since],
	                     cwd=root, capture_output=True, text=True, encoding="utf-8")
	db = load(dbp)
	by_key = {}
	for f in db["findings"]:
		by_key.setdefault(f["key"], []).append(f)
	n = 0
	for entry in log.stdout.split("\x01"):
		if "\x00" not in entry:
			continue
		h, body = entry.split("\x00", 1)
		h = h.strip()
		for line in body.split("\n"):
			if not line.startswith("applied:"):
				continue
			for key in line[len("applied:"):].split():
				for f in by_key.get(key, []):
					# ハッシュを持たない「対応済」も更新する。報告書に
					# 「対応済(本コミット)」と書いたまま放置される回があり、
					# review_status.py がそれを規律違反として拾う。
					if not HASH.search(f["state"]):
						f["state"] = "対応済 %s" % h
						n += 1
	save(dbp, db)
	print("コミットの applied: から %d 件を対応済にした。" % n)
	return 0


def _repo_root(path):
	d = os.path.dirname(os.path.abspath(path))
	r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=d,
	                   capture_output=True, text=True, encoding="utf-8")
	return r.stdout.strip() or d


USAGE = """使い方:
  py finding_db.py init   <review-dir> <tex> [db.json]
  py finding_db.py verify <db.json> <tex>
  py finding_db.py shift  <db.json> <at> <deleted> <added>
  py finding_db.py sync   <db.json> <tex> <since-commit>
  py finding_db.py status <db.json> <since-commit>"""

if __name__ == "__main__":
	a = sys.argv[1:]
	if not a:
		print(USAGE)
		sys.exit(2)
	c = a[0]
	if c == "init" and len(a) >= 3:
		sys.exit(cmd_init(a[1], a[2], a[3] if len(a) > 3 else "findings.json"))
	if c == "verify" and len(a) >= 3:
		sys.exit(cmd_verify(a[1], a[2]))
	if c == "shift" and len(a) >= 5:
		sys.exit(cmd_shift(a[1], int(a[2]), int(a[3]), int(a[4])))
	if c == "sync" and len(a) >= 4:
		sys.exit(cmd_sync(a[1], a[2], a[3]))
	if c == "status" and len(a) >= 3:
		sys.exit(cmd_status(a[1], a[2]))
	print(USAGE)
	sys.exit(2)
