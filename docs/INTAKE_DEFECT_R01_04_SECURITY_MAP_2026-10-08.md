# INTAKE_DEFECT_R01_04_SECURITY_MAP_2026-10-08.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **导入缺陷的根因、修正与验证**（★ 已修正数据 + 导入器） |
> | 触发 | K 线对照发现「记录峰值不被已登记标的证实」→ 追到**标的清单** → 追到**导入器的映射表** |
> | 检查器 | `research/scripts/check_intake_security_map_v0_1.py`（可复现，覆盖全部 6 个 R01 包） |
> | 修正 | 导入器 `import_r01_04_canonical_v0_2.py`（v0_1 保留）+ 数据侧 `fix_r01_04_security_map_v0_1.py` |
> | 影响 | **7 个对象**（DB 内 **5 条 campaign**） |

---

## 一、缺陷：导入器的映射表相对**包自己的声明**循环错位

`import_r01_04_canonical_v0_1.py` 里的 `SEC_CANON`（intake security_id → canonical 标的）
与包自己的 `research/intake/packages/R01-04/securities.json` **对不上**：

```
SEC016–SEC031 共 16 项，整体**旋转 3 位**：
  导入器 SEC016 = 美的集团   ← 包 SEC019
  导入器 SEC017 = 格力电器   ← 包 SEC020
  ...
  导入器 SEC029 = 科沃斯     ← 包 SEC016（绕回）
  导入器 SEC030 = 石头科技   ← 包 SEC017
  导入器 SEC031 = 小熊电器   ← 包 SEC018
```

**SEC001–SEC015 两边完全一致** —— 错位只发生在后半段。

---

## 二、后果：错的标的被挂到 campaign 上

| candidate | campaign | 包声明（应挂） | 错位后（实际挂） |
|---|---|---|---|
| `008` | `C-2020-CONS-WHITE-GOODS` | **美的 · 格力 · 海尔 · 老板电器** | 老板电器 · 爱美客 · 华熙生物 · 朗姿 |
| `009` | `C-2019-CONS-AESTHETICS` | **爱美客 · 华熙生物 · 朗姿** | 珀莱雅 · 贝泰妮 · 万辰集团 |
| `010` | `C-2020-CONS-BEAUTY-CN` | **珀莱雅 · 贝泰妮** | 盐津铺子 · 乖宝宠物 |
| `011` | `C-2024-CONS-TRADE-IN` | **美的 · 格力 · 海尔 · 老板电器** | 老板电器 · 爱美客 · 华熙生物 · 朗姿 |
| `012` | `C-2023-CONS-VALUE-RETAIL` | **万辰集团 · 盐津铺子** | 中宠股份 · 科沃斯 |
| `007` | `RC-2020-CONS-SMALL-APPLIANCE` | 科沃斯 · 石头科技 · 小熊电器 | （**未挂载**，不在 `campaigns` 表） |
| `013` | `RC-2024-CONS-PET-FOOD` | 乖宝宠物 · 中宠股份 | （**未挂载**，同上） |

**这一条解释了此前所有孤立发现**：

- 「**家用电器** campaign 的标的清单里一个白电龙头都没有」（`WHITE-GOODS` / `TRADE-IN`）
- 「**美妆** campaign 登记的是宠物食品 + 零食」（`BEAUTY-CN`）
- 「两条不同 campaign 的清单**完全相同**」（`WHITE-GOODS` = `TRADE-IN`）
- 「`GAMBO` 乖宝宠物**上市于 2023-08**，而 `BEAUTY-CN` 止于 2022-12」——
  `GAMBO` 本属 `013`（宠物食品，2024），被错位挂到了 `BEAUTY-CN`

---

## 三、★★ 为什么结构校验抓不到

```
validate_db.py         PASS
validate_timeline_export.py  PASS
intake validator       PASS
```

**它们查的是「形状」** —— 标的合法、日期合法、外键完整、角色合法。
**没有一处检查「映射是否忠于 intake 包自己的声明」。**

> 这与本日更早的教训是同一条：**校验器会愉快地放过语义错误。**
> 上一次是「错误日期全 PASS」，这一次是「错标的全 PASS」。

---

## 四、全库排查：**只有 R01-04 有缺陷**

| 包 | 结论 |
|---|---|
| `R01-01` | `MERGED` ✓ —— 唯一差异是包内 SEC008/SEC017（拓斯达）**有意合并**，导入器有注释说明 |
| `R01-02` | `MATCH` ✓ |
| `R01-03` | `MATCH` ✓ |
| **`R01-04`** | ★ **`MISMATCH` 16 项** |
| `R01-05` | `MATCH` ✓ |
| `R01-06` | `MATCH` ✓（含 1 个无 ticker 的指数，检查器已适配 `None`） |

