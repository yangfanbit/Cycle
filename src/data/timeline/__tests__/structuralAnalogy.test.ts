import { describe, it, expect } from 'vitest';

import canonicalJson from '@observation/structural_analogy_explanations_v0_4.json';
import {
  DIMENSION_LABEL,
  DIMENSION_STATUS_LABEL,
  EMPTY_STRUCTURAL_ANALOGY_DATASET,
  STRUCTURAL_STATUS_LABEL,
  THEME_RELATION_LABEL,
  parseStructuralAnalogyDataset,
  explanationByHistoricalCycleId,
  explanationCount,
  explanationsByStatus,
  isIndeterminate,
  isStructuralStatus,
  navigationTargetOf,
  structuralAnalogyForCandidate,
  type DriverStatus,
  type StructuralAnalogyIdentity,
  type StructuralStatus,
} from '../structuralAnalogy';

const dataset = parseStructuralAnalogyDataset(canonicalJson);

describe('structuralAnalogy · 解析与覆盖度', () => {
  it('从静态 Artifact 解析出完整数据集（无网络请求）', () => {
    expect(dataset.artifactVersion).toBe('0.4');
    expect(dataset.ruleSetVersion).toBe('structural-analogy-ruleset-v0.3');
    expect(dataset.snapshotDate).toBe('2026-09-15');
    expect(dataset.candidates).toHaveLength(5);
  });

  it('395 个 Research explanations 全部可被稳定解析', () => {
    expect(explanationCount(dataset)).toBe(395);
    for (const c of dataset.candidates) {
      expect(c.explanations).toHaveLength(79);
    }
  });

  it('artifact 与 canonical JSON 的条数一致（无静默丢弃）', () => {
    const rawTotal = (canonicalJson as { candidates: { explanations: unknown[] }[] }).candidates.reduce(
      (n, c) => n + c.explanations.length,
      0,
    );
    expect(explanationCount(dataset)).toBe(rawTotal);
  });

  it('五级 structural status 全部出现在数据集中', () => {
    const present = new Set<StructuralStatus>();
    for (const c of dataset.candidates) for (const e of c.explanations) present.add(e.structuralStatus);
    for (const s of Object.keys(STRUCTURAL_STATUS_LABEL) as StructuralStatus[]) {
      expect(present.has(s)).toBe(true);
    }
  });

  it('候选的 summary 计数之和等于其 explanations 数', () => {
    for (const c of dataset.candidates) {
      const sum = Object.values(c.summary).reduce((a, b) => a + (b ?? 0), 0);
      expect(sum).toBe(c.explanations.length);
    }
  });
});

describe('structuralAnalogy · 保持 artifact 原始顺序（不重排）', () => {
  it('explanations 顺序与 artifact 完全一致', () => {
    const raw = canonicalJson as {
      candidates: { candidate_id: string; explanations: { identity: { historical_cycle_id: string } }[] }[];
    };
    for (const rawC of raw.candidates) {
      const view = structuralAnalogyForCandidate(dataset, rawC.candidate_id);
      expect(view).not.toBeNull();
      expect(view!.explanations.map((e) => e.identity.historicalCycleId)).toEqual(
        rawC.explanations.map((e) => e.identity.historical_cycle_id),
      );
    }
  });

  it('explanations 按 historical_cycle_id 升序（稳定 identity 顺序，不是排名）', () => {
    for (const c of dataset.candidates) {
      const ids = c.explanations.map((e) => e.identity.historicalCycleId);
      expect([...ids].sort()).toEqual(ids);
    }
  });
});

describe('structuralAnalogy · 五级状态各自可解析', () => {
  const cases: [StructuralStatus, string, string][] = [
    ['STRUCTURAL_SUPPORTED', 'CC-2026-BCI-MEDTECH', 'C-2023-AD'],
    ['STRUCTURAL_PARTIAL', 'CC-2026-BCI-MEDTECH', 'C-2019-COMM-5G'],
    ['THEME_ONLY', 'CC-2026-OPTICAL-LINK', 'C-2019-COMM-5G'],
    ['NO_VALID_CORRESPONDENCE', 'CC-2026-EMBODIED-AI', 'C-2024-ROBOTAXI'],
  ];

  for (const [status, candidateId, cycleId] of cases) {
    it(`${status} 可稳定解析`, () => {
      const c = structuralAnalogyForCandidate(dataset, candidateId);
      expect(c).not.toBeNull();
      const e = explanationByHistoricalCycleId(c!, cycleId);
      expect(e).not.toBeNull();
      expect(e!.structuralStatus).toBe(status);
    });
  }

  it('INSUFFICIENT_EVIDENCE 可稳定解析', () => {
    const found = dataset.candidates
      .flatMap((c) => c.explanations)
      .find((e) => e.structuralStatus === 'INSUFFICIENT_EVIDENCE');
    expect(found).toBeDefined();
    expect(found!.unknownDimensions.length).toBeGreaterThan(0);
  });

  it('strict 标记只出现在 STRUCTURAL_SUPPORTED 上，且恰有 1 条', () => {
    const strict = dataset.candidates
      .flatMap((c) => c.explanations)
      .filter((e) => e.strictStructuralSupported);
    expect(strict).toHaveLength(1);
    for (const e of strict) expect(e.structuralStatus).toBe('STRUCTURAL_SUPPORTED');
  });
});

