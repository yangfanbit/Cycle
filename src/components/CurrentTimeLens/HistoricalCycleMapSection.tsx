/**
 * Historical Cycle Map Section —— 「当前周 ↔ 历史时间窗口」横向观察（Historical Cycle Map v0.1）。
 *
 * ## 定位
 * 回答：**「现在这一周，在历史上有没有出现过类似的周期窗口？这些周期在当时处于什么阶段？」**
 *
 * 与其它视角的分工（**不得合并**）：
 * - **Historical Cycle Map** = 时间窗口浏览（Calendar Window + Lifecycle Position）
 * - **Structural Analogy** = 当前结构与历史结构的**正式对应**
 *
 * ## 边界（不得违反）
 * - **不排序**：无 similarity score / ranking / probability / Top-N / 「最强」「最像」。
 *   超过屏幕承载量时只用**筛选**（时间窗口 / Macro Theme / Theme Cycle / Lifecycle）。
 * - **周级分辨率**：日期只用于排序与窗口相交；**不制造虚假的日期精确度**。
 * - **UNKNOWN ≠ 不存在**：无阶段信息显示 `UNKNOWN`，并说明「资料不足」。
 * - **不重定义 Lifecycle**：阶段原样来自 Research `phases`。
 * - **不联网 / 无 LLM**：只消费既有 `TimelineDataSource`。
 */

import { useMemo, useState } from 'react';

import type { Selection } from '../Timeline/Timeline';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import {
  cycleMapFacets,
  filterCycleMapEntries,
  historicalCycleMap,
  spanRatio,
  type CycleMapEntry,
  type WeekWindow,
} from '../../data/timeline/historicalCycleMap';

/** 窗口默认跨度：当前周 ± 2 周（共 5 周）。 */
const WINDOW_HALF_SPAN = 2;

