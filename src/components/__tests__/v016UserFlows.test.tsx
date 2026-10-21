// @vitest-environment jsdom
/**
 * ★★ v0.16 端到端用户场景 —— **页面级** jsdom 交互（挂载真实 `<App />` + 真实点击）。
 *
 * 场景（半导体 / AI 算力 / 存储新题材）：
 *  ① 首页「历史题材地图」→ 选「半导体 / AI 算力 / 存储」→ 标的索引 16 只；
 *  ② 2023 AI 算力事件：窗口 + 相关标的 + 实测行情（基准/超额）→ 查看对象详情 → 关闭回上下文；
 *  ③ 反例（京东方A＝COUNTER_EXAMPLE）与证据不足（中芯国际＝INSUFFICIENT）在**同一卡**里并存且不混同；
 *  ④ Research Candidate 不伪装 Campaign（大基金三期），行情全无覆盖如实留空、不补 0。
 *
 * ★ 环境说明：本机无 Chrome/Chromium → 未做浏览器截图；这里用真实 DOM 点击，断言基于点击后状态。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import App from '../../App';

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  window.localStorage.clear();
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

async function mountApp(): Promise<{ root: Root; doc: Document }> {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => { root.render(<App />); });
  return { root, doc: document };
}

const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };
const detailPanel = (doc: Document) =>
  doc.querySelector('aside.detail-panel[role="dialog"][aria-label="完整历史案例"]');
const detailId = (doc: Document) =>
  detailPanel(doc)?.getAttribute('data-campaign-id') ?? '';

async function openTheme(doc: Document): Promise<HTMLElement> {
  const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
  const tab = maps.querySelector('button[data-theme-id="SEMICONDUCTOR_AI"]') as HTMLButtonElement;
  expect(tab, '应有 SEMICONDUCTOR_AI tab').toBeTruthy();
  await click(tab);
  expect(tab.getAttribute('aria-selected')).toBe('true');
  return maps;
}

describe('v0.16 端到端：半导体 / AI 算力题材 → 标的证据 → 历史对象详情', () => {
  it('★★ 题材 → 标的索引（16 只）→ 2023 事件行情 → 对象详情 → 关闭回上下文', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);

    // ① 标的索引先于逐事件列表（16 只标的）
    const index = maps.querySelector('[aria-label="历史参与标的索引"]')!;
    expect(index.textContent).toContain('16');
    const iIndex = maps.innerHTML.indexOf('aria-label="历史参与标的索引"');
    const iEvents = maps.innerHTML.indexOf('class="fem-list"');
    expect(iIndex).toBeLessThan(iEvents);

    // ② 展开 2023 AI 算力事件卡
    const card = maps.querySelector('li[data-event-id="SEMI-2023-AI-COMPUTE"]') as HTMLElement;
    expect(card, '应有 SEMI-2023-AI-COMPUTE 事件卡').toBeTruthy();
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    expect(card.querySelector('.fem-event-body')).not.toBeNull();

    // ③ 事件窗口 + 对象身份是 Campaign
    expect(card.textContent).toContain('2023-01-30 → 2023-04-10');
    expect(card.textContent).toContain('C-2023-AI-COMPUTE-SEMI');

    // ④ 实测行情：基准在场，寒武纪的「至高点超额」自洽
    expect(card.textContent).toContain('SH000300');
    expect(card.textContent).toContain('寒武纪');
    expect(card.textContent).toContain('至高点涨幅');

    // ⑤ 查看对象详情（App 层两道检查满足 → 有按钮）
    const openBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('查看对象详情')) as HTMLButtonElement;
    expect(openBtn, '事件卡应有「查看对象详情」按钮').toBeTruthy();
    await click(openBtn);

    // ⑥ 详情打开，对象 id 一致
    expect(detailPanel(doc)).not.toBeNull();
    expect(detailId(doc)).toBe('C-2023-AI-COMPUTE-SEMI');
    expect(detailPanel(doc)!.textContent).toContain('2023');

    // ⑦ 关闭 → 回到题材地图，上下文不丢（tab 仍选中、事件卡仍展开）
    await click(detailPanel(doc)!.querySelector('button[aria-label="关闭"]') as HTMLButtonElement);
    expect(detailPanel(doc)).toBeNull();
    expect(maps.querySelector('button[data-theme-id="SEMICONDUCTOR_AI"]')!
      .getAttribute('aria-selected')).toBe('true');
    const cardAgain = maps.querySelector('li[data-event-id="SEMI-2023-AI-COMPUTE"]') as HTMLElement;
    expect(cardAgain.querySelector('.fem-event-body')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 反例（COUNTER_EXAMPLE）与证据不足（INSUFFICIENT）在同一卡片并存且不混同', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);

    const card = maps.querySelector('li[data-event-id="SEMI-2019-LOCALIZATION"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    const t = card.textContent ?? '';

    // 京东方A = 显示面板，与集成电路不同轴 → 反例标签
    expect(t).toContain('京东方A');
    expect(t).toContain('反例（不同轴）');
    // 中芯国际（该事件里无行情登记）→ 证据不足标签，**与反例不同**
    expect(t).toContain('中芯国际');
    expect(t).toContain('证据不足');
    // 两标签同卡并存（各自独立，取**参与者行** li.fem-part 判断）
    const boeRow = [...card.querySelectorAll('li.fem-part')].find((el) =>
      el.textContent?.includes('京东方A')) as HTMLElement;
    const smicRow = [...card.querySelectorAll('li.fem-part')].find((el) =>
      el.textContent?.includes('中芯国际')) as HTMLElement;
    expect(boeRow, '京东方A 应标「反例（不同机制轴）」').toBeTruthy();
    expect(smicRow, '中芯国际 应标「证据不足」').toBeTruthy();
    expect(boeRow.textContent).toContain('反例（不同机制轴）');
    expect(boeRow.textContent).not.toContain('证据不足');
    expect(smicRow.textContent).toContain('证据不足');
    expect(smicRow.textContent).not.toContain('反例');

    await act(async () => { root.unmount(); });
  });

  it('★★ Research Candidate 不伪装 Campaign；大基金三期行情已可算但仍非因果', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);

    const card = maps.querySelector('li[data-event-id="SEMI-2024-FUND3"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    const t = card.textContent ?? '';

    // 身份：Research Candidate（不是 Campaign）
    expect(t).toContain('RC-2024-SEMI-FUND3');
    expect(t).toContain('Research Candidate');
    expect(card.querySelector('.ecp-kind-candidate')).not.toBeNull();

    // ★★ v0.24：4 只标的窗口行情已可计算 → 逐行 COMPUTED（不再显示「行情不可得」行）
    expect(t).toContain('中芯国际');
    expect(t).toContain('+101.3%');
    for (const sid of ['SMIC', 'AMEC', 'PIOTECH', 'HYGON']) {
      const row = card.querySelector(`tr[data-security-id="${sid}"]`) as HTMLElement;
      expect(row, sid).toBeTruthy();
      expect(row.getAttribute('data-perf-status'), sid).toBe('COMPUTED');
      expect(row.textContent, sid).toContain('完整窗口已计算');
      expect(row.textContent, sid).toContain('44');
    }
    // 没有任何一行落在「行情不可得」
    expect(card.querySelectorAll('tr[data-perf-status="UNAVAILABLE"]').length).toBe(0);

    // ★★ 但「行情可算」≠「机制被证明」：Beta Contamination 与 INSUFFICIENT 必须同屏可见
    expect(t).toContain('Beta Contamination');
    expect(t).toContain('INSUFFICIENT');
    // 不补 0：不得出现把无覆盖显示成 0% 的情况
    expect(t).not.toContain('+0.0%');

    await act(async () => { root.unmount(); });
  });
});
