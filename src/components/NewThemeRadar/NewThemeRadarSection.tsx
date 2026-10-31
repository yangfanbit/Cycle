/**
 * 自动发现的新题材线索（v0.70 · 产物 `new_theme_radar_v0_5`）。
 *
 * ## 市场状态 ≠ 事件性质（v0.70 核心修正）
 *
 * `status` 是**机械的市场反应筛选**（事件后窗口内是否跑赢沪深300），`nature.kind` 是
 * **事件本身的性质**（新催化 / 常规重复 / 背景 / 未分类）。两者**正交**：
 *
 * - 候选区的标题必须写成「市场反应筛选结果」，**不能**暗示这些都属于新催化；
 * - `CANDIDATE` 的文案是「相对基准为正、待人工复核」，不是「利好」「催化已确认」；
 * - **背景类事件（会议/活动/评选）即使窗口内跑赢基准，也只作市场观察**，
 *   页面上显式标注，不得称为产业催化。
 *
 * ## 具体主题 ≠ 研究方向（v0.70）
 *
 * `theme_tags` 由**实际命中的关键词**映射而来（如「医用耗材」→ 医用耗材分类与价格）；
 * `research_directions` 只是**上层分组**（一个方向可能挂多个共享序列），
 * 用它反推具体主题会把不同主题合并。
 *
 * ## 区域划分（v0.68/v0.69）
 *
 * - **一、市场反应筛选结果**：全部 `CANDIDATE` 事件（不截断、不按收益率排序）；
 * - **二、与当前研究方向相关的事件**：全部，按上层方向分组；
 * - **三、最近事件**：最近 12 条，排除前两段已展示的。
 *
 * ## 计数语义
 *
 * `CANDIDATE` 计数是**事件条数**，不是「独立新题材数」。
 *
 * ## 红线
 *
 * 只展示事实 + 核验状态；不含打分 / 概率 / 收益排序 / 交易信号；覆盖范围就地写明。
 */
import raw from '@current/new_theme_radar_v0_5.json';
import { RichText } from '../RichText';

interface ThemeLink {
  keyword: string; matched_in: 'TITLE' | 'QUOTE'; theme_tag?: string | null;
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
  theme_tags?: string[];
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
  coverage: { publisher?: string; publishers?: string[]; sources?: { id: string; name: string; category?: string }[];
    date_range?: [string, string] | null; events: number;
    pages_fetched?: { source: string; url: string; items: number }[];
    failures?: { source: string; url: string; reason: string }[];
    historical_only?: number;
    limits?: string[] };
  rules?: { reaction_trading_days?: number; candidate_meaning?: string; count_semantics?: string;
    time_rule?: string; not_scored?: string; nature_rule?: string; research_direction_rule?: string };
  nature_legend?: Record<string, string>;
  research_directions?: { direction: string; series: string[]; scope_note?: string }[];
  summary: { events: number; by_status: Record<string, number>; candidates: number;
    candidates_are?: string; by_presence?: Record<string, number>; review_verdicts?: Record<string, number>;
    by_nature?: Record<string, number>; by_direction?: Record<string, number>;
    routine_repeat_groups?: Record<string, number> };
  status_legend: Record<string, string>;
  events: RadarEvent[];
}
const doc = raw as unknown as Doc;

