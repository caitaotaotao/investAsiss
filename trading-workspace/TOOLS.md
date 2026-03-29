# TOOLS.md - Trading Workspace Local Notes

Skills define _how_ tools work. This file records environment-specific paths, formats, and quick references for daily use.

---

## Data Paths

| 用途 | 路径 | 格式 |
|------|------|------|
| 当前持仓 | `./holdings/holdings.xlsx` | Excel |
| 交易日志 | `./trading-logs/trading_log.xlsx` | Excel |

## Holdings Excel Schema

Sheet: `holdings`

| Column | Type | Description |
|--------|------|-------------|
| date | string | 快照日期 `YYYY-MM-DD` |
| code | string | `600519.SH` |
| short_name | string | `贵州茅台` |
| quantity | int | 持有数量（股） |
| market_value | float | 持有市值（元），2 位小数 |
| weight | float | 持有权重，4 位小数 |
| total_account_value | float | 账户总价值（元） |

约束：同一 date 同一 code 仅一行；weight 之和 ≤ 1.0（差额 = 现金）。

## Trading Log Excel Schema

Sheet: `log`

| Column | Type | 写入时机 | Description |
|--------|------|---------|-------------|
| trade_id | string | 开仓 | `T{YYYYMMDD}{序号}`，如 `T20260328001` |
| open_date | string | 开仓 | `YYYY-MM-DD` |
| code | string | 开仓 | `600519.SH` |
| short_name | string | 开仓 | `贵州茅台` |
| direction | string | 开仓 | `买入` / `卖出` |
| open_price | float | 开仓 | 开仓价格 |
| quantity | int | 开仓 | 交易数量（股） |
| trade_amount | float | 开仓 | = open_price × quantity |
| trade_rationale | string | 开仓 | 交易逻辑（1-2 句） |
| stop_loss | float | 开仓 | 止损价（可空） |
| target_price | float | 开仓 | 目标价（可空） |
| status | string | 开仓/平仓 | `open` → `closed` |
| close_date | string | 平仓 | `YYYY-MM-DD` |
| close_price | float | 平仓 | 平仓价格 |
| pnl | float | 平仓 | = (close - open) × quantity |
| pnl_pct | float | 平仓 | = (close - open) / open |
| holding_days | int | 平仓 | = close_date - open_date（自然日） |
| close_reason | string | 平仓 | 止盈 / 止损 / 调仓 / 其他 |

部分平仓时拆分记录，trade_id 加后缀（`a` 留存，`b` 已平）。

## Stock Code Conventions

| 场景 | 格式 | 示例 |
|------|------|------|
| 代码字段 / 对话引用 | `{代码}.{交易所大写}` | `600519.SH` |
| 交易所映射 | 沪 `.SH` / 深 `.SZ` / 北 `.BJ` | — |

## Trade Plan Review Dimensions

审查 5 维度速查：

1. **研究支撑** — 有无 rationale-card？评分档位？是否在核心池？
2. **仓位合理** — 单标的 >15% 提醒，>25% 警告
3. **风险收益** — 盈亏比 < 2:1 提醒，无止损 警告
4. **周期时机** — 是否追高 / 抄底过早
5. **交易纪律** — 频繁交易 / 情绪化 / 与此前计划矛盾

## Cross-Workspace

| 引用来源 | 路径 | 用途 |
|---------|------|------|
| 投资哲学 | `../research-workspace/PHILOSOPHY.md` | 审查与复盘的评价锚点 |
| 个股逻辑卡片 | `../research-workspace/knowledge/stock-rationale-card/` | 验证交易逻辑有无研究支撑 |
| 行业逻辑卡片 | `../research-workspace/knowledge/sector-rationale-card/` | 行业周期判断 |
| 核心池 | `../research-workspace/knowledge/core_stock_pool.xlsx` | 判断标的是否在核心池 |

---

_Add your own notes below as you learn what works._
