/**
 * Timeline 数据视图模型（Adapter 层）——不是正式数据 schema。
 *
 * 边界（见 docs/ARCHITECTURE.md / AGENTS.md）：
 * - 本层的类型只服务时间轴渲染，不落库、不替代 src/models/ 的核心模型
 *   （HistoricalCampaign / Theme / Security 等保持不变）。
 * - timeline_export_v1 类型与 Cycle-Research canonical Contract 对齐
 *   （research/methodology/timeline_export_contract_v1.md，commit 4bbe257 冻结版）。
 *   Cycle 只消费、不修改该 JSON；所有结构变更回 Research 项目完成。
 * - Research-only 字段（research_status / theme_cycle_id / promotion_status /
 *   first_signal_date 等）是 research metadata，不伪装成 HistoricalCampaign 正式字段。
 */

/* ---------------- 视图层：数据状态 / 生命周期 ---------------- */

/** 数据状态：verified 已核验 / provisional 初步核验 / preview 研究预览 / conflict 研究存在分歧 */
export type TimelineDataStatus = 'verified' | 'provisional' | 'preview' | 'conflict';

/**
 * Campaign 生命周期阶段（视图表达）：
 * Early Signal → Main Rise → Peak → Retracement → Declining → Ended。
 * 仅靠形状 / 线型 / 透明度 / 标签区分，不单靠颜色（避免色盲不可分辨）。
 */
export type LifecyclePhase = 'early_signal' | 'main_rise' | 'peak' | 'retracement' | 'declining' | 'ended';

export interface TimelinePhaseSegment {
  phase: Exclude<LifecyclePhase, 'peak' | 'ended'>;
  start: string; // ISO
  end: string; // ISO
}

/** Campaign 主升前的早期信号（较淡显示，不得呈现为正式 Campaign） */
export interface TimelineEarlySignal {
  start: string;
  end: string;
  label?: string;
}

/* ---------------- timeline_export_v1 canonical Contract（v1.0） ---------------- */

/** 研究层状态（research metadata，大写枚举） */
export type ExportResearchStatus = 'PROVISIONAL' | 'CONFLICT' | 'INSUFFICIENT' | 'VERIFIED';

/** 生产兼容状态（Cycle 消费，小写枚举） */
export type ExportProductionStatus = 'verified' | 'provisional' | 'conflict' | 'preview';

export type ExportSignalType = 'EARLY_SIGNAL' | 'THEME_FORMING' | 'CONFIRMATION_CANDIDATE';
export type ExportSignalConfidence = 'low' | 'medium' | 'high';

export interface ExportRuleV1 {
  rule_id: string;
  name?: string | null;
  base_pattern?: string | null;
  definition?: string | null;
  observation_window?: string | null;
}

export interface ExportThemeV1 {
  name: string;
  theme_type?: string | null;
  role?: string | null;
}

/**
 * 研究信号（扁平数组）。归属：campaign_id XOR research_candidate_id（二选一）。
 * Research Signal 是"值得观察"的研究层信息，不是交易信号。
 * 注：导出中未归属的一侧字段可以缺省（如仅含 campaign_id 的信号没有 research_candidate_id 键）。
 */
export interface ExportSignalV1 {
  type: ExportSignalType;
  date: string;
  confidence: ExportSignalConfidence;
  campaign_id?: string | null;
  research_candidate_id?: string | null;
}

/** 日期口径分歧：保留 candidate A / B 双方，不自行选一个 */
export interface ExportConflictSideV1 {
  date: string;
  label: string;
}

export interface ExportConflictV1 {
  field: string;
  candidate_a: ExportConflictSideV1;
  candidate_b: ExportConflictSideV1;
}

/**
 * Research V1.7 生命周期阶段（campaigns / research_candidates 可选新增字段）。
 * stage 为研究层枚举（EARLY_SIGNAL / THEME_FORMING / BROAD_CONFIRMATION / MAIN_RISE /
 * PEAK / SECONDARY / FIRST_DECLINE / RETRACEMENT / DECLINING / MAIN_END 等）；
 * precision 区分 EXACT_DATE（单日）与 DATE_WINDOW / PHASE_WINDOW（区间）。
 */
