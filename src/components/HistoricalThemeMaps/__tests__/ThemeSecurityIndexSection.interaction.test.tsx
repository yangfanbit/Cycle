// @vitest-environment jsdom
/**
 * ★★ 历史参与标的索引 —— **真实搜索与展开**（v0.11）。
 *
 * SSR 只能证明「默认渲染了什么」；搜索与展开必须真点。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { eventMapByTheme } from '../../../data/timeline/historicalEventMaps';
import { ThemeSecurityIndexSection } from '../ThemeSecurityIndexSection';

const fluDoc = eventMapByTheme('FLU')!.doc;

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
  await act(async () => { root.render(<ThemeSecurityIndexSection doc={fluDoc} />); });
  return { root, host };
}

const rows = (host: HTMLElement) => [...host.querySelectorAll('tr[data-security-id]')];

/** React 受控 input：必须用 native setter + dispatch，否则值被 tracker 吞掉 */
async function type(host: HTMLElement, value: string): Promise<void> {
  const input = host.querySelector('input[aria-label="按名称或代码搜索标的"]') as HTMLInputElement;
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => {
    setter.call(input, value);
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
}

describe('标的索引 · 搜索与展开（jsdom 真点）', () => {
  it('★★ 搜索按名称 / 代码过滤；清除后恢复全部', async () => {
    const { root, host } = await mount();
    expect(rows(host)).toHaveLength(20);

    await type(host, '华兰');
    expect(rows(host).map((r) => r.getAttribute('data-security-id')))
      .toEqual(['HUALAN-002007', 'HUALANVAX']);

    await type(host, '002007');
    expect(rows(host)).toHaveLength(1);
    expect(rows(host)[0].getAttribute('data-security-id')).toBe('HUALAN-002007');

    await type(host, '不存在的公司');
    expect(rows(host)).toHaveLength(0);
    expect(host.textContent).toContain('未记录 ≠ 未参与');

    await type(host, '');
    expect(rows(host)).toHaveLength(20);

    await act(async () => { root.unmount(); });
  });

  it('★★ 点「展开」看到该标的的逐次事件记录（含证据等级与纳入理由）', async () => {
    const { root, host } = await mount();
    await type(host, '百克生物');

    const row = rows(host)[0];
    expect(row.getAttribute('data-security-id')).toBe('BAIKEBIO');
    // 摘要里两类证据都在（不合并成单一标签）
    expect(row.textContent).toContain('业务机制已核实');
    expect(row.textContent).toContain('仅报道点名');

    const toggle = row.querySelector('button') as HTMLButtonElement;
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    await act(async () => { toggle.click(); });
    expect(toggle.getAttribute('aria-expanded')).toBe('true');

    // 明细里逐次列出事件、理由、证据等级
    const occs = [...host.querySelectorAll('li[data-occ-event]')];
    expect(occs.length).toBe(2);
    expect(host.textContent).toContain('纳入理由');
    expect(host.textContent).toContain('来源');
    // 两次出现的证据等级都在明细里（逐次呈现）
    expect(host.querySelectorAll('.tsi-ev.ev-business_verified').length).toBe(1);
    expect(host.querySelectorAll('.tsi-ev.ev-report_named').length).toBe(1);

    // 再点一次收起
    await act(async () => { toggle.click(); });
    expect(host.querySelectorAll('li[data-occ-event]')).toHaveLength(0);

    await act(async () => { root.unmount(); });
  });
});
