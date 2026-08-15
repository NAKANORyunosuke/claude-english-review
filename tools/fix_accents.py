# -*- coding: utf-8 -*-
# TeX ソース中の生の UTF-8 アクセント文字を LaTeX コマンドへ戻す。
# 使い方: py fix_accents.py <file.tex> [apply]
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 生の文字 -> LaTeX コマンド
TABLE = [
	("ö", '\\"o'),
	("ä", '\\"a'),
	("ü", '\\"u'),
	("Ö", '\\"O'),
	("Ä", '\\"A'),
	("Ü", '\\"U'),
	("é", "\\'e"),
	("è", "\\`e"),
	("ê", "\\^e"),
	("á", "\\'a"),
	("à", "\\`a"),
	("í", "\\'i"),
	("ó", "\\'o"),
	("ú", "\\'u"),
	("ñ", "\\~n"),
	("ç", "\\c c"),
	("ß", "\\ss{}"),
	("ř", "\\v r"),
	("å", "\\aa{}"),
	("ø", "\\o{}"),
]

path = sys.argv[1]
apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
raw = io.open(path, "rb").read()
nl = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n") else "\n"
body = io.open(path, encoding="utf-8").read()

total = 0
for ch, cmd in TABLE:
	n = body.count(ch)
	if n:
		print(f"  {ch!r} -> {cmd!r} : {n}")
		total += n
		if apply:
			body = body.replace(ch, cmd)

# 残る非 ASCII を報告する(改行と通常の空白を除く)
rest = sorted({c for c in body if ord(c) > 127})
print("total replaced:" if apply else "total found:", total)
if rest:
	print("remaining non-ASCII:", " ".join(f"{c!r}({body.count(c)})" for c in rest))
else:
	print("remaining non-ASCII: none")

if apply:
	io.open(path, "w", encoding="utf-8", newline=nl).write(body)
	print("applied")
