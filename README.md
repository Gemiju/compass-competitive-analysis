# Compass - AI 驱动的竞品分析工具

> 输入竞品名称，自动生成包含「功能对标、价格策略、渠道打法」的结构化竞品分析报告，每条结论带证据引用，杜绝 AI 瞎编。

## 项目组成

| 模块 | 路径 | 说明 |
|---|---|---|
| **Compass Skill** | `compass/` | TRAE AI Skill，核心竞品分析引擎 |
| **Web 演示应用** | `compass-app/` | Vercel 部署的网页应用，让非技术用户也能体验 |
| **案例报告** | `compass/examples/` | 脱敏竞品分析案例（单页 Demo） |

## 核心特性

- **6 步分析框架**：明确目标 → 选择竞品 → 确定分析维度 → 收集竞品信息 → 信息整理与分析 → 总结报告
- **证据驱动（RAG 架构）**：每条结论带证据引用，标注置信度和数据来源
- **三维深度分析**：功能 Gap 矩阵 + 价格策略 + 渠道与用户画像
- **结构化输出**：禁止纯文字描述，强制矩阵/表格/段落 + 引用

## 快速开始

### 方式一：查看案例报告

打开 `compass/examples/商用平板/demo.html` 查看单页可视化报告。

### 部署 Web 应用

```bash
cd compass-app
npm install
vercel dev    # 本地开发
vercel --prod # 部署上线
```

两种方式使用 API Key：
1. **前端输入**（推荐）：在网页上直接输入 DeepSeek API Key，无需配置环境变量
2. **环境变量**：在 Vercel 中设置 `DEEPSEEK_API_KEY`（[DeepSeek 开发者平台](https://platform.deepseek.com/)获取）

### 方式二：在 TRAE 中使用 Skill

将 `compass/` 文件夹导入 TRAE Skill 系统，在对话中输入：

```
分析 [竞品名称]，[目标市场]，业务决策：[决策方向]
```

## 技术架构

```
用户输入 → 6步分析框架 → 结构化报告
               │
        ┌──────┴──────┐
        │  RAG 证据层   │
        │  本地库优先    │
        │  联网搜索兜底  │
        └─────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| AI 引擎 | DeepSeek API | 大语言模型生成分析内容 |
| 证据层 | RAG 架构 | 本地证据库 + 联网搜索，每条结论可溯源 |
| Web 前端 | 原生 HTML/CSS/JS | 深色主题，无框架依赖 |
| Web 后端 | Vercel Serverless | Node.js API Routes |
| Skill 层 | TRAE Skill | SKILL.md 定义触发规则和工作流 |

## 项目结构

```
.
├── compass/                    # AI Skill（核心引擎）
│   ├── SKILL.md                # Skill 定义（触发规则 + 工作流）
│   ├── README.md               # Skill 产品介绍
│   ├── references/             # 知识库（分类规则、证据规则等）
│   ├── scripts/                # Python 工具脚本
│   ├── templates/              # 报告模板
│   ├── assets/                 # 证据库 Schema + 项目配置模板
│   └── examples/               # 案例报告
│       └── 商用平板/
│           └── demo.html       # 单页可视化 Demo
├── compass-app/                # Web 演示应用
│   ├── index.html              # 前端页面
│   ├── api/analyze.js          # 后端 API（调用 DeepSeek）
│   ├── vercel.json             # 部署配置
│   └── package.json
└── README.md                   # 本文件
```

## 案例报告说明

`compass/examples/商用平板/demo.html` 是一份脱敏后的单页可视化竞品分析报告，涵盖：

- 产品概述与核心差异化
- 关键规格对比
- 价格定位
- 竞争差距速览
- 核心场景覆盖
- Message House 信息框架

适合在作品集中以截图或网页形式展示。

## License

MIT
