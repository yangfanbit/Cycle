/**
 * ★★ 外部季节性**参考时间轴**（ThreeC 1.3 · v0.12；v0.13 加历史窗口对照与研究请求入口）。
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
 *   ★ v0.13 修：未提供 `onOpenMap` 时**不渲染按钮**（不给「看起来能点但点了没反应」的东西）。
 * - **不与 ThreeC 历史地图同色**：本区用中性/琥珀色系 + 「外部参考」徽标，
 *   与上方季节性地图的主题色区分；历史对照层用青蓝色。
 */
import { Fragment, useMemo, useState } from 'react';

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
  type TimelineSegment,
} from '../../data/timeline/externalSeasonalTimeline';
import { eventMapByExternalId } from '../../data/timeline/historicalEventMaps';
import type { ThemeAnnualRow } from '../../data/timeline/themeAnnualWindow';
import { RichText } from '../RichText';
import { ExternalThemeComparisonPanel } from './ExternalThemeComparisonPanel';

/** 该外部线索是否已有历史题材地图（有则给出跳转） */
function themeMapOf(entryId: string) {
  return eventMapByExternalId(entryId);
}

/**
 * ★ v0.25：无地图线索的**下一步**是否应给「带入研究请求草稿」。
 * 判据 = v0_2 逐项核验结论的 `next_step.kind`（DRAFT / OBSERVE），
 * **不再**看 `mapping.status` —— v0_2 之后「已映射宏观主题」与「有地图」不是一回事
 * （映射 ≠ 规律成立 ≠ 已有历史事件地图）。REJECTED（NONE）不给入口： verdict 已说明依据。
 */
function wantsDraftEntry(entry: ExternalCalendarEntry): boolean {
  if (themeMapOf(entry.id)) return false;
  const kind = entry.verification?.next_step.kind;
  return kind === 'DRAFT' || kind === 'OBSERVE';
}

function MapLink({ entry, onOpenMap }: {
  entry: ExternalCalendarEntry; onOpenMap?: (themeId: string) => void;
}) {
  const map = themeMapOf(entry.id);
  if (!map) {
    return <span className="est-no-map">未建历史题材地图</span>;
  }
  // ★ v0.13：没有回调就**不给按钮**—— 只给事实说明，不假装可点
  if (!onOpenMap) {
    return <span className="est-map-plain">已有历史题材地图（本页未接线跳转）</span>;
  }
  return (
    <button
      type="button"
      className="est-map-link"
      data-map-theme={map.theme_id}
      onClick={() => onOpenMap(map.theme_id)}
    >
      历史题材地图 →
    </button>
  );
}

