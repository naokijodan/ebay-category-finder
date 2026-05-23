#!/usr/bin/env python3
"""Build the bundled static category data for the eBay Category Finder extension.

入力 (eBay 公式 Taxonomy API getCategoryTree から取得した CSV):
  - ~/Desktop/ebay-categories-full.csv     全葉カテゴリ (列: categoryId,department,level,categoryName,fullPath)
  - ~/Desktop/ebay-categories-curated.csv  厳選版       (列: categoryId,department,fullPath)

出力:
  - ../data/categories.json  拡張に同梱する静的データ

注意:
  - data/categories.json は **自動生成物。手で編集しないこと**。
    eBay のカテゴリ改訂時は、新しい CSV を取り直してこのスクリプトを再実行する。
  - 実行時に eBay や外部 API を一切叩かない (オフライン生成)。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# CSV を取得した時点の eBay タクソノミー (README にも明記する事実)
MARKETPLACE = "EBAY_US"
TREE_VERSION = "134"
SOURCE = "eBay Taxonomy API getCategoryTree"

DESKTOP = Path.home() / "Desktop"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_FULL = DESKTOP / "ebay-categories-full.csv"
DEFAULT_CURATED = DESKTOP / "ebay-categories-curated.csv"
DEFAULT_OUT = SCRIPT_DIR.parent / "data" / "categories.json"

ROOT_PREFIX = "Root > "


def strip_root(full_path: str) -> str:
    """先頭の 'Root > ' を除去する。枝は path を ' > ' で割って再構成するため葉のみ ID を持つ。"""
    path = full_path.strip()
    if path.startswith(ROOT_PREFIX):
        path = path[len(ROOT_PREFIX):]
    return path


def read_curated_ids(curated_path: Path) -> set[str]:
    """厳選版 CSV から categoryId の集合だけを読む (葉に curated フラグを立てるのに使う)。"""
    if not curated_path.exists():
        print(f"[warn] curated CSV が見つかりません: {curated_path} (curated フラグは全て false)")
        return set()
    ids: set[str] = set()
    with curated_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if "categoryId" not in (reader.fieldnames or []):
            raise ValueError(f"curated CSV に categoryId 列がありません: {curated_path}")
        for row in reader:
            cid = (row.get("categoryId") or "").strip()
            if cid:
                ids.add(cid)
    return ids


def read_leaves(full_path: Path, curated_ids: set[str]) -> list[dict]:
    """全葉 CSV を読み、{id, name, path, department, curated} のフラット配列を作る。"""
    if not full_path.exists():
        raise FileNotFoundError(f"full CSV が見つかりません: {full_path}")
    by_id: dict[str, dict] = {}
    duplicates = 0
    with full_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"categoryId", "department", "categoryName", "fullPath"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"full CSV に必要な列がありません: {sorted(missing)}")
        for row in reader:
            cid = (row.get("categoryId") or "").strip()
            if not cid:
                continue
            path = strip_root(row.get("fullPath") or "")
            name = (row.get("categoryName") or "").strip()
            if not name and path:
                name = path.split(" > ")[-1]
            leaf = {
                "id": cid,
                "name": name,
                "path": path,
                "department": (row.get("department") or "").strip(),
                "curated": cid in curated_ids,
            }
            if cid in by_id:
                duplicates += 1
            by_id[cid] = leaf
    if duplicates:
        print(f"[warn] 重複 categoryId {duplicates} 件 (最後の行を採用しました)")
    leaves = list(by_id.values())
    leaves.sort(key=lambda x: (x["department"], x["path"]))
    return leaves


def build(full_path: Path, curated_path: Path, out_path: Path) -> dict:
    curated_ids = read_curated_ids(curated_path)
    leaves = read_leaves(full_path, curated_ids)
    departments = sorted({leaf["department"] for leaf in leaves if leaf["department"]})
    curated_count = sum(1 for leaf in leaves if leaf["curated"])
    meta = {
        "marketplace": MARKETPLACE,
        "treeVersion": TREE_VERSION,
        "source": SOURCE,
        "leafCount": len(leaves),
        "departmentCount": len(departments),
        "curatedCount": curated_count,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    payload = {"meta": meta, "departments": departments, "leaves": leaves}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    return meta


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build categories.json for the eBay Category Finder extension")
    parser.add_argument("--full", type=Path, default=DEFAULT_FULL, help=f"全葉 CSV (default: {DEFAULT_FULL})")
    parser.add_argument("--curated", type=Path, default=DEFAULT_CURATED, help=f"厳選版 CSV (default: {DEFAULT_CURATED})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"出力 JSON (default: {DEFAULT_OUT})")
    args = parser.parse_args(argv)

    try:
        meta = build(args.full, args.curated, args.out)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    size_mb = args.out.stat().st_size / (1024 * 1024)
    print("[ok] categories.json を生成しました")
    print(f"     出力     : {args.out}")
    print(f"     葉カテゴリ : {meta['leafCount']:,} 件")
    print(f"     部門数    : {meta['departmentCount']} 部門")
    print(f"     厳選版該当 : {meta['curatedCount']:,} 件")
    print(f"     treeVersion: {meta['treeVersion']} ({meta['marketplace']})")
    print(f"     ファイル   : {size_mb:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
