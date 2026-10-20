// @vitest-environment jsdom
/**
 * ★★ v0.14 四个真实用户场景 —— **页面级** jsdom 交互（挂载真实 `<App />` + 真实点击）。
 *
 * 场景 1：汽车 —— 历史季节性地图选主题 → 附页明细 → Campaign 详情；
 *         再在「查一个方向」里查「汽车」，核对当前/历史两侧与「查找 ≠ 结构对应」。
 * 场景 2：医药健康 —— 方向查询「医药」→ 历史对象详情（生命周期 / 研究问题）
 *         → 流感历史题材地图（标的索引 / 事件详情 / 经验基准概率）。
 * 场景 3：文化传媒 —— 查询后确认历史侧如实、当前侧**不谎报**；
 *         进完整对象详情 → 草稿可编辑、导出不假报。
 * 场景 4：外部线索 —— EXT-12 对照 → **查看对象详情** → 关闭返回对照上下文；
 *         EXT-17（未映射）→ 带入研究请求草稿（空草稿直接带入）。
 *
 * ★ 环境说明：本机无 Chrome/Chromium，`playwright-core` 因沙箱拦截装不上
 *   → 未做浏览器截图级验证；这里用真实 DOM 点击（断言全部基于点击后状态）。
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
/** 详情面板的关闭按钮（文本是「×」，按 aria-label 选） */
const closeBtn = (panel: ParentNode) =>
  panel.querySelector('button[aria-label="关闭"]') as HTMLButtonElement;