describe('structuralAnalogy · UNKNOWN / NOT_AVAILABLE 保持可区分且不被压缩', () => {
  it('isIndeterminate 只对 UNKNOWN / NOT_AVAILABLE 为真（MISMATCH 为假）', () => {
    expect(isIndeterminate('UNKNOWN')).toBe(true);
    expect(isIndeterminate('NOT_AVAILABLE')).toBe(true);
    expect(isIndeterminate('MISMATCH')).toBe(false);
    expect(isIndeterminate('PARTIAL')).toBe(false);
    expect(isIndeterminate('MATCH')).toBe(false);
  });

  it('unknownDimensions 只包含 UNKNOWN / NOT_AVAILABLE 对应的维度', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        for (const k of e.unknownDimensions) {
          const status =
            k === 'lifecycle'
              ? e.dimensions.lifecycle.status
              : k === 'mechanism_driver'
                ? e.dimensions.mechanismDriver.status
                : k === 'evidence_sequence'
                  ? e.dimensions.evidenceSequence.status
                  : e.dimensions.eventStructure.status;
          expect(isIndeterminate(status as DriverStatus)).toBe(true);
        }
      }
    }
  });

  it('三个维度数组互不重叠且并集为全部四维', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        const all = [...e.supportedDimensions, ...e.unknownDimensions, ...e.unsupportedDimensions];
        expect(new Set(all).size).toBe(all.length);
        expect([...all].sort()).toEqual(['event_structure', 'evidence_sequence', 'lifecycle', 'mechanism_driver']);
      }
    }
  });

  it('PERIPHERAL_OVERLAP 不计为 supported（只在 unsupported 中出现）', () => {
    const hits = dataset.candidates
      .flatMap((c) => c.explanations)
      .filter((e) => e.dimensions.mechanismDriver.status === 'PERIPHERAL_OVERLAP');
    expect(hits.length).toBeGreaterThan(0);
    for (const e of hits) {
      expect(e.supportedDimensions).not.toContain('mechanism_driver');
      expect(e.unsupportedDimensions).toContain('mechanism_driver');
    }
  });
});

describe('structuralAnalogy · identity（统一稳定引用）', () => {
  it('campaign identity：campaign id 非空、research candidate id 为空', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = explanationByHistoricalCycleId(c, 'C-2023-AD')!;
    expect(e.identity.historicalObjectKind).toBe('campaign');
    expect(e.identity.historicalCampaignId).toBe('C-2023-AD');
    expect(e.identity.historicalResearchCandidateId).toBeNull();
    expect(e.identity.historicalCycleId).toBe('C-2023-AD');
    expect(e.identity.historicalThemeCycleId).toBe('auto_intelligence_2023');
  });

  it('research candidate identity：research candidate id 非空、campaign id 为空', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = explanationByHistoricalCycleId(c, 'RC-2023-HUAWEI')!;
    expect(e.identity.historicalObjectKind).toBe('research_candidate');
    expect(e.identity.historicalCampaignId).toBeNull();
    expect(e.identity.historicalResearchCandidateId).toBe('RC-2023-HUAWEI');
  });

  it('historical_cycle_id 始终非空（统一稳定引用）', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) expect(e.identity.historicalCycleId.length).toBeGreaterThan(0);
    }
  });

  it('kind 与两个 identity 字段一一对应（campaign 260 / research_candidate 135）', () => {
    let campaign = 0;
    let rc = 0;
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        if (e.identity.historicalObjectKind === 'campaign') {
          campaign += 1;
          expect(e.identity.historicalCampaignId).not.toBeNull();
          expect(e.identity.historicalResearchCandidateId).toBeNull();
        } else {
          rc += 1;
          expect(e.identity.historicalCampaignId).toBeNull();
          expect(e.identity.historicalResearchCandidateId).not.toBeNull();
        }
      }
    }
    expect(campaign).toBe(260);
    expect(rc).toBe(135);
  });

  it('navigationTargetOf：campaign 可导航；research_candidate 不可导航到 Campaign', () => {
    const campaign: StructuralAnalogyIdentity = {
      historicalObjectKind: 'campaign',
      historicalCycleId: 'C-2023-AD',
      historicalCampaignId: 'C-2023-AD',
      historicalResearchCandidateId: null,
      historicalThemeCycleId: null,
      identityNote: '',
    };
    const rc: StructuralAnalogyIdentity = {
      ...campaign,
      historicalObjectKind: 'research_candidate',
      historicalCycleId: 'RC-2023-HUAWEI',
      historicalCampaignId: null,
      historicalResearchCandidateId: 'RC-2023-HUAWEI',
    };
    expect(navigationTargetOf(campaign)).toEqual({ kind: 'campaign', id: 'C-2023-AD', navigableToCampaign: true });
    expect(navigationTargetOf(rc)).toEqual({
      kind: 'research_candidate',
      id: 'RC-2023-HUAWEI',
      navigableToCampaign: false,
    });
  });

  it('explanations 的 navigationTarget 与 identity 一致', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        expect(e.navigationTarget).toEqual(navigationTargetOf(e.identity));
      }
    }
  });
});

