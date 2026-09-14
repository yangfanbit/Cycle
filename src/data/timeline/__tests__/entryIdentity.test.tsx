import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { SamePeriodView } from '../../../components/SamePeriodView/SamePeriodView';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import { themeRowsOf } from '../themeRows';
import { currentTimeLens } from '../currentTimeLens';
import { previewTimelineSource, verifiedTimelineSource } from '../timelineAdapter';
import { timelineEntryId } from '../entryIdentity';
import type { HistoricalCampaign } from '../../../models';

/**
 * Timeline Entry Identity v1 测试。
 *
 * 规则：`entryId = `${campaign_id}@${display_year}``（见 `src/data/timeline/entryIdentity.ts`）。
 * 背景：一个 Campaign 可跨多个年份（C-2019-PHARMA-INNOV 2019-01-02 ~ 2022-10-31），
 * Timeline 会在 2019/2020/2021/2022 各年份行各生成一条明细 —— UI 层不得再用
 * `campaign_id` 作明细身份（React key 重复 / focus 无法区分年份 / 页签同时高亮）。
 *
 * 分组：
 *   1. timelineEntryId() 规则
 *   2. 跨年 Campaign 在 themeRows 的 identity（真实导出数据）
 *   3. 汽车（单年度）identity 数量不变化
 *   4. CurrentTimeLens 条目的 identity
 *   5. 数据集无关性（合成跨年 Campaign）
 *   6. UI 层 identity 使用（源码守护）+ 组件渲染
 */

const TODAY = '2026-09-13'; // 9 月 → 窗口 08-15 ~ 10-15
const SEPT = 9;

const fs = require('node:fs') as typeof import('node:fs');
const path = require('node:path') as typeof import('node:path');
/** 读取仓库内文件（vitest 的 cwd = 仓库根） */
const read = (rel: string) => fs.readFileSync(path.resolve(process.cwd(), rel), 'utf-8');

const PHARMA = 'C-2019-PHARMA-INNOV';

/* ---------------- 1. timelineEntryId() 规则 ---------------- */

describe('1. timelineEntryId()：唯一 identity 规则', () => {
  it('entryId = `${campaign_id}@${display_year}`', () => {
    expect(timelineEntryId(PHARMA, 2021)).toBe('C-2019-PHARMA-INNOV@2021');
    expect(timelineEntryId('C-2019-AD', 2019)).toBe('C-2019-AD@2019');
  });

  it('同一 Campaign 不同展示年份 → 4 个互不相同的 entryId', () => {
    const ids = [2019, 2020, 2021, 2022].map((y) => timelineEntryId(PHARMA, y));
    expect(ids).toEqual([
      'C-2019-PHARMA-INNOV@2019',
      'C-2019-PHARMA-INNOV@2020',
      'C-2019-PHARMA-INNOV@2021',
      'C-2019-PHARMA-INNOV@2022',
    ]);
    expect(new Set(ids).size).toBe(4);
  });

  it('不同 Campaign 同一年份 → 不同 entryId（不误合并）', () => {
    expect(timelineEntryId('A', 2021)).not.toBe(timelineEntryId('B', 2021));
  });
});

/* ---------------- 2. themeRows 的 identity（真实导出数据） ---------------- */

