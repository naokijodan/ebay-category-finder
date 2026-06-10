# 引き継ぎ — ebayカテゴリー発見君（Chrome拡張 / 旧称 eBay Category Finder）

場所: `~/Desktop/ebay-category-finder/`
モード: STANDALONE
名称: **ebayカテゴリー発見君**（2026-05-24 変更。manifest / sidepanel.html 反映ずみ）
アイコン: `icons/icon{16,32,48,128}.png`（青角丸＋白虫眼鏡）。生成は `scripts/make_icon.py`。manifest の `icons` と `action.default_icon` に登録ずみ。

## このプロジェクトは何か
eBay に手動出品するとき、商品に合う **カテゴリID** を探す Chrome 拡張（Manifest V3・サイドパネル）。
完全オフライン、**eBay には一切アクセスしない**（同梱 JSON のみ）。元の指示文: `~/Desktop/ebay-category-finder_拡張機能_指示文.md`。

## できていること（実装・検証ずみ）
- データ: `data/categories.json`（葉 **15,111件 / 34部門 / 厳選 4,931件**、EBAY_US treeVersion 134、2.62MB）。生成は `scripts/build_categories.py`（CSV→JSON、手編集禁止）。
- 機能: ①キーワード検索 ②ツリー(34部門→葉) ③IDコピー ④検証 ⑤部門/厳選フィルタ。
- 受け入れ基準: 9/9 パス（Wristwatch→31387、Reel→261030、検証、34部門 等）。
- バグ修正: アクセント無視検索（`pokemon`→`Pokémon`）。例文の `Pokemon` は撤去ずみ。
- 追加: **日本語ジャンル検索**。`data/aliases.json`（約70語、トレカ/フィギュア/時計…）。検索 7/7 パス（トレカ→CCG Individual Cards 183454 等、辞書全キーがヒット、誤ヒットなし）。
- UI改善: 画面上部に使い方ガイド（① 言葉→② 候補→③ コピー）、絞り込みを開閉式に。

## Git / 公開（2026-05-24 完了）
- 本体リポジトリ(PUBLIC): https://github.com/naokijodan/ebay-category-finder （commit 8231639、push済み）
- プライバシーポリシー(PUBLIC): https://github.com/naokijodan/ebay-category-finder-privacy
- プライバシーポリシー公開URL: https://naokijodan.github.io/ebay-category-finder-privacy/
- 公開前に秘密情報フルスキャン→検出ゼロ。`.gitignore` あり。`git add -A` 不使用（明示add）。

## Chrome ウェブストア 申請素材（2026-05-24 完了）
場所: `~/Desktop/ebayカテゴリー発見君_提出用/`
- `ebayカテゴリー発見君-v1.0.0.zip`（提出用・manifest直下・scripts/docs除外）
- `アイコン_128x128.png`（ストアアイコン）
- `スクショ1〜4_*.png`（1280x800・24bit PNG・アルファなし）。生成 `scripts/make_screenshots.py`
- `privacy-policy.html`
- 概要文・詳細説明文・「プライバシーの取り扱い」フォーム回答 → このセッションのチャットに記載

## 2026-06-10: v1.1.0 おすすめ固定表示（審査送信済み）
**背景**: EAGLE のトレカ用テンプレは細かいカードコンディション前提。CCG/スポーツトレカ以外（非スポーツトレカ 183050系）は一律USEDでエラーになる。「スポーツトレカ」検索は「非スポーツトレカ〜」だけ誤ヒットし正解0件だった。
**実装（Fact）**:
- `data/recommendations.json`（新規）: 検索語→おすすめID。正規化＋スペース除去クエリに部分一致・最長キー優先。「トレカ」→[183454, 183455]（CCGシングル/まとめ）、「スポーツカード」「スポーツトレカ」→[261328, 261329]（Sports Singles/Lots）。
- おすすめは「おすすめ」バッジ付きで最上部固定、下に「参考」区切り→通常ヒット全件（重複ID除外）。通常ヒット0でもおすすめ表示。非該当クエリは従来と完全同一動作。
- 訳語4件変更: 183454「トレカシングル（CCG）」/ 183455「トレカまとめ売り（CCG）」/ 261328「スポーツカードシングル」/ 261329「スポーツカードまとめ」。
- manifest 1.0.0→1.1.0。変更は sidepanel.js / styles.css / translations_ja.json(4件のみ) / recommendations.json / manifest.json。
**検証**: 機械テスト14/14 PASS（/tmp/verify_reco.js）・独立レビューPASS（eBayアクセスなし・権限追加なし）・Playwright実画面確認済み。
**申請**: `~/Desktop/ebayカテゴリー発見君_提出用/ebayカテゴリー発見君-v1.1.0.zip` を 2026-06-10 ユーザーが審査送信済み。

