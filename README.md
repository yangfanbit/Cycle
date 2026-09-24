# ThreeC

**A股历史机会时间轴 / 历史机会地图**

> 看今天处于一年中的什么位置 → 看历史同期 → 看历史周期阶段 → 看当前研究对象 → 找历史结构对应 → 继续研究。

**ThreeC = Research + Cycle Product**

- **Research**：历史研究 / 数据生产 / Research Artifacts（`research/`）
- **Product**：Timeline / Current Lens / 历史比较呈现（`src/`）

> **核心价值 = 机会发现。**
> ThreeC 不负责基本面、技术面、个股选择、买卖时机、预测或自动交易。

---

## 当前状态

截至 **2026-09-24**：

| 项 | 当前基线 |
|---|---|
| Historical Universe | **79** Historical Objects（52 Campaign + 27 Research Candidate） |
| Macro Theme roots | **11** |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.5**（395 pairs） |
| Time Observation | **v0.2**（内部 `artifact_version` 0.3） |
| Current Candidates | **5** |
| Product | **已消费最新 SA / TO artifact**（5 / 5 Current Candidate 可走通完整研究闭环） |

**Research Core 状态**：**Release 完成并冻结** —— 后续只允许由「真实 Product Usage 暴露的问题」触发新研究轮次。

**当前阶段**：**ThreeC 1.0 Deployment / Release Engineering —— 已完成**，线下唯一剩余 Release 前置为 **Gate M（真机 / 实际浏览器复核）**（详见 `docs/ROADMAP.md`）。

> ⚠️ **尚未正式发布。** 部署工程已完成（静态部署 / 访问入口 / 可追溯 / 可回滚），
> **`package.json` 仍为 `0.1.0`，没有 `v1.0.0` tag**。
> **Deployment Engineering 完成 ≠ 正式 1.0 Release。**
> Gate R/P/T/Q/U/D（部署工程）/G 已 PASS；**Gate M 待真机复核**。
> 只有 8 个 Release Gate 全部 PASS 后，下一独立 Release 轮才执行版本号变更与正式发布。

最新状态详见：

- `docs/PROJECT_STATE.md`（动态状态，以它为准）
- `docs/ROADMAP.md`（路线）
- `docs/THREEC_1_0_RELEASE_DEFINITION.md`（1.0 发布定义与 Gate）
- `docs/DEPLOYMENT_RUNBOOK.md`（部署 / 重建 / 回滚规程）

---

## 线上访问入口（Production）

| 项 | 值 |
|---|---|
| **正式入口** | **https://yangfanbit.github.io/Cycle/** |
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
