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
import { HistoricalEventMap, MarketPerformanceBlock, ParticipantRow } from '../HistoricalEventMap';
import {
  MARKET_DATA_STATUS_LABEL,
  allResolvedEventMaps,
  eventMapByExternalId,
  eventMapByTheme,
  eventMapIndex,
  eventMapsNotIncluded,
  eventStudyState,
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

  it('★ 四个题材全部解析成功（索引有条目 + 注册表有文档）', () => {
    const maps = allResolvedEventMaps();
    expect(maps.map((m) => m.theme_id).sort()).toEqual(
      ['FLU', 'MEDIA', 'POWER_SUMMER', 'ROBOTICS'].sort());
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

  it('★ 所有题材的事件都有可分析行情（本轮补数生效）', () => {
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        expect(eventStudyState(e), `${m.theme_id}/${e.event_id}`).toBe('HAS_PRICE_DATA');
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
  it('★ FLU 题材已升版 v0_5（6 事件，含 2018/2024 跨年份）', () => {
    const m = eventMapByTheme('FLU')!;
    expect(m.doc.artifact_version).toBe('0.5');
    expect(m.doc.events).toHaveLength(6);
    // ★ 跨年份事件已接入
    expect(m.doc.events.map((e) => e.event_id)).toContain('FLU-2018-SEASONAL');
    expect(m.doc.events.map((e) => e.event_id)).toContain('FLU-2024-SEASONAL');
    // ★ 流感专属的 corrections 更正痕迹仍在
    expect(JSON.stringify(m.doc.corrections)).toContain('600513');
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
    const e = mkEvent({ market_performance: mkMp({ SID: { trading_days: 30 } }) });
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
    const computed = mkEvent({ market_performance: mkMp({ SID: { trading_days: 100 } }) });
    const notComputed = mkEvent({ market_performance: mkMp({}) });
    const unavailable = mkEvent({ participants: [{ security_id: 'SID', ticker: '000001', name: '无行情标的',
      category: 'MARKET_PARTICIPANT', rationale: '测试用', source: 'test', market_data: '无行情' }] });
    const insufficient = mkEvent({ market_performance: mkMp({ SID: { trading_days: 30 } }) });

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
