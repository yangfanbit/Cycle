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

**当前阶段**：**Product / Real Usage Iteration**（详见 `docs/ROADMAP.md`）。

最新状态详见：

- `docs/PROJECT_STATE.md`（动态状态，以它为准）
- `docs/ROADMAP.md`（路线）
- `docs/THREEC_1_0_RELEASE_DEFINITION.md`（1.0 发布定义与 Gate）

---

## 快速开始

### Product

需要 Node.js ≥18。

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
