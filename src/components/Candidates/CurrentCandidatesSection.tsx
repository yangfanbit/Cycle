/**
 * 当前候选前瞻（v0.39.1）—— 紧凑精选列表 + 详情抽屉 + 完整候选面板。
 * ★ 精选 6 条来自产物 `featured`（OOS 证据优先 + 月份/类型多样性 + 当前题材保底）。
 * ★ 详情按**字段真实结构**渲染（对象/数组不转字符串）；无数据时诚实显示。
 */
import { useEffect, useMemo, useState } from 'react';
// ★ v0.60：v0_10 = 行情刷新到 2026-10-29 后重算的候选摘要
import raw from '@current/candidate_digest_v0_10.json';
import { RichText } from '../RichText';

interface Card {
  id: string; source: string[]; kind: string; title: string; subtitle?: string;
  why_now?: string | null; time_position: string; group: 'G1' | 'G2' | 'G3' | 'G4';
  history: Record<string, unknown>;
  representative_stocks?: { series_id: string; name?: string | null; median_excess_pct: number; years?: number }[];
  gap?: string | null; watch_next?: string | null; invalidate_if?: string | null;
  trigger?: { items?: { category?: string; note?: string }[] };
  watchboard?: {
    attention_state?: string | null; candidate_status?: string | null; theme_type?: string | null;
    phase_window?: { start?: string | null; end?: string | null } | null;
    phase_evidence?: Record<string, string> | null;
    narrative_types?: string[] | null; conflict_notes?: string[] | null;
    uncertainty_notes?: string[] | string | null; research_questions?: string[] | null;
    reference_cases?: { campaign_id?: string; note?: string }[] | null;
    source_summary?: string | null;
  } | null;
  dates: { price_as_of?: string | null; research_as_of?: string | null; data_as_of?: string | null;
    artifact_generated_at?: string | null;
    research_days_old?: number | null; research_stale?: boolean };
  evidence_ref?: Record<string, string>;
}
interface Doc {
  as_of: string; counts: Record<string, number>; group_rule: Record<string, string>;
  data_dates: Record<string, unknown>; cards: Card[]; featured?: string[]; featured_note?: string;
  limitations: string[];
}
const doc = raw as unknown as Doc;

const GROUP_OF: Record<string, string> = { G1: '优先观察', G2: '结构参照', G3: '结构参照', G4: '探索线索' };
const KIND_LABEL: Record<string, string> = {
  SEASONAL_WINDOW: '季节窗口', SPECIAL_HYPOTHESIS: '专项假设', CURRENT_OBJECT: '当前新题材',
};
const TIME_LABEL: Record<string, string> = {
  PRE_WINDOW: '窗口未到', IN_WINDOW: '窗口内', ALREADY_WARM: '已升温', DATA_STALE: '数据陈旧',
  INSUFFICIENT: '证据不足', WATCH_ONLY: '事件驱动', UNKNOWN: '状态未知', PASSED: '窗口已过', LATER: '窗口较远',
};
const TIME_ORDER = ['PRE_WINDOW', 'IN_WINDOW', 'ALREADY_WARM', 'DATA_STALE', 'INSUFFICIENT',
  'WATCH_ONLY', 'UNKNOWN', 'PASSED', 'LATER',
  // ★ 当前题材的阶段状态（attention_state）也参与「时间位置」
  'THEME_FORMING', 'BROAD_CONFIRMATION', 'EXPANSION', 'COOLING', 'DORMANT'];
const ATTENTION_LABEL: Record<string, string> = {
  THEME_FORMING: '主题形成中', BROAD_CONFIRMATION: '广泛确认', EXPANSION: '扩散阶段',
  COOLING: '降温', DORMANT: '沉寂', UNKNOWN: '未知',
};
const STATUS_LABEL: Record<string, string> = {
  RESEARCHING: '研究中', WATCHING: '观察中', ARCHIVED: '已归档', CANDIDATE: '候选',
};
const EVIDENCE_DIM: Record<string, string> = {
  breadth: '市场广度', information_marginal: '信息边际', narrative: '叙事',
  policy: '政策', industry: '产业', capital: '资金',
};
const EVIDENCE_VAL: Record<string, string> = {
  EMERGING: '初现', PRESENT: '已出现', ABSENT: '缺失', STRONG: '强', WEAK: '弱', UNKNOWN: '未知',
};

