/**
 * 自动发现的新题材线索（v0.69 · 产物 `new_theme_radar_v0_4`）。
 *
 * ## 两个区域，职责分开（v0.68 修复）
 *
 * - **一、当前候选事件**：列出**全部** `CANDIDATE` 事件（按日期倒序，**不按收益率排序**）。
 *   原实现只渲染「最近 12 条」，导致较早的候选（如 2026-09-24 成品油）在页面上**根本找不到**。
 * - **二、最近事件**：仍只给最近 12 条，但**排除**已在上方候选区出现的条目（避免重复展示）。
 *
 * ## 计数语义（v0.68）
 *
 * `CANDIDATE` 计数是**事件条数**，不是「独立新题材数」：同一政策在不同日期多次发布时，
 * 每次事件分别计数。没有可靠的主题唯一标识 → **不输出题材数**，也不靠关键词相同就合并。
 *
 * ## 逐板块（v0.68）
 *
 * 每个板块各自给窗口 / 绝对收益 / 相对超额 / **各自**的「绝对 vs 相对」说明；
 * 不再由第一条已观察板块生成一个可能与其他板块矛盾的整体结论。
 *
 * ## 红线
 *
 * 只展示事实 + 核验状态；不含打分 / 概率 / 收益排序 / 交易信号；覆盖范围就地写明。
 */
import raw from '@current/new_theme_radar_v0_4.json';
import { RichText } from '../RichText';

interface ThemeLink {
  keyword: string; matched_in: 'TITLE' | 'QUOTE';
  board_series: string; board_name: string;
  relation: 'DIRECT' | 'PROXY'; rationale: string;
}
interface MarketRow {
  board_series: string; board_name?: string; relation?: string;
  as_of?: string | null; window?: [string, string] | null;
  board_ret_pct?: number | null; bench_ret_pct?: number | null; excess_pp?: number | null;
  observation_trading_days?: number | null; breadth?: number | null;
  drift?: { window: [string, string]; excess_pp: number; note?: string } | null;
  assessment?: { relative_positive: boolean; absolute_positive: boolean; note: string } | null;
  status: string; gaps?: string[];
}
interface Evidence {
  kind: 'BODY_TEXT' | 'ATTACHMENT_ONLY' | 'NONE';
  quote?: string | null; quote_sha256_16?: string | null;
  attachments?: { name: string; url: string }[];
  published?: { date?: string | null; time?: string | null } | null;
  note?: string | null;
}
interface Nature { kind: string; basis: string; note: string;
  repeat_group?: string; repeat_count?: number; repeat_note?: string }
interface RadarEvent {
  event_id: string; title: string; event_date: string; doc_type?: string;
  nature?: Nature | null;
  research_directions?: string[];
  first_seen: string; last_seen?: string; seen_count?: number;
  presence?: 'IN_LATEST_LIST' | 'HISTORICAL_ONLY';
  source: { id?: string; name: string; publisher: string; url: string; category?: string };
  time?: { basis_day?: string | null; observe_from?: string | null; reaction_basis?: string;
    event_date_source?: string; published_date?: string | null; published_time?: string | null;
    note?: string };
  evidence?: Evidence | null;
  theme_links: ThemeLink[];
  rejected_links?: { keyword: string; doc_type?: string; reason: string }[];
  markets?: MarketRow[];
  review?: { verdict: string; note: string } | null;
  security_mapping?: { status: string; reason?: string } | null;
  status: string;
  gaps: string[];
}
interface Doc {
  as_of: string; generated_at: string; artifact_version?: string;
  coverage: { publisher?: string; sources?: { id: string; name: string; category?: string }[];
    date_range?: [string, string] | null; events: number;
    pages_fetched?: { source: string; url: string; items: number }[];
    failures?: { source: string; url: string; reason: string }[];
    historical_only?: number;
    limits?: string[] };
  rules?: { reaction_trading_days?: number; candidate_meaning?: string; count_semantics?: string;
    time_rule?: string; not_scored?: string; nature_rule?: string; research_direction_rule?: string };
  nature_legend?: Record<string, string>;
  research_directions?: { direction: string; series: string[] }[];
  summary: { events: number; by_status: Record<string, number>; candidates: number;
    candidates_are?: string; by_presence?: Record<string, number>; review_verdicts?: Record<string, number>;
    by_nature?: Record<string, number>; by_direction?: Record<string, number>;
    routine_repeat_groups?: Record<string, number> };
  status_legend: Record<string, string>;
  events: RadarEvent[];
}
const doc = raw as unknown as Doc;

