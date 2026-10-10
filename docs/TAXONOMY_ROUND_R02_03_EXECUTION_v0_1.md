# TAXONOMY_ROUND_R02_03_EXECUTION_v0_1.md

> | 项 | 值 |
> |---|---|
> | 性质 | **taxonomy 轮次执行记录**（R02-03 后续） |
> | 依据 | `docs/TAXONOMY_ROUND_PROPOSAL_R02_03_v0_1.md`（ThreeC Agent 建议 · 用户 2026-10-10 批准） |
> | 脚本 | `research/scripts/add_themes_r02_03_taxonomy_v0_1.py` |
> | 结果 | **DB `themes` 53 → 57 行 · 根节点 11 → 13** · **CMTR 验收 PASS** |
> | 边界 | **只 INSERT 4 行**。未改 `schema.sql` · 未改任何既有行 · 未改 Campaign / Evidence · **未动 `exports/`** |

---

## 一、做了什么

向 `research/database/cycle_research.db` 的 `themes` 表**插入 4 行**：

| `theme_id` | `name` | `theme_type` | `parent_theme_id` |
|---|---|---|---|
| `TH-POWER-OP` | **`电力（运营端）`** | `industry` | **`NULL`（根）** |
| `TH-MEDIA` | **`文化传媒`** | `industry` | **`NULL`（根）** |
| `TH-RES-COAL` | `煤炭` | `industry` | `TH-RES`（资源） |
| `TH-PHARMA-FLU` | `流感疫苗` | `concept` | `TH-PHARMA`（医药健康） |

**判定规则**（根 = 机制族；子 = 具体行业 / 题材）：
只有 `电力（运营端）` 与 `文化传媒` 的**机制轴在既有 11 个根中零代表**，故新增为根；
`煤炭`（供给收缩）与 `流感疫苗`（事件 + 季节性需求）的机制已被 `资源` / `医药健康` 代表，故为子。
★ 决定性先例：**`半导体` 在 DB 里是 `电子` 的子节点** —— 标志性不足以成为根。

**表结构无需变更**：`themes(theme_id PK, name, theme_type CHECK IN ('sector','industry','concept'), parent_theme_id → themes, description)`。
本次纯数据变更 → **未触碰 `schema.sql`**（`AGENTS.md` §4 冻结区）。

---

## 二、★★ 命名避坑（实测）

DB 里**没有**「电力」，但有「**电力设备**」（`TH-POWER`，根节点）。
**任何字面 / 子串匹配都会把「电力」误判进「电力设备」。**

→ 新根名称取 **`电力（运营端）`**，**不使用裸「电力」**。
`themes` 表本就允许括号与斜杠（既有 `CXO(研发外包)` · `减重 / GLP-1`）。

**回归测试（已通过）**：插入后裸「电力」经 CMTR 仍为 `UNRESOLVED_NAME` ——
**没有被误判进「电力设备」**。

---

## 三、CMTR v1 验收（插入前 → 插入后）

| 名称 | 插入前 | 插入后 |
|---|---|---|
| `煤炭` | `UNRESOLVED_NAME` | **`RESOLVED` → 根 `资源`** ✅ |
| `流感疫苗` | `UNRESOLVED_NAME` | **`RESOLVED` → 根 `医药健康`** ✅ |
| `文化传媒` | `UNRESOLVED_NAME` | **`RESOLVED` → 根 `文化传媒`** ✅ |
| `电力（运营端）`（全名） | `UNRESOLVED_NAME` | **`RESOLVED` → 根 `电力（运营端）`** ✅ |
| `电力`（**裸名 · 回归**） | `UNRESOLVED_NAME` | **`UNRESOLVED_NAME`** ✅（未误判） |

**CMTR 验收：PASS**

★ **仍有未解析名称，这是预期的**：各方向的其它候选名
（`动力煤` / `焦煤` / `煤炭开采` · `绿电` / `绿色电力` / `虚拟电厂` / `电力体制改革` /
`新能源运营商` · `流感` / `抗流感` / `疫苗` · `传媒` / `游戏` / `影视` / `出版` / `广告`）
**仍然 `UNRESOLVED_NAME`** —— 本次**只解决「归属根节点」**，
这些**别名 / 子题材的归一化**属**候选级改动**（下一步），**不在本轮范围**。

---

## 四、安全与回归验证（全部实测）

| 检查 | 结果 |
|---|---|
| 备份 | `.tmp/db-backup/cycle_research.before-taxonomy.db`（sha256 `ec204713…`，与改前逐字节一致） |
| `validate_db.py` | **PASS: True** + **3 条警告** —— **与改前基线完全一致**（未新增任何警告） |
| `validate_timeline_export.py` | **PASS（0 警告）** · 53 Campaign / 27 RC / 143 Event / 261 Security —— **全部未变** |
| `exports/` 是否改动 | **未改动**（本次未新增任何 `campaign_themes` 关联 → 导出不变） |
| 幂等复跑 `--apply` | 4 行全部 `SKIP(已存在且一致)` · **已插入 0 行** |
| 前端文件改动 | **0 个**（`.ts/.tsx/.js/.jsx/.css` 零改动） |
| 单事务 | 是（任一步失败即 `ROLLBACK`） |

★ 脚本的**安全设计**（`--dry-run` 可先看计划）：
幂等（同 id 不同内容 → **拒绝**而非静默改写）· **重名防护**（CMTR 的 `ambiguous_names` 会让重名主题
不可解析 → 插入前逐一校验名称尚不存在）· 父节点存在性且**必须是根** · 单事务 · 插入后自动 CMTR 验收。

---

## 五、这一轮**解除**了什么 / **没有**解除什么

### ✅ 解除

R02-03 审查 §二 的**阻塞条件**：

> 9 条候选在 taxonomy 轮次完成前，一律不得写入 canonical。

→ 四个方向现在**都有可上溯的根节点**，该阻塞**已解除**。

### ❌ 未解除（仍需按序做）

| # | 事项 | 说明 |
|---|---|---|
| 1 | **候选级改动** | R02-03 审查里 4 条 `ACCEPT_WITH_CHANGES` 的 `required_changes`（含 **peak 参照物声明**） |
| 2 | **Campaign Independence Gate Q1–Q5** | 三组边界：`COAL-001`↔`POWER-002` · `VACCINE-001`↔`002` · 与 `RC-2020-PANDEMIC` |
| 3 | 别名 / 子题材归一化 | 上表「仍未解析」的 16 个名称 |
| 4 | **SF-1：Export Contract v1.1 立项** | 产品侧 `macroThemeOf` 用 direct 口径；**新加的族会被同样错误分组** |
| 5 | `DEFER` 两条的缺失项补做 | 由 Research Agent 做 |

> ★★ **特别注意 #4**：本轮新增了 2 个根节点，但**产品仍按字面名归组** ——
> 也就是说，等候选写入 canonical 之后，`电力（运营端）` 与 `文化传媒` 在首页地图上
> **会渲染成与「未标注」相同的灰色**（同 `航天装备` 的现状）。
> **合同轮次不是可选项，是这一轮的前置配套。**

---

## 六、边界声明

- 本轮的**唯一**写入是 `themes` 表 4 行 INSERT。
- **未**改 `research/schema/schema.sql` · **未**改任何既有 theme / campaign / evidence / 日期。
- **未**把任何 R02-03 候选写入 `campaigns`（那要等候选级改动 + 独立性闸门）。
- **未**重出 `exports/`。
- **未**改 `src/**`。

---

*taxonomy 轮次执行记录 · 2026-10-10 · CMTR 验收 PASS · DB 53 → 57 行*
