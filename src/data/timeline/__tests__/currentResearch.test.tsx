import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import fixtureJson from '@current/fixtures/example_candidates.json';
import annotationsJson from '@current/narrative_annotations.json';
import canonicalJson from '@current/current_candidates.json';

import { previewTimelineSource } from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import { allResearchObjects, PHASE_LABEL } from '../researchAttention';
import {
  EMPTY_CURRENT_CANDIDATE_DATASET,
  PHASE_DIMENSIONS,
  defaultCurrentCandidateDataset,
  parseCurrentCandidateDataset,
  type CurrentCandidate,
  type CurrentCandidateDataset,
  type EvidenceItem,
} from '../currentCandidate';
import {
  evidenceLedgerOf,
  evidenceSummaryOf,
  phaseMatrixOf,
  conflictsOf,
  temporalRelationOf,
  isAdmissible,
} from '../currentEvidence';
import { inferCurrentPhase } from '../currentPhaseInference';
import {
  candidatePatternOf,
  narrativeTypesOfCampaign,
  similarPhaseForCandidate,
} from '../currentSimilarity';
import { buildCurrentCandidateViews } from '../currentCandidateAdapter';
import { CurrentCandidateSection } from '../../../components/CurrentTimeLens/CurrentCandidateSection';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';

/**
 * Phase 7 · Current Research Discovery 测试（v1）。
 *
 * ## 分组
 *   1. 数据协议与完整性（ID 唯一 / 枚举 / canonical 空集）
 *   2. Temporal Firewall（快照后证据不得参与判断）
 *   3. Phase 推断（透明规则、不得强行推断）
 *   4. Evidence Ledger（强度只用有限枚举、冲突检测、状态门只降不升）
 *   5. Similarity v2（候选 × 历史；不引用未来历史记录；Top 3；空态）
 *   6. Theme Boundary（候选绝不自动变成 Campaign）
 *   7. UI（空态优雅降级 / 无百分比 / 无预测语 / Conflict 不显示为可升级）
 *   8. 边界守护（纯 View 层，不写 DB / schema / export / contracts）
 */

const TODAY = '2026-09-15';
const FIXTURE = parseCurrentCandidateDataset(fixtureJson).dataset;
const SOURCE = previewTimelineSource();

const viewsOf = (dataset: CurrentCandidateDataset) =>
  buildCurrentCandidateViews(SOURCE, dataset, TODAY).views;
const viewOf = (id: string) => {
  const v = viewsOf(FIXTURE).find((x) => x.candidate.candidate_id === id);
  if (!v) throw new Error(`fixture candidate not found: ${id}`);
  return v;
};

/** 合成候选（用于 Temporal Firewall / 退化路径的最小构造） */
function makeCandidate(over: Partial<CurrentCandidate> = {}): CurrentCandidate {
  return {
    candidate_id: 'CC-TEST-1',
    snapshot_date: TODAY,
    display_name: '合成候选（测试用，非真实研究数据）',
    macro_theme: null,
    theme_type: null,
    core_narrative: '合成叙事（测试用）。',
    candidate_status: 'CANDIDATE',
    attention_state: 'UNKNOWN',
    phase_window: { start: null, end: null },
    phase_evidence: {},
    evidence: [],
    drivers: [],
    narrative_types: [],
    reference_cases: [],
    research_questions: [],
    source_summary: null,
    uncertainty_notes: [],
    conflict_notes: [],
    last_updated: TODAY,
    ...over,
  };
}

const ev = (over: Partial<EvidenceItem> = {}): EvidenceItem => ({
  evidence_id: 'E-TEST-1',
  source_type: 'POLICY',
  claim: '合成事实（测试用）。',
  evidence_strength: 'MEDIUM',
  direction: 'SUPPORTIVE',
  ...over,
});

/* ================= 1. 数据协议与完整性 ================= */

