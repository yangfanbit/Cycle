import { useState } from 'react';
import type { Selection } from '../Timeline/Timeline';
import {
  type CurrentCandidateListView,
  type CurrentCandidateView,
  CURRENT_CANDIDATE_HINT,
  CURRENT_SIMILARITY_DISCLAIMER,
} from '../../data/timeline/currentCandidateAdapter';
import {
  CANDIDATE_STATUS_LABEL,
  DIMENSION_LABEL,
  EVIDENCE_DIRECTION_LABEL,
  EVIDENCE_SOURCE_LABEL,
  EVIDENCE_STRENGTH_LABEL,
  ORIGIN_LABEL,
  PHASE_DIMENSIONS,
  SIGNAL_LEVEL_LABEL,
  TEMPORAL_LABEL,
  NARRATIVE_TYPE_LABEL,
} from '../../data/timeline/currentCandidate';
import {
  AGGREGATE_LEVEL_LABEL,
  CONFLICT_KIND_LABEL,
} from '../../data/timeline/currentEvidence';
import { TIER_LABEL } from '../../data/timeline/historicalSimilarPhase';
import { PHASE_LABEL } from '../../data/timeline/researchAttention';
import {
  PRE_OBSERVATION_HINT,
  PRE_OBSERVATION_LABEL,
} from '../../data/timeline/preObservation';

/**
 * 当前研究候选（Phase 7 — Current Research Discovery v1）。
 *
 * ## 这一区域回答什么
 * 「**今天这个时间点，我应该去历史资料里研究什么？**」
 * —— 而不是「明天应该买什么」。
 *
 * ## 克制的设计约束
 * 每条候选最多展示：名称 · 当前研究阶段 · 一句话解释 · 证据充分度 · 相似案例数 ·
 * 研究问题入口。**不展示新闻流、不展示评分、不展示概率**。
 * 详情为**就地展开**（不打开新面板、不遮挡 Timeline）。
 *
 * ## 空数据模式（必须保留）
 * 没有候选时**不编造内容**：明确说明「暂无经过验证的 Current Candidate 数据」，
 * 并说明历史研究覆盖到哪一年、实时数据未接入。
 */
