# 2024 Robotaxi Point-in-Time Review（Pilot 1-C1.2）

> 对象：`C-2024-ROBOTAXI`。本轮只做 **Point-in-Time 识别** 与 **Campaign 结束边界** 校准，**不修改** campaigns / annual_status / rule，**不写入** verified / Cycle。
> 术语：`Historical Leader Equal-Weight Index` = 事后选定的 5 只核心股票等权归一化指数（base 07-08=100, raw close 信号口径）。**这是历史复盘指数，不是板块指数、也不是投资者当时可获取的收益。**
> 识别表：`research/c2/point_in_time_leaders.csv`；原始行情沿用腾讯 GTIMG。

---

## 1. Historical Leader Set

| security | name | identified_date | type | confidence | 备注 |
|---|---|---|---|---|---|
| DAZHONGTONG | 大众交通 | 2024-07-08 | market_breadth | medium | 7/8 放量+6.12%、7/9 一字板；早段可观察异动（主题归因低置信） |
| JINJIANG | 锦江在线 | 2024-07-09 | media_identified | medium | 7/9 无人驾驶概念一字连板 |
| XINGYUYUDA | 星网宇达 | 2024-07-09 | media_identified | medium | 7/9 无人驾驶概念一字连板 |
| TIANMAI | 天迈科技 | 2024-07-10 | media_identified | high | 证券时报 7/10 报道 20cm 涨停（「E-2024-05」） |
| JINLONG | 金龙汽车 | 2024-07-12 | media_identified | medium | 7/12 涨停（无人驾驶客车/萝卜快跑） |

**这一集合是行情结束后回看得到的**，供复盘，不当作 Point-in-Time Basket。

## 2. Point-in-Time Identification（三个时间切片）

规则：进入某切片 = 该股 `identified_date ≤ 切片日`，且有当日/此前公开证据；**不因后来涨幅倒推**。

### 07-08（Slice A）
- **point_in_time_basket = unavailable**。
- 无可靠"当时公开主题识别"：仅大众交通有 market_breadth 观测性异动（低置信），不足以认定为已确立的无人驾驶 theme basket。
- 结论：07-08 时点**无法可靠预建篮子**。

### 07-10（Slice B）
- **point_in_time_basket = { 大众交通, 锦江在线, 星网宇达, 天迈科技 }（4 只）**。
- 依据：大众（07-08/09）、锦江（07-09）、星网（07-09）、天迈（07-10 证券时报点名）。
- 金龙 **不在** B（07-12 才被公开识别）。

### 07-15（Slice C）
- **point_in_time_basket = { 大众, 锦江, 星网, 天迈, 金龙 }（5 只）**。
- 金龙 07-12 识别纳入；至此与 Historical Leader Set 一致（时间上刚好重合是巧合，识别顺序有先后）。

## 3. Start Reassessment

- **07-08 = 起势日**（EW 基准 100）：事实为"指数起点"，不足以独立证明广泛启动。
- **07-09 = 首个广泛确认日**：EW 单日 +10.1%（Historical Leader EW Index），5 只中 4 只在当日/两日大幅上涨。
- 但两点时序 bias 警示：
  1. 该 +10.1% 的"5只"含事后才识别的金龙（07-12）与天迈（07-10）——**若用完整 Historical Leader Set 证明 07-09 广泛启动，属 look-ahead**。
  2. 按 Point-in-Time 口径，07-09 当时能确认的 basket 仅是 07-08 已知信息（≈只有大众 + 低置信观察），**严格讲 07-09 的"广泛"在当时尚不足以确证**。
- **结论**：candidate `start=07-08`/首个广泛确认 `07-09` 仍成立，但**必须标注为 retrospective 增强**；当时可确认的仅有大众（market_breadth）。

## 4. Peak

- **Historical Leader EW Index 峰值 = 2024-08-05（234.8）**，07-30 为中途高（230.3）。
- Peak 判断基于 raw close（signal），未改变。
- 个股峰值：大众 08-05(11.22)、锦江 07-30(16.07)、金龙 08-15(19.79)、星网 08-02(23.84)、天迈 07-18(41.41)。

