# ROADMAP.md — 阶段规划

> 规则：未来功能记录在这里，而不是提前实现在代码里。

## V1（已完成）— 历史地图 / 数据化经验 / 时间轴

- 全年四层时间轴（事件 / 季节性规律 / 历史题材 / 状态）
- TODAY 标记与年份切换
- 跨年行情完整建模与延续渲染
- Pre-heat 四态相位（NOT_ACTIVE / PRE_HEAT / ACTIVE / ENDED）
- Rule / Campaign 详情抽屉
- 未来关注窗口（7/30/60/90 天）
- 10 条候选规律种子数据（全部 candidate，来源可追溯）
- 治理文档体系（AGENTS.md + docs/）

## V1.6（当前进行中）— Cycle Timeline MVP + Real Research Export Integration

> 2026-09-13 启动。Research 与 Timeline MVP 并行：不再等待全部人工 Review 后才开发 UI。

- Timeline Data Adapter 层（src/data/timeline/）：`TimelineDataSource` 统一接口
  - `verified` 数据源：来自 data/verified/（allCampaigns / events / themes / securities）
  - `preview` 数据源：Cycle-Research 真实导出 timeline_export_v1.json（canonical Contract
    v1.0，commit 49797cc），2018—2025 全量；不进入 data/verified、不污染 allCampaigns
- 365 天全年时间轴：按真实日期比例布局（月份长度不同），非 12 等分
- Campaign 生命周期视觉主体：Early Signal（淡显，前置观察）→ 主升（实色）→ 峰值（标记）→
  高位回撤（条纹）→ 退潮（虚线纹理）→ 结束；形状 / 线型 / 透明度 / 标签区分，不单靠颜色
- 数据状态视觉区分：VERIFIED 实色 / PROVISIONAL·PREVIEW 虚线淡化 / CONFLICT 警示标记
- URL Preview：`?preview=1` 启用，顶部「开发预览数据」横幅（含 Research commit）；默认生产数据
- 年份切换接入数据源（不硬编码年份）；TODAY 标记沿用 Asia/Shanghai 基准
- CampaignDetail 支持 Research Preview 数据并明确标注「非正式 Verified 数据」
- 提前观察中性表达：如「历史观察窗口将在约 N 天后进入」，禁止买卖建议用语

### V1.6.1（已完成，2026-09-13）— Real Research Export Integration

- 接入 Cycle-Research canonical Contract `timeline_export_version = "1.0"`（冻结版
  research/methodology/timeline_export_contract_v1.md，Research commit 4bbe257）：
  - `TimelineExportV1` 类型与 Contract 11 字段白名单对齐；旧字段（export_version /
    source_project / purpose）不再兼容，Cycle 内不维护第二套 v1 格式
  - `validateTimelineExportV1`：只验证 Cycle 实际消费的部分（顶层白名单 / version /
    status 一致性 / candidate 无生产 status / 引用完整性 / signals XOR 归属 /
    CONFLICT ⇔ conflicts），不重写完整 Research Validator
- 真实导出替换手工 fixture：`src/data/timeline/data/timeline_export_v1.json`
  （逐字节拷贝，Cycle 只消费不修改）；`timelinePreview.ts` 静态 import JSON
  （无运行时网络请求，静态 PWA 不变）
- Campaign / Candidate / Signal / Event / Security 完整映射：
  - 正式 Campaign：research_status → Timeline 状态（PROVISIONAL→provisional /
    CONFLICT→conflict / VERIFIED→verified）
  - Research Candidate（RC- 前缀）：kind = candidate，status 只为 preview / conflict，
    永不 verified；与正式 Campaign 并列（非"候选→正式"升级关系）
  - Signals：EARLY_SIGNAL 早于正式起点 → TimelineEarlySignal（淡显 / 虚线）；
    研究信号是"值得观察"，不是交易信号
  - Events / Securities：顶层扁平数组 + owner 引用，Adapter 建 lookup 解析
    （不要求嵌套在 Campaign 内）
  - first_decline_date 作回撤起点；缺省以 peak→end 中点近似（仅渲染）
- Conflict 结构化显示：保留 candidate A / B 双方口径（2022 C-2022-POLICY start
  04-27 vs 05-23；2024 C-2024-ROBOTAXI peak / end 双分歧），不自行选一个
- 年份自动推导：campaigns + research_candidates + events → 连续区间 2018—2025
  （2018 反例年份可见但无 Campaign，空态合法，不编造行情）
- Timeline UI：研究事件行（Research Export 具体日期事件）；Candidate RC 徽章；
  空态文案「该年份当前无正式 Historical Campaign 数据」
- CampaignDetail：结构化分歧（⚠ field：A date（label） vs B date（label））、
  关联事件（日期 + 类型 + 角色）、研究信号（类型 + 置信度）、Candidate 标记、
  openEnded（候选观察中，end 为年末近似）
- App：researchEvents 透传；预览横幅带 Research 源 commit；初始年份回退
  （preview 源 2018—2025、当前 2026 → 打开即显示 2025）

