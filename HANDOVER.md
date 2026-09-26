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
- 検証スクリプト: `/tmp/verify_finder.js`（受け入れ基準）, `/tmp/verify_alias.js`（日本語検索）。※これらは `/tmp` のため現在は消えている。2026-09-26 の検証は下記の新スクリプトで実施。
- 本文を短くしてツール呼び出しの malformed を避ける（CLAUDE.md ツール呼び出しの鉄則）。

## 2026-09-26: eBay Motors カテゴリ追加（v1.2.0 → 次バージョンで申請予定）

**背景**: 既存は通常ツリー（EBAY_US, treeVersion 134, 15,111葉/34部門/厳選4,931件）のみ。自動車・バイク・ボート等の部品出品向けに eBay Motors ツリー（treeId 100, treeVersion 83, 2026-09-08取得）を追加。

**実装（Fact）**:
- `scripts/build_categories.py`: `--motors-tree <json> --motors-curated <json>` を追加（任意引数、両方指定時のみ有効）。
  - Motors 公式ツリー(`category_tree_100.json`)の root→eBay Motors(6000)→8カテゴリ配下を再帰的に走査し、葉（`leafCategoryTreeNode:true` または子なし）を抽出。path は `"eBay Motors > ... > 葉名"`（root は含めない）。
  - 各葉に `department: "eBay Motors"`、`tree: "MOTORS"` を付与。既存の通常ツリー葉には `tree: "US"` を追加。
  - curated 判定は `motors-category-reference.json` の `sections` 配下に載っている葉ID（mark=exclude/caution を含む全1,891件）に一致するかどうか。
  - `departments` 末尾に `"eBay Motors"` を追加。`meta.motors = {treeId:"100", treeVersion:"83", source, leafCount:2965, curatedCount:1891, fetchedAt:"2026-09-08"}`。
  - 通常ツリーとMotorsツリーの categoryId 重複チェックあり（重複0件を確認）。
- `data/categories.json` 再生成: **18,076 葉 / 35 部門 / 厳選 6,822 件**（通常15,111葉・厳選4,931 ＋ Motors 2,965葉・厳選1,891）。ID重複なし（機械確認ずみ）。
- `data/aliases.json`: Motors向け日本語ジャンル語を20件追加（車/自動車→car,truck、パーツ/部品→parts、バイク/オートバイ→motorcycle、マフラー→muffler,exhaust、ホイール→wheel、タイヤ→tire、ブレーキ→brake、ヘッドライト→headlight、ミラー→mirror、ステアリング→steering、シート→seat、エンジン→engine、キャブレター→carburetor、バッテリー→battery、ボート→boat、トラック→truck、工具→tool）。各語は Motors葉のname/pathに実在することをgrepで確認ずみ。**注**: タスク指示にあった「車 部品」等スペース入りキーはそのままでは使えない（検索は語ごとにAND照合する実装のため、スペース入りキーは絶対に一致しない）。単語単位に分割して登録し、複合語検索（例:「バイク パーツ」）は既存のAND方式で成立する設計にした（判断）。
- `scripts/translate_categories.py`: SYSTEM_PROMPT にMotors向け注意（Exhaust→排気系、Mufflers→マフラー、Fenders→フェンダー等）を追記。「未収録のみ翻訳」は元から既定動作のため変更なし。
- `src/sidepanel.js` / `src/sidepanel.html` / `src/styles.css`: `tree`フィールドはそのまま透過的に扱われる（検索・ツリー・部門フィルタ・厳選トグル・お気に入りは無改修で動作、Playwright実機確認ずみ）。選択中カテゴリの eBay リンク横に、`tree==="MOTORS"`の葉だけ小さな「Motors」タグを表示する処理を追加（`#selection-motors-tag`）。部門名は既存の `selection-path`（フルパス、先頭が部門名）にそのまま出るため追加UIは不要と判断。
- `manifest.json` のバージョンは変更していない（親の判断待ち）。

**元データの所在についての事実確認（Fact）**: タスク指示は `~/Desktop/ebay-categories-full.csv` を前提としていたが、実際には存在せず、`~/Desktop/eBayカテゴリ調査/ebay-categories-full.csv` にあった（行数・treeVersion・葉数が現行categories.jsonと一致することを確認して同一ファイルと判断）。`build_categories.py`のデフォルトパスは変更せず、今回は `--full` で実パスを明示指定した。**Unknown**: なぜ既定パスと実ファイル位置がずれているか（移動した経緯）は未確認。READMEの「データの更新手順」も参照。

