# Compass 竞品分析

> 一款基于 **TRAE Skill** 体系构建的通用竞品分析 **AI Product**。
> 采用 **6 步分析框架**（明确目标 → 选择竞品 → 确定维度 → 收集信息 → 整理分析 → 总结报告）。
> 采用 **RAG** 架构（本地证据库优先 + 联网搜索兜底），杜绝 **LLM** 编造数据。
> 任意品类、任意市场均可生成结构化报告。

---

## 为什么是「产品」而不是「SKILL」

单个 SKILL 只是一个工具脚本；而 **AI Product** = 明确的用户 + 固定的场景 + 标准化的输入输出 + 可衡量的业务价值。Compass 体现的是「定义问题 - 拆解需求 - 用 AI 落地 - 拿到业务结果」的完整能力，层级从「会用工具」升级为「能做 AI 产品落地」。

---

## 核心价值（降本增效）

| 指标 | 人工 | Compass | 提升 |
|---|---|---|---|
| 单份报告产出时间 | 8 小时 | 40 分钟 | **+1100%** |
| 分析维度覆盖率 | 60% | 100% | +67% |
| 数据可追溯性 | 无 | 每条声明带 evidence_id | 数据驱动 |

---

## 产品架构

```
┌─────────────────────────────────────────────────────┐
│       Compass 竞品分析 · 单 SKILL 入口               │
│  输入：竞品名 + 目标市场 + 分析深度（基础/深度）       │
│  通用：任意品类任意市场均可生成；品类接入本地库        │
└─────────────────┬───────────────────────────────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 1: 明确目标      │  ← COT 思想
      │  输出 ICP/竞品清单/    │
      │  决策问题/数据源策略   │
      │  用户确认后继续        │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 2: 选择竞品      │
      │  寻找 → 划分 → 挑选    │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 3: 确定分析维度  │
      │  产品/用户/市场三视角  │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 4: 收集竞品信息  │
      │  规格对比总表 + 来源   │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 5: 信息整理与分析│
      │  功能对标 + 价格策略   │
      │  + 渠道与用户画像      │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  Step 6: 总结报告      │
      │  优劣势 + 定位 + 行动  │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  RAG 数据层            │  ← MCP 思想：统一 evidence schema
      │  · 本地 evidence_db/   │     实现步间证据互通
      │  · WebSearch 兜底      │
      │  · 统一 evidence.json  │
      └───────────┬───────────┘
                  ▼
      ┌───────────────────────┐
      │  结构化竞品分析报告    │
      │  · Markdown 主报告     │
      │  · HTML 仪表盘         │
      │  · 证据库 JSON         │
      └───────────────────────┘
```

### 单 SKILL 6 步框架设计

Compass 采用 **6 步分析框架**：一个入口，6 步（明确目标 → 选择竞品 → 确定维度 → 收集信息 → 整理分析 → 总结报告）内部串联，统一 evidence schema 实现步间数据互通，降低复杂度同时保留步化质量门。

---

## 技术栈与 AI 能力落地

| 技术 | 在 Compass 中的落地 | 文件位置 |
|---|---|---|
| **LLM** | 整个 SKILL 基于 TRAE LLM 运行，6 步皆由 LLM 驱动 | `SKILL.md` |
| **RAG** | 本地证据库优先 + 联网搜索兜底，解决 LLM 编造数据 | `references/evidence_rules.md` / `scripts/evidence_store.py` |
| **Agent** | 6 步 Agent，每步 Plan→Research→Synthesize→Review→Write | `references/workflow.md` |
| **Agent Workflow** | 6 步端到端 Workflow | `SKILL.md` / `references/workflow.md` |
| **Function Calling** | SKILL 调用 `scripts/*.py` 做 PDF 解析、价格算术 | `scripts/pricing_calc.py` |
| **Prompt Engineering** | expected_output 契约 + 强制矩阵输出 + 引用规则 + ICP 段落 | `SKILL.md` / `templates/report_template.md` |
| **MCP（Model Context Protocol）** | 借鉴 MCP 思想，统一 `evidence_schema.json` 实现步间证据互通 | `assets/evidence_db/evidence_schema.json` |
| **COT（Chain of Thought）** | Step 1 大纲质量门 + 每步 Review 自我审查 | `references/workflow.md` |
| **数据驱动 / Data-driven** | 每条声明必带 evidence_id 引用 + ⚠️ 待验证 标记 | `references/evidence_rules.md` |
| **降本增效** | 8h→40min, 维度 60%→100% | 本 README |
| **AI Product / AI 落地** | 整个 Compass 通用竞品分析品类落地 | 本 README / `examples/` |