describe('2. 跨年 Campaign 在 themeRows 的 identity（真实导出数据）', () => {
  it('C-2019-PHARMA-INNOV 生成 2019/2020/2021/2022 四个互不相同的 entryId', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const row = result.rows.find((r) => r.themeKey === '创新药');
    expect(row).toBeDefined();
    expect(row!.campaigns.map((e) => e.entryId)).toEqual([
      'C-2019-PHARMA-INNOV@2019',
      'C-2019-PHARMA-INNOV@2020',
      'C-2019-PHARMA-INNOV@2021',
      'C-2019-PHARMA-INNOV@2022',
    ]);
    // 四个 identity 必须不同
    expect(new Set(row!.campaigns.map((e) => e.entryId)).size).toBe(4);
    // 但它们都属于【同一个】Campaign
    expect(new Set(row!.campaigns.map((e) => e.campaign_id)).size).toBe(1);
    expect(row!.campaigns.every((e) => e.campaign_id === PHARMA)).toBe(true);
  });

  it('entryId 与 (campaign_id, 展示年份) 严格一一对应', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    for (const row of result.rows) {
      for (const e of row.campaigns) {
        expect(e.entryId).toBe(timelineEntryId(e.campaign_id, e.year));
      }
    }
  });

  it('整个月份视图内 entryId 全局唯一（不存在 React key 冲突）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const ids = result.rows.flatMap((r) => r.campaigns.map((e) => e.entryId));
    expect(ids.length).toBeGreaterThan(0);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('每行内 entryId 唯一（React key 无重复）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    for (const row of result.rows) {
      const ids = row.campaigns.map((e) => e.entryId);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });
});

/* ---------------- 3. 汽车 identity 数量不变化 ---------------- */

describe('3. 汽车（单年度）identity 数量不变化', () => {
  /**
   * 单年度 Campaign：`campaign_year === display_year` → entryId 与 campaign_id **一一对应**，
   * 即 identity 数量与 V1.9 之前（以 campaign_id 计数）**完全一致**，视觉不变。
   */
  it('单年度明细：entryId ↔ campaign_id 一一对应，数量与修复前一致', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const singles = result.rows
      .flatMap((r) => r.campaigns)
      .filter((e) => e.campaign.start.slice(0, 4) === e.campaign.end.slice(0, 4));
    // 9 月窗口下的单年度（汽车）明细总数：1+2+1+1+2 = 7（引入 entryId 前后不变）
    expect(singles).toHaveLength(7);
    expect(new Set(singles.map((e) => e.campaign_id)).size).toBe(singles.length);
    expect(new Set(singles.map((e) => e.entryId)).size).toBe(singles.length);
    for (const e of singles) {
      expect(e.entryId).toBe(`${e.campaign_id}@${e.year}`);
      expect(e.year).toBe(e.campaign.year); // 单年度：展示年份 = Campaign 年份
    }
  });

  it('跨 1–12 月：单年度明细 identity 恒为 1:1（数量不变化）', () => {
    const src = previewTimelineSource();
    let scanned = 0;
    for (let m = 1; m <= 12; m += 1) {
      const entries = themeRowsOf(src, m)
        .rows.flatMap((r) => r.campaigns)
        .filter((e) => e.campaign.start.slice(0, 4) === e.campaign.end.slice(0, 4));
      scanned += entries.length;
      // identity 数量 = 明细数量（无重复、无合并）
      expect(new Set(entries.map((e) => e.entryId)).size).toBe(entries.length);
      // 单年度下 entryId 与 campaign_id 一一对应 → 与引入前（按 campaign_id 计数）完全一致
      expect(new Set(entries.map((e) => e.campaign_id)).size).toBe(entries.length);
      for (const e of entries) expect(e.entryId).toBe(`${e.campaign_id}@${e.year}`);
    }
    expect(scanned).toBeGreaterThan(7); // 12 个月累计扫描量（9 月单月为 7）
  });

  it('汽车 5 个主题行的年份 / 代表阶段不因 identity 引入而变化', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const pin = (key: string, years: number[], primary: string | null) => {
      const row = result.rows.find((r) => r.themeKey === key);
      expect(row, key).toBeDefined();
      expect(row!.years).toEqual(years);
      expect(row!.primaryPhase).toBe(primary);
    };
    pin('智能驾驶/无人驾驶', [2019], '主升');
    pin('新能源汽车/电池', [2020, 2021], '退潮');
    pin('汽车消费/购置税刺激', [2022], '退潮');
    pin('华为汽车', [2023], '主升');
    pin('Robotaxi/无人驾驶/智能网约车', [2024, 2025], '主段结束');
  });
});

/* ---------------- 4. CurrentTimeLens 条目的 identity ---------------- */

