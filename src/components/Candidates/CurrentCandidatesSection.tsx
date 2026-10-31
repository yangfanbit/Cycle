/**
 * 当前候选前瞻（v0.65）—— **三类对象分三段展示**，不再共用一组六条精选。
 *
 * ## 为什么必须分段
 *
 * v0_11 把 213 张卡片（季节窗口 204 · 专项假设 3 · 当前研究主题 6）混排后取前 6 条精选：
 * 季节窗口一旦占满，6 个当前研究主题里就有 4 个被挤出主入口 —— 而当前研究主题是
 * 「人正在研究什么」，不该由统计候选的数量决定是否可见。
 *
 * 现在的三段（id 列表来自产物 `sections`，不在前端重算）：
 * 1. **当前研究主题**：全部展示；属于当前主题证据研究，不是算法发现的季节窗口，
 *    也**不适用** 5/10/20 交易日结算。
 * 2. **季节性统计窗口**：只放预览（`seasonal_preview`），并就地给出全量规模
 *    （`seasonal_scale`），避免「只有 6 条」被读成「系统只发现了 6 条」。
 * 3. **专项假设的历史检验**：人工预设假设（生肖 / 台海 / 流感），不是通用挖掘器。
 *
 * ★ 缺股按 `stock_gap_reason` 三分显示（行业板块无历史成分 / 当前主题未建映射 / 专项假设未接入），
 *   不再一律写成「没有可核实的成分」。
 * ★ 详情按**字段真实结构**渲染；无数据时诚实显示。
 */
import { useEffect, useMemo, useState } from 'react';
// ★ v0.60：v0_10 = 行情刷新到 2026-10-29 后重算的候选摘要
// ★ v0.62：v0_11 = 行情刷新到 2026-10-30 后重算的候选摘要
// ★ v0.65：v0_12 = 三类对象分段（sections）+ 缺股原因 + 当前主题标的映射
import raw from '@current/candidate_digest_v0_12.json';
import { RichText } from '../RichText';

