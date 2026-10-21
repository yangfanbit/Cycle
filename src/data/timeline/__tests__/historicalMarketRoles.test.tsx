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

  it('★ 切片：07-08 不可用、07-10 起可用（与原始研究一致）', () => {
    const e = eventRoles('AUTO-2024-ROBOTAXI')!;
    expect(e.pit_slices[0].basket_status).toBe('NOT_USABLE');
    expect(e.pit_slices[1].basket_status).toBe('USABLE');
    for (const s of e.pit_slices) expect(s.matches_document).toBe(true);
  });

  it('★ 未研究的事件必须写明缺什么（不得静默留空）', () => {
    const e = eventRoles('MEDIA-2018-GAMELICENSE')!;
    expect(e.research_status).toBe('NOT_RESEARCHED');
    expect(e.roles).toHaveLength(0);
    expect(e.gaps.length).toBeGreaterThan(0);
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
  });

  it('★ 未绑定角色显式标注「未在地图参与者中」+ 名称匹配待确认', () => {
    const e = eventOf('AUTO_INTELLIGENCE', 'AUTO-2024-ROBOTAXI');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('data-role-unbound="1"');
    expect(html).toContain('未在地图参与者中');
    expect(html).toContain('data-role-review="NAME_MATCH_ONLY"');
  });

  it('★ 未研究事件显示「不设角色」+ 缺什么（不展示假角色）', () => {
    const e = eventOf('MEDIA', 'MEDIA-2018-GAMELICENSE');
    const html = renderToStaticMarkup(<EventCardBody e={e} />);
    expect(html).toContain('尚未研究');
    expect(html).toContain('不设角色');
    expect(html).toContain('需补');
  });
});