**翻訳（B節）— 完了（2026-09-26 追記）**:
- 親が `~/.codex/config.toml` の `OPENAI_API_KEY` を有効なキーに差し替え（キーの値はログ・本引き継ぎに一切書いていない）。
- `python3 scripts/translate_categories.py` を引数なしで実行 → Motors厳選1,891件を19バッチ全て成功（失敗0件）で翻訳。既訳4,931件は自動スキップされ、未訳分のみ処理される設計どおり動作。
- カバレッジ: **6,822/6,822（100%）**（内訳: 通常ツリー厳選 4,931/4,931、Motors厳選 1,891/1,891）。
- `data/translations_ja.json` はJSONとして妥当（`json.load`で検証）、`translations`件数6,822件（想定4,931+1,891=6,822と一致）、空文字の訳0件。
- 抜き取り20件（Motors厳選からランダム抽出、機械的に対応確認）: `262095 Battery Management Systems (BMS)→BMS` `263175 ATV & UTV Covers→ATV・UTVカバー` `262177 Truck Beds & Repair Sections→トラック荷台・補修パーツ` `263192 Stereos & Radios→ステレオ・ラジオ` `179526 Slide Hammers→スライドハンマー` `263246 Accessory Mounts→アクセサリーマウント` `173657 Dyno Headers→ダイノヘッダー` `184793 Antennas→アンテナ` `178930 Brake Sensors & Switches→ブレーキセンサー・スイッチ` `33632 Manifolds & Headers→マニホールド・ヘッダー` `184904 Suspension & Steering Links→サス・ステアリングリンク` `179512 Roller Seats & Creepers→ローラーシート・クリーパー` `100452 Brakes→ブレーキ` `184706 Brake Wheel Cylinders→ブレーキホイールシリンダー` `179412 Signs & Decor→サイン・装飾` `179494 Gear/Differential Oil→ギア・デフオイル` `263154 Roll Cages→ロールケージ` `33717 Turn Signal Light Assemblies→ウインカーランプ` `174077 Shift Knobs→シフトノブ` `263358 Manifold Intake Adapter, Inlet & Joint→インマニアダプター・接続部`。全件、英語名と訳が対応していることを目視確認。
- `grep -n China data/translations_ja.json` → 0件（不適切語なし）。

**検証（D節・実施ずみ、Fact）**:
- `python3 -c 'import json;...'` で件数・部門・tree集合・ID重複なしを確認（上記の数値どおり）。
- Playwright (`~/.npm-global/lib/node_modules/playwright`) で `--load-extension` 読み込み、`chrome-extension://<id>/src/sidepanel.html` を開いて確認:
  - 「マフラー」検索 → 81件中に `eBay Motors > ...Catalytic Converters...` がヒット（同時に「スカーフ」の日本語訳「マフラー」も上位に出るが、これは日本語の実際の多義語であり誤りではない）。
  - 「brake」→116件中の多くが `eBay Motors >` パス。「ヘッドライト」→7件全てMotors。
  - 部門フィルタで「eBay Motors」を選ぶと「brake」の結果が106件に絞り込まれ、全て `eBay Motors >` パスのみ。
  - ツリータブの部門一覧に `eBay Motors ›2,965 件のカテゴリ` が表示。
  - 「トレカ」検索は従来どおり（おすすめ2件＋参考61件、Collectibles/Toys & Hobbies配下）、回帰なし。
  - 葉を選択すると `#selection-motors-tag` が Motors葉のときだけ表示され、非Motors葉では非表示に切り替わることを確認。
  - スクリーンショット: `/private/tmp/claude-501/-Users-naokijodan/4efe65ef-f141-44fe-871b-2a339447b593/scratchpad/motors_search.png`（このセッションのスクラッチパッド。恒久保存が必要なら移動要）。

## 2026-09-26: v1.3.0 申請素材 作成（実施ずみ）

**背景**: 上記の Motors データ追加（v1.2.0→次バージョン用データ）を受けて、Chrome ウェブストア更新申請用の一式を作成した。

**実施内容（Fact）**:
- `manifest.json`: `version` を `1.2.0`→`1.3.0` に変更。`description` 末尾に「eBay Motors（自動車・オートバイ部品）のカテゴリにも対応。」を追記（125文字、132文字以内。`len()`で確認ずみ）。`permissions` は無変更（`sidePanel`, `clipboardWrite`, `storage`）。
- `docs/store-listing.md`（新規）: 概要文・詳細説明文・「更新内容（What's new）」短文・プライバシー設問回答・件数まとめ表を作成。**Unknown**: v1.2.0 申請時の掲載文言そのものを保存したファイルは見つからず（README/HANDOVER の記述にも実際の文面は残っていなかった）。そのため文面は HANDOVER と README の記述内容から新規に組み立てた（作業指示どおり「無ければHANDOVERの記述から復元」）。
- スクリーンショット: `scripts/make_screenshots.py` を再利用（`FINDER_RAW_DIR` 環境変数で生画像の入力先を指定できるよう修正。ロジック自体は変更なし）。Playwright（`~/.npm-global/lib/node_modules/playwright`）で拡張を `--load-extension` 読み込みし、`sidepanel.html` を直接開いて360x800で4枚撮影（トレカ検索／腕時計選択(日本語訳)／ツリータブ／Motors部門フィルタ+マフラー検索+葉選択）→ `make_screenshots.py` で1280x800・RGB・アルファなしに合成。
  - 新: `スクショ1_検索.png`（同じ構図・同じ文言で再生成）
  - 新: `スクショ2_日本語訳.png`（文言の件数のみ4,931→6,822に更新）
  - 新: `スクショ3_ツリー.png`（文言を34→35大分類・eBay Motors含む、に更新）
  - 新: `スクショ4_Motors.png`（旧スクショ4_検証を置き換え。eBay Motors対応をアピール。マフラー検索でMotors結果＋「Motors」タグ付き選択状態を撮影）
  - 旧4枚（v1.2.0時点）は `提出用/old-v1.2.0/` に移動して保存ずみ。
