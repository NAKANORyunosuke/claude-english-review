-- 点検指摘の横断集計。
--
-- **ここは正ではない。**各リポジトリの findings.json が正であり、この DB はそこから
-- 完全に再生成できる派生である。壊れたら drop して入れ直せばよい。権威を2箇所に
-- 分けないための約束であって、性能や手間の話ではない。
--
-- 正を JSON 側に置く理由は、DB が原稿と同じコミットに乗るからである。原稿が commit X
-- なら、その X の findings.json はその版の原稿を指す。サーバに正を移すと、ブランチを
-- 切り替えたときや過去を見たときに、位置が別の版を指す。この DB がまさに防ぐために
-- 作られた事故がそこで起きる。
--
-- ここで答えるのは1つの問いだけである。**1リポジトリでは答えられない問い**、すなわち
-- プロジェクトを横断した再発と棄却率。単一プロジェクトの状態は findings.json を見る。

CREATE TABLE IF NOT EXISTS project (
	id     serial PRIMARY KEY,
	name   text UNIQUE NOT NULL,
	remote text
);

CREATE TABLE IF NOT EXISTS report (
	id          serial PRIMARY KEY,
	project_id  int NOT NULL REFERENCES project(id) ON DELETE CASCADE,
	name        text NOT NULL,
	reviewed_on date,
	-- 同じ日に複数回まわることがある。名前順では並ばない。命名は
	-- `<日付>-<通し>-<主題>` で、その日の1本目だけ通し番号を省くため、
	-- 名前で並べると1本目が最後に来る。日付だけでも同着になる。
	seq         int NOT NULL DEFAULT 0,
	UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS finding (
	id          bigserial PRIMARY KEY,
	report_id   int NOT NULL REFERENCES report(id) ON DELETE CASCADE,
	key         text NOT NULL,
	-- 件番号の接頭字。**意味は報告書ごとに違う**(ある回の N は記号、別の回の A は
	-- 自律判断)。横断の分類軸として使ってはいけない。素の記録として持つだけである。
	prefix      text NOT NULL,
	state       text,
	-- 状態欄を正規化したもの。横断で比較できるのはこの列である。
	disposition text NOT NULL CHECK (disposition IN
	              ('applied', 'rejected', 'deferred', 'open', 'unknown')),
	commit_sha  text,
	line        int,
	anchor      text,
	body        text,
	UNIQUE (report_id, key)
);

-- 取り込みの記録。どの版の原稿から作った集計かを後から言えるようにする。
CREATE TABLE IF NOT EXISTS ingest (
	id         bigserial PRIMARY KEY,
	project_id int NOT NULL REFERENCES project(id) ON DELETE CASCADE,
	tex        text,
	tex_sha    text,
	repo_head  text,
	n_findings int,
	at         timestamptz NOT NULL DEFAULT now()
);

-- 後から足した列。既にある DB でも通るようにする。この DB は捨てて作り直せるが、
-- 「作り直せる」に頼って毎回 drop すると、他のプロジェクトの取り込みまで消える。
ALTER TABLE report ADD COLUMN IF NOT EXISTS seq int NOT NULL DEFAULT 0;

-- ビューは列を変えると CREATE OR REPLACE が通らないので、先に落とす。
DROP VIEW IF EXISTS v_convergence;
DROP VIEW IF EXISTS v_disposition;
DROP VIEW IF EXISTS v_finding;

CREATE INDEX IF NOT EXISTS finding_disposition_idx ON finding (disposition);
CREATE INDEX IF NOT EXISTS finding_body_idx ON finding USING gin (to_tsvector('simple', coalesce(body, '')));

CREATE OR REPLACE VIEW v_finding AS
SELECT p.name AS project, r.name AS report, r.reviewed_on, r.seq,
       f.key, f.prefix, f.disposition, f.state, f.commit_sha, f.line, f.body, f.anchor
FROM finding f
JOIN report r ON r.id = f.report_id
JOIN project p ON p.id = r.project_id;

-- 回ごとの裁定の内訳。棄却が多い回は、指摘側の精度が落ちている回である。
CREATE OR REPLACE VIEW v_disposition AS
SELECT project, report, reviewed_on, seq,
       count(*) FILTER (WHERE disposition = 'applied')  AS applied,
       count(*) FILTER (WHERE disposition = 'rejected') AS rejected,
       count(*) FILTER (WHERE disposition = 'deferred') AS deferred,
       count(*) FILTER (WHERE disposition = 'open')     AS open,
       count(*) AS total,
       round(100.0 * count(*) FILTER (WHERE disposition = 'rejected') / count(*), 1) AS rejected_pct
FROM v_finding
GROUP BY project, report, reviewed_on, seq
ORDER BY project, reviewed_on, seq;

-- 収束しているか。回を追うごとに件数が減らないなら、点検が同じ場所を回っている。
CREATE OR REPLACE VIEW v_convergence AS
SELECT project, reviewed_on, seq, report, total,
       total - lag(total) OVER (PARTITION BY project ORDER BY reviewed_on, seq) AS delta
FROM v_disposition
ORDER BY project, reviewed_on, seq;
