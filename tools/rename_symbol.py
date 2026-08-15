# -*- coding: utf-8 -*-
# 記号の範囲限定改名。証明や小節の内側だけで使われる記号を、行範囲を指定して置換する。
# 使い方: py rename_symbol.py <spec.json> count|apply
#
# spec.json 形式:
# {"file": "path/to/paper.tex",
#  "renames": [
#    {"why": "1行の理由", "from": 2360, "to": 2520, "pairs": [["\\fp_", "\\fA_"], ...], "want": 12}
#  ]}
#
# from/to は 1 始まりの行番号(両端を含む)。want はその rename の総置換数の期待値。
# want が合わなければ何も書かずに終了する。範囲外は一切触らない。
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def run(cfg_path, mode):
	cfg = json.load(io.open(cfg_path, encoding="utf-8"))
	path = cfg["file"]
	raw = io.open(path, "rb").read()
	nl = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n") else "\n"
	lines = io.open(path, encoding="utf-8").read().split("\n")
	ok = True
	planned = []
	for rn in cfg["renames"]:
		lo, hi = rn["from"] - 1, rn["to"]
		total = 0
		hits = []
		for i in range(lo, min(hi, len(lines))):
			n = sum(lines[i].count(old) for old, _ in rn["pairs"])
			if n:
				total += n
				hits.append(i + 1)
		want = rn.get("want")
		mark = ""
		if want is not None and total != want:
			ok = False
			mark = f"  <== 期待{want}"
		print(f"{rn['why']}: L{rn['from']}--{rn['to']} 置換{total}{mark}")
		print(f"    行: {hits}")
		planned.append((lo, hi, rn["pairs"]))
	# 範囲外に同じ記号が残るかを報告する(改名漏れの検出)
	for rn in cfg["renames"]:
		lo, hi = rn["from"] - 1, rn["to"]
		outside = []
		for i, l in enumerate(lines):
			if lo <= i < hi:
				continue
			if any(old in l for old, _ in rn["pairs"]):
				outside.append(i + 1)
		if outside:
			print(f"    範囲外に残存: {outside[:20]}{' ...' if len(outside) > 20 else ''}")
	print("照合:", "all matched" if ok else "mismatches above")
	if mode != "apply" or not ok:
		return 0 if ok else 1
	for lo, hi, pairs in planned:
		for i in range(lo, min(hi, len(lines))):
			for old, new in pairs:
				lines[i] = lines[i].replace(old, new)
	io.open(path, "w", encoding="utf-8", newline=nl).write("\n".join(lines))
	print("applied")
	return 0


if __name__ == "__main__":
	sys.exit(run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "count"))
