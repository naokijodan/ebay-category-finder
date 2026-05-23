// ツールバーのアイコンをクリックしたらサイドパネルを開く設定。
// この拡張は eBay や外部サーバーに一切アクセスしない (同梱 JSON のみ)。

function enablePanelOnClick() {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error("setPanelBehavior failed:", error));
}

chrome.runtime.onInstalled.addListener(enablePanelOnClick);
// Service Worker が再起動した場合にも設定を保証する。
enablePanelOnClick();