> 检查器两处**自身**的假阳性也已修：① 包写 `688981.SH`、导入器写 `688981`（同一标的，需去后缀）；
> ② 指数类 ticker 位置是 `None` 而非字符串。

---

## 五、修正

### 5.1 数据侧（`fix_r01_04_security_map_v0_1.py`）

- **期望值从包推导**（`securities.json` 的 ticker → canonical `security_id`），**不写死手工表**
- 备份 → dry-run → 事务应用 → **逐条与包对照验证**
- 结果：**删除 13 行 · 新增 13 行**；`campaign_securities` 总行数 **197 → 197**（不变）
- `role` 保持 `representative`（导入器硬编码如此，属既有约定，不在本次范围）

### 5.2 导入器侧（`import_r01_04_canonical_v0_2.py`）

- 按包声明逐条改正 `SEC016–SEC031`；**v0_1 逐字节保留**
- 用同一检查器验证：**31 条全部与包一致**

### 5.3 导出重出（零回归）

```
campaigns 53 → 53 · research_candidates 27 → 27 · securities 261 → 261
★ 变化的 campaign：恰好 5 条（全部消费族），且**仅 security_ids 字段**
★ research_candidates：零变化
```

---

## 六、★★ 修正暴露的**第二个缺陷**（在对照器里）

修正后 `C-2023-CONS-VALUE-RETAIL` 登记了万辰集团，却仍报「差 **997 日**」。

查证：万辰集团原始价 `high` 峰为 **2025-09-01 = 214.93**（与记录峰值 2025-08-29 差 **3 日**）。

**根因**：`build_kline_alignment_v0_2.py` 对 **开放式 campaign**（`end_date = None`）用
`e or s` 回退到 **start**，窗口被截成 `[start−60, start+30]` —— **算出的峰必然错**。

> ★ 这与我在 2026-10-07 修过的**抓取器**是同一个 bug（那次把抓取窗口截断在 start）。
> **当时只修了抓取侧，没检查对照侧。** 修正后 `C-2024-SEMI-MEMORY` 亦由「不适用」变为「已证实」。

---

## 七、结果

```
K 线证实：CONFIRMED 32 → 34 · UNCONFIRMED 5 → 3
清单核对：NAMED_ONLY_EXPLAINS 2 → 0   ← 清单错位**完全消解**
```

**5 条修正后的 campaign 全部为 `CONFIRMED`，最近标的差 0–3 日**：

| campaign | 状态 | 最近标的 |
|---|---|---|
| `C-2020-CONS-WHITE-GOODS` | `CONFIRMED` | `HAIER` 海尔智家（差 0 日） |
| `C-2019-CONS-AESTHETICS` | `CONFIRMED` | `BLOOMAGE` 华熙生物（差 0 日） |
| `C-2020-CONS-BEAUTY-CN` | `CONFIRMED` | `PROYA` 珀莱雅（差 0 日） |
| `C-2024-CONS-TRADE-IN` | `CONFIRMED` | `GREE` 格力电器（差 0 日） |
| `C-2023-CONS-VALUE-RETAIL` | `CONFIRMED` | `WANCHEN` 万辰集团（差 3 日） |

**剩余 3 个 `UNCONFIRMED`** 全部是「**参照物未界定 + 记录里 0 条依据**」：
`C-2016-CONS-BAIJIU-UPGRADE`（差 15 日）· `C-2016-HIEQ-CONSTR`（差 17 日）· `C-2019-AD`（差 84 日）。
—— 这三条**不是映射问题**，是记录本身缺依据，需另一轮研究。

---

## 八、教训

1. **「包声明」与「导入器映射」是两份可以各自漂移的真相** —— 必须有一条检查把它们对起来。
   该检查已固化为 `check_intake_security_map_v0_1.py`，**建议纳入 intake 验收**。
2. **结构校验查形状，不查语义。** 今天两次踩到：错日期全 PASS、错标的全 PASS。
3. **修一个 bug 时要问「同一个错误还在别处吗」。** 开放式窗口的 bug 在抓取器修过，
   却在对照器里留了一个月 —— 直到这次才暴露。

---

## 九、诚实记录

- 本报告**已修正数据**（这是本日唯一一次改动 canonical 关联表），但：
  - **只改 `campaign_securities`**，未改任何 campaign 的日期 / 名称 / 主题 / 事件 / 证据
  - 备份在 `/tmp/cycle_research.db.bak3`
  - 修正前后 `campaign_securities` 行数不变（197）
  - `validate_db` / `validate_timeline_export` 均 PASS
- `named_not_listed`（点名但未登记）清单**不宜再当缺陷信号** ——
  它包含大量「证据里顺带提到别家标的」的情形；**真正的判据是 `NAMED_ONLY_EXPLAINS`**（现为 0）。

---

*导入缺陷根因与修正 · 2026-10-08*
