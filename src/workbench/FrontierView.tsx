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
}
export interface FrontierDoc {
  artifact: string; artifact_version: string; purpose: string;
  tracks: { statistical: { as_of: string; cadence: string; source: string; note: string };
            mechanism: { as_of: string; cadence: string; source: string[];
                         note: string; feed_window: [string, string] } };
  group_rule: { order: string[]; meaning: string;
                attention_label_rule: Record<string, string> };
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
function pct(v: unknown): string {
  return typeof v === 'number' ? `${(v * 100).toFixed(0)}%` : '—';
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
  const shown = showAll ? rows : rows.slice(0, 30);
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

      {/* ── 一、值得关注（默认按 G1→G4 排序） ── */}
      <section className="fb-section" data-frontier-section="items">
        <h2>一、接下来值得关注（{doc.items.length} 条）</h2>
        <p className="fb-hint">
          统计理由来自历史重复与样本外检验，<strong>未校准、不是未来概率</strong>；
          行情超额只作<strong>行情附注</strong>，不参与验收。
          窗口只有<strong>月份级</strong>，不推算具体交易日。
        </p>
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
        <p className="fb-count" data-frontier-count={rows.length}>
          命中 <strong>{rows.length}</strong> 条 · 当前显示 {shown.length} 条
        </p>

        <ol className="fb-list" data-frontier-list="1">
          {shown.map((x) => {
            const h = (x.statistical_reason ?? {}) as Record<string, unknown>;
            return (
              <li key={x.id} className="fb-row" data-frontier-row={x.id}
                  data-group={x.group} data-track="STATISTICAL"
                  data-attention={x.attention_label} data-order={x.order}>
                <div className="fb-r1">
                  <span className={`fb-grp g-${x.group.toLowerCase()}`}>{x.group}</span>
                  <span className="fb-att">{x.attention_label}</span>
                  <span className="fb-pos">{POS_LABEL[x.time_position ?? ''] ?? x.time_position}</span>
                  <span className="fb-win">{x.window_hint}</span>
                </div>
                <h3 className="fb-title">{x.title}</h3>
                <p className="fb-sub">{x.subtitle} · {x.why_now ?? '—'}</p>

                <div className="fb-reasons">
                  <div className="fb-reason" data-reason="STATISTICAL">
                    <span className="fb-reason-tag">统计理由（季度轨）</span>
                    {x.statistical_reason ? (
                      <p>
                        {String(h.n_years ?? '—')} 年历史 · 命中率 {pct(h.hit_rate)} ·
                        历史中位超额 {num(h.median_excess_pct)} pp ·
                        样本外 {String(h.oos_status ?? '—')}（{String(h.oos_tests ?? 0)} 次） ·
                        时点资格 {String(h.pit_eligible_years ?? '—')} 年
                      </p>
                    ) : <p>本条为专项假设 / 当前对象，无板块月度统计。</p>}
                    <p className="fb-caveat">历史统计，未校准，不是未来概率；只作行情附注，不参与研究增量验收。</p>
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
          })}
        </ol>
        {rows.length > shown.length && (
          <button type="button" className="wb-btn primary" data-show-all="1"
                  onClick={() => setShowAll(true)}>显示全部 {rows.length} 条</button>
        )}
      </section>

      {/* ── 二、机制轨独立信息流 ── */}
      <section className="fb-section" data-frontier-section="mechanism">
        <h2>二、近 7 日可核事件（{feedRows.length} / {doc.mechanism_feed.length} 条）</h2>
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
        <h2>三、已知日程 / 前置观察窗口（{cal.entries.length} 条）</h2>
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

      <p className="fb-foot" data-frontier-limits="1">
        {doc.limits.map((t, i) => <span key={i}><RichText text={t} />{' '}</span>)}
      </p>
    </main>
  );
}
