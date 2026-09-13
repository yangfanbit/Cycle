/**
 * Timeline 数据视图模型（Adapter 层）——不是正式数据 schema。
 *
 * 边界（见 docs/ARCHITECTURE.md / AGENTS.md）：
 * - 本层的类型只服务时间轴渲染，不落库、不替代 src/models/ 的核心模型
 *   （HistoricalCampaign / Theme / CampaignSecurity 等保持不变）。
 * - 未来 Cycle-Research 数据从 preview → provisional → verified 演进时，
 *   只改 Adapter 实现，不改 Timeline UI。
 */

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

/** Timeline 行情视图对象：由 Adapter 从 verified 生产数据或 Research 预览数据映射 */
export interface TimelineCampaign {
  campaign_id: string;
  rule_id: string;
  season_id: string;
  year: number;
  /** 显示标题，如「汽车 · 智能驾驶」 */
  title: string;
  start: string;
  end: string;
  peak?: string | null;
  cross_year: boolean;
  status: TimelineDataStatus;
  /** status = conflict 时的分歧说明（不得被描述成历史事实） */
  conflicts?: string[];
  early_signal?: TimelineEarlySignal | null;
  /** 生命周期分段（start → end 内部，按序覆盖不留空隙） */
  phases: TimelinePhaseSegment[];
  themes: { id?: string; name: string; role?: string }[];
  securities: { name: string; role?: string }[];
  description?: string;
  /** 来源说明（生产数据来自 Source 注册表；预览数据来自 Research） */
  sourceNote?: string;
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
  events: TimelineEventPoint[];
}

/**
 * 时间轴数据源：Timeline UI 只面对本接口。
 * kind = 'verified'：生产数据（data/verified，经 src/data barrel 聚合）；
 * kind = 'preview'：Cycle-Research 导出预览（本地 fixture / 导入文件，非正式历史事实）。
 */
export interface TimelineDataSource {
  kind: 'verified' | 'preview';
  /** 数据源可展示的年份（UI 不硬编码年份） */
  years(): number[];
  yearData(year: number): TimelineYearData;
}

/* ---------------- timeline_export_v1 兼容格式 ---------------- */

/** Cycle-Research 导出的单条研究行情（timeline_export_v1.json 兼容） */
export interface ExportCampaignV1 {
  campaign_id: string;
  rule_id: string;
  year: number;
  season_id: string;
  title: string;
  themes: { name: string; role?: string }[];
  start_date: string;
  peak_date?: string | null;
  end_date: string;
  early_signal?: { start_date: string; end_date: string; label?: string } | null;
  /** 高位回撤起点；缺省时 Adapter 以 peak → end 中点近似分段 */
  retracement_start?: string | null;
  securities?: { name: string; role?: string }[];
  description?: string;
  research_status?: 'preview' | 'provisional' | 'conflict';
  conflicts?: string[];
  notes?: string;
}

/** timeline_export_v1.json 顶层结构（Cycle-Research 导出） */
export interface TimelineExportV1 {
  export_version: '1';
  generated_at: string;
  source_project: string;
  campaigns: ExportCampaignV1[];
}
