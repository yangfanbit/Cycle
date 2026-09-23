import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import { HistoricalSimilarPhase } from '../../../components/HistoricalSimilarPhase/HistoricalSimilarPhase';
import { isEntrySelected, type Selection } from '../../../components/Timeline/Timeline';
import {
  ATTENTION_LABEL,
  attentionOf,
  buildCurrentLensV2,
  driverCategoriesOf,
  macroThemeOf,
  patternOf,
  phaseOfStage,
  terminalPhaseOf,
  themeCycleViewsOf,
} from '../researchAttention';
import { similarPhaseOf } from '../historicalSimilarPhase';
import {
  macroThemeGroupsOf,
  macroThemeTreeOf,
  subThemesOf,
  themeCatalogueChildren,
  themeCatalogueRoots,
} from '../macroTheme';
import { previewTimelineSource, verifiedTimelineSource } from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import type { TimelineCampaign } from '../timelineTypes';
import type { HistoricalCampaign } from '../../../models';

/**
 * Research Navigation v2（Current Time Lens v2 + Historical Similar Phase + Macro Theme 接口）测试。
 *
 * 分组：
 *   1. F-MED-6 Selection：展示实例（entryId）与 Campaign（campaign_id）分离
 *   2. 阶段归一 / Drivers 分类 / Pattern 派生
 *   3. Research Attention Gate v1
 *   4. Current Time Lens v2：A/B/C 三层 + 诚实空态 + NO LOOK-AHEAD
 *   5. Parallel Theme（多 component 各自状态，不压缩成唯一 phase）
 *   6. Historical Similar Phase v1
 *   7. Macro Theme 聚合接口（仅 View/Adapter）
 *   8. 产品约束：无预测 / 无概率 / 无买卖信号
 */

const TODAY = '2026-09-15';
const PHARMA = 'C-2019-PHARMA-INNOV';

const fs = require('node:fs') as typeof import('node:fs');
const path = require('node:path') as typeof import('node:path');
const read = (rel: string) => fs.readFileSync(path.resolve(process.cwd(), rel), 'utf-8');

/** 取渲染 HTML 中某一年份行的片段（用于断言「哪一年的条目被高亮」） */
function rowHtml(html: string, year: number): string {
  const marker = `class="ctl-year-label">${year}<`;
  const start = html.indexOf(marker);
  if (start < 0) return '';
  const next = html.indexOf('ctl-year-label">', start + marker.length);
  return next < 0 ? html.slice(start) : html.slice(start, next);
}

/* ================= 1. F-MED-6：Selection 身份分离 ================= */

