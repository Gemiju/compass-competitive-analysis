# 功能分类法（Taxonomy）

> Step 5 功能对标使用的四级分类法。所有功能 aspect 必须归入其中一级。
> 这是 gap 矩阵的行索引，确保不同竞品的功能差异可比。

## 一级：硬件（Hardware）

物理规格与外设。

| aspect | 单位 | 决策影响度参考 |
|---|---|---|
| display_size | inch | medium（同尺寸非差异） |
| display_type | IPS/OLED/TN | high（户外场景影响大） |
| resolution | px | low |
| touch | capacitive/resistive/none | high（零售场景） |
| cpu | model | medium |
| ram | GB | medium |
| storage | GB | low |
| battery | mAh | high（移动场景） |
| connectivity | wifi/bt/4g/5g | high |
| ports | usb-c/rj45/serial | high（外设集成） |
| printer | built-in/none | high（小票场景） |
| scanner | built-in/none | high（条码场景） |
| nfc | yes/no | medium |
| camera | mp | low |
| durability | ip-rating | high（工业场景） |
| dimensions | mm | low |
| weight | g | medium |

## 二级：系统（System）

操作系统与软件平台。

| aspect | 决策影响度参考 |
|---|---|
| os | high（Android vs Windows vs Linux 决定生态） |
| os_version | high（生命周期影响） |
| mdm_support | high（企业部署必需） |
| kiosk_mode | high（零售必需） |
| app_store | medium |
| sdk_openness | high（二次开发） |
| update_policy | high（安全合规） |
| security_cert | high（PCI DSS / GDPR） |
| multi_user | medium |
| remote_management | high（连锁运维） |

## 三级：场景（Scenario）

行业场景适配。**这是差异化的核心**——同样是 10.1 寸平板，零售场景和物流场景的需求完全不同。

| aspect | 决策影响度参考 |
|---|---|
| scenario_retail | high（POS / 自助结账 / 货架管理） |
| scenario_hospitality | high（点餐 / 客房服务） |
| scenario_logistics | high（仓储 / 配送） |
| scenario_healthcare | high（病历 / 床旁护理） |
| scenario_industrial | high（产线 / 巡检） |
| scenario_education | medium |
| scenario_outdoor | medium |
| scenario_qsr | high（快餐连锁） |
| scenario_parking | medium |
| scenario_ticketing | medium |

## 四级：服务（Service）

售后服务与商业条款。

| aspect | 决策影响度参考 |
|---|---|
| warranty | high（B2B 必看） |
| rma_policy | high |
| tech_support | high（连锁运维） |
| onsite_service | high |
| training | medium |
| spare_parts | high（生命周期） |
| sla | high |
| custom_firmware | medium |
| co_branding | medium |
| eol_notice_period | high（退市管理） |

---

## aspect 命名约定

- 全小写 + 下划线：`display_size` / `scenario_retail`
- 多值用 `/` 分隔：`connectivity: wifi/bt/4g`
- 布尔用 `yes/no`：`nfc: yes`
- 缺失值用 `null`，不用 `N/A` 或 `未知`

## 决策影响度判定原则

| impact | 判定 |
|---|---|
| high | 直接影响 ICP 购买决策（进报告主体） |
| medium | 间接影响（进附录或脚注） |
| low | 无影响（不进报告） |

**判断标准**：问「如果删除这条差异，ICP 的购买决策会改变吗？」
- 会 → high
- 不会但会影响体验 → medium
- 完全无关 → low

## 自定义 aspect

若品类需要新 aspect（如医疗场景的 `fda_cert`），在 `project.yaml` 的 `custom_taxonomy` 字段补充，SKILL 会自动合并。

## 反模式（禁止）

- 用「品牌力」「用户口碑」等无法验证的模糊维度
- 用「性价比」作为 aspect（性价比是分析结论，不是功能维度）
- 把 VOC 评论直接当 aspect（用户反馈走 Step 5，不进 taxonomy）
