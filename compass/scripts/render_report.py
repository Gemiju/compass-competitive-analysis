#!/usr/bin/env python3
"""
Compass 竞品分析 · Report Renderer

职责：
  1. 读取 report.md (主报告 Markdown) + evidence.json + gap_matrix.json + pricing_analysis.json + voc_analysis.json
  2. 用 Jinja2 渲染 HTML 仪表盘 (基于 templates/dashboard.html)
  3. 输出 report.html（可双击打开，5 个 Tab：摘要/功能/价格/渠道/证据）

Usage:
    python render_report.py --report report.md --evidence evidence.json --gap gap_matrix.json --pricing pricing_analysis.json --voc voc_analysis.json --template ../templates/dashboard.html --output report.html
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def _import_jinja2():
    try:
        from jinja2 import Template
        return Template
    except ImportError:
        print("ERROR: jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
        sys.exit(2)


# === 内置 HTML 模板（若 templates/dashboard.html 不存在时用这个） ===
BUILTIN_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Compass 竞品分析 · {{ self_product }} vs {{ competitors|join(", ") }}</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, "PingFang SC", sans-serif; margin: 0; background: #f5f5f7; color: #1d1d1f; }
  .header { background: linear-gradient(135deg, #1d1d1f 0%, #424245 100%); color: white; padding: 32px 48px; }
  .header h1 { margin: 0 0 8px 0; font-size: 28px; }
  .header .meta { font-size: 14px; opacity: 0.7; }
  .tabs { display: flex; background: white; border-bottom: 1px solid #d2d2d7; position: sticky; top: 0; z-index: 10; }
  .tab { padding: 16px 24px; cursor: pointer; border-bottom: 3px solid transparent; font-size: 14px; font-weight: 500; }
  .tab.active { border-bottom-color: #0071e3; color: #0071e3; }
  .tab:hover { background: #f5f5f7; }
  .panel { display: none; padding: 32px 48px; max-width: 1200px; margin: 0 auto; }
  .panel.active { display: block; }
  .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .card h2 { margin: 0 0 16px 0; font-size: 20px; }
  .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
  .metric { background: white; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .metric .value { font-size: 32px; font-weight: 700; color: #0071e3; }
  .metric .label { font-size: 12px; color: #6e6e73; margin-top: 4px; text-transform: uppercase; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e5ea; }
  th { background: #f5f5f7; font-weight: 600; }
  tr:hover { background: #fafafa; }
  .ev-ref { color: #0071e3; font-size: 11px; font-family: monospace; }
  .warning { color: #ff9500; font-weight: 600; }
  .quote { background: #f5f5f7; border-left: 3px solid #0071e3; padding: 12px 16px; margin: 8px 0; font-style: italic; font-size: 13px; }
  .persona-tag { display: inline-block; background: #e8f0fe; color: #1967d2; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; }
  .sentiment-neg { color: #d93025; }
  .sentiment-pos { color: #0d904f; }
  .sentiment-neu { color: #5f6368; }
  pre { background: #1d1d1f; color: #f5f5f7; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 12px; }
</style>
</head>
<body>
<div class="header">
  <h1>Compass 竞品分析 · {{ self_product }} vs {{ competitors|join(", ") }}</h1>
  <div class="meta">生成时间: {{ generated_at }} | 市场区域: {{ market_region }} | 时间窗口: {{ time_window }}</div>
</div>
<div class="tabs">
  <div class="tab active" data-panel="summary">Executive Summary</div>
  <div class="tab" data-panel="feature">Feature Benchmark</div>
  <div class="tab" data-panel="pricing">Pricing Strategy</div>
  <div class="tab" data-panel="channel">Channel & GTM</div>
  <div class="tab" data-panel="evidence">Evidence</div>
</div>

<div class="panel active" id="panel-summary">
  <div class="metric-grid">
    <div class="metric"><div class="value">{{ gap_count }}</div><div class="label">功能差距项</div></div>
    <div class="metric"><div class="value">{{ differentiation_count }}</div><div class="label">差异化机会</div></div>
    <div class="metric"><div class="value">{{ voc_count }}</div><div class="label">VOC 样本</div></div>
    <div class="metric"><div class="value">{{ persona_count }}</div><div class="label">Persona 覆盖</div></div>
    <div class="metric"><div class="value">{{ evidence_count }}</div><div class="label">证据总数</div></div>
    <div class="metric"><div class="value">{{ high_confidence_pct }}%</div><div class="label">高置信度占比</div></div>
  </div>
  <div class="card"><h2>执行摘要</h2><div>{{ report_summary|e }}</div></div>
  <div class="card"><h2>定价模型识别</h2>
    <table><tr><th>竞品</th><th>定价模型</th><th>折扣栈深度</th></tr>
    {% for comp, model in pricing_models.items() %}
    <tr><td>{{ comp }}</td><td>{{ model }}</td><td>{{ competitor_stacks|selectattr("competitor","equalto",comp)|list|first|attr('stacks')|first|attr('discount_stack')|length if competitor_stacks else '-' }}</td></tr>
    {% endfor %}
    </table>
  </div>
</div>

<div class="panel" id="panel-feature">
  <div class="card"><h2>功能 Gap 矩阵</h2>
    <table><tr><th>分类</th><th>维度</th><th>我方</th>{% for c in competitors %}<th>{{ c }}</th>{% endfor %}<th>差距方向</th><th>决策影响</th><th>证据</th></tr>
    {% for gap in gap_matrix %}
    <tr>
      <td>{{ gap.taxonomy_level }}</td>
      <td>{{ gap.aspect }}</td>
      <td>{{ gap.self_value or '⚠️ 未验证' }}</td>
      {% for c in competitors %}<td>{{ gap.competitor_values.get(c, '-') }}</td>{% endfor %}
      <td>{% for comp, d in gap.gap_directions.items() %}{{ comp }}: {{ d }} {% endfor %}</td>
      <td>{{ gap.decision_impact }}</td>
      <td>{% for eid in gap.evidence_ids %}<span class="ev-ref">[{{ eid }}]</span> {% endfor %}</td>
    </tr>
    {% endfor %}
    </table>
  </div>
  <div class="card"><h2>差异化机会</h2>
    {% for opp in differentiation_opportunities %}
    <div>{{ opp.opportunity }} {% for eid in opp.evidence_ids %}<span class="ev-ref">[{{ eid }}]</span>{% endfor %}</div>
    {% endfor %}
  </div>
</div>

<div class="panel" id="panel-pricing">
  <div class="card"><h2>折扣栈反推</h2>
    {% for stack in competitor_stacks %}
      {% for s in stack.stacks %}
      <h3>{{ stack.competitor }} · {{ s.product }}</h3>
      <table><tr><th>层级</th><th>价格 USD</th><th>折扣 %</th><th>置信度</th><th>证据</th></tr>
      {% for layer in s.discount_stack %}
      <tr><td>{{ layer.layer }}</td><td>{{ layer.price_usd }}</td><td>{{ layer.discount_pct if layer.discount_pct is not none else '-' }}</td><td>{{ layer.confidence }}</td><td><span class="ev-ref">[{{ layer.evidence_id }}]</span></td></tr>
      {% endfor %}
      </table>
      <p>总折扣: {{ s.total_discount_pct if s.total_discount_pct is not none else '-' }}%</p>
      {% endfor %}
    {% endfor %}
  </div>
  <div class="card"><h2>Price-per-Unit ({{ icp_value_metric }})</h2>
    <table><tr><th>竞品</th><th>产品</th><th>End-User Price</th><th>度量值</th><th>Price/Unit</th><th>证据</th></tr>
    {% for p in price_per_unit %}
    <tr><td>{{ p.competitor }}</td><td>{{ p.product }}</td><td>USD {{ p.end_user_price_usd }}</td><td>{{ p.metric_value or '⚠️ 未验证' }}</td><td>{{ p.price_per_unit or '⚠️ 未验证' }}</td><td><span class="ev-ref">[{{ p.evidence_id }}]</span></td></tr>
    {% endfor %}
    </table>
  </div>
  <div class="card"><h2>ICP 价格弹性矩阵</h2>
    <table><tr><th>Persona</th><th>价格敏感度</th><th>价值感知</th><th>推荐策略</th></tr>
    {% for e in elasticity_matrix %}
    <tr><td>{{ e.persona }}</td><td>{{ e.price_sensitivity }}</td><td>{{ e.value_perception }}</td><td>{{ e.strategy }}</td></tr>
    {% endfor %}
    </table>
  </div>
</div>

<div class="panel" id="panel-channel">
  {% for sidebar in voc_sidebars %}
  <div class="card"><h2>{{ sidebar.competitor }} · VOC 侧边栏 ({{ sidebar.voc_count }} 条)</h2>
    {% for v in sidebar.sidebar %}
    <div class="quote">
      <div>{{ v.verbatim_quote }}</div>
      <div style="margin-top:8px;font-size:11px;">
        <span class="persona-tag">{{ v.persona or '未识别' }}</span>
        <span class="sentiment-{{ 'neg' if v.sentiment=='negative' else ('pos' if v.sentiment=='positive' else 'neu') }}">{{ v.sentiment }}</span>
        | {{ v.source_date }} | <span class="ev-ref">[{{ v.evidence_id }}]</span>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endfor %}
  <div class="card"><h2>Message House 建议</h2>
    <p>{{ message_house.recommendation }}</p>
    {% for comp, pains in message_house.competitor_pain_points.items() %}
    <h4>{{ comp }} Top 痛点</h4>
    <ul>{% for aspect, count in pains %}<li>{{ aspect }} ({{ count }} 条负面)</li>{% endfor %}</ul>
    {% endfor %}
  </div>
</div>

<div class="panel" id="panel-evidence">
  <div class="card"><h2>证据库 ({{ evidence_count }} 条)</h2>
    <table><tr><th>ID</th><th>竞品</th><th>维度</th><th>值</th><th>来源类型</th><th>置信度</th><th>验证方式</th><th>日期</th><th>URL</th></tr>
    {% for ev in evidences %}
    <tr>
      <td class="ev-ref">{{ ev.evidence_id }}</td>
      <td>{{ ev.competitor }}</td>
      <td>{{ ev.aspect }}</td>
      <td>{{ ev.value[:60] }}</td>
      <td>{{ ev.source_type }}</td>
      <td>{{ ev.confidence }}</td>
      <td>{{ ev.verified_by }}</td>
      <td>{{ ev.source_date }}</td>
      <td style="font-size:10px;max-width:200px;overflow:hidden;text-overflow:ellipsis;">{{ ev.source_url }}</td>
    </tr>
    {% endfor %}
    </table>
  </div>
</div>

<script>
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      document.getElementById('panel-' + t.dataset.panel).classList.add('active');
    });
  });
</script>
</body>
</html>"""


