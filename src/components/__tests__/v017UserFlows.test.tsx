// @vitest-environment jsdom
/**
 * ★★ v0.17 端到端用户场景 —— **页面级** jsdom 交互（挂载真实 `<App />` + 真实点击）。
 *
 * ① 半导体 2023 AI 算力事件：行情表显示**名称 / 代码 / 关系类别 / 窗口状态**（不再只给 security_id），
 *    完整窗口行标「完整窗口已计算」；
 * ② 参与者行与事件正文都呈现「与 Research 对象的标的对账」（精确匹配三类之一）；
 * ③ 覆盖不足行情（海光信息 2022-08-12 ~ 2022-10-12）如实显示
 *    「仅局部数据，不可视为完整窗口可比结果」+ 实际可用首末日期；
 * ④ 走通「事件行情 → 查看对象详情 → 关闭回上下文」。
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
  await click(tab);
  expect(tab.getAttribute('aria-selected')).toBe('true');
  return maps;
}

async function expandCard(maps: HTMLElement, eventId: string): Promise<HTMLElement> {
  const card = maps.querySelector(`li[data-event-id="${eventId}"]`) as HTMLElement;
  expect(card, `应有 ${eventId} 事件卡`).toBeTruthy();
  await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
  expect(card.querySelector('.fem-event-body')).not.toBeNull();
  return card;
}

describe('v0.17 端到端：行情表可信展示 + 标的对账 → 对象详情', () => {
  it('★★ 2023 AI 算力事件：行情表有类别/窗口状态，对账呈现，且能进对象详情再关闭', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);
    const card = await expandCard(maps, 'SEMI-2023-AI-COMPUTE');
    const t = card.textContent ?? '';

    // ① 行情表列头 + 状态：不再只显示 security_id
    expect(t).toContain('关系类别');
    expect(t).toContain('窗口状态');
    expect(t).toContain('完整窗口已计算');
    // 名称在场（寒武纪），代码在场
    expect(t).toContain('寒武纪');
    expect(t).toContain('688256');

    // ② 事件正文的标的对账汇总
    expect(t).toContain('与 Research 对象的标的对账');
    expect(t).toContain('对象已登记关联');
    expect(t).toContain('C-2023-AI-COMPUTE-SEMI');

    // ③ 参与者行带「对象对账」徽标（精确匹配）
    const cambriconRow = [...card.querySelectorAll('li.fem-part')].find((el) =>
      el.textContent?.includes('寒武纪')) as HTMLElement;
    expect(cambriconRow, '应有寒武纪参与者行').toBeTruthy();
    expect(cambriconRow.textContent).toContain('对象对账：对象已登记关联');

    // ④ 进入对象详情（对象可解析 → 有按钮）
    const openBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('查看对象详情')) as HTMLButtonElement;
    expect(openBtn, '事件卡应有「查看对象详情」按钮').toBeTruthy();
    await click(openBtn);
    expect(detailPanel(doc)).not.toBeNull();
    expect(detailId(doc)).toBe('C-2023-AI-COMPUTE-SEMI');

    // ⑤ 关闭 → 上下文不丢
    await click(detailPanel(doc)!.querySelector('button[aria-label="关闭"]') as HTMLButtonElement);
    expect(detailPanel(doc)).toBeNull();
    expect(maps.querySelector('button[data-theme-id="SEMICONDUCTOR_AI"]')!
      .getAttribute('aria-selected')).toBe('true');

    await act(async () => { root.unmount(); });
  });

  it('★★ 覆盖不足行情如实显示实际首末 + 不得与完整窗口结果等价', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);
    const card = await expandCard(maps, 'SEMI-2022-DOWNTURN');
    const t = card.textContent ?? '';

    // 覆盖不足行（海光信息 trading_days 38 < 窗口 60%）→ 局部数据声明 + 实际可用首末
    expect(t).toContain('仅局部数据，不可视为完整窗口可比结果');
    expect(t).toContain('实际可用 2022-08-12 ~ 2022-10-12');
    // 同一张表里也有完整窗口行
    expect(t).toContain('完整窗口已计算');

    // 行为层面：既有 INSUFFICIENT 行，也有 COMPUTED 行
    const statuses = [...card.querySelectorAll('tr[data-perf-status]')]
      .map((tr) => tr.getAttribute('data-perf-status'));
    expect(statuses).toContain('INSUFFICIENT');
    expect(statuses).toContain('COMPUTED');

    await act(async () => { root.unmount(); });
  });

  it('★★ 标的索引逐次记录呈现对账结果（六题材通用，半导体已登记）', async () => {
    const { root, doc } = await mountApp();
    const maps = await openTheme(doc);
    const index = maps.querySelector('[aria-label="历史参与标的索引"]')!;

    // 索引头部对账汇总
    const totals = index.querySelector('[data-tsi-recon="totals"]')!;
    expect(totals.textContent).toContain('对象已登记关联');
    expect(totals.textContent).toContain('地图补充记录');
    expect(totals.textContent).toContain('无法核对');

    // 展开一只标的 → 逐次记录里带对账行
    const expandBtn = [...index.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('展开')) as HTMLButtonElement;
    expect(expandBtn).toBeTruthy();
    await click(expandBtn);
    expect(index.querySelector('[data-recon-link]')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });
});
