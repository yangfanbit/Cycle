/**
 * 当前候选前瞻（v0.39）—— 紧凑列表 + 详情抽屉 + 完整列表面板。
 * ★ 首屏只列 6 条：方向 / 类型 / 时机 / 一句为什么 / 一行历史证据 / 陈旧提示。
 * ★ 其余信息（观察台阶段、依据、代表股票、历史案例、验证、日期与限制）全部进抽屉。
 * ★ 分组只保留三种标签（优先观察 / 结构参照 / 探索线索），证据含义不变。
 */
import { useMemo, useState } from 'react';
import raw from '@current/candidate_digest_v0_2.json';
import { RichText } from '../RichText';

interface Card {
  id: string; source: string[]; kind: string; title: string; subtitle?: string;
  why_now?: string | null; time_position: string; group: 'G1' | 'G2' | 'G3' | 'G4';
  history: Record<string, unknown>;
  representative_stocks?: { series_id: string; name?: string | null; median_excess_pct: number; years?: number }[];
  gap?: string | null; watch_next?: string | null; invalidate_if?: string | null;
  trigger?: { items?: { category?: string; note?: string }[] };
  watchboard?: Record<string, unknown> | null;
  dates: { price_as_of?: string | null; research_as_of?: string | null;
    research_days_old?: number | null; research_stale?: boolean };
  evidence_ref?: Record<string, string>;
}
interface Doc {
  as_of: string; counts: Record<string, number>; group_rule: Record<string, string>;
  data_dates: Record<string, unknown>; cards: Card[]; limitations: string[];
}
const doc = raw as unknown as Doc;

const GROUP_OF: Record<string, '优先观察' | '结构参照' | '探索线索'> = {
  G1: '优先观察', G2: '结构参照', G3: '结构参照', G4: '探索线索',
};
const KIND_LABEL: Record<string, string> = {
  SEASONAL_WINDOW: '季节窗口', SPECIAL_HYPOTHESIS: '专项假设', CURRENT_OBJECT: '当前新题材',
};
const TIME_LABEL: Record<string, string> = {
  PRE_WINDOW: '窗口未到', IN_WINDOW: '窗口内', ALREADY_WARM: '已升温',
  DATA_STALE: '数据陈旧', INSUFFICIENT: '证据不足', WATCH_ONLY: '事件驱动',
  UNKNOWN: '状态未知', PASSED: '窗口已过', LATER: '窗口较远',
};
const HOME_N = 6;

