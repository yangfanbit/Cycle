# ThreeC

**A股历史机会时间轴 / 历史机会地图**

> 看今天处于一年中的什么位置 → 看历史同期 → 看历史周期阶段 → 看当前研究对象 → 找历史结构对应 → 继续研究。

**ThreeC = Research + Cycle Product**

- **Research**：历史研究 / 数据生产 / Research Artifacts（`research/`）
- **Product**：Timeline / Current Lens / 历史比较呈现（`src/`）

> **核心价值 = 机会发现。**
> ThreeC 不负责基本面、技术面、个股选择、买卖时机、预测或自动交易。

**明确不提供（Product 非目标）**：

- ❌ 不提供买卖信号 / 不自动交易
- ❌ 不选股 / 不荐股
- ❌ 不预测价格 / 不预测收益
- ❌ 不提供概率 / 胜率 / 推荐分
- ❌ 不运行时联网 / 不做实时行情或资金异动监控

---

## 当前状态

> ★ **本节 2026-10-13 重写** —— 原表格停留在 **2026-09-24**（79 对象 / 11 根 / SA v0.5），
> 完全未反映其后的 **R02 波次**、**Contract v1.1 / v1.2**、**SA v0.6 → v0.13**。
> 下方「ThreeC 1.0 — RELEASED」小节保留（仍是事实），但**不代表当前进度**。

截至 **2026-10-13**（全部实测）：

| 项 | 当前基线 |
|---|---|
| Historical Universe | **89** Historical Objects（**62 Campaign** + 27 Research Candidate） |
| Macro Theme roots | **13**（DB `themes` 共 59 行） |
| Export Contract | **v1.2**（含 `macro_theme_root` + `taxonomy` 段） |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.13**（**534** pairs · 规则集 `structural-analogy-ruleset-v0.3` **冻结未变**） |
| Time Observation | **v0.2**（内部 `artifact_version` 0.3） |
| Current Candidates | **6** |
| Market Snapshot | `MS-2026-10-13-01` = **DRAFT**（待签发）· `MS-2026-10-12-01` = CANONICAL |
| 测试 | **881 passed / 0 failed / 33 files** |
| CI 门禁 | **Product**（tsc / npm test / build）+ **Research 只读**（5 项校验，2026-10-13 接入） |

**当前阶段**：**R02 波次**（历史宇宙扩展）—— 已完成 R02-01 / R02-03 / R02-04 / R02-05，
4 条 DEFER 待处置；粒度已裁定为「**机制段**」。

### ThreeC 1.0 — RELEASED（历史，仍是事实）

| 项 | 值 |
|---|---|
| **Version** | **`1.0.0`** |
| **Tag** | **`v1.0.0`**（annotated） |
| **Release commit** | **`064d39c`** |
| **Production** | **https://yangfanbit.github.io/Cycle/** |
| **Gate R / P / T / Q / U / M / D / G** | **全部 PASS** |
| **P0 / P1** | **0 / 0** |

> ✅ **ThreeC 1.0 已正式发布。**
> Research Core 冻结 · Product 1.0 已发布 · Deployment 已进入生产 · 8 个 Release Gate 全部 PASS。
> 后续版本（1.1+）只允许由真实 Product Usage 或明确 Research Question 触发，**不预设新功能**。

最新状态详见：

- `docs/PROJECT_STATE.md`（动态状态，以它为准）
- `docs/ROADMAP.md`（路线）
- `docs/THREEC_1_0_RELEASE_DEFINITION.md`（1.0 发布定义与 Gate）
- `docs/DEPLOYMENT_RUNBOOK.md`（部署 / 重建 / 回滚规程）

---

## 线上访问入口（Production · v1.0.0）

| 项 | 值 |
|---|---|
| **正式入口** | **https://yangfanbit.github.io/Cycle/** |
| **版本** | **`1.0.0`**（tag `v1.0.0`，release commit `064d39c`） |
| 宿主 | GitHub Pages（纯静态） |
| 部署 | GitHub Actions（`.github/workflows/deploy.yml`）· push `main` 自动构建 + 部署 |
| 研究预览 | https://yangfanbit.github.io/Cycle/?preview=1 |
| 示例 fixture | https://yangfanbit.github.io/Cycle/?candidates=example |

**构建溯源**：页面页脚「Build Provenance」可查本次线上 build 的
`Product version` / `构建 commit` / **Research export `source_commit`** / SA 版本 / TO 版本 ——
用于确认线上 build 与 Research artifact 的对应关系（Gate D7）。

部署与回滚规程：`docs/DEPLOYMENT_RUNBOOK.md`。

---

## 快速开始

### Product

需要 Node.js ≥18（CI 使用 Node 22）。

```bash
npm install
npm run dev
npm test
npx tsc -b
npm run build
```

默认运行的是静态 Product。

Research Preview：

```
http://localhost:5173/?preview=1
```

Current Candidate 示例 fixture：

```
http://localhost:5173/?candidates=example
```

**复现 GitHub Pages 子路径行为**（本地验证 `/Cycle/` 下的资源是否正确）：

```bash
GITHUB_ACTIONS=true npx vite build      # base 变为 /Cycle/
grep -oE '(src|href)="[^"]*"' dist/index.html   # 期望 /Cycle/assets/...
```

本地 `dev` / `preview` / `build` 默认 `base = /`，**不受子路径影响**。
规则与回滚方式见 `docs/DEPLOYMENT_RUNBOOK.md` §4。

### Research

需要 Python 3 + 标准库 sqlite3。

```bash
cd research
python scripts/validate_db.py
python scripts/validate_timeline_export.py
python scripts/validate_current_research.py
```

研究脚本与 Artifact 均要求可复现。

---

## 数据流

```
Research DB / Current Research
        ↓
Research Artifacts / canonical export
        ↓
Product Adapter
        ↓
Timeline / Current Lens / Calendar / Lifecycle
```

Product runtime 不联网、不调用 LLM。

---

## 仓库原则

- 一个 Git / 一个项目根
- 一个 canonical Research
- 一个 Product
- Research 与 Product 逻辑分层
- 不编造历史事实
- `PROVISIONAL ≠ VERIFIED`
- UNKNOWN / NOT_AVAILABLE 是合法状态
- 历史比较禁止 look-ahead
- 不为了“好看”放松研究门槛

接手顺序：

`AGENTS.md → docs/PROJECT_STATE.md → 按任务读取局部文档`