/** 在「查一个方向」里提交一个关键词 */
async function queryDirection(doc: Document, q: string) {
  const input = doc.querySelector('input.dl-input') as HTMLInputElement;
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => {
    setter.call(input, q);
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
  // ★ v0.25：按**类选择器**点查询按钮 —— 页面上还有 radar 的「带入…草稿」按钮，
  //   用文本包含匹配会误点它（这是 v0.25 接线时真实踩到的坑）。
  const btn = doc.querySelector('button.dl-btn') as HTMLButtonElement;
  await click(btn);
  return doc.querySelector('div.dl-result[role="status"]') as HTMLElement;
}

const detailPanel = (doc: Document) =>
  doc.querySelector('aside.detail-panel[role="dialog"][aria-label="完整历史案例"]');
/** 详情面板的对象 id 锚点（v0.14：页面自身可核对「这是哪个对象」） */
const detailId = (doc: Document) =>
  detailPanel(doc)?.getAttribute('data-campaign-id') ?? '';

describe('场景 1：汽车（地图 → 附页 → 详情 → 方向查询）', () => {
  it('★★ 主题行 → 历史年度明细 → 打开 Campaign 详情 → 关闭回上下文', async () => {
    const { root, doc } = await mountApp();

    // 首页季节性地图上找「汽车」行（大主题粒度）
    const row = [...doc.querySelectorAll('div.sm-row')].find(
      (r) => (r.textContent ?? '').includes('汽车'),
    );
    expect(row, '首页应有「汽车」主题行').toBeTruthy();
    await click(row as HTMLElement);

    // 附页（MacroThemeSheet）：口径如实（8 Campaign / 1 Research Candidate）
    const sheet = doc.querySelector('div.theme-sheet[role="dialog"]') as HTMLElement;
    expect(sheet).not.toBeNull();
    expect(sheet.getAttribute('aria-label')).toContain('汽车');
    expect(sheet.textContent).toContain('8 Campaign / 1 Research Candidate');

    // 打开第一个对象（附页里第一个 ts-open 按钮）
    const firstOpen = sheet.querySelector('button.ts-open') as HTMLButtonElement;
    const firstTitle = (firstOpen.textContent ?? '').slice(0, 12);
    await click(firstOpen);

    const panel = detailPanel(doc)!;
    expect(panel).not.toBeNull();
    expect(panel.textContent).toContain('历史行情 ·');   // Campaign 身份
    expect(panel.textContent?.slice(0, 200)).toContain(firstTitle.slice(0, 4));

    // 关闭 → 回到附页（上下文不丢），附页仍在
    await click(closeBtn(panel));
    expect(detailPanel(doc)).toBeNull();
    expect(doc.querySelector('div.theme-sheet[role="dialog"]')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 「查一个方向」查「汽车」：当前 / 历史两侧如实，并能进历史对象', async () => {
    const { root, doc } = await mountApp();

    // 先关掉可能开着的附页，避免遮挡（点主题行切换）——直接开始查询
    const result = await queryDirection(doc, '汽车');
    expect(result).not.toBeNull();
    const t = result.textContent ?? '';

    // 语义边界必须在场：这是查找，不是结构对应
    expect(t).toContain('该方向');
    expect(t).toMatch(/两侧都有|只有历史案例|只有当前研究对象/);

    // 历史侧命中并如实显示
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    );
    expect(hist, '汽车应有历史案例命中').toBeTruthy();
    const firstCase = hist!.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    expect(caseId.startsWith('C-')).toBe(true);
    await click(firstCase);

    // 进入历史对象详情（复用同一 CampaignDetail）
    const panel = detailPanel(doc)!;
    expect(detailId(doc)).toBe(caseId);

    await act(async () => { root.unmount(); });
  });
});

describe('场景 2：医药健康（方向查询 → 详情 → 流感地图）', () => {
  it('★★ 查「医药」：两侧命中 / 进详情看生命周期 / 流感地图全套仍在', async () => {
    const { root, doc } = await mountApp();
    const result = await queryDirection(doc, '医药');
    const t = result.textContent ?? '';

    // 历史侧有命中；当前侧如实（有就显示块，没有就不显示「当前研究对象」块）
    const cur = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('当前研究对象'),
    );
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    );
    expect(hist, '医药应有历史案例').toBeTruthy();
    // 不得谎报：verdict 与块的存在必须一致
    if (cur) expect(t).toMatch(/两侧都有/);
    else expect(t).not.toContain('两侧都有');

    // 进历史对象详情：生命周期字段在场
    const firstCase = hist!.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    await click(firstCase);
    const panel = detailPanel(doc)!;
    expect(detailId(doc)).toBe(caseId);
    expect(panel.textContent).toContain('生命周期');

    // 关闭 → 回查询结果
    await click(closeBtn(panel));
    expect(detailPanel(doc)).toBeNull();

    // 进入流感历史题材地图：标的索引 / 事件详情 / 经验基准概率 / 跨年份 全部仍在
    const maps = doc.querySelector(`[aria-label="历史题材地图"]`) as HTMLElement;
    // 切到流感题材（若默认已是它，再点一次仍是幂等）
    await click(maps.querySelector('button[data-theme-id="FLU"]') as HTMLButtonElement);
    expect(maps.querySelector('button[data-theme-id="FLU"]')?.getAttribute('aria-selected'))
      .toBe('true');
    expect(maps.querySelector('[aria-label="历史参与标的索引"]')).not.toBeNull();
    expect(maps.querySelector('[data-event-id="FLU-2017-AVIAN"]')).not.toBeNull();
    expect(maps.querySelector('[data-empirical-probability="1"]')).not.toBeNull();
    expect(maps.querySelector('[data-cross-year="1"]')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });
});

