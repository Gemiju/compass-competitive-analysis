#!/usr/bin/env python3
"""
Compass 竞品分析 · Step 5: VOC Extractor

职责：
  1. 从 evidence.json 提取 VOC 类证据 (stage=C_channel 或 source_type=review/forum)
  2. aspect-based 情感聚合：按 aspect × persona 聚合 sentiment
  3. persona 多样性检查：至少覆盖 3 个 persona
  4. 输出 VOC 侧边栏（每个竞品 3-5 条 persona 标签原声）+ Message House 建议

多视角预研究（STORM 借鉴）+ 三角化 VOC（Reddit/YouTube/Amazon）。

Usage:
    python voc_extract.py --input evidence.json --self-product "商米 CPAD" --output voc_analysis.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


# === persona 推断规则（参考 icp_persona_library.md） ===
PERSONA_KEYWORDS = {
    "procurement_officer": ["procurement", "rfq", "vendor evaluation", "supplier", "rfp", "tender"],
    "cfo": ["budget", "roi", "depreciation", "capex", "opex", "payback"],
    "it_admin": ["mdm", "deploy", "firmware", "sdk", "integration", "admin", "configure"],
    "channel_partner": ["margin", "resell", "distributor", "partner program", "dealer"],
    "end_user": ["my shift", "checkout", "customer", "i use", "daily", "cashier", "waiter"],
    "industry_analyst": ["market share", "category trend", "forecast", "analyst"],
}


def infer_persona(verbatim_quote: str, existing_persona: str = None) -> str:
    """从 VOC 原声推断 persona"""
    if existing_persona and existing_persona != "null":
        return existing_persona
    if not verbatim_quote:
        return None
    text = verbatim_quote.lower()
    for persona, keywords in PERSONA_KEYWORDS.items():
        if any(k in text for k in keywords):
            return persona
    return None


# === aspect-based 情感聚合 ===
def aggregate_aspect_sentiment(voc_evidences: List[Dict]) -> Dict:
    """
    按 aspect × persona 聚合 sentiment。
    输出：aspect -> persona -> {positive, negative, neutral, quotes}
    """
    aspect_persona = defaultdict(lambda: defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "quotes": []}))
    for ev in voc_evidences:
        aspect = ev.get("aspect", "unknown")
        sentiment = ev.get("sentiment", "neutral")
        persona = infer_persona(ev.get("verbatim_quote"), ev.get("persona"))
        if persona is None:
            persona = "unidentified"
        if sentiment in aspect_persona[aspect][persona]:
            aspect_persona[aspect][persona][sentiment] += 1
        aspect_persona[aspect][persona]["quotes"].append({
            "evidence_id": ev["evidence_id"],
            "verbatim_quote": ev.get("verbatim_quote"),
            "source_url": ev.get("source_url"),
            "source_date": ev.get("source_date"),
            "competitor": ev.get("competitor"),
        })
    return aspect_persona


# === persona 多样性检查 ===
def check_persona_diversity(voc_evidences: List[Dict]) -> Dict:
    """检查是否覆盖 ≥3 个 persona"""
    personas = set()
    for ev in voc_evidences:
        p = infer_persona(ev.get("verbatim_quote"), ev.get("persona"))
        if p:
            personas.add(p)
    return {
        "persona_count": len(personas),
        "personas": list(personas),
        "passes_diversity_gate": len(personas) >= 3,
        "rule": "Stage C 必须覆盖 ≥3 个 persona（参考 icp_persona_library.md）",
    }


# === VOC 侧边栏（每个竞品 3-5 条 persona 标签原声） ===
def build_voc_sidebar(voc_evidences: List[Dict], max_per_competitor: int = 5) -> List[Dict]:
    """每个竞品输出 3-5 条带 persona + 日期的原声"""
    by_competitor = defaultdict(list)
    for ev in voc_evidences:
        by_competitor[ev.get("competitor", "unknown")].append(ev)

    sidebars = []
    for competitor, evs in by_competitor.items():
        # 优先选 persona 已识别 + verbatim_quote 非空 + sentiment 非 neutral
        scored = []
        for ev in evs:
            score = 0
            if ev.get("verbatim_quote"):
                score += 2
            persona = infer_persona(ev.get("verbatim_quote"), ev.get("persona"))
            if persona and persona != "unidentified":
                score += 2
            if ev.get("sentiment") in ("positive", "negative"):
                score += 1
            if ev.get("confidence") == "high":
                score += 1
            scored.append((score, ev, persona))
        scored.sort(key=lambda x: -x[0])
        selected = []
        seen_personas = set()
        for score, ev, persona in scored:
            if len(selected) >= max_per_competitor:
                break
            # 优先不同 persona（保证多样性）
            if persona in seen_personas and len(selected) < max_per_competitor - 1:
                continue
            selected.append({
                "competitor": competitor,
                "persona": persona,
                "sentiment": ev.get("sentiment"),
                "verbatim_quote": ev.get("verbatim_quote"),
                "aspect": ev.get("aspect"),
                "source_url": ev.get("source_url"),
                "source_date": ev.get("source_date"),
                "evidence_id": ev["evidence_id"],
            })
            if persona:
                seen_personas.add(persona)
        sidebars.append({"competitor": competitor, "voc_count": len(evs), "sidebar": selected})
    return sidebars


# === Message House 建议（简化版） ===
def build_message_house(voc_evidences: List[Dict], self_product: str) -> Dict:
    """
    基于 VOC 痛点 + 我方优势，输出 Message House 建议。
    简化逻辑：找竞品 negative sentiment 最多的 aspect → 我方在该 aspect 若领先则作为核心卖点。
    """
    # 竞品负面 aspect 排行
    competitor_negative = defaultdict(lambda: defaultdict(int))
    for ev in voc_evidences:
        if ev.get("competitor", "").lower() in (self_product.lower(), "self", "商米", "cpad"):
            continue
        if ev.get("sentiment") == "negative":
            competitor_negative[ev["competitor"]][ev.get("aspect", "unknown")] += 1
    # 取每个竞品 top 3 痛点
    pain_points = {}
    for comp, aspects in competitor_negative.items():
        pain_points[comp] = sorted(aspects.items(), key=lambda x: -x[1])[:3]
    return {
        "self_product": self_product,
        "competitor_pain_points": pain_points,
        "recommendation": "针对竞品 top 痛点 aspect，结合 Stage A 的我方领先 gap，构建差异化话术",
    }


def cmd_run(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    evidences = data.get("evidences", [])
    voc_evidences = [e for e in evidences if e.get("stage") == "C_channel" or e.get("source_type") in ("review", "forum", "analyst", "web_search") and e.get("verbatim_quote")]
    print(f"[load] {len(voc_evidences)} VOC evidences", file=sys.stderr)

    aspect_sentiment = aggregate_aspect_sentiment(voc_evidences)
    diversity = check_persona_diversity(voc_evidences)
    sidebars = build_voc_sidebar(voc_evidences)
    message_house = build_message_house(voc_evidences, args.self_product)

    output = {
        "schema_version": "1.0",
        "self_product": args.self_product,
        "voc_count": len(voc_evidences),
        "persona_diversity": diversity,
        "aspect_sentiment_matrix": {k: dict(v) for k, v in aspect_sentiment.items()},
        "voc_sidebars": sidebars,
        "message_house": message_house,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[done] VOC analysis → {out_path}", file=sys.stderr)
    print(f"  personas covered: {diversity['persona_count']} (gate: {'PASS' if diversity['passes_diversity_gate'] else 'FAIL'})", file=sys.stderr)
    print(f"  competitors: {len(sidebars)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Stage C: VOC Extractor")
    parser.add_argument("--input", required=True, help="evidence.json path")
    parser.add_argument("--self-product", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cmd_run(args)


if __name__ == "__main__":
    main()
