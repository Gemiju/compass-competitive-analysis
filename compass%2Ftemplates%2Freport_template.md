# Compass 竞品分析 · 主报告模板

> 本文件是 SKILL 生成 `report.md` 的结构骨架。
> SKILL LLM 按本骨架填充内容。
> 占位符用 `{{...}}` 标注，SKILL 根据分析结果替换。

---

# {{product}} 竞品分析报告

**主品**：{{self_product}}
**竞品**：{{competitors_list}}
**市场**：{{market_region}}
**时间窗口**：{{time_window}}
**业务决策**：{{business_decision}}
**生成时间**：{{generated_at}}

---

## 执行摘要

{{one_paragraph_summary}}

**关键指标**：
- 功能差距项：{{gap_count}}（差异化机会 {{differentiation_count}}）
- 价格定位：{{pricing_position_summary}}
- 渠道覆盖：{{channel_coverage_summary}}
- 证据总数：{{evidence_count}}（高置信度 {{high_confidence_pct}}%）

---

## 三、功能对标分析

### A.1 分析方法

按 `references/taxonomy.md` 四级分类（硬件/系统/场景/服务）生成 gap 矩阵。每条 gap 标注 gap_direction（领先/落后/持平）与 decision_impact（high/medium/low）。Review 阶段过滤 decision_impact=low 的项。

### A.2 Gap 矩阵

| 分类 | 维度 | {{self_product}} | {{competitor_1}} | {{competitor_2}} | 差距方向 | 决策影响 | 证据 |
|---|---|---|---|---|---|---|---|
| hardware | display_size | {{self_display}} | {{comp1_display}} [EV-xxxx] | {{comp2_display}} [EV-xxxx] | {{direction}} | {{impact}} | [EV-xxxx] |
| ... | ... | ... | ... | ... | ... | ... | ... |

### A.3 差异化机会

{{opportunity_paragraph_1_with_citations}}

{{opportunity_paragraph_2_with_citations}}

{{opportunity_paragraph_3_with_citations}}

> 每个 opportunity 段落必须引用 ≥2 条证据。

---

## 四、价格策略分析

### B.1 分析方法

强制用 Python 做真实价格算术（Function Calling），禁止只用文字描述价格。基于 `references/pricing_models.md` 反推折扣栈与识别定价模型。

### B.2 折扣栈反推

**{{competitor_1}}**

| 层级 | 价格 USD | 折扣 % | 置信度 | 证据 |
|---|---|---|---|---|
| list | {{list_price}} | - | {{confidence}} | [EV-xxxx] |
| distributor | {{distributor_price}} | {{discount_pct}} | {{confidence}} | [EV-xxxx] |
| reseller | {{reseller_price}} | {{discount_pct}} | {{confidence}} | [EV-xxxx] |
| end_user | {{end_user_price}} | {{discount_pct}} | {{confidence}} | [EV-xxxx] |

**总折扣**：{{total_discount_pct}}%

### B.3 Price-per-Unit（{{icp_value_metric}}）

| 竞品 | 产品 | End-User Price | 度量值 | Price/Unit | 证据 |
|---|---|---|---|---|---|
| {{competitor_1}} | {{product}} | USD {{price}} | {{metric_value}} | {{per_unit}} | [EV-xxxx] |
| ... | ... | ... | ... | ... | ... |

### B.4 定价模型识别

{{pricing_model_paragraph_with_citations}}

### B.5 ICP 价格弹性矩阵

| Persona | 价格敏感度 | 价值感知 | 推荐策略 |
|---|---|---|---|
| procurement_officer | 高 | 中 | {{strategy}} |
| cfo | 高 | 高 | {{strategy}} |
| it_admin | 中 | 高 | {{strategy}} |
| channel_partner | 极高 | 中 | {{strategy}} |

### B.6 价格定位建议

**当前定位**：{{positioning_paragraph_1_with_≥2_citations}}

**风险**：{{positioning_paragraph_2_with_≥2_citations}}

**建议**：{{positioning_paragraph_3_with_≥2_citations}}

---

## 五、用户画像与场景分析

### C.1 多视角预研究

按 `references/icp_persona_library.md` 从 7 个 persona 视角提问。**禁止只从我方视角分析**。

**procurement_officer 视角**：{{answer_with_citations}}

**cfo 视角**：{{answer_with_citations}}

**it_admin 视角**：{{answer_with_citations}}

**channel_partner 视角**：{{answer_with_citations}}

**competitor_sales 视角**（反向推导竞品 GTM）：{{answer_with_citations}}

**industry_analyst 视角**：{{answer_with_citations}}

**end_user 视角**：{{answer_with_citations}}

### C.2 渠道覆盖矩阵

| 渠道类型 | {{self_product}} | {{competitor_1}} | {{competitor_2}} |
|---|---|---|---|
| 直营官网 | {{yes_no}} | {{yes_no}} | {{yes_no}} |
| 授权经销 | {{yes_no}} | {{yes_no}} | {{yes_no}} |
| 电商 | {{yes_no}} | {{yes_no}} | {{yes_no}} |
| 集成商 | {{yes_no}} | {{yes_no}} | {{yes_no}} |

### C.3 Message House 建议

{{message_house_paragraph_with_citations}}

---

## ICP 与决策建议

### 推荐 ICP

{{icp_recommendation}}

### 决策建议

**{{business_decision}}**：

{{decision_recommendation_with_citations}}

---

## 证据附录

### EV-2026-001
- competitor: {{competitor}}
- product: {{product}}
- aspect: {{aspect}}
- value: {{value}}
- source_type: {{source_type}}
- source_url: {{source_url}}
- source_date: {{source_date}}
- confidence: {{confidence}}
- verified_by: {{verified_by}}

### EV-2026-002
...

---

## 假设与局限

{{assumptions_list}}

## 未验证项

{{unverified_items_with_warning_marks}}

---

> 本报告由 Compass 竞品分析 AI 产品自动生成。
> 数据策略：RAG 架构（本地证据库优先 + 联网搜索兜底）。详见 `references/evidence_rules.md`。