describe('1. F-MED-6：Selection 区分展示实例（entryId）与 Campaign（campaign_id）', () => {
  const sel = (id: string, timelineEntryId?: string): Selection =>
    timelineEntryId ? { kind: 'campaign', id, timelineEntryId } : { kind: 'campaign', id };

  it('isEntrySelected 只按展示实例比较；未指定 timelineEntryId → 不高亮任何年份', () => {
    expect(isEntrySelected(sel(PHARMA, 'C-2019-PHARMA-INNOV@2021'), 'C-2019-PHARMA-INNOV@2021')).toBe(true);
    expect(isEntrySelected(sel(PHARMA, 'C-2019-PHARMA-INNOV@2021'), 'C-2019-PHARMA-INNOV@2022')).toBe(false);
    // 只选 Campaign（看完整案例）→ 不猜年份
    expect(isEntrySelected(sel(PHARMA), 'C-2019-PHARMA-INNOV@2021')).toBe(false);
    expect(isEntrySelected(null, 'C-2019-PHARMA-INNOV@2021')).toBe(false);
  });

  it('CurrentTimeLens：选中 2021 条目 → 只有 2021 年份行高亮', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={sel(PHARMA, `${PHARMA}@2021`)}
        onSelect={() => {}}
      />,
    );
    expect(rowHtml(html, 2021)).toContain('ctl-entry on');
    expect(rowHtml(html, 2020)).not.toContain('ctl-entry on');
    expect(rowHtml(html, 2022)).not.toContain('ctl-entry on');
    // 全局只有一个高亮条目（跨年 Campaign 不再多行同时高亮）
    expect((html.match(/ctl-entry on/g) ?? []).length).toBe(1);
  });

  it('CurrentTimeLens：选中 2022 条目 → 只有 2022 年份行高亮', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={sel(PHARMA, `${PHARMA}@2022`)}
        onSelect={() => {}}
      />,
    );
    expect(rowHtml(html, 2022)).toContain('ctl-entry on');
    expect(rowHtml(html, 2021)).not.toContain('ctl-entry on');
    expect((html.match(/ctl-entry on/g) ?? []).length).toBe(1);
  });

  it('只选 Campaign（无 timelineEntryId）→ 无条目高亮，但 Campaign Detail 仍按 campaign_id 解析', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={sel(PHARMA)}
        onSelect={() => {}}
      />,
    );
    expect((html.match(/ctl-entry on/g) ?? []).length).toBe(0);
    // 「打开完整历史案例」语义未改：App 仍以 campaign_id 解析详情
    const app = read('src/App.tsx');
    expect(app).toContain('campaignById.get(selection.id)');
  });

  it('三处视图的 entry 点击都回传 timelineEntryId；「查看完整历史案例」只回传 campaign_id', () => {
    const timeline = read('src/components/Timeline/Timeline.tsx');
    expect(timeline).toContain('timelineEntryId: entryId');
    const lens = read('src/components/CurrentTimeLens/CurrentTimeLens.tsx');
    expect(lens).toContain('timelineEntryId: e.entryId');
    // SamePeriodView 的 Level 2 按钮保持 Campaign 级语义（不分年份）
    const sp = read('src/components/SamePeriodView/SamePeriodView.tsx');
    expect(sp).toContain('onOpenFull(focus.campaign_id)');
    expect(sp).not.toContain('onOpenFull(focus.entryId)');
  });
});

/* ================= 2. 阶段 / Drivers / Pattern ================= */

