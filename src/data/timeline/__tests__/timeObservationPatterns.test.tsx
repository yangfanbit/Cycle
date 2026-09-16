import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalJson from '@observation/time_observation_patterns_v0_1.json';
import {
  EMPTY_TIME_OBSERVATION_DATASET,
  buildTimeObservationLayer,
  daysFromWindow,
  defaultTimeObservationDataset,
  isValidMd,
  isMdInWindow,
  mdFractionInYear,
  nearWindowDays,
  parseTimeObservationPatterns,
  proximityOf,
  windowBandsForYear,
  type TimeObservationDataset,
} from '../timeObservationPatterns';
import { timelineEntryId } from '../entryIdentity';
import { TimeObservationLayer } from '../../../components/TimeObservation/TimeObservationLayer';

/**
 * Time-based Observation Layer 测试（Phase 7.2）。
 *
 * 覆盖四组：① 解析（正常 / 空 / 缺字段 / 非法日期 / 非法类型）·
 * ② 窗口（普通 / 月初 / 月末 / **跨年**）· ③ 当前日期关系（IN / NEAR / OUTSIDE）·
 * ④ 映射与 UI（窗口内 / 窗口外 / 空态 / 限制说明 / **不出现预测与买卖语义**）。
 *
 * 所有断言针对「历史观察窗口」语义 —— 出现概率、胜率、买卖建议即视为失败。
 */

/* ---------------- 夹具 ---------------- */

/** 构造一个最小可用的 Artifact（只填必需字段，逐条覆盖时再覆写） */
function rawPattern(over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    pattern_id: 'TOP-99',
    source_pattern_id: 'SOP-99',
    pattern_type: 'MIXED',
    title: '测试观察窗口',
    description: '测试用的历史时间聚集描述。',
    theme_key: '测试主题',
    theme_scope: '测试主题',
    anchor_type: 'EARLY_SIGNAL',
    center_date: '06-11',
    typical_window: {
      start: '05-27',
      end: '06-26',
      width_days: 31,
      method: 'Median ± 1×MAD',
      center_date: '06-11',
    },
    observations: [
      {
        year: 2024,
        date: '2024-06-11',
        md: '06-11',
        campaign_id: 'C-2024-V2X',
        title: '测试历史行情',
        kind: 'campaign',
        in_typical_window: true,
      },
    ],
    recurrence: {
      matched_count: 1,
      eligible_years: 1,
      matched_years: [2024],
      missed_years: [],
      historical_ratio: 1.0,
      label: '历史样本中的窗口复现情况（不是未来概率）',
    },
    stability: { status: 'SPLIT', drift_flag: 'STABLE', median_shift_days: 1.0 },
    data_quality: { grade: 'MEDIUM', note: '测试用数据质量说明。' },
    research_strength: { grade: 'A', rationale: '' },
    status: 'MODERATE_CANDIDATE',
    timeline_eligibility: 'TIMELINE_ELIGIBLE',
    timeline_eligible: true,
    timeline_eligibility_reason: '测试用纳入理由。',
    mechanism: {
      type: 'MIXED',
      primary_mechanism: 'CALENDAR_DRIVEN',
      note: '测试用机制说明。',
      is_lunar_driven: false,
    },
    limitations: ['样本仅测试用，不代表真实研究结论。'],
    ...over,
  };
}

function rawArtifact(patterns: Record<string, unknown>[]): Record<string, unknown> {
  return {
    artifact: 'time_observation_patterns',
    artifact_version: '0.1',
    snapshot_date: '2026-09-16',
    patterns,
  };
}

/** 正例：任何断言不要落到「非否定语境的预测 / 买卖用词」上 */
function expectNoPredictiveLanguage(markup: string) {
  for (const hard of ['推荐', '目标价', '胜率', '大概率', '买入区', '布局窗口']) {
    expect(markup, `不应出现「${hard}」`).not.toContain(hard);
  }
  for (const phrase of ['买入', '卖出', '预测', '概率']) {
    let i = markup.indexOf(phrase);
    while (i >= 0) {
      const before = markup.slice(Math.max(0, i - 12), i);
      expect(
        ['不', '非', '无', '未', '禁止'].some((n) => before.includes(n)),
        `「${phrase}」必须处于否定语境`,
      ).toBe(true);
      i = markup.indexOf(phrase, i + 1);
    }
  }
}

/* ---------------- ① 解析 ---------------- */

