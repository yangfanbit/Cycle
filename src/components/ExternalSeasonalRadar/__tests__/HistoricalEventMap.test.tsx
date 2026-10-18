/**
 * 通用历史事件地图 —— 必要测试（2026-10-14 多题材通用化）。
 *
 * 只覆盖**必要**检查：
 *   A. 索引驱动：题材能被解析、无数据题材不显示空壳
 *   B. 多题材数据通过通用校验
 *   C. 通用组件能渲染非流感题材（且带该题材自己的免责声明）
 *   D. ★ 向后兼容：流感 4 事件语义未变（由 FluEventMap.test.tsx 覆盖，此处只验入口）
 *   E. ★★ 行情超额两列：区间超额（excess_period_pp）与至高点超额（excess_to_high_pp）各自取值
 *   F. ★★ 四类行情状态：COMPUTED / NOT_COMPUTED / UNAVAILABLE / INSUFFICIENT
 *   G. ★ 索引一致性校验（event_count / external_entry_ids / theme_id / display）
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { EventCardBody, HistoricalEventMap, MarketPerformanceBlock, ParticipantRow } from '../HistoricalEventMap';
import {
  CROSS_YEAR_CAVEAT,
  CROSS_YEAR_OUTCOME_LABEL,
  MARKET_DATA_STATUS_LABEL,
  allResolvedEventMaps,
  crossYearComparisonOf,
  eventMapByExternalId,
  eventMapByTheme,
  eventMapIndex,
  eventMapsNotIncluded,
  eventStudyState,
  marketDataCoverage,
  marketDataStatus,
  validateEventMapIndex,
  validateHistoricalEvents,
  type HistoricalEvent,
  type SecurityPerformance,
} from '../../../data/timeline/historicalEventMaps';

describe('A. 索引驱动', () => {
  it('★ 按外部线索 ID 能解析到题材（数据驱动，非硬编码）', () => {
    expect(eventMapByExternalId('EXT-12')?.theme_id).toBe('FLU');
    expect(eventMapByExternalId('EXT-14')?.theme_id).toBe('POWER_SUMMER');
    expect(eventMapByExternalId('EXT-13')?.theme_id).toBe('MEDIA');
    expect(eventMapByExternalId('EXT-23')?.theme_id).toBe('ROBOTICS');
  });

  it('★ 无数据文件的题材 → undefined（**不显示空壳**）', () => {
    // EXT-09 / EXT-05 / EXT-19 已在索引的 not_included 里记录原因
    for (const id of ['EXT-09', 'EXT-05', 'EXT-19', 'EXT-01', 'EXT-25']) {
      expect(eventMapByExternalId(id), id).toBeUndefined();
    }
    expect(eventMapsNotIncluded().length).toBeGreaterThanOrEqual(3);
  });

  it('★ 题材全部解析成功（索引有条目 + 注册表有文档；v0.16 起 6 个）', () => {
    const maps = allResolvedEventMaps();
    expect(maps.map((m) => m.theme_id).sort()).toEqual(
      ['AUTO_INTELLIGENCE', 'FLU', 'MEDIA', 'POWER_SUMMER', 'ROBOTICS', 'SEMICONDUCTOR_AI'].sort());
    for (const m of maps) expect(m.doc.events.length, m.theme_id).toBeGreaterThan(0);
  });

  it('★ 每个题材的 display 配置齐全（title / aria / badge / note / class_order）', () => {
    for (const m of allResolvedEventMaps()) {
      expect(m.display.title, m.theme_id).toBeTruthy();
      expect(m.display.aria_label, m.theme_id).toBeTruthy();
      expect(m.display.badge, m.theme_id).toBeTruthy();
      expect(m.display.note, m.theme_id).toBeTruthy();
      expect(m.display.class_order.length, m.theme_id).toBeGreaterThan(0);
    }
  });
});

describe('B. 多题材数据通过通用校验', () => {
  it('★ 所有题材事件数据通过结构校验（含业务机制 caveat / is_campaign_ruling）', () => {
    for (const m of allResolvedEventMaps()) {
      expect(validateHistoricalEvents(m.doc, m.theme_id), m.theme_id).toEqual([]);
    }
  });

  it('能发现：缺 event_class / 缺 known_gaps / 非法 category', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const bad = JSON.parse(JSON.stringify(m.doc));
    delete bad.events[0].event_class;
    bad.events[0].known_gaps = [];
    bad.events[0].participants[0].category = 'WEIRD';
    const issues = validateHistoricalEvents(bad, 'X');
    expect(issues.some((i) => i.field === 'event_class')).toBe(true);
    expect(issues.some((i) => i.field === 'known_gaps')).toBe(true);
    expect(issues.some((i) => i.field.includes('participants.category'))).toBe(true);
  });
});

describe('C. 通用组件渲染非流感题材', () => {
  it('★ 电力题材可渲染，且带该题材自己的 class caveat 与 note', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain(m.display.aria_label);
    expect(html).toContain('POWER-2023-SUMMER');
    // ★ 四个概念区分提示（题材专属，非流感的三概念）
    expect(html).toContain('窗口口径');
    expect(html).toContain('不可混用');
    // ★ Campaign 事实（含 peak_date，且注明不是行情高点）
    expect(html).toContain('C-2023-POWEROP-THERMAL');
  });

  it('★ 传媒题材可渲染，且明确标注机制非暑期档', () => {
    const m = eventMapByTheme('MEDIA')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain('MEDIA-2021-METAVERSE');
    expect(html).toContain(m.display.note.slice(0, 20));
  });

  it('★ 机器人题材可渲染', () => {
    const m = eventMapByTheme('ROBOTICS')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain('ROBOTICS-2023-HUMANOID');
  });

  it('★ 每个题材都有事件带可分析行情（本轮补数生效；诚实空洞事件必须显式留 error）', () => {
    for (const m of allResolvedEventMaps()) {
      const states = m.doc.events.map((e) => eventStudyState(e));
      // 每个题材至少有一个事件带可分析行情（题材可用）
      expect(states, m.theme_id).toContain('HAS_PRICE_DATA');
      for (const e of m.doc.events) {
        if (eventStudyState(e) !== 'NO_PRICE_DATA') continue;
        // ★★ 诚实空洞：行情块必须逐条显式 error，**不得**静默缺省或补 0
        const by = e.market_performance?.by_security ?? {};
        const keys = Object.keys(by);
        expect(keys.length, `${m.theme_id}/${e.event_id}`).toBeGreaterThan(0);
        for (const k of keys) {
          expect(by[k].error, `${m.theme_id}/${e.event_id}/${k}`).toBe('insufficient_data_in_window');
        }
      }
    }
  });

  it('★ 每个题材的行情表都含基准（SH000300）', () => {
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        const mp = e.market_performance;
        if (!mp) continue;
        expect(Object.keys(mp.benchmark), `${m.theme_id}/${e.event_id}`).toContain('SH000300');
        expect(mp.is_campaign_ruling, `${m.theme_id}/${e.event_id}`).toBe(false);
      }
    }
  });
});

describe('D. 向后兼容（入口层）', () => {
  it('★ FLU 题材已升版 v0_6（6 事件，含 2018/2024 跨年份）', () => {
    const m = eventMapByTheme('FLU')!;
    expect(m.doc.artifact_version).toBe('0.6');
    expect(m.doc.events).toHaveLength(6);
    // ★ 跨年份事件已接入
    expect(m.doc.events.map((e) => e.event_id)).toContain('FLU-2018-SEASONAL');
    expect(m.doc.events.map((e) => e.event_id)).toContain('FLU-2024-SEASONAL');
    // ★ 流感专属的 corrections 更正痕迹仍在
    expect(JSON.stringify(m.doc.corrections)).toContain('600513');
  });

  it('★★ FLU 跨年份：11 个季节窗口 · year=季节开始年 · 含 2025/26 季', () => {
    const cy = crossYearComparisonOf(eventMapByTheme('FLU')!.doc)!;
    expect(cy.years).toHaveLength(11);
    expect(cy.years.map((y) => y.year)).toEqual(
      Array.from({ length: 11 }, (_, i) => 2015 + i));
    // ★ season_label 与窗口必须显式（不得只有 year）
    for (const y of cy.years) {
      expect(y.season_label, String(y.year)).toBeTruthy();
      expect(y.window, String(y.year)).toEqual([`${y.year}-09-01`, `${y.year + 1}-01-31`]);
      expect(y.window_type).toBe('SEASON_WINDOW_9_1');
    }
    // ★ 2025/26 季必须存在且端点可达（用户明确要求补数的窗口）
    const last = cy.years[cy.years.length - 1];
    expect(last.year).toBe(2025);
    expect(last.coverage).toBe('FULL');
    expect(last.comparable).toBe(true);
    expect(last.benchmark!.last!.date >= '2026-01-01').toBe(true);
    // ★ 11 季中「不可比」为 0 —— 不得用 10 行数据宣称 11 个完整窗口
    expect(cy.years.filter((y) => y.comparable === false)).toHaveLength(0);
  });

  it('★★ 窗口外事件被显式列出（不得混入 9–1 月季节性）', () => {
    const doc = eventMapByTheme('FLU')!.doc as unknown as {
      cross_year: { out_of_window_events: { year: number; why_out: string }[] };
    };
    const ids = doc.cross_year.out_of_window_events.map((x) => x.year);
    expect(ids).toContain(2017);
    expect(ids).toContain(2022);
    for (const x of doc.cross_year.out_of_window_events) expect(x.why_out).toContain('不得');
  });

  it('★★ POWER 跨年份：每年都带 window_type / coverage / comparable（口径不得缺失）', () => {
    const cy = crossYearComparisonOf(eventMapByTheme('POWER_SUMMER')!.doc)!;
    expect(cy.years).toHaveLength(10);
    for (const y of cy.years) {
      expect(y.window_type, String(y.year)).toBe('SEASON_WINDOW_5_7');
      expect(y.window, String(y.year)).toEqual([`${y.year}-05-01`, `${y.year}-07-31`]);
      expect(['FULL', 'PARTIAL', 'NONE'], String(y.year)).toContain(y.coverage!);
      expect(y.comparable, String(y.year)).toBeDefined();
    }
    // ★ 2024 华电停牌至 07-18 → 端点不可达 → 该年必须标为「部分可比」而非「可比」
    const y2024 = cy.years.find((y) => y.year === 2024)!;
    expect(y2024.coverage).toBe('PARTIAL');
    expect(y2024.comparable).toBe('partial');
    expect(y2024.comparable_reason).toContain('2024-07-18');
    // ★ outcome 与数值对齐：2024 四只全跌 → ALL_DOWN
    expect(y2024.outcome).toBe('ALL_DOWN');
    // ★ 2017 四只全部跑输（天富 +8.03% 并非全跌）→ UNDERPERFORM，且不在 all_down 里
    const cyRaw = eventMapByTheme('POWER_SUMMER')!.doc as unknown as {
      cross_year_comparison: { all_down_years: number[]; all_underperform_years: number[] };
    };
    expect(cyRaw.cross_year_comparison.all_down_years).toEqual([2024]);
    expect(cyRaw.cross_year_comparison.all_underperform_years).toContain(2017);
  });

  it('★ 流感题材的 class caveat 文本与既有常量一致（未在通用化中改写）', () => {
    const m = eventMapByTheme('FLU')!;
    const caveat = m.display.class_caveats?.ADJACENT_PUBLIC_HEALTH ?? '';
    expect(caveat).toContain('不是流感');
    expect(caveat).toContain('不得');
  });
});

/* ---------------------------------------------- E. ★★ 行情超额：区间 vs 至高点（两列） */

