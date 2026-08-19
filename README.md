# claude-english-review

Claude をオーケストレータとする数学論文(TeX)英文修正システム。
2026-08 の Paper I 全文修正(3ラウンド点検 166 指摘+用語統一 95 箇所)で確立した手法の汎用化。

## 構成

- `PLAYBOOK.md` — オーケストレータ(Claude 本体)が従う実行手順書。フェーズ・裁定基準・収束条件・同期手順。
- `templates/` — 並列サブエージェントに渡すプロンプト雛形。`{{...}}` を置換して使う。
- `tools/apply_fixes.py` — 採用指摘の一括適用器(平坦一致アンカー、dry-run/apply)。
- `tools/coinage_scan.py` — 造語候補スキャン(「the+複合名詞句」の承認外・低頻度句)。
- `tools/glossary.py` — 単語帳生成(承認済み/emph定義/標準/先行研究/要審査に分類)。
- `tools/ledger_gate.py` — 記号を変えたのに台帳を直していないコミットを止めるゲート。原稿の記号集合の変化だけを見るので偽陽性がほぼ無く、記号を触っていなければ何も言わない。`py tools/ledger_gate.py <file.tex> <ledger.md>`。
- `tools/ledger_check.py` — 台帳と原稿の突き合わせ。既にある乖離を洗う。偽陽性が残るので基準値と比べる。
- `tools/depgraph.py` — 依存グラフと番号系列の点検(番号の欠番・重複、ラベルの無い番号付き環境、結果間の前方依存、入次数0)。印字番号は `.aux` から取る。`py tools/depgraph.py <file.tex>`。
- `config.example.json` — プロジェクト設定例。
- `rules/english-writing-rules.md` — 修正用の誤り型カタログ(実点検446件から作った10型+手続き規則)。
- `rules/notation-rules.md` — 記法の設計と点検(アクセント・添字・予約文字・命名・マクロ・台帳運用)。記号は序文で決まり本文へ波及するため、英文点検より先に確定する。
- `rules/writing-guide.md` — 新規執筆・翻訳用の文体仕様(声と時制・骨格・構成・用語衛生・禁止事項)。プロジェクト固有の規則ファイルが無い場合の既定。
- `rules/phrasebook.md` — 機能別フレーズ集(Trzeciak, Writing Mathematical Papers in English の抜粋。原本 PDF は同梱せずパス参照)。**規則の優先順位**: プロジェクト規約・writing-guide > phrasebook(相違点は phrasebook 末尾に列挙。文体の禁止事項は guide が勝つ)。

## 前提

- 対象プロジェクトに執筆規則ファイルがあること(誤り型カタログと用語規則。例: `english-writing-rules.md`、`terminology-rules.md`)。
- 機械監査スクリプト(banned リスト付き)が CLEAN を返す状態から開始する。
- 一文一行の TeX であること(行単位の指摘・置換が前提)。

## クイックスタート

1. `config.example.json` を対象プロジェクト用にコピーして書き換える。
2. Claude に「PLAYBOOK.md に従って <config> の論文の英文修正を回して」と指示する。
3. Claude がフェーズ 0(序文・記号の確定)→ A(分割点検)→ B(用語・造語・構成)→ C(同期・検証)を収束まで反復する。

## 設計原則

- **指摘と適用の分離**: エージェントは指摘のみ(別ファイル出力で競合回避)。適用はオーケストレータが裁定してからスクリプトで行う。
- **確実な適用**: すべての置換は旧文面のアサート付き。ヒット数が期待と違えば何も書かない。
- **検証ゲート**: 各適用後にビルド(×2)と機械監査を通す。レンダリング不変の変更は pdftotext 差分ゼロで確認する。
- **先行研究基準**: 用語は推測でなく原文(arXiv PDF)から実測した語彙集と照合する。
