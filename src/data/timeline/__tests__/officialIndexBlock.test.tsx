/**
 * 官方指数并列行情（Wave 2.1 / v0.56）—— 展示层不变量。
 *
 * ★ 全部使用**合成 fixture 数值**（明显是假的），因为真实中证派生收益在授权明确前
 *   **不得**进入仓库与公开页面。本测试只验证「结构与语义」。
 *
 * 断言六件事：
 *  ① 区块能渲染出指数名称/代码/窗口/区间收益/基准/超额/发布日/基日；
 *  ② `backfilled` 三态语义（true 警示 / false 说明 / null 未知且不得当 false）；
 *  ③ 缺失字段显示「字段缺失」，**不补 0**、不静默成 false；
 *  ④ 官方口径**不覆盖**原有 `board` / `market_performance`（两区块并存、数值互不串）；
 *  ⑤ 没有 `official_index` 时区块不渲染（生产现状）；
 *  ⑥ 两个 Research Candidate 的研究状态不因行情接入而变化。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { EventCardBody, OfficialIndexBlock } from '../../../components/ExternalSeasonalRadar/HistoricalEventMap';
import { eventMapByTheme } from '../historicalEventMaps';
import type { HistoricalEvent, OfficialIndexPerformance } from '../historicalEventMaps';
import { eventRoles, roleCounts } from '../historicalMarketRoles';

const SEMI = eventMapByTheme('SEMICONDUCTOR_AI')!.doc.events as HistoricalEvent[];
const eventOf = (id: string) => SEMI.find((e) => e.event_id === id)!;

/** ★ 合成 fixture：数值明显是假的，不代表任何真实官方行情。 */
function fakeOI(over: Partial<OfficialIndexPerformance> = {}): OfficialIndexPerformance {
  return {
    provider: 'FIXTURE-PROVIDER',
    index_code: 'T99999',
    index_name: '合成测试指数（非真实）',
    identity: 'OFFICIAL_EXACT',
    identity_note: '★ 合成 fixture，仅用于结构测试。',
    published_from: '2013-07-15',
    base_date: '2004-12-31',
    base_value: 1000,
    source_first_date: '2005-01-01',
    source_last_date: '2026-10-23',
    rows_before_publish: 2068,
    backfilled: false,
    window: ['2023-01-30', '2023-04-10'],
    window_actual: {
      first_trade_date: '2023-01-30', last_trade_date: '2023-04-10',
      first_close: 5000, last_close: 6000, trading_days: 50,
    },
    period_return_pct: 12.34,
    benchmark_index_code: 'B00000',
    benchmark_index_name: '合成基准',
    benchmark_return_pct: -1.11,
    excess_period_pp: 13.45,
    price_basis: '合成点位',
    source_url: 'https://example.invalid/a',
    benchmark_source_url: 'https://example.invalid/b',
    status: 'COMPUTED',
    error: null,
    calculation_note: '区间收益 = 末交易日 close / 首交易日 close − 1；★ 首尾收盘口径：…；不插值。',
    ...over,
  };
}

const withOI = (oi: OfficialIndexPerformance | null) =>
  ({ ...eventOf('SEMI-2023-AI-COMPUTE'), official_index: oi }) as HistoricalEvent;

