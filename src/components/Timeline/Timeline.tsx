import { useMemo, useState } from 'react';
import {
  anchorResolver,
  events,
  ruleById,
  rules,
  sourceById,
  windowsOfRule,
} from '../../data';
import {
  conflictSeverity,
  getConflictBoundaryCandidates,
  peakWindowOf,
} from '../../data/timeline/timelineAdapter';
import { preObservationChainOf } from '../../data/timeline/preObservation';
import type { TimelineCampaign, TimelineResearchEvent } from '../../data/timeline/timelineTypes';
import type { TimeWindow } from '../../models';
import {
  computeWindowStatus,
  dayOfYearISO,
  daysInYear,
  occurrenceForSeason,
  resolveEventForYear,
  segmentForYear,
  windowSegmentsForYear,
  yearFraction,
  type WindowStatusResult,
  type YearSegment,
} from '../../utils';
import {
  CONFLICT_FIELD_LABEL,
  conflictLine,
  DATA_STATUS_CLASS,
  DATA_STATUS_LABEL,
  EVENT_TYPE_LABEL,
  LIFECYCLE_LABEL,
  PHASE_LABEL,
  ROLE_LABEL,
  sectorColor,
  windowRangeLabel,
} from '../labels';

export type Selection =
  | { kind: 'rule'; id: string }
  | { kind: 'campaign'; id: string }
  | null;

interface TooltipState {
  x: number;
  y: number;
  title: string;
  lines: string[];
}

interface TimelineProps {
  year: number;
  today: string;
  selection: Selection;
  onSelect: (sel: Selection) => void;
  /** 第三层数据：由 TimelineDataSource（verified / preview）经 App 注入 */
  campaigns: TimelineCampaign[];
  /** Research 导出的具体日期事件（仅 preview 数据源提供） */
  researchEvents?: TimelineResearchEvent[];
  /** 数据源类型：verified = 生产；preview = Research 开发预览 */
  sourceKind: 'verified' | 'preview';
}

const MONTHS = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
const MONTH_START_FRACTIONS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

function monthFractions(year: number): number[] {
  const diy = daysInYear(year);
  const leap = diy === 366 ? 1 : 0;
  return MONTH_START_FRACTIONS.map((d, i) => (d + (i > 1 ? leap : 0)) / diy);
}

function pct(f: number): string {
  return `${(f * 100).toFixed(3)}%`;
}

/** 网格线（12个月） */
function MonthGrid({ year }: { year: number }) {
  return (
    <div className="tl-grid">
      {monthFractions(year).map((f, i) => (
        <div key={i} className="gl" style={{ left: pct(f) }} />
      ))}
    </div>
  );
}

