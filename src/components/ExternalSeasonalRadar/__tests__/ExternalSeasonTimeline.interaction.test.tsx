// @vitest-environment jsdom
/**
 * ★★ 时间轴交互（v0.13）：历史窗口对照 / 带入研究请求 —— jsdom 真点。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { externalCalendarEntries } from '../../../data/timeline/externalSeasonalCalendar';
import { researchTimelineSource } from '../../../data/timeline/timelineAdapter';
import { themeAnnualRowsOf } from '../../../data/timeline/themeAnnualWindow';
import { ExternalSeasonTimeline } from '../ExternalSeasonTimeline';
import type { ExternalCalendarEntry } from '../../../data/timeline/externalSeasonalCalendar';

const all = externalCalendarEntries();
const macroRows = themeAnnualRowsOf(researchTimelineSource(), 'macro');

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

async function mount(opts: {
  onRequestDraft?: (e: ExternalCalendarEntry) => void;
  onOpenMap?: (id: string) => void;
} = {}) {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => {
    root.render(
      <ExternalSeasonTimeline
        entries={all}
        allEntries={all}
        categories={['ALL', '行业季节性']}
        category="ALL"
        onCategory={() => {}}
        onOpenMap={opts.onOpenMap}
        onRequestDraft={opts.onRequestDraft}
        macroRows={macroRows}
        today="2026-10-18"
      />,
    );
  });
  return { root, host };
}

const rowBtn = (host: HTMLElement, entryId: string, label: string) => {
  const row = host.querySelector(`tr[data-est-row="${entryId}"]`);
  const btn = [...(row?.querySelectorAll('button') ?? [])].find(
    (b) => (b.textContent ?? '').includes(label),
  );
  if (!btn) throw new Error(`${entryId} 行没有按钮：${label}`);
  return btn as HTMLButtonElement;
};

describe('时间轴 · 历史窗口对照（jsdom 真点）', () => {
  it('★★ 场景 1：点 EXT-12「对照历史窗口」→ 两层时间轴 + 流感疫苗 2–3 月', async () => {
    const { root, host } = await mount();

    // 初始没有对照面板
    expect(host.querySelector('[data-ecp-status]')).toBeNull();

    await act(async () => { rowBtn(host, 'EXT-12', '对照历史窗口').click(); });

    const panel = host.querySelector('[data-ecp-status="matched"]');
    expect(panel).not.toBeNull();
    const text = panel?.textContent ?? '';
    // 两层 + 来源标签
    expect(text).toContain('外部资料声称的月份窗口');
    expect(text).toContain('历史');
    expect(text).toContain('MAIN_RISE');
    expect(text).toContain('外部参考');
    // 外部层原文
    expect(text).toContain('9 月至次年 1 月');
    // 历史对象：流感疫苗的 MAIN_RISE 在 2–3 月
    expect(panel!.querySelector('[data-ecp-hist="C-2023-PHARMA-FLU"]')).not.toBeNull();
    expect(text).toContain('2023-02-20 → 2023-03-20');
    expect(text).toContain('C-2023-PHARMA-FLU');
    // 语义声明：明确「不判断机制一致」「不计算重合率/命中率」
    expect(text).toContain('宏观主题映射 ≠ 事件机制相同');
    expect(text).toContain('不是统计验证');
    expect(text).toContain('不计算重合率');
    // 没有把「重合率」算出来的数字（不是声明，而是结果）
    expect(text).not.toMatch(/重合率[^\n]{0,6}\d/);

    // 再点一次收起
    await act(async () => { rowBtn(host, 'EXT-12', '收起历史窗口对照').click(); });
    expect(host.querySelector('[data-ecp-status]')).toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 场景 4：EXT-23 无固定窗口但有映射 → 可看历史主题窗口，外部层明示无窗口', async () => {
    const { root, host } = await mount();
    const item = host.querySelector('[data-est-nowin-id="EXT-23"]')!;
    const btn = [...item.querySelectorAll('button')].find((b) => (b.textContent ?? '').includes('对照历史窗口'))!;
    await act(async () => { (btn as HTMLButtonElement).click(); });

    const panel = host.querySelector('[data-ecp-status="matched"]');
    expect(panel).not.toBeNull();
    const text = panel?.textContent ?? '';
    expect(text).toContain('无固定月份窗口');
    expect(text).toContain('不绘制外部月份条');
    expect(text).toContain('不虚构');
    expect(panel!.querySelector('[data-ecp-hist]')).not.toBeNull();
    await act(async () => { root.unmount(); });
  });

  it('★★ 场景 3：未映射线索给「带入研究请求」并回调该条目；已映射线索不给', async () => {
    const seen: string[] = [];
    const { root, host } = await mount({ onRequestDraft: (e) => seen.push(e.id) });

    // 未映射（EXT-17）
    await act(async () => { rowBtn(host, 'EXT-17', '带入研究请求').click(); });
    expect(seen).toEqual(['EXT-17']);

    // 已映射行**没有**「带入研究请求」按钮
    const mappedRow = host.querySelector('tr[data-est-row="EXT-12"]')!;
    expect([...mappedRow.querySelectorAll('button')].some(
      (b) => (b.textContent ?? '').includes('带入研究请求'),
    )).toBe(false);

    await act(async () => { root.unmount(); });
  });

  it('★ 当前月份被标出（仅日历事实）', async () => {
    const { root, host } = await mount();
    expect(host.querySelector('[data-est-current-month="10"]')).not.toBeNull();
    expect(host.textContent).toContain('无涨跌含义');
    await act(async () => { root.unmount(); });
  });
});