### V1.6 后续（待人工 Review 后）

- Research 导出升级 v1.1+ 时同步 Adapter（Contract 变更回 Research 项目）
- preview → provisional → verified 数据源演进（Timeline UI 不变）
- verified 层逐年录入后，生产首页逐步从空态过渡到真实历史数据

## V1.5 — 历史规律核验与季节性验证

### 第零阶段（已完成，2026-09-12）：Preflight 数据语义清理

- 跨年结构示例（cmp_media_2026_2027）迁出生产层 → tests/fixtures/campaignFixtures.ts
- 方案 A：candidate 层不再承载未核验 HistoricalCampaign，线索仅存 Evidence；
  生产层行情聚合 allCampaigns = verifiedCampaigns
- Timeline 第三层改为「已核验历史行情」+ 空态文案
- ValidationRecord 审计字段修正：created_at（建记录）/ reviewed_at 可空（无核验人不得有核验日期）
- 市场日期基准 marketTodayISO（Asia/Shanghai），App / Pre-heat / Radar 统一接入
- Source URL 补登记（src_exp_001）

### 第一阶段（已完成）：核验基础建设

- 核验规范文档 docs/HISTORICAL_VALIDATION.md（Campaign / 启动结束定义 / 结果分类 / 人工优先）
- Evidence / ValidationRecord / RawExcerpt 模型与数据
- data/ 四层数据目录（raw / candidate / verified / validation）
- Campaign 扩展字段：peak_date、date basis、date_confidence
- 3 条 Pilot 核验数据骨架（汽车 L1 / 广电 L1 / 大消费 L0，全部 not_tested）
- 数据完整性测试扩展

### 第二阶段（待人工 Review 后启动）：3 条 Pilot 历史事实核验

- 夏季汽车 / 年底广电 / 国庆后大消费的逐年人工核验（L0/L1 → L2）
- 核验产出的历史事实迁入 data/verified/，CHANGELOG 留痕
- 广电 2021—2023、大消费各子方向的事实补齐（以核验到的事实为准）

### 待治理（V1.5 后续）：Event 日期精度治理

Preflight 审计结论（2026-09-12，仅记录，本轮未改数据）：

| Event | 当前建模 | 审计结论 |
|-------|---------|---------|
| 春节 evt_spring_festival | variable，dates 登记至 2028 | 逐年精确 ✅；2028 之后回退 approx_md（已有 approximate 机制，可接受） |
| 全国两会 evt_two_sessions | range 03-03 → 03-11 固定 | **近似被当作确定**：实际会期逐年公告（如近年多为 03-04 / 03-05 开幕），应改 variable + 逐年登记，或标注 approximate |
| 一季报披露期 evt_q1_report | range 04-01 → 04-30 | 法定披露期 ✅ |
| 五一 evt_labor_day | fixed 05-01 | 事件日固定 ✅（放假安排变动不影响事件本日） |
| 中报披露期 evt_interim_report | range 07-01 → 08-31 | 法定披露期 ✅ |
| 国庆节 evt_national_day | range 10-01 → 10-07 | 基本精确；个别年份长假安排与中秋连休（如 8 天假）会偏离 7 天固定段，近似可接受，可在 description 说明 |
| 三季报披露期 evt_q3_report | range 10-08 → 10-31 | 法定披露期近似 ✅（披露截止 10-31 精确） |

处理要求：两会会期是唯一"近似日期被当成确定事实"的明显问题；
后续将其改为 variable 或加 approximate 标注，不得大规模改动其他 Event。

### 第三阶段：统计验证（L3）

- 接入历史行情数据，计算可追溯统计量：sample_count / launch_date_median / launch_date_std /
  average_duration / excess_return / repeat_rate / seasonality_score
- 统计方法论必须写入 statistics.methodology
- 统计结果表述为"历史统计特征"，禁止外推为未来承诺（见 PRODUCT.md「前瞻性分析 ≠ 确定性预测」）
- 评估 Rule.status 拆分为 evidence_status / verification_status 双字段（映射见 DATA_GOVERNANCE.md）
- 数据源迁移：TS 模块 → SQLite（待业务模型经 Pilot 验证稳定后）

## V2 — 当前状态 / Future Opportunity Radar

- Observation 录入 UI（人工观察，不得直接修改 Rule）
- 实时市场状态（行情接入在本阶段才允许评估）
- 雷达规则化升级

## V3 — 历史规律 vs 当年偏离

- 当年实际走势与历史窗口的偏离度对比
- 「今年是否重演」的情景分析框架（前瞻性分析，不是确定性预测）
- 历史相似案例检索、当前状态与历史条件的分布对比

## V4 — 个人投资研究工作台

- 个性化观察池
- 通知（仅在本阶段评估）
- 多来源研究材料管理

## 未来可能加入（均需届时单独评估授权）

- 实时行情、资金流、市场异动
- 个性化观察池
- 通知
- 组件级测试与 E2E 框架
