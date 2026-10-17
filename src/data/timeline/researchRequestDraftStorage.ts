/**
 * 研究请求草稿的**本机存储适配层**（ThreeC 1.3 · v0.7）。
 *
 * ## 为什么单独成模块
 * v0.6 把 `loadDraft` / `saveDraft` 直接写在组件里，导致三类问题无法测、也修不干净：
 *   ① `JSON.parse` 只挡语法错误 —— **合法 JSON 但字段类型错误**（如 `{"direction":123}`）
 *      会被展开进草稿，下游 `.trim()` 抛 `TypeError` → **组件崩溃**（浏览器与 SSR 都会崩）；
 *   ② `setItem` 抛错（配额超限 / 权限）被静默吞掉，UI 却仍显示「存在本机」→ **假装保存成功**；
 *   ③ `window` 只在 try/catch 里被间接保护（**零处 `typeof window` 守卫**），
 *      SSR 不崩是**副作用式**的，不是设计。
 *
 * → 本模块：**不碰 `window`**（除 `browserDraftStorage()` 一处显式探测），
 *   把「校验 / 规范化 / 读写结果」变成**纯函数 + 可注入接口**，在无 DOM 环境下可测。
 *
 * ## 设计要点
 * - **白名单**：只接受已知字段；未知字段**丢弃**（不再回流到存储）。
 * - **非字符串一律视为缺失**（**不做** `String()` 强转 —— 强转会把 `123` 变成 `'123'`，
 *   把用户的坏数据伪装成合法内容）。
 * - **超长截断**到 `DRAFT_FIELD_MAX`（与输入路径同一上限）。
 * - **不抛错**：所有存储异常都转成**结果对象**，由调用方决定怎么告知用户。
 * - ★ 存储失败**必须**能被调用方感知 —— 宁可说「未保存」，也不假装保存成功。
 */
import {
  DRAFT_FIELD_MAX,
  EMPTY_DRAFT,
  isDraftBlank,
  type CoverageHit,
  type LinkedCoverage,
  type ResearchRequestDraft,
} from './researchRequestDraft';

/** 存储适配器写入的**结构版本**（与 `draft_version` 同步演进；用于识别旧草稿） */
export const DRAFT_STORAGE_FORMAT_VERSION = 3;
/** 序列化时写入的版本键名（读取时在白名单内，**不**当未知字段丢弃） */
export const DRAFT_VERSION_KEY = '__v';

/** 可注入的存储接口（测试传内存实现；浏览器传 `localStorage`） */
export interface DraftStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

/** ★ 键名带版本：将来改结构时可安全弃用旧键（读旧键 → 规范化 → 写新键） */
export const DRAFT_STORAGE_KEY = 'threec.researchRequestDraft.v1';

/** 单条记录上限：超过即视为损坏（防止被塞进超大 JSON 拖垮页面） */
export const DRAFT_STORAGE_MAX_BYTES = 64 * 1024;

const FIELDS = [
  'direction', 'researchQuestions', 'whyCare', 'knownLeads', 'timeRange',
  'linkedQuery', 'linkedAt',
] as const satisfies readonly (keyof ResearchRequestDraft)[];
/** 读取时的**白名单键**（含结构版本键与关联证据键） */
const KNOWN_KEYS = new Set<string>([...FIELDS, 'linkedCoverage', DRAFT_VERSION_KEY]);

/** 取一个「一定是字符串」的值；非字符串（含 null / 数字 / 对象 / 数组 / 布尔）→ '' */
function asText(v: unknown): string {
  return typeof v === 'string' ? v.slice(0, DRAFT_FIELD_MAX) : '';
}

