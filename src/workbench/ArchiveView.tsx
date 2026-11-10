/**
 * 研究对象档案（v0.82）—— **存档待复核**，已退出默认工作台。
 *
 * 默认工作台现在只放「从当前市场信息 + 客观行情结构挖出来的主题」。
 * 这里保留 2026-10-23 人工离线轮次设定的 6 个研究对象、后续研究轮次复查、
 * 阶段治理与专项假设，供事后回测与人工复核；不参与当前主题挖掘。
 *
 * ★ 所有研究侧字符串一律过 RichText（产物文案含 ** 强调标记）。
 */
import { RichText } from '../components/RichText';
import type { FrontierDoc, FrontierItem, WeeklyResearchDoc } from './FrontierView';

const POS_LABEL: Record<string, string> = {
  IN_WINDOW: '窗口内', PRE_WINDOW: '窗口未开始', PRE_OBSERVATION: '前置观察',
  THEME_FORMING: '主题形成中', BROAD_CONFIRMATION: '广度确认',
  EXPANSION: '扩散', WATCH_ONLY: '仅观察', INSUFFICIENT: '证据不足',
};
const VERDICT_LABEL: Record<string, string> = {
  MAINTAINED_WITH_NEW_LEAD: '维持 · 新线索',
  MAINTAINED_ADJACENT_EVIDENCE: '维持 · 相邻证据',
  MAINTAINED_COVERAGE_GAP: '维持 · 覆盖缺口',
};

