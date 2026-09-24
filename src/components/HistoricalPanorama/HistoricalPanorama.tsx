import { useMemo } from 'react';
import type { Selection } from '../Timeline/Timeline';
import { isEntrySelected } from '../Timeline/Timeline';
import { MONTHS, MonthGrid, TodaySpan, monthFractions, pct } from '../Timeline/trackPrimitives';
import type { TimelineCampaign, TimelineDataSource } from '../../data/timeline/timelineTypes';
import { dayOfYearISO, daysInYear, yearFraction } from '../../utils';

/**
 * Historical Opportunity Panorama（Product 1.1 · 首页第一视觉）。
 *
 * 目的：**一眼看到历史上全年时间维度（Jan–Dec）的题材 / Campaign 炒作分布**，
 * 而不是只看当前一年的行情。纵向 = 历史年份，每一行 = 该年（2015–2025），
 * 横向 = 1–12 月；每条 = 一个 Historical Object 在该年的生命周期分段。
 *
 * 复用（不新增研究逻辑）：
 * - 数据源：与单年 Timeline 同源（同一个 `TimelineDataSource`，同一 Adapter）；
 * - 生命周期：沿用已有 `campaign.phases`（主升 / 高位回撤 / 退潮 / 早期信号）；
 * - 月份网格与比例：沿用 `trackPrimitives` 的 `MonthGrid` / `monthFractions` / `pct`。
 *
 * 语义边界：
 * - Research Candidate（`kind === 'candidate'`）以虚线边框 + RC 徽章区分，
 *   **不伪装成正式 Historical Campaign**；
 * - 不新增信号 / 评分 / 排名 / 预测；
 * - Today 只画**一根**贯穿式细红线（`TodaySpan`），不再逐行重复。
 */

interface HistoricalPanoramaProps {
  dataSource: TimelineDataSource;
  today: string;
  year: number;
  selection: Selection;
  onSelect: (sel: Selection) => void;
}

/** 每年一行：该年在时间轴上出现过的 Historical Object（含纵向车道分配） */
interface PanoramaObject {
  obj: TimelineCampaign;
  /** 命中区在年内的比例区间 */
  boxStart: number;
  boxEnd: number;
  /** 裁剪到本年的生命周期分段（相对命中区起点） */
  segs: { phase: string; sf: number; ef: number }[];
  peakFrac: number | null;
  lane: number;
  color: string;
  entryId: string;
}

interface PanoramaRow {
  year: number;
  objects: PanoramaObject[];
  lanes: number;
  campaignCount: number;
  candidateCount: number;
}

/** 每行最多车道数（超出则复用最后一条车道，保持高度可控） */
const MAX_LANES = 3;
const LANE_H = 11;
const LANE_GAP = 2;
const ROW_PAD = 3;

/**
 * 主题配色（稳定哈希 → 固定调色板）。
 *
 * 说明：export 的 `rule_id`（如 `rule_semiconductor`）属于 Research 侧 vocabulary，
 * **不在** Product 侧 `data/candidate/rules.ts` 内，故不能复用 `sectorColor(rule.base_sector)`。
 * 这里改用对象**自身已透传的主题名**（`themes[0].name`）做稳定配色 ——
 * 不新增研究口径，只是给既有字段一个稳定的视觉区分。
 */
const PALETTE = [
  '#5a7a9a', '#9a6a6a', '#5a8a7a', '#b08355', '#7a6a8a',
  '#6a8aaa', '#7a9a6a', '#aa7a8a', '#8a7f6a', '#a8914f',
  '#5f7f9f', '#8a5f6f',
];
function themeColor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

function buildRow(y: number, dataSource: TimelineDataSource): PanoramaRow {
  const raw = dataSource.yearData(y).campaigns;
  const built: Omit<PanoramaObject, 'lane'>[] = [];
  for (const obj of raw) {
    const segs = obj.phases
      .map((p) => ({
        phase: p.phase,
        sf: yearFraction(p.start),
        ef: (dayOfYearISO(p.end) + 1) / daysInYear(y),
        inYear: p.start <= `${y}-12-31` && p.end >= `${y}-01-01`,
      }))
      .filter((s) => s.inYear);
    if (segs.length === 0) continue;
    const boxStart = Math.min(...segs.map((s) => Math.max(s.sf, 0)));
    const boxEnd = Math.max(...segs.map((s) => s.ef));
    built.push({
      obj,
      boxStart,
      boxEnd,
      segs: segs.map((s) => ({
        phase: s.phase,
        sf: Math.max(s.sf - boxStart, 0),
        ef: Math.max(s.ef - boxStart, 0.006),
      })),
      peakFrac: obj.peak && obj.peak.startsWith(`${y}-`) ? yearFraction(obj.peak) : null,
      color: themeColor(obj.themes[0]?.name ?? obj.title),
      entryId: `${obj.campaign_id}@${y}`,
    });
  }
  // 车道分配：起点排序，贪心放入第一条不重叠的车道（最多 MAX_LANES 条）
  built.sort((a, b) => a.boxStart - b.boxStart);
  const laneEnds: number[] = [];
  const objects: PanoramaObject[] = built.map((b) => {
    let lane = laneEnds.findIndex((end) => b.boxStart >= end - 0.002);
    if (lane === -1) {
      if (laneEnds.length < MAX_LANES) {
        laneEnds.push(b.boxEnd);
        lane = laneEnds.length - 1;
      } else {
        lane = MAX_LANES - 1; // 超出 → 复用最后一条车道（不丢对象，只重叠）
        laneEnds[lane] = Math.max(laneEnds[lane], b.boxEnd);
      }
    } else {
      laneEnds[lane] = b.boxEnd;
    }
    return { ...b, lane };
  });
  return {
    year: y,
    objects,
    lanes: Math.max(1, Math.min(laneEnds.length, MAX_LANES)),
    campaignCount: raw.filter((o) => o.kind === 'campaign').length,
    candidateCount: raw.filter((o) => o.kind === 'candidate').length,
  };
}