---

## 目录结构

```
compass/
├── SKILL.md                          # 单 SKILL 入口，定义何时使用 + 6 步工作流
├── assets/
│   ├── evidence_db/
│   │   └── evidence_schema.json      # 统一证据 schema（MCP 思想，步间互通）
│   └── project.example.yaml          # 项目配置模板
├── references/                       # LLM 读取的规则库
│   ├── workflow.md                   # 6 步 Agent Workflow 详解
│   ├── evidence_rules.md             # 引用规则（RAG 优先级、⚠️ 待验证 标记）
│   ├── taxonomy.md                   # 功能四级分类（硬件/系统/场景/服务）
│   ├── pricing_models.md             # 定价模型识别规则
│   └── icp_persona_library.md        # 7 persona 多视角研究库
├── scripts/                          # Function Calling 调用的 Python 脚本
│   ├── evidence_store.py             # RAG 数据层 CRUD
│   ├── gap_matrix.py                 # 功能 gap 矩阵生成
│   ├── pricing_calc.py               # 真实价格算术（折扣栈反推）
│   └── render_report.py              # Markdown + JSON → HTML 仪表盘
├── templates/
│   ├── report_template.md            # 主报告骨架（Prompt Engineering 契约）
│   └── dashboard.html                # HTML 仪表盘模板
└── examples/
    └── 商用平板/                     # 脱敏案例：单页可视化 Demo
        └── demo.html                 # 单页可视化竞品分析报告
```

---

## 快速开始

### 1. 通用竞品分析（任意品类）

在 TRAE 中触发 Compass SKILL，输入：

```
竞品：Notion
市场：北美 SaaS
业务决策：是否进入企业级协作赛道
数据源：联网搜索
```

SKILL 会走 6 步框架，本地库未命中时全自动联网搜索补全并标 `⚠️ 待验证`。

### 2. 数据源策略（RAG 核心）

| 场景 | 数据源 | 标记 |
|---|---|---|
| 品类 + 本地库命中 | `evidence_db/` | 无 |
| 任意品类 + 本地库未命中 | WebSearch 兜底 | `⚠️ 待验证` |
| 用户上传数据 | 用户文件 | `verified_by=user_upload` |

---

## 演示案例

`examples/商用平板/demo.html` 是一份脱敏后的单页可视化竞品分析报告，涵盖产品概述、核心差异化、规格对比、价格定位、场景覆盖与 Message House 信息框架。适合在作品集中以截图或网页形式展示。

---

## 输出契约（Prompt Engineering）

每步的 `expected_output` 强制：

- 矩阵 / 表格 / 段落，**禁止纯 bullet list**
- 每条声明带 evidence_id 引用
- 未带引用的声明必须打 `⚠️ 待验证` 标记，禁止用于客户交付
- 必须显式引用 ICP（「对 {persona} 而言...」）
- 价格类声明必须有 `price_list` 或 `official_spec` 支撑

---

## 路线图（v2）

- **Embedding + 向量数据库**：evidence_db 接入向量检索，支持语义匹配命中判断（替代当前关键词匹配）
- **LLMOps**：evidence_db 版本化 + 报告可复现可审计
- **PPT 导出**：报告 → PPT 一键导出，贴合真实汇报场景

---

## License

MIT
