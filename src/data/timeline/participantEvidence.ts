/**
 * 参与者**证据维度**（产品侧读取器）—— v0.28。
 *
 * ## 为什么单独一层
 *
 * 历史地图里每只股票身上混着**四种不同性质**的信息，此前只能从自由文本读出来：
 *
 * | 维度 | 回答的问题 | 不能推出什么 |
 * |---|---|---|
 * | `market_participation` | 同期报道能证明它**参与过**当次行情吗？ | 不能推出它的业务与题材机制有关 |
 * | `mechanism_relation` | 它的业务与**题材机制**有关吗？ | **不能**推出它驱动了当次行情 |
 * | `registry_role` | 它在 **Research 对象**里被登记成什么角色？ | **不能**推出它是「当时的龙头」 |
 * | `study_standing` | 它是纳入 / 反例 / 证据不足？ | 不能与上面三者混成一类 |
 *
 * 数据来自 `research/current/participant_evidence_v0_1.json`（确定性生成器
 * `build_participant_evidence_v0_1.py`，`--check` 为 CI 门禁）。★ 本模块**只做读取与文案**，
 * 不重新推导任何维度 —— 单一真相在产物里。
 */

// ★ v0.30：v0_3 —— 报道**发布日**与**事实日期**分开；新增 `UNVERIFIED_REPORT_ATTRIBUTION`
import raw from '@current/participant_evidence_v0_3.json';

export type MarketParticipationStatus =
  | 'REPORT_CONFIRMED_LIMIT_UP'
  | 'REPORT_CONFIRMED_GAIN'
  | 'REPORT_CONFIRMED_WINDOW_GAIN'
  | 'REPORT_CONFIRMED_NAMED'
  | 'RESEARCH_OR_DB_ONLY'
  | 'NOT_RECORDED'
  | 'UNKNOWN'
  /** ★ v0.30：来源指向报道，但**无法把任何一篇报道与该股的涨跌事实对上**（或发布日不可确定） */
  | 'UNVERIFIED_REPORT_ATTRIBUTION';

/** ★ v0.29：来源类型 —— 决定「报道点名」这句话能不能说 */
export type SourceKind =
  | 'REPORT_WITH_URL'
  | 'REPORT_NAMED_NO_URL'
  | 'DB_OR_RESEARCH_ONLY'
  | 'NOT_RECORDED'
  | 'UNKNOWN_SOURCE';

export type MechanismRelationStatus =
  | 'DIRECT_CONFIRMED'
  | 'INDIRECT_CONFIRMED'
  | 'BUSINESS_DESCRIBED_UNCONFIRMED'
  | 'NOT_STUDIED'
  | 'DIFFERENT_AXIS'
  | 'UNKNOWN';

export type RegistryVerification =
  | 'VERIFIED_DB'
  | 'SECURITY_IN_OBJECT_ROLE_UNVERIFIED'
  | 'SECURITY_NOT_IN_OBJECT'
  | 'ROLE_MISMATCH'
  | 'UNSOURCED';

export type StudyStanding = 'INCLUDED' | 'COUNTER_EXAMPLE' | 'INSUFFICIENT' | 'UNKNOWN';

export interface MarketParticipation {
  status: MarketParticipationStatus;
  /** ★ 来源类型：`DB_OR_RESEARCH_ONLY` 时**不得**说「报道点名」 */
  source_kind: SourceKind;
  source_text?: string | null;
  reported_move?: string | null;
  basis: string;
  /** ★ v0.30：报道背书来自哪里（参与者自己的来源 / 事件催化剂） */
  source_kind_from?: 'PARTICIPANT_SOURCE' | 'EVENT_CATALYST';
  /** ★ v0.30：关联级别 —— 正文点名 / 多股汇总 */
  attribution?: 'NAME_IN_TEXT' | 'REPORT_LIST_AGGREGATE' | null;
  /**
   * 同期报道的可追溯出处。
   * ★★ v0.30：`published_at` 是**报道发布日**，`fact_date` 是**事实日期**（盘面/采访日）。
   * 两者不得混用；`identified_date` 只能取 `published_at`。
   */
  report?: {
    published_at?: string | null;
    published_at_source?: string | null;
    fact_date?: string | null;
    publisher?: string | null;
    text?: string | null;
    url?: string | null;
    attribution?: string | null;
  } | null;
  /** ★ PIT 可识别日（= published_at；不可确定 → 不出现） */
  identified_date?: string | null;
}

