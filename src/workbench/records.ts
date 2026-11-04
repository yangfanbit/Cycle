/**
 * 研究工作台的记录层（v0.74）—— 轻量真实使用协议 `docs/REAL_USE_LITE_v0_1.md`。
 *
 * ★★ 两条硬边界：
 *  ① T 时刻正文（records）与事后核对（evals）**物理分离**：两个 localStorage key、
 *     导出时两个独立数组。写事后核对**不会**改动正文。
 *  ② 内部排序 / 评分**不在这里**，也不在默认页面；只在 EvalView 按需加载。
 */
import type { IndexDoc, PosthocEval, UseRecord, WorkbenchItem } from './types';

const RECORDS_KEY = 'threec.workbench.records.v1';
const EVALS_KEY = 'threec.workbench.evals.v1';

function store(): Storage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage;
  } catch {
    return null;
  }
}

function read<T>(key: string): T[] {
  const s = store();
  if (!s) return [];
  try {
    const v = JSON.parse(s.getItem(key) ?? '[]');
    return Array.isArray(v) ? (v as T[]) : [];
  } catch {
    return [];
  }
}

function write<T>(key: string, rows: T[]): void {
  const s = store();
  if (!s) return;
  try {
    s.setItem(key, JSON.stringify(rows));
  } catch {
    /* 存储不可用/配额满：UI 仍可用，只是不持久化 */
  }
}

export const loadRecords = (): UseRecord[] => read<UseRecord>(RECORDS_KEY);
export const loadEvals = (): PosthocEval[] => read<PosthocEval>(EVALS_KEY);

/** 纯函数：按当天已有条数生成 `RU-YYYYMMDD-NN`。 */
export function nextRecordId(existing: UseRecord[], now: Date): string {
  const day = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0')].join('');
  const prefix = `RU-${day}-`;
  const max = existing.reduce((m, r) => {
    if (!r.record_id.startsWith(prefix)) return m;
    const n = Number(r.record_id.slice(prefix.length));
    return Number.isFinite(n) ? Math.max(m, n) : m;
  }, 0);
  return prefix + String(max + 1).padStart(2, '0');
}

export interface FrozenInput {
  question: string;
  verdict_at_T: string;
  type: UseRecord['type'];
  cluster_id: string;
  item_ref?: string | null;
}

/** 纯函数：冻结 T 时刻正文（不含 posthoc_check）。 */
export function freezeRecord(input: FrozenInput, doc: IndexDoc, now: Date,
                             existing: UseRecord[] = []): UseRecord {
  return {
    record_id: nextRecordId(existing, now),
    frozen_at: now.toISOString(),
    data_as_of: doc.as_of,
    question: input.question.trim(),
    verdict_at_T: input.verdict_at_T.trim(),
    type: input.type,
    cluster_id: input.cluster_id.trim(),
    artifact_ref: `workbench_index_v0_1@${doc.generated_at}`,
    item_ref: input.item_ref ?? null,
  };
}

/** 追加式：只增不改，已存在的 record_id 不会被覆盖。 */
export function saveRecord(r: UseRecord): UseRecord[] {
  const rows = loadRecords();
  if (rows.some((x) => x.record_id === r.record_id)) return rows;
  const next = [...rows, r];
  write(RECORDS_KEY, next);
  return next;
}

/** 事后核对单独存；同一记录可追加多条（不改正文，等价于 amend 的轻量形态）。 */
export function saveEval(e: PosthocEval): PosthocEval[] {
  const rows = loadEvals();
  const next = [...rows, e];
  write(EVALS_KEY, next);
  return next;
}

/** 导出：正文与事后核对是两个独立数组，方便落到 .tmp/real_use/records/。 */
export function exportBundle(): string {
  return JSON.stringify({
    protocol: 'REAL_USE_LITE_v0_1',
    exported_at: new Date().toISOString(),
    records: loadRecords(),
    evals: loadEvals(),
  }, null, 2);
}

/** 纯函数检索：多词 AND、大小写不敏感；空 query 返回空（默认不铺 385 条）。 */
export function searchItems(items: WorkbenchItem[], query: string): WorkbenchItem[] {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return [];
  return items.filter((it) => {
    const hay = [it.title ?? '', (it.themes ?? []).join(' '), it.why ?? '',
      it.source?.name ?? '', it.id].join(' ').toLowerCase();
    return words.every((w) => hay.includes(w));
  });
}

export function downloadText(filename: string, text: string): void {
  if (typeof document === 'undefined') return;
  const blob = new Blob([text], { type: 'application/json;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
