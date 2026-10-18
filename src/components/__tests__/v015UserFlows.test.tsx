// @vitest-environment jsdom
/**
 * ★★ v0.15 端到端用户场景 —— **页面级** jsdom 交互（挂载真实 `<App />` + 真实点击）。
 *
 * 场景（汽车智能化新题材）：首页「历史题材地图」→ 选「汽车智能化」→ 标的历史事件 →
 * 查看事件窗口与相关标的（含反例）→ 查看证据 → **进入历史对象详情** → 关闭回到原上下文。
 *
 * ★ 环境说明：本机无 Chrome/Chromium（playwright-core 因沙箱拦截装不上）
 *   → 未做浏览器截图 / 窄屏视觉核验；这里用真实 DOM 点击，断言基于点击后状态。
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

describe('v0.15 端到端：汽车智能化题材 → 标的证据 → 历史对象详情', () => {
  it('★★ 题材 → 事件 → 反例标的 → 证据 → 对象详情 → 关闭回上下文', async () => {
    const { root, doc } = await mountApp();

    // ① 首页「历史题材地图」切到汽车智能化（第 5 个题材）
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    const tab = maps.querySelector('button[data-theme-id="AUTO_INTELLIGENCE"]') as HTMLButtonElement;
    expect(tab, '应有 AUTO_INTELLIGENCE tab').toBeTruthy();
    await click(tab);
    expect(tab.getAttribute('aria-selected')).toBe('true');

    // ② 标的索引先于逐事件列表（19 只标的）
    const index = maps.querySelector('[aria-label="历史参与标的索引"]')!;
    expect(index).not.toBeNull();
    expect(index.textContent).toContain('19');       // 标的数
    const iIndex = maps.innerHTML.indexOf('aria-label="历史参与标的索引"');
    const iEvents = maps.innerHTML.indexOf('class="fem-list"');
    expect(iIndex).toBeLessThan(iEvents);            // 索引在事件列表之前

    // ③ 展开 2024 Robotaxi 事件卡
    const card = maps.querySelector('li[data-event-id="AUTO-2024-ROBOTAXI"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    expect(card.querySelector('.fem-event-body')).not.toBeNull();

    // ④ 事件窗口 + 依据在场；对象身份是 Campaign（不是 RC）
    expect(card.textContent).toContain('2024-07-11 → 2024-07-29');
    expect(card.textContent).toContain('C-2024-ROBOTAXI');

    // ⑤ ★★ 反例标的：大众交通 category=COUNTER_EXAMPLE（运营牌照方，非智驾技术链）
    //    ★★ 反例（COUNTER_EXAMPLE）与证据不足（INSUFFICIENT）是**两回事**，页面不得混同
    const dt = [...card.querySelectorAll('li, tr, div')].find((el) =>
      el.textContent?.includes('大众交通')
      && el.textContent?.includes('反例')) as HTMLElement;
    expect(dt, '大众交通应标「反例（不同轴）」').toBeTruthy();
    expect(dt.textContent).toContain('反例（不同轴）');
    expect(dt.textContent).not.toContain('证据不足');
    // 反例的行情如实显示（不是隐藏）
    expect(card.textContent).toContain('600611');

    // ⑥ 查看对象详情（两道检查在 App 层都满足 → 有按钮）
    const openBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('查看对象详情')) as HTMLButtonElement;
    expect(openBtn, '事件卡应有「查看对象详情」按钮').toBeTruthy();
    await click(openBtn);

    // ⑦ CampaignDetail 打开，对象 id 一致（锚点核对；面板标题显示 season_id 而非 campaign_id）
    expect(detailPanel(doc)).not.toBeNull();
    expect(detailId(doc)).toBe('C-2024-ROBOTAXI');
    expect(detailPanel(doc)!.textContent).toContain('历史行情 · 2024');

    // ⑧ 关闭 → 回到题材地图，**上下文不丢**（tab 仍选中、事件卡仍展开）
    await click(detailPanel(doc)!.querySelector('button[aria-label="关闭"]') as HTMLButtonElement);
    expect(detailPanel(doc)).toBeNull();
    expect(maps.querySelector('button[data-theme-id="AUTO_INTELLIGENCE"]')!
      .getAttribute('aria-selected')).toBe('true');
    const cardAgain = maps.querySelector('li[data-event-id="AUTO-2024-ROBOTAXI"]') as HTMLElement;
    expect(cardAgain.querySelector('.fem-event-body')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ Research Candidate 不伪装成 Campaign；行情无覆盖如实留空', async () => {
    const { root, doc } = await mountApp();
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="AUTO_INTELLIGENCE"]') as HTMLButtonElement);

    const card = maps.querySelector('li[data-event-id="AUTO-2023-HUAWEI"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    const t = card.textContent ?? '';
    expect(t).toContain('RC-2023-HUAWEI');
    expect(t).toContain('Research Candidate');       // 身份标注
    expect(card.querySelector('.ecp-kind-candidate')).not.toBeNull();
    // 赛力斯：注册表在册，但行情不覆盖 2023 窗口 → 如实显示无数据状态
    expect(t).toContain('赛力斯');
    expect(t).toMatch(/行情数据不足|insufficient/);

    await act(async () => { root.unmount(); });
  });

  it('★★ 标的索引可搜索（万安科技跨 2019/2023 两个事件出现）', async () => {
    const { root, doc } = await mountApp();
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="AUTO_INTELLIGENCE"]') as HTMLButtonElement);

    const search = maps.querySelector('.tsi-search input') as HTMLInputElement;
    expect(search).not.toBeNull();
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    await act(async () => {
      setter.call(search, '万安');
      search.dispatchEvent(new window.Event('input', { bubbles: true }));
    });
    const index = maps.querySelector('[aria-label="历史参与标的索引"]')!;
    expect(index.textContent).toContain('万安科技');
    expect(index.textContent).not.toContain('大众交通');
    // 展开该标的：能看到两次出现的年份与纳入理由
    await click([...index.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('展开')) as HTMLButtonElement);
    expect(index.textContent).toContain('2019');
    expect(index.textContent).toContain('2023');

    await act(async () => { root.unmount(); });
  });
});
