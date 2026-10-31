// @vitest-environment jsdom
/**
 * ★★ v0.64 使用 BUG 回归（App 级）：
 *
 * ① **默认标签 = 年内窗口** —— 页头与注释都把季节性地图定义为首页第一视觉，
 *    默认值却曾是 `events`，打开页面看不到「今天处在年内的什么位置」。
 * ② **跨模块跳转必须切标签** —— 从外部季节性雷达点「在历史题材地图中查看」时，
 *    原实现只改题材 + `scrollIntoView`；若用户停在「年内窗口」，目标区块在
 *    `<div hidden>` 里（display:none），滚到的是**隐藏节点**，点击看起来「没反应」。
 * ③ **说明文字必须与视图一致** —— 「横轴 1–12 月 / 条形 = 历史炒作窗口」只适用于
 *    年内窗口图，原先无条件渲染，切到「历史题材 / 事件」仍在讲季节图。
 * ④ **年份切换不得越界** —— 原 `y ± 1` 能进入没有数据的年份，Timeline / 全景变空。
 * ⑤ **历史案例详情支持 Escape** —— 与候选详情一致（原先只有关闭按钮）。
 *
 * 断言全部由**页面实际数据**推导（年份集合取自 `.year-chip`，题材取自雷达卡片），
 * 不写死具体年份或题材，避免变成「旧行为快照」。
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import App, { stepYear } from '../../App';
import { CampaignDetail } from '../CampaignDetail/CampaignDetail';
import { researchTimelineSource } from '../../data/timeline/timelineAdapter';

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  window.localStorage.clear();
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };

async function mountApp(): Promise<{ root: Root; doc: Document }> {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => { root.render(<App />); });
  return { root, doc: document };
}

const tabSel = (doc: Document, k: 'seasonal' | 'events') =>
  doc.querySelector(`button[data-map-tab="${k}"]`)?.getAttribute('aria-selected');

describe('v0.64 使用修复：地图标签 / 跳转 / 说明文字', () => {
  it('★★ 默认停在「年内窗口」，且说明文字只在该标签下出现', async () => {
    const { root, doc } = await mountApp();
    expect(tabSel(doc, 'seasonal')).toBe('true');
    expect(tabSel(doc, 'events')).toBe('false');
    // 年内窗口的语义说明在场（横轴 1–12 月 / 条形 = 历史炒作窗口）
    const note = doc.querySelector('.seasonal-note');
    expect(note, '默认视图应有季节图口径说明').not.toBeNull();
    expect(note!.textContent).toContain('横轴 1–12 月');

    await act(async () => { root.unmount(); });
  });

  it('★★ 雷达「在历史题材地图中查看」→ 切到 events 标签、目标可见、说明文字撤走', async () => {
    const { root, doc } = await mountApp();

    // 取一个**确实带地图入口**的雷达卡片（不写死条目，按按钮文本找）
    const cards = [...doc.querySelectorAll('li[data-entry-id]')] as HTMLElement[];
    const card = cards.find((c) =>
      [...c.querySelectorAll('button')].some((b) => b.textContent?.includes('在「历史题材地图」中查看')),
    );
    expect(card, '应至少有一条线索带地图跳转入口').toBeTruthy();
    const mapBtn = [...card!.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('在「历史题材地图」中查看')) as HTMLButtonElement;

    await click(mapBtn);

    // ① 标签已切到 events（原实现不切 → 目标区域仍在 hidden 容器里）
    expect(tabSel(doc, 'events')).toBe('true');
    expect(tabSel(doc, 'seasonal')).toBe('false');

    // ② 事件地图容器不再被 hidden 包裹（点击后能真正看到目标内容）
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    expect(maps).not.toBeNull();
    expect(maps.closest('div[hidden]'), '事件地图不得仍在 hidden 容器内').toBeNull();

    // ③ 至少有一个题材被选中（跳转确实带上了题材，而不是只切标签）
    const active = maps.querySelectorAll('button[data-theme-id][aria-selected="true"]');
    expect(active.length).toBe(1);

    // ④ 季节图专用说明不得残留在事件视图
    expect(doc.querySelector('.seasonal-note')).toBeNull();

    await act(async () => { root.unmount(); });
  });
});

describe('v0.64 使用修复：年份切换边界', () => {
  it('★★ stepYear 只在可用年份内步进（含不连续年份集合）', () => {
    // 连续：首尾必须夹住
    expect(stepYear(2015, -1, [2015, 2016, 2017])).toBe(2015);
    expect(stepYear(2017, 1, [2015, 2016, 2017])).toBe(2017);
    expect(stepYear(2016, -1, [2015, 2016, 2017])).toBe(2015);
    expect(stepYear(2016, 1, [2015, 2016, 2017])).toBe(2017);

    // ★ 不连续（Research 源可能缺年）：取相邻的**存在**年份，不是 ±1
    expect(stepYear(2015, 1, [2015, 2018, 2020])).toBe(2018);
    expect(stepYear(2020, -1, [2015, 2018, 2020])).toBe(2018);
    expect(stepYear(2018, -1, [2015, 2018, 2020])).toBe(2015);

    // 单年 / 空集合：原地不动
    expect(stepYear(2020, 1, [2020])).toBe(2020);
    expect(stepYear(2020, -1, [2020])).toBe(2020);
    expect(stepYear(2020, 1, [])).toBe(2020);
  });

  it('★★ 页面上的左右切换与年份快捷按钮一致：到边界即禁用，不进入空年份', async () => {
    const { root, doc } = await mountApp();

    const chips = [...doc.querySelectorAll('.year-chip')].map((c) => Number(c.textContent));
    expect(chips.length, '应有年份快捷按钮（数据源年份）').toBeGreaterThan(0);
    const min = Math.min(...chips);
    const max = Math.max(...chips);

    const prev = () => doc.querySelector('button[aria-label="上一年"]') as HTMLButtonElement;
    const next = () => doc.querySelector('button[aria-label="下一年"]') as HTMLButtonElement;
    const yearNow = () => Number(doc.querySelector('.year-label')!.textContent);

    // 一路往最早年份走：每次都必须落在可用年份里，最后停在最小值且按钮禁用
    let guard = 0;
    while (!prev().disabled && guard++ < 50) {
      const before = yearNow();
      await click(prev());
      expect(chips, '切换后的年份必须在可用年份集合内').toContain(yearNow());
      expect(yearNow()).toBeLessThan(before);
    }
    expect(yearNow()).toBe(min);
    expect(prev().disabled).toBe(true);

    // 直接点最新年份快捷按钮 → 「下一年」应禁用（与左切换行为一致）
    const maxChip = [...doc.querySelectorAll('.year-chip')]
      .find((c) => Number(c.textContent) === max) as HTMLButtonElement;
    await click(maxChip);
    expect(yearNow()).toBe(max);
    expect(next().disabled).toBe(true);

    await act(async () => { root.unmount(); });
  });
});

describe('v0.64 使用修复：详情面板 Escape', () => {
  it('★★ 历史案例 / 研究对象详情按 Escape 关闭（与候选详情一致）', async () => {
    // ★ 用产品实际数据源（Research export）取一个真实对象，不硬编码 campaign_id
    const src = researchTimelineSource();
    const campaign = src.years()
      .map((y) => src.yearData(y).campaigns)
      .find((cs) => cs.length > 0)?.[0];
    // 显式抛出（`expect(...).toBeTruthy()` 不会做类型收窄）
    if (!campaign) throw new Error('应有可用于渲染的 Campaign（Research export 为空）');

    const host = document.createElement('div');
    document.body.appendChild(host);
    const root: Root = createRoot(host);
    const onClose = vi.fn();
    await act(async () => {
      root.render(<CampaignDetail campaign={campaign} onOpenRule={() => {}} onClose={onClose} />);
    });
    expect(host.querySelector('aside.detail-panel[role="dialog"]')).not.toBeNull();

    await act(async () => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(onClose, 'Escape 应触发关闭').toHaveBeenCalledTimes(1);

    await act(async () => { root.unmount(); });
  });
});
