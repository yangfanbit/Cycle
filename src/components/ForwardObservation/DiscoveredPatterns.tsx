/**
 * 从多年行情**发现**的季节性结构（v0.34 · v0.42 起改读**前端摘要**）。
 * ★ 只展示 STRICT（预先声明标准）与少量 EXPLORATORY；每条必须带年份数、命中率、中位超额。
 * ★ 当前状态：IN_WINDOW（当月）/ PRE_WINDOW（下月，前置观察）。
 * ★★ 三层口径分开显示：① 历史统计 ② 滚动检验（双层资格）③ 时点结论。**历史命中率不是未来概率**。
 * ★★ `pit_eligible_years` 是「**历史序列时点资格**」——按**当前**序列、只用过去数据取得的**统计**资格。
 *
 * ★★★ v0.42 数据源变更：此前静态 import 完整研究产物（~5.7MB），组件实际只用
 *   计数 / 覆盖 / 标准 / 限制 / 排序前 6 的窗口。现改读 `pattern_discovery_summary_v0_1.json`
 *   （由 `build_pattern_summary_v0_1.py` 从完整产物**确定性派生**，~12KB，带 sha256 指纹）。
 *   完整产物仍在仓库中，供研究与审计；本组件**不再**读它。
 *
 * ★★★ v0.50：接入**候选账本**（`candidate_ledger_v0_1.json` 经摘要带入）——
 *   每条候选显示「窗口内 5 / 10 / 20 个交易日的实际表现」：板块 / 基准 / 超额 / 代表股中位超额。
 *   ★ 必须区分两种结果类型：`FORWARD_PENDING`（窗口开始前形成 → 真前瞻，未结算）
 *     与 `IN_WINDOW_PARTIAL`（形成日已在窗口内 → 已实现部分**不是**样本外前瞻）。
 */
import raw from '@current/pattern_discovery_summary_v0_1.json';
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
  outcome?: Outcome | null;
}
interface Horizon {
  status: string; settle_date?: string | null;
  board_ret?: number | null; bench_ret?: number | null; excess_pp?: number | null;
  rep_median_excess_pp?: number | null; n_reps?: number;
}
interface Outcome {
  outcome_type: 'FORWARD_PENDING' | 'IN_WINDOW_PARTIAL' | string;
  anchor?: string | null; window_note?: string | null;
  horizons: Record<'5' | '10' | '20', Horizon>;
}
interface Cov { series: number; rows: number; first_date: string | null; last_date: string | null }
interface D {
  as_of: string;
  coverage_detail: { stocks: Cov; industry_boards: Cov; concept_baskets: Cov; indices: Cov };
  criteria: { min_years: number; min_median_excess: number; min_hit_rate: number; min_train_years?: number;
    min_oos_tests?: number; in_sample_min_years?: number };
  source: { file: string; artifact_version: string; sha256: string; bytes: number };
  counts: { patterns: number; strict: number; exploratory: number; current_windows: number; top_windows: number };
  top_windows: P[]; tier_note: string; limitations: string[];
  ledger?: {
    file: string; as_of: string; sha256: string;
    summary: { candidates: number; by_outcome_type: Record<string, number>;
      horizon_status: Record<string, Record<string, number>> };
  } | null;
  realized_windows?: {
    pattern_id: string; board: string; month: number; kind: string; tier: string;
    median_excess_pct: number; hit_rate: number; current_status: string; outcome: Outcome;
  }[];
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

const pct = (v?: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(2)}%`);
const pp = (v?: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(2)}pp`);
const HZ = ['5', '10', '20'] as const;
/** 单个 horizon 的展示：已结算给三行数字，未结算给明确状态（不补 0）。 */
function Hz({ o }: { o: Horizon }) {
  if (o.status === 'AVAILABLE') {
    return (
      <>
        板块 <strong>{pct(o.board_ret)}</strong> / 基准 {pct(o.bench_ret)} /
        超额 <strong>{pp(o.excess_pp)}</strong>
        {o.rep_median_excess_pp != null && (
          <span className="fwd-note">（代表股中位超额 {pp(o.rep_median_excess_pp)}·n={o.n_reps}）</span>
        )}
      </>
    );
  }
  if (o.status === 'PENDING') return <span className="fwd-note">待结算（交易日不足）</span>;
  if (o.status === 'NOT_STARTED') return <span className="fwd-note">窗口未开始</span>;
  return <span className="fwd-note">{o.status}</span>;
}

const OUTCOME_NOTE: Record<string, string> = {
  FORWARD_PENDING: '★ 该候选在窗口开始前形成 → 这是**真正的前瞻**，尚未结算（PENDING 是正确状态）',
  IN_WINDOW_PARTIAL: '★ 形成日已在窗口内 → 已实现的天数**不是**样本外前瞻，只是窗口内已发生的部分',
};

