"use strict";

// eBay Category Finder — サイドパネル本体。
// 同梱の data/categories.json だけを使う完全オフライン動作。eBay には一切アクセスしない。

const MAX_RESULTS = 200; // 検索結果の表示上限 (件数自体は全件カウントする)

// アクセント記号を無視して比較するための正規化。
// 例: eBay の "Pokémon" を、ユーザー入力 "pokemon" でも検索できるようにする。
function normalizeText(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// 日本語ジャンル辞書 (data/aliases.json) の英語語を、単語単位+複数形で照合する正規表現を作る。
// 例: "watch" は "Watches" に一致し、"cap" は "Capacitor" には一致しない。
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function aliasWordRegex(word) {
  const w = normalizeText(word);
  const body = /y$/.test(w) ? escapeRegex(w.slice(0, -1)) + "(y|ies)" : escapeRegex(w) + "(es|s)?";
  return new RegExp("\\b" + body + "\\b");
}

// ---- 状態 ----
const state = {
  leaves: [], // [{id, name, path, department, curated}]
  byId: new Map(), // id -> leaf
  root: null, // ツリーのルートノード
  departments: [],
  deptFilter: "", // 部門フィルタ ("" = すべて)
  curatedOnly: false, // 厳選版のみ
  treePath: [], // ツリーの現在地 (セグメント名の配列)
  selectedId: null,
  aliasMatchers: new Map(), // 正規化した日本語ジャンル -> 英語語の正規表現配列
  recommendations: [], // [{normalizedKeys: string[], ids: string[]}] おすすめカテゴリ一覧
};

// ---- DOM ----
const els = {};
function cacheEls() {
  const ids = [
    "meta-line", "selection", "selection-id", "selection-path", "selection-ebay-link",
    "copy-btn", "department-filter", "curated-toggle", "search-input", "search-status",
    "search-results", "breadcrumb", "tree-list", "verify-input", "verify-result",
  ];
  for (const id of ids) {
    els[id] = document.getElementById(id);
  }
}

// ---- ツリー構築 ----
function buildTree(leaves) {
  const root = { name: "", children: new Map(), leaf: null };
  for (const leaf of leaves) {
    const segs = leaf.path.split(" > ");
    let node = root;
    for (let i = 0; i < segs.length; i++) {
      const seg = segs[i];
      if (!node.children.has(seg)) {
        node.children.set(seg, { name: seg, children: new Map(), leaf: null });
      }
      node = node.children.get(seg);
      if (i === segs.length - 1) {
        node.leaf = leaf;
      }
    }
  }
  computeFlags(root);
  return root;
}

// 各ノードに「配下に厳選版の葉があるか」「配下の葉の総数」を付与する。
function computeFlags(node) {
  let hasCurated = node.leaf ? node.leaf.curated : false;
  let leafTotal = node.leaf ? 1 : 0;
  for (const child of node.children.values()) {
    computeFlags(child);
    hasCurated = hasCurated || child.hasCurated;
    leafTotal += child.leafTotal;
  }
  node.hasCurated = hasCurated;
  node.leafTotal = leafTotal;
}

function getNode(path) {
  let node = state.root;
  for (const seg of path) {
    if (!node || !node.children.has(seg)) return null;
    node = node.children.get(seg);
  }
  return node;
}

// ---- 選択 ----
function selectLeaf(leaf) {
  state.selectedId = leaf.id;
  els["selection"].classList.remove("hidden");
  els["selection-id"].textContent = leaf.id;
  els["selection-path"].textContent = leaf.path;
  const link = els["selection-ebay-link"];
  link.href = `https://www.ebay.com/b/-/${encodeURIComponent(leaf.id)}`;
  link.classList.remove("hidden");
  resetCopyButton(els["copy-btn"], "コピー");
}

function resetCopyButton(btn, label) {
  btn.textContent = label;
  btn.classList.remove("copied");
}

// ---- コピー ----
async function copyText(text, btn, doneLabel) {
  let ok = false;
  try {
    await navigator.clipboard.writeText(text);
    ok = true;
  } catch (_e) {
    // セキュアコンテキスト外などのフォールバック
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      ok = document.execCommand("copy");
    } catch (_e2) {
      ok = false;
    }
    ta.remove();
  }
  if (btn) {
    const prev = btn.textContent;
    btn.textContent = ok ? doneLabel : "失敗";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = prev;
      btn.classList.remove("copied");
    }, 1200);
  }
}

