# TOOLS.md - Research Workspace Local Notes

Skills define _how_ tools work. This file records environment-specific paths, formats, and quick references for daily use.

---

## Data Paths

**重要：所有路径必须使用绝对路径，不要使用 `./` 相对路径（因为通过 session_send 调用时，工作目录可能不是 research-workspace）。**

| 用途 | 路径 | 格式 |
|------|------|------|
| 个股逻辑卡片 | `/app/custom/research-workspace/knowledge/stock-rationale-card/{代码}_{交易所小写}.md` | Markdown |
| 行业逻辑卡片 | `/app/custom/research-workspace/knowledge/sector-rationale-card/{行业名称}.md` | Markdown |
| 核心池 | `/app/custom/research-workspace/knowledge/core_stock_pool.xlsx` | Excel |

## Stock Code Quick Reference

| 场景 | 格式 | 示例 |
|------|------|------|
| 文件名 | `{代码}_{交易所小写}.md` | `600519_sh.md` |
| 代码字段 / 对话引用 | `{代码}.{交易所大写}` | `600519.SH` |
| 交易所映射 | 沪 `.SH` / 深 `.SZ` / 北 `.BJ` | — |

## Core Pool Excel Schema

Sheet: `core_stock_pool`

| Column | Type | Description |
|--------|------|-------------|
| code | string | `600519.SH` |
| short_name | string | `贵州茅台` |
| in_pool_date | string | `YYYY-MM-DD` |
| out_pool_date | string | `YYYY-MM-DD`（空 = 在池） |
| update_date | string | `YYYY-MM-DD` |

池规模：~500 只（450-550），科技医药成长股优先，红利价值股 ≥ 50 只。

## Search Source Control

### Whitelist (P0-P2)

- 官方披露：cninfo.com.cn、sse.com.cn、szse.cn
- 高质量社区：xueqiu.com、zhihu.com
- 财经媒体：caixin.com、cls.cn、yicai.com
- 微信公众号：需逐号判断质量

### Blacklist

- guba.eastmoney.com（股吧）
- baijiahao.baidu.com（百家号）
- 其他 UGC 低信噪比平台

黑名单来源命中时直接丢弃，不纳入分析。

## Cross-Workspace

| 引用方向 | 路径 |
|---------|------|
| 投资哲学 | `/app/custom/research-workspace/PHILOSOPHY.md` |
| Trading 持仓 | `/app/custom/trading-workspace/holdings/holdings.xlsx` |
| Trading 日志 | `/app/custom/trading-workspace/trading-logs/trading_log.xlsx` |

---

_Add your own notes below as you learn what works._