export function ArchiveView({ doc, weekly, onRecord }: {
  doc: FrontierDoc;
  weekly: WeeklyResearchDoc;
  onRecord: (title: string, id: string) => void;
}) {
  const phaseGov = doc.theme_market.phase_governance as Record<string, Record<string, unknown>>;
  const govText = (group: string, key: string) => String(phaseGov[group]?.[key] ?? '');
  const byId = new Map(doc.items.map((x) => [x.id, x]));
  const fixedRows = (ids: string[]) => ids.map((id) => byId.get(id)).filter(
    (x): x is FrontierItem => Boolean(x));

  return (
    <main className="wb-main fb" data-archive-view="1">
      <h2>研究对象档案 · 存档待复核</h2>
      <p className="fb-hint">
        2026-10-23 人工离线研究轮次设定的 {doc.theme_market.themes.length} 个研究对象与后续复查记录。
        <strong>已退出默认工作台</strong>，保留供回测与人工复核；不参与当前主题挖掘。
      </p>

      <details className="fb-rule" data-declaration-policy="1">
        <summary>阶段声明去哪了 / 口径与后续更新 SOP</summary>
        <p><strong>为什么移走</strong>：产业机制阶段是人工研究轮次的判定，一次声明停在某个日期；
          行情每周更新，静态旧声明放在首屏既不能说明当下，也容易被误读成行情状态。</p>
        <p><strong>保留在哪</strong>：<code>phase_declaration_log_v0_1.json</code>（追加式、只增不改、
          带 PIT 锚点、不含结算字段），可在「内部评估视图」按声明时间查看完整依据与当时的推理。</p>
        <p><strong>研究侧声明</strong>：<RichText text={govText('research_declared', 'criteria')} /></p>
        <p><strong>最近一次评审</strong>：<RichText text={govText('research_declared', 'last_review')} /> ·
           <RichText text={govText('research_declared', 'last_verdict')} /></p>
        <p><strong>为什么没跟行情变</strong>：<RichText text={govText('research_declared', 'market_exclusion')} /></p>
        <p><strong>产品端推导</strong>：<RichText text={govText('product_inferred', 'engine')} />；
           <RichText text={govText('product_inferred', 'forbidden')} /></p>
        <p><strong>后续更新 SOP</strong>：<RichText text={govText('update_policy', 'weekly')} />
           <RichText text={govText('update_policy', 'manual_round')} /></p>
        <p><strong>默认页口径</strong>：<RichText text={govText('update_policy', 'default_page')} /></p>
        <p><strong>声明日志</strong>：<RichText text={govText('update_policy', 'declaration_log')} /></p>
        <p className="fb-caveat">信号只提示人工复核，不构成阶段变更，不参与定档、不自动改阶段，也不参与验收。</p>
      </details>

      {weekly.research_round && (
        <div className="fb-round" data-research-round="1">
          <h3>研究轮次复查 · <code>{weekly.research_round.round_id}</code>
            （{weekly.research_round.as_of}）</h3>
          <p className="fb-hint">
            {weekly.research_round.theme_reviews.length} 主题复查 ·{' '}
            {weekly.research_round.new_watch_directions.length} 条观察方向 ·{' '}
            {String(weekly.research_round.counts.sources ?? '—')} 来源
          </p>
          <ul className="fb-watch">
            {weekly.research_round.new_watch_directions.map((w) => (
              <li key={w.direction_id} data-watch-direction={w.direction_id}>
                <div><strong>{w.title}</strong>
                  <span className="fb-date">{w.time_position} · {w.window_hint}</span></div>
                <span className="fb-sub2">
                  {w.board_series
                    ? `${w.board_name ?? ''}（${w.board_series} · ${w.board_mapping_status}）`
                    : <>未映射板块：<RichText text={w.board_mapping_reason} /></>}
                </span>
                <p className="fb-round-reason"><RichText text={w.reason} /></p>
                <a href={w.event.url} target="_blank" rel="noreferrer">{w.event.title}</a>
                <span className="fb-caveat"> {w.event.date} · <RichText text={w.caveat} /></span>
              </li>
            ))}
          </ul>
          <details className="fb-rule" data-theme-reviews="1">
            <summary>逐主题复查（{weekly.research_round.theme_reviews.length}）</summary>
            <ul>
              {weekly.research_round.theme_reviews.map((r) => (
                <li key={r.candidate_id} data-theme-review={r.candidate_id}>
                  <strong>{r.display_name}</strong> · {VERDICT_LABEL[r.verdict] ?? r.verdict} ·
                  新证据 {r.new_evidence_count} · 下一步：
                  <RichText text={r.next_research_question} />
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}

      <details className="fb-rule" data-weekly-archive="1">
        <summary>本周研究明细 · 存档待复核（不是当前主题挖掘）</summary>
      <div className="fb-weekly" data-weekly-research="1">
        <h3>本周最新研究 · <code>{weekly.feed_window[0]}</code> → <code>{weekly.feed_window[1]}</code>
          （机制轨 as_of {weekly.as_of}）</h3>
        <p className="fb-hint">
          本周 {weekly.counts.events_in_window} 条可核文件 ·{' '}
          <strong>{weekly.counts.linked_to_direction}</strong> 条精确关联 ·{' '}
          {weekly.counts.directions_with_match}/{weekly.counts.directions} 方向命中 · 未命中写原因
        </p>
        <ol className="fb-weekly-list">
          {weekly.directions.map((d) => (
            <li key={d.direction} data-weekly-direction={d.direction}
                data-weekly-match={d.matched_events.length}>
              <div className="fb-weekly-head">
                <strong>{d.direction}</strong> · 板块 <code>{d.series.join(' / ') || '—'}</code>
                {' '}· 对应当前研究主题 {d.candidate_ids.length} 个
              </div>
              {d.matched_events.length > 0 ? (
                <ul className="fb-weekly-events">
                  {d.matched_events.map((e) => (
                    <li key={e.event_id} data-weekly-event={e.event_id}>
                      <a href={e.url ?? '#'} target="_blank" rel="noreferrer">{e.title}</a>
                      <span className="fb-date">{e.event_date} · {e.publisher ?? '来源未标注'}</span>
                      <span className="fb-sub2">主题：{e.theme_tags.join(' / ') || '—'}</span>
                      {e.boards.map((b) => (
                        <span key={`${e.event_id}-${b.board_series}`} className="fb-sub2"
                              data-weekly-board={b.board_series ?? ''}>
                          {b.board_name}（{b.board_series} · {b.relation}）：{b.rationale}
                        </span>
                      ))}
                      <span className="fb-caveat">
                        观察起点 {e.observe_from ?? '—'} · {e.observation_status.join(' / ') || '—'}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="fb-gap" data-weekly-gap={d.direction}>
                  <RichText text={d.no_match_reason ?? '本周无可核新增事件（原因未标注）'} />
                </p>
              )}
            </li>
          ))}
        </ol>
        <p className="fb-hint">
          本周其它可核文件 {weekly.other_verifiable_documents.count} 条
          （{Object.entries(weekly.other_verifiable_documents.by_nature)
            .map(([k, v]) => `${k} ${v}`).join(' · ')}）：{weekly.other_verifiable_documents.note}
        </p>
        <h3>前置观察窗口（库内可核）</h3>
        <ul className="fb-weekly-windows">
          {weekly.observation_windows.map((w) => (
            <li key={`${w.date}-${w.label}`} data-observation-window={w.date}>
              <strong>{w.date}</strong> · {w.label ?? '—'}
              <span className="fb-caveat"> {w.fact_vs_assumption ?? ''}</span>
            </li>
          ))}
        </ul>
      </div>
      </details>

      <div className="fb-fixed-group" data-archived-themes="1">
        <h3>人工研究对象（{doc.theme_market.themes.length}）· 存档待复核</h3>
        <ul className="fb-fixed">
          {doc.theme_market.themes.map((t) => (
            <li key={t.candidate_id} data-fixed-row={t.candidate_id} className="fb-theme-row">
              <div className="fb-theme-r1">
                <button type="button" className="wb-linkbtn"
                        onClick={() => onRecord(t.display_name, t.candidate_id)}>{t.display_name}</button>
                <span className="fb-weekly-link"
                      data-weekly-theme-count={weekly.theme_index[t.candidate_id]?.matched_count ?? 0}>
                  本周研究：{weekly.theme_index[t.candidate_id]
                    ? `${weekly.theme_index[t.candidate_id].direction} · ${weekly.theme_index[t.candidate_id].matched_count} 条命中`
                    : '当前采集范围未建立方向映射'}
                </span>
              </div>
              {weekly.theme_index[t.candidate_id]?.no_match_reason && (
                <p className="fb-gap" data-weekly-theme-gap={t.candidate_id}>
                  <RichText text={weekly.theme_index[t.candidate_id].no_match_reason ?? ''} />
                </p>
              )}
              <p className="fb-market" data-market-as-of={t.market_as_of}>
                行情附注 as_of <code>{t.market_as_of}</code>（{t.stock_count} 只人工声明标的等权，相对沪深300）：
                5 日 <strong>{t.equal_weight['5']?.equal_weight_excess_pp ?? '—'} pp</strong> ·
                10 日 <strong>{t.equal_weight['10']?.equal_weight_excess_pp ?? '—'} pp</strong> ·
                20 日 <strong>{t.equal_weight['20']?.equal_weight_excess_pp ?? '—'} pp</strong>
              </p>
              {t.signals.map((sg) => (
                <p key={sg.id} className="fb-signal" data-signal={sg.id}>
                  <strong>{sg.id}</strong>：{sg.detail}
                </p>
              ))}
            </li>
          ))}
        </ul>
      </div>

      <div className="fb-fixed-group">
        <h3>专项假设（{doc.fixed_sections.special_hypotheses.length}）</h3>
        <ul className="fb-fixed">
          {fixedRows(doc.fixed_sections.special_hypotheses).map((x) => (
            <li key={x.id} data-fixed-row={x.id}>
              <button type="button" className="wb-linkbtn"
                      onClick={() => onRecord(x.title, x.id)}>{x.title}</button>
              <span className="fb-date">{POS_LABEL[x.time_position ?? ''] ?? x.time_position}</span>
              {x.gap && <span className="fb-sub2">缺口：<RichText text={x.gap} /></span>}
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