export function CurrentCandidateSection({
  list,
  onSelect,
  initialOpenId = null,
}: {
  list: CurrentCandidateListView;
  onSelect: (sel: Selection) => void;
  /** 初始展开的候选（深链 / 测试用）；默认全部收起 */
  initialOpenId?: string | null;
}) {
  const [openId, setOpenId] = useState<string | null>(initialOpenId);

  return (
    <div className="ctl2-layer ccs-layer" aria-label="当前研究候选">
      <h4 className="ctl2-layer-title">
        当前研究候选
        <span className="ctl2-badge">Current Research Discovery</span>
      </h4>

      {/* fixture 强提示：示例数据绝不冒充真实研究数据 */}
      {list.fixture && (
        <p className="ccs-fixture" role="status">
          <strong>示例 fixture（非真实研究数据）</strong>
          本页当前展示的是协议示例，用于验证 Temporal Firewall / 阶段推断 / 相似度链路，
          <strong>不是</strong>任何真实研究对象，也不构成投资依据。
        </p>
      )}

      <p className="ctl2-note">{CURRENT_CANDIDATE_HINT}</p>

      {/* 快照日与滞后提示：明确「这不是实时」 */}
      {list.snapshotDate ? (
        <p className="ccs-meta">
          研究快照日：<em>{list.snapshotDate}</em>
          {list.researchCoverageUntil != null && <> · 历史研究覆盖至 {list.researchCoverageUntil}</>}
          {' · '}数据来源：离线研究生成（非实时行情 / 非实时新闻）
          {list.stale && list.stalenessDays !== null && (
            <span className="ccs-stale">（快照距今 {list.stalenessDays} 天，不是当前市场状态）</span>
          )}
        </p>
      ) : (
        <p className="ctl2-note ctl2-note-empty">
          数据集缺少 snapshot_date —— Temporal Firewall 无法工作，因此本区域不展示任何候选。
        </p>
      )}

      {/* ---------- 空数据模式：诚实空态，不编造 ---------- */}
      {list.views.length === 0 ? (
        <div className="ccs-empty" role="note">
          <p className="ccs-empty-line">当前暂无经过验证的 Current Candidate 数据。</p>
          <ul className="ccs-empty-list">
            <li>历史研究覆盖至：{list.researchCoverageUntil ?? '未知'}</li>
            <li>当前市场实时数据：未接入</li>
          </ul>
          <p className="ccs-empty-line">
            因此本页面不对当前年份的 Theme 作未经验证的判断，也不使用历史年份的数据冒充当前状态。
            —— 这是正常结果，不是错误。
          </p>
        </div>
      ) : (
        <ol className="ccs-list">
          {list.views.map((v, idx) => (
            <CandidateRow
              key={v.candidate.candidate_id}
              view={v}
              index={idx + 1}
              open={openId === v.candidate.candidate_id}
              onToggle={() =>
                setOpenId(openId === v.candidate.candidate_id ? null : v.candidate.candidate_id)
              }
              onSelect={onSelect}
            />
          ))}
        </ol>
      )}

      {list.issues.length > 0 && (
        <details className="ccs-issues">
          <summary>数据解析告警（{list.issues.length} 条）</summary>
          <ul>
            {list.issues.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

/** 单条候选：概览 + 就地展开详情 */
function CandidateRow({
  view,
  index,
  open,
  onToggle,
  onSelect,
}: {
  view: CurrentCandidateView;
  index: number;
  open: boolean;
  onToggle: () => void;
  onSelect: (sel: Selection) => void;
}) {
  const c = view.candidate;
  const highCount = view.similarity.results.filter((r) => r.tier === 'HIGH').length;
  const midCount = view.similarity.results.filter((r) => r.tier === 'MEDIUM').length;

  return (
    <li className={`ccs-item${open ? ' open' : ''}`}>
      <button className="ccs-head" onClick={onToggle} aria-expanded={open}>
        <span className="ccs-idx">{String(index).padStart(2, '0')}</span>
        <span className="ccs-name">
          {c.candidate_id.startsWith('FX-') && <em className="ccs-fx">示例</em>}
          {c.display_name}
        </span>
        <span className={`ccs-phase ph-${view.phase.toLowerCase()}`}>{view.phaseLabel}</span>
        <span className="ccs-status">{view.gate.effectiveLabel}</span>
        <span className={`ccs-ev ev-${view.summary.level.toLowerCase()}`}>
          证据：{AGGREGATE_LEVEL_LABEL[view.summary.level]}
        </span>
        <span className="ccs-sim">
          {view.similarity.insufficient
            ? '历史相似：暂无足够相似阶段'
            : `历史相似：${view.similarity.results.length} 条` +
              (highCount || midCount ? `（高 ${highCount} / 中 ${midCount}）` : '')}
        </span>
        {/* Temporal Firewall 在概览层即可见（透明性：不隐藏被隔离的证据） */}
        {view.summary.excludedCount > 0 && (
          <span className="ccs-fw-badge">已隔离 {view.summary.excludedCount} 条快照后证据</span>
        )}
        <span className="ccs-caret">{open ? '收起' : '展开'}</span>
      </button>

      <p className="ccs-oneliner">{view.oneLiner}</p>

      {c.candidate_status !== view.gate.effective && (
        <p className="ccs-demote">
          研究声明状态为「{CANDIDATE_STATUS_LABEL[c.candidate_status]}」，
          但未通过产品端状态门 → 显示为「{view.gate.effectiveLabel}」。
        </p>
      )}

      {open && <CandidateDetail view={view} onSelect={onSelect} />}
    </li>
  );
}

function CandidateDetail({
  view,
  onSelect,
}: {
  view: CurrentCandidateView;
  onSelect: (sel: Selection) => void;
}) {
  const c = view.candidate;
  const inferred = view.inference.phase;
  const declared = view.inference.declared;

  return (
    <div className="ccs-detail">
      {/* ---------- Why now? ---------- */}
      <section className="ccs-sec">
        <h5>Why now?（为什么现在研究它）</h5>
        <p>{c.core_narrative}</p>
        {c.phase_window.start && (
          <p className="ccs-dim">
            候选阶段窗口起点：{c.phase_window.start}
            {c.phase_window.end ? ` ~ ${c.phase_window.end}` : '（尚未结束）'}
          </p>
        )}
        {c.macro_theme && <p className="ccs-dim">所属 Macro Theme：{c.macro_theme}</p>}
      </section>

      {/* ---------- Current Evidence ---------- */}
      <section className="ccs-sec">
        <h5>Current Evidence（证据台账）</h5>
        <p className="ccs-dim">
          证据充分度：{AGGREGATE_LEVEL_LABEL[view.summary.level]} ·
          可用 {view.summary.admissibleCount} 条 ·
          隔离 {view.summary.excludedCount} 条 ·
          日期未知 {view.summary.undatedCount} 条
        </p>
        {view.summary.basis.length > 0 && (
          <ul className="ccs-basis">
            {view.summary.basis.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        )}
        {view.ledger.admissible.length === 0 ? (
          <p className="ccs-none">快照内没有任何可用证据 —— 不做判断（不编造）。</p>
        ) : (
          <ul className="ccs-ev-list">
            {view.ledger.admissible.map(({ item }) => (
              <li key={item.evidence_id}>
                <span className="ccs-ev-id">{item.evidence_id}</span>
                <span className="ccs-ev-src">{EVIDENCE_SOURCE_LABEL[item.source_type]}</span>
                <span className="ccs-ev-str">{EVIDENCE_STRENGTH_LABEL[item.evidence_strength]}</span>
                <span className="ccs-ev-dir">{EVIDENCE_DIRECTION_LABEL[item.direction ?? 'UNKNOWN']}</span>
                <span className="ccs-ev-date">{item.source_date ?? item.event_date ?? '日期未知'}</span>
                <span className="ccs-ev-claim">{item.claim}</span>
                {item.source_title && <span className="ccs-ev-title">{item.source_title}</span>}
              </li>
            ))}
          </ul>
        )}

        {/* Temporal Firewall 的可见性：被隔离的证据必须明示，且说明不参与判断 */}
        {view.ledger.excluded.length > 0 && (
          <div className="ccs-firewall" role="note">
            <strong>Temporal Firewall · 已隔离 {view.ledger.excluded.length} 条</strong>
            <ul>
              {view.ledger.excluded.map(({ item }) => (
                <li key={item.evidence_id}>
                  {item.evidence_id}（{item.source_date ?? item.event_date} ·
                  {TEMPORAL_LABEL.AFTER_SNAPSHOT}）—— {item.claim}
                </li>
              ))}
            </ul>
            <p>这些证据晚于研究快照日，不得参与阶段推断、状态判定与相似度检索。</p>
          </div>
        )}
        {view.ledger.undated.length > 0 && (
          <p className="ccs-none">另有 {view.ledger.undated.length} 条证据日期未知，按不可用处理。</p>
        )}
        {view.ledger.declaredMismatch.length > 0 && (
          <ul className="ccs-basis">
            {view.ledger.declaredMismatch.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        )}
      </section>

      {/* ---------- Possible Drivers ---------- */}
      <section className="ccs-sec">
        <h5>Possible Drivers（可能相关因素）</h5>
        {view.drivers.length === 0 && c.drivers.length === 0 ? (
          <p className="ccs-none">未标注、且无可派生来源（不推断）。</p>
        ) : (
          <ul className="ccs-chips">
            {c.drivers.map((d) => (
              <li key={d.category} className="ccs-chip">
                {d.category}
                {d.note ? `：${d.note}` : ''}
              </li>
            ))}
          </ul>
        )}
        <p className="ccs-dim">
          语义为「可能相关因素」，不是因果结论、不是交易建议。
        </p>
      </section>

      {/* ---------- Estimated Phase ---------- */}
      <section className="ccs-sec">
        <h5>Estimated Phase（阶段推断）</h5>
        <p className="ccs-dim">
          推导阶段：<strong>{PHASE_LABEL[inferred]}</strong>
          {declared !== inferred && <> · 研究声明：{PHASE_LABEL[declared]}（不一致，两者并列保留）</>}
          {' · '}命中规则：<code>{view.inference.matchedRule}</code>
          {' · '}证据覆盖度：{view.coverage.label}（{view.coverage.known}/{view.coverage.total} 维度）
        </p>
        <p className="ccs-dim">{view.inference.ruleLabel}</p>

        <table className="ccs-matrix">
          <thead>
            <tr>
              <th>维度</th>
              <th>水平</th>
              <th>来源</th>
              <th>依据</th>
            </tr>
          </thead>
          <tbody>
            {PHASE_DIMENSIONS.map((d) => {
              const e = view.matrix[d];
              return (
                <tr key={d}>
                  <td>{DIMENSION_LABEL[d]}</td>
                  <td>{SIGNAL_LEVEL_LABEL[e.level]}</td>
                  <td>{ORIGIN_LABEL[e.origin]}</td>
                  <td className="ccs-matrix-basis">{e.basis}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <details className="ccs-rules">
          <summary>推断依据（逐条）</summary>
          <ul>
            {view.inference.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </details>
      </section>

      {/* ---------- Historical Similar Cases ---------- */}
      <section className="ccs-sec">
        <h5>Historical Similar Cases（历史相似阶段 · Lifecycle Lens）</h5>
        <p className="ccs-dim">{CURRENT_SIMILARITY_DISCLAIMER}</p>
        {view.similarity.insufficient ? (
          <p className="ccs-none">{view.similarity.note}</p>
        ) : (
          <ul className="ccs-sim-list">
            {view.similarity.results.map((r) => (
              <li key={r.campaign_id} className={`ccs-sim-item tier-${r.tier.toLowerCase()}`}>
                <div className="ccs-sim-head">
                  <span className="ccs-sim-title">{r.title}</span>
                  <span className="ccs-sim-year">{r.year}</span>
                  <span className="ccs-tier">
                    {TIER_LABEL[r.tier]} <span className="ccs-stars">{r.stars}</span>
                  </span>
                </div>
                <dl className="ccs-sim-kv">
                  <dt>当时阶段</dt>
                  <dd>
                    {r.phaseLabel}（{r.phaseMatchLabel}
                    {r.matchedStage ? ` ${r.matchedStage.start}~${r.matchedStage.end}` : ''}）
                  </dd>
                  <dt>Pattern</dt>
                  <dd>{r.pattern}</dd>
                  <dt>Drivers</dt>
                  <dd>{r.drivers.length > 0 ? r.drivers.join(' / ') : '未标注'}</dd>
                  <dt>叙事类型</dt>
                  <dd>
                    {r.narrativeTypes.length > 0
                      ? r.narrativeTypes.map((n) => NARRATIVE_TYPE_LABEL[n]).join('、')
                      : '未标注（该层不参与）'}
                  </dd>
                  {r.driverNotes.length > 0 && (
                    <>
                      <dt>当时归因</dt>
                      <dd>{r.driverNotes.join('；')}</dd>
                    </>
                  )}
                  <dt>后来结束</dt>
                  <dd>
                    {r.terminalPhaseLabel}（区间 {r.start} ~ {r.end}）
                  </dd>
                  <dt>{PRE_OBSERVATION_LABEL}</dt>
                  <dd>
                    {r.preObservation ? (
                      <>
                        {r.preObservation.start} ~ {r.preObservation.end}
                        （形成日 {r.preObservation.formation} · 锚点 {r.preObservation.formationAnchor}）
                        <span className="ccs-dim"> {PRE_OBSERVATION_HINT}</span>
                      </>
                    ) : (
                      '无法推导（不编造）'
                    )}
                  </dd>
                </dl>
                <div className="ccs-sim-why">
                  <span className="ccs-dim">为什么类似：</span>
                  <ul>
                    {r.reasons.map((x) => (
                      <li key={x}>{x}</li>
                    ))}
                  </ul>
                </div>
                <button
                  className="ccs-open"
                  onClick={() => onSelect({ kind: 'campaign', id: r.campaign_id })}
                >
                  查看完整历史案例 →
                </button>
              </li>
            ))}
          </ul>
        )}
        {view.similarity.excludedByFirewall > 0 && (
          <p className="ccs-dim">
            另有 {view.similarity.excludedByFirewall} 条历史对象在本次快照时点尚未结束，
            已按 Temporal Firewall 排除（否则会引用未来信息）。
          </p>
        )}
      </section>

      {/* ---------- What to research next? ---------- */}
      <section className="ccs-sec">
        <h5>What to research next?（研究问题）</h5>
        <ol className="ccs-questions">
          {view.researchQuestions.map((q) => (
            <li key={q}>{q}</li>
          ))}
        </ol>
        <p className="ccs-dim">
          这些是<strong>研究问题</strong>（要去查什么资料），不是买卖问题、不是操作建议。
        </p>
      </section>

      {/* ---------- Uncertainty / Conflicts ---------- */}
      <section className="ccs-sec">
        <h5>Uncertainty / Conflicts（未知与冲突）</h5>
        {c.uncertainty_notes.length > 0 ? (
          <ul className="ccs-notes">
            {c.uncertainty_notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        ) : (
          <p className="ccs-none">未声明不确定性（这本身也是一个待补的字段）。</p>
        )}
        {view.conflicts.length > 0 ? (
          <ul className="ccs-conflicts">
            {view.conflicts.map((x) => (
              <li key={x.note}>
                <span className="ccs-conflict-kind">{CONFLICT_KIND_LABEL[x.kind]}</span>
                {x.note}
              </li>
            ))}
          </ul>
        ) : (
          <p className="ccs-dim">未检测到证据方向冲突。</p>
        )}
      </section>

      {/* ---------- 为什么它仍然只是 Candidate ---------- */}
      <section className="ccs-sec">
        <h5>为什么它现在仍是 Candidate，而不是正式 Theme / Campaign</h5>
        <ul className="ccs-criteria">
          {view.upgradeCriteria.map((crit) => (
            <li key={crit.id} className={crit.met ? 'met' : 'unmet'}>
              <span className="ccs-crit-mark">{crit.met ? '✓' : '✗'}</span>
              <span className="ccs-crit-label">{crit.label}</span>
              <span className="ccs-crit-detail">{crit.detail}</span>
            </li>
          ))}
        </ul>
        {view.missingDimensions.length > 0 && (
          <p className="ccs-dim">
            尚未达到「明确」水平的维度：
            {view.missingDimensions.map((d) => DIMENSION_LABEL[d]).join('、')}
          </p>
        )}
        <ul className="ccs-basis">
          {view.gate.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <p className="ccs-dim">
          Current Candidate 是研究对象，不是已验证 Theme；升级为正式 Campaign 属于 Research 的独立评审流程。
        </p>
      </section>
    </div>
  );
}
