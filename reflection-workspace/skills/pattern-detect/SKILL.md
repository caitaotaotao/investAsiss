---
name: pattern-detect
description: 错误模式识别。当同类亏损案例累积 ≥3 次、用户说"检查错误模式"、"有什么反复犯的错"时触发。
---

# Pattern Detect

对 `/app/custom/reflection-workspace/lessons/cases/` 中的反思案例进行聚合分析，识别重复出现的错误模式，输出模式报告。借鉴 Alpha Journal 的复合事后分析（Compound Post-Mortem）思想——从模式而非个案中提取洞察。

## 核心约束

- 模式必须基于 **≥ 3 个独立案例**，不可从 1-2 个案例中强行归纳
- 聚类必须基于**具体共性特征**，不可仅按 attribution 大类笼统合并
- 模式报告写入 `/app/custom/reflection-workspace/lessons/patterns/`，**不可直接修改 PHILOSOPHY.md**

---

## 触发场景

| 类型 | 条件 |
|------|------|
| **自动提示** | loss-reflect 写入新 case 后，同类 attribution 累计 ≥ 3 → 提示用户运行 |
| **手动触发** | 用户说"检查错误模式"、"有什么反复犯的错"、"模式分析" |
| **定期检查** | 月度/季度复盘时主动运行 |

---

## 执行流程

### Step 1: 读取全部案例

读取 `/app/custom/reflection-workspace/lessons/cases/` 下所有 `.md` 文件，解析 front matter 中的结构化字段：
- case_id, trade_id, code, short_name, attribution, date, pnl, pnl_pct

### Step 2: 一级聚类（按 attribution 类型）

将案例按四种归因类型分组：

| 归因类型 | 案例数 |
|---------|--------|
| research_error | n |
| execution_error | n |
| risk_error | n |
| market_noise | n |

`market_noise` 类不进入模式检测（噪声无模式可言），但若数量异常多（>50% 总案例），需提醒可能存在归因偏宽松的问题。

### Step 3: 二级聚类（按具体特征细分）

在每个 attribution 类型内部，基于案例正文的"归因依据"和"教训"进行语义聚类，识别共性子模式。

**聚类维度**：

| 归因类型 | 典型子模式 |
|---------|-----------|
| research_error | 数据验证不足、渗透率/增速高估、竞争格局误判、周期阶段误读 |
| execution_error | 追涨/追跌、偏离计划仓位、建仓时机不当、情绪化加仓 |
| risk_error | 止损未设定、止损未执行、仓位超限、亏损加仓 |

每个子模式需有明确的**共性特征描述**，不可仅标注类型标签。

### Step 4: 模式强度评估

对每个检测到的子模式（案例数 ≥ 3），评估其强度：

| 强度 | 条件 | 后续动作 |
|------|------|---------|
| **weak** | 3 次，但案例场景差异大，因果链不清晰 | 记录观察，暂不行动 |
| **moderate** | 3-5 次，有明确共性特征 | 记录 + 在对话中提醒用户关注 |
| **strong** | ≥ 5 次，或因果证据充分（虽 < 5 次但因果链极清晰） | 记录 + 触发 philosophy-evolve 建议 |

**强度判定辅助指标**：
- 时间密度：短期内集中出现（如 1 个月内 3 次）比分散出现更值得警惕
- 损失规模：涉及的总亏损金额/比例
- 因果一致性：各案例的归因依据是否指向同一根因

### Step 5: 写入模式文件

将识别出的模式写入 `/app/custom/reflection-workspace/lessons/patterns/{pattern_id}.md`。

**Pattern ID 格式**：`P{NNN}_{error_type}`，如 `P001_research_error`

若已存在相同子模式的 pattern 文件，则**更新**（追加新 case、重新评估强度），不另建新文件。

**文件模板**：

```markdown
---
pattern_id: P001_research_error
error_type: research_error
sub_type: 数据验证不足
case_count: 4
cases: [C20260115001, C20260203002, C20260228001, C20260328001]
first_seen: 2026-01-15
last_seen: 2026-03-28
strength: strong
status: pending_review
---

# 模式：周期拐点判断依赖单一数据源

## 共性特征
- 均为基于"行业周期拐点"假设的建仓
- 核心数据来源为单一券商研报或单一指标
- 未做经营数据（订单、库存、产能利用率）交叉验证

## 案例聚合

| Case ID | 标的 | 日期 | 亏损% | 核心失误 |
|---------|------|------|-------|---------|
| C20260115001 | XX半导体（688XXX.SH） | 2026-01-15 | -8.2% | 产能利用率单源 |
| C20260203002 | XX新能源（300XXX.SZ） | 2026-02-03 | -6.1% | 渗透率数据过时 |
| C20260228001 | XX材料（002XXX.SZ） | 2026-02-28 | -4.5% | 库存周期忽略 |
| C20260328001 | 贵州茅台（600519.SH） | 2026-03-28 | -5.0% | 产能利用率单源 |

**累计亏损**：-{总金额} 元

## 根因分析

PHILOSOPHY §3.1 已有"多重交叉验证"原则，但缺乏对"周期拐点假设"
场景的具体验证标准。现有原则为方向性指导，未规定最低数据源数量
和必须涵盖的验证维度。

## 建议规则

涉及周期拐点判断的建仓决策，必须有 ≥3 个独立维度的数据交叉确认：
（1）行业官方/协会数据，（2）上市公司经营数据，（3）产业链上下游验证。

## Philosophy 变更建议

**目标模块**：PHILOSOPHY.md §3.1 数据与基本面趋势验证原则
**变更类型**：重写"3. 多重交叉验证"小节
**变更草案**：{具体的重写内容}
**状态**：pending_review
```

### Step 6: 对话输出

```
## 模式识别报告（{YYYY-MM-DD}）

### 检测到的模式

| Pattern ID | 错误类型 | 子模式 | 案例数 | 强度 | 累计亏损 |
|------------|---------|--------|--------|------|---------|
| P001 | research_error | 数据验证不足 | 4 | strong | -XX 元 |
| P002 | execution_error | 追涨建仓 | 3 | moderate | -XX 元 |

### 需要关注
- **P001**（strong）：建议运行 philosophy-evolve 审视是否需要更新投资哲学
- **P002**（moderate）：暂不建议更新哲学，但需在后续交易中警惕

### 归因分布
research_error: X 次 | execution_error: X 次 | risk_error: X 次 | market_noise: X 次

### market_noise 占比检查
{正常 / 异常（>50%，可能存在归因偏宽松）}
```

---

## 与其他技能的协同

- **loss-reflect** → 产出 case 文件，是本技能的输入源
- **philosophy-evolve** → strong 模式触发哲学演进建议
- **trade-review** → 复盘报告中的行为模式可引用本技能检测结果
