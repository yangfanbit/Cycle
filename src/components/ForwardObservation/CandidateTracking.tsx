/**
 * 候选追踪（跨月滚动）—— v0.51。
 *
 * ★★★ 为什么需要这一块：`DiscoveredPatterns` 只显示**当前/下月**窗口，上一批候选在新一版里
 *   就消失了 → 产品上根本无法回答「上次形成的候选后来怎么样了」。
 *
 * ★★★ 数据来源与纪律：
 * - 形成字段来自 `candidate_formation_log_v0_1.json`（**追加式日志，永不改写**），
 *   经 `candidate_ledger_v0_2.json` 逐字投影进前端摘要的 `tracking.instances`；
 * - 结算字段由构建器钉在 `market_as_of` 重算 —— 因此**同一结算日永远同一结果**，
 *   行情推进只会**新增**一个结算快照，不会改写历史批次；
 * - `FORWARD_PENDING`（形成日早于窗口起点）= 真前瞻；`IN_WINDOW_PARTIAL`（形成日已在窗口内）
 *   的已实现部分**不是**样本外前瞻。
 *
 * ★ 不做的事：不评分、不排名（按板块名排序，不按结果）、不预测、不给买卖信号。
 */
import raw from '@current/pattern_discovery_summary_v0_1.json';
import { RichText } from '../RichText';

interface TH { status: string; board_ret: number | null; excess_pp: number | null; settle_date: string | null }
interface TI {
  instance_id: string; board: string; month: number; window_year: number;
  formed_at: string; batch_id: string | null; kind: string;
  tier: string | null; n_years: number | null; median_excess_pct: number | null;
  hit_rate: number | null; evidence_grade: string | null;
  anchor: string | null; status: string; outcome_type: string;
  horizons: Record<'5' | '10' | '20', TH>;
}
interface TBatch { batch_id: string; formed_at: string; new_instances: number; reappeared: number }
interface TRun {
  formed_at: string; source_as_of: string; skipped: string | null;
  new_instances: number; reappeared: number; batch_id: string | null;
}
interface Tracking {
  market_as_of: string;
  formation_log: { file: string; batches: number; instances: number; earliest_formed_at: string } | null;
  formation_run: TRun | null;
  batches: TBatch[] | null;
  settled: Record<string, number> | null;
  pending: Record<string, number> | null;
  by_outcome_type: Record<string, number> | null;
  instances: TI[];
}

const T = ((raw as unknown as { tracking?: Tracking | null }).tracking) ?? null;

const HZ = ['5', '10', '20'] as const;
const pct = (v?: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(2)}%`);
const pp = (v?: number | null) => (v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(2)}pp`);

const HZ_STATUS: Record<string, string> = {
  PENDING: '待结算', NOT_STARTED: '未开始', NO_SERIES: '无序列', NO_ANCHOR: '无锚点',
};
const TIER_SHORT: Record<string, string> = { STRICT: 'A', EXPLORATORY: 'C' };
const OTYPE_SHORT: Record<string, string> = {
  FORWARD_PENDING: '前瞻', IN_WINDOW_PARTIAL: '窗口内',
};

const CAVEAT =
  '★ 形成记录写在**追加式日志**里，行情推进**不会**改写它；结算固定在当日重算，' +
  '同一结算日永远同一结果。标「窗口内」的实例其已实现部分**不是**样本外前瞻。' +
  '行业板块**无历史成分**（不绑个股），概念篮子用**当前**成分回溯。' +
  '本表按板块名称排序，**不按结果排名**，不含打分、预测或买卖信号。';

/** 单个 horizon：已结算给超额（主）+ 板块收益（次），未结算给明确状态（不补 0）。 */
function Cell({ o }: { o: TH }) {
  if (o.status === 'AVAILABLE') {
    return (
      <>
        <strong>{pp(o.excess_pp)}</strong>
        <span className="fwd-note">{pct(o.board_ret)} · {o.settle_date ?? '—'}</span>
      </>
    );
  }
  return <span className="fwd-note">{HZ_STATUS[o.status] ?? o.status}</span>;
}