describe('Time Observation Pattern · 解析', () => {
  it('canonical Artifact 解析零告警，并保留四条模式', () => {
    const ds = defaultTimeObservationDataset();
    expect(ds.issues).toEqual([]);
    expect(ds.artifact).toBe('time_observation_patterns');
    expect(ds.snapshotDate).toBe('2026-09-16');
    expect(ds.patterns.map((p) => p.patternId)).toEqual([
      'TOP-01',
      'TOP-02',
      'TOP-03',
      'TOP-04',
    ]);
  });

  it('canonical：只有一条进入 Timeline，且带窗口 / 复现 / 限制说明', () => {
    const ds = defaultTimeObservationDataset();
    const eligible = ds.patterns.filter((p) => p.timelineEligible);
    expect(eligible.length).toBeGreaterThanOrEqual(1);
    for (const p of eligible) {
      expect(p.window).not.toBeNull();
      expect(p.recurrence.eligibleYears).toBeGreaterThanOrEqual(5);
      expect(p.limitations.length).toBeGreaterThan(0);
      expect(p.status).toBe('MODERATE_CANDIDATE');
    }
    const top01 = ds.patterns.find((p) => p.patternId === 'TOP-01')!;
    expect(top01.timelineEligibility).toBe('TIMELINE_ELIGIBLE');
    expect(top01.window!.label).toBe('05-27 ~ 06-26');
    expect(top01.centerDate).toBe('06-11');
    expect(top01.recurrence.matchedCount).toBe(5);
    expect(top01.recurrence.eligibleYears).toBe(7);
    expect(top01.observations).toHaveLength(7);
  });

  it('canonical：其余三条为 RESEARCH_ONLY / REJECTED，且不可进入 Timeline 展示', () => {
    const ds = defaultTimeObservationDataset();
    const others = ds.patterns.filter((p) => !p.timelineEligible);
    expect(others.length).toBeGreaterThanOrEqual(3);
    for (const p of others) {
      expect(['RESEARCH_ONLY', 'REJECTED']).toContain(p.timelineEligibility);
    }
    const model = buildTimeObservationLayer(ds, '2026-09-16');
    expect(model.views.every((v) => v.patternId === 'TOP-01')).toBe(true);
    expect(model.researchOnlyCount).toBeGreaterThanOrEqual(2);
    expect(model.rejectedCount).toBeGreaterThanOrEqual(1);
  });

  it('空数组 → 合法空数据集（不崩溃、不编造）', () => {
    const ds = parseTimeObservationPatterns(rawArtifact([]));
    expect(ds.patterns).toEqual([]);
    const model = buildTimeObservationLayer(ds, '2026-09-16');
    expect(model.views).toEqual([]);
    expect(model.current.emptyNote).toBe(ds.labels.none);
  });

  it('缺 pattern_id / 缺观测字段 → 丢弃该条并记录 issue', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([
        rawPattern({ pattern_id: undefined }),
        rawPattern({
          observations: [{ year: 2024, campaign_id: 'C-1' }, { year: 2025, date: '坏日期', campaign_id: 'C-2' }],
        }),
      ]),
    );
    expect(ds.patterns).toHaveLength(1);
    expect(ds.patterns[0].observations).toEqual([]);
    expect(ds.issues.some((i) => i.includes('缺少 pattern_id'))).toBe(true);
    expect(ds.issues.filter((i) => i.includes('丢弃一条 observation')).length).toBe(2);
  });

  it('非法窗口日期 → 窗口置空；且声明可进入 Timeline 会被降级为 RESEARCH_ONLY', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([
        rawPattern({
          typical_window: {
            start: '06-31',
            end: '07-40',
            width_days: 10,
            method: 'M',
            center_date: '06-11',
          },
        }),
      ]),
    );
    const p = ds.patterns[0];
    expect(p.window).toBeNull();
    expect(p.timelineEligibility).toBe('RESEARCH_ONLY');
    expect(p.timelineEligible).toBe(false);
    expect(ds.issues.some((i) => i.includes('窗口日期非法'))).toBe(true);
    expect(ds.issues.some((i) => i.includes('降级为 RESEARCH_ONLY'))).toBe(true);
  });

  it('非法 pattern_type → UNKNOWN（不做强制分类）', () => {
    const ds = parseTimeObservationPatterns(rawArtifact([rawPattern({ pattern_type: '季节' })]));
    expect(ds.patterns[0].patternType).toBe('UNKNOWN');
  });

  it('timeline_eligible 与 timeline_eligibility 不一致 → 记录 issue，以判定字段为准', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([rawPattern({ timeline_eligibility: 'RESEARCH_ONLY', timeline_eligible: true })]),
    );
    expect(ds.patterns[0].timelineEligibility).toBe('RESEARCH_ONLY');
    expect(ds.issues.some((i) => i.includes('不一致'))).toBe(true);
  });

  it('非 TOP- 命名空间 → 记录 issue（命名空间卫生）', () => {
    const ds = parseTimeObservationPatterns(rawArtifact([rawPattern({ pattern_id: 'SOP-99' })]));
    expect(ds.issues.some((i) => i.includes('TOP- 命名空间'))).toBe(true);
  });

  it('空数据集常量可用（诚实兜底）', () => {
    expect(EMPTY_TIME_OBSERVATION_DATASET.patterns).toEqual([]);
    expect(buildTimeObservationLayer(EMPTY_TIME_OBSERVATION_DATASET, '2026-06-12').views).toEqual([]);
  });
});

