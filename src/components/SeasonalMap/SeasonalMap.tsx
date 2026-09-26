import { useMemo } from 'react';
import { MONTHS, MonthGrid, TodaySpan, monthFractions, pct } from '../Timeline/trackPrimitives';
import type { ThemeAnnualRow, AnnualWindow } from '../../data/timeline/themeAnnualWindow';
import { themeKey } from '../../data/timeline/themeAnnualWindow';
import { themeColorOf, themeOnsetColorOf } from './themeColors';
import { dayOfYearISO, daysInYear } from '../../utils';

/**
 * 历史季节性机会地图（Product 1.1 第二轮 · 首页第一视觉）。
 *
 * 回答的问题是：**一年中历史上哪些时间窗口反复出现过什么类型的题材炒作**。
 *
 * - 横轴 = 1–12 月；纵轴 = **Macro Theme（大主题，一主题一行）**。
 *   不是一 Campaign 一行，也不是一年一行 —— 同主题的历史多次出现**聚合在同一行**。
 * - 每条只画 Research `MAIN_RISE`（主要炒作）在年内的投影；
 *   **不画**完整生命周期 / Decline / End 跨度（那些在主题附页与 CampaignDetail）。
 * - 长周期（跨年、总跨度 > 183 天）只投影**起始月-日**一次，极淡呈现，不铺满首页。
 * - Research Candidate 仅在有 MAIN_RISE 时以弱化样式参与，**不伪装成正式 Campaign**。
 * - Today 只有**一根**贯穿全图的细红线 + 表头一个日期标记，不逐行重复 `TODAY`。
 *
 * 统计口径：「历史 N 次 / 覆盖 N 个可比年份」是**计数事实**，
 * 不是概率、不是胜率、不是推荐分、不是预测。
 */

interface SeasonalMapProps {
  /** 已过滤为「有年内窗口」的主题行 */
  rows: ThemeAnnualRow[];
  today: string;
  /** 当前展开的主题 key（null = 未展开） */
  openTheme: string | null;
  onOpenTheme: (key: string | null) => void;
}

const LANE_H = 9;
const LANE_GAP = 2;
const ROW_PAD = 5;
const MAX_LANES = 4;

/** 比例 → 「M月D日」（用于共识窗口文案） */
function fracToMD(f: number): string {
  const diy = 365;
  let doy = Math.round(f * diy) + 1;
  if (doy < 1) doy = 1;
  if (doy > diy) doy = diy;
  const D = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  let m = 1;
  while (m < 12 && doy > D[m]) m += 1;
  return `${m}月${doy - D[m - 1]}日`;
}

/** 车道打包：同主题内不互相遮挡（最多 MAX_LANES 条） */
function packLanes(windows: AnnualWindow[]): { w: AnnualWindow; lane: number }[] {
  const sorted = [...windows].sort((a, b) => a.startFrac - b.startFrac);
  const laneEnds: number[] = [];
  return sorted.map((w) => {
    let lane = laneEnds.findIndex((end) => w.startFrac >= end - 0.002);
    if (lane === -1) {
      if (laneEnds.length < MAX_LANES) {
        laneEnds.push(w.endFrac);
        lane = laneEnds.length - 1;
      } else {
        lane = MAX_LANES - 1;
        laneEnds[lane] = Math.max(laneEnds[lane], w.endFrac);
      }
    } else {
      laneEnds[lane] = w.endFrac;
    }
    return { w, lane };
  });
}

