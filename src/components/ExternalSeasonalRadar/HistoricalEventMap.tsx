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
  EVENT_STUDY_LABEL,
  EVIDENCE_LEVEL_LABEL,
  MARKET_PERFORMANCE_CAVEAT,
  NO_MARKET_DATA_LABEL,
  PARTICIPANT_CATEGORY_LABEL,
  eventStudyState,
  eventsByClass,
  hasMarketData,
  type HistoricalEvent,
  type HistoricalEventsDoc,
  type HistoricalParticipant,
  type ThemeDisplay,
} from '../../data/timeline/historicalEventMaps';

/** 中国股市惯例：涨红跌绿 */
function cls(v?: number | null): string {
  if (v == null) return '';
  return v > 0 ? 'num-up' : v < 0 ? 'num-down' : '';
}

function fmtPct(v?: number | null): string {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
}

function MarketPerformanceBlock({ e }: { e: HistoricalEvent }) {
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
              <th>高点日</th><th>自高点回撤</th><th>超额(vs 基准)</th>
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
                <td className={cls(st.excess_to_high_pp)}>
                  {st.excess_to_high_pp == null ? '—'
                    : (st.excess_to_high_pp > 0 ? '+' : '') + st.excess_to_high_pp + 'pp'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="fem-perf-note">
        ★ 「报道当日涨幅」见上方各标的（`reported_move`），与这里的**区间行情是两回事**。
      </p>
    </>
  );
}

function ParticipantRow({ p }: { p: HistoricalParticipant }) {
  const ok = hasMarketData(p);
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
        {ok ? (
          <span className="fem-part-md ok">行情: {p.market_data}</span>
        ) : (
          <span className="fem-part-md miss">{NO_MARKET_DATA_LABEL}</span>
        )}
      </div>
      {p.business_mechanism && (
        <p className="fem-part-biz">
          <strong>业务机制</strong>：{p.business_mechanism}
          {p.business_mechanism_caveat && (
            <span className="fem-part-biz-caveat">{p.business_mechanism_caveat}</span>
          )}
        </p>
      )}
      <p className="fem-part-why"><strong>纳入理由</strong>：{p.rationale}</p>
      <p className="fem-part-src"><strong>来源</strong>：{p.source}</p>
      {p.note && <p className="fem-part-note">{p.note}</p>}
    </li>
  );
}

function EventCard({ e, classCaveat }: { e: HistoricalEvent; classCaveat?: string }) {
  const [open, setOpen] = useState(false);
  const state = eventStudyState(e);
  const conceptsNote = e.three_peaks_note ?? e.four_concepts_note;
  return (
    <li className="fem-event" data-event-id={e.event_id}
        data-event-class={e.event_class ?? ''} data-study-state={state}>
      <button type="button" className="fem-event-head" aria-expanded={open}
              onClick={() => setOpen((v) => !v)}>
        <span className="fem-event-year">{e.year}</span>
        <span className="fem-event-label">{e.label}</span>
        <span className={`fem-event-state st-${state.toLowerCase()}`}>
          {EVENT_STUDY_LABEL[state] ?? state}
        </span>
        <span className="fem-event-caret">{open ? '收起' : '展开'}</span>
      </button>

      <p className="fem-event-win">窗口：{e.window_text}</p>
      <p className="fem-event-basis">依据：{e.evidence_basis}</p>

      {classCaveat && <p className="fem-adjacent-caveat">{classCaveat}</p>}
      {conceptsNote && <p className="fem-three-peaks">{conceptsNote}</p>}

      {open && (
        <div className="fem-event-body">
          {e.campaign_facts && (
            <>
              <h5>Campaign 事实</h5>
              <p className="fem-media-note">
                <code>{e.campaign_facts.campaign_id}</code> ·{' '}
                start {e.campaign_facts.start ?? '—'} · <strong>peak_date {e.campaign_facts.peak_date ?? '—'}</strong> ·{' '}
                end {e.campaign_facts.end ?? '—'}
                {e.campaign_facts.note && <span className="fem-campaign-note">{e.campaign_facts.note}</span>}
              </p>
            </>
          )}

          {e.media_label_note && (
            <>
              <h5>媒体标签 vs 可核实催化</h5>
              <p className="fem-media-note">{e.media_label_note}</p>
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
                  <span className="fem-cat-text">{c.text}</span>
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
                    <span className="fem-cat-text"><strong>{ph.phase_type}</strong>：{ph.description}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h5>当次历史炒作标的（{e.participants.length} 只）</h5>
          <p className="fem-biz-caveat">{BUSINESS_MECHANISM_CAVEAT}</p>
          {e.participants.length === 0 ? (
            <p className="fem-empty">（未建立候选清单）</p>
          ) : (
            <ul className="fem-parts">
              {e.participants.map((p) => <ParticipantRow key={p.security_id} p={p} />)}
            </ul>
          )}

          <MarketPerformanceBlock e={e} />

          <h5>报道当日涨幅</h5>
          <p className="fem-perf-note">{e.observed_performance.note}</p>
          {e.observed_performance.by_security ? (
            <ul className="fem-perf">
              {Object.entries(e.observed_performance.by_security).map(([k, v]) => (
                <li key={k}><code>{k}</code> {v}</li>
              ))}
            </ul>
          ) : (
            <p className="fem-empty">（无行情 → 不展示数字，**不**以 0 涨幅代替）</p>
          )}

          <h5>缺失 / 不确定事项</h5>
          <ul className="fem-gaps">
            {e.known_gaps.map((g) => <li key={g.slice(0, 20)}>{g}</li>)}
          </ul>
        </div>
      )}
    </li>
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
      {note && <p className="fem-note">{note}</p>}

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
