// @vitest-environment jsdom
/**
 * ★★ 外部线索带入研究请求草稿（v0.13）—— jsdom 真点。
 *
 * 验证三件事：
 * ① 空草稿 → 种子直接带入（字段、月份精度、来源标记都正确）；
 * ② 非空草稿 → **先问用户**，绝不静默覆盖；
 * ③ 「保留现有草稿」真的保留；「替换现有草稿」才生效。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';

import { researchTimelineSource } from '../../../data/timeline/timelineAdapter';
import { parseCurrentCandidateDataset } from '../../../data/timeline/currentCandidate';
import { externalCalendarDoc, externalCalendarEntries } from '../../../data/timeline/externalSeasonalCalendar';
import { makeDraftSeed, type DraftSeed } from '../../../data/timeline/externalLeadDraft';
import {
  DRAFT_STORAGE_KEY,
  serializeDraft,
} from '../../../data/timeline/researchRequestDraftStorage';
import type { ResearchRequestDraft } from '../../../data/timeline/researchRequestDraft';
import { DirectionLookupSection } from '../DirectionLookupSection';
import canonicalJson from '@current/current_candidates.json';

const source = researchTimelineSource();
const dataset = parseCurrentCandidateDataset(canonicalJson).dataset;
const all = externalCalendarEntries();
const entry17 = all.find((e) => e.id === 'EXT-17')!;

const inMemoryStorage = () => {
  const m = new Map<string, string>();
  return {
    getItem: (k: string) => (m.has(k) ? m.get(k)! : null),
    setItem: (k: string, v: string) => { m.set(k, v); },
    removeItem: (k: string) => { m.delete(k); },
  };
};

const seed = (token: number): DraftSeed =>
  makeDraftSeed(entry17, externalCalendarDoc().source_reports, token);

/** 预置一份「用户自己写的」非空草稿（直接写入内存存储） */
const storageWithMyDraft = () => {
  const mine: ResearchRequestDraft = {
    direction: '我自己的方向',
    researchQuestions: '我的研究问题',
    whyCare: '我在关注',
    knownLeads: '',
    timeRange: '',
    linkedQuery: '',
    linkedAt: '',
    linkedCoverage: null,
  };
  const base = inMemoryStorage();
  base.setItem(DRAFT_STORAGE_KEY, serializeDraft(mine)!);
  return base;
};

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

async function mount(opts: { storage?: ReturnType<typeof inMemoryStorage>; seed?: DraftSeed | null } = {}) {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root: Root = createRoot(host);
  await act(async () => {
    root.render(
      <DirectionLookupSection
        source={source}
        dataset={dataset}
        draftStorage={opts.storage}
        seed={opts.seed ?? null}
      />,
    );
  });
  return { root, host };
}

const dirInput = (host: HTMLElement) =>
  host.querySelector('input[aria-label="研究方向"]') as HTMLInputElement;
describe('外部线索带入草稿（jsdom 真点）', () => {
  it('★★ 空草稿 → 直接带入（方向 / 月份 / 来源 / 未关联查询）', async () => {
    const storage = inMemoryStorage();
    const { root, host } = await mount({ storage, seed: seed(1) });

    expect(dirInput(host).value).toBe('防汛 / 水利');
    const known = host.querySelector('textarea[aria-label="已知线索"]') as HTMLTextAreaElement;
    expect(known.value).toContain('6–7 月');
    expect(known.value).toContain('A股季节性题材日历（2026版）');
    expect(known.value).toContain('未经 ThreeC 验证');
    expect(known.value).not.toMatch(/\d{4}-\d{2}-\d{2}/);
    // 页面：不出现替换确认（没有静默发生过替换）
    expect(host.querySelector('[data-seed-entry]')).toBeNull();
    // 草稿区确实被渲染（用户能继续编辑）
    expect(host.textContent).toContain('把');
    await act(async () => { root.unmount(); });
  });

  it('★★ 非空草稿 → **不静默覆盖**，先出确认横幅', async () => {
    // 内存里已有一份用户自己写的草稿
    const storage = storageWithMyDraft();
    const { root, host } = await mount({ storage, seed: null });
    expect(dirInput(host).value).toBe('我自己的方向');

    // 重新挂载同一份存储 + 一个种子（模拟用户在别处点了「带入研究请求」）
    await act(async () => { root.unmount(); });
    const second = await mount({ storage, seed: seed(7) });

    // ★ 确认横幅出现，且**原草稿未被覆盖**
    const banner = second.host.querySelector('[data-seed-entry="EXT-17"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('非空草稿');
    expect(banner?.textContent).toContain('保留现有草稿');
    expect(dirInput(second.host).value).toBe('我自己的方向');

    await act(async () => { second.root.unmount(); });
  });

  it('★★ 「保留现有草稿」不替换；「替换现有草稿」才写入', async () => {
    const storage = storageWithMyDraft();
    const first = await mount({ storage, seed: null });
    expect(dirInput(first.host).value).toBe('我自己的方向');
    await act(async () => { first.root.unmount(); });

    const second = await mount({ storage, seed: seed(3) });
    expect(second.host.querySelector('[data-seed-entry]')).not.toBeNull();

    // 保留 → 仍是用户自己的内容
    await act(async () => {
      [...second.host.querySelectorAll('button')]
        .find((b) => (b.textContent ?? '').includes('保留现有草稿'))!
        .click();
    });
    expect(dirInput(second.host).value).toBe('我自己的方向');
    expect(second.host.querySelector('[data-seed-entry]')).toBeNull();

    // 再触发一次（token 递增）→ 替换
    await act(async () => { second.root.unmount(); });
    const third = await mount({ storage, seed: seed(4) });
    expect(dirInput(third.host).value).toBe('我自己的方向');   // 先确认，不覆盖
    await act(async () => {
      [...third.host.querySelectorAll('button')]
        .find((b) => (b.textContent ?? '').includes('替换现有草稿'))!
        .click();
    });
    expect(dirInput(third.host).value).toBe('防汛 / 水利');
    expect(third.host.querySelector('[data-seed-entry]')).toBeNull();

    await act(async () => { third.root.unmount(); });
  });
});