## 5. First Decline

- **首个显著回撤 = 2024-08-06**（EW 234.8→214.1，-8.8%）。
- 保留为 **First Decline**；它不是最终 End（见后）。

## 6. Secondary Rally

- **08-13~08-15 二次上攻**：金龙 08-15 创新高 19.79（个股 secondary）、EW 回升至 213.1。
- **08-21~08-22 再度活跃**：锦江（08-22 13.99）、星网走强，EW 回到 207.6/207.3。
- **板块等权从未收复 08-05 峰值**：secondary 均为**部分个股/板块反弹**，非完整二次主升。

## 7. Final End Candidate

尾段跟踪（EW raw，base 100）：08-06 214.1 → 08-08 198.1 → 08-12 196.0 → 08-15 213.1 → **08-21 207.6（重新活跃）→ 08-22 207.3 → 08-23 197.8（明显跳水）** → 08-26 191.8 → 08-28 188.8 → 08-29 185.4 → 08-30 188.6。

- **08-23 是比 08-06 更强的 Final End Candidate**：
  - 08-21/08-22 的重新活跃被 08-23 一根明显跳水打断（单日 -4.6%）。
  - **08-23 之后 08-26→08-30 板块等权持续走弱、无任何集体回升/新高**，且个股不再同步（锦江回落、金龙下行、大众横盘）→ 主题**失去持续主导地位**，转入 decline/tail。
- 判定逻辑（非"单日跌X%"）：综合 ①核心样本走弱 ②无新高 ③无新集体催化 ④个股不再同步 → **End Candidate ≈ 08-23**；08-06 仅是 First Decline。
- **这只影响"结束边界的候选"，本轮不改 Campaign end_date（07-31），留待人工。**

## 8. Historical vs Point-in-Time

| | Historical Leader Set | Point-in-Time Basket |
|---|---|---|
| 定义 | 行情结束后回看确认的核心/高表现样本 | 截至某日已有公开证据识别的主题样本 |
| 用途 | 复盘、归因 | 模拟实时研究 |
| 本案例 | 5 只（07-18 后全确认） | 07-08: unavailable；07-10: 4 只；07-15: 5 只 |
| 风险 | 事后选择/幸存者 | look-ahead 最小，但样本小、覆盖不全 |

- 两者**不得混用**：122.4%（07-08→07-31，5 只等权调整后累计）语义为"**历史核心样本五股等权累计收益**"，**不是** Robotaxi 板块平均收益，**更不是**普通投资者当时可获得的收益。

## 9. Look-Ahead Bias Risks

- **主要残留**：①start/首个确认日的"广泛"是事后增强；②"peak=08-05"、"first decline=08-06"、"final end≈08-23" 都是 retrospective 判定；③Historical Leader Set 是后验选择。
- **已防护**：Point-in-Time 切片只使用 `identified_date ≤ 切片日` 的证据；金龙（07-12）不进 07-08/07-10；未把 7/30 之后文章倒推 7/10。
- **不能把以上任何一个日期当作"当时已知催化剂"** 用于更早时点。

## 10. Remaining Unknowns

1. **Point-in-Time Start 难以确证**：07-08/07-09 当时公开信息不足，basket 无法在 07-08 可靠建立（`unavailable`）。
2. **Final End 存在多候选**：First Decline 08-06、二次反弹 08-15、重新活跃 08-21-22、跳水 08-23 —— 需要人工定夺"失去主导地位"的确切日，取决于是否把 08-23 后算 decline/tail。
3. `AUTO_SW`（申万801880）仍 unavailable；516110 仅限 2024 行业代理，不可用于 2018–2020。
4. Breadth 仍 unavailable（无 2024 历史成分快照）。
5. Point-in-Time 识别基于公开报道 + 盘面推断，个别 identified_date 为近似（如大众 07-08 market_breadth），需人工复核日报/公告时间戳。

---

*数据：`python scripts/point_in_time_robotaxi.py`（§15 测试全 PASS）；行情原始见 `_calib_raw.json`。/渲染见 `point_in_time_leaders.csv`。*