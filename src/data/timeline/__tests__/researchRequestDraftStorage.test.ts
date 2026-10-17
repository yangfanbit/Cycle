import { describe, it, expect } from 'vitest';

import {
  DRAFT_STORAGE_MAX_BYTES,
  DRAFT_STORAGE_KEY,
  browserDraftStorage,
  loadDraft,
  normalizeDraft,
  saveDraft,
  serializeDraft,
  shouldAutoFillDirection,
  type DraftStorage,
} from '../researchRequestDraftStorage';
import {
  DRAFT_FIELD_MAX,
  EMPTY_DRAFT,
  isDraftBlank,
  type ResearchRequestDraft,
} from '../researchRequestDraft';

/**
 * 研究请求草稿 · **存储与生命周期**回归（v0.7）。
 *
 * ★★ 为什么需要这个文件：
 *   v0.6 的草稿测试全部是 `renderToStaticMarkup`（SSR）—— 而 **SSR 不执行 `useEffect`**，
 *   于是「保存 / 恢复 / 清空 / 回填」这些**生命周期行为从未被验证**，
 *   却因为测试是绿的而显得已覆盖。
 *   → 本文件把存储与判定抽成**可注入接口 + 纯函数**后直测（无需 jsdom）。
 */

/** 内存存储（可模拟抛错）—— 不进 src，只在测试里 */
function memStorage(seed: Record<string, string> = {}, opts: {
  throwOnGet?: boolean; throwOnSet?: boolean; throwOnRemove?: boolean;
} = {}): DraftStorage & { data: Record<string, string>; sets: number } {
  const data = { ...seed };
  const api = {
    data,
    sets: 0,
    getItem(k: string) {
      if (opts.throwOnGet) throw new Error('SecurityError');
      return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null;
    },
    setItem(k: string, v: string) {
      api.sets += 1;
      if (opts.throwOnSet) {
        const e = new Error('QuotaExceededError');
        e.name = 'QuotaExceededError';
        throw e;
      }
      data[k] = v;
    },
    removeItem(k: string) {
      if (opts.throwOnRemove) throw new Error('remove failed');
      delete data[k];
    },
  };
  return api;
}

const FULL: ResearchRequestDraft = {
  direction: '汽车',
  researchQuestions: 'q1\nq2',
  whyCare: 'why',
  knownLeads: 'lead',
  timeRange: '2018-2025',
  linkedQuery: '汽车',
  linkedAt: '2026-10-16T00:00:00.000Z',
  linkedCoverage: {
    query: '汽车',
    verdict: 'both',
    current: [{ id: 'CC-2026-AUTO-SMARTDRIVE', title: '智能驾驶合规化', matchedOn: ['汽车', '智能驾驶合规化'] }],
    historical: [{ id: 'C-2019-AD', title: '自动驾驶', matchedOn: ['汽车'] }],
    resolution: null,
    captured_at: '2026-10-16T00:00:00.000Z',
  },
};

/* ================================================================
 * 1. ★★ 坏数据矩阵：任何输入都不得让产品崩
 * ================================================================ */

describe('草稿存储 · 坏数据一律安全降级（不得崩）', () => {
  const CRASHERS: [string, unknown][] = [
    ['direction 是数字', { direction: 123 }],
    ['direction 是对象', { direction: { a: 1 } }],
    ['direction 是数组', { direction: [1, 2] }],
    ['direction 是 null', { direction: null }],
    ['direction 是布尔', { direction: true }],
    ['researchQuestions 是数字', { researchQuestions: 42 }],
    ['whyCare 是对象', { whyCare: { x: 1 } }],
    ['knownLeads 是 null', { knownLeads: null }],
    ['timeRange 是数组', { timeRange: ['a'] }],
    ['linkedQuery 是对象', { linkedQuery: {} }],
    ['linkedCoverage 是字符串', { linkedCoverage: 'nope' }],
    ['linkedCoverage.verdict 非法', { linkedCoverage: { query: 'x', verdict: 'MAYBE' } }],
    ['linkedCoverage.current 不是数组', { linkedCoverage: { query: 'x', verdict: 'none', current: 'x' } }],
    ['顶层是数组', [1, 2, 3]],
    ['顶层是数字', 7],
    ['顶层是 null', null],
    ['顶层是字符串', 'hello'],
  ];

  it.each(CRASHERS)('%s → 规范化不抛错且产出安全草稿', (_name, bad) => {
    const { draft } = normalizeDraft(bad);
    // 五个文本字段必须**都是字符串**（下游 .trim() 才不会炸）
    for (const k of ['direction', 'researchQuestions', 'whyCare', 'knownLeads', 'timeRange', 'linkedQuery', 'linkedAt'] as const) {
      expect(typeof draft[k], k).toBe('string');
      expect(() => draft[k].trim(), k).not.toThrow();
    }
    expect(draft.linkedCoverage === null || typeof draft.linkedCoverage === 'object').toBe(true);
  });

  it('★ 不把坏类型强转成看似合法的文本（123 不得变成 "123"）', () => {
    const { draft, issues } = normalizeDraft({ direction: 123, whyCare: { a: 1 } });
    expect(draft.direction).toBe('');
    expect(draft.whyCare).toBe('');
    expect(issues.join('；')).toContain('direction');
    expect(issues.join('；')).toContain('whyCare');
  });

  it('★★ 未知字段被丢弃（不再回流到存储）', () => {
    const { draft, issues } = normalizeDraft({ direction: '汽车', evil: 'x', __v: 99 });
    expect(Object.keys(draft).sort()).toEqual(Object.keys(EMPTY_DRAFT).sort());
    expect(issues.some((s) => s.includes('evil'))).toBe(true);
    // 序列化后不得再出现未知字段
    expect(serializeDraft(draft) ?? '').not.toContain('evil');
  });

  it('★ 超长字段被截断到上限', () => {
    const long = 'x'.repeat(DRAFT_FIELD_MAX + 500);
    const { draft, issues } = normalizeDraft({ direction: long });
    expect(draft.direction.length).toBe(DRAFT_FIELD_MAX);
    expect(issues.some((s) => s.includes('超长'))).toBe(true);
  });
});

