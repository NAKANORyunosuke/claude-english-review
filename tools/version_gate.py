# -*- coding: utf-8 -*-
# 中身を変えたのに版を上げていないコミットを止める。
#
# 使い方
#   py tools/version_gate.py            これから commit する内容(staged)を見る
#   py tools/version_gate.py <A>..<B>   その区間のコミットをまとめて見る
#
# なぜ要るか
#   スキルが実際に読むのは cache のスナップショットで、導入の記録は**版で引く**。
#   版が同じなら中身をいくら変えても「更新なし」と判定され、cache は作り直されない。
#   つまり**版を上げ忘れると、直したこと自体が届かない。**しかも何のエラーも出ない。
#   2026-08-22 に実害が出た。cache が commit 8つ分古いまま止まり、ツール4本と
#   直した規則が届いていなかった。次の点検は、潰したはずの欠陥が無い状態から
#   始まるところだった。
#
#   規律は PLAYBOOK に書いたが、規則があっても人が読まないと守られない。
#   `ledger_gate.py` と同じく、規則ではなく検査で止める。
import io
import json
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 配布物として届く場所。ここが変われば版を上げなければならない。
WATCHED = ("tools/", "rules/", "skills/", "templates/", "db/", "hooks/",
           "PLAYBOOK.md", "config.example.json")
MANIFEST = ".claude-plugin/plugin.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def git(*args):
	p = subprocess.run(["git"] + list(args), capture_output=True, text=True, encoding="utf-8")
	return p.stdout if p.returncode == 0 else None


def version_at(ref):
	raw = git("show", "%s:%s" % (ref, MANIFEST))
	if raw is None:
		return None
	try:
		return json.loads(raw).get("version")
	except ValueError:
		return None


def newer(a, b):
	"""b が a より新しいか。semver でないものは文字列として違えばよしとする。"""
	ma, mb = SEMVER.match(a or ""), SEMVER.match(b or "")
	if ma and mb:
		return tuple(int(x) for x in mb.groups()) > tuple(int(x) for x in ma.groups())
	return (a or "") != (b or "")


def main(rng=None):
	if rng:
		files = (git("diff", "--name-only", rng) or "").split("\n")
		old, new = version_at(rng.split("..")[0]), version_at(rng.split("..")[-1] or "HEAD")
		where = rng
	else:
		files = (git("diff", "--cached", "--name-only") or "").split("\n")
		old, new = version_at("HEAD"), None
		raw = git("show", ":" + MANIFEST)
		if raw:
			try:
				new = json.loads(raw).get("version")
			except ValueError:
				pass
		else:
			new = old  # manifest を staged にしていない = 版は変わらない
		where = "staged"

	hit = sorted(f for f in files if f and f.startswith(WATCHED))
	if not hit:
		return 0
	if newer(old, new):
		print("版 %s -> %s。配布物 %d 件の変更に版が付いている。" % (old, new, len(hit)))
		return 0

	print("配布物を変えたのに版が上がっていない(%s)。" % where)
	print("  版: %s のまま" % old)
	for f in hit[:12]:
		print("  変更: %s" % f)
	if len(hit) > 12:
		print("  ほか %d 件" % (len(hit) - 12))
	print()
	print("%s の version を上げてから commit すること。" % MANIFEST)
	print("上げないと cache は作り直されず、**直したこと自体が届かない**。")
	print("commit のあとは次の2つを回す。")
	print("  claude plugin marketplace update english-review")
	print("  claude plugin update english-review@english-review")
	return 1


if __name__ == "__main__":
	a = [x for x in sys.argv[1:] if not x.startswith("--")]
	sys.exit(main(a[0] if a else None))
