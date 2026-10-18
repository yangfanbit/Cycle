/**
 * ★★ 外部窗口 × 历史 `MAIN_RISE` 窗口的**并排对照面板**（v0.13 → v0.14）。
 *
 * 位置：`ExternalSeasonTimeline` 某条 MAPPED 线索被点开后展开。
 *
 * ## 两层时间轴（颜色、标题、来源标签都不同）
 *
 * ① **外部资料声称的月份窗口**（琥珀色 · 月份精度 · 外部参考）
 * ② **该宏观主题的历史 `MAIN_RISE` 窗口**（青蓝色 · 来自 Research 投影）
 *
 * ★★ v0.14：两层共用**同一把月份坐标尺**（`externalSeasonalTimeline` 的
 *   `monthToMonthFraction` / `fracToMonthFraction` / `monthFractionToPct`）——
 *   1–12 月刻度、外部条、历史条全在 `mf ∈ [0,12]` 上定位。
 *   外部只走整数月边界（保持月份精度），历史 frac 经换算对齐；两边都不重算原始日期。
 *
 * ★ 两层**不合并**成一套窗口；不计算重合率 / 命中率 / 规律成立率；不生成分数、排名或预测。
 */

import {
  fracToMonthFraction,
  monthFractionToPct,
  monthToMonthFraction,
  MONTHS,
  type TimelineSegment,
} from '../../data/timeline/externalSeasonalTimeline';
import {
  THEME_COMPARISON_DISCLAIMER,
  compareExternalToTheme,
  type ComparisonWindow,
} from '../../data/timeline/externalThemeComparison';
import type { ExternalCalendarEntry } from '../../data/timeline/externalSeasonalCalendar';
import type { ThemeAnnualRow } from '../../data/timeline/themeAnnualWindow';
import { RichText } from '../RichText';

/** 未进入窗口的原因 → 人话（逐条展示，不合并） */
const OUTSIDE_REASON_LABEL: Record<'no-main-rise' | 'main-rise-not-projected', string> = {
  'no-main-rise': '没有 MAIN_RISE 记录 → 无法投影',
  'main-rise-not-projected': '有 MAIN_RISE 记录但投影为空 → 待核对（异常路径）',
};

/** 12 等分刻度轨道（两层共用的「尺」） */
function MonthScale() {
  return (
    <div className="ecp-scale" aria-hidden="true">
      {MONTHS.map((m) => (
        <span
          key={m}
          className="ecp-scale-tick"
          style={{ left: monthFractionToPct(monthToMonthFraction(m)) }}
        />
      ))}
    </div>
  );
}

/** 外部层：月份段（琥珀） */
function ExternalLayer({ entry, segments }: {
  entry: ExternalCalendarEntry; segments: TimelineSegment[];
}) {
  return (
    <div className="ecp-layer ecp-layer-ext">
      <h5 className="ecp-layer-title">
        <span className="ecp-tag ecp-tag-ext">外部参考</span>
        外部资料声称的月份窗口
        <span className="ecp-layer-src">来源：外部季节性日历（月份精度）</span>
      </h5>
      {segments.length === 0 ? (
        <p className="ecp-empty">
          该外部线索**无固定月份窗口** → 不绘制外部月份条（不虚构）。
        </p>
      ) : (
        <>
          <div className="ecp-track">
            <MonthScale />
            {segments.map((s) => (
              <div
                key={s.months.join('-')}
                className="ecp-bar ecp-bar-ext"
                style={{
                  left: monthFractionToPct(monthToMonthFraction(s.months[0])),
                  width: monthFractionToPct(s.months.length),
                }}
                title={`${s.rawText}（月份精度）`}
              >
                {s.months.length === 1
                  ? `${s.months[0]} 月`
                  : `${s.months[0]}–${s.months[s.months.length - 1]} 月`}
              </div>
            ))}
          </div>
          <p className="ecp-raw">原文：{segments.map((s) => s.rawText).join('；')}</p>
        </>
      )}
    </div>
  );
}

