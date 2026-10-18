/**
 * ★★ v0.15：汽车智能化题材纵切片 —— 数据口径测试。
 *
 * 验证的是**可核对性**，不是结论正确性：
 *  ① 每个参与者都能在 canonical export 的 securities 注册表里找到（不编造证券）；
 *  ② category / evidence_level 只用既有枚举（不发明新等级）；
 *  ③ 行情数字内部自洽（超额 = 个股 − 基准；first/last/high 的日期与数值关系成立）；
 *  ④ 无覆盖的标的如实留 error（不补 0、不借数）；
 *  ⑤ 题材边界：不把新能源消费 / 购置税叙事混进「智能化」。
 */
import { describe, it, expect } from 'vitest';

import { eventMapByTheme } from '../historicalEventMaps';
import { themeSecurityIndexOf } from '../themeSecurityIndex';
import timelineExport from '../../../../exports/timeline_export_v1.json';

const doc = eventMapByTheme('AUTO_INTELLIGENCE')!.doc;
const exportSecurities = (timelineExport as {
  securities: { security_id: string; ticker: string; name: string }[];
}).securities;

const PART_CATEGORIES = new Set([
  'MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'INSUFFICIENT',
]);
const EVIDENCE_LEVELS = new Set(['REPORT_NAMED', 'BUSINESS_VERIFIED']);

describe('汽车智能化题材 · 结构', () => {
  it('★★ 6 个事件，id 唯一，年份升序可读', () => {
    expect(doc.events).toHaveLength(6);
    expect(new Set(doc.events.map((e) => e.event_id)).size).toBe(6);
    for (const e of doc.events) {
      expect(e.event_id.startsWith('AUTO-')).toBe(true);
      expect(Number.isInteger(e.year)).toBe(true);
      expect(e.window_text.length).toBeGreaterThan(4);
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
      if (objId!.startsWith('RC-')) expect(cf!.object_kind).toBe('candidate');
      if (cf!.object_kind === 'candidate') expect(objId!.startsWith('RC-')).toBe(true);
    }
    // 6 个事件 = 6 个不同对象；且不含新能源消费 / 购置税叙事对象
    expect(ids.size).toBe(6);
    for (const bad of ['C-2020-NEV', 'C-2021-NEV', 'C-2022-POLICY', 'RC-2024-SECONDARY']) {
      expect([...ids]).not.toContain(bad);
    }
  });
});

describe('汽车智能化题材 · 参与者与证据', () => {
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
        expect(p.source.length, p.security_id).toBeGreaterThan(2);
      }
    }
    expect(n).toBe(22);                       // 22 条参与记录（6 事件合计）
  });

  it('★★ category / evidence_level 只用既有枚举', () => {
    for (const e of doc.events) {
      for (const p of e.participants) {
        expect(PART_CATEGORIES.has(p.category), `${p.security_id} ${p.category}`).toBe(true);
        expect(EVIDENCE_LEVELS.has(p.evidence_level ?? ''), p.security_id).toBe(true);
        // business_mechanism 必须配 caveat（业务证据 ≠ 驱动证明）
        if (p.business_mechanism) expect(p.business_mechanism_caveat).toBeTruthy();
      }
    }
  });

  it('★★ 关系性质含四类：直接机制 / 间接扩散 / 运营侧反例 / 证据不足', () => {
    const cats = new Set(doc.events.flatMap((e) => e.participants.map((p) => p.category)));
    expect(cats.has('MECHANISM_DIRECT')).toBe(true);
    expect(cats.has('SPILLOVER')).toBe(true);
    expect(cats.has('INSUFFICIENT')).toBe(true);   // 反例（大众交通）
    // 大众交通 = 运营牌照方反例：category=INSUFFICIENT 且说明写在 rationale
    const dt = doc.events.flatMap((e) => e.participants).find((p) => p.security_id === 'DADONGTRAFFIC')!;
    expect(dt.category).toBe('INSUFFICIENT');
    expect(dt.rationale).toContain('反例');
  });

  it('★★ 标的索引：19 只（22 次出现按 security_id 合并），多事件标的带多年份', () => {
    const idx = themeSecurityIndexOf(doc);
    expect(idx.totals.occurrences).toBe(22);
    expect(idx.totals.securities).toBe(19);
    expect(idx.totals.unlinkedReports).toBe(0);
    const desay = idx.entries.find((x) => x.securityId === 'DESAYSV')!;
    expect(desay.eventCount).toBe(2);          // 2023-NOA + 2025-ROBOTAXI
    expect(desay.years).toEqual([2023, 2025]);
    // 跨事件不汇总收益：entry 上不得有聚合收益字段
    const keys = Object.keys(desay);
    for (const bad of ['periodReturnPct', 'totalReturnPct', 'score', 'rank']) {
      expect(keys).not.toContain(bad);
    }
  });
});

describe('汽车智能化题材 · 行情实测（内部自洽）', () => {
  it('★★ 无覆盖如实留 error（赛力斯 series 止于 2021-12-31，不覆盖 2023 窗口）', () => {
    const huawei = doc.events.find((e) => e.event_id === 'AUTO-2023-HUAWEI')!;
    const xk = huawei.market_performance!.by_security.XIAOKANG;
    expect(xk.error).toBe('insufficient_data_in_window');
    // 事件其余 4 只可算
    const ok = Object.entries(huawei.market_performance!.by_security)
      .filter(([, v]) => !v.error).length;
    expect(ok).toBe(4);
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
        // 窗口内 first ≤ high ≤ last? —— 只验证日期顺序与数值关系
        expect(s.first!.date <= s.last!.date, sid).toBe(true);
        expect(s.high!.close!, sid).toBeGreaterThanOrEqual(Math.min(s.first!.close!, s.last!.close!));
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