describe('场景 3：文化传媒（历史侧如实 + 草稿可编辑可导出）', () => {
  it('★★ 查「文化传媒」：历史侧展示、当前侧不谎报；草稿可编辑、导出不假报', async () => {
    const { root, doc } = await mountApp();
    const result = await queryDirection(doc, '文化传媒');
    const t = result.textContent ?? '';

    const cur = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('当前研究对象'),
    );
    const hist = [...result.querySelectorAll('div.dl-block')].find(
      (b) => b.querySelector('h4')?.textContent?.includes('历史案例'),
    );
    // ★ 当前侧没有研究对象时，**不得**渲染「当前研究对象」块、不得说「两侧都有」
    if (!cur) {
      expect(t).not.toContain('两侧都有');
      expect(t).toContain('只有历史案例');
    }
    expect(hist, '文化传媒应有历史案例').toBeTruthy();

    // 从历史案例进入完整对象详情
    const firstCase = hist!.querySelector('button.dl-id.dl-link') as HTMLButtonElement;
    const caseId = firstCase.textContent ?? '';
    await click(firstCase);
    const panel = detailPanel(doc)!;
    expect(detailId(doc)).toBe(caseId);
    await click(closeBtn(panel));

    // 研究请求草稿：可编辑（改研究方向 → 输入值真的变）
    const dirInput = doc.querySelector('input[aria-label="研究方向"]') as HTMLInputElement;
    expect(dirInput).not.toBeNull();
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    await act(async () => {
      setter.call(dirInput, '文化传媒的待研究问题');
      dirInput.dispatchEvent(new window.Event('input', { bubbles: true }));
    });
    expect(dirInput.value).toBe('文化传媒的待研究问题');

    // 导出：jsdom 无 clipboard → 必须明确告知失败，**绝不**假报「已复制」
    const dl = doc.querySelector('section.dl') as HTMLElement;
    await click(btnIn(dl, '复制 JSON'));
    expect(dl.textContent).toContain('复制失败');
    expect(dl.textContent).toContain('手动选中复制');
    expect(dl.textContent).not.toContain('已复制');

    await act(async () => { root.unmount(); });
  });
});

describe('场景 4：外部线索 → 对象详情 / 研究请求（v0.13 路径回归 + v0.14 详情跳转）', () => {
  it('★★ EXT-12：对照 → 查看对象详情 → 关闭后**保留对照上下文**', async () => {
    const { root, doc } = await mountApp();

    const row = doc.querySelector('tr[data-est-row="EXT-12"]')!;
    await click(btnIn(row, '对照历史窗口'));
    const panel = doc.querySelector('[data-ecp-status="matched"]') as HTMLElement;
    expect(panel).not.toBeNull();

    // 计数语义（v0.14）：段数 ≠ 对象数
    expect(panel.querySelector('[data-ecp-counts="1"]')?.textContent)
      .toContain('段数不是对象数');

    // 点第一条历史对象的「查看对象详情」
    const firstLi = panel.querySelector('li[data-ecp-hist]') as HTMLElement;
    const objectId = firstLi.dataset.ecpHist!;
    await click(btnIn(firstLi, '查看对象详情'));

    const detail = detailPanel(doc)!;
    expect(detailId(doc)).toBe(objectId);

    // ★ 关闭详情 → 回到时间轴，**对照面板仍然展开**（线索与对照上下文不丢）
    await click(closeBtn(detail));
    expect(detailPanel(doc)).toBeNull();
    expect(doc.querySelector('tr[data-est-row="EXT-12"]')).not.toBeNull();
    expect(doc.querySelector('[data-ecp-status="matched"]')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ EXT-17（未映射）：带入研究请求 → 草稿含原文与来源（空草稿直接带入）', async () => {
    const { root, doc } = await mountApp();
    window.localStorage.clear();

    const row = doc.querySelector('tr[data-est-row="EXT-17"]')!;
    await click(btnIn(row, '带入研究请求'));

    const dirInput = doc.querySelector('input[aria-label="研究方向"]') as HTMLInputElement;
    expect(dirInput.value).toContain('防汛');
    const dl = doc.querySelector('section.dl') as HTMLElement;
    const t = dl.textContent ?? '';
    expect(t).toContain('6–7 月');            // 原始窗口文本（月份精度）
    expect(t).toContain('外部参考');           // 来源不被伪装成已验证证据

    await act(async () => { root.unmount(); });
  });
});
