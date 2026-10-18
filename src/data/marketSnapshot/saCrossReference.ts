/**
 * ★★ 历史事件 × **冻结 SA** 的精确交叉引用（ThreeC v0.21）。
 *
 * ## 这是什么
 *
 * 历史题材地图里的每个事件都登记了一个**正式历史对象**（`campaign_facts.object_id`，
 * 兼容旧字段 `campaign_id`）。本模块回答一个问题：
 *
 * > 这个历史对象，是否被**当前唯一 `CANONICAL` 快照**的 SA 结果**引用**了？在哪一个
 * > 当前研究对象下、已有 `structural_status` 是什么？
 *
 * ## 这不是什么（硬边界）
 *
 * - **不重算 SA**：只**读**快照里的 `historical_candidates`，不实现、不推断任何结构规则
 *   （`AGENTS.md` §4：Product 不得重算 Structural Analogy）。
 * - **只做精确 ID 匹配**：历史对象 id 取自事件的 `object_id` / `campaign_id`；
 *   SA 侧按 `identity.historical_campaign_id` / `identity.historical_research_candidate_id`
 *   **完全相等**匹配。**不**按主题名、年份、名称相似度推测。
 * - **不把对象级结构状态读成「某只股票被确认」**：SA 是**对象之间**的结构判定；
 *   与证券注册表 / 四分类对账是**两回事**，不得混为一谈。
 * - **未找到 ≠ 不存在**：快照未收录只说明「这一份快照没有它的对象级记录」，
 *   既不等于不存在结构对应，也不等于研究侧已否决该对象。
 * - **只读**：不写文件、不联网、不调 LLM、不改冻结产物。
 */
import type { MarketSnapshot } from './types';
import { CANONICAL, snapshotIndex } from './snapshotAdapter';
import { STRUCTURAL_STATUS_LABEL, type StructuralStatus } from '../timeline/structuralAnalogy';

const SNAPSHOT_BASE = '/research/current/market_snapshots/snapshots/';
const LOADERS = import.meta.glob<{ default: MarketSnapshot }>(
  '/research/current/market_snapshots/snapshots/*.json',
);

/** 一个当前研究对象对某历史对象的 SA 记录（原样取自快照，不改写） */
export interface SaReferenceRow {
  currentObjectId: string;
  /** 当前研究对象显示名（取自快照 `research_objects`；缺 → 退回 id） */
  currentObjectName: string;
  currentObjectTheme: string | null;
  /** 快照里的 `structural_status`（**原样**） */
  structuralStatus: string;
  /** 中文标签（取自冻结 SA 的既有码表，未知名原样显示码值） */
  statusLabel: string;
  strictStructuralSupported: boolean;
}

export interface SaCrossReferenceIndex {
  /** ★ 是否成功载入 CANONICAL 快照 —— `false` 表示**无法判定**（**不是**「未找到」） */
  loaded: boolean;
  snapshotId: string;
  marketSnapshotVersion: string;
  snapshotStatus: string;
  ruleSetVersion: string | null;
  artifactVersion: string | null;
  sourceCommit: string | null;
  /** 历史对象 id → 引用它的当前研究对象（按 `current_object_id` 升序） */
  byHistoricalObject: Map<string, SaReferenceRow[]>;
  /** `identity` 两侧都为空 → 无法建立精确关联的候选行数（记录原因，不推测） */
  unidentifiedRows: number;
  /** 载入失败原因（`loaded=false` 时给出；成功时为 null） */
  loadError: string | null;
}

/** 空索引（无 CANONICAL 快照 / 载入失败）—— `loaded=false`，**不得**当成「未找到」 */
export function emptySaCrossReference(reason: string | null = null): SaCrossReferenceIndex {
  return {
    loaded: false,
    snapshotId: '',
    marketSnapshotVersion: '',
    snapshotStatus: '',
    ruleSetVersion: null,
    artifactVersion: null,
    sourceCommit: null,
    byHistoricalObject: new Map<string, SaReferenceRow[]>(),
    unidentifiedRows: 0,
    loadError: reason,
  };
}

/**
 * ★★ 载入唯一 `CANONICAL` 快照并建立「历史对象 → 当前研究对象」索引。
 *
 * ★ 默认门禁与页面一致：**只读 `CANONICAL`**；索引里没有任何 CANONICAL → 返回空索引。
 * ★ 任何异常都转成空索引（诚实「无法判定」），**不**让页面崩。
 */