function basis(i: TI) {
  const t = i.tier ? (TIER_SHORT[i.tier] ?? i.tier) : '—';
  const med = i.median_excess_pct == null ? '—' : `${i.median_excess_pct > 0 ? '+' : ''}${i.median_excess_pct}%`;
  const hit = i.hit_rate == null ? '—' : `${Math.round(i.hit_rate * 100)}%`;
  return `${t} · ${i.n_years ?? '—'} 年 · 中位 ${med} · 命中 ${hit}`;
}

export function CandidateTracking() {
  if (!T || T.instances.length === 0) return null;

  const batches = T.batches ?? [];
  const order = batches.map((b) => b.batch_id);
  const groups = new Map<string, TI[]>();
  for (const i of T.instances) {
    const k = i.batch_id ?? '（未知批次）';
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(i);
  }
  const keys = [...groups.keys()].sort(
    (a, b) => (order.indexOf(b) - order.indexOf(a)) || a.localeCompare(b));

  const run = T.formation_run;
  const log = T.formation_log;

  return (
    <div className="fwd-track" data-tracking={T.market_as_of}>
      <h4 className="fwd-sub">四、候选追踪（跨月滚动 · 形成记录不可变）</h4>
      <p className="fwd-note" data-track-meta={`${log?.batches ?? 0}/${T.instances.length}`}>
        形成批次 <strong>{log?.batches ?? batches.length}</strong> 个 ·
        累计候选 <strong>{T.instances.length}</strong> 个 ·
        最早形成 <strong>{log?.earliest_formed_at ?? '—'}</strong> ·
        结算日 <strong>{T.market_as_of}</strong>
        <span className="fwd-note">
          5 日 已结算 {T.settled?.['5d'] ?? 0} / 待 {T.pending?.['5d'] ?? 0} ·
          10 日 已结算 {T.settled?.['10d'] ?? 0} / 待 {T.pending?.['10d'] ?? 0} ·
          20 日 已结算 {T.settled?.['20d'] ?? 0} / 待 {T.pending?.['20d'] ?? 0}
          （锚点 = 窗口首个交易日；超额 = 板块 − 沪深300）
        </span>
      </p>
      {run && (
        <p className="fwd-note" data-track-run={`${run.new_instances}/${run.reappeared}`}>
          本次刷新（{run.formed_at}，候选源 {run.source_as_of}）：新增
          <strong>{run.new_instances}</strong> 条 · 已存在 <strong>{run.reappeared}</strong> 条
          {run.skipped ? <span className="fwd-note"> —— {run.skipped}</span> : null}
        </p>
      )}
      {keys.map((k) => {
        const rows = groups.get(k)!;
        const meta = batches.find((b) => b.batch_id === k);
        return (
          <details className="fwd-track-batch" key={k} data-track-batch={k} open>
            <summary>
              批次 {k} · 形成于 {meta?.formed_at ?? rows[0].formed_at} · 新增{' '}
              {meta?.new_instances ?? rows.length} 条
              {meta && meta.reappeared > 0 ? ` · 重现 ${meta.reappeared} 条` : ''}
            </summary>
            <table className="fwd-track-table">
              <thead>
                <tr>
                  <th>板块 · 月</th><th>类型</th><th>历史依据</th><th>锚点</th>
                  {HZ.map((h) => <th key={h}>{h} 日</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((i) => (
                  <tr key={i.instance_id} data-track-row={i.instance_id}
                      data-otype={i.outcome_type} data-status={i.status}>
                    <td>
                      {i.board} · {i.month} 月
                      <span className="fwd-note" data-otype-badge={i.outcome_type}>
                        {OTYPE_SHORT[i.outcome_type] ?? i.outcome_type}
                        {i.outcome_type === 'IN_WINDOW_PARTIAL' ? '（形成时窗口已开始）' : '（窗口开始前形成）'}
                      </span>
                    </td>
                    <td>{i.kind === 'concept_basket' ? '概念' : '行业'}</td>
                    <td>{basis(i)}</td>
                    <td>{i.anchor ?? '—'}</td>
                    {HZ.map((h) => (
                      <td key={h} data-h={h} data-h-status={i.horizons[h].status}>
                        <Cell o={i.horizons[h]} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        );
      })}
      <p className="fwd-bias" data-track-caveat="1"><RichText text={CAVEAT} /></p>
    </div>
  );
}