def cmd_run(args):
    Template = _import_jinja2()

    # 加载所有输入
    with open(args.report, "r", encoding="utf-8") as f:
        report_md = f.read()
    with open(args.evidence, "r", encoding="utf-8") as f:
        evidence_data = json.load(f)
    with open(args.gap, "r", encoding="utf-8") as f:
        gap_data = json.load(f)
    with open(args.pricing, "r", encoding="utf-8") as f:
        pricing_data = json.load(f)
    with open(args.voc, "r", encoding="utf-8") as f:
        voc_data = json.load(f)

    # 计算指标
    evidences = evidence_data.get("evidences", [])
    evidence_count = len(evidences)
    high_confidence = sum(1 for e in evidences if e.get("confidence") == "high")
    high_confidence_pct = round(high_confidence / evidence_count * 100, 1) if evidence_count else 0

    competitors = list(set(e["competitor"] for e in evidences if e.get("competitor") and e["competitor"] not in (args.self_product, "self", "商米", "CPAD")))

    # 模板选择：优先外部模板，否则用内置
    template_str = BUILTIN_TEMPLATE
    if args.template and Path(args.template).exists():
        with open(args.template, "r", encoding="utf-8") as f:
            template_str = f.read()

    tpl = Template(template_str)
    html = tpl.render(
        self_product=args.self_product,
        competitors=competitors,
        generated_at=evidence_data.get("generated_at", ""),
        market_region=args.market_region or "N/A",
        time_window=args.time_window or "N/A",
        gap_count=gap_data.get("gap_count", 0),
        gap_matrix=gap_data.get("gap_matrix", []),
        differentiation_opportunities=gap_data.get("differentiation_opportunities", []),
        differentiation_count=len(gap_data.get("differentiation_opportunities", [])),
        voc_count=voc_data.get("voc_count", 0),
        persona_count=voc_data.get("persona_diversity", {}).get("persona_count", 0),
        voc_sidebars=voc_data.get("voc_sidebars", []),
        message_house=voc_data.get("message_house", {}),
        pricing_models=pricing_data.get("pricing_models", {}),
        competitor_stacks=pricing_data.get("competitor_stacks", []),
        price_per_unit=pricing_data.get("price_per_unit", []),
        elasticity_matrix=pricing_data.get("elasticity_matrix", []),
        icp_value_metric=pricing_data.get("icp_value_metric", ""),
        evidence_count=evidence_count,
        high_confidence_pct=high_confidence_pct,
        evidences=evidences,
        report_summary=report_md[:2000],
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[done] HTML dashboard → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Report Renderer: Markdown + JSON → HTML")
    parser.add_argument("--report", required=True, help="report.md path")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--gap", required=True)
    parser.add_argument("--pricing", required=True)
    parser.add_argument("--voc", required=True)
    parser.add_argument("--template", help="dashboard.html template path (optional, has builtin fallback)")
    parser.add_argument("--output", required=True)
    parser.add_argument("--market-region")
    parser.add_argument("--time-window")
    args = parser.parse_args()
    cmd_run(args)


if __name__ == "__main__":
    main()