/* ================================================================
 * 2. ★★ loadDraft：五种情况必须被区分
 * ================================================================ */

describe('草稿存储 · loadDraft 结果语义', () => {
  it('★ 无存储（SSR / node）→ unavailable（**不崩**，且与「没有草稿」不同）', () => {
    const r = loadDraft(null);
    expect(r.status).toBe('unavailable');
  });

  it('★ 没有记录 → empty', () => {
    expect(loadDraft(memStorage()).status).toBe('empty');
  });

  it('★ 正常记录 → loaded（含关联证据）', () => {
    const s = memStorage({ [DRAFT_STORAGE_KEY]: JSON.stringify(FULL) });
    const r = loadDraft(s);
    expect(r.status).toBe('loaded');
    if (r.status !== 'loaded') throw new Error('unreachable');
    expect(r.draft.direction).toBe('汽车');
    expect(r.draft.linkedQuery).toBe('汽车');
    expect(r.draft.linkedCoverage?.verdict).toBe('both');
    expect(r.issues).toEqual([]);
  });

  it('★★ JSON 语法损坏 → corrupt(json)，不崩、不冒充「没有草稿」', () => {
    const r = loadDraft(memStorage({ [DRAFT_STORAGE_KEY]: '{oops' }));
    expect(r.status).toBe('corrupt');
    if (r.status !== 'corrupt') throw new Error('unreachable');
    expect(r.reason).toBe('json');
  });

  it('★★ 合法 JSON 但顶层是数组/数字 → corrupt(shape)', () => {
    for (const raw of ['[1,2]', '7', '"str"', 'null']) {
      const r = loadDraft(memStorage({ [DRAFT_STORAGE_KEY]: raw }));
      expect(r.status, raw).toBe('corrupt');
      if (r.status === 'corrupt') expect(r.reason).toBe('shape');
    }
  });

  it('★★ 超大内容 → corrupt(oversized)（不把页面拖垮）', () => {
    const raw = '{"direction":"' + 'x'.repeat(DRAFT_STORAGE_MAX_BYTES + 10) + '"}';
    const r = loadDraft(memStorage({ [DRAFT_STORAGE_KEY]: raw }));
    expect(r.status).toBe('corrupt');
    if (r.status === 'corrupt') expect(r.reason).toBe('oversized');
  });

  it('★ 合法 JSON 但字段类型错 → loaded（已规范化）+ issues 披露', () => {
    const r = loadDraft(memStorage({
      [DRAFT_STORAGE_KEY]: JSON.stringify({ direction: 123, researchQuestions: 'ok' }),
    }));
    expect(r.status).toBe('loaded');
    if (r.status !== 'loaded') throw new Error('unreachable');
    expect(r.draft.direction).toBe('');
    expect(r.draft.researchQuestions).toBe('ok');
    expect(r.issues.length).toBeGreaterThan(0);
  });

  it('★ 读取抛错（隐私模式 / 被禁）→ unavailable（不崩）', () => {
    const r = loadDraft(memStorage({}, { throwOnGet: true }));
    expect(r.status).toBe('unavailable');
  });

  it('★ 规范化后全空的记录 → empty（不把一堆空字段当用户内容）', () => {
    const r = loadDraft(memStorage({ [DRAFT_STORAGE_KEY]: JSON.stringify({ direction: '', evil: 1 }) }));
    expect(r.status).toBe('empty');
  });
});

/* ================================================================
 * 3. ★★ saveDraft：失败必须**可感知**（不假装成功）
 * ================================================================ */

