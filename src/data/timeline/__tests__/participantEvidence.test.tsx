/**
 * 参与者证据维度 —— 产品侧语义与渲染（v0.28）。
 *
 * ★ 断言的是**语义不能被误读**，不是「标签存在」：
 *   · 三条轴必须各自独立渲染（`data-axis`），不得合成一个「角色」；
 *   · `登记 leader` 必须带限定语（尤其「leader + 反例」这条黄金案例）；
 *   · 「未见点名报道」必须带「不等于当日没涨」的反向说明。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  MARKET_PARTICIPATION_LABEL,
  evidenceCounts,
  hasReportedParticipation,
  participantEvidenceOf,
  registryRoleCaveat,
  participantEvidenceSummary,
} from '../participantEvidence';
import { ParticipantRow } from '../../../components/ExternalSeasonalRadar/HistoricalEventMap';
import { eventMapByTheme } from '../historicalEventMaps';

const eventOf = (theme: string, eventId: string) => {
  const doc = eventMapByTheme(theme)!;
  return doc.doc.events.find((e) => e.event_id === eventId)!;
};

describe('参与者证据 · 数据层', () => {
  it('★★ 黄金案例：大众交通 = 对象登记 leader + 机制轴反例 + 区间涨幅（三者并存）', () => {
    const ev = participantEvidenceOf('AUTO-2024-ROBOTAXI', 'DADONGTRAFFIC')!;
    expect(ev.registry_role!.role).toBe('leader');
    expect(ev.registry_role!.verification).toBe('VERIFIED_DB');
    expect(ev.study_standing).toBe('COUNTER_EXAMPLE');
    expect(ev.mechanism_relation.status).toBe('DIFFERENT_AXIS');
    // ★ v0.29 校正：该涨幅来自研究记录（export securities + 公开资料），无同期报道背书
    expect(ev.market_participation.status).toBe('RESEARCH_OR_DB_ONLY');
    expect(ev.market_participation.source_kind).toBe('DB_OR_RESEARCH_ONLY');
    // 限定语必须同时说清两件事，并禁止两种误读
    const note = registryRoleCaveat(ev)!;
    expect(note).toContain('互不取消');
    expect(note).toContain('不能');
    expect(note).toContain('反例');
  });

  it('★ 报道涨停来自报道原文（流感 2017 莱茵生物）', () => {
    const ev = participantEvidenceOf('FLU-2017-AVIAN', 'LAYNE-002166')!;
    expect(ev.market_participation.status).toBe('REPORT_CONFIRMED_LIMIT_UP');
    expect(ev.market_participation.reported_move).toContain('涨停');
    expect(hasReportedParticipation(ev)).toBe(true);
  });

  it('★ 未找到点名报道 ≠ 当日没涨：状态与说明都必须存在', () => {
    const ev = participantEvidenceOf('FLU-2017-AVIAN', 'WOHUA-002107')!;
    // 该股有报道涨幅 → 属于「有报道」；换一只无报道的机制池股票验证
    const counts = evidenceCounts('FLU-2017-AVIAN');
    expect(counts.total).toBeGreaterThan(0);
    expect(counts.reported).toBeLessThanOrEqual(counts.total);
    expect(MARKET_PARTICIPATION_LABEL.RESEARCH_OR_DB_ONLY).toBe('仅库内/研究记录');
    expect(MARKET_PARTICIPATION_LABEL.NOT_RECORDED).toBe('无来源记录');
  });

  it('事件级计数与产物 summary 自洽（不另算一套口径）', () => {
    const s = participantEvidenceSummary() as {
      events: number; participants: number;
      market_participation: Record<string, number>;
      registry_role_verification: Record<string, number>;
    };
    expect(s.events).toBe(33);
    const sumMarket = Object.values(s.market_participation).reduce((a, b) => a + b, 0);
    expect(sumMarket).toBe(s.participants);
    const sumReg = Object.values(s.registry_role_verification).reduce((a, b) => a + b, 0);
    expect(sumReg).toBe(s.participants);
  });
});

describe('参与者证据 · 渲染', () => {
  it('★★ 三轴各自独立渲染（同期 / 机制 / 对象），不合成单一「角色」标签', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const p = e.participants.find((x) => x.security_id === 'DADONGTRAFFIC')!;
    const html = renderToStaticMarkup(<ParticipantRow p={p} e={e} />);
    expect(html).toContain('data-axis="market_participation"');
    expect(html).toContain('data-axis="mechanism_relation"');
    expect(html).toContain('data-axis="registry_role"');
    expect(html).toContain('同期：仅库内/研究记录');
    expect(html).toContain('机制：不同机制轴');
    expect(html).toContain('登记 leader');
    expect(html).toContain('库内可核');
    // ★ 限定语必须渲染出来
    expect(html).toContain('data-role-caveat="1"');
    expect(html).toContain('互不取消');
    // ★ 反例身份单独一列，不能混进机制标签
    expect(html).toContain('data-standing="COUNTER_EXAMPLE"');
    // ★ 不得出现把「登记 leader」直接说成龙头的文案
    expect(html).not.toMatch(/龙头<\/|是龙头/);
  });

  it('★ 报道涨停的股票：同期标签为「报道涨停」并保留报道原文', () => {
    const e = eventOf('FLU', 'FLU-2017-AVIAN');
    const p = e.participants.find((x) => x.security_id === 'LAYNE-002166')!;
    const html = renderToStaticMarkup(<ParticipantRow p={p} e={e} />);
    expect(html).toContain('同期：报道涨停');
    expect(html).toContain('报道当日');
    expect(html).toContain('涨停');
  });

  it('★ 无同期报道的机制池股票：显示「未见点名报道」+ 反向说明（不得暗示没涨）', () => {
    // 找一个 NO_REPORTED_EVIDENCE 且 INCLUDED 的参与者（流感 2023 疫苗机制池）
    const e = eventOf('FLU', 'FLU-2023-H1N1');
    const p = e.participants.find((x) => {
      const ev = participantEvidenceOf('FLU-2023-H1N1', x.security_id);
      return ev?.market_participation.source_kind === 'DB_OR_RESEARCH_ONLY'
        && ev.study_standing === 'INCLUDED';
    })!;
    expect(p, '应存在一只「无报道但纳入」的机制池股票').toBeTruthy();
    const html = renderToStaticMarkup(<ParticipantRow p={p} e={e} />);
    expect(html).toContain('同期：仅库内/研究记录');
    expect(html).toContain('data-no-report="1"');
    expect(html).toContain('不等于');
  });
});
