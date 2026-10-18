/**
 * 当前研究对象 ↔ 历史对象 **生命周期并排对照**（ThreeC 1.3 P2 · v0.8 交付）。
 *
 * ## 这是什么
 * 用户看着「本期研究快照」里的某个**当前研究对象**，想知道「它的阶段、和历史案例比处在什么位置」。
 * 本组件把**当前侧自述阶段**与**若干历史对象的阶段序列**并排列出来。
 *
 * ## ★★ 这不是什么（硬约束，UI 上必须原样出现）
 * - **不是结构对应**：结构对应**唯一**入口是冻结 SA（`StructuralAnalogySection`）。
 * - **不是进度 / 领先 / 落后 / 快慢比较**：不计算对齐比例、不排序、不做时间轴归一化。
 * - **不补数据**：缺失阶段、开放区间（`end = null`）、`UNKNOWN` **原样显示** ——
 *   「未记录 ≠ 未发生」；「开放区间 = 研究未给出结束日」。
 * - **不引入评分 / 排名 / 概率 / 预测**。
 *
 * ## 数据来源（全部复用现有链路，不新建管线）
 * - 当前侧：`CurrentCandidate.attention_state` / `phase_window`（研究侧自述）
 * - 历史侧序列：`dataSource.yearData(y).campaigns[].lifecycle`（Contract v1.2 导出字段）
 * - 历史对象范围与阶段语境的**权威口径**：冻结 SA 的 `dimensions.lifecycle`
 *   （`candidate_phase` / `historical_stage_at_comparable_point` / `forbidden_comparison`）
 *   ★ 本组件**只引用**它，不重算、不改写。
 */
import { useEffect, useMemo, useState } from 'react';

import {
  DIMENSION_STATUS_LABEL,
  INDETERMINATE_DIMENSION_STATUSES,
  STRUCTURAL_STATUS_LABEL,
  loadStructuralAnalogyDataset,
  type StructuralAnalogyDataset,
} from '../../data/timeline/structuralAnalogy';
import { PHASE_LABEL, phaseOfStage } from '../../data/timeline/researchAttention';
import { formatDuration, stageDurationOf } from '../../data/timeline/lifecycleDuration';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import type { CurrentCandidate } from '../../data/timeline/currentCandidate';

/** 一行对照：一个历史对象 + SA 对它的 lifecycle 语境 */
export interface LifecycleComparisonRow {
  cycleId: string;
  kind: 'campaign' | 'research_candidate';
  structuralStatus: string;
  structuralStatusLabel: string;
  /** 冻结 SA 的 lifecycle 维度（原样透传，不改写） */
  saLifecycle: {
    status: string;
    statusLabel: string;
    candidatePhase: string | null;
    historicalStageAtComparablePoint: string | null;
    forbiddenComparison: string | null;
  };
  /** 历史对象标题（来自 dataSource；找不到 → null，UI 用 id） */
  title: string | null;
  /** 历史阶段序列（导出原序，**不重排**） */
  lifecycle: { stage: string; start: string | null; end: string | null; precision: string }[];
}

/** ★★ 组件自带的语义声明（`MarketingSection` — 红线的 UI 载体，必须随组件一起渲染） */
export const LIFECYCLE_COMPARISON_DISCLAIMER =
  '★★ **并排展示，不是结论**：这里只把「当前对象的研究自述阶段」与「历史对象的阶段序列」'
  + '放在一起，便于**看出顺序、时长与日期差异**。'
  + '它**不**说明谁领先/落后/更快/更慢，**也 不 是 结构对应** —— '
  + '结构对应唯一入口是上方冻结 SA 解释。'
  + '缺失阶段、开放区间与 UNKNOWN 均**原样显示**（未记录 ≠ 未发生；开放区间 = 研究未给出结束日）。';

/** 阶段标签：先查 ResearchPhase 口径（11 阶段 → 8 相位），查不到回落小写 lifecycle 标签 */
function stageLabel(stage: string): string {
  const phase = phaseOfStage(stage);
  return PHASE_LABEL[phase] ?? stage;
}

function phaseWindowLabel(w: { start: string | null; end: string | null }): string {
  return `${w.start ?? '（未记录）'} → ${w.end ?? '开放（研究未给出结束日）'}`;
}