describe('1. 数据协议与完整性', () => {
  /**
   * Phase 7.1 起 canonical 不再是空集：它承载**第一轮真实离线研究数据**。
   * 本用例锁定的是「数据集仍然诚实」这一不变量，而不是具体条数：
   * 快照日明确、命名空间隔离、每条候选都有可核验证据、历史研究覆盖仍止于 2025。
   */
  it('canonical 数据集 = 第一轮真实候选（非空，且协议不变量成立）', () => {
    const ds = defaultCurrentCandidateDataset();
    expect(ds.contract).toBe('current_candidates');
    expect(ds.snapshot_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(ds.candidates.length).toBeGreaterThan(0);
    expect(ds.research_coverage_until).toBe(2025);
    for (const c of ds.candidates) {
      expect(c.candidate_id).toMatch(/^CC-/);
      expect(c.snapshot_date).toBe(ds.snapshot_date);
      expect(c.core_narrative.length).toBeGreaterThan(0);
      expect(c.evidence.length).toBeGreaterThanOrEqual(3); // 每个候选至少 3 条证据
      expect(c.research_questions.length).toBeGreaterThanOrEqual(3);
      // 每条证据必须有日期（本轮真实数据不留「日期未知」作为主要依据的隐式缺口）
      const dated = c.evidence.filter((e) => e.source_date ?? e.event_date).length;
      expect(dated).toBeGreaterThanOrEqual(3);
    }
  });

  it('canonical 无「诚实空集」回退：空态仅由显式空数据集触发（不再由 canonical 承担）', () => {
    expect(defaultCurrentCandidateDataset().candidates.length).not.toBe(0);
    expect(EMPTY_CURRENT_CANDIDATE_DATASET.candidates).toHaveLength(0);
  });

  it('canonical JSON 与 narrative_annotations 契约字段正确', () => {
    expect((canonicalJson as { contract: string }).contract).toBe('current_candidates');
    expect((annotationsJson as { contract: string }).contract).toBe('narrative_annotations');
  });

  it('Test 1 · candidate_id 全局唯一（canonical + fixture）', () => {
    for (const ds of [defaultCurrentCandidateDataset(), FIXTURE]) {
      const ids = ds.candidates.map((c) => c.candidate_id);
      expect(new Set(ids).size).toBe(ids.length);
    }
    const ids = FIXTURE.candidates.map((c) => c.candidate_id);
    expect(ids).toEqual([
      'FX-AI-MEDICAL',
      'FX-SOLID-BATTERY',
      'FX-CONFLICT-CASE',
      'FX-INSUFFICIENT',
    ]);
  });

  it('Test 1（反例）· 重复 candidate_id 会被解析器标记为问题', () => {
    const dup = {
      contract: 'current_candidates',
      current_candidates_version: '1.0',
      snapshot_date: TODAY,
      candidates: [makeCandidate(), makeCandidate()],
    };
    const { issues } = parseCurrentCandidateDataset(dup);
    expect(issues.some((i) => i.includes('candidate_id 重复'))).toBe(true);
  });

  it('候选命名空间隔离：不得使用 C- / RC- 前缀（解析器告警）', () => {
    const bad = {
      contract: 'current_candidates',
      current_candidates_version: '1.0',
      snapshot_date: TODAY,
      candidates: [makeCandidate({ candidate_id: 'C-2026-NOT-A-CANDIDATE' })],
    };
    const { issues } = parseCurrentCandidateDataset(bad);
    expect(issues.some((i) => i.includes('不得使用 C- / RC- 前缀'))).toBe(true);
  });

  it('非法枚举会退化为保守默认值（不因脏数据崩溃）', () => {
    const dirty = {
      contract: 'current_candidates',
      current_candidates_version: '1.0',
      snapshot_date: TODAY,
      candidates: [
        makeCandidate({
          candidate_status: 'CONFIRMED' as never,
          attention_state: 'MOONSHOT' as never,
          phase_evidence: { narrative: 'SUPER' as never },
        }),
      ],
    };
    const c = parseCurrentCandidateDataset(dirty).dataset.candidates[0];
    expect(c.candidate_status).toBe('CANDIDATE');
    expect(c.attention_state).toBe('UNKNOWN');
    expect(c.phase_evidence.narrative).toBe('UNKNOWN');
  });

  it('数据集缺少 snapshot_date 时给出告警（Temporal Firewall 无法工作）', () => {
    const { issues } = parseCurrentCandidateDataset({ contract: 'current_candidates', candidates: [] });
    expect(issues.some((i) => i.includes('snapshot_date'))).toBe(true);
  });

  it('narrative_annotations 只引用真实存在且不晚于快照的历史案例', () => {
    const exportIds = new Set(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map(
        (c) => c.campaign_id,
      ),
    );
    const starts = new Map(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map((c) => [
        c.campaign_id,
        c.start_date,
      ]),
    );
    const anns = (annotationsJson as { annotations: { campaign_id: string }[] }).annotations;
    expect(anns.length).toBeGreaterThan(0);
    for (const a of anns) {
      expect(exportIds.has(a.campaign_id)).toBe(true);
      expect(starts.get(a.campaign_id)! <= FIXTURE.snapshot_date).toBe(true);
    }
  });
});

/* ================= 2. Temporal Firewall ================= */

describe('2. Temporal Firewall（时间防火墙）', () => {
  it('时间关系推导：前 / 当日 / 后 / 日期未知', () => {
    expect(temporalRelationOf(ev({ source_date: '2026-09-14' }), TODAY)).toBe('BEFORE_SNAPSHOT');
    expect(temporalRelationOf(ev({ source_date: TODAY }), TODAY)).toBe('AT_SNAPSHOT');
    expect(temporalRelationOf(ev({ source_date: '2026-09-16' }), TODAY)).toBe('AFTER_SNAPSHOT');
    expect(temporalRelationOf(ev({ source_date: null, event_date: null }), TODAY)).toBe('UNKNOWN');
    // event_date 作为 source_date 的回退
    expect(temporalRelationOf(ev({ source_date: null, event_date: '2026-09-10' }), TODAY)).toBe(
      'BEFORE_SNAPSHOT',
    );
    expect(isAdmissible('BEFORE_SNAPSHOT')).toBe(true);
    expect(isAdmissible('AT_SNAPSHOT')).toBe(true);
    expect(isAdmissible('AFTER_SNAPSHOT')).toBe(false);
    expect(isAdmissible('UNKNOWN')).toBe(false);
  });

  it('Test 2 · snapshot_date 之后的 evidence 不参与判断（台账隔离）', () => {
    const v = viewOf('FX-AI-MEDICAL');
    expect(v.ledger.admissible.map((e) => e.item.evidence_id)).toEqual([
      'E-FX-01',
      'E-FX-02',
      'E-FX-03',
      'E-FX-04',
    ]);
    expect(v.ledger.excluded.map((e) => e.item.evidence_id)).toEqual(['E-FX-05']);
    expect(v.summary.admissibleCount).toBe(4);
    expect(v.summary.excludedCount).toBe(1);
  });

  it('Test 2（关键）· 被隔离的强证据不影响维度水平', () => {
    const v = viewOf('FX-AI-MEDICAL');
    // 若无防火墙，E-FX-05（INDUSTRY / STRONG / 快照后）会把 industry 抬到 STRONG
    expect(v.matrix.industry.level).toBe('PRESENT');
    expect(v.matrix.industry.origin).toBe('DERIVED_FROM_EVIDENCE');
    expect(v.summary.byStrength.STRONG).toBe(0);
    expect(v.summary.basis.join(' ')).toContain('已被隔离');
  });

  it('Test 2 · 仅有快照后证据的候选 → 无可用证据 → 阶段 UNKNOWN 且状态不高于候选', () => {
    const cand = makeCandidate({
      candidate_id: 'CC-ONLY-AFTER',
      evidence: [
        ev({ source_date: '2027-01-01' }),
        ev({ evidence_id: 'E-TEST-2', source_date: '2027-02-01', evidence_strength: 'STRONG' }),
      ],
      phase_evidence: { narrative: 'STRONG', breadth: 'STRONG' },
      candidate_status: 'PROMOTABLE',
    });
    const led = evidenceLedgerOf(cand);
    expect(led.admissible).toHaveLength(0);
    expect(led.excluded).toHaveLength(2);
    const inf = inferCurrentPhase(cand, led);
    expect(inf.phase).toBe('UNKNOWN');
    expect(inf.matchedRule).toBe('R0_INSUFFICIENT_EVIDENCE');
    const v = viewsOf({
      contract: 'current_candidates',
      current_candidates_version: '1.0',
      snapshot_date: TODAY,
      candidates: [cand],
    })[0];
    expect(v.gate.effective).toBe('CANDIDATE');
    expect(v.gate.demoted).toBe(true);
  });

  it('数据集声明的 temporal_relation 与推导不一致时被显式指出（以推导为准）', () => {
    const cand = makeCandidate({
      evidence: [ev({ source_date: '2026-01-01', temporal_relation: 'AFTER_SNAPSHOT' })],
    });
    const led = evidenceLedgerOf(cand);
    expect(led.admissible).toHaveLength(1);
    expect(led.declaredMismatch).toHaveLength(1);
    expect(led.declaredMismatch[0]).toContain('以推导值为准');
  });
});

/* ================= 3. Phase 推断 ================= */

describe('3. Phase 推断（透明规则引擎）', () => {
  it('Test 3 · 无任何证据 / 无标注 → UNKNOWN，不强行推断', () => {
    const v = viewOf('FX-INSUFFICIENT');
    expect(v.phase).toBe('UNKNOWN');
    expect(v.inference.matchedRule).toBe('R0_INSUFFICIENT_EVIDENCE');
    expect(v.coverage.known).toBe(0);
    expect(v.similarityReady).toBe(false);
    expect(v.researchReady).toBe(false);
  });

  it('Test 3 · 规则表可枚举：每个命中规则 id 都来自固定规则集合', () => {
    const RULES = [
      'R0_INSUFFICIENT_EVIDENCE',
      'R1_NARRATIVE_WEAKENING',
      'R2_MARKET_ABSENT_WITHOUT_BASIS',
      'R3_PEAK_SATURATION',
      'R4_EXPANSION_DIFFUSION',
      'R5_BROAD_CONFIRMATION',
      'R6_THEME_FORMING',
      'R7_EARLY_SIGNAL',
      'R8_UNCLASSIFIED',
    ];
    for (const v of viewsOf(FIXTURE)) {
      expect(RULES).toContain(v.inference.matchedRule);
    }
  });

  it('四个 fixture 候选分别命中预期的规则与阶段', () => {
    expect(viewOf('FX-AI-MEDICAL').phase).toBe('THEME_FORMING');
    expect(viewOf('FX-AI-MEDICAL').inference.matchedRule).toBe('R6_THEME_FORMING');
    expect(viewOf('FX-SOLID-BATTERY').phase).toBe('EARLY_SIGNAL');
    expect(viewOf('FX-SOLID-BATTERY').inference.matchedRule).toBe('R7_EARLY_SIGNAL');
    expect(viewOf('FX-CONFLICT-CASE').phase).toBe('DECLINE');
    expect(viewOf('FX-CONFLICT-CASE').inference.matchedRule).toBe('R1_NARRATIVE_WEAKENING');
    expect(viewOf('FX-INSUFFICIENT').phase).toBe('UNKNOWN');
  });

  it('相位矩阵：研究声明优先，缺失维度由证据派生，逐维标注来源', () => {
    const v = viewOf('FX-AI-MEDICAL');
    // 研究声明
    expect(v.matrix.narrative.level).toBe('PRESENT');
    expect(v.matrix.narrative.origin).toBe('RESEARCH_DECLARED');
    // 由证据派生
    expect(v.matrix.policy.level).toBe('PRESENT');
    expect(v.matrix.policy.origin).toBe('DERIVED_FROM_EVIDENCE');
    expect(v.matrix.market.level).toBe('EMERGING');
    // 未标注
    expect(v.matrix.capital.level).toBe('UNKNOWN');
    expect(v.matrix.capital.origin).toBe('UNSET');
    expect(Object.keys(v.matrix).sort()).toEqual([...PHASE_DIMENSIONS].sort());
  });

  it('研究声明与证据派生不一致时**不静默取舍**（并列保留）', () => {
    const cand = makeCandidate({
      phase_evidence: { narrative: 'PRESENT', industry: 'STRONG' },
      evidence: [
        ev({ source_type: 'INDUSTRY', evidence_strength: 'WEAK', source_date: '2026-01-01' }),
      ],
    });
    const led = evidenceLedgerOf(cand);
    const { matrix, disagreements } = phaseMatrixOf(cand, led);
    expect(matrix.industry.level).toBe('STRONG'); // 研究声明胜出
    expect(disagreements).toHaveLength(1);
    expect(disagreements[0]).toContain('证据派生');
  });

  it('推导阶段与研究声明不一致时 agreesWithDeclared=false 且两值并列保留', () => {
    const v = viewOf('FX-CONFLICT-CASE');
    expect(v.inference.declared).toBe('THEME_FORMING');
    expect(v.inference.phase).toBe('DECLINE');
    expect(v.inference.agreesWithDeclared).toBe(false);
    expect(v.inference.reasons.join(' ')).toContain('不一致');
  });

  it('阶段标签与 7 值枚举对齐（不含 END）', () => {
    const ALLOWED = [
      'EARLY_SIGNAL',
      'THEME_FORMING',
      'BROAD_CONFIRMATION',
      'EXPANSION',
      'PEAK',
      'DECLINE',
      'UNKNOWN',
    ];
    for (const v of viewsOf(FIXTURE)) {
      expect(ALLOWED).toContain(v.phase);
      expect(v.phase).not.toBe('END');
      expect(v.phaseLabel).toBe(PHASE_LABEL[v.phase]);
    }
  });
});

/* ================= 4. Evidence Ledger / 冲突 / 状态门 ================= */

describe('4. Evidence Ledger、冲突检测与状态门', () => {
  it('强度只用有限枚举 HIGH / MEDIUM / LOW / UNKNOWN（无百分比）', () => {
    for (const v of viewsOf(FIXTURE)) {
      expect(['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']).toContain(v.summary.level);
    }
    expect(viewOf('FX-AI-MEDICAL').summary.level).toBe('MEDIUM');
    expect(viewOf('FX-SOLID-BATTERY').summary.level).toBe('LOW');
    expect(viewOf('FX-INSUFFICIENT').summary.level).toBe('UNKNOWN');
  });

  it('冲突检测：结构冲突（政策支持 + 市场/叙事走弱）+ 证据方向冲突', () => {
    const v = viewOf('FX-CONFLICT-CASE');
    const kinds = v.conflicts.map((c) => c.kind);
    expect(kinds).toContain('STRUCTURE');
    expect(kinds).toContain('EVIDENCE');
    // 无冲突的候选不得被误报
    expect(viewOf('FX-AI-MEDICAL').conflicts).toHaveLength(0);
  });

  it('Test 7 · Conflict 候选不得显示为可升级状态（状态门只降不升）', () => {
    const v = viewOf('FX-CONFLICT-CASE');
    expect(v.gate.declared).toBe('PROMOTABLE');
    expect(v.gate.effective).not.toBe('PROMOTABLE');
    expect(v.gate.effective).toBe('WATCH');
    expect(v.gate.demoted).toBe(true);
    expect(v.gate.reasons.join(' ')).toContain('证据冲突');
  });

  it('状态门不得把研究声明**拔高**（只降不升）', () => {
    const cand = makeCandidate({
      candidate_status: 'CANDIDATE',
      phase_evidence: { narrative: 'STRONG', breadth: 'STRONG' },
      evidence: [ev({ evidence_strength: 'STRONG' }), ev({ evidence_id: 'E2', evidence_strength: 'STRONG' })],
    });
    const v = viewsOf({
      contract: 'current_candidates',
      current_candidates_version: '1.0',
      snapshot_date: TODAY,
      candidates: [cand],
    })[0];
    expect(v.gate.effective).toBe('CANDIDATE');
  });

  it('升级条件核对表：明确列出「为什么它仍然只是 Candidate」', () => {
    const v = viewOf('FX-SOLID-BATTERY');
    expect(v.upgradeCriteria).toHaveLength(5);
    // 单条弱证据 → 证据条数与扩散广度均不满足
    const byId = new Map(v.upgradeCriteria.map((c) => [c.id, c]));
    expect(byId.get('EVIDENCE_COUNT')!.met).toBe(false);
    expect(byId.get('BREADTH')!.met).toBe(false);
    expect(byId.get('PHASE_ACTIVE')!.met).toBe(true); // EARLY_SIGNAL 属于可研究阶段
    expect(v.missingDimensions.length).toBeGreaterThan(0);
  });

  it('证据不足时**不编造结论**：无可用证据的候选 researchReady=false', () => {
    expect(viewOf('FX-INSUFFICIENT').researchReady).toBe(false);
    expect(viewOf('FX-AI-MEDICAL').researchReady).toBe(true);
  });
});

/* ================= 5. Similarity v2 ================= */

describe('5. Similarity v2（当前候选 × 历史）', () => {
  it('Test 5 · 当前候选可正常进入 Historical Similar Phase（含四问答案）', () => {
    const v = viewOf('FX-AI-MEDICAL');
    expect(v.similarity.insufficient).toBe(false);
    expect(v.similarity.results.length).toBeGreaterThan(0);
    const top = v.similarity.results[0];
    // ① 历史上什么时候开始值得关注？
    expect(top.preObservation).not.toBeNull();
    expect(top.preObservation!.days).toBe(30);
    // ② 当时处于什么阶段？
    expect(top.phaseLabel).toBeTruthy();
    expect(['SAME', 'ADJACENT']).toContain(top.phaseMatch);
    // ③ 当时为什么形成？
    expect(Array.isArray(top.drivers)).toBe(true);
    // ④ 后来怎么结束？
    expect(top.terminalPhaseLabel).toBeTruthy();
    expect(top.end >= top.start).toBe(true);
    // 必给「为什么类似」
    expect(top.reasons.length).toBeGreaterThan(0);
  });

  it('Test 5 · 医药候选与医药历史案例形成高相似（结构 + 叙事都匹配）', () => {
    const v = viewOf('FX-AI-MEDICAL');
    const pharma = v.similarity.results.find((r) => r.campaign_id === 'C-2019-PHARMA-INNOV');
    expect(pharma).toBeDefined();
    expect(pharma!.tier).toBe('HIGH');
    expect(pharma!.phaseMatch).toBe('SAME');
    expect(pharma!.narrativeTypes).toContain('INDUSTRY_UPGRADE');
  });

  it('最多 Top 3；等级只用「高相似 / 中相似 / 参考案例」，无百分比', () => {
    for (const v of viewsOf(FIXTURE)) {
      expect(v.similarity.results.length).toBeLessThanOrEqual(3);
      for (const r of v.similarity.results) {
        expect(['HIGH', 'MEDIUM', 'REFERENCE']).toContain(r.tier);
      }
      expect(v.similarity.note).not.toMatch(/\d+\s*%/);
    }
  });

  it('Test 6 · Similarity 不会引用未来历史记录（Temporal Firewall）', () => {
    const snapshot = '2020-06-30';
    const cand = makeCandidate({
      candidate_id: 'CC-LOOKAHEAD-CHECK',
      snapshot_date: snapshot,
      attention_state: 'THEME_FORMING',
      phase_evidence: { narrative: 'PRESENT', breadth: 'EMERGING' },
      evidence: [ev({ source_date: '2020-03-01' })],
    });
    const view = similarPhaseForCandidate(
      SOURCE,
      cand,
      'THEME_FORMING',
      ['POLICY'],
    );

    const all = allResearchObjects(SOURCE);
    const eligible = all.filter((c) => c.end <= snapshot);
    expect(view.excludedByFirewall).toBe(all.length - eligible.length);
    expect(view.excludedByFirewall).toBeGreaterThan(0);

    // 任何出现在结果里的历史案例，其结束日必须 <= 快照（否则就是引用了未来）
    for (const r of view.results) {
      expect(r.end <= snapshot).toBe(true);
    }
    const futureIds = new Set(all.filter((c) => c.end > snapshot).map((c) => c.campaign_id));
    expect(futureIds.size).toBeGreaterThan(0);
    for (const r of view.results) {
      expect(futureIds.has(r.campaign_id)).toBe(false);
    }
  });

  it('无足够证据时不硬凑数：阶段 UNKNOWN 的候选 → insufficient', () => {
    const v = viewOf('FX-INSUFFICIENT');
    expect(v.similarity.results).toHaveLength(0);
    expect(v.similarity.insufficient).toBe(true);
    expect(v.similarity.note).toContain('不强行给出相似结果');
  });

  it('第 4 层（Narrative）只在候选已标注叙事类型时生效', () => {
    expect(viewOf('FX-AI-MEDICAL').similarity.narrativeLayerActive).toBe(true);
    expect(viewOf('FX-INSUFFICIENT').similarity.narrativeLayerActive).toBe(false);
    const inactive = viewOf('FX-INSUFFICIENT');
    expect(inactive.similarity.results).toHaveLength(0);
  });

  it('候选 Pattern 由该 Macro Theme 的历史 cycle 形态推导（无历史 → UNKNOWN，不推断）', () => {
    // 医药健康：历史 cycle 存在 → 可推导
    expect(candidatePatternOf(SOURCE, viewOf('FX-AI-MEDICAL').candidate)).toBe('PARALLEL');
    // 电力设备：Wave 1A 补录 2 个历史 cycle（C-2020-POWER-NE / C-2022-POWER-GRID）后，
    // 由 UNKNOWN → 可推导（两个 cycle 各为单组件 → SEQUENTIAL）
    expect(candidatePatternOf(SOURCE, viewOf('FX-SOLID-BATTERY').candidate)).toBe('SEQUENTIAL');
    // 仍无历史 cycle 的 Macro Theme → 依旧 UNKNOWN（不推断）
    expect(candidatePatternOf(SOURCE, makeCandidate({ macro_theme: '无历史主题（测试用）' }))).toBe('UNKNOWN');
    expect(candidatePatternOf(SOURCE, makeCandidate({ macro_theme: null }))).toBe('UNKNOWN');
  });

  it('未标注叙事类型的历史案例 → Narrative 层不参与（不推断）', () => {
    expect(narrativeTypesOfCampaign('NOT-ANNOTATED-XYZ')).toEqual([]);
    expect(narrativeTypesOfCampaign('C-2019-PHARMA-INNOV').length).toBeGreaterThan(0);
  });

  it('Test 6（自反）· 相似结果互不重复且不与候选自身冲突', () => {
    const v = viewOf('FX-AI-MEDICAL');
    const ids = v.similarity.results.map((r) => r.campaign_id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).not.toContain('FX-AI-MEDICAL');
  });
});

/* ================= 6. Theme Boundary ================= */

describe('6. Theme Boundary（候选 ≠ Campaign）', () => {
  it('Test 4 · Candidate 不会自动变成 Campaign（不在 export 任何 id 空间内）', () => {
    const exportIds = new Set(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map(
        (c) => c.campaign_id,
      ),
    );
    for (const ds of [defaultCurrentCandidateDataset(), FIXTURE]) {
      for (const c of ds.candidates) {
        expect(exportIds.has(c.candidate_id)).toBe(false);
        expect(c.candidate_id).not.toMatch(/^(C|RC)-/);
      }
    }
  });

  it('Test 4 · 候选 ID 不出现在 Timeline 的任何年份数据中', () => {
    const ids = new Set(FIXTURE.candidates.map((c) => c.candidate_id));
    for (const y of SOURCE.years()) {
      for (const c of SOURCE.yearData(y).campaigns) {
        expect(ids.has(c.campaign_id)).toBe(false);
      }
    }
  });

  it('相似检索只引用 export 中真实存在的历史案例', () => {
    const exportIds = new Set(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map(
        (c) => c.campaign_id,
      ),
    );
    for (const v of viewsOf(FIXTURE)) {
      for (const r of v.similarity.results) {
        expect(exportIds.has(r.campaign_id)).toBe(true);
      }
      for (const rc of v.candidate.reference_cases) {
        expect(exportIds.has(rc.campaign_id)).toBe(true);
      }
    }
  });

  it('候选状态枚举不含「CONFIRMED / 上涨确认」语义', () => {
    const allowed = ['CANDIDATE', 'WATCH', 'RESEARCHING', 'PROMOTABLE', 'REJECTED'];
    for (const c of FIXTURE.candidates) {
      expect(allowed).toContain(c.candidate_status);
    }
  });
});

/* ================= 7. UI ================= */

describe('7. UI', () => {
  const renderFixture = (openId: string | null = null) =>
    renderToStaticMarkup(
      <CurrentCandidateSection
        list={buildCurrentCandidateViews(SOURCE, FIXTURE, TODAY)}
        onSelect={() => {}}
        initialOpenId={openId}
      />,
    );

  it('Test 8 · 无 Current Candidate 数据时优雅降级（诚实空态，不编造）', () => {
    const list = buildCurrentCandidateViews(SOURCE, EMPTY_CURRENT_CANDIDATE_DATASET, TODAY);
    expect(list.views).toHaveLength(0);
    const html = renderToStaticMarkup(<CurrentCandidateSection list={list} onSelect={() => {}} />);
    expect(html).toContain('当前暂无经过验证的 Current Candidate 数据');
    expect(html).toContain('当前市场实时数据：未接入');
    expect(html).toContain('这是正常结果，不是错误');
    expect(html).not.toContain('ccs-item');
  });

  it('Test 8 · Current Lens 在无候选数据时仍完整渲染（显式空数据集 → 空态，其余区块保留）', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={SOURCE}
        today={TODAY}
        selection={null}
        onSelect={() => {}}
        currentCandidates={EMPTY_CURRENT_CANDIDATE_DATASET}
      />,
    );
    expect(html).toContain('当前时间研究导航');
    expect(html).toContain('当前研究候选');
    expect(html).toContain('A股整体周期：Unknown');
    expect(html).toContain('当前暂无经过验证的 Current Candidate 数据');
  });

  it('Test 8b · 缺省数据源 = canonical 真实候选 → Lens 渲染真实候选（不再是空态）', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens dataSource={SOURCE} today={TODAY} selection={null} onSelect={() => {}} />,
    );
    expect(html).toContain('当前研究候选');
    expect(html).toContain('算电协同');
    expect(html).toContain('脑机接口');
    expect(html).toContain('ccs-item');
    expect(html).not.toContain('当前暂无经过验证的 Current Candidate 数据');
  });

  it('fixture 模式显式标注「示例（非真实研究数据）」', () => {
    const html = renderFixture();
    expect(html).toContain('示例 fixture（非真实研究数据）');
    expect(html).toContain('ccs-fx');
  });

  it('每条候选展示：名称 / 阶段 / 状态 / 证据充分度 / 结构对应入口', () => {
    const html = renderFixture();
    expect(html).toContain('AI 医疗');
    expect(html).toContain('ccs-phase ph-theme_forming">主题形成<');
    expect(html).toContain('ccs-ev ev-medium">证据：证据中等<');
    expect(html).toContain('ccs-status">研究中<');
    // 正式入口为 Structural Analogy（结构对应），不再是「历史相似 N 条」
    expect(html).toContain('ccs-sa-hint');
    // 4 条候选全部可见
    expect((html.match(/ccs-head/g) || []).length).toBe(4);
  });

  it('G-1 退役 · UI 不再出现 Product 自算的历史相似分档 / 星级', () => {
    // 旧视图（currentSimilarity: SIMILARITY_WEIGHTS + score + tier + stars）已于 G-1 退役。
    // 其 tier/stars 是 Product 自算，不是 Research 的正式结构结论 → 不得再出现在 UI。
    for (const html of [renderFixture(), renderFixture('FX-AI-MEDICAL')]) {
      expect(html).not.toContain('ccs-sim');
      expect(html).not.toContain('ccs-stars');
      expect(html).not.toContain('ccs-tier');
      expect(html).not.toContain('高相似');
      expect(html).not.toContain('中相似');
      expect(html).not.toContain('历史相似阶段');
    }
  });

  it('UI 不显示相似度分数 / 百分比（避免被读成概率）', () => {
    const html = renderFixture();
    expect(html).not.toMatch(/\d+\s*%/);
    expect(html).not.toContain('相似度分数');
    expect(html).not.toContain('得分');
  });

  it('UI 不含预测 / 荐股 / 买卖信号语（含否定性限定）', () => {
    const banned = ['建议买入', '建议卖出', '目标价', '大概率上涨', '胜率', '推荐股票'];
    for (const html of [renderFixture(), renderFixture('FX-AI-MEDICAL'), renderFixture('FX-CONFLICT-CASE')]) {
      for (const b of banned) expect(html).not.toContain(b);
    }
    // 必须存在的边界声明（详情层）
    const open = renderFixture('FX-AI-MEDICAL');
    expect(open).toContain('不是概率、不是评分、不是买卖信号');
    expect(open).toContain('不是未来走势');
    expect(open).toContain('不是买卖问题、不是操作建议');
    expect(open).toContain('不是因果结论、不是交易建议');
  });

  it('Test 7（UI）· Conflict 候选显示为「保持观察」并明示未通过状态门', () => {
    const collapsed = renderFixture();
    expect(collapsed).toContain('未通过产品端状态门');
    expect(collapsed).toContain('保持观察');
    // 冲突必须明示、不得被隐藏（详情层）
    const open = renderFixture('FX-CONFLICT-CASE');
    expect(open).toContain('结构冲突');
    expect(open).toContain('证据方向冲突');
    expect(open).toContain('Uncertainty / Conflicts');
  });

  it('Temporal Firewall 在 UI 中可见（概览徽标 + 详情单列 + 不参与判断说明）', () => {
    // 概览层即可见（不隐藏被隔离的证据）
    expect(renderFixture()).toContain('已隔离 1 条快照后证据');
    const html = renderFixture('FX-AI-MEDICAL');
    expect(html).toContain('Temporal Firewall · 已隔离');
    expect(html).toContain('不得参与阶段推断、状态判定与相似度检索');
    expect(html).toContain('E-FX-05');
    // 被隔离证据只出现在防火墙区块（不在可用证据列表中）
    expect((html.match(/E-FX-05/g) || []).length).toBe(1);
    // 可用证据 4 条均在列
    for (const id of ['E-FX-01', 'E-FX-02', 'E-FX-03', 'E-FX-04']) {
      expect(html).toContain(id);
    }
  });

  it('候选列表排序确定：阶段靠前优先（EARLY_SIGNAL → … → UNKNOWN）', () => {
    const ids = viewsOf(FIXTURE).map((v) => `${v.phase}:${v.candidate.candidate_id}`);
    expect(ids).toEqual([
      'EARLY_SIGNAL:FX-SOLID-BATTERY',
      'THEME_FORMING:FX-AI-MEDICAL',
      'DECLINE:FX-CONFLICT-CASE',
      'UNKNOWN:FX-INSUFFICIENT',
    ]);
  });

  it('快照滞后时提示「不是实时研究结果」（Refresh Loop v0.1 文案）', () => {
    const list = buildCurrentCandidateViews(SOURCE, FIXTURE, '2026-10-15');
    expect(list.stale).toBe(true);
    expect(list.stalenessDays).toBe(30);
    const html = renderToStaticMarkup(<CurrentCandidateSection list={list} onSelect={() => {}} />);
    expect(html).toContain('当前研究快照已滞后');
    expect(html).toContain('不是实时研究结果');
    // 字段语义不混淆：snapshot_date / 距今天数 / 历史覆盖年份 分别展示
    expect(html).toContain('研究快照');
    expect(html).toContain('距今天');
    expect(html).toContain('历史研究覆盖至');
  });
});

