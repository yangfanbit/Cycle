/**
 * 历史**市场角色**（Point-in-Time）—— 产品侧读取器（v0.29）。
 *
 * ## 与其它维度的区别（不得混为一谈）
 *
 * | 维度 | 回答 | 来源 |
 * |---|---|---|
 * | `market_participation` | 同期报道能证明什么 | participant_evidence_v0_2 |
 * | `mechanism_relation` | 业务与题材机制的关系 | 同上 |
 * | `registry_role` | Research 对象内部登记 | 同上（库内可核） |
 * | **`historical_market_role`** | **当时那个时点，谁是可识别的市场核心** | 本模块 |
 *
 * ★ 本库**没有任何**同期材料明确称某股为「龙头」→ `PIT_MEDIA_NAMED_LEADER` 目前 0 条。
 *   页面不得把「报道涨停」显示成「龙头」。
 * ★ `POSTHOC_LEADER_SET` 是**后验**结论（含幸存者偏差），必须单独呈现并标注。
 */

// ★ v0.30：v0_2 —— 新增 `DERIVED_FROM_MARKET`（盘面连板）、切片 `match_scope` 三态、
//   身份绑定冲突（ID_CONFLICT_NAME_MISMATCH / registry_name_conflict）
import raw from '@current/historical_market_roles_v0_2.json';

export type MarketRoleType =
  | 'PIT_MEDIA_NAMED_LEADER'
  | 'PIT_MEDIA_NAMED_MOVER'
  | 'PIT_MARKET_OBSERVED'
  | 'POSTHOC_LEADER_SET'
  | 'INSUFFICIENT';

export type ResearchStatus =
  | 'RESEARCHED_PIT'
  | 'DERIVED_FROM_REPORT'
  /** ★ v0.30：只有盘面可观察信息（窗口内 ≥2 次涨停且至少一次连板），**无媒体定性** */
  | 'DERIVED_FROM_MARKET'
  | 'NOT_RESEARCHED';

export interface RoleEvidence {
  source_type?: string | null;
  source_text?: string | null;
  url?: string | null;
  /** ★ 报道发布日（媒体角色）或首次连板日（盘面角色）—— 与 `fact_date` 严格区分 */
  published_at?: string | null;
  /** ★ 事实日期（盘面/采访日）—— **不得**当作识别日 */
  fact_date?: string | null;
  attribution?: string | null;
  summary?: string | null;
  /** ★ 盘面角色的涨停日明细（判据可复核） */
  limit_up_days?: { date: string; pct: number }[] | null;
  rule?: string | null;
}

export interface RoleBinding {
  bound_to: string | null;
  /** ★ v0.30：`ID_CONFLICT_NAME_MISMATCH` = ID 相同但名称不一致 → **不绑定**，等人工确认 */
  status: 'BOUND' | 'BOUND_BY_NAME' | 'UNBOUND' | 'AMBIGUOUS' | 'ID_CONFLICT_NAME_MISMATCH';
  method: string;
  note?: string | null;
  /** ★ 名称绑定没有证明力 → 标 NAME_MATCH_ONLY，需人工确认 */
  review?: string | null;
  /** ★ v0.30：该 id 在注册表里指向**另一家公司**（如 JINJIANG = 锦江酒店） */
  registry_name_conflict?: { registry_name: string; registry_ticker?: string | null } | null;
}

export interface MarketRole {
  /** 地图参与者 id；**未绑定**时为 null（不强行挂靠） */
  security_id: string | null;
  /** 原始来源（PIT CSV / 参与者列表）里的 id —— 与 security_id 可能不同 */
  source_security_id?: string | null;
  binding?: RoleBinding | null;
  name?: string | null;
  role: MarketRoleType;
  identified_date: string;
  identification_type?: string | null;
  confidence?: string | null;
  evidence: RoleEvidence;
  pit_safe: boolean;
  posthoc: boolean;
  notes?: string | null;
  source_record?: string | null;
}

export type SliceMatchScope = 'FULL' | 'SUBSET' | 'MISMATCH';

export interface PitSlice {
  date: string;
  members: string[];
  basket_status: 'USABLE' | 'NOT_USABLE';
  documented_members: string[];
  documented_status: string;
  /** ★★ 三态：FULL 完全一致 / SUBSET 地图只覆盖一部分 / MISMATCH 真不一致 */
  match_scope: SliceMatchScope;
  /** ★ 只有 FULL 才为真 —— 不得用子集匹配冒充完全一致 */
  matches_document: boolean;
  documented_count?: number;
  bound_count?: number;
  /** ★ 原始篮子中**不在本地图**的成员（覆盖缺口，不是不一致） */
  not_in_map?: string[];
  not_in_map_names?: string[];
  note?: string | null;
}

