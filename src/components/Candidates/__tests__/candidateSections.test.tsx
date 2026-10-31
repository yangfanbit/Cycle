// @vitest-environment jsdom
/**
 * ★★ v0.65 回归：发现链路的信息组织。
 *
 * 真实使用问题（不是文案偏好）：
 * ① `candidate_digest_v0_11` 把 213 张卡片（季节窗口 204 / 专项假设 3 / 当前主题 6）混排后
 *    取前 6 条精选 → 季节窗口占满时，**6 个当前研究主题里有 4 个被挤出主入口**。
 * ② 缺股三种情况（行业板块无历史成分 / 当前主题未建映射 / 专项假设未接入）都显示成
 *    「没有可核实的成分」，读者无法区分「数据边界」与「研究待办」。
 * ③ 「历史重复模式」只有两个预设假设，标题却像通用挖掘器。
 *
 * 断言全部按**产物真实数据**推导（不写死卡片数量以外的结论）。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { CurrentCandidatesSection } from '../CurrentCandidatesSection';
import raw from '@current/candidate_digest_v0_12.json';

interface D {
  cards: { id: string; kind: string; title: string; stock_gap_reason?: string | null }[];
  sections?: { current_objects?: { ids: string[] }; seasonal_preview?: { ids: string[] };
    special_hypotheses?: { ids: string[] } };
}
const doc = raw as unknown as D;

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

async function mount(): Promise<{ root: Root; doc: Document }> {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => { root.render(<CurrentCandidatesSection />); });
  return { root, doc: document };
}
const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };
const rowsOf = (d: Document, key: string) =>
  [...d.querySelectorAll(`[data-rows="${key}"] li[data-candidate]`)] as HTMLElement[];
const rowById = (d: Document, id: string) =>
  d.querySelector(`li[data-candidate="${id}"] button`) as HTMLButtonElement | null;

describe('v0.65 发现链路：当前研究主题独立成段', () => {
  it('★★ 6 个当前研究主题**全部**出现在主入口（不被季节窗口挤出）', async () => {
    const { root, doc: d } = await mount();
    const want = doc.sections?.current_objects?.ids ?? [];
    expect(want.length, '当前研究主题应有 6 个').toBe(6);

    const rows = rowsOf(d, 'current_objects');
    expect(rows.length, '主入口必须展示全部当前主题').toBe(want.length);
    const shown = rows.map((r) => r.getAttribute('data-candidate'));
    for (const id of want) expect(shown, `${id} 必须在主入口可见`).toContain(id);

    // 三段标题都在，且季节窗口单独成段
    expect(d.querySelector('[data-cand-section="current_objects"]')).not.toBeNull();
    expect(d.querySelector('[data-cand-section="seasonal_preview"]')).not.toBeNull();
    expect(d.querySelector('[data-cand-section="special_hypotheses"]')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 季节窗口只作预览，并就地给出全量规模（不让人以为只有 6 条）', async () => {
    const { root, doc: d } = await mount();
    const preview = rowsOf(d, 'seasonal_preview');
    const previewIds = doc.sections?.seasonal_preview?.ids ?? [];
    expect(preview.length).toBe(previewIds.length);

    const note = d.querySelector('[data-cand-section="seasonal_preview"]')!.parentElement!.textContent ?? '';
    expect(note).toContain('预览');
    expect(note).toContain('不等于');

    // 规模数字必须来自产物 seasonal_scale，且四类数字同时出现
    const scale = d.querySelector('[data-seasonal-scale]')!.textContent ?? '';
    expect(scale).toContain('1300');       // 全量模式
    expect(scale).toContain('204');        // 当前/下月窗口
    expect(scale).toContain('736');        // 样本外可报告
    expect(scale).toContain('967');        // 仅时点资格

    await act(async () => { root.unmount(); });
  });

  it('★★ 专项假设段明确标注「人工预设、不是通用挖掘器」', async () => {
    const { root, doc: d } = await mount();
    const h3 = d.querySelector('[data-cand-section="special_hypotheses"]')!;
    const note = h3.parentElement!.textContent ?? '';
    expect(note).toContain('人工预设');
    expect(note).toContain('不是通用主题挖掘器');
    expect(note).toContain('不得混算');
    // 三个预设假设都在
    expect(rowsOf(d, 'special_hypotheses').length).toBe(doc.sections?.special_hypotheses?.ids.length);
    await act(async () => { root.unmount(); });
  });
});

describe('v0.65 发现链路：缺股原因三分 + 当前相关标的', () => {
  it('★★ 行业板块窗口：说明「没有历史成分数据」，不是笼统「没有成分」', async () => {
    const { root, doc: d } = await mount();
    const row = rowsOf(d, 'seasonal_preview')
      .find((r) => (r.textContent ?? '').includes('不绑个股'));
    expect(row, '预览里应至少有一个「行业板块无历史成分」的窗口').toBeTruthy();
    await click(row!.querySelector('button') as HTMLButtonElement);
    const panel = d.querySelector('[data-stock-gap="NO_HISTORICAL_CONSTITUENTS"]');
    expect(panel, '详情应标注缺股原因 = 无历史成分').not.toBeNull();
    expect(panel!.textContent).toContain('没有已接入的历史成分数据');
    await act(async () => { root.unmount(); });
  });

  it('★★ 当前主题已有可核验映射：显示「当前相关标的」+ 代码 + 原文出处，不叫历史代表股', async () => {
    const { root, doc: d } = await mount();
    const btn = rowById(d, 'CC-2026-OPTICAL-LINK');
    expect(btn).toBeTruthy();
    await click(btn!);
    const sec = d.querySelector('[data-related-securities="MAPPED"]');
    expect(sec, '光互联主题应有映射').not.toBeNull();
    const t = sec!.textContent ?? '';
    expect(t).toContain('当前相关标的');
    expect(t).toContain('300502');            // 新易盛
    expect(t).toContain('300308');            // 中际旭创
    expect(t).toContain('原文：');            // 附出处片段
    expect(t).toContain('不是');
    expect(t).toContain('历史代表股');
    await act(async () => { root.unmount(); });
  });

  it('★★ 当前主题尚未建映射：显示「尚未建立映射」并说明下一步（不推断、不编造）', async () => {
    const { root, doc: d } = await mount();
    const btn = rowById(d, 'CC-2026-BCI-MEDTECH');
    expect(btn).toBeTruthy();
    await click(btn!);
    const sec = d.querySelector('[data-related-securities="NOT_MAPPED"]');
    expect(sec).not.toBeNull();
    const t = sec!.textContent ?? '';
    expect(t).toContain('尚未建立映射');
    expect(t).toContain('下一步');
    await act(async () => { root.unmount(); });
  });

  it('★ 当前主题详情不出现 5/10/20 交易日结算措辞（不套用不适用规则）', async () => {
    const { root, doc: d } = await mount();
    await click(rowById(d, 'CC-2026-COMPUTE-POWER')!);
    const panel = d.querySelector('[data-candidate-detail]')!.textContent ?? '';
    expect(panel).not.toMatch(/5\s*日.*(结算|收益)/);
    expect(panel).not.toMatch(/20\s*个交易日.*结算/);
    await act(async () => { root.unmount(); });
  });
});
