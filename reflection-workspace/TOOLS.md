# TOOLS.md - Reflection Workspace Local Notes

Skills define _how_ tools work. This file records environment-specific paths, formats, and quick references for daily use.

---

## Data Paths

| 用途 | 路径 | 格式 |
|------|------|------|
| 反思案例 | `./lessons/cases/C{YYYYMMDD}{NNN}.md` | Markdown + YAML front matter |
| 聚合模式 | `./lessons/patterns/P{NNN}_{error_type}.md` | Markdown + YAML front matter |

## Case File Front Matter Schema

```yaml
case_id: C20260328001       # 唯一 ID
trade_id: T20260328001      # 关联交易 ID
code: 600519.SH             # 股票代码（含交易所后缀）
short_name: 贵州茅台         # 股票简称
attribution: research_error  # research_error | execution_error | risk_error | market_noise
date: 2026-03-28            # 反思日期
pnl: -45000                 # 盈亏金额
pnl_pct: -0.05              # 盈亏百分比
```

## Pattern File Front Matter Schema

```yaml
pattern_id: P001_research_error  # 唯一 ID
error_type: research_error       # 一级归因类型
sub_type: 数据验证不足            # 二级子模式
case_count: 4                    # 关联案例数
cases: [C20260115001, ...]       # 关联案例 ID 列表
first_seen: 2026-01-15           # 最早案例日期
last_seen: 2026-03-28            # 最近案例日期
strength: strong                 # weak | moderate | strong
status: pending_review           # pending_review | confirmed | rejected
```

## Attribution Decision Tree

```
过程是否正确？（执行是否遵循计划）
├─ 否 → 风控规则是否被违反？
│       ├─ 是 → risk_error
│       └─ 否 → execution_error
└─ 是 → 研究论证是否正确？（核心假设是否被证伪）
        ├─ 是 → market_noise
        └─ 否 → research_error
```

每笔交易只标记一个主归因，选因果链最上游的错误。

## Pattern Strength Criteria

| 强度 | 案例数 | 条件 | 后续动作 |
|------|--------|------|---------|
| weak | 3 | 场景差异大，因果不清晰 | 记录观察 |
| moderate | 3-5 | 有明确共性特征 | 提醒关注 |
| strong | ≥5（或 <5 但因果极清晰） | 因果证据充分 | 触发 philosophy-evolve |

辅助指标：时间密度、损失规模、因果一致性。

## Philosophy Write Safety

1. 单案例 → lessons/cases only
2. 模式 ≥3 cases → lessons/patterns
3. Strong pattern → 可提议 philosophy 变更
4. 人工确认 → 写入 PHILOSOPHY.md
5. 被拒绝 → 标记 rejected，不重复提议

变更方式仅限：模块重写 / 新增独立模块。禁止碎片化追加。

## Cross-Workspace References

| 引用来源 | 路径 | 用途 |
|---------|------|------|
| 交易日志 | `../trading-workspace/trading-logs/trading_log.xlsx` | 交易事实（loss-reflect 数据包） |
| 持仓 | `../trading-workspace/holdings/holdings.xlsx` | 持仓上下文 |
| 个股逻辑卡片 | `../research-workspace/knowledge/stock-rationale-card/` | 研究基础（loss-reflect 数据包） |
| 行业逻辑卡片 | `../research-workspace/knowledge/sector-rationale-card/` | 行业逻辑 |
| 投资哲学 | `../research-workspace/PHILOSOPHY.md` | 哲学锚点 + 变更目标 |
| 核心池 | `../research-workspace/knowledge/core_stock_pool.xlsx` | 影响评估 |

---

_Add your own notes below as you learn what works._
