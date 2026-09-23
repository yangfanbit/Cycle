import { describe, expect, it } from 'vitest';
import { yearCoverageOf, yearOf, yearSpan, timelineYears } from '../yearCoverage';
import { previewTimelineSource, verifiedTimelineSource } from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import { themeRowsOf } from '../themeRows';
import { fixtureCrossYearMedia } from '../../../../tests/fixtures/campaignFixtures';
import type { HistoricalCampaign } from '../../../models';

/**
 * Timeline Year Coverage Rule v1 测试（V1.9.1，修复 F-MED-5）。
 *
 * 规则：Campaign / Research Candidate 覆盖的展示年份 = 从 `start_date` 年
 * **连续生成** 到 `end_date` 年（含两端）。
 * `verified`（生产）与 `preview`（研究预览）必须使用**同一规则、同一 helper**。
 *
 * 分组：
 *   1. yearSpan()：单区间连续年份
 *   2. yearCoverageOf() / timelineYears()：并集与连续区间
 *   3. 生产源（verified）：Campaign Year Coverage
 *   4. 汽车（单年度）年份覆盖不变化
 *   5. 两源口径一致（同 helper）
 */

const fs = require('node:fs') as typeof import('node:fs');
const path = require('node:path') as typeof import('node:path');
/** 读取仓库内文件（vitest 的 cwd = 仓库根） */
const read = (rel: string) => fs.readFileSync(path.resolve(process.cwd(), rel), 'utf-8');

const SEPT = 9;
const PHARMA = 'C-2019-PHARMA-INNOV';
const MULTI = 'cmp_synth_multiyear';

/** 合成跨年 Campaign：2019-01-02 ~ 2022-10-31（非真实历史行情，仅测试规则） */
const multiYear: HistoricalCampaign = {
  campaign_id: MULTI,
  rule_id: 'rule_auto_summer',
  season_id: '2019',
  campaign_year: 2019,
  start_date: '2019-01-02',
  end_date: '2022-10-31',
  peak_date: null,
  cross_year: true,
  strength: 'strong',
  result: 'positive',
  description: '合成 fixture：仅用于验证年份覆盖规则，不是真实历史行情。',
  source_id: 'fx_spec_001',
  start_date_basis: 'unknown',
  end_date_basis: 'unknown',
  date_confidence: 'low',
};

/** 合成单年度 Campaign（模拟汽车：campaign_year === display_year） */
const singleYear = (year: number): HistoricalCampaign => ({
  campaign_id: `cmp_synth_single_${year}`,
  rule_id: 'rule_auto_summer',
  season_id: String(year),
  campaign_year: year,
  start_date: `${year}-06-01`,
  end_date: `${year}-09-30`,
  peak_date: null,
  cross_year: false,
  strength: 'medium',
  result: 'positive',
  description: '合成 fixture：单年度对照，不是真实历史行情。',
  source_id: 'fx_spec_001',
  start_date_basis: 'unknown',
  end_date_basis: 'unknown',
  date_confidence: 'low',
});

/* ---------------- 1. yearOf() / yearSpan() ---------------- */

describe('1. yearOf()：严格年份解析（空串不得变成 0）', () => {
  it('标准日期 → 年份', () => {
    expect(yearOf('2019-01-02')).toBe(2019);
    expect(yearOf('2022-10-31')).toBe(2022);
    expect(yearOf('2026')).toBe(2026);
  });

  it('空串 / null / undefined / 非日期 → null（不可用 Number()：Number("") === 0）', () => {
    expect(yearOf('')).toBeNull();
    expect(yearOf(null)).toBeNull();
    expect(yearOf(undefined)).toBeNull();
    expect(yearOf('abcd')).toBeNull();
    expect(yearOf('-')).toBeNull();
  });
});