describe('4. CurrentTimeLens 条目的 identity', () => {
  it('跨年条目在不同年份行 entryId 互不相同', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    const ids = lens.samePeriod
      .flatMap((r) => r.entries)
      .filter((e) => e.campaign_id === PHARMA)
      .map((e) => e.entryId);
    expect(ids).toEqual([
      'C-2019-PHARMA-INNOV@2019',
      'C-2019-PHARMA-INNOV@2020',
      'C-2019-PHARMA-INNOV@2021',
      'C-2019-PHARMA-INNOV@2022',
    ]);
    expect(new Set(ids).size).toBe(4);
  });

  it('每个年份行内 entryId 唯一（React key 无重复）', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    for (const row of lens.samePeriod) {
      const ids = row.entries.map((e) => e.entryId);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it('条目 entryId 与 (campaign_id, 展示年份) 严格对应', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    for (const row of lens.samePeriod) {
      for (const e of row.entries) {
        expect(e.entryId).toBe(timelineEntryId(e.campaign_id, e.year));
      }
    }
  });
});

/* ---------------- 5. 数据集无关性（合成跨年 Campaign） ---------------- */

describe('5. identity 规则与数据集无关（合成跨年 Campaign）', () => {
  const multi: HistoricalCampaign = {
    campaign_id: 'cmp_synth_multiyear',
    rule_id: 'rule_auto_summer',
    season_id: '2019',
    campaign_year: 2019,
    start_date: '2019-01-02',
    end_date: '2022-10-31',
    peak_date: null,
    cross_year: true,
    strength: 'strong',
    result: 'positive',
    description: '合成 fixture：仅用于验证跨年 identity 规则，不是真实历史行情。',
    source_id: 'fx_spec_001',
    start_date_basis: 'unknown',
    end_date_basis: 'unknown',
    date_confidence: 'low',
  };
  const single = (id: string, year: number): HistoricalCampaign => ({
    campaign_id: id,
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
  // 另加 2020 / 2021 单年度行情，使 verified 源覆盖 2019–2022 四个年份行
  const dataset = [multi, single('cmp_synth_single_2020', 2020), single('cmp_synth_single_2021', 2021)];

  it('跨年 Campaign：4 个展示年份 → 4 个互不相同的 entryId', () => {
    const result = themeRowsOf(verifiedTimelineSource(dataset), SEPT);
    const entries = result.rows
      .flatMap((r) => r.campaigns)
      .filter((e) => e.campaign_id === 'cmp_synth_multiyear');
    expect(entries.map((e) => e.entryId)).toEqual([
      'cmp_synth_multiyear@2019',
      'cmp_synth_multiyear@2020',
      'cmp_synth_multiyear@2021',
      'cmp_synth_multiyear@2022',
    ]);
    expect(new Set(entries.map((e) => e.entryId)).size).toBe(4);
    expect(new Set(entries.map((e) => e.campaign_id)).size).toBe(1);
  });

  it('同一数据集内单年度 Campaign：identity 1:1（数量不变化）', () => {
    const result = themeRowsOf(verifiedTimelineSource(dataset), SEPT);
    const singles = result.rows
      .flatMap((r) => r.campaigns)
      .filter((e) => e.campaign_id !== 'cmp_synth_multiyear');
    expect(singles).toHaveLength(2); // 2 条单年度明细 → 2 个 identity
    expect(new Set(singles.map((e) => e.entryId)).size).toBe(2);
    for (const e of singles) expect(e.entryId).toBe(`${e.campaign_id}@${e.year}`);
  });

  /**
   * 已知限制（Audit Finding F-MED-5，**与 entryId 无关**，属既有源差异）：
   * `verifiedTimelineSource().years()` 只收集各 Campaign 的 **起止年份**（无区间填充），
   * 而 `previewTimelineSource().years()` 做 min..max **全量填充**。
   * → 生产模式下，跨年 Campaign 的**中间年份行会缺失**（本 fixture 只剩 2019 / 2022）。
   * 当前 `data/verified/campaigns.ts` 为空（0 条），故尚未显现。
   * 本用例固定当前行为；若决定统一 years() 口径，应改为 4 个年份。
   */
  it('已知限制 F-MED-5：verified 源 years() 只含起止年份（跨年中间年缺失）', () => {
    const src = verifiedTimelineSource([multi]);
    expect(src.years()).toEqual([2019, 2022]);
    const entries = themeRowsOf(src, SEPT).rows.flatMap((r) => r.campaigns);
    expect(entries.map((e) => e.entryId)).toEqual([
      'cmp_synth_multiyear@2019',
      'cmp_synth_multiyear@2022',
    ]);
  });
});

/* ---------------- 6. UI 层 identity 使用（源码守护）+ 组件渲染 ---------------- */

describe('6. UI 层 identity 使用（源码守护）', () => {
  it('SamePeriodView 年份页签：key / active / focus 均用 entryId', () => {
    const src = read('src/components/SamePeriodView/SamePeriodView.tsx');
    expect(src).toContain('key={e.entryId}');
    expect(src).toContain('e.entryId === focus.entryId');
    expect(src).toContain('onFocus(e.entryId)');
    expect(src).toContain('find((e) => e.entryId === focusEntryId)');
    expect(src).toContain('.entryId : null');
    // 禁止回到 campaign_id 作明细身份
    expect(src).not.toContain('key={e.campaign_id}');
    expect(src).not.toContain('onFocus(e.campaign_id)');
    // selection（打开 Campaign Detail）仍以 campaign_id 为准：未被本层改动
    expect(src).toContain('onOpenFull(focus.campaign_id)');
    expect(src).toContain('selection.id === focus.campaign_id');
  });

  it('CurrentTimeLens 条目 key 用 entryId（drivers 行用 timelineEntryId()）', () => {
    const src = read('src/components/CurrentTimeLens/CurrentTimeLens.tsx');
    expect(src).toContain('key={e.entryId}');
    expect(src).toContain('key={timelineEntryId(d.campaign_id, d.year)}');
    expect(src).not.toContain('key={e.campaign_id}');
  });

  it('Timeline 行情行 key 用 timelineEntryId(campaign_id, year)', () => {
    const src = read('src/components/Timeline/Timeline.tsx');
    expect(src).toContain('key={timelineEntryId(campaign.campaign_id, year)}');
  });

  it('entryIdentity.ts 只被 Timeline / ViewModel 层引用（不进 DB / Export / Research）', () => {
    const src = read('src/data/timeline/entryIdentity.ts');
    expect(src).toContain('仅供 UI / ViewModel');
    expect(src).toContain('不是持久化标识');
  });
});

describe('7. 组件渲染：跨年主题行的 4 条明细逐条保留', () => {
  it('SamePeriodView 渲染创新药行：4 条明细 + 4 个年份', () => {
    const html = renderToStaticMarkup(
      <SamePeriodView dataSource={previewTimelineSource()} today={TODAY} />,
    );
    expect(html).toContain('创新药');
    expect(html).toContain('4 条'); // 明细逐条保留，不合并
    for (const y of [2019, 2020, 2021, 2022]) {
      expect(html).toContain(`sp-theme-year">${y}</span>`);
    }
  });
});

describe('8. identity 是纯内部身份：不泄漏到渲染输出（视觉不变）', () => {
  it('SamePeriodView / CurrentTimeLens 的渲染 HTML 不含任何 entryId 字符串', () => {
    const source = previewTimelineSource();
    const result = themeRowsOf(source, SEPT);
    const ids = result.rows.flatMap((r) => r.campaigns.map((e) => e.entryId));
    expect(ids.length).toBeGreaterThan(0);

    const html =
      renderToStaticMarkup(<SamePeriodView dataSource={source} today={TODAY} />) +
      renderToStaticMarkup(
        <CurrentTimeLens dataSource={source} today={TODAY} selection={null} onSelect={() => {}} />,
      );
    // entryId 只用于 React key / focus 标识，绝不进入可见输出 → 汽车视觉与 V1.9 之前一致
    for (const id of ids) expect(html).not.toContain(id);
    expect(html).not.toContain('C-2019-PHARMA-INNOV@');
  });
});