export interface PosthocSet {
  basis: string;
  members: string[];
  posthoc: boolean;
  pit_safe: boolean;
  survivorship_note: string;
}

export interface EventRoles {
  theme_id: string;
  object_id: string | null;
  window: [string, string] | null;
  research_status: ResearchStatus;
  source_records: string[];
  roles: MarketRole[];
  pit_slices: PitSlice[];
  posthoc_leader_set: PosthocSet | null;
  coverage: { participants: number; report_backed_participants: number; pit_roles: number };
  gaps: string[];
}

interface RolesDoc {
  artifact: string;
  artifact_version: string;
  historical_market_roles_contract: { version: string; [k: string]: unknown };
  summary: Record<string, unknown>;
  events: Record<string, EventRoles>;
}

const doc = raw as unknown as RolesDoc;

export const MARKET_ROLES_ARTIFACT = doc.artifact_version;
export const MARKET_ROLES_CONTRACT = doc.historical_market_roles_contract.version;
export const marketRolesSummary = () => doc.summary;

export function eventRoles(eventId: string): EventRoles | null {
  return doc.events[eventId] ?? null;
}

/** 某只股票在该事件里的历史市场角色（可能不存在 —— 不猜） */
export function marketRoleOf(eventId: string, securityId: string): MarketRole | null {
  return doc.events[eventId]?.roles?.find((r) => r.security_id === securityId) ?? null;
}

/** 未绑定到地图参与者的角色（覆盖缺口）—— 单独展示，不挂到任何行上 */
export function unboundRoles(eventId: string): MarketRole[] {
  return (doc.events[eventId]?.roles ?? []).filter((r) => !r.security_id);
}

export const MARKET_ROLE_LABEL: Record<MarketRoleType, string> = {
  PIT_MEDIA_NAMED_LEADER: '报道称龙头',
  PIT_MEDIA_NAMED_MOVER: '报道点名（有涨幅）',
  PIT_MARKET_OBSERVED: '盘面异动',
  POSTHOC_LEADER_SET: '事后龙头集合',
  INSUFFICIENT: '证据不足',
};

/** ★ 每个角色都必须带「这句话意味着什么 / 不意味着什么」 */
export const MARKET_ROLE_MEANING: Record<MarketRoleType, string> = {
  PIT_MEDIA_NAMED_LEADER: '同期报道**明确**称其为龙头 / 领涨 / 核心。当前库内无此类记录。',
  PIT_MEDIA_NAMED_MOVER: '同期报道点名并给出涨停 / 涨幅 —— 可证明「被报道点名」，'
    + '**不等于**报道称其为龙头。',
  PIT_MARKET_OBSERVED: '只有当日盘面可观察异动（放量 / 涨停 / 连板），无媒体报道定性 —— '
    + '属**盘面推断**，不是媒体认定。',
  POSTHOC_LEADER_SET: '**行情结束后**回看总结的集合，含幸存者偏差 —— '
    + '**不得**用来证明当时已能识别同样的股票池。',
  INSUFFICIENT: '有研究但证据不足以判定角色。',
};

export const RESEARCH_STATUS_LABEL: Record<ResearchStatus, string> = {
  RESEARCHED_PIT: '已做 Point-in-Time 研究',
  DERIVED_FROM_REPORT: '由同期报道推导（未做完整 PIT 切片）',
  DERIVED_FROM_MARKET: '仅由盘面连板推导（无媒体报道）',
  NOT_RESEARCHED: '尚未研究',
};

/** ★ 切片匹配范围文案（FULL / SUBSET / MISMATCH） */
export const SLICE_SCOPE_LABEL: Record<SliceMatchScope, string> = {
  FULL: '与原始研究完全一致',
  SUBSET: '地图只覆盖其中一部分',
  MISMATCH: '与原始研究不一致',
};

/** 该事件是否有可展示的角色证据 */
export function hasRoleEvidence(eventId: string): boolean {
  const e = eventRoles(eventId);
  return !!e && (e.roles.length > 0 || !!e.posthoc_leader_set);
}

/** 事件级角色统计（页面可核对口径） */
export function roleCounts(eventId: string) {
  const e = eventRoles(eventId);
  if (!e) return { pit: 0, media: 0, observed: 0, posthoc: 0, leaderNamed: 0 };
  return {
    pit: e.roles.length,
    media: e.roles.filter((r) => r.role === 'PIT_MEDIA_NAMED_MOVER').length,
    observed: e.roles.filter((r) => r.role === 'PIT_MARKET_OBSERVED').length,
    posthoc: e.posthoc_leader_set?.members.length ?? 0,
    unbound: e.roles.filter((r) => !r.security_id).length,
    leaderNamed: e.roles.filter((r) => r.role === 'PIT_MEDIA_NAMED_LEADER').length,
  };
}
