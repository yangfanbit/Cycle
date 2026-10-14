/**
 * 历史事件地图 —— 必要测试（2026-10-14 v0.2：事件归属更正后）。
 *
 * 覆盖三类**必要**检查（不为覆盖率增加形式化测试）：
 *   A. 数据正确性（结构校验能拦下非法数据；事件类别必须显式）
 *   B. 核心展示（行情不可得不得伪装；邻近事件必须带免责声明）
 *   C. ★★ 事件归属（本轮核心）：不得把邻近传染病算作流感；不得仅凭报道点名认定业务机制
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { FluEventMap } from '../FluEventMap';
import {
  ADJACENT_EVENT_CAVEAT,
  EVENT_CLASS_LABEL,
  EVENT_STUDY_LABEL,
  EVIDENCE_LEVEL_LABEL,
  NO_MARKET_DATA_LABEL,
  eventStudyState,
  fluEventById,
  fluEvents,
  fluEventsByClass,
  fluEventsDoc,
  hasMarketData,
  validateFluEvents,
  type FluEventsDoc,
} from '../../../data/timeline/fluHistoricalEvents';

/** 构造「只有壳」的 doc（用于构造非法输入；以真实 doc 为底，保证类型完整） */
const doc = (): FluEventsDoc => ({ ...JSON.parse(JSON.stringify(fluEventsDoc())), events: [] });

/* ---------------------------------------------------- A. 数据正确性 */

describe('A. 数据正确性', () => {
  const real = fluEvents();

  it('真实数据通过结构校验（基线）', () => {
    expect(validateFluEvents(fluEventsDoc())).toEqual([]);
  });

  it('能发现：事件 id 重复', () => {
    const d = doc(); d.events = [{ ...real[0], event_id: 'X' }, { ...real[0], event_id: 'X' }];
    expect(validateFluEvents(d).some((i) => /重复/.test(i.message))).toBe(true);
  });

  it('★ 能发现：事件缺 event_class（归属必须显式）', () => {
    const d = doc();
    const e = { ...real[0] } as Partial<typeof real[0]>;
    delete e.event_class;
    d.events = [e as typeof real[0]];
    expect(validateFluEvents(d).some((i) => i.field === 'event_class')).toBe(true);
  });

  it('能发现：非法事件类别', () => {
    const d = doc(); d.events = [{ ...real[0], event_class: 'NOPE' as never }];
    expect(validateFluEvents(d).some((i) => i.field === 'event_class')).toBe(true);
  });

  it('能发现：非法证据等级', () => {
    const d = doc();
    d.events = [{ ...real[0], participants: [{ ...real[0].participants[0],
      evidence_level: 'MAYBE' as never }] }];
    expect(validateFluEvents(d).some((i) => i.field.includes('evidence_level'))).toBe(true);
  });

  it('能发现：非法标的分类 / 缺纳入理由 / 缺 known_gaps', () => {
    const bad = doc();
    bad.events = [{ ...real[0], known_gaps: [], participants: [{ ...real[0].participants[0],
      category: 'WEIRD' as never, rationale: '' }] }];
    const issues = validateFluEvents(bad);
    expect(issues.some((i) => i.field.includes('participants.category'))).toBe(true);
    expect(issues.some((i) => i.field.includes('participants.rationale'))).toBe(true);
    expect(issues.some((i) => i.field === 'known_gaps')).toBe(true);
  });
});

/* ---------------------------------------------------- B. 核心展示 */

