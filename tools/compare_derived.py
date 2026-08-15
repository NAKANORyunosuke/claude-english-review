# -*- coding: utf-8 -*-
# 正本と派生ファイルの同期点検。片方にしか無い「地の文の文」を報告する。
# 派生側は証明を圧縮していることがあるので、差が出ること自体は異常ではない。
# 目的は、同期し忘れた文が正本側に残っていないかを機械的に見ることである。
# 使い方: py compare_derived.py <canonical.tex> <derived.tex>
import io
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")


def sentences(path):
	text = io.open(path, encoding="utf-8").read()
	text = text.split("\\begin{document}", 1)[-1].split("\\begin{thebibliography}")[0]
	out = Counter()
	for line in text.split("\n"):
		s = line.strip()
		if not s or s.startswith("%") or s.startswith("\\"):
			continue
		# 数式だけの行と表の行を落とす
		if "&" in s and "\\\\" in s:
			continue
		if not re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", s):
			continue
		out[" ".join(s.split())] += 1
	return out


a = sentences(sys.argv[1])
b = sentences(sys.argv[2])
only_a = sorted(set(a) - set(b))
only_b = sorted(set(b) - set(a))
print(f"canonical only: {len(only_a)}")
print(f"derived only:   {len(only_b)}")
print(f"shared:         {len(set(a) & set(b))}")
print()
print("=== derived only(派生側にしか無い文。圧縮の言い換えなら正常)===")
for s in only_b:
	print(" ", s[:200])
print()
print("=== canonical only(正本側にしか無い文。同期漏れの候補)===")
for s in only_a:
	print(" ", s[:200])