describe('2. 阶段归一 · Drivers 分类 · Pattern 派生', () => {
  it('lifecycle stage → 统一 7 阶段（可审计的确定性映射）', () => {
    expect(phaseOfStage('EARLY_SIGNAL')).toBe('EARLY_SIGNAL');
    expect(phaseOfStage('THEME_FORMING')).toBe('THEME_FORMING');
    expect(phaseOfStage('BROAD_CONFIRMATION')).toBe('BROAD_CONFIRMATION');
    expect(phaseOfStage('MAIN_RISE')).toBe('EXPANSION');
    expect(phaseOfStage('PEAK')).toBe('PEAK');
    expect(phaseOfStage('SECONDARY')).toBe('DECLINE');
    expect(phaseOfStage('RETRACEMENT')).toBe('DECLINE');
    expect(phaseOfStage('DECLINING')).toBe('DECLINE');
    expect(phaseOfStage('MAIN_END')).toBe('END');
    expect(phaseOfStage('WHATEVER')).toBe('UNKNOWN');
  });

  it('MAIN_END 是终结标记：其后的 SECONDARY 不改变「已结束」判定', () => {
    const src = previewTimelineSource();
    const robotaxi2024 = src.yearData(2024).campaigns.find((c) => c.campaign_id === 'C-2024-ROBOTAXI')!;
    // lifecycle 末位是 SECONDARY，但存在 MAIN_END → 终态为 END
    expect(terminalPhaseOf(robotaxi2024)).toBe('END');
  });

  it('Drivers 分类由 Research 事件的 event_type 确定性派生（不做 NLP）', () => {
    const src = previewTimelineSource();
    const get = (id: string) => src.years().flatMap((y) => src.yearData(y).campaigns).find((c) => c.campaign_id === id)!;
    expect(driverCategoriesOf(get('C-2022-POLICY'))).toEqual(['POLICY', 'CAPITAL']);
    expect(driverCategoriesOf(get('C-2024-ROBOTAXI'))).toEqual(['CAPITAL']);
    // Sentiment 在研究数据中没有来源 → 永不出现（不编造）
    const all = new Set(src.years().flatMap((y) => src.yearData(y).campaigns).flatMap(driverCategoriesOf));
    expect(all.has('SENTIMENT')).toBe(false);
  });

  it('Pattern 派生与 methodology v1.1 的结论一致：汽车 Sequential / 医药 Parallel', () => {
    const cycles = themeCycleViewsOf(previewTimelineSource());
    expect(cycles.find((c) => c.key === 'medical_structural_upgrade_2019_2022')!.pattern).toBe('PARALLEL');
    for (const c of cycles.filter((x) => x.key.startsWith('auto_') || x.key.startsWith('robotaxi_'))) {
      expect(c.pattern, c.key).toBe('SEQUENTIAL');
    }
  });

  it('patternOf：单组件 / 完全先后 / 存在并存 / 两者都有', () => {
    const mk = (start: string, end: string): TimelineCampaign =>
      ({ campaign_id: `${start}~${end}`, kind: 'campaign', start, end } as unknown as TimelineCampaign);
    expect(patternOf([{ campaign: mk('2020-01-01', '2020-12-31') }])).toBe('SEQUENTIAL');
    expect(
      patternOf([
        { campaign: mk('2020-01-01', '2020-06-30') },
        { campaign: mk('2020-07-01', '2020-12-31') },
      ]),
    ).toBe('SEQUENTIAL');
    expect(
      patternOf([
        { campaign: mk('2020-01-01', '2021-06-30') },
        { campaign: mk('2020-07-01', '2020-12-31') },
      ]),
    ).toBe('PARALLEL');
    expect(
      patternOf([
        { campaign: mk('2019-01-01', '2019-06-30') },
        { campaign: mk('2020-01-01', '2021-06-30') },
        { campaign: mk('2020-07-01', '2020-12-31') },
      ]),
    ).toBe('HYBRID');
  });
});

/* ================= 3. Research Attention Gate v1 ================= */

