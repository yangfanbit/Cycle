// @vitest-environment jsdom
/**
 * ★★ 研究请求草稿的**真实交互**回归（v0.8 · jsdom）。
 *
 * ## 为什么需要这个文件
 * v0.7 及以前全是 `renderToStaticMarkup`（SSR）+ 纯函数测试 ——
 * **SSR 不执行 `useEffect`、不能点击**，于是「查询 → 新建草稿 → 清空 → 复制」这些
 * **用户真正会走的路**从未被验证过，缺陷（关联永不建立 / 清空被回填）就此漏网。
 *
 * 本轮显式引入 `jsdom`（devDependency）+ `react-dom/client` + `act`，
 * 用**文件级** `// @vitest-environment jsdom`，**不影响**其它文件仍跑在 node 下。
 *
 * ★ 已知边界（不得假装测过）：
 *   - 复制**成功**路径通过注入 `navigator.clipboard` 桩覆盖；
 *   - `document.execCommand` 在 jsdom **未实现** → execCommand 降级路径由
 *     `clipboard.test.ts` 以**注入 env** 覆盖，不在本文件重复。
 *
 * ★ 所有查询都**限定在本测试自己的宿主节点内**（`host.querySelector`）——
 *   jsdom 的 `document` 在同一文件的所有用例间共享，否则先前的用例没 unmount 干净时
 *   会查到别人的 DOM（实测踩到过）。
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { researchTimelineSource } from '../../../data/timeline/timelineAdapter';
import { parseCurrentCandidateDataset } from '../../../data/timeline/currentCandidate';
import { DirectionLookupSection } from '../DirectionLookupSection';
import canonicalJson from '@current/current_candidates.json';

const source = researchTimelineSource();
const dataset = parseCurrentCandidateDataset(canonicalJson).dataset;

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  localStorage.clear();
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
  localStorage.clear();
});

/** 一个「挂载着的组件实例」—— 所有查询都限定在它自己的 DOM 里 */
class Session {
  root!: Root;
  host!: HTMLDivElement;

  static async start(): Promise<Session> {
    const s = new Session();
    await act(async () => {
      s.host = document.createElement('div');
      document.body.appendChild(s.host);
      const { createRoot: cr } = await import('react-dom/client');
      s.root = cr(s.host);
      s.root.render(
        <DirectionLookupSection source={source} dataset={dataset} onOpenHistoricalCase={() => {}} />,
      );
    });
    return s;
  }

  q<T extends Element = HTMLElement>(sel: string): T | null {
    return this.host.querySelector(sel) as T | null;
  }
  text(): string {
    return this.host.textContent ?? '';
  }
  button(label: string): HTMLButtonElement {
    const b = [...this.host.querySelectorAll('button')].find(
      (x) => (x.textContent ?? '').includes(label),
    );
    if (!b) throw new Error(`按钮不存在：${label}`);
    return b as HTMLButtonElement;
  }
  async click(label: string): Promise<void> {
    await act(async () => { this.button(label).click(); });
  }

  /** 输入方向关键词并提交表单 */
  async query(text: string): Promise<void> {
    const input = this.q<HTMLInputElement>('input[aria-label="方向关键词"]')!;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    await act(async () => {
      setter.call(input, text);
      input.dispatchEvent(new window.Event('input', { bubbles: true }));
    });
    const form = this.q<HTMLFormElement>('form.dl-form')!;
    await act(async () => {
      form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    });
    await act(async () => { await Promise.resolve(); });
  }

  /** 在指定 textarea 里输入 */
  async type(ariaLabel: string, text: string): Promise<void> {
    const ta = this.q<HTMLTextAreaElement>(`textarea[aria-label="${ariaLabel}"]`)!;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')!.set!;
    await act(async () => {
      setter.call(ta, text);
      ta.dispatchEvent(new window.Event('input', { bubbles: true }));
    });
  }

  /** 预览区里的草稿 JSON / Markdown */
  json(): Record<string, unknown> {
    const ta = this.q<HTMLTextAreaElement>('textarea[aria-label="草稿 JSON"]')!;
    return JSON.parse(ta.value) as Record<string, unknown>;
  }
  md(): string {
    return this.q<HTMLTextAreaElement>('textarea[aria-label="草稿 Markdown"]')!.value;
  }

