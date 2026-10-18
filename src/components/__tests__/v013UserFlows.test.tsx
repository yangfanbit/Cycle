// @vitest-environment jsdom
/**
 * ★★ v0.13 三个真实用户场景 —— **页面级** jsdom 交互（不是静态字符串断言）。
 *
 * 本文件挂载**真实的 `<App />`**（首页全部区块、真实 state、真实事件处理），
 * 按用户路径逐点点下去：
 *
 * 场景 1：EXT-12 流感 / 医药 → 对照历史窗口 → 历史主题地图跳转
 * 场景 2：EXT-14 迎峰度夏电力 → 对照历史窗口（含原始年份/起止/来源区别）
 * 场景 3：EXT-17 防汛 / 水利（未映射）→ 带入研究请求草稿（不覆盖已有草稿）
 * 附加：EXT-23 无固定窗口但有映射 → 历史主题窗口可看、外部层不虚构
 *
 * ★ 环境限制（如实说明）：本机没有 Chrome/Chromium，`playwright-core` 也因沙箱
 *   拦截 node_modules rename 而装不上 → 无法做 Chromium 级截图验证。
 *   这里用真实 DOM 点击替代：所有断言都基于**点击后**的真实状态，
 *   不是静态 HTML 扫描。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import App from '../../App';

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
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

/** 在某一行里找按钮（按文案） */
const btnIn = (scope: ParentNode, label: string) => {
  const b = [...scope.querySelectorAll('button')].find((x) => (x.textContent ?? '').includes(label));
  if (!b) throw new Error(`找不到按钮「${label}」`);
  return b as HTMLButtonElement;
};
const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };

describe('场景 1：流感 / 医药（EXT-12）', () => {
  it('★★ 外部 9–1 月 vs 历史 MAIN_RISE 2–3 月：差异被如实呈现', async () => {
    const { root, doc } = await mountApp();

    // 时间轴上 EXT-12 行存在
    const row = doc.querySelector('tr[data-est-row="EXT-12"]');
    expect(row).not.toBeNull();
    expect(row?.textContent).toContain('流感 / 医药');
    expect(row?.textContent).toContain('9 月至次年 1 月');

    // 点「对照历史窗口」
    await click(btnIn(row!, '对照历史窗口'));

    const panel = doc.querySelector('[data-ecp-status="matched"]');
    expect(panel).not.toBeNull();
    const t = panel?.textContent ?? '';
    // 两层 + 来源标签
    expect(t).toContain('外部资料声称的月份窗口');
    expect(t).toContain('外部参考');
    expect(t).toContain('MAIN_RISE');
    // ★★ 关键：流感疫苗对象的历史 MAIN_RISE 在 2–3 月，**与外部 9–1 月不同**
    expect(panel!.querySelector('[data-ecp-hist="C-2023-PHARMA-FLU"]')).not.toBeNull();
    expect(t).toContain('2023-02-20 → 2023-03-20');
    expect(t).toContain('Campaign');
    // 语义边界
    expect(t).toContain('宏观主题映射 ≠ 事件机制相同');
    expect(t).toContain('不是统计验证');

    await act(async () => { root.unmount(); });
  });

  it('★★ 从 EXT-12 跳到流感历史题材地图，并能看到历史事件', async () => {
    const { root, doc } = await mountApp();
    const row = doc.querySelector('tr[data-est-row="EXT-12"]')!;
    await click(btnIn(row, '历史题材地图'));

    // 首页「历史题材地图」区被选中为 FLU 题材
    const maps = doc.querySelector('#historical-theme-maps')!;
    expect(maps).not.toBeNull();
    expect(maps.querySelector('button[data-theme-id="FLU"]')?.getAttribute('aria-selected')).toBe('true');
    // 流感历史事件在页面上（事件卡 + 跨年份段）
    expect(maps.querySelector('[data-event-id="FLU-2017-AVIAN"]')).not.toBeNull();
    expect(maps.textContent).toContain('2017 年禽流感概念行情');
    expect(maps.textContent).toContain('历史参与标的');   // v0.11 的标的索引
    expect(maps.querySelector('[data-empirical-probability]')).not.toBeNull();  // v0.9 经验概率

    await act(async () => { root.unmount(); });
  });
});

describe('场景 2：迎峰度夏电力（EXT-14）', () => {
  it('★★ 历史侧显示真实年份 / 原始起止 / 类型，且与外部来源区分', async () => {
    const { root, doc } = await mountApp();
    const row = doc.querySelector('tr[data-est-row="EXT-14"]')!;
    expect(row?.textContent).toContain('5–7 月');

    await click(btnIn(row, '对照历史窗口'));
    const panel = doc.querySelector('[data-ecp-status="matched"]')!;
    const t = panel.textContent ?? '';
    expect(t).toContain('电力（运营端）');
    expect(t).toContain('C-2023-POWEROP-THERMAL');
    expect(t).toContain('2023-01-03 → 2023-05-29');
    expect(t).toContain('C-2021-POWER-GREEN');
    expect(t).toContain('2021-09-07 → 2021-09-28');
    // 两层来源标签都在（外部参考 / Research 历史）
    expect(t).toContain('外部参考');
    expect(t).toContain('Research');
    // 外部层原文
    expect(t).toContain('5–7 月');

    // 再进入电力历史事件地图
    await click(btnIn(row, '历史题材地图'));
    const maps = doc.querySelector('#historical-theme-maps')!;
    expect(maps.querySelector('button[data-theme-id="POWER_SUMMER"]')?.getAttribute('aria-selected')).toBe('true');
    expect(maps.querySelector('[data-event-id="POWER-2022-SUMMER"]')).not.toBeNull();
    expect(maps.textContent).toContain('2022 年迎峰度夏 + 煤价见顶预期行情');

    await act(async () => { root.unmount(); });
  });
});

