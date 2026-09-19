/**
 * Structural Analogy Section —— Product UI Integration v0.1（ROADMAP Step 3）。
 *
 * ## 定位
 * `structuralAnalogy.ts`（Adapter，只读消费 Explanation Artifact v0.2）
 * → **Current Candidate 内的「Structural Analogy」视图**。
 *
 * 回答：**「当前结构与哪些历史结构存在对应关系？为什么？哪里不同？」**
 *
 * ## 这不是什么（硬约束）
 * - **不是**相似度 / 排名 / 评分 / 概率 / 预测 / 买卖信号。
 * - **不重新计算** Structural Analogy，**不重新判断**任何维度 —— 全部状态直接来自 Adapter。
 * - **不按 Structural Status 排序**：默认保持 Adapter 的 **stable identity order**
 *   （artifact 原始顺序 = `historical_cycle_id` 升序）。状态只作为**筛选**，不作为排序。
 *
 * ## 状态语义（不得压缩）
 * - `UNKNOWN` / `NOT_AVAILABLE` **≠** `MISMATCH`
 * - `PARTIAL` **≠** `MATCH`
 * - `THEME_ONLY` **≠** `STRUCTURAL_SUPPORTED`
 * - `CROSS_MACRO_THEME` **≠** 「不相似」（Theme Relation 仅 metadata）
 *
 * ## 加载策略（Performance Gate v0.1）
 * Explanation Artifact（488 KB）**不进首屏 bundle** —— 组件挂载时才动态加载独立 chunk。
 * 加载中显示「正在加载」，**不显示空态**（避免把「尚未加载」误判成「没有结构对应」）。
 *
 * ## 导航
 * - 真实历史 **Campaign** → 提供 Campaign Detail 入口。
 * - **Research Candidate** → **不提供** Campaign Detail 入口（它不在 `campaigns` 集合内），
 *   并明确标注其历史对象类型。
 */

import { useEffect, useMemo, useState } from 'react';

import type { Selection } from '../Timeline/Timeline';
import type { HistoricalCaseAnalogyContext } from '../../data/timeline/historicalCase';
import {
  DIMENSION_LABEL,
  DIMENSION_STATUS_LABEL,
  EMPTY_STRUCTURAL_ANALOGY_DATASET,
  STRUCTURAL_STATUS_LABEL,
  THEME_RELATION_LABEL,
  explanationCount,
  loadStructuralAnalogyDataset,
  isIndeterminate,
  structuralAnalogyForCandidate,
  type DimensionKey,
  type DriverStatus,
  type StructuralAnalogyDataset,
  type StructuralAnalogyExplanationView,
  type StructuralStatus,
} from '../../data/timeline/structuralAnalogy';

/* ================= 文案（研究措辞，不做营销化改写） ================= */

const KIND_LABEL = {
  campaign: '历史 Campaign',
  research_candidate: '历史 Research Candidate',
} as const;

const FILTERS: { key: StructuralStatus | 'ALL'; label: string }[] = [
  { key: 'ALL', label: '全部' },
  { key: 'STRUCTURAL_SUPPORTED', label: STRUCTURAL_STATUS_LABEL.STRUCTURAL_SUPPORTED },
  { key: 'STRUCTURAL_PARTIAL', label: STRUCTURAL_STATUS_LABEL.STRUCTURAL_PARTIAL },
  { key: 'THEME_ONLY', label: STRUCTURAL_STATUS_LABEL.THEME_ONLY },
  { key: 'INSUFFICIENT_EVIDENCE', label: STRUCTURAL_STATUS_LABEL.INSUFFICIENT_EVIDENCE },
  { key: 'NO_VALID_CORRESPONDENCE', label: STRUCTURAL_STATUS_LABEL.NO_VALID_CORRESPONDENCE },
];

/**
 * 默认一次展示的历史对象条数（**渐进披露**，不是排名）。
 * 17 条全部展开会产生约 83 KB 标记与过长的信息流 → 默认只展示前 N 条（保持稳定顺序）。
 */
const DEFAULT_VISIBLE = 6;

const DIMENSION_ORDER: DimensionKey[] = [
  'lifecycle',
  'mechanism_driver',
  'evidence_sequence',
  'event_structure',
];

/** 该维度当前状态（用于逐维展示）。**纯映射，不做判定**。 */
export function dimensionStatusOf(
  e: StructuralAnalogyExplanationView,
  key: DimensionKey,
): DriverStatus {
  switch (key) {
    case 'lifecycle':
      return e.dimensions.lifecycle.status;
    case 'mechanism_driver':
      return e.dimensions.mechanismDriver.status;
    case 'evidence_sequence':
      return e.dimensions.evidenceSequence.status;
    default:
      return e.dimensions.eventStructure.status;
  }
}

