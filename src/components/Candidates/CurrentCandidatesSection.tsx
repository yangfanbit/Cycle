/**
 * 当前候选前瞻（v0.38）—— 统一候选池：历史地图之后的第二主模块。
 * 来源：pattern_discovery（当前/下月窗口）· forward_observation（专项假设）·
 *      current_candidates（当前研究对象）· market_snapshots（仅披露日期状态）。
 * ★ 分组是研究浏览优先顺序，不是概率/胜率/荐股；各来源日期原样显示，不统一改写。
 */
import { useMemo, useState } from 'react';
import raw from '@current/candidate_digest_v0_1.json';
import { RichText } from '../RichText';

interface Card {
  id: string; source: string[]; kind: string; title: string; subtitle?: string;
  why_now?: string | null; time_position: string; group: 'G1' | 'G2' | 'G3' | 'G4';
  history: Record<string, unknown>;
  representative_stocks?: { series_id: string; name?: string | null; median_excess_pct: number }[];
  gap?: string | null; watch_next?: string | null; invalidate_if?: string | null;
  trigger?: { items?: { category?: string; note?: string }[] };
  dates: { price_as_of?: string | null; research_as_of?: string | null };
  evidence_ref?: Record<string, string>;
}
interface Doc {
  as_of: string; counts: Record<string, number>; group_rule: Record<string, string>;
  data_dates: Record<string, unknown>; cards: Card[]; limitations: string[];
}
const doc = raw as unknown as Doc;

const GROUP_LABEL: Record<string, string> = {
  G1: '优先组 · 历史重复 + 样本外 + 时间优势',
  G2: '第二组 · 结构参照 / 催化临近',
  G3: '第三组 · 有当前事实、历史证据不足',
  G4: '探索 / 待核实 · 证据不足或数据陈旧',
};
const KIND_LABEL: Record<string, string> = { SEASONAL_WINDOW: '季节窗口', SPECIAL_HYPOTHESIS: '专项假设', CURRENT_OBJECT: '当前题材' };
const TIME_LABEL: Record<string, string> = {
  PRE_WINDOW: '窗口未到', IN_WINDOW: '窗口内', ALREADY_WARM: '已升温（偏晚）', DATA_STALE: '数据陈旧',
  INSUFFICIENT: '证据不足', WATCH_ONLY: '事件驱动（无时间优势）', UNKNOWN: '状态未知',
  PASSED: '窗口已过', LATER: '窗口较远',
};
const TOP: Record<string, number> = { G1: 6, G2: 4, G3: 3, G4: 3 };

