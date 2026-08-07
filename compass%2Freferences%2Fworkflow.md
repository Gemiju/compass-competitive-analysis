# Compass 竞品分析 · 工作流（Workflow）

> 借鉴 GPT-Researcher（Plan→Research→Synthesize→Write）+ Stanford STORM（多视角预研究 + 大纲质量门）+ Microsoft AutoGen（代码执行算术）。
> 单 SKILL 内 6 步框架：Step 1 明确目标 → Step 2 选择竞品 → Step 3 确定维度 → Step 4 收集信息 → Step 5 整理分析 → Step 6 总结报告。

## Step 1：明确目标（COT 思想）

**目标**：在分析开始前对齐业务决策 / ICP / 时间窗 / 数据源策略。这是质量门，未确认不进后续步骤。

**输入**：`project.yaml` 配置 + 用户输入（竞品名 / 目标市场 / 分析深度）

**步骤**：
1. 读取 `project.yaml`，解析：品类 / 目标市场 / 时间窗 / 业务决策 / 数据源
2. 检索本地证据库 `evidence_db/`，判断「竞品是否命中本地库」
3. 输出大纲（Markdown）：

```markdown
## 分析大纲

### 1. ICP（理想客户画像）
- 行业：[从 project.yaml 或推断]
- 角色：[procurement_officer / it_admin / ...]
- 场景：零售 / 餐饮 / 物流 / ...
- 地理：[目标市场]

### 2. 竞品清单（候选 + 命中状态）
| 竞品 | 本地库命中 | 联网需补 | 优先级 |
|---|---|---|---|
| 竞品 A | ✅ (cpad_competitive.xlsx) | - | P0 |
| 竞品 B | ❌ | 官网规格 + 评论 | P1 |

### 3. 决策相关问题（不超过 5 个，禁止泛泛功能清单）
1. 对 [persona] 而言，自身产品 vs 主要竞品的核心差异化机会在哪？
2. 主要竞品经销商折扣栈如何？自身产品应如何定位？
3. 目标市场渠道结构如何？自身产品该选哪些渠道商？

### 4. 数据源策略
- Step 5.1 功能对标：本地库为主，缺项 WebSearch 补
- Step 5.2 价格策略：竞品价目表 PDF / 官方定价页，竞品价格 WebSearch
- Step 5.3 用户画像与渠道：本地库 + WebSearch（Reddit/YouTube/Amazon）

### 5. 假设（用户未补充时显式列出）
- 时间窗默认最近 90 天
- 目标市场默认主要语言评论
- ...
```

4. 等待用户确认。用户可调整 ICP / 竞品清单 / 决策问题。
5. 确认后进入 Step 2。

**禁止**：跳过 Step 1 直接分析（会导致泛泛画像）。

---

## Step 2：选择竞品（寻找 → 划分 → 挑选）

**目标**：从候选池中筛出与本竞品分析决策最相关的 5-10 款竞品。已知竞品仅作为搜索起点，不能直接当作最终竞品名单。

### 2.1 寻找
- 基于品类 + 目标市场，从本地证据库 + 联网搜索拉出候选竞品清单（不限数量）
- 来源：行业报告 / 招标网站 / 电商平台品类页 / 行业媒体 / 搜索引擎「top N + 品类」查询

### 2.2 划分
按以下三类对候选竞品分组：
- **直接竞品**：同品类、同价位段、同目标 ICP
- **替代方案**：不同品类但解决同一场景需求
- **间接竞品**：上下游延伸或可能进入的玩家

### 2.3 挑选
- 结合 Step 1 的业务决策，挑出 5-10 款最相关的竞品进入后续分析
- 至少覆盖 1 款替代方案，避免遗漏跨界威胁
- 输出最终竞品清单表（竞品 / 类型 / 优先级 / 命中状态）

---

## Step 3：确定分析维度

**目标**：把 Step 1 的决策问题拆解为可验证的 aspect 清单，作为 Step 4 收集信息的指引。

**步骤**：
1. 参考 `references/taxonomy.md` 四级分类（硬件 / 系统 / 场景 / 服务），并扩展价格 / 渠道 / 用户画像维度
2. 把 Step 1 的决策相关问题拆解为可验证的子问题
   - 示例：「屏幕尺寸差异」→「display_size 对 retail 场景 ICP 的影响」
