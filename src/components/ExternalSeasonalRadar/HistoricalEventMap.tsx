/**
 * 通用历史事件地图 —— 题材无关的事件展示组件。
 *
 * 交互：`题材 → 年份 → 历史事件 → 相关证券 → 证据与行情`
 *
 * ★ 由 `HistoricalEventsDoc` + `ThemeDisplay` 驱动，**不按题材硬编码**。
 * ★ 流感题材的 `FluEventMap` 是本组件的薄封装，既有语义（业务机制 / 负面参照 / 证据边界）不变。
 */
import { useState } from 'react';
import {
  BUSINESS_MECHANISM_CAVEAT,
  COMPARABLE_LABEL,
  CROSS_YEAR_CAVEAT,
  CROSS_YEAR_OUTCOME_LABEL,
  EVENT_STUDY_LABEL,
  EVIDENCE_LEVEL_LABEL,
  MARKET_DATA_STATUS_LABEL,
  MARKET_PERFORMANCE_CAVEAT,
  PARTICIPANT_CATEGORY_LABEL,
  WINDOW_BASIS_LABEL,
  WINDOW_TYPE_LABEL,
  crossYearComparisonOf,
  eventStudyState,
  eventsByClass,
  marketDataCoverage,
  type CrossYearYear,
  type HistoricalEvent,
  type HistoricalEventsDoc,
  type HistoricalParticipant,
  type ThemeDisplay,
} from '../../data/timeline/historicalEventMaps';
import { EmpiricalProbabilityBlock } from './EmpiricalProbabilityBlock';

/**
 * ★★ 源数据文本里的 `**强调**` → `<strong>`。
 *
 * 索引 JSON 的 `display.note` / `class_caveats` 是**研究侧写的 Markdown**，
 * 直接塞进 JSX 会**原样显示两个星号**（本项目已知陷阱）。这里统一渲染。
 */
function RichText({ text }: { text: string }) {
  const parts = text.split('**');
  return (
    <>
      {parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>))}
    </>
  );
}

/** 纯文本化：`title` 属性里不能放标签，只能把 `**` 去掉（可见文本仍走 RichText） */
function plain(text: string): string {
  return text.split('**').join('');
}

/** 中国股市惯例：涨红跌绿 */
function cls(v?: number | null): string {
  if (v == null) return '';
  return v > 0 ? 'num-up' : v < 0 ? 'num-down' : '';
}

function fmtPct(v?: number | null): string {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
}

/** ★ 超额（pp）：不可计算时显示 `—`，**不得**补 0 */
function fmtPp(v?: number | null): string {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1) + 'pp';
}

