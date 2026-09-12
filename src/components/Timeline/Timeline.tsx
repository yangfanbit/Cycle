import { useMemo, useState } from 'react';
import {
  allCampaigns,
  anchorResolver,
  events,
  ruleById,
  rules,
  sourceById,
  themeById,
  themesOfCampaign,
  windowsOfRule,
} from '../../data';
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
import { PHASE_LABEL, sectorColor, windowRangeLabel } from '../labels';

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

export function Timeline({ year, today, selection, onSelect }: TimelineProps) {
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

  // ---------- 已核验历史行情层（仅 verified；candidate 线索不入本层） ----------
  const campaignRows = useMemo(() => {
    return allCampaigns
      .map((c) => ({ campaign: c, segment: segmentForYear(c.start_date, c.end_date, year) }))
      .filter((r) => r.segment !== null);
  }, [year]);

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

        {/* 第三层：已核验历史行情（仅展示 verified 层；candidate 线索不入本层） */}
        <section className="tl-layer">
          <h3 className="tl-layer-title">已核验历史行情</h3>
          {campaignRows.length === 0 && (
            <div className="empty-note">暂无已核验历史行情（历史核验尚未开始）。</div>
          )}
          {campaignRows.map(({ campaign, segment }) => {
            const rule = ruleById.get(campaign.rule_id);
            const seg = segment!;
            const mainTheme = themesOfCampaign(campaign.campaign_id).find((ct) => ct.role === 'main');
            const themeName = mainTheme ? themeById.get(mainTheme.theme_id)?.name : undefined;
            const color = sectorColor(rule?.base_sector ?? '');
            return (
              <div className="tl-row" key={campaign.campaign_id}>
                <div className="tl-row-label">
                  <span className="name">{campaign.season_id}</span>
                  <span className="sub">{themeName ?? rule?.base_sector ?? ''}</span>
                </div>
                <div className="tl-track">
                  <MonthGrid year={year} />
                  <div
                    className={`bar window${seg.continuesFromPrevYear ? ' cont-prev' : ''}${
                      seg.continuesIntoNextYear ? ' cont-next' : ''
                    }${selection?.kind === 'campaign' && selection.id === campaign.campaign_id ? ' selected' : ''}`}
                    style={{
                      left: pct(seg.startFraction),
                      width: pct(Math.max(seg.endFraction - seg.startFraction, 0.003)),
                      background: color,
                      boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.18)',
                    }}
                    onMouseEnter={(e) =>
                      showTooltip(e, `${campaign.season_id} ${themeName ?? ''}`.trim(), [
                        `完整区间：${campaign.start_date} → ${campaign.end_date}`,
                        `跨年：${campaign.cross_year ? '是' : '否'}`,
                        `所属规律：${rule?.name ?? campaign.rule_id}`,
                        `来源：${sourceById.get(campaign.source_id)?.title ?? campaign.source_id}`,
                      ])
                    }
                    onMouseLeave={hideTooltip}
                    onClick={() => onSelect({ kind: 'campaign', id: campaign.campaign_id })}
                  >
                    {seg.continuesFromPrevYear && <span className="bar-arrow left">◂</span>}
                    {seg.continuesIntoNextYear && <span className="bar-arrow right">▸</span>}
                    <span className="bar-label">
                      {themeName ?? campaign.season_id}
                      {campaign.cross_year ? ' ↻' : ''}
                    </span>
                  </div>
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
                      ? `（约 ${status.daysToStart} 天后）`
                      : ''}
                    {phase === 'PRE_HEAT' && status ? `（约 ${status.daysToStart} 天后进入窗口）` : ''}
                    {phase === 'ACTIVE' && status ? `（余 ${status.daysToEnd} 天）` : ''}
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
