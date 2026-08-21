# -*- coding: utf-8 -*-
# 採用指摘の一括適用器。fixes JSON を読み、平坦一致アンカーで置換する。
# 使い方: py apply_fixes.py <fixes.json> count|apply
#
# fixes.json 形式:
# {"file": "path/to/paper.tex",
#  "items": [
#    {"kind": "sub",  "key": "一意な平坦部分文字列", "subs": [["旧", "新"], ...], "want": 1},
#    {"kind": "full", "key": "...", "new": ["行1", "行2"]},
#    {"kind": "insert_after", "key": "...", "new": ["挿入行"]}
#  ],
#  "globals": [["旧文字列", "新文字列"], ...]}
#
# key はその行の空白を除いた文字列に含まれる一意な部分文字列(空白は無視して照合)。
# want 個の行にヒットしなければ何も書かずに終了する。full/insert_after は want=1 固定。
# 置換行は元行のタブインデントを引き継ぐ。
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def flat(s):
	return "".join(s.split())


def run(cfg_path, mode, db=None):
	cfg = json.load(io.open(cfg_path, encoding="utf-8"))
	path = cfg["file"]
	lines = io.open(path, encoding="utf-8").read().split("\n")
	fl = [flat(l) for l in lines]
	ok = True
	plan = []
	for it in cfg.get("items", []):
		k = flat(it["key"])
		hits = [i for i, l in enumerate(fl) if k in l]
		want = it.get("want", 1)
		if it["kind"] != "sub":
			want = 1
		if len(hits) != want:
			ok = False
			print(f"{it['kind']} {it['key'][:40]}: hits={len(hits)} 期待{want}")
			continue
		for i in hits:
			if it["kind"] == "sub":
				for old, new in it["subs"]:
					if old not in lines[i]:
						ok = False
						print(f"sub {it['key'][:40]}: 行内に '{old[:32]}' なし")
			plan.append((it["kind"], i, it))
	print("照合:", "all matched" if ok else "mismatches above")
	if mode != "apply" or not ok:
		return 0 if ok else 1
	for kind, i, it in sorted(plan, key=lambda t: -t[1]):
		indent = lines[i][:len(lines[i]) - len(lines[i].lstrip("\t"))]
		if kind == "sub":
			for old, new in it["subs"]:
				lines[i] = lines[i].replace(old, new)
		elif kind == "full":
			lines[i:i + 1] = [indent + s for s in it["new"]]
		else:
			lines[i + 1:i + 1] = [indent + s for s in it["new"]]
	body = "\n".join(lines)
	for old, new in cfg.get("globals", []):
		print(f"global '{old[:32]}' x{body.count(old)}")
		body = body.replace(old, new)
	# 読み込みは universal newlines で "\n" に潰れるので、元ファイルの改行で書き戻す。
	raw = io.open(path, "rb").read()
	nl = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n") else "\n"
	io.open(path, "w", encoding="utf-8", newline=nl).write(body)
	print("applied")
	if db:
		# 指摘を当てると行数が変わり、以降の行番号が全部ずれる。アンカーで引き直す。
		# ここで「消失」と出る件は、その指摘の対象の文が消えたということであり、
		# 片づいた証拠である。改名(apply_renames)と違ってアンカーは追随させない。
		import os
		sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
		import finding_db
		print("\n-- 指摘 DB の位置を引き直す --")
		finding_db.cmd_verify(db, path)
	return 0


if __name__ == "__main__":
	argv, a, db = sys.argv[1:], [], None
	i = 0
	while i < len(argv):
		if argv[i] == "--db" and i + 1 < len(argv):
			db, i = argv[i + 1], i + 2
			continue
		a.append(argv[i])
		i += 1
	if not a:
		print("使い方: py apply_fixes.py <fixes.json> count|apply [--db <findings.json>]")
		sys.exit(2)
	sys.exit(run(a[0], a[1] if len(a) > 1 else "count", db))
