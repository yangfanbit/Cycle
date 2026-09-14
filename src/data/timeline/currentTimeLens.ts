/**
 * Current Time Lens v0 —— 「今天这个时间点，历史上附近发生过什么？」
 *
 * 回答的问题（且仅此三问）：
 *   1. 今天处在一年的什么位置？（时间定位）
 *   2. 历史上同一时间窗口附近，出现过哪些行情 / 研究候选？（同期事实）
 *   3. 那些行情在「当时那个时间点」处于什么阶段？可能有哪些驱动 / 相关因素？（历史映射 + 可能驱动）
 *
 * 刻意不回答（超出本模块范围）：
 *   ✗ 「今年一定会发生什么」——不做预测
 *   ✗ 「现在应该买什么」——不做交易决策
 *   ✗ 「历史上出现过 N 次，所以概率是 …」——不做概率 / 频次统计
 *
 * 数据边界：
 *   - 只消费 TimelineDataSource（App 注入；来源 = exports/timeline_export_v1.json）。
 *   - 不新建数据、不联网、不加 Schema；只做视图层聚合。
 *   - 日期口径完全复用 samePeriodWindow()，不发明第二套日期逻辑。
 *   - 判断不出来时输出 Unknown /「当前研究数据未覆盖」，绝不编造。
 */

import type {
  ExportLifecycleStageV1,
  TimelineCampaign,
  TimelineDataSource,
} from './timelineTypes';
import { campaignDrivers, samePeriodCampaigns, samePeriodWindow } from './timelineAdapter';
import { timelineEntryId, type TimelineEntryId } from './entryIdentity';
import { diffDays } from '../../utils';

/* ---------------- 输出模型 ---------------- */

/** 今日在一年的位置（纯日历坐标，不代表市场状态） */
export interface LensTimePosition {
  /** ISO 日期（A股市场基准，Asia/Shanghai） */
  today: string;
  year: number;
  month: number;
  day: number;
  /** 展示用月份标签，如「9 月」 */
  monthLabel: string;
  /** 同期窗口（[m-1月15日, m+1月15日]，与 SamePeriodView 同口径） */
  window: { start: string; end: string };
  /** 展示用窗口标签，如「08-15 ~ 10-15」 */
  windowLabel: string;
}

/**
 * 单条历史同期行情的「历史阶段映射」。
 * phaseLabel 描述的是「当年这个时间窗口内它处于什么阶段」——是历史事实，
 * 不是对今天的判断，也不是该 Campaign 的当前状态。
 */
export interface LensHistoricalEntry {
  campaign_id: string;
  /**
   * 【条目唯一身份】= `${campaign_id}@${展示年份}`（跨年 Campaign 同 id 不同年份 → 不同 entryId）。
   * UI 必须用 entryId 作 React key；**不得用 campaign_id**（会重复）。见 `entryIdentity.ts`。
   */
  entryId: TimelineEntryId;
  /** 正式 Campaign 或 Research Candidate */
  kind: 'campaign' | 'candidate';
  title: string;
  /**
   * 【该条目所属的展示年份】= 年份行年份（row.year），不是 Campaign 起始年份。
   * 跨年 Campaign 会在多个年度各成一条；Campaign 自身年份见 `campaign.year`。
   */
  year: number;
  /** verified / provisional / preview / conflict */
  status: TimelineCampaign['status'];
  /** 完整历史区间（历史事实） */
  start: string;
  end: string;
  /** 是否 open-ended 候选（end 为年末近似） */
  openEnded: boolean;
  /**
   * 历史阶段标签：当年窗口内「主要」阶段（覆盖天数最多者，同长取 lifecycle 靠前）。
   * 无 lifecycle 时为 null →「阶段未标注」（不编造）。
   */
  phaseLabel: string | null;
  /**
   * 窗口内命中的其余阶段（非主要阶段），按 lifecycle 顺序——UI 以「另有…」轻量呈现。
   * 目的：保留全部历史事实，又不让阶段标签喧宾夺主。
   */
  phaseAlso: string[];
  /** 主要阶段在当年窗口内被命中的日期区间 */
  phaseHit: { start: string; end: string } | null;
  /** 可能驱动 / 相关因素（四问汇总；语义为「可能」，非因果结论；无则空数组） */
  possibleDrivers: string[];
  /** 原始 Campaign 视图对象（供 UI 经现有 selection 打开 Campaign Detail，不重复构造） */
  campaign: TimelineCampaign;
}