export interface ExportLifecycleStageV1 {
  stage: string;
  start: string;
  end: string;
  precision: string;
}

/**
 * Research V1.7 驱动因素归因（四问；keys：start / accelerator / turning / ending）。
 * 研究层人工归因，非因果结论；数组可空（研究未归因时不编造）。
 */
export interface ExportDriversV1 {
  start: string[];
  accelerator: string[];
  turning: string[];
  ending: string[];
}

/** 正式 HistoricalCampaign（Research 导出；不含 research candidates） */
export interface ExportCampaignV1 {
  campaign_id: string;
  rule_id: string;
  year: number;
  start_date: string;
  peak_date: string | null;
  // ★ Research Release 修正：`end_date` 可为 null —— R01 的 Peak/End 四态允许 end 无法确定
  //   （与 `ExportResearchCandidateV1.end_date: string | null` 口径一致）
  end_date: string | null;
  status: ExportProductionStatus;
  confidence?: string | null;
  classification?: string | null;
  strength?: string | null;
  result?: string | null;
  themes: ExportThemeV1[];
  event_ids: string[];
  security_ids: string[];
  research_status: ExportResearchStatus;
  theme_cycle_id?: string | null;
  promotion_status?: string | null;
  first_signal_date?: string | null;
  broad_confirmation_date?: string | null;
  first_decline_date?: string | null;
  conflicts: ExportConflictV1[];
  notes?: string | null;
  /** Research V1.7 新增：生命周期阶段（可选；旧导出无此字段） */
  lifecycle?: ExportLifecycleStageV1[];
  /** Research V1.7 新增：驱动因素四问归因（可选；旧导出无此字段） */
  drivers?: ExportDriversV1;
}

/**
 * Research Candidate（未达正式 Campaign 门槛的候选；RC- 前缀）。
 * 没有生产 `status` 字段，只有 research_status；不得伪装 verified。
 */
export interface ExportCandidateV1 {
  campaign_id: string;
  rule_id: string;
  year: number;
  title: string;
  // ★ Research Release 修正：`start_date` 也可为 null（起始未确定）
  start_date: string | null;
  peak_date: string | null;
  end_date: string | null;
  themes: ExportThemeV1[];
  event_ids: string[];
  security_ids: string[];
  early_signal: string | null;
  research_status: ExportResearchStatus;
  theme_cycle_id?: string | null;
  conflicts: ExportConflictV1[];
  notes?: string | null;
  /** Research V1.7 新增：生命周期阶段（可选；旧导出无此字段） */
  lifecycle?: ExportLifecycleStageV1[];
  /** Research V1.7 新增：驱动因素四问归因（可选；旧导出无此字段） */
  drivers?: ExportDriversV1;
}

/** 事件（顶层扁平数组；Campaign 经 event_ids 引用，不要求嵌套在 Campaign 内） */
export interface ExportEventV1 {
  event_id: string;
  name: string;
  date: string;
  event_type: string;
  role: string | null;
  campaign_id: string | null;
  research_candidate_id: string | null;
}

/** 证券（顶层扁平数组；每 (security_id, owner) 一条，禁止无归属） */
export interface ExportSecurityV1 {
  security_id: string;
  name: string;
  ticker: string;
  exchange: string;
  role: string;
  campaign_id: string | null;
  research_candidate_id: string | null;
}

/** timeline_export_v1.json 顶层结构（canonical，11 字段白名单） */
export interface TimelineExportV1 {
  contract: 'timeline_export';
  timeline_export_version: '1.0';
  generated_at: string;
  source_commit: string;
  project: string;
  rules: ExportRuleV1[];
  signals: ExportSignalV1[];
  campaigns: ExportCampaignV1[];
  research_candidates: ExportCandidateV1[];
  events: ExportEventV1[];
  securities: ExportSecurityV1[];
}

