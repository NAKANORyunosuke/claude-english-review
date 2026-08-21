# 用語執筆規則(造語防止)

英語論文に技術的な名詞句を書く**前**に適用する規則。
機械検査(プロジェクトの banned リスト)は事後の網であり、本規則は生成時の関門である。

禁止パターンの実例は、2026-08-03〜04 に A-超幾何の障害論文で行った4次の駆逐(計約150語)で判明したものである。分野が違っても型は転用できる。

**プロジェクト側で埋めるもの**は3つある。banned リストのファイル名、承認済み用語の一覧の置き場(`CLAUDE.md` の規約か、プロジェクトの用語規則か)、そして日本語文書の一覧である。それ以外はどのプロジェクトでも同じ。

## 命名の決定手続き

技術的な複合名詞句(2語以上、または普通語の術語的使用)を書こうとしたら、書く前に次を順に問う。

1. **標準数学用語か**(教科書・当該分野の文献で確立しているか)。→ そのまま書く。
2. **承認リストにあるか**。→ そのまま書く。
3. **本文でこれから正式に定義する新概念か**。→ 定義する前に、**そもそも名前が要るか**を問う。記号+一般名詞で全出現を書けるなら名前を付けない。名前を与えるのは、記号で指すと文が読めなくなる中心概念だけに限り、そのときも一つの構成に一つの名前。
   **`\emph` で用語を定義しない**(`writing-guide.md` の禁止と同じ)。`\emph` は強調と証明のステップ名にだけ使う。名前を与える必要があるなら、定義文で普通に述べる(`We call ... the ...`)か、記号+一般名詞へ展開する。
   **新たに定義する語の総数を最小にする。**語が1つ増えるたびに、読者が覚える負担と、後から一物多名・適用範囲逸脱が生える余地が増える。既存の名前を地の文へ広げるときも同じ関門を通す(記号表に名前があることは、地の文でその名前を使ってよい根拠にならない)。
4. **どれでもない**。→ **その句を書かない**。次の代替で書く。
   - 記号がある対象は**記号+一般名詞**で指す(the ideal \(U_q\)、the affine semigroup \(\mathcal C(\boldsymbol w)\)、the lattice \(L_{\Phi}(x)\))。
   - 記号がなければ**普通の文に展開**する(«a boundary support» ではなく «a realized support outside \(\mathcal N\)»)。
   - 既に定義済みの語があるなら**言い換えずその語**を使う(elegant variation 禁止)。

疑わしければ造語である。
「係り受けが自然だから可」とは判断しない(support Stanley--Reisner ring は文法的に自然だが造語だった)。

## 禁止パターン(実例つき)

新規に書く文が以下の型に当てはまったら、その場で言い換える。過去の駆逐例はすべて banned リストに登録済み。

1. **名詞積み**: 修飾名詞+定義済み語で新名を作る。
   例: boundary colon ideal、obstruction Hilbert series、support data、finite boundary data。
   → 記号形(the Hilbert series of the obstruction module、the data \(K_{\bv}\), \(E_{\bv}\), …)。
2. **一物多名**: 同じ対象を場所ごとに別の句で呼ぶ。
   例: ideal-equality criterion / equality criterion / ideal equality、of the initial kind / initial index。
   → 初出で一つに決め、全箇所で同語を使う。
3. **メタファーの術語化**: 普通語に未定義の数学的意味を負わせる。
   例: visible (along/through/after)、oriented / orientation(向き付けの規約を言う場合は written so that … のように内容を書く)、separated、propagates、amplification。
   → 主張内容を陳述する(the part represented by multiples of \(e\))。
   なお measures・persists・places … in・intertwines・detects 等、**内容を代行しない**普通の数学英語の動詞は可。
4. **定義済み形容詞の適用範囲逸脱**: 集合に定義した形容詞を要素に流用する等。
   例: admissible cells(admissible は collection の属性)、marked row(定義済みは marked set のみ)。
   → 定義どおりの対象にだけ付け、他は展開する(the coordinates in the marked set)。
5. **引用結果への命名**: 他論文の定理・命題に呼び名を発明する。
   例: the support-extension result、the complete Frobenius theorems。
   → 番号で引く(Proposition~6.3 and Corollary~6.4 of \cite{OS25})。
6. **圧縮逆参照の名前化**: 既出の構成を短縮句で再指示し、それが名前として振る舞う。
   例: the product collection、the other colon image。
   → 記号か完全な句で再指示する。
7. **ad hoc ハイフン連結**: ideal-equality criterion、proper-initial case、inverse-system obstruction complexes。
   → 文法的複合修飾語(five-column、three-connected)と標準用語(rank-deficient、ideal-theoretic)以外のハイフン新造を禁止。

## 許されるもの

- 標準用語・承認済み用語・本文が定義文で導入した新概念(`\emph` は使わない)。
- 文法的な数量複合修飾語(five-column configuration、one-block、all-ones row)。
- 表示式・記号に係留された普通名詞(the displayed jump、the two tables、the extended family ― 直前の動詞 extend の分詞的逆参照)。
- 出典が明示された輸入用語(本文に帰属を明記したもの)。

## 運用

- 新しい文を書いたら、提出前に必ず tex-style-audit(プロジェクトの banned リスト付き)を実行する。
- 過去に排除した語を**別綴り・別語形で再導入しない**(weight check → weight condition の再発例がある)。動詞形・形容詞形も同罪。
- 造語を1語でも排除したら banned リストに追加し、本規則の実例が増える場合はここに追記する。
- **日本語文書では排除語の訳語も同時に排除する。**英語文字列の照合でも日本語単独の照合でもすり抜けるので、和英混成形(`Prym格子`・`Gr\"obner半群` 等)は組版後の PDF で見る。
- 疑わしい句の網羅探索には同梱の `tools/coinage_scan.py` と `tools/glossary.py`、および並列エージェント走査を使う。

## プロジェクト側に置くもの

このファイルは型だけを持つ。次はプロジェクトごとに違うので、プロジェクトの規約か用語規則に置く。

- **承認済み用語の一覧**(本文が定義文で導入する語の全部、出典を明示して輸入する語、その論文固有の語感)。
- **banned リスト**のファイル名と中身。
- **日本語文書**の一覧。