/** 取出包含 `marker` 的 `<tr>` 的单元格文本（用于验证「哪一列取了哪个字段」） */
function rowOf(html: string, marker: string): string[] {
  const tr = html.split('<tr').find((s) => s.includes(marker));
  if (!tr) throw new Error('未找到行: ' + marker);
  return tr.split(/<td[^>]*>/).slice(1).map((c) => c.slice(0, c.indexOf('</td>')));
}

describe('E. ★★ 行情超额必须拆成两列（区间超额 / 至高点超额）', () => {
  // ★ 按 event_id 定位（**不依赖数组顺序** —— v0_2 排序后 events[0] 已变为 2017 事件）
  const power = eventMapByTheme('POWER_SUMMER')!.doc.events
    .find((e) => e.event_id === 'POWER-2023-SUMMER')!;
  const html = renderToStaticMarkup(<MarketPerformanceBlock e={power} />);

  it('★ 列标题为「区间超额」与「至高点超额」，不再有含混的「超额(vs 基准)」', () => {
    expect(html).toContain('区间超额');
    expect(html).toContain('至高点超额');
    expect(html).not.toContain('超额(vs 基准)');
  });

  it('★★ 锚点：华电国际 区间超额 = -17.0pp（excess_period_pp），至高点超额 = +4.8pp（excess_to_high_pp）', () => {
    const cells = rowOf(html, 'HUADIAN');
    expect(cells).toHaveLength(8);
    expect(cells[2]).toBe('-27.6%');      // 区间涨跌
    expect(cells[6]).toBe('-17.0pp');     // ★ 区间超额 = 区间涨跌 - 基准(-10.6%)
    expect(cells[7]).toBe('+4.8pp');      // ★ 至高点超额
  });

  it('★★ 锚点：建投能源 区间超额 +8.1pp 与至高点超额 +48.1pp 分列（旧实现会把 +48.1 当成区间超额）', () => {
    const cells = rowOf(html, 'JIANTONENERGY');
    expect(cells[6]).toBe('+8.1pp');
    expect(cells[7]).toBe('+48.1pp');
    expect(cells[6]).not.toBe(cells[7]);
  });

  it('★ 基准行两列超额均为 —（不可计算时不得补 0）', () => {
    const cells = rowOf(html, '（基准）');
    expect(cells[6]).toBe('—');
    expect(cells[7]).toBe('—');
  });

  it('★ 超额字段确实来自 by_security 的两个不同字段', () => {
    const st = power.market_performance!.by_security['HUADIAN'];
    expect(st.excess_period_pp).toBe(-17.0);
    expect(st.excess_to_high_pp).toBe(4.8);
  });
});