/** 规范化 `linkedCoverage`：形状不对 → null（**不猜**、不半信半疑地保留） */
function asLinkedCoverage(v: unknown): LinkedCoverage | null {
  if (v === null || v === undefined) return null;
  if (typeof v !== 'object' || Array.isArray(v)) return null;
  const o = v as Record<string, unknown>;
  const verdict = o.verdict;
  if (verdict !== 'both' && verdict !== 'current-only' && verdict !== 'historical-only' && verdict !== 'none') {
    return null;
  }
  const hits = (x: unknown): CoverageHit[] => {
    if (!Array.isArray(x)) return [];
    return x
      .filter((h): h is Record<string, unknown> => !!h && typeof h === 'object' && !Array.isArray(h))
      .map((h) => {
        // ★ v0.8：`matchedOn` 三态保留 —— 缺键 / null → null（旧草稿未保存该信息）；
        //   是数组 → 只留字符串元素；其它类型 → null（**不得**伪造成 []）
        const mo = Object.prototype.hasOwnProperty.call(h, 'matchedOn') ? h.matchedOn : null;
        return {
          id: asText(h.id),
          title: asText(h.title),
          matchedOn: Array.isArray(mo)
            ? (mo.filter((s): s is string => typeof s === 'string'))
            : null,
        };
      })
      .filter((h) => h.id.length > 0);
  };
  const res = o.resolution;
  const resolution = res && typeof res === 'object' && !Array.isArray(res)
    ? (res as LinkedCoverage['resolution'])
    : null;
  return {
    query: asText(o.query),
    verdict,
    current: hits(o.current),
    historical: hits(o.historical),
    resolution,
    captured_at: asText(o.captured_at),
  };
}

/**
 * ★★ 把**不可信**的本机存储内容规范化为一份安全草稿。
 *
 * 无论输入多离谱都**不抛错**：坏字段 → `''`，坏关联 → `null`，未知字段 → 丢弃。
 * @returns `{ draft, issues }` —— `issues` 列出**被丢弃/被修正**的字段（供 UI 诚实披露）
 */
export function normalizeDraft(value: unknown): { draft: ResearchRequestDraft; issues: string[] } {
  const issues: string[] = [];
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    return { draft: { ...EMPTY_DRAFT }, issues: ['内容不是对象（已丢弃）'] };
  }
  const o = value as Record<string, unknown>;

  // 未知字段：丢弃（不再写回存储）
  for (const k of Object.keys(o)) {
    if (!KNOWN_KEYS.has(k)) {
      issues.push(`未知字段已丢弃：${k}`);
    }
  }

  const draft: ResearchRequestDraft = { ...EMPTY_DRAFT };
  for (const f of FIELDS) {
    const raw = o[f];
    const text = asText(raw);
    if (raw !== undefined && typeof raw !== 'string') {
      issues.push(`${f} 类型错误（${raw === null ? 'null' : typeof raw}）→ 已置空`);
    } else if (typeof raw === 'string' && raw.length > DRAFT_FIELD_MAX) {
      issues.push(`${f} 超长（${raw.length} > ${DRAFT_FIELD_MAX}）→ 已截断`);
    }
    draft[f] = text;
  }

  const lc = asLinkedCoverage(o.linkedCoverage);
  if (o.linkedCoverage !== undefined && o.linkedCoverage !== null && lc === null) {
    issues.push('linkedCoverage 形状不合法 → 已置空（原查询证据不可恢复）');
  }
  draft.linkedCoverage = lc;

  return { draft, issues };
}

/** 序列化：空草稿（含关联）→ `null`（调用方据此 `removeItem`，不留垃圾记录） */
export function serializeDraft(d: ResearchRequestDraft): string | null {
  if (isDraftBlank(d)) return null;
  return JSON.stringify({ [DRAFT_VERSION_KEY]: DRAFT_STORAGE_FORMAT_VERSION, ...d });
}

export type LoadDraftResult =
  /** 存储不可用（无 window / 被禁 / 读取抛错）—— ★ 与「没有草稿」是两件事 */
  | { status: 'unavailable'; reason: string }
  /** 没有草稿记录 */
  | { status: 'empty' }
  /** 读到并规范化成功（`issues` 非空表示原内容有坏字段，已修正） */
  | { status: 'loaded'; draft: ResearchRequestDraft; issues: string[] }
  /** 有内容但不可用（语法坏 / 形状坏 / 超大）—— ★ 不冒充「没有草稿」，也不静默丢弃 */
  | { status: 'corrupt'; reason: 'json' | 'shape' | 'oversized'; rawLength: number };