// ---- 葉の行を生成 (検索結果・ツリー共通) ----
function createLeafItem(leaf, options = {}) {
  const li = document.createElement("li");
  li.className = "result-item";

  const main = document.createElement("div");
  main.className = "result-main";

  // 日本語訳があれば日本語を主役 (大きく) に、英語名を補助 (小さく) として下に出す。
  // 高齢の利用者でも日本語だけで意味が分かるようにするため。
  if (leaf.ja) {
    const jaRow = document.createElement("div");
    jaRow.className = "result-ja";
    jaRow.textContent = leaf.ja;
    if (leaf.curated) {
      const badge = document.createElement("span");
      badge.className = "badge-curated";
      badge.textContent = "厳選";
      jaRow.append(" ");
      jaRow.append(badge);
    }
    main.append(jaRow);

    const enRow = document.createElement("div");
    enRow.className = "result-en";
    enRow.textContent = leaf.name;
    main.append(enRow);
  } else {
    const nameRow = document.createElement("div");
    nameRow.className = "result-name";
    nameRow.textContent = leaf.name;
    if (leaf.curated) {
      const badge = document.createElement("span");
      badge.className = "badge-curated";
      badge.textContent = "厳選";
      nameRow.append(" ");
      nameRow.append(badge);
    }
    main.append(nameRow);
  }

  if (options.showPath !== false) {
    const pathRow = document.createElement("div");
    pathRow.className = "result-path";
    pathRow.textContent = leaf.path;
    main.append(pathRow);
  }

  const idSpan = document.createElement("span");
  idSpan.className = "result-id";
  idSpan.textContent = leaf.id;

  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "mini-copy";
  copyBtn.textContent = "コピー";
  copyBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    copyText(leaf.id, copyBtn, "済");
  });

  li.append(main, idSpan, copyBtn);
  li.addEventListener("click", () => selectLeaf(leaf));
  return li;
}

// ---- おすすめカテゴリ選定 ----
// クエリのスペース除去文字列 qNoSpace に部分一致するキーを持つエントリを探し、
// 最長キー優先でエントリを返す。該当なしは null を返す。
function findRecommendation(qNoSpace) {
  let bestEntry = null;
  let bestKeyLen = -1;
  for (const entry of state.recommendations) {
    for (const key of entry.normalizedKeys) {
      if (qNoSpace.includes(key) && key.length > bestKeyLen) {
        bestEntry = entry;
        bestKeyLen = key.length;
      }
    }
  }
  return bestEntry;
}

