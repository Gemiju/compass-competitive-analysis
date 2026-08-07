---
name: compass-competitive-analysis
description: 通用竞品分析 AI 产品。当任务涉及竞品分析、功能对标、价格拆解、渠道打法、ICP 画像、GTM 策略、Message House、市场机会判断、新品上市决策、定价策略验证时使用本 Skill。输入竞品名+目标市场，输出 6 步框架结构化报告（Markdown + HTML 仪表盘）。禁止纯参数表/情绪统计/泛泛画像输出。本地证据库命中时优先用库内数据，未命中时联网搜索补全并标 ⚠️ 待验证。
dependency:
  python: ">=3.9"
---

# Compass 竞品分析

> 一款基于 TRAE Skill 体系的通用竞品分析 AI 产品。
> 采用 6 步分析框架（明确目标 → 选择竞品 → 确定维度 → 收集信息 → 整理分析 → 总结报告）。
> 采用 RAG 架构（本地证据库优先 + 联网搜索兜底），杜绝 LLM 编造数据。

## 何时使用

当任务涉及以下任一目标时使用本 Skill：
- 通用竞品分析（任意品类、任意市场）
- 功能对标 / gap 矩阵 / 差异化机会识别
- 价格拆解 / 定价模型识别 / 折扣栈反推 / 价格定位建议
- 渠道打法 / GTM 策略 / Message House / ICP 渠道偏好
- 真实竞品、替代方案和「不购买」识别
- 用户购买决策、切换、升级、退货或流失分析
- ICP、使用场景、市场机会和优先级判断
- 新品上市 / H2 价格切换 / 退市决策支撑

## 不要在以下情况下直接执行完整分析

- 用户只需要官网参数整理（直接给参数表即可）
- 没有可验证数据源，且用户不允许搜索或导入数据
- 用户要求伪造评论、链接、样本量、用户身份或结论
- 产品名称或研究市场存在关键歧义且无法消除

## 开始前

1. 读取 `assets/project.example.yaml`，优先寻找用户项目中的 `project.yaml`
2. 读取 `references/workflow.md`、`references/evidence_rules.md`、`references/taxonomy.md`
3. 价格分析额外读取 `references/pricing_models.md`
4. 渠道分析额外读取 `references/icp_persona_library.md`
5. 若需要生成 HTML，再读取 `templates/dashboard.html` 并使用 `scripts/render_report.py`
6. 只追问会改变研究设计的关键缺失项：目标市场、业务决策、数据源
7. 未得到补充时可以使用默认值继续，但必须明确列出假设

## 必需输入

至少确定：
- 目标产品与品类
- 目标国家、语言或市场
- 时间窗口（默认最近 90 天）
- 本次分析要支持的业务决策
- 可用数据源（本地证据库 / 联网搜索 / 用户上传）

## 可选输入

已知竞品、官方定位、重点场景、业务阶段、最低独立作者门槛、输出目录。

**已知竞品仅作为搜索起点，不能直接当作最终竞品名单。**

## 工作流（6 步框架）

详见 `references/workflow.md`。核心 6 步：

```
┌─────────────────────────────────────────────────────┐
│       Compass 竞品分析 · 单 SKILL 入口               │
│  输入：竞品名 + 目标市场 + 分析深度（基础/深度）       │
└─────────────────┬───────────────────────────────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 1: 明确目标       │
      │  业务决策 / ICP /       │
      │  时间窗 / 数据源        │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 2: 选择竞品       │
      │  寻找 → 划分 → 挑选     │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 3: 确定分析维度   │
      │  硬件 / 系统 / 场景 /   │
      │  服务 / 价格 / 渠道     │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 4: 收集竞品信息   │
      │  · evidence_db/        │
      │  · WebSearch 兜底      │
      │  · 统一 evidence.json  │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 5: 信息整理与分析 │
      │  · 功能对标             │
      │  · 价格策略             │
      │  · 用户画像与渠道       │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 6: 总结报告       │
      │  · Markdown 主报告     │
      │  · HTML 仪表盘         │
      │  · 证据库 JSON         │
      └───────────────────────┘
```

### Step 1：明确目标

1. 读取 `project.yaml` 配置
2. 与用户对齐：业务决策 / ICP / 目标市场 / 时间窗 / 数据源策略（本地库 or 联网）
3. **目标未确认不进分析**——这是质量门
4. 用户确认后进入 Step 2

### Step 2：选择竞品（寻找 → 划分 → 挑选）

- **寻找**：基于品类 + 目标市场，从本地库 + 联网搜索拉出候选竞品清单（不限数量）
- **划分**：按直接竞品 / 替代方案 / 间接竞品三类分组
- **挑选**：结合 Step 1 的业务决策，挑出 5-10 款最相关的竞品进入分析
- **已知竞品仅作为搜索起点，不能直接当作最终竞品名单**

