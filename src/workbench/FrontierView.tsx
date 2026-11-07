/**
 * 前瞻排程（v0.77）—— 工作台**默认主入口**。
 *
 * ★★ 方向纠正：v0.74 的工作台是「我提问 → 系统给历史对照」的 pull / 事后研究，
 * 与使用者的目标相反。这里改成 push / 事前：系统主动推出「接下来值得关注的
 * 概念板块 / 窗口 + 理由」，用户点进去才看证据与来源。
 *
 * ## 双轨并列（不做因果拼接）
 *  - 统计轨（季度更新）：候选摘要的历史重复 / 样本外检验 / G1→G4 研究浏览顺序
 *  - 机制轨（每周更新）：本周新增可核政策事件 + 已知日历事实 + A_CALENDAR 前置观察
 * 两轨各自 as_of 独立标注。★ 实测 177 张统计卡里能与雷达板块序列**精确**匹配的
 * 只有 1 条 → 机制轨作为独立信息流展示，不给统计卡硬贴理由、不做模糊匹配。
 *
 * ## 措辞边界（v0.77）
 * 「值得关注 / 可斟酌的决策点」= 前置观察窗口 / 研究起点，**不是买卖点**；
 * 具体的买卖决策由使用者自行做出。不出现买入/卖出/目标价/仓位/胜率。
 */
import { useMemo, useState } from 'react';
import { RichText } from '../components/RichText';

export interface FrontierItem {
  id: string; track: string; group: string; order: number; attention_label: string;
  title: string; subtitle?: string | null; kind?: string; time_position?: string;
  window_hint?: string; why_now?: string | null;
  statistical_reason?: Record<string, unknown> | null;
  mechanism_reason?: { kind: string; relation: string; board_series: string;
    event_id: string; event_date: string; title: string; url: string; caveat: string } | null;
  trigger_type?: string | null; watch_next?: string | null; invalidate_if?: string | null;
  gap?: string | null; evidence_ref?: Record<string, unknown> | null;
  source_artifacts?: string[];
  representative_stocks?: { series_id: string; name?: string | null;
    median_excess_pct?: number; years?: number; source?: string }[];
  representative_stocks_total?: number; stock_gap_reason?: string | null;
}
export interface FrontierDoc {
  artifact: string; artifact_version: string; purpose: string;
  tracks: { statistical: { as_of: string; cadence: string; source: string; note: string };
            mechanism: { as_of: string; cadence: string; source: string[];
                         note: string; feed_window: [string, string] } };
  group_rule: { order: string[]; meaning: string;
                attention_label_rule: Record<string, string> };
  selection_rule: { hard_gate: string; sort_keys: string[]; month_quota: null | number;
                    month_quota_note: string; fixed_sections_not_competing: string[]; note: string };
  top6: { id: string; rank: number; rank_reason: string }[];
  fixed_sections: { current_objects: string[]; special_hypotheses: string[] };
  hit_rate_definition: string;
  counts: Record<string, unknown>;
  limits: string[]; items: FrontierItem[];
  mechanism_feed: { event_id: string; date: string; title: string; publisher?: string;
                    url: string; doc_class?: string; theme_tags: string[];
                    fact_vs_assumption: string; caveat: string }[];
  calendar_ref: string;
}
export interface EventCalendar {
  artifact: string; as_of: string; track: string; cadence: string; scope_note: string;
  entries: { date: string; kind: string; label?: string; year?: number; animal?: string;
             fact_vs_assumption: string }[];
  hypotheses: { family: string; pattern_id: string; title: string; not_a_theme: boolean;
                note: string; role?: string; status_in_existing_artifact: string;
                mapping_layers: { layer: string; rule: string; examples: string[];
                                  status: string; usage?: string; note: string }[] }[];
  known_gaps: { id: string; detail: string; blocks: string }[];
}

