# R02_03_CANONICALIZATION_PLAN_v0_1.md

> | 项 | 值 |
> |---|---|
> | 性质 | **canonicalization 前置判定**（独立性闸门 + 导入方案）· **尚未写库** |
> | 依据 | `docs/R02_03_REVIEW_v0_1.md`（八种结果）· `theme_campaign_separation_v1.md`（Q1–Q5）· `macro_theme_primary_related_v0_1.md`（R1–R5）· `research_model_v1_0.md` |
> | 日期 | 2026-10-10 |
> | 结论 | **4 条候选进入 canonical**（4 个新 Campaign）· **5 条不进入** |

---

## 一、进入 / 不进入

| candidate | 审查结果 | 是否进入 canonical |
|---|---|---|
| `R02-COAL-001` 2021 动力煤 | `ACCEPT_WITH_CHANGES` | ✅ **进入** |
| `R02-POWER-002` 2021 绿电 | `ACCEPT_WITH_CHANGES` | ✅ **进入** |
| `R02-VACCINE-002` 2023 春季甲流 | `ACCEPT_WITH_CHANGES` | ✅ **进入** |
| `R02-MEDIA-001` 2023 AI+传媒 | `ACCEPT_WITH_CHANGES` | ✅ **进入** |
| `R02-COAL-002` 煤炭高股息 | `DEFER` | ❌ 留 intake |
| `R02-MEDIA-002` 2018 版号周期 | `DEFER` | ❌ 留 intake |
| `R02-POWER-001` 2015 新电改 | `INSUFFICIENT` | ❌ 留 intake |
| `R02-VACCINE-001` 2022 夏季流感 | `INSUFFICIENT` | ❌ 留 intake |
| `R02-POWER-003` 2022 虚拟电厂 | `OBSERVATION_ONLY` | ❌ 留 intake（可作观察记录） |

**→ 历史宇宙 80 → 84 个对象（53 → 57 Campaign）** —— 若全部按方案写入。

---

## 二、Campaign Independence Gate（Q1–Q5）

### 组 A ★ 同时间重叠：`COAL-001`（2021-08~11）↔ `POWER-002`（2021-09-07~09-28）

> 依据：规则 4「**同一时间 ≠ 同一个 Campaign**」+ 方法学 R5「时间重叠 ≠ 必须合并，但必须**分别证明**独立性」

| Q | 判定 | 依据 |
|---|---|---|
| **Q1** 独立注意力中心 | **是** | 煤炭板块 vs 电力/绿电板块；交易逻辑不同：**供给缺口 + 价格暴涨** vs **电价市场化 + 消纳预期** |
| **Q2** 独立代表标的 | **是** | 中国神华 / 陕西煤业 / 兖矿能源 vs 三峡能源 / 京能电力 / 银星能源 —— **零重叠** |
| **Q3** 独立持续性 | **是** | 煤炭约 2.5 个月；绿电约 3 周，各自有独立持续时间 |
| **Q4** 独立生命周期 | **是** | 煤炭：`MAIN_RISE` → `RETRACEMENT`（政策干预为转折）；绿电：`MAIN_RISE`（end 未界定） |
| **Q5** Residual Test | **是** | 去掉煤炭段，绿电段仍能独立解释；去掉绿电段，煤炭段仍完整 |

**→ 多数为「是」：两个独立 Campaign 成立。** 且 `POWER-002` 的 `end` 未界定 → 记 `OPEN_ENDED`（既有 6 条开放式 Campaign 的先例）。

★ 两者共享的只是**宏观背景**（2021 能耗双控 / 限电）—— 那是**共同环境**，不是共同 Campaign。

### 组 B ★ 同族跨年：`VACCINE-002`（2023-02~04）↔ 库内 `RC-2020-PANDEMIC`

| Q | 判定 | 依据 |
|---|---|---|
| Q1 | **是** | 2020 新冠（一次性疫情事件）vs 2023 季节性流感（可预期年度高发）—— 机制不同 |
| Q2 | **是** | 代表标的完全不同 |
| Q3 | **是** | 相隔 3 年，各自独立 |
| Q4 | **是** | 生命周期各自可描述 |
| Q5 | **是** | 互为独立 |

**→ 独立成立。** 且 `RC-2020-PANDEMIC` 是 **Research Candidate**，不是 Campaign，本就不构成重复。

### 组 C `VACCINE-001` ↔ `VACCINE-002`

- `VACCINE-001` 已判 `INSUFFICIENT`（无一手周报、无 peak/end）→ **本轮不建**。
- ★ **该边界问题因此不触发**：规则 3「不同时间 ≠ 不同 Campaign」要求**正面证明独立性**，
  而 001 连自身结构都不完整 —— 没有可比较的对象。**待 001 补齐证据后再判**。

### 组 D ★ 同期不同族：`MEDIA-001`（2022-11~2023-09）↔ 库内 `C-2023-COMM-OPTICAL`（光模块，2023）

> 审查曾提出：「2023 年 AI 主题同时驱动电子 / 通信 / 计算机，传媒段为何可分离？」

