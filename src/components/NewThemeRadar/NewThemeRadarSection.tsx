/**
 * 自动发现的新题材线索（v0.66 第一版）。
 *
 * ## 它和现有三个入口的区别（不得混为一谈）
 *
 * | 入口 | 谁产出的 | 单位 |
 * |---|---|---|
 * | **当前研究主题** | 人工提出的研究方向（研究记录） | 主题 |
 * | **季节性统计窗口** | 月度收益模式（自动统计，历史重复） | 板块 × 月份 |
 * | **专项假设的历史检验** | 人工预设假设（生肖 / 台海 / 流感） | 假设 |
 * | **本区：自动发现的新题材线索** | 公开政策事件 → 关键词关联 → 行情核验 | 事件 |
 *
 * ## 红线
 *
 * - 只展示**采集到的事实 + 核验状态**，不含打分 / 概率 / 收益排序 / 交易信号；
 * - `CANDIDATE` 只是「值得人工看一眼」的机械筛选，**不是**「已确认的题材」；
 * - 覆盖范围（单一发布机构、两个栏目）**就地写明**，不假装是全市场挖掘；
 * - 缺失一律显示 `gaps`（广度不可得 / 个股未映射 / 交易日不足），不补 0、不推断。
 */
import raw from '@current/new_theme_radar_v0_1.json';
import { RichText } from '../RichText';

interface ThemeLink {
  keyword: string; matched_in: 'TITLE' | 'QUOTE';
  board_series: string; board_name: string;
  relation: 'DIRECT' | 'PROXY'; rationale: string;
}
interface Market {
  board_series?: string | null; as_of?: string | null;
  window?: [string, string] | null;
  board_ret_pct?: number | null; bench_ret_pct?: number | null; excess_pp?: number | null;
  observation_trading_days?: number | null; breadth?: number | null;
  status: string; gaps?: string[];
  drift?: { window: [string, string]; excess_pp: number; note?: string } | null;
}
interface RadarEvent {
  event_id: string; title: string; event_date: string; first_seen: string;
  source: { id?: string; name: string; publisher: string; url: string;
    list_url?: string; category?: string; access?: string };
  evidence_quote?: string | null;
  theme_links: ThemeLink[];
  market: Market;
  security_mapping?: { status: string; reason?: string } | null;
  status: string;
  gaps: string[];
}
interface Doc {
  as_of: string; generated_at: string;
  coverage: { publisher?: string; sources?: { id: string; name: string; category?: string }[];
    date_range?: [string, string] | null; events: number;
    by_source?: Record<string, number>; limits?: string[] };
  rules?: { reaction_trading_days?: number; min_observation_trading_days?: number;
    max_event_age_days?: number; not_scored?: string };
  summary: { events: number; by_status: Record<string, number>; candidates: number };
  status_legend: Record<string, string>;
  events: RadarEvent[];
}
const doc = raw as unknown as Doc;

const STATUS_LABEL: Record<string, string> = {
  CANDIDATE: '候选线索',
  WATCH: '仅留档',
  PENDING_MARKET: '窗口不足',
  INSUFFICIENT: '无法核验',
  NO_THEME_LINK: '未建立关联',
};

const num = (v: number | null | undefined, suffix = '', digits = 2) =>
  typeof v === 'number' && Number.isFinite(v)
    ? `${v > 0 ? '+' : ''}${v.toFixed(digits)}${suffix}` : '—';

/** 展示条数上限：第一版只给最近的若干条，其余在产物里（不做分页/筛选，避免假装成完整工作台） */
const SHOW_LIMIT = 12;

