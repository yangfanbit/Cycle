# C · 别名归一化 —— **设计（修正版）** v0_1

> 2026-10-12 · ThreeC Agent · **尚未实施**（合同变更需先确认）
> 原方向 C1 已获认可；但实测发现**原问题描述的前提不成立**，故先交修正后的设计。

---

## 一、★★ 前提修正：原描述不成立

原任务描述：*「`动力煤` / `游戏` / `影视` / `虚拟电厂` 查不到父主题」*。

**实测（DB `themes` 表 58 行，逐名核对）**：

| 查询名 | 在 DB `themes` 中？ | 当前 verdict |
|---|---|---|
| `动力煤` | **否**（精确、子串均无） | `none` |
| `游戏` | **否** | `none` |
| `影视` | **否** | `none` |
| `虚拟电厂` | **否** | `none` |

→ 这四个名字**从来不是库内主题** —— 它们只是 R02 系列 intake 里的
`theme_name_candidates`（**提案**），在 canonicalization 时**未被采纳**。

★ **因此「把 taxonomy 导进 export」并不能解决这四个名字** ——
taxonomy 只能回答「**库内已有的**主题的父子关系」，无法回答一个不在库内的名字。

→ 若要修这四个名字，唯一途径是**新增 taxonomy 行**（数据决策，需你授权；
且按协议 §3.4 属**独立轮次**）。而它们目前**没有任何对象挂在名下**，
为其建行 = 造出**空主题行**（「为整齐而造行」，规则 6 禁止）。

---

## 二、真正可修的缺口（实测确认）

```
半导体材料   → none        ★ 库内真实主题（concept，parent=半导体 → 根 电子）
                             但**无对象直接挂它** → 产品只能说「未覆盖」
半导体设备   → historical-only (1)      ← 有对象，正常
半导体       → historical-only (9)      ← 正常
资源         → historical-only (13)     ← 正常
```

**缺口 = 「库内主题但无直接对象」这一类查询**。产品现在无法区分三种情况：

| 情况 | 现在 | 应能说 |
|---|---|---|
| A. 库内主题，且有对象 | `historical-only` | 不变 |
| B. **库内主题，但无对象** | `none`（与「不是库内主题」**混同**） | ★「库内主题，属「电子」；该主题下暂无对象，但「电子」有 9 个」 |
| C. 不是库内主题（如 `动力煤`） | `none` | ★「该名称不在库内主题表中（库内共 58 个主题）」 |

→ 这正是 **C1 机制能交付的东西**：把**名称 → 根**解析能力交给产品，
并让「未覆盖」**变成精确陈述**而不是一个笼统的空结果。

---

## 三、设计：Contract v1.2 —— export 增加 `themes` taxonomy 段

### 3.1 Research 侧（唯一事实来源）

`batch_auto_research.py` 写盘前，从 DB `themes` 表导出**全量 taxonomy**：

```json
"themes": [
  { "theme_id": "TH-RES",      "name": "资源",  "theme_type": "industry", "parent_theme_id": null },
  { "theme_id": "TH-RES-COAL", "name": "煤炭",  "theme_type": "industry", "parent_theme_id": "TH-RES" },
  …
]
```

★ **与 v1.1 的 `macro_theme_root` 同源**（都来自 **CMTR v1** / 同一张表）——
是**唯一事实来源的延伸**，不引入第二套 taxonomy。

★ 段名用 `themes`，与既有两个段落（`campaigns` / `research_candidates` 上的
`themes` **数组字段**）**不同层级**，需在合同文档写清避免混淆；
若你更希望避免同名，可改 `taxonomy`（**我倾向 `taxonomy`**）。

### 3.2 产品侧（只读不算）

1. `timelineTypes.ts` / `timelineAdapter.ts`：透传 `taxonomy` 段
2. `directionLookup.ts`：查询名先做 **名称 → 主题** 解析（精确匹配库内主题名），
   再按「根」给出**披露信息**，**不改变命中集合**：

```
新增字段（不改 verdict 语义）：
  resolution?: {
    matchedTheme: { id, name, type } | null,
    root: { id, name } | null,
    rootObjectCount: number | null,     // 根的「大主题」层对象数
    directObjectCount: number,          // 该主题直接挂的对象数（通常 0）
  }
```

★★ **硬约束（不得违反）**：
- **不得**因为「根有对象」就把根的对象算作该查询的命中 —— 那是**over-claim**。
  查 `半导体材料` 不能返回 `电子` 下全部 9 个（含面板等无关对象）。
- **不得**引入 score / 相似度 / 模糊匹配 / 别名表。
- 库内**没有**的名字，**不得**编造映射（如 `动力煤` → `煤炭`）。

### 3.3 措辞（产品可见）

| 情况 | 措辞 |
|---|---|
| B（库内主题·无对象） | 「**库内主题**（属「电子」）。该主题下暂无对象；「电子」大主题下有 9 个历史对象。」 |
| C（不在库内） | 「该名称**不在库内主题表中**（库内共 58 个主题，可换用其中之一）。」 |

---

## 四、不做（明确列出）

| # | 不做 | 理由 |
|---|---|---|
| 1 | 为 `动力煤` / `游戏` / `影视` / `虚拟电厂` **建 taxonomy 行** | 无对象挂靠 → 造空行；且属**数据决策 + 独立轮次**（协议 §3.4）。**需你授权** |
| 2 | 产品内硬编码别名表 | 造**第二套 taxonomy**；CMTR v1 明确拒绝 |
| 3 | 把 intake 的 `theme_name_candidates` 当别名导出 | 会把**未采纳的提案**变成产品可见事实 |

---

## 五、影响面与验证

```
Research：batch_auto_research.py（+taxonomy 段）· validate_timeline_export.py（接受 1.2 + 白名单）
Contract：两份副本（timeline_export_contract_v1.md · contracts/timeline_export_v1.md）→ 1.2 + §2.2
Product ：timelineTypes.ts · timelineAdapter.ts · directionLookup.ts · DirectionLookupSection（措辞）
Test    ：版本断言 1.1→1.2（含 timelineAdapter 的 validateTimelineExportV1）· 新增 B/C 两类断言
自检    ：refresh_downstream C6/C7 会检查版本一致性（合同文档 + 适配器）
```

★ **风险点（已在 v1.1 踩过）**：版本号「多处出现」—— 改 1.1 → 1.2 必须
**全局 grep** `timeline_export_version` / `'1.1'`，并跑全套测试。

---

## 六、待你决定

1. **确认修正后的范围**：做「名称 → 根」披露（第二节 B/C 两类），
   而**不是**去修那四个名字？
2. 段名用 **`taxonomy`**（我倾向）还是 `themes`？
3. 那四个名字（`动力煤` / `游戏` / `影视` / `虚拟电厂`）**是否要建行** ——
   属数据决策；若建，建议**单独一轮**，且只在有对象挂靠时建。

---

*C 设计 v0.1 · 2026-10-12 · 尚未实施*
