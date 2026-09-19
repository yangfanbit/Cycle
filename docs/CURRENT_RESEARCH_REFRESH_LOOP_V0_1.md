# CURRENT_RESEARCH_REFRESH_LOOP_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **研究运维闭环**（不新增 Product 页面、不新增 Research 能力） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 726390c`，ahead/behind `0/0`，工作树 clean（**自行核对**；远程无新增，已在同步状态） |
> | **Gate** | **`PASS`** |
> | 未修改 | `research/**` 中的**研究内容**（`current_candidates.json` 逐字节未变）· Rule Set v0.2 · Structural Analogy Artifact · schema · export contract · 历史数据 |

---

## 1. Product Objective

把 **Current Candidate** 从「一次性静态成果」变成**可重复更新的 Current Research Snapshot 工作流**：

```
市场新信息 → 离线 Research → Current Candidate Snapshot → Product 静态消费 → 历史结构比较
```

| 侧 | 边界 |
|---|---|
| **Research** | 可离线网络检索 · 可用 AI 作研究辅助 · 输出**确定性、可审查**的 snapshot |
| **Product runtime** | **无外部网络 · 无 LLM · 无 Research runtime**（仍是 Static PWA） |

---

## 2. Current Snapshot Contract（正式语义，**不得混淆**）

| 字段 | 语义 |
|---|---|
| `snapshot_date` | 本次 Current Research **可以使用的最新信息截止日**（Temporal Firewall 基准） |
| `generated_at` | 该 snapshot 的**生成时间** |
| `last_updated`（candidate 级） | 单个 candidate **最近一次研究更新** |
| `research_coverage_until` | **历史 Research 数据覆盖到哪一年** |
| `current_candidates_version` | snapshot 的**版本号**（结构变更时递增） |

**Refresh Contract 校验**（`check_contract`）：

- 必需字段齐全（`snapshot_date` / `generated_at` / `research_coverage_until` / `version`）
- `generated_at ≥ snapshot_date`
- `snapshot_date` **晚于** `research_coverage_until`
- candidate 命名空间必须 `CC-*`；**禁止** `C-*` / `RC-*`
- 无重复 `candidate_id`
- `candidate_status ∈ {CANDIDATE, WATCH, RESEARCHING, PROMOTABLE, REJECTED}`（**不新增状态**）
- `attention_state ∈ {EARLY_SIGNAL, THEME_FORMING, BROAD_CONFIRMATION, EXPANSION, PEAK, DECLINE, UNKNOWN}`（**不新增阶段模型**）
- `last_updated ≤ snapshot_date`
- **所有 evidence 日期 ≤ `snapshot_date`**（Temporal Firewall）

---

## 3. Research → Snapshot Pipeline

```
Collect    收集新一轮公开信息（Tier 1 官方 → Tier 2 公告/产业 → Tier 3 媒体转述）
   ↓       —— source policy **不变**
Normalize  统一为 event date / source date / source type / claim / strength / direction
   ↓       —— **不把新闻标题直接变成 Candidate**
Evidence   每个重要判断至少可追溯到 Evidence
   ↓       —— claim(事实) / core_narrative(叙事) / uncertainty_notes(不确定) / conflict_notes(冲突) **不混用**
Candidate  Signal → Evidence → Candidate（命名空间 CC-*）
   ↓       —— Candidate ≠ Theme ≠ Campaign ≠ Buy/Sell Signal ≠ Prediction
Validate   refresh_current_research.py --check
   ↓
Snapshot   research/current/current_candidates.json（+ snapshots/manifest.json 元信息）
   ↓
Product    currentCandidate.ts → currentCandidateAdapter → Current Time Lens
```

### 自动化边界（审计结论）

| 步骤 | 现状 | 说明 |
|---|---|---|
| Collect / Normalize / Evidence / **Candidate 判断** | **必须人工（+ AI 辅助）** | 属**研究判断**，不可机械生成 |
| Validate | ✅ **已确定性自动化** | 复用 `validate_current_research.py` + Refresh Contract |
| Candidate **Diff** | ✅ **已确定性自动化** | 本轮新增 |
| Snapshot 记录 | ✅ **已确定性自动化** | 本轮新增（manifest，幂等） |
| Product 消费 | ✅ 确定性（静态 import） | 既有能力 |

> **本脚本不做研究判断** —— 它只做 Refresh 的**机械动作**。

---

## 4. Temporal Firewall（硬约束）

对 `snapshot_date = D`：**所有** evidence / event / source-derived claim / phase input 必须满足

> **不得使用 D 之后才知道的信息。**

- ✅ **复用既有实现**（`validate_current_research.py` 的 `derive_temporal`），
  **未重新实现第二套时间过滤逻辑**
- ✅ Refresh CLI 额外做**独立**的 evidence 日期 ≤ snapshot_date 检查（双重把关）
- 实测：`2026-09-15` snapshot 的全部 evidence 日期 **≤ 2026-09-15** ✅

---

## 5. Incremental Refresh

