---
name: trading-log
description: 交易日志记录与更新。当用户说"记录交易"、"这笔交易平仓了"、"更新交易结果"、"交易已执行"时触发。
---

# Trading Log

交易日志的记录、更新与维护。记录每笔交易从开仓到平仓的完整生命周期。

## 核心约束

- 交易日志是**事实记录**，不可篡改历史数据（仅允许补充平仓信息）
- 股票代码必须含交易所后缀
- 每笔交易有唯一 `trade_id`，贯穿开仓到平仓

---

## 文件规范

- **路径**：`/app/custom/trading-workspace/trading-logs/trading_log.xlsx`
- **Sheet 名**：`log`

### Columns

| 列名 | 类型 | 说明 | 写入时机 |
|------|------|------|---------|
| trade_id | string | 交易唯一 ID，格式 `T{YYYYMMDD}{序号}`（如 `T20260328001`） | 开仓时 |
| open_date | string | 开仓日期，`YYYY-MM-DD` | 开仓时 |
| code | string | 股票代码，含交易所后缀 | 开仓时 |
| short_name | string | 股票简称 | 开仓时 |
| direction | string | `买入` / `卖出`（做空标记） | 开仓时 |
| open_price | float | 开仓价格 | 开仓时 |
| quantity | int | 交易数量（股） | 开仓时 |
| trade_amount | float | 交易金额，= open_price × quantity | 开仓时 |
| trade_rationale | string | 交易逻辑简述（1-2 句） | 开仓时 |
| stop_loss | float | 止损价格（可为空） | 开仓时 |
| target_price | float | 目标价格（可为空） | 开仓时 |
| status | string | `open` / `closed` | 开仓时写 open |
| close_date | string | 平仓日期，`YYYY-MM-DD` | 平仓时 |
| close_price | float | 平仓价格 | 平仓时 |
| pnl | float | 区间盈亏金额，= (close_price - open_price) × quantity | 平仓时 |
| pnl_pct | float | 区间盈亏百分比，= (close_price - open_price) / open_price | 平仓时 |
| holding_days | int | 持有天数，= close_date - open_date | 平仓时 |
| close_reason | string | 平仓原因（止盈 / 止损 / 调仓 / 其他） | 平仓时 |

---

## 执行流程

### 场景一：新建交易记录（开仓）

通常由 `trade-plan-review` 确认后自动调用，也支持用户直接告知。

1. **生成 trade_id**：读取当日已有记录数，生成递增序号
2. **填写开仓字段**：open_date、code、short_name、direction、open_price、quantity、trade_amount、trade_rationale、stop_loss、target_price
3. **status 设为 `open`**
4. **平仓字段留空**
5. **写入 Excel**
6. **对话确认**：

```
## 交易记录已创建

**Trade ID**：T20260328001
**标的**：贵州茅台（600519.SH）
**方向**：买入  |  **价格**：1,800.00  |  **数量**：500 股
**交易金额**：900,000.00 元
**交易逻辑**：{rationale}
**止损**：1,710.00  |  **目标**：2,050.00
```

### 场景二：更新交易结果（平仓）

用户在未来对话中告知某笔交易的结果。

1. **识别目标交易**：根据用户描述（标的名称、代码、日期等）匹配 `status = open` 的记录
   - 若匹配到多条，列出候选让用户确认
   - 若未匹配到，提示用户确认信息
2. **提取平仓信息**：close_date、close_price、close_reason
3. **自动计算**：
   - `pnl = (close_price - open_price) × quantity`
   - `pnl_pct = (close_price - open_price) / open_price`
   - `holding_days = close_date - open_date`（自然日）
4. **更新 status 为 `closed`**
5. **写入 Excel**
6. **对话确认**：

```
## 交易记录已更新

**Trade ID**：T20260328001
**标的**：贵州茅台（600519.SH）
**开仓**：2026-03-28 @ 1,800.00 → **平仓**：2026-04-15 @ 1,950.00
**盈亏**：+75,000.00 元（+8.33%）
**持有天数**：18 天
**平仓原因**：止盈
```

### 场景三：部分平仓

用户仅卖出部分持仓时：

1. 原记录保留，数量改为剩余部分
2. 新建一条 `closed` 记录，数量为卖出部分，写入完整平仓信息
3. 两条记录的 trade_id 使用后缀区分：`T20260328001a`（留存部分）、`T20260328001b`（已平部分）

---

## 查询支持

用户可随时查询交易日志：

| 查询意图 | 示例 |
|---------|------|
| 查看未平仓交易 | "目前有哪些未平仓的交易" |
| 查看某标的历史交易 | "茅台的交易记录" |
| 查看某时间段交易 | "三月份的交易记录" |
| 查看盈亏汇总 | "这个月赚了多少" |

查询结果在对话中以表格形式呈现。

---

## 与其他技能的协同

- **trade-plan-review** → 确认执行后调用本技能创建开仓记录
- **holdings-manage** → 开仓/平仓后同步更新持仓
- **trade-review** → 复盘时读取本技能的交易日志数据
