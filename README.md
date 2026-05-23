# eBay Category Finder（手動出品用 カテゴリID 検索拡張）

eBay に1件ずつ手動出品するとき、その商品に合う **eBay カテゴリID** を素早く見つけるための Chrome 拡張機能です。
**完全オフラインで動作し、eBay には一切アクセスしません**（同梱した静的データだけを使います）。

- マーケットプレイス: **EBAY_US**
- treeVersion: **134**
- 収録: **15,111 葉カテゴリ / 34 部門**（うち厳選版 **4,931 件**）

---

## できること

1. **キーワード検索** — 英語キーワード（例: `Wristwatch`, `Reel`, `Card`）で候補をフルパス付き一覧表示。スペース区切りで AND 検索。
2. **ツリーを辿る** — 34 部門 → 枝 → 葉までドリルダウン。パンくずで上の階層へ戻れます。
3. **IDコピー** — 見つけた categoryID をワンクリックでコピー。
4. **検証** — categoryID を入力すると、その正式パスを表示。存在しなければ「存在しません」と表示。
5. **絞り込み** — 部門で絞る／「厳選版のみ」（一括ツールが使う 4,931 件）に切替。

---

## インストール手順（はじめて使うとき）

1. Google Chrome で `chrome://extensions` を開きます。
2. 右上の **「デベロッパーモード」** をオンにします。
3. **「パッケージ化されていない拡張機能を読み込む」** をクリックします。
4. このフォルダ **`ebay-category-finder`** を選びます。
5. Chrome ツールバーの拡張アイコン（パズルのピース）から **「eBay Category Finder」** をクリックすると、画面右側にパネルが開きます。

> アイコンを常に表示したいときは、ツールバーのパズルピースから「eBay Category Finder」をピン留めしてください。
> 必要な Chrome バージョン: **114 以上**（サイドパネル機能のため）。

---

## 使い方

- **検索タブ**: 上の欄に英語キーワードを入力 → 下に候補が出ます。行をクリックすると上部に categoryID とフルパスが大きく表示され、「コピー」できます。
- **ツリータブ**: 部門をクリックして枝・葉へと辿ります。葉（末端）をクリックすると選択され、コピーできます。
- **検証タブ**: categoryID を入力すると、その正式なカテゴリパスが出ます。
- **部門で絞り込み** / **厳選版のみ**: 検索とツリーの両方に効きます。
- **「eBay のカテゴリページを開く ↗」**: 任意。クリックしたときだけ、あなたのブラウザで eBay の該当ページを開きます（拡張自身は eBay にアクセスしません）。

---

## データの更新手順（eBay がカテゴリを改訂したとき）

eBay は年に数回カテゴリを改訂します。最新化するには次の手順です。

1. eBay 公式の Taxonomy API `getCategoryTree`（`~/Desktop/ebay-manager` 等）で最新ツリーを取得し、CSV を更新します。
   - `~/Desktop/ebay-categories-full.csv`（列: `categoryId,department,level,categoryName,fullPath`）
   - `~/Desktop/ebay-categories-curated.csv`（厳選版・任意）
2. 生成スクリプトを実行して同梱データを作り直します。
   ```bash
   cd ~/Desktop/ebay-category-finder
   python3 scripts/build_categories.py
   ```
   実行後、収録件数・部門数・treeVersion がターミナルに表示されます。
3. `chrome://extensions` で拡張の **更新（再読み込み）** ボタンを押します。
4. 新しい treeVersion を控え、この README の数値も更新してください。

> **`data/categories.json` は自動生成物です。手で編集しないでください。**

---

## ファイル構成

```
ebay-category-finder/
├── manifest.json              拡張の定義（Manifest V3・サイドパネル・最小権限）
├── README.md                  このファイル
├── src/
│   ├── service_worker.js      アイコンクリックでサイドパネルを開く
│   ├── sidepanel.html         画面
│   ├── sidepanel.js           検索・ツリー・コピー・検証のロジック
│   └── styles.css             見た目
├── data/
│   └── categories.json        同梱データ（自動生成・手編集禁止）
└── scripts/
    └── build_categories.py    CSV → categories.json 生成スクリプト
```

---

## 安全性（eBay アカウント保護）

- 実行時に eBay や外部サーバーへ一切アクセスしません（`host_permissions` なし）。
- スクレイピング・自動操作は行いません。データは取得済み CSV から生成した静的 JSON のみ。
- eBay ページを開くのは「リンクをあなたが手動でクリックしたとき」だけです（任意機能）。
