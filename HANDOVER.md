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

## 残タスク（次セッション）
1. **実機確認**: ユーザーが `chrome://extensions`→デベロッパーモード→「パッケージ化されていない拡張機能を読み込む」→このフォルダ。検索欄に「トレカ」「時計」等で動作確認。
2. **ユーザーの追加フィードバック反映**: 「使い方が難しい」への対応は日本語検索＋ガイド＋フィルタ折りたたみまで実施。さらに要望があれば対応。辞書 `aliases.json` は手で追記可能。
3. **完了処理（ルール: completion.md / STANDALONE C-S1）**: ユーザー承認後に
   - git（このフォルダは未 init。`git init`→コミットの可否をユーザーに確認）
   - Obsidian 開発ログ（`/開発ログ/` に `ebay-category-finder_開発.md`）
   - Discord 通知（`~/.claude/scripts/notify-discord.sh`）

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