/** 一条线索的名称单元格（名称 / 类别 / 窗口 / 映射状态 / 操作） */
function RowLabel({
  row,
  onOpenMap,
  onCompare,
  onRequestDraft,
  compareOpen,
}: {
  row: TimelineRow;
  onOpenMap?: (themeId: string) => void;
  onCompare?: (entry: ExternalCalendarEntry) => void;
  onRequestDraft?: (entry: ExternalCalendarEntry) => void;
  compareOpen?: boolean;
}) {
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
      <span className="est-actions">
        <MapLink entry={e} onOpenMap={onOpenMap} />
        {e.mapping.status === 'MAPPED' && onCompare && (
          <button
            type="button"
            className="est-cmp-btn"
            aria-expanded={Boolean(compareOpen)}
            onClick={() => onCompare(e)}
          >
            {compareOpen ? '收起历史窗口对照' : '对照历史窗口'}
          </button>
        )}
        {wantsDraftEntry(e) && onRequestDraft && (
          <button
            type="button"
            className="est-draft-btn"
            onClick={() => onRequestDraft(e)}
          >
            带入研究请求
          </button>
        )}
      </span>
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
  onRequestDraft,
  onOpenObject,
  canOpenObject,
  macroRows,
  today,
}: {
  /** 当前筛选后的条目（由雷达统一筛选，保证时间轴与详细卡片口径一致） */
  entries: readonly ExternalCalendarEntry[];
  /** 全部条目（用于显示「全部 N 条」与总数） */
  allEntries: readonly ExternalCalendarEntry[];
  categories: readonly string[];
  category: string;
  onCategory: (c: string) => void;
  onOpenMap?: (themeId: string) => void;
  /** ★ v0.13：未映射线索 → 带入现有研究请求草稿（由 App 注入） */
  onRequestDraft?: (entry: ExternalCalendarEntry) => void;
  /** ★ v0.14：历史窗口 → 对象详情（复用 App 的 selection / CampaignDetail 流程） */
  onOpenObject?: (objectId: string, year: number) => void;
  /** ★ v0.14：对象能否被现有详情流程解析（不可解析 → 不渲染无效按钮） */
  canOpenObject?: (objectId: string) => boolean;
  /** **宏观粒度**的主题行（v0.13：历史窗口对照；与首页当前粒度无关） */
  macroRows: readonly ThemeAnnualRow[];
  /** 当前日期（ISO）→ 只用于标出当前月份，**不产生任何涨跌含义** */
  today?: string;
}) {
  const timeline = useMemo(() => buildExternalTimeline(entries), [entries]);
  const allTimeline = useMemo(() => buildExternalTimeline(allEntries), [allEntries]);
  const [openCompareId, setOpenCompareId] = useState<string | null>(null);

  // ★ 当前日历月份（1..12）—— 只表示「现在是几月」，不带任何市场含义
  const currentMonth = today && /^\d{4}-\d{2}-\d{2}$/.test(today)
    ? Number(today.slice(5, 7))
    : null;

  const countOf = (c: string) => (c === 'ALL'
    ? allEntries.length
    : allEntries.filter((e) => e.category === c).length);

  const toggleCompare = (e: ExternalCalendarEntry) =>
    setOpenCompareId(openCompareId === e.id ? null : e.id);

  /** 某条线索的展开行（历史窗口对照） */
  const compareRow = (entry: ExternalCalendarEntry, segments: TimelineSegment[]) => (
    <tr className="est-detail-row" data-est-detail={entry.id}>
      <td colSpan={MONTHS.length + 1}>
        <ExternalThemeComparisonPanel
          entry={entry}
          segments={segments}
          macroRows={macroRows}
          onOpenObject={onOpenObject}
          canOpenObject={canOpenObject}
        />
      </td>
    </tr>
  );

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
        {currentMonth !== null && (
          <span className="est-current-month" data-est-current-month={currentMonth}>
            当前月份：{currentMonth} 月（仅日历事实，无涨跌含义）
          </span>
        )}
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
              {currentMonth !== null && `深色表头 = 当前月份（${currentMonth} 月）。`}
            </caption>
            <thead>
              <tr>
                <th scope="col" className="est-corner">线索 / 窗口</th>
                {MONTHS.map((m) => (
                  <th
                    key={m}
                    scope="col"
                    className={`est-month-head${currentMonth === m ? ' is-current' : ''}`}
                  >
                    {m}月{currentMonth === m && <span className="est-now">今</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeline.axisRows.map((row) => (
                <Fragment key={row.entry.id}>
                  <tr data-est-row={row.entry.id}
                      className={row.entry.mapping.status === 'MAPPED' ? 'is-mapped' : 'is-unmapped'}>
                    <RowLabel
                      row={row}
                      onOpenMap={onOpenMap}
                      onCompare={onCompareToggle(setOpenCompareId, openCompareId)}
                      onRequestDraft={onRequestDraft}
                      compareOpen={openCompareId === row.entry.id}
                    />
                      {MONTHS.map((m) => {
                        const seg = segmentAt(row, m);
                        const on = isActiveInMonth(row, m);
                        return (
                          <td
                            key={m}
                            className={`est-cell${on ? ' is-on' : ''}${seg?.fromCrossYear ? ' is-cross' : ''}${currentMonth === m ? ' is-current' : ''}`}
                            data-month={m}
                            data-active={on ? '1' : '0'}
                            title={on ? seg?.rawText : undefined}
                          >
                            {on && <span className="est-dot" aria-hidden="true" />}
                          </td>
                        );
                      })}
                  </tr>
                  {openCompareId === row.entry.id && compareRow(row.entry, row.segments)}
                </Fragment>
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
            {timeline.noWindowRows.map((row) => {
              const e = row.entry;
              const open = openCompareId === e.id;
              return (
                <li key={e.id} data-est-nowin-id={e.id}>
                  <span className="est-name">{e.name}</span>
                  <span className="est-cat">{e.category}</span>
                  <span className="est-ext">外部参考</span>
                  {e.mapping.status === 'MAPPED'
                    ? <span className="est-mapped">已映射 · {e.mapping.macro_theme}</span>
                    : <span className="est-unmapped">未映射</span>}
                  <span className="est-window">
                    无固定月份窗口 · {MATURITY_LABEL[e.maturity]}
                  </span>
                  <span className="est-actions">
                    <MapLink entry={e} onOpenMap={onOpenMap} />
                    {e.mapping.status === 'MAPPED' && (
                      <button
                        type="button"
                        className="est-cmp-btn"
                        aria-expanded={open}
                        onClick={() => toggleCompare(e)}
                      >
                        {open ? '收起历史窗口对照' : '对照历史窗口'}
                      </button>
                    )}
                    {wantsDraftEntry(e) && onRequestDraft && (
                      <button
                        type="button"
                        className="est-draft-btn"
                        onClick={() => onRequestDraft(e)}
                      >
                        带入研究请求
                      </button>
                    )}
                  </span>
                  {open && (
                    <ExternalThemeComparisonPanel
                      entry={e}
                      segments={[]}
                      macroRows={macroRows}
                    />
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <p className="est-legend">
        <span className="est-legend-dot" aria-hidden="true" /> 填充 = 外部资料声称的窗口内 ·
        「已映射」只表示名称对应 ThreeC 宏观主题，<strong>不是</strong> ThreeC 验证结论 ·
        点「对照历史窗口」可在下方看到该主题的历史 `MAIN_RISE` 窗口（<strong>并排对照，
        不是统计验证</strong>）
      </p>
    </section>
  );
}

/** 让 `Fragment` 里的键与状态切换更直白的小工具（axisRows.map 使用） */
function onCompareToggle(
  setOpen: (v: string | null) => void,
  current: string | null,
) {
  return (e: ExternalCalendarEntry) => setOpen(current === e.id ? null : e.id);
}