/* ---------------- ② 窗口 ---------------- */

describe('Time Observation Pattern · 窗口（含跨年）', () => {
  it('普通窗口：边界包含、窗外排除', () => {
    expect(isMdInWindow('06-11', '05-27', '06-26')).toBe(true);
    expect(isMdInWindow('05-27', '05-27', '06-26')).toBe(true);
    expect(isMdInWindow('06-26', '05-27', '06-26')).toBe(true);
    expect(isMdInWindow('05-26', '05-27', '06-26')).toBe(false);
    expect(isMdInWindow('06-27', '05-27', '06-26')).toBe(false);
  });

  it('月初窗口（06-01 起）', () => {
    expect(isMdInWindow('06-01', '06-01', '06-30')).toBe(true);
    expect(isMdInWindow('05-31', '06-01', '06-30')).toBe(false);
  });

  it('月末窗口（至 06-30）', () => {
    expect(isMdInWindow('06-30', '06-25', '06-30')).toBe(true);
    expect(isMdInWindow('07-01', '06-25', '06-30')).toBe(false);
  });

  it('跨年窗口（12-20 ~ 01-15）两端都在窗口内，年中在窗口外', () => {
    expect(isMdInWindow('12-20', '12-20', '01-15')).toBe(true);
    expect(isMdInWindow('12-31', '12-20', '01-15')).toBe(true);
    expect(isMdInWindow('01-01', '12-20', '01-15')).toBe(true);
    expect(isMdInWindow('01-15', '12-20', '01-15')).toBe(true);
    expect(isMdInWindow('06-15', '12-20', '01-15')).toBe(false);
    // 距离：01-20 距窗口末端 5 天；12-15 距窗口起点 5 天
    expect(daysFromWindow('01-20', '12-20', '01-15')).toBe(5);
    expect(daysFromWindow('12-15', '12-20', '01-15')).toBe(5);
  });

  it('窗口内距离恒为 0；普通窗口外距离 = 到最近边界', () => {
    expect(daysFromWindow('06-01', '05-27', '06-26')).toBe(0);
    expect(daysFromWindow('05-24', '05-27', '06-26')).toBe(3);
    expect(daysFromWindow('07-01', '05-27', '06-26')).toBe(5);
  });

  it('跨年窗口在年内轨道上渲染为两段（年末段 + 年初段）', () => {
    const segs = windowBandsForYear('12-20', '01-15', 2025);
    expect(segs).toHaveLength(2);
    expect(segs[0].continuesIntoNextYear).toBe(true);
    expect(segs[1].continuesFromPrevYear).toBe(true);
    expect(segs[1].left).toBe(0);
  });

  it('普通窗口在年内轨道上渲染为一段，位置与日期一致', () => {
    const segs = windowBandsForYear('05-27', '06-26', 2025);
    expect(segs).toHaveLength(1);
    expect(segs[0].continuesFromPrevYear).toBe(false);
    expect(segs[0].continuesIntoNextYear).toBe(false);
    expect(segs[0].left).toBeCloseTo(mdFractionInYear('05-27', 2025), 6);
    expect(segs[0].width).toBeGreaterThan(0);
  });

  it('非法 MM-DD 被拒绝（含伪合法日期）', () => {
    expect(isValidMd('06-11')).toBe(true);
    expect(isValidMd('02-29')).toBe(true); // 闰年基准允许
    expect(isValidMd('13-01')).toBe(false);
    expect(isValidMd('06-31')).toBe(false);
    expect(isValidMd('02-30')).toBe(false);
    expect(isValidMd('6-1')).toBe(false);
    expect(isValidMd('')).toBe(false);
  });
});