export function Timeline({ year, today, selection, onSelect, campaigns, researchEvents, sourceKind }: TimelineProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const showTooltip = (e: React.MouseEvent, title: string, lines: string[]) => {
    setTooltip({ x: e.clientX + 12, y: e.clientY + 14, title, lines });
  };
  const hideTooltip = () => setTooltip(null);

  // ---------- 事件层 ----------
  const resolvedEvents = useMemo(
    () =>
      events
        .map((ev) => resolveEventForYear(ev, year))
        .filter((r): r is NonNullable<typeof r> => r !== null),
    [year],
  );

  // ---------- 规律层 ----------
  const ruleRows = useMemo(() => {
    return rules.map((rule) => {
      const window: TimeWindow | undefined = windowsOfRule(rule.rule_id)[0];
      const status: WindowStatusResult | null = window
        ? computeWindowStatus(window, today, anchorResolver)
        : null;
      const segments: YearSegment[] = window
        ? windowSegmentsForYear(window, year, anchorResolver)
        : [];
      // preheat 段：对每个覆盖本年的 occurrence 单独裁剪预热区
      const preheatSegments: YearSegment[] = [];
      if (window) {
        for (const seasonYear of [year, year - 1]) {
          const occ = windowSegmentsForYearOccurrence(window, seasonYear);
          if (!occ) continue;
          const seg = segmentForYear(occ.preheatStart, occ.start, year);
          if (seg) preheatSegments.push(seg);
        }
      }
      return { rule, window, status, segments, preheatSegments };
    });
  }, [year, today]);

  // ---------- 历史行情层（verified 生产数据或 Research 预览，经 Adapter 注入） ----------
  const campaignRows = useMemo(() => {
    return campaigns.filter(
      (c) => segmentForYear(c.start, c.end, year) !== null,
    );
  }, [campaigns, year]);

  // 事件归属标题查询（研究事件 tooltip 用：正式 Campaign 与 Research Candidate 并列）
  const campaignTitleById = useMemo(() => {
    return new Map(campaigns.map((c) => [c.campaign_id, c.title]));
  }, [campaigns]);

  const showTodayLine = today.startsWith(`${year}-`);
  const todayFrac = showTodayLine ? yearFraction(today) : 0;

  return (
    <div className="timeline-scroll">
      <div className="timeline">
        {/* 月份表头 */}
        <div className="tl-months">
          <div className="corner">{year} 年</div>
          <div className="months">
            {monthFractions(year).map((f, i) => (
              <span key={i} className="month-label" style={{ left: pct(f) }}>
                {MONTHS[i]}
              </span>
            ))}
          </div>
        </div>

        {/* 第一层：事件层 */}
        <section className="tl-layer">
          <h3 className="tl-layer-title">事件</h3>
          <div className="tl-row">
            <div className="tl-row-label">
              <span className="sub">节假日 / 披露期</span>
            </div>
            <div className="tl-track" style={{ height: 30 }}>
              <MonthGrid year={year} />
              {resolvedEvents.map((r) => {
                const sf = yearFraction(r.start);
                const ef = (dayOfYearISO(r.end) + 1) / daysInYear(year);
                const label = r.approximate ? `${r.event.name}（近似）` : r.event.name;
                return (
                  <div
                    key={r.event.event_id}
                    className={`evt-chip${r.start === r.end ? ' point' : ''}`}
                    style={{ left: pct(sf), width: pct(Math.max(ef - sf, 0.004)) }}
                    onMouseEnter={(e) =>
                      showTooltip(e, r.event.name, [
                        `${r.start}${r.start === r.end ? '' : ` → ${r.end}`}`,
                        r.event.event_type,
                        ...(r.event.description ? [r.event.description] : []),
                      ])
                    }
                    onMouseLeave={hideTooltip}
                  >
                    {label}
                  </div>
                );
              })}
              {showTodayLine && <TodayLine frac={todayFrac} />}
            </div>
          </div>
          {/* 研究事件（Research Export 具体日期事件；非正式历史事实） */}
          {(researchEvents?.length ?? 0) > 0 && (
            <div className="tl-row">
              <div className="tl-row-label">
                <span className="sub">研究事件（Research）</span>
              </div>
              <div className="tl-track" style={{ height: 46 }}>
                <MonthGrid year={year} />
                {researchEvents!.map((ev, i) => {
                  const f = yearFraction(ev.date);
                  const ownerId = ev.campaign_id ?? ev.research_candidate_id;
                  const owner = ownerId
                    ? campaignTitleById.get(ownerId) ?? ownerId
                    : null;
                  return (
                    <div
                      key={ev.event_id}
                      className="evt-chip res point"
                      style={{ left: pct(f), top: i % 2 === 0 ? 2 : 24 }}
                      onMouseEnter={(e) =>
                        showTooltip(e, ev.name, [
                          ev.date,
                          `${EVENT_TYPE_LABEL[ev.event_type] ?? ev.event_type}${
                            ev.role ? ` · ${ROLE_LABEL[ev.role] ?? ev.role}` : ''
                          }`,
                          owner ? `关联：${owner}` : '全局事件（不绑定 Campaign）',
                          '研究事件为 Research 导出，非正式历史事实。',
                        ])
                      }
                      onMouseLeave={hideTooltip}
                    >
                      {ev.name}
                    </div>
                  );
                })}
                {showTodayLine && <TodayLine frac={todayFrac} />}
              </div>
            </div>
          )}
        </section>

        {/* 第二层：行业 / 季节性规律 */}
        <section className="tl-layer">
          <h3 className="tl-layer-title">行业 / 季节性规律（候选，待验证）</h3>
          {ruleRows.map(({ rule, window, status, segments, preheatSegments }) => {
            const color = sectorColor(rule.base_sector);
            return (
              <div className="tl-row" key={rule.rule_id}>
                <div className="tl-row-label">
                  <span
                    className={`phase-dot phase-${status?.phase ?? 'NO_WINDOW'}`}
                    title={status ? PHASE_LABEL[status.phase] : '经验窗口（暂不可计算）'}
                  />
                  <span className="name">{rule.base_sector}</span>
                </div>
                <div className="tl-track">
                  <MonthGrid year={year} />
                  {preheatSegments.map((seg, i) => (
                    <div
                      key={`ph${i}`}
                      className={`bar preheat${seg.continuesFromPrevYear ? ' cont-prev' : ''}${
                        seg.continuesIntoNextYear ? ' cont-next' : ''
                      }`}
                      style={{
                        left: pct(seg.startFraction),
                        width: pct(seg.endFraction - seg.startFraction),
                        background: color,
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${rule.name} · 提前观察区`, [
                          `${seg.start} → ${seg.end}`,
                          `状态：${status ? PHASE_LABEL[status.phase] : '未知'}`,
                          `来源：${sourceById.get(rule.source_id)?.title ?? rule.source_id}`,
                        ])
                      }
                      onMouseLeave={hideTooltip}
                      onClick={() => onSelect({ kind: 'rule', id: rule.rule_id })}
                    />
                  ))}
                  {segments.map((seg, i) => {
                    const occ = status?.occurrence;
                    const rangeText = windowRangeLabel(
                      occ ? occ.start : (window?.start_md ?? '未定'),
                      occ ? occ.end : (window?.end_md ?? '未定'),
                      window?.approximate,
                    );
                    return (
                      <div
                        key={`w${i}`}
                        className={`bar window${seg.continuesFromPrevYear ? ' cont-prev' : ''}${
                          seg.continuesIntoNextYear ? ' cont-next' : ''
                        }${selection?.kind === 'rule' && selection.id === rule.rule_id ? ' selected' : ''}`}
                        style={{
                          left: pct(seg.startFraction),
                          width: pct(Math.max(seg.endFraction - seg.startFraction, 0.003)),
                          background: color,
                        }}
                        onMouseEnter={(e) =>
                          showTooltip(e, rule.name, [
                            `窗口：${rangeText}`,
                            `状态：${status ? PHASE_LABEL[status.phase] : '未知'}`,
                            `跨年：${occ?.crossYear ? '是' : '否'}`,
                            `来源：${sourceById.get(rule.source_id)?.title ?? rule.source_id}`,
                          ])
                        }
                        onMouseLeave={hideTooltip}
                        onClick={() => onSelect({ kind: 'rule', id: rule.rule_id })}
                      >
                        {seg.continuesFromPrevYear && <span className="bar-arrow left">◂</span>}
                        {seg.continuesIntoNextYear && <span className="bar-arrow right">▸</span>}
                        <span className="bar-label">{rule.base_sector}</span>
                      </div>
                    );
                  })}
                  {showTodayLine && <TodayLine frac={todayFrac} />}
                </div>
              </div>
            );
          })}
        </section>

        {/* 第三层：历史行情（Campaign 为视觉主体；verified 或 Research 预览） */}
        <section className="tl-layer layer-campaigns">
          <h3 className="tl-layer-title">
            {sourceKind === 'preview' ? '历史行情（Research 预览，非正式历史事实）' : '已核验历史行情'}
          </h3>
          {campaignRows.length === 0 && (
            <div className="empty-note">
              {sourceKind === 'preview'
                ? '该年份当前无正式 Historical Campaign 数据。'
                : '当前暂无已核验历史行情（历史核验尚未开始）。'}
            </div>
          )}
          {campaignRows.map((campaign) => {
            const rule = ruleById.get(campaign.rule_id);
            const color = sectorColor(rule?.base_sector ?? '');
            const selected = selection?.kind === 'campaign' && selection.id === campaign.campaign_id;
            // 生命周期分段裁剪到当前年份（跨年行情在两年各显示覆盖段）
            const phaseSegs = campaign.phases
              .map((p) => ({ phase: p.phase, seg: segmentForYear(p.start, p.end, year) }))
              .filter((r): r is { phase: typeof r.phase; seg: YearSegment } => r.seg !== null);
            const earlySeg = campaign.early_signal
              ? segmentForYear(campaign.early_signal.start, campaign.early_signal.end, year)
              : null;
            // 提前观察区（V1.8.2）：主题形成前 historicalPreObservationDays(30) 天的研究浏览缓冲。
            // 极淡视觉；层级 Pre-observation → Early Signal? → Theme Formation。
            // 语义：不是预测、不是买入建议、不是历史统计事实。
            const preObsChain = preObservationChainOf(campaign);
            const preObsSeg = preObsChain
              ? segmentForYear(
                  preObsChain.preObservation.start,
                  preObsChain.preObservation.end,
                  year,
                )
              : null;
            // 冲突分级：minor（同一 Phase Window 内，≤10 天）→ 显示窗口；major（跨月份/影响生命周期）→ 大型 Conflict 视觉
            const majorConflicts = (campaign.conflicts ?? []).filter(
              (c) => conflictSeverity(c) === 'major',
            );
            const hasMajorConflict = majorConflicts.length > 0;
            // Conflict 边界候选（仅 major 字段触发大视觉；从 conflicts 推导，不做任何取舍）
            const conflictCandidates =
              campaign.status === 'conflict' ? getConflictBoundaryCandidates(campaign) : null;
            const startCands = majorConflicts.some((c) => c.field === 'start_date')
              ? conflictCandidates?.startCandidates ?? null
              : null;
            const peakMajorCands = majorConflicts.some((c) => c.field === 'peak_date')
              ? conflictCandidates?.peakCandidates ?? null
              : null;
            const endCands = majorConflicts.some((c) => c.field === 'end_date')
              ? conflictCandidates?.endCandidates ?? null
              : null;
            // Peak Window：时间轴优先显示窗口（±7 天）而非单一精确日期；轻微分歧时为候选 A→B 窗口
            const peakWin = peakWindowOf(campaign);
            const peakWinSeg = peakWin
              ? segmentForYear(peakWin.start, peakWin.end, year)
              : null;
            // 起点分歧区间：A → B（研究分歧区间，非正式起点）
            const startEnvelopeSeg = startCands
              ? segmentForYear(startCands[0], startCands[startCands.length - 1], year)
              : null;
            // End 候选区间：DB Candidate（campaign.end）与候选日期的整体包络
            const endEnvelopeSeg = endCands
              ? segmentForYear(
                  [campaign.end, ...endCands].reduce((a, b) => (a < b ? a : b)),
                  [campaign.end, ...endCands].reduce((a, b) => (a > b ? a : b)),
                  year,
                )
              : null;
            const peakInYear = campaign.peak && campaign.peak.startsWith(`${year}-`);
            const peakFrac = peakInYear ? yearFraction(campaign.peak!) : 0;
            const themeNames = campaign.themes.map((t) => t.name).join('、');
            const statusLabel = DATA_STATUS_LABEL[campaign.status];
            const tooltipLines = [
              `完整区间${hasMajorConflict ? '（日期存在研究分歧）' : ''}：${campaign.start} → ${campaign.end}${
                campaign.openEnded ? '（候选观察中，end 为年末近似）' : ''
              }`,
              campaign.kind === 'candidate'
                ? 'Research Candidate：未达正式 Campaign 门槛，非 Historical Confirmed Campaign'
                : `生命周期：${campaign.phases
                    .map((p) => `${LIFECYCLE_LABEL[p.phase]} ${p.start.slice(5)}→${p.end.slice(5)}`)
                    .join(' / ')}`,
              ...(campaign.early_signal
                ? [`早期信号：${campaign.early_signal.start} → ${campaign.early_signal.end}${campaign.early_signal.label ? `（${campaign.early_signal.label}）` : ''}`]
                : []),
              peakWin
                ? `峰值窗口：${peakWin.start} ~ ${peakWin.end}${peakWin.disputed ? '（研究分歧窗口：候选 A / B）' : ''}`
                : '峰值：未核验',
              `题材：${themeNames || '待补充'}`,
              `所属规律：${rule?.name ?? campaign.rule_id}`,
              `数据状态：${statusLabel}${campaign.status !== 'verified' ? '（非正式历史事实）' : ''}`,
              ...(campaign.conflicts ?? []).map((c) => conflictLine(c)),
              `来源：${campaign.sourceNote ?? '—'}`,
            ];
            /** 候选 marker 渲染（A / B 竖线，不依赖颜色） */
            const renderCandMarkers = (
              dates: string[] | null,
              field: 'start_date' | 'end_date',
            ) => {
              if (!dates) return null;
              const fieldLabel = CONFLICT_FIELD_LABEL[field];
              return dates.map((d) => {
                if (!d.startsWith(`${year}-`)) return null;
                const side = campaign.conflicts!.find((c) => c.field === field)!
                  .candidate_a.date === d
                  ? 'A'
                  : 'B';
                return (
                  <span
                    key={`cand-${field}-${d}`}
                    className={`cand-marker cand-${side.toLowerCase()}`}
                    style={{ left: pct(yearFraction(d)) }}
                    onMouseEnter={(e) =>
                      showTooltip(e, `${campaign.title} · ${fieldLabel}候选 ${side}`, [
                        `${fieldLabel}候选 ${side}：${d}`,
                        `${fieldLabel}日期存在研究分歧（A / B 均未确认）`,
                      ])
                    }
                    onMouseLeave={hideTooltip}
                  >
                    {side}
                  </span>
                );
              });
            };
            return (
              <div className="tl-row cmp-row" key={campaign.campaign_id}>
                <div className="tl-row-label">
                  {campaign.kind === 'candidate' && (
                    <span className="rc-badge" title="Research Candidate：研究候选，非正式 Historical Campaign">
                      RC
                    </span>
                  )}
                  <span className={`st-badge ${DATA_STATUS_CLASS[campaign.status]}`}>{statusLabel}</span>
                  <span className="name">{campaign.title}</span>
                  <span className="sub">
                    {campaign.season_id}
                    {campaign.cross_year ? ' ↻' : ''}
                  </span>
                </div>
                <div className="tl-track">
                  <MonthGrid year={year} />
                  {/* 提前观察区：最淡的一层，位于 Campaign 主体之前（不抢主升 / Peak） */}
                  {preObsSeg && preObsChain && (
                    <div
                      className="bar cmp pre-obs"
                      style={{
                        left: pct(preObsSeg.startFraction),
                        width: pct(Math.max(preObsSeg.endFraction - preObsSeg.startFraction, 0.004)),
                        borderColor: color,
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · 历史提前观察区`, [
                          `观察区：${preObsChain.preObservation.start} → ${preObsChain.preObservation.end}（${preObsChain.preObservation.days} 天）`,
                          `主题形成：${preObsChain.formation}`,
                          ...(preObsChain.hasEarlySignal
                            ? [`早期信号：${preObsChain.earlySignal!.start} → ${preObsChain.earlySignal!.end}`]
                            : []),
                          '层级：提前观察区 → ' +
                            (preObsChain.hasEarlySignal ? '早期信号 → ' : '') +
                            '主题形成',
                          '仅为研究浏览缓冲，不代表历史平均领先期；不是预测，也不是买入建议。',
                        ])
                      }
                      onMouseLeave={hideTooltip}
                      onClick={() => onSelect({ kind: 'campaign', id: campaign.campaign_id })}
                    >
                      <span className="bar-label pre-obs-label">提前观察区</span>
                    </div>
                  )}
                  {/* 早期信号：较淡显示，不得呈现为正式 Campaign */}
                  {earlySeg && (
                    <div
                      className="bar cmp early-signal"
                      style={{
                        left: pct(earlySeg.startFraction),
                        width: pct(Math.max(earlySeg.endFraction - earlySeg.startFraction, 0.004)),
                        borderColor: color,
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · 早期信号`, [
                          `信号区间：${campaign.early_signal!.start} → ${campaign.early_signal!.end}`,
                          ...(campaign.early_signal!.label ? [campaign.early_signal!.label] : []),
                          '早期信号为前置观察，不是正式行情起点。',
                        ])
                      }
                      onMouseLeave={hideTooltip}
                      onClick={() => onSelect({ kind: 'campaign', id: campaign.campaign_id })}
                    >
                      <span className="bar-label es-label">早期信号</span>
                    </div>
                  )}
                  {/* 生命周期分段：主升（实色）→ 高位回撤（条纹）→ 退潮（虚线纹理） */}
                  {phaseSegs.map(({ phase, seg: ps }) => (
                    <div
                      key={phase}
                      className={`bar cmp cmp-${phase}${ps.continuesFromPrevYear ? ' cont-prev' : ''}${
                        ps.continuesIntoNextYear ? ' cont-next' : ''
                      }${selected ? ' selected' : ''}${
                        campaign.status === 'provisional' || campaign.status === 'preview' ? ' st-dashed' : ''
                      }${hasMajorConflict ? ' st-conflict-visual' : ''}`}
                      style={{
                        left: pct(ps.startFraction),
                        width: pct(Math.max(ps.endFraction - ps.startFraction, 0.004)),
                        background: color,
                      }}
                      onMouseEnter={(e) => showTooltip(e, campaign.title, tooltipLines)}
                      onMouseLeave={hideTooltip}
                      onClick={() => onSelect({ kind: 'campaign', id: campaign.campaign_id })}
                    >
                      {ps.continuesFromPrevYear && phase === campaign.phases[0].phase && (
                        <span className="bar-arrow left">◂</span>
                      )}
                      {ps.continuesIntoNextYear &&
                        phase === campaign.phases[campaign.phases.length - 1].phase && (
                          <span className="bar-arrow right">▸</span>
                        )}
                      <span className="bar-label">
                        {LIFECYCLE_LABEL[phase]}
                        {campaign.cross_year ? ' ↻' : ''}
                      </span>
                    </div>
                  ))}
                  {/* 起点研究分歧区间（Start Conflict：A → B，均未确认） */}
                  {startEnvelopeSeg && startCands && (
                    <div
                      className="conflict-envelope"
                      style={{
                        left: pct(startEnvelopeSeg.startFraction),
                        width: pct(
                          Math.max(startEnvelopeSeg.endFraction - startEnvelopeSeg.startFraction, 0.004),
                        ),
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · 起点研究分歧区间`, [
                          `起点候选：${startCands.join(' / ')}`,
                          '起点日期存在研究分歧（A / B 均未确认），本区间不是正式起点。',
                        ])
                      }
                      onMouseLeave={hideTooltip}
                    />
                  )}
                  {/* End 候选区间（End Conflict：A → B 虚线延伸，非正式延伸） */}
                  {endEnvelopeSeg && endCands && (
                    <div
                      className="end-extension"
                      style={{
                        left: pct(endEnvelopeSeg.startFraction),
                        width: pct(
                          Math.max(endEnvelopeSeg.endFraction - endEnvelopeSeg.startFraction, 0.004),
                        ),
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · End 候选区间`, [
                          `结束候选：${endCands.join(' / ')}`,
                          '结束日期存在研究分歧（A / B 均未确认），延伸部分不是正式行情延续。',
                        ])
                      }
                      onMouseLeave={hideTooltip}
                    >
                      <span className="bar-label">End 候选区间</span>
                    </div>
                  )}
                  {/* 起点候选 marker（A / B） */}
                  {renderCandMarkers(startCands, 'start_date')}
                  {/* 结束候选 marker（A / B） */}
                  {renderCandMarkers(endCands, 'end_date')}
                  {/* Peak Window（优先显示窗口而非单一精确日期；轻微分歧 = 候选 A→B 窗口） */}
                  {peakWinSeg && peakWin && (
                    <div
                      className={`peak-window${peakWin.disputed ? ' disputed' : ''}`}
                      style={{
                        left: pct(peakWinSeg.startFraction),
                        width: pct(
                          Math.max(peakWinSeg.endFraction - peakWinSeg.startFraction, 0.006),
                        ),
                      }}
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · Peak Window`, [
                          `峰值窗口：${peakWin.start} ~ ${peakWin.end}`,
                          ...(peakWin.disputed
                            ? [
                                '窗口由研究分歧候选 A / B 构成（同一窗口内，不画大型 Conflict）。',
                              ]
                            : []),
                        ])
                      }
                      onMouseLeave={hideTooltip}
                    />
                  )}
                  {/* 峰值标记：无分歧 → 中心 ▲；严重分歧 → A / B 双候选标记 */}
                  {peakMajorCands ? (
                    peakMajorCands
                      .filter((d) => d.startsWith(`${year}-`))
                      .map((d) => {
                        const isA =
                          campaign.conflicts!.find((c) => c.field === 'peak_date')!.candidate_a.date === d;
                        return (
                          <span
                            key={`peak-cand-${d}`}
                            className="peak-marker cand"
                            style={{ left: pct(yearFraction(d)) }}
                            onMouseEnter={(e) =>
                              showTooltip(e, `${campaign.title} · 峰值候选 ${isA ? 'A' : 'B'}`, [
                                `Peak Candidate ${isA ? 'A' : 'B'}：${d}`,
                                '峰值日期存在研究分歧（A / B 均未确认）。',
                              ])
                            }
                            onMouseLeave={hideTooltip}
                          >
                            ▲<sup>{isA ? 'A' : 'B'}</sup>
                          </span>
                        );
                      })
                  ) : (
                    peakInYear && (
                      <span
                        className="peak-marker"
                        style={{ left: pct(peakFrac) }}
                        onMouseEnter={(e) =>
                          showTooltip(e, `${campaign.title} · 峰值`, [`峰值日期：${campaign.peak}`])
                        }
                        onMouseLeave={hideTooltip}
                      >
                        ▲
                      </span>
                    )
                  )}
                  {/* 研究分歧警示（仅严重分歧；CONFLICT 不得被描述成历史事实） */}
                  {hasMajorConflict && (
                    <span
                      className="conflict-flag"
                      onMouseEnter={(e) =>
                        showTooltip(e, `${campaign.title} · 研究分歧`, [
                        ...(campaign.conflicts ?? []).map((c) => conflictLine(c)),
                        '分歧数据仅用于研究预览，不构成历史事实。',
                      ])
                      }
                      onMouseLeave={hideTooltip}
                    >
                      ⚠
                    </span>
                  )}
                  {showTodayLine && <TodayLine frac={todayFrac} />}
                </div>
              </div>
            );
          })}
        </section>

        {/* 第四层：当前 / 观察状态 */}
        <section className="tl-layer">
          <h3 className="tl-layer-title">当前 / 观察状态（{today}）</h3>
          <div className="status-strip">
            {ruleRows.map(({ rule, status, window }) => {
              const phase = status?.phase;
              return (
                <div className="status-item" key={rule.rule_id}>
                  <span className={`phase-dot phase-${phase ?? 'NO_WINDOW'}`} />
                  <span>{rule.base_sector}</span>
                  <span className="phase-text">
                    {phase ? PHASE_LABEL[phase] : '暂无相关窗口'}
                    {phase === 'NOT_ACTIVE' && status && status.daysToStart > 0
                      ? `（历史观察窗口将在约 ${status.daysToStart} 天后进入）`
                      : ''}
                    {phase === 'PRE_HEAT' && status ? `（历史观察窗口将在约 ${status.daysToStart} 天后进入）` : ''}
                    {phase === 'ACTIVE' && status ? `（观察窗口余 ${status.daysToEnd} 天）` : ''}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {tooltip && (
        <div className="tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          <div className="tt-title">{tooltip.title}</div>
          {tooltip.lines.map((l, i) => (
            <div key={i} className={i === 0 ? '' : 'tt-dim'}>
              {l}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TodayLine({ frac }: { frac: number }) {
  return (
    <div className="today-line" style={{ left: pct(frac) }}>
      <span className="today-flag">TODAY</span>
    </div>
  );
}

// 供规律层 preheat 段计算使用：直接实例化某季 occurrence
function windowSegmentsForYearOccurrence(window: TimeWindow, seasonYear: number) {
  return occurrenceForSeason(window, seasonYear, anchorResolver);
}
