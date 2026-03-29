# investAssis — OpenClaw 投资分析助手系统

基于 OpenClaw 平台的多智能体投资研究、交易与反思系统。通过 Docker 容器外挂卷方式部署，四个专属智能体各司其职，协同完成从研究到交易到复盘的完整投资闭环。

## 架构概览

```
用户
 │
 ▼
supervisor（主控）─── session_send ───┬── research（研究）
                                      ├── trading（交易）
                                      └── reflection（反思）
```

- **supervisor** 理解用户意图，路由给对应子智能体，汇总结果返回
- 子智能体在各自 workspace 中独立工作，通过 `knowledge/` 目录持久化研究成果
- 所有智能体共享 `PHILOSOPHY.md` 投资哲学约束（红灯思维）

## 智能体与技能

### Supervisor（主控）— `supervisor-workspace/`

负责任务路由与分发，不直接执行研究/交易/反思任务。

| 技能 | 功能 |
|------|------|
| tushare-data | A 股/指数/ETF/宏观数据获取（Tushare API，并发限制 2） |

### Research（研究）— `research-workspace/`

投资研究的核心智能体，负责信息收集、逻辑卡片建档、研究评分与核心池维护。

| 技能 | 功能 |
|------|------|
| search-for-research | 双引擎（搜狗 + Bocha API）迭代式深度搜索，优先检索公众号纪要/点评 |
| stock-rationale-card | 个股投资逻辑卡片（按业务线拆分量/价驱动、产能规划、叙事交叉验证） |
| sector-rationale-card | 行业/产业链逻辑卡片（景气度指标体系、周期判断、竞争格局） |
| research-quality-scoring | 研究成果 B/A/S 三档评分 |
| core-pool-manage | 核心池维护（~500 只，A/S 档筛选，红利价值股 ≥50 只） |

**知识库**：
- `PHILOSOPHY.md` — 投资哲学约束，所有研究输出的锚定框架
- `knowledge/stock-rationale-card/` — 个股逻辑卡片（持久化，支持人工编辑）
- `knowledge/sector-rationale-card/` — 行业逻辑卡片
- `knowledge/core_stock_pool.xlsx` — 核心股票池

### Trading（交易）— `trading-workspace/`

交易计划评估、持仓管理与交易日志记录。

| 技能 | 功能 |
|------|------|
| trade-plan-review | 交易计划评估（基于 PHILOSOPHY.md 约束） |
| trade-review | 交易复盘与评价 |
| holdings-manage | 持仓管理（holdings.xlsx） |
| trading-log | 交易日志记录（trading_log.xlsx） |

### Reflection（反思）— `reflection-workspace/`

从交易历史中提炼教训，推动投资哲学迭代进化。

| 技能 | 功能 |
|------|------|
| loss-reflect | 亏损交易反思，生成案例卡片 |
| pattern-detect | 从多个案例中识别重复犯错模式 |
| philosophy-evolve | 基于反思成果推动 PHILOSOPHY.md 迭代更新 |

## 项目结构

```
investAssis/
├── docker-compose.yaml          # OpenClaw 容器配置
├── .env                         # 环境变量（API Key，gitignored）
├── .openclaw-config/            # OpenClaw 运行时配置
├── scripts/
│   └── sogou_search.py          # 双引擎搜索脚本（搜狗 + Bocha API）
├── supervisor-workspace/
│   └── skills/tushare-data/     # Tushare 数据技能
├── research-workspace/
│   ├── PHILOSOPHY.md            # 投资哲学（红灯思维）
│   ├── knowledge/               # 研究产出持久化
│   │   ├── stock-rationale-card/
│   │   ├── sector-rationale-card/
│   │   └── core_stock_pool.xlsx
│   └── skills/                  # 5 个研究技能
├── trading-workspace/
│   ├── holdings/                # 持仓数据
│   ├── trading-logs/            # 交易日志
│   └── skills/                  # 4 个交易技能
├── reflection-workspace/
│   ├── lessons/                 # 反思案例与模式
│   │   ├── cases/
│   │   └── patterns/
│   └── skills/                  # 3 个反思技能
└── .venv-container/             # 容器内 Python 虚拟环境（gitignored）
```

## 部署

### 环境要求

- Docker & Docker Compose
- OpenClaw 镜像（`dr34m/openclaw:latest`）

### 配置环境变量

在 `.env` 中填入：

```bash
MINIMAX_API_KEY=your_minimax_key    # LLM 模型 API
TUSHARE_TOKEN=your_tushare_token    # Tushare 数据（https://tushare.pro）
BOCHA_API_KEY=your_bocha_key        # Bocha WebSearch API（https://bocha.cn）
```

### 启动

```bash
docker-compose up -d
```

容器通过卷挂载使用项目目录：
- `~/quantWorld/investAssis` → `/app/custom`（workspace、scripts、知识库）
- `.openclaw-config` → `/home/node/.openclaw`（OpenClaw 运行时配置）

容器内自动激活 `.venv-container` Python 虚拟环境（已预装 tushare、pandas 等依赖）。

### 安装 Python 包

```bash
docker exec invest-agent-claw pip install <package_name>
```

### 访问 Web UI

浏览器打开 `http://localhost:18789`

## 设计理念

- **AI 无法替代研究者的努力** — 逻辑卡片支持人工编辑，AI 是辅助工具而非决策者
- **投资哲学是锚** — 所有输出必须通过 PHILOSOPHY.md 约束校验（红灯思维）
- **持久化跟踪** — 好的投资机会来源于持续跟踪，逻辑卡片按个股/行业维度持久化保存
- **闭环反思** — 从交易历史中提炼教训，推动投资哲学迭代进化