/** ★ 统一「时间位置 / 阶段」标签：时间状态优先，其次阶段状态，未知保留原值 */
function timeLabel(tp: string): string {
  return TIME_LABEL[tp] ?? ATTENTION_LABEL[tp] ?? tp;
}

const num = (v: unknown, s = '%') => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(2)}${s}` : '—');
const asList = (v: string[] | string | null | undefined): string[] =>
  Array.isArray(v) ? v : (typeof v === 'string' && v.trim() ? [v] : []);

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

function useEscape(onClose: () => void) {
  useEffect(() => {
    const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', fn);
    return () => document.removeEventListener('keydown', fn);
  }, [onClose]);
}

function Detail({ c, onClose }: { c: Card; onClose: () => void }) {
  useEscape(onClose);
  const h = c.history as Record<string, unknown>;
  const wb = c.watchboard ?? {};
  const years = (h.years as string[] | undefined) ?? [];
  const per = (h.per_year as { year: string; excess_pct: number }[] | undefined) ?? [];
  const pw = wb.phase_window;
  const pe = wb.phase_evidence ?? {};
  const refs = wb.reference_cases ?? [];
  const unc = asList(wb.uncertainty_notes);
  const conflicts = asList(wb.conflict_notes);
  const questions = asList(wb.research_questions);

  return (
    <div className="cd-backdrop" onClick={onClose} role="presentation">
      <aside className="cd-panel" role="dialog" aria-modal="true" aria-label={`${c.title} 详情`}
             onClick={(e) => e.stopPropagation()} data-candidate-detail={c.id}>
        <header className="cd-head">
          <div>
            <h3>{c.title}</h3>
            <p className="cd-sub">
              {KIND_LABEL[c.kind] ?? c.kind}{c.subtitle ? ` · ${c.subtitle}` : ''} ·
              {timeLabel(c.time_position)} · {GROUP_OF[c.group]}
            </p>
          </div>
          <button type="button" className="cd-close" onClick={onClose} aria-label="关闭详情">✕</button>
        </header>

        <section className="cd-sec">
          <h4>当前判断依据</h4>
          {c.why_now && <p><RichText text={c.why_now} /></p>}
          {c.trigger?.items?.length ? (
            <ul>{c.trigger.items.map((t, i) => <li key={i}>{t.category} · <RichText text={t.note ?? ''} /></li>)}</ul>
          ) : <p className="cd-gap">未记录结构化触发（日历窗口或研究假设，不是已发生事实）。</p>}
          <p className="cd-kv">
            阶段：{ATTENTION_LABEL[wb.attention_state ?? ''] ?? (wb.attention_state ?? '未知')}
            {wb.candidate_status ? ` · 状态：${STATUS_LABEL[wb.candidate_status] ?? wb.candidate_status}` : ''}
            {wb.phase_window
              ? ` · 阶段窗口：${pw?.start ?? '起点未知'} → ${pw?.end ?? '进行中（未定结束）'}`
              : ''}
          </p>
          {Object.keys(pe).length > 0 && (
            <ul className="cd-dims">
              {Object.entries(pe).map(([k, v]) => (
                <li key={k}>{EVIDENCE_DIM[k] ?? k}：{EVIDENCE_VAL[v] ?? v}</li>
              ))}
            </ul>
          )}
          {asList(wb.narrative_types).length > 0 && (
            <p className="cd-gap">叙事类型：{asList(wb.narrative_types).join(' · ')}</p>
          )}
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
              ? `历史参照 ${(h.reference_cases as unknown[]).length} 个案例（见下方「历史案例」）`
              : '暂无可靠历史参照 —— 该方向属当前事实驱动，历史证据不足。'}</p>
          )}
          {refs.length > 0 && (
            <>
              <h4 className="cd-h4-sub">历史案例</h4>
              <ul>{refs.map((r, i) => (
                <li key={i}><code>{r.campaign_id ?? '未知案例'}</code>
                  {r.note ? <> · <RichText text={r.note} /></> : null}</li>))}
              </ul>
              <p className="cd-gap">案例 ID 可在「历史机会地图 → 历史题材/事件」中按对象检索。</p>
            </>
          )}
          {c.evidence_ref?.artifact && (
            <p className="cd-gap">证据文件：{c.evidence_ref.artifact}
              {c.evidence_ref.pattern_id ? ` · ${c.evidence_ref.pattern_id}` : ''}</p>
          )}
        </section>

        <section className="cd-sec">
          <h4>代表股票</h4>
          {(c.representative_stocks ?? []).length ? (
            <>
              <ul>{(c.representative_stocks ?? []).map((s) => (
                <li key={s.series_id}>{s.name ?? s.series_id}（{s.series_id}）· 该月中位超额 {num(s.median_excess_pct)}
                  {s.years ? ` · ${s.years} 年` : ''}</li>))}
              </ul>
              <p className="cd-gap">★ 当前成分回溯，非当年成分；不代表当年龙头。</p>
            </>
          ) : <p className="cd-gap">无个股映射：{c.gap ?? '该方向没有可核实的成分或历史成分。'}</p>}
        </section>

        <section className="cd-sec">
          <h4>下一步观察 / 降低关注</h4>
          {c.watch_next ? <p>接下来看：<RichText text={c.watch_next} /></p> : <p className="cd-gap">未记录。</p>}
          {c.invalidate_if ? <p>降低关注：<RichText text={c.invalidate_if} /></p> : null}
          {questions.length > 0 && (
            <ul>{questions.slice(0, 3).map((q, i) => <li key={i}>研究问题：{q}</li>)}</ul>
          )}
        </section>

        {conflicts.length > 0 && (
          <section className="cd-sec">
            <h4>冲突与未决</h4>
            <ul>{conflicts.map((t, i) => <li key={i}><RichText text={t} /></li>)}</ul>
          </section>
        )}

        <section className="cd-sec">
          <h4>数据日期与限制</h4>
          <p>
            {c.dates.research_as_of
              ? <>研究记录 {c.dates.research_as_of}
                {c.dates.research_stale ? `（比行情基准早 ${c.dates.research_days_old} 天，当前状态待确认）` : ''}
                {' · '}</>
              : <>统计截至 {c.dates.data_as_of ?? c.dates.price_as_of ?? '—'}（模式统计，无研究对象记录日）· </>}
            行情 {c.dates.price_as_of ?? '—'}
            {c.dates.artifact_generated_at ? ` · 产物生成 ${c.dates.artifact_generated_at}` : ''}
          </p>
          {unc.length > 0 && (
            <>
              <h4 className="cd-h4-sub">不确定项</h4>
              <ul>{unc.slice(0, 6).map((t, i) => <li key={i}><RichText text={t} /></li>)}</ul>
            </>
          )}
          {wb.source_summary ? <p className="cd-gap"><RichText text={wb.source_summary} /></p> : null}
          <p className="cd-gap"><RichText text={doc.limitations[0]} /></p>
        </section>
      </aside>
    </div>
  );
}

function FullList({ cards, onPick, onClose }: { cards: Card[]; onPick: (c: Card) => void; onClose: () => void }) {
  useEscape(onClose);
  const [q, setQ] = useState('');
  const [month, setMonth] = useState('all');
  const [kind, setKind] = useState('all');
  const [time, setTime] = useState('all');
  const months = useMemo(() => {
    const s = new Set<string>();
    cards.forEach((c) => { const m = /·\s*(\d+)\s*月/.exec(c.title); if (m) s.add(m[1]); });
    return [...s].sort((a, b) => Number(a) - Number(b));
  }, [cards]);
  const times = useMemo(() => {
    const present = new Set(cards.map((c) => c.time_position));
    const known = TIME_ORDER.filter((t) => present.has(t));
    const unknown = [...present].filter((t) => !TIME_ORDER.includes(t)).sort();
    return [...known, ...unknown];   // ★ 未知新状态保留原值，不被静默过滤
  }, [cards]);
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
      <aside className="cd-panel cd-panel-wide" role="dialog" aria-modal="true" aria-label="全部候选"
             onClick={(e) => e.stopPropagation()}>
        <header className="cd-head">
          <div><h3>全部候选（{list.length}/{cards.length}）</h3>
            <p className="cd-sub">筛选：月份 / 类型 / 时间位置 / 名称搜索（选项随产物动态生成）</p></div>
          <button type="button" className="cd-close" onClick={onClose} aria-label="关闭">✕</button>
        </header>
        <div className="cd-filters">
          <input aria-label="搜索候选名称" placeholder="搜索名称…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select aria-label="月份" value={month} onChange={(e) => setMonth(e.target.value)}>
            <option value="all">全部月份</option>
            {months.map((m) => <option key={m} value={m}>{m} 月</option>)}
          </select>
          <select aria-label="类型" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="all">全部类型</option>
            <option value="SEASONAL_WINDOW">季节窗口</option>
            <option value="CURRENT_OBJECT">当前新题材</option>
            <option value="SPECIAL_HYPOTHESIS">专项假设</option>
          </select>
          <select aria-label="时间位置" value={time} onChange={(e) => setTime(e.target.value)}>
            <option value="all">全部时机</option>
            {times.map((t) => <option key={t} value={t}>{timeLabel(t)}</option>)}
          </select>
        </div>
        <ul className="cd-full-list">
          {list.slice(0, 400).map((c) => (
            <li key={c.id}>
              <button type="button" onClick={() => onPick(c)}>
                <span className="cd-fl-title">{c.title}</span>
                <span className="cd-fl-meta">{KIND_LABEL[c.kind] ?? c.kind} · {timeLabel(c.time_position)} · {GROUP_OF[c.group]}</span>
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
  const byId = useMemo(() => new Map(doc.cards.map((c) => [c.id, c])), []);
  const top = (doc.featured ?? doc.cards.slice(0, 6).map((c) => c.id))
    .map((id) => byId.get(id)).filter((c): c is Card => Boolean(c));
  const dd = doc.data_dates as Record<string, unknown>;
  const snap = dd.snapshot_latest_canonical as { snapshot_date?: string } | null;
  const oldDays = Number(dd.research_candidates_days_old ?? 0);

  return (
    <section className="cand" aria-label="当前候选前瞻" data-candidates-as-of={doc.as_of}>
      <div className="cand-head-row">
        <h2 className="cand-h2">当前候选前瞻</h2>
        <span className="cand-meta" data-dates="1">
          行情截至 <code>{doc.as_of}</code> · 当前研究对象记录于 <code>{String(dd.research_candidates_as_of ?? '—')}</code>
          {oldDays > 7 ? `（比行情基准早 ${oldDays} 天）` : ''} · 最新已签发快照 <code>{snap?.snapshot_date ?? '—'}</code>
        </span>
      </div>
      <p className="cand-lead">
        按<strong>历史证据与时间优势</strong>排序的研究浏览顺序（不是收益预测）：先看有样本外支持、窗口未走完的方向，
        并为当前政策／产业题材保留位置。点条目看完整依据、代表股票与限制。
      </p>

      <ol className="cand-rows">
        {top.map((c) => (
          <li key={c.id} className="cand-row" data-candidate={c.id} data-group={c.group}
              data-time={c.time_position} data-kind={c.kind}>
            <button type="button" className="cand-row-btn" onClick={() => setDetail(c)}>
              <span className="cr-line1">
                <strong>{c.title}</strong>
                <span className="cr-chip">{KIND_LABEL[c.kind] ?? c.kind}</span>
                <span className={`cr-time t-${c.time_position.toLowerCase()}`}>{timeLabel(c.time_position)}</span>
                <span className="cr-group">{GROUP_OF[c.group]}</span>
                {c.dates.research_stale && <span className="cr-stale">研究记录较旧</span>}
              </span>
              <span className="cr-line2"><RichText text={c.why_now ?? ''} /></span>
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
