#!/usr/bin/env python3
"""
Compass 竞品分析 · Step 5: Pricing Calculator

职责：
  1. 从 evidence.json 提取价格类证据 (stage=B_pricing 或 aspect 含 price)
  2. 反推折扣栈 (list → distributor → reseller → end-user)
  3. 计算 price_per_unit（按 ICP 价值度量）
  4. 识别定价模型 (value-based / cost-plus / tiered / subscription)
  5. 输出价格定位象限 + ICP 价格弹性矩阵

强制用 Python 做真实算术（Function Calling），禁止只用文字描述价格。

Usage:
    python pricing_calc.py --input evidence.json --self-product "商米 CPAD" --icp-value-metric per_inch_display --output pricing_analysis.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


# === 价格数字提取 ===
def extract_price_usd(value: str) -> Optional[float]:
    """从字符串提取 USD 价格。支持 'USD 245' / '$245' / '245' / 'USD 245.50'"""
    if not value:
        return None
    s = str(value).replace(",", "").strip()
    # 优先匹配 USD / $ 前缀
    m = re.search(r"(?:usd|\$)\s*(\d+(?:\.\d+)?)", s, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # 退而求其次：纯数字
    m = re.search(r"^\s*(\d+(?:\.\d+)?)\s*$", s)
    if m:
        return float(m.group(1))
    return None


# === 折扣栈反推 ===
def reverse_engineer_discount_stack(price_evidences: List[Dict], competitor: str) -> Dict:
    """
    从价格类证据反推折扣栈。
    输入：所有价格类 evidences（aspect 含 list_price/distributor_price/reseller_price/end_user_price 等）
    输出：discount_stack JSON
    """
    layer_keywords = {
        "list": ["list_price", "msrp", "list", "retail_price"],
        "distributor": ["distributor_price", "distributor", "partner_price", "dealer"],
        "reseller": ["reseller_price", "reseller", "wholesale"],
        "end_user": ["end_user_price", "end_user", "amazon", "street_price", "selling_price"],
    }

    # 按 product + layer 聚合
    product_layer_price = defaultdict(dict)  # product -> layer -> (price, evidence_id)
    for ev in price_evidences:
        if ev.get("competitor", "").lower() != competitor.lower():
            continue
        product = ev.get("product") or "unknown"
        aspect = ev.get("aspect", "").lower()
        price = extract_price_usd(ev.get("value", ""))
        if price is None:
            continue
        for layer, keywords in layer_keywords.items():
            if any(k in aspect for k in keywords):
                # 取最高 confidence 的证据
                existing = product_layer_price[product].get(layer)
                if not existing or ev.get("confidence") == "high":
                    product_layer_price[product][layer] = {
                        "price_usd": price,
                        "evidence_id": ev["evidence_id"],
                        "source_type": ev.get("source_type"),
                        "confidence": ev.get("confidence"),
                    }
                break

    # 计算折扣栈
    stacks = []
    for product, layers in product_layer_price.items():
        stack = []
        layer_order = ["list", "distributor", "reseller", "end_user"]
        prev_price = None
        for layer in layer_order:
            if layer not in layers:
                continue
            entry = layers[layer]
            discount_pct = None
            if prev_price and prev_price > 0:
                discount_pct = round((prev_price - entry["price_usd"]) / prev_price * 100, 2)
            stack.append({
                "layer": layer,
                "price_usd": entry["price_usd"],
                "discount_pct": discount_pct,
                "evidence_id": entry["evidence_id"],
                "confidence": entry["confidence"],
            })
            prev_price = entry["price_usd"]
        if stack:
            total_discount = None
            if len(stack) >= 2:
                first = stack[0]["price_usd"]
                last = stack[-1]["price_usd"]
                if first > 0:
                    total_discount = round((first - last) / first * 100, 2)
            stacks.append({
                "competitor": competitor,
                "product": product,
                "discount_stack": stack,
                "total_discount_pct": total_discount,
            })
    return {"competitor": competitor, "stacks": stacks}


# === price_per_unit 计算 ===
def compute_price_per_unit(stacks: Dict, icp_value_metric: str, feature_evidences: List[Dict]) -> List[Dict]:
    """
    按 ICP 价值度量归一化价格。
    per_inch_display: price / display_size
    per_year_warranty: price / warranty_years
    per_day_use: price / (warranty_years × 365)
    """
    results = []
    for stack_obj in stacks["stacks"]:
        product = stack_obj["product"]
        end_user_price = next((s["price_usd"] for s in stack_obj["discount_stack"] if s["layer"] == "end_user"), None)
        if not end_user_price:
            end_user_price = stack_obj["discount_stack"][-1]["price_usd"] if stack_obj["discount_stack"] else None
        if not end_user_price:
            continue
        # 找价值度量对应的 feature 值
        metric_value = None
        metric_aspect_map = {
            "per_inch_display": "display_size",
            "per_year_warranty": "warranty",
            "per_day_use": "warranty",
        }
        target_aspect = metric_aspect_map.get(icp_value_metric)
        if target_aspect:
            for ev in feature_evidences:
                if ev.get("competitor", "").lower() == stacks["competitor"].lower() and target_aspect in ev.get("aspect", "").lower():
                    m = re.search(r"(\d+(?:\.\d+)?)", str(ev.get("value", "")))
                    if m:
                        metric_value = float(m.group(1))
                        break
        price_per_unit = None
        if metric_value and metric_value > 0:
            if icp_value_metric == "per_day_use":
                price_per_unit = round(end_user_price / (metric_value * 365), 4)
            else:
                price_per_unit = round(end_user_price / metric_value, 2)
        results.append({
            "competitor": stacks["competitor"],
            "product": product,
            "end_user_price_usd": end_user_price,
            "icp_value_metric": icp_value_metric,
            "metric_value": metric_value,
            "price_per_unit": price_per_unit,
            "evidence_id": stack_obj["discount_stack"][-1]["evidence_id"],
        })
    return results


# === 定价模型识别 ===
def identify_pricing_model(stacks: Dict) -> str:
    """
    基于折扣栈结构识别定价模型。
    - 多层 partner tier → tiered
    - 折扣稳定（每层折扣接近）→ cost-plus
    - 折扣差异大、分层明显 → value-based
    - 有 monthly/annual → subscription
    """
    if not stacks["stacks"]:
        return "unknown"
    # 取第一个 stack 判断
    stack = stacks["stacks"][0]["discount_stack"]
    if len(stack) >= 3:
        # 多层 → tiered
        return "tiered"
    if len(stack) == 2:
        discounts = [s["discount_pct"] for s in stack if s.get("discount_pct") is not None]
        if discounts and max(discounts) - min(discounts) < 5:
            return "cost_plus"
        return "value_based"
    return "unknown"


# === 价格定位象限 ===
def build_positioning_quadrant(per_unit_data: List[Dict], self_product: str) -> Dict:
    """构建价格定位象限：X=price, Y=价值感知分（简化版：用 evidence 数量代理）"""
    if not per_unit_data:
        return {"quadrants": {}}
    prices = [p["end_user_price_usd"] for p in per_unit_data if p.get("end_user_price_usd")]
    if not prices:
        return {"quadrants": {}}
    median_price = sorted(prices)[len(prices) // 2]
    quadrants = {"premium": [], "value_leader": [], "overpriced": [], "budget": []}
    for p in per_unit_data:
        x = p["end_user_price_usd"]
        # 简化：value 感知用 confidence 高低代理（high=高感知）
        y_high = p.get("confidence") == "high"
        if x >= median_price and y_high:
            quadrants["premium"].append(p)
        elif x < median_price and y_high:
            quadrants["value_leader"].append(p)
        elif x >= median_price and not y_high:
            quadrants["overpriced"].append(p)
        else:
            quadrants["budget"].append(p)
    return {"median_price_usd": median_price, "quadrants": quadrants}


# === ICP 价格弹性矩阵 ===
def build_elasticity_matrix(per_unit_data: List[Dict]) -> List[Dict]:
    """按 persona 输出价格敏感度 vs 价值感知矩阵（参考 icp_persona_library.md）"""
    persona_matrix = [
        {"persona": "procurement_officer", "price_sensitivity": "high", "value_perception": "medium", "strategy": "强调 TCO、折扣栈、长期成本"},
        {"persona": "cfo", "price_sensitivity": "high", "value_perception": "high", "strategy": "强调 ROI、回本周期"},
        {"persona": "it_admin", "price_sensitivity": "medium", "value_perception": "high", "strategy": "强调易维护、降运维成本"},
        {"persona": "channel_partner", "price_sensitivity": "very_high", "value_perception": "medium", "strategy": "强调 margin、补贴政策"},
    ]
    return persona_matrix


def cmd_run(args):
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    evidences = data.get("evidences", [])
    price_evidences = [e for e in evidences if e.get("stage") == "B_pricing" or "price" in e.get("aspect", "").lower()]
    feature_evidences = [e for e in evidences if e.get("stage") in ("A_feature", "shared")]
    print(f"[load] {len(price_evidences)} price evidences, {len(feature_evidences)} feature evidences", file=sys.stderr)

    competitors = set(e["competitor"] for e in price_evidences if e.get("competitor"))
    all_stacks = []
    all_per_unit = []
    for comp in competitors:
        if comp.lower() in (args.self_product.lower(), "self", "商米", "cpad"):
            continue
        print(f"[analyze] competitor: {comp}", file=sys.stderr)
        stacks = reverse_engineer_discount_stack(price_evidences, comp)
        all_stacks.append(stacks)
        per_unit = compute_price_per_unit(stacks, args.icp_value_metric, feature_evidences)
        all_per_unit.extend(per_unit)

    pricing_models = {s["competitor"]: identify_pricing_model(s) for s in all_stacks}
    quadrant = build_positioning_quadrant(all_per_unit, args.self_product)
    elasticity = build_elasticity_matrix(all_per_unit)

    output = {
        "schema_version": "1.0",
        "self_product": args.self_product,
        "icp_value_metric": args.icp_value_metric,
        "competitor_stacks": all_stacks,
        "price_per_unit": all_per_unit,
        "pricing_models": pricing_models,
        "positioning_quadrant": quadrant,
        "elasticity_matrix": elasticity,
        "notes": "所有价格数字由 Python 计算产出（Function Calling），禁止只用文字描述价格",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[done] pricing analysis → {out_path}", file=sys.stderr)
    print(f"  competitors analyzed: {len(all_stacks)}", file=sys.stderr)
    print(f"  pricing models: {pricing_models}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Stage B: Pricing Calculator")
    parser.add_argument("--input", required=True, help="evidence.json path")
    parser.add_argument("--self-product", required=True)
    parser.add_argument("--icp-value-metric", default="per_inch_display",
                        choices=["per_inch_display", "per_year_warranty", "per_day_use"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cmd_run(args)


if __name__ == "__main__":
    main()