interface RelatedSecurity {
  security_id: string; name: string; ticker?: string | null;
  basis?: string; evidence_id?: string | null; quote?: string;
}
interface RelatedSecurities {
  status: 'MAPPED' | 'NOT_MAPPED';
  label?: string; nature?: string; basis_rule?: string; as_of?: string | null;
  items?: RelatedSecurity[]; reason?: string; what_is_needed?: string;
  dropped?: { security_id: string; reason: string }[];
}
interface Card {
  id: string; source: string[]; kind: string; title: string; subtitle?: string;
  why_now?: string | null; time_position: string; group: 'G1' | 'G2' | 'G3' | 'G4';
  history: Record<string, unknown>;
  representative_stocks?: { series_id: string; name?: string | null; median_excess_pct: number; years?: number }[];
  /** ★ v0.65：缺股**原因**（null = 有股） */
  stock_gap_reason?: 'NO_HISTORICAL_CONSTITUENTS' | 'NO_SECURITY_MAPPING' | 'HYPOTHESIS_NO_SECURITY_LINK' | null;
  /** ★ v0.65：当前研究主题的「当前相关标的」 */
  related_securities?: RelatedSecurities | null;
  /** ★ v0.65：发现结果的公共元信息 */
  discovery?: {
    source_class?: string; source?: string[]; method_version?: string | null;
    as_of?: string | null; coverage?: string; tracking?: string;
    settlement_horizons?: string[] | null;
  } | null;
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
interface Section { ids: string[]; note: string }
interface Doc {
  as_of: string; counts: Record<string, number>; group_rule: Record<string, string>;
  data_dates: Record<string, unknown>; cards: Card[];
  /** ★ v0.65：三个入口（取代原 featured 单一 6 条混合精选） */
  sections?: { current_objects?: Section; seasonal_preview?: Section; special_hypotheses?: Section };
  /** ★ v0.65：季节性统计规模（全量 / 当前窗口 / 样本外 / 仅时点资格） */
  seasonal_scale?: Record<string, number | string | null>;
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
/**
 * ★★ v0.64：比例（命中率）的显示 —— **0 是有效值**，不能与「缺失」混为一谈。
 *
 * 原实现用 truthy 判断 `h.hit_rate ? … : '—'` → `hit_rate === 0`（真实存在、就是 0%）
 * 被当成缺失显示「—」，把「0% 命中」读成「没有数据」。
 * 判据改为**显式数值判断**：有限数值 → 百分比（含 0%）；其余 → `—`。
 * 不改统计口径与排序逻辑。
 */
export const pctOrDash = (v: unknown): string =>
  typeof v === 'number' && Number.isFinite(v) ? `${Math.round(v * 100)}%` : '—';

const asList = (v: string[] | string | null | undefined): string[] =>
  Array.isArray(v) ? v : (typeof v === 'string' && v.trim() ? [v] : []);

function historyLine(c: Card): string {
  const h = c.history as Record<string, unknown>;
  if (typeof h.n_years === 'number') {
    const oos = h.oos_status === 'REPORTED'
      ? ` · 样本外 ${h.oos_tests} 年命中 ${pctOrDash(h.oos_hit_rate)}`
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

/**
 * ★★ v0.65：缺股**原因**的三分文案。
 *
 * 原来三种情况都显示「没有可核实的成分或历史成分」，读者无法区分
 * 「这个板块本来就没有历史成分数据」与「这个当前主题还没做标的映射」——
 * 后者是研究待办，前者是数据边界，混在一起会让人误判研究进度。
 */
const STOCK_GAP_SHORT: Record<string, string> = {
  NO_HISTORICAL_CONSTITUENTS: '不绑个股：行业板块没有已接入的历史成分数据',
  NO_SECURITY_MAPPING: '尚未建立标的映射：本主题研究正文未出现可与证券注册表精确对应的公司名',
  HYPOTHESIS_NO_SECURITY_LINK: '不列个股：专项假设未接入个股列表',
};

/** 卡片列表里的一行个股说明（完整说明见详情） */
function stockLine(c: Card): string {
  if (c.kind === 'CURRENT_OBJECT') {
    const rel = c.related_securities;
    const items = rel?.items ?? [];
    if (rel?.status === 'MAPPED' && items.length > 0) {
      return `当前相关标的：${items.map((x) => `${x.name}${x.ticker ? ` ${x.ticker}` : ''}`).join(' · ')}`
        + '（研究正文点名，非历史代表股）';
    }
    return STOCK_GAP_SHORT.NO_SECURITY_MAPPING;
  }
  const stocks = c.representative_stocks ?? [];
  if (stocks.length > 0) {
    return `代表股票：${stocks.slice(0, 4).map((x) => x.name ?? x.series_id).join(' · ')}`
      + `${stocks.length > 4 ? ` 等 ${stocks.length} 只` : ''}`;
  }
  return STOCK_GAP_SHORT[c.stock_gap_reason ?? ''] ?? '未列个股';
}

/** ★ 当前研究主题的「当前相关标的」区块（带出处；不是历史代表股） */
function RelatedSecuritiesBlock({ rel }: { rel: RelatedSecurities }) {
  if (rel.status === 'MAPPED') {
    return (
      <section className="cd-sec" data-related-securities="MAPPED">
        <h4>{rel.label ?? '当前相关标的'}</h4>
        <ul className="cd-secs">
          {(rel.items ?? []).map((x) => (
            <li key={x.security_id}>
              <strong>{x.name}</strong>
              {x.ticker ? <code> {x.ticker}</code> : null}
              <span className="cd-sec-basis">
                {x.basis ?? '研究正文点名'}
                {x.evidence_id ? `（${x.evidence_id}）` : ''}
              </span>
              {x.quote ? <p className="cd-sec-quote">原文：…{x.quote}…</p> : null}
            </li>
          ))}
        </ul>
        <p className="cd-gap"><RichText text={rel.nature ?? ''} /></p>
        {rel.basis_rule ? <p className="cd-gap">{rel.basis_rule}</p> : null}
      </section>
    );
  }
  return (
    <section className="cd-sec" data-related-securities="NOT_MAPPED">
      <h4>{rel.label ?? '当前相关标的'}</h4>
      <p className="cd-gap">尚未建立映射：{rel.reason ?? '本主题还没有可核验的标的映射'}</p>
      {rel.what_is_needed ? <p className="cd-gap">下一步：{rel.what_is_needed}</p> : null}
    </section>
  );
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

        {/* ★★ v0.65：个股区按**原因**分开展示 ——
            当前主题用「当前相关标的」（带出处），季节窗口/专项假设用各自的原因说明。 */}
        {c.kind === 'CURRENT_OBJECT' && c.related_securities ? (
          <RelatedSecuritiesBlock rel={c.related_securities} />
        ) : (
          <section className="cd-sec" data-stock-gap={c.stock_gap_reason ?? 'NONE'}>
            <h4>代表股票</h4>
            <p className="cd-gap">
              {STOCK_GAP_SHORT[c.stock_gap_reason ?? ''] ?? '未列个股'}
            </p>
            {(c.representative_stocks ?? []).length > 0 && (
              <ul className="cd-secs">
                {(c.representative_stocks ?? []).map((s) => (
                  <li key={s.series_id}>
                    <strong>{s.name ?? s.series_id}</strong>
                    {s.years ? <span className="cd-sec-basis"> {s.years} 年</span> : null}
                    <span className="cd-sec-basis"> 中位超额 {num(s.median_excess_pct)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        <section className="cd-sec">
          <h4>历史结构与验证</h4>
          {typeof h.n_years === 'number' ? (
            <>
              <p>样本 {h.n_years} 年（{years.length ? `${years[0]}–${years[years.length - 1]}` : '—'}）
                · 中位超额 {num(h.median_excess_pct)} · 命中 {pctOrDash(h.hit_rate)}</p>
              <p>样本外：{h.oos_status === 'REPORTED'
                ? `${h.oos_tests} 个检验年 · 命中 ${pctOrDash(h.oos_hit_rate)} · 中位 ${num(h.oos_median_excess_pct)}`
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

/** 一段候选列表（三类对象共用同一行样式，但各有自己的标题与说明） */
function CardRow({ c, onPick }: { c: Card; onPick: (c: Card) => void }) {
  return (
    <li className="cand-row" data-candidate={c.id} data-group={c.group}
        data-time={c.time_position} data-kind={c.kind}>
      <button type="button" className="cand-row-btn" onClick={() => onPick(c)}>
        <span className="cr-line1">
          <strong>{c.title}</strong>
          <span className="cr-chip">{KIND_LABEL[c.kind] ?? c.kind}</span>
          <span className={`cr-time t-${c.time_position.toLowerCase()}`}>{timeLabel(c.time_position)}</span>
          <span className="cr-group">{GROUP_OF[c.group]}</span>
          {c.dates.research_stale && <span className="cr-stale">研究记录较旧</span>}
        </span>
        <span className="cr-line2"><RichText text={c.why_now ?? ''} /></span>
        <span className="cr-line3">{historyLine(c)}</span>
        <span className="cr-line4" data-stock-line="1">{stockLine(c)}</span>
      </button>
    </li>
  );
}

export function CurrentCandidatesSection() {
  const [detail, setDetail] = useState<Card | null>(null);
  const [all, setAll] = useState(false);
  const byId = useMemo(() => new Map(doc.cards.map((c) => [c.id, c])), []);
  const pick = (ids: string[] | undefined) =>
    (ids ?? []).map((id) => byId.get(id)).filter((c): c is Card => Boolean(c));
  // ★ 兼容旧产物：没有 `sections` 时按 kind 回退（当前主题仍然全部展示，不再只给 1 条）
  const fallback = (kind: string) => doc.cards.filter((c) => c.kind === kind).map((c) => c.id);
  const curObjects = pick(doc.sections?.current_objects?.ids ?? fallback('CURRENT_OBJECT'));
  const seasonal = pick(doc.sections?.seasonal_preview?.ids
    ?? doc.cards.filter((c) => c.kind === 'SEASONAL_WINDOW').slice(0, 6).map((c) => c.id));
  const hypotheses = pick(doc.sections?.special_hypotheses?.ids ?? fallback('SPECIAL_HYPOTHESIS'));
  const dd = doc.data_dates as Record<string, unknown>;
  const snap = dd.snapshot_latest_canonical as { snapshot_date?: string } | null;
  const oldDays = Number(dd.research_candidates_days_old ?? 0);
  const scale = doc.seasonal_scale ?? {};
  const seasonalTotal = Number(scale.current_windows ?? 0);

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
        这里有三类<strong>互不替代</strong>的研究入口：<strong>当前研究主题</strong>（人正在研究什么）、
        <strong>季节性统计窗口</strong>（历史月度收益模式的当前/下月窗口）、
        <strong>专项假设的历史检验</strong>（人工预设假设）。分组是研究浏览顺序，
        <strong>不是</strong>概率、胜率或收益预测。
      </p>

      {/* ---------- ① 当前研究主题：全部展示，不受统计候选数量影响 ---------- */}
      <h3 className="cand-sec-h3" data-cand-section="current_objects">
        一、当前研究主题（{curObjects.length}）
      </h3>
      <p className="cand-sec-note">
        <RichText text={doc.sections?.current_objects?.note
          ?? '当前研究主题：独立入口、全部展示；不适用 5/10/20 交易日结算。'} />
      </p>
      <ol className="cand-rows" data-rows="current_objects">
        {curObjects.map((c) => <CardRow key={c.id} c={c} onPick={setDetail} />)}
      </ol>

      {/* ---------- ② 季节性统计窗口：预览 + 全量规模 ---------- */}
      <h3 className="cand-sec-h3" data-cand-section="seasonal_preview">
        二、季节性统计窗口 · 预览（{seasonal.length} / {seasonalTotal || '—'}）
      </h3>
      <p className="cand-sec-note">
        <RichText text={doc.sections?.seasonal_preview?.note
          ?? '季节性统计窗口：这里只是预览，全量见「查看全部」。'} />
      </p>
      {seasonalTotal > 0 && (
        <p className="cand-scale" data-seasonal-scale="1">
          全量模式 <strong>{String(scale.patterns_total ?? '—')}</strong> 条
          （STRICT {String(scale.patterns_strict ?? '—')} / 探索 {String(scale.patterns_exploratory ?? '—')}）
          · 当前或下月窗口 <strong>{String(scale.current_windows ?? '—')}</strong>
          · 样本外可报告 <strong>{String(scale.oos_reportable ?? '—')}</strong>
          · 仅时点资格 <strong>{String(scale.pit_only ?? '—')}</strong>
          <span className="cand-note">（四个数互不替代；结算结果见候选账本，不在此处）</span>
        </p>
      )}
      <ol className="cand-rows" data-rows="seasonal_preview">
        {seasonal.map((c) => <CardRow key={c.id} c={c} onPick={setDetail} />)}
      </ol>

      {/* ---------- ③ 专项假设：人工预设，不是通用挖掘器 ---------- */}
      <h3 className="cand-sec-h3" data-cand-section="special_hypotheses">
        三、专项假设的历史检验（{hypotheses.length}）
      </h3>
      <p className="cand-sec-note">
        <RichText text={doc.sections?.special_hypotheses?.note
          ?? '专项假设的历史检验：人工预设假设，不是通用主题挖掘器。'} />
      </p>
      <ol className="cand-rows" data-rows="special_hypotheses">
        {hypotheses.map((c) => <CardRow key={c.id} c={c} onPick={setDetail} />)}
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
