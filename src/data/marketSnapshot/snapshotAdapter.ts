import indexJson from '@market/index.json';
import { diffSnapshots } from './snapshotDiff';
import type { MarketSnapshot, SnapshotDiff } from './types';
import {
  DIMENSION_LABEL,
  DIMENSION_STATUS_LABEL,
  STRUCTURAL_STATUS_LABEL,
  THEME_RELATION_LABEL,
  loadStructuralAnalogyDataset,
  structuralAnalogyForCandidate,
  type DimensionKey,
  type DriverStatus,
  type StructuralStatus,
  type ThemeRelationValue,
} from '../timeline/structuralAnalogy';

/**
 * Market Snapshot 的 **Product 只读适配器**（ThreeC 1.1 Phase 1.3）。
 *
 * ## 门禁（硬约束）
 * 默认**只展示 `CANONICAL`** —— 按 `AGENTS.md` §5.1 与快照契约：只有已签发快照允许 Product 消费。
 * `?snapshot=draft` 可放宽为「预览任意状态」，但页面**必须常驻醒目徽章**标明「未签发」。
 *
 * ## 为什么 index 静态 import、快照 lazy import
 * 快照按月累积（~192 KB/份），全量静态 import 会让主包随月份持续膨胀。
 * `index.json` 极小（只有 id / date / status / file），静态 import；
 * 真正需要的那 1–2 份快照走 `import.meta.glob` 的**按需**加载。
 *
 * ## 只读
 * 不写任何文件、不联网、不调 LLM、不修改快照。
 */

export interface SnapshotIndexEntry {
  snapshot_id: string;
  snapshot_date: string;
  status: string;
  market_snapshot_version: string;
  file: string;
}

interface SnapshotIndexDoc {
  contract: string;
  index_version: string;
  snapshots: SnapshotIndexEntry[];
}

const LOADERS = import.meta.glob<{ default: MarketSnapshot }>(
  '/research/current/market_snapshots/snapshots/*.json',
);

const SNAPSHOT_BASE = '/research/current/market_snapshots/snapshots/';

export const CANONICAL = 'CANONICAL';

/** 索引条目，按 snapshot_date 升序（同日按 id） */
export function snapshotIndex(): SnapshotIndexEntry[] {
  const doc = indexJson as unknown as SnapshotIndexDoc;
  return [...(doc?.snapshots ?? [])].sort((a, b) =>
    `${a.snapshot_date}::${a.snapshot_id}`.localeCompare(`${b.snapshot_date}::${b.snapshot_id}`),
  );
}

async function loadOne(file: string): Promise<MarketSnapshot | null> {
  const loader = LOADERS[`${SNAPSHOT_BASE}${file}`];
  if (!loader) return null;
  const mod = await loader();
  return (mod?.default ?? null) as MarketSnapshot | null;
}

/**
 * ★ 回指解析结果（P0「接通」）：快照只存 `identity + status`，**细节在冻结 SA artifact 里**。
 * 这里按契约把两者合并，让「79 条比对」变成**可看的明细**。
 *
 * 只做合并与改名，**不重算**任何判定（见 `structuralAnalogy.ts` 的边界声明）。
 */
export interface CandidateDetail {
  historicalCycleId: string;
  historicalObjectKind: string;
  status: StructuralStatus;
  statusLabel: string;
  themeRelation: ThemeRelationValue | null;
  themeRelationLabel: string;
  /** 四维度状态（lifecycle / mechanism_driver / evidence_sequence / event_structure） */
  dimensions: { key: DimensionKey; label: string; status: DriverStatus; statusLabel: string }[];
  whySimilar: string[];
  whyNotSimilar: string[];
}

/** 按对象聚合的候选明细；`resolved=false` 表示 SA 数据未能载入（诚实空态，不是「无对应」） */
export interface ObjectCandidateDetails {
  objectId: string;
  resolved: boolean;
  details: CandidateDetail[];
}

export interface CurrentSnapshotView {
  /**
   * `ok`          = 有可展示的快照
   * `no-canonical`= 有快照，但全部未签发（默认门禁下无可展示内容）
   * `empty`       = 索引里没有任何快照
   */
  state: 'ok' | 'no-canonical' | 'empty';
  /** 是否为「放宽门禁的预览」（对应 ?snapshot=draft） */
  preview: boolean;
  snapshot: MarketSnapshot | null;
  /** 上一份可展示的快照（用于 diff）；没有则 null */
  previous: MarketSnapshot | null;
  diff: SnapshotDiff | null;
  /** 索引里最新的快照日期（用于空态文案） */
  latestDate: string | null;
  /** 未签发快照的数量（用于空态文案） */
  draftCount: number;
  /** ★ 按对象聚合的候选明细（回指解析结果） */
  detailsByObject: ObjectCandidateDetails[];
}

const EMPTY: CurrentSnapshotView = {
  state: 'empty',
  preview: false,
  snapshot: null,
  previous: null,
  diff: null,
  latestDate: null,
  draftCount: 0,
  detailsByObject: [],
};

