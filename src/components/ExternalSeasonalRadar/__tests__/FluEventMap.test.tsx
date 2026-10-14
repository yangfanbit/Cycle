/**
 * 历史流感事件地图 —— 必要测试。
 *
 * 只覆盖三类**必要**检查（用户 2026-10-14 要求，不为覆盖率增加形式化测试）：
 *   A. 数据正确性（结构校验能拦下非法数据）
 *   B. 核心展示（行情不可得**不得**显示为 0 涨幅 / 空数据）
 *   C. 事件—标的关联（`INSUFFICIENT` 不当作该事件的表现证据；两池分离）
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { FluEventMap } from '../FluEventMap';
import {
  EVENT_STUDY_LABEL,
  NO_MARKET_DATA_LABEL,
  eventStudyState,
  fluEventById,
  fluEvents,
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

  it('能发现：同事件内标的重复', () => {
    const d = doc();
    d.events = [{ ...real[0], participants: [real[0].participants[0], real[0].participants[0]] }];
    expect(validateFluEvents(d).some((i) => i.field.includes('participants.security_id'))).toBe(true);
  });

  it('能发现：非法标的分类', () => {
    const d = doc();
    d.events = [{ ...real[0], participants: [{ ...real[0].participants[0],
      category: 'WEIRD' as never }] }];
    expect(validateFluEvents(d).some((i) => i.field.includes('participants.category'))).toBe(true);
  });

  it('能发现：标的缺纳入理由（禁止仅凭标签纳入）', () => {
    const d = doc();
    d.events = [{ ...real[0], participants: [{ ...real[0].participants[0], rationale: '' }] }];
    expect(validateFluEvents(d).some((i) => i.field.includes('participants.rationale'))).toBe(true);
  });

  it('能发现：缺 known_gaps（不确定性必须显式记录）', () => {
    const d = doc(); d.events = [{ ...real[0], known_gaps: [] }];
    expect(validateFluEvents(d).some((i) => i.field === 'known_gaps')).toBe(true);
  });

  it('能发现：events 为空', () => {
    const d = doc(); d.events = [];
    expect(validateFluEvents(d).some((i) => i.field === 'events')).toBe(true);
  });
});

/* ---------------------------------------------------- B. 核心展示 */

describe('B. 核心展示：行情不可得不得伪装', () => {
  it('未登记/无行情的标的 → hasMarketData=false', () => {
    for (const e of fluEvents()) {
      for (const p of e.participants) {
        if (p.market_data && (p.market_data.includes('无登记') || p.market_data.includes('无行情'))) {
          expect(hasMarketData(p), `${p.security_id} 应判为无行情`).toBe(false);
        }
      }
    }
  });

  it('★ 无行情事件的状态 = NO_PRICE_DATA，且渲染不含伪造涨幅', () => {
    const e = fluEventById('FLU-2019-ANTIFLU')!;
    expect(eventStudyState(e)).toBe('NO_PRICE_DATA');
    const html = renderToStaticMarkup(<FluEventMap />);
    // 折叠态即必须可见：状态标签 + 「行情不可得」徽标
    expect(html).toContain(NO_MARKET_DATA_LABEL);
    expect(html).toContain(EVENT_STUDY_LABEL.NO_PRICE_DATA);
    expect(html).toContain('data-study-state="NO_PRICE_DATA"');
    // ★ 不得把空数据展示成「0%」这类数字表现
    expect(html).not.toMatch(/\+?0\.0%/);
  });

  it('★ 未核实事件显示为 NOT_VERIFIED（不假装已研究）', () => {
    const e = fluEventById('FLU-2017-AVIAN')!;
    expect(eventStudyState(e)).toBe('NOT_VERIFIED');
    expect(renderToStaticMarkup(<FluEventMap />)).toContain(EVENT_STUDY_LABEL.NOT_VERIFIED);
  });

  it('有 Campaign 的事件显示为 HAS_PRICE_DATA', () => {
    expect(eventStudyState(fluEventById('FLU-2023-H1N1')!)).toBe('HAS_PRICE_DATA');
  });
});

/* ---------------------------------------------------- C. 事件—标的关联 */

describe('C. 事件—标的关联与两池分离', () => {
  it('★ INSUFFICIENT 标的**不**计入该事件的表现证据', () => {
    const e = fluEventById('FLU-2019-ANTIFLU')!;
    const ins = e.participants.filter((p) => p.category === 'INSUFFICIENT');
    expect(ins.length).toBeGreaterThan(0);                 // 恒瑞/泰格/药明：有行情但无参与证据
    // 事件的 observed_performance 不得引用这些标的
    const json = JSON.stringify(e.observed_performance);
    for (const p of ins) expect(json).not.toContain(p.security_id);
  });

  it('★ 「有行情」不等于「参与该事件」——库内医药股被显式标为 INSUFFICIENT', () => {
    const e = fluEventById('FLU-2019-ANTIFLU')!;
    const hen = e.participants.find((p) => p.security_id === 'HENGRUI')!;
    expect(hen.category).toBe('INSUFFICIENT');
    expect(hen.rationale).toContain('未找到同期报道');
    expect(hen.market_data).toContain('1215');              // 有行情，但类别仍是 INSUFFICIENT
  });

  it('★ 季节性研究股票池**未**由事后挑选领涨股构成', () => {
    const d = fluEventsDoc();
    expect(d.research_pool_note.seasonal_pool).toContain('尚未建立');
    expect(d.research_pool_note.seasonal_pool).toContain('不得');
  });

  it('概念指数不可得被如实记录（不代以其他指数）', () => {
    const d = fluEventsDoc();
    const ci = d.concept_index_availability as Record<string, { result: string; note?: string }>;
    expect(ci.flu_885879.result).toContain('不可得');
    expect(ci.flu_885879.note).toContain('不代以');
  });

  it('三个事件齐全（2023 有据 / 2019 有据 / 2017 未核实）', () => {
    const ids = fluEvents().map((e) => e.event_id);
    expect(ids).toContain('FLU-2023-H1N1');
    expect(ids).toContain('FLU-2019-ANTIFLU');
    expect(ids).toContain('FLU-2017-AVIAN');
  });
});
