/**
 * ★★ 外部季节性**参考时间轴**（ThreeC 1.3 · v0.12）。
 *
 * ## 位置与职责
 *
 * 在 `ExternalSeasonalRadar` 内部、详细卡片**之前**。把 25 条外部线索按 1–12 月铺开，
 * 让用户一眼看到「哪些月份有哪些外部线索」。
 *
 * ## 硬约束
 *
 * - **全部 25 条默认可见**：23 条上轴（24 段窗口 → 跨年拆分后 28 段），
 *   2 条无固定窗口（EXT-23 / EXT-24）单列，**不因没有月份而消失**。
 * - **月份精度**：不显示任何日级日期（源数据只有 `MONTH`）。
 * - **一律外部参考**：`MAPPED` 只表示名称映射，**不是** ThreeC 验证结论；
 *   每条都带「外部参考」标记。
 * - **跳转只在索引真有关系时出现**：`eventMapByExternalId()` 有值才给按钮；
 *   否则明写「未建历史题材地图」，**不虚构入口**。
 * - **不与 ThreeC 历史地图同色**：本区用中性/琥珀色系 + 「外部参考」徽标，
 *   与上方季节性地图的主题色区分。
 */
import { useMemo } from 'react';

import {
  EXTERNAL_SOURCE_LABEL,
  MATURITY_LABEL,
  windowTextOf,
  type ExternalCalendarEntry,
} from '../../data/timeline/externalSeasonalCalendar';
import {
  EXTERNAL_TIMELINE_NOTE,
  MONTHS,
  buildExternalTimeline,
  crossYearNote,
  isActiveInMonth,
  segmentAt,
  type TimelineRow,
} from '../../data/timeline/externalSeasonalTimeline';
import { eventMapByExternalId } from '../../data/timeline/historicalEventMaps';
import { RichText } from '../RichText';

/** 该外部线索是否已有历史题材地图（有则给出跳转） */
function themeMapOf(entryId: string) {
  return eventMapByExternalId(entryId);
}

function MapLink({ entry, onOpenMap }: {
  entry: ExternalCalendarEntry; onOpenMap?: (themeId: string) => void;
}) {
  const map = themeMapOf(entry.id);
  if (!map) {
    return <span className="est-no-map">未建历史题材地图</span>;
  }
  return (
    <button
      type="button"
      className="est-map-link"
      data-map-theme={map.theme_id}
      onClick={() => onOpenMap?.(map.theme_id)}
    >
      历史题材地图 →
    </button>
  );
}

/** 一条线索的名称单元格（名称 / 类别 / 窗口 / 映射状态 / 跳转） */
function RowLabel({ row, onOpenMap }: { row: TimelineRow; onOpenMap?: (themeId: string) => void }) {
  const e = row.entry;
  return (
    <th scope="row" className="est-label" data-entry-id={e.id}>
      <span className="est-name">{e.name}</span>
      <span className="est-tags">
        <span className="est-cat">{e.category}</span>
        <span className="est-ext">外部参考</span>
        {e.mapping.status === 'MAPPED'
          ? <span className="est-mapped">已映射 · {e.mapping.macro_theme}</span>
          : <span className="est-unmapped">未映射</span>}
      </span>
      <span className="est-window">
        {e.windows.length > 0 ? windowTextOf(e) : '无固定月份窗口'}
      </span>
      <MapLink entry={e} onOpenMap={onOpenMap} />
    </th>
  );
}