/** 维度顺序（契约顺序）+ 到 SA view 的 camelCase 键映射 */
const DIMENSION_ORDER: { key: DimensionKey; viewKey: string }[] = [
  { key: 'lifecycle', viewKey: 'lifecycle' },
  { key: 'mechanism_driver', viewKey: 'mechanismDriver' },
  { key: 'evidence_sequence', viewKey: 'evidenceSequence' },
  { key: 'event_structure', viewKey: 'eventStructure' },
];

/**
 * ★ 回指解析：把快照的 `identity + status` 与冻结 SA artifact 的**细节**合并。
 *
 * 契约要求读取方先校验 artifact 的 `rule_set_version` 与快照 `candidates_source` 一致 ——
 * 不一致时**不合并**（宁可显示「未解析」，也不显示可能对不上的细节）。
 */
async function resolveDetails(snapshot: MarketSnapshot): Promise<ObjectCandidateDetails[]> {
  const fallback = () =>
    (snapshot.research_objects ?? []).map((o) => ({
      objectId: o.object_id,
      resolved: false,
      details: [] as CandidateDetail[],
    }));

  try {
    const ds = await loadStructuralAnalogyDataset();
    const expected = (snapshot as unknown as { candidates_source?: { rule_set_version?: string } })
      .candidates_source?.rule_set_version;
    if (expected && ds.ruleSetVersion !== expected) {
      // 版本不一致 → 拒绝合并（诚实空态），避免用错版本的细节
      return fallback();
    }

    return (snapshot.research_objects ?? []).map((o) => {
      const cand = structuralAnalogyForCandidate(ds, o.object_id);
      if (!cand) return { objectId: o.object_id, resolved: false, details: [] };
      const details: CandidateDetail[] = cand.explanations.map((e) => {
        const tr = e.themeRelation?.value ?? null;
        return {
          historicalCycleId: e.identity.historicalCycleId,
          historicalObjectKind: e.identity.historicalObjectKind,
          status: e.structuralStatus,
          statusLabel: STRUCTURAL_STATUS_LABEL[e.structuralStatus] ?? e.structuralStatus,
          themeRelation: tr,
          themeRelationLabel: tr ? THEME_RELATION_LABEL[tr] ?? tr : '',
          dimensions: DIMENSION_ORDER.map(({ key, viewKey }) => {
            const raw = (e.dimensions as unknown as Record<string, { status?: DriverStatus }>)[viewKey];
            const st = (raw?.status ?? 'UNKNOWN') as DriverStatus;
            return {
              key,
              label: DIMENSION_LABEL[key],
              status: st,
              statusLabel: DIMENSION_STATUS_LABEL[st] ?? st,
            };
          }),
          whySimilar: e.whySimilar ?? [],
          whyNotSimilar: e.whyNotSimilar ?? [],
        };
      });
      return { objectId: o.object_id, resolved: true, details };
    });
  } catch {
    return fallback();
  }
}

/**
 * 载入「当前快照」视图。
 *
 * @param previewMode `true` 时放宽为「任意状态」（页面需自行显示未签发徽章）
 */
export async function loadCurrentSnapshot(previewMode = false): Promise<CurrentSnapshotView> {
  const entries = snapshotIndex();
  if (entries.length === 0) return EMPTY;

  const latestDate = entries[entries.length - 1].snapshot_date;
  const draftCount = entries.filter((e) => e.status !== CANONICAL).length;

  const eligible = previewMode ? entries : entries.filter((e) => e.status === CANONICAL);
  if (eligible.length === 0) {
    return { ...EMPTY, state: 'no-canonical', preview: previewMode, latestDate, draftCount };
  }

  const latestEntry = eligible[eligible.length - 1];
  // ★ 「上一期」= **更早的、snapshot_date 不同的最近一份**（不限状态）。
  //   ① 不限状态：归档/被取代的上一期仍是对照基准，diff 不会因归档而凭空消失；
  //   ② 必须换日期：月度工具要的是「跟上个月比」，**同日的 revision 不算上一期**
  //      （否则一次修正就会把月度对照挤掉）。
  const prevEntry =
    [...entries].reverse().find((e) => e.snapshot_date < latestEntry.snapshot_date) ?? null;

  const snapshot = await loadOne(latestEntry.file);
  if (!snapshot) return { ...EMPTY, state: 'empty', preview: previewMode, latestDate, draftCount };

  // ★ 二次门禁（防索引漂移）：非预览模式下，载入后再次确认状态
  if (!previewMode && snapshot.status !== CANONICAL) {
    return { ...EMPTY, state: 'no-canonical', preview: false, latestDate, draftCount };
  }

  const previous = prevEntry ? await loadOne(prevEntry.file) : null;
  const diff = previous ? diffSnapshots(previous, snapshot) : null;
  const detailsByObject = await resolveDetails(snapshot);

  return {
    state: 'ok',
    preview: previewMode && snapshot.status !== CANONICAL,
    snapshot,
    previous,
    diff,
    latestDate,
    draftCount,
    detailsByObject,
  };
}
