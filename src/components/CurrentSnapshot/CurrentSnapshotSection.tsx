import { useEffect, useState } from 'react';
import {
  loadCurrentSnapshot,
  type CurrentSnapshotView,
  type ObjectCandidateDetails,
} from '../../data/marketSnapshot/snapshotAdapter';
import type {
  MarketSnapshot,
  SnapshotDiff,
  SnapshotHistoricalCandidate,
} from '../../data/marketSnapshot/types';

/**
 * 本期研究快照（Current Snapshot）—— ThreeC 1.1 Phase 1.3。
 *
 * ## 这一区域回答什么
 * 「**跟上一次比，变了什么？现在该研究什么？**」—— 而不是「明天买什么」。
 *
 * ## 三条设计原则
 * 1. **主角是「变化」**：第一屏就是 diff 摘要；「本期无变化」也要明确说出来（那本身是信息）。
 * 2. **「无对应」是一等公民**：实测 57% 的结构比对是 `NO_VALID_CORRESPONDENCE`。
 *    这不是缺陷 —— 「看起来像 ≠ 结构上成立」正是 ThreeC 区别于主题名匹配工具的地方。
 *    因此它有自己的呈现、计数与说明，不是灰色空态。
 * 3. **门禁**：默认只展示 `CANONICAL`；预览未签发快照时**常驻醒目徽章**。
 *
 * ★ 只读：不联网、不调 LLM、不修改任何数据。
 */

const REGIME_LABEL: Record<string, string> = {
  broad_index_state: '宽基方向',
  breadth_state: '市场广度',
  liquidity_state: '流动性',
  risk_appetite_state: '风险偏好',
};

const REGIME_VALUE_LABEL: Record<string, string> = {
  UP: '上行', FLAT: '震荡', DOWN: '下行', UNKNOWN: '未知',
  BROAD: '广泛', NORMAL: '一般', NARROW: '狭窄',
  EXPANDING: '扩张', STABLE: '平稳', CONTRACTING: '收缩',
  RISK_ON: '偏好上升', NEUTRAL: '中性', RISK_OFF: '偏好下降',
};

const STATUS_LABEL: Record<string, string> = {
  STRUCTURAL_SUPPORTED: '结构支持',
  STRUCTURAL_PARTIAL: '结构部分对应',
  THEME_ONLY: '仅主题相同',
  INSUFFICIENT_EVIDENCE: '证据不足',
  NO_VALID_CORRESPONDENCE: '无有效对应',
};

const STATUS_ORDER = [
  'STRUCTURAL_SUPPORTED',
  'STRUCTURAL_PARTIAL',
  'THEME_ONLY',
  'INSUFFICIENT_EVIDENCE',
  'NO_VALID_CORRESPONDENCE',
];

const PHASE_LABEL: Record<string, string> = {
  EARLY_SIGNAL: '早期信号',
  THEME_FORMING: '主题形成',
  BROAD_CONFIRMATION: '广泛确认',
  EXPANSION: '扩张',
  PEAK: '高峰',
  DECLINE: '退潮',
  UNKNOWN: '阶段未标注',
};

const RESOLUTION_LABEL: Record<string, string> = {
  RESOLVED: '已完成研究',
  NEEDS_RESEARCH_ROUND: '需要研究轮次',
  INSUFFICIENT: '证据不足',
};

function statusCounts(cands: SnapshotHistoricalCandidate[]): [string, number][] {
  const m = new Map<string, number>();
  for (const c of cands) m.set(c.structural_status, (m.get(c.structural_status) ?? 0) + 1);
  return STATUS_ORDER.filter((s) => m.has(s)).map((s) => [s, m.get(s)!]);
}

/* ---------------- 候选明细（★ P0「接通」：把计数变成可看的内容） ---------------- */

/**
 * 展示该对象的**历史结构对应明细**。
 *
 * 设计取舍：
 * - **「有结构对应」默认展开** —— 那是用户真正要看的（通常只有个位数）。
 * - **「无有效对应」默认收起** —— 数量大（常 40+），且**它同样重要**，所以给入口、给说明，不隐藏。
 * - 未解析时**明确说「未解析」**，而不是显示空 —— 空会被误读成「没有对应」。
 */