const GROUP_LABEL: Record<string, string> = {
  G1: '优先观察 · 值得关注', G2: '结构参照 · 可斟酌的决策点',
  G3: '结构参照（证据不足）', G4: '探索线索 / 仅留档',
};
const POS_LABEL: Record<string, string> = {
  IN_WINDOW: '窗口内', PRE_WINDOW: '窗口未开始', PRE_OBSERVATION: '前置观察',
  THEME_FORMING: '主题形成中', BROAD_CONFIRMATION: '广度确认',
  EXPANSION: '扩散', WATCH_ONLY: '仅观察', INSUFFICIENT: '证据不足',
};

function num(v: unknown, digits = 2): string {
  return typeof v === 'number' ? v.toFixed(digits) : '—';
}

const STOCK_GAP_LABEL: Record<string, string> = {
  NO_HISTORICAL_CONSTITUENTS: '行业板块是编制指数，库内无历史成分名单 → 不列代表股（不编造）',
  NO_SECURITY_MAPPING: '当前研究主题尚未建立标的映射',
  HYPOTHESIS_NO_SECURITY_LINK: '专项假设未接入个股',
};

interface PriceDoc {
  artifact: string;
  index: { code: string; name: string; published_from: string; published_from_source: string };
  source: { rows: number; first_date: string; last_date: string };
  rows_before_publish: number;
  segments: { status: string; from: string | null; to: string | null;
              rows: number; backfilled: boolean | null; note: string }[];
  overlap_check: { local_first: string; local_last: string; matched_trading_days: number;
                   exact_close_matches: number; median_abs_close_diff: number;
                   daily_return_correlation: number; conclusion: string };
  cross_check_summary: { baskets_checked: number; pearson_range: number[];
                         median_abs_diff_pp_max: number; listed_1y_diff_pp_max: number;
                         conclusion: string } | null;
  license: { state: string; program_verified: boolean;
             operator_attestation: { basis: string } | null };
  limits: string[];
}

