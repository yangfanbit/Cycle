// @vitest-environment jsdom
/**
 * ★★ 历史题材地图 —— **真实点击**切换（v0.10）。
 *
 * SSR 测试只能证明「默认渲染了哪个题材」；「点另一个题材会不会真的换内容」
 * 必须靠 jsdom（本项目 v0.8 起已引入，文件级启用，不影响其它文件跑 node）。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { HistoricalThemeMaps } from '../HistoricalThemeMaps';

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

async function mount(): Promise<{ root: Root; host: HTMLDivElement }> {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () => { root.render(<HistoricalThemeMaps />); });
  return { root, host };
}

const tab = (host: HTMLElement, id: string) =>
  host.querySelector(`button[data-theme-id="${id}"]`) as HTMLButtonElement;

describe('历史题材地图 · 题材切换（jsdom 真实点击）', () => {
  it('★★ 默认第一个题材；点第二个题材 → 面板与选中态真的切换', async () => {
    const { root, host } = await mount();

    // 默认 = FLU（索引第一条）
    expect(tab(host, 'FLU').getAttribute('aria-selected')).toBe('true');
    expect(host.querySelector('[role="tabpanel"]')!.id).toBe('htm-panel-FLU');
    expect(host.querySelector('[data-empirical-probability]')).not.toBeNull();

    // 切到电力
    await act(async () => { tab(host, 'POWER_SUMMER').click(); });
    expect(tab(host, 'POWER_SUMMER').getAttribute('aria-selected')).toBe('true');
    expect(tab(host, 'FLU').getAttribute('aria-selected')).toBe('false');
    expect(host.querySelector('[role="tabpanel"]')!.id).toBe('htm-panel-POWER_SUMMER');
    // 电力题材的经验概率区块（1/7）随之出现
    expect(host.textContent).toContain('1 / 7');

    // 切到文化传媒（无跨年份段 → 不应出现概率区块）
    await act(async () => { tab(host, 'MEDIA').click(); });
    expect(host.querySelector('[role="tabpanel"]')!.id).toBe('htm-panel-MEDIA');
    expect(host.querySelector('[data-empirical-probability]')).toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★ 受控模式：外部传入 activeThemeId 时以它为准（雷达跳转用）', async () => {
    const host = document.createElement('div');
    document.body.appendChild(host);
    const root = createRoot(host);
    await act(async () => {
      root.render(<HistoricalThemeMaps activeThemeId="ROBOTICS" onSelectTheme={() => {}} />);
    });
    expect(host.querySelector('[role="tabpanel"]')!.id).toBe('htm-panel-ROBOTICS');
    expect(tab(host, 'ROBOTICS').getAttribute('aria-selected')).toBe('true');
    await act(async () => { root.unmount(); });
  });
});
