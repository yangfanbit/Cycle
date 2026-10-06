# THREEC_1_1_LIFECYCLE_TRACKING_DESIGN.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **设计（Design）** —— ThreeC 1.1 Phase 1.4 最后一跳 |
> | 日期 | 2026-10-06 |
> | 上游 | `docs/MARKET_SNAPSHOT_CONTRACT_v0.3.md` · `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` · `docs/MONTHLY_RESEARCH_RUNBOOK.md` |
> | 目标（用户目标 #3） | **理解主题生命周期** |

---

## 1. 这一层解决什么

历史侧已有生命周期（52 Campaign 的 `lifecycle` 分段）。
但**当前对象**只有「一个时点的阶段」，没有「它是怎么走到这里的」。

> **Lifecycle Tracking = 当前对象的「追加式观察时间线」。**
> 它回答：这个对象**依次**出现了哪些可核验事件，阶段是怎么演进的。

## 2. ★ 核心设计判断：**派生，不新增 artifact**

**不建立独立的「生命周期日志文件」** —— 而是**从快照序列派生**。

理由（与 v0.2「回指」同源）：

| 若独立建日志 | 若从快照派生 |
|---|---|
| 同一事实存两处 → 可能漂移 | **单一事实来源**（快照里的 `observations`） |
| 需要额外的 append-only 维护纪律 | **append-only 由构造保证**：新快照只追加 |
| 需要额外校验「日志与快照一致」 | **不可能不一致**（本来就是同一份数据） |

**派生规则**：把全部快照的 `observations[]` 按 `linked_object_id` 分组，按 `date` 升序 —— 即得该对象的观察时间线。

## 3. 三条硬约束

| # | 约束 | 落地方式 |
|---|---|---|
| **1** | **append-only** | 时间线由快照序列派生；快照本身不可变（`CANONICAL` 改内容必须新 revision）→ 时间线**只增不改** |
| **2** | **禁 look-ahead（PIT 安全）** | 每条观察的 `date <= 该快照的 snapshot_date`（校验 **V4/O5** 强制）；派生时**以观察所在快照的日期为可见上界** |
| **3** | **只陈述事实** | 时间线只列「何时发生了什么」，**不做阶段判断、不做因果推断、不给评分** |

### ★ 约束 2 的关键细节：可见上界 ≠ 今天

派生某对象的完整时间线时，**必须**按快照逐个推进：
第 N 期的时间线**只能**包含第 1..N 期快照里的观察。

否则会出现「用 10 月的信息去解释 9 月的状态」——**这正是 look-ahead**。
因此派生函数必须支持 `asOf(snapshotDate)`：**只回放该日期之前的快照**。

## 4. 数据结构

```jsonc
// 派生结果（不落盘，Product 侧运行时计算）
{
  "object_id": "CC-2026-…",
  "display_name": "…",
  "entries": [
    {
      "date": "2026-09-14",
      "observation_id": "OBS-…",
      "observation_type": "POLICY",
      "claim": "…",
      "evidence_strength": "STRONG",
      "direction": "SUPPORTIVE",
      "source_tier": "T2",
      "source_title": "…",
      "first_seen_in": "MS-2026-10-06-02"   // ★ 哪一期快照首次登记了它（可追溯）
    }
  ],
  "count": 7,
  "first_date": "…",
  "last_date": "…"
}
```

**字段说明**：

- `first_seen_in` 记录「这条观察是哪一期快照带进来的」—— 用于回答「我上个月看到它了吗」，
  且**同一 `observation_id` 在多期出现时取最早一期**（append-only 语义）。
- 时间线**不做阶段推断** —— 阶段仍由快照的 `research_objects[].declared_phase` 承载。

## 5. 校验规则（新增 L1–L3）

| # | 规则 | 级别 |
|---|---|---|
| **L1** | 观察的 `linked_object_id`（若有）必须能在**同一快照**的 `research_objects[].object_id` 中找到 | FAIL |
| **L2** | 同一 `observation_id` 在**同一快照内**不得重复（已有 O4） | FAIL |
| **L3** | 同一 `observation_id` 跨快照出现时，**内容必须一致**（不得悄悄改写历史） | FAIL |

> **L3 的意义**：append-only 的真正保证。没有它，同一 id 的 claim 可以被后续快照改写，
> 「时间线」就变成了「随时可重写的叙述」。

## 6. 与「当前 → 历史」的关系

| 层 | 内容 | 来源 |
|---|---|---|
| 当前对象的时间线 | 观察序列（本设计） | 快照序列派生 |
| 当前对象的**阶段** | `declared_phase` | 快照（研究声明 / 证据派生） |
| 当前 ↔ 历史的**结构对应** | SA 四维解释 | 冻结 SA artifact（回指） |

**本设计不重复 SA 的职责** —— 它只补上「当前对象自己的时间维度」。

## 7. 本轮不做

- ❌ 不做阶段自动推断（阶段仍由研究侧声明）
- ❌ 不做「当前时间线 vs 历史时间线」的自动对齐（那属 SA 的 `lifecycle` 维度）
- ❌ 不新增独立日志 artifact（见 §2）
- ❌ 不做因果 / 预测 / 评分

---

*设计 · ThreeC 1.1 Phase 1.4 · 2026-10-06*