/** 历史行情校正（官方基准并列 + 真实个股交叉校验）—— 折叠时才按需加载 */
function PriceCalibration() {
  const [state, setState] = useState<'IDLE' | 'LOADING' | 'LOADED' | 'ERROR'>('IDLE');
  const [d, setD] = useState<PriceDoc | null>(null);
  async function onToggle(e: React.SyntheticEvent<HTMLDetailsElement>) {
    if (!e.currentTarget.open || state !== 'IDLE') return;
    setState('LOADING');
    try {
      const m = await import('@current/benchmark_parallel_v0_1.json');
      setD((m as { default?: PriceDoc }).default ?? (m as unknown as PriceDoc));
      setState('LOADED');
    } catch {
      setState('ERROR');
    }
  }
  return (
    <details className="fb-rule" data-price-calibration="1"
             data-price-state={state} onToggle={onToggle}>
      <summary>查看历史行情校正结论（按需加载）</summary>
      {state === 'LOADING' && <p>校正数据加载中…</p>}
      {state === 'ERROR' && <p>加载失败；可收起后重新展开重试。</p>}
      {state === 'LOADED' && d && (
        <>
          <p><strong>官方基准并列</strong>：中证 <code>{d.index.code}</code> {d.index.name}，
             发布日 <code>{d.index.published_from}</code>（{d.index.published_from_source}）。
             官方序列 <strong>{d.source.rows}</strong> 行（{d.source.first_date} → {d.source.last_date}）。</p>
          <ul>
            {d.segments.map((s) => (
              <li key={s.status} data-segment={s.status}>
                <code>{s.status}</code> · {s.from} → {s.to} · {s.rows} 行 ·
                backfilled={String(s.backfilled)} — {s.note}
              </li>
            ))}
          </ul>
          <p><strong>与库内 CSI300 对照</strong>：重叠 {d.overlap_check.matched_trading_days} 个交易日，
             0.01 容差内一致 {d.overlap_check.exact_close_matches} 日，
             中位差 {d.overlap_check.median_abs_close_diff}（小数位精度），
             日收益相关 {d.overlap_check.daily_return_correlation}。
             {d.overlap_check.conclusion}</p>
          {d.cross_check_summary && (
            <p><strong>真实个股交叉校验</strong>：{d.cross_check_summary.baskets_checked} 个自建概念篮子，
               与真实 A 股个股日收益相关 {d.cross_check_summary.pearson_range.join('–')}，
               中位差上限 {d.cross_check_summary.median_abs_diff_pp_max} pp，
               「已上市满 1 年」过滤后差异上限 {d.cross_check_summary.listed_1y_diff_pp_max} pp。
               {d.cross_check_summary.conclusion}</p>
          )}
          <p><strong>授权</strong>：state <code>{d.license.state}</code> ·
             program_verified <code>{String(d.license.program_verified)}</code> ·
             依据为操作人员提交、程序未独立核验。</p>
          <ul>{d.limits.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </>
      )}
    </details>
  );
}

/** 单条完整卡片（精选区与全量区共用，字段一致） */
function FrontierRow({ x, rank, rankReason, onRecord }: {
  x: FrontierItem; rank?: number; rankReason?: string;
  onRecord: (title: string, id: string) => void;
}) {
  const h = (x.statistical_reason ?? {}) as Record<string, unknown>;
  const stocks = x.representative_stocks ?? [];
  return (
    <li className="fb-row" data-frontier-row={x.id} data-group={x.group}
        data-track="STATISTICAL" data-attention={x.attention_label}
        data-order={x.order} data-rank={rank ?? ''}>
      <div className="fb-r1">
        {rank ? <span className="fb-rank">#{rank}</span> : null}
        <span className={`fb-grp g-${x.group.toLowerCase()}`}>{x.group}</span>
        <span className="fb-att">{x.attention_label}</span>
        <span className="fb-pos">{POS_LABEL[x.time_position ?? ''] ?? x.time_position}</span>
        <span className="fb-win">{x.window_hint}</span>
      </div>
      {rankReason && (
        <p className="fb-rankreason" data-rank-reason="1">
          <strong>为什么排这里</strong>：{rankReason}
        </p>
      )}
      <h3 className="fb-title">{x.title}</h3>
      <p className="fb-sub">{x.subtitle} · {x.why_now ?? '—'}</p>

      <div className="fb-reasons">
        <div className="fb-reason" data-reason="STATISTICAL">
          <span className="fb-reason-tag">统计理由（季度轨）</span>
          {x.statistical_reason ? (
            <p>
              <strong>历史跑赢 {String(h.hit_years ?? '—')}/{String(h.n_years ?? '—')} 年</strong>
              <span className="fb-def" title={String(h.hit_rate_definition ?? '')}>（口径？）</span> ·
              历史中位超额 {num(h.median_excess_pct)} pp ·
              样本外 {String(h.oos_status ?? '—')}（{String(h.oos_tests ?? 0)} 次） ·
              时点资格 {String(h.pit_eligible_years ?? '—')} 年
            </p>
          ) : <p>本条为专项假设 / 当前对象，无板块月度统计。</p>}
          <p className="fb-caveat">历史统计，未校准，不预测未来涨跌；只作行情附注，不参与研究增量验收。</p>
        </div>
        <div className="fb-reason" data-reason="MECHANISM">
          <span className="fb-reason-tag">机制理由（周更轨）</span>
          {x.mechanism_reason ? (
            <p>
              <a href={x.mechanism_reason.url} target="_blank" rel="noreferrer noopener">
                {x.mechanism_reason.title}
              </a>
              （{x.mechanism_reason.event_date} · 序列 {x.mechanism_reason.board_series} 精确匹配）
            </p>
          ) : (
            <p>本期机制轨<strong>无可核关联</strong> —— 不给统计卡硬贴理由。</p>
          )}
          <p className="fb-caveat">关联是序列匹配，不证明因果；机制轨整体见下方独立信息流。</p>
        </div>
      </div>

      {stocks.length > 0 ? (
        <p className="fb-stocks" data-stocks={x.representative_stocks_total}>
          <strong>个股参照</strong>（当前概念成分 + 基准日历对齐，<strong>不是历史成分</strong>）：
          {stocks.map((s) => (
            <span key={s.series_id}> {s.name ?? s.series_id}
              （历史中位超额 {num(s.median_excess_pct)} pp / {String(s.years ?? '—')} 年）·</span>
          ))}
          {(x.representative_stocks_total ?? 0) > stocks.length
            ? ` …另 ${(x.representative_stocks_total ?? 0) - stocks.length} 只见产物` : ''}
        </p>
      ) : (
        <p className="fb-stockgap" data-stock-gap={x.stock_gap_reason ?? 'NONE'}>
          <strong>未列个股</strong>：{STOCK_GAP_LABEL[x.stock_gap_reason ?? ''] ?? '本条无个股参照'}
        </p>
      )}

      <ul className="fb-meta">
        {x.trigger_type && <li>触发类型：<code>{x.trigger_type}</code></li>}
        {x.watch_next && <li>接下来看：<RichText text={x.watch_next} /></li>}
        {x.invalidate_if && <li>失效条件：<RichText text={x.invalidate_if} /></li>}
        {x.gap && <li>缺口：<RichText text={x.gap} /></li>}
        <li>出处：<code>{String((x.evidence_ref ?? {}).artifact ?? '—')}</code></li>
      </ul>
      <button type="button" className="wb-btn" data-record-from={x.id}
              onClick={() => onRecord(x.title, x.id)}>
        记下我此刻的判断 →
      </button>
    </li>
  );
}

export function FrontierView({ doc, cal, onRecord }: {
  doc: FrontierDoc; cal: EventCalendar; onRecord: (title: string, id: string) => void;
}) {
  const [group, setGroup] = useState('ALL');
  const [position, setPosition] = useState('ALL');
  const [keyword, setKeyword] = useState('');
  const [showAll, setShowAll] = useState(false);

  const rows = useMemo(() => doc.items.filter((x) => {
    if (group !== 'ALL' && x.group !== group) return false;
    if (position !== 'ALL' && x.time_position !== position) return false;
    if (keyword.trim()) {
      const k = keyword.trim();
      const hay = [x.title, x.subtitle, x.why_now, x.watch_next, x.gap]
        .filter(Boolean).join(' ');
      if (!hay.includes(k)) return false;
    }
    return true;
  }), [doc.items, group, position, keyword]);
  // ★★ v0.78：默认只显示按证据强度规则选出的 6 条；固定区不参与精选、不占名额。
  const byId = useMemo(() => new Map(doc.items.map((x) => [x.id, x])), [doc.items]);
  const topIds = useMemo(() => new Set(doc.top6.map((t) => t.id)), [doc.top6]);
  const fixedIds = useMemo(() => new Set([
    ...doc.fixed_sections.current_objects, ...doc.fixed_sections.special_hypotheses,
  ]), [doc.fixed_sections]);
  const topRows = doc.top6
    .map((t) => ({ t, x: byId.get(t.id) }))
    .filter((p): p is { t: typeof p.t; x: FrontierItem } => Boolean(p.x));
  const restTotal = doc.items.length - topIds.size - fixedIds.size;
  const restRows = showAll
    ? rows.filter((x) => !topIds.has(x.id) && !fixedIds.has(x.id))
    : [];
  const fixedRows = (ids: string[]) => ids.map((id) => byId.get(id)).filter(
    (x): x is FrontierItem => Boolean(x));
  const positions = [...new Set(doc.items.map((x) => x.time_position ?? ''))].filter(Boolean).sort();
  // ★ 关键词同时过滤机制轨事件（否则「医用耗材」这类只在政策事件里出现的词查不到）
  const feedRows = useMemo(() => {
    const k = keyword.trim();
    if (!k) return doc.mechanism_feed;
    return doc.mechanism_feed.filter((e) =>
      [e.title, e.publisher, (e.theme_tags ?? []).join(' ')].filter(Boolean).join(' ').includes(k));
  }, [doc.mechanism_feed, keyword]);

  return (
    <main className="wb-main fb" data-frontier-view="1">
      {/* ── 双轨状态：各自 as_of，不混读 ── */}
      <section className="fb-tracks" data-tracks="1">
        <div className="fb-track fb-stat" data-track="STATISTICAL">
          <span className="fb-track-tag">统计轨 · 季度更新</span>
          <strong>历史重复与样本外检验</strong>
          <p>as_of <code>{doc.tracks.statistical.as_of}</code> · 来源 <code>{doc.tracks.statistical.source}</code></p>
          <p className="fb-track-note">{doc.tracks.statistical.note}</p>
        </div>
        <div className="fb-track fb-mech" data-track="MECHANISM">
          <span className="fb-track-tag">机制轨 · 每周更新</span>
          <strong>本周新增可核事件 + 已知日程</strong>
          <p>as_of <code>{doc.tracks.mechanism.as_of}</code> · 本期窗口{' '}
             <code>{doc.tracks.mechanism.feed_window[0]}</code> → <code>{doc.tracks.mechanism.feed_window[1]}</code></p>
          <p className="fb-track-note">{doc.tracks.mechanism.note}</p>
        </div>
      </section>

      <p className="fb-caliber" data-frontier-caliber="1">
        <strong>系统主动推出的前置观察清单</strong>：默认按 <strong>G1→G4 研究浏览顺序</strong>
        （产物已有分组，<strong>无分数、不是收益排序</strong>）排列；
        <strong>「值得关注 / 可斟酌的决策点」= 前置观察窗口 / 研究起点</strong>，
        <strong>不是买卖点</strong>，具体的买卖决策由你自行做出。
        两轨理由分别标注、<strong>不做因果拼接</strong>；内部评估打分只在单独的评估视图。
      </p>

      {/* ── 一、精选 Top 6（默认主入口） ── */}
      <section className="fb-section" data-frontier-section="top6">
        <h2>一、接下来值得关注 · 精选 {doc.top6.length} 条</h2>
        <p className="fb-hint">
          只显示按<strong>证据强度规则</strong>选出的 {doc.top6.length} 条：
          {doc.selection_rule.hard_gate}。排序键：{doc.selection_rule.sort_keys.slice(0, 4).join(' → ')}。
          <strong>不设同月配额</strong>（{doc.selection_rule.month_quota_note}）。
          统计理由来自历史重复与样本外检验，<strong>未校准、不预测未来涨跌</strong>；
          行情超额只作<strong>行情附注</strong>，不参与验收。窗口只有<strong>月份级</strong>。
        </p>
        <details className="fb-rule" data-selection-rule="1">
          <summary>查看完整排序规则与命中率定义</summary>
          <p><strong>硬门槛</strong>：{doc.selection_rule.hard_gate}</p>
          <ul>{doc.selection_rule.sort_keys.map((k) => <li key={k}>{k}</li>)}</ul>
          <p><strong>命中率定义</strong>：{doc.hit_rate_definition}</p>
          <p><strong>个股参照</strong>：来自当前概念成分 + 基准日历对齐（不是历史成分）；
             行业板块无历史成分名单，如实标注不列代表股。</p>
          <p>{doc.selection_rule.note}</p>
        </details>
        <ol className="fb-list" data-frontier-list="top6" data-top6={doc.top6.length}>
          {topRows.map(({ t, x }) => (
            <FrontierRow key={x.id} x={x} rank={t.rank} rankReason={t.rank_reason}
                         onRecord={onRecord} />
          ))}
        </ol>
        <p className="fb-count" data-frontier-count={rows.length} data-rest-total={restTotal}>
          全部 {doc.items.length} 条 = 精选 {doc.top6.length} + 固定区 {fixedIds.size} + 其余 {restTotal}；
          当前筛选命中 <strong>{rows.length}</strong> 条
        </p>
        {!showAll ? (
          <button type="button" className="wb-btn primary" data-show-all="1"
                  onClick={() => setShowAll(true)}>
            查看全部（其余 {restTotal} 条，可筛选）
          </button>
        ) : (
          <div className="fb-rest" data-rest="1">
            <h3>其余记录（{restRows.length} / {restTotal} 条）</h3>
            <div className="fb-filters">
              <label>分组
                <select value={group} onChange={(e) => setGroup(e.target.value)} data-filter="group">
                  <option value="ALL">全部（G1→G4）</option>
                  {doc.group_rule.order.map((g) => (
                    <option key={g} value={g}>{g} · {GROUP_LABEL[g] ?? g}</option>
                  ))}
                </select>
              </label>
              <label>时间位置
                <select value={position} onChange={(e) => setPosition(e.target.value)} data-filter="position">
                  <option value="ALL">全部</option>
                  {positions.map((p) => <option key={p} value={p}>{POS_LABEL[p] ?? p}</option>)}
                </select>
              </label>
              <label>关键词（标题 / 理由 / 接下来看）
                <input value={keyword} onChange={(e) => setKeyword(e.target.value)}
                       placeholder="例如：光伏、医用耗材、证券" data-filter="keyword" />
              </label>
            </div>
            <ol className="fb-list" data-frontier-list="rest">
              {restRows.map((x) => (
                <FrontierRow key={x.id} x={x} onRecord={onRecord} />
              ))}
            </ol>
          </div>
        )}
      </section>

      {/* ── 二、固定区：当前研究主题 / 专项假设（不占精选名额） ── */}
      <section className="fb-section" data-frontier-section="fixed">
        <h2>二、当前研究主题与专项假设（{fixedIds.size} 条，固定区）</h2>
        <p className="fb-hint">
          这些对象在证据强度排序里排在末尾（无板块月度统计），
          但属于人工设定的研究对象，<strong>不与精选 6 条竞争名额</strong>，固定展示。
        </p>
        {([
          ['当前研究主题', doc.fixed_sections.current_objects],
          ['专项假设', doc.fixed_sections.special_hypotheses],
        ] as [string, string[]][]).map(([label, ids]) => (
          <div key={label} className="fb-fixed-group">
            <h3>{label}（{ids.length}）</h3>
            <ul className="fb-fixed">
              {fixedRows(ids).map((x) => (
                <li key={x.id} data-fixed-row={x.id}>
                  <button type="button" className="wb-linkbtn"
                          onClick={() => onRecord(x.title, x.id)}>{x.title}</button>
                  <span className="fb-date">{POS_LABEL[x.time_position ?? ''] ?? x.time_position}</span>
                  {x.why_now && <span className="fb-sub2">{x.why_now}</span>}
                  {x.gap && <span className="fb-sub2">缺口：{x.gap}</span>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* ── 二、机制轨独立信息流 ── */}
      <section className="fb-section" data-frontier-section="mechanism">
        <h2>三、近 7 日可核事件（{feedRows.length} / {doc.mechanism_feed.length} 条）</h2>
        <p className="fb-hint">
          动态窗口 = 雷达最新事件日往前 7 天（本期 {doc.tracks.mechanism.feed_window[0]} →{' '}
          {doc.tracks.mechanism.feed_window[1]}），不是自然周，也不等于「本周新增」。
          标题 / 日期 / URL 是<strong>已发布文件的事实</strong>；与板块的关联是关键词匹配，
          <strong>不证明因果</strong>。机制轨按周更新，统计轨按季度更新，两者 as_of 独立。
          <strong>上方关键词同时筛选这里</strong>——政策事件里出现而统计卡标题没有的词，可在此查到。
        </p>
        <ol className="fb-feed" data-mechanism-feed={doc.mechanism_feed.length}
            data-mechanism-shown={feedRows.length}>
          {feedRows.map((e) => (
            <li key={e.event_id} data-feed={e.event_id}>
              <span className="fb-date">{e.date}</span>
              <a href={e.url} target="_blank" rel="noreferrer noopener">{e.title}</a>
              <span className="fb-src">{e.publisher}</span>
              {e.doc_class && <span className="fb-dc">{e.doc_class}</span>}
              {e.theme_tags.length > 0 && <span className="fb-tags">{e.theme_tags.join(' · ')}</span>}
            </li>
          ))}
        </ol>
        {feedRows.length === 0 && (
          <p className="wb-empty" data-feed-empty="1">
            当前关键词在这 7 日窗口内<strong>未发现</strong>可核事件 —— 这是采集覆盖缺口，
            <strong>不代表</strong>现实中没发生。
          </p>
        )}
      </section>

      {/* ── 三、已知日程与生肖试点 ── */}
      <section className="fb-section" data-frontier-section="calendar">
        <h2>四、已知日程 / 前置观察窗口（{cal.entries.length} 条）</h2>
        <p className="fb-hint">{cal.scope_note}</p>
        <ol className="fb-cal" data-calendar-entries={cal.entries.length}>
          {cal.entries.map((e, i) => (
            <li key={`${e.date}-${e.kind}-${i}`} data-cal-kind={e.kind}>
              <span className="fb-date">{e.date}</span>
              <span>{e.kind === 'LUNAR_NEW_YEAR'
                ? `农历新年（${e.year} ${e.animal}年）`
                : e.label}</span>
              <span className="fb-fact">{e.fact_vs_assumption.startsWith('FACT') ? '事实' : '人工设定的观察起点'}</span>
            </li>
          ))}
        </ol>

        {cal.hypotheses.map((h) => (
          <div key={h.pattern_id} className="fb-hypo" data-calendar-hypothesis={h.pattern_id}>
            <h3>{h.title} <span className="fb-hypo-tag">{h.family} · 行为假说，不是题材</span></h3>
            <p>既有产物状态 <code>{h.status_in_existing_artifact}</code>。{h.note}</p>
            <ul>
              {h.mapping_layers.map((l) => (
                <li key={l.layer} data-layer={l.layer} data-layer-status={l.status}>
                  <strong>{l.layer}</strong>：{l.rule}
                  {(l.examples ?? []).length > 0 && <> · 例：{(l.examples ?? []).join(' / ')}</>}
                  {' '}<em>{l.status === 'UNVERIFIED_ASSUMPTION'
                    ? '（人工声明草案，未核验；不进统计、不参与排序、不构成篮子）'
                    : '（现有假设仅覆盖这一层）'}</em>
                </li>
              ))}
            </ul>
            <h4>已核实的缺口（不得绕过）</h4>
            <ul className="fb-gaps">
              {cal.known_gaps.map((g) => (
                <li key={g.id} data-gap={g.id}><strong>{g.id}</strong>：{g.detail}</li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* ── 五、历史行情校正（真实 A 股 / 官方基准并列） ── */}
      <section className="fb-section" data-frontier-section="calibration">
        <h2>五、历史行情校正</h2>
        <p className="fb-hint">
          统计轨原本建立在「同花顺编制指数 / 当前成分等权自建篮子 / raw 未复权 / 新浪 CSI300」之上。
          这里给出用<strong>真实 A 股个股</strong>与<strong>中证官方基准</strong>做的独立复核，
          <strong>并列展示、不合并、不替换</strong>，也不改任何历史统计产物。
        </p>
        <PriceCalibration />
      </section>

      <p className="fb-foot" data-frontier-limits="1">
        {doc.limits.map((t, i) => <span key={i}><RichText text={t} />{' '}</span>)}
      </p>
    </main>
  );
}