- ZIP: `提出用/ebayカテゴリー発見君-v1.3.0.zip` を、v1.2.0 と同じ13ファイル構成（manifest.json / src4点 / data4点 / icons4点）で作成。`unzip -l` で内容確認、`unzip`で取り出したmanifest.jsonの`version`が`1.3.0`であることを確認ずみ。v1.2.0のZIPは削除していない。
- README.md: バージョン表記（1.3.0）追加、ファイル構成に`docs/`と`scripts/make_screenshots.py`等を追記、「Chrome ウェブストア 申請素材」節を新設し場所を明記。
- プライバシーポリシー: 権限・データ取り扱いに変更がないため**変更していない**（`privacy-policy.html` 無改修）。

**検証（Fact）**:
- `sips` で4枚とも 1280x800 / RGB / アルファなし を確認。
- `python3 -c "import json; json.load(...)"` で `manifest.json` のJSON妥当性を確認。
- `grep -rn 'ann-pain|deepjapan'` を本プロジェクト・提出用フォルダに実行 → 0件。
- 絵文字チェック（Unicode絵文字レンジで走査）→ 今回新規作成・編集したファイル（manifest.json / docs/store-listing.md / README.md 追記部分 / HANDOVER.md 本節）に絵文字なし。矢印記号（→ ↗）は既存箇所に従来からあるナビゲーション表記で絵文字ではない。
- `data/*.json`・`scripts/build_*.py`・`src/` のロジックは無変更（今回のdiffは manifest.json のversion/description、scripts/make_screenshots.pyの入力パス変数化とSHOTS文言・ファイル名のみ）。
- eBayサイトへのアクセスなし（Playwrightは拡張のsidepanel.htmlをchrome-extension://で開いただけ）。APIキー出力なし。git commit/pushは実施していない（親のレビュー後に実施の方針どおり）。

**判断に迷った点（Fact/報告用）**:
- v1.2.0時点の実際の掲載文言ファイルが見当たらなかったため、`docs/store-listing.md` は新規に文章を組み立てた。内容はHANDOVER/READMEの事実（件数・機能・安全性）のみで構成し、誇張や未確認の効能は書いていない。
- スクショ4は「検証タブ」から「Motors対応」に差し替えた（指示の「スクショ4_Motors.png等にする」という書き方に沿った判断）。検証タブ自体の説明はストア詳細説明文の「できること」欄に文章で残している。

## 次にやること（次セッション・ユーザー承認後）
1. ~~ユーザーが実機で確認~~ → 完了（2026-09-26 ユーザーが `https://www.ebay.com/b/-/6028` を開き、「eBay > eBay Motors > Parts & Accessories（Auto Parts & Accessories）」のページが表示されることを確認。Motors 葉でも `ebay.com/b/-/<categoryId>` 形式のリンクは有効、Fact）
2. **ストア更新申請（ユーザー作業）**: Chrome Web Store Developer Dashboard で `提出用/ebayカテゴリー発見君-v1.3.0.zip` をアップロードし、`docs/store-listing.md` の文言で更新申請を提出する。プライバシー設問は「変更なし」で回答。
3. **公開後の記載更新**: 審査通過・公開後、`~/Desktop/ガイド・ドキュメント/bulk-tools-guide/extensions.html` の当該拡張の記載（バージョン・対応範囲）を更新する。
4. v1.2.0 はストアで公開済み（一般公開、2026-07-29 更新、ユーザー数96。2026-09-26 にユーザーがデベロッパーダッシュボードの画面で確認、Fact）。Motors 追加は v1.3.0 の更新申請として出す。
5. 翻訳は完了ずみ（上記参照）。次回のeBayカテゴリ改訂時は README「データの更新手順」に従い build_categories.py → translate_categories.py の順で再生成する。