export interface MechanismRelation {
  status: MechanismRelationStatus;
  basis: string;
  caveat?: string | null;
}

export interface RegistryRole {
  role: string;
  object_id: string | null;
  object_kind: string | null;
  verification: RegistryVerification;
  source: string;
}

export interface ParticipantUnknown {
  field: string;
  reason: string;
}

export interface ParticipantEvidence {
  name?: string | null;
  ticker?: string | null;
  evidence_level?: string | null;
  study_standing: StudyStanding;
  market_participation: MarketParticipation;
  mechanism_relation: MechanismRelation;
  registry_role: RegistryRole | null;
  source_text?: string | null;
  unknowns: ParticipantUnknown[];
}

interface EvidenceDoc {
  artifact: string;
  artifact_version: string;
  participant_evidence_contract: { version: string; [k: string]: unknown };
  summary: Record<string, unknown>;
  events: Record<string, {
    theme_id: string;
    object_id: string | null;
    object_kind: string | null;
    participants: Record<string, ParticipantEvidence>;
  }>;
}

const doc = raw as unknown as EvidenceDoc;

export const PARTICIPANT_EVIDENCE_ARTIFACT = doc.artifact_version;
export const PARTICIPANT_EVIDENCE_CONTRACT = doc.participant_evidence_contract.version;
export const participantEvidenceSummary = () => doc.summary;

/** 单条参与者证据；不存在 → null（**不猜**） */
export function participantEvidenceOf(
  eventId: string, securityId: string,
): ParticipantEvidence | null {
  return doc.events[eventId]?.participants?.[securityId] ?? null;
}

/** 事件级：参与者的证据维度（缺失 → 空对象，调用方据此走「未登记」分支） */
export function eventParticipantEvidence(eventId: string): Record<string, ParticipantEvidence> {
  return doc.events[eventId]?.participants ?? {};
}

// ---------------------------------------------------------------- 文案

/** ★ 同期市场表现：说的是**报道证明了什么**，不是「它涨了多少」 */
export const MARKET_PARTICIPATION_LABEL: Record<MarketParticipationStatus, string> = {
  REPORT_CONFIRMED_LIMIT_UP: '报道涨停',
  REPORT_CONFIRMED_GAIN: '报道涨幅',
  REPORT_CONFIRMED_WINDOW_GAIN: '报道区间涨幅',
  REPORT_CONFIRMED_NAMED: '报道点名',
  RESEARCH_OR_DB_ONLY: '仅库内/研究记录',
  NOT_RECORDED: '无来源记录',
  UNKNOWN: '来源未归类',
  UNVERIFIED_REPORT_ATTRIBUTION: '报道未对上该股',
};

/** 来源类型的展示文案（与「报道点名」是否成立直接相关） */
export const SOURCE_KIND_LABEL: Record<SourceKind, string> = {
  REPORT_WITH_URL: '同期报道（有链接）',
  REPORT_NAMED_NO_URL: '同期报道（无链接）',
  DB_OR_RESEARCH_ONLY: '仅数据库/研究记录',
  NOT_RECORDED: '无来源记录',
  UNKNOWN_SOURCE: '来源未归类',
};

/** ★ 机制关系：业务与题材机制的关系，**不**代表驱动了行情 */
export const MECHANISM_RELATION_LABEL: Record<MechanismRelationStatus, string> = {
  DIRECT_CONFIRMED: '直接机制',
  INDIRECT_CONFIRMED: '间接/扩散',
  BUSINESS_DESCRIBED_UNCONFIRMED: '业务相关·未定级',
  NOT_STUDIED: '机制未研究',
  DIFFERENT_AXIS: '不同机制轴',
  UNKNOWN: '机制未知',
};

/** ★ 对象登记角色：**Research 对象内部**的角色，不是历史炒作龙头 */
export const REGISTRY_ROLE_LABEL: Record<string, string> = {
  leader: '登记 leader',
  second_leader: '登记 second_leader',
  representative: '登记 representative',
  follow: '登记 follow',
};

export const REGISTRY_VERIFICATION_LABEL: Record<RegistryVerification, string> = {
  VERIFIED_DB: '库内可核',
  SECURITY_IN_OBJECT_ROLE_UNVERIFIED: '仅文档登记',
  SECURITY_NOT_IN_OBJECT: '对象内无登记',
  ROLE_MISMATCH: '与库不一致',
  UNSOURCED: '来源缺失',
};

