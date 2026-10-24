/**
 * 当前前瞻观察（Forward Observation）—— 首页「当前」侧的极简入口（v0.33）。
 *
 * ★ 只做三件事：说清 as_of / 展示已验证到什么程度的模式 / 列候选并**标明可不可执行**。
 * ★ 不建 Dashboard、不改历史事件地图、不做排序与评分。
 */
import {
  EVIDENCE_STATUS_LABEL,
  FORWARD_OBSERVATION as D,
  PATTERN_STATUS_LABEL,
  type ForwardCandidate,
  type ForwardPattern,
} from '../../data/timeline/forwardObservation';
import { RichText } from '../RichText';

function num(v: number | null | undefined, suffix = '%'): string {
  return v === null || v === undefined ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(2)}${suffix}`;
}

function PatternRow({ p }: { p: ForwardPattern }) {
  const s = p.stats;
  return (
    <li className="fwd-pattern" data-pattern-id={p.pattern_id} data-pattern-status={p.status}>
      <div className="fwd-pattern-head">
        <strong>{p.title}</strong>
        <span className={`fwd-status st-${p.status.toLowerCase()}`}>{PATTERN_STATUS_LABEL[p.status]}</span>
      </div>
      <p className="fwd-stats" data-stats="1">
        独立事件/年份 <strong>{s.occurrence_count}</strong> ·
        出现响应 <strong>{s.response_count}</strong> ·
        响应率 <strong>{s.response_rate === null ? '—' : `${(s.response_rate * 100).toFixed(1)}%`}</strong>
        {s.median_lead_days !== null && s.median_lead_days !== undefined && (
          <> · 典型提前量 <strong>{s.median_lead_days}</strong> 个交易日</>
        )}
        {s.sample_years?.length > 0 && <> · 样本年份 {s.sample_years.join(' / ')}</>}
      </p>
      {p.status_reason && <p className="fwd-reason"><RichText text={p.status_reason} /></p>}
      {p.pattern_id === 'ZODIAC_NAME' && p.years && (
        <p className="fwd-detail" data-zodiac-years="1">
          {p.years.filter((y) => y.testable).map((y) => (
            <span key={y.year} className="fwd-chip" data-year={y.year}>
              {y.year} {y.animal}年 · {y.name_matches} 只 ·
              {y.window?.status === 'OK'
                ? ` 中位超额 ${num(y.window.median_excess_pct)} · 广度 ${y.window.breadth?.toFixed(2)}`
                : y.window?.status === 'FUTURE' ? ' 窗口未到' : ' 不可测'}
            </span>
          ))}
          <span className="fwd-note">
            ★ 另有 {p.stats.not_testable_years?.length ?? 0} 个年份<strong>不可测</strong>（当前名称里匹配不到，
            缺历史名称快照）—— 这不是「当年没有炒作」。
          </span>
        </p>
      )}
      {p.pattern_id === 'TAIWAN_STRAIT_EVENT' && p.events && (
        <p className="fwd-detail" data-strait-events="1">
          {p.events.map((e) => (
            <span key={e.event_id} className={`fwd-chip ${e.responded ? 'is-hit' : ''}`} data-event={e.event_id}>
              {e.event_date} {e.label.slice(0, 12)} · {e.responded ? '有响应' : '无响应'}
            </span>
          ))}
          {p.basket && (
            <span className="fwd-note">
              篮子：{p.basket.concept}（当前成分 {p.basket.members} 只 / 有数据 {p.basket.members_with_data} 只）——
              <RichText text={p.basket.membership_bias} />
            </span>
          )}
        </p>
      )}
      <p className="fwd-bias" data-known-biases="1">已知偏差：<RichText text={p.known_biases[0]} /></p>
    </li>
  );
}

function CandidateRow({ c }: { c: ForwardCandidate }) {
  const perf = c.current_performance;
  return (
    <li className="fwd-cand" data-candidate-id={c.candidate_id} data-evidence-status={c.evidence_status}>
      <div className="fwd-cand-head">
        <strong>{c.title}</strong>
        <span className={`fwd-ev st-${c.evidence_status.toLowerCase()}`}>
          {EVIDENCE_STATUS_LABEL[c.evidence_status]}
        </span>
      </div>
      <p className="fwd-why"><RichText text={c.why_now} /></p>
      {c.window.start && (
        <p className="fwd-window">
          窗口：{c.window.start} → {c.window.end}
          {c.window.peak ? `（峰值参考 ${c.window.peak}）` : ''}
        </p>
      )}
      {perf && (
        <p className="fwd-perf" data-current-perf="1">
          当前 20 日：中位超额 <strong>{num(perf.median_20d_excess_pct)}</strong> ·
          广度 <strong>{perf.breadth_20d?.toFixed(2) ?? '—'}</strong> ·
          有数据 {perf.participants_with_data ?? 0} 只
        </p>
      )}
      {c.not_a_candidate_reason && (
        <p className="fwd-not"><RichText text={c.not_a_candidate_reason} /></p>
      )}
      {c.what_to_watch && <p className="fwd-watch">下一步观察：<RichText text={c.what_to_watch} /></p>}
      {c.invalidate_if && <p className="fwd-invalidate">降低关注：<RichText text={c.invalidate_if} /></p>}
      {c.fact_vs_assumption && (
        <p className="fwd-fact" data-fact-vs-assumption="1">
          计算事实：<RichText text={c.fact_vs_assumption.fact ?? ''} />；
          研究假设：<RichText text={c.fact_vs_assumption.assumption ?? ''} />
        </p>
      )}
    </li>
  );
}

export function ForwardObservationSection() {
  const b = D.benchmark;
  return (
    <section className="fwd" aria-label="当前前瞻观察" data-forward-as-of={D.as_of}>
      <div className="fwd-head">
        <h2 className="fwd-title">当前前瞻观察</h2>
        <span className="fwd-asof">观察时点 <code>{D.as_of}</code>（{D.as_of_source}）</span>
      </div>
      <p className="fwd-lead">
        从历史行情里批量找<strong>重复模式</strong>，再看当前是否处在窗口内 ——
        这里只给<strong>证据状态</strong>与<strong>下一步看什么</strong>，不打分、不给买卖信号。
      </p>
      <p className="fwd-bench" data-benchmark="1">
        基准 {b.name} 收 {b.close?.toFixed(2)} · 5 日 {num(b.ret_5d)} · 10 日 {num(b.ret_10d)} ·
        20 日 {num(b.ret_20d)} · 60 日 {num(b.ret_60d)}
      </p>

      <h4 className="fwd-sub">一、历史重复模式（验证到什么程度）</h4>
      <ul className="fwd-patterns">
        {D.patterns.map((p) => <PatternRow key={p.pattern_id} p={p} />)}
      </ul>

      <h4 className="fwd-sub">二、当前候选（{D.candidates.length} 个）</h4>
      <p className="fwd-cand-note" data-actionable-count={D.candidates.filter((c) => c.evidence_status === 'PRE_OBSERVATION').length}>
        ★ 只有标「前置观察」的才具有时间优势；「已升温」是<strong>事后</strong>描述，
        <strong>不得</strong>当成提前发现。
      </p>
      <ul className="fwd-cands">
        {D.candidates.map((c) => <CandidateRow key={c.candidate_id} c={c} />)}
      </ul>

      <p className="fwd-sectors" data-sector-scan="1">
        当前行业强弱（{D.sector_scan.boards_scanned} 个板块 · 20 日）：
        {D.sector_scan.top_20d.slice(0, 5).map((x) => `${x.name} ${num(x.ret_20d)}`).join(' · ')}
        <span className="fwd-note">（仅用于定位「哪些已经涨过」，不作为候选）</span>
      </p>

      <details className="fwd-limits">
        <summary>已知限制（必读）</summary>
        <ul>
          {D.limitations.map((t, i) => <li key={i}><RichText text={t} /></li>)}
        </ul>
      </details>
    </section>
  );
}
