/**
 * ★★ 历史参与标的索引（v0.11）—— 跨事件汇总与证据保留。
 *
 * 全部用仓库真实数据（4 个题材文档），不造假样例；
 * 唯一的合成输入用于验证「报道点名但未关联」的独立状态（真实数据当前没有这种记录）。
 */
import { describe, it, expect } from 'vitest';

import { eventMapByTheme, type HistoricalEventsDoc } from '../historicalEventMaps';
import {
  SECURITY_INDEX_DISCLAIMER,
  evidenceSummaryOf,
  filterSecurityIndex,
  themeSecurityIndexOf,
} from '../themeSecurityIndex';

const flu = themeSecurityIndexOf(eventMapByTheme('FLU')!.doc);
const power = themeSecurityIndexOf(eventMapByTheme('POWER_SUMMER')!.doc);
const media = themeSecurityIndexOf(eventMapByTheme('MEDIA')!.doc);
const robotics = themeSecurityIndexOf(eventMapByTheme('ROBOTICS')!.doc);

const entry = (idx: typeof flu, id: string) => {
  const x = idx.entries.find((e) => e.securityId === id);
  if (!x) throw new Error(`索引里没有 ${id}`);
  return x;
};

describe('题材标的索引 · 跨事件汇总', () => {
  it('★★ 四个题材各自的标的数 / 次数 / 事件数（全部由文档生成）', () => {
    expect(flu.totals).toMatchObject({ securities: 20, occurrences: 42, eventsWithParticipants: 6 });
    expect(power.totals).toMatchObject({ securities: 6, occurrences: 21, eventsWithParticipants: 4 });
    expect(media.totals).toMatchObject({ securities: 4, occurrences: 4, eventsWithParticipants: 2 });
    expect(robotics.totals).toMatchObject({ securities: 5, occurrences: 5, eventsWithParticipants: 1 });
  });

  it('★★ 同一标的跨事件按 `security_id` 关联：华电国际 4 次 / 4 个年份', () => {
    const x = entry(power, 'HUADIAN');
    expect(x.ticker).toBe('600027');
    expect(x.eventCount).toBe(4);
    expect(x.years).toEqual([2017, 2022, 2023, 2024]);
    // 每次出现都保留自己的事件与理由
    expect(x.occurrences.map((o) => o.year)).toEqual([2017, 2022, 2023, 2024]);
    for (const o of x.occurrences) {
      expect(o.eventId).toBeTruthy();
      expect(o.rationale.length).toBeGreaterThan(5);
    }
  });

  it('★★ 名称变体合并到同一 `security_id`（香雪制药 / ST香雪），别名不丢', () => {
    const x = entry(flu, 'XIANGXUE-300147');
    expect(x.ticker).toBe('300147');
    expect(x.eventCount).toBe(3);   // 2017 / 2018 / 2024 三次（名称在 2024 变为「ST香雪」）
    // 展示名 + 别名合起来覆盖两个历史名称
    const names = [x.name, ...x.aliases];
    expect(names).toContain('香雪制药');
    expect(names.some((n) => n.includes('ST香雪'))).toBe(true);
  });

  it('★★ 证据等级**逐次**保留，不合并成单一标签', () => {
    const x = entry(flu, 'BAIKEBIO');   // 百克生物：一次 REPORT_NAMED、一次 BUSINESS_VERIFIED
    const levels = x.occurrences.map((o) => o.evidenceLevel);
    expect(new Set(levels)).toEqual(new Set(['REPORT_NAMED', 'BUSINESS_VERIFIED']));
    // 摘要按类型计数，不分高低
    expect(evidenceSummaryOf(x)).toContain('业务机制已核实 ×1');
    expect(evidenceSummaryOf(x)).toContain('仅报道点名 ×1');
    expect(x.evidenceLevels).toEqual(['BUSINESS_VERIFIED', 'REPORT_NAMED']);
  });

  it('★★ 排序只看名称（不按出现次数 / 涨幅），且确定性', () => {
    const names = flu.entries.map((x) => x.name);
    const sorted = [...names].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
    expect(names).toEqual(sorted);
    // 出现次数不参与排序：3 次的标的可以排在 1 次的后面
    const counts = flu.entries.map((x) => x.eventCount);
    expect(counts).not.toEqual([...counts].sort((a, b) => b - a));
  });

  it('★★ 不提供任何跨事件收益汇总字段（口径不可合并）', () => {
    for (const x of flu.entries) {
      const keys = Object.keys(x);
      for (const banned of ['totalReturn', 'avgReturn', 'score', 'rank', 'relevance']) {
        expect(keys, banned).not.toContain(banned);
      }
      // 每次出现的行情数字只挂在 occurrence 上，不在 entry 上
      expect(keys).not.toContain('periodReturnPct');
    }
  });

  it('★ 声明「参与 ≠ 业务相关 ≠ 上涨」与「不打分 / 不合并收益」', () => {
    // 常量里用 `**` 标强调，比较前先去掉标记（渲染层会转成 <strong>）
    const plainText = SECURITY_INDEX_DISCLAIMER.split('**').join('');
    expect(plainText).toContain('历史参与 ≠ 业务相关 ≠ 行情上涨');
    expect(plainText).toContain('不给概念相关度打分');
    expect(plainText).toContain('不跨事件合并收益');
  });
});