/* ---------------------------------------------- F. ★★ 四类行情状态 */

function mkEvent(over: Partial<HistoricalEvent> = {}): HistoricalEvent {
  return {
    event_id: 'T-1', label: '测试事件', year: 2020, window_text: 'w',
    external_window_ref: null, evidence_basis: 'test',
    catalysts: [{ date: '2020-01-01', text: 'c', source: 's' }],
    participants: [{
      security_id: 'SID', ticker: '000001', name: '测试标的',
      category: 'MARKET_PARTICIPANT', rationale: '测试用', source: 'test',
    }],
    observed_performance: { note: 'n', by_security: null },
    known_gaps: ['g'],
    ...over,
  };
}

/** 合成 market_performance：窗口交易日 = windowDays */
function mkMp(by: Record<string, SecurityPerformance>, windowDays = 100) {
  return {
    window: ['2020-01-01', '2020-06-30'] as [string, string],
    is_campaign_ruling: false as const,
    note: 'n',
    benchmark: { SH000300: { trading_days: windowDays } },
    by_security: by,
  };
}

describe('F. ★★ 区分「行情未计算」与「行情不可得」（四类状态）', () => {
  it('COMPUTED：电力 华电国际 该窗口已计算（trading_days = 窗口交易日）', () => {
    const e = eventMapByTheme('POWER_SUMMER')!.doc.events
      .find((x) => x.event_id === 'POWER-2023-SUMMER')!;
    expect(marketDataStatus(e, 'HUADIAN')).toBe('COMPUTED');
  });

  it('NOT_COMPUTED：传媒 巨人网络 有行情登记但未在本事件窗口计算（★ 不等于不可得）', () => {
    const e = eventMapByTheme('MEDIA')!.doc.events[0];
    expect(e.market_performance).toBeTruthy();
    expect(marketDataStatus(e, 'GIANTNET')).toBe('NOT_COMPUTED');
    expect(marketDataStatus(e, 'GIANTNET')).not.toBe('UNAVAILABLE');
  });

  it('UNAVAILABLE：market_data 显式标注「无登记」→ 行情不可得', () => {
    const e = mkEvent({ participants: [{ security_id: 'SID', ticker: '000001', name: '无行情标的',
      category: 'MARKET_PARTICIPANT', rationale: '测试用', source: 'test',
      market_data: '无登记行情' }] });
    expect(marketDataStatus(e, 'SID')).toBe('UNAVAILABLE');
  });

  it('UNAVAILABLE：by_security[sid].status === NO_DATA → 行情不可得', () => {
    const e = mkEvent({ market_performance: mkMp({ SID: { status: 'NO_DATA', trading_days: 0 } }) });
    expect(marketDataStatus(e, 'SID')).toBe('UNAVAILABLE');
  });

  it('INSUFFICIENT：trading_days 仅 30 < 窗口 100 的 60% → 覆盖不足', () => {
    // ★ A3 起：本窗口「有可用行情」要求 `period_return_pct` 存在（缺失即视为未算出）→ 合成数据补上该字段
    const e = mkEvent({ market_performance: mkMp({ SID: { trading_days: 30, period_return_pct: 1 } }) });
    expect(marketDataStatus(e, 'SID')).toBe('INSUFFICIENT');
  });

  it('★ 四类文案互不相同（页面据此显示不同提示，不得用 0 代表缺失）', () => {
    const labels = Object.values(MARKET_DATA_STATUS_LABEL);
    expect(new Set(labels).size).toBe(4);
    expect(MARKET_DATA_STATUS_LABEL.UNAVAILABLE).toBe('行情不可得');
    expect(MARKET_DATA_STATUS_LABEL.NOT_COMPUTED).toBe('该窗口未计算');
    expect(MARKET_DATA_STATUS_LABEL.INSUFFICIENT).toBe('覆盖不足');
  });

  it('★ 标的行按状态渲染不同文案', () => {
    const computed = mkEvent({ market_performance: mkMp({ SID: { trading_days: 100, period_return_pct: 1 } }) });
    const notComputed = mkEvent({ market_performance: mkMp({}) });
    const unavailable = mkEvent({ participants: [{ security_id: 'SID', ticker: '000001', name: '无行情标的',
      category: 'MARKET_PARTICIPANT', rationale: '测试用', source: 'test', market_data: '无行情' }] });
    const insufficient = mkEvent({ market_performance: mkMp({ SID: { trading_days: 30, period_return_pct: 1 } }) });

    const text = (e: HistoricalEvent) =>
      renderToStaticMarkup(<ParticipantRow p={e.participants[0]} e={e} />);

    expect(text(computed)).toContain('data-market-status="COMPUTED"');
    expect(text(notComputed)).toContain('该窗口未计算');
    expect(text(unavailable)).toContain('行情不可得');
    expect(text(insufficient)).toContain('覆盖不足');
  });
});