function CandidateList({ details }: { details?: ObjectCandidateDetails }) {
  if (!details) return null;
  if (!details.resolved) {
    return (
      <p className="cs-dim cs-cand-unresolved">
        结构解释<strong>未解析</strong>（SA artifact 与快照的规则版本不一致，或尚未载入）——
        此处不显示可能对不上的细节。<strong>这不等于「没有对应」。</strong>
      </p>
    );
  }

  const meaningful = details.details.filter((d) => d.status !== 'NO_VALID_CORRESPONDENCE');
  const noValid = details.details.filter((d) => d.status === 'NO_VALID_CORRESPONDENCE');

  const renderItem = (d: (typeof details.details)[number]) => (
    <li key={d.historicalCycleId} className="cs-cand">
      <div className="cs-cand-head">
        <span className="cs-cand-id">{d.historicalCycleId}</span>
        <span className={`cs-cand-status cs-st-${d.status.toLowerCase()}`}>{d.statusLabel}</span>
        {d.themeRelationLabel && <span className="cs-cand-theme">{d.themeRelationLabel}</span>}
      </div>
      <ul className="cs-cand-dims">
        {d.dimensions.map((x) => (
          <li key={x.key}>
            <span className="cs-cand-dim-name">{x.label}</span>
            <span className={`cs-cand-dim-val cs-dim-${x.status.toLowerCase()}`}>{x.statusLabel}</span>
          </li>
        ))}
      </ul>
      {d.whySimilar.length > 0 && (
        <p className="cs-cand-why">
          <strong>为什么对应</strong>
          {d.whySimilar.map((w, i) => (
            <span key={i}>{w}</span>
          ))}
        </p>
      )}
      {d.whyNotSimilar.length > 0 && (
        <p className="cs-cand-why cs-cand-why-not">
          <strong>哪里不同 / 限制</strong>
          {d.whyNotSimilar.map((w, i) => (
            <span key={i}>{w}</span>
          ))}
        </p>
      )}
    </li>
  );

  return (
    <>
      {meaningful.length > 0 && (
        <details className="cs-cands" open>
          <summary>
            有结构对应 <strong>{meaningful.length}</strong> 条 —— 展开看是哪些历史对象、为什么
          </summary>
          <ul className="cs-cand-list">{meaningful.map(renderItem)}</ul>
        </details>
      )}
      {noValid.length > 0 && (
        <details className="cs-cands">
          <summary>
            无有效对应 <strong>{noValid.length}</strong> 条 —— 同样可查（默认收起）
          </summary>
          <ul className="cs-cand-list">{noValid.map(renderItem)}</ul>
        </details>
      )}
    </>
  );
}

/* ---------------- 空态 ---------------- */

function NoCanonical({ view }: { view: CurrentSnapshotView }) {
  return (
    <section className="cs-sec cs-empty" aria-label="本期研究快照">
      <h5>本期研究快照</h5>
      <p className="cs-empty-lead">
        当前<strong>尚无已签发的快照</strong>（<code>CANONICAL</code>）。
      </p>
      <p className="cs-dim">
        索引里有 {view.draftCount} 份快照，最新为 <code>{view.latestDate}</code>，但都还处于
        <strong>未签发</strong>状态。按项目约定，只有经人工审核签发的 `CANONICAL` 快照才允许产品展示 ——
        这是防止「未经审核的研究被当成结论」的门禁，不是缺陷。
      </p>
      <p className="cs-dim">
        签发方式见 <code>docs/MONTHLY_RESEARCH_RUNBOOK.md</code> 步骤 7；
        想先看未签发内容可加 <code>?snapshot=draft</code>（会带醒目标识）。
      </p>
    </section>
  );
}

/* ---------------- diff 摘要 ---------------- */

