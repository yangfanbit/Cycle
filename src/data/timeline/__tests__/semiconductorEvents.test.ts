/**
 * ★★ v0.16 建立 · v0.24 重写行情段：半导体 / AI 算力 / 存储题材纵切片 —— 数据口径测试。
 *
 * 验证的是**可核对性**，不是结论正确性：
 *  ① 参与者都能在 canonical export 的 securities 注册表里找到（不编造证券）；
 *  ② category / evidence_level 只用既有枚举，且**反例（COUNTER_EXAMPLE）≠ 证据不足（INSUFFICIENT）**；
 *  ③ 行情数字内部自洽（超额 = 个股 − 基准；至高点 ≥ 区间末值；回撤 ≤ 0）；
 *  ④ ★★ v0.24：大基金三期窗口 4 只标的**已可计算**（各 44 个交易日，口径
 *     `theme_market_performance_v1`）；**真正缺失**的标的仍必须显式留 error（不补 0、不借数）；
 *  ⑤ 事件都挂库内对象，Research Candidate **不**伪装成 Campaign；
 *  ⑥ ★★ 声明的 `study_state` 必须与按数据现算的 `eventStudyState()` 一致（Python 转写 ↔ TS 渲染同规则）。
 */
import { describe, it, expect } from 'vitest';

import {
  eventMapByTheme, eventStudyState, highPointOf, isThemeParticipant, marketDataCoverage,
  allResolvedEventMaps,
} from '../historicalEventMaps';
import { themeSecurityIndexOf } from '../themeSecurityIndex';
import timelineExport from '../../../../exports/timeline_export_v1.json';

const doc = eventMapByTheme('SEMICONDUCTOR_AI')!.doc;
const exportSecurities = (timelineExport as {
  securities: { security_id: string; ticker: string; name: string }[];
}).securities;

const PART_CATEGORIES = new Set([
  'MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'COUNTER_EXAMPLE', 'INSUFFICIENT',
]);
const EVIDENCE_LEVELS = new Set(['REPORT_NAMED', 'BUSINESS_VERIFIED']);

describe('半导体 / AI 算力题材 · 结构', () => {
  it('★★ 7 个事件，id 唯一，类别与必填字段齐全', () => {
    expect(doc.events).toHaveLength(7);
    expect(new Set(doc.events.map((e) => e.event_id)).size).toBe(7);
    for (const e of doc.events) {
      expect(e.event_id.startsWith('SEMI-'), e.event_id).toBe(true);
      expect(Number.isInteger(e.year)).toBe(true);
      expect(e.event_class, e.event_id).toBeTruthy();
      expect(e.window_text.length, e.event_id).toBeGreaterThan(4);
      expect(e.known_gaps.length, e.event_id).toBeGreaterThan(0);
      expect(e.catalysts.length, e.event_id).toBeGreaterThan(0);
      for (const c of e.catalysts) {
        expect(c.date.length, c.text.slice(0, 12)).toBeGreaterThan(3);
        expect(c.source.length).toBeGreaterThan(4);
      }
    }
  });

  it('★★ 事件都挂到库内对象（Campaign 或 Research Candidate），身份不伪装', () => {
    const ids = new Set<string>();
    for (const e of doc.events) {
      const cf = e.campaign_facts;
      expect(cf, e.event_id).toBeTruthy();
      const objId = cf!.object_id ?? cf!.campaign_id;
      expect(objId, e.event_id).toBeTruthy();
      ids.add(objId!);
      // Research Candidate 必须标 object_kind=candidate（不得按 Campaign 呈现）
      if (objId!.startsWith('RC-')) expect(cf!.object_kind, e.event_id).toBe('candidate');
      if (cf!.object_kind === 'candidate') expect(objId!.startsWith('RC-'), e.event_id).toBe(true);
    }
    // 7 个事件 = 7 个不同对象
    expect(ids.size).toBe(7);
    // ★★ 两个官方 INSUFFICIENT 的 Research Candidate 如实保留身份
    expect([...ids]).toContain('RC-2024-SEMI-FUND3');
    expect([...ids]).toContain('RC-2022-SEMI-CHIPSHORTAGE');
  });
});