// ---- 検索 ----
function runSearch() {
  const query = normalizeText(els["search-input"].value.trim());
  const list = els["search-results"];
  list.replaceChildren();
  if (!query) {
    els["search-status"].textContent = "キーワードを入力してください。";
    return;
  }
  const terms = query.split(/\s+/).filter(Boolean);
  const joined = terms.join(" ");

  // スペースを除去した文字列でおすすめを選定する。
  const qNoSpace = terms.join("");
  const recoEntry = findRecommendation(qNoSpace);

  // おすすめIDのSet（通常ヒットから除外するため）。
  const recoIds = recoEntry ? new Set(recoEntry.ids) : new Set();

  // 各キーワードを {plain: 語そのもの, alias: 英語語の正規表現群|null} に変換。
  // 照合は「英語語(alias)に一致」または「語が訳文等にそのまま含まれる(plain)」のどちらかで採用。
  const termMatchers = terms.map((t) => {
    const res = state.aliasMatchers.get(t);
    return { plain: t, alias: res || null };
  });

  let pool = state.leaves;
  if (state.deptFilter) pool = pool.filter((l) => l.department === state.deptFilter);
  if (state.curatedOnly) pool = pool.filter((l) => l.curated);

  const matches = [];
  for (const leaf of pool) {
    // おすすめと重複するIDは通常ヒット側から除外する。
    if (recoIds.has(leaf.id)) continue;
    const hay = leaf._search; // 起動時にアクセント除去・小文字化済み
    const ok = termMatchers.every((m) => {
      const aliasOk = m.alias && m.alias.some((re) => re.test(hay));
      // alias語(例「時計」)は、訳語(_ja)にそのまま含まれる場合も拾う。
      // 英語名/パスへの偶発一致を避けるため _ja に限定し、誤検出防止に2文字以上に限る。
      const plainOk = m.alias ? m.plain.length >= 2 && leaf._ja.includes(m.plain) : hay.includes(m.plain);
      return aliasOk || plainOk;
    });
    if (ok) matches.push(leaf);
  }

  matches.sort((a, b) => scoreLeaf(b, joined, terms) - scoreLeaf(a, joined, terms) || a.path.localeCompare(b.path));

  const total = matches.length;

  // おすすめも通常ヒットもない場合は「一致なし」を表示。
  if (!recoEntry && total === 0) {
    els["search-status"].textContent = "一致するカテゴリはありません。";
    return;
  }

  const frag = document.createDocumentFragment();

  // おすすめがある場合はリスト最上部に固定表示する。
  if (recoEntry) {
    for (const id of recoEntry.ids) {
      const leaf = state.byId.get(id);
      if (!leaf) continue;
      const li = createLeafItem(leaf);
      // 「おすすめ」バッジを日本語訳行に付与する。
      const jaRow = li.querySelector(".result-ja") || li.querySelector(".result-name");
      if (jaRow) {
        const badge = document.createElement("span");
        badge.className = "badge-reco";
        badge.textContent = "おすすめ";
        jaRow.append(" ");
        jaRow.append(badge);
      }
      frag.append(li);
    }
  }

  // 通常ヒットが1件以上あれば「参考」区切り見出しを挟む。
  if (recoEntry && total > 0) {
    const sep = document.createElement("li");
    sep.className = "reco-separator";
    sep.textContent = "参考";
    frag.append(sep);
  }

  // ステータス表示を組み立てる。
  const shown = Math.min(total, MAX_RESULTS);
  if (recoEntry) {
    if (total === 0) {
      els["search-status"].textContent = `おすすめ ${recoEntry.ids.length} 件`;
    } else {
      const refPart =
        total > MAX_RESULTS
          ? `参考 ${total.toLocaleString()} 件中 上位 ${shown} 件を表示`
          : `参考 ${total.toLocaleString()} 件`;
      els["search-status"].textContent = `おすすめ ${recoEntry.ids.length} 件 ・ ${refPart}`;
    }
  } else {
    els["search-status"].textContent =
      total > MAX_RESULTS ? `${total.toLocaleString()} 件中 上位 ${shown} 件を表示` : `${total.toLocaleString()} 件`;
  }

  for (let i = 0; i < shown; i++) {
    frag.append(createLeafItem(matches[i]));
  }
  list.append(frag);
}

function scoreLeaf(leaf, joined, terms) {
  const name = leaf._name; // 起動時にアクセント除去・小文字化済み (英語名)
  const ja = leaf._ja || ""; // 同上 (日本語訳)
  if (name === joined || ja === joined) return 100;
  if (name.startsWith(joined) || ja.startsWith(joined)) return 60;
  if (ja && ja.includes(joined)) return 45;
  if (terms.every((t) => name.includes(t) || ja.includes(t))) return 30;
  return 0;
}

// ---- ツリー描画 ----
function renderTree() {
  renderBreadcrumb();
  const list = els["tree-list"];
  list.replaceChildren();

  const node = getNode(state.treePath);
  if (!node) {
    state.treePath = [];
    return renderTree();
  }

  const frag = document.createDocumentFragment();

  // このノード自体が葉でもある場合 (枝かつ葉のレアケース) は選択肢として先頭に出す。
  if (node.leaf) {
    frag.append(createLeafItem(node.leaf, { showPath: false }));
  }

  const children = [...node.children.values()].sort((a, b) => a.name.localeCompare(b.name));
  for (const child of children) {
    if (state.curatedOnly && !child.hasCurated) continue;
    const isBranch = child.children.size > 0;
    if (isBranch) {
      frag.append(createBranchItem(child));
    } else if (child.leaf) {
      frag.append(createLeafItem(child.leaf, { showPath: false }));
    }
  }

  if (!frag.childNodes.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = state.curatedOnly ? "厳選版に該当する項目がありません。" : "項目がありません。";
    frag.append(empty);
  }
  list.append(frag);
}