describe('structuralAnalogy · theme relation 仅为 metadata', () => {
  it('CROSS_MACRO_THEME 可解析，且 role 标注 METADATA_ONLY', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = explanationByHistoricalCycleId(c, 'C-2023-AD')!;
    expect(e.themeRelation.value).toBe('CROSS_MACRO_THEME');
    expect(e.themeRelation.role).toContain('METADATA_ONLY');
  });

  it('SAME_MACRO_THEME 可解析', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-OPTICAL-LINK')!;
    const e = explanationByHistoricalCycleId(c, 'C-2023-COMM-OPTICAL')!;
    expect(e.themeRelation.value).toBe('SAME_MACRO_THEME');
  });

  it('whyNotSimilar 不含任何 theme 依据（跨主题不是「不相似」的依据）', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        for (const t of e.whyNotSimilar) {
          expect(t.toLowerCase()).not.toContain('macro theme');
          expect(t).not.toContain('跨 Macro Theme');
        }
      }
    }
  });

  it('THEME_RELATION_LABEL 覆盖两个取值', () => {
    expect(THEME_RELATION_LABEL.SAME_MACRO_THEME).toBeTruthy();
    expect(THEME_RELATION_LABEL.CROSS_MACRO_THEME).toBeTruthy();
  });
});

describe('structuralAnalogy · provenance 分层不丢失', () => {
  it('dimension_evidence 四个维度键均存在', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        expect(Object.keys(e.dimensionEvidence).sort()).toEqual([
          'eventStructure',
          'evidenceSequence',
          'lifecycle',
          'mechanismDriver',
        ]);
      }
    }
  });

  it('background_sources 全部标记 BACKGROUND_ONLY（不得作为维度依据）', () => {
    let total = 0;
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        expect(e.backgroundSources.length).toBeGreaterThan(0);
        for (const b of e.backgroundSources) {
          expect(b.role).toContain('BACKGROUND_ONLY');
          total += 1;
        }
      }
    }
    expect(total).toBeGreaterThan(0);
  });

  it('mechanism driver 证据保留 raw_driver 与 mapping_status', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = explanationByHistoricalCycleId(c, 'C-2023-AD')!;
    expect(e.dimensionEvidence.mechanismDriver.length).toBeGreaterThan(0);
    for (const row of e.dimensionEvidence.mechanismDriver) {
      expect(typeof row.raw_driver).toBe('string');
      expect(typeof row.mapping_status).toBe('string');
    }
  });

  it('supplementary context 标注 SUPPLEMENTARY_ONLY', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        expect(e.supplementaryContext.marketStructure).toContain('SUPPLEMENTARY_ONLY');
        expect(e.supplementaryContext.temporalStructure).toContain('SUPPLEMENTARY_ONLY');
      }
    }
  });
});

describe('structuralAnalogy · 无 score / ranking / probability', () => {
  it('数据集 JSON 序列化后不含禁止字段名', () => {
    const json = JSON.stringify(dataset);
    for (const banned of ['"score"', '"ranking"', '"probability"', '"percentage"', '"winner"', '"confidence"']) {
      expect(json).not.toContain(banned);
    }
  });

  it('解释对象不含数值型“打分”字段', () => {
    for (const c of dataset.candidates) {
      for (const e of c.explanations) {
        const keys = Object.keys(e);
        for (const k of keys) {
          expect(k.toLowerCase()).not.toContain('score');
          expect(k.toLowerCase()).not.toContain('rank');
        }
      }
    }
  });

  it('Driver 分层命名：证据类别 ≠ 驱动机制', () => {
    expect(dataset.dimensionNaming.evidenceCategoryLabel).toBe('证据类别');
    expect(dataset.dimensionNaming.mechanismDriverLabel).toBe('驱动机制');
    expect(dataset.dimensionNaming.rule).toContain('不要');
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    // 两条轴取值域不重叠
    for (const v of c.currentStructuralProfile.mechanismDrivers) {
      expect(c.currentStructuralProfile.evidenceCategories).not.toContain(v);
    }
  });
});