/* ---------------------------------------------- G. ★ 索引一致性校验 */

describe('G. ★ 索引一致性校验（event_count / external_entry_ids / theme_id / display）', () => {
  it('★ 真实索引通过校验（event_count 与实际事件数一致）', () => {
    expect(validateEventMapIndex()).toEqual([]);
  });

  it('★★ v0.15：显式声明 NO_EXTERNAL_COUNTERPART 的题材允许无外部挂靠', () => {
    const idx = JSON.parse(JSON.stringify(eventMapIndex()));
    const auto = idx.maps.find((m: { theme_id: string }) => m.theme_id === 'AUTO_INTELLIGENCE');
    expect(auto.external_entry_ids).toEqual([]);
    expect(auto.external_link_status).toBe('NO_EXTERNAL_COUNTERPART');
    expect(validateEventMapIndex(idx)).toEqual([]);
  });

  it('★★ v0.15：未声明而 external_entry_ids 为空 → 仍然报问题', () => {
    const idx = JSON.parse(JSON.stringify(eventMapIndex()));
    const auto = idx.maps.find((m: { theme_id: string }) => m.theme_id === 'AUTO_INTELLIGENCE');
    delete auto.external_link_status;
    const issues = validateEventMapIndex(idx);
    expect(issues.some((i) => i.themeId === 'AUTO_INTELLIGENCE'
      && i.field === 'external_entry_ids')).toBe(true);
  });

  it('★★ 能抓到 event_count 与实际不一致（A2 的 MEDIA 虚增 bug）', () => {
    const idx = JSON.parse(JSON.stringify(eventMapIndex()));
    const media = idx.maps.find((m: { theme_id: string }) => m.theme_id === 'MEDIA');
    expect(media.event_count).toBe(2);
    media.event_count = 1;                       // 复现 A2
    const issues = validateEventMapIndex(idx);
    expect(issues.some((i) => i.themeId === 'MEDIA' && i.field === 'event_count')).toBe(true);
  });

  it('★ 能抓到：external_entry_ids 为空 / 被两个题材占用 / theme_id 无 doc / display 缺字段', () => {
    const idx = JSON.parse(JSON.stringify(eventMapIndex()));
    idx.maps[0].external_entry_ids = [];            // FLU：为空
    idx.maps[2].external_entry_ids = ['EXT-23'];    // MEDIA 抢占 ROBOTICS 的 EXT-23
    delete idx.maps[2].display.badge;               // MEDIA：display 缺 badge
    idx.maps[3].theme_id = 'NOT_REGISTERED';        // ROBOTICS：无对应 doc
    const issues = validateEventMapIndex(idx);
    expect(issues.some((i) => i.field === 'external_entry_ids' && /为空/.test(i.message))).toBe(true);
    expect(issues.some((i) => i.field === 'external_entry_ids' && /占用/.test(i.message))).toBe(true);
    expect(issues.some((i) => i.field === 'theme_id')).toBe(true);
    expect(issues.some((i) => i.field === 'display.badge')).toBe(true);
  });
});

