#!/usr/bin/env python3
"""
Compass 竞品分析 · Evidence Store (RAG 数据层)

职责：
  1. 扫描本地证据库 (Excel/PDF)，自适应解析为 evidence 对象
  2. 提供 CRUD API：init / query / add / list / stats / export
  3. 实现 RAG 命中判断：本地库优先 (confidence=high)，未命中走 WebSearch 兜底

这是 MCP 思想实现 Step 5 证据互通的基础。
所有 Step 通过本脚本读写 evidence.json，避免重复存储。

Usage:
    python evidence_store.py init --db assets/evidence_db/ --output evidence.json
    python evidence_store.py query --input evidence.json --competitor iMin --aspect "*price*"
    python evidence_store.py add --input evidence.json --competitor iMin --aspect list_price --value "USD 350" --source-type price_list --source-url "file://..." --source-date 2026-04-11
    python evidence_store.py list --input evidence.json
    python evidence_store.py stats --input evidence.json
    python evidence_store.py export --input evidence.json --output report_evidence.json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

# === 自适应解析依赖（懒加载，缺失时给出清晰报错） ===
def _import_openpyxl():
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        print("ERROR: openpyxl not installed. Run: pip install openpyxl", file=sys.stderr)
        sys.exit(2)

def _import_pdfplumber():
    try:
        import pdfplumber
        return pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
        sys.exit(2)


# === Evidence ID 生成 ===
def gen_evidence_id(source_date: str, counter: int) -> str:
    """格式 EV-YYYY-NNN"""
    year = source_date[:4] if source_date and len(source_date) >= 4 else str(date.today().year)
    return f"EV-{year}-{counter:03d}"


# === 自适应 Excel 解析 ===
def parse_excel(filepath: Path, competitor_hint: str = "unknown") -> List[Dict[str, Any]]:
    """
    自适应解析 Excel：每个 sheet 第一行作为 header，每行作为一条 evidence。
    aspect = 列名；value = 单元格值。
    competitor 从 competitor_hint 或第一列推断。
    """
    openpyxl = _import_openpyxl()
    wb = openpyxl.load_workbook(filepath, data_only=True)
    evidences = []
    counter = 1
    today = date.today().isoformat()

    for sheet in wb.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        header = [str(c).strip().lower().replace(" ", "_") if c is not None else f"col_{i}" for i, c in enumerate(rows[0])]
        # 推断 competitor 列：找 header 中含 'competitor'/'brand'/'product' 的列
        comp_col_idx = next((i for i, h in enumerate(header) if "compet" in h or "brand" in h or "product" in h), None)

        for row in rows[1:]:
            if all(c is None or str(c).strip() == "" for c in row):
                continue
            competitor = str(row[comp_col_idx]).strip() if comp_col_idx is not None and row[comp_col_idx] else competitor_hint
            product = ""
            for i, h in enumerate(header):
                if "product" in h and row[i]:
                    product = str(row[i]).strip()
                    break
            # 每个非空单元格生成一条 evidence
            for i, (h, v) in enumerate(zip(header, row)):
                if v is None or str(v).strip() == "" or h in ("competitor", "brand", "product", "notes"):
                    continue
                ev = {
                    "evidence_id": gen_evidence_id(today, counter),
                    "competitor": competitor,
                    "product": product,
                    "aspect": h,
                    "value": str(v).strip(),
                    "unit": None,
                    "sentiment": "not_applicable",
                    "verbatim_quote": None,
                    "persona": None,
                    "source_type": "official_spec",
                    "source_url": f"file://{filepath.name}#{sheet.title}",
                    "source_date": today,
                    "confidence": "high",
                    "verified_by": "local_evidence_db",
                    "stage": "shared",
                    "decision_impact": "medium",
                    "notes": f"Auto-parsed from {sheet.title}",
                }
                evidences.append(ev)
                counter += 1
    return evidences


# === 自适应 PDF 解析 ===
def parse_pdf(filepath: Path, competitor_hint: str = "unknown") -> List[Dict[str, Any]]:
    """
    自适应解析 PDF：提取每页表格，每行作为一条 evidence。
    价格类 PDF（如价目表）会识别价格列并标 source_type=price_list。
    """
    pdfplumber = _import_pdfplumber()
    evidences = []
    counter = 1
    today = date.today().isoformat()
    # 从文件名推断 source_date（如 iMin IN Q2 FY26 Partner Price List 260411.pdf → 2026-04-11）
    filename_date_match = re.search(r"(\d{6})", filepath.name)
    inferred_date = today
    if filename_date_match:
        d = filename_date_match.group(1)
        if len(d) == 6:
            inferred_date = f"20{d[:2]}-{d[2:4]}-{d[4:6]}"

    is_price_list = "price" in filepath.name.lower() or "pricelist" in filepath.name.lower()

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables() or []
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                header = [str(c).strip().lower().replace(" ", "_") if c else f"col_{i}" for i, c in enumerate(table[0])]
                comp_col_idx = next((i for i, h in enumerate(header) if "compet" in h or "brand" in h or "product" in h or "model" in h or "sku" in h), None)
                for row in table[1:]:
                    if all(c is None or str(c).strip() == "" for c in row):
                        continue
                    competitor = str(row[comp_col_idx]).strip() if comp_col_idx is not None and row[comp_col_idx] else competitor_hint
                    product = ""
                    for i, h in enumerate(header):
                        if ("product" in h or "model" in h or "sku" in h) and row[i]:
                            product = str(row[i]).strip()
                            break
                    for i, (h, v) in enumerate(zip(header, row)):
                        if v is None or str(v).strip() == "" or h in ("competitor", "brand", "product", "model", "sku", "notes"):
                            continue
                        aspect = h
                        # 价格列识别
                        price_match = re.search(r"(usd|\$|price|cost|mrp)", h, re.IGNORECASE)
                        source_type = "price_list" if (is_price_list and price_match) else "official_spec"
                        stage = "B_pricing" if source_type == "price_list" else "A_feature"
                        ev = {
                            "evidence_id": gen_evidence_id(inferred_date, counter),
                            "competitor": competitor,
                            "product": product,
                            "aspect": aspect,
                            "value": str(v).strip(),
                            "unit": "USD" if price_match else None,
                            "sentiment": "not_applicable",
                            "verbatim_quote": None,
                            "persona": None,
                            "source_type": source_type,
                            "source_url": f"file://{filepath.name}#p{page_num}_t{table_idx}",
                            "source_date": inferred_date,
                            "confidence": "high",
                            "verified_by": "local_evidence_db",
                            "stage": stage,
                            "decision_impact": "high" if source_type == "price_list" else "medium",
                            "notes": f"Auto-parsed from PDF page {page_num} table {table_idx}",
                        }
                        evidences.append(ev)
                        counter += 1
    return evidences


# === init: 扫描本地证据库 ===
def cmd_init(args):
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: db path not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    all_evidences = []
    for fp in db_path.iterdir():
        if fp.is_dir():
            continue
        ext = fp.suffix.lower()
        competitor_hint = "unknown"
        # 从文件名推断竞品
        for comp in ["imin", "lenovo", "apple", "sunmi", "cpad", "verifone", "square", "stripe"]:
            if comp in fp.name.lower():
                competitor_hint = comp
                break
        try:
            if ext in (".xlsx", ".xls"):
                print(f"[parse] Excel: {fp.name}")
                evs = parse_excel(fp, competitor_hint)
            elif ext == ".pdf":
                print(f"[parse] PDF: {fp.name}")
                evs = parse_pdf(fp, competitor_hint)
            elif ext == ".json":
                print(f"[skip] schema file: {fp.name}")
                continue
            else:
                print(f"[skip] unsupported: {fp.name}")
                continue
            all_evidences.extend(evs)
            print(f"  → {len(evs)} evidences parsed")
        except Exception as e:
            print(f"  → ERROR parsing {fp.name}: {e}", file=sys.stderr)
    # 写入输出文件
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "source_db": str(db_path),
            "evidence_count": len(all_evidences),
            "evidences": all_evidences,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[done] {len(all_evidences)} evidences → {out_path}")


# === query: 按 competitor / aspect / stage / confidence 查询 ===
def cmd_query(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    evidences = data.get("evidences", [])
    results = []
    for ev in evidences:
        if args.competitor and args.competitor.lower() not in ev.get("competitor", "").lower():
            continue
        if args.aspect:
            pattern = args.aspect.replace("*", ".*").replace("?", ".")
            if not re.search(pattern, ev.get("aspect", ""), re.IGNORECASE):
                continue
        if args.stage and ev.get("stage") != args.stage:
            continue
        if args.confidence and ev.get("confidence") != args.confidence:
            continue
        results.append(ev)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n[done] {len(results)} matches", file=sys.stderr)


# === add: 添加单条 evidence ===
def cmd_add(args):
    with open(args.input, "r+", encoding="utf-8") as f:
        data = json.load(f)
    evidences = data.get("evidences", [])
    counter = len(evidences) + 1
    ev = {
        "evidence_id": gen_evidence_id(args.source_date, counter),
        "competitor": args.competitor,
        "product": args.product or "",
        "aspect": args.aspect,
        "value": args.value,
        "unit": args.unit,
        "sentiment": args.sentiment or "not_applicable",
        "verbatim_quote": args.verbatim_quote,
        "persona": args.persona,
        "source_type": args.source_type,
        "source_url": args.source_url,
        "source_date": args.source_date,
        "confidence": args.confidence,
        "verified_by": args.verified_by,
        "stage": args.stage or "shared",
        "decision_impact": args.decision_impact or "medium",
        "notes": args.notes,
    }
    evidences.append(ev)
    data["evidences"] = evidences
    data["evidence_count"] = len(evidences)
    f.seek(0)
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.truncate()
    print(f"[added] {ev['evidence_id']}")


# === list / stats / export ===
def cmd_list(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    for ev in data.get("evidences", []):
        print(f"{ev['evidence_id']:14s} | {ev['competitor']:10s} | {ev['aspect']:25s} | {ev['value'][:40]:40s} | {ev['confidence']:6s} | {ev['source_type']}")


def cmd_stats(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    evs = data.get("evidences", [])
    from collections import Counter
    by_comp = Counter(e["competitor"] for e in evs)
    by_stage = Counter(e["stage"] for e in evs)
    by_conf = Counter(e["confidence"] for e in evs)
    by_source = Counter(e["source_type"] for e in evs)
    print(f"Total evidences: {len(evs)}")
    print(f"\nBy competitor: {dict(by_comp)}")
    print(f"\nBy stage: {dict(by_stage)}")
    print(f"\nBy confidence: {dict(by_conf)}")
    print(f"\nBy source_type: {dict(by_source)}")


def cmd_export(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[exported] {data['evidence_count']} evidences → {args.output}")


# === CLI ===
def main():
    parser = argparse.ArgumentParser(description="Compass Evidence Store (RAG data layer)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Scan local evidence_db and parse to evidence.json")
    p_init.add_argument("--db", required=True, help="Path to evidence_db directory")
    p_init.add_argument("--output", required=True, help="Output evidence.json path")
    p_init.set_defaults(func=cmd_init)

    p_query = sub.add_parser("query", help="Query evidences by competitor/aspect/stage/confidence")
    p_query.add_argument("--input", required=True)
    p_query.add_argument("--competitor")
    p_query.add_argument("--aspect", help="glob pattern, e.g. '*price*' or 'display_*'")
    p_query.add_argument("--stage", choices=["A_feature", "B_pricing", "C_channel", "shared"])
    p_query.add_argument("--confidence", choices=["high", "medium", "low"])
    p_query.set_defaults(func=cmd_query)

    p_add = sub.add_parser("add", help="Add a single evidence")
    p_add.add_argument("--input", required=True)
    p_add.add_argument("--competitor", required=True)
    p_add.add_argument("--product")
    p_add.add_argument("--aspect", required=True)
    p_add.add_argument("--value", required=True)
    p_add.add_argument("--unit")
    p_add.add_argument("--sentiment", choices=["positive", "neutral", "negative", "mixed", "not_applicable"])
    p_add.add_argument("--verbatim-quote")
    p_add.add_argument("--persona", choices=["procurement_officer", "cfo", "it_admin", "channel_partner", "competitor_sales", "industry_analyst", "end_user"])
    p_add.add_argument("--source-type", required=True, choices=["official_spec", "price_list", "review", "forum", "analyst", "internal_data", "web_search"])
    p_add.add_argument("--source-url", required=True)
    p_add.add_argument("--source-date", required=True)
    p_add.add_argument("--confidence", required=True, choices=["high", "medium", "low"])
    p_add.add_argument("--verified-by", required=True, choices=["local_evidence_db", "web_search", "llm_inference", "user_provided"])
    p_add.add_argument("--stage", choices=["A_feature", "B_pricing", "C_channel", "shared"])
    p_add.add_argument("--decision-impact", choices=["high", "medium", "low"])
    p_add.add_argument("--notes")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all evidences")
    p_list.add_argument("--input", required=True)
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser("stats", help="Show evidence statistics")
    p_stats.add_argument("--input", required=True)
    p_stats.set_defaults(func=cmd_stats)

    p_export = sub.add_parser("export", help="Export evidences to another file")
    p_export.add_argument("--input", required=True)
    p_export.add_argument("--output", required=True)
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