export function DiscoveredPatterns() {
  const strictN = doc.counts.strict;
  const explN = doc.counts.exploratory;
  // ★ 摘要已按 median_excess_pct 降序排好前 N 条（与旧逻辑 sort+slice 等价），此处不再重排
  const top = doc.top_windows;
  return (
    <section className="fwd-disc" aria-label="数据发现的历史季节性结构" data-discovery-as-of={doc.as_of}>
      <h4 className="fwd-sub">
        三、从多年行情发现的结构（行业 {doc.coverage_detail.industry_boards.series} 个 · 概念{' '}
        {doc.coverage_detail.concept_baskets.series} 个 · 覆盖{' '}
        {doc.coverage_detail.industry_boards.first_date}–{doc.coverage_detail.industry_boards.last_date}）
      </h4>
      <p className="fwd-cand-note" data-discovery-counts={`${strictN}/${doc.counts.patterns}`}>
        STRICT <strong>{strictN}</strong> 条（标准：≥{doc.criteria.min_years} 年 · 中位超额 ≥
        {doc.criteria.min_median_excess}pp · 命中 ≥ {(doc.criteria.min_hit_rate * 100).toFixed(0)}%）
        · 探索 <strong>{explN}</strong> 条 · 当前/下月窗口 <strong>{doc.counts.current_windows}</strong> 条
        <span className="fwd-note">
          数据：股票 {doc.coverage_detail.stocks.series} 只（{doc.coverage_detail.stocks.first_date}–
          {doc.coverage_detail.stocks.last_date}）· 概念 {doc.coverage_detail.concept_baskets.rows.toLocaleString()} 行
          · 仅用<strong>已完成月份</strong>做历史统计；样本外资格按年份滚动（训练 ≥
          {doc.criteria.min_train_years ?? 5} 年、报告需 ≥{doc.criteria.min_oos_tests ?? 5} 个检验年）
        </span>
      </p>
      {doc.ledger && (
        <p className="fwd-note" data-ledger={doc.ledger.as_of}>
          候选账本（{doc.ledger.as_of}）：<strong>{doc.ledger.summary.candidates}</strong> 个候选 ·
          {/* ★ 键是产物里的 "5d"/"10d"/"20d"（带 d），不是 "5" —— 写错会静默显示 0 */}
          5 日已结算 <strong>{doc.ledger.summary.horizon_status['5d']?.AVAILABLE ?? 0}</strong> ·
          10 日已结算 <strong>{doc.ledger.summary.horizon_status['10d']?.AVAILABLE ?? 0}</strong> ·
          20 日待结算 <strong>{doc.ledger.summary.horizon_status['20d']?.PENDING ?? 0}</strong> ·
          待窗口开始 <strong>{doc.ledger.summary.by_outcome_type.FORWARD_PENDING ?? 0}</strong>
          <span className="fwd-note">（锚点=窗口首个交易日；超额=板块−沪深300）</span>
        </p>
      )}
      {(doc.realized_windows ?? []).length > 0 && (
        <div className="fwd-realized" data-realized-windows={doc.realized_windows!.length}>
          <p className="fwd-note" data-realized-title="1">
            <strong>本月窗口已实现部分</strong>（按<strong>历史</strong>中位超额排序，<strong>不按结果排名</strong>；
            锚点 = 窗口首个交易日；超额 = 板块 − 沪深300）：
          </p>
          <ul>
            {doc.realized_windows!.map((w) => (
              <li key={w.pattern_id} data-realized={w.pattern_id}
                  data-anchor={w.outcome.anchor ?? ''}>
                <strong>{w.board} · {w.month} 月</strong>
                <span className="fwd-note">
                  历史中位 {w.median_excess_pct > 0 ? '+' : ''}{w.median_excess_pct}%
                  · 命中 {(w.hit_rate * 100).toFixed(0)}%
                </span>
                {' — '}
                {HZ.map((h, i) => (
                  <span key={h} data-h={h} data-h-status={w.outcome.horizons[h].status}>
                    {i > 0 ? ' · ' : ''}{h} 日 <Hz o={w.outcome.horizons[h]} />
                  </span>
                ))}
              </li>
            ))}
          </ul>
          <p className="fwd-note" data-realized-caveat="1">
            ★ 这些窗口在<strong>形成日之前</strong>就已开始 → 已实现部分<strong>不是</strong>样本外前瞻，
            只是窗口内已发生的部分；20 日待结算。代表股为<strong>当前</strong>名单，含幸存者偏差。
          </p>
        </div>
      )}
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
            {p.outcome && (
              <>
                <p className="fwd-stats" data-outcome={p.outcome.outcome_type}
                   data-anchor={p.outcome.anchor ?? ''}>
                  窗口内实际（锚点 {p.outcome.anchor ?? '—'}）：
                  {HZ.map((h, i) => {
                    const o = p.outcome!.horizons[h];
                    return (
                      <span key={h} data-h={h} data-h-status={o.status}>
                        {i > 0 ? ' · ' : ''}
                        {h} 日 <Hz o={o} />
                      </span>
                    );
                  })}
                </p>
                <p className="fwd-note" data-outcome-note={p.outcome.outcome_type}>
                  <RichText text={OUTCOME_NOTE[p.outcome.outcome_type] ?? ''} />
                  {p.outcome.window_note ? `（${p.outcome.window_note}）` : ''}
                </p>
              </>
            )}
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