```
旧 Snapshot → 新 Evidence（离线产出）→ Candidate diff → 校验 → 新 Snapshot
```

**CLI**：

```bash
python research/scripts/refresh_current_research.py --check
python research/scripts/refresh_current_research.py --check --snapshot-date 2026-09-15
python research/scripts/refresh_current_research.py --diff --baseline <path.json>
python research/scripts/refresh_current_research.py --check --record
```

| 参数 | 作用 |
|---|---|
| `--check` | 默认动作：Refresh Contract + 复用既有 validator |
| `--snapshot-date` | 期望的 `snapshot_date`；不一致 → **FAIL（防漂移）** |
| `--diff --baseline` | 与基线 snapshot 做 Candidate diff |
| `--record` | 把当前 snapshot **元信息**登记进 `snapshots/manifest.json`（**幂等**） |
| `--json` | 机器可读输出（**确定性**） |

**确定性**：无随机 · 无当前时间依赖 · **无网络** · 无 LLM。实测两次 `--json` 输出**逐字节一致** ✅

---

## 6. Candidate Diff

| 类别 | 判据 | 可机械判定 |
|---|---|---|
| **NEW** | id 在 target 不在 baseline | ✅ |
| **UPDATED** | id 两侧都有，**内容指纹不同**，且状态非 `REJECTED` | ✅ |
| **UNCHANGED** | id 两侧都有，内容指纹**相同** | ✅ |
| **REJECTED** | (id 在 baseline 不在 target) **或**（状态变为 `REJECTED`） | ✅ |
| **MERGED** | 两个 Candidate 被研究判断为同一对象 | ❌ **不可机械判定** |

> **MERGED 的 limitation（按 §十 记录，不擅自扩展状态机）**：
> 「两个 Candidate 是同一对象」属**研究判断**，无法由数据结构机械推出。
> CLI 输出 `MERGED: 0` 并附 `merged_limitation` 说明，需**离线研究显式声明**。

**实测（`2026-09-15` 自身为基线）**：

```
NEW 0 · UPDATED 0 · UNCHANGED 5 · REJECTED 0 · MERGED 0
stable: True
```

✅ 无理由的数量变化 / ID 变化 / snapshot_date 漂移 —— **均未发生**。

---

## 7. Validation

| 校验 | 实现 |
|---|---|
| schema / Temporal Firewall / Theme Boundary / Similarity / Evidence | **复用** `validate_current_research.py`（未重复实现） |
| Refresh Contract（字段语义 / 命名空间 / 必需项 / 重复 ID / 日期一致性） | 本轮新增 |
| 确定性 | 两次 `--json` 逐字节一致 |
| 幂等性 | 连续 `--record` → `snapshot_count` 稳定为 1，`changed=False`，manifest 逐字节一致 |

**退出码**：0 = PASS；1 = FAIL。

---

## 8. Product Consumption

**未新增任何 Product 页面。** 既有链路继续成立：

```
新 snapshot → Current Candidate → Structural Analogy → Historical Case → Historical Cycle Map
```

| 验证项 | 结果 |
|---|---|
| snapshot 变新后 Current Candidate 正确更新 | ✅ 5 个候选全部进入 Product View，数量不漂移 |
| `stale` 提示正确变化 | ✅ `today > snapshot_date` → stale；`today = snapshot_date` → 不提示 |
| 历史数据不变 | ✅ 历史 Timeline 不受影响 |
| Structural Analogy 不受影响 | ✅ 测试全绿 |
| Historical Cycle Map 不受影响 | ✅ 测试全绿 |
| **Product parser 不被破坏** | ✅ `tsc -b` exit 0 · `npm test` 555 passed |

---

## 9. Snapshot Freshness（文案优化）

**改进前**：`（快照距今 N 天，不是当前市场状态）` —— 混在元信息行内，不够醒目。

**改进后**：

```
研究快照：2026-09-15 · 距今天：4 天 · 历史研究覆盖至 2025 · 数据来源：离线研究生成（非实时行情 / 非实时新闻）

[stale 时] 当前研究快照已滞后（距今 4 天）—— 以下内容不是实时研究结果，
           请在离线研究侧完成新一轮 Refresh 后再作参考。
```

- ✅ 字段语义**分别展示**，不混淆
- ✅ stale 提示**独立成块**（`role="note"`，警示配色），明确「**不是实时研究结果**」
- ✅ 仍复用既有 `snapshotDate` / `stalenessDays` / `stale`（**未新增字段**）

---

## 10. Historical Data Precision Boundary

**正式确定**：

| 阶段 | 观察分辨率 |
|---|---|
| **现在** | 产品观察 = **周级**；历史时间**足以支持「这一时期」的比较即可** |
| 后续 | 由**真实使用反馈**决定：哪些 Campaign 值得精确到周 / 日 / source-level verification |

> **数据精度提升由产品使用价值驱动**，不是由「数据库看起来还不够漂亮」驱动。

**本轮明确不做**：`campaign_date_observations verified = 0/24` 继续作为 **Future Debt**；
**不逐条验证 · 不补来源 · 不修日期 · 不升级历史精度**。