function createBranchItem(node) {
  const li = document.createElement("li");
  li.className = "result-item";

  const main = document.createElement("div");
  main.className = "result-main";

  const nameRow = document.createElement("div");
  nameRow.className = "result-name";
  nameRow.textContent = node.name;
  const caret = document.createElement("span");
  caret.className = "branch-caret";
  caret.textContent = " ›";
  nameRow.append(caret);
  main.append(nameRow);

  const count = document.createElement("div");
  count.className = "result-path";
  count.textContent = `${node.leafTotal.toLocaleString()} 件のカテゴリ`;
  main.append(count);

  li.append(main);
  li.addEventListener("click", () => {
    state.treePath = [...state.treePath, node.name];
    renderTree();
  });
  return li;
}

function renderBreadcrumb() {
  const bc = els["breadcrumb"];
  bc.replaceChildren();

  const rootBtn = document.createElement("button");
  rootBtn.type = "button";
  rootBtn.className = "crumb" + (state.treePath.length === 0 ? " current" : "");
  rootBtn.textContent = "すべて";
  if (state.treePath.length > 0) {
    rootBtn.addEventListener("click", () => {
      state.treePath = [];
      renderTree();
    });
  }
  bc.append(rootBtn);

  state.treePath.forEach((seg, idx) => {
    const sep = document.createElement("span");
    sep.className = "crumb-sep";
    sep.textContent = "›";
    bc.append(sep);

    const isLast = idx === state.treePath.length - 1;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "crumb" + (isLast ? " current" : "");
    btn.textContent = seg;
    if (!isLast) {
      btn.addEventListener("click", () => {
        state.treePath = state.treePath.slice(0, idx + 1);
        renderTree();
      });
    }
    bc.append(btn);
  });
}

// ---- 検証 ----
function runVerify() {
  const raw = els["verify-input"].value.trim();
  const box = els["verify-result"];
  box.replaceChildren();
  if (!raw) return;

  const leaf = state.byId.get(raw);
  if (!leaf) {
    const div = document.createElement("div");
    div.className = "verify-not-found";
    div.textContent = `categoryID ${raw} は treeVersion ${state.treeVersion} (${state.marketplace}) に存在しません。`;
    box.append(div);
    return;
  }

  const div = document.createElement("div");
  div.className = "verify-found";

  const head = document.createElement("div");
  head.innerHTML = "";
  const strong = document.createElement("strong");
  strong.textContent = `${leaf.id} : ${leaf.name}`;
  head.append(strong);
  if (leaf.curated) {
    const badge = document.createElement("span");
    badge.className = "badge-curated";
    badge.textContent = "厳選";
    head.append(" ");
    head.append(badge);
  }
  div.append(head);

  if (leaf.ja) {
    const jaLine = document.createElement("div");
    jaLine.className = "result-ja";
    jaLine.style.marginTop = "4px";
    jaLine.textContent = leaf.ja;
    div.append(jaLine);
  }

  const path = document.createElement("div");
  path.className = "verify-path";
  path.textContent = leaf.path;
  div.append(path);

  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "mini-copy";
  copyBtn.textContent = "IDをコピー";
  copyBtn.style.marginTop = "8px";
  copyBtn.addEventListener("click", () => copyText(leaf.id, copyBtn, "済"));
  div.append(copyBtn);

  box.append(div);
  selectLeaf(leaf);
}

// ---- タブ ----
function setupTabs() {
  const tabs = document.querySelectorAll(".tab");
  const panels = {
    search: document.getElementById("panel-search"),
    tree: document.getElementById("panel-tree"),
    verify: document.getElementById("panel-verify"),
  };
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      Object.values(panels).forEach((p) => p.classList.remove("active"));
      panels[tab.dataset.tab].classList.add("active");
    });
  });
}

// ---- フィルタ ----
function populateDepartments() {
  const sel = els["department-filter"];
  for (const dept of state.departments) {
    const opt = document.createElement("option");
    opt.value = dept;
    opt.textContent = dept;
    sel.append(opt);
  }
}

function setupEvents() {
  let timer = null;
  els["search-input"].addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(runSearch, 150);
  });

  els["verify-input"].addEventListener("input", runVerify);

  els["department-filter"].addEventListener("change", (e) => {
    state.deptFilter = e.target.value;
    state.treePath = state.deptFilter ? [state.deptFilter] : [];
    runSearch();
    renderTree();
  });

  els["curated-toggle"].addEventListener("change", (e) => {
    state.curatedOnly = e.target.checked;
    runSearch();
    renderTree();
  });

  els["copy-btn"].addEventListener("click", () => {
    if (state.selectedId) copyText(state.selectedId, els["copy-btn"], "コピー済");
  });
}