describe('structuralAnalogy · 容错解析与空态', () => {
  it('非对象输入 → 空数据集', () => {
    expect(parseStructuralAnalogyDataset(null)).toBe(EMPTY_STRUCTURAL_ANALOGY_DATASET);
    expect(parseStructuralAnalogyDataset('x')).toBe(EMPTY_STRUCTURAL_ANALOGY_DATASET);
    expect(parseStructuralAnalogyDataset([])).toBe(EMPTY_STRUCTURAL_ANALOGY_DATASET);
  });

  it('缺字段输入 → 安全默认（不抛错）', () => {
    const parsed = parseStructuralAnalogyDataset({ candidates: [{ candidate_id: 'X', explanations: [{}] }] });
    expect(parsed.candidates).toHaveLength(1);
    expect(parsed.candidates[0].explanations).toHaveLength(0);
    expect(parsed.candidates[0].displayName).toBeNull();
  });

  it('缺失 structural_status 的 explanation 被跳过（不猜测）', () => {
    const parsed = parseStructuralAnalogyDataset({
      candidates: [
        { candidate_id: 'X', explanations: [{ identity: { historical_cycle_id: 'A' } }] },
      ],
    });
    expect(parsed.candidates[0].explanations).toHaveLength(0);
  });

  it('未知 structural_status 不被映射为任何已知状态', () => {
    const parsed = parseStructuralAnalogyDataset({
      candidates: [
        { candidate_id: 'X', explanations: [{ structural_status: 'MADE_UP', identity: { historical_cycle_id: 'A' } }] },
      ],
    });
    expect(parsed.candidates[0].explanations).toHaveLength(0);
  });

  it('未知候选返回 null', () => {
    expect(structuralAnalogyForCandidate(dataset, 'CC-NOPE')).toBeNull();
    expect(structuralAnalogyForCandidate(EMPTY_STRUCTURAL_ANALOGY_DATASET, 'X')).toBeNull();
  });
});

describe('structuralAnalogy · 分组与文案辅助', () => {
  it('explanationsByStatus 分组总数与 explanations 数一致', () => {
    for (const c of dataset.candidates) {
      const grouped = explanationsByStatus(c);
      const total = Object.values(grouped).reduce((n, arr) => n + arr.length, 0);
      expect(total).toBe(c.explanations.length);
    }
  });

  it('isStructuralStatus 只对 SUPPORTED / PARTIAL 为真', () => {
    expect(isStructuralStatus('STRUCTURAL_SUPPORTED')).toBe(true);
    expect(isStructuralStatus('STRUCTURAL_PARTIAL')).toBe(true);
    expect(isStructuralStatus('THEME_ONLY')).toBe(false);
    expect(isStructuralStatus('INSUFFICIENT_EVIDENCE')).toBe(false);
    expect(isStructuralStatus('NO_VALID_CORRESPONDENCE')).toBe(false);
  });

  it('标签表覆盖全部枚举（含 PERIPHERAL_OVERLAP）', () => {
    for (const s of Object.keys(STRUCTURAL_STATUS_LABEL)) expect(STRUCTURAL_STATUS_LABEL[s as StructuralStatus]).toBeTruthy();
    for (const d of Object.keys(DIMENSION_STATUS_LABEL)) expect(DIMENSION_STATUS_LABEL[d as DriverStatus]).toBeTruthy();
    for (const d of Object.keys(DIMENSION_LABEL)) expect(DIMENSION_LABEL[d as keyof typeof DIMENSION_LABEL]).toBeTruthy();
    expect(DIMENSION_STATUS_LABEL.PERIPHERAL_OVERLAP).toBeTruthy();
  });

  it('STRUCTURAL_PARTIAL 不被转成 MATCH（标签与状态均保持独立）', () => {
    expect(STRUCTURAL_STATUS_LABEL.STRUCTURAL_PARTIAL).not.toBe(STRUCTURAL_STATUS_LABEL.STRUCTURAL_SUPPORTED);
    expect(DIMENSION_STATUS_LABEL.PARTIAL).not.toBe(DIMENSION_STATUS_LABEL.MATCH);
  });
});
