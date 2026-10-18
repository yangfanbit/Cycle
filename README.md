# ThreeC

**A股历史机会时间轴 / 历史机会地图**

> 看今天处于一年中的什么位置 → 看历史同期 → 看历史周期阶段 → 看当前研究对象 → 找历史结构对应 → 继续研究。

**ThreeC = Research + Cycle Product**

- **Research**：历史研究 / 数据生产 / Research Artifacts（`research/`）
- **Product**：Timeline / Current Lens / 历史比较呈现（`src/`）

> **核心价值 = 机会发现。**
> ThreeC 不负责基本面、技术面、个股选择、买卖时机或自动交易。

**明确不提供（Product 非目标）**：

- ❌ 不提供买卖信号 / 不自动交易
- ❌ 不选股 / 不荐股
- ❌ 不提供「没有口径的预测」/ 不提供「未经验证的概率」
- ❌ 不运行时联网 / 不做实时行情或资金异动监控

> ★★ **2026-10-18 规则调整（v0.9）**：原「不预测价格 / 不预测收益 / 不提供概率」已**撤销**。
> ThreeC **可以**研究历史频率、条件概率、阶段变化概率与未来窗口预测，但**必须**写明
> 预测目标 / 样本范围 / 观察期限 / 分母 / 排除规则 / 来源 / 不确定性，
> 并以**时间顺序**验证、与**简单历史基准**比较、记录**校准与误差**（见 `AGENTS.md` §3.1）。
>
> **三层口径分开**：① 历史统计描述 · ② **经验基准概率**（比例 + 95% Wilson 区间，**未校准**）·
> ③ 已验证预测模型（**目前没有**）。②**不得**写成「未来概率」。

---

## 当前状态

> ★ **本节 2026-10-18 重写（v0.9）** —— 上一版停在 **2026-10-13**，未反映其后的
> 行情库拆分、事件地图跨年份产品化、**v0.5–v0.8** 五轮修复，以及本轮 **v0.9 概率层**。
> 下方「ThreeC 1.0 — RELEASED」小节保留（仍是事实），但**不代表当前进度**。

截至 **2026-10-18**（全部实测）：

| 项 | 当前基线 |
|---|---|
| Historical Universe | **89** Historical Objects（**62 Campaign** + 27 Research Candidate） |
| Macro Theme roots | **13**（DB `themes` 共 59 行） |
| Export Contract | **v1.2**（含 `macro_theme_root` + `taxonomy` 段） |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.13**（**534** pairs · 规则集 `structural-analogy-ruleset-v0.3` **冻结未变**） |
| Time Observation | **v0.2**（内部 `artifact_version` 0.3） |
| Current Candidates | **6** |
| Market Snapshot | `MS-2026-10-13-01` = **CANONICAL**（已签发 · supersedes `MS-2026-10-12-01`） |
| 测试 | **1312 passed / 0 failed / 61 files** |
| CI 门禁 | **Product**（tsc / npm test / build）+ **Research 只读**（5 项校验，2026-10-13 接入） |
| 外部季节性日历 | **v0.1**（25 项外部线索 · 全部 `EXTERNAL_REFERENCE`）· **v0.12 起 25 条全部铺到 1–12 月时间轴**（23 条上轴 / 24 段窗口 / 跨年拆成 28 段 + 2 条无固定窗口单列）· **v0.13 起每条 MAPPED 线索可展开「外部月份窗口 × 该主题历史 MAIN_RISE 窗口」两层对照；UNMAPPED 线索可带入现有研究请求草稿** |
| **经验基准概率（v0.9 新增）** | 电力 **1/7**（95% Wilson **2.6%–51.3%**）· 流感 **1/9**（**2.0%–43.5%**，唯一 UP 属 `UNKNOWN_PUBLIC_HEALTH`）· 均标「**未校准**」 |
| 预测模型 | **未建立**（样本外 4–6 步 << 门槛 30，且 **0 个事前特征**）· 已交付 Jeffreys 平滑基线与可行性结论 |
| **历史题材地图（v0.10/v0.11）** | 首页**直接入口**：4 题材 / **13 事件** 可切换 · 每题材含**历史参与标的索引**（流感 20 只 / 电力 6 只 / 文化传媒 4 只 / 机器人 5 只），可搜索、可展开逐次证据 |

**当前阶段**：**ThreeC 1.3**（用户驱动研究 + 概率研究）—— v0.9 已撤销「概率 / 预测」全局禁令
（见 `AGENTS.md` §3.1），交付**首个经验基准概率原型**；预测模型因样本不足**未训练**，缺口已列明。
R02 波次仍有 4 条 DEFER 待处置；粒度已裁定为「**机制段**」。

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
