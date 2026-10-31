/**
 * 自动发现的新题材线索（v0.72 · 展示包 `new_theme_radar_v0_7_view`）。
 *
 * ## 本轮三件事
 *
 * **① 时点口径可解释（P0）** —— 每条事件必须能回答「为什么用/不用精确发布时间」：
 * 只有「来源时间语义 = 首次公开时间 + 有到分钟时间 + `published_date == event_date`」
 * 三条同时成立才用盘前/盘后规则；否则退回保守规则并在 `precise_time_rejected.reason`
 * 写明原因。日期冲突严重（档案/迁移）→ `time_certainty = UNCERTAIN`，**不计算数值反应**。
 *
 * **② 低信号不再主导默认视图（P1）** —— `doc_class = ADMIN_REPLY`（提案/建议答复）
 * 从最近事件区移到「低信号归档」，保留标题、URL、分类理由与统计。
 *
 * **③ 主包轻量化（P1）** —— 只 import 展示包（`display = FULL | INDEX`）；
 * 原文 / 附件 / 被拒关联在 `_evidence.json`，展开时按需动态加载。
 *
 * ## 不变的约束
 *
 * 市场状态（`status`）与事件性质（`nature.kind`）正交；`CANDIDATE` 只说「相对基准为正、
 * 待人工复核」；具体主题看「主题：」（由实际命中关键词映射），方向只是上层分组。
 */
import { useState } from 'react';
import raw from '@current/new_theme_radar_v0_7_view.json';
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
/** 时点冲突（v0.71）：普通不一致 vs 档案/迁移冲突必须分开 */
interface DateConflict {
  kind: string; published_date: string; delta_days: number | null;
  shared_by?: number; semantics?: string; note: string;
}
interface TimeInfo {
  basis_day?: string | null; observe_from?: string | null; reaction_basis?: string;
  event_date_source?: string; published_date?: string | null; published_time?: string | null;
  time_precision?: string;
  time_field_semantics?: string;
  time_certainty?: 'EXACT' | 'CONSERVATIVE' | 'UNCERTAIN';
  precise_time_rejected?: { reason: string; published_date?: string | null;
    published_time?: string | null; semantics?: string; note: string } | null;
  date_conflict?: DateConflict | null;
  note?: string;
}
interface Nature { kind: string; basis: string; note: string;
  repeat_group?: string; repeat_count?: number; repeat_note?: string }