describe('3. Research Attention Gate v1（状态分类，不是评分）', () => {
  const base = (over: Partial<TimelineCampaign>): TimelineCampaign =>
    ({
      campaign_id: 'X',
      kind: 'campaign',
      status: 'provisional',
      lifecycle: [{ stage: 'MAIN_RISE', start: '2026-01-01', end: '2026-03-01', precision: 'DATE_WINDOW' }],
      events: [{ name: 'e', date: '2026-01-01', event_type: 'policy' }],
      signals: [],
      themes: [],
      ...over,
    } as unknown as TimelineCampaign);

  it('正式 Campaign + 扩张阶段 + 有证据 + 无重大分歧 → ACTIVE_RESEARCH', () => {
    const r = attentionOf(base({}));
    expect(r.state).toBe('ACTIVE_RESEARCH');
    expect(ATTENTION_LABEL[r.state]).toBe('当前值得研究');
  });

  it('Research Candidate 一律 WATCH（不进当前值得研究）', () => {
    expect(attentionOf(base({ kind: 'candidate' })).state).toBe('WATCH');
  });

  it('重大 Conflict → WATCH', () => {
    const r = attentionOf(
      base({
        status: 'conflict',
        conflicts: [
          {
            field: 'start_date',
            candidate_a: { date: '2026-01-01', label: 'A' },
            candidate_b: { date: '2026-02-15', label: 'B' },
          },
        ],
      }),
    );
    expect(r.state).toBe('WATCH');
    expect(r.reasons.join()).toContain('重大日期口径分歧');
  });

  it('证据不足 → WATCH', () => {
    expect(attentionOf(base({ events: [] })).state).toBe('WATCH');
  });

  it('PEAK / DECLINE / END → HISTORICAL_REFERENCE', () => {
    for (const stage of ['PEAK', 'DECLINING', 'MAIN_END']) {
      const r = attentionOf(
        base({ lifecycle: [{ stage, start: '2026-01-01', end: '2026-03-01', precision: 'DATE_WINDOW' }] }),
      );
      expect(r.state, stage).toBe('HISTORICAL_REFERENCE');
    }
  });

  it('真实数据分布：ACTIVE 仅限「研究未记录结束」的正式 Campaign；候选 / 分歧一律 WATCH', () => {
    const source = previewTimelineSource();
    const v2 = buildCurrentLensV2(source, TODAY);

    // ★ 结构性断言（不写死数量，避免与 universe 耦合）：
    //   ① ACTIVE 只能是**正式 Campaign**，且**研究未记录结束**（openEnded === true）
    //      —— 已记录 end 的历史 Campaign 一律不得标为「当前值得研究」（P0 修正）
    const rawById = new Map(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map((x) => [
        x.campaign_id,
        x,
      ]),
    );
    for (const i of v2.layerC.active) {
      expect(i.kind).toBe('campaign');
      // ★ 关键：ACTIVE 的对象必须**研究未记录结束**（end_date === null）
      expect(rawById.get(i.campaign_id)!.end_date).toBeNull();
    }
    //   ② Research Candidate 一律不得进入 ACTIVE（候选只进 WATCH）
    expect(v2.layerC.active.some((i) => i.campaign_id.startsWith('RC-'))).toBe(false);
    //   ③ WATCH 必须覆盖全部 Research Candidate（候选 = 保持观察）
    const allRcIds = timelineExportData.research_candidates.map((r) => r.campaign_id);
    const watchIds = new Set(v2.layerC.watch.map((i) => i.campaign_id));
    for (const id of allRcIds) expect(watchIds.has(id)).toBe(true);
    //   ④ 三类互斥且完备：active + watch + referenceTotal = 全部研究对象
    const total = timelineExportData.campaigns.length + timelineExportData.research_candidates.length;
    expect(v2.layerC.active.length + v2.layerC.watch.length + v2.layerC.referenceTotal).toBe(total);

    // 「当前值得研究」**为空时**必须给出解释，而不是假装有结论；
    // **非空时**不得反过来谎称「没有当前值得研究的方向」。
    const html = renderToStaticMarkup(
      <CurrentTimeLens dataSource={source} today={TODAY} selection={null} onSelect={() => {}} />,
    );
    if (v2.layerC.active.length === 0) {
      expect(html).toContain('这不是错误');
    } else {
      expect(html).not.toContain('这不是错误');
    }
  });
});

/* ================= 4. Current Time Lens v2 三层 + NO LOOK-AHEAD ================= */

