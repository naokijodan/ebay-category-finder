#!/usr/bin/env python3
"""厳選版カテゴリ (curated) の名称を日本語に翻訳し、検索・表示用の辞書を作る。

出力: ../data/translations_ja.json
  {"meta": {...}, "translations": {"<categoryId>": "<日本語訳>", ...}}

特徴:
  - OpenAI API を使う (モデルは --model、既定 gpt-5.4-mini)。
  - API キーはコードに書かず、環境変数 OPENAI_API_KEY か ~/.codex/config.toml から実行時に読む。
  - バッチ処理 (既定 100件/回)。各バッチ後に途中結果を保存するので、中断しても再開できる。
  - 1バッチが失敗しても全体は止めず、次のバッチに進む (--retries で再試行回数を指定)。
  - 既に訳のある ID は再実行時にスキップ (--force で上書き)。

使い方:
  python3 translate_categories.py --limit 10          # まず10件だけ試す
  python3 translate_categories.py                      # 残り全部 (厳選版のみ)
  python3 translate_categories.py --force              # 全部訳し直す

注意: eBay や外部サービスには一切アクセスしない (OpenAI API のみ)。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_IN = SCRIPT_DIR.parent / "data" / "categories.json"
DEFAULT_OUT = SCRIPT_DIR.parent / "data" / "translations_ja.json"
CONFIG_TOML = Path.home() / ".codex" / "config.toml"
API_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "あなたは日本のeBay出品者向けのカテゴリ翻訳者です。"
    "英語のeBayカテゴリ名を、日本人出品者が日本語で検索しやすい短い日本語に訳します。\n"
    "ルール:\n"
    "- 日本人が普段使うジャンル語を必ず含める。例: trading card→トレカ、figure→フィギュア、"
    "watch→腕時計、reel→リール、camera→カメラ、doll→人形、comic→漫画。\n"
    "- 区別語も日本語で含める。例: Individual/Single→シングル、Lot/Bundle/Mixed→まとめ、"
    "Sealed→未開封、Set→セット、Parts→パーツ、Accessories→アクセサリー。\n"
    "- カテゴリの意味が一目で分かる自然で短い日本語にする (目安20文字以内)。\n"
    "- パス(階層)を文脈として正確さの参考にする。\n"
    "- 訳語のみ。説明文・記号の装飾・英語の併記は不要。\n"
    "- 各カテゴリは独立して訳す。同じバッチ内の別カテゴリの語(例: トレカ等)を流用しない。"
    "そのカテゴリ自身の name と path だけを根拠に訳すこと。\n"
    "- 出力は必ず指定のJSON形式のみを返す。"
)


def read_api_key() -> str:
    env = os.environ.get("OPENAI_API_KEY")
    if env:
        return env.strip()
    if not CONFIG_TOML.exists():
        sys.exit(f"APIキーが見つかりません (環境変数 OPENAI_API_KEY も {CONFIG_TOML} も無し)")
    m = re.search(r'OPENAI_API_KEY\s*=\s*"([^"]+)"', CONFIG_TOML.read_text(encoding="utf-8"))
    if not m:
        sys.exit(f"OPENAI_API_KEY が {CONFIG_TOML} に見つかりません")
    return m.group(1).strip()


def load_curated(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [l for l in data.get("leaves", []) if l.get("curated")]


def load_existing(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return dict(data.get("translations", {}))
    except (json.JSONDecodeError, OSError):
        return {}


def save_translations(path: Path, translations: dict[str, str], model: str, total_curated: int) -> None:
    payload = {
        "meta": {
            "source": "OpenAI Chat Completions",
            "model": model,
            "curatedCount": total_curated,
            "translatedCount": len(translations),
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "厳選版カテゴリの日本語訳。translate_categories.py の自動生成物 (手編集可)。",
        },
        "translations": dict(sorted(translations.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0)),
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def extract_json_object(text: str) -> dict:
    """応答からJSONオブジェクトを取り出す (前後に余計な文字があっても拾う)。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("応答からJSONを抽出できませんでした")


def call_api(model: str, key: str, batch: list[dict], timeout: int) -> dict[str, str]:
    items = [{"id": l["id"], "name": l["name"], "path": l["path"]} for l in batch]
    user_prompt = (
        '次のカテゴリを日本語訳し、JSONで返してください。'
        '形式は {"翻訳": {"<id>": "<日本語訳>", ...}} とします。\n'
        + json.dumps(items, ensure_ascii=False)
    )
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    content = data["choices"][0]["message"]["content"]
    obj = extract_json_object(content)
    # {"翻訳": {...}} でも {id: ja} でも受け取れるようにする。
    mapping = obj.get("翻訳") or obj.get("translations") or obj
    valid_ids = {l["id"] for l in batch}
    return {str(k): str(v).strip() for k, v in mapping.items() if str(k) in valid_ids and str(v).strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description="厳選版カテゴリの日本語訳を生成する")
    ap.add_argument("--in", dest="in_path", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out", dest="out_path", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--model", default="gpt-5.4-mini")
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--limit", type=int, default=0, help="先頭から N 件だけ訳す (0=全部)")
    ap.add_argument("--retries", type=int, default=2, help="バッチ失敗時の再試行回数")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--force", action="store_true", help="既訳も含めて訳し直す")
    args = ap.parse_args()

    key = read_api_key()
    curated = load_curated(args.in_path)
    translations = {} if args.force else load_existing(args.out_path)
    total_curated = len(curated)

    todo = [l for l in curated if args.force or l["id"] not in translations]
    if args.limit > 0:
        todo = todo[: args.limit]

    print(f"厳選版: {total_curated} 件 / 既訳: {len(translations)} 件 / 今回対象: {len(todo)} 件 (model={args.model})")
    if not todo:
        print("対象がありません。完了。")
        return 0

    batches = [todo[i : i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
    failed = 0
    for bi, batch in enumerate(batches, 1):
        ok = False
        for attempt in range(1, args.retries + 2):
            try:
                result = call_api(args.model, key, batch, args.timeout)
                translations.update(result)
                save_translations(args.out_path, translations, args.model, total_curated)
                print(f"[{bi}/{len(batches)}] +{len(result)}件 (累計 {len(translations)}/{total_curated})")
                ok = True
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "replace")[:200]
                print(f"[{bi}/{len(batches)}] HTTP {e.code} (試行{attempt}): {msg}")
            except Exception as e:  # noqa: BLE001 - 1バッチの失敗で全体を止めない
                print(f"[{bi}/{len(batches)}] エラー (試行{attempt}): {e}")
            time.sleep(min(2 ** attempt, 20))
        if not ok:
            failed += 1
            print(f"[{bi}/{len(batches)}] スキップ (このバッチは後で再実行で補完できます)")

    remaining = total_curated - len(translations)
    print(f"完了: 訳済 {len(translations)}/{total_curated} 件 / 失敗バッチ {failed} 個 / 未訳 {remaining} 件")
    print(f"出力: {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
