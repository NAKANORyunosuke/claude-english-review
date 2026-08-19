# -*- coding: utf-8 -*-
# 報告書の裁定表を全部読んで、横断の残件を出す。引き継ぎ資料の元になる。
# 使い方: py review_status.py <review-dir> [--write] [--selftest]
#   --write は <review-dir>/HANDOVER.md のマーカー
#   <!-- review_status:open --> と <!-- review_status:rejected --> の間を差し替える。
#
# なぜ要るか
#   報告書は点検1回につき1ファイルで、残件はその数だけ散る。次に来た人が
#   「何がまだ決まっていないか」を知るのに全ファイルを開くことになり、開かない。
#   棄却の記録も同じで、読まれないと次のラウンドが同じ指摘を出し直す。
#
# 何を見るか
#   各ファイルで最初に現れる「件」と「状態」を持つ表を裁定表とみなす
#   (PLAYBOOK が報告書の先頭に置くと定めている)。以降の表は読まない。
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROW = re.compile(r"^\|(.+)\|\s*$")
HASH = re.compile(r"\b[0-9a-f]{7,40}\b")


def norm(state):
	s = state.replace("*", "").replace("`", "").strip()
	for k in ("未処理", "保留", "棄却"):
		if s.startswith(k):
			return k, s
	if s.startswith("対応済") or s.startswith("適用済"):
		return "対応済", s
	return "不明", s


def cells(line):
	m = ROW.match(line)
	return [c.strip() for c in m.group(1).split("|")] if m else None


def declares_commits(path):
	"""ファイル冒頭で適用コミットをまとめて宣言していれば、行ごとのハッシュを求めない。

	1件1コミットで進む回もあれば、1本の報告書の指摘が10本以上のコミットに散る回もある。
	後者で33行に後から考古学をやる価値は無い。コミットの件名が指摘番号を持つなら、
	報告書の冒頭で範囲を宣言すれば git log から辿れる。
	"""
	for line in io.open(path, encoding="utf-8"):
		if line.startswith("適用コミット:") and HASH.search(line):
			return True
	return False


def parse(path):
	"""裁定表の行を (件, 状態, 正規化前の状態, 残りの列) で返す。"""
	out, in_table, seen = [], False, False
	for line in io.open(path, encoding="utf-8"):
		c = cells(line)
		if c is None:
			if in_table:
				break
			continue
		if not in_table:
			if not seen and "件" in c[0] and any("状態" in x for x in c):
				in_table, seen = True, True
			continue
		if all(set(x) <= set("-: ") for x in c):
			continue
		if len(c) < 2:
			break
		key, raw = norm(c[1])
		out.append((c[0], key, raw, " / ".join(x for x in c[2:] if x)))
	return out


HEAD = "| 報告書 | 件 | 状態 | 内容 |" + "\n" + "| --- | --- | --- | --- |"


def table(hit):
	if not hit:
		return "なし。"
	body = "\n".join("| %s | %s | %s | %s |" % (f[:-3], i, raw, rest) for f, (i, _k, raw, rest) in hit)
	return HEAD + "\n" + body


def graft(path, key, body):
	"""HANDOVER.md のマーカーの間を差し替える。無ければ何もしない。"""
	a, b = "<!-- review_status:%s -->" % key, "<!-- /review_status:%s -->" % key
	t = io.open(path, encoding="utf-8").read()
	i, j = t.find(a), t.find(b)
	if i < 0 or j < i:
		return False
	t = t[: i + len(a)] + "\n\n" + body + "\n\n" + t[j:]
	io.open(path, "w", encoding="utf-8", newline="\r\n").write(t)
	return True


def main(d, write=False):
	files = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "HANDOVER.md")
	bulk = {f for f in files if declares_commits(os.path.join(d, f))}
	rows = [(f, r) for f in files for r in parse(os.path.join(d, f))]
	if not rows:
		print("裁定表が見つからない: %s" % d)
		return 2

	def pick(keep):
		return [(f, r) for f, r in rows if keep(f, r)]

	def dump(title, hit):
		print("\n## %s %d" % (title, len(hit)))
		print(table(hit))
		return len(hit)

	opens = pick(lambda f, r: r[1] in ("未処理", "保留"))
	rejected = pick(lambda f, r: r[1] == "棄却")
	open_n = dump("未決（未処理・保留）", opens)
	nohash = dump(
		"対応済だがコミットのハッシュが無い",
		pick(lambda f, r: r[1] == "対応済" and not HASH.search(r[2]) and f not in bulk),
	)
	dump("棄却（次のラウンドで出し直さない）", rejected)
	dump("状態が読めない", pick(lambda f, r: r[1] == "不明"))

	if write:
		h = os.path.join(d, "HANDOVER.md")
		if not os.path.exists(h):
			print("\n%s が無い。templates/handover.md から作る。" % h)
		else:
			ok = graft(h, "open", table(opens)) and graft(h, "rejected", table(rejected))
			print("\nHANDOVER.md: %s" % ("未決と棄却を差し替えた" if ok else "マーカーが見つからない"))

	tally = {}
	for _f, r in rows:
		tally[r[1]] = tally.get(r[1], 0) + 1
	print("\n## 集計 全 %d 件（報告書 %d 本）" % (len(rows), len(files)))
	print("   " + "  ".join("%s %d" % kv for kv in sorted(tally.items())))
	if nohash:
		print("\nNG: 対応済なのにハッシュが無い行がある。適用したコミットの短縮ハッシュを書く。")
	return 1 if nohash else (0 if not open_n else 0)


def selftest():
	import tempfile
	sample = (
		"# 見出し\n\n"
		"| 節 | 行 |\n| --- | --- |\n| A | 1 |\n\n"       # 裁定表ではない表は読まない
		"| 件 | 状態 | 箇所 | 内容 |\n| --- | --- | --- | --- |\n"
		"| F1 | 対応済 `5315606` | L10 | あ |\n"
		"| B1 | **対応済** | L20 | い |\n"
		"| S1 | 保留 | L30 | う |\n"
		"| E1 | 未処理 | L40 | え |\n"
		"| S2 | 棄却 | L50 | お |\n\n"
		"| 件 | 状態 | 次 |\n| --- | --- |\n| S1 | 保留 | 二度読みしない |\n"
	)
	p = os.path.join(tempfile.mkdtemp(), "t.md")
	io.open(p, "w", encoding="utf-8").write(sample)
	got = [(i, k) for i, k, _r, _x in parse(p)]
	assert got == [("F1", "対応済"), ("B1", "対応済"), ("S1", "保留"), ("E1", "未処理"), ("S2", "棄却")], got
	assert HASH.search("対応済 `5315606`") and not HASH.search("対応済")
	print("selftest ok")


if __name__ == "__main__":
	if "--selftest" in sys.argv:
		selftest()
	elif len(sys.argv) < 2:
		print("usage: py review_status.py <review-dir> [--write] [--selftest]")
		sys.exit(2)
	else:
		sys.exit(main(sys.argv[1], "--write" in sys.argv))
