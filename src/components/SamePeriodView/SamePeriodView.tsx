import { useMemo, useState } from 'react';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import { themeRowsOf, type ThemeCampaignEntry, type TimelineThemeRow } from '../../data/timeline/themeRows';
import { samePeriodWindow } from '../../data/timeline/timelineAdapter';
import { DATA_STATUS_CLASS, DATA_STATUS_LABEL } from '../labels';
import type { Selection } from '../Timeline/Timeline';

interface SamePeriodViewProps {
  dataSource: TimelineDataSource;
  /** A股市场日期基准（Asia/Shanghai） */
  today: string;
  /** 现有选中态（与 Timeline / Lens 共用，不新建 state management） */
  selection?: Selection;
  /** 现有选中回调（点击明细 → 打开 Campaign Detail） */
  onSelect?: (sel: Selection) => void;
}

const MONTH_LABEL = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

/**
 * 历史同周期查看（V1.8.1：主题级视图）。
 *
 * 一行 = 一个【主主题】（历史上同期出现过的主题），而不是一行一个 Campaign / 个股。
 * 同主题下的多条独立行情（正式 Campaign / Research Candidate）仍逐条展示、互不合并：
 * 点击主题行展开明细，明细再点击进入 Campaign Detail。
 *
 * 边界：仅历史列表（不是统计模型、不做相似度评分、不构成任何预测）；
 * 主题分组来自导出既有 themes 字段，不新建主题、不落库。
 */
export function SamePeriodView({ dataSource, today, selection, onSelect }: SamePeriodViewProps) {
  // 默认选中当前月份（TODAY 只表示日期位置，不代表当前市场状态）
  const [month, setMonth] = useState(() => Number(today.slice(5, 7)));
  // 默认展开第一个主题行（如有），其余折叠
  const [expanded, setExpanded] = useState<string | null>(null);

  const result = useMemo(() => themeRowsOf(dataSource, month), [dataSource, month]);
  const windowSample = samePeriodWindow(2026, month); // 仅用于展示窗口口径

  const rows = result.rows;
  // 默认展开：月份切换后若 expanded 失效则回落到首个主题行
  const firstKey = rows[0]?.themeKey ?? null;
  const openKey = expanded !== null && rows.some((r) => r.themeKey === expanded) ? expanded : firstKey;

  if (rows.length === 0) {
    return (
      <section className="sp-view">
        <h3 className="tl-layer-title">历史同周期主题</h3>
        <p className="sp-sub">
          选择月份，查看历史各年在同期窗口（约 {windowSample.start.slice(5)} ~ {windowSample.end.slice(5)}）内出现过哪些主题；
          仅历史列表，不是统计模型，不构成任何预测。
        </p>
        <div className="sp-months">
          {MONTH_LABEL.map((label, i) => (
            <button
              key={label}
              className={`sp-month${month === i + 1 ? ' active' : ''}`}
              onClick={() => setMonth(i + 1)}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="phase-text">当前研究数据未覆盖：该月份窗口内暂无研究数据（不是「历史没有机会」）。</p>
      </section>
    );
  }

  return (
    <section className="sp-view">
      <h3 className="tl-layer-title">历史同周期主题</h3>
      <p className="sp-sub">
        选择月份，查看历史各年在同期窗口（约 {windowSample.start.slice(5)} ~ {windowSample.end.slice(5)}）内出现过哪些
        <strong>主题</strong>；一行 = 一个主题，展开可见该主题下的独立行情（同主题多条不合并）。
        仅历史列表，不是统计模型，不构成任何预测。
      </p>
      <div className="sp-months">
        {MONTH_LABEL.map((label, i) => (
          <button
            key={label}
            className={`sp-month${month === i + 1 ? ' active' : ''}`}
            onClick={() => setMonth(i + 1)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="sp-themes">
        {rows.map((row) => (
          <ThemeRowBlock
            key={row.themeKey}
            row={row}
            open={openKey === row.themeKey}
            onToggle={() => setExpanded(openKey === row.themeKey ? '' : row.themeKey)}
            selection={selection}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}

/** 主题行：标题 + 年份 + 代表阶段 + 相关概念；点击展开独立行情明细 */
function ThemeRowBlock({
  row,
  open,
  onToggle,
  selection,
  onSelect,
}: {
  row: TimelineThemeRow;
  open: boolean;
  onToggle: () => void;
  selection?: Selection;
  onSelect?: (sel: Selection) => void;
}) {
  return (
    <div className={`sp-theme-row${open ? ' open' : ''}`}>
      <button className="sp-theme-head" onClick={onToggle} aria-expanded={open}>
        <span className="sp-theme-caret">{open ? '▾' : '▸'}</span>
        <span className="sp-theme-title">{row.title}</span>
        <span className="sp-theme-years">
          {row.years.map((y) => (
            <span className="sp-theme-year" key={y}>
              {y}
            </span>
          ))}
        </span>
        <span className="sp-theme-phase">{row.phaseSummary}</span>
        <span className="sp-theme-count">{row.campaigns.length} 条</span>
      </button>
      {!row.untitled && row.relatedConcepts.length > 0 && (
        <div className="sp-theme-related">
          相关概念：
          {row.relatedConcepts.map((c) => (
            <span className="sp-related-chip" key={c}>
              {c}
            </span>
          ))}
        </div>
      )}
      {open && (
        <div className="sp-campaigns">
          {row.campaigns.map((e) => (
            <CampaignEntryLine
              key={e.campaign_id}
              entry={e}
              active={selection?.kind === 'campaign' && selection.id === e.campaign_id}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/** 独立行情明细行（一条 = 一个 Campaign / RC，不合并） */
function CampaignEntryLine({
  entry,
  active,
  onSelect,
}: {
  entry: ThemeCampaignEntry;
  active: boolean;
  onSelect?: (sel: Selection) => void;
}) {
  const statusLabel = DATA_STATUS_LABEL[entry.status];
  return (
    <button
      className={`sp-item sp-item-line ${active ? 'on ' : ''}${DATA_STATUS_CLASS[entry.status]}`}
      onClick={() => onSelect?.({ kind: 'campaign', id: entry.campaign_id })}
      title={`${entry.title}｜历史区间 ${entry.start} → ${entry.end}\n${
        entry.phaseLabel ? `当时处于：${entry.phaseLabel}` : '历史阶段未标注'
      }\n数据状态：${statusLabel}${entry.status !== 'verified' ? '（非正式历史事实）' : ''}`}
    >
      <span className="sp-line-year">{entry.year}</span>
      {entry.kind === 'candidate' && <em className="rc-badge">RC</em>}
      <span className="sp-line-title">{entry.title}</span>
      <span className="sp-dates">
        {entry.start.slice(5)}~{entry.end.slice(5)}
        {entry.openEnded ? '（观察中）' : ''}
      </span>
      <span className="sp-line-phase">
        {entry.phaseLabel ? (
          <>
            当时处于：<strong>{entry.phaseLabel}</strong>
            {entry.phaseAlso.length > 0 && <span className="sp-phase-also">，另有 {entry.phaseAlso.join(' / ')}</span>}
          </>
        ) : (
          <span className="sp-phase-none">历史阶段未标注</span>
        )}
      </span>
      {entry.hasMajorConflict && (
        <span className="sp-conflict-flag" title="该行情存在重大日期口径分歧（研究分歧，未自行取舍）">
          ⚠ 研究分歧
        </span>
      )}
      <span className={`st-badge ${DATA_STATUS_CLASS[entry.status]}`}>{statusLabel}</span>
    </button>
  );
}
