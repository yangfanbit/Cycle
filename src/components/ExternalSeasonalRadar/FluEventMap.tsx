/**
 * 历史流感事件地图 —— 从季节性主题进入年份事件，再点进股票与事件细节。
 *
 * ★ 事件按**机制**分组：直接流感相关 vs 邻近传染病 / 公共卫生事件。
 *   后者（超级真菌 / 不明原因肺炎）**不是流感**，页面必须显式声明其不得用于支持流感季节性。
 * ★ 静态架构：数据 = `@current/flu_historical_events_v0_2.json`，无后端、无运行时请求。
 * ★ 「行情不可得」一律显式标注，不显示为 0 涨幅。
 */
import { useState } from 'react';
import {
  ADJACENT_EVENT_CAVEAT,
  EVENT_CLASS_LABEL,
  EVENT_STUDY_LABEL,
  EVIDENCE_LEVEL_LABEL,
  FLU_EVENTS_NOTE,
  MARKET_PERFORMANCE_CAVEAT,
  NO_MARKET_DATA_LABEL,
  PARTICIPANT_CATEGORY_LABEL,
  eventStudyState,
  fluEventsByClass,
  hasMarketData,
  type FluEvent,
  type FluParticipant,
} from '../../data/timeline/fluHistoricalEvents';

function MarketPerformanceBlock({ e }: { e: FluEvent }) {
  const mp = e.market_performance;
  if (!mp) return null;
  const bench = Object.entries(mp.benchmark)[0];
  const rows = Object.entries(mp.by_security);
  return (
    <>
      <h5>实测行情（窗口 {mp.window[0]} ~ {mp.window[1]}）</h5>
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
                  {st.excess_to_high_pp == null ? '—' : (st.excess_to_high_pp > 0 ? '+' : '') + st.excess_to_high_pp + 'pp'}
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

/** 中国股市惯例：涨红跌绿 */
function cls(v?: number | null): string {
  if (v == null) return '';
  return v > 0 ? 'num-up' : v < 0 ? 'num-down' : '';
}

function fmtPct(v?: number | null): string {
  if (v == null) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
}

function ParticipantRow({ p }: { p: FluParticipant }) {
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
      <p className="fem-part-why"><strong>纳入理由</strong>：{p.rationale}</p>
      <p className="fem-part-src"><strong>来源</strong>：{p.source}</p>
      {p.note && <p className="fem-part-note">{p.note}</p>}
    </li>
  );
}

function EventCard({ e }: { e: FluEvent }) {
  const [open, setOpen] = useState(false);
  const state = eventStudyState(e);
  const adjacent = e.event_class === 'ADJACENT_PUBLIC_HEALTH';
  return (
    <li
      className="fem-event"
      data-event-id={e.event_id}
      data-event-class={e.event_class ?? ''}
      data-study-state={state}
    >
      <button
        type="button"
        className="fem-event-head"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="fem-event-year">{e.year}</span>
        <span className="fem-event-label">{e.label}</span>
        <span className={`fem-event-state st-${state.toLowerCase()}`}>{EVENT_STUDY_LABEL[state]}</span>
        <span className="fem-event-caret">{open ? '收起' : '展开'}</span>
      </button>

      <p className="fem-event-win">窗口：{e.window_text}</p>
      <p className="fem-event-basis">依据：{e.evidence_basis}</p>

      {adjacent && <p className="fem-adjacent-caveat">{ADJACENT_EVENT_CAVEAT}</p>}

      {open && (
        <div className="fem-event-body">
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

          <h5>当次历史炒作标的（{e.participants.length} 只）</h5>
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

export function FluEventMap() {
  const groups = fluEventsByClass();
  return (
    <section className="fem" aria-label="历史流感事件地图">
      <div className="fem-head">
        <h3 className="fem-title">历史事件（按年份）</h3>
        <span className="fem-badge">事后重建 · 同期报道 + 库内 Campaign</span>
      </div>
      <p className="fem-note">{FLU_EVENTS_NOTE}</p>

      {groups.length === 0 ? (
        <p className="fem-empty">（无历史事件记录）</p>
      ) : (
        groups.map((g) => (
          <div key={g.cls} className={`fem-group grp-${g.cls.toLowerCase()}`}>
            <h4 className="fem-group-title">
              {EVENT_CLASS_LABEL[g.cls]}
              <span className="fem-group-count">{g.events.length} 个事件</span>
            </h4>
            <ul className="fem-list">
              {g.events.map((e) => <EventCard key={e.event_id} e={e} />)}
            </ul>
          </div>
        ))
      )}
    </section>
  );
}