3. 形成 aspect 清单，覆盖：
   - 硬件规格类（CPU / 屏幕 / 接口 / 续航 / 防护等级 ...）
   - 系统与软件类（OS / SDK / MDM 兼容 / 预装应用 ...）
   - 场景适配类（零售 / 餐饮 / 物流 / 工业 ...）
   - 服务类（保修 / RMA / 技术支持 / 培训 ...）
   - 价格类（list / 折扣栈 / 价格模型 ...）
   - 渠道类（直营 / 经销 / 电商 / 集成商 ...）
4. 输出 aspect 清单作为 Step 4 的查询脚本入参

---

## Step 4：收集竞品信息（RAG）

**目标**：按 Step 3 的 aspect 清单收集数据，落库到统一 `evidence_schema.json`。

### 4.1 Plan
- 读取 Step 3 输出的 aspect 清单
- 为每个 aspect × 竞品组合规划查询路径（本地库优先，联网兜底）

### 4.2 Research（RAG）
- 调 `scripts/evidence_store.py query --competitor <竞品> --aspect <aspect>`
- 本地库命中 → 直接取用
- 未命中 → WebSearch 搜索「<竞品> <aspect> specifications」→ 解析 → 落库（标注 `⚠️ 待验证`）
- 价格类数据优先抓取价目表 PDF / 官方定价页：调 `pricing_calc.py parse-pdf --file <pdf>`
- 每条数据写入 `evidence_schema.json`，附 URL + 抓取日期

### 4.3 Review
- 检查数据覆盖度：每个 P0 竞品的关键 aspect 必须有数据
- 缺失项标注「数据缺失，建议人工补充」，不编造

---

## Step 5：信息整理与分析

**目标**：把 Step 4 收集的数据按三个子维度做整理与交叉分析。**禁止只用文字描述价格——所有数字必须由 Python 计算产出**。

### 5.1 功能对标（feature benchmark）

**GPT-Researcher 借鉴**：Plan → Research → Synthesize → Review → Write

#### 5.1.1 Plan
- 从 Step 1 大纲读取功能相关决策问题
- 列出需要查询的 aspect 清单（参考 `taxonomy.md`）

#### 5.1.2 Research
- 复用 Step 4 已落库的 evidence.json
- 缺项追加查询

#### 5.1.3 Synthesize
- 调 `scripts/gap_matrix.py --input evidence.json --output gap_matrix.json`
- 按 taxonomy 四级分类生成 gap 矩阵
- 每条 gap 标注：gap_direction（领先 / 落后 / 持平）+ decision_impact（high / medium / low）

#### 5.1.4 Review（COT 自我审查）
- 对每条 gap 问：「如果删除这条差异，ICP 的购买决策会改变吗？」
- decision_impact=low 的不进报告主体（进附录或丢弃）
- 至少保留 3 条 decision_impact=high 的差异化机会

#### 5.1.5 Write
- 输出 markdown 段落 + gap 矩阵表
- 末尾输出「差异化机会」段落（≥3 条，每条引用 ≥2 条证据）

**expected_output 契约**：
- 矩阵 + 段落，禁止纯 bullet list
- 必须显式引用 ICP（「对 {persona} 而言...」）
- 未带数据源支撑的声明打 `⚠️ 待验证`

---

### 5.2 价格策略（pricing strategy）

**目标**：反推竞品折扣栈，识别定价模型，给出价格定位建议。**强制用 Python 做真实算术**（Function Calling，AutoGen 借鉴）。

#### 5.2.1 Plan
- 读取 Step 1 大纲中价格相关决策问题
- 列出需要的数据：list_price / distributor_price / reseller_price / end_user_price / 折扣栈

#### 5.2.2 Research
- 本地库：调 `evidence_store.py query --competitor <竞品> --aspect "*price*"`
- 联网：WebSearch 搜索竞品官网定价 / Amazon list price
- 价目表 PDF：调 `pricing_calc.py parse-pdf --file <pdf>`

#### 5.2.3 Synthesize（AutoGen 代码执行借鉴）
- 调 `pricing_calc.py compute --input evidence.json --output pricing_analysis.json`
- 计算项：
  - price_per_unit（按 ICP 价值度量，如「每台 / 每寸屏 / 每 SKU」）
  - 折扣栈反推：list → distributor → reseller → end-user 的每一层折扣 %
  - 价格模型识别：value-based / cost-plus / tiered（基于价目表结构判断）