function DiffSummary({ diff, previous }: { diff: SnapshotDiff | null; previous: MarketSnapshot | null }) {
  if (!diff || !previous) {
    return (
      <section className="cs-sec" aria-label="与上期对比">
        <h5>与上期对比</h5>
        <p className="cs-dim">
          这是<strong>第一份</strong>可展示的快照，没有可比对象 —— 从下一期开始这里会显示「变了什么」。
        </p>
      </section>
    );
  }

  const { summary } = diff;
  const layers: [string, number][] = [
    ['市场环境', summary.regime],
    ['研究对象', summary.objects],
    ['历史候选', summary.candidates],
    ['观察', summary.observations],
  ];

  return (
    <section className="cs-sec cs-diff" aria-label="与上期对比">
      <h5>
        与上期对比
        <span className="cs-dim cs-diff-from">
          {previous.snapshot_id}（{previous.snapshot_date}）→ {diff.to.snapshot_id}
        </span>
      </h5>

      {summary.unchanged ? (
        <p className="cs-diff-none" role="status">
          本期<strong>无变化</strong> —— 与上期逐层比对后，市场环境 / 研究对象 / 历史候选 / 观察四层均未变动。
          「没有变化」本身也是结论：说明本轮没有新的研究进展。
        </p>
      ) : (
        <>
          <p className="cs-diff-total" role="status">
            共 <strong>{summary.total}</strong> 处变化
          </p>
          <ul className="cs-diff-layers">
            {layers.map(([name, n]) => (
              <li key={name} className={n > 0 ? 'on' : ''}>
                <span className="cs-diff-layer-name">{name}</span>
                <span className="cs-diff-layer-n">{n > 0 ? `+${n}` : '0'}</span>
              </li>
            ))}
          </ul>

          {diff.regime.length > 0 && (
            <ul className="cs-diff-list">
              {diff.regime.map((r) => (
                <li key={r.dimension}>
                  市场环境 · {REGIME_LABEL[r.dimension] ?? r.dimension}：
                  <code>{REGIME_VALUE_LABEL[r.from] ?? r.from}</code> → <code>{REGIME_VALUE_LABEL[r.to] ?? r.to}</code>
                </li>
              ))}
            </ul>
          )}
          {diff.objects.changed.map((c) => (
            <ul className="cs-diff-list" key={`${c.object_id}-${c.field}`}>
              <li>
                研究对象 · {c.display_name} · <code>{c.field}</code>：{c.from || '（空）'} → {c.to || '（空）'}
              </li>
            </ul>
          ))}
          {diff.objects.added.length > 0 && (
            <ul className="cs-diff-list">
              {diff.objects.added.map((o) => (
                <li key={o.object_id}>新增研究对象 · {o.display_name}（{PHASE_LABEL[o.declared_phase] ?? o.declared_phase}）</li>
              ))}
            </ul>
          )}
          {diff.objects.removed.length > 0 && (
            <ul className="cs-diff-list">
              {diff.objects.removed.map((o) => (
                <li key={o.object_id}>移除研究对象 · {o.display_name}</li>
              ))}
            </ul>
          )}
          {diff.candidates.statusChanged.length > 0 && (
            <ul className="cs-diff-list">
              {diff.candidates.statusChanged.map((c) => (
                <li key={`${c.current_object_id}-${c.historical_cycle_id}`}>
                  历史候选 · {c.current_object_id} × {c.historical_cycle_id}：
                  <code>{STATUS_LABEL[c.from] ?? c.from}</code> → <code>{STATUS_LABEL[c.to] ?? c.to}</code>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      <p className="cs-dim">
        以上只陈述<strong>事实</strong>（哪个字段从什么变成什么），不含好坏判断 —— 判断属研究结论，不在产品端产生。
      </p>
    </section>
  );
}

/* ---------------- 主体 ---------------- */

/**
 * **纯展示层** —— 输入一个已载入的 ViewModel，输出静态标记。
 *
 * ★ 刻意与异步载入分离：项目用 `renderToStaticMarkup` 做组件测试（无 jsdom），
 * 异步容器在 SSR 下只会渲染「载入中」。把渲染逻辑做成**同步纯函数**，
 * 才能真正测到「无对应」等关键呈现。
 */
export function CurrentSnapshotBody({ view }: { view: CurrentSnapshotView }) {
  if (view.state === 'empty') {
    return (
      <section className="cs-sec cs-empty" aria-label="本期研究快照">
        <h5>本期研究快照</h5>
        <p className="cs-dim">
          尚未有任何 Market Snapshot。首次建立方式见 <code>docs/MONTHLY_RESEARCH_RUNBOOK.md</code>。
        </p>
      </section>
    );
  }
  if (view.state === 'no-canonical') return <NoCanonical view={view} />;

  const s = view.snapshot!;
  const regime = s.market_regime;
  const unknownDims = (Object.keys(REGIME_LABEL) as string[]).filter(
    (d) => (regime as unknown as Record<string, string>)[d] === 'UNKNOWN',
  );

  return (
    <section className="cs-wrap" aria-label="本期研究快照">
      <div className="cs-head">
        <h5>本期研究快照</h5>
        <span className="cs-meta">
          <code>{s.snapshot_id}</code> · 快照日 {s.snapshot_date} · 契约 {s.market_snapshot_version}
        </span>
        {view.preview && (
          <span className="cs-badge cs-badge-preview" role="status">
            未签发 · 仅供预览
          </span>
        )}
      </div>

      <DiffSummary diff={view.diff} previous={view.previous} />

      <section className="cs-sec" aria-label="当前市场环境">
        <h5>当前市场环境</h5>
        <ul className="cs-regime">
          {(Object.keys(REGIME_LABEL) as string[]).map((d) => {
            const v = (regime as unknown as Record<string, string>)[d];
            return (
              <li key={d} className={v === 'UNKNOWN' ? 'unknown' : ''}>
                <span className="cs-regime-name">{REGIME_LABEL[d]}</span>
                <span className="cs-regime-value">{REGIME_VALUE_LABEL[v] ?? v}</span>
              </li>
            );
          })}
        </ul>
        {regime.beta_note && <p className="cs-dim">{regime.beta_note}</p>}
        {unknownDims.length > 0 && (
          <p className="cs-unknown-note">
            <strong>{unknownDims.length} 个维度为「未知」</strong> —— 这是<strong>诚实空态</strong>：
            未接入可核验数据源时<strong>不猜测</strong>。「不知道」是合法结论，不是待办。
          </p>
        )}
      </section>

      <section className="cs-sec" aria-label="研究对象">
        <h5>研究对象（{s.research_objects.length}）</h5>
        <ul className="cs-objs">
          {s.research_objects.map((o) => {
            const mine = s.historical_candidates.filter((c) => c.current_object_id === o.object_id);
            const counts = statusCounts(mine);
            const noValid = mine.filter((c) => c.structural_status === 'NO_VALID_CORRESPONDENCE').length;
            const useful = mine.filter(
              (c) => c.structural_status === 'STRUCTURAL_SUPPORTED' || c.structural_status === 'STRUCTURAL_PARTIAL',
            ).length;
            return (
              <li key={o.object_id} className="cs-obj">
                <div className="cs-obj-head">
                  <span className="cs-obj-name">{o.display_name}</span>
                  <span className="cs-obj-id">{o.object_id}</span>
                  <span className="cs-obj-phase">{PHASE_LABEL[o.declared_phase] ?? o.declared_phase}</span>
                  <span className="cs-obj-res">{RESOLUTION_LABEL[o.resolution_state] ?? o.resolution_state}</span>
                </div>
                <p className="cs-dim">
                  大主题 {o.macro_theme ?? '未标注'}
                  {o.canonical_drivers?.length ? ` · 驱动机制 ${o.canonical_drivers.join(' / ')}` : ''}
                  {o.evidence_categories?.length ? ` · 证据类别 ${o.evidence_categories.join(' / ')}` : ''}
                </p>

                {mine.length === 0 ? (
                  <p className="cs-dim">该对象尚无历史结构候选。</p>
                ) : (
                  <>
                    <ul className="cs-statusbar">
                      {counts.map(([st, n]) => (
                        <li key={st} className={`cs-status cs-st-${st.toLowerCase()}`}>
                          <span className="cs-status-n">{n}</span>
                          <span className="cs-status-name">{STATUS_LABEL[st] ?? st}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="cs-dim">
                      共 {mine.length} 条比对 · 有结构对应 <strong>{useful}</strong> 条 ·
                      无有效对应 <strong>{noValid}</strong> 条
                    </p>

                    {/* ★ P0「接通」：计数 → 可看的明细（含「为什么对应 / 哪里不同」） */}
                    <CandidateList
                      details={view.detailsByObject.find((d) => d.objectId === o.object_id)}
                    />

                    {noValid > 0 && (
                      <p className="cs-no-valid">
                        <strong>「无有效对应」不是缺陷。</strong>
                        它意味着这些历史对象与该对象<strong>主题可能同名、但结构不成立</strong> ——
                        这正是 ThreeC 与「按主题名找相似」的工具的区别所在。
                      </p>
                    )}
                  </>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <section className="cs-sec" aria-label="观察">
        <h5>观察（{s.observations.length}）</h5>
        {s.observations.length === 0 ? (
          <p className="cs-dim">本期未登记新观察（空是合法状态，不为凑数而写）。</p>
        ) : (
          <ul className="cs-obs">
            {s.observations.map((o) => (
              <li key={o.observation_id}>
                <code>{o.date}</code> · {o.observation_type} · {o.claim}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="cs-sec" aria-label="研究声明">
        <h5>研究声明</h5>
        <p className="cs-dim">
          本轮研究问题：{String((s as unknown as Record<string, { research_question?: string }>).research_context?.research_question ?? '（未填写）')}
        </p>
        <p className="cs-dim cs-cs-note">
          Current Snapshot 是<strong>研究过程的记录</strong>，不是预测、不是信号、不是买卖建议；
          其中「历史候选」是<strong>研究候选</strong>，不是买入机会。
        </p>
      </section>
    </section>
  );
}

/**
 * **异步容器** —— 负责载入快照（index 静态、快照按需 lazy），把 ViewModel 交给纯展示层。
 */
export function CurrentSnapshotSection({ previewMode }: { previewMode: boolean }) {
  const [view, setView] = useState<CurrentSnapshotView | null>(null);

  useEffect(() => {
    let alive = true;
    loadCurrentSnapshot(previewMode).then((v) => {
      if (alive) setView(v);
    });
    return () => {
      alive = false;
    };
  }, [previewMode]);

  if (!view) return <p className="cs-dim">正在载入本期快照…</p>;
  return <CurrentSnapshotBody view={view} />;
}