/** 一个年份的同期结果 */
export interface LensSamePeriodYear {
  year: number;
  /** 该年同期窗口内出现过的行情（历史事实） */
  entries: LensHistoricalEntry[];
}

/** 「可能驱动 / 相关因素」汇总项（去重后归属于某年） */
export interface LensPossibleDriver {
  year: number;
  campaign_id: string;
  title: string;
  labels: string[];
}

/** Lens 完整输出 */
export interface CurrentTimeLensResult {
  /** A. 时间定位 */
  position: LensTimePosition;
  /** B + C. 历史同期（按年份；含历史阶段映射） */
  samePeriod: LensSamePeriodYear[];
  /** 有研究数据的年份数量（不作为"N 次"概率口径，仅覆盖度提示） */
  coveredYears: number;
  /** D. 可能驱动 / 相关因素（跨年份汇总，标注为「可能」） */
  possibleDrivers: LensPossibleDriver[];
  /** 是否当前研究数据未覆盖任何同期（true → UI 输出「当前研究数据未覆盖」） */
  uncovered: boolean;
}

/* ---------------- 阶段映射 ---------------- */

/** lifecycle stage → 中文阶段标签（严格照 Research 枚举，不做语义扩写） */
const STAGE_LABEL: Record<string, string> = {
  EARLY_SIGNAL: '早期信号',
  THEME_FORMING: '主题形成',
  BROAD_CONFIRMATION: '广泛确认',
  MAIN_RISE: '主升',
  PEAK: '峰值',
  SECONDARY: '次级行情',
  FIRST_DECLINE: '首次回撤',
  RETRACEMENT: '高位回撤',
  DECLINING: '退潮',
  MAIN_END: '主段结束',
};

export function stageLabel(stage: string): string {
  return STAGE_LABEL[stage] ?? stage;
}

/** 两个 ISO 日期是否相交（闭区间） */
function overlaps(aStart: string, aEnd: string, bStart: string, bEnd: string): boolean {
  return aStart <= bEnd && aEnd >= bStart;
}

/** 区间交集；无交集返回 null */
function intersect(
  aStart: string,
  aEnd: string,
  bStart: string,
  bEnd: string,
): { start: string; end: string } | null {
  const start = aStart > bStart ? aStart : bStart;
  const end = aEnd < bEnd ? aEnd : bEnd;
  return start <= end ? { start, end } : null;
}

/**
 * 历史阶段映射：找出「当年同期窗口」内命中的 lifecycle 阶段。
 *
 * 关键语义（不得违反）：
 *   - 返回的是该 Campaign 在「历史上那个时间窗口」所处的阶段（历史事实）；
 *   - 绝不能说成「该 Campaign 当前处于某阶段」；
 *   - 一个窗口内可能命中多个阶段（如 08-15 起 SECONDARY 后接 MAIN_END），
 *     全部保留（不合并），由调用方挑选「主要阶段」并保留其余为「另有…」。
 */
export function historicalPhasesInWindow(
  campaign: Pick<TimelineCampaign, 'lifecycle'>,
  win: { start: string; end: string },
): { stage: string; label: string; hit: { start: string; end: string }; days: number }[] {
  const stages: ExportLifecycleStageV1[] = campaign.lifecycle ?? [];
  const out: { stage: string; label: string; hit: { start: string; end: string }; days: number }[] = [];
  for (const s of stages) {
    const hit = intersect(s.start, s.end, win.start, win.end);
    if (hit) {
      out.push({
        stage: s.stage,
        label: stageLabel(s.stage),
        hit,
        days: diffDays(hit.start, hit.end) + 1,
      });
    }
  }
  return out;
}

/* ---------------- 可能驱动 / 相关因素 ---------------- */

/**
 * 汇总「可能驱动 / 相关因素」。
 *
 * 严格约束：
 *   - 只做汇总与展示，不推断因果、不排序为「原因」；
 *   - 标签始终带「可能驱动 / 相关因素」前缀由 UI 呈现（数据层只给出原始标签）；
 *   - 四问中的 ending 常含「unknown（…）」这类研究层占位——原样保留（不编造）；
 *   - 去重（同一年同一 Campaign 内相同标签只出一次）。
 */