const STATUS_LABEL: Record<string, string> = {
  CANDIDATE: '候选线索（相对为正）',
  WATCH: '仅留档',
  PENDING_MARKET: '窗口不足',
  INSUFFICIENT: '无法核验',
  NO_THEME_LINK: '未建立关联',
};
const EVIDENCE_LABEL: Record<string, string> = {
  BODY_TEXT: '正文片段',
  ATTACHMENT_ONLY: '正文在附件内（未解析）',
  NONE: '无正文',
};
const NATURE_LABEL: Record<string, string> = {
  ROUTINE_RECURRING: '常规重复事件',
  NEW_CATALYST: '新出现的产业催化',
  BACKGROUND: '背景信息',
  UNCLASSIFIED: '性质未分类',
};
const DATE_SOURCE_LABEL: Record<string, string> = {
  LIST_PAGE: '列表页标注日',
  URL_PATH: '文章路径日期',
};

const REVIEW_LABEL: Record<string, string> = {
  IRRELEVANT: '与产业无关',
  INCIDENTAL_MENTION: '背景性提及',
  NO_SERIES_AVAILABLE: '主题相关但无对应序列',
  REVIEWED_NO_KEYWORD: '已复核未命中',
  MAPPED_AFTER_REVIEW: '本轮已补关联',
};

/** ★ 关联性质标签：PROXY 必须显式说明「代理板块，非主题本身」（导出以便单测） */
export const relationLabel = (relation?: string): string =>
  relation === 'PROXY' ? '代理板块，非主题本身' : '直接';

const num = (v: number | null | undefined, suffix = '', digits = 2) =>
  typeof v === 'number' && Number.isFinite(v)
    ? `${v > 0 ? '+' : ''}${v.toFixed(digits)}${suffix}` : '—';

const RECENT_LIMIT = 12;