## 残タスク（次セッション）
1. **ストア審査結果待ち**（v1.1.0 審査送信済み 2026-06-10）。
2. **実機確認**: `chrome://extensions`→拡張を更新(⟳)→「トレカ」「スポーツカード」でおすすめ表示を確認。
3. **将来課題**: 正規化のNFKC化／1文字ジャンル語の許可リスト化／残り英語のみカテゴリ(10,180件)の翻訳／おすすめの他ジャンル展開（recommendations.json に追記するだけ）。

## 大仕事: 各カテゴリの日本語訳 — ✅ 完了（2026-05-24）
**目的**: 厳選版カテゴリに日本語訳を付け、(1) 検索ワードとマッチ (2) 候補の各行に日本語を主役表示（高齢者でも分かるように） (3)「トレカ シングル」等の複合語で検索可能に。→ すべて実装・検証ずみ。

**実装内容（Fact）**:
- 翻訳: 厳選版 **4,931件すべて**を OpenAI API（`gpt-5.4-mini`）で日本語訳。カバレッジ100%・誤訳ゼロ。
- データ: `data/translations_ja.json`（`{meta, translations:{id→日本語訳}}`）。`categories.json` は無改変（自動生成物のため）。`sidepanel.js` が起動時に `aliases.json` 同様に合成する。
- 生成スクリプト: `scripts/translate_categories.py`（再生成・再開可。`--limit`/`--force`/`--batch-size`）。APIキーはコードに書かず環境変数か `~/.codex/config.toml` から実行時に読む。出力にキーは入れない。
- 翻訳プロンプト: ジャンル語（トレカ/フィギュア/腕時計/シングル/まとめ/未開封 等）を含めて訳す。各カテゴリを独立に訳す（文脈引きずり防止）。
- `sidepanel.js`: `_search` に `ja` を追加。各行は日本語訳を大きく(主役)・英語名を小さく(補助)表示。検索照合は「英語語(alias) または 訳語に語が含まれる(2文字以上)」。`scoreLeaf` も `ja` 対応。検証パネルにも `ja` 表示。
- `styles.css`: `.result-ja`(15px 太字)/`.result-en`(11px 補助)を追加。
- 検証: `/tmp/verify_ja.js` 8/8 PASS（「トレカ シングル」→183454 等）。回帰 `/tmp/verify_alias.js` 7/7・`/tmp/verify_finder.js` 9/9。
- 文脈引きずり誤訳（「トレカレギンス」等20件）を1件ずつ再翻訳で修正ずみ。

**未実施（次セッション・ユーザー承認後）**: 実機確認 → git init/コミット → Obsidian開発ログ → Discord通知。
**任意の将来課題（Codexレビュー指摘・今回見送り）**: 正規化を NFKC 化（全角半角/かな揺れ吸収）。1文字ジャンル語（本/靴等）の許可リスト化。残り英語のみカテゴリ(10,180件)の翻訳。

## 注意
- eBay 非アクセス厳守（host_permissions なし）。
- 検証スクリプト: `/tmp/verify_finder.js`（受け入れ基準）, `/tmp/verify_alias.js`（日本語検索）。
- 本文を短くしてツール呼び出しの malformed を避ける（CLAUDE.md ツール呼び出しの鉄則）。