| Q | 判定 | 依据 |
|---|---|---|
| Q1 | **是** | 传媒 = **AI 应用落地**（内容生产）；光模块 = **AI 算力基建**。叙事不同 |
| Q2 | **是** | 三七互娱 / 光线传媒 / 中文在线 vs 光模块厂商 —— **零重叠** |
| Q3 | **是** | 各自独立持续 |
| Q4 | **是** | 各自独立生命周期 |
| Q5 | **是** | 去掉任一段，另一段仍自洽 |

**→ 独立成立。** 共享的只是「AI」这个**上位叙事**，不是同一个 Campaign。

### 组 E 与同族既有对象的时间重叠

实测：`煤炭`（新）与 `电力（运营端）`（新）为**新族**，无同族既有对象；
`流感疫苗` 属 `医药健康`，2023 年同族既有 `C-2023-PHARMA-GLP1`（减重/GLP-1）——
**不同 Sub-theme、不同标的、不同机制** → 规则 4 支持并存。
`文化传媒` 为全库零覆盖 → 无冲突。

**→ 无 `MERGE`、无 `DUPLICATE`。**

---

## 三、逐候选 canonicalization 方案

| # | canonical_id | 标题 | main / related | start | peak | end |
|---|---|---|---|---|---|---|
| 1 | `C-2021-RES-COAL` | 2021 年动力煤供需缺口与保供稳价干预 | `煤炭/main` + `资源/related` | `2021-08-01` | **`2021-10-19`** | `2021-11-30` |
| 2 | `C-2021-POWER-GREEN` | 2021 年绿色电力交易试点与新能源运营商 | `绿电 / 新能源运营商/main` + `电力（运营端）/related` | `2021-09-07` | **`2021-09-28`** | **`NULL`（OPEN_ENDED）** |
| 3 | `C-2023-PHARMA-FLU` | 2023 年春季甲流高发驱动的流感概念 | `流感疫苗/main` + `医药健康/related` | `2023-02-20` | `2023-03-20` | `2023-04-15` |
| 4 | `C-2023-MEDIA-AI` | 2023 年 AI 主题驱动的传媒板块 | `文化传媒/main` | `2023-03-31` | **`NULL`（未界定）** | `2023-07-31` |

★ **ID 命名**沿用既有格式 `C-<YYYY>-<DOMAIN>-<SLUG>`（对照 `C-2024-RES-GOLD-CB` · `C-2023-PHARMA-GLP1` · `C-2021-NEV`）。

### 3.1 ★★ peak 参照物声明（审查要求，必须落库）

| canonical_id | peak | **参照物** | **K 线证实状态** |
|---|---|---|---|
| `C-2021-RES-COAL` | 2021-10-19 | **政策事件**（发改委干预） | **`NOT_APPLICABLE`** |
| `C-2021-POWER-GREEN` | 2021-09-28 | **政策事件**（绿电交易启动） | **`NOT_APPLICABLE`** |
| `C-2023-PHARMA-FLU` | 2023-03-20 | **行业指标**（流感活动高峰） | **`NOT_APPLICABLE`** |
| `C-2023-MEDIA-AI` | NULL | **未界定** | — |

> ★★ 依据 `AGENTS.md` §5.1 硬语义边界：参照物**不是股价**时，K 线证实状态为
> **`NOT_APPLICABLE`**（K 线不是合适的检验工具），**不得**记为 `UNCONFIRMED`。
> 参照物声明写入 `campaign_date_observations.notes` + `campaigns.start_date_basis/end_date_basis`。

### 3.2 其它字段

| canonical_id | classification | result | date_confidence | 备注 |
|---|---|---|---|---|
| `C-2021-RES-COAL` | `theme_campaign` | `positive` | `medium` | start/end 为 `DATE_WINDOW` → 取窗口端点，`basis` 说明为窗口 |
| `C-2021-POWER-GREEN` | `theme_campaign` | `positive` | `medium` | end 开放式 |
| `C-2023-PHARMA-FLU` | `event_driven` | `positive` | `medium` | 驱动为季节性公共卫生事件 |
| `C-2023-MEDIA-AI` | `theme_campaign` | `positive` | `low` | peak 未界定；行情侧全为二手 |

★ 全部 `result = positive` 是**如实**的（四段都是上涨行情）；
**不因此**说明「该方向必然有机会」—— 失败的段（`MEDIA-002` 下行段）留在 intake。

---

## 四、★ 需要新增的 taxonomy 行（**1 条**，与导入同批提交）

| theme_id | name | type | parent | 用于 |
|---|---|---|---|---|
| `TH-POWER-OP-GREEN` | **`绿电 / 新能源运营商`** | `concept` | `TH-POWER-OP` | `C-2021-POWER-GREEN` 的 `main` |

**依据**：用户 2026-10-09 指令「**电力 细分 根据市场炒作过的概念/板块进行区分**」——
把该段记为 `电力（运营端）/main` 会丢掉「绿电」这个**当年真实被炒作的概念名**。

★ 其余候选名（`动力煤` / `焦煤` / `虚拟电厂` / `电力体制改革` / `游戏` / `影视` / `出版` / `流感` / `抗流感` …）
**本轮不新增行** —— 它们对应的候选**未进入 canonical**，为其建行属**为整齐而造行**
（规则 6）。待相应候选补足证据后再加。