/** 一层历史窗口条（青蓝）—— 位置由 frac 经月份坐标换算得到 */
function HistoryBar({ w }: { w: ComparisonWindow }) {
  const left = fracToMonthFraction(w.startFrac);
  // 同一把尺上算宽度；单日窗口给最小可视宽度（不能因此夸大时长）
  const width = Math.max(fracToMonthFraction(w.endFrac) - left, 0.8 / 12);
  return (
    <div
      className={`ecp-bar ecp-bar-hist${w.kind === 'onset' ? ' is-onset' : ''}`}
      style={{ left: monthFractionToPct(left), width: monthFractionToPct(width) }}
      title={w.mainRise
        ? `${w.objectId} · MAIN_RISE ${w.mainRise.start} → ${w.mainRise.end}`
        : `${w.objectId} · 无 MAIN_RISE 起止记录`}
    >
      {w.kind === 'onset' ? '起始' : `${w.year}`}
    </div>
  );
}

/** 历史层：按对象逐行 */
function HistoryLayer({
  windows,
  onOpenObject,
  canOpenObject,
}: {
  windows: ComparisonWindow[];
  /** ★ v0.14：进入对象详情（复用 App 的 selection 流程，不另建弹窗） */
  onOpenObject?: (objectId: string, year: number) => void;
  /** 该对象能否通过现有详情流程解析（不能 → 不渲染按钮，给真实说明） */
  canOpenObject?: (objectId: string) => boolean;
}) {
  return (
    <div className="ecp-layer ecp-layer-hist">
      <h5 className="ecp-layer-title">
        <span className="ecp-tag ecp-tag-hist">Research 历史</span>
        该宏观主题的历史 `MAIN_RISE` 窗口
        <span className="ecp-layer-src">来源：Research 投影（长周期只投影起始位置）</span>
      </h5>
      {windows.length === 0 ? (
        <p className="ecp-empty">当前研究数据里**没有**可对照的历史窗口 —— 不补造。</p>
      ) : (
        <ul className="ecp-hlist">
          {windows.map((w) => {
            // 同一对象的多个投影段：每段都能进同一个详情（详情本身按对象呈现）
            // ★ 两道检查，缺一不可（v0.13 MapLink 教训：不给「看起来能点但没反应」的东西）：
            //   ① 页面注入了 onOpenObject（有接线）；
            //   ② 该对象能通过现有详情流程解析（canOpenObject 未注入时默认可解析）。
            const resolvable = canOpenObject ? canOpenObject(w.objectId) : true;
            return (
              <li key={`${w.objectId}-${w.year}-${w.startFrac}`} data-ecp-hist={w.objectId}>
                <div className="ecp-htrack">
                  <MonthScale />
                  <HistoryBar w={w} />
                </div>
                <div className="ecp-hmeta">
                  <strong>{w.title}</strong>
                  <code>{w.objectId}</code>
                  <span className={`ecp-kind ecp-kind-${w.objectKind}`}>
                    {w.objectKind === 'campaign' ? 'Campaign' : 'Research Candidate'}
                  </span>
                  <span className="ecp-year">{w.year} 年</span>
                  {w.mainRise
                    ? <span className="ecp-dates">原始 MAIN_RISE {w.mainRise.start} → {w.mainRise.end}</span>
                    : <span className="ecp-dates ecp-dates-missing">MAIN_RISE 起止未记录</span>}
                  {w.kind === 'onset' && (
                    <span className="ecp-onset-note">（长周期：仅投影起始位置）</span>
                  )}
                  <span className="ecp-actions">
                    {onOpenObject && resolvable ? (
                      <button
                        type="button"
                        className="ecp-open-btn"
                        onClick={() => onOpenObject(w.objectId, w.year)}
                      >
                        查看对象详情
                      </button>
                    ) : resolvable ? (
                      <span className="ecp-open-na">本页未接线对象详情</span>
                    ) : (
                      <span className="ecp-open-na">
                        该对象无法通过现有详情流程解析（不渲染无效按钮）
                      </span>
                    )}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/** 计数摘要（v0.14：段数 / 去重对象数 / 未进入窗口的对象可展开） */
function CountSummary({
  windowSegments,
  windowCounts,
  objectsOutsideWindows,
  totalObjects,
}: {
  windowSegments: number;
  windowCounts: { campaign: number; candidate: number };
  objectsOutsideWindows: readonly {
    objectId: string; title: string;
    objectKind: 'campaign' | 'candidate';
    reason: 'no-main-rise' | 'main-rise-not-projected';
  }[];
  totalObjects: number;
}) {
  const outside = objectsOutsideWindows.length;
  return (
    <dl className="ecp-counts" data-ecp-counts="1">
      <dt>历史窗口投影段数</dt>
      <dd>{windowSegments} 段</dd>
      <dt>投影涉及对象（去重）</dt>
      <dd>
        {windowCounts.campaign} 个 Campaign + {windowCounts.candidate} 个 Research Candidate
        <span className="ecp-count-note">
          （同一对象跨年可有多段投影，段数不是对象数）
        </span>
      </dd>
      {outside > 0 && (
        <>
          <dt>未进入窗口的对象</dt>
          <dd>
            <details className="ecp-outside">
              <summary>
                {outside} 个（该主题共 {totalObjects} 个对象）
              </summary>
              <ul className="ecp-outside-list">
                {objectsOutsideWindows.map((o) => (
                  <li key={o.objectId}>
                    <strong>{o.title}</strong>
                    <code>{o.objectId}</code>
                    <span className={`ecp-kind ecp-kind-${o.objectKind}`}>
                      {o.objectKind === 'campaign' ? 'Campaign' : 'Research Candidate'}
                    </span>
                    <span className="ecp-outside-reason">{OUTSIDE_REASON_LABEL[o.reason]}</span>
                  </li>
                ))}
              </ul>
            </details>
          </dd>
        </>
      )}
    </dl>
  );
}

export function ExternalThemeComparisonPanel({
  entry,
  segments,
  macroRows,
  onOpenObject,
  canOpenObject,
}: {
  entry: ExternalCalendarEntry;
  /** 该线索的月份段（由外部层复用；无窗口 → 空数组） */
  segments: TimelineSegment[];
  /** **宏观粒度**的主题行 */
  macroRows: readonly ThemeAnnualRow[];
  /** ★ v0.14：打开历史对象详情（复用 App 既有 selection / CampaignDetail 流程） */
  onOpenObject?: (objectId: string, year: number) => void;
  /** ★ v0.14：对象能否被现有详情流程解析（不可解析 → 不渲染无效按钮） */
  canOpenObject?: (objectId: string) => boolean;
}) {
  const cmp = compareExternalToTheme(entry, macroRows);
  // 主题下对象总数：从 macroRows 现取（matched 才有；真实空态不显示这块）
  const row = cmp.theme
    ? macroRows.find((r) => r.theme === cmp.theme) ?? null
    : null;

  return (
    <div className="ecp" data-ecp-status={cmp.status} aria-label="外部窗口与历史窗口对照">
      <p className="ecp-disc"><RichText text={THEME_COMPARISON_DISCLAIMER} /></p>

      {entry.mapping.status === 'MAPPED' && entry.mapping.basis && (
        <p className="ecp-basis">映射依据（原文）：<RichText text={entry.mapping.basis} /></p>
      )}

      <p className="ecp-note" data-ecp-note="1"><RichText text={cmp.note} /></p>

      <ExternalLayer entry={entry} segments={segments} />

      {cmp.status === 'matched' && cmp.windows.length > 0 && row && (
        <CountSummary
          windowSegments={cmp.windows.length}
          windowCounts={cmp.windowCounts}
          objectsOutsideWindows={cmp.objectsOutsideWindows}
          totalObjects={row.objects.length}
        />
      )}

      <HistoryLayer
        windows={cmp.windows}
        onOpenObject={onOpenObject}
        canOpenObject={canOpenObject}
      />

      {cmp.status === 'matched' && cmp.windows.length > 0 && (
        <p className="ecp-hint">
          ★ 两套窗口**并排显示**即可自行比对：外部是月份精度，历史是原始起止日期。
          本面板**不**计算重合率 / 命中率 / 规律成立率，**不**生成分数、排名或预测结论。
        </p>
      )}
    </div>
  );
}