describe('1b. yearSpan()：单区间连续年份（含两端）', () => {
  it('2019-01-02 ~ 2022-10-31 → [2019, 2020, 2021, 2022]', () => {
    expect(yearSpan('2019-01-02', '2022-10-31')).toEqual([2019, 2020, 2021, 2022]);
  });

  it('单年度区间 → 单一年份', () => {
    expect(yearSpan('2024-06-01', '2024-09-30')).toEqual([2024]);
  });

  it('跨越相邻两年（2026-11-01 ~ 2027-01-15）→ [2026, 2027]', () => {
    expect(yearSpan('2026-11-01', '2027-01-15')).toEqual([2026, 2027]);
  });

  it('起止倒置时仍返回连续区间（防御性，不产生空集）', () => {
    expect(yearSpan('2022-10-31', '2019-01-02')).toEqual([2019, 2020, 2021, 2022]);
  });

  it('无法解析出年份 → []（不编造年份）', () => {
    expect(yearSpan('', '')).toEqual([]);
    expect(yearSpan('abcd', '2020-01-01')).toEqual([]);
    expect(yearSpan('2020-01-01', 'abcd')).toEqual([]);
  });
});

/* ---------------- 2. yearCoverageOf() / timelineYears() ---------------- */

describe('2. yearCoverageOf() / timelineYears()：并集与连续区间', () => {
  it('多区间并集升序去重', () => {
    expect(
      yearCoverageOf([
        { start: '2020-06-01', end: '2020-09-30' },
        { start: '2019-01-02', end: '2019-12-31' },
        { start: '2020-06-01', end: '2020-09-30' },
      ]),
    ).toEqual([2019, 2020]);
  });

  it('跨年区间自动补齐中间年份（这是 F-MED-5 的核心）', () => {
    expect(yearCoverageOf([{ start: '2019-01-02', end: '2022-10-31' }])).toEqual([
      2019, 2020, 2021, 2022,
    ]);
  });

  it('timelineYears 相邻年份补齐（UI 年份轴无空洞）', () => {
    expect(
      timelineYears([
        { start: '2019-01-02', end: '2019-12-31' },
        { start: '2022-01-01', end: '2022-12-31' },
      ]),
    ).toEqual([2019, 2020, 2021, 2022]);
  });

  it('extraYears（声明年份）并入并扩展区间下界', () => {
    expect(timelineYears([{ start: '2020-01-01', end: '2021-12-31' }], [2018])).toEqual([
      2018, 2019, 2020, 2021,
    ]);
  });

  it('extraYears 中的非法值被忽略', () => {
    expect(timelineYears([{ start: '2020-01-01', end: '2021-12-31' }], [Number.NaN, 2020])).toEqual([
      2020, 2021,
    ]);
  });

  it('空输入 → []（不编造年份）', () => {
    expect(timelineYears([])).toEqual([]);
    expect(timelineYears([], [])).toEqual([]);
    expect(timelineYears([{ start: '', end: '' }])).toEqual([]);
  });
});

/* ---------------- 3. 生产源（verified）：Campaign Year Coverage ---------------- */

describe('3. 生产源（verified）：跨年 Campaign 必须连续覆盖', () => {
  it('2019-2022 跨年 Campaign → years() = [2019, 2020, 2021, 2022]', () => {
    const src = verifiedTimelineSource([multiYear]);
    expect(src.years()).toEqual([2019, 2020, 2021, 2022]);
  });

  it('中间年份行也含该行情（旧实现只出 2019 / 2022，中间年缺失）', () => {
    const src = verifiedTimelineSource([multiYear]);
    for (const y of [2019, 2020, 2021, 2022]) {
      expect(
        src.yearData(y).campaigns.some((c) => c.campaign_id === MULTI),
        `${y} 年应含 ${MULTI}`,
      ).toBe(true);
    }
  });

  it('主题行层面：跨年 Campaign 在 4 个年份各成一条明细', () => {
    const result = themeRowsOf(verifiedTimelineSource([multiYear]), SEPT);
    const row = result.rows.find((r) => r.campaigns.some((e) => e.campaign_id === MULTI));
    expect(row).toBeDefined();
    expect(row!.years).toEqual([2019, 2020, 2021, 2022]);
  });

  it('跨年相邻 fixture（2026-11-01 ~ 2027-01-15）→ [2026, 2027]（既有行为保持）', () => {
    expect(verifiedTimelineSource([fixtureCrossYearMedia]).years()).toEqual([2026, 2027]);
  });

  it('空数据 → []（不编造年份）', () => {
    expect(verifiedTimelineSource([]).years()).toEqual([]);
  });
});

