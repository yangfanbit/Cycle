/**
 * 历史市场角色（PIT）—— 产品侧语义与渲染（v0.29）。
 *
 * 断言的是**不能误读**的三件事：
 *  ① 「报道点名」不等于「龙头」——库内没有任何 `PIT_MEDIA_NAMED_LEADER`；
 *  ② 事后集合必须标为后验、不得与 PIT 角色混排；
 *  ③ 未绑定到地图参与者的角色必须显式标出（不强行挂靠）。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  MARKET_ROLE_LABEL,
  MARKET_ROLE_MEANING,
  eventRoles,
  marketRoleOf,
  roleCounts,
  unboundRoles,
} from '../historicalMarketRoles';
import { EventCardBody } from '../../../components/ExternalSeasonalRadar/HistoricalEventMap';
import { eventMapByTheme } from '../historicalEventMaps';

const eventOf = (theme: string, eventId: string) =>
  eventMapByTheme(theme)!.doc.events.find((e) => e.event_id === eventId)!;

describe('历史市场角色 · 数据', () => {
  it('★★ 全库没有「报道称龙头」—— 报道点名 ≠ 龙头', () => {
    const all = ['AUTO-2024-ROBOTAXI', 'FLU-2017-AVIAN', 'PUBLICHEALTH-2019-WUHAN'];
    for (const eid of all) {
      const c = roleCounts(eid);
      expect(c.leaderNamed, eid).toBe(0);
    }
    expect(MARKET_ROLE_LABEL.PIT_MEDIA_NAMED_LEADER).toBe('报道称龙头');
    expect(MARKET_ROLE_MEANING.PIT_MEDIA_NAMED_MOVER).toContain('不等于');
  });

  it('★ Robotaxi：PIT 角色 5 条、事后集合 5 只且标为后验', () => {
    const e = eventRoles('AUTO-2024-ROBOTAXI')!;
    expect(e.research_status).toBe('RESEARCHED_PIT');
    expect(e.roles).toHaveLength(5);
    expect(e.posthoc_leader_set!.posthoc).toBe(true);
    expect(e.posthoc_leader_set!.pit_safe).toBe(false);
    expect(e.posthoc_leader_set!.survivorship_note).toContain('后验');
    // 大众交通是盘面异动（非报道定性）
    expect(marketRoleOf('AUTO-2024-ROBOTAXI', 'DADONGTRAFFIC')!.role).toBe('PIT_MARKET_OBSERVED');
    // 天迈科技是报道点名（07-10，high）
    expect(marketRoleOf('AUTO-2024-ROBOTAXI', 'TIANMAI')).toBeNull(); // 未绑定到地图
    expect(unboundRoles('AUTO-2024-ROBOTAXI').map((r) => r.source_security_id).sort())
      .toEqual(['TIANMAI', 'XINGYUYUDA']);
  });

  it('★★ 切片：07-08 不可用、07-10 起可用；覆盖范围必须三态明确', () => {
    const e = eventRoles('AUTO-2024-ROBOTAXI')!;
    expect(e.pit_slices[0].basket_status).toBe('NOT_USABLE');
    expect(e.pit_slices[1].basket_status).toBe('USABLE');
    const byDate = Object.fromEntries(e.pit_slices.map((s) => [s.date, s]));
    // 07-08：原始 1 只，全部可绑定 → FULL
    expect(byDate['2024-07-08'].match_scope).toBe('FULL');
    expect(byDate['2024-07-08'].matches_document).toBe(true);
    // 07-10 / 07-15：原始 4 / 5 只，地图只覆盖 2 / 3 只 → SUBSET（**不是**完全一致）
    for (const d of ['2024-07-10', '2024-07-15']) {
      expect(byDate[d].match_scope, d).toBe('SUBSET');
      expect(byDate[d].matches_document, d).toBe(false);
      expect(byDate[d].not_in_map!.sort()).toEqual(['TIANMAI', 'XINGYUYUDA']);
      expect(byDate[d].not_in_map_names!.sort()).toEqual(['天迈科技', '星网宇达']);
      expect(byDate[d].bound_count!).toBeLessThan(byDate[d].documented_count!);
    }
    // 任何切片都不允许 MISMATCH
    for (const s of e.pit_slices) expect(s.match_scope).not.toBe('MISMATCH');
  });

  it('★★ 超级真菌：8 条角色识别日 = 报道发布日 2019-04-11（不是事实日 04-08）', () => {
    const e = eventRoles('SUPERFUNGUS-2019-CANDIDA')!;
    expect(e.research_status).toBe('DERIVED_FROM_REPORT');
    expect(e.roles).toHaveLength(8);
    for (const r of e.roles) {
      expect(r.identified_date, r.security_id ?? '').toBe('2019-04-11');
      expect(r.evidence.published_at ?? '', r.security_id ?? '').toBe('2019-04-11');
      // 事实日期保留原样（东北制药的「04-11 涨逾 5%」来自 04-11 那条）
      expect(['2019-04-10', '2019-04-11']).toContain(r.evidence.fact_date ?? '');
    }
  });

  it('★ 盘面角色（DERIVED_FROM_MARKET）不得声称媒体定性', () => {
    const e = eventRoles('AUTO-2023-NOA')!;
    expect(e.research_status).toBe('DERIVED_FROM_MARKET');
    const obs = e.roles.filter((r) => r.role === 'PIT_MARKET_OBSERVED');
    expect(obs.length).toBeGreaterThan(0);
    for (const r of obs) {
      expect(r.evidence.source_type).not.toContain('同期报道');
      // ★★ v0.31：支持性证据只含识别日及之前的信号，且带计算基础
      const asOf = r.evidence.limit_up_days_as_of!;
      expect(asOf.length).toBeGreaterThanOrEqual(2);
      for (const x of asOf) {
        expect(x.date <= r.identified_date, `${r.security_id}/${x.date}`).toBe(true);
        expect(['both_series_agree', 'adjusted_ratio_ex_dividend',
                'adjusted_ratio_action_day']).toContain(x.basis);
      }
      expect(r.evidence.evidence_as_of_date).toBe(r.identified_date);
      expect(r.confidence).toBe('medium');
    }
  });

  it('★ 未研究的事件必须写明缺什么（不得静默留空）', () => {
    // ★ v0.43：GAMELICENSE 已补 PIT 报道证据 → 空态断言改用**仍未研究**的事件
    const e = eventRoles('POWER-2022-SUMMER')!;
    expect(e.research_status).toBe('NOT_RESEARCHED');
    expect(e.roles).toHaveLength(0);
    expect(e.gaps.length).toBeGreaterThan(0);
  });

  it('★★ v0.43：补证后的事件必须转为 RESEARCHED_PIT，且仍不出现「报道称龙头」', () => {
    const e = eventRoles('MEDIA-2018-GAMELICENSE')!;
    expect(e.research_status).toBe('RESEARCHED_PIT');
    expect(e.roles.length).toBeGreaterThanOrEqual(2);
    expect(roleCounts('MEDIA-2018-GAMELICENSE').leaderNamed).toBe(0);
    for (const r of e.roles) {
      // 每个角色都必须带 URL + 支持性证据，且证据日期 ≤ 识别日
      const label = String(r.security_id);
      expect(String(r.evidence.url ?? ''), label).toMatch(/^https?:\/\//);
      expect(r.pit_safe, label).toBe(true);
      for (const x of r.evidence.supporting_evidence ?? []) {
        expect(x.date <= r.identified_date, `${label} 证据 ${x.date}`).toBe(true);
      }
    }
  });
});

describe('历史市场角色 · 渲染', () => {
  it('★★ 事件卡出现独立「历史市场角色」区块，且与参与证据分开', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('data-market-roles="1"');
    expect(html).toContain('历史市场角色（Point-in-Time）');
    expect(html).toContain('已做 Point-in-Time 研究');
    // 三条切片都在
    for (const d of ['2024-07-08', '2024-07-10', '2024-07-15']) {
      expect(html).toContain(`data-slice-date="${d}"`);
    }
    // 事后集合单独一块并带幸存者偏差说明
    expect(html).toContain('data-posthoc="1"');
    expect(html).toContain('后验');
    // 不得把「报道点名」渲染成龙头
    expect(html).not.toContain('报道称龙头</span>');
    // ★ 两处「报道点名」口径不同 → 必须有显式说明，否则用户会把数量差读成矛盾
    expect(html).toContain('data-role-scope-note="1"');
    expect(html).toContain('口径不同');
    // ★ 计数行不得把「有业务说明但机制未定级」算进「机制已确认」
    expect(html).toContain('机制已确认');
    expect(html).toContain('有业务说明但机制未定级');
  });

  it('★★ 切片必须显示覆盖缺口（未纳入本地图的成员 + 原始规模 vs 地图覆盖）', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    // 三态标记
    expect(html).toContain('data-match-scope="FULL"');
    expect(html).toContain('data-match-scope="SUBSET"');
    expect(html).not.toContain('data-match-scope="MISMATCH"');
    // 缺口数字与成员名
    expect(html).toContain('data-slice-gap="2"');
    expect(html).toContain('未纳入本地图');
    expect(html).toContain('星网宇达');
    expect(html).toContain('天迈科技');
    // 原始规模 vs 地图覆盖
    expect(html).toContain('原始研究记录 4 只，地图覆盖 2 只');
    expect(html).toContain('原始研究记录 5 只，地图覆盖 3 只');
  });

  it('★★★ PIT 封口：支持性证据不得晚于识别日；识别日后的信号只能进事后集合', () => {
    // AUTO-2024-V2X / SUOLING：识别日 2024-06-18，之后还有 06-19~06-21 的信号
    const e = eventRoles('AUTO-2024-V2X')!;
    const r = e.roles.find((x) => x.security_id === 'SUOLING')!;
    expect(r.role).toBe('PIT_MARKET_OBSERVED');
    expect(r.identified_date).toBe('2024-06-18');
    expect(r.evidence.evidence_as_of_date).toBe('2024-06-18');
    expect(r.evidence.limit_up_days_as_of!.map((x) => x.date)).toEqual(['2024-06-17', '2024-06-18']);
    expect(r.evidence.retrospective_limit_up_days!.map((x) => x.date))
      .toEqual(['2024-06-19', '2024-06-20', '2024-06-21']);
    expect(r.pit_safe).toBe(true);
    // 两个集合不得重叠
    const a = new Set(r.evidence.limit_up_days_as_of!.map((x) => x.date));
    for (const x of r.evidence.retrospective_limit_up_days!) expect(a.has(x.date)).toBe(false);
  });

  it('★★ 窗口语义：行情窗口与 PIT 观察窗口分开，Robotaxi 观察窗口早于行情窗口', () => {
    const e = eventRoles('AUTO-2024-ROBOTAXI')!;
    const ws = e.window_semantics!;
    expect(ws.market_performance_window).toEqual(['2024-07-11', '2024-07-29']);
    expect(ws.pit_observation_window![0]).toBe('2024-07-08');
    expect(ws.pit_observation_window![0] < ws.market_performance_window![0]).toBe(true);
  });

  it('★★ 页面必须把「识别日之后的信号」标成全窗口事后统计', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-V2X');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('data-signals-retro="3"');
    expect(html).toContain('全窗口事后统计');
    expect(html).toContain('不参与本角色成立判断');
    // 支持性证据与事后统计必须分开呈现
    expect(html).toContain('截至识别日');
  });

  it('★ 未绑定角色显式标注「未在地图参与者中」+ 名称匹配待确认', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('data-role-unbound="1"');
    expect(html).toContain('未在地图参与者中');
    expect(html).toContain('data-role-review="NAME_MATCH_ONLY"');
  });

  // ───────────────────────────── v0.32：PIT 全路径封口

  it('★★★ 大众交通 7/8 记录：支持性证据只有 7/8，7/9 事实被隔离到事后背景', () => {
    const e = eventRoles('AUTO-2024-ROBOTAXI')!;
    const r = e.roles.find((x) => x.source_security_id === 'DAZHONGTONG')!;
    expect(r.identified_date).toBe('2024-07-08');
    expect(r.support_level).toBe('EARLY_LOW_CONFIDENCE_OBSERVATION');
    expect(r.confidence).toBe('low');
    expect(r.evidence.evidence_as_of_date).toBe('2024-07-08');
    expect(r.evidence.supporting_evidence!.map((x) => x.date)).toEqual(['2024-07-08']);
    expect(r.evidence.supporting_evidence![0].text).toContain('6.12');
    expect(r.evidence.posthoc_background!.map((x) => x.date)).toEqual(['2024-07-09']);
    // 支持性文字里不得出现 7/9
    for (const blob of [r.evidence.source_text, r.notes, r.evidence.summary]) {
      expect(String(blob ?? '')).not.toContain('7/9');
      expect(String(blob ?? '')).not.toContain('2024-07-09');
    }
    // 盘面记录不得伪造发布日
    expect(r.evidence.published_at ?? null).toBeNull();
    // 降级必须写明限制
    expect((r.support_limits ?? []).join(' ')).toContain('不构成');
  });

  it('★★ 页面：早期低置信观察徽标 + 支持性证据截止日 + 事后背景独立成段', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('data-support-level="EARLY_LOW_CONFIDENCE_OBSERVATION"');
    expect(html).toContain('data-support-as-of="2024-07-08"');
    expect(html).toContain('早期低置信观察');
    expect(html).toContain('支持性证据截至 2024-07-08');
    expect(html).toContain('data-posthoc-background="1"');
    expect(html).toContain('事后背景');
    expect(html).toContain('不参与');
    expect(html).toContain('data-support-limits="1"');
  });

  it('★★ 每条 pit_safe 角色都有 support_level 与 evidence_as_of_date（无类别豁免）', () => {
    const allowed = ['AUTO_RULE_MET', 'MEDIA_NAMED_SAME_DAY', 'REPORT_BACKED',
      'EARLY_LOW_CONFIDENCE_OBSERVATION'];
    let n = 0;
    for (const eid of ['AUTO-2024-ROBOTAXI', 'AUTO-2023-NOA', 'SUPERFUNGUS-2019-CANDIDA',
      'SEMI-2019-LOCALIZATION', 'RES-2020-RAREEARTH']) {
      for (const r of eventRoles(eid)!.roles) {
        n += 1;
        expect(allowed, `${eid}/${r.security_id}`).toContain(r.support_level);
        if (r.pit_safe) {
          expect(r.evidence.evidence_as_of_date, `${eid}/${r.security_id}`)
            .toMatch(/^\d{4}-\d{2}-\d{2}$/);
          expect(r.evidence.supporting_evidence!.length, `${eid}/${r.security_id}`)
            .toBeGreaterThan(0);
          for (const x of r.evidence.supporting_evidence!) {
            expect(x.date <= r.identified_date, `${eid}/${r.security_id} 证据 ${x.date}`).toBe(true);
          }
        }
      }
    }
    expect(n).toBeGreaterThan(10);
  });

  it('★★ 来源路径必须指向本次真实输入（不得残留 v0_3）', () => {
    const seen = new Set<string>();
    for (const eid of ['AUTO-2024-ROBOTAXI', 'AUTO-2023-NOA', 'SUPERFUNGUS-2019-CANDIDA',
      'SEMI-2019-LOCALIZATION']) {
      for (const r of eventRoles(eid)!.roles) {
        const rec = String(r.source_record ?? '');
        seen.add(rec);
        expect(rec).not.toContain('participant_evidence_v0_3');
      }
    }
    expect([...seen].some((x) => x.includes('participant_evidence_v0_4.json'))).toBe(true);
  });

  it('★ 未研究事件显示「不设角色」+ 缺什么（不展示假角色）', () => {
    // ★ v0.43：改用仍未研究的事件（GAMELICENSE 已有 PIT 角色）
    const e = eventOf('POWER_SUMMER', 'POWER-2022-SUMMER');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('尚未研究');
    expect(html).toContain('不设角色');
    expect(html).toContain('需补');
  });

  it('★★ v0.43：补证后的事件渲染出角色 + 来源原文链接，且仍标「报道称龙头 0」', () => {
    const e = eventOf('MEDIA', 'MEDIA-2018-GAMELICENSE');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('已做 Point-in-Time 研究');
    expect(html).toContain('报道称龙头 0');
    expect(html).toContain('data-role-url="1"');
    expect(html).toContain('时间切片');
  });
});