export function ExternalSeasonTimeline({
  entries,
  allEntries,
  categories,
  category,
  onCategory,
  onOpenMap,
}: {
  /** 当前筛选后的条目（由雷达统一筛选，保证时间轴与详细卡片口径一致） */
  entries: readonly ExternalCalendarEntry[];
  /** 全部条目（用于显示「全部 N 条」与总数） */
  allEntries: readonly ExternalCalendarEntry[];
  categories: readonly string[];
  category: string;
  onCategory: (c: string) => void;
  onOpenMap?: (themeId: string) => void;
}) {
  const timeline = useMemo(() => buildExternalTimeline(entries), [entries]);
  const allTimeline = useMemo(() => buildExternalTimeline(allEntries), [allEntries]);

  const countOf = (c: string) => (c === 'ALL'
    ? allEntries.length
    : allEntries.filter((e) => e.category === c).length);

  return (
    <section className="est" aria-label="外部季节性参考时间轴">
      <div className="est-head">
        <h3 className="est-title">外部季节性参考时间轴</h3>
        <span className="est-badge">{EXTERNAL_SOURCE_LABEL}</span>
      </div>

      <p className="est-note"><RichText text={EXTERNAL_TIMELINE_NOTE} /></p>
      <p className="est-totals" data-est-totals="1">
        {category === 'ALL' ? (
          <>共 <strong>{timeline.totals.entries}</strong> 条线索：
            <strong>{timeline.totals.withWindow}</strong> 条有月份窗口 ·{' '}
            <strong>{timeline.totals.withoutWindow}</strong> 条无固定窗口 ·
            已映射 {timeline.totals.mapped} / 未映射 {timeline.totals.unmapped}</>
        ) : (
          <>当前类别「{category}」：<strong>{timeline.totals.entries}</strong> 条
            （全部 {allEntries.length} 条）</>
        )}
        <span className="est-carry">{crossYearNote(allTimeline)}</span>
      </p>

      <div className="est-filters" role="group" aria-label="按类别筛选（不是排序）">
        {categories.map((c) => (
          <button
            key={c}
            type="button"
            className={`est-chip${category === c ? ' is-on' : ''}`}
            aria-pressed={category === c}
            onClick={() => onCategory(c)}
          >
            {c === 'ALL' ? '全部类别' : c}
            <span className="est-chip-n">{countOf(c)}</span>
          </button>
        ))}
      </div>

      {/* ---------- 月份轴（有窗口的条目） ---------- */}
      {timeline.axisRows.length === 0 ? (
        <p className="est-empty">该类别下没有带固定月份窗口的线索。</p>
      ) : (
        <div className="est-table-wrap">
          <table className="est-table">
            <caption>
              1–12 月为<strong>月份精度</strong>（不推断日级日期）；
              填充格 = 该外部线索声称覆盖该月。跨年窗口拆到年末与年初两段显示。
            </caption>
            <thead>
              <tr>
                <th scope="col" className="est-corner">线索 / 窗口</th>
                {MONTHS.map((m) => (
                  <th key={m} scope="col" className="est-month-head">{m}月</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeline.axisRows.map((row) => (
                <tr key={row.entry.id} data-est-row={row.entry.id}>
                  <RowLabel row={row} onOpenMap={onOpenMap} />
                  {MONTHS.map((m) => {
                    const seg = segmentAt(row, m);
                    const on = isActiveInMonth(row, m);
                    return (
                      <td
                        key={m}
                        className={`est-cell${on ? ' is-on' : ''}${seg?.fromCrossYear ? ' is-cross' : ''}`}
                        data-month={m}
                        data-active={on ? '1' : '0'}
                        title={on ? seg?.rawText : undefined}
                      >
                        {on && <span className="est-dot" aria-hidden="true" />}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- 无固定窗口（事件驱动） ---------- */}
      {timeline.noWindowRows.length > 0 && (
        <div className="est-nowin" data-est-nowin={timeline.noWindowRows.length}>
          <h4 className="est-nowin-title">
            事件驱动 / 无固定窗口（{timeline.noWindowRows.length} 条）
            <span className="est-nowin-hint">没有月份窗口，故不上轴 —— 但同样属于外部参考</span>
          </h4>
          <ul className="est-nowin-list">
            {timeline.noWindowRows.map((row) => (
              <li key={row.entry.id} data-est-nowin-id={row.entry.id}>
                <span className="est-name">{row.entry.name}</span>
                <span className="est-cat">{row.entry.category}</span>
                <span className="est-ext">外部参考</span>
                {row.entry.mapping.status === 'MAPPED'
                  ? <span className="est-mapped">已映射 · {row.entry.mapping.macro_theme}</span>
                  : <span className="est-unmapped">未映射</span>}
                <span className="est-window">{MATURITY_LABEL[row.entry.maturity]}</span>
                <MapLink entry={row.entry} onOpenMap={onOpenMap} />
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="est-legend">
        <span className="est-legend-dot" aria-hidden="true" /> 填充 = 外部资料声称的窗口内 ·
        「已映射」只表示名称对应 ThreeC 宏观主题，<strong>不是</strong> ThreeC 验证结论 ·
        与上方历史季节性地图<strong>不同色、不同源</strong>
      </p>
    </section>
  );
}