#### 5.2.4 Review
- 检查数据源支撑：价格类声明需有 price_list / official_spec 支撑，否则打 `⚠️ 待验证`
- 检查一致性：discount_stack 各层乘积应等于 end_user_price / list_price

#### 5.2.5 Write
- 输出 markdown：
  - price-per-unit 对比表
  - 折扣栈反推表（瀑布图数据）
  - 价格模型识别段落
  - ICP 价格弹性矩阵（persona × 价格敏感度 × 价值感知）
  - 价格定位建议 3 段落（当前定位 / 风险 / 建议），每段引用 ≥2 条证据

---

### 5.3 用户画像与渠道（persona & channel）

**目标**：多视角预研究 + persona 维度聚类，输出 persona 标签的画像 + 渠道覆盖矩阵 + Message House 建议。**禁止泛泛画像**。

#### 5.3.1 Plan
- 读取 Step 1 大纲中渠道相关决策问题
- 列出多视角预研究问题（STORM 借鉴）：
  - ICP 买家视角：「我在哪个渠道买？为什么选这个不选那个？」
  - 渠道商视角：「我为什么推这个品牌？margin 多少？」
  - 竞品销售视角：「他们主推哪个 SKU？话术是什么？」
  - 行业分析师视角：「这个品类的渠道趋势？」

#### 5.3.2 Research（RAG + 多源三角化）
- 本地库：调 `evidence_store.py query --competitor <竞品> --aspect "*channel*"`
- 联网三角化：
  - Reddit：相关 sub（ICP 痛点）
  - YouTube：评测标题 + transcript（reviewer 判决）
  - Amazon：评论 + 评分（end-user 体验）
- 每条数据落库时打 persona 标签（基于评论上下文推断）

#### 5.3.3 Synthesize
- persona 维度聚类：每个 persona 提取 top 3 痛点 + top 3 满意点
- 渠道覆盖图：竞品 × 渠道类型（直营 / 经销 / 电商 / 集成商）
- 参考 `references/icp_persona_library.md` 完善画像

#### 5.3.4 Review
- 检查 persona 多样性：至少覆盖 3 个 persona
- 过滤泛泛画像（如「用户喜欢」无具体引用）

#### 5.3.5 Write
- 输出 markdown：
  - 多视角预研究问题 + 回答（每个 persona 一段）
  - persona 画像侧边栏：每个竞品 3-5 条 persona 标签要点
  - 渠道覆盖矩阵
  - Message House 建议（针对自身产品的差异化话术）

---

## Step 6：总结报告

**目标**：把 Step 5 三个子维度输出合并为统一报告 + HTML 仪表盘。

**步骤**：
1. 读取 Step 5 三个子维度的 JSON 输出
2. 用 `templates/report_template.md` 渲染 `report.md`：
   - 执行摘要（1 段，含 3 维度关键指标）
   - Step 5.1 功能对标章节
   - Step 5.2 价格策略章节
   - Step 5.3 用户画像与渠道章节
   - ICP 与决策建议
   - 证据附录（所有数据源 URL + 抓取日期 + 文件路径）
3. 调 `render_report.py --input report.md --evidence evidence.json --output report.html`
4. 输出三件套：`report.md` + `report.html` + `evidence.json`

---

## 异常处理

| 异常 | 处理 |
|---|---|
| 本地库 + 联网都无数据 | 该维度标注「数据缺失，建议人工补充」，不编造 |
| 用户拒绝 LLM 推断 | 该项留空，不强行填 |
| 价目表 PDF 解析失败 | 提示用户「PDF 可能是扫描件，需 OCR」并降级到 manual extract |
| WebSearch 不可用 | 通用性路径降级，仅支持本地库命中场景，报告标注「联网数据未获取」 |
| evidence_id 冲突 | 重新分配，保留最早的一条 |

---

## 输出目录约定

默认输出到 `examples/<竞品 vs 自身>_<YYYYQ#>/`：
- `examples/cpad/report.md`
- `examples/cpad/report.html`
- `examples/cpad/evidence.json`

用户可在 `project.yaml` 的 `output_dir` 字段自定义。