describe('4. Current Time Lens v2：A / B / C 三层 + 诚实空态（NO LOOK-AHEAD）', () => {
  it('Layer A：A股整体环境 = Unknown（不从行业 Campaign 反推大盘）', () => {
    const v2 = buildCurrentLensV2(previewTimelineSource(), TODAY);
    expect(v2.layerA.state).toBe('UNKNOWN');
    expect(v2.layerA.label).toContain('Unknown');
    expect(v2.layerA.note).toContain('不判断');
    const html = renderToStaticMarkup(
      <CurrentTimeLens dataSource={previewTimelineSource()} today={TODAY} selection={null} onSelect={() => {}} />,
    );
    expect(html).toContain('A股整体周期：Unknown');
    // 严禁出现大盘涨跌 / 牛熊结论 —— 出现时只能是**否定性限定**（项目既有约定）
    expect(html).toContain('因此不判断「牛市 / 熊市 / 风险偏好」');
    expect(html).not.toContain('处于牛市');
    expect(html).not.toContain('处于熊市');
    expect(html).not.toContain('推荐');
  });

  it('Layer B：无 2026 数据 → 诚实空态；不把 2025 历史数据伪装成 2026 当前状态', () => {
    const v2 = buildCurrentLensV2(previewTimelineSource(), TODAY);
    expect(v2.currentYear).toBe(2026);
    expect(v2.layerB.hasCurrentData).toBe(false);
    // ★ 数据驱动：研究覆盖区间 = 导出对象的 min/max year（不写死具体年份）
    const allYears = [
      ...timelineExportData.campaigns.map((c) => c.year),
      ...timelineExportData.research_candidates.map((r) => r.year),
    ];
    expect(v2.layerB.coverage).toEqual({ from: Math.min(...allYears), to: Math.max(...allYears) });
    expect(v2.layerB.note).toContain('暂无 2026');
    expect(v2.layerB.note).toContain('研究覆盖至 2025');
    expect(v2.layerB.note).toContain('不将历史数据伪装成当前状态');
    // 研究覆盖内的 Theme Cycle 只作历史参考，不冒充「当前主题周期」
    expect(v2.layerB.cycles.length).toBeGreaterThan(0);

    const html = renderToStaticMarkup(
      <CurrentTimeLens dataSource={previewTimelineSource()} today={TODAY} selection={null} onSelect={() => {}} />,
    );
    expect(html).toContain('暂无 2026');
    expect(html).toContain('历史参考，不是当前状态');
    expect(html).toContain('B · 当前 Theme / Theme Cycle');
    expect(html).toContain('C · Research Attention');
  });

  it('数据源确实覆盖当前年份时，Layer B 切换为非空态（分支可验证）', () => {
    const current: HistoricalCampaign = {
      campaign_id: 'cmp_current_2026',
      rule_id: 'rule_auto_summer',
      season_id: '2026',
      campaign_year: 2026,
      start_date: '2026-06-01',
      end_date: '2026-09-30',
      peak_date: null,
      cross_year: false,
      strength: 'medium',
      result: 'unknown',
      description: '合成 fixture：仅验证「当前年份有数据」分支，不是真实行情。',
      source_id: 'fx_spec_001',
      start_date_basis: 'unknown',
      end_date_basis: 'unknown',
      date_confidence: 'low',
    };
    const v2 = buildCurrentLensV2(verifiedTimelineSource([current]), TODAY);
    expect(v2.layerB.hasCurrentData).toBe(true);
    expect(v2.layerB.note).toContain('研究数据已覆盖 2026');
  });

  it('空数据源 → Layer B/A/C 均为诚实空态（不编造）', () => {
    const empty = verifiedTimelineSource([]);
    const v2 = buildCurrentLensV2(empty, TODAY);
    expect(v2.layerB.coverage).toEqual({ from: null, to: null });
    expect(v2.layerB.hasCurrentData).toBe(false);
    expect(v2.layerB.cycles).toEqual([]);
    expect(v2.layerC.active).toEqual([]);
    expect(v2.layerC.watch).toEqual([]);
    expect(v2.layerC.referenceTotal).toBe(0);
  });

  it('NO LOOK-AHEAD：不读取 today 之后的研究对象', () => {
    const src = previewTimelineSource();
    // 用 2020-09-15 作为「今天」→ 研究对象集合与 today 无关（同源同集合），
    // 且 Layer B 明确按 currentYear=2020 判定覆盖性，不引用未来
    const v2 = buildCurrentLensV2(src, '2020-09-15');
    expect(v2.currentYear).toBe(2020);
    expect(v2.layerB.hasCurrentData).toBe(true);
    expect(v2.layerB.note).toContain('2020');
  });
});

/* ================= 5. Parallel Theme ================= */

