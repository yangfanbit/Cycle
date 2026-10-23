// @vitest-environment jsdom
/**
 * ★★ 不变量：研究侧字符串里的 Markdown `**强调**` **不得**原样显示成星号。
 *
 * 这是本项目反复踩到的陷阱（v0.28 / v0.31 都出现过）：研究侧 JSON 里的 `**...**`
 * 直接塞进 JSX 会渲染成两个星号。修法是**渲染侧**过 `RichText`（或改写成 `<strong>`），
 * 不改研究产物。
 *
 * 本测试是**页面级**扫描：挂载真实 `<App />`（真实静态数据），
 * 对整棵渲染树的 `textContent` 做一次正则扫描 —— 只要页面上还有一处裸星号就失败。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { renderToStaticMarkup } from 'react-dom/server';

import App from '../../App';
import { ExternalSeasonalRadar } from '../ExternalSeasonalRadar/ExternalSeasonalRadar';

const RAW_MD = /\*\*[^*\n]+\*\*/;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  window.localStorage.clear();
});

afterEach(() => {
  act(() => { root?.unmount(); });
  container?.remove();
  root = null;
  container = null;
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

describe('★★ 渲染不变量 · Markdown 星号不得原样显示', () => {
  it('外部季节性雷达（真实数据）：整块渲染无裸 **', () => {
    const html = renderToStaticMarkup(<ExternalSeasonalRadar today="2026-10-13" />);
    const text = html.replace(/<[^>]+>/g, ' ');
    expect(text).not.toMatch(RAW_MD);
  });

  it('整页 <App />（真实数据 · jsdom）：正文无裸 **', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => { root!.render(<App />); });
    // 快照/SA 为异步载入 —— 给它们落地时间（不等待具体文案，只等稳定）
    for (let i = 0; i < 20; i += 1) {
      await act(async () => { await new Promise((r) => setTimeout(r, 100)); });
    }
    // ★ 只看**渲染出来的正文**：`<textarea>` 里是导出原文（Markdown / JSON），
    //   本来就该保留 `**`，不算渲染缺陷。
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    const offenders: string[] = [];
    let node: Node | null = walker.nextNode();
    while (node) {
      const tag = (node.parentElement?.tagName ?? '').toUpperCase();
      const text = node.nodeValue ?? '';
      if (!['TEXTAREA', 'SCRIPT', 'STYLE'].includes(tag) && RAW_MD.test(text)) {
        offenders.push(`${tag}: ${text.slice(0, 60)}`);
      }
      node = walker.nextNode();
    }
    expect(offenders, `页面上出现了裸 Markdown：${offenders.slice(0, 3).join(' | ')}`).toEqual([]);
  });
});
