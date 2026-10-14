/**
 * 通用历史事件地图 —— 必要测试（2026-10-14 多题材通用化）。
 *
 * 只覆盖**必要**检查：
 *   A. 索引驱动：题材能被解析、无数据题材不显示空壳
 *   B. 多题材数据通过通用校验
 *   C. 通用组件能渲染非流感题材（且带该题材自己的免责声明）
 *   D. ★ 向后兼容：流感 4 事件语义未变（由 FluEventMap.test.tsx 覆盖，此处只验入口）
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { HistoricalEventMap } from '../HistoricalEventMap';
import {
  allResolvedEventMaps,
  eventMapByExternalId,
  eventMapByTheme,
  eventMapsNotIncluded,
  eventStudyState,
  validateHistoricalEvents,
} from '../../../data/timeline/historicalEventMaps';

describe('A. 索引驱动', () => {
  it('★ 按外部线索 ID 能解析到题材（数据驱动，非硬编码）', () => {
    expect(eventMapByExternalId('EXT-12')?.theme_id).toBe('FLU');
    expect(eventMapByExternalId('EXT-14')?.theme_id).toBe('POWER_SUMMER');
    expect(eventMapByExternalId('EXT-13')?.theme_id).toBe('MEDIA');
    expect(eventMapByExternalId('EXT-23')?.theme_id).toBe('ROBOTICS');
  });

  it('★ 无数据文件的题材 → undefined（**不显示空壳**）', () => {
    // EXT-09 / EXT-05 / EXT-19 已在索引的 not_included 里记录原因
    for (const id of ['EXT-09', 'EXT-05', 'EXT-19', 'EXT-01', 'EXT-25']) {
      expect(eventMapByExternalId(id), id).toBeUndefined();
    }
    expect(eventMapsNotIncluded().length).toBeGreaterThanOrEqual(3);
  });

  it('★ 四个题材全部解析成功（索引有条目 + 注册表有文档）', () => {
    const maps = allResolvedEventMaps();
    expect(maps.map((m) => m.theme_id).sort()).toEqual(
      ['FLU', 'MEDIA', 'POWER_SUMMER', 'ROBOTICS'].sort());
    for (const m of maps) expect(m.doc.events.length, m.theme_id).toBeGreaterThan(0);
  });

  it('★ 每个题材的 display 配置齐全（title / aria / badge / note / class_order）', () => {
    for (const m of allResolvedEventMaps()) {
      expect(m.display.title, m.theme_id).toBeTruthy();
      expect(m.display.aria_label, m.theme_id).toBeTruthy();
      expect(m.display.badge, m.theme_id).toBeTruthy();
      expect(m.display.note, m.theme_id).toBeTruthy();
      expect(m.display.class_order.length, m.theme_id).toBeGreaterThan(0);
    }
  });
});

describe('B. 多题材数据通过通用校验', () => {
  it('★ 所有题材事件数据通过结构校验（含业务机制 caveat / is_campaign_ruling）', () => {
    for (const m of allResolvedEventMaps()) {
      expect(validateHistoricalEvents(m.doc, m.theme_id), m.theme_id).toEqual([]);
    }
  });

  it('能发现：缺 event_class / 缺 known_gaps / 非法 category', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const bad = JSON.parse(JSON.stringify(m.doc));
    delete bad.events[0].event_class;
    bad.events[0].known_gaps = [];
    bad.events[0].participants[0].category = 'WEIRD';
    const issues = validateHistoricalEvents(bad, 'X');
    expect(issues.some((i) => i.field === 'event_class')).toBe(true);
    expect(issues.some((i) => i.field === 'known_gaps')).toBe(true);
    expect(issues.some((i) => i.field.includes('participants.category'))).toBe(true);
  });
});

describe('C. 通用组件渲染非流感题材', () => {
  it('★ 电力题材可渲染，且带该题材自己的 class caveat 与 note', () => {
    const m = eventMapByTheme('POWER_SUMMER')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain(m.display.aria_label);
    expect(html).toContain('POWER-2023-SUMMER');
    // ★ 四个概念区分提示（题材专属，非流感的三概念）
    expect(html).toContain('四个不同概念');
    // ★ Campaign 事实（含 peak_date，且注明不是行情高点）
    expect(html).toContain('C-2023-POWEROP-THERMAL');
  });

  it('★ 传媒题材可渲染，且明确标注机制非暑期档', () => {
    const m = eventMapByTheme('MEDIA')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain('MEDIA-2021-METAVERSE');
    expect(html).toContain(m.display.note.slice(0, 20));
  });

  it('★ 机器人题材可渲染', () => {
    const m = eventMapByTheme('ROBOTICS')!;
    const html = renderToStaticMarkup(<HistoricalEventMap doc={m.doc} display={m.display} />);
    expect(html).toContain('ROBOTICS-2023-HUMANOID');
  });

  it('★ 所有题材的事件都有可分析行情（本轮补数生效）', () => {
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        expect(eventStudyState(e), `${m.theme_id}/${e.event_id}`).toBe('HAS_PRICE_DATA');
      }
    }
  });

  it('★ 每个题材的行情表都含基准（SH000300）', () => {
    for (const m of allResolvedEventMaps()) {
      for (const e of m.doc.events) {
        const mp = e.market_performance;
        if (!mp) continue;
        expect(Object.keys(mp.benchmark), `${m.theme_id}/${e.event_id}`).toContain('SH000300');
        expect(mp.is_campaign_ruling, `${m.theme_id}/${e.event_id}`).toBe(false);
      }
    }
  });
});

describe('D. 向后兼容（入口层）', () => {
  it('★ FLU 题材仍解析为 v0_4 数据（4 事件）', () => {
    const m = eventMapByTheme('FLU')!;
    expect(m.doc.artifact_version).toBe('0.4');
    expect(m.doc.events).toHaveLength(4);
    // ★ 流感专属的 corrections 更正痕迹仍在
    expect(JSON.stringify(m.doc.corrections)).toContain('600513');
  });

  it('★ 流感题材的 class caveat 文本与既有常量一致（未在通用化中改写）', () => {
    const m = eventMapByTheme('FLU')!;
    const caveat = m.display.class_caveats?.ADJACENT_PUBLIC_HEALTH ?? '';
    expect(caveat).toContain('不是流感');
    expect(caveat).toContain('不得');
  });
});