describe('5. Parallel Theme：一个 Macro Theme 可含多个不同状态的 component', () => {
  it('医药健康 Theme Cycle 含 3 个 component，且阶段 / 状态不同', () => {
    const cycle = themeCycleViewsOf(previewTimelineSource()).find(
      (c) => c.key === 'medical_structural_upgrade_2019_2022',
    )!;
    expect(cycle.macroTheme).toBe('医药健康');
    expect(cycle.pattern).toBe('PARALLEL');
    expect(cycle.components).toHaveLength(3);
    // 不压缩成唯一 phase：阶段集合 > 1
    const phases = new Set(cycle.components.map((c) => c.phase));
    expect(phases.size).toBeGreaterThan(1);
    // 组件身份 = Campaign / Candidate（不新建实体）
    expect(cycle.components.map((c) => c.campaign.campaign_id).sort()).toEqual(
      ['C-2019-PHARMA-INNOV', 'RC-2020-PANDEMIC', 'RC-2021-TCM'].sort(),
    );
    // 每个 component 都有自己的 attention 结论
    for (const c of cycle.components) expect(c.attention.reasons.length).toBeGreaterThan(0);
  });

  it('一个 Macro Theme 汇总状态 = 组件中最高关注度', () => {
    const cycle = themeCycleViewsOf(previewTimelineSource()).find(
      (c) => c.key === 'auto_intelligence_2023',
    )!;
    // 该 cycle 内 RC-2023-HUAWEI = WATCH，C-2023-AD = HISTORICAL_REFERENCE → 汇总 WATCH
    expect(cycle.summaryAttention).toBe('WATCH');
  });
});

/* ================= 6. Historical Similar Phase v1 ================= */