export function HistoricalCycleMapSection({
  dataSource,
  today,
  onSelect,
}: {
  dataSource: TimelineDataSource;
  today: string;
  onSelect: (sel: Selection) => void;
}) {
  const map = useMemo(() => historicalCycleMap(dataSource, today), [dataSource, today]);
  const [macroTheme, setMacroTheme] = useState<string | null>(null);
  const [themeCycle, setThemeCycle] = useState<string | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  const [showAllYears, setShowAllYears] = useState(false);

  const facets = useMemo(() => cycleMapFacets(map.allEntries), [map.allEntries]);
  const filter = { macroTheme, themeCycle, stage };

  const filteredYears = useMemo(
    () =>
      map.years
        .map((y) => ({ ...y, entries: filterCycleMapEntries(y.entries, filter) }))
        .filter((y) => y.entries.length > 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [map.years, macroTheme, themeCycle, stage],
  );

  const hasFilter = Boolean(macroTheme || themeCycle || stage);
  const visibleYears = showAllYears ? filteredYears : filteredYears.slice(0, 4);
  const totalShown = filteredYears.reduce((n, y) => n + y.entries.length, 0);

  return (
    <section className="hcm-sec" aria-label="Historical Cycle Map">
      <h4 className="hcm-title">
        Historical Cycle Map（历史周期地图）
        <span className="hcm-tag">周级 · 时间窗口浏览</span>
      </h4>
      <p className="hcm-intro">
        回答：<strong>现在这一周，历史上有没有出现过类似的周期窗口？这些周期在当时走到了哪一步？</strong>
        本视图只做<strong>时间窗口浏览</strong>，不做相似度、不排序、不评分。
      </p>

      {/* ---------- 现在这一周在哪里 ---------- */}
      <div className="hcm-now">
        <div className="hcm-now-head">
          <span className="hcm-now-label">当前交易周</span>
          <span className="hcm-now-week">{map.currentWeek.label}</span>
          <span className="hcm-now-range">
            {map.currentWeek.start} ~ {map.currentWeek.end}
          </span>
        </div>
        <ol className="hcm-weeks" aria-label={`当前周 ± ${WINDOW_HALF_SPAN} 周`}>
          {map.weeks.map(({ window, offset, entries }) => (
            <li
              key={window.label}
              className={`hcm-week${offset === 0 ? ' is-now' : ''}`}
              title={`${window.start} ~ ${window.end}`}
            >
              <span className="hcm-week-off">{offset === 0 ? '本周' : `${offset > 0 ? '+' : ''}${offset}周`}</span>
              <span className="hcm-week-label">{window.label}</span>
              <span className="hcm-week-count">{entries.length} 个周期</span>
            </li>
          ))}
        </ol>
        <p className="hcm-note">
          窗口 = 当前周 ± {WINDOW_HALF_SPAN} 周（周级分辨率）。日期只用于排序与窗口相交，
          <strong>不要求日级精度</strong>。
        </p>
      </div>

      {/* ---------- 筛选（筛选 ≠ 排序） ---------- */}
      {map.allEntries.length > 0 && (
        <div className="hcm-filters" role="group" aria-label="按维度筛选（不是排序）">
          <FilterRow
            label="Macro Theme"
            value={macroTheme}
            options={facets.macroThemes}
            onChange={setMacroTheme}
          />
          <FilterRow
            label="Theme Cycle"
            value={themeCycle}
            options={facets.themeCycles}
            onChange={setThemeCycle}
          />
          <FilterRow label="Lifecycle" value={stage} options={facets.stages} onChange={setStage} />
          {hasFilter && (
            <button
              type="button"
              className="hcm-chip"
              onClick={() => {
                setMacroTheme(null);
                setThemeCycle(null);
                setStage(null);
              }}
            >
              清除筛选
            </button>
          )}
        </div>
      )}

      {/* ---------- 历史时间窗口 ---------- */}
      {map.isEmpty ? (
        <p className="hcm-empty">
          研究覆盖范围内，这一周附近没有记录到历史周期 —— 这不代表「历史上没有发生」，只代表当前研究快照内没有记录。
        </p>
      ) : filteredYears.length === 0 ? (
        <p className="hcm-empty">该筛选下没有历史周期。</p>
      ) : (
        <>
          <p className="hcm-order-note">
            按<strong>年份</strong>升序排列（不是从强到弱）；年份内按案例开始日期升序。
            共 {totalShown} 个历史周期落在这一日历窗口内。
          </p>
          <ul className="hcm-years">
            {visibleYears.map((y) => (
              <li key={y.year} className="hcm-year">
                <div className="hcm-year-head">
                  <span className="hcm-year-num">{y.year}</span>
                  <span className="hcm-year-win">
                    {y.window.start} ~ {y.window.end}
                  </span>
                  <span className="hcm-year-count">{y.entries.length} 个周期</span>
                </div>
                <ul className="hcm-entries">
                  {y.entries.map((e) => (
                    <CycleRow key={e.campaignId} e={e} window={y.window} onSelect={onSelect} />
                  ))}
                </ul>
              </li>
            ))}
          </ul>
          {filteredYears.length > 4 && (
            <button
              type="button"
              className="hcm-chip hcm-more"
              onClick={() => setShowAllYears((v) => !v)}
              aria-expanded={showAllYears}
            >
              {showAllYears ? '收起（仅显示前 4 个年份）' : `显示全部 ${filteredYears.length} 个年份`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

/* ================= 单行 ================= */

function CycleRow({
  e,
  window,
  onSelect,
}: {
  e: CycleMapEntry;
  window: WeekWindow;
  onSelect: (sel: Selection) => void;
}) {
  const { left, width } = spanRatio(e, window);
  const stageClass = e.stageStatus === 'UNKNOWN' ? 'is-unknown' : 'is-known';

  return (
    <li className="hcm-entry">
      <button
        type="button"
        className="hcm-entry-btn"
        onClick={() => onSelect({ kind: 'campaign', id: e.navigation.id })}
      >
        <span className="hcm-entry-title">{e.title}</span>
        {e.macroTheme && <span className="hcm-chip-sm">{e.macroTheme}</span>}
        {e.themeCycleId && <span className="hcm-chip-sm hcm-chip-cycle">{e.themeCycleId}</span>}
        <span className={`hcm-stage ${stageClass}`}>
          {e.stageLabel}
          {e.stageStatus === 'ENTERED_IN_WINDOW' && <span className="hcm-entered">· 本窗口内开始</span>}
        </span>
        <span className="hcm-open-hint">查看历史案例 →</span>
      </button>

      {/* 横向 span：该案例在窗口中的位置（**不是分数**） */}
      <div className="hcm-span" aria-hidden="true">
        <span className="hcm-span-bar" style={{ left: `${left * 100}%`, width: `${width * 100}%` }} />
      </div>

      <div className="hcm-entry-meta">
        <span className="hcm-dim">
          案例区间 {e.caseStart} ~ {e.caseEnd}
        </span>
        {e.stageStatus === 'UNKNOWN' && (
          <span className="hcm-dim">
            该窗口锚点不落在任何已记录生命周期区间内（UNKNOWN）—— <strong>不是</strong>「没有阶段」。
          </span>
        )}
      </div>
    </li>
  );
}

/* ================= 筛选行 ================= */

function FilterRow({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string | null;
  options: string[];
  onChange: (v: string | null) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div className="hcm-filter-row">
      <span className="hcm-filter-label">{label}</span>
      <button
        type="button"
        className={`hcm-chip${value === null ? ' is-on' : ''}`}
        aria-pressed={value === null}
        onClick={() => onChange(null)}
      >
        全部
      </button>
      {options.map((o) => (
        <button
          key={o}
          type="button"
          className={`hcm-chip${value === o ? ' is-on' : ''}`}
          aria-pressed={value === o}
          onClick={() => onChange(value === o ? null : o)}
        >
          {o}
        </button>
      ))}
    </div>
  );
}
