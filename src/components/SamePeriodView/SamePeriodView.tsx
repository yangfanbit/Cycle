import { useMemo, useState } from 'react';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import {
  themeRowsOf,
  type ThemeCampaignEntry,
  type TimelineThemeRow,
} from '../../data/timeline/themeRows';
import { samePeriodWindow } from '../../data/timeline/timelineAdapter';
import { campaignDrivers } from '../../data/timeline/timelineAdapter';
import {
  PRE_OBSERVATION_HINT,
  PRE_OBSERVATION_LABEL,
} from '../../data/timeline/preObservation';
import { DATA_STATUS_CLASS, DATA_STATUS_LABEL, ROLE_LABEL } from '../labels';
import type { Selection } from '../Timeline/Timeline';

interface SamePeriodViewProps {
  dataSource: TimelineDataSource;
  /** A股市场日期基准（Asia/Shanghai） */
  today: string;
  /** 现有选中态（与 Timeline / Lens 共用，不新建 state management） */
  selection?: Selection;
  /** 现有选中回调（仅 Level 2「查看完整历史案例」使用；Level 1 不打开侧栏） */
  onSelect?: (sel: Selection) => void;
}

const MONTH_LABEL = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

/**
 * 历史同周期查看（V1.8.2：主题级 + 两级详情）。
 *
 * 一行 = 一个【主主题】。两级详情：
 *   Level 1（Inline Summary）：点击主题行 → 在下方就地展开摘要，**不离开主页面**、不遮挡 Timeline；
 *   Level 2（Full Campaign Detail）：摘要内点「查看完整历史案例」才打开现有 CampaignDetail。
 *
 * 边界：仅历史列表（不是统计模型、不做相似度评分、不构成任何预测）；
 * 主题分组来自导出既有 themes 字段，不新建主题、不落库。
 */
