// @vitest-environment jsdom
/**
 * ★★ v0.19 三场景真实工作流 —— **页面级** jsdom（真实 `<App />` + 真实数据 + 真实点击）。
 *
 * 目标（ThreeC 1.3 当前主线）：**方向查询 → 历史证据 → 可交接的研究请求草稿**。
 *
 * 场景 1｜汽车智能化（历史证据多、当前覆盖窄）
 * 场景 2｜医药（当前与历史两侧都有）
 * 场景 3｜文化传媒（历史有记录、当前无对应对象）
 *
 * ★ 所有断言基于**真实数据接线**：题材来自 `historical_event_maps_index.json`，
 *   方向命中来自 `exports/timeline_export_v1.json` + `current_candidates.json`。
 * ★ 环境说明：本机无 Chrome/Chromium → **未做浏览器截图 / 窄屏视觉核验**；
 *   这里用真实 DOM 点击，断言基于点击后状态（不为此停工）。
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

const btnIn = (scope: ParentNode, label: string) => {
  const b = [...scope.querySelectorAll('button')].find((x) => (x.textContent ?? '').includes(label));
  if (!b) throw new Error(`找不到按钮「${label}」`);
  return b as HTMLButtonElement;
};
const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };
const closeBtn = (panel: ParentNode) =>
  panel.querySelector('button[aria-label="关闭"]') as HTMLButtonElement;
const detailPanel = (doc: Document) =>
  doc.querySelector('aside.detail-panel[role="dialog"][aria-label="完整历史案例"]');
const detailId = (doc: Document) =>
  detailPanel(doc)?.getAttribute('data-campaign-id') ?? '';

/** 在「查一个方向」里提交一个关键词，返回结果块 */
async function queryDirection(doc: Document, q: string) {
  const input = doc.querySelector('input.dl-input') as HTMLInputElement;
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => {
    setter.call(input, q);
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
  await click(btnIn(doc, '查询'));
  return doc.querySelector('div.dl-result[role="status"]') as HTMLElement;
}

/** 在草稿里填「研究问题」与「历史时间范围」（模拟真实用户输入） */
async function fillDraft(doc: Document, questions: string, range: string) {
  const ta = doc.querySelector('textarea[aria-label="研究问题"]') as HTMLTextAreaElement;
  const tset = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')!.set!;
  await act(async () => {
    tset.call(ta, questions);
    ta.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
  const tr = doc.querySelector('input[aria-label="历史时间范围"]') as HTMLInputElement;
  const iset = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => {
    iset.call(tr, range);
    tr.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
}

/** 读取导出载荷（JSON / Markdown 预览 textarea） */
const exportJsonRaw = (doc: Document): string =>
  (doc.querySelector('textarea[aria-label="草稿 JSON"]') as HTMLTextAreaElement).value;
const exportJson = (doc: Document): Record<string, unknown> => JSON.parse(exportJsonRaw(doc));
const exportMd = (doc: Document): string =>
  (doc.querySelector('textarea[aria-label="草稿 Markdown"]') as HTMLTextAreaElement).value;

/** ★ 注入可捕获的剪贴板（`currentClipboardEnv()` 读 `navigator.clipboard`） */
function stubClipboard(impl: { writeText(text: string): Promise<void> } | null) {
  Object.defineProperty(window.navigator, 'clipboard', { configurable: true, value: impl });
}

/* ================================================================ 场景 1 */

describe('场景 1｜汽车智能化：历史证据较丰富，当前覆盖较窄', () => {
  it('★★ 方向查询 → 当前/历史两侧命中与覆盖边界可见 → 进历史对象详情 → 草稿带上方向+证据', async () => {
    const { root, doc } = await mountApp();
    const result = await queryDirection(doc, '汽车');
    const t = result.textContent ?? '';

    // ① 覆盖边界：verdict 说明是哪一种，且**不**声称「当前覆盖充分」
    expect(t).toContain('该方向');
    expect(t).toMatch(/两侧都有|只有历史案例|只有当前研究对象/);
    expect(t).not.toContain('覆盖充分');

    // ② 两侧命中各自成块、**计数可见**（历史丰富 vs 当前窄，用户自己看得出）
    const cur = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('当前研究对象'),
    )!;
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    )!;
    expect(cur, '汽车应有当前研究对象块').toBeTruthy();
    expect(hist, '汽车应有历史案例块').toBeTruthy();
    const curN = Number(/(\d+)/.exec(cur.querySelector('h4')!.textContent!)![1]);
    const histN = Number(/(\d+)/.exec(hist.querySelector('h4')!.textContent!)![1]);
    expect(curN).toBeGreaterThanOrEqual(1);
    expect(histN).toBeGreaterThanOrEqual(5);
    expect(histN).toBeGreaterThan(curN);          // ★ 两侧不对称**可见**

    // ③ 命中依据可解释（不是光给一个 id）
    const firstCase = hist.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    expect(caseId.startsWith('C-')).toBe(true);
    expect(hist.textContent).toContain('命中：');

    // ④ 打开历史对象详情
    await click(firstCase);
    expect(detailPanel(doc)).not.toBeNull();
    expect(detailId(doc)).toBe(caseId);
    await click(closeBtn(detailPanel(doc)!));
    expect(detailPanel(doc)).toBeNull();

    // ⑤ 把关注方向 + 研究问题 + 时间范围带入草稿；覆盖证据随草稿冻结
    await fillDraft(doc, 'L3 强制国标落地前后，产业链哪一段先反应？', '2018-2025');
    const payload = exportJson(doc) as {
      request: { direction: string; research_questions: string[]; time_range: string };
      linkage: { linked_query: string; evidence_source: string };
      coverage_check: { executed: boolean; query: string; current_objects: unknown[]; historical_cases: unknown[] };
    };
    expect(payload.request.direction).toBe('汽车');                 // 方向 = 查询词
    expect(payload.request.research_questions).toContain('L3 强制国标落地前后，产业链哪一段先反应？');
    expect(payload.request.time_range).toBe('2018-2025');           // 用户填写的时间范围保留
    expect(payload.linkage.linked_query).toBe('汽车');
    expect(payload.linkage.evidence_source).toBe('frozen_snapshot');
    expect(payload.coverage_check.executed).toBe(true);
    expect(payload.coverage_check.current_objects.length).toBeGreaterThanOrEqual(1);
    expect(payload.coverage_check.historical_cases.length).toBeGreaterThanOrEqual(5);

    await act(async () => { root.unmount(); });
  });

  it('★★ 历史题材地图（汽车智能化）：事件 → 相关标的 → 纳入理由 全部可达', async () => {
    const { root, doc } = await mountApp();
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="AUTO_INTELLIGENCE"]') as HTMLButtonElement);

    expect(maps.querySelector('[aria-label="历史参与标的索引"]')).not.toBeNull();
    const card = maps.querySelector('li[data-event-id="AUTO-2024-ROBOTAXI"]') as HTMLElement;
    expect(card).toBeTruthy();
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    expect(card.textContent).toContain('纳入理由');
    expect(card.querySelector('li.fem-part')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });
});

/* ================================================================ 场景 2 */

describe('场景 2｜医药：当前与历史两侧都有数据', () => {
  it('★★ 两侧命中清晰 · 详情可打开 · 草稿保留用户输入与查询证据 · 两侧证据不混为一条', async () => {
    const { root, doc } = await mountApp();
    const result = await queryDirection(doc, '医药');
    const t = result.textContent ?? '';
    expect(t).toMatch(/两侧都有|只有历史案例|只有当前研究对象/);

    const cur = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('当前研究对象'),
    );
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    )!;
    // ★ 两侧证据**分成两个块**（不混为同一条证据）
    expect(cur, '医药应有当前研究对象块').toBeTruthy();
    expect(hist, '医药应有历史案例块').toBeTruthy();

    // 进历史对象详情
    const firstCase = hist.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    await click(firstCase);
    expect(detailId(doc)).toBe(caseId);
    expect(detailPanel(doc)!.textContent).toContain('生命周期');
    await click(closeBtn(detailPanel(doc)!));

    // 草稿：用户输入 + 查询证据都保留
    await fillDraft(doc, '历史上医药行情由政策驱动时，持续时间中位数是多少？', '2015-2023');
    const payload = exportJson(doc) as {
      request: { research_questions: string[]; time_range: string };
      coverage_check: {
        current_objects: { id: string; matched_on: string[] | null }[];
        historical_cases: { id: string; matched_on: string[] | null }[];
      };
    };
    expect(payload.request.research_questions).toContain('历史上医药行情由政策驱动时，持续时间中位数是多少？');
    expect(payload.request.time_range).toBe('2015-2023');

    // ★★ 两侧证据必须是**两个独立数组**，各自带自己的命中依据
    const curIds = payload.coverage_check.current_objects.map((o) => o.id);
    const histIds = payload.coverage_check.historical_cases.map((o) => o.id);
    expect(curIds.length).toBeGreaterThanOrEqual(1);
    expect(histIds.length).toBeGreaterThanOrEqual(1);
    expect(curIds.every((id) => !histIds.includes(id))).toBe(true);
    expect(payload.coverage_check.current_objects[0].matched_on).not.toBeNull();
    expect(payload.coverage_check.historical_cases[0].matched_on).not.toBeNull();

    await act(async () => { root.unmount(); });
  });
});