export function NewThemeRadarSection() {
  const c = doc.coverage;
  const srcNames = (c.sources ?? []).map((s) => s.name).join(' / ') || c.publisher || '—';
  const cats = [...new Set((c.sources ?? []).map((s) => s.category).filter(Boolean))].join(' / ');
  const shown = doc.events.slice(0, SHOW_LIMIT);

  return (
    <section className="ntr" aria-label="自动发现的新题材线索" data-radar-as-of={doc.as_of}
             data-radar-events={doc.summary.events}>
      <div className="ntr-head">
        <h2 className="ntr-h2">自动发现的新题材线索</h2>
        <span className="ntr-badge" data-radar-version="0.1">第一版 · 覆盖有限</span>
        <span className="ntr-meta">
          行情截至 <code>{doc.as_of}</code> · 采集 <code>{doc.generated_at}</code>
        </span>
      </div>

      <p className="ntr-lead">
        从<strong>公开政策发布页</strong>自动采集带日期的事件 → 按<strong>显式关键词表</strong>关联行业板块 →
        用<strong>真实行情</strong>核验事件附近的相对基准表现。这里只给<strong>线索与核验状态</strong>：
        不含打分、概率、收益排序或交易信号；<strong>不是买卖建议</strong>，
        也不代表「题材已被确认」。
      </p>

      <p className="ntr-coverage" data-coverage="1">
        来源：<strong>{srcNames}</strong>{cats ? `（${cats}）` : ''}
        {c.date_range ? <> · 覆盖 <code>{c.date_range[0]}</code> → <code>{c.date_range[1]}</code></> : null}
        {' '}· 事件 <strong>{c.events}</strong> 条 · 其中候选线索{' '}
        <strong data-candidate-count={doc.summary.candidates}>{doc.summary.candidates}</strong> 条
        {doc.rules?.reaction_trading_days != null && (
          <> · 反应窗口 = 事件日 + {doc.rules.reaction_trading_days} 个交易日</>
        )}
      </p>

      <p className="ntr-legend" data-status-legend="1">
        {Object.entries(doc.status_legend).map(([k, v]) => (
          <span key={k} className="ntr-lg"><code>{k}</code> {v}</span>
        ))}
      </p>

      <ol className="ntr-list">
        {shown.map((e) => {
          const mk = e.market ?? { status: 'INSUFFICIENT' };
          const observed = mk.status === 'OBSERVED';
          return (
            <li key={e.event_id} className="ntr-row" data-event={e.event_id} data-status={e.status}>
              <div className="ntr-row1">
                <span className="ntr-date">{e.event_date}</span>
                <a href={e.source.url} target="_blank" rel="noreferrer noopener" className="ntr-title">
                  {e.title}
                </a>
                <span className={`ntr-st st-${e.status.toLowerCase()}`}>{STATUS_LABEL[e.status] ?? e.status}</span>
              </div>

              <div className="ntr-row2">
                {e.theme_links.length > 0 ? e.theme_links.map((l, i) => (
                  <span key={i} className="ntr-link" data-relation={l.relation}>
                    关联 <strong>{l.board_name}</strong>（{l.board_series}）· 命中「{l.keyword}」于
                    {l.matched_in === 'TITLE' ? '标题' : '原文'} · {l.relation === 'PROXY' ? '代理' : '直接'}
                  </span>
                )) : (
                  <span className="ntr-link ntr-none">未命中显式关键词表 → 不建立板块关联</span>
                )}
              </div>

              {observed && (
                <div className="ntr-row3" data-market="1">
                  反应窗口 <code>{mk.window?.[0]} → {mk.window?.[1]}</code>
                  （{mk.observation_trading_days} 个交易日）· 板块 <strong>{num(mk.board_ret_pct, '%')}</strong>
                  {' '}· 沪深300 <strong>{num(mk.bench_ret_pct, '%')}</strong>
                  {' '}· 超额 <strong>{num(mk.excess_pp, 'pp')}</strong>
                  {mk.drift ? (
                    <span className="ntr-drift">
                      {' '}· 事件至今（背景，不参与判定）超额 {num(mk.drift.excess_pp, 'pp')}
                    </span>
                  ) : null}
                </div>
              )}

              {e.gaps.length > 0 && (
                <ul className="ntr-gaps" data-gaps={e.gaps.length}>
                  {e.gaps.map((g, i) => <li key={i}><RichText text={g} /></li>)}
                </ul>
              )}

              {e.evidence_quote && (
                <details className="ntr-evi">
                  <summary>原文片段与来源</summary>
                  <p><RichText text={e.evidence_quote} /></p>
                  <p className="ntr-src">
                    来源：{e.source.name} · <a href={e.source.url} target="_blank" rel="noreferrer noopener">
                      {e.source.url}
                    </a>
                  </p>
                </details>
              )}
            </li>
          );
        })}
      </ol>

      {doc.events.length > shown.length && (
        <p className="ntr-note">
          本区只列最近 {shown.length} 条（共 {doc.events.length} 条，其余在产物
          <code> new_theme_radar_v0_1.json</code> 内）；不做筛选与排序工作台，避免看起来像完整挖掘系统。
        </p>
      )}

      <details className="ntr-limits">
        <summary>覆盖范围与已知局限（必读）</summary>
        <ul>
          {(c.limits ?? []).map((t, i) => <li key={i}><RichText text={t} /></li>)}
        </ul>
        {doc.rules?.not_scored ? <p className="ntr-note"><RichText text={doc.rules.not_scored} /></p> : null}
      </details>
    </section>
  );
}
