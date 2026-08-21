# -*- coding: utf-8 -*-
# findings.json を集計サーバへ送って取り込む。**手元で動く。**
#
# 使い方
#   py findings_push.py <findings.json> <ssh先>            送って取り込む
#   py findings_push.py <findings.json> <ssh先> --query    取り込んだあと集計を表示する
#
# ssh 先は `user@host`。手元の環境に固有の値なので、このリポジトリには書かない。
# 対象プロジェクト側の引き継ぎ資料に控える。
#
# なぜ SSH 越しか
#   PostgreSQL の口をネットワークに開けず、パスワードも配らないためである。サーバ側は
#   peer 認証だけを許し、認証は SSH が持つ。手元に DB クライアントも要らない。
#
# なぜ JSON をそのまま送るか
#   手元で SQL を組み立ててシェル越しに渡すと、アンカーに入っている TeX の
#   バックスラッシュが壊れる。ファイルを `cat >` で流し込めば内容はシェルを通らない。
#   サーバ側の Python が json モジュールで読む。
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

REMOTE_DIR = "~/.local/share/english-review"


def run(args, **kw):
	return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", **kw)


def send(ssh, local, remote):
	"""1ファイルを送る。内容はシェルを通らない。"""
	data = io.open(local, "rb").read()
	p = subprocess.run(["ssh", "-o", "BatchMode=yes", ssh, "cat > %s/%s" % (REMOTE_DIR, remote)],
	                   input=data, capture_output=True)
	if p.returncode:
		print("送信に失敗: %s\n%s" % (remote, p.stderr.decode("utf-8", "replace")))
		return False
	return True


def main(db_path, ssh, query=False):
	db_path = os.path.abspath(db_path)
	if not os.path.exists(db_path):
		print("見つからない: %s" % db_path)
		return 2
	root = run(["git", "rev-parse", "--show-toplevel"],
	           cwd=os.path.dirname(db_path)).stdout.strip()
	if not root:
		print("git リポジトリの中にない: %s" % db_path)
		return 2
	project = os.path.basename(root)
	remote = run(["git", "remote", "get-url", "origin"], cwd=root).stdout.strip() or None
	head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip() or None

	n = len(json.load(io.open(db_path, encoding="utf-8"))["findings"])
	print("送る: %s (%d 件) -> %s" % (project, n, ssh))

	here = os.path.dirname(os.path.abspath(__file__))
	dbdir = os.path.join(os.path.dirname(here), "db")
	if run(["ssh", "-o", "BatchMode=yes", ssh, "mkdir -p %s" % REMOTE_DIR]).returncode:
		print("サーバに繋がらない: %s" % ssh)
		return 1
	for local, name in ((os.path.join(dbdir, "schema.sql"), "schema.sql"),
	                    (os.path.join(dbdir, "load.py"), "load.py"),
	                    (db_path, "findings.json")):
		if not send(ssh, local, name):
			return 1

	cmd = ("psql -q -d review -v ON_ERROR_STOP=1 -f {d}/schema.sql && "
	       "python3 {d}/load.py {d}/findings.json {p} {r} {h}").format(
	           d=REMOTE_DIR, p=project, r=remote or "-", h=head or "-")
	p = run(["ssh", "-o", "BatchMode=yes", ssh, cmd])
	print(p.stdout.strip() or p.stderr.strip())
	if p.returncode:
		return 1

	if query:
		q = ("psql -d review -c '\\x off' "
		     "-c 'SELECT * FROM v_disposition' "
		     "-c 'SELECT project, reviewed_on, report, total, delta FROM v_convergence'")
		print()
		print(run(["ssh", "-o", "BatchMode=yes", ssh, q]).stdout)
	return 0


if __name__ == "__main__":
	a = [x for x in sys.argv[1:] if not x.startswith("--")]
	if len(a) < 2:
		print("使い方: py findings_push.py <findings.json> <user@host> [--query]")
		sys.exit(2)
	sys.exit(main(a[0], a[1], "--query" in sys.argv))