describe('草稿存储 · saveDraft 诚实性', () => {
  it('★ 正常写入 → ok(written)，且内容可被读回', () => {
    const s = memStorage();
    expect(saveDraft(s, FULL)).toEqual({ ok: true, action: 'written' });
    const back = loadDraft(s);
    expect(back.status).toBe('loaded');
  });

  it('★ 空草稿 → ok(removed)，记录被删除（不留垃圾）', () => {
    const s = memStorage({ [DRAFT_STORAGE_KEY]: JSON.stringify(FULL) });
    expect(saveDraft(s, { ...EMPTY_DRAFT })).toEqual({ ok: true, action: 'removed' });
    expect(s.data[DRAFT_STORAGE_KEY]).toBeUndefined();
  });

  it('★★ 配额超限 → ok:false（**不得**假装成功），但内容仍在内存可用', () => {
    const s = memStorage({}, { throwOnSet: true });
    const r = saveDraft(s, FULL);
    expect(r.ok).toBe(false);
    if (r.ok) throw new Error('unreachable');
    expect(r.reason).toBe('write_failed');
    expect(r.detail).toContain('Quota');
    // ★ 内存里的草稿对象本身没被破坏
    expect(FULL.direction).toBe('汽车');
  });

  it('★★ 存储不可用 → ok:false(unavailable)', () => {
    const r = saveDraft(null, FULL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('unavailable');
  });

  it('★ 删除失败 → ok:false(remove_failed)', () => {
    const s = memStorage({ [DRAFT_STORAGE_KEY]: 'x' }, { throwOnRemove: true });
    const r = saveDraft(s, { ...EMPTY_DRAFT });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('remove_failed');
  });
});

/* ================================================================
 * 4. ★★ shouldAutoFillDirection：清空后**不得**被回填
 * ================================================================ */

describe('草稿 · 自动回填判定（缺陷 #1 的核心）', () => {
  it('★★ 用户为当前查询清空过 → **不得**回填', () => {
    expect(shouldAutoFillDirection({
      query: '汽车', direction: '', draftEmpty: true, userClearedFor: '汽车',
    })).toBe(false);
  });

  it('★★ 草稿非空（用户已开始写）→ 绝不覆盖', () => {
    expect(shouldAutoFillDirection({
      query: '汽车', direction: '', draftEmpty: false, userClearedFor: '',
    })).toBe(false);
  });

  it('★★ 方向已有内容 → 不覆盖', () => {
    expect(shouldAutoFillDirection({
      query: '汽车', direction: '智能驾驶合规化', draftEmpty: true, userClearedFor: '',
    })).toBe(false);
  });

  it('★ 空草稿 + 新查询 + 未清空过 → 允许填一次', () => {
    expect(shouldAutoFillDirection({
      query: '医药', direction: '', draftEmpty: true, userClearedFor: '',
    })).toBe(true);
  });

  it('★ 为**别的**查询清空过，现在换了新查询 → 允许填（换查询是新意图）', () => {
    expect(shouldAutoFillDirection({
      query: '医药', direction: '', draftEmpty: true, userClearedFor: '汽车',
    })).toBe(true);
  });

  it('★ 无查询 → 不填', () => {
    expect(shouldAutoFillDirection({
      query: '   ', direction: '', draftEmpty: true, userClearedFor: '',
    })).toBe(false);
  });
});

/* ================================================================
 * 5. browserDraftStorage：SSR 安全
 * ================================================================ */

describe('草稿存储 · 浏览器适配', () => {
  it('★ node / SSR 环境（无 window）→ null，不抛错', () => {
    // 本测试环境即 environment: 'node'
    expect(typeof window).toBe('undefined');
    expect(browserDraftStorage()).toBeNull();
  });
});

/* ================================================================
 * 6. 生命周期组合（模拟「清空 → 再持久化」不得复活记录）
 * ================================================================ */

describe('草稿 · 清空生命周期（存储层）', () => {
  it('★★ 清空后持久化记录确实消失，且不会被空内容复活', () => {
    const s = memStorage();
    saveDraft(s, FULL);
    expect(s.data[DRAFT_STORAGE_KEY]).toBeDefined();

    // 用户点「清空草稿」→ 组件 setDraft(EMPTY) → 持久化 effect 跑
    const cleared: ResearchRequestDraft = { ...EMPTY_DRAFT };
    const r = saveDraft(s, cleared);
    expect(r).toEqual({ ok: true, action: 'removed' });
    expect(s.data[DRAFT_STORAGE_KEY]).toBeUndefined();
    expect(loadDraft(s).status).toBe('empty');
  });

  it('★ isDraftBlank 区分「五字段全空」与「有内容」', () => {
    expect(isDraftBlank({ ...EMPTY_DRAFT })).toBe(true);
    expect(isDraftBlank({ ...EMPTY_DRAFT, whyCare: 'x' })).toBe(false);
    expect(isDraftBlank({ ...EMPTY_DRAFT, linkedQuery: '汽车' })).toBe(false);
  });

  it('★ 序列化 → 反序列化往返不丢字段（含关联证据）', () => {
    const s = memStorage();
    saveDraft(s, FULL);
    const back = loadDraft(s);
    if (back.status !== 'loaded') throw new Error('unreachable');
    expect(back.draft.direction).toBe(FULL.direction);
    expect(back.draft.linkedCoverage?.current).toEqual(FULL.linkedCoverage?.current);
    expect(back.draft.linkedAt).toBe(FULL.linkedAt);
  });
});
