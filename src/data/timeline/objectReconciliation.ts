/**
 * ★★ 历史题材地图 × Research 对象：**标的对账**（ThreeC v0.17）。
 *
 * ## 这是什么
 *
 * 把题材事件（`HistoricalEvent`）里 `participants[].security_id` 与
 * canonical export（`exports/timeline_export_v1.json`）中**事件关联对象**
 * （`campaign_facts.object_id`，兼容旧字段 `campaign_id`）的 `security_ids`
 * 做**精确对账**。
 *
 * ## 这不是什么（硬边界）
 *
 * - **不做模糊匹配**：只按 `security_id` 字符串**完全相等**比对。
 * - **不推断证券身份**：不解析名称、代码前缀、来源文本里的对象引用。
 * - **不修改 Research 数据**：纯只读派生，不写回、不改冻结产物。
 * - **不把「地图补充」当成错误**：Product 地图里的补充关联是**记录**，不是判定。
 *
 * ## 四种对账结果（封闭集合）
 *
 * | link | 含义 |
 * |---|---|
 * | `OBJECT_REGISTERED` | 该证券在**关联对象**的 `security_ids` 中（Research 侧已登记关联） |
 * | `MAP_SUPPLEMENT` | 该证券在**全局注册表**中存在，但**不在**关联对象的 `security_ids` 中（Product 地图补充记录） |
 * | `NO_OBJECT_REFERENCE` | 事件**未记录关联对象**（无 `campaign_facts` / 无 `object_id`）→ 当前**无法进行对象级对账**（★ **不**暗示证券不存在，**不**自动判定其应属于某个 Campaign） |
 * | `UNRESOLVED` | **已提供**对象引用，但对象**无法解析**（不在 canonical export），**或**证券注册信息缺失 → **无法核对** |
 *
 * ★ 对账是**结构事实核对**，**不是**「相关度」或「对错」判定。
 * ★ ★★ 2026-10-18（v0.18）：把「事件未记录对象」从 `UNRESOLVED` 中**拆出**为
 *   `NO_OBJECT_REFERENCE` —— 否则汇总会把「缺少关联字段」误读成「对象解析失败」。
 */
import exportJson from '@exports/timeline_export_v1.json';
import type { HistoricalEvent, HistoricalEventsDoc } from './historicalEventMaps';

export type ReconLink =
  | 'OBJECT_REGISTERED'
  | 'MAP_SUPPLEMENT'
  | 'NO_OBJECT_REFERENCE'
  | 'UNRESOLVED';

export const RECON_LINK_LABEL: Record<ReconLink, string> = {
  OBJECT_REGISTERED: '对象已登记关联',
  MAP_SUPPLEMENT: '地图补充记录',
  NO_OBJECT_REFERENCE: '未登记对象关联',
  UNRESOLVED: '无法核对',
};

/** ★ 对账语义声明（事件详情与标的索引原样渲染） */
export const RECON_CAVEAT =
  '★ 对账只做**精确匹配**：按「事件关联对象的 `security_ids`」与「canonical export 的证券注册表」'
  + '逐条比对，**不**按名称模糊匹配、**不**推断证券身份、**不**修改 Research 数据。'
  + '「地图补充记录」= 该证券在全局注册表中、但不在关联对象的 `security_ids` 中，'
  + '属 Product 地图的**补充关联**，**不自动**视为错误；'
  + '「**未登记对象关联**」= 该事件**未记录关联对象**（缺 `object_id`）→ 当前**无法做对象级对账**，'
  + '**不**暗示证券不存在、**不**自动判定其应属于某个 Campaign；'
  + '「无法核对」= **已提供**对象引用但对象无法解析，**或**证券注册信息缺失，**不猜测**身份。';

export interface ObjectSecurityReconciliation {
  /** 事件关联对象 id（`campaign_facts.object_id` ?? `campaign_facts.campaign_id`） */
  objectId: string | null;
  objectKind: 'campaign' | 'candidate' | null;
  /** 该对象是否在 canonical export 中解析到 */
  objectFound: boolean;
  /** 该证券是否在 canonical export 的 `securities` 注册表中 */
  securityRegistered: boolean;
  /** 该证券是否在该对象的 `security_ids` 中 */
  inObjectSecurityIds: boolean;
  link: ReconLink;
  /** 判定原因的完整说明（无法核对时逐条列出缺什么） */
  reason: string;
}

export const RECON_LINK_ORDER: ReconLink[] = [
  'OBJECT_REGISTERED', 'MAP_SUPPLEMENT', 'NO_OBJECT_REFERENCE', 'UNRESOLVED',
];

/* ------------------------------------------------------ 只读索引（canonical export） */

interface ObjEntry {
  kind: 'campaign' | 'candidate';
  securityIds: Set<string>;
}

interface ExportCampaignLike {
  campaign_id?: string;
  security_ids?: string[] | null;
}
interface ExportSecurityLike {
  security_id?: string;
}

const OBJECT_INDEX: Map<string, ObjEntry> = (() => {
  const map = new Map<string, ObjEntry>();
  const raw = exportJson as unknown as {
    campaigns?: ExportCampaignLike[];
    research_candidates?: ExportCampaignLike[];
  };
  for (const c of raw.campaigns ?? []) {
    if (!c.campaign_id) continue;
    map.set(c.campaign_id, { kind: 'campaign', securityIds: new Set(c.security_ids ?? []) });
  }
  // ★ Research Candidate 的 id 字段与 Campaign 同名（`campaign_id`），kind 区分身份
  for (const c of raw.research_candidates ?? []) {
    if (!c.campaign_id) continue;
    map.set(c.campaign_id, { kind: 'candidate', securityIds: new Set(c.security_ids ?? []) });
  }
  return map;
})();