/* ---------------- ③ 当前日期关系 ---------------- */

describe('Time Observation Pattern · 当前日期关系', () => {
  const win = { start: '05-27', end: '06-26' };

  it('IN_WINDOW / NEAR_WINDOW / OUTSIDE 三态', () => {
    expect(proximityOf('06-11', win.start, win.end)).toBe('IN_WINDOW');
    expect(proximityOf('05-27', win.start, win.end)).toBe('IN_WINDOW');
    expect(proximityOf('06-26', win.start, win.end)).toBe('IN_WINDOW');
    expect(proximityOf('07-05', win.start, win.end)).toBe('NEAR_WINDOW');
    expect(proximityOf('05-20', win.start, win.end)).toBe('NEAR_WINDOW');
    expect(proximityOf('08-01', win.start, win.end)).toBe('OUTSIDE');
  });

  it('NEAR_WINDOW 边界：恰好 = 邻近缓冲天数时仍算「接近」', () => {
    const md = '07-10'; // 距 06-26 共 14 天
    expect(daysFromWindow(md, win.start, win.end)).toBe(nearWindowDays);
    expect(proximityOf(md, win.start, win.end)).toBe('NEAR_WINDOW');
    expect(proximityOf('07-11', win.start, win.end)).toBe('OUTSIDE');
  });

  it('今天落在窗口内 → current.inWindow 命中；窗口外 → emptyNote 给出诚实空态', () => {
    const ds = defaultTimeObservationDataset();
    const inside = buildTimeObservationLayer(ds, '2026-06-12');
    expect(inside.current.inWindow.map((v) => v.patternId)).toEqual(['TOP-01']);
    expect(inside.current.near).toEqual([]);
    expect(inside.current.emptyNote).toBeNull();

    const outside = buildTimeObservationLayer(ds, '2026-09-16');
    expect(outside.current.inWindow).toEqual([]);
    expect(outside.current.near).toEqual([]);
    expect(outside.current.emptyNote).toBe(ds.labels.none);
  });

  it('多条模式同时命中时不人为只保留一条（§26）', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([
        rawPattern({ pattern_id: 'TOP-81', title: '窗口 A' }),
        rawPattern({
          pattern_id: 'TOP-82',
          title: '窗口 B',
          typical_window: { start: '06-01', end: '06-20', width_days: 20, method: 'M', center_date: '06-10' },
        }),
      ]),
    );
    const model = buildTimeObservationLayer(ds, '2026-06-12');
    expect(model.current.inWindow.map((v) => v.patternId).sort()).toEqual(['TOP-81', 'TOP-82']);
    expect(model.views).toHaveLength(2);
  });

  it('排序：窗口内 → 接近 → 较远；同为窗口内时按数据质量 / 稳定性 / 样本量', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([
        rawPattern({
          pattern_id: 'TOP-71',
          title: '较远窗口',
          typical_window: { start: '01-05', end: '01-20', width_days: 16, method: 'M', center_date: '01-12' },
        }),
        rawPattern({ pattern_id: 'TOP-72', title: '窗口内' }),
        rawPattern({
          pattern_id: 'TOP-73',
          title: '接近窗口',
          typical_window: { start: '06-25', end: '07-03', width_days: 9, method: 'M', center_date: '06-29' },
        }),
      ]),
    );
    const model = buildTimeObservationLayer(ds, '2026-06-12');
    expect(model.views.map((v) => v.patternId)).toEqual(['TOP-72', 'TOP-73', 'TOP-71']);
  });
});

/* ---------------- ④ 映射 + UI ---------------- */