export function SeasonalMap({ rows, today, openTheme, onOpenTheme }: SeasonalMapProps) {
  // Today 的年内位置（月-日）：季节性地图的横轴是「一年」，与具体年份无关
  const todayFrac = useMemo(() => {
    const y = Number(today.slice(0, 4));
    return (dayOfYearISO(today) - 1) / daysInYear(y);
  }, [today]);

  const packed = useMemo(
    () => rows.map((row) => ({ row, items: packLanes(row.windows) })),
    [rows],
  );

  return (
    <section className="seasonal-block" aria-label="历史季节性机会地图">
      <div className="seasonal-head">
        <h2 className="seasonal-title">历史季节性机会地图</h2>
        <p className="seasonal-legend">
          <span className="lg win">主要炒作窗口</span>
          <span className="lg onset">长周期起始（仅标起点）</span>
          <span className="lg rc">Research Candidate</span>
          <span className="lg now">Today</span>
          <span className="lg-note">柱子颜色 = 该行大主题（分类，不表示强弱 / 涨跌）</span>
        </p>
      </div>

      <div className="seasonal-scroll">
        <div className="seasonal-map">
          {/* 月份表头 + 唯一的 Today 日期标记 */}
          <div className="sm-month-row">
            <div className="sm-axis">大主题</div>
            <div className="sm-months">
              {monthFractions(2025).map((f, i) => (
                <span key={i} className="month-label" style={{ left: pct(f) }}>
                  {MONTHS[i]}
                </span>
              ))}
              <span className="sm-today-mark" style={{ left: pct(todayFrac) }}>
                {today.slice(5)}
              </span>
            </div>
          </div>

          {packed.map(({ row, items }) => {
            const lanes = Math.max(
              1,
              Math.min(items.reduce((m, x) => Math.max(m, x.lane + 1), 1), MAX_LANES),
            );
            const key = themeKey(row);
            const open = openTheme === key;
            // 每个大主题一个分类色（颜色只表示「属于哪个主题」，不表示强弱 / 涨跌）
            const rowColor = themeColorOf(row.theme);
            const rowOnsetColor = themeOnsetColorOf(row.theme);
            return (
              <div
                className={`sm-row${open ? ' on' : ''}`}
                key={key}
                onClick={() => onOpenTheme(open ? null : key)}
                role="button"
                tabIndex={0}
                aria-expanded={open}
                title="查看该主题的历史年度明细"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onOpenTheme(open ? null : key);
                  }
                }}
              >
                <div className="sm-axis">
                  <span className="sm-theme">{row.label}</span>
                  <span className="sm-stat">
                    历史 {row.occurrences} 次 · 覆盖 {row.comparableYears} 个年份
                    {row.consensus
                      ? ` · 集中 ${fracToMD(row.consensus.startFrac)}–${fracToMD(row.consensus.endFrac)}`
                      : ''}
                  </span>
                </div>
                <div
                  className="sm-track"
                  style={{ height: lanes * LANE_H + (lanes - 1) * LANE_GAP + ROW_PAD * 2 }}
                >
                  <MonthGrid year={2025} />
                  {/* 共识窗口：该主题历史主要炒作的集中区间（中位数，确定性聚合） */}
                  {row.consensus && (
                    <span
                      className="sm-consensus"
                      style={{
                        left: pct(row.consensus.startFrac),
                        width: pct(Math.max(row.consensus.endFrac - row.consensus.startFrac, 0.004)),
                      }}
                    />
                  )}
                  {items.map(({ w, lane }) => {
                    const isRc = w.object.kind === 'candidate';
                    const cls = ['sm-bar', w.kind === 'onset' ? 'onset' : 'win', isRc ? 'rc' : '']
                      .filter(Boolean)
                      .join(' ');
                    const tip =
                      w.kind === 'onset'
                        ? `${w.object.title} · ${w.year}（长周期起始，真实区间 ${w.mainRise?.start} → ${w.mainRise?.end}）`
                        : `${w.object.title} · ${w.year}（主要炒作 ${w.mainRise?.start} → ${w.mainRise?.end}）`;
                    return (
                      <span
                        key={`${w.object.campaign_id}@${w.year}`}
                        className={cls}
                        title={tip}
                        style={{
                          left: pct(w.startFrac),
                          width: pct(Math.max(w.endFrac - w.startFrac, 0.004)),
                          top: ROW_PAD + lane * (LANE_H + LANE_GAP),
                          height: LANE_H,
                          // Research Candidate 保持「未晋升」语义：透明填充 + 该主题色虚线描边
                          ...(isRc
                            ? { borderColor: rowColor }
                            : { background: w.kind === 'onset' ? rowOnsetColor : rowColor }),
                        }}
                      />
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* 贯穿整张地图的**唯一** Today 细红线 */}
          <div className="sm-today-layer" aria-hidden="true">
            <TodaySpan frac={todayFrac} />
          </div>
        </div>
      </div>

      <p className="seasonal-hint">点击任一主题 → 查看该主题按年份的历史明细（完整生命周期在对象详情页）。</p>
    </section>
  );
}