const REGISTERED_SECURITIES: Set<string> = (() => {
  const raw = exportJson as unknown as { securities?: ExportSecurityLike[] };
  const set = new Set<string>();
  for (const s of raw.securities ?? []) if (s.security_id) set.add(s.security_id);
  return set;
})();

/** 该对象是否在 canonical export 中（Campaign / Research Candidate） */
export function isExportObject(objectId: string): boolean {
  return OBJECT_INDEX.has(objectId);
}

/** 该对象在 export 中登记的 `security_ids`（对象不存在时返回 `null`，不猜） */
export function objectSecurityIds(objectId: string): ReadonlySet<string> | null {
  return OBJECT_INDEX.get(objectId)?.securityIds ?? null;
}

/** 该证券是否在 canonical export 的证券注册表中 */
export function isRegisteredSecurity(securityId: string): boolean {
  return REGISTERED_SECURITIES.has(securityId);
}

/** 从事件解析关联对象 id（`object_id` 优先，兼容旧 `campaign_id`） */
export function eventObjectId(event: HistoricalEvent): string | null {
  const cf = event.campaign_facts;
  if (!cf) return null;
  return cf.object_id ?? cf.campaign_id ?? null;
}

/* ------------------------------------------------------ 对账 */

/**
 * ★★ 单个标的的对账（纯函数、确定性）。
 *
 * 判定顺序：
 *  1. 无关联对象 id → `UNRESOLVED`（原因：事件未记录关联对象）
 *  2. 对象不在 export → `UNRESOLVED`（原因：关联对象不存在）
 *  3. 证券在对象的 `security_ids` 中 → `OBJECT_REGISTERED`
 *  4. 否则证券在全局注册表 → `MAP_SUPPLEMENT`
 *  5. 否则 → `UNRESOLVED`（原因：证券不在注册表 / 对象 security_ids 不可解析）
 */
export function reconciliationOf(
  event: HistoricalEvent, securityId: string,
): ObjectSecurityReconciliation {
  const objectId = eventObjectId(event);
  const entry = objectId ? OBJECT_INDEX.get(objectId) ?? null : null;
  const objectFound = entry !== null;
  const securityRegistered = REGISTERED_SECURITIES.has(securityId);
  const inObjectSecurityIds = entry ? entry.securityIds.has(securityId) : false;
  const objectKind = entry?.kind ?? null;

  const base = {
    objectId, objectKind, objectFound, securityRegistered, inObjectSecurityIds,
  };

  if (!objectId) {
    return {
      ...base, link: 'NO_OBJECT_REFERENCE',
      reason: '事件**未记录关联对象**（`campaign_facts` 缺失或未填 `object_id` / `campaign_id`）'
        + '→ 当前**无法做对象级对账**；★ 这不表示该证券不存在、也不表示它应属于某个 Campaign',
    };
  }
  if (!objectFound) {
    return {
      ...base, link: 'UNRESOLVED',
      reason: `关联对象 \`${objectId}\` 不在 canonical export 的 Campaign / Research Candidate 中 → 无法核对`
        + (securityRegistered ? '' : `；且证券 \`${securityId}\` 不在全局注册表中`),
    };
  }
  if (inObjectSecurityIds) {
    return {
      ...base, link: 'OBJECT_REGISTERED',
      reason: `证券 \`${securityId}\` 在关联对象 \`${objectId}\` 的 \`security_ids\` 中`,
    };
  }
  if (securityRegistered) {
    return {
      ...base, link: 'MAP_SUPPLEMENT',
      reason: `证券 \`${securityId}\` 在全局注册表中，但**不在**关联对象 \`${objectId}\` 的 \`security_ids\` 中 —— Product 地图补充关联，不自动视为错误`,
    };
  }
  return {
    ...base, link: 'UNRESOLVED',
    reason: `证券 \`${securityId}\` 不在全局注册表中，且也不在关联对象 \`${objectId}\` 的 \`security_ids\` 中 → 无法核对`,
  };
}

export interface EventReconciliation {
  objectId: string | null;
  objectKind: 'campaign' | 'candidate' | null;
  objectFound: boolean;
  /** 逐标的：`securityId → 对账结果` */
  bySecurity: Map<string, ObjectSecurityReconciliation>;
  counts: Record<ReconLink, number>;
}

/** ★★ 单个事件的逐标的对账（供事件详情 / 标的索引共用，避免两处各自判定） */
export function eventReconciliation(event: HistoricalEvent): EventReconciliation {
  const bySecurity = new Map<string, ObjectSecurityReconciliation>();
  const counts: Record<ReconLink, number> = {
    OBJECT_REGISTERED: 0, MAP_SUPPLEMENT: 0, NO_OBJECT_REFERENCE: 0, UNRESOLVED: 0,
  };
  for (const p of event.participants ?? []) {
    const r = reconciliationOf(event, p.security_id);
    bySecurity.set(p.security_id, r);
    counts[r.link] += 1;
  }
  const objectId = eventObjectId(event);
  const entry = objectId ? OBJECT_INDEX.get(objectId) ?? null : null;
  return {
    objectId,
    objectKind: entry?.kind ?? null,
    objectFound: entry !== null,
    bySecurity,
    counts,
  };
}

/** ★★ 整个题材文档的对账汇总（供索引头部 / 报表共用） */
export function themeReconciliation(doc: HistoricalEventsDoc): Record<ReconLink, number> {
  const totals: Record<ReconLink, number> = {
    OBJECT_REGISTERED: 0, MAP_SUPPLEMENT: 0, NO_OBJECT_REFERENCE: 0, UNRESOLVED: 0,
  };
  for (const e of doc.events ?? []) {
    for (const p of e.participants ?? []) {
      totals[reconciliationOf(e, p.security_id).link] += 1;
    }
  }
  return totals;
}