describe('Time Observation Pattern · 映射与 UI', () => {
  it('观测映射到 Campaign 与展示实例身份（entryId = campaign_id@年份）', () => {
    const ds = defaultTimeObservationDataset();
    const top01 = ds.patterns.find((p) => p.patternId === 'TOP-01')!;
    const obs = top01.observations.find((o) => o.year === 2024)!;
    expect(obs.campaignId).toBe('C-2024-V2X');
    expect(obs.timelineEntryId).toBe(timelineEntryId('C-2024-V2X', 2024));
    expect(obs.md).toBe('06-11');
  });

  it('今天在窗口内：渲染窗口带、复现计数与限制说明', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('时间型观察层');
    expect(html).toContain('历史观察窗口');
    expect(html).toContain('05-27 ~ 06-26');
    expect(html).toContain('当前位于历史观察窗口');
    // Level 2 摘要必须同时给出「历史复现」标签与计数（不是百分比、不是概率）
    expect(html).toContain('历史复现');
    expect(html).toContain('5 / 7 个观测年份');
    // Level 2 摘要默认展开（今天处于窗口内的最相关一条）
    expect(html).toContain('为什么值得看');
    expect(html).toContain('注意');
    expect(html).toContain('不代表今年必然重演');
    expectNoPredictiveLanguage(html);
  });

  it('今天不在窗口内：给出诚实空态文案，且不显示「当前位于」', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-09-16" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('当前没有发现处于历史时间观察窗口的模式');
    expect(html).not.toContain('当前位于历史观察窗口');
    expectNoPredictiveLanguage(html);
  });

  it('今天接近窗口：显示「接近历史观察窗口」与距离天数', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-07-05" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('接近历史观察窗口');
    expect(html).toContain('距边界');
    expectNoPredictiveLanguage(html);
  });

  it('展示年份上点出该年的研究观察起点，并可点击进入历史案例', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2024} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('tob-obs-dot');
    expect(html).toContain('2024 · 06-11');
  });

  it('窗口外年份的起点标记与窗口内标记在样式上可区分', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2022} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('tob-obs-dot outside');
  });

  it('无可用窗口 → 不渲染本层（不显示空壳）', () => {
    const ds = EMPTY_TIME_OBSERVATION_DATASET;
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toBe('');
  });

  it('全部为 RESEARCH_ONLY 时不渲染窗口行，但保留研究层说明', () => {
    const ds = parseTimeObservationPatterns(
      rawArtifact([
        rawPattern({ pattern_id: 'TOP-61', timeline_eligibility: 'RESEARCH_ONLY', timeline_eligible: false }),
      ]),
    );
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toBe('');
    expect(buildTimeObservationLayer(ds as TimeObservationDataset, '2026-06-12').researchOnlyCount).toBe(1);
  });

  it('探索性标记必须出现（样本有限 / 未人工核验）', () => {
    const ds = defaultTimeObservationDataset();
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2025} today="2026-06-12" onSelect={() => {}} dataset={ds} />,
    );
    expect(html).toContain('探索性');
    expect(html).toContain('未经行情人工最终核验');
  });
});

/* ---------------- ⑤ 研究产物卫生（产品侧能看见的红线） ---------------- */

describe('Time Observation Pattern · 产物卫生', () => {
  /** 收集 JSON 中所有对象键（只查键名，避免把「禁用字段清单」本身误判为字段） */
  function collectKeys(node: unknown, out: Set<string> = new Set()): Set<string> {
    if (Array.isArray(node)) {
      node.forEach((x) => collectKeys(x, out));
    } else if (node && typeof node === 'object') {
      for (const [k, v] of Object.entries(node)) {
        out.add(k);
        collectKeys(v, out);
      }
    }
    return out;
  }

  it('canonical 不含被禁止的字段名', () => {
    const keys = collectKeys(canonicalJson);
    for (const f of [
      'future_probability',
      'confidence_percent',
      'expected_return',
      'win_rate',
      'buy_signal',
      'sell_signal',
      'target_price',
      'seasonality_score',
    ]) {
      expect(keys.has(f), `不应出现字段 ${f}`).toBe(false);
    }
  });

  it('historical_ratio 只在 [0,1] 内，且复现计数自洽', () => {
    const ds = defaultTimeObservationDataset();
    for (const p of ds.patterns) {
      const r = p.recurrence;
      if (r.historicalRatio !== null) {
        expect(r.historicalRatio).toBeGreaterThanOrEqual(0);
        expect(r.historicalRatio).toBeLessThanOrEqual(1);
      }
      if (p.window === null) {
        // 无法构建窗口时**不计算**复现（避免人为造一个窗口再数命中）
        expect(r.matchedCount).toBe(0);
        expect(r.matchedYears).toEqual([]);
        expect(r.missedYears).toEqual([]);
        continue;
      }
      expect(r.matchedYears.length).toBe(r.matchedCount);
      expect(r.matchedYears.length + r.missedYears.length).toBe(r.eligibleYears);
      expect(r.matchedCount).toBeLessThanOrEqual(r.eligibleYears);
    }
  });

  it('锚点日期不晚于研究快照日，且都在研究覆盖年份内', () => {
    const ds = defaultTimeObservationDataset();
    for (const p of ds.patterns) {
      for (const o of p.observations) {
        expect(o.date <= ds.snapshotDate).toBe(true);
        expect(o.year).toBe(Number(o.date.slice(0, 4)));
      }
    }
  });
});