/* ---------------- 4. 汽车（单年度）年份覆盖不变化 ---------------- */

describe('4. 汽车（单年度）年份覆盖不变化', () => {
  it('单年度 Campaign 合集 → 与逐年起止年份完全一致（无新增年份）', () => {
    const years = [2019, 2020, 2021, 2022, 2023, 2024, 2025];
    const src = verifiedTimelineSource(years.map(singleYear));
    expect(src.years()).toEqual(years);
    // 每一年只有自己的那条（无跨年串扰）
    for (const y of years) {
      expect(src.yearData(y).campaigns.map((c) => c.campaign_id)).toEqual([`cmp_synth_single_${y}`]);
    }
  });

  it('单年度 Campaign 的 yearSpan 长度为 1（恒等：不会引入中间年份）', () => {
    for (const y of [2019, 2023, 2025]) {
      expect(yearSpan(`${y}-06-01`, `${y}-09-30`)).toEqual([y]);
    }
  });

  it('真实导出：preview 年份覆盖 = 导出对象的 min/max year（升序连续，数据驱动）', () => {
    // ★ 不再写死 2018–2025（旧 universe 耦合）—— 断言年份序列的**结构性质**
    const years = previewTimelineSource().years();
    expect(years).toEqual([...years].sort((a, b) => a - b));
    for (let i = 1; i < years.length; i += 1) expect(years[i] - years[i - 1]).toBe(1);
    const allYears = [
      ...timelineExportData.campaigns.map((c) => c.year),
      ...timelineExportData.research_candidates.map((r) => r.year),
    ];
    expect(years[0]).toBe(Math.min(...allYears));
    expect(years[years.length - 1]).toBe(Math.max(...allYears));
  });
});

/* ---------------- 5. 两源口径一致 ---------------- */

describe('5. 两源口径一致（同一规则、同一 helper）', () => {
  it('源码守护：verified 与 preview 均调用同一 timelineYears()', () => {
    const src = read('src/data/timeline/timelineAdapter.ts');
    const calls = src.match(/timelineYears\(/g) ?? [];
    expect(calls).toHaveLength(2); // verified 1 处 + preview 1 处
    // 旧的两套手写逻辑不得回归
    expect(src).not.toContain("set.add(Number(c.start.slice(0, 4)))");
    expect(src).not.toContain('set.add(c.year)');
  });

  it('覆盖性不变式：preview 与 verified 都满足「Campaign 的每个覆盖年份都在 years() 中」', () => {
    const sources = [
      previewTimelineSource(),
      verifiedTimelineSource([multiYear, singleYear(2020), singleYear(2021)]),
    ];
    for (const src of sources) {
      const years = src.years();
      for (const y of years) {
        for (const c of src.yearData(y).campaigns) {
          for (const spanned of yearSpan(c.start, c.end)) {
            expect(years, `${c.campaign_id} 覆盖 ${spanned} 应在 years()`).toContain(spanned);
          }
        }
      }
    }
  });

  it('preview：跨年医药 Campaign（2019-01-02 ~ 2022-10-31）在 2019–2022 各年均可命中', () => {
    const src = previewTimelineSource();
    const years = src.years();
    for (const y of [2019, 2020, 2021, 2022]) {
      expect(years).toContain(y);
      expect(src.yearData(y).campaigns.some((c) => c.campaign_id === PHARMA)).toBe(true);
    }
  });
});