describe('官方指数并列行情 · 展示', () => {
  it('① 渲染指数名称/代码/窗口/收益/基准/超额/发布日/基日', () => {
    const html = renderToStaticMarkup(<OfficialIndexBlock e={withOI(fakeOI())} />);
    expect(html).toContain('data-official-index="T99999"');
    expect(html).toContain('合成测试指数（非真实）');
    expect(html).toContain('2023-01-30 ~ 2023-04-10');
    expect(html).toContain('+12.34%');
    expect(html).toContain('+13.45pp');
    expect(html).toContain('-1.11%');
    expect(html).toContain('发布日 <strong>2013-07-15</strong>');
    expect(html).toContain('2068');
    // ★ 必须显式声明「两套口径不合并」
    expect(html).toContain('data-oi-separate="1"');
    expect(html).toContain('不合并成一个收益值');
  });

  it('② backfilled 三态语义', () => {
    const t = renderToStaticMarkup(<OfficialIndexBlock e={withOI(fakeOI({ backfilled: true }))} />);
    expect(t).toContain('data-oi-backfilled="true"');
    expect(t).toContain('事后回溯');
    expect(t).toContain('不得');

    const f = renderToStaticMarkup(<OfficialIndexBlock e={withOI(fakeOI({ backfilled: false }))} />);
    expect(f).toContain('data-oi-backfilled="false"');
    expect(f).toContain('全部落在发布日之后');
    // ★ 即使窗口级 false，也要说明「指数序列本身仍含发布前回溯段」
    expect(f).toContain('发布前数据点');

    const u = renderToStaticMarkup(<OfficialIndexBlock e={withOI(fakeOI({ backfilled: null }))} />);
    expect(u).toContain('data-oi-backfilled="unknown"');
    expect(u).toContain('未知');
    expect(u).toContain('不得');
  });

  it('③ 缺失字段显示「字段缺失」，不补 0', () => {
    const html = renderToStaticMarkup(<OfficialIndexBlock e={withOI(fakeOI({
      period_return_pct: null, excess_period_pp: null, benchmark_return_pct: null,
      missing_required_fields: ['period_return_pct', 'excess_period_pp', 'benchmark_return_pct'],
    }))} />);
    expect(html).toContain('字段缺失');
    expect(html).not.toContain('+0.00%');
    expect(html).not.toContain('+0.00pp');
    expect(html).toContain('data-oi-missing="period_return_pct,excess_period_pp,benchmark_return_pct"');
    expect(html).toContain('不补 0、不填 false');
  });

  it('④ 官方口径不覆盖原 board / market_performance（两区块并存且数值互不串）', () => {
    const base = eventOf('SEMI-2023-AI-COMPUTE');
    const htmlBefore = renderToStaticMarkup(<EventCardBody e={base} />);
    const htmlAfter = renderToStaticMarkup(<EventCardBody e={withOI(fakeOI())} />);

    // ① 没有 official_index 时根本没有官方区块
    expect(htmlBefore).not.toContain('官方指数并列行情');
    expect(htmlAfter).toContain('官方指数并列行情');

    // ② 原有「实测行情」表的数值在注入前后**完全一致**（逐个股断言，不用切片）
    for (const token of ['+228.1%', '+230.4pp', '+8.0%', '+10.3pp', '+23.1%', '+25.4pp', '-2.3%']) {
      expect(htmlBefore, token).toContain(token);
      expect(htmlAfter, token).toContain(token);
    }
    expect(htmlBefore).toContain('实测行情');
    expect(htmlAfter).toContain('实测行情');

    // ③ 官方数值**只**出现在官方区块（以区块起点为界切开）
    const [before, after] = htmlAfter.split('class="fem-official-index"');
    expect(before).not.toContain('+12.34%');
    expect(before).not.toContain('+13.45pp');
    expect(after).toContain('+12.34%');
    expect(after).toContain('+13.45pp');
  });

  it('⑤ 生产产物当前无 official_index → 区块不渲染', () => {
    for (const e of SEMI) {
      expect(e.official_index ?? null, e.event_id).toBeNull();
      expect(renderToStaticMarkup(<OfficialIndexBlock e={e} />)).toBe('');
    }
  });

  it('⑥ 两个 Research Candidate 的研究状态不因行情接入而变化', () => {
    const before = {
      a: eventRoles('SEMI-2020-CHIPSHORTAGE')!.research_status,
      b: eventRoles('SEMI-2024-FUND3')!.research_status,
    };
    expect(before.a).toBe('RESEARCHED_PIT');
    expect(before.b).toBe('DERIVED_FROM_MARKET');
    const cntBefore = { a: roleCounts('SEMI-2020-CHIPSHORTAGE'), b: roleCounts('SEMI-2024-FUND3') };
    // 注入官方指数后重新渲染，不应改变角色计数与状态
    renderToStaticMarkup(<EventCardBody e={{ ...eventOf('SEMI-2020-CHIPSHORTAGE'), official_index: fakeOI() } as HistoricalEvent} />);
    renderToStaticMarkup(<EventCardBody e={{ ...eventOf('SEMI-2024-FUND3'), official_index: fakeOI() } as HistoricalEvent} />);
    expect(eventRoles('SEMI-2020-CHIPSHORTAGE')!.research_status).toBe(before.a);
    expect(eventRoles('SEMI-2024-FUND3')!.research_status).toBe(before.b);
    expect(roleCounts('SEMI-2020-CHIPSHORTAGE')).toEqual(cntBefore.a);
    expect(roleCounts('SEMI-2024-FUND3')).toEqual(cntBefore.b);
    // ★ 官方指数不得把任何参与者标成「领导股」
    expect(roleCounts('SEMI-2020-CHIPSHORTAGE').leaderNamed).toBe(0);
    expect(roleCounts('SEMI-2024-FUND3').leaderNamed).toBe(0);
  });

  it('⑦ 覆盖半导体地图的全部事件（数量以仓库实际清单为准）', () => {
    expect(SEMI.length).toBe(7);
    for (const e of SEMI) {
      const html = renderToStaticMarkup(<EventCardBody e={{ ...e, official_index: fakeOI() } as HistoricalEvent} />);
      expect(html, e.event_id).toContain('官方指数并列行情');
    }
  });
});
