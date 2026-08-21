# -*- coding: utf-8 -*-
# findings.json をサーバの PostgreSQL へ取り込む。**サーバ側で動く。**
#
# 使い方: python3 load.py <findings.json> <project> [remote] [repo_head]
#
# 全入れ替えである。1プロジェクト分を消して入れ直す。差分更新はしない。
#   findings.json は原稿と報告書から完全に再生成できるので、DB 側で履歴を保つ意味が無い。
#   差分更新にすると「消えた指摘」が残り続け、JSON 側と食い違ったときに、どちらが正か
#   分からなくなる。全入れ替えなら常に JSON が正である。
import json
import io
import os
import re
import sys

import psycopg2

DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
SEQ = re.compile(r"^\d{4}-\d{2}-\d{2}-(\d{2})-")
HASH = re.compile(r"\b([0-9a-f]{7,40})\b")


def disposition(state):
	"""状態欄を横断で比較できる値に畳む。

	状態欄は日本語の自由記述なので、そのままでは回をまたいで数えられない。
	判定の順序に意味がある。「保留: ... 対応した」のように両方を含む欄があるため、
	**保留と棄却を先に見る**。対応済を先に見ると、保留の件が適用済みに化ける。
	"""
	s = state or ""
	if "棄却" in s:
		return "rejected"
	if "保留" in s:
		return "deferred"
	if "対応済" in s or "適用" in s:
		return "applied"
	if "未処理" in s:
		return "open"
	return "unknown"


def main(path, project, remote=None, head=None):
	db = json.load(io.open(path, encoding="utf-8"))
	rows = db["findings"]
	conn = psycopg2.connect(dbname=os.environ.get("REVIEW_DB", "review"))
	conn.autocommit = False
	cur = conn.cursor()

	cur.execute("""INSERT INTO project (name, remote) VALUES (%s, %s)
	               ON CONFLICT (name) DO UPDATE SET remote = COALESCE(EXCLUDED.remote, project.remote)
	               RETURNING id""", (project, remote))
	pid = cur.fetchone()[0]

	# 全入れ替え。report を消せば finding は cascade で落ちる。
	cur.execute("DELETE FROM report WHERE project_id = %s", (pid,))

	rid = {}
	for f in rows:
		name = f["report"]
		if name not in rid:
			m = DATE.match(name)
			on = "-".join(m.groups()) if m else None
			# 命名は `<日付>-<通し>-<主題>` で、その日の1本目は通し番号を省く。
			s = SEQ.match(name)
			seq = int(s.group(1)) if s else 0
			cur.execute("""INSERT INTO report (project_id, name, reviewed_on, seq)
			               VALUES (%s, %s, %s, %s) RETURNING id""", (pid, name, on, seq))
			rid[name] = cur.fetchone()[0]
		state = f.get("state") or ""
		m = HASH.search(state)
		cur.execute("""INSERT INTO finding
		               (report_id, key, prefix, state, disposition, commit_sha, line, anchor, body)
		               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
		               ON CONFLICT (report_id, key) DO NOTHING""",
		            (rid[name], f["key"], re.sub(r"[0-9]+$", "", f["key"]), state,
		             disposition(state), m.group(1) if m else None,
		             f.get("line"), f.get("anchor"), f.get("text")))

	cur.execute("""INSERT INTO ingest (project_id, tex, tex_sha, repo_head, n_findings)
	               VALUES (%s, %s, %s, %s, %s)""",
	            (pid, db.get("tex"), db.get("sha"), head, len(rows)))
	conn.commit()

	cur.execute("""SELECT disposition, count(*) FROM v_finding WHERE project = %s
	               GROUP BY 1 ORDER BY 2 DESC""", (project,))
	print("取り込んだ: %s / %d 件" % (project, len(rows)))
	for d, n in cur.fetchall():
		print("  %-9s %d" % (d, n))
	conn.close()
	return 0


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("使い方: python3 load.py <findings.json> <project> [remote] [repo_head]")
		sys.exit(2)
	sys.exit(main(*sys.argv[1:5]))
