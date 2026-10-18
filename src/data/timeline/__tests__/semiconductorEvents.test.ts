/**
 * ★★ v0.16：半导体 / AI 算力 / 存储题材纵切片 —— 数据口径测试。
 *
 * 验证的是**可核对性**，不是结论正确性：
 *  ① 参与者都能在 canonical export 的 securities 注册表里找到（不编造证券）；
 *  ② category / evidence_level 只用既有枚举，且**反例（COUNTER_EXAMPLE）≠ 证据不足（INSUFFICIENT）**；
 *  ③ 行情数字内部自洽（超额 = 个股 − 基准）；
 *  ④ 无覆盖的标的如实留 error（不补 0、不借数）—— 大基金三期窗口全无覆盖；
 *  ⑤ 事件都挂库内对象，Research Candidate **不**伪装成 Campaign。
 */
import { describe, it, expect } from 'vitest';

import { eventMapByTheme, eventStudyState, isThemeParticipant } from '../historicalEventMaps';
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
  it('★★ 大基金三期窗口（2024-09→2024-11）全无覆盖 → 逐条如实留 error', () => {
    const e = doc.events.find((x) => x.event_id === 'SEMI-2024-FUND3')!;
    const by = e.market_performance!.by_security;
    for (const [sid, v] of Object.entries(by)) {
      expect(v.error, sid).toBe('insufficient_data_in_window');
    }
    expect(eventStudyState(e)).toBe('NO_PRICE_DATA');
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

  it('★ 每事件都声明 is_campaign_ruling=false（行情不是裁定）', () => {
    for (const e of doc.events) {
      expect(e.market_performance!.is_campaign_ruling).toBe(false);
      expect(e.market_performance!.note).toContain('非 Campaign 裁定');
    }
  });
});
