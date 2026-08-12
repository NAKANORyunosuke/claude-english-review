# 英文執筆規則(Codex 等の生成エージェント向け)

本文の英語を1文でも書く・直すときに適用する。
根拠は 2026-08-07 に Paper I 正本 5944 行を12分割して行った全文点検で、446 件の指摘が出た。
1.1--1.10 は**実際にこの原稿で起きたもの**であり、頻度順に並べてある。1.11 は文体方針として足したもの。
用語(造語禁止)は `terminology-rules.md`、体裁は `CLAUDE.md` 規約1--14 を先に満たすこと。

---

## 1. 書く前に守る11型

### 1.1 代名詞に先行詞を与える(41件・最多)

`it` / `its` / `this` / `the latter` は、直前の名詞句が一意に決まるときだけ使う。
主語が2つ以上ある文、直前に別の名詞が挟まる文では**必ず名詞を書く**。

- 悪い: `Its image is finite-dimensional because it is contained in \(\mathcal V_{\boldsymbol w}\).`
- 良い: `The image of \(\mathscr F_{\bv,\mathcal N}\) is finite-dimensional because it is contained in \(\mathcal V_{\boldsymbol w}\).`
- 悪い: `By \eqref{eq:one-block-G}, its annihilator is \(G_i\).`
- 良い: `By \eqref{eq:one-block-G}, the annihilator of \(\overline e_i\) is \(G_i\).`
- 悪い: `This is well-defined, and \(a_1<\cdots<a_m\).`
- 良い: `The number \(a_k\) is well-defined, and \(a_1<\cdots<a_m\).`

### 1.2 修飾句の係り先を主語に合わせる(40件)

分詞・不定詞の暗黙の主語は主節の主語と一致させる。
一致しないなら受動態にするか、主語を明示する。

- 悪い: `Two rows in distinct parallel classes belong to a three-element circuit after choosing a row in a third parallel class.`(選ぶ主体が「2行」になる)
- 良い: `Two rows in distinct parallel classes, together with a row in a third parallel class, form a three-element circuit.`
- 悪い: `Before imposing the remaining form in \eqref{eq:connected-U}, the module is`(課す主体が「加群」になる)
- 良い: `Before the remaining form in \eqref{eq:connected-U} is imposed, the module is`

関係節も同じ。`X with a Y whose Z` と書くと `Z` は `Y` の属性になる。`Z` が `X` の属性なら、コンマで切るか `for which` を使う。

- 悪い: `a configuration of lattice rank 2 with a normal affine semigroup whose obstruction has dimension one`
- 良い: `a configuration of lattice rank 2, with a normal affine semigroup, whose obstruction has dimension one`

### 1.3 語を離さない(33件)

動詞と目的語、動詞と `as ...` 補語の間に長い挿入を置かない。

- 悪い: `Theorem X expresses the failure of taking a colon after applying \(\Phi_0\) at each factor of \(e\) as the image of a \(\operatorname{Tor}_1\) map.`
- 良い: `Theorem X expresses, as the image of a \(\operatorname{Tor}_1\) map, the failure of taking a colon after applying \(\Phi_0\) at each factor of \(e\).`

### 1.4 数学的動作に正しい動詞を選ぶ(31件)

- 悪い `places X in Y` → 良い `shows that X lies in Y`
- 悪い `the colon by \(e\) commutes with base change` → 良い `taking the colon by \(e\) commutes with base change`
- 悪い `gives vanishing` → 良い `proves vanishing` / `gives the vanishing of \(\mathfrak D_{\mathcal N}(e)\)`
- 悪い `Applying \eqref{eq:connected-Phi} to ...`(式番号は写像ではない) → 良い `Applying \(\Phi\) to ...`
- 悪い `the map is isomorphic` → 良い `the map is an isomorphism`
- 悪い `states the criterion as an equality` → 良い `expresses the criterion as an equality`

### 1.5 `while` / `whereas` を等位接続詞に使わない(28件)

対比なら `but`、無関係な並列なら**2文に分ける**。
`while` は時間的同時性にだけ使う。

- 悪い: `The index set of \(m_{\bv,\mathcal N}\) is independent of \(B\), while its polynomial expression depends on \(B\).`
- 良い: `The index set of \(m_{\bv,\mathcal N}\) is independent of \(B\), but the polynomial expression of \(m_{\bv,\mathcal N}\) depends on \(B\).`
- 悪い: `Nagamine \cite{Nag26} studies the local fake indicial inverse system, while the present paper studies the quotient ...`
- 良い: 2文に分割する。

### 1.6 冠詞(26件)

単数可算名詞には必ず冠詞。
未導入の対象に `the` を付けない。

- 悪い: `differentiating with respect to the perturbation parameters`(未導入) → 良い `... the resulting perturbation parameters`
- 悪い: `in direction \(\boldsymbol w\)` → 良い `in the direction \(\boldsymbol w\)`

### 1.7 同じ対象は同じ語で呼ぶ(22件)