/** 单条事件卡片（候选区与最近区共用同一渲染，字段一致） */
function EventRow({ e }: { e: RadarEvent }) {
  const ev = e.evidence ?? { kind: 'NONE' as const };
  const ms = e.markets ?? [];
  return (
    <li className="ntr-row" data-event={e.event_id}
        data-status={e.status} data-presence={e.presence ?? 'IN_LATEST_LIST'}>
      <div className="ntr-row1">
        <span className="ntr-date">{e.event_date}</span>
        <a href={e.source.url} target="_blank" rel="noreferrer noopener" className="ntr-title">
          {e.title}
        </a>
        <span className={`ntr-st st-${e.status.toLowerCase()}`}>{STATUS_LABEL[e.status] ?? e.status}</span>
        {/* ★ 事件性质与「状态」是两件事：状态=市场相对表现；性质=事件本身是否新催化 */}
        {e.nature ? (
          <span className={`ntr-nat nat-${e.nature.kind.toLowerCase()}`} data-nature={e.nature.kind}
                title={e.nature.basis}>
            {NATURE_LABEL[e.nature.kind] ?? e.nature.kind}
            {e.nature.kind === 'ROUTINE_RECURRING' && e.nature.repeat_count
              ? `（同机制第 ${e.nature.repeat_count} 条记录）` : ''}
          </span>
        ) : null}
        {e.presence === 'HISTORICAL_ONLY' && (
          <span className="ntr-hist" data-historical-only="1">历史保留（本次列表未见）</span>
        )}
      </div>

      <div className="ntr-row2">
        {(e.research_directions ?? []).map((d) => (
          <span key={d} className="ntr-dir" data-direction={d}>研究方向：{d}</span>
        ))}
        {e.theme_links.length > 0 ? e.theme_links.map((l, i) => (
          <span key={i} className="ntr-link" data-relation={l.relation}>
            关联 <strong>{l.board_name}</strong>（{l.board_series}）· 命中「{l.keyword}」于
            {l.matched_in === 'TITLE' ? '标题' : '原文'} · {l.relation === 'PROXY' ? '代理' : '直接'}
          </span>
        )) : (
          <span className="ntr-link ntr-none">
            未命中显式关键词表 → 不建立板块关联
            {e.review ? <>（复核结论：<strong>{REVIEW_LABEL[e.review.verdict] ?? e.review.verdict}</strong>）</> : null}
          </span>
        )}
      </div>

      {/* ★ 逐板块：每个板块各自的窗口、收益与「绝对 vs 相对」说明 */}
      {ms.length > 0 && (
        <ul className="ntr-markets" data-markets={ms.length}>
          {ms.map((m) => (
            <li key={m.board_series} data-market-board={m.board_series} data-market-status={m.status}>
              <strong>{m.board_name ?? m.board_series}</strong>
              {m.relation === 'PROXY' ? <span className="ntr-proxy">（{relationLabel(m.relation)}）</span> : null}
              {m.status === 'OBSERVED' ? (
                <>
                  {' '}窗口 <code>{m.window?.[0]} → {m.window?.[1]}</code>
                  （{m.observation_trading_days} 个交易日）· 板块 <strong>{num(m.board_ret_pct, '%')}</strong>
                  {' '}· 沪深300 <strong>{num(m.bench_ret_pct, '%')}</strong>
                  {' '}· 超额 <strong>{num(m.excess_pp, 'pp')}</strong>
                  {m.drift ? (
                    <span className="ntr-drift">
                      {' '}· 事件至今（背景，不参与判定）超额 {num(m.drift.excess_pp, 'pp')}
                    </span>
                  ) : null}
                  {m.assessment ? (
                    <span className="ntr-assess" data-assess={m.assessment.relative_positive ? 'REL_POS' : 'REL_NEG'}>
                      {' '}· <RichText text={m.assessment.note} />
                    </span>
                  ) : null}
                </>
              ) : (
                <> 行情不可核验（{m.gaps?.[0] ?? '原因未记录'}）</>
              )}
            </li>
          ))}
        </ul>
      )}

      {e.review ? <p className="ntr-review" data-review={e.review.verdict}><RichText text={e.review.note} /></p> : null}

      {e.gaps.length > 0 && (
        <ul className="ntr-gaps" data-gaps={e.gaps.length}>
          {e.gaps.map((g, i) => <li key={i}><RichText text={g} /></li>)}
        </ul>
      )}

      <details className="ntr-evi">
        <summary>
          原文与来源 · {EVIDENCE_LABEL[ev.kind] ?? ev.kind}
          {e.time?.published_date ? ` · 文章页发布时间 ${e.time.published_date}` : ''}
          {e.time?.published_time ? ` ${e.time.published_time}` : ''}
        </summary>
        {ev.quote ? <p><RichText text={ev.quote} /></p> : null}
        {ev.note ? <p className="ntr-note"><RichText text={ev.note} /></p> : null}
        {(ev.attachments ?? []).length > 0 && (
          <p className="ntr-src">
            附件：
            {(ev.attachments ?? []).map((x, i) => (
              <span key={i}><a href={x.url} target="_blank" rel="noreferrer noopener">{x.name}</a>{' '}</span>
            ))}
          </p>
        )}
        {e.time?.basis_day ? (
          <p className="ntr-note">
            时点口径：基准日 <code>{e.time.basis_day}</code> · 观察起点 <code>{e.time.observe_from}</code>
            {e.time.event_date_source
              ? <> · 事件日期来源 {DATE_SOURCE_LABEL[e.time.event_date_source] ?? e.time.event_date_source}</>
              : null}
            {' '}· <RichText text={e.time.note ?? ''} />
          </p>
        ) : null}
        {e.nature ? (
          <p className="ntr-note" data-nature-basis={e.nature.kind}>
            性质判据：<RichText text={e.nature.basis} /> · <RichText text={e.nature.note} />
            {e.nature.repeat_note ? <> · <RichText text={e.nature.repeat_note} /></> : null}
          </p>
        ) : null}
        <p className="ntr-src">
          来源：{e.source.name} · <a href={e.source.url} target="_blank" rel="noreferrer noopener">
            {e.source.url}
          </a>
          {ev.quote_sha256_16 ? <> · 原文摘要 <code>{ev.quote_sha256_16}</code></> : null}
        </p>
      </details>
    </li>
  );
}

