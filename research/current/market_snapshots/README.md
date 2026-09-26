# research/current/market_snapshots —— Market Snapshot（ThreeC 1.1 Phase 1.2）

> **Market Snapshot = 当前研究过程的「状态记录 Artifact」。**
> 它不是算法、不是模型、不是信号、不是预测。
> 输入：`market_regime` / `research_context` / `observations` / `research_objects`
> 输出：`historical_candidates`（历史**研究候选**）
>
> 规范：`docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` ·
> `docs/MARKET_SNAPSHOT_CONTRACT_v0.1.md` ·
> `docs/MARKET_SNAPSHOT_GOVERNANCE.md` ·
> `docs/MARKET_REGIME_AI_INTERFACE_v0.1.md`

---

## 1. 目录结构

```
research/current/market_snapshots/
├── README.md
├── schema/
│   ├── market_snapshot.schema.json     # Market Snapshot 契约 v0.1（JSON Schema draft-07）
│   └── market_regime.schema.json       # market_regime AI draft 契约 v0.1
├── scripts/
│   ├── validate_market_snapshot_v0_1.py   # 校验器（快照 V1–V10；regime R1–R10）
│   └── build_market_snapshot_v0_1.py      # 生成器（装配 + CANONICAL 闸门）
├── example/                            # ★ 示例，不是真实研究数据
│   ├── example_market_regime_draft.json
│   └── example_market_snapshot.json
├── market_regime/                      # AI 生成的 market_regime draft（Phase 1.2 起）
└── snapshots/                          # 完整 Market Snapshot（MS-*）
```

## 2. 生命周期

```
DRAFT  →  REVIEW  →  CANONICAL  →  ARCHIVED
```

> ★ **只有 `CANONICAL` 允许 Product 消费。**
> `URO-*`（用户研究对象）**仅 Draft**：CANONICAL 快照不得直接包含未评审的 `URO-*`（校验项 V7 强制）。

## 3. 用法

```bash
# 校验（默认校验本目录下全部 *.json，排除 schema/）
python3 research/current/market_snapshots/scripts/validate_market_snapshot_v0_1.py

# 校验单个文件
python3 research/current/market_snapshots/scripts/validate_market_snapshot_v0_1.py --file <path>

# 装配一个 DRAFT 快照
python3 research/current/market_snapshots/scripts/build_market_snapshot_v0_1.py \
    --snapshot-date 2026-09-30 \
    --regime   research/current/market_snapshots/market_regime/2026-09.json \
    --objects  <objects.json> \
    --observations <observations.json> \
    --out research/current/market_snapshots/snapshots/MS-2026-09-30-01.json

# 晋升 CANONICAL（必须显式给 reviewer；生成器会**先校验后落盘**，FAIL 则拒绝并降级为 DRAFT）
... --canonical --reviewer "<name>"

# 可复现性校验（需固定 --timestamp）
... --out <file> --check
```

## 4. 硬边界（不得违反）

| # | 边界 |
|---|---|
| 1 | **不计算** `historical_candidates` —— 必须由**冻结 SA v0.3** 的比较步骤产出，经 `--candidates` 传入。**严禁**在此重实现匹配 / 相似度算法。 |
| 2 | **不生成** `market_regime` —— 由 AI 离线生成 + 人工审核（见 `MARKET_REGIME_AI_INTERFACE_v0.1.md`）。 |
| 3 | **不写数据库**、不改 `exports/` / `contracts/` / `schema.sql`、不改任何既有 artifact。 |
| 4 | **不出现** `score` / `ranking` / `probability` / `prediction` / `signal`（校验器 R9 / V8 强制）。 |
| 5 | **不参与** Structural Status —— `market_regime` 只作 supplementary context。 |
| 6 | Product **只读**消费，且**仅** `CANONICAL`；产品运行时不联网、不调 LLM。 |
| 7 | **Temporal Firewall**：所有 `date` 必须 `<= snapshot_date`；`AFTER_SNAPSHOT` 必须被隔离。 |

## 5. 与冻结基座的关系

本目录是 **ThreeC 1.1 新增**，**纯增量**：

- 不修改 `research/` 下任何既有目录 / artifact；
- 不修改 `research/scripts/` 既有脚本（本目录自带 `scripts/`）；
- Market Snapshot **不进入** `exports/timeline_export_v1.json`（独立 Artifact）。