/* ---------------------------------------------- H. ★★ 跨年份比较（A1） */

describe('H. ★★ 跨年份比较：取值映射 + 渲染 + 缺失不补 0', () => {
  it('★★ 两列超额锚点：华电国际 区间超额 ≈ -17.0pp 且 ≠ 至高点超额 ≈ +4.8pp（不得混用）', () => {
    const e = eventMapByTheme('POWER_SUMMER')!.doc.events
      .find((x) => x.event_id === 'POWER-2023-SUMMER')!;
    const st = e.market_performance!.by_security['HUADIAN'];
    expect(st.excess_period_pp).toBeCloseTo(-17.0, 0);
    expect(st.excess_to_high_pp).toBeCloseTo(4.8, 0);
    expect(st.excess_period_pp).not.toBe(st.excess_to_high_pp);
    const cells = rowOf(renderToStaticMarkup(<MarketPerformanceBlock e={e} />), 'HUADIAN');
    expect(cells[6]).toBe('-17.0pp');
    expect(cells[7]).toBe('+4.8pp');
  });

  it('★★ 跨年份区段真的渲染：FLU / POWER 均非 null（≥4 年），HTML 含年份与中文 outcome 标签', () => {
    for (const theme of ['FLU', 'POWER_SUMMER']) {
      const m = eventMapByTheme(theme)!;
      const cy = crossYearComparisonOf(m.doc);
      expect(cy, theme).not.toBeNull();
      expect(cy!.years.length, theme).toBeGreaterThanOrEqual(4);
      const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
      expect(html, theme).toContain('data-cross-year="1"');
      expect(html, theme).toContain(CROSS_YEAR_CAVEAT);
      // ★ 徽标：season_window 与 target_pool
      expect(cy!.season_window, theme).toBeTruthy();
      expect(cy!.target_pool, theme).toBeTruthy();
      expect(html, theme).toContain(cy!.season_window!);
      expect(html, theme).toContain(cy!.target_pool!);
      // ★ 年份与**中文** outcome 标签都要出现（不得只显示英文码）
      expect(html, theme).toContain(String(cy!.years[0].year));
      expect(html, theme).toContain(CROSS_YEAR_OUTCOME_LABEL[cy!.years[0].outcome]);
      expect(html, theme).toContain('个年份');
    }
  });

  it('★ 无跨年份数据 → 不渲染空壳（crossYearComparisonOf 返回 null）', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const stripped = JSON.parse(JSON.stringify(m.doc));
    delete stripped.cross_year_comparison;
    delete stripped.cross_year;
    expect(crossYearComparisonOf(stripped)).toBeNull();
    const html = renderToStaticMarkup(<HistoricalEventMap doc={stripped} display={m.display} />);
    expect(html).not.toContain('data-cross-year');
    // 传媒 / 机器人本就没有跨年份数据
    expect(crossYearComparisonOf(eventMapByTheme('MEDIA')!.doc)).toBeNull();
    expect(crossYearComparisonOf(eventMapByTheme('ROBOTICS')!.doc)).toBeNull();
  });

  it('★ 缺失不补 0：跨年份表缺失显示 —，不出现 +0.0% / 0.0pp', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).not.toContain('+0.0%');
    expect(html).not.toContain('0.0pp');
    // ★ FLU 跨年份**已有**逐标的数值（v0_6 补数后）→ 必须渲染出逐标的行，
    //   而上市前无数据的标的必须显示 `—`（不得补 0）
    const flu = eventMapByTheme('FLU')!;
    const fluHtml = renderToStaticMarkup(<HistoricalEventMap doc={flu.doc} display={flu.display} />);
    expect(fluHtml).toContain('data-cy-sec="HUALAN-002007"');
    // ★ 短历史三只在 2015 季为上市前 → 该行必须出现且不显示数字
    expect(fluHtml).toContain('data-cy-sec="HUALANVAX"');
    expect(fluHtml).toContain('—');
    expect(fluHtml).not.toContain('+0.0%');
    // ★ 精确断言：不存在「整格就是 0.0pp」的单元格（避免误伤 +80.0pp 这类**真实**值）
    expect(fluHtml).not.toMatch(/>\+?0\.0pp</);
    // 合成：字段缺失 → `—`
    const doc = JSON.parse(JSON.stringify(m.doc));
    doc.cross_year_comparison.years = [
      { year: 1999, window_type: 'SEASON_WINDOW_5_7', outcome: 'DIVERGENT', by_security: { X: {} } },
    ];
    const h2 = renderToStaticMarkup(<HistoricalEventMap doc={doc} display={m.display} />);
    expect(h2).toContain('1999');
    expect(h2).toContain('—');
    expect(h2).not.toContain('+0.0%');
    expect(h2).not.toContain('0.0pp');
  });
});