const num = (v: unknown, s = '%') => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(2)}${s}` : '—');

function historyLine(c: Card): string {
  const h = c.history as Record<string, unknown>;
  if (typeof h.n_years === 'number') {
    const oos = h.oos_status === 'REPORTED'
      ? ` · 样本外 ${h.oos_tests} 年命中 ${Math.round(Number(h.oos_hit_rate ?? 0) * 100)}%`
      : ' · 样本外证据不足';
    return `历史 ${h.n_years} 年 · 中位 ${num(h.median_excess_pct)}${oos}`;
  }
  const refs = h.reference_cases;
  if (Array.isArray(refs) && refs.length) return `历史参照 ${refs.length} 个案例`;
  return '尚无可靠历史参照';
}

function Detail({ c, onClose }: { c: Card; onClose: () => void }) {
  const h = c.history as Record<string, unknown>;
  const wb = (c.watchboard ?? {}) as Record<string, unknown>;
  const years = (h.years as string[] | undefined) ?? [];
  const per = (h.per_year as { year: string; excess_pct: number }[] | undefined) ?? [];
  return (
    <div className="cd-backdrop" onClick={onClose} role="presentation">
      <aside className="cd-panel" role="dialog" aria-label={`${c.title} 详情`} onClick={(e) => e.stopPropagation()}
             data-candidate-detail={c.id}>
        <header className="cd-head">
          <div>
            <h3>{c.title}</h3>
            <p className="cd-sub">
              {KIND_LABEL[c.kind] ?? c.kind}{c.subtitle ? ` · ${c.subtitle}` : ''} ·
              {TIME_LABEL[c.time_position] ?? c.time_position} · {GROUP_OF[c.group]}
            </p>
          </div>
          <button type="button" className="cd-close" onClick={onClose} aria-label="关闭详情">✕</button>
        </header>

        <section className="cd-sec">
          <h4>当前判断依据</h4>
          {c.why_now && <p><RichText text={c.why_now} /></p>}
          {c.trigger?.items?.length ? (
            <ul>{c.trigger.items.map((t, i) => <li key={i}>{t.category} · <RichText text={t.note ?? ''} /></li>)}</ul>
          ) : <p className="cd-gap">未记录结构化触发（可能是日历窗口或研究假设，不是已发生事实）。</p>}
          {wb.phase_window ? <p>阶段窗口：{String(wb.phase_window)}</p> : null}
          {Array.isArray(wb.phase_evidence) && (wb.phase_evidence as unknown[]).length > 0 && (
            <ul>{(wb.phase_evidence as { note?: string }[]).slice(0, 4).map((x, i) =>
              <li key={i}><RichText text={x.note ?? ''} /></li>)}</ul>
          )}
          {wb.attention_state ? <p className="cd-gap">观察台状态：{String(wb.attention_state)}</p> : null}
        </section>

        <section className="cd-sec">
          <h4>历史结构与验证</h4>
          {typeof h.n_years === 'number' ? (
            <>
              <p>样本 {h.n_years} 年（{years.length ? `${years[0]}–${years[years.length - 1]}` : '—'}）
                · 中位超额 {num(h.median_excess_pct)} · 命中 {h.hit_rate ? `${Math.round(Number(h.hit_rate) * 100)}%` : '—'}</p>
              <p>样本外：{h.oos_status === 'REPORTED'
                ? `${h.oos_tests} 个检验年 · 命中 ${Math.round(Number(h.oos_hit_rate ?? 0) * 100)}% · 中位 ${num(h.oos_median_excess_pct)}`
                : '证据不足，不作结论'}</p>
              {per.length > 0 && (
                <p className="cd-per">逐年：{per.map((x) => `${x.year} ${x.excess_pct > 0 ? '+' : ''}${x.excess_pct}%`).join(' · ')}</p>
              )}
            </>
          ) : (
            <p>{(h.reference_cases as unknown[] | undefined)?.length
              ? `历史参照 ${(h.reference_cases as unknown[]).length} 个案例（详见历史机会地图）`
              : '暂无可靠历史参照 —— 该方向属当前事实驱动，历史证据不足。'}</p>
          )}
          {c.evidence_ref?.artifact && (
            <p className="cd-gap">证据文件：{c.evidence_ref.artifact}
              {c.evidence_ref.pattern_id ? ` · ${c.evidence_ref.pattern_id}` : ''}</p>
          )}
        </section>

        <section className="cd-sec">
          <h4>代表股票</h4>
          {(c.representative_stocks ?? []).length ? (
            <ul>{(c.representative_stocks ?? []).map((s) => (
              <li key={s.series_id}>
                {s.name ?? s.series_id}（{s.series_id}）· 该月中位超额 {num(s.median_excess_pct)}
                {s.years ? ` · ${s.years} 年` : ''}
              </li>))}
            </ul>
          ) : <p className="cd-gap">无个股映射：{c.gap ?? '该方向没有可核实的成分或历史成分。'}</p>}
          {(c.representative_stocks ?? []).length > 0 && (
            <p className="cd-gap">★ 当前成分回溯，非当年成分；不代表当年龙头。</p>
          )}
        </section>

        <section className="cd-sec">
          <h4>下一步观察 / 降低关注</h4>
          {c.watch_next ? <p>接下来看：<RichText text={c.watch_next} /></p> : <p className="cd-gap">未记录。</p>}
          {c.invalidate_if ? <p>降低关注：<RichText text={c.invalidate_if} /></p> : null}
          {Array.isArray(wb.research_questions) && (wb.research_questions as string[]).length > 0 && (
            <ul>{(wb.research_questions as string[]).slice(0, 3).map((q, i) => <li key={i}>研究问题：{q}</li>)}</ul>
          )}
        </section>

        <section className="cd-sec">
          <h4>数据日期与限制</h4>
          <p>行情 {c.dates.price_as_of ?? '—'} · 研究记录 {c.dates.research_as_of ?? '—'}
            {c.dates.research_stale ? `（较旧 ${c.dates.research_days_old} 天，当前状态待确认）` : ''}</p>
          {wb.uncertainty_notes ? <p className="cd-gap"><RichText text={String(wb.uncertainty_notes)} /></p> : null}
          <p className="cd-gap"><RichText text={doc.limitations[0]} /></p>
        </section>
      </aside>
    </div>
  );
}

function FullList({ cards, onPick, onClose }: { cards: Card[]; onPick: (c: Card) => void; onClose: () => void }) {
  const [q, setQ] = useState('');
  const [month, setMonth] = useState('all');
  const [kind, setKind] = useState('all');
  const [time, setTime] = useState('all');
  const list = useMemo(() => cards.filter((c) => {
    if (q && !c.title.includes(q)) return false;
    if (kind !== 'all' && c.kind !== kind) return false;
    if (time !== 'all' && c.time_position !== time) return false;
    if (month !== 'all') {
      const m = /·\s*(\d+)\s*月/.exec(c.title);
      if (!m || m[1] !== month) return false;
    }
    return true;
  }), [cards, q, kind, time, month]);
  return (
    <div className="cd-backdrop" onClick={onClose} role="presentation">
      <aside className="cd-panel cd-panel-wide" role="dialog" aria-label="全部候选" onClick={(e) => e.stopPropagation()}>
        <header className="cd-head">
          <div><h3>全部候选（{list.length}/{cards.length}）</h3>
            <p className="cd-sub">筛选：月份 / 类型 / 时间位置 / 名称搜索</p></div>
          <button type="button" className="cd-close" onClick={onClose} aria-label="关闭">✕</button>
        </header>
        <div className="cd-filters">
          <input aria-label="搜索候选名称" placeholder="搜索名称…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select aria-label="月份" value={month} onChange={(e) => setMonth(e.target.value)}>
            <option value="all">全部月份</option><option value="10">10 月</option><option value="11">11 月</option>
          </select>
          <select aria-label="类型" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="all">全部类型</option>
            <option value="SEASONAL_WINDOW">季节窗口</option>
            <option value="CURRENT_OBJECT">当前新题材</option>
            <option value="SPECIAL_HYPOTHESIS">专项假设</option>
          </select>
          <select aria-label="时间位置" value={time} onChange={(e) => setTime(e.target.value)}>
            <option value="all">全部时机</option>
            <option value="PRE_WINDOW">窗口未到</option>
            <option value="IN_WINDOW">窗口内</option>
            <option value="DATA_STALE">数据陈旧</option>
            <option value="INSUFFICIENT">证据不足</option>
          </select>
        </div>
        <ul className="cd-full-list">
          {list.slice(0, 400).map((c) => (
            <li key={c.id}>
              <button type="button" onClick={() => onPick(c)}>
                <span className="cd-fl-title">{c.title}</span>
                <span className="cd-fl-meta">{KIND_LABEL[c.kind] ?? c.kind} · {TIME_LABEL[c.time_position] ?? c.time_position} · {GROUP_OF[c.group]}</span>
                <span className="cd-fl-hist">{historyLine(c)}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}

export function CurrentCandidatesSection() {
  const [detail, setDetail] = useState<Card | null>(null);
  const [all, setAll] = useState(false);
  const top = doc.cards.slice(0, HOME_N);
  const dd = doc.data_dates as Record<string, unknown>;
  const snap = dd.snapshot_latest_canonical as { snapshot_date?: string } | null;
  const oldDays = Number(dd.research_candidates_days_old ?? 0);

  return (
    <section className="cand" aria-label="当前候选前瞻" data-candidates-as-of={doc.as_of}>
      <div className="cand-head-row">
        <h2 className="cand-h2">当前候选前瞻</h2>
        <span className="cand-meta" data-dates="1">
          行情截至 <code>{doc.as_of}</code> · 当前研究对象记录于 <code>{String(dd.research_candidates_as_of ?? '—')}</code>
          {oldDays > 7 ? `（较旧 ${oldDays} 天）` : ''} · 最新已签发快照 <code>{snap?.snapshot_date ?? '—'}</code>
        </span>
      </div>
      <p className="cand-lead">
        按历史证据与时间优势排序的<strong>研究浏览顺序</strong>（不是收益预测）：先看有样本外支持、窗口未走完的方向。
        点条目看完整依据、代表股票与限制。
      </p>

      <ol className="cand-rows">
        {top.map((c) => (
          <li key={c.id} className="cand-row" data-candidate={c.id} data-group={c.group}
              data-time={c.time_position} data-kind={c.kind}>
            <button type="button" className="cand-row-btn" onClick={() => setDetail(c)}>
              <span className="cr-line1">
                <strong>{c.title}</strong>
                <span className="cr-chip">{KIND_LABEL[c.kind] ?? c.kind}</span>
                <span className={`cr-time t-${c.time_position.toLowerCase()}`}>{TIME_LABEL[c.time_position] ?? c.time_position}</span>
                <span className="cr-group">{GROUP_OF[c.group]}</span>
                {c.dates.research_stale && <span className="cr-stale">研究记录较旧</span>}
              </span>
              <span className="cr-line2"><RichText text={(c.why_now ?? '').slice(0, 90)} /></span>
              <span className="cr-line3">{historyLine(c)}</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="cand-actions">
        <button type="button" className="cand-all" onClick={() => setAll(true)} data-show-all="1">
          查看全部（{doc.cards.length}）
        </button>
        <span className="cand-note">
          共 {doc.cards.length} 条 · 优先观察 {doc.counts.G1} · 结构参照 {doc.counts.G2 + doc.counts.G3}
          {' '}· 探索线索 {doc.counts.G4}
        </span>
      </div>

      {detail && <Detail c={detail} onClose={() => setDetail(null)} />}
      {all && <FullList cards={doc.cards} onPick={(c) => { setAll(false); setDetail(c); }} onClose={() => setAll(false)} />}
    </section>
  );
}
