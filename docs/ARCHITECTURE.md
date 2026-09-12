# ARCHITECTURE.md — 当前实际技术架构

本文描述 **现在实际存在的架构**，不是理想状态。未来规划见文末 Future Architecture。

## 技术栈

- Vite 5 + React 18 + TypeScript 5（strict）
- Vitest 2（测试，globals: true, environment: node）
- 无后端、无路由库、无状态管理库、无 CSS 框架（单一 src/styles.css + CSS 变量）
- 构建：`npm run build`（tsc -b + vite build）；开发：`npm run dev`

## 数据读取方式

- V1 数据源为 `src/data/*.ts` 类型化 TS 模块，构建期静态打包。
- `src/data/index.ts` 聚合导出并提供查询辅助（ruleById / campaignsOfRule / windowsOfRule / anchorResolver 等）。
- 无网络请求、无异步加载；所有数据同步可得。

## 组件结构

```
src/
  App.tsx                        # 头部（标题/日期/年份切换）+ Timeline + OpportunityRadar + 详情抽屉
  components/
    Timeline/Timeline.tsx        # 四层时间轴（事件/规律/历史行情/状态），hover tooltip，TODAY 竖线
    RuleDetail/RuleDetail.tsx    # 规律详情（右侧抽屉）
    CampaignDetail/CampaignDetail.tsx
    OpportunityRadar/OpportunityRadar.tsx  # 未来 7/30/60/90 天关注窗口
    labels.ts                    # 中文枚举映射 + 行业配色
  utils/
    date/dateUtils.ts            # UTC 日期运算（无 DST 误差）
    preheat/windowStatus.ts      # 窗口实例化 / 四态相位 / 跨年分段
    events.ts                    # Event 逐年解析（fixed/range/variable）
```

## 时间计算逻辑

- 全部日期运算使用 `Date.UTC`，对外格式统一 ISO `YYYY-MM-DD`；年内窗口用 `MM-DD`。
- `dayOfYearISO` / `yearFraction` 提供 0..1 年内定位，驱动时间轴横坐标。
- 相对事件窗口通过注入式 `AnchorResolver` 解析（utils 不依赖 data，避免循环依赖）。

## 跨年实现方式

- 数据层：跨年是一条完整记录（cross_year: true），见 DATA_MODEL.md。
- 计算层：`segmentForYear(start, end, year)` 将任意区间与视图年求交，产出带
  `continuesFromPrevYear` / `continuesIntoNextYear` 标记的分段；
  `windowSegmentsForYear` 对 recurring 窗口额外补算上一季跨到本年的尾段。
- 表现层：分段按行业共享配色，开口端渲染 ◂ / ▸ 延续箭头，hover 显示完整日期范围。

## Pre-heat 实现方式

- `preheatStart = start - preheat_days`。
- 相位机（computeWindowStatus）：
  - today ∈ [preheatStart, start) → PRE_HEAT
  - today ∈ [start, end] → ACTIVE
  - 本年内窗口刚结束 → ENDED
  - 其余 → NOT_ACTIVE（携带最近一次未来实例的倒计时）
- 候选年份窗口检查 today 的上一年/当年/下一年三个实例，保证 1 月能识别去年 11 月开启的跨年窗口。

## 测试方式

- 单框架：Vitest（`src/utils/__tests__/timeline.test.ts`）。
- 覆盖：日期运算、普通/跨年窗口实例化与分段、Pre-heat 四态、春节锚点逐年解析、TODAY 定位、
  年份切换无错位、种子数据完整性（来源存在、无 verified、无虚假分数、跨年示例为单条记录）。
- 组件交互（点击打开详情等）当前通过类型检查与人工验证覆盖，暂无组件级测试。

## Future Architecture（仅规划，未实现）

- 数据源迁移：TS 模块 → SQLite → PostgreSQL（字段已 snake_case 对齐）
- V1.5：历史统计计算管线，回填 Rule.statistics
- V2：Observation 录入 UI、实时市场状态接入
- 组件级测试（Testing Library）与 E2E