### Step 3：确定分析维度

参考 `references/taxonomy.md` 四级分类（硬件 / 系统 / 场景 / 服务），并扩展价格 / 渠道 / 用户画像维度：
- 列出本竞品分析需要回答的决策相关问题（不超过 5 个，禁止泛泛功能清单）
- 把问题拆解为可验证的子问题（如「屏幕尺寸差异」→「display_size 对 retail 场景 ICP 的影响」）
- 形成 aspect 清单，作为 Step 4 收集信息的指引

### Step 4：收集竞品信息（RAG）

- 本地证据库 `evidence_db/` 命中 → 直接取用
- 未命中 → WebSearch 抓取（官网 / 评测 / 价目表 / 评论摘要）→ 解析 → 落库（标注 `⚠️ 待验证`）
- 每条数据写入 `evidence_schema.json`，附 URL + 抓取日期
- 价格类数据优先抓取价目表 PDF / 官方定价页

### Step 5：信息整理与分析

把 Step 4 收集的数据按三个子维度做整理与交叉分析：

#### 5.1 功能对标（feature benchmark）

调用 `scripts/gap_matrix.py`，按 `references/taxonomy.md` 四级分类生成 gap 矩阵。
- Plan：从 Step 1 大纲读取决策相关问题，列出 aspect 清单
- Research：复用 Step 4 已落库的 evidence.json，缺项追加查询
- Synthesize：按 taxonomy 生成 gap 矩阵，每条标注 gap_direction + decision_impact
- Review：自我审查——「这个功能差异是否对 ICP 决策有影响？」无影响的不进报告
- Write：输出 markdown 段落 + gap 矩阵表，至少保留 3 条 decision_impact=high 的差异化机会

#### 5.2 价格策略（pricing strategy）

调用 `scripts/pricing_calc.py`，**强制用 Python 做真实价格算术**（Function Calling），禁止只用文字描述价格。
- 解析价目表 PDF → 反推经销商折扣栈（list → distributor → reseller → end-user）
- 价格模型识别：value-based / cost-plus / tiered
- ICP 价格弹性提示：按 persona 给出「价格敏感度 vs 价值感知」矩阵
- 价格定位建议：3 段落（当前定位 / 风险 / 建议），每段必须引用 ≥2 条证据

#### 5.3 用户画像与渠道（persona & channel）

调用 `references/icp_persona_library.md`，输出 persona 标签的画像 + 渠道覆盖矩阵 + Message House 建议。
- 多视角预研究（STORM 借鉴）：ICP 买家 / 渠道商 / 竞品销售 / 行业分析师
- persona 维度聚类：每个 persona 提取 top 3 痛点 + top 3 满意点
- 渠道覆盖图：竞品 × 渠道类型（直营 / 经销 / 电商 / 集成商）
- Message House 建议：针对自身产品的差异化话术

### Step 6：总结报告

1. 把 Step 5 三个子维度输出 → `templates/report_template.md` 填充
2. 调 `scripts/render_report.py` 生成 HTML 仪表盘
3. 输出 `report.md` + `report.html` + `evidence.json` 三件套

## 输出契约（Prompt Engineering）

每个 Step 的 `expected_output` 强制：
- 矩阵 / 表格 / 段落，禁止纯 bullet list
- 未带数据源支撑的声明必须打 `⚠️ 待验证` 标记
- 必须显式引用 ICP（「对 {persona} 而言...」）
- 价格类声明需有 price_list 或 official_spec 支撑，否则打 `⚠️ 待验证`

## 引用规则

详见 `references/evidence_rules.md`。核心 5 条：
1. 每条声明需在文末附录列出证据来源（URL / 文件 / 抓取日期）
2. 未带数据源支撑的声明必须打 `⚠️ 待验证` 标记，禁止用于客户交付
3. 价格类声明需有 source_type=price_list 或 official_spec 支撑，否则打 `⚠️ 待验证`
4. 联网搜索抓取的数据需附 URL + 抓取日期
5. RAG 优先级：本地库命中 → 直接用；未命中 → WebSearch → 落库 → 打 `⚠️ 待验证`

## RAG 数据层（MCP 思想）

统一 `evidence_schema.json` 实现各 Step 间证据互通：
- `scripts/evidence_store.py` 提供 CRUD API
- 本地证据库优先
- 联网搜索兜底（标注 `⚠️ 待验证`）
- 用户可上传自己的竞品数据扩充本地库

## 演示案例

`examples/商用平板/` 提供一份脱敏的单页可视化 Demo，展示产品核心价值。实际使用时由 SKILL 自动覆盖。