describe('场景 3：防汛 / 水利（EXT-17 · 未映射）', () => {
  it('★★ 未映射不给历史关联；带入研究请求后草稿可用且保留原文', async () => {
    const { root, doc } = await mountApp();
    const row = doc.querySelector('tr[data-est-row="EXT-17"]')!;
    // 未映射行没有「对照历史窗口」
    expect(row.textContent).toContain('未映射');
    expect([...row.querySelectorAll('button')].some(
      (b) => (b.textContent ?? '').includes('对照历史窗口'),
    )).toBe(false);

    // 点「带入研究请求」
    await click(btnIn(row, '带入研究请求'));

    // 方向查询区出现草稿，且内容来自该线索
    const lookup = doc.querySelector('#direction-lookup')!;
    const dir = lookup.querySelector('input[aria-label="研究方向"]') as HTMLInputElement;
    expect(dir.value).toBe('防汛 / 水利');
    const known = lookup.querySelector('textarea[aria-label="已知线索"]') as HTMLTextAreaElement;
    expect(known.value).toContain('6–7 月');
    expect(known.value).toContain('A股季节性题材日历（2026版）');
    expect(known.value).toContain('未经 ThreeC 验证');
    expect(known.value).not.toMatch(/\d{4}-\d{2}-\d{2}/);
    // 空草稿 → 不应出现替换确认横幅
    expect(lookup.querySelector('[data-seed-entry]')).toBeNull();

    await act(async () => { root.unmount(); });
  });

  it('★★ 已有草稿时：带入**不静默覆盖**，需用户确认', async () => {
    // 预置一份用户草稿，再触发带入
    const key = 'threec.researchRequestDraft.v1';
    localStorage.setItem(key, JSON.stringify({
      __v: 3,
      direction: '我自己的方向',
      researchQuestions: '我的研究问题',
      whyCare: '',
      knownLeads: '',
      timeRange: '',
      linkedQuery: '',
      linkedAt: '',
      linkedCoverage: null,
    }));
    const { root, doc } = await mountApp();

    const lookup = doc.querySelector('#direction-lookup')!;
    expect((lookup.querySelector('input[aria-label="研究方向"]') as HTMLInputElement).value)
      .toBe('我自己的方向');

    await click(btnIn(doc.querySelector('tr[data-est-row="EXT-17"]')!, '带入研究请求'));

    // 出现确认横幅，且**原草稿未被覆盖**
    const banner = lookup.querySelector('[data-seed-entry="EXT-17"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('非空草稿');
    expect((lookup.querySelector('input[aria-label="研究方向"]') as HTMLInputElement).value)
      .toBe('我自己的方向');

    // 点「保留现有草稿」→ 仍是用户内容
    await click(btnIn(banner!, '保留现有草稿'));
    expect((lookup.querySelector('input[aria-label="研究方向"]') as HTMLInputElement).value)
      .toBe('我自己的方向');
    expect(lookup.querySelector('[data-seed-entry]')).toBeNull();

    // 再点一次「带入研究请求」→ 确认横幅回来；点「替换现有草稿」→ 写入线索内容
    await click(btnIn(doc.querySelector('tr[data-est-row="EXT-17"]')!, '带入研究请求'));
    await click(btnIn(lookup.querySelector('[data-seed-entry="EXT-17"]')!, '替换现有草稿'));
    expect((lookup.querySelector('input[aria-label="研究方向"]') as HTMLInputElement).value)
      .toBe('防汛 / 水利');

    await act(async () => { root.unmount(); });
  });
});

describe('场景 4：EXT-23 无固定窗口但有映射', () => {
  it('★★ 历史主题窗口可看，外部层明示无窗口、不虚构月份条', async () => {
    const { root, doc } = await mountApp();
    const item = doc.querySelector('[data-est-nowin-id="EXT-23"]')!;
    expect(item.textContent).toContain('无固定');
    await click(btnIn(item, '对照历史窗口'));

    const panel = doc.querySelector('[data-ecp-status="matched"]')!;
    expect(panel.textContent).toContain('无固定月份窗口');
    expect(panel.textContent).toContain('不绘制外部月份条');
    expect(panel.querySelector('[data-ecp-hist]')).not.toBeNull();
    await act(async () => { root.unmount(); });
  });
});