export function possibleDriversOf(campaign: TimelineCampaign): string[] {
  const d = campaignDrivers(campaign);
  const all = [...d.start, ...d.accelerate, ...d.turn, ...d.end];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const t of all) {
    const key = t.trim();
    if (key.length === 0 || seen.has(key)) continue;
    seen.add(key);
    out.push(key);
  }
  return out;
}

/* ---------------- 主函数 ---------------- */

/**
 * Current Time Lens 主函数。
 *
 * @param source TimelineDataSource（App 注入：生产 verified 或 Research preview）
 * @param today  A股市场日期基准（Asia/Shanghai），ISO 字符串
 *
 * 行为：
 *   - 以 today 的月份复用 samePeriodWindow()，逐年份查同期 Campaign/RC；
 *   - 对每条结果做历史阶段映射（当年窗口内命中哪些阶段）；
 *   - 汇总可能驱动 / 相关因素（带「可能」语义）；
 *   - 若全无覆盖 → uncovered = true（UI 输出「当前研究数据未覆盖」）。
 */
export function currentTimeLens(source: TimelineDataSource, today: string): CurrentTimeLensResult {
  const year = Number(today.slice(0, 4));
  const month = Number(today.slice(5, 7));
  const day = Number(today.slice(8, 10));
  // 复用现有窗口口径：以今天所在年份计算 [m-1月15日, m+1月15日]
  const window = samePeriodWindow(year, month);

  const position: LensTimePosition = {
    today,
    year,
    month,
    day,
    monthLabel: `${month} 月`,
    window,
    windowLabel: `${window.start.slice(5)} ~ ${window.end.slice(5)}`,
  };

  // 复用 samePeriodCampaigns（内部即 samePeriodCampaigns → samePeriodWindow，不另造日期逻辑）
  const rows = samePeriodCampaigns(source, month);

  const samePeriod: LensSamePeriodYear[] = [];
  const possibleDrivers: LensPossibleDriver[] = [];
  let coveredYears = 0;

  for (const row of rows) {
    // 每条 row 的年份窗口（samePeriodCampaigns 已按各年计算；此处仅为阶段映射复算同口径窗口）
    const win = samePeriodWindow(row.year, month);
    const entries: LensHistoricalEntry[] = row.campaigns.map((c) => {
      const hits = historicalPhasesInWindow(c, win);
      const labels = possibleDriversOf(c);
      if (labels.length > 0) {
        possibleDrivers.push({
          year: row.year,
          campaign_id: c.campaign_id,
          title: c.title,
          labels,
        });
      }
      // 主要阶段：覆盖天数最多者（同长取 lifecycle 靠前者，即 hits 中先出现者）
      let primary: (typeof hits)[number] | null = null;
      for (const h of hits) {
        if (primary === null || h.days > primary.days) primary = h;
      }
      const also = hits.filter((h) => h !== primary).map((h) => h.label);
      return {
        campaign_id: c.campaign_id,
        // 条目身份 = campaign_id@展示年份（跨年 Campaign 同 id 不同年份 → 不同 entryId）
        entryId: timelineEntryId(c.campaign_id, row.year),
        kind: c.kind,
        title: c.title,
        // 与同一 map 内 possibleDrivers 的 year 口径保持一致：
        // 取【当前行年份】而非 Campaign 自身年份（跨年 Campaign 见 F-MED-1）。
        year: row.year,
        status: c.status,
        start: c.start,
        end: c.end,
        openEnded: c.openEnded === true,
        phaseLabel: primary ? primary.label : null,
        phaseAlso: also,
        phaseHit: primary ? primary.hit : null,
        possibleDrivers: labels,
        campaign: c,
      };
    });
    if (entries.length > 0) coveredYears += 1;
    samePeriod.push({ year: row.year, entries });
  }

  // 只保留有内容的年份？——保留全部年份，UI 自行决定是否折叠空年份；
  // 但 uncovered 以「是否所有年份皆空」判定。
  const uncovered = samePeriod.every((r) => r.entries.length === 0);

  return {
    position,
    samePeriod,
    coveredYears,
    possibleDrivers,
    uncovered,
  };
}
