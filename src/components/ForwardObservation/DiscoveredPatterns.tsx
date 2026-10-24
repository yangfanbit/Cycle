/**
 * 从多年行情**发现**的季节性结构（v0.34 · v0.41 起接双层时点资格产物）。
 * ★ 只展示 STRICT（预先声明标准）与少量 EXPLORATORY；每条必须带年份数、命中率、中位超额。
 * ★ 当前状态：IN_WINDOW（当月）/ PRE_WINDOW（下月，前置观察）。
 * ★★ 三层口径分开显示：① 历史统计（n_years/中位/命中）② 滚动检验（逐年训练+测试，双层资格）
 *    ③ 时点结论（oos_* / oos_by_train_tier / evidence_grade）。**历史命中率不是未来概率**。
 * ★★ `pit_eligible_years` 是「**历史序列时点资格**」——按**当前**序列、只用过去数据取得的**统计**资格，
 *    不等于当时的分类/成分/研究机会可得；0 表示只有回看才成立。
 */
import raw from '@current/pattern_discovery_v0_9.json';
import { RichText } from '../RichText';

interface TierStat { tests: number; hit_rate: number | null; median_excess_pct: number | null; status?: string }
interface P {
  pattern_id: string; board: string; month: number; n_years: number; years: string[];
  median_excess_pct: number; hit_rate: number; tier: string;
  current_status: string; kind: string; best_year: { year: string; excess_pct: number };
  worst_year: { year: string; excess_pct: number };
  representative_stocks?: { series_id: string; name?: string | null; name_status?: string;
    median_excess_pct: number; years: number; source?: string }[];
  rep_stock_gap?: string;
  oos_tests?: number; oos_hit_rate?: number | null; oos_median_excess_pct?: number | null;
  oos_status?: string; oos_note?: string | null;
  oos_by_train_tier?: { STRICT: TierStat; EXPLORATORY: TierStat };
  pit_eligible_years?: number; pit_first_year?: string | null; pit_basis?: string;
  discovery_basis?: string; evidence_grade?: string;
}
interface Cov { series: number; rows: number; first_date: string | null; last_date: string | null }
interface D {
  as_of: string;
  coverage_detail: { stocks: Cov; industry_boards: Cov; concept_baskets: Cov; indices: Cov };
  criteria: { min_years: number; min_median_excess: number; min_hit_rate: number; min_train_years?: number;
    min_oos_tests?: number; in_sample_min_years?: number };
  source: { industry_boards: string; concept_baskets: string; benchmark: string };
  patterns: P[]; current_windows: P[]; tier_note: string; limitations: string[];
  pit_only_count?: number;
  pit_only_summary?: {
    total: number;
    by_history_tier?: { INSUFFICIENT_HISTORY?: number; BELOW_THRESHOLD?: number };
    oos_reportable?: number;
    oos_reportable_hit_rate?: number | null;
    median_positive?: number;
    note?: string;
  };
}
const doc = raw as unknown as D;

const STATUS: Record<string, string> = { IN_WINDOW: '当月窗口', PRE_WINDOW: '下月窗口（前置）' };

