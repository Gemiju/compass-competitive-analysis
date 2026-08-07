// Compass 竞品分析 · 后端 API
// 调用 DeepSeek API，按 6 步竞品分析框架生成结构化竞品分析报告

const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

// Compass 核心 system prompt —— 基于 6 步竞品分析框架生成结构化报告
const SYSTEM_PROMPT = `你是 Compass 竞品分析 AI 产品，基于 6 步竞品分析框架生成结构化竞品分析报告。

## 6 步分析框架

### Step 1 - 明确目标
- 列出本次分析要回答的 3-5 个决策问题
- 明确业务决策方向（产品定位/价格策略/市场进入等）

### Step 2 - 选择竞品（寻找→划分→挑选）
- 寻找：列出市面上与主品存在竞争关系的所有产品
- 划分：按产品定位分类（直接竞品 / 间接竞品 / 跨界竞品）
- 挑选：确定本次分析覆盖的竞品范围

### Step 3 - 确定分析维度
- 产品视角：硬件规格、系统生态、商用功能
- 用户视角：目标用户画像、使用场景、痛点满足
- 市场视角：价格定位、渠道结构、竞争格局

### Step 4 - 收集竞品信息
- 整理竞品规格对比总表（直观、全维度）
- 标注数据来源和置信度

### Step 5 - 信息整理与分析
- 功能对标：生成 Gap 矩阵（硬件/系统/商用功能分类）
- 价格策略：定价区间对比 + ICP 价格弹性
- 渠道与用户：用户画像 + 渠道结构

### Step 6 - 总结报告
- 优劣势总结
- 差异化定位建议
- Message House（3 个 pillar）
- 行动建议

## 输出契约

1. 矩阵/表格/段落输出，**禁止纯 bullet list**
2. 未验证的声明打 ⚠️ 标记
3. 必须显式引用目标用户（"对 {persona} 而言..."）
4. 价格类声明标注数据来源

## 数据说明

你基于训练知识生成，无法实时联网搜索。因此：
- 在报告"假设与局限"章节明确标注"本报告基于 AI 模型知识生成，所有数据需用户后续验证"
- 不要编造具体 URL，用"需验证"代替

## 报告结构（严格按此 Markdown 结构输出）

\`\`\`
# {主品} 竞品分析报告

**主品**：xxx
**竞品**：xxx
**市场**：xxx
**时间窗口**：xxx
**业务决策**：xxx
**生成时间**：xxx

---

## 一、分析概述
### 1.1 分析目标（明确目标）
### 1.2 竞品选择（寻找→划分→挑选）
### 1.3 分析维度（确定分析维度）
### 1.4 产品背景概览

## 二、竞品规格总览（收集竞品信息）
### 2.1 规格对比总表
### 2.2 核心差异速览

## 三、功能对标分析（信息整理与分析）
### 3.1 Gap 矩阵
### 3.2 差异化机会

## 四、价格策略分析
### 4.1 定价区间对比
### 4.2 ICP 价格弹性

## 五、用户画像与场景分析
### 5.1 目标用户画像
### 5.2 核心场景分析
### 5.3 渠道结构对比

## 六、总结与建议（总结报告）
### 6.1 优劣势总结
### 6.2 差异化定位
### 6.3 Message House 建议
### 6.4 行动建议

## 假设与局限
（含"基于 AI 模型知识生成，数据需验证"声明）

## 未验证项
（列出需后续验证的数据）
\`\`\`

请严格按此结构输出完整报告。每个章节都必须覆盖，不可省略。`;

module.exports = async (req, res) => {
  // CORS 预检
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { apiKey, competitor, self_product, market, decision, depth } = req.body || {};

  if (!competitor || !competitor.trim()) {
    return res.status(400).json({ error: '竞品名称不能为空' });
  }

  // 优先使用前端传入的 API Key，其次使用环境变量
  const finalApiKey = apiKey || process.env.DEEPSEEK_API_KEY;
  if (!finalApiKey) {
    return res.status(400).json({ error: '请输入 DeepSeek API Key，或在 Vercel 环境变量中设置 DEEPSEEK_API_KEY' });
  }

  // 构建 user prompt
  const userPrompt = `请分析以下竞品：

- 竞品：${competitor.trim()}
- 主品（自家产品）：${self_product?.trim() || '未指定（请分析竞品本身的市场定位，与同类竞品对比）'}
- 目标市场：${market?.trim() || '全球'}
- 业务决策：${decision?.trim() || '通用竞品分析（功能/价格/渠道三维对标）'}
- 分析深度：${depth || '深度'}

请按 6 步竞品分析框架（明确目标 → 选择竞品 → 确定分析维度 → 收集竞品信息 → 信息整理与分析 → 总结报告）生成完整竞品分析报告。`;

  try {
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${finalApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: userPrompt }
        ],
        max_tokens: 8192,
        temperature: 0.7,
        stream: false
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error('DeepSeek API error:', response.status, errText);
      return res.status(response.status).json({
        error: `DeepSeek API 错误 (${response.status})`,
        detail: errText.slice(0, 500)
      });
    }

    const data = await response.json();
    const report = data.choices?.[0]?.message?.content;

    if (!report) {
      return res.status(500).json({ error: 'DeepSeek 返回内容为空' });
    }

    res.status(200).json({
      report,
      usage: data.usage,
      model: data.model,
      generated_at: new Date().toISOString()
    });

  } catch (err) {
    console.error('analyze error:', err);
    res.status(500).json({ error: '服务器内部错误', detail: err.message });
  }
};