/* ---------------------------------------------- I. ★★ 事件级状态必须基于「本事件窗口」 */

describe('I. ★★ 事件级行情状态基于事件窗口（A2/A3）', () => {
  it('★★ market_data 有字符串但未在本事件窗口计算 → 不得 HAS_PRICE_DATA（钉死旧实现漏洞）', () => {
    const e = mkEvent({
      participants: [{
        security_id: 'SID', ticker: '000001', name: '别处有行情的标的',
        category: 'MARKET_PARTICIPANT', rationale: '测试用', source: 'test',
        market_data: '2022-01-04~2023-04-14（310 行）',   // ★ 看起来「有行情」
      }],
      market_performance: mkMp({}),                        // ★ 本窗口 by_security 不含 SID
    });
    expect(marketDataStatus(e, 'SID')).toBe('NOT_COMPUTED');
    expect(eventStudyState(e)).not.toBe('HAS_PRICE_DATA');
    expect(eventStudyState(e)).toBe('NOT_COMPUTED');
  });

  it('★ 四类标的级状态各一断言（COMPUTED / NOT_COMPUTED / UNAVAILABLE / INSUFFICIENT）', () => {
    const participant = (market_data?: string) => ({
      security_id: 'SID', ticker: '000001', name: '测试标的',
      category: 'MARKET_PARTICIPANT' as const, rationale: '测试用', source: 'test', market_data,
    });
    const computed = mkEvent({ market_performance: mkMp({ SID: { trading_days: 100, period_return_pct: 1 } }) });
    const notComputed = mkEvent({ market_performance: mkMp({}) });
    const unavailable = mkEvent({ participants: [participant('无登记行情')] });
    const insufficient = mkEvent({ market_performance: mkMp({ SID: { trading_days: 30, period_return_pct: 1 } }) });

    expect(marketDataStatus(computed, 'SID')).toBe('COMPUTED');
    expect(marketDataStatus(notComputed, 'SID')).toBe('NOT_COMPUTED');
    expect(marketDataStatus(unavailable, 'SID')).toBe('UNAVAILABLE');
    expect(marketDataStatus(insufficient, 'SID')).toBe('INSUFFICIENT');
  });

  it('★★ 端点不可达 → INSUFFICIENT（交易日数量达标也**不等于**完整窗口已计算）', () => {
    const e = mkEvent({
      market_performance: mkMp({
        SID: {
          trading_days: 100, period_return_pct: 1.2,
          first: { date: '2020-03-02', close: 10 }, last: { date: '2020-06-30', close: 11 },
        },
      }),
    });
    const c = marketDataCoverage(e, 'SID');
    expect(c.tradingDays).toBe(100);
    expect(c.ratio).toBe(1);                       // ★ 数量阈值达标
    expect(c.endpointsCovered).toBe(false);        // ★ 但窗口起点端点不可达
    expect(c.status).toBe('INSUFFICIENT');
    expect(c.reasons.join('；')).toContain('窗口起点端点不可达');
  });

  it('★ 覆盖不足的 reasons 明确区分「交易日数量不足」与「端点不可达」', () => {
    const fewDays = mkEvent({
      market_performance: mkMp({ SID: { trading_days: 30, period_return_pct: 1 } }),
    });
    const c = marketDataCoverage(fewDays, 'SID');
    expect(c.status).toBe('INSUFFICIENT');
    expect(c.reasons.join('；')).toContain('交易日覆盖');
    expect(c.reasons.join('；')).not.toContain('端点不可达');
  });
});