describe('B. 核心展示', () => {
  it('★ 邻近传染病事件在页面上带免责声明（不得作为流感季节性证据）', () => {
    const html = renderToStaticMarkup(<FluEventMap />);
    expect(html).toContain(ADJACENT_EVENT_CAVEAT);
    expect(html).toContain(EVENT_CLASS_LABEL.ADJACENT_PUBLIC_HEALTH);
  });

  it('★ 按事件类别分组渲染（直接流感 / 邻近传染病 都在）', () => {
    const html = renderToStaticMarkup(<FluEventMap />);
    expect(html).toContain(EVENT_CLASS_LABEL.FLU_DIRECT);
    expect(html).toContain('data-event-class="FLU_DIRECT"');
    expect(html).toContain('data-event-class="ADJACENT_PUBLIC_HEALTH"');
  });

  it('★ 行情不可得显式标注，且渲染不含伪造涨幅', () => {
    const html = renderToStaticMarkup(<FluEventMap />);
    expect(html).toContain(NO_MARKET_DATA_LABEL);
    expect(html).not.toMatch(/\+?0\.0%/);
  });

  it('无行情事件状态 = NO_PRICE_DATA；2023 事件 = HAS_PRICE_DATA', () => {
    expect(eventStudyState(fluEventById('SUPERFUNGUS-2019-CANDIDA')!)).toBe('NO_PRICE_DATA');
    expect(eventStudyState(fluEventById('PUBLICHEALTH-2019-WUHAN')!)).toBe('NO_PRICE_DATA');
    expect(eventStudyState(fluEventById('FLU-2017-AVIAN')!)).toBe('NO_PRICE_DATA');
    expect(eventStudyState(fluEventById('FLU-2023-H1N1')!)).toBe('HAS_PRICE_DATA');
    expect(renderToStaticMarkup(<FluEventMap />)).toContain(EVENT_STUDY_LABEL.NO_PRICE_DATA);
  });

  it('证据等级标签常量存在且被使用', () => {
    expect(EVIDENCE_LEVEL_LABEL.REPORT_NAMED).toBe('仅报道点名');
    const named = fluEvents().flatMap((e) => e.participants)
      .filter((p) => p.evidence_level === 'REPORT_NAMED');
    expect(named.length).toBeGreaterThan(0);
  });
});

/* ---------------------------------------------------- C. 事件归属（本轮核心） */