export function NewThemeRadarSection() {
  const c = doc.coverage;
  const srcNames = (c.sources ?? []).map((s) => s.name).join(' / ') || c.publisher || '—';
  const cats = [...new Set((c.sources ?? []).map((s) => s.category).filter(Boolean))].join(' / ');

  // ★★ v0.68：候选事件**全部**展示（不截断、不按收益排序）
  const candidates = doc.events.filter((e) => e.status === 'CANDIDATE');
  const candIds = new Set(candidates.map((e) => e.event_id));
  // ★★ v0.69：与当前研究方向相关的事件**全部**展示（同样不截断、不按收益排序）
  const dirEvents = doc.events.filter(
    (e) => !candIds.has(e.event_id) && (e.research_directions ?? []).length > 0);
  const dirIds = new Set(dirEvents.map((e) => e.event_id));
  // 近期区：既不候选、也不方向相关的事件，取最近 N 条（三段互不重复）
  const recent = doc.events
    .filter((e) => !candIds.has(e.event_id) && !dirIds.has(e.event_id))
    .slice(0, RECENT_LIMIT);
  const dirGroups = (doc.research_directions ?? [])
    .map((d) => ({ ...d, events: dirEvents.filter((e) => (e.research_directions ?? []).includes(d.direction)) }))
    .filter((g) => g.events.length > 0);

  return (
    <section className="ntr" aria-label="自动发现的新题材线索" data-radar-as-of={doc.as_of}
             data-radar-events={doc.summary.events} data-radar-version={doc.artifact_version ?? ''}
             data-candidates={candidates.length}>
      <div className="ntr-head">
        <h2 className="ntr-h2">自动发现的新题材线索</h2>
        <span className="ntr-badge">第一版 · 覆盖有限</span>
        <span className="ntr-meta">
          行情截至 <code>{doc.as_of}</code> · 采集 <code>{doc.generated_at}</code>
        </span>
      </div>

      <p className="ntr-lead">
        从<strong>公开政策发布页</strong>自动采集带日期的事件 → 按<strong>显式关键词表</strong>关联行业板块 →
        用<strong>真实行情</strong>核验事件后窗口的相对基准表现。这里只给<strong>线索与核验状态</strong>：
        不含打分、概率、收益排序或交易信号；<strong>不是买卖建议</strong>，
        也不代表「题材已被确认」或「事件已产生因果效果」。
      </p>

      <p className="ntr-coverage" data-coverage="1">
        来源：<strong>{srcNames}</strong>{cats ? `（${cats}）` : ''}
        {c.date_range ? <> · 覆盖 <code>{c.date_range[0]}</code> → <code>{c.date_range[1]}</code></> : null}
        {' '}· 事件 <strong>{c.events}</strong> 条
        {c.historical_only ? `（其中历史保留 ${c.historical_only} 条）` : ''}
        {' '}· 候选<strong>事件</strong>{' '}
        <strong data-candidate-count={doc.summary.candidates}>{doc.summary.candidates}</strong> 条
        {doc.rules?.reaction_trading_days != null && (
          <> · 反应窗口 = 事件后 {doc.rules.reaction_trading_days} 个交易日</>
        )}
        {doc.summary.by_nature ? (
          <> · 性质：新催化 {doc.summary.by_nature.NEW_CATALYST ?? 0} / 常规重复{' '}
            {doc.summary.by_nature.ROUTINE_RECURRING ?? 0} / 背景 {doc.summary.by_nature.BACKGROUND ?? 0}</>
        ) : null}
      </p>

      {(c.failures ?? []).length > 0 && (
        <p className="ntr-fail" data-failures={c.failures!.length}>
          ⚠ 本次有 {c.failures!.length} 个列表页未成功抓取：
          {c.failures!.map((f, i) => <span key={i}> <code>{f.url}</code>（{f.reason}）</span>)}
          {' '}—— 因此本次覆盖<strong>不完整</strong>。
        </p>
      )}

      {/* ---------- 一、当前候选事件：全部展示 ---------- */}
      <h3 className="ntr-h3" data-cand-section="candidates">
        一、当前候选事件（{candidates.length}）
      </h3>
      <p className="ntr-note" data-count-semantics="EVENTS_NOT_THEMES">
        这里是<strong>事件条数</strong>，不是「独立新题材数」：同一政策在不同日期多次发布时，
        每次事件<strong>分别计数</strong>；系统没有可靠的主题唯一标识，因此
        <strong>不输出题材数</strong>，也不因为命中同一关键词就把两条事件合并成一条。
        {doc.rules?.count_semantics ? <RichText text={doc.rules.count_semantics} /> : null}
      </p>
      {candidates.length > 0 ? (
        <ol className="ntr-list" data-rows="candidates">
          {candidates.map((e) => <EventRow key={e.event_id} e={e} />)}
        </ol>
      ) : (
        <p className="ntr-empty" data-empty="candidates">
          当前<strong>没有</strong>满足规则的候选事件（事件后 3 个交易日内相对基准为正、且全部必要
          DIRECT 板块都可核验）。这是正常结果，<strong>不会</strong>为了填满区域而放宽规则。
        </p>
      )}

      {/* ---------- 二、与当前研究方向相关的事件：全部展示 ---------- */}
      <h3 className="ntr-h3" data-cand-section="directions">
        二、与当前研究方向相关的事件（{dirEvents.length}）
      </h3>
      <p className="ntr-note">
        只列<strong>已建立可核验序列映射</strong>的研究方向；映射表写死在产物
        <code> research_directions</code>（序列 → 方向），<strong>没有合适序列的主题不出现</strong>，
        不强行代理。这里<strong>不按收益排序</strong>，也不代表这些方向已被验证。
      </p>
      {dirGroups.length > 0 ? dirGroups.map((g) => (
        <div key={g.direction} data-direction-group={g.direction}>
          <p className="ntr-dirhead">
            <strong>{g.direction}</strong>
            <span className="ntr-note"> · 序列 {g.series.join(' / ')} · {g.events.length} 条事件</span>
          </p>
          <ol className="ntr-list" data-rows="directions">
            {g.events.map((e) => <EventRow key={e.event_id} e={e} />)}
          </ol>
        </div>
      )) : (
        <p className="ntr-empty" data-empty="directions">
          本次抓取范围内<strong>没有</strong>与已映射研究方向相关的事件。
          这是采集覆盖的缺口，<strong>不代表</strong>这些方向没有发生事情。
        </p>
      )}

      {/* ---------- 三、最近事件：只给最近 N 条，排除已展示的候选与方向事件 ---------- */}
      <h3 className="ntr-h3" data-cand-section="recent">
        三、最近事件（{recent.length}）
      </h3>
      <p className="ntr-note">
        最近 {RECENT_LIMIT} 条中<strong>既不在候选区、也不属已映射研究方向</strong>的事件
        {candIds.size + dirIds.size > 0
          ? <>（已展示的 {candIds.size} 条候选 + {dirIds.size} 条方向事件不重复列出）</> : null}。
        全部 {doc.events.length} 条（含历史保留）都在产物 <code>new_theme_radar_v0_4.json</code> 内。
      </p>
      <ol className="ntr-list" data-rows="recent">
        {recent.map((e) => <EventRow key={e.event_id} e={e} />)}
      </ol>

      {/* ★ v0.69：事件性质图例（状态=市场相对表现；性质=事件本身是否新催化，两者不可混读） */}
      <p className="ntr-legend" data-nature-legend="1">
        {Object.entries(doc.nature_legend ?? {}).map(([k, v]) => (
          <span key={k} className="ntr-lg">
            <code>{k}</code> {NATURE_LABEL[k] ?? k}：<RichText text={v} />
          </span>
        ))}
      </p>

      <p className="ntr-legend" data-status-legend="1">
        {Object.entries(doc.status_legend).map(([k, v]) => (
          <span key={k} className="ntr-lg"><code>{k}</code> <RichText text={v} /></span>
        ))}
      </p>

      <details className="ntr-limits">
        <summary>覆盖范围与已知局限（必读）</summary>
        <ul>
          {(c.limits ?? []).map((t, i) => <li key={i}><RichText text={t} /></li>)}
        </ul>
        {doc.rules?.candidate_meaning ? (
          <p className="ntr-note">状态含义：<RichText text={doc.rules.candidate_meaning} /></p>
        ) : null}
        {doc.rules?.not_scored ? <p className="ntr-note"><RichText text={doc.rules.not_scored} /></p> : null}
      </details>
    </section>
  );
}