const STATUS_LABEL: Record<string, string> = {
  // ★★ v0.70：只说「相对基准为正、待人工复核」—— 不得写成「利好 / 催化确认 / 建议关注」
  CANDIDATE: '相对基准为正 · 待人工复核',
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

/**
 * ★★ v0.70：**「相对为正」不等于「产业催化」** —— 当事件性质是背景信息或常规重复时，
 * 即使市场反应筛选通过，也必须显式说明这只是市场观察。导出以便单测。
 */
export function natureCaveat(kind?: string | null, status?: string): string | null {
  if (status !== 'CANDIDATE') return null;
  if (kind === 'BACKGROUND') {
    return '本条是**背景信息**（会议/活动/评选类）：窗口内跑赢基准只作**市场观察**，'
      + '**不构成产业催化**，也不说明事件与行情有因果关系。';
  }
  if (kind === 'ROUTINE_RECURRING') {
    return '本条是**按既有机制重复发布**的事件（如成品油调价）：行情表现属常规波动，'
      + '**不是新催化**，不构成新的产业线索。';
  }
  if (kind === 'UNCLASSIFIED') {
    return '本条**性质未分类**：只表示窗口内相对基准为正，**不推断**它是不是产业催化。';
  }
  return null;
}

/** 单条事件卡片（候选区与最近区共用同一渲染，字段一致） */
function EventRow({ e }: { e: RadarEvent }) {
  const ev = e.evidence ?? { kind: 'NONE' as const };
  const ms = e.markets ?? [];
  const caveat = natureCaveat(e.nature?.kind, e.status);
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
        {/* ★ v0.70：具体主题来自实际命中的关键词（不是由共享序列反推的上层方向） */}
        {(e.theme_tags ?? []).map((t) => (
          <span key={t} className="ntr-tag" data-theme-tag={t}>主题：{t}</span>
        ))}
        {(e.research_directions ?? []).map((d) => (
          <span key={d} className="ntr-dir" data-direction={d}>上层方向：{d}</span>
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

      {/* ★★ v0.70：性质与状态的**交叉**说明 —— 防止「相对为正」被读成「产业催化」 */}
      {caveat ? (
        <p className="ntr-caveat" data-nature-caveat={e.nature?.kind}>
          <RichText text={caveat} />
        </p>
      ) : null}

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
  // ★ v0.70：方向分组**不过滤 0 条** —— 未覆盖的方向要显式写「当前采集范围未发现」，
  //   否则读者会以为这些方向不存在（采集缺口 ≠ 现实没有发生）。
  const dirGroups = (doc.research_directions ?? [])
    .map((d) => ({ ...d, events: dirEvents.filter((e) => (e.research_directions ?? []).includes(d.direction)) }));

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
        ★ 每条事件同时标注<strong>市场状态</strong>（是否跑赢基准）与<strong>事件性质</strong>
        （是否新催化），两者<strong>互不替代</strong>。
      </p>

      <p className="ntr-coverage" data-coverage="1">
        {c.publishers && c.publishers.length > 0
          ? <>发布机构：<strong>{c.publishers.join(' / ')}</strong> · </>
          : null}
        来源：<strong>{srcNames}</strong>{cats ? `（${cats}）` : ''}
        {c.date_range ? <> · 覆盖 <code>{c.date_range[0]}</code> → <code>{c.date_range[1]}</code></> : null}
        {' '}· 事件 <strong>{c.events}</strong> 条
        {c.historical_only ? `（其中历史保留 ${c.historical_only} 条）` : ''}
        {' '}· 市场反应筛选通过 <strong data-candidate-count={doc.summary.candidates}>{doc.summary.candidates}</strong> 条
        {doc.rules?.reaction_trading_days != null && (
          <> · 反应窗口 = 事件后 {doc.rules.reaction_trading_days} 个交易日</>
        )}
        {doc.summary.by_nature ? (
          <> · 性质：新催化 {doc.summary.by_nature.NEW_CATALYST ?? 0} / 常规重复{' '}
            {doc.summary.by_nature.ROUTINE_RECURRING ?? 0} / 背景 {doc.summary.by_nature.BACKGROUND ?? 0}{' '}
            / 未分类 {doc.summary.by_nature.UNCLASSIFIED ?? 0}</>
        ) : null}
      </p>

      {(c.failures ?? []).length > 0 && (
        <p className="ntr-fail" data-failures={c.failures!.length}>
          ⚠ 本次有 {c.failures!.length} 个列表页未成功抓取：
          {c.failures!.map((f, i) => <span key={i}> <code>{f.url}</code>（{f.reason}）</span>)}
          {' '}—— 因此本次覆盖<strong>不完整</strong>。
        </p>
      )}

      {/* ---------- 一、市场反应筛选结果：全部展示 ---------- */}
      {/* ★★ v0.70：标题不得暗示「这些都是新催化」—— 这里筛的只是**市场相对表现** */}
      <h3 className="ntr-h3" data-cand-section="candidates">
        一、市场反应筛选结果（{candidates.length} 条事件）
      </h3>
      <p className="ntr-note" data-market-filter-note="1">
        这一区的筛选条件<strong>只有市场条件</strong>：事件后 {doc.rules?.reaction_trading_days ?? 3}{' '}
        个交易日内，<strong>全部必要 DIRECT 板块</strong>都跑赢沪深300（相对基准为正）。
        它<strong>不代表</strong>这些事件都是新催化 —— 每条的性质（新催化 / 常规重复 / 背景 / 未分类）
        单独标注在事件上；<strong>背景类与常规重复类即使行情为正，也只作市场观察</strong>。
        结果<strong>待人工复核</strong>，不含打分、概率或买卖建议。
      </p>
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
        不强行代理。★ 这里的<strong>方向是上层分组</strong>（一个方向可能挂多个共享序列），
        具体主题看每条事件上的<strong>「主题：」标签</strong>——它由实际命中的关键词映射而来，
        <strong>不由序列反推</strong>。这里<strong>不按收益排序</strong>，也不代表这些方向已被验证。
      </p>
      {dirGroups.length > 0 ? dirGroups.map((g) => (
        <div key={g.direction} data-direction-group={g.direction}
             data-direction-count={g.events.length}>
          <p className="ntr-dirhead">
            <strong>{g.direction}</strong>
            <span className="ntr-note"> · 序列 {g.series.join(' / ')} · {g.events.length} 条事件</span>
          </p>
          {/* ★ v0.70：方向的**范围说明**由产物给出（避免「海上风电方向」被读成「发现了海上风电事件」） */}
          {g.scope_note ? (
            <p className="ntr-note" data-scope-note={g.direction}><RichText text={g.scope_note} /></p>
          ) : null}
          {g.events.length > 0 ? (
            <ol className="ntr-list" data-rows="directions">
              {g.events.map((e) => <EventRow key={e.event_id} e={e} />)}
            </ol>
          ) : (
            <p className="ntr-empty" data-empty="direction">
              <strong>当前采集范围未发现</strong>该方向的事件 —— 这是<strong>采集覆盖的缺口</strong>，
              <strong>不代表</strong>现实中该方向没有发生事情。
            </p>
          )}
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
        全部 {doc.events.length} 条（含历史保留）都在产物 <code>new_theme_radar_v0_5.json</code> 内。
      </p>
      <ol className="ntr-list" data-rows="recent">
        {recent.map((e) => <EventRow key={e.event_id} e={e} />)}
      </ol>

      {/* ★ v0.70：性质图例 + **正交说明**（状态=市场相对表现；性质=事件本身是否新催化） */}
      <p className="ntr-note" data-orthogonal="1">
        <strong>「状态」与「性质」是两个独立的维度</strong>：状态回答「事件后是否跑赢沪深300」，
        性质回答「事件本身是不是新催化」。因此会出现「性质=背景信息、状态=相对为正」的组合 ——
        那只是<strong>市场观察</strong>，<strong>不是</strong>产业催化，也<strong>不是</strong>因果结论。
      </p>
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
