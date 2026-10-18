/**
 * ★★ 外部窗口 × 历史 `MAIN_RISE` 窗口的**并排对照面板**（v0.13）。
 *
 * 位置：`ExternalSeasonTimeline` 某条 MAPPED 线索被点开后展开。
 *
 * ## 两层时间轴（颜色、标题、来源标签都不同）
 *
 * ① **外部资料声称的月份窗口**（琥珀色 · 月份精度 · 外部参考）
 * ② **该宏观主题的历史 `MAIN_RISE` 窗口**（青蓝色 · 来自 Research 投影 · 历史结论）
 *
 * ★ 两层**不合并**成一套窗口；不计算重合率 / 命中率 / 规律成立率；不生成分数、排名或预测。
 */

import {
  THEME_COMPARISON_DISCLAIMER,
  compareExternalToTheme,
  type ComparisonWindow,
} from '../../data/timeline/externalThemeComparison';
import {
  MONTHS,
  type TimelineSegment,
} from '../../data/timeline/externalSeasonalTimeline';
import type { ExternalCalendarEntry } from '../../data/timeline/externalSeasonalCalendar';
import type { ThemeAnnualRow } from '../../data/timeline/themeAnnualWindow';
import { RichText } from '../RichText';

/** 12 等分刻度轨道（两层共用的「尺」） */
function MonthScale() {
  return (
    <div className="ecp-scale" aria-hidden="true">
      {MONTHS.map((m) => (
        <span key={m} className="ecp-scale-tick" style={{ left: `${((m - 1) / 12) * 100}%` }} />
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
                  left: `${((s.months[0] - 1) / 12) * 100}%`,
                  width: `${(s.months.length / 12) * 100}%`,
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

/** 一层历史窗口条（青蓝） */
function HistoryBar({ w }: { w: ComparisonWindow }) {
  const left = w.startFrac * 100;
  const width = Math.max((w.endFrac - w.startFrac) * 100, 0.8);
  return (
    <div
      className={`ecp-bar ecp-bar-hist${w.kind === 'onset' ? ' is-onset' : ''}`}
      style={{ left: `${left}%`, width: `${width}%` }}
      title={w.mainRise
        ? `${w.objectId} · MAIN_RISE ${w.mainRise.start} → ${w.mainRise.end}`
        : `${w.objectId} · 无 MAIN_RISE 起止记录`}
    >
      {w.kind === 'onset' ? '起始' : `${w.year}`}
    </div>
  );
}

/** 历史层：按对象逐行 */
function HistoryLayer({ windows }: { windows: ComparisonWindow[] }) {
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
          {windows.map((w) => (
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
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ExternalThemeComparisonPanel({
  entry,
  segments,
  macroRows,
}: {
  entry: ExternalCalendarEntry;
  /** 该线索的月份段（由外部层复用；无窗口 → 空数组） */
  segments: TimelineSegment[];
  /** **宏观粒度**的主题行 */
  macroRows: readonly ThemeAnnualRow[];
}) {
  const cmp = compareExternalToTheme(entry, macroRows);

  return (
    <div className="ecp" data-ecp-status={cmp.status} aria-label="外部窗口与历史窗口对照">
      <p className="ecp-disc"><RichText text={THEME_COMPARISON_DISCLAIMER} /></p>

      {entry.mapping.status === 'MAPPED' && entry.mapping.basis && (
        <p className="ecp-basis">映射依据（原文）：<RichText text={entry.mapping.basis} /></p>
      )}

      <p className="ecp-note" data-ecp-note="1"><RichText text={cmp.note} /></p>

      <ExternalLayer entry={entry} segments={segments} />
      <HistoryLayer windows={cmp.windows} />

      {cmp.status === 'matched' && cmp.windows.length > 0 && (
        <p className="ecp-hint">
          ★ 两套窗口**并排显示**即可自行比对：外部是月份精度，历史是原始起止日期。
          本面板**不**计算重合率 / 命中率 / 规律成立率，**不**生成分数、排名或预测结论。
        </p>
      )}
    </div>
  );
}