describe('半导体 / AI 算力题材 · 参与者与证据', () => {
  it('★★ 每个参与者都是 export securities 注册表里的真实条目', () => {
    const byId = new Map(exportSecurities.map((s) => [s.security_id, s]));
    let n = 0;
    for (const e of doc.events) {
      for (const p of e.participants) {
        n += 1;
        const reg = byId.get(p.security_id);
        expect(reg, `${p.security_id} 应在 export 注册表中`).toBeTruthy();
        expect(p.ticker, p.security_id).toBe(reg!.ticker);
        expect(p.name, p.security_id).toBe(reg!.name);
        expect(p.rationale.length, p.security_id).toBeGreaterThan(4);
      }
    }
    expect(n).toBe(29);                       // 29 条参与记录（7 事件合计）
  });

  it('★★ category / evidence_level 只用既有枚举', () => {
    for (const e of doc.events) {
      for (const p of e.participants) {
        expect(PART_CATEGORIES.has(p.category), `${p.security_id} ${p.category}`).toBe(true);
        expect(EVIDENCE_LEVELS.has(p.evidence_level ?? ''), p.security_id).toBe(true);
        if (p.business_mechanism) expect(p.business_mechanism_caveat, p.security_id).toBeTruthy();
      }
    }
  });

  it('★★ 反例（COUNTER_EXAMPLE）与证据不足（INSUFFICIENT）是两回事', () => {
    const all = doc.events.flatMap((e) => e.participants);
    const cats = new Set(all.map((p) => p.category));
    expect(cats.has('MECHANISM_DIRECT')).toBe(true);
    expect(cats.has('SPILLOVER')).toBe(true);
    expect(cats.has('MARKET_PARTICIPANT')).toBe(true);
    expect(cats.has('COUNTER_EXAMPLE')).toBe(true);
    expect(cats.has('INSUFFICIENT')).toBe(true);
    // 京东方A = 显示面板，与集成电路不同轴 → 反例，**不是**证据不足
    const boe = all.find((p) => p.security_id === 'BOE' && p.category === 'COUNTER_EXAMPLE');
    expect(boe, '京东方A 应为 COUNTER_EXAMPLE').toBeTruthy();
    // ★★ 反例与证据不足**都**不属于「本题材方向」（isThemeParticipant=false），但彼此不互等
    const insuff = all.filter((p) => p.category === 'INSUFFICIENT');
    expect(insuff.length).toBeGreaterThan(0);
    for (const p of [...insuff, ...all.filter((x) => x.category === 'COUNTER_EXAMPLE')]) {
      expect(isThemeParticipant(p), p.security_id).toBe(false);
      expect(p.category).not.toBe(
        p.category === 'INSUFFICIENT' ? 'COUNTER_EXAMPLE' : 'INSUFFICIENT');
    }
  });

  it('★★ 标的索引：16 只（29 次出现按 security_id 合并）', () => {
    const idx = themeSecurityIndexOf(doc);
    expect(idx.totals.occurrences).toBe(29);
    expect(idx.totals.securities).toBe(16);
    expect(idx.totals.unlinkedReports).toBe(0);
    const gigadevice = idx.entries.find((x) => x.securityId === 'GIGADEVICE')!;
    expect(gigadevice.eventCount).toBe(3);      // 2019 / 2023 / 2025
    expect(gigadevice.years).toEqual([2019, 2023, 2025]);
    // 跨事件不汇总收益：entry 上不得有聚合收益字段
    for (const bad of ['periodReturnPct', 'totalReturnPct', 'score', 'rank']) {
      expect(Object.keys(gigadevice)).not.toContain(bad);
    }
  });
});

