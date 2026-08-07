# 定价模型参考（Pricing Models）

> Step 5 价格策略使用的定价模型分类与识别规则。
> 这是 `pricing_calc.py` 识别竞品定价模型的依据。

## 1. 定价模型分类

### 1.1 Value-based Pricing（价值定价）

**定义**：价格基于客户感知价值，而非成本或市场均价。

**识别信号**：
- 不同 SKU 间价差 > 2x（同成本结构下）
- 高端 SKU 价格接近竞品旗舰，入门 SKU 明显低于竞品
- 价目表分层明显（good/better/best）
- 价格与 ICP 价值度量（如「每台设备收入」）强相关

**典型场景**：SaaS、差异化强的硬件（如 Apple iPad 商业版）。

### 1.2 Cost-plus Pricing（成本加成）

**定义**：价格 = 成本 × (1 + 加成率)。

**识别信号**：
- 不同 SKU 间价差与配置差异成比例
- 加成率稳定（如统一 30%）
- 价目表结构线性（配置越高价格等比上升）

**典型场景**：低差异化硬件、经销商品。

### 1.3 Tiered Pricing（分层定价）

**定义**：按购买量或客户等级分多层价格。

**识别信号**：
- 价目表有明确的 quantity break（如 1-9 / 10-49 / 50+）
- 或有 partner tier（Authorized / Gold / Platinum）
- 同 SKU 多个价格列

**典型场景**：B2B 硬件经销。

### 1.4 Subscription Pricing（订阅）

**定义**：按月/年付费，硬件可能 0 元或低价。

**识别信号**：
- 价目表有 monthly / annual 列
- 硬件 + 服务打包价
- 有 commitment period（12/24/36 月）

**典型场景**：SaaS、硬件+SaaS 组合（如 Square Terminal）。

### 1.5 Skimming Pricing（撇脂定价）

**定义**：新品高价，随时间逐步降价。

**识别信号**：
- 同一 SKU 历史价格持续下降
- 新 SKU 价格显著高于老 SKU

**典型场景**：技术领先型新品。

### 1.6 Penetration Pricing（渗透定价）

**定义**：低价进入市场，抢占份额。

**识别信号**：
- 价格显著低于竞品同档 SKU
- 常配合「首单优惠」「渠道补贴」

**典型场景**：新进入市场的二线品牌。

---

## 2. 折扣栈反推（Discount Stack）

B2B 硬件典型折扣栈：

```
List Price (MSRP)
    ↓ distributor discount (e.g. 30%)
Distributor Price
    ↓ reseller discount (e.g. 15%)
Reseller Price
    ↓ end-user discount (e.g. 5%)
End-User Price
```

**反推规则**：
1. 若价目表含 list + distributor 两列 → 直接得 distributor discount %
2. 若仅含 distributor price → 需 WebSearch 找 list price 反推
3. 若有多层 partner tier → 每层独立折扣
4. end-user price 缺失时用 Amazon / 零售站价格补全

**输出格式**（pricing_calc.py 产出）：

```json
{
  "competitor": "竞品A",
  "product": "产品X",
  "discount_stack": [
    {"layer": "list", "price_usd": 350, "evidence_id": "EV-2026-010"},
    {"layer": "distributor", "price_usd": 245, "discount_pct": 30.0, "evidence_id": "EV-2026-011"},
    {"layer": "reseller", "price_usd": 295, "discount_pct": 20.4, "evidence_id": "EV-2026-012"},
    {"layer": "end_user", "price_usd": 320, "discount_pct": 8.5, "evidence_id": "EV-2026-013"}
  ],
  "total_discount_pct": 8.6,
  "pricing_model": "tiered",
  "confidence": "high",
  "notes": "Q2 FY26 印度价目表 + Amazon 印度零售价反推"
}
```

---

## 3. price_per_unit 计算

按 ICP 价值度量归一化，避免「贵 / 便宜」的绝对价格误导。

**常见 ICP 价值度量**：

| 品类 | 价值度量 | 示例 |
|---|---|---|
| 商用平板 | 每寸屏 USD | price / display_size |
| POS 终端 | 每天使用成本 | price / (warranty_years × 365) |
| 支付硬件 | 每笔交易成本 | price / 月均交易笔数 |
| SaaS | 每用户月费 | monthly_fee / active_users |

**计算规则**：
1. 在 `project.yaml` 的 `icp_value_metric` 字段定义价值度量
2. `pricing_calc.py` 自动计算 price_per_unit
3. 输出对比表：competitor × product × price × value_metric × price_per_unit

---

## 4. 价格定位象限

二维矩阵，用于 Step 5 输出的「价格定位建议」段落。

```
高价值感知
    │
    │  Premium（高价值高价格）  │  Value Leader（高价值低价格）
    │  - 高端商用平板           │  - 主品（目标定位）
    │                          │
────┼──────────────────────────┼──────────────────────────
    │                          │
    │  Overpriced（低价值高价格）│  Budget（低价值低价格）
    │  - 部分竞品旗舰           │  - 入门级竞品
    │                          │
低价值感知
    低价格 ←─────────────────→ 高价格
```

**绘制规则**：
- X 轴：end_user_price（或 price_per_unit）
- Y 轴：价值感知分（基于 Step 5 功能对标 + Step 5 VOC 情感综合得分）
- 主品默认画在 Value Leader 象限作为目标定位

---

## 5. ICP 价格弹性矩阵

按 persona 维度输出「价格敏感度 vs 价值感知」矩阵：

| persona | 价格敏感度 | 价值感知 | 推荐策略 |
|---|---|---|---|
| procurement_officer | 高 | 中 | 强调 TCO、折扣栈、长期成本 |
| cfo | 高 | 高 | 强调 ROI、回本周期 |
| it_admin | 中 | 高 | 强调易维护、降运维成本 |
| channel_partner | 极高 | 中 | 强调 margin、补贴政策 |

**禁止**：把所有 persona 都标「价格敏感度=高」（这是泛泛画像，违反 Step 5 规则）。

---

## 6. 价格类声明的 confidence 规则

（详见 `evidence_rules.md` 第 3 条，此处重申核心）

| 声明 | confidence=high 要求 | confidence=medium 容许 |
|---|---|---|
| list_price | official_spec 或 price_list | review, web_search |
| distributor_price | price_list 或 internal_data | web_search, analyst |
| 折扣栈反推值 | 基于 price_list 反推 | 基于 web_search 反推 |
| pricing_model 识别 | 基于 ≥3 个 SKU 的 price_list 模式 | 基于 web_search 推断 |

**禁止**：仅凭 LLM 训练知识报价格（confidence 永远不得为 high）。

---

## 7. 产品落地映射

Step 5 的输出必须能映射产品核心价值：

| 产品能力 | Step 5 对应输出 |
|---|---|
| 经营看板（毛利优化） | 「低毛利区域识别」段落（基于 price_per_unit 反推毛利） |
| 定价 SOP（AI 自动化定价） | 「定价模型识别」段落（自动化判定 value-based/cost-plus/tiered） |