---

## 11. Known Limitations

| # | Limitation |
|---|---|
| 1 | **Candidate 判断不可自动化** —— Collect / Normalize / Evidence / Candidate 仍需离线研究（人工 + AI 辅助） |
| 2 | **MERGED 不可机械判定** —— 需离线研究显式声明（见 §6） |
| 3 | **snapshot history 只保留 manifest** —— 不复制大型冗余文件；历史快照内容需从 git 历史取得 |
| 4 | **无自动写入 canonical** —— `--record` 只写 manifest；`current_candidates.json` 的更新由离线研究显式产出 |
| 5 | `campaign_date_observations verified = 0/24`（Future Debt，不阻塞） |
| 6 | 交易日历不完整 → 采用**自然周**（周一→周日） |
| 7 | 无 snapshot 之间的 **evidence 级 diff**（仅 candidate 级） |

---

## 12. Test Results

```
python research/scripts/refresh_current_research.py --check   → PASS
python research/scripts/refresh_current_research.py --check --snapshot-date 2026-09-15  → PASS
python research/scripts/refresh_current_research.py --check --diff --baseline <self>    → stable: True

npm test       → 555 passed（15 files；上轮 547 + 本轮新增 8）
npx tsc -b     → exit 0
npm run build  → PASS，无 chunk >500 kB 警告
```

**新增 Product 测试（`currentResearchRefresh.test.tsx`，8 项）**：
快照字段语义分展 · `stale` 提示「不是实时研究结果」 · 离线来源明示 ·
`today = snapshot_date` 时不提示 · 缺 `snapshot_date` 时不展示候选 ·
`CC-*` 命名空间隔离 · 5 个候选数量不漂移 · 历史 Timeline 不受影响

**回归**：上轮 547 项全部通过（含 1 项按 §十一 更新文案断言）。

**Research validators**：7 个全部 **PASS**。

---

## 13. Gate

> ## ✅ **`PASS`**

| 验收项 | 结果 |
|---|---|
| Refresh CLI 存在且支持 `--check` | ✅ |
| Refresh Contract 校验 | ✅ 字段语义 / 命名空间 / 必需项 / 重复 ID / 日期一致性 |
| Temporal Firewall | ✅ **复用既有实现** + 独立日期检查 |
| Candidate Diff（NEW/UPDATED/UNCHANGED/REJECTED） | ✅ 确定性 |
| MERGED | ✅ 按 §十 记录 limitation，**未扩展状态机** |
| 无输入变化 → deterministic / stable output | ✅ `stable: True`；`--json` 逐字节一致；`--record` 幂等 |
| 无理由数量 / ID 变化 / snapshot_date 漂移 | ✅ 均未发生 |
| evidence 日期不超过 snapshot | ✅ |
| Product parser 不被破坏 | ✅ |
| 历史 Research 不被改变 | ✅ `current_candidates.json` 逐字节未变 |
| snapshot 新鲜度文案优化 | ✅ |
| `npm test` / `tsc -b` / `npm run build` | ✅ 555 passed / exit 0 / PASS |
| build 无新 `>500 kB` warning | ✅ |
| research / schema / export 无变化 | ✅ 研究内容零改动 |

### 本轮修改

| 文件 | 说明 |
|---|---|
| **A** `research/scripts/refresh_current_research.py` | Refresh CLI（Contract + Diff + Manifest + 复用 validator） |
| **A** `research/current/snapshots/manifest.json` | snapshot 元信息（幂等；**不复制内容**） |
| **A** `src/data/timeline/__tests__/currentResearchRefresh.test.tsx` | 8 项 Product 消费测试 |
| **A** `docs/CURRENT_RESEARCH_REFRESH_LOOP_V0_1.md` | 本文档 |
| M `src/components/CurrentTimeLens/CurrentCandidateSection.tsx` | 快照新鲜度文案（字段分展 + stale 独立提示） |
| M `src/data/timeline/__tests__/currentResearch.test.tsx` | 文案断言更新 |
| M `src/styles.css` | `.ccs-stale-note` |
| M `docs/PROJECT_STATE.md` | HEAD / Current Stage / Next Step 同步 |

### 本轮**未**修改
`research/current/current_candidates.json`（**研究内容逐字节未变**）· Rule Set v0.2 ·
Structural Analogy Artifact · schema · export contract · 历史数据 ·
`currentSimilarity.ts` · `historicalSimilarPhase.ts` · `OpportunityRadar`

---

## 14. 完成后的工作循环

```
新一轮市场研究（离线）
      ↓
Current Research Snapshot（refresh_current_research.py --check）
      ↓
ThreeC（Static PWA）
      ↓
当前候选 → 历史周期 / Structural Analogy → Historical Case
      ↓
人工研究
      ↓
下一轮 Snapshot
```

ThreeC 从此不再只是「一次做完的产品原型」，而是**可以持续更新的研究工具**。

---

*文档结束 · Current Research Refresh Loop v0.1 · 2026-09-19*