export function HistoricalPanorama({
  dataSource,
  today,
  year,
  selection,
  onSelect,
}: HistoricalPanoramaProps) {
  const years = useMemo(() => dataSource.years(), [dataSource]);

  const rows = useMemo<PanoramaRow[]>(
    () => years.map((y) => buildRow(y, dataSource)),
    [dataSource, years],
  );

  const totalObjects = useMemo(
    () =>
      new Set(rows.flatMap((r) => r.objects.map((o) => o.obj.campaign_id))).size,
    [rows],
  );

  // Today 的季节性位置（月-日）：即使今天所在年份不在历史区间内也成立
  const todayFraction = useMemo(() => {
    const doy = dayOfYearISO(today);
    const diy = daysInYear(Number(today.slice(0, 4)));
    return doy / diy;
  }, [today]);

  return (
    <section className="panorama-block" aria-label="Historical Opportunity Panorama">
      <div className="panorama-head">
        <h2 className="panorama-title">历史机会全景</h2>
        <p className="panorama-sub">
          横轴 = 1–12 月 · 纵向 = 历史年份（{years[0]}–{years[years.length - 1]}）·
          共 {totalObjects} 个 Historical Object（正式 Campaign 与 Research Candidate 并列呈现）
        </p>
        <p className="panorama-legend">
          <span className="lg cmp">正式 Campaign</span>
          <span className="lg rc">Research Candidate</span>
          <span className="lg now">Today 竖线</span>
          <span className="lg dim">数据：Research canonical export（非正式历史事实）</span>
        </p>
      </div>

      <div className="panorama-scroll">
        <div className="panorama">
          {/* 月份表头 + 唯一 Today 日期标记 */}
          <div className="pan-month-row">
            <div className="pan-year-axis">年份</div>
            <div className="pan-months">
              {monthFractions(2025).map((f, i) => (
                <span key={i} className="month-label" style={{ left: pct(f) }}>
                  {MONTHS[i]}
                </span>
              ))}
              <span className="pan-today-mark" style={{ left: pct(todayFraction) }}>
                {today.slice(5)}
              </span>
            </div>
          </div>

          {rows.map((row) => (
            <div
              className={`pan-row${row.year === year ? ' on' : ''}`}
              key={row.year}
            >
              <div className="pan-year-axis">
                <span className="pan-year">{row.year}</span>
                <span className="pan-count">
                  {row.campaignCount}C
                  {row.candidateCount > 0 ? ` / ${row.candidateCount}RC` : ''}
                </span>
              </div>
              <div
                className="pan-track"
                style={{ height: row.lanes * LANE_H + (row.lanes - 1) * LANE_GAP + ROW_PAD * 2 }}
              >
                <MonthGrid year={row.year} />
                {row.objects.map((o) => {
                  const obj = o.obj;
                  const selected = isEntrySelected(selection, o.entryId);
                  const isCandidate = obj.kind === 'candidate';
                  return (
                    <div
                      key={o.entryId}
                      className={`pan-obj${isCandidate ? ' rc' : ''}${selected ? ' selected' : ''}`}
                      style={{
                        left: pct(o.boxStart),
                        width: pct(Math.max(o.boxEnd - o.boxStart, 0.006)),
                        top: ROW_PAD + o.lane * (LANE_H + LANE_GAP),
                        height: LANE_H,
                      }}
                      title={`${obj.title}（${obj.start} → ${obj.end}）`}
                      onClick={() =>
                        onSelect({ kind: 'campaign', id: obj.campaign_id, timelineEntryId: o.entryId })
                      }
                    >
                      {o.segs.map((s) => (
                        <span
                          key={s.phase}
                          className={`pan-bar ph-${s.phase}`}
                          style={{
                            left: pct(s.sf),
                            width: pct(Math.max(s.ef - s.sf, 0.006)),
                            background: o.color,
                          }}
                        />
                      ))}
                      {o.peakFrac !== null && (
                        <span className="pan-peak" style={{ left: pct(o.peakFrac) }} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* 贯穿整张全景的**唯一** Today 细红线 */}
          <div className="pan-today-span-layer" aria-hidden="true">
            <TodaySpan frac={todayFraction} />
          </div>
        </div>
      </div>
    </section>
  );
}