/** 从 `background_sources` 读取 macro theme（**纯展示查找，非判定**）。 */
export function macroThemeOf(e: StructuralAnalogyExplanationView): string | null {
  for (const b of e.backgroundSources) {
    if (b.source === 'historical_macro_theme' && typeof b.value === 'string') return b.value;
  }
  return null;
}

/** 该维度的**直接依据**条数（用于展示「有据可查」）。 */
function evidenceCountOf(e: StructuralAnalogyExplanationView, key: DimensionKey): number {
  switch (key) {
    case 'lifecycle':
      return e.dimensionEvidence.lifecycle.length;
    case 'mechanism_driver':
      return e.dimensionEvidence.mechanismDriver.length;
    case 'evidence_sequence':
      return e.dimensionEvidence.evidenceSequence.length;
    default:
      return e.dimensionEvidence.eventStructure.length;
  }
}

/**
 * 按 structural status 筛选（**筛选，不是排序**）。
 * 返回顺序 = 传入顺序（Adapter 的 stable identity order）。
 */
export function filterExplanations(
  explanations: StructuralAnalogyExplanationView[],
  filter: StructuralStatus | 'ALL',
): StructuralAnalogyExplanationView[] {
  if (filter === 'ALL') return explanations;
  return explanations.filter((e) => e.structuralStatus === filter);
}

/* ================= 组件 ================= */