/* ================= 8. 边界守护 ================= */

describe('8. 边界守护（纯 View 层）', () => {
  const read = (rel: string) =>
    readFileSync(resolve(__dirname, '../../../../', rel), 'utf-8');

  const MODULES = [
    'src/data/timeline/currentCandidate.ts',
    'src/data/timeline/currentEvidence.ts',
    'src/data/timeline/currentPhaseInference.ts',
    'src/data/timeline/currentSimilarity.ts',
    'src/data/timeline/currentCandidateAdapter.ts',
  ];

  it('新模块均声明「不写 DB / schema / export / contracts」边界', () => {
    for (const m of MODULES) {
      const src = read(m);
      expect(src).toMatch(/不写(入)? DB|不写入 DB/);
      expect(src).toContain('contracts');
    }
  });

  it('新模块不得引入 DB / models / 网络依赖', () => {
    const banned = [
      'src/models',
      'better-sqlite3',
      'fetch(',
      'XMLHttpRequest',
      'axios',
      'child_process',
    ];
    for (const m of MODULES) {
      const src = read(m);
      for (const b of banned) expect(src).not.toContain(b);
    }
  });

  it('候选模块只消费既有 timeline 模块，不反向依赖组件层', () => {
    for (const m of MODULES) {
      const src = read(m);
      expect(src).not.toMatch(/from '\.\.\/\.\.\/components/);
      expect(src).not.toMatch(/from '\.\.\/components/);
    }
  });

  it('候选数据集不被写入 export / verified（只读消费）', () => {
    const exportIds = new Set(
      [...timelineExportData.campaigns, ...timelineExportData.research_candidates].map(
        (c) => c.campaign_id,
      ),
    );
    // ★ 数据驱动：export 的规模由 Research 侧决定，不写死 17（旧 universe 耦合）。
    //   断言恒等式 + 本测试的真实不变量（候选走独立 Artifact，不进入 export id 空间）。
    expect(exportIds.size).toBe(
      timelineExportData.campaigns.length + timelineExportData.research_candidates.length,
    );
    expect(exportIds.size).toBeGreaterThan(0);
    // Phase 7.1 起 canonical 承载真实候选；关键不变量是「候选 ID 全部落在 export id 空间之外」
    const canonical = defaultCurrentCandidateDataset();
    expect(canonical.candidates.length).toBeGreaterThan(0);
    for (const c of canonical.candidates) {
      expect(exportIds.has(c.candidate_id)).toBe(false);
    }
  });
});