export function LifecycleComparisonSection({
  candidate,
  dataSource,
  onSelect,
  dataset: injectedDataset,
}: {
  candidate: CurrentCandidate;
  dataSource?: TimelineDataSource | null;
  /**
   * ★ 刻意用 `onSelect`（而非 SA 的 `onOpenHistoricalCase`）：本区是**并排展示**，
   *   **不**构成结构对应声明 —— 因此打开历史案例时**不附带** SA 上下文。
   */
  onSelect?: (sel: { kind: 'campaign'; id: string }) => void;
  /** 显式注入 SA 数据集（测试 / 已加载场景）；缺省时按需动态加载。 */
  dataset?: StructuralAnalogyDataset;
}) {
  const [dataset, setDataset] = useState<StructuralAnalogyDataset | null>(injectedDataset ?? null);
  const [state, setState] = useState<'loading' | 'ready' | 'failed'>(
    injectedDataset ? 'ready' : 'loading');
  /** 默认只列 SA 判为「结构支持」的历史对象；需要时可展开全部 */
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (injectedDataset) { setDataset(injectedDataset); setState('ready'); return; }
    let alive = true;
    setState('loading');
    loadStructuralAnalogyDataset()
      .then((ds) => { if (alive) { setDataset(ds); setState('ready'); } })
      .catch(() => { if (alive) setState('failed'); });
    return () => { alive = false; };
  }, [injectedDataset]);

  /** 历史对象索引：id → {title, lifecycle}（89 个对象，挂载时扫一次即可） */
  const historicalIndex = useMemo(() => {
    const m = new Map<string, { title: string; lifecycle: LifecycleComparisonRow['lifecycle'] }>();
    if (!dataSource) return m;
    for (const y of dataSource.years()) {
      for (const c of dataSource.yearData(y).campaigns) {
        m.set(c.campaign_id, {
          title: c.title,
          lifecycle: (c.lifecycle ?? []).map((p) => ({
            stage: p.stage, start: p.start, end: p.end, precision: p.precision,
          })),
        });
      }
    }
    return m;
  }, [dataSource]);

  const rows = useMemo<LifecycleComparisonRow[]>(() => {
    if (!dataset) return [];
    const cand = dataset.candidates.find((c) => c.candidateId === candidate.candidate_id);
    if (!cand) return [];
    return cand.explanations.map((e) => {
      // ★ v0.8：读**解析后视图**的 camelCase 字段（raw artifact 是 snake_case，
      //   直接读 raw 会全部得到 null —— 实测踩到过）。
      const lc = e.dimensions.lifecycle;
      const hist = historicalIndex.get(e.identity.historicalCycleId);
      return {
        cycleId: e.identity.historicalCycleId,
        kind: e.identity.historicalObjectKind,
        structuralStatus: e.structuralStatus,
        structuralStatusLabel: STRUCTURAL_STATUS_LABEL[e.structuralStatus] ?? e.structuralStatus,
        saLifecycle: {
          status: lc.status,
          statusLabel: DIMENSION_STATUS_LABEL[lc.status] ?? lc.status,
          candidatePhase: lc.candidatePhase ?? null,
          historicalStageAtComparablePoint: lc.historicalStageAtComparablePoint ?? null,
          forbiddenComparison: lc.forbiddenComparison || null,
        },
        title: hist?.title ?? null,
        lifecycle: hist?.lifecycle ?? [],
      };
    });
  }, [dataset, candidate.candidate_id, historicalIndex]);

  const supported = rows.filter((r) => r.structuralStatus === 'STRUCTURAL_SUPPORTED');
  const visible = showAll ? rows : supported;
  const unrecordedStages = useMemo(
    () => '（该历史对象未登记阶段序列）',
    [],
  );

  return (
    <section className="lcc" aria-label="生命周期对照">
      <h5 className="lcc-title">
        生命周期对照<span className="lcc-badge">并排展示 · 非结构对应</span>
      </h5>

      <p className="lcc-disc">{LIFECYCLE_COMPARISON_DISCLAIMER.split('**').map((seg, i) =>
        i % 2 === 1 ? <strong key={i}>{seg}</strong> : <span key={i}>{seg}</span>)}</p>

      {/* 当前侧（研究自述）—— 一行固定展示，作为对照的左列基准 */}
      <div className="lcc-current">
        <div className="lcc-current-head">
          <strong>当前研究对象</strong>
          <span className="lcc-current-id">{candidate.candidate_id}</span>
        </div>
        <dl className="lcc-current-kv">
          <dt>研究自述阶段</dt>
          <dd>{PHASE_LABEL[candidate.attention_state] ?? candidate.attention_state}
            <span className="lcc-raw">（{candidate.attention_state}）</span></dd>
          <dt>阶段窗口</dt>
          <dd>{phaseWindowLabel(candidate.phase_window)}</dd>
        </dl>
        <p className="lcc-current-note">
          ★ 以上是<strong>研究侧自述</strong>（attention_state / phase_window），不是从行情推导的结论；
          窗口结束日为 null 表示<strong>研究未给出结束日</strong>（开放区间）。
        </p>
      </div>

      {state === 'loading' && <p className="lcc-state">正在载入冻结 SA 解释…</p>}
      {state === 'failed' && (
        <p className="lcc-state lcc-state-warn">
          ★ 冻结 SA 解释<strong>未能载入</strong> —— 无法给出历史对象范围。这不代表「没有历史对照」，
          只代表本次没能取到；请稍后重试或查看上方结构对应区。
        </p>
      )}
      {state === 'ready' && !dataSource && (
        <p className="lcc-state lcc-state-warn">
          ★ 当前数据源<strong>未提供</strong> Timeline（verified 源）→ 无法读取历史阶段序列。
          上方冻结 SA 仍给出结构对应结论；本节仅做阶段展示，故暂不可用。
        </p>
      )}

      {state === 'ready' && dataSource && (
        <>
          {rows.length === 0 && (
            <p className="lcc-state">
              冻结 SA 里没有该候选的解释 → 无历史对象可对照。
            </p>
          )}

          {rows.length > 0 && (
            <>
              <div className="lcc-toolbar">
                <label className="lcc-toggle">
                  <input type="checkbox" checked={showAll}
                         onChange={(e) => setShowAll(e.target.checked)} />
                  显示全部 {rows.length} 个历史对象（默认只列 SA 判为「结构支持」的
                  {supported.length} 个）
                </label>
              </div>

              {visible.length === 0 && (
                <p className="lcc-state">
                  ★ 该候选<strong>没有</strong> SA 判为「结构支持」的历史对象（共 {rows.length} 个，
                  状态分布见上方结构对应区）。勾选上方复选框可查看全部。
                </p>
              )}

              <table className="lcc-table">
                <caption>
                  左列 = <strong>历史对象</strong>（含结构状态与入口）·
                  第二列 = <strong>当前研究对象</strong>（研究自述阶段）·
                  第三列 = 该历史对象的<strong>阶段序列</strong>（导出原序 + 起止 + 可计算时给持续时长）·
                  末列 = 冻结 SA 的 lifecycle 维度（原样引用，非本组件计算）
                </caption>
                <thead>
                  <tr>
                    <th scope="col">历史对象</th>
                    <th scope="col">当前侧（自述）</th>
                    <th scope="col">历史阶段序列</th>
                    <th scope="col">冻结 SA · lifecycle 维度</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((r) => (
                    <tr key={r.cycleId}>
                      <td>
                        <code className="lcc-id">{r.cycleId}</code>
                        {r.title && <span className="lcc-htitle">{r.title}</span>}
                        <span className={`lcc-st lcc-st-${r.structuralStatus.toLowerCase()}`}>
                          {r.structuralStatusLabel}
                        </span>
                        {onSelect && r.kind === 'campaign' && (
                          <button type="button" className="lcc-open"
                                  onClick={() => onSelect({ kind: 'campaign', id: r.cycleId })}>
                            打开该历史案例
                          </button>
                        )}
                      </td>
                      <td className="lcc-cur">
                        {PHASE_LABEL[candidate.attention_state] ?? candidate.attention_state}
                        <span className="lcc-raw">（{candidate.attention_state}）</span>
                        <span className="lcc-win">{phaseWindowLabel(candidate.phase_window)}</span>
                      </td>
                      <td>
                        {r.lifecycle.length === 0 ? (
                          <span className="lcc-missing">{unrecordedStages}</span>
                        ) : (
                          <ol className="lcc-stages">
                            {r.lifecycle.map((p, i) => {
                              const dur = stageDurationOf(p.start, p.end, p.precision);
                              return (
                                <li key={`${p.stage}-${i}`}>
                                  <strong>{stageLabel(p.stage)}</strong>
                                  <span className="lcc-raw">（{p.stage}）</span>
                                  <span className="lcc-dates">
                                    {p.start ?? '起点未记录'} → {p.end ?? '开放区间'}
                                  </span>
                                  <span className="lcc-prec">{p.precision}</span>
                                  {/* ★ v0.9：能算才给时长；不能算就说明原因，**不推断** */}
                                  <span
                                    className={`lcc-dur${dur.ok ? '' : ' lcc-dur-na'}`}
                                    data-duration={dur.ok ? 'ok' : dur.reason}
                                  >
                                    {dur.ok ? `持续 ${formatDuration(dur)}` : dur.label}
                                  </span>
                                </li>
                              );
                            })}
                          </ol>
                        )}
                      </td>
                      <td>
                        <span className={`lcc-dim lcc-dim-${r.saLifecycle.status.toLowerCase()}`}>
                          {r.saLifecycle.statusLabel}
                        </span>
                        {INDETERMINATE_DIMENSION_STATUSES.includes(
                          r.saLifecycle.status as 'UNKNOWN',
                        ) && <span className="lcc-indet">（不确定，<strong>不得</strong>读作「不对应」）</span>}
                        <dl className="lcc-sa-kv">
                          <dt>SA 记载的候选阶段</dt>
                          <dd>{r.saLifecycle.candidatePhase ?? '（未记载）'}</dd>
                          <dt>历史在可比观测点的阶段</dt>
                          <dd>{r.saLifecycle.historicalStageAtComparablePoint ?? '（未记载）'}</dd>
                        </dl>
                        {r.saLifecycle.forbiddenComparison && (
                          <p className="lcc-forbid">
                            ★ SA 明文禁止：
                            {/* ★ 源数据文本自带 `**`，按强调渲染（否则会露出两个星号） */}
                            {r.saLifecycle.forbiddenComparison.split('**').map((seg, i) =>
                              i % 2 === 1 ? <strong key={i}>{seg}</strong> : <span key={i}>{seg}</span>)}
                          </p>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
    </section>
  );
}