describe('半导体 / AI 算力题材 · 行情实测（内部自洽）', () => {
  it('★★ 大基金三期窗口（2024-09-24 → 2024-11-29）四只标的均已可计算（各 44 个交易日）', () => {
    const e = doc.events.find((x) => x.event_id === 'SEMI-2024-FUND3')!;
    const mp = e.market_performance!;
    expect(mp.window).toEqual(['2024-09-24', '2024-11-29']);
    // ★ 不变量：合同版本必须是「本仓库当前合同」（v2 起），**不写死**具体小版本号以外的东西
    expect(mp.contract_version).toMatch(/^theme_market_performance_v\d+$/);
    expect(mp.contract_version).toBe('theme_market_performance_v2');

    // 基准（同窗口、同口径）
    const bench = mp.benchmark.SH000300;
    expect(bench.trading_days).toBe(44);
    expect(bench.first!.date).toBe('2024-09-24');
    expect(bench.last!.date).toBe('2024-11-29');
    expect(bench.period_return_pct).toBeCloseTo(16.8, 1);
    expect(bench.to_high_pct).toBeCloseTo(27.0, 1);

    const expected: Record<string, [number, string]> = {
      SMIC: [101.3, '2024-11-11'],
      AMEC: [83.6, '2024-11-12'],
      PIOTECH: [86.2, '2024-11-11'],
      HYGON: [61.4, '2024-11-07'],
    };
    for (const [sid, [pct, highDate]] of Object.entries(expected)) {
      const st = mp.by_security[sid];
      expect(st.error, sid).toBeUndefined();
      expect(st.trading_days, sid).toBe(44);
      expect(st.first!.date, sid).toBe('2024-09-24');
      expect(st.last!.date, sid).toBe('2024-11-29');
      expect(st.high!.date, sid).toBe(highDate);
      expect(st.period_return_pct, sid).toBeCloseTo(pct, 1);
      // ★ 窗口状态必须是 COMPUTED（不是「局部数据」）
      expect(marketDataCoverage(e, sid).status, sid).toBe('COMPUTED');
    }
    // ★★ 事件级状态随之更正；但 RC 官方判定不变
    expect(eventStudyState(e)).toBe('HAS_PRICE_DATA');
    expect(e.study_state).toBe('HAS_PRICE_DATA');
    expect(e.campaign_facts!.status).toBe('INSUFFICIENT');
    expect(e.campaign_facts!.object_kind).toBe('candidate');
  });

  it('★★ 至高点 / 回撤 / 区间三者的定义自洽（不得把 peak_date 当个股高点）', () => {
    const e = doc.events.find((x) => x.event_id === 'SEMI-2024-FUND3')!;
    for (const [sid, st] of Object.entries(e.market_performance!.by_security)) {
      if (st.error) continue;
      // 至高点 ≥ 区间末值（至高点 = 窗口内最高收盘价）
      expect(st.to_high_pct!, sid).toBeGreaterThanOrEqual(st.period_return_pct! - 1e-9);
      expect(st.high!.close, sid).toBeGreaterThanOrEqual(st.last!.close - 1e-9);
      // 日期序：first ≤ high ≤ last
      expect(st.first!.date <= st.high!.date, sid).toBe(true);
      expect(st.high!.date <= st.last!.date, sid).toBe(true);
      // 回撤从至高点之后算 → 必然 ≤ 0
      expect(st.max_drawdown_from_high_pct!, sid).toBeLessThanOrEqual(0);
      // ★ 个股高点 ≠ Campaign / RC 的 peak_date（2024-12-31）
      expect(st.high!.date, sid).not.toBe('2024-12-31');
    }
  });

  it('★★ 超额 = 个股 − 基准（同窗口、同口径）', () => {
    for (const e of doc.events) {
      const mp = e.market_performance!;
      const bench = mp.benchmark.SH000300;
      expect(bench.error, e.event_id).toBeUndefined();
      for (const [sid, s] of Object.entries(mp.by_security)) {
        if (s.error) continue;
        expect(s.trading_days!, sid).toBeGreaterThanOrEqual(2);
        expect(s.excess_period_pp!, sid)
          .toBeCloseTo(s.period_return_pct! - bench.period_return_pct!, 1);
        expect(s.excess_to_high_pp!, sid)
          .toBeCloseTo(s.to_high_pct! - bench.to_high_pct!, 1);
        expect(s.first!.date <= s.last!.date, sid).toBe(true);
        expect(s.max_drawdown_from_high_pct!, sid).toBeLessThanOrEqual(0);
      }
    }
  });

  it('★ 真正缺失的窗口仍逐条显式留 error（不补 0、不借数）', () => {
    // 2021 窗口早于拓荆科技上市（2022-04-20）→ 仍不可得
    const eq = doc.events.find((x) => x.event_id === 'SEMI-2021-EQUIPMENT')!;
    expect(eq.market_performance!.by_security.PIOTECH.error).toBe('insufficient_data_in_window');
    expect(eq.market_performance!.by_security.PIOTECH.trading_days).toBeUndefined();
    // 2020 窗口内 TFME 库内无该序列
    const cs = doc.events.find((x) => x.event_id === 'SEMI-2020-CHIPSHORTAGE')!;
    expect(cs.market_performance!.by_security.TFME.error).toBe('insufficient_data_in_window');
    // ★ 不得出现「缺失被写成 0」
    for (const sid of ['PIOTECH', 'TFME']) {
      const block = (sid === 'PIOTECH' ? eq : cs).market_performance!.by_security[sid];
      expect(block.period_return_pct).toBeUndefined();
      expect(block.to_high_pct).toBeUndefined();
    }
  });

  it('★★ v2 起每个标的块显式声明 price_basis（口径不得隐式）', () => {
    for (const e of doc.events) {
      const mp = e.market_performance!;
      for (const [sid, s] of Object.entries(mp.by_security)) {
        expect(s.price_basis, `${e.event_id}/${sid}`).toBe('adjusted_qfq');
      }
      expect(mp.benchmark.SH000300.price_basis, e.event_id).toBe('adjusted_qfq');
    }
  });

  it('★ 每事件都声明 is_campaign_ruling=false（行情不是裁定）', () => {
    for (const e of doc.events) {
      expect(e.market_performance!.is_campaign_ruling).toBe(false);
      expect(e.market_performance!.note).toContain('非 Campaign 裁定');
    }
  });
});

describe('★★ 全部题材 · 声明的行情状态必须与现算一致（Python 转写 ↔ Product 同规则）', () => {
  it('study_state === eventStudyState(event)，且 COMPUTED 的标的必须字段齐全', () => {
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        expect(e.study_state, `${m.theme_id}/${e.event_id}`).toBe(eventStudyState(e));
        for (const p of e.participants) {
          if (!isThemeParticipant(p)) continue;
          const cov = marketDataCoverage(e, p.security_id);
          const st = e.market_performance?.by_security?.[p.security_id];
          if (cov.status === 'COMPUTED') {
            expect(st?.period_return_pct, `${m.theme_id}/${e.event_id}/${p.security_id}`)
              .not.toBeUndefined();
            // ★ 高点日必须可读（兼容扁平 high_date 写法）—— 否则 UI 会静默显示 `—`
            expect(highPointOf(st)?.date, `${m.theme_id}/${e.event_id}/${p.security_id}`)
              .toBeTruthy();
          }
        }
      }
    }
  });
});