const num = (v: unknown, s = '%') => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(2)}${s}` : '—');

function CardView({ c }: { c: Card }) {
  const [open, setOpen] = useState(false);
  const h = c.history as Record<string, number | string | null>;
  return (
    <li className={`cand-card g-${c.group.toLowerCase()}`} data-candidate={c.id} data-group={c.group}
        data-time={c.time_position} data-kind={c.kind}>
      <div className="cand-head">
        <strong className="cand-title">{c.title}</strong>
        <span className="cand-chip">{KIND_LABEL[c.kind] ?? c.kind}</span>
        {c.subtitle && <span className="cand-sub">{c.subtitle}</span>}
        <span className={`cand-time t-${c.time_position.toLowerCase()}`}>{TIME_LABEL[c.time_position] ?? c.time_position}</span>
        <span className="cand-date">
          {c.dates.price_as_of ? `行情 ${c.dates.price_as_of}` : ''}
          {c.dates.research_as_of ? ` · 研究 ${c.dates.research_as_of}` : ''}
        </span>
      </div>
      {c.why_now && <p className="cand-why"><RichText text={c.why_now} /></p>}
      <p className="cand-hist" data-hist="1">
        {h.n_years ? (
          <>历史 <strong>{h.n_years}</strong> 年 · 中位超额 <strong>{num(h.median_excess_pct)}</strong>
            {' · '}{h.oos_status === 'REPORTED'
              ? <>样本外 <strong>{h.oos_tests}</strong> 年 · 命中 <strong>{Math.round(Number(h.oos_hit_rate ?? 0) * 100)}%</strong></>
              : <span className="cand-gap">样本外证据不足</span>}</>
        ) : (Array.isArray(h.reference_cases) && h.reference_cases.length > 0
          ? <>历史参照：{(h.reference_cases as unknown[]).length} 个案例</>
          : <span className="cand-gap">暂无可验证历史参照</span>)}
      </p>
      {(c.representative_stocks ?? []).length > 0 && (
        <p className="cand-stocks" data-stocks={c.representative_stocks!.length}>
          代表股票：{c.representative_stocks!.slice(0, 3).map((s) =>
            `${s.name ?? s.series_id}（${s.series_id}）${num(s.median_excess_pct)}`).join(' · ')}
          <span className="cand-gap">★ 当前成分回溯</span>
        </p>
      )}
      {c.gap && <p className="cand-gap" data-gap="1"><RichText text={c.gap} /></p>}
      <button type="button" className="cand-more" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? '收起' : '展开依据'}
      </button>
      {open && (
        <div className="cand-detail">
          {c.trigger?.items?.length ? (
            <p>触发：{c.trigger.items.map((t, i) => <span key={i}>{t.category} · {t.note}；</span>)}</p>
          ) : null}
          {c.watch_next && <p>接下来看：<RichText text={c.watch_next} /></p>}
          {c.invalidate_if && <p>降低关注：<RichText text={c.invalidate_if} /></p>}
          <p className="cand-gap">来源：{c.source.join(' / ')} · 证据：{c.evidence_ref?.artifact}</p>
        </div>
      )}
    </li>
  );
}

export function CurrentCandidatesSection() {
  const [showAll, setShowAll] = useState(false);
  const [month, setMonth] = useState('all');
  const [kind, setKind] = useState('all');
  const filtered = useMemo(() => doc.cards.filter((c) => {
    if (kind !== 'all' && c.kind !== kind) return false;
    if (month !== 'all') {
      const m = /·\s*(\d+)\s*月/.exec(c.title);
      if (!m || m[1] !== month) return false;
    }
    return true;
  }), [month, kind]);

  return (
    <section className="cand" aria-label="当前候选前瞻" data-candidates-as-of={doc.as_of}>
      <div className="cand-head-row">
        <h2 className="cand-h2">当前候选前瞻</h2>
        <span className="cand-meta">
          统一候选 <strong>{doc.cards.length}</strong> 张 · 优先 {doc.counts.G1} · 结构 {doc.counts.G2}
          {' '}· 探索 {doc.counts.G4} · 行情截至 <code>{doc.as_of}</code>
        </span>
      </div>
      <p className="cand-lead">
        把「自动发现窗口 / 专项假设 / 当前研究对象」放进同一列表：先看有历史重复与样本外证据的方向，
        再看只有当前事实的方向。分组是<strong>研究浏览顺序</strong>，不是收益预测。
      </p>
      <p className="cand-dates" data-dates="1">
        数据日期：研究候选 {String(doc.data_dates.research_candidates_as_of ?? '—')}
        · 模式发现 {String(doc.data_dates.pattern_discovery_generated_at ?? '').slice(0, 10)}
        · 最新已签发快照 {String((doc.data_dates.snapshot_latest_canonical as { snapshot_date?: string } | null)?.snapshot_date ?? '—')}
        · 行情 {doc.as_of}
      </p>
      <div className="cand-filters">
        <button type="button" className={showAll ? 'is-on' : ''} onClick={() => setShowAll(!showAll)}
                data-show-all={showAll ? '1' : '0'}>
          {showAll ? '收起全部' : `查看全部（${doc.cards.length}）`}
        </button>
        <select aria-label="按月份筛选" value={month} onChange={(e) => setMonth(e.target.value)}>
          <option value="all">全部月份</option>
          <option value="10">10 月</option>
          <option value="11">11 月</option>
        </select>
        <select aria-label="按类型筛选" value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="all">全部类型</option>
          <option value="SEASONAL_WINDOW">季节窗口</option>
          <option value="CURRENT_OBJECT">当前题材</option>
        </select>
      </div>
      {(['G1', 'G2', 'G3', 'G4'] as const).map((g) => {
        const list = filtered.filter((c) => c.group === g);
        if (!list.length) return null;
        const shown = showAll ? list : list.slice(0, TOP[g]);
        return (
          <div key={g} className="cand-group" data-group={g}>
            <h3 className="cand-gh">{GROUP_LABEL[g]} <span>{list.length}</span></h3>
            <ul className="cand-list">{shown.map((c) => <CardView key={c.id} c={c} />)}</ul>
            {!showAll && list.length > shown.length && (
              <button type="button" className="cand-more" onClick={() => setShowAll(true)}>
                还有 {list.length - shown.length} 条 · 查看全部
              </button>
            )}
          </div>
        );
      })}
      <details className="cand-limits">
        <summary>排序规则与限制</summary>
        <ul>{Object.entries(doc.group_rule).map(([k, v]) => <li key={k}><strong>{k}</strong>：<RichText text={v} /></li>)}</ul>
        <ul>{doc.limitations.map((t, i) => <li key={i}><RichText text={t} /></li>)}</ul>
      </details>
    </section>
  );
}