/** 读取并规范化。**任何情况下都不抛错。** */
export function loadDraft(storage: DraftStorage | null): LoadDraftResult {
  if (!storage) return { status: 'unavailable', reason: '存储不可用' };
  let raw: string | null;
  try {
    raw = storage.getItem(DRAFT_STORAGE_KEY);
  } catch (e) {
    return { status: 'unavailable', reason: e instanceof Error ? e.message : '读取失败' };
  }
  if (raw === null || raw === '') return { status: 'empty' };
  if (raw.length > DRAFT_STORAGE_MAX_BYTES) {
    return { status: 'corrupt', reason: 'oversized', rawLength: raw.length };
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { status: 'corrupt', reason: 'json', rawLength: raw.length };
  }
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return { status: 'corrupt', reason: 'shape', rawLength: raw.length };
  }
  const { draft, issues } = normalizeDraft(parsed);
  // 规范化后**全空**（含关联）→ 视为没有草稿（避免把一堆空字段当成用户内容展示）
  if (isDraftBlank(draft)) {
    return { status: 'empty' };
  }
  return { status: 'loaded', draft, issues };
}

export type SaveDraftResult =
  | { ok: true; action: 'written' | 'removed' }
  /** ★ 保存失败**必须**能被调用方感知 —— UI 据此显示「未保存」，不得假装成功 */
  | { ok: false; reason: 'unavailable' | 'write_failed' | 'remove_failed'; detail: string };

/** 写入（或空草稿时删除）。**不抛错**，失败转结果对象。 */
export function saveDraft(storage: DraftStorage | null, d: ResearchRequestDraft): SaveDraftResult {
  if (!storage) return { ok: false, reason: 'unavailable', detail: '存储不可用' };
  const payload = serializeDraft(d);
  try {
    if (payload === null) {
      storage.removeItem(DRAFT_STORAGE_KEY);
      return { ok: true, action: 'removed' };
    }
    storage.setItem(DRAFT_STORAGE_KEY, payload);
    return { ok: true, action: 'written' };
  } catch (e) {
    const detail = e instanceof Error ? e.message : '写入失败';
    return payload === null
      ? { ok: false, reason: 'remove_failed', detail }
      : { ok: false, reason: 'write_failed', detail };
  }
}

/**
 * ★ **唯一**触碰 `window` 的地方（显式探测，不靠 try/catch 兜）。
 * 无 window（SSR / node 测试）/ 被禁 / 探测抛错 → `null`（调用方走「存储不可用」分支）。
 */
export function browserDraftStorage(): DraftStorage | null {
  try {
    if (typeof window === 'undefined') return null;
    const ls = window.localStorage;
    if (!ls) return null;
    return {
      getItem: (k) => ls.getItem(k),
      setItem: (k, v) => ls.setItem(k, v),
      removeItem: (k) => ls.removeItem(k),
    };
  } catch {
    // Safari 隐私模式等：访问 localStorage 本身可能抛错
    return null;
  }
}

/**
 * ★★ 是否应把当前查询词**自动填入**草稿方向（纯函数，可测）。
 *
 * v0.6 的判定是「方向字段为空就填」—— 于是：
 *   · 用户点「清空草稿」后**立刻被填回**；
 *   · 用户**手动删掉方向**也会被填回 ⇒ 该字段在有查询时**等同不可清空**。
 *
 * v0.7 改为**只对「空草稿」自动填一次**，并记住「用户为哪个查询显式清空过」：
 *   - 草稿非空（用户已开始写）→ **绝不自动覆盖**
 *   - 用户为**当前这个查询**清空过 → 不再自动填（清空是真的清空）
 *   - 用户为**别的查询**清空过，现在换了一个查询 → 允许为新查询填一次
 *     （换查询是新的意图；但不会静默改绑已有关联，见 `linkage`）
 */
export function shouldAutoFillDirection(args: {
  /** 当前查询词（无查询 → ''） */
  query: string;
  /** 当前草稿方向 */
  direction: string;
  /** 草稿是否为空（五字段 + 关联都空） */
  draftEmpty: boolean;
  /** 用户最近一次显式清空时对应的查询词（未清空过 → ''） */
  userClearedFor: string;
}): boolean {
  const q = args.query.trim();
  if (!q) return false;
  if (!args.draftEmpty) return false;
  if (args.direction.trim()) return false;
  if (args.userClearedFor && args.userClearedFor === q) return false;
  return true;
}
