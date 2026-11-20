# -*- coding: utf-8 -*-
# apply_renames.py の事後アサートの回帰テスト。
# 使い方: py tools/test_apply_renames.py   (成功なら "ok" を出して終了コード 0)
#
# 新しい記号が旧い記号を含む改名(X_ -> \mathcal X_)で、置換が済んでいるのに
# 「旧記号が残存」と判定して止まった(2026-11-21)。その再発を見る。
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "apply_renames.py")

TEX = "Write $F^rK(A)$ for the tower.\r\nThen $\\pi_iF^rK(A)=0$ and $X_s$ here.\r\nOutside $F^rK(A)$.\r\n"
JOBS = {"jobs": [
    {"name": "F", "from": 1, "to": 2, "old": "F^rK(A)", "new": "\\mathcal F^rK(A)", "count": 2},
    {"name": "X", "from": 1, "to": 2, "old": "X_s", "new": "\\mathcal X_s", "count": 1},
]}
WANT = "Write $\\mathcal F^rK(A)$ for the tower.\r\nThen $\\pi_i\\mathcal F^rK(A)=0$ and $\\mathcal X_s$ here.\r\nOutside $F^rK(A)$.\r\n"

with tempfile.TemporaryDirectory() as d:
    tex, spec = os.path.join(d, "t.tex"), os.path.join(d, "r.json")
    io.open(tex, "w", encoding="utf-8", newline="").write(TEX)
    json.dump(JOBS, io.open(spec, "w", encoding="utf-8"))
    run = subprocess.run([sys.executable, TOOL, tex, spec, "--apply"], capture_output=True, text=True, encoding="utf-8")
    got = io.open(tex, encoding="utf-8", newline="").read()
    assert run.returncode == 0 and "NG" not in run.stdout, run.stdout
    assert got == WANT, got  # 範囲外(3行目)は変わらない
print("ok")
