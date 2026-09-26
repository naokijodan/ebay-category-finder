#!/usr/bin/env python3
"""Build the bundled static category data for the eBay Category Finder extension.

入力 (eBay 公式 Taxonomy API getCategoryTree から取得した CSV):
  - ~/Desktop/ebay-categories-full.csv     全葉カテゴリ (列: categoryId,department,level,categoryName,fullPath)
  - ~/Desktop/ebay-categories-curated.csv  厳選版       (列: categoryId,department,fullPath)

任意 (eBay Motors を追加する場合。両方指定したときだけ有効):
  - --motors-tree <json>     Taxonomy API getCategoryTree の生レスポンス (treeId 100)
  - --motors-curated <json>  Motors 厳選 (部品用途) の葉一覧。{"sections": {セクション名: [{"id":..., ...}, ...]}} 形式

出力:
  - ../data/categories.json  拡張に同梱する静的データ

注意:
  - data/categories.json は **自動生成物。手で編集しないこと**。
    eBay のカテゴリ改訂時は、新しい CSV (・Motors JSON) を取り直してこのスクリプトを再実行する。
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

# eBay Motors (treeId 100) 側の事実。取得元 JSON に埋め込まれている値と一致させる。
MOTORS_DEPARTMENT = "eBay Motors"
MOTORS_TREE_ID = "100"
MOTORS_TREE_VERSION = "83"
MOTORS_FETCHED_AT = "2026-09-08"

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
    """全葉 CSV を読み、{id, name, path, department, curated, tree} のフラット配列を作る。"""
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
                "tree": "US",
            }
            if cid in by_id:
                duplicates += 1
            by_id[cid] = leaf
    if duplicates:
        print(f"[warn] 重複 categoryId {duplicates} 件 (最後の行を採用しました)")
    leaves = list(by_id.values())
    leaves.sort(key=lambda x: (x["department"], x["path"]))
    return leaves


def read_motors_curated_ids(motors_curated_path: Path) -> set[str]:
    """Motors 厳選 (部品用途) JSON から categoryId の集合だけを読む。

    形式: {"sections": {"セクション名": [{"id": "...", ...}, ...], ...}}
    mark (exclude/caution) の有無に関わらず、ファイルに載っている葉IDはすべて curated として扱う。
    """
    if not motors_curated_path.exists():
        print(f"[warn] Motors 厳選 JSON が見つかりません: {motors_curated_path} (curated フラグは全て false)")
        return set()
    data = json.loads(motors_curated_path.read_text(encoding="utf-8"))
    sections = data.get("sections", {})
    ids: set[str] = set()
    for entries in sections.values():
        for entry in entries:
            cid = str(entry.get("id") or "").strip()
            if cid:
                ids.add(cid)
    return ids


def read_motors_leaves(motors_tree_path: Path, curated_ids: set[str]) -> list[dict]:
    """eBay Motors の公式ツリー JSON (getCategoryTree 生レスポンス) を読み、葉のフラット配列を作る。

    root (categoryId "0") の直下から "eBay Motors" (categoryId "6000") ノードを探し、
    そこから葉 (子を持たない、または leafCategoryTreeNode=true のノード) を再帰的に集める。
    path は "eBay Motors" から始め、root 自体は含めない。
    """
    if not motors_tree_path.exists():
        raise FileNotFoundError(f"Motors ツリー JSON が見つかりません: {motors_tree_path}")
    data = json.loads(motors_tree_path.read_text(encoding="utf-8"))
    root = data.get("rootCategoryNode") or {}

    motors_node = None
    for child in root.get("childCategoryTreeNodes") or []:
        cat = child.get("category") or {}
        if cat.get("categoryId") == "6000" or cat.get("categoryName") == "eBay Motors":
            motors_node = child
            break
    if motors_node is None:
        raise ValueError(f"Motors ツリー JSON に 'eBay Motors' (categoryId 6000) ノードが見つかりません: {motors_tree_path}")

    leaves: list[dict] = []

    def walk(node: dict, path_segs: list[str]) -> None:
        children = node.get("childCategoryTreeNodes") or []
        cat = node.get("category") or {}
        name = (cat.get("categoryName") or "").strip()
        new_path = path_segs + [name]
        is_leaf = bool(node.get("leafCategoryTreeNode")) or not children
        if is_leaf:
            cid = str(cat.get("categoryId") or "").strip()
            if cid:
                leaves.append(
                    {
                        "id": cid,
                        "name": name,
                        "path": " > ".join(new_path),
                        "department": MOTORS_DEPARTMENT,
                        "curated": cid in curated_ids,
                        "tree": "MOTORS",
                    }
                )
        for child in children:
            walk(child, new_path)

    walk(motors_node, [])
    leaves.sort(key=lambda x: x["path"])
    return leaves


def build(
    full_path: Path,
    curated_path: Path,
    out_path: Path,
    motors_tree_path: Path | None = None,
    motors_curated_path: Path | None = None,
) -> dict:
    curated_ids = read_curated_ids(curated_path)
    leaves = read_leaves(full_path, curated_ids)
    departments = sorted({leaf["department"] for leaf in leaves if leaf["department"]})

    motors_meta: dict | None = None
    if motors_tree_path is not None and motors_curated_path is not None:
        motors_curated_ids = read_motors_curated_ids(motors_curated_path)
        motors_leaves = read_motors_leaves(motors_tree_path, motors_curated_ids)

        us_ids = {leaf["id"] for leaf in leaves}
        motors_ids = {leaf["id"] for leaf in motors_leaves}
        overlap = sorted(us_ids & motors_ids, key=lambda x: int(x) if x.isdigit() else 0)
        if overlap:
            raise ValueError(
                f"通常ツリーと Motors ツリーで categoryId が重複しています ({len(overlap)} 件): {overlap[:20]}"
            )

        leaves = leaves + motors_leaves
        leaves.sort(key=lambda x: (x["department"], x["path"]))
        if MOTORS_DEPARTMENT not in departments:
            departments = departments + [MOTORS_DEPARTMENT]

        motors_curated_count = sum(1 for leaf in motors_leaves if leaf["curated"])
        motors_meta = {
            "treeId": MOTORS_TREE_ID,
            "treeVersion": MOTORS_TREE_VERSION,
            "source": SOURCE,
            "leafCount": len(motors_leaves),
            "curatedCount": motors_curated_count,
            "fetchedAt": MOTORS_FETCHED_AT,
        }

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
    if motors_meta is not None:
        meta["motors"] = motors_meta

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
    parser.add_argument(
        "--motors-tree",
        type=Path,
        default=None,
        help="eBay Motors の公式ツリー JSON (getCategoryTree 生レスポンス, treeId 100)。指定時のみ Motors を追加。",
    )
    parser.add_argument(
        "--motors-curated",
        type=Path,
        default=None,
        help="eBay Motors 厳選 (部品用途) の葉一覧 JSON。--motors-tree と両方指定したときのみ有効。",
    )
    args = parser.parse_args(argv)

    if bool(args.motors_tree) != bool(args.motors_curated):
        print("[error] --motors-tree と --motors-curated は両方指定してください (片方だけは不可)", file=sys.stderr)
        return 1

    try:
        meta = build(args.full, args.curated, args.out, args.motors_tree, args.motors_curated)
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
    if "motors" in meta:
        mm = meta["motors"]
        print(
            f"     Motors     : 葉 {mm['leafCount']:,} 件 / 厳選 {mm['curatedCount']:,} 件"
            f" (treeId {mm['treeId']}, treeVersion {mm['treeVersion']})"
        )
    print(f"     ファイル   : {size_mb:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