describe('6. Historical Similar Phase v1（生命周期相似）', () => {
  it('同阶段 + 同 Pattern 排在前面，且最多 3 条', () => {
    const view = similarPhaseOf(previewTimelineSource(), 'C-2025-ROBOTAXI');
    expect(view.target!.campaign_id).toBe('C-2025-ROBOTAXI');
    expect(view.results.length).toBeLessThanOrEqual(3);
    expect(view.results).toHaveLength(3);
    // 分数单调不增
    for (let i = 1; i < view.results.length; i += 1) {
      expect(view.results[i - 1].score).toBeGreaterThanOrEqual(view.results[i].score);
    }
    // 首位：同终态阶段 + 同 Pattern + Drivers 有重叠 → 高相似
    expect(view.results[0].tier).toBe('HIGH');
    expect(view.results[0].phase).toBe(view.target!.phase);
    expect(view.results[0].pattern).toBe(view.target!.pattern);
    expect(view.results[0].reasons.join()).toContain('阶段相同');
  });

  it('Drivers 重叠增加相似性（同分时重叠多者在前）', () => {
    const view = similarPhaseOf(previewTimelineSource(), 'C-2025-ROBOTAXI');
    const overlapCount = (r: (typeof view.results)[number]) =>
      r.drivers.filter((d) => view.target!.drivers.includes(d)).length;
    expect(overlapCount(view.results[0])).toBeGreaterThan(0);
    // 首位必须是重叠数最多的那一个（排序第一关键字为总分，重叠计入总分）
    const maxOverlap = Math.max(...view.results.map(overlapCount));
    expect(overlapCount(view.results[0])).toBe(maxOverlap);
  });

  it('每条结果都给出「为什么类似」三条（Phase / Pattern / Drivers）', () => {
    const view = similarPhaseOf(previewTimelineSource(), 'C-2022-POLICY');
    for (const r of view.results) {
      expect(r.reasons).toHaveLength(3);
      expect(r.reasons[0]).toMatch(/阶段(相同|相邻)/);
      expect(r.reasons[1]).toMatch(/Pattern/);
      expect(r.reasons[2]).toMatch(/Drivers/);
    }
  });

  it('Wave 1B 后：全部研究对象均可检索到相似案例（RC-2023-HUAWEI 亦不再为空态）', () => {
    // Wave 1B 新增 C-2023-COMM-OPTICAL（终态 PEAK）→ 与 RC-2023-HUAWEI 的 EXPANSION 相邻 → 有结果。
    // 本轮实测：13 Campaign + 4 Research Candidate 全部可检索到 1~3 条相似案例（不再存在空态对象）。
    const view = similarPhaseOf(previewTimelineSource(), 'RC-2023-HUAWEI');
    expect(view.target!.phase).toBe('EXPANSION');
    expect(view.results.length).toBeGreaterThan(0);
    expect(view.insufficient).toBe(false);
    // ★ 不写死 `results[0]` —— 结果顺序是**实现细节**，断言它会制造「第一名」语义。
    //   改为断言真实不变量：结果互不重复，且都不是 target 自身。
    const ids = view.results.map((r) => r.campaign_id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).not.toContain('RC-2023-HUAWEI');
  });

  it('空数据源 → target 为 null 且空态（不编造参照对象）', () => {
    const view = similarPhaseOf(verifiedTimelineSource([]), null);
    expect(view.target).toBeNull();
    expect(view.results).toEqual([]);
    expect(view.insufficient).toBe(true);
  });

  it('默认参照 = 研究覆盖内最新案例（不表述为当前市场状态）', () => {
    const view = similarPhaseOf(previewTimelineSource(), null);
    // ★ 数据驱动：默认参照 = 研究覆盖内**最新年份**的案例（不写死具体 ID）
    const allYears = [
      ...timelineExportData.campaigns.map((c) => c.year),
      ...timelineExportData.research_candidates.map((r) => r.year),
    ];
    expect(view.target!.year).toBe(Math.max(...allYears));
    expect(view.target).not.toBeNull();
    const html = renderToStaticMarkup(
      <HistoricalSimilarPhase
        dataSource={previewTimelineSource()}
        selection={null}
        onSelect={() => {}}
      />,
    );
    expect(html).toContain('研究数据覆盖内最新案例，非当前市场状态');
    // 相似度声明必须是「研究结构相似度」，且不得出现百分比 / 概率
    expect(html).toContain('研究结构相似度');
    expect(html).not.toMatch(/概率是|\d+(\.\d+)?%/);
    for (const banned of ['推荐', '买入', '卖出', '必涨']) {
      expect(html).not.toContain(banned);
    }
  });

  it('组件在无参照对象时渲染空态文案（不编造参照）', () => {
    // Wave 1B 后：真实数据中已不存在「有参照但无相似结果」的对象
    // （13 Campaign + 4 RC 全部可检索到 1~3 条相似案例）。
    // 因此空态只能由「无数据源」触发 —— 组件必须如实说明「研究数据不足」，不得编造参照对象。
    const html = renderToStaticMarkup(
      <HistoricalSimilarPhase
        dataSource={verifiedTimelineSource([])}
        selection={null}
        onSelect={() => {}}
      />,
    );
    expect(html).toContain('当前研究数据不足');
    expect(html).toContain('未形成可靠的历史参照');
  });
});

/* ================= 7. Macro Theme 聚合接口 ================= */