// ---- 日本語訳 (translations_ja.json) の読み込み ----
// 厳選版カテゴリの日本語訳。id -> 日本語訳 の Map を返す。
// categories.json とは別ファイルにしておき、起動時にここで合成する
// (categories.json は自動生成物なので触らない方針)。
async function loadTranslations() {
  const map = new Map();
  try {
    const resp = await fetch("../data/translations_ja.json");
    if (!resp.ok) return map;
    const data = await resp.json();
    const t = data.translations || {};
    for (const [id, ja] of Object.entries(t)) {
      if (ja) map.set(id, ja);
    }
  } catch (error) {
    console.warn("translations_ja.json を読み込めませんでした (日本語訳は非表示):", error);
  }
  return map;
}

// ---- おすすめカテゴリ辞書の読み込み ----
// data/recommendations.json を読み込み、state.recommendations に格納する。
// 読み込み失敗時は console.warn して従来動作を維持する。
async function loadRecommendations() {
  try {
    const resp = await fetch("../data/recommendations.json");
    if (!resp.ok) {
      console.warn("recommendations.json を読み込めませんでした (おすすめ機能は無効):", resp.status);
      return;
    }
    const data = await resp.json();
    const list = data.recommendations || [];
    for (const entry of list) {
      if (!Array.isArray(entry.keys) || !Array.isArray(entry.ids)) continue;
      // キーは normalizeText で正規化してからスペースを除去して保持する。
      const normalizedKeys = entry.keys.map((k) => normalizeText(k).replace(/\s+/g, ""));
      state.recommendations.push({ normalizedKeys, ids: entry.ids });
    }
  } catch (error) {
    console.warn("recommendations.json を読み込めませんでした (おすすめ機能は無効):", error);
  }
}

// ---- 日本語ジャンル辞書の読み込み ----
async function loadAliases() {
  try {
    const resp = await fetch("../data/aliases.json");
    if (!resp.ok) return;
    const data = await resp.json();
    const aliases = data.aliases || {};
    for (const [jp, words] of Object.entries(aliases)) {
      if (!Array.isArray(words) || !words.length) continue;
      state.aliasMatchers.set(normalizeText(jp), words.map(aliasWordRegex));
    }
  } catch (error) {
    console.warn("aliases.json を読み込めませんでした (日本語検索は無効):", error);
  }
}

// ---- 初期化 ----
async function init() {
  cacheEls();
  setupTabs();
  try {
    const resp = await fetch("../data/categories.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    state.leaves = data.leaves || [];
    state.departments = data.departments || [];
    state.marketplace = data.meta?.marketplace || "EBAY_US";
    state.treeVersion = data.meta?.treeVersion || "?";
    const translations = await loadTranslations(); // id -> 日本語訳
    for (const leaf of state.leaves) {
      state.byId.set(leaf.id, leaf);
      leaf.ja = translations.get(leaf.id) || "";
      // アクセントを無視した検索用文字列を事前計算 (名前 + パス + 日本語訳)。
      leaf._search = normalizeText(leaf.name + " " + leaf.path + " " + leaf.ja);
      leaf._name = normalizeText(leaf.name);
      leaf._ja = normalizeText(leaf.ja);
    }
    state.translatedCount = translations.size;
    state.root = buildTree(state.leaves);
    await loadAliases();
    await loadRecommendations();

    const m = data.meta || {};
    const jaPart = state.translatedCount ? ` ・ 日本語訳 ${state.translatedCount.toLocaleString()}` : "";
    els["meta-line"].textContent =
      `${(m.leafCount || state.leaves.length).toLocaleString()} 葉 / ${m.departmentCount || state.departments.length} 部門` +
      ` ・ 厳選 ${(m.curatedCount || 0).toLocaleString()}${jaPart} ・ ${state.marketplace} treeVersion ${state.treeVersion}`;

    populateDepartments();
    setupEvents();
    els["search-status"].textContent = "キーワードを入力してください。";
    renderTree();
  } catch (error) {
    console.error("データの読み込みに失敗しました:", error);
    els["meta-line"].textContent = "データの読み込みに失敗しました。";
    els["search-status"].textContent =
      "data/categories.json を読み込めませんでした。拡張を再読み込みしてください。";
  }
}

document.addEventListener("DOMContentLoaded", init);