describe('题材标的索引 · 报道点名但未关联（独立状态）', () => {
  /** 合成文档：一个标的 + 两条报道记录（一条精确匹配 ticker，一条对不上） */
  const doc = {
    artifact: 'synthetic', artifact_version: '0', position: '', events: [{
      event_id: 'E-1', label: '合成事件', year: 2020, window_text: '', external_window_ref: null,
      evidence_basis: '', catalysts: [],
      participants: [{
        security_id: 'AAA-000001', ticker: '000001', name: '甲公司',
        category: 'MECHANISM_DIRECT', evidence_level: 'REPORT_NAMED',
        rationale: '合成理由', source: '合成来源',
      }],
      observed_performance: {
        note: '',
        by_security: null,
        reported_same_day_moves: { '000001': '+3.0%', 'BBB-000002': '+9.9%' },
      },
      known_gaps: [],
    }],
  } as unknown as HistoricalEventsDoc;

  it('★★ 精确匹配 ticker 的报道记录挂到标的上', () => {
    const idx = themeSecurityIndexOf(doc);
    expect(idx.entries).toHaveLength(1);
    expect(idx.entries[0].occurrences[0].eventReportedMove).toBe('+3.0%');
  });

  it('★★ 无法匹配的代码 → 独立状态，不并入标的、不猜身份', () => {
    const idx = themeSecurityIndexOf(doc);
    expect(idx.unlinkedReports).toHaveLength(1);
    const r = idx.unlinkedReports[0];
    expect(r.code).toBe('BBB-000002');
    expect(r.move).toBe('+9.9%');
    expect(r.status).toBe('REPORTED_NOT_LINKED');
    expect(r.statusLabel).toContain('尚未关联');
    // 不得被当成第二只股票
    expect(idx.entries.map((x) => x.securityId)).toEqual(['AAA-000001']);
  });

  it('★ 真实数据当前没有未关联记录（不是漏算，而是数据里全部精确匹配）', () => {
    for (const idx of [flu, power, media, robotics]) {
      expect(idx.totals.unlinkedReports).toBe(0);
    }
  });
});

describe('题材标的索引 · 搜索', () => {
  it('★ 按代码 / 名称 / 别名搜索，且不改变排序', () => {
    expect(filterSecurityIndex(flu, '002007').entries.map((x) => x.securityId)).toEqual(['HUALAN-002007']);
    expect(filterSecurityIndex(flu, '华兰').entries.map((x) => x.name)).toEqual(['华兰生物', '华兰疫苗']);
    expect(filterSecurityIndex(flu, 'ST香雪').entries.map((x) => x.securityId)).toEqual(['XIANGXUE-300147']);
    // 空查询 → 原样返回
    expect(filterSecurityIndex(flu, '   ').entries).toHaveLength(flu.entries.length);
  });

  it('★ 无命中 → 空列表（不是退回全部）', () => {
    expect(filterSecurityIndex(flu, '不存在的公司').entries).toHaveLength(0);
  });
});