/* ================================================================ 场景 3 */

describe('场景 3｜文化传媒：历史有记录，当前无对应对象', () => {
  it('★★ 当前侧明确「未命中」而非系统故障 · 历史事件/标的可查看 · 草稿仍可建立', async () => {
    const { root, doc } = await mountApp();
    const result = await queryDirection(doc, '文化传媒');
    const t = result.textContent ?? '';

    const cur = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('当前研究对象'),
    );
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    )!;
    // ★ 当前侧：**明确说明**当前结构化数据未命中（不得只说「未覆盖」或装作故障）
    expect(cur, '文化传媒当前侧应为空').toBeFalsy();
    expect(t).toContain('只有历史案例');
    expect(t).toContain('当前侧没有研究对象');
    expect(t).toContain('历史可用');                 // 不得误报为「完全没有历史覆盖」
    expect(t).not.toContain('两侧都有');
    expect(hist, '文化传媒应有历史案例').toBeTruthy();

    // 进历史对象详情
    const firstCase = hist.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    await click(firstCase);
    expect(detailId(doc)).toBe(caseId);
    await click(closeBtn(detailPanel(doc)!));

    // 研究请求草稿仍然可建立（即便当前侧为空）
    await fillDraft(doc, '文化传媒 2023 的 AI 行情，历史上是否有同类「技术叙事驱动」案例？', '2015-2025');
    const payload = exportJson(doc) as {
      request: { direction: string; research_questions: string[]; time_range: string };
      coverage_check: { executed: boolean; current_objects: unknown[]; historical_cases: unknown[]; verdict: string };
    };
    expect(payload.request.research_questions).toContain('文化传媒 2023 的 AI 行情，历史上是否有同类「技术叙事驱动」案例？');
    expect(payload.request.time_range).toBe('2015-2025');
    expect(payload.coverage_check.executed).toBe(true);
    expect(payload.coverage_check.current_objects).toHaveLength(0);
    expect(payload.coverage_check.historical_cases.length).toBeGreaterThan(0);
    expect(payload.coverage_check.verdict).toBe('historical-only');

    // ★★ Markdown 导出：**用户输入**（§1–5）与**系统命中**（§6）必须分开
    const md = exportMd(doc);
    expect(md).toContain('## 1. 研究方向');
    expect(md).toContain('## 2. 希望回答的研究问题');
    expect(md).toContain('## 5. 希望调查的历史时间范围');
    expect(md).toContain('## 6. 覆盖查询结果（工具侧事实）');
    expect(md).toContain('文化传媒 2023 的 AI 行情，历史上是否有同类「技术叙事驱动」案例？');
    expect(md).toContain('2015-2025');
    expect(md).toContain('当前研究对象命中 0 个');
    expect(md).toContain('历史案例命中');

    await act(async () => { root.unmount(); });
  });

  it('★★ 历史题材地图（文化传媒 MEDIA）：事件 → 相关标的 → 纳入理由 可查看', async () => {
    const { root, doc } = await mountApp();
    const maps = doc.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="MEDIA"]') as HTMLButtonElement);
    expect(maps.querySelector('button[data-theme-id="MEDIA"]')!.getAttribute('aria-selected')).toBe('true');
    expect(maps.querySelector('[aria-label="历史参与标的索引"]')).not.toBeNull();

    const card = maps.querySelector('li[data-event-id]') as HTMLElement;
    expect(card).toBeTruthy();
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    expect(card.textContent).toContain('纳入理由');
    expect(card.querySelector('li.fem-part')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 复制 JSON / Markdown：捕获真实复制内容，与预览一致，且用户输入与系统命中分开', async () => {
    const { root, doc } = await mountApp();
    const copied: string[] = [];
    stubClipboard({ writeText: async (t) => { copied.push(t); } });

    await queryDirection(doc, '文化传媒');
    await fillDraft(doc, '文化传媒 2023 的 AI 行情是否有历史同类案例？', '2015-2025');

    const jsonPreview = exportJsonRaw(doc);
    const mdPreview = exportMd(doc);
    const dl = doc.querySelector('section.dl') as HTMLElement;

    // ① 复制 JSON：捕获内容 = 预览内容
    await click(btnIn(dl, '复制 JSON'));
    expect(copied).toHaveLength(1);
    expect(copied[0]).toBe(jsonPreview);
    expect(dl.textContent).toContain('已复制');

    // ② 复制 Markdown：捕获内容 = 预览内容
    await click(btnIn(dl, '复制 Markdown'));
    expect(copied).toHaveLength(2);
    expect(copied[1]).toBe(mdPreview);

    // ③ 复制内容里，**用户输入**与**系统命中**仍然分开
    const payload = JSON.parse(copied[0]) as {
      request: { research_questions: string[]; time_range: string };
      coverage_check: { executed: boolean; current_objects: unknown[]; historical_cases: unknown[] };
    };
    expect(payload.request.research_questions).toContain('文化传媒 2023 的 AI 行情是否有历史同类案例？');
    expect(payload.request.time_range).toBe('2015-2025');
    expect(payload.coverage_check.executed).toBe(true);
    expect(payload.coverage_check.current_objects).toHaveLength(0);      // 当前侧空
    expect(payload.coverage_check.historical_cases.length).toBeGreaterThan(0);
    expect(copied[1]).toContain('## 1. 研究方向');
    expect(copied[1]).toContain('## 6. 覆盖查询结果（工具侧事实）');
    expect(copied[1]).toContain('当前研究对象命中 0 个');

    await act(async () => { root.unmount(); });
  });

  it('★★ 复制失败（权限被拒）不虚报成功，并给出下一步（复用既有失败路径）', async () => {
    const { root, doc } = await mountApp();
    stubClipboard({
      writeText: async () => {
        const err = new Error('denied');
        err.name = 'NotAllowedError';
        throw err;
      },
    });

    await queryDirection(doc, '文化传媒');
    const dl = doc.querySelector('section.dl') as HTMLElement;
    await click(btnIn(dl, '复制 JSON'));

    expect(dl.textContent).toContain('复制失败');
    expect(dl.textContent).toContain('权限被拒绝');
    expect(dl.textContent).toContain('手动选中复制');       // 给出下一步
    expect(dl.textContent).not.toContain('已复制');         // ★ 绝不虚报成功

    await act(async () => { root.unmount(); });
  });
});