export const STUDY_STANDING_LABEL: Record<StudyStanding, string> = {
  INCLUDED: '纳入',
  COUNTER_EXAMPLE: '反例',
  INSUFFICIENT: '证据不足',
  UNKNOWN: '未判定',
};

/**
 * ★★ 最容易被误读的一处：有 `registry_role` 时，用户很容易把它读成「当时的龙头」。
 * 这里给出**必须同时显示**的限定语；没有角色 → 返回 null（不显示空话）。
 */
export function registryRoleCaveat(ev: ParticipantEvidence | null): string | null {
  const rr = ev?.registry_role;
  if (!rr) return null;
  const mp = ev!.market_participation.status;
  const st = ev!.study_standing;
  const mr = ev!.mechanism_relation.status;
  // ★★ 最容易被读错的一种：**对象登记 leader + 本题材机制轴属反例**（如大众交通）。
  //   两者并不矛盾：leader 说的是「它在当次行情里涨得最猛」，反例说的是「它的业务不在本题材机制轴上」。
  if ((rr.role === 'leader' || rr.role === 'second_leader')
      && (st === 'COUNTER_EXAMPLE' || mr === 'DIFFERENT_AXIS')) {
    return '★ 两条**互不取消**的事实同时成立：① Research 对象把它登记为 '
      + `${rr.role}（按当次行情表现）；② 在本题材的**机制轴**上它是**反例**`
      + '（业务与该机制不同轴）。★ 因此：**不能**用它的涨幅证明机制成立，'
      + '**也不能**因为它是反例就说它当时没涨。';
  }
  if (rr.role === 'leader' || rr.role === 'second_leader') {
    if (mp === 'REPORT_CONFIRMED_LIMIT_UP' || mp === 'REPORT_CONFIRMED_GAIN'
      || mp === 'REPORT_CONFIRMED_WINDOW_GAIN') {
      return '★ 该角色来自 Research 对象登记；同期报道也点名了它，但报道**未**称其为「龙头」——'
        + '「登记 leader」≠「当时公认的龙头」。';
    }
    return '★ 该角色来自 Research 对象登记，**本库无同期报道背书**——'
      + '不能据此认定它是当时的龙头或行情驱动者。';
  }
  return '★ 该角色来自 Research 对象登记，不是历史市场角色的认定。';
}

/** 该参与者在同期报道层面的**最强**证据是否足以支持「参与过」 */
export function hasReportedParticipation(ev: ParticipantEvidence | null): boolean {
  const s = ev?.market_participation.status;
  return s === 'REPORT_CONFIRMED_LIMIT_UP' || s === 'REPORT_CONFIRMED_GAIN'
    || s === 'REPORT_CONFIRMED_WINDOW_GAIN' || s === 'REPORT_CONFIRMED_NAMED';
}

/** 同期报道**可追溯**（有 URL）—— 比「有报道」更严一档 */
export function hasTraceableReport(ev: ParticipantEvidence | null): boolean {
  return ev?.market_participation.source_kind === 'REPORT_WITH_URL';
}

/** 事件级统计：报道点名数 / 有机制说明数 / 有对象登记角色数（页面可核对口径） */
export function evidenceCounts(eventId: string) {
  const all = Object.values(eventParticipantEvidence(eventId));
  return {
    total: all.length,
    reported: all.filter(hasReportedParticipation).length,
    limitUp: all.filter((x) => x.market_participation.status === 'REPORT_CONFIRMED_LIMIT_UP').length,
    traceable: all.filter(hasTraceableReport).length,
    /** ★ 机制**已确认**（直接 / 间接）—— 不含「有业务说明但未定级」 */
    mechanism: all.filter((x) => x.mechanism_relation.status === 'DIRECT_CONFIRMED'
      || x.mechanism_relation.status === 'INDIRECT_CONFIRMED').length,
    /** ★ v0.29.1：有业务说明但研究**未**确认与本题材机制的关系（≠ 机制相关） */
    businessOnly: all.filter((x) =>
      x.mechanism_relation.status === 'BUSINESS_DESCRIBED_UNCONFIRMED').length,
    registry: all.filter((x) => x.registry_role).length,
    registryVerified: all.filter((x) => x.registry_role?.verification === 'VERIFIED_DB').length,
  };
}