export function StructuralAnalogySection({
  candidateId,
  onSelect,
  onOpenHistoricalCase,
  dataset: injectedDataset,
  historicalLabelOf,
  initialOpenCycleId = null,
}: {
  candidateId: string;
  onSelect: (sel: Selection) => void;
  /** 打开 Historical Case 时携带 SA 上下文（缺省回退到 `onSelect`，不带上下文）。 */
  onOpenHistoricalCase?: (sel: Selection, ctx: HistoricalCaseAnalogyContext) => void;
  /** 显式注入数据集（测试 / 已加载场景）；**缺省时按需动态加载**。 */
  dataset?: StructuralAnalogyDataset;
  /** 可选：历史对象显示名（由调用方从 timeline 数据源解析）；缺省回退到稳定 identity。 */
  historicalLabelOf?: (cycleId: string) => string | null;
  /** 初始展开的历史对象（测试 / 深链用）；默认全部收起 */
  initialOpenCycleId?: string | null;
}) {
  const [loaded, setLoaded] = useState<StructuralAnalogyDataset | null>(injectedDataset ?? null);
  const [loadState, setLoadState] = useState<'idle' | 'loading' | 'ready' | 'failed'>(
    injectedDataset ? 'ready' : 'idle',
  );

  // 按需加载（仅在未注入 dataset 时触发一次）
  useEffect(() => {
    if (injectedDataset) {
      setLoaded(injectedDataset);
      setLoadState('ready');
      return;
    }
    let alive = true;
    setLoadState('loading');
    loadStructuralAnalogyDataset()
      .then((ds) => {
        if (!alive) return;
        setLoaded(ds);
        setLoadState('ready');
      })
      .catch(() => {
        if (!alive) return;
        setLoadState('failed');
      });
    return () => {
      alive = false;
    };
  }, [injectedDataset]);

  const dataset = loaded ?? EMPTY_STRUCTURAL_ANALOGY_DATASET;

  const candidate = useMemo(
    () => (loadState === 'ready' ? structuralAnalogyForCandidate(dataset, candidateId) : null),
    [dataset, candidateId, loadState],
  );
  const [filter, setFilter] = useState<StructuralStatus | 'ALL'>('ALL');
  const [openId, setOpenId] = useState<string | null>(initialOpenCycleId);
  // 深链 / 测试指定了初始展开项时，若其不在前 N 条内则自动展开全部（否则会「打开了看不见」）
  const [showAll, setShowAll] = useState(() => {
    if (!initialOpenCycleId) return false;
    const idx = (injectedDataset ?? EMPTY_STRUCTURAL_ANALOGY_DATASET).candidates
      .find((c) => c.candidateId === candidateId)
      ?.explanations.findIndex((e) => e.identity.historicalCycleId === initialOpenCycleId);
    return idx !== undefined && idx >= DEFAULT_VISIBLE;
  });

  // ---------- 加载中（**不是空态**，避免误判） ----------
  if (loadState === 'idle' || loadState === 'loading') {
    return (
      <section className="ccs-sec sa-sec" aria-label="Structural Analogy">
        <h5>
          Structural Analogy（结构对应 · 当前 → 历史）
          <span className="sa-tag">研究 · 非预测</span>
        </h5>
        <p className="ccs-none" role="status">正在加载结构对应数据…</p>
      </section>
    );
  }

  // ---------- 加载失败：诚实提示，**不得**退化成「没有结构对应」 ----------
  if (loadState === 'failed') {
    return (
      <section className="ccs-sec sa-sec" aria-label="Structural Analogy">
        <h5>
          Structural Analogy（结构对应 · 当前 → 历史）
          <span className="sa-tag">研究 · 非预测</span>
        </h5>
        <p className="ccs-none" role="alert">
          结构对应数据加载失败 —— 这不代表「没有历史对应」，请刷新重试。
        </p>
      </section>
    );
  }

  // ---------- 诚实空态 ----------
  if (candidate === null || candidate.explanations.length === 0) {
    return (
      <section className="ccs-sec sa-sec" aria-label="Structural Analogy">
        <h5>
          Structural Analogy（结构对应 · 当前 → 历史）
          <span className="sa-tag">研究 · 非预测</span>
        </h5>
        <p className="ccs-none">
          {candidate === null || dataset === EMPTY_STRUCTURAL_ANALOGY_DATASET || dataset.candidates.length === 0
            ? '暂无 Structural Analogy 研究数据 —— 不做判断（不编造）。'
            : '该候选暂无结构对应记录 —— 这不代表「历史上没有类似结构」，只代表当前研究快照内没有可用记录。'}
        </p>
      </section>
    );
  }

  // ★ 默认顺序 = Adapter 提供的 stable identity order（**不按 status 排序**）
  const filtered = filterExplanations(candidate.explanations, filter);
  // ★ 渐进披露：截断**不改变顺序**，被隐藏的是「后面的」，不是「较弱的」
  const visible = showAll ? filtered : filtered.slice(0, DEFAULT_VISIBLE);

  const total = explanationCount(dataset);

  return (
    <section className="ccs-sec sa-sec" aria-label="Structural Analogy">
      <h5>
        Structural Analogy（结构对应 · 当前 → 历史）
        <span className="sa-tag">研究 · 非预测</span>
      </h5>

      <p className="ccs-dim sa-intro">
        回答：<strong>当前结构与哪些历史结构存在对应关系？为什么？哪里不同？</strong>
        对应关系由 Research 侧判定并冻结（Rule Set v0.2），产品只读展示，不重新计算、不评分、不排名。
      </p>

      {/* ---------- 当前研究对象 ---------- */}
      <div className="sa-subject">
        <span className="sa-subject-label">当前研究对象</span>
        <span className="sa-subject-name">{candidate.displayName ?? candidate.candidateId}</span>
        {candidate.macroTheme && <span className="sa-chip">{candidate.macroTheme}</span>}
        {candidate.currentStructuralProfile.currentPhase && (
          <span className="sa-chip">
            当前阶段：{candidate.currentStructuralProfile.currentPhase}
          </span>
        )}
      </div>

      <dl className="sa-current-kv">
        <dt>驱动机制</dt>
        <dd>
          {candidate.currentStructuralProfile.mechanismDrivers.length > 0
            ? candidate.currentStructuralProfile.mechanismDrivers.join(' / ')
            : '未标注'}
        </dd>
        <dt>证据类别</dt>
        <dd>
          {candidate.currentStructuralProfile.evidenceCategories.length > 0
            ? candidate.currentStructuralProfile.evidenceCategories.join(' / ')
            : '未标注'}
        </dd>
      </dl>
      <p className="ccs-dim">
        注：「驱动机制」是机制判断（如 `POLICY_DRIVEN`），「证据类别」是证据来源（如 `POLICY`），两者不是同一维。
      </p>

      {/* ---------- 状态筛选（筛选 ≠ 排序） ---------- */}
      <div className="sa-filters" role="group" aria-label="按结构等级筛选（不是排序）">
        {FILTERS.map((f) => {
          const n =
            f.key === 'ALL'
              ? candidate.explanations.length
              : candidate.explanations.filter((e) => e.structuralStatus === f.key).length;
          return (
            <button
              key={f.key}
              type="button"
              className={`sa-filter${filter === f.key ? ' is-on' : ''}`}
              aria-pressed={filter === f.key}
              onClick={() => setFilter(f.key)}
            >
              {f.label} {n}
            </button>
          );
        })}
      </div>
      <p className="ccs-dim sa-order-note">
        列表按<strong>历史对象稳定顺序</strong>排列（不是从强到弱）；上方按钮仅做筛选。
      </p>

      {/* ---------- 历史结构对应 ---------- */}
      {visible.length === 0 ? (
        <p className="ccs-none">该筛选下没有历史对象。</p>
      ) : (
        <ul className="sa-list">
          {visible.map((e) => (
            <ExplanationItem
              key={e.identity.historicalCycleId}
              e={e}
              open={openId === e.identity.historicalCycleId}
              onToggle={() =>
                setOpenId((cur) => (cur === e.identity.historicalCycleId ? null : e.identity.historicalCycleId))
              }
              onSelect={onSelect}
              onOpenHistoricalCase={onOpenHistoricalCase}
              candidateId={candidate.candidateId}
              candidateName={candidate.displayName}
              historicalLabelOf={historicalLabelOf}
            />
          ))}
        </ul>
      )}

      {filtered.length > DEFAULT_VISIBLE && (
        <div className="sa-more">
          <button
            type="button"
            className="sa-filter"
            onClick={() => setShowAll((v) => !v)}
            aria-expanded={showAll}
          >
            {showAll
              ? `收起（仅显示前 ${DEFAULT_VISIBLE} 个）`
              : `显示全部 ${filtered.length} 个历史对象`}
          </button>
          {!showAll && (
            <span className="ccs-dim">
              按历史对象稳定顺序展示前 {DEFAULT_VISIBLE} 个；<strong>不是</strong>「最强的 {DEFAULT_VISIBLE} 个」。
            </span>
          )}
        </div>
      )}

      <p className="ccs-dim sa-coverage">
        本快照共 {candidate.explanations.length} 个历史对象参与结构比较（数据集合计 {total} 条记录）。
        「证据不足」「无有效结构对应」是<strong>研究结论</strong>，不是预测失败。
      </p>
    </section>
  );
}