/* ------------------------------------ I. ★★ 2026-10-16 三项修复的回归（真实缺陷，非凑数） */

describe('I. 2026-10-16 修复回归', () => {
  /** 取某题材某事件（原始 doc，不经过适配器改写） */
  const rawEvent = (themeId: string, eventId: string): HistoricalEvent => {
    const m = eventMapByTheme(themeId)!;
    const e = (m.doc.events as HistoricalEvent[]).find((x) => x.event_id === eventId);
    if (!e) throw new Error(`未找到事件 ${themeId}/${eventId}`);
    return e;
  };

  it('★★ 报道当日涨幅渲染 `reported_same_day_moves`（by_security 为 null ≠ 无数据）', () => {
    // 真实数据：FLU-2017-AVIAN 的 observed_performance.by_security 是 null，
    // 但同期报道点名的 10 只当日涨幅一直在 `reported_same_day_moves` 里 ——
    // 旧组件只读 by_security → 页面恒显「无行情」，而 note 又引用并不存在的「上表」。
    const e = rawEvent('FLU', 'FLU-2017-AVIAN');
    expect(e.observed_performance.by_security).toBeNull();
    const moves = e.observed_performance.reported_same_day_moves ?? {};
    expect(Object.keys(moves)).toHaveLength(10);
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('涨停');                       // LAYNE-002166 莱茵生物
    expect(html).toContain('+8.36%');                     // LUKANG-600789 鲁抗医药
    expect(html).not.toContain('无行情');                  // ★ 不得再出现误导性空态
  });

  it('★ 阶段名读取研究侧 `stage` 字段（旧实现只读 phase_type → 渲染成空）', () => {
    // 真实数据：power v0_3 的 phases 用 `stage`，组件原读 `phase_type` → <strong></strong> 空标签
    const e = rawEvent('POWER_SUMMER', 'POWER-2023-SUMMER');
    const ph = (e.phases ?? [])[0];
    expect(ph).toBeTruthy();
    expect(ph.phase_type).toBeUndefined();   // 研究侧**没有**这个字段
    expect(ph.stage).toBeTruthy();           // 真字段是 stage
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).not.toContain('<strong></strong>');
    expect(html).toContain(String(ph.stage));
  });

  it('★ 标的区标题不再硬编码「炒作」——机制池事件同样是研究池', () => {
    // FLU-2018-SEASONAL 的 participants 是**机制研究池**（未按收益筛选），
    // 旧标题「当次历史炒作标的」把研究池说成炒作池（研究池 ≠ 炒作池 正是本文件的核心结论）。
    const e = rawEvent('FLU', 'FLU-2018-SEASONAL');
    expect(e.participants.length).toBeGreaterThan(0);
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('事件相关标的');
    expect(html).not.toContain('炒作标的');
  });

  it('★★ 事件级 by_security 不得出现重复序列 id（与跨年表口径一致）', () => {
    // `YILING-002603` 是 `YILING` 的重复碎片序列（同窗口数值完全相同）——
    // 曾有三个事件用它当键，与同文件跨年表的 `YILING` 撞成两个 id。
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        const keys = Object.keys(e.market_performance?.by_security ?? {});
        expect(keys, `${m.theme_id}/${e.event_id}`).not.toContain('YILING-002603');
        const seen = new Set<string>();
        for (const k of keys) {
          expect(seen.has(k), `${m.theme_id}/${e.event_id} 重复键 ${k}`).toBe(false);
          seen.add(k);
        }
      }
    }
    // 跨年表侧仍用 YILING，且同一文件内两个口径已统一
    const cy = crossYearComparisonOf(eventMapByTheme('FLU')!.doc)!;
    const anyYear = cy.years.find((y) => (y.by_security ?? {})['YILING']);
    expect(anyYear, '跨年表应仍含 YILING').toBeTruthy();
  });

  it('★★ 反例事件不再被标为「机制不同轴」的 THEME_ADJACENT', () => {
    // power 的两个 COUNTEREXAMPLE 是迎峰度夏**同机制**的负面结果；
    // 旧分类 THEME_ADJACENT（定义：机制不同轴、仅供参考）会把最强负面证据挡在范围外。
    const m = eventMapByTheme('POWER_SUMMER')!.doc as unknown as {
      events: { event_id: string; event_class: string }[];
    };
    for (const id of ['POWER-2017-SUMMER-COUNTEREXAMPLE', 'POWER-2024-SUMMER-COUNTEREXAMPLE']) {
      const e = m.events.find((x) => x.event_id === id)!;
      expect(e.event_class).toBe('THEME_DIRECT');
    }
    // label 仍写明「反例」——证据方向不因改分类而丢失
    const labels = m.events.map((x) => (x as unknown as { label: string }).label);
    expect(labels.filter((l) => l.includes('反例'))).toHaveLength(2);
  });
});