interface RadarEvent {
  event_id: string; title: string; event_date: string; doc_type?: string;
  doc_class?: string;
  nature?: Nature | null;
  theme_tags?: string[];
  research_directions?: string[];
  display?: 'FULL' | 'INDEX';
  first_seen?: string; last_seen?: string; seen_count?: number;
  presence?: 'IN_LATEST_LIST' | 'HISTORICAL_ONLY';
  source: { id?: string; name?: string; publisher?: string; url: string; category?: string };
  time?: TimeInfo;
  evidence?: Evidence | null;
  theme_links?: ThemeLink[];
  rejected_links?: { keyword: string; doc_type?: string; reason: string }[];
  markets?: MarketRow[];
  review?: { verdict: string; note: string } | null;
  security_mapping?: { status: string; reason?: string } | null;
  status: string;
  gaps?: string[];
}
interface Doc {
  as_of: string; generated_at: string; artifact_version?: string;
  coverage: { publisher?: string; publishers?: string[]; sources?: { id: string; name: string; category?: string }[];
    date_range?: [string, string] | null; events: number;
    pages_fetched?: { source: string; url: string; items: number }[];
    failures?: { source: string; url: string; reason: string }[];
    historical_only?: number;
    by_time_certainty?: Record<string, number>;
    date_conflicts?: Record<string, { events: number; max_abs_days: number }>;
    limits?: string[] };
  rules?: { reaction_trading_days?: number; candidate_meaning?: string; count_semantics?: string;
    time_rule?: string; not_scored?: string; nature_rule?: string; research_direction_rule?: string;
    time_rules?: Record<string, string>;
    time_certainty_legend?: Record<string, string>;
    time_field_semantics_legend?: Record<string, string> };
  nature_legend?: Record<string, string>;
  doc_class_legend?: Record<string, string>;
  low_signal_doc_classes?: string[];
  research_directions?: { direction: string; series: string[]; scope_note?: string }[];
  source_artifact?: string;
  display_policy?: Record<string, string>;
  summary: { events: number; by_status: Record<string, number>; candidates: number;
    candidates_are?: string; by_presence?: Record<string, number>; review_verdicts?: Record<string, number>;
    by_nature?: Record<string, number>; by_direction?: Record<string, number>;
    by_doc_class?: Record<string, number>; low_signal_events?: number;
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
/** ★★ v0.71：时点可信度（决定能不能把「数值化反应」当事实看） */
const CERTAINTY_LABEL: Record<string, string> = {
  EXACT: '精确（收盘后/开盘前可判定）',
  CONSERVATIVE: '保守（事件日涨跌不计入）',
  UNCERTAIN: '时点不确定（不计算数值反应）',
};
/** ★★ v0.71：精确时间被拒的原因 —— 必须说清楚，不能静默退回 */
const REJECT_LABEL: Record<string, string> = {
  SEMANTICS_UNTRUSTED: '来源时间字段不是「首次公开时间」',
  DATE_MISMATCH: '文章日期 ≠ 事件日期',
  PRECISION_UNAVAILABLE: '无到分钟的发布时间',
  // ★★ v0.72：三条门槛都满足、但规则仍用不上时的原因（v0.6 有 19 条缺这块）
  INTRADAY_AMBIGUOUS: '发布时间在盘中（09:30–15:00）',
  EVENT_DATE_NON_TRADING: '发布时间在收盘后，但事件日不是交易日',
  CALENDAR_EDGE: '开盘前发布，但日历中没有更早的交易日',
};
const DOC_CLASS_LABEL: Record<string, string> = {
  ADMIN_REPLY: '行政答复',
  ACTIVITY_PROMO: '活动/宣传',
  STANDARD_PROCEDURE: '标准程序节点',
  INDUSTRY_DATA: '产业数据发布',
  POLICY_ACTION: '政策行动',
  OTHER: '未分类',
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
 * ★★ v0.71 P1：原文 / 附件 / 被拒关联在独立文件里，**展开时才加载**。
 * 只 import 一次（模块级 Promise），失败不影响主视图。
 */
interface EvDetail {
  quote?: string;
  attachments?: { name: string; url: string }[];
  rejected_links?: { keyword: string; doc_type?: string; reason: string }[];
}
type EvMap = Record<string, EvDetail>;
let evPromise: Promise<EvMap> | null = null;
/** ★★ v0.72：**不在内部吞掉错误** —— 加载失败必须能被界面区分出来 */
function loadEvidence(): Promise<EvMap> {
  if (!evPromise) {
    evPromise = import('@current/new_theme_radar_v0_7_evidence.json')
      .then((m) => ((m as { default?: EvMap }).default ?? (m as unknown as EvMap)));
    evPromise.catch(() => { evPromise = null; });   // 失败后允许重试
  }
  return evPromise;
}

/** ★★ v0.72：证据加载的四态 —— 不能凭 `quote == null` 就说「加载中」 */
type EvState = 'IDLE' | 'LOADING' | 'LOADED' | 'ERROR';

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

/**
 * ★★ v0.71 P0：时点口径的可读解释。**必须能回答「为什么用/不用精确时间」**。
 * 导出以便单测（这是本轮最核心的语义不变量）。
 */
export function timeExplain(t?: TimeInfo | null): string | null {
  if (!t) return null;
  const c = t.time_certainty;
  if (c === 'UNCERTAIN') {
    const d = t.date_conflict;
    return `时点不确定：${d?.note ?? '日期冲突严重'} —— 因此**不计算**数值化事件反应。`;
  }
  const r = t.precise_time_rejected;
  if (c === 'CONSERVATIVE' && r?.reason) {
    return `退回保守规则（${REJECT_LABEL[r.reason] ?? r.reason}）：${r.note}`;
  }
  if (c === 'EXACT') {
    return `精确时点：来源时间语义为首次公开时间，文章日期与事件日期同天，可用时分判断。`;
  }
  return null;
}

/** 单条事件卡片（候选区与最近区共用同一渲染，字段一致） */
function EventRow({ e }: { e: RadarEvent }) {
  const ev = e.evidence ?? { kind: 'NONE' as const };
  const ms = e.markets ?? [];
  const links = e.theme_links ?? [];
  const gaps = e.gaps ?? [];
  const caveat = natureCaveat(e.nature?.kind, e.status);
  const [extra, setExtra] = useState<EvDetail | null>(null);
  const [evState, setEvState] = useState<EvState>('IDLE');
  const doLoad = () => {
    setEvState('LOADING');
    loadEvidence()
      .then((m) => { setExtra(m[e.event_id] ?? null); setEvState('LOADED'); })
      .catch(() => setEvState('ERROR'));
  };
  const onToggle = (x: React.SyntheticEvent<HTMLDetailsElement>) => {
    if (!x.currentTarget.open) return;
    if (evState === 'LOADING' || evState === 'LOADED') return;
    doLoad();
  };
  const quote = extra?.quote ?? ev.quote ?? null;
  const atts = extra?.attachments ?? ev.attachments ?? [];
  return (
    <li className="ntr-row" data-event={e.event_id} data-display={e.display ?? 'FULL'}
        data-status={e.status} data-presence={e.presence ?? 'IN_LATEST_LIST'}>
      <div className="ntr-row1">
        <span className="ntr-date">{e.event_date}</span>
        <a href={e.source.url} target="_blank" rel="noreferrer noopener" className="ntr-title">
          {e.title}
        </a>
        <span className={`ntr-st st-${e.status.toLowerCase()}`}>{STATUS_LABEL[e.status] ?? e.status}</span>
        {/* ★ 事件性质与「状态」是两件事：状态=市场相对表现；性质=事件本身是否新催化 */}
        {e.nature?.kind ? (
          <span className={`ntr-nat nat-${e.nature.kind.toLowerCase()}`} data-nature={e.nature.kind}
                title={e.nature.basis}>
            {NATURE_LABEL[e.nature.kind] ?? e.nature.kind}
            {e.nature.kind === 'ROUTINE_RECURRING' && e.nature.repeat_count
              ? `（同机制第 ${e.nature.repeat_count} 条记录）` : ''}
          </span>
        ) : null}
        {/* ★★ v0.71：时点可信度必须可见 —— 不能让人把「保守规则」的数字当成精确反应 */}
        {e.time?.time_certainty ? (
          <span className={`ntr-cert cert-${e.time.time_certainty.toLowerCase()}`}
                data-certainty={e.time.time_certainty}
                title={CERTAINTY_LABEL[e.time.time_certainty]}>
            {CERTAINTY_LABEL[e.time.time_certainty] ?? e.time.time_certainty}
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
        {links.length > 0 ? links.map((l, i) => (
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

      {gaps.length > 0 && (
        <ul className="ntr-gaps" data-gaps={gaps.length}>
          {gaps.map((g, i) => <li key={i}><RichText text={g} /></li>)}
        </ul>
      )}

      <details className="ntr-evi" onToggle={onToggle}>
        <summary>
          原文与来源 · {EVIDENCE_LABEL[ev.kind] ?? ev.kind}
          {e.time?.published_date ? ` · 文章日期 ${e.time.published_date}` : ''}
          {e.time?.published_time ? ` ${e.time.published_time}` : ''}
          {e.time?.time_precision === 'MINUTE' && e.time.time_certainty !== 'EXACT'
            ? '（未用于盘前/盘后判断）' : ''}
        </summary>
        {/* ★★ v0.72：四态分开 —— 折叠未展开 / 加载中 / 已加载但无正文 / 加载失败 */}
        {quote ? <p><RichText text={quote} /></p> : null}
        {!quote && evState === 'LOADING' ? (
          <p className="ntr-note" data-evidence-state="LOADING">正在加载原文…</p>
        ) : null}
        {!quote && evState === 'ERROR' ? (
          <p className="ntr-note" data-evidence-state="ERROR">
            原文加载失败（网络或资源不可用）。
            <button type="button" className="ntr-retry" onClick={doLoad}>重试</button>
            {' '}· 原始链接仍可直接打开
          </p>
        ) : null}
        {!quote && evState === 'LOADED' ? (
          <p className="ntr-note" data-evidence-state="NO_BODY">
            已加载：该来源<strong>没有可提取的正文</strong>
            （{EVIDENCE_LABEL[ev.kind] ?? ev.kind}）→ 只有标题、原始链接与原文摘要可核。
          </p>
        ) : null}
        {ev.note ? <p className="ntr-note"><RichText text={ev.note} /></p> : null}
        {atts.length > 0 && (
          <p className="ntr-src">
            附件：
            {atts.map((x, i) => (
              <span key={i}><a href={x.url} target="_blank" rel="noreferrer noopener">{x.name}</a>{' '}</span>
            ))}
          </p>
        )}
        {/* ★★ v0.71：时点口径 —— 为什么用/不用精确时间，必须逐条可解释 */}
        {e.time?.basis_day ? (
          <p className="ntr-note" data-time-basis={e.time.reaction_basis}>
            时点口径：基准日 <code>{e.time.basis_day}</code> · 观察起点 <code>{e.time.observe_from}</code>
            {e.time.event_date_source
              ? <> · 事件日期来源 {DATE_SOURCE_LABEL[e.time.event_date_source] ?? e.time.event_date_source}</>
              : null}
            {e.time.time_field_semantics
              ? <> · 文章时间字段语义 <code>{e.time.time_field_semantics}</code></> : null}
            {' '}· <RichText text={e.time.note ?? ''} />
          </p>
        ) : null}
        {timeExplain(e.time) ? (
          <p className="ntr-note" data-time-explain={e.time?.time_certainty ?? ''}>
            <RichText text={timeExplain(e.time) ?? ''} />
          </p>
        ) : null}
        {e.time?.date_conflict ? (
          <p className="ntr-note" data-date-conflict={e.time.date_conflict.kind}>
            日期差异：事件日 <code>{e.event_date}</code> · 文章日期{' '}
            <code>{e.time.date_conflict.published_date}</code>（{e.time.date_conflict.delta_days != null
              ? `${e.time.date_conflict.delta_days > 0 ? '+' : ''}${e.time.date_conflict.delta_days} 天`
              : '天数不可解析'}）· <RichText text={e.time.date_conflict.note} />
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

  // ★★ v0.71：只渲染展示包里的 `display === FULL` 事件（INDEX 是索引行，另有归档区）
  const full = doc.events.filter((e) => (e.display ?? 'FULL') === 'FULL');
  // ★★ v0.68：候选事件**全部**展示（不截断、不按收益排序）
  const candidates = full.filter((e) => e.status === 'CANDIDATE');
  const candIds = new Set(candidates.map((e) => e.event_id));
  // ★★ v0.69：与当前研究方向相关的事件**全部**展示（同样不截断、不按收益排序）
  const dirEvents = full.filter(
    (e) => !candIds.has(e.event_id) && (e.research_directions ?? []).length > 0);
  const dirIds = new Set(dirEvents.map((e) => e.event_id));
  // 近期区：既不候选、也不方向相关的事件，取最近 N 条（三段互不重复）
  const recent = full
    .filter((e) => !candIds.has(e.event_id) && !dirIds.has(e.event_id))
    .slice(0, RECENT_LIMIT);
  // ★★ v0.71：日期冲突严重 → 不计算数值反应，但**必须在页面上显式披露**（不能静默消失）
  const uncertain = doc.events.filter((e) => e.time?.time_certainty === 'UNCERTAIN');
  // ★★ v0.71：低信号归档 —— 只隐藏展示，**不删除**：标题 / URL / 分类理由 / 统计都保留
  const lowSignal = new Set(doc.low_signal_doc_classes ?? ['ADMIN_REPLY']);
  const archived = doc.events.filter((e) => (e.display ?? 'FULL') === 'INDEX'
    && lowSignal.has(e.doc_class ?? ''));
  // ★★ v0.72：**其他事件索引** —— INDEX 里除去「行政答复归档」与「时点不确定」的其余记录。
  //   三个区域互斥：FULL 区 / 归档区 / 不确定区 / 本索引区 = 全部事件，不重不漏。
  const archivedIds = new Set(archived.map((e) => e.event_id));
  const uncertainIds = new Set(uncertain.map((e) => e.event_id));
  const indexEvents = doc.events.filter((e) => (e.display ?? 'FULL') === 'INDEX'
    && !archivedIds.has(e.event_id) && !uncertainIds.has(e.event_id));
  // ★★ v0.72：索引区的本地筛选（标题关键词 + 来源 / 类别 / 状态），只用轻量字段
  const [idxQ, setIdxQ] = useState('');
  const [idxSrc, setIdxSrc] = useState('ALL');
  const [idxClass, setIdxClass] = useState('ALL');
  const [idxStatus, setIdxStatus] = useState('ALL');
  const idxFiltered = indexEvents.filter((e) => {
    if (idxSrc !== 'ALL' && (e.source.id ?? '') !== idxSrc) return false;
    if (idxClass !== 'ALL' && (e.doc_class ?? '') !== idxClass) return false;
    if (idxStatus !== 'ALL' && e.status !== idxStatus) return false;
    const kw = idxQ.trim().toLowerCase();
    if (kw && !(e.title ?? '').toLowerCase().includes(kw)) return false;
    return true;
  });
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
        （是否新催化），两者<strong>互不替代</strong>。★ 另标注<strong>时点可信度</strong>：
        只有「来源时间语义是首次公开时间 + 有到分钟时间 + 文章日期与事件日期同天」三条同时成立，
        才用盘前/盘后规则；否则退回<strong>保守规则</strong>（事件日涨跌不计入反应），
        并在原文区写明<strong>为什么没用精确时间</strong>。
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
        {c.by_time_certainty ? (
          <> · 时点：精确 {c.by_time_certainty.EXACT ?? 0} / 保守{' '}
            {c.by_time_certainty.CONSERVATIVE ?? 0} / 不确定 {c.by_time_certainty.UNCERTAIN ?? 0}</>
        ) : null}
        {doc.summary.low_signal_events ? (
          <> · 低信号归档 {doc.summary.low_signal_events} 条（不占默认视图）</>
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
          ? <>（已展示的 {candIds.size} 条候选 + {dirIds.size} 条方向事件不重复列出）</> : null}
        {archived.length > 0
          ? <>；<strong>低信号文档（行政答复）已移出本区</strong>，见下方归档。</> : null}
        展示包只带这 {full.length} 条的完整字段，其余 {doc.events.length - full.length} 条
        以<strong>索引行</strong>保留在产物 <code>{doc.source_artifact ?? 'new_theme_radar_v0_7.json'}</code> 内。
      </p>
      <ol className="ntr-list" data-rows="recent">
        {recent.map((e) => <EventRow key={e.event_id} e={e} />)}
      </ol>

      {/* ---------- 四、时点不确定：不计算数值反应，但必须披露 ---------- */}
      {/* ★★ v0.71 P0：日期冲突严重的档案**不得伪造精确反应时点**，也不能静默消失。 */}
      {uncertain.length > 0 && (
        <details className="ntr-uncertain" data-uncertain-events={uncertain.length}>
          <summary>
            四、时点不确定（{uncertain.length} 条）—— 已停止计算数值化反应
          </summary>
          <p className="ntr-note" data-uncertain-note="1">
            这些事件的<strong>列表日期与文章元数据冲突严重</strong>（相差超过一年，
            或该文章日期被多条共享 = 网站迁移的批量赋值）→ 无法确认哪个日期才是可观察的事件日。
            因此<strong>不计算</strong>板块收益 / 沪深300 / 相对超额，
            <strong>不展示</strong>貌似精确的反应数值。原始标题、URL 与冲突说明保留在下方，可逐条核对。
          </p>
          <ul className="ntr-list ntr-archlist" data-rows="uncertain">
            {uncertain.map((e) => (
              <li key={e.event_id} className="ntr-archrow" data-event={e.event_id}
                  data-certainty="UNCERTAIN" data-conflict={e.time?.date_conflict?.kind}>
                <span className="ntr-date">{e.event_date}</span>{' '}
                <a href={e.source.url} target="_blank" rel="noreferrer noopener">{e.title}</a>
                {e.time?.date_conflict ? (
                  <span className="ntr-note">
                    {' '}· 文章日期 <code>{e.time.date_conflict.published_date}</code>
                    {e.time.date_conflict.delta_days != null
                      ? `（${e.time.date_conflict.delta_days > 0 ? '+' : ''}${e.time.date_conflict.delta_days} 天）`
                      : ''}
                    {' '}· <RichText text={e.time.date_conflict.note} />
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* ---------- 五、低信号归档：不占默认视图，但**不删除** ---------- */}
      {/* ★★ v0.71 P1：行政答复（提案/建议答复）标题只有编号，产业指向在正文 →
          默认视图隐藏，但保留标题 / URL / 分类理由 / 统计，可追溯。 */}
      {archived.length > 0 && (
        <details className="ntr-archive" data-low-signal-archive={archived.length}>
          <summary>
            五、低信号归档（{archived.length} 条）—— 默认视图已隐藏，可追溯
          </summary>
          <p className="ntr-note" data-archive-note="1">
            这些文档的<strong>标题只有行政编号</strong>（提案答复 / 建议答复），产业指向写在正文里，
            按标题无法绑定板块 → 不进入默认视图，但<strong>不删除、不丢统计</strong>：
            原始 URL、标题、分类理由都在这里，完整档案在产物内。
            <strong>不是</strong>「与产业无关」的判断 —— 只是「标题不足以支撑板块关联」。
          </p>
          <ul className="ntr-list ntr-archlist" data-rows="archive">
            {archived.map((e) => (
              <li key={e.event_id} className="ntr-archrow" data-event={e.event_id}
                  data-doc-class={e.doc_class}>
                <span className="ntr-date">{e.event_date}</span>{' '}
                <a href={e.source.url} target="_blank" rel="noreferrer noopener">{e.title}</a>
                {' '}<span className="ntr-dc" data-doc-class={e.doc_class}>
                  {DOC_CLASS_LABEL[e.doc_class ?? ''] ?? e.doc_class}
                </span>
                {e.review ? (
                  <span className="ntr-note"> · <RichText text={e.review.note} /></span>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* ---------- 六、其他事件索引：让「没进默认视图」的事件也能被查到 ---------- */}
      {/* ★★ v0.72 P1：INDEX 里除归档/不确定之外的其余记录（本轮 162 条）。
          只用展示包的轻量字段，**不加载完整档案、不加载证据文件**；三个区域互斥。 */}
      {indexEvents.length > 0 && (
        <details className="ntr-index" data-event-index={indexEvents.length}>
          <summary>
            六、其他事件索引（{indexEvents.length} 条）—— 已采集但未进入上方区域
          </summary>
          <p className="ntr-note" data-index-note="1">
            这里列的是<strong>已经采集、但未进入候选 / 方向 / 近期视图</strong>的事件
            （多为未命中当前关键词表的潜在线索）。只用轻量索引字段，<strong>不加载</strong>
            完整档案与原文；点标题可打开原始来源核对。
            {' '}区域互斥：完整展示 {full.length} 条 + 时点不确定 {uncertain.length} 条 +
            低信号归档 {archived.length} 条 + 本索引 {indexEvents.length} 条
            = <strong>{doc.events.length}</strong> 条。
          </p>

          <div className="ntr-idxbar">
            <input type="search" className="ntr-idxq" value={idxQ}
                   placeholder="按标题关键词搜索…"
                   aria-label="索引事件标题搜索"
                   data-index-search="1"
                   onChange={(ev) => setIdxQ(ev.currentTarget.value)} />
            <select value={idxSrc} aria-label="按来源筛选" data-index-filter="source"
                    onChange={(ev) => setIdxSrc(ev.currentTarget.value)}>
              <option value="ALL">全部来源</option>
              {(c.sources ?? []).map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <select value={idxClass} aria-label="按文档类别筛选" data-index-filter="doc_class"
                    onChange={(ev) => setIdxClass(ev.currentTarget.value)}>
              <option value="ALL">全部类别</option>
              {Object.keys(doc.doc_class_legend ?? {}).map((k) => (
                <option key={k} value={k}>{DOC_CLASS_LABEL[k] ?? k}</option>
              ))}
            </select>
            <select value={idxStatus} aria-label="按市场状态筛选" data-index-filter="status"
                    onChange={(ev) => setIdxStatus(ev.currentTarget.value)}>
              <option value="ALL">全部状态</option>
              {Object.keys(doc.status_legend).map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
            <span className="ntr-note" data-index-count={idxFiltered.length}>
              命中 {idxFiltered.length} / {indexEvents.length}
            </span>
          </div>

          <ul className="ntr-list ntr-archlist" data-rows="index">
            {idxFiltered.map((e) => {
              const tags = e.theme_tags ?? [];
              return (
                <li key={e.event_id} className="ntr-archrow" data-event={e.event_id}
                    data-doc-class={e.doc_class} data-status={e.status}
                    data-linked={tags.length > 0 ? '1' : '0'}>
                  <span className="ntr-date">{e.event_date}</span>{' '}
                  <a href={e.source.url} target="_blank" rel="noreferrer noopener">{e.title}</a>
                  {' '}<span className="ntr-dc" data-doc-class={e.doc_class}>
                    {DOC_CLASS_LABEL[e.doc_class ?? ''] ?? e.doc_class}
                  </span>
                  {' '}<span className="ntr-idxst" data-idx-status={e.status}>
                    {STATUS_LABEL[e.status] ?? e.status}
                  </span>
                  {' '}<span className="ntr-note">· {e.source.name}</span>
                  {/* ★ 区分「有明确主题关联」与「尚未建立关联」 */}
                  {tags.length > 0 ? (
                    <span className="ntr-idxtag" data-idx-linked="THEME">
                      {' '}· 主题：{tags.join(' / ')}
                    </span>
                  ) : (
                    <span className="ntr-idxtag ntr-none" data-idx-linked="NONE">
                      {' '}· 尚未建立关联
                      {e.review?.verdict === 'NO_SERIES_AVAILABLE'
                        ? '（主题相关但库内无对应序列）' : ''}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
          {idxFiltered.length === 0 ? (
            <p className="ntr-empty" data-index-empty="1">
              当前筛选条件下<strong>没有</strong>事件。清空关键词或改回「全部」即可恢复。
            </p>
          ) : null}
        </details>
      )}
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
