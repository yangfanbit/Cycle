/**
 * ★★ 外部季节性线索 → **研究请求草稿种子**（ThreeC 1.3 · v0.13）。
 *
 * ## 为什么需要它
 *
 * 未映射（`UNMAPPED`）的外部线索此前在页面上的终点是「未映射 + 原因」——
 * 用户看完仍然无处可去。本模块把一条外部线索转成**可编辑的草稿种子**，
 * 由用户确认后带入**现有**的研究请求草稿（`DirectionLookupSection` + 本机存储）。
 *
 * ★ 不新建第二套表单 / 存储 / 导出 —— 草稿仍是同一个 `ResearchRequestDraft`、
 *   同一个 localStorage 键、同一个导出格式。
 *
 * ## 硬约束
 *
 * - **月份保持原始精度**：只带 `raw_text`（如「6–7 月」），**不补日级日期**；
 *   无固定窗口的线索不得补出月份。
 * - **来源标记为外部参考**：`knownLeads` 里必须写明「未经 ThreeC 验证」，
 *   **不得**伪装成已验证证据。
 * - **不关联覆盖查询**：种子来自外部线索，**不是**一次覆盖查询 →
 *   `linkedQuery` / `linkedCoverage` 均为空（否则导出的「查询证据」是伪造的）。
 * - **不编造研究问题**：只给一条**可核实**的建议句式，字段仍可编辑。
 */

import {
  windowTextOf,
  MATURITY_LABEL,
  type ExternalCalendarEntry,
  type ExternalCalendarSource,
} from './externalSeasonalCalendar';
import type { ResearchRequestDraft } from './researchRequestDraft';

/** 草稿种子（带上来源元信息，供 UI 展示「你正在带入的是哪条线索」） */
export interface ExternalLeadDraftSeed {
  /** 来源线索 id（用于 UI 提示与测试核对） */
  entryId: string;
  /** 来源线索名称 */
  entryName: string;
  /** 建议带入的草稿内容 */
  draft: ResearchRequestDraft;
}

/**
 * ★ 带入方向查询区的种子（含单调递增 `token`）。
 * 同一线索再次点击时 token 变化 → 组件重新执行「带入」判定。
 */
export interface DraftSeed {
  token: number;
  entryId: string;
  entryName: string;
  draft: ResearchRequestDraft;
}

/** 构造种子（`token` 由调用方提供，通常自增） */
export function makeDraftSeed(
  entry: ExternalCalendarEntry,
  sources: readonly ExternalCalendarSource[],
  token: number,
): DraftSeed {
  const built = draftFromExternalLead(entry, sources);
  return { token, ...built };
}

/**
 * ★★ 由外部线索构造草稿种子（纯函数）。
 *
 * @param entry   外部线索
 * @param sources 来源表（`externalCalendarDoc().source_reports`）或查找函数返回的单条
 */
export function draftFromExternalLead(
  entry: ExternalCalendarEntry,
  sources: readonly ExternalCalendarSource[],
): ExternalLeadDraftSeed {
  const windowText = windowTextOf(entry);   // 无窗口 → 「—（无固定窗口）」
  const hasWindow = (entry.windows ?? []).length > 0;
  const sourceTitles = entry.source_ids
    .map((id) => sources.find((s) => s.source_id === id)?.title)
    .filter((t): t is string => Boolean(t));

  // ★ 已知线索：只放**事实字段**（原文、类别、来源、证据引用），不放判断
  const knownLeads: string[] = [
    `外部线索：${entry.id} · ${entry.name}（类别：${entry.category}）`,
    hasWindow
      ? `原始窗口（月份精度，未转日级）：${windowText}`
      : '原始窗口：无固定月份窗口（源数据未给出月份）',
    `外部来源：${sourceTitles.length > 0 ? sourceTitles.join('、') : '（源数据未记录来源名）'}`,
    entry.evidence_refs.length > 0
      ? `外部资料证据引用：${entry.evidence_refs.join('；')}`
      : '外部资料证据引用：（无）',
    '★ 以上均为**外部参考**（外部资料声称，未经 ThreeC 验证）—— 不是已核实事实。',
  ];

  // ★★ v0.25：把 ThreeC **已有的核验结论**一并带入（不是从头问起）。
  //   措辞必须是描述性的：disposition / 反例 / 原因是研究判断的转述，
  //   **不得**写成「已验证 / 成立」之类结论。
  const ver = entry.verification;
  if (ver) {
    // ★ 核验日期只到**月份精度** —— 草稿红线：不得出现日级日期（会被当成精确证据）
    const reviewedMonth = String(ver.reviewed_at).slice(0, 7);
    knownLeads.push(
      `★ ThreeC 已有核验（${reviewedMonth}，描述性转述，非最终结论）：`
      + `性质「${ver.nature}」· 处置「${MATURITY_LABEL[ver.disposition] ?? ver.disposition}」`,
    );
    if (ver.reason) knownLeads.push(`核验依据：${ver.reason}`);
    for (const c of ver.counter_evidence) knownLeads.push(`反例 / 不支持证据：${c}`);
    if (ver.threec_evidence.note) knownLeads.push(`库内情况：${ver.threec_evidence.note}`);
    if (ver.next_step?.text) knownLeads.push(`建议下一步：${ver.next_step.text}`);
  }

  // ★ 研究问题建议：只给「可核实」的两条，用户可改
  const researchQuestions = [
    hasWindow
      ? `核查研究库历史对象中是否存在与「${entry.name}」${windowText}相关的时段`
        + '（按月份核对，不推断日级日期）；'
      : `核查研究库历史对象中是否存在与「${entry.name}」相关的时段（该外部线索无固定月份窗口）；`,
    '如存在，核实具体机制与时间证据：哪个环节在该时段真正受益、催化时间线是否可溯源。',
  ].join('\n');

  return {
    entryId: entry.id,
    entryName: entry.name,
    draft: {
      direction: entry.name,
      researchQuestions,
      whyCare: '',
      knownLeads: knownLeads.join('\n'),
      timeRange: '',
      // ★ 不伪造覆盖查询关联：这不是一次查询，没有查询证据
      linkedQuery: '',
      linkedAt: '',
      linkedCoverage: null,
    },
  };
}

/** ★ 带入前必须让用户看到的说明（UI 原样渲染） */
export const EXTERNAL_LEAD_DRAFT_NOTE =
  '★ 以下内容带入后可**全部编辑**：研究方向、原始窗口文本（月份精度）、'
  + '线索类别、外部来源名与证据引用。★ 来源标记为**外部参考**，不伪装成已验证证据。'
  + '★ 草稿仍只存本机、需经 Research 审查，**不会**自动入库或获得正式编号。';

/** 非空草稿被替换时的确认文案（`label` = 线索名） */
export function draftReplaceConfirmText(label: string): string {
  return `★ 你已有一份**非空草稿**。用外部线索「${label}」替换它？`
    + '替换后原草稿内容会被覆盖（导出前请自行备份）；也可以保留现有草稿。';
}
