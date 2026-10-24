/**
 * 从多年行情**发现**的季节性结构（v0.34）。
 * ★ 只展示 STRICT（预先声明标准）与少量 EXPLORATORY；每条必须带年份数、命中率、中位超额。
 * ★ 当前状态：IN_WINDOW（当月）/ PRE_WINDOW（下月，前置观察）。
 */
import raw from '@current/pattern_discovery_v0_3.json';
import { RichText } from '../RichText';

interface P {
  pattern_id: string; board: string; month: number; n_years: number; years: string[];
  median_excess_pct: number; hit_rate: number; tier: string;
  current_status: string; best_year: { year: string; excess_pct: number };
  worst_year: { year: string; excess_pct: number };
}
interface D {
  as_of: string; coverage: string; criteria: { min_years: number; min_median_excess: number; min_hit_rate: number };
  source: { boards_scanned: number; provider: string };
  patterns: P[]; current_windows: P[]; tier_note: string; limitations: string[];
}
const doc = raw as unknown as D;

const STATUS: Record<string, string> = { IN_WINDOW: '当月窗口', PRE_WINDOW: '下月窗口（前置）' };

export function DiscoveredPatterns() {
  const strict = doc.patterns.filter((p) => p.tier === 'STRICT');
  const top = [...doc.current_windows].sort((a, b) => b.median_excess_pct - a.median_excess_pct).slice(0, 6);
  return (
    <section className="fwd-disc" aria-label="数据发现的历史季节性结构" data-discovery-as-of={doc.as_of}>
      <h4 className="fwd-sub">三、从多年行情发现的结构（{doc.source.boards_scanned} 个行业板块 · 覆盖 {doc.coverage}）</h4>
      <p className="fwd-cand-note" data-discovery-counts={`${strict.length}/${doc.patterns.length}`}>
        STRICT <strong>{strict.length}</strong> 条（标准：≥{doc.criteria.min_years} 年 · 中位超额 ≥
        {doc.criteria.min_median_excess}pp · 命中 ≥ {(doc.criteria.min_hit_rate * 100).toFixed(0)}%）
        · 探索 {doc.patterns.length - strict.length} 条 · 当前/下月窗口 <strong>{doc.current_windows.length}</strong> 条
      </p>
      <ul className="fwd-patterns">
        {top.map((p) => (
          <li key={p.pattern_id} className="fwd-pattern" data-discovery={p.pattern_id}
              data-tier={p.tier} data-status={p.current_status}>
            <div className="fwd-pattern-head">
              <strong>{p.board} · {p.month} 月</strong>
              <span className={`fwd-status ${p.tier === 'STRICT' ? 'st-a_repeated' : 'st-c_exploratory'}`}>
                {p.tier === 'STRICT' ? 'A · 达到预先标准' : 'C · 探索线索'}
              </span>
              <span className="fwd-ev st-pre_observation">{STATUS[p.current_status] ?? p.current_status}</span>
            </div>
            <p className="fwd-stats">
              {p.n_years} 年（{p.years[0]}–{p.years[p.years.length - 1]}）· 中位超额 <strong>+{p.median_excess_pct}%</strong>
              · 命中 <strong>{(p.hit_rate * 100).toFixed(0)}%</strong>
              · 最好 {p.best_year.year} {p.best_year.excess_pct > 0 ? '+' : ''}{p.best_year.excess_pct}%
              / 最差 {p.worst_year.year} {p.worst_year.excess_pct}%
            </p>
          </li>
        ))}
      </ul>
      <p className="fwd-bias" data-discovery-tier-note="1"><RichText text={doc.tier_note} /></p>
      <p className="fwd-bias"><RichText text={doc.limitations[0]} /></p>
    </section>
  );
}