/* ================= 单个历史对象 ================= */

function ExplanationItem({
  e,
  open,
  onToggle,
  onSelect,
  onOpenHistoricalCase,
  candidateId,
  candidateName,
  historicalLabelOf,
}: {
  e: StructuralAnalogyExplanationView;
  open: boolean;
  onToggle: () => void;
  onSelect: (sel: Selection) => void;
  onOpenHistoricalCase?: (sel: Selection, ctx: HistoricalCaseAnalogyContext) => void;
  candidateId: string;
  candidateName: string | null;
  historicalLabelOf?: (cycleId: string) => string | null;
}) {
  const cycleId = e.identity.historicalCycleId;
  const label = historicalLabelOf?.(cycleId) ?? null;
  const macroTheme = macroThemeOf(e);
  const unknownDims = DIMENSION_ORDER.filter((k) => isIndeterminate(dimensionStatusOf(e, k)));
  const mismatchDims = DIMENSION_ORDER.filter((k) => dimensionStatusOf(e, k) === 'MISMATCH');

  return (
    <li className={`sa-item status-${e.structuralStatus.toLowerCase().replace(/_/g, '-')}`}>
      <div className="sa-head">
        <button type="button" className="sa-toggle" aria-expanded={open} onClick={onToggle}>
          <span className="sa-caret" aria-hidden="true">
            {open ? '▾' : '▸'}
          </span>
          <span className="sa-name">{label ?? cycleId}</span>
          {label && <span className="sa-id">{cycleId}</span>}
        </button>
        <span className={`sa-status s-${e.structuralStatus.toLowerCase().replace(/_/g, '-')}`}>
          {STRUCTURAL_STATUS_LABEL[e.structuralStatus]}
        </span>
        {e.strictStructuralSupported && <span className="sa-strict">严格口径</span>}
      </div>

      <div className="sa-meta">
        <span className={`sa-kind k-${e.identity.historicalObjectKind}`}>
          {KIND_LABEL[e.identity.historicalObjectKind]}
        </span>
        {macroTheme && <span className="sa-chip">{macroTheme}</span>}
        {/* Theme Relation —— 明确标注为 metadata */}
        <span className="sa-chip sa-theme" title={e.themeRelation.role}>
          {THEME_RELATION_LABEL[e.themeRelation.value]}（背景信息）
        </span>
      </div>

      {/* ---------- 四维（始终可见） ---------- */}
      <ul className="sa-dims">
        {DIMENSION_ORDER.map((k) => {
          const st = dimensionStatusOf(e, k);
          return (
            <li key={k} className={`sa-dim ${isIndeterminate(st) ? 'is-indeterminate' : `is-${st.toLowerCase()}`}`}>
              <span className="sa-dim-label">{DIMENSION_LABEL[k]}</span>
              <span className="sa-dim-status">{DIMENSION_STATUS_LABEL[st]}</span>
            </li>
          );
        })}
      </ul>

      {/* ---------- 展开详情 ---------- */}
      {open && (
        <div className="sa-detail">
          {/* 为什么对应 */}
          <div className="sa-block">
            <h6>为什么对应</h6>
            {e.whySimilar.length === 0 ? (
              <p className="ccs-none">四个结构维度均未形成对应。</p>
            ) : (
              <ul className="sa-why">
                {e.whySimilar.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </div>

          {/* 哪里不同 */}
          <div className="sa-block">
            <h6>哪里不同</h6>
            {e.whyNotSimilar.length === 0 ? (
              <p className="ccs-none">本记录未标注结构差异。</p>
            ) : (
              <ul className="sa-why sa-why-not">
                {e.whyNotSimilar.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </div>

          {/* 哪些维度未知（与 MISMATCH 严格区分） */}
          <div className="sa-block">
            <h6>哪些维度未知</h6>
            {unknownDims.length === 0 ? (
              <p className="ccs-none">四个维度均有判定，无未知项。</p>
            ) : (
              <ul className="sa-why">
                {unknownDims.map((k) => (
                  <li key={k}>
                    {DIMENSION_LABEL[k]}：{DIMENSION_STATUS_LABEL[dimensionStatusOf(e, k)]}
                    <span className="ccs-dim"> —— 资料不足，不等于「不存在」或「不对应」</span>
                  </li>
                ))}
              </ul>
            )}
            {mismatchDims.length > 0 && (
              <p className="ccs-dim">
                明确不对应的维度：{mismatchDims.map((k) => DIMENSION_LABEL[k]).join('、')}
              </p>
            )}
          </div>

          {/* 逐维依据（provenance 入口） */}
          <details className="sa-block sa-prov">
            <summary>逐维依据（Provenance）</summary>
            <ul className="sa-why">
              {DIMENSION_ORDER.map((k) => (
                <li key={k}>
                  {DIMENSION_LABEL[k]}：{evidenceCountOf(e, k)} 条直接依据
                </li>
              ))}
            </ul>
            {e.backgroundSources.length > 0 && (
              <p className="ccs-dim">
                另有 {e.backgroundSources.length} 条背景来源（{e.backgroundSources
                  .map((b) => b.source)
                  .join('、')}）—— 仅作背景，不作为维度判定依据。
              </p>
            )}
          </details>

          {/* 导航 */}
          {e.navigationTarget.navigableToCampaign ? (
            <button
              type="button"
              className="ccs-open"
              onClick={() => {
                const sel: Selection = { kind: 'campaign', id: e.navigationTarget.id };
                if (onOpenHistoricalCase) {
                  onOpenHistoricalCase(sel, {
                    candidateId,
                    candidateName,
                    structuralStatus: STRUCTURAL_STATUS_LABEL[e.structuralStatus],
                    strictStructuralSupported: e.strictStructuralSupported,
                    themeRelation: {
                      value: e.themeRelation.value,
                      label: THEME_RELATION_LABEL[e.themeRelation.value],
                    },
                    dimensions: DIMENSION_ORDER.map((k) => {
                      const st = dimensionStatusOf(e, k);
                      return {
                        key: k,
                        label: DIMENSION_LABEL[k],
                        status: st,
                        statusLabel: DIMENSION_STATUS_LABEL[st],
                      };
                    }),
                    whySimilar: e.whySimilar,
                    whyNotSimilar: e.whyNotSimilar,
                    unknownDimensionLabels: DIMENSION_ORDER.filter((k) =>
                      isIndeterminate(dimensionStatusOf(e, k)),
                    ).map((k) => DIMENSION_LABEL[k]),
                    snapshotDate: e.snapshotDate,
                    ruleSetVersion: e.ruleSetVersion,
                  });
                } else {
                  onSelect(sel);
                }
              }}
            >
              查看完整历史案例 →
            </button>
          ) : (
            <p className="ccs-dim sa-nonav">
              该历史对象是 <strong>Research Candidate</strong>（不是 Campaign），
              没有对应的 Campaign Detail 页面 —— 不提供不存在的入口。
            </p>
          )}

          <p className="ccs-dim">
            快照 {e.snapshotDate} · 规则版本 {e.ruleSetVersion}
          </p>
        </div>
      )}
    </li>
  );
}