★ `煤炭` 与 `流感疫苗` 已在 taxonomy 轮次建好，**无需再加**。

---

## 五、`rule_id` 处置（已决）

实测：**53 / 53 个既有 Campaign 都有 `rule_id`**（`research_rules`，10 条规则，对应各族的「历史观察窗口」）。

| canonical_id | `rule_id` | 理由 |
|---|---|---|
| `C-2021-RES-COAL` | **`rule_resources`**（复用） | 同族（煤炭挂 `资源` 下） |
| `C-2023-PHARMA-FLU` | **`rule_pharma_upgrade`**（复用） | 同族 |
| `C-2021-POWER-GREEN` | **`rule_power_operation`（新建）** | `rule_power_equipment` 是**制造端**，机制不同，**不得复用** |
| `C-2023-MEDIA-AI` | **`rule_media`（新建）** | 新族，无对应规则 |

### 为什么这样定

1. **保持 53/53 的既有惯例** —— 不引入 `rule_id = NULL` 的例外（那会造出「一半有规则、一半没有」的新不一致）。
2. ★ **新规则以 `status = 'candidate'` 建立**，`description` 明确写
   「**观察窗口未经核验**，不得据此推断季节性」。
   依据：`research_rules.status` 本就允许 `candidate` / `weak` / `confirmed` 三档；
   而 R02-03 包**明确记载季节性「未取得可复现证据」**
   （`R02-MEDIA-Q002` / `R02-POWER-Q003`）。
   → **不得**为了让规则看起来完整而写成 `confirmed` —— 那是**编造研究结论**。
3. 复用的两条规则**同族**，符合 `base_pattern` 语义，不虚增族数（方法学 R2）。

★ **这是本次导入唯一需要额外判断的地方**，其余全部有既有先例可循。

---

## 六、导入将写入什么（下一轮的施工范围）

| 表 | 新增行数（估） | 说明 |
|---|---|---|
| `sources` | 约 20 | 仅 4 条进入候选所用到的来源（非全包 32 条） |
| `evidences` | 约 13 | 同上 |
| `securities` | 9 | 煤炭 3 + 电力 3 + 疫苗 3（媒体 3 中若有重复则去重） |
| `campaigns` | **4** | 见 §三 |
| `campaign_themes` | 6 | 见 §三（1+2+2+1） |
| `campaign_evidences` | 约 13 | 桥表 |
| `campaign_securities` | 9 | 桥表 |
| `campaign_phases` | 6 | 来自候选 `lifecycle`（`MAIN_RISE` / `RETRACEMENT`） |
| `campaign_date_observations` | 12 | start/peak/end × 4，含**参照物声明** |
| `themes` | **1** | 见 §四 |
| `research_rules` | **0 或 2** | 见 §五（未决） |

★ **不写入**：`events` / `campaign_events`（候选未提供事件实体，证据已覆盖）。

### 导入后必须跑的验证

1. `validate_db` —— 必须仍为 **PASS**（且不新增警告）
2. 重出 `exports/timeline_export_v1.json` → `validate_timeline_export` **PASS**
3. **CMTR v1**：4 个新 Campaign 的 `themes` 必须全部 `RESOLVED` 且落在预期根
4. **产品侧**：`macroThemeOf` 对 4 个新对象的归组 = 预期根（**注意 SF-1**）
5. 前端测试套件（若导出变化影响到快照 / 覆盖率测试）

---

## 七、风险

| # | 风险 | 处置 |
|---|---|---|
| 1 | 新增 2 个根节点，但产品仍按**字面名**归组 → 新族在地图上**渲染成灰色**（同 `航天装备`） | ★★ **SF-1（Export Contract v1.1）必须同时立项** |
| 2 | 4 段 `result` 全为 `positive` → 可能被读成「这些方向都有机会」 | 页面已常驻「计数事实、非预测」声明；且 `MEDIA-002`（下行段）留在 intake 备查 |
| 3 | `C-2021-RES-COAL` 与 `C-2021-POWER-GREEN` 同处 2021-09/10 | 已过 Q1–Q5（组 A），且规则 4 明确允许 |
| 4 | 新规则的观察窗口未经核验 | 以 `status = 'candidate'` 建立并写明「未核验」 |

---

## 八、结论

> **4 条候选具备 canonicalization 条件** —— 独立性闸门 Q1–Q5 **全部通过**，
> 方案已定到字段级（含 **peak 参照物声明** 与 **K 线连带后果**）。
>
> 待施工清单（下一轮）：**1 条新 theme 行 + 2 条新 rule 行（`status='candidate'`）
> + 4 Campaign + 9 桥表行 + 约 20 来源 / 13 证据 / 9 证券 + 12 条日期观察**。
>
> ★★ **唯一的前置配套**：**SF-1（Export Contract v1.1）** ——
> 否则新加的 `电力（运营端）` 与 `文化传媒` 在首页地图上会渲染成与「未标注」相同的灰色。

---

*canonicalization 前置判定 · R02-03 · 2026-10-10 · 尚未写库*