/* ---------------- Timeline 视图模型 ---------------- */

/**
 * Timeline 行情视图对象：由 Adapter 从 verified 生产数据或 Research 导出映射。
 * kind = 'campaign'：正式 Historical Campaign（Research Export 或 data/verified）；
 * kind = 'candidate'：Research Candidate（并列来源，非"候选→正式"升级关系；
 *   不得显示为 Historical Confirmed Campaign，永不映射为 verified）。
 */
export interface TimelineCampaign {
  campaign_id: string;
  kind: 'campaign' | 'candidate';
  rule_id: string;
  season_id: string;
  year: number;
  /** 显示标题，如「汽车 · 智能驾驶」 */
  title: string;
  start: string;
  end: string;
  /** 结束日期缺省（候选观察中）：end 为年末近似，仅渲染用 */
  openEnded?: boolean;
  peak?: string | null;
  cross_year: boolean;
  status: TimelineDataStatus;
  /** status = conflict 时的日期口径分歧（candidate A / B 双方保留） */
  conflicts?: ExportConflictV1[];
  early_signal?: TimelineEarlySignal | null;
  /** 生命周期分段（start → end 内部，按序覆盖不留空隙） */
  phases: TimelinePhaseSegment[];
  /**
   * 关联题材。`theme_type`（industry / sector / concept）为导出既有字段的**透传**
   * （契约 §11 已声明，research metadata），用于「Macro Theme → Campaign」层级推导；
   * 缺失时保持 undefined，不推断。
   */
  themes: { name: string; role?: string; theme_type?: string }[];
  /**
   * Theme Cycle（研究层归组，**research metadata 透传**）：同一 Theme Cycle 可含多个
   * Campaign / Candidate（见 methodology `theme_campaign_separation_v1.md`）。
   * 缺失时保持 undefined —— 不推断、不编造。
   */
  theme_cycle_id?: string | null;
  securities: { name: string; ticker?: string; role?: string }[];
  /** 关联事件（经 event_id → 顶层 events lookup 解析） */
  events: { name: string; date: string; event_type: string; role?: string | null }[];
  /** 研究信号（研究层信息，不是交易信号） */
  signals: { type: string; date: string; confidence?: string }[];
  /** Research V1.7 生命周期阶段（仅 Research 导出数据源提供；生产 verified 无此字段） */
  lifecycle?: ExportLifecycleStageV1[];
  /** Research V1.7 驱动因素归因（四问；仅 Research 导出数据源提供） */
  drivers?: ExportDriversV1;
  description?: string;
  /** 来源说明（生产数据来自 Source 注册表；预览数据来自 Research） */
  sourceNote?: string;
}

/** Research 导出的具体日期事件（区别于生产日历事件：单日、带归属） */
export interface TimelineResearchEvent {
  event_id: string;
  name: string;
  date: string;
  event_type: string;
  role: string | null;
  campaign_id: string | null;
  research_candidate_id: string | null;
}

export interface TimelineEventPoint {
  event_id: string;
  name: string;
  start: string;
  end: string;
  event_type: string;
  description?: string;
  approximate?: boolean;
  source?: string;
}

export interface TimelineYearData {
  year: number;
  campaigns: TimelineCampaign[];
  /** 生产日历事件（节假日 / 披露期，两个数据源共用） */
  events: TimelineEventPoint[];
  /** Research 导出的研究事件（仅 preview 数据源；生产数据源不提供） */
  researchEvents?: TimelineResearchEvent[];
}

/**
 * 时间轴数据源：Timeline UI 只面对本接口。
 * kind = 'verified'：生产数据（data/verified，经 src/data barrel 聚合）；
 * kind = 'preview'：Cycle-Research 导出预览（timeline_export_v1，非正式历史事实）。
 */
export interface TimelineDataSource {
  kind: 'verified' | 'preview';
  /** 数据源可展示的年份（UI 不硬编码年份） */
  years(): number[];
  yearData(year: number): TimelineYearData;
}
