// @vitest-environment jsdom
/**
 * ★★ v0.21 端到端：历史事件详情里的「与当前冻结 SA 的关系」（页面级 jsdom + 真实 App + 真实数据）。
 *
 * ① 有对象引用且被冻结 SA 引用 → 列出引用它的当前研究对象 + 既有 `structural_status`；
 * ② 事件未记录对象 → 明确说明「无法进行对象级交叉引用」（**不**推测归属）；
 * ③ SA 对象级状态与「证券注册表 / 四分类对账」**分开呈现**，不混为一谈。
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

const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };

/** 等待异步（冻结 SA 快照按需载入）完成：轮询式 act 冲刷 */
async function waitFor(pred: () => boolean, tries = 60): Promise<boolean> {
  for (let i = 0; i < tries; i += 1) {
    if (pred()) return true;
    // eslint-disable-next-line no-await-in-loop
    await act(async () => { await new Promise((r) => { setTimeout(r, 10); }); });
  }
  return pred();
}

async function mountAndOpenTheme(themeId: string): Promise<{ root: Root; doc: Document; maps: HTMLElement }> {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => { root.render(<App />); });
  const maps = document.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
  await click(maps.querySelector(`button[data-theme-id="${themeId}"]`) as HTMLButtonElement);
  return { root, doc: document, maps };
}

describe('v0.21 端到端：历史事件 × 冻结 SA 交叉引用', () => {
  it('★★ 半导体 2023 AI 算力事件：列出引用它的当前研究对象与既有 SA 状态', async () => {
    const { root, maps } = await mountAndOpenTheme('SEMICONDUCTOR_AI');
    const card = maps.querySelector('li[data-event-id="SEMI-2023-AI-COMPUTE"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);

    // 快照按需载入 → 等 SA 块出现
    const ok = await waitFor(() => card.querySelector('[data-sa-match]:not([data-sa-match="not-loaded"])') !== null);
    expect(ok, '冻结 SA 块应载入（不再是 not-loaded）').toBe(true);

    const found = card.querySelector('[data-sa-match="found"]');
    expect(found, '该事件对象应在冻结 SA 中有记录').not.toBeNull();
    expect(card.textContent).toContain('与当前冻结 SA 的关系');
    expect(card.textContent).toContain('MS-2026-10-13-01');

    // 列出 6 个当前研究对象（快照是对每个当前对象各一条）
    const rows = card.querySelectorAll('[data-sa-current]');
    expect(rows.length).toBe(6);
    const ids = [...rows].map((r) => r.getAttribute('data-sa-current'));
    expect(ids.every((x) => (x ?? '').startsWith('CC-'))).toBe(true);
    // 每条都有状态标签
    const statuses = [...rows].map((r) => r.getAttribute('data-sa-status'));
    expect(statuses.some((s) => s === 'NO_VALID_CORRESPONDENCE')).toBe(true);

    // ★ 与证券对账**分开**：两块的声明同时在场
    expect(card.textContent).toContain('行情记录存在');

    await act(async () => { root.unmount(); });
  });

  it('★★ 流感 2017 事件：未记录对象 → 明确「无法进行对象级交叉引用」（不推测）', async () => {
    const { root, maps } = await mountAndOpenTheme('FLU');
    const card = maps.querySelector('li[data-event-id="FLU-2017-AVIAN"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);

    const ok = await waitFor(() => card.querySelector('[data-sa-match="no-object"]') !== null);
    expect(ok, '应有「未记录对象」说明').toBe(true);
    expect(card.textContent).toContain('事件未记录关联对象');
    expect(card.querySelector('[data-sa-match="found"]')).toBeNull();

    await act(async () => { root.unmount(); });
  });
});
