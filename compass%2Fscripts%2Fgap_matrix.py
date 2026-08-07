#!/usr/bin/env python3
"""
Compass 竞品分析 · Step 5: Gap Matrix Generator

职责：
  1. 读取 evidence.json，按 taxonomy 四级分类生成功能 gap 矩阵
  2. 每条 gap 标注 gap_direction (领先/落后/持平) + decision_impact (high/medium/low)
  3. 输出差异化机会段落（≥3 条，每条引用 ≥2 条证据）

这是 Step 5 Synthesize 阶段的 Function Calling 入口。
Review 阶段（COT 自我审查）由 SKILL LLM 基于 gap_matrix.json 完成。

Usage:
    python gap_matrix.py --input evidence.json --self-product "商米 CPAD" --output gap_matrix.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


# === aspect → taxonomy level 映射（参考 references/taxonomy.md） ===
TAXONOMY_MAP = {
    # level 1: hardware
    "display_size": "hardware", "display_type": "hardware", "resolution": "hardware",
    "touch": "hardware", "cpu": "hardware", "ram": "hardware", "storage": "hardware",
    "battery": "hardware", "connectivity": "hardware", "ports": "hardware",
    "printer": "hardware", "scanner": "hardware", "nfc": "hardware", "camera": "hardware",
    "durability": "hardware", "dimensions": "hardware", "weight": "hardware",
    # level 2: system
    "os": "system", "os_version": "system", "mdm_support": "system",
    "kiosk_mode": "system", "app_store": "system", "sdk_openness": "system",
    "update_policy": "system", "security_cert": "system", "multi_user": "system",
    "remote_management": "system",
    # level 3: scenario
    "scenario_retail": "scenario", "scenario_hospitality": "scenario",
    "scenario_logistics": "scenario", "scenario_healthcare": "scenario",
    "scenario_industrial": "scenario", "scenario_education": "scenario",
    "scenario_outdoor": "scenario", "scenario_qsr": "scenario",
    # level 4: service
    "warranty": "service", "rma_policy": "service", "tech_support": "service",
    "onsite_service": "service", "training": "service", "spare_parts": "service",
    "sla": "service", "custom_firmware": "service", "co_branding": "service",
    "eol_notice_period": "service",
}


def infer_taxonomy_level(aspect: str) -> str:
    """根据 aspect 名推断 taxonomy level"""
    if aspect in TAXONOMY_MAP:
        return TAXONOMY_MAP[aspect]
    # 模糊匹配
    a = aspect.lower()
    if any(k in a for k in ["display", "cpu", "ram", "battery", "port", "printer", "scanner", "nfc", "camera", "weight", "dimension"]):
        return "hardware"
    if any(k in a for k in ["os", "mdm", "kiosk", "sdk", "firmware", "security", "remote"]):
        return "system"
    if any(k in a for k in ["scenario", "retail", "qsr", "hospitality", "logistics", "healthcare"]):
        return "scenario"
    if any(k in a for k in ["warranty", "rma", "support", "sla", "spare", "eol", "training"]):
        return "service"
    return "uncategorized"


def parse_numeric(value: str) -> float:
    """尝试从字符串提取数字，用于 gap direction 比较"""
    if not value:
        return None
    # 提取首个数字（支持小数）
    m = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(m.group(1)) if m else None


def determine_gap_direction(self_val: str, their_val: str, aspect: str) -> str:
    """
    判断 gap direction：领先 / 落后 / 持平 / 不可比
    规则简化版：相同=持平；数值差>10%=领先或落后；文本不同=不可比
    """
    if not self_val or not their_val:
        return "data_missing"
    if str(self_val).strip().lower() == str(their_val).strip().lower():
        return "parity"
    s_num = parse_numeric(self_val)
    t_num = parse_numeric(their_val)
    if s_num is not None and t_num is not None and t_num != 0:
        diff_pct = abs(s_num - t_num) / max(abs(t_num), 0.001) * 100
        if diff_pct < 10:
            return "parity"
        # 对于 battery/ram/storage，越大越好；对于 weight，越小越好
        if aspect in ("battery", "ram", "storage", "resolution"):
            return "ahead" if s_num > t_num else "behind"
        if aspect in ("weight", "dimensions"):
            return "ahead" if s_num < t_num else "behind"
        return "ahead" if s_num > t_num else "behind"
    return "incomparable"


def build_gap_matrix(evidences: List[Dict], self_product: str) -> Dict:
    """
    构建功能 gap 矩阵。
    输入：所有 evidences（含 self 与 competitors）
    输出：{level, aspect, self_value, competitor_values, gap_directions, decision_impacts, evidence_ids}
    """
    # 按 (aspect, competitor) 聚合 value
    aspect_comp_value = defaultdict(dict)  # aspect -> competitor -> value
    aspect_ev_ids = defaultdict(list)      # aspect -> [evidence_id]
    aspect_decision_impact = {}             # aspect -> decision_impact

    for ev in evidences:
        if ev.get("stage") not in ("A_feature", "shared"):
            continue
        aspect = ev["aspect"]
        comp = ev["competitor"]
        val = ev["value"]
        aspect_comp_value[aspect][comp] = val
        aspect_ev_ids[aspect].append(ev["evidence_id"])
        # 取最高 decision_impact
        cur = aspect_decision_impact.get(aspect, "low")
        if ev.get("decision_impact") == "high" or (ev.get("decision_impact") == "medium" and cur == "low"):
            aspect_decision_impact[aspect] = ev.get("decision_impact", "medium")

    # 构建 gap 矩阵
    gap_matrix = []
    for aspect, comp_values in aspect_comp_value.items():
        self_val = comp_values.get(self_product) or comp_values.get("self") or comp_values.get("商米") or comp_values.get("CPAD")
        level = infer_taxonomy_level(aspect)
        gap_directions = {}
        for comp, their_val in comp_values.items():
            if comp == self_product or comp in ("self", "商米", "CPAD"):
                continue
            gap_directions[comp] = determine_gap_direction(self_val, their_val, aspect)
        gap_matrix.append({
            "taxonomy_level": level,
            "aspect": aspect,
            "self_value": self_val,
            "competitor_values": {k: v for k, v in comp_values.items() if k != self_product and k not in ("self", "商米", "CPAD")},
            "gap_directions": gap_directions,
            "decision_impact": aspect_decision_impact.get(aspect, "medium"),
            "evidence_ids": aspect_ev_ids[aspect],
        })

    # 按 taxonomy level + decision_impact 排序
    level_order = {"hardware": 1, "system": 2, "scenario": 3, "service": 4, "uncategorized": 5}
    impact_order = {"high": 1, "medium": 2, "low": 3}
    gap_matrix.sort(key=lambda x: (level_order.get(x["taxonomy_level"], 9), impact_order.get(x["decision_impact"], 9)))

    return {
        "schema_version": "1.0",
        "self_product": self_product,
        "gap_count": len(gap_matrix),
        "gap_matrix": gap_matrix,
    }


def generate_differentiation_opportunities(gap_matrix: Dict) -> List[Dict]:
    """
    从 gap_matrix 提取差异化机会（decision_impact=high 且 gap_direction != parity）
    """
    opps = []
    for gap in gap_matrix["gap_matrix"]:
        if gap["decision_impact"] != "high":
            continue
        for comp, direction in gap["gap_directions"].items():
            if direction == "parity" or direction == "data_missing":
                continue
            opps.append({
                "aspect": gap["aspect"],
                "competitor": comp,
                "direction": direction,  # ahead=我方领先 / behind=我方落后
                "self_value": gap["self_value"],
                "their_value": gap["competitor_values"].get(comp),
                "evidence_ids": gap["evidence_ids"],
                "opportunity": (
                    f"差异化机会（我方领先）：{gap['aspect']} 对 {comp} 领先，可作为 Message House 核心卖点"
                    if direction == "ahead"
                    else f"差异化风险（我方落后）：{gap['aspect']} 对 {comp} 落后，需在定价或服务侧补偿"
                ),
            })
    return opps


def cmd_run(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    evidences = data.get("evidences", [])
    print(f"[load] {len(evidences)} evidences from {args.input}", file=sys.stderr)

    gap_matrix = build_gap_matrix(evidences, args.self_product)
    opps = generate_differentiation_opportunities(gap_matrix)
    gap_matrix["differentiation_opportunities"] = opps

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(gap_matrix, f, ensure_ascii=False, indent=2)

    print(f"\n[done] gap matrix → {out_path}", file=sys.stderr)
    print(f"  total gaps: {gap_matrix['gap_count']}", file=sys.stderr)
    print(f"  differentiation opportunities: {len(opps)}", file=sys.stderr)
    by_level = defaultdict(int)
    for g in gap_matrix["gap_matrix"]:
        by_level[g["taxonomy_level"]] += 1
    print(f"  by level: {dict(by_level)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Stage A: Gap Matrix Generator")
    parser.add_argument("--input", required=True, help="evidence.json path")
    parser.add_argument("--self-product", required=True, help="主品名称（如 商米 CPAD）")
    parser.add_argument("--output", required=True, help="gap_matrix.json output path")
    args = parser.parse_args()
    cmd_run(args)


if __name__ == "__main__":
    main()
