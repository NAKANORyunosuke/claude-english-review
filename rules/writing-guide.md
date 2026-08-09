# 数学英語の書き方(新規執筆・翻訳用の文体仕様)

`english-writing-rules.md` が「直すとき」の誤り型カタログであるのに対し、本書は「書くとき」の仕様。
規範原本は `D:\Workspace\TeX\EnglishBible\mathematical-writing.md` と `matsumoto-style-guide.md`(あればそちらを優先して全文読む)。

## 声と時制

- 数学的行為の主語はすべて "we"。現在形で通す(論文内の既出参照のみ現在完了、歴史的事実のみ過去形)。
- 受動態は命名・輸入にのみ: "is defined by", "is called", "is denoted by", "It is shown in [X] that"。
- 法助動詞は "can" が基本。論理的必然は "must"(should は使わない)。「〜とは限らない」は "need not"。
- 先行研究の数学的結果は現在形: "X proves ...", "Theorem Y states ..."。

## 文の骨格

- 三大型: "Since A, we have B." / "By X, we have Y." / "Using X, we obtain Y."。帰結は Thus/Hence/Therefore をローテーション。
- 導入儀式: We set / We put / We define ... by / We fix / We choose / We denote ... by。"Let X be ..." は仮定用。
- 定理の前触れ(herald)は1文: "Then we have the following proposition." / "We prepare a lemma on ..."。
- ディスプレイ式の直後に "where" インベントリで全記号を列挙する。式の意味づけは ", which implies/yields that ..."。
- 証明は即行動で開始("Proof. We set ...")、段階は "First, ... Next, ... Finally, ..."、対称ケースは "in a similar way"、終端は □。
- 文を記号で始めない。ディスプレイ式にも句読点。1文=1行(TeX ソース)。

## 構成

- Abstract: 2〜5文、全文 "We ..."。背景・動機・文献番号なし。
- Introduction: コールドオープン(定義か式)→ 先行研究は受動態1文+文献括弧 → "However, ..." → "In this paper, we ..." → 定理番号を本文に埋め込む。ロードマップ段落は書かない。
- セクション冒頭に1文の目的宣言。恒常仮定は "Throughout this paper, we assume ..."。締めの文は書かない。
- 既知の結果は "Fact 2.3 ([X])." で輸入。補足は番号付き Remark に隔離。

## 記号と用語の衛生

- 記号は使用前に \emph で定義。一物一名(同じ対象は毎回同じ語。elegant variation 禁止)。
- 技術的な複合名詞句は書く前に用語規則の関門を通す: 標準用語か → 承認済みか → \emph で定義する新概念か → どれでもなければ**書かず**に記号+一般名詞か普通の文に展開。
- 引用結果に名前を発明しない(番号で引く)。既出構成の短縮句を名前化しない。ad hoc なハイフン連結をしない。
- 先行研究の用語は原文の形を実測して使う(例: DMM の標準形は basic Nilsson solution・domain of convergence)。

## 禁止(ゼロ違反)

- 評価形容詞(important, interesting, remarkable, novel ...)、ヘッジ(seems, perhaps, essentially ...)、読者管理修辞(it is worth noting, unfortunately ...)、文頭 Clearly/Obviously/Indeed。
- 対比の while/whereas(→ but か2文に分割)。文頭 Although(→ Though)。
- ":=" (→ define/put/set + =)。定理環境の括弧題。数式記号の 's 複数形。

## 日本人が特に誤る点(機械的に自己検査)

冠詞(単数可算名詞に必須、"in the direction \(\bw\)")・contradicts X(to 不要)・equals X・"a system of parameters for"・based at・consequence of・単複一致・comma splice("Substituting ..., we have ...")・"the map is an isomorphism"(isomorphic は空間用)・In particular(文頭 Especially 不可)・First(At first 不可)。