export function SamePeriodView({ dataSource, today, selection, onSelect }: SamePeriodViewProps) {
  // 默认选中当前月份（TODAY 只表示日期位置，不代表当前市场状态）
  const [month, setMonth] = useState(() => Number(today.slice(5, 7)));
  // 展开的主题行（Level 1 Inline Summary）
  const [openThemeKey, setOpenThemeKey] = useState<string | null>(null);
  // Level 1 内选中的明细（用于 Inline Summary 的「可能相关因素」聚焦）
  // 保存的是 **entryId**（`campaign_id@展示年份`），不是 campaign_id ——
  // 跨年 Campaign 同 id 会在多年度各成一条明细，必须用明细级身份区分（见 entryIdentity.ts）。
  const [focusEntryId, setFocusEntryId] = useState<string | null>(null);

  const result = useMemo(() => themeRowsOf(dataSource, month), [dataSource, month]);
  const windowSample = samePeriodWindow(2026, month); // 仅用于展示窗口口径

  const rows = result.rows;
  const openRow = rows.find((r) => r.themeKey === openThemeKey) ?? null;

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
        <strong>主题</strong>；一行 = 一个主题。点击主题就地展开摘要（不离开本页），需要时再进入完整历史案例。
        仅历史列表，不是统计模型，不构成任何预测。
      </p>
      <div className="sp-months">
        {MONTH_LABEL.map((label, i) => (
          <button
            key={label}
            className={`sp-month${month === i + 1 ? ' active' : ''}`}
            onClick={() => {
              setMonth(i + 1);
              setOpenThemeKey(null);
              setFocusEntryId(null);
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="sp-themes">
        {rows.map((row) => (
          <div key={row.themeKey}>
            <ThemeRowSummary
              row={row}
              open={openThemeKey === row.themeKey}
              onToggle={() => {
                const next = openThemeKey === row.themeKey ? null : row.themeKey;
                setOpenThemeKey(next);
                // 默认聚焦【最后一条明细】：用 entryId（不是 campaign_id，跨年会重复）
                setFocusEntryId(next ? row.campaigns[row.campaigns.length - 1].entryId : null);
              }}
            />
            {/* Level 1：Inline Summary —— 就地展开，不打开侧栏、不遮挡 Timeline */}
            {openThemeKey === row.themeKey && (
              <InlineThemeSummary
                row={row}
                focusEntryId={focusEntryId}
                onFocus={setFocusEntryId}
                selection={selection}
                onOpenFull={(id) => onSelect?.({ kind: 'campaign', id })}
              />
            )}
          </div>
        ))}
      </div>

      {openRow && (
        <p className="sp-footnote">
          摘要为历史研究信息；{PRE_OBSERVATION_LABEL} {PRE_OBSERVATION_HINT}
        </p>
      )}
    </section>
  );
}

/** 主题行（折叠头 + 年份 + 代表阶段 + 相关概念） */
function ThemeRowSummary({
  row,
  open,
  onToggle,
}: {
  row: TimelineThemeRow;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={`sp-theme-row${open ? ' open' : ''}`}>
      <button className="sp-theme-head" onClick={onToggle} aria-expanded={open} aria-controls={`theme-${row.themeKey}`}>
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
    </div>
  );
}

/**
 * Level 1 Inline Summary（主题级摘要）：
 *   Theme / Year / Phase / 关键阶段 / 可能相关因素 / 数据状态 / RC / Conflict。
 * 就地渲染在主页面内，不打开侧栏；只有点「查看完整历史案例」才进入 Level 2。
 */
function InlineThemeSummary({
  row,
  focusEntryId,
  onFocus,
  selection,
  onOpenFull,
}: {
  row: TimelineThemeRow;
  /** 明细唯一身份（`campaign_id@展示年份`）；null → 默认取最后一条 */
  focusEntryId: string | null;
  /** 回传明细唯一身份（entryId），不是 campaign_id */
  onFocus: (entryId: string) => void;
  selection?: Selection;
  onOpenFull: (id: string) => void;
}) {
  // 外部选中（展示实例）优先：Timeline / Lens 选中的条目若落在本行，则本行聚焦它
  // —— 三处选择语义一致（entryId = 展示实例；campaign_id = 完整历史案例）。
  const selectedEntryId = selection?.kind === 'campaign' ? selection.timelineEntryId : undefined;
  const focusedEntryId = row.campaigns.some((e) => e.entryId === selectedEntryId)
    ? selectedEntryId
    : focusEntryId;
  // 用 entryId 匹配：跨年 Campaign 同 campaign_id 多条明细时才能区分到具体年份
  const focus =
    row.campaigns.find((e) => e.entryId === focusedEntryId) ??
    row.campaigns[row.campaigns.length - 1];

  return (
    <div className="sp-inline" id={`theme-${row.themeKey}`}>
      {/* 主题 / 年份 / 阶段 */}
      <div className="sp-inline-head">
        <span className="sp-inline-kicker">主题摘要</span>
        <span className="sp-inline-title">{row.title}</span>
        <span className="sp-inline-years">{row.years.join(' · ')}</span>
        <span className="sp-inline-phase">代表阶段：{row.primaryPhase ?? '阶段未标注'}</span>
      </div>

      {/* 年份切换（同主题多条独立行情，仍逐条保留）
          tab identity = entryId（campaign_id@展示年份）：
          跨年 Campaign 同 id 会在多年度各成一条 → 必须按明细区分 key / active / focus。 */}
      {row.campaigns.length > 1 && (
        <div className="sp-inline-years-tabs">
          {row.campaigns.map((e) => (
            <button
              key={e.entryId}
              className={`sp-year-tab${e.entryId === focus.entryId ? ' active' : ''}`}
              onClick={() => onFocus(e.entryId)}
            >
              {e.year}
              {e.kind === 'candidate' && <em className="rc-badge">RC</em>}
            </button>
          ))}
        </div>
      )}

      {/* 数据状态 / RC / Conflict */}
      <div className="sp-inline-flags">
        <span className={`st-badge ${DATA_STATUS_CLASS[focus.status]}`}>
          {DATA_STATUS_LABEL[focus.status]}
        </span>
        {focus.kind === 'candidate' && (
          <span className="rc-badge" title="Research Candidate：研究候选，非正式 Historical Campaign">
            Research Candidate
          </span>
        )}
        {focus.hasMajorConflict && (
          <span className="sp-conflict-flag" title="该行情存在重大日期口径分歧（研究分歧，未自行取舍）">
            ⚠ 研究分歧
          </span>
        )}
        {focus.status !== 'verified' && <span className="sp-inline-warn">非正式历史事实</span>}
      </div>

      {/* 关键阶段：历史区间 + 当时处于 */}
      <dl className="sp-inline-kv">
        <dt>历史区间</dt>
        <dd>
          {focus.start} → {focus.end}
          {focus.openEnded ? '（观察中，结束日期为年末近似）' : ''}
        </dd>

        <dt>当时处于</dt>
        <dd>
          {focus.phaseLabel ? (
            <>
              <strong>{focus.phaseLabel}</strong>
              {focus.phaseAlso.length > 0 && (
                <span className="sp-phase-also">，另有 {focus.phaseAlso.join(' / ')}</span>
              )}
            </>
          ) : (
            <span className="sp-phase-none">历史阶段未标注</span>
          )}
          <span className="sp-inline-note">（历史窗口内的阶段，不是当前状态）</span>
        </dd>

        {/* 提前观察参考区：三层链 Pre-observation Reference → Early Signal? → Formation */}
        {focus.preObservation && (
          <>
            <dt>{PRE_OBSERVATION_LABEL}</dt>
            <dd>
              <span className="sp-pre-window">
                {focus.preObservation.preObservation.start} → {focus.preObservation.preObservation.end}
              </span>
              <span className="sp-inline-note">（{PRE_OBSERVATION_HINT}）</span>
              <div className="sp-pre-chain">
                <span className="sp-pre-step pre">{PRE_OBSERVATION_LABEL}</span>
                {focus.preObservation.hasEarlySignal && (
                  <>
                    <span className="sp-pre-arrow">→</span>
                    <span className="sp-pre-step es">早期信号</span>
                  </>
                )}
                <span className="sp-pre-arrow">→</span>
                <span className="sp-pre-step formation">主题形成 {focus.preObservation.formation}</span>
              </div>
            </dd>
          </>
        )}

        <dt>题材</dt>
        <dd>
          {focus.campaign.themes.length === 0 ? (
            <span className="phase-text">题材信息待补充</span>
          ) : (
            focus.campaign.themes.map((t) => (
              <span className="tag" key={t.name}>
                {t.name}
                {t.role ? `（${ROLE_LABEL[t.role] ?? t.role}）` : ''}
              </span>
            ))
          )}
        </dd>
      </dl>

      {/* 可能相关因素（统一称「可能相关因素」；不由 Event 自动生成） */}
      <PossibleFactors entry={focus} />

      {/* 进入 Level 2 的唯一显式动作 */}
      <div className="sp-inline-actions">
        <button
          className={`sp-btn-full${selection?.kind === 'campaign' && selection.id === focus.campaign_id ? ' on' : ''}`}
          onClick={() => onOpenFull(focus.campaign_id)}
        >
          查看完整历史案例 →
        </button>
        <span className="sp-inline-hint">完整案例含生命周期、精确日期、日期候选、分歧、龙头、事件与来源。</span>
      </div>
    </div>
  );
}

/** 可能相关因素：沿用 campaignDrivers（Research 归因），语义为「可能」，非因果、非建议 */
function PossibleFactors({ entry }: { entry: ThemeCampaignEntry }) {
  const d = campaignDrivers(entry.campaign);
  const all = [...d.start, ...d.accelerate, ...d.turn, ...d.end];
  const seen = new Set<string>();
  const labels: string[] = [];
  for (const t of all) {
    const k = t.trim();
    if (k.length === 0 || seen.has(k)) continue;
    seen.add(k);
    labels.push(k);
  }
  return (
    <div className="sp-inline-factors">
      <h4 className="sp-inline-factors-title">可能相关因素</h4>
      {labels.length === 0 ? (
        <p className="sp-inline-note">当前研究数据未覆盖：暂无可用归因（不编造）。</p>
      ) : (
        <>
          <div className="sp-factor-chips">
            {labels.map((l) => (
              <span className="sp-factor-chip" key={l} title={l}>
                {l}
              </span>
            ))}
          </div>
          <p className="sp-inline-note">
            来自 Research 层归因，语义为「可能相关因素」，不是因果结论、不是买卖建议。
          </p>
        </>
      )}
    </div>
  );
}