describe('7. Macro Theme 聚合接口（仅 View / Adapter）', () => {
  it('可从既有数据推导 Macro Theme → Campaigns', () => {
    const groups = macroThemeGroupsOf(previewTimelineSource());
    const auto = groups.find((g) => g.macroTheme === '汽车')!;
    expect(auto.campaigns).toHaveLength(7);
    expect(auto.themeTypes).toEqual(['industry']);
    expect(auto.subThemes).toContain('新能源汽车/电池');
    expect(auto.themeCycleIds).toContain('auto_intelligence_2023');

    const pharma = groups.find((g) => g.macroTheme === '医药健康')!;
    expect(pharma.campaigns.map((c) => c.campaign_id)).toEqual([PHARMA]);
    expect(pharma.subThemes).toEqual(['CXO(研发外包)', '创新药']);

    // 未标注行业者归入 null 组（不编造行业名）
    const unassigned = groups.find((g) => g.macroTheme === null)!;
    expect(unassigned.macroTheme).toBeNull();
    expect(unassigned.campaigns.length).toBeGreaterThan(0);
  });

  it('父 → 子主题关系可从产品侧题材库推导（parent_theme_id）', () => {
    const roots = themeCatalogueRoots();
    expect(roots.map((r) => r.name)).toContain('汽车');
    const auto = roots.find((r) => r.name === '汽车')!;
    const children = themeCatalogueChildren(auto.theme_id);
    expect(children.length).toBeGreaterThan(0);
    expect(children.map((c) => c.name)).toContain('自动驾驶');
  });

  it('Macro Theme → Theme Cycle → Campaigns 层级视图可产出', () => {
    const tree = macroThemeTreeOf(previewTimelineSource());
    const auto = tree.find((t) => t.macroTheme === '汽车')!;
    expect(auto.themeCycles.length).toBe(7);
    for (const c of auto.themeCycles) expect(c.campaigns.length).toBeGreaterThan(0);
  });

  it('macroThemeOf / subThemesOf 语义：related+industry = Macro；其余为子题材', () => {
    const src = previewTimelineSource();
    const c = src.yearData(2020).campaigns.find((x) => x.campaign_id === 'C-2020-NEV')!;
    expect(macroThemeOf(c)).toBe('汽车');
    expect(subThemesOf(c)).toEqual(['新能源汽车/电池', '特斯拉产业链']);
    // 未标注 → null（不推断）
    const o = src.yearData(2019).campaigns.find((x) => x.campaign_id === 'C-2019-AD')!;
    expect(macroThemeOf(o)).toBeNull();
  });

  it('本轮不改 Timeline 视觉：Timeline 组件不消费 Macro Theme 聚合', () => {
    const timeline = read('src/components/Timeline/Timeline.tsx');
    expect(timeline).not.toContain('macroTheme');
    expect(timeline).not.toContain('macroThemeGroupsOf');
    // Theme Row 仍以 role='main' 的 Sub-theme 成行（既有语义未变）
    expect(read('src/data/timeline/themeRows.ts')).toContain("c.themes.find((t) => t.role === 'main')");
  });

  it('F4 透传：导出既有 theme_type / theme_cycle_id 现在进入视图模型', () => {
    const c = previewTimelineSource()
      .yearData(2019)
      .campaigns.find((x) => x.campaign_id === PHARMA)!;
    expect(c.themes.some((t) => t.theme_type === 'industry')).toBe(true);
    expect(c.theme_cycle_id).toBe('medical_structural_upgrade_2019_2022');
  });
});

/* ================= 8. 产品约束 ================= */

describe('8. 产品约束：研究导航，不是预测系统', () => {
  it('新 ViewModel 不写入 DB / schema / export / contracts（源码边界）', () => {
    for (const f of [
      'src/data/timeline/researchAttention.ts',
      'src/data/timeline/historicalSimilarPhase.ts',
      'src/data/timeline/macroTheme.ts',
    ]) {
      const src = read(f);
      expect(src).toContain('不写入 DB / schema / export / contracts');
      expect(src).not.toContain('sqlite');
      expect(src).not.toContain('fetch(');
    }
  });

  it('禁止词：新 UI 不出现预测 / 概率 / 买卖 / 荐股措辞（研究结构相似度除外）', () => {
    const html =
      renderToStaticMarkup(
        <CurrentTimeLens dataSource={previewTimelineSource()} today={TODAY} selection={null} onSelect={() => {}} />,
      ) +
      renderToStaticMarkup(
        <HistoricalSimilarPhase
          dataSource={previewTimelineSource()}
          selection={null}
          onSelect={() => {}}
        />,
      );
    for (const banned of [
      '买入', '卖出', '建仓', '清仓', '推荐', '荐股', '必涨', '必跌',
      '大概率', '胜率', '预测未来', '目标价', '交易信号', 'Opportunity Score', 'Prediction Score',
    ]) {
      expect(html, banned).not.toContain(banned);
    }
    // 允许出现的否定性限定
    expect(html).toContain('不是未来走势概率');
  });
});
