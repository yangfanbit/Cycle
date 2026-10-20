// @vitest-environment jsdom
/**
 * ★★ v0.25 端到端用户场景 —— 「季节性日历 → 历史地图 → 历史事件 → 标的及证据 →
 *    启动前观察」一条路径走通（Phase D 验收标准第 7 项）。
 *
 * 走 **双十一（EXT-08，默认优先区）→ 消费旺季 / 大众消费**（v0.25 新地图）：
 *   ① 首页「外部季节性观察雷达」卡片 → 「在历史题材地图中查看」→ 选中 CONSUMER_SEASON；
 *   ② 该题材地图渲染 5 个事件，展开第一个（白酒消费升级）；
 *   ③ 事件卡显示窗口（Campaign 主升段，不是季节性月份）+ 参与标的与关系性质；
 *   ④ 「查看对象详情」→ Campaign 详情 = 启动前观察（L1 市场层 + L2 标的层，
 *      **缺数据标的原因**也在内：2016 段行情为负价 → invalid_price_series 的声明可见）；
 *   ⑤ 关闭 → 回地图，上下文不丢。
 *
 * ★ 全部基于真实数据点击；预期失败即失败（不得伪造通过）。
 * ★ 用 **EXT-08（双十一）** 而不是 EXT-02：雷达详细卡片默认只铺开 4 个优先项
 *   （EXT-11/08/12/09），EXT-02 的卡在折叠区 —— 这与产品行为一致，不是缺陷。
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

describe('v0.25 端到端：季节性线索 → 新题材地图 → 事件 → 标的证据 → 启动前观察', () => {
  it('★★ 双十一线索 → 消费旺季地图 → 白酒事件 → 对象详情（含启动前观察）', async () => {
    const { root, doc } = await mountApp();

    // ① 外部季节性雷达：双十一卡片带「在历史题材地图中查看」按钮
    const card = doc.querySelector('li[data-entry-id="EXT-08"]') as HTMLElement;
    expect(card, '应有 EXT-08（双十一）卡片').toBeTruthy();
    const mapBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('在「历史题材地图」中查看')) as HTMLButtonElement;
    expect(mapBtn, 'EXT-08 应带地图跳转按钮（映射到 CONSUMER_SEASON）').toBeTruthy();
    await click(mapBtn);

    // ② 首页地图切到 CONSUMER_SEASON，且渲染 5 个事件
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    const tab = maps.querySelector('button[data-theme-id="CONSUMER_SEASON"]') as HTMLButtonElement;
    expect(tab, '应有 CONSUMER_SEASON tab').toBeTruthy();
    expect(tab.getAttribute('aria-selected')).toBe('true');
    expect(maps.querySelectorAll('li[data-event-id]').length).toBe(5);

    // ③ 展开第一个事件（白酒消费升级）—— 窗口 = Campaign 主升段
    const first = maps.querySelector('li[data-event-id="CONS-2016-BAIJIU"]') as HTMLElement;
    expect(first, '应有 CONS-2016-BAIJIU 事件卡').toBeTruthy();
    await click(first.querySelector('button.fem-event-head') as HTMLButtonElement);
    expect(first.querySelector('.fem-event-body')).not.toBeNull();
    const t = first.textContent ?? '';
    expect(t).toContain('C-2016-CONS-BAIJIU-UPGRADE');       // 挂库内 Campaign
    expect(t).toContain('贵州茅台');                          // 代表参与标的
    expect(t).toContain('直接机制');                          // 关系性质分层
    // 2016 段行情不可用（qfq 负价）→ 明确缺失，不补 0
    expect(t).toMatch(/行情不可得|invalid_price|无法|不足/);
    expect(t).not.toContain('+0.0%');

    // ④ 查看对象详情 → Campaign 详情（启动前观察在）
    const openBtn = [...first.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('查看对象详情')) as HTMLButtonElement;
    expect(openBtn, '事件卡应有「查看对象详情」按钮').toBeTruthy();
    await click(openBtn);
    const panel = detailPanel(doc)!;
    expect(panel).not.toBeNull();
    expect(panel.getAttribute('data-campaign-id')).toBe('C-2016-CONS-BAIJIU-UPGRADE');
    const pt = panel.textContent ?? '';
    expect(pt).toContain('启动前观察');                        // Phase D 区块
    expect(pt).toContain('L1 · 市场层');                      // 基准层（无选择偏差）
    // ★ 该 Campaign 启动前观察 = **OK**（提前观察用**原始价**算；负价只影响前复权窗口指标）
    //   —— 断言与产物逐字一致，不把「事件行情不可算」误当成「启动前观察也没有」
    expect(pt).toContain('贵州茅台');
    expect(pt).not.toContain('启动前数据不足');
    expect(pt).toContain('T-60');                             // L1 多检查点

    // ⑤ 关闭 → 回地图，上下文不丢（tab 仍选中、事件卡仍展开）
    await click(panel.querySelector('button[aria-label="关闭"]') as HTMLButtonElement);
    expect(detailPanel(doc)).toBeNull();
    expect(maps.querySelector('li[data-event-id="CONS-2016-BAIJIU"] .fem-event-body'))
      .not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 无地图线索（供暖 / 能源）→ 「带入『研究方向』草稿」按钮存在且不带地图假入口', async () => {
    const { root, doc } = await mountApp();
    const card = doc.querySelector('li[data-entry-id="EXT-09"]') as HTMLElement;
    expect(card, '应有 EXT-09（供暖 / 能源）卡片').toBeTruthy();
    // 无地图：不显示地图跳转按钮，明写「暂无历史事件地图」
    expect(card.textContent).toContain('暂无历史事件地图');
    const mapBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('在「历史题材地图」中查看'));
    expect(mapBtn, '无地图不得给地图跳转按钮').toBeUndefined();
    // 有草稿入口
    const draftBtn = [...card.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('带入「研究方向」草稿')) as HTMLButtonElement;
    expect(draftBtn, '无地图线索应有草稿入口').toBeTruthy();

    await act(async () => { root.unmount(); });
  });
});