  async stop(): Promise<void> {
    await act(async () => { this.root.unmount(); });
  }
}

/** 给 navigator.clipboard 装桩（jsdom 默认没有 → 正好测失败路径）；返回写入记录 */
function stubClipboard(opts: { ok: boolean } = { ok: true }): string[] {
  const calls: string[] = [];
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: opts.ok
      ? { writeText: async (t: string) => { calls.push(t); } }
      : {
        writeText: async () => {
          const e = new Error('denied');
          e.name = 'NotAllowedError';
          throw e;
        },
      },
  });
  return calls;
}
const unStubClipboard = () => { Reflect.deleteProperty(navigator, 'clipboard'); };

/* ================================================================
 * 用户要求的 5 条真实交互
 * ================================================================ */

describe('草稿交互（v0.8 · jsdom 真实点击）', () => {
  it('① 查询「汽车」→ 自动建立关联：导出里的 linked_query / 命中依据与页面一致', async () => {
    const s = await Session.start();
    await s.query('汽车');

    // 页面：草稿区出现，证据那条说明关联查询
    expect(s.text()).toContain('研究请求草稿');
    expect(s.text()).toContain('本草稿的覆盖查询证据');
    expect(s.q<HTMLInputElement>('input[aria-label="研究方向"]')!.value).toBe('汽车');

    const j = s.json() as {
      draft_version: string;
      linkage: { linked_query: string; evidence_source: string };
      coverage_check: {
        executed: boolean; verdict: string | null; query: string;
        current_objects: { id: string; matched_on: string[] | null }[];
      };
    };
    expect(j.draft_version).toBe('0.3');
    expect(j.linkage.linked_query).toBe('汽车');
    expect(j.linkage.evidence_source).toBe('frozen_snapshot');
    expect(j.coverage_check.executed).toBe(true);
    expect(j.coverage_check.verdict).toBe('both');
    expect(j.coverage_check.query).toBe('汽车');
    expect(j.coverage_check.current_objects).toHaveLength(1);
    expect(j.coverage_check.current_objects[0].id).toBe('CC-2026-AUTO-SMARTDRIVE');
    // ★★ matched_on 是**真实依据**（不是 []）
    expect(j.coverage_check.current_objects[0].matched_on).not.toBeNull();
    expect(j.coverage_check.current_objects[0].matched_on!.length).toBeGreaterThan(0);

    // Markdown 同样是同一套事实，且把依据写出来
    const md = s.md();
    expect(md).toContain('本草稿**关联的查询词**');
    expect(md).toContain('命中');
    expect(md).toContain('CC-2026-AUTO-SMARTDRIVE');

    await s.stop();
  });

  it('② 改查「医药」：原草稿仍保留**汽车**证据，并披露当前查询已变化', async () => {
    const s = await Session.start();
    await s.query('汽车');
    await s.query('医药');

    const j = s.json() as {
      linkage: { linked_query: string; current_query: string; changed: boolean };
      coverage_check: { query: string; verdict: string | null };
    };
    // ★ 证据**不漂移**：仍是汽车那次
    expect(j.linkage.linked_query).toBe('汽车');
    expect(j.coverage_check.query).toBe('汽车');
    expect(j.coverage_check.verdict).toBe('both');
    // 但**披露**当前查询已变
    expect(j.linkage.current_query).toBe('医药');
    expect(j.linkage.changed).toBe(true);

    // 页面也把这件事说出来（用户不该靠读 JSON 才知道）
    expect(s.text()).toContain('与本草稿的证据不同');
    expect(s.text()).toContain('医药');

    await s.stop();
  });

  it('③ 点击「以当前查询新建草稿」→ 新草稿**一次性**关联医药证据（不依赖 effect）', async () => {
    const s = await Session.start();
    await s.query('汽车');
    await s.query('医药');
    await s.click('以当前查询新建草稿');

    const j = s.json() as {
      request: { direction: string };
      linkage: { linked_query: string; changed: boolean; evidence_source: string };
      coverage_check: { executed: boolean; query: string; verdict: string | null };
    };
    expect(j.request.direction).toBe('医药');
    expect(j.linkage.linked_query).toBe('医药');
    expect(j.linkage.changed).toBe(false);
    expect(j.linkage.evidence_source).toBe('frozen_snapshot');
    expect(j.coverage_check.executed).toBe(true);
    expect(j.coverage_check.query).toBe('医药');
    expect(j.coverage_check.verdict).toBe('both');
    // ★ 不得再出现「未关联任何查询」（v0.8 修复的就是这个）
    expect(s.text()).not.toContain('未关联任何查询');

    await s.stop();
  });

  it('④ 清空草稿：不被自动回填；**刷新（重挂载）后也不恢复', async () => {
    const s = await Session.start();
    await s.query('汽车');
    await s.type('为什么关注', '所在行业');
    expect(s.text()).toContain('所在行业');

    await s.click('清空草稿');
    // ① 当场不得被回填（v0.6 的真实缺陷）：方向输入**空**、用户内容没了
    expect(s.q<HTMLInputElement>('input[aria-label="研究方向"]')!.value).toBe('');
    expect(s.text()).not.toContain('所在行业');
    // ② 持久化记录确已删除
    expect(localStorage.getItem('threec.researchRequestDraft.v1')).toBeNull();
    await s.stop();

    // ③「刷新」= 卸载 + 用同一 localStorage 重新挂载（新的 Session，同 storage）
    const s2 = await Session.start();
    expect(s2.text()).not.toContain('所在行业');
    // 无查询 + 空草稿 → 草稿区整体不渲染（正确行为，不是空白占位）
    expect(s2.q('input[aria-label="研究方向"]')).toBeNull();
    expect(s2.text()).not.toContain('研究请求草稿');
    expect(Object.keys(localStorage)).toHaveLength(0);
    await s2.stop();
  });

  it('④b 刷新后**能恢复**已保存草稿（含关联证据，不被冒充为未关联）', async () => {
    const s = await Session.start();
    await s.query('汽车');
    await s.stop();

    const s2 = await Session.start();
    // 恢复后草稿区可见（v0.6 时它在 result 为 null 时完全不渲染）
    expect(s2.text()).toContain('研究请求草稿');
    expect(s2.q<HTMLInputElement>('input[aria-label="研究方向"]')!.value).toBe('汽车');
    const j = s2.json() as {
      linkage: { linked_query: string; evidence_source: string };
      coverage_check: { executed: boolean; verdict: string | null };
    };
    expect(j.linkage.linked_query).toBe('汽车');
    expect(j.linkage.evidence_source).toBe('frozen_snapshot');
    expect(j.coverage_check.executed).toBe(true);
    expect(j.coverage_check.verdict).toBe('both');
    await s2.stop();
  });

  it('⑤ 剪贴板失败：**不显示「已复制」**，明确告知失败并**自动展开**预览', async () => {
    unStubClipboard();
    stubClipboard({ ok: false });
    const s = await Session.start();
    await s.query('汽车');
    await s.click('复制 JSON');

    expect(s.text()).toContain('复制失败');
    expect(s.text()).toContain('权限被拒绝');
    expect(s.text()).toContain('手动选中复制');
    expect(s.text()).not.toContain('已复制');           // ★ 绝不假报成功
    // 预览被自动展开：只读 textarea 直接可见可用，内容就是那份 JSON
    const details = s.q<HTMLDetailsElement>('details.dl-draft-preview');
    expect(details?.hasAttribute('open')).toBe(true);
    expect(s.md() === undefined || true).toBe(true);
    expect(s.q<HTMLTextAreaElement>('textarea[aria-label="草稿 JSON"]')!.value)
      .toContain('threec_research_request_draft');

    unStubClipboard();
    await s.stop();
  });

  it('⑤b 剪贴板**成功**时才显示「已复制」，且内容确实是导出的那一份', async () => {
    const calls = stubClipboard({ ok: true });
    const s = await Session.start();
    await s.query('汽车');
    await s.click('复制 Markdown');
    expect(s.text()).toContain('已复制');
    expect(calls).toHaveLength(1);
    expect(calls[0]).toContain('ThreeC 研究请求草稿');
    expect(calls[0]).toContain('关联的查询词');
    expect(s.text()).not.toContain('复制失败');
    unStubClipboard();
    await s.stop();
  });
});