/** ★ 导出以便测试直接渲染（页面仍只经 `EventCard` 使用） */
export function MarketPerformanceBlock({ e }: { e: HistoricalEvent }) {
  const mp = e.market_performance;
  if (!mp) return null;
  const bench = Object.entries(mp.benchmark)[0];
  const rows = Object.entries(mp.by_security);
  return (
    <>
      <h5>实测行情（窗口 {mp.window?.[0]} ~ {mp.window?.[1]}）</h5>
      <p className="fem-perf-caveat">{MARKET_PERFORMANCE_CAVEAT}</p>
      <div className="fem-table-wrap">
        <table className="fem-table">
          <thead>
            <tr>
              <th>标的</th><th>交易日</th><th>区间涨跌</th><th>至高点</th>
              <th>高点日</th><th>自高点回撤</th>
              <th title="区间涨跌 − 基准区间涨跌（excess_period_pp）">区间超额</th>
              <th title="至高点涨幅 − 基准至高点涨幅（excess_to_high_pp）">至高点超额</th>
            </tr>
          </thead>
          <tbody>
            {bench && (
              <tr className="fem-bench-row">
                <td>{bench[0]}（基准）</td>
                <td>{bench[1].trading_days ?? '—'}</td>
                <td>{fmtPct(bench[1].period_return_pct)}</td>
                <td>{fmtPct(bench[1].to_high_pct)}</td>
                <td>{bench[1].high?.date ?? '—'}</td>
                <td>{fmtPct(bench[1].max_drawdown_from_high_pct)}</td>
                <td>—</td>
                <td>—</td>
              </tr>
            )}
            {rows.map(([sid, st]) => (
              <tr key={sid}>
                <td><code>{sid}</code></td>
                <td>{st.trading_days ?? '—'}</td>
                <td className={cls(st.period_return_pct)}>{fmtPct(st.period_return_pct)}</td>
                <td className={cls(st.to_high_pct)}>{fmtPct(st.to_high_pct)}</td>
                <td>{st.high?.date ?? '—'}</td>
                <td>{fmtPct(st.max_drawdown_from_high_pct)}</td>
                <td className={cls(st.excess_period_pp)}>{fmtPp(st.excess_period_pp)}</td>
                <td className={cls(st.excess_to_high_pp)}>{fmtPp(st.excess_to_high_pp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="fem-perf-note">
        ★ <strong>两列超额口径不同，不得混用</strong>：「区间超额」= 区间涨跌 − 基准区间涨跌
        （<code>excess_period_pp</code>）；「至高点超额」= 至高点涨幅 − 基准至高点涨幅
        （<code>excess_to_high_pp</code>）。不可计算时显示 <code>—</code>，<strong>不补 0</strong>。
      </p>
      <p className="fem-perf-note">
        ★ 「报道当日涨幅」见上方各标的（<code>reported_move</code>），
        与这里的<strong>区间行情是两回事</strong>。
      </p>
    </>
  );
}

/** ★ 导出以便测试直接渲染（页面仍只经 `EventCard` 使用） */
export function ParticipantRow({ p, e }: { p: HistoricalParticipant; e: HistoricalEvent }) {
  // ★ 四类状态：已计算 / 该窗口未计算 / 行情不可得 / 覆盖不足 —— 不得用 0 代表缺失
  const coverage = marketDataCoverage(e, p.security_id);
  const status = coverage.status;
  const mdClass = status === 'COMPUTED' ? 'ok'
    : status === 'UNAVAILABLE' ? 'miss'
      : status === 'INSUFFICIENT' ? 'warn' : 'pending';
  return (
    <li className="fem-part">
      <div className="fem-part-head">
        <span className="fem-part-name">{p.name}</span>
        <span className="fem-part-ticker">{p.ticker}</span>
        <span className={`fem-part-cat cat-${p.category.toLowerCase()}`}>
          {PARTICIPANT_CATEGORY_LABEL[p.category]}
        </span>
        {p.evidence_level && (
          <span className={`fem-part-ev ev-${p.evidence_level.toLowerCase()}`}>
            {EVIDENCE_LEVEL_LABEL[p.evidence_level]}
          </span>
        )}
        {p.reported_move && <span className="fem-part-move">报道当日 {p.reported_move}</span>}
        <span className={`fem-part-md ${mdClass}`} data-market-status={status}
              title={status === 'COMPUTED' ? undefined : plain(coverage.reasons.join('；'))}>
          {status === 'COMPUTED'
            ? `行情: ${p.market_data}`
            : MARKET_DATA_STATUS_LABEL[status]}
        </span>
      </div>
      {p.business_mechanism && (
        <p className="fem-part-biz">
          <strong>业务机制</strong>：<RichText text={p.business_mechanism} />
          {p.business_mechanism_caveat && (
            <span className="fem-part-biz-caveat"><RichText text={p.business_mechanism_caveat} /></span>
          )}
        </p>
      )}
      <p className="fem-part-why"><strong>纳入理由</strong>：<RichText text={p.rationale} /></p>
      <p className="fem-part-src"><strong>来源</strong>：<RichText text={p.source} /></p>
      {p.note && <p className="fem-part-note"><RichText text={p.note} /></p>}
    </li>
  );
}

/**
 * ★★ 事件卡**展开后的正文**（单独导出：`EventCard` 只负责折叠状态，
 *   正文抽出来才能被测试直接渲染 —— 单一实现，不为测试复制逻辑）。
 */
export function EventCardBody({ e, classCaveat }: { e: HistoricalEvent; classCaveat?: string }) {
  const conceptsNote = e.three_peaks_note ?? e.four_concepts_note;
  return (
    <div className="fem-event-body">
          {e.campaign_facts && (
            <>
              <h5>Campaign 事实</h5>
              <p className="fem-media-note">
                <code>{e.campaign_facts.campaign_id}</code> ·{' '}
                start {e.campaign_facts.start ?? '—'} · <strong>peak_date {e.campaign_facts.peak_date ?? '—'}</strong> ·{' '}
                end {e.campaign_facts.end ?? '—'}
                {e.campaign_facts.note && <span className="fem-campaign-note"><RichText text={e.campaign_facts.note} /></span>}
              </p>
            </>
          )}

          {e.media_label_note && (
            <>
              <h5>媒体标签 vs 可核实催化</h5>
              <p className="fem-media-note"><RichText text={e.media_label_note} /></p>
            </>
          )}

          <h5>催化时间线</h5>
          {e.catalysts.length === 0 ? (
            <p className="fem-empty">（本轮未核实到催化事件）</p>
          ) : (
            <ul className="fem-cats">
              {e.catalysts.map((c) => (
                <li key={c.date + c.text.slice(0, 12)}>
                  <span className="fem-cat-date">{c.date}</span>
                  <span className="fem-cat-text"><RichText text={c.text} /></span>
                  <span className="fem-cat-src">{c.source}</span>
                </li>
              ))}
            </ul>
          )}

          {e.phases && e.phases.length > 0 && (
            <>
              <h5>阶段划分（Campaign 记录）</h5>
              <ul className="fem-cats">
                {e.phases.map((ph) => (
                  <li key={ph.phase_id}>
                    <span className="fem-cat-date">{ph.start} → {ph.end}</span>
                    {/* ★ 研究侧字段名是 `stage`；`phase_type` 为旧别名 —— 两读，都不许渲染成空 */}
                    <span className="fem-cat-text">
                      <strong>{ph.phase_type ?? ph.stage ?? '（阶段名未标注）'}</strong>：
                      <RichText text={ph.description} />
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* ★ 2026-10-16：标题不再硬编码「历史炒作标的」——
             机制池事件的 participants 是**研究池**（事后重建、未按收益筛选），
             不是炒作池；池的性质由各标的 `category` / `rationale` 逐条说明。 */}
          <h5>事件相关标的（{e.participants.length} 只）</h5>
          <p className="fem-biz-caveat">{BUSINESS_MECHANISM_CAVEAT}</p>
          {e.participants.length === 0 ? (
            <p className="fem-empty">（未建立候选清单）</p>
          ) : (
            <ul className="fem-parts">
              {e.participants.map((p) => <ParticipantRow key={p.security_id} p={p} e={e} />)}
            </ul>
          )}

          <MarketPerformanceBlock e={e} />

          <h5>报道当日涨幅</h5>
          <p className="fem-perf-note"><RichText text={e.observed_performance.note} /></p>
          {e.observed_performance.by_security ? (
            <ul className="fem-perf">
              {Object.entries(e.observed_performance.by_security).map(([k, v]) => (
                <li key={k}><code>{k}</code> {v}</li>
              ))}
            </ul>
          ) : e.observed_performance.reported_same_day_moves
            && Object.keys(e.observed_performance.reported_same_day_moves).length > 0 ? (
            /* ★ 2026-10-16 修复：`by_security` 为 null **不代表没有报道当日涨幅** ——
               研究侧把同期报道点名的当日涨幅放在 `reported_same_day_moves`
               （此前从不渲染 → 页面恒显「无行情」，而 note 又引用不存在的「上表」）。 */
            <ul className="fem-perf">
              {Object.entries(e.observed_performance.reported_same_day_moves).map(([k, v]) => (
                <li key={k}><code>{k}</code> {v}</li>
              ))}
            </ul>
          ) : (
            <p className="fem-empty">（无同期报道点名的当日涨幅 → 不展示数字，**不**以 0 涨幅代替）</p>
          )}

          <h5>缺失 / 不确定事项</h5>
          <ul className="fem-gaps">
            {e.known_gaps.map((g) => <li key={g.slice(0, 20)}><RichText text={g} /></li>)}
          </ul>
    </div>
  );
}

/** 事件卡：头部（可折叠）+ 展开后的 `EventCardBody` */
export function EventCard({ e, classCaveat }: { e: HistoricalEvent; classCaveat?: string }) {
  const [open, setOpen] = useState(false);
  const state = eventStudyState(e);
  return (
    <li className="fem-event" data-event-id={e.event_id}
        data-event-class={e.event_class ?? ''} data-study-state={state}>
      <button type="button" className="fem-event-head" aria-expanded={open}
              onClick={() => setOpen((v) => !v)}>
        <span className="fem-event-year">{e.year}</span>
        <span className="fem-event-label"><RichText text={e.label} /></span>
        <span className={`fem-event-state st-${state.toLowerCase()}`}>
          {EVENT_STUDY_LABEL[state] ?? state}
        </span>
        <span className="fem-event-caret">{open ? '收起' : '展开'}</span>
      </button>

      <p className="fem-event-win">窗口：<RichText text={e.window_text} /></p>
      <p className="fem-event-basis">依据：<RichText text={e.evidence_basis} /></p>

      {classCaveat && <p className="fem-adjacent-caveat"><RichText text={classCaveat} /></p>}
      {open && <EventCardBody e={e} classCaveat={classCaveat} />}
    </li>
  );
}

/* ---------------------------------------------- 跨年份比较（默认折叠；无数据不渲染） */

/** ★ 摘要按固定顺序统计 outcome（未知码原样显示码值，**不猜含义**） */
const CROSS_YEAR_SUMMARY_ORDER = [
  'UP', 'ALL_DOWN', 'UNDERPERFORM', 'DIVERGENT', 'NO_CLEAR_REACTION',
  'NO_EVENT', 'INSUFFICIENT_DATA', 'WINDOW_MISMATCH', 'NOT_COMPARABLE',
];

function outcomeLabel(code: string): string {
  return CROSS_YEAR_OUTCOME_LABEL[code] ?? code;
}

/** 结果颜色类（未知码 → 中性，不给颜色暗示） */
function outcomeClass(code: string): string {
  if (code === 'UP') return 'up';
  if (code === 'ALL_DOWN' || code === 'UNDERPERFORM') return 'down';
  if (code === 'DIVERGENT' || code === 'NO_CLEAR_REACTION') return 'flat';
  return 'muted';
}

/** 折叠态摘要：`N 个年份 · 一致上涨 X · …`（只列出现过的 outcome） */
function crossYearSummary(years: CrossYearYear[]): string {
  const counts = new Map<string, number>();
  for (const y of years) counts.set(y.outcome, (counts.get(y.outcome) ?? 0) + 1);
  const known = CROSS_YEAR_SUMMARY_ORDER.filter((c) => counts.has(c));
  const unknown = [...counts.keys()].filter((k) => !CROSS_YEAR_SUMMARY_ORDER.includes(k)).sort();
  const parts = [...known, ...unknown].map((c) => `${outcomeLabel(c)} ${counts.get(c)}`);
  return [`${years.length} 个年份`, ...parts].join(' · ');
}

/** 窗口日期：有目标窗口用目标窗口，否则用实际可得区间（并标注「实际」） */
function windowText(y: CrossYearYear): string {
  const w = y.window ?? y.actual_window;
  if (!w) return '—';
  return `${y.window ? '' : '实际 '}${w[0]} ~ ${w[1]}`;
}

function comparableText(y: CrossYearYear): string {
  if (y.comparable === undefined || y.comparable === null) return '—';
  return COMPARABLE_LABEL[String(y.comparable)] ?? String(y.comparable);
}

/**
 * ★★ 跨年份比较区段（A1）。
 *
 * - 默认**折叠**；折叠时显示一行摘要
 * - 无跨年份数据 → **不渲染**（不显示空壳）
 * - ★ 不挤占逐事件详情：本区段独立于事件分组，事件详情原样保留
 */
export function CrossYearSection({ doc }: { doc: HistoricalEventsDoc }) {
  const [open, setOpen] = useState(false);
  const cmp = crossYearComparisonOf(doc);
  if (!cmp) return null;                        // ★ 无数据 → 不渲染空壳
  const years = cmp.years ?? [];
  const basis = WINDOW_BASIS_LABEL[cmp.window_basis] ?? cmp.window_basis;
  const withSecurity = years.filter((y) => y.by_security && Object.keys(y.by_security).length > 0);
  const withNote = years.filter((y) => Boolean(y.note));

  return (
    <div className="fem-cy" data-cross-year="1">
      <button type="button" className="fem-cy-head" aria-expanded={open}
              onClick={() => setOpen((v) => !v)}>
        <span className="fem-cy-title">跨年份比较（{basis}）</span>
        {cmp.season_window && <span className="fem-cy-tag">窗口 {cmp.season_window}</span>}
        {cmp.target_pool && <span className="fem-cy-tag">标的池 {cmp.target_pool}</span>}
        <span className="fem-event-caret">{open ? '收起' : '展开'}</span>
      </button>
      <p className="fem-cy-summary">{crossYearSummary(years)}</p>
      <p className="fem-cy-caveat">{CROSS_YEAR_CAVEAT}</p>

      {/* ★ 默认折叠：折叠时摘要可见，明细 `hidden`（内容仍在 DOM，便于检索/打印） */}
      <div className="fem-cy-body" hidden={!open}>
        <h5>年份表（{years.length} 个年份）</h5>
          <div className="fem-table-wrap">
            <table className="fem-table fem-cy-table">
              <thead>
                <tr>
                  <th>年份</th><th>窗口类型 / 日期</th><th>机制 / 事件类型</th><th>结果</th>
                  <th>可比性</th><th>基准区间涨跌</th><th>标的数</th><th>覆盖</th>
                </tr>
              </thead>
              <tbody>
                {years.map((y) => (
                  <tr key={y.year} data-cy-year={y.year}>
                    <td>{y.year}{y.season_label ? ` ${y.season_label}` : ''}</td>
                    <td>{WINDOW_TYPE_LABEL[y.window_type] ?? y.window_type} · {windowText(y)}</td>
                    <td>{[y.mechanism, y.event_type].filter(Boolean).join(' / ') || '—'}</td>
                    <td className={`fem-cy-outcome out-${outcomeClass(y.outcome)}`}>{outcomeLabel(y.outcome)}</td>
                    <td title={y.comparable_reason ? plain(y.comparable_reason) : undefined}>{comparableText(y)}</td>
                    <td className={cls(y.benchmark?.period_return_pct)}>{fmtPct(y.benchmark?.period_return_pct)}</td>
                    <td>{y.by_security ? Object.keys(y.by_security).length : '—'}</td>
                    <td>{y.coverage ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ★★ v0.9：历史结果分布 / 经验基准概率 —— 挂在**既有**跨年份区段内部，
              不另造第二套地图；数据仍是同一份题材文档。 */}
          <EmpiricalProbabilityBlock doc={doc} cmp={cmp} />

          {withSecurity.length === 0 ? (
            <p className="fem-empty">
              源数据未提供逐标的数值（`by_security` 为空）—— 如实留空，**不补造数字**。
            </p>
          ) : (
            <>
              <h5>逐年 × 标的明细（{withSecurity.length} 个年份有数值）</h5>
              <div className="fem-table-wrap">
                <table className="fem-table fem-cy-table">
                  <thead>
                    <tr>
                      <th>年份</th><th>标的</th><th>交易日</th><th>区间涨跌</th><th>至高点</th>
                      <th>高点日</th><th>自高点回撤</th><th>区间超额</th><th>至高点超额</th>
                    </tr>
                  </thead>
                  <tbody>
                    {withSecurity.flatMap((y) => Object.entries(y.by_security!)
                      .map(([sid, s]) => (
                        <tr key={`${y.year}-${sid}`} data-cy-sec={sid}>
                          <td>{y.year}</td>
                          <td><code>{sid}</code></td>
                          <td>{s.trading_days ?? '—'}</td>
                          <td className={cls(s.period_return_pct)}>{fmtPct(s.period_return_pct)}</td>
                          <td className={cls(s.to_high_pct)}>{fmtPct(s.to_high_pct)}</td>
                          <td>{s.high?.date ?? '—'}</td>
                          <td>{fmtPct(s.max_drawdown_from_high_pct)}</td>
                          <td className={cls(s.excess_period_pp)}>{fmtPp(s.excess_period_pp)}</td>
                          <td className={cls(s.excess_to_high_pp)}>{fmtPp(s.excess_to_high_pp)}</td>
                        </tr>
                      )))}
                  </tbody>
                </table>
              </div>
              <p className="fem-perf-note">
                ★ 「区间超额」与「至高点超额」口径不同，<strong>不得混用</strong>；
                缺失一律显示 <code>—</code>，<strong>不补 0</strong>。
              </p>
            </>
          )}

          {withNote.length > 0 && (
            <>
              <h5>年份备注（含其他窗口口径，不得混用）</h5>
              <ul className="fem-gaps">
                {withNote.map((y) => (
                  <li key={y.year}><strong>{y.year}</strong>：<RichText text={y.note ?? ''} /></li>
                ))}
              </ul>
            </>
          )}

          {cmp.conclusion_short && (
            <p className="fem-cy-note">
              <strong>结论摘要</strong>：<RichText text={cmp.conclusion_short} />
            </p>
          )}
          {cmp.reading && <p className="fem-cy-note"><RichText text={cmp.reading} /></p>}
          {cmp.inclusion_principle && (
            <p className="fem-cy-note">
              <strong>纳入原则</strong>：<RichText text={cmp.inclusion_principle} />
            </p>
          )}
          {cmp.limitations && cmp.limitations.length > 0 && (
            <>
              <h5>本比较不能得出（源数据已声明）</h5>
              <ul className="fem-gaps">
                {cmp.limitations.map((l) => <li key={l.slice(0, 24)}><RichText text={l} /></li>)}
              </ul>
            </>
          )}
      </div>
    </div>
  );
}

export interface HistoricalEventMapProps {
  /** ★ 题材事件数据（由调用方注入） */
  doc: HistoricalEventsDoc;
  /** ★ 题材展示配置（标题 / 免责声明 / 分组顺序） */
  display?: ThemeDisplay;
}

export function HistoricalEventMap({ doc, display }: HistoricalEventMapProps) {
  const groups = eventsByClass(doc, display?.class_order);
  const title = display?.title ?? '历史事件（按年份）';
  const ariaLabel = display?.aria_label ?? '历史事件地图';
  const badge = display?.badge ?? '事后重建';
  const note = display?.note;

  return (
    <section className="fem" aria-label={ariaLabel}>
      <div className="fem-head">
        <h3 className="fem-title">{title}</h3>
        <span className="fem-badge">{badge}</span>
      </div>
      {note && <p className="fem-note"><RichText text={note} /></p>}

      {/* ★ 跨年份比较：在 note 之后、事件分组之前（不挤占逐事件详情） */}
      <CrossYearSection doc={doc} />

      {groups.length === 0 ? (
        <p className="fem-empty">（无历史事件记录）</p>
      ) : (
        groups.map((g) => (
          <div key={g.cls} className={`fem-group grp-${g.cls.toLowerCase()}`}>
            <h4 className="fem-group-title">
              {g.label}
              <span className="fem-group-count">{g.events.length} 个事件</span>
            </h4>
            <ul className="fem-list">
              {g.events.map((e) => (
                <EventCard key={e.event_id} e={e} classCaveat={display?.class_caveats?.[g.cls]} />
              ))}
            </ul>
          </div>
        ))
      )}
    </section>
  );
}