export async function loadSaCrossReference(): Promise<SaCrossReferenceIndex> {
  try {
    const entries = snapshotIndex().filter((e) => e.status === CANONICAL);
    if (entries.length === 0) return emptySaCrossReference('索引中没有 CANONICAL 快照');
    const entry = entries[entries.length - 1];

    const loader = LOADERS[`${SNAPSHOT_BASE}${entry.file}`];
    if (!loader) return emptySaCrossReference(`快照文件未随构建打包：${entry.file}`);

    const mod = await loader();
    const snap = (mod?.default ?? null) as MarketSnapshot | null;
    if (!snap) return emptySaCrossReference(`快照文件为空：${entry.file}`);

    // ★ 二次门禁（防索引漂移）——与 `loadCurrentSnapshot` 同一原则
    if (snap.status !== CANONICAL) {
      return emptySaCrossReference(`快照状态不是 CANONICAL：${snap.status}`);
    }

    const metaById = new Map(snap.research_objects.map((o) => [o.object_id, o]));
    const byHistoricalObject = new Map<string, SaReferenceRow[]>();
    let unidentifiedRows = 0;

    for (const c of snap.historical_candidates ?? []) {
      const identity = c.identity;
      // ★ 只认**精确对象 id**：对象类型决定取哪个字段
      const key = identity?.historical_campaign_id
        ?? identity?.historical_research_candidate_id
        ?? null;
      if (!key) {
        unidentifiedRows += 1;      // 记录原因，**不**推测归属
        continue;
      }
      const meta = metaById.get(c.current_object_id);
      const row: SaReferenceRow = {
        currentObjectId: c.current_object_id,
        currentObjectName: meta?.display_name ?? c.current_object_id,
        currentObjectTheme: meta?.macro_theme ?? null,
        structuralStatus: c.structural_status,
        // ★ 未知码**原样显示码值**（不编造含义）
        statusLabel: STRUCTURAL_STATUS_LABEL[c.structural_status as StructuralStatus] ?? c.structural_status,
        strictStructuralSupported: Boolean(c.strict_structural_supported),
      };
      const arr = byHistoricalObject.get(key) ?? [];
      arr.push(row);
      byHistoricalObject.set(key, arr);
    }
    for (const arr of byHistoricalObject.values()) {
      arr.sort((a, b) => a.currentObjectId.localeCompare(b.currentObjectId));
    }

    const src = (snap as unknown as {
      candidates_source?: { artifact_version?: string; rule_set_version?: string };
    }).candidates_source;
    const prov = (snap as unknown as { provenance?: { source_commit?: string } }).provenance;

    return {
      loaded: true,
      snapshotId: snap.snapshot_id,
      marketSnapshotVersion: snap.market_snapshot_version,
      snapshotStatus: snap.status,
      ruleSetVersion: src?.rule_set_version ?? null,
      artifactVersion: src?.artifact_version ?? null,
      sourceCommit: prov?.source_commit ?? null,
      byHistoricalObject,
      unidentifiedRows,
      loadError: null,
    };
  } catch (e) {
    return emptySaCrossReference(e instanceof Error ? e.message : String(e));
  }
}

/** 某个历史对象 id 的 SA 引用（纯函数；`objectId` 为空 → 未匹配，**不推测**） */
export function saReferenceFor(
  index: SaCrossReferenceIndex, objectId: string | null | undefined,
): { matched: boolean; rows: SaReferenceRow[] } {
  if (!objectId) return { matched: false, rows: [] };
  const rows = index.byHistoricalObject.get(objectId);
  return { matched: Boolean(rows && rows.length > 0), rows: rows ?? [] };
}

/** 索引汇总（供测试 / 报表；只做计数事实，不做判定） */
export function summarizeSaCrossReference(index: SaCrossReferenceIndex): {
  loaded: boolean;
  historicalObjects: number;
  rows: number;
  byStatus: Record<string, number>;
} {
  const byStatus: Record<string, number> = {};
  let rows = 0;
  for (const arr of index.byHistoricalObject.values()) {
    for (const r of arr) {
      rows += 1;
      byStatus[r.structuralStatus] = (byStatus[r.structuralStatus] ?? 0) + 1;
    }
  }
  return { loaded: index.loaded, historicalObjects: index.byHistoricalObject.size, rows, byStatus };
}

/* ------------------------------------------------------ 展示文案（UI 原样渲染） */

export const SA_BLOCK_TITLE = '与当前冻结 SA 的关系';

/** ★★ 未匹配事件的**明确**说明（不得读成「不存在结构对应」或「已被否决」） */
export const SA_NOT_FOUND_LABEL = '当前冻结 SA 快照未找到该历史对象的对应记录';

export const SA_NOT_FOUND_CAVEAT =
  '★ 「未找到」只表示**这一份快照未收录它的对象级记录** —— **不等于**不存在结构对应，'
  + '也**不等于**研究侧已否决该对象。';

/** ★★ 对象级 SA 状态 ≠ 个股确认（与证券注册表 / 四分类对账是两回事） */
export const SA_OBJECT_LEVEL_CAVEAT =
  '★ 对象级 `structural_status` 是**对象之间**的结构判定（由冻结 SA 规则给出），'
  + '**不是**对某只股票的确认 —— 与上面的**证券注册表 / 四分类对账**是两回事，**不得混为一谈**。';

/** ★ 事件未记录对象 → 无法做对象级交叉引用（也不得推测） */
export const SA_NO_OBJECT_LABEL =
  '事件未记录关联对象（缺 `campaign_facts.object_id`）→ 当前无法进行对象级 SA 交叉引用（不推测归属）。';

/** ★ 快照未载入 → 无法判定（不是「未找到」） */
export const SA_NOT_LOADED_LABEL =
  '未能载入 CANONICAL 快照 —— **无法判定**是否有对应记录（这不等于「未找到」）。';