describe('C. ★★ 事件归属更正', () => {
  it('★★ 原 `FLU-2019-ANTIFLU` 已被移除（不得把两个不同机制合并为流感）', () => {
    expect(fluEventById('FLU-2019-ANTIFLU')).toBeUndefined();
  });

  it('★★ 2019-04 超级真菌 与 2019-12 不明原因肺炎 是两个独立事件，且都非流感', () => {
    const fungus = fluEventById('SUPERFUNGUS-2019-CANDIDA')!;
    const wuhan = fluEventById('PUBLICHEALTH-2019-WUHAN')!;
    expect(fungus).toBeDefined();
    expect(wuhan).toBeDefined();
    expect(fungus.event_class).toBe('ADJACENT_PUBLIC_HEALTH');
    expect(wuhan.event_class).toBe('ADJACENT_PUBLIC_HEALTH');
    // 两者不合并：催化日期落在不同月份
    const fd = fungus.catalysts.map((c) => c.date).join(',');
    const wd = wuhan.catalysts.map((c) => c.date).join(',');
    expect(fd).toContain('2019-04');
    expect(wd).toContain('2019-12');
  });

  it('★★ 只有 2017 禽流感 与 2023 甲流 被归为直接流感', () => {
    const direct = fluEvents().filter((e) => e.event_class === 'FLU_DIRECT').map((e) => e.event_id);
    expect(direct.sort()).toEqual(['FLU-2017-AVIAN', 'FLU-2023-H1N1'].sort());
  });

  it('★ 媒体标签与可核实催化分开保存（2019-12 的「抗流感概念」是媒体标签）', () => {
    const wuhan = fluEventById('PUBLICHEALTH-2019-WUHAN')!;
    expect(wuhan.media_label_note).toBeTruthy();
    expect(wuhan.media_label_note).toContain('媒体标签');
    expect(wuhan.media_label_note).toContain('武汉不明原因肺炎');
  });

  it('★★ 仅凭报道点名的标的**不得**标为 MECHANISM_DIRECT', () => {
    for (const e of fluEvents()) {
      for (const p of e.participants) {
        if (p.evidence_level === 'REPORT_NAMED') {
          expect(p.category, `${e.event_id}/${p.name} 仅报道点名却被标为直接机制相关`).not.toBe('MECHANISM_DIRECT');
        }
      }
    }
  });

  it('★ 2023 的三只有业务依据 → BUSINESS_VERIFIED + MECHANISM_DIRECT', () => {
    const e = fluEventById('FLU-2023-H1N1')!;
    for (const p of e.participants) {
      expect(p.evidence_level).toBe('BUSINESS_VERIFIED');
      expect(p.category).toBe('MECHANISM_DIRECT');
    }
  });

  it('★ 2017 事件已升级为「已找到同期报道」并有 10 只点名标的', () => {
    const e = fluEventById('FLU-2017-AVIAN')!;
    expect(e.catalysts).toHaveLength(1);
    expect(e.catalysts[0].date).toBe('2017-02-15');
    expect(e.participants).toHaveLength(10);
    for (const p of e.participants) {
      expect(p.reported_move, `${p.name} 缺报道涨幅`).toBeTruthy();
      expect(p.evidence_level).toBe('REPORT_NAMED');
    }
  });

  it('★ 联环药业代码为 600513（更正 v0_1 的 600735）', () => {
    const e = fluEventById('FLU-2017-AVIAN')!;
    const lh = e.participants.find((p) => p.name === '联环药业')!;
    expect(lh.ticker).toBe('600513');
    // ★ 标的清单里不得再出现错误代码（`corrections` 段**保留**旧代码作为更正痕迹，那是正确的 provenance）
    const allTickers = fluEvents().flatMap((x) => x.participants).map((p) => p.ticker);
    expect(allTickers).not.toContain('600735');
    // 且更正痕迹确实记录了这次更正
    expect(JSON.stringify(fluEventsDoc().corrections)).toContain('600735');
  });

  it('★ 联环药业的「澄清」作为反例被保留（炒作标签 ≠ 业务机制）', () => {
    const e = fluEventById('SUPERFUNGUS-2019-CANDIDA')!;
    const lh = e.participants.find((p) => p.name === '联环药业')!;
    expect(lh.note).toBeTruthy();
    expect(lh.note).toContain('澄清');
  });

  it('★ 更正痕迹被保留（corrections 段）', () => {
    const c = fluEventsDoc().corrections ?? [];
    expect(c.length).toBeGreaterThanOrEqual(3);
    const joined = JSON.stringify(c);
    expect(joined).toContain('FLU-2019-ANTIFLU');
    expect(joined).toContain('600513');
    expect(joined).toContain('FLU-2017-AVIAN');
  });

  it('★ 邻近事件不得作为流感季节性证据（数据文件显式声明）', () => {
    expect(fluEventsDoc().research_pool_note.adjacent_events_rule).toContain('不得');
  });

  it('分组函数把 2 个邻近事件与 2 个直接事件分开', () => {
    const groups = fluEventsByClass();
    expect(groups.map((g) => g.cls)).toEqual(['FLU_DIRECT', 'ADJACENT_PUBLIC_HEALTH']);
    expect(groups[0].events).toHaveLength(2);
    expect(groups[1].events).toHaveLength(2);
  });

  it('跨事件重复的股票只出现一次/事件（同事件内 security_id 唯一）', () => {
    for (const e of fluEvents()) {
      const ids = e.participants.map((p) => p.security_id);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it('★ hasMarketData 对未登记标的返回 false（2017/2019 标的全部）', () => {
    for (const id of ['FLU-2017-AVIAN', 'SUPERFUNGUS-2019-CANDIDA', 'PUBLICHEALTH-2019-WUHAN']) {
      const e = fluEventById(id)!;
      for (const p of e.participants) {
        expect(hasMarketData(p), `${p.name} 不应被判为有行情`).toBe(false);
      }
    }
  });
});
