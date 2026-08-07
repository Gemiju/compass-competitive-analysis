# 证据规则（Evidence Rules）

> 本文件是 Compass 竞品分析所有 Step 共享的引用规则。
> 违反任一规则的报告视为不合格，禁止用于客户交付。

## 1. 强制引用

报告中**每条事实声明**必须带 `[EV-xxxx]` 引用，文末附录列出证据全文。

**声明**定义：任何可被验证的真伪命题，包括但不限于：
- 规格类：「天之河 TZH-P13 屏幕 10.1 寸」
- 价格类：「经销商价 USD 245」
- 渠道类：「iMin 在印度通过 distributor X 销售」
- VOC 类：「IT 管理员反馈安装复杂」

**非声明**（无需引用）：分析结论、推荐建议、推理过程——但前提是结论必须基于已引用的证据。

## 2. 未验证标记

未带引用的声明必须打 `⚠️ 未验证` 标记。

```markdown
# 正确示例
天之河 TZH-P13 经销商价为 USD 245 [EV-2026-002]，较 list price 折扣约 30%。

# 错误示例（无引用）
天之河 TZH-P13 经销商价为 USD 245，较 list price 折扣约 30%。

# 允许但需标记
据行业惯例，B2B 硬件经销商毛利约 15-20% ⚠️ 未验证。
```

**禁止**：`⚠️ 未验证` 的声明不得用于客户交付物（如正式报价单、合同附件、对外 PPT）。

## 3. 价格类声明的额外要求

价格类声明的 `confidence=high` 必须有 `source_type=price_list` 或 `official_spec` 支撑。

| 声明类型 | confidence=high 允许的 source_type | confidence=medium 允许的 source_type |
|---|---|---|
| list_price | official_spec, price_list | review, web_search |
| distributor_price | price_list, internal_data | web_search, analyst |
| reseller_margin | price_list, internal_data | analyst, web_search |
| price_per_unit（计算值） | 基于 confidence=high 的输入计算 | 基于 confidence=medium 的输入计算 |
| discount_stack（反推值） | 基于 price_list 反推 | 基于 web_search 反推 |

**价格类声明禁止**：
- 仅凭 LLM 训练知识报价格（confidence 永远不得为 high）
- 仅凭单条 Reddit 评论推断官方定价
- 用「大约」「左右」等模糊词替代具体数字（除非证据本身模糊）

## 4. 联网搜索数据规则

联网搜索抓取的数据 `verified_by=web_search`，需附：
- 完整 URL（`source_url`）
- 抓取日期（`source_date`）
- 网站类型（`source_type`: review / forum / analyst / web_search）
- 原文摘录（`verbatim_quote`，VOC 类必填）

**联网数据默认 confidence=medium**，除非：
- 来自官方竞品官网（可升 confidence=high，source_type=official_spec）
- 来自权威分析师报告（可升 confidence=high，source_type=analyst）

## 5. RAG 优先级（核心）

数据获取严格按以下优先级：

```
1. 本地证据库命中 (confidence=high, verified_by=local_evidence_db)
       ↓ 未命中
2. 联网搜索 (confidence=medium, verified_by=web_search)
       ↓ 搜索无结果
3. LLM 推断 (confidence=low, verified_by=llm_inference, 必须标 ⚠️ 未验证)
       ↓ 用户拒绝 LLM 推断
4. 报告中标注「数据缺失，建议人工补充」
```

**禁止跳级**：不得在本地库未查的情况下直接用 LLM 推断。

## 6. evidence_id 分配规则

- 格式：`EV-YYYY-NNN`（如 EV-2026-001）
- YYYY = 证据年份（用 source_date 的年份，不是当前年份）
- NNN = 年内顺序号（001 起，三位数）
- 一次分析会话内不重复

## 7. 多 Step 共享证据

`stage=shared` 的证据可被各 Step 同时引用，避免重复存储。
例如「天之河 TZH-P13 在印度上市」既是功能背景（Step 5）又是渠道事实（Step 5）。

## 8. 决策影响度过滤

Step 5 Review 阶段必须对每条证据评估 `decision_impact`：
- `high`：直接影响 ICP 购买决策（进报告主体）
- `medium`：间接影响（进附录或脚注）
- `low`：无影响（不进报告）

**判断标准**：问「如果删除这条差异，ICP 的购买决策会改变吗？」
- 会 → high
- 不会但会影响体验 → medium
- 完全无关 → low

## 9. 证据附录格式

报告文末必须附「证据附录」章节，列出所有引用的 evidence 全文：

```markdown
## 证据附录

### EV-2026-001
- competitor: iMin
- product: 天之河 TZH-P13
- aspect: display_size
- value: 10.1 inch
- source_type: official_spec
- source_url: file://evidence_db/cpad_competitive.xlsx#Sheet1
- source_date: 2026-04-11
- confidence: high
- verified_by: local_evidence_db

### EV-2026-002
...
```

## 10. 反作弊规则

- 禁止伪造 evidence_id
- 禁止用 LLM 生成的「 plausible 」数据冒充真实证据
- 禁止把 confidence=low 的推断标为 high
- 禁止删除不利证据（如竞品优于我方的数据）
- 任何被发现作弊的报告立即作废，重新分析