export function DiscoveredPatterns() {
  const strict = doc.patterns.filter((p) => p.tier === 'STRICT');
  const expl = doc.patterns.filter((p) => p.tier === 'EXPLORATORY');
  const top = [...doc.current_windows].sort((a, b) => b.median_excess_pct - a.median_excess_pct).slice(0, 6);
  return (
    <section className="fwd-disc" aria-label="数据发现的历史季节性结构" data-discovery-as-of={doc.as_of}>
      <h4 className="fwd-sub">
        三、从多年行情发现的结构（行业 {doc.coverage_detail.industry_boards.series} 个 · 概念{' '}
        {doc.coverage_detail.concept_baskets.series} 个 · 覆盖{' '}
        {doc.coverage_detail.industry_boards.first_date}–{doc.coverage_detail.industry_boards.last_date}）
      </h4>
      <p className="fwd-cand-note" data-discovery-counts={`${strict.length}/${doc.patterns.length}`}>
        STRICT <strong>{strict.length}</strong> 条（标准：≥{doc.criteria.min_years} 年 · 中位超额 ≥
        {doc.criteria.min_median_excess}pp · 命中 ≥ {(doc.criteria.min_hit_rate * 100).toFixed(0)}%）
        · 探索 <strong>{expl.length}</strong> 条 · 当前/下月窗口 <strong>{doc.current_windows.length}</strong> 条
        <span className="fwd-note">
          数据：股票 {doc.coverage_detail.stocks.series} 只（{doc.coverage_detail.stocks.first_date}–
          {doc.coverage_detail.stocks.last_date}）· 概念 {doc.coverage_detail.concept_baskets.rows.toLocaleString()} 行
          · 仅用<strong>已完成月份</strong>做历史统计；样本外资格按年份滚动（训练 ≥
          {doc.criteria.min_train_years ?? 5} 年、报告需 ≥{doc.criteria.min_oos_tests ?? 5} 个检验年）
        </span>
      </p>
      <p className="fwd-note" data-pit-only={doc.pit_only_count ?? 0}>
        ★ 另有 <strong>{doc.pit_only_count ?? 0}</strong> 个模式「曾在历史序列上取得时点资格、但全样本等级不达标」：
        历史样本不足 8 年 <strong>{doc.pit_only_summary?.by_history_tier?.INSUFFICIENT_HISTORY ?? 0}</strong> 个 ·
        ≥8 年但未达阈值 <strong>{doc.pit_only_summary?.by_history_tier?.BELOW_THRESHOLD ?? 0}</strong> 个；
        其中 <strong>{doc.pit_only_summary?.oos_reportable ?? 0}</strong> 个具备可报告的样本外结果，
        这些里样本外命中率 ≥50% 的占{' '}
        <strong>{Math.round((doc.pit_only_summary?.oos_reportable_hit_rate ?? 0) * 100)}%</strong>。
        本轮<strong>不放进首页</strong>，仅作为方法对照留在产物里 —— 是否开独立探索入口需另行评估。
        时点资格 ≠ 未来有效：<strong>历史命中率不是成功概率</strong>。
      </p>
      <ul className="fwd-patterns">
        {top.map((p) => (
          <li key={p.pattern_id} className="fwd-pattern" data-discovery={p.pattern_id}
              data-tier={p.tier} data-status={p.current_status}>
            <div className="fwd-pattern-head">
              <strong>{p.board} · {p.month} 月</strong>
              <span className="fwd-role-asof">{p.kind === 'concept_basket' ? '自建概念等权' : '行业板块'}</span>
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
            <p className="fwd-stats" data-oos={p.oos_status ?? ''}>
              样本外（滚动 · 两层合并）：{p.oos_status === 'REPORTED'
                ? <>检验 <strong>{p.oos_tests}</strong> 年 · 命中 <strong>{((p.oos_hit_rate ?? 0) * 100).toFixed(0)}%</strong>
                    · 中位超额 <strong>{p.oos_median_excess_pct}%</strong></>
                : <span className="fwd-note">证据不足（{p.oos_note ?? '检验年数不足，不作结论'}）</span>}
            </p>
            {p.oos_by_train_tier && (
              <p className="fwd-stats" data-oos-by-tier="1">
                分训练层级：STRICT 训练 <strong>{p.oos_by_train_tier.STRICT.tests}</strong> 年
                （命中 {((p.oos_by_train_tier.STRICT.hit_rate ?? 0) * 100).toFixed(0)}%）·
                EXPLORATORY 训练 <strong>{p.oos_by_train_tier.EXPLORATORY.tests}</strong> 年
                （命中 {((p.oos_by_train_tier.EXPLORATORY.hit_rate ?? 0) * 100).toFixed(0)}%）
              </p>
            )}
            <p className="fwd-stats" data-pit={p.pit_eligible_years ?? 0}>
              历史序列时点资格：{(p.pit_eligible_years ?? 0) > 0
                ? <><strong>{p.pit_eligible_years}</strong> 个年份在「只用该年之前的数据」下取得统计资格
                    {p.pit_first_year ? `（最早 ${p.pit_first_year}）` : ''}</>
                : <span className="fwd-note">★ 0 次 —— 该窗口<strong>只有回看才成立</strong>（当年无法被发现），不得当作「当时可预判」</span>}
            </p>
            {(p.representative_stocks ?? []).length > 0 && (
              <p className="fwd-stats" data-rep-stocks={p.representative_stocks!.length}>
                代表性股票（当前成分）：{p.representative_stocks!.map((x) =>
                  `${x.name ? x.name : x.series_id}（${x.series_id}）${x.name ? '' : '· 名称缺失'} ${
                    x.median_excess_pct > 0 ? '+' : ''}${x.median_excess_pct}%`).join(' · ')}
                <span className="fwd-note">★ 当前成分回溯，非当年成分</span>
              </p>
            )}
            {p.kind !== 'concept_basket' && (
              <p className="fwd-note" data-rep-stock-gap="1">
                数据缺口：行业板块<strong>没有历史成分</strong> → 不绑定个股（不代表没有代表股，只代表本数据无法证明）
              </p>
            )}
          </li>
        ))}
      </ul>
      <p className="fwd-bias" data-discovery-tier-note="1"><RichText text={doc.tier_note} /></p>
      <p className="fwd-bias"><RichText text={doc.limitations[0]} /></p>
      <p className="fwd-bias" data-pit-limitation="1">
        ★ 时点资格的边界：概念成员与板块分类都是<strong>当前口径回溯</strong>，退市股不在库内 ——
        滚动检验只能约束「有没有用未来数据」，<strong>不能</strong>消除成分/分类回溯与幸存者偏差；
        它也不是当时可得的研究机会。
      </p>
    </section>
  );
}