言い換え(elegant variation)は禁止。
実際に混在していた例: `polynomial model` / `polynomial quotient`、`degreewise dual` / `graded dual`、`arrow` / `map`、`order` / `ordering`、`Formula` / `Equation`。
書く前に、その対象が既に本文で何と呼ばれているかを grep して確認する。

### 1.8 単複の一致(22件)

- 悪い: `no column permutation and invertible row transformation put its matrix into ...`
- 良い: `... puts its matrix into ...`

### 1.9 前置詞(16件)

- `a system of parameters` **for** a ring(`on` ではない)
- `based` **at** an exponent(`in` ではない)
- `contradicts X` / `equals X` / `approaches X`(`to` を足さない)
- `a consequence` **of**(`from` ではない)

### 1.10 主張の射程を合わせる(4件だが最も危険)

定理が導く結論を「要求する」と書かない。
反例が1つあるだけの性質を「常に成り立たない」と書かない。

- 悪い: `Theorem X requires the linear forms to form a regular sequence.`(定理は仮定していない、導いている)
- 良い: `Theorem X forces the linear forms to be a regular sequence.`
- 悪い: `the obstruction dimension is not monotone` → 良い `the obstruction dimension need not be monotone`

### 1.11 主語を短くする

**動詞に届くまでに8語を超える主語**は書き換える。手段は次の3つで、上から順に試す。

1. `we` を主語にして長い名詞句を動詞の後ろへ回す。
2. 仮主語 `It` を立てて `that` 節を後ろへ送る(`It follows from X that ...` / `It is equivalent to ... that ...`)。
3. 受動態にして長い名詞句を `by` 句へ送る。命名・輸入以外の受動態はここでだけ許す(`writing-guide.md` の受動態制限の例外)。

- 悪い: `That the annihilator of \(\overline e_i\) equals \(G_i\) for every \(i\) follows from \eqref{eq:one-block-G}.`
- 良い: `It follows from \eqref{eq:one-block-G} that the annihilator of \(\overline e_i\) equals \(G_i\) for every \(i\).`
- 悪い: `A column permutation and an invertible row transformation preserving the parallel classes of \(A\) put the matrix into the form \eqref{eq:normal-form}.`
- 良い: `The matrix is put into the form \eqref{eq:normal-form} by a column permutation and an invertible row transformation preserving the parallel classes of \(A\).`
- 悪い: `The failure of taking a colon after applying \(\Phi_0\) at each factor of \(e\) is measured by \(\mathfrak D_{\mathcal N}(e)\).`
- 良い: `We measure by \(\mathfrak D_{\mathcal N}(e)\) the failure of taking a colon after applying \(\Phi_0\) at each factor of \(e\).`

短くできない主語は、その名詞句自体を記号で置く(`Set \(N=\dots\). Then \(N\) ...`)。

---

## 2. その他に多かったもの

- 目的語の欠落: 悪い `is equivalent to vanishing` → 良い `is equivalent to the vanishing of \(\mathfrak D_{\mathcal N}(e)\)`
- 先行研究は現在形: 悪い `this method was developed by Saito` → 良い `this method is developed by Saito`
- コンマ列挙を `and` で閉じる: 悪い `\(t_3^2+t_3t_6, \qquad 2t_3^2+t_3t_6\)` → 良い `... \qquad\text{and}\qquad ...`
- マクロの不統一: `\mathbb Z` と `\Z` を混在させない(本文のマクロに合わせる)。

---

## 3. 既存の文を直すときの手続き規則

英語点検の適用時に事故が起きたのはここなので、機械的に守る。

1. **完全な文を出力する。** 直したい語句だけでなく、**その行全体**を差し替え可能な形で書く。断片や「この語をこう変える」という指示文を出力しない。
2. **節を落とさない。** 元の行にある `\ref` / `\eqref` / `\cite` / 数式 / `\item` は、直後の文へ移すか、そのまま残す。1文が長すぎるなら**2文に分割**し、両方の内容を保つ。
3. **一文一行を守る。** 分割したら改行して2行にする(`CLAUDE.md` 規約1)。
4. **英語修正の依頼で数学を足さない。** 新しい主張・新しい仮定・新しい記号を導入しない。必要だと思ったら本文を変えずに指摘だけする。
5. **用語を新造しない。** `terminology-rules.md` の命名手続きを通す。

---

## 4. 書いた後の自己検査

提出前に必ず次を実行し、すべて通ってから完了とする。

```
py "C:\Users\toppo\.claude\skills\tex-style-audit\audit_tex.py" <file.tex> --banned "C:\Users\toppo\.claude\skills\tex-style-audit\banned-terms-nagamine.txt"
```

- audit が `CLEAN` であること。
- `pdflatex` を2回通し、**Overfull 0・未定義参照 0** であること。
- 正本を直したら arXiv 版へ同じ数学的内容を反映すること(`CLAUDE.md` 同期チェックリスト)。
- 自分が書いた文を読み返し、上の11型を1つずつ当てること。特に 1.1(代名詞)と 1.5(while)は機械的に grep できる。1.11(長い主語)は最初の動詞までの語数を数える。
