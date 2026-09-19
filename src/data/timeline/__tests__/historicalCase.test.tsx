import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalizationJson from '@observation/historical_driver_canonicalization_v0_1.json';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import {
  EVIDENCE_CATEGORY_LABEL,
  LIFECYCLE_STAGE_LABEL,
  MAPPING_STATUS_LABEL,
  __setMechanismDriversForTest,
  evidenceCategoriesOf,
  historicalCaseOf,
  loadMechanismDrivers,
  withMechanismDrivers,
  type HistoricalCaseAnalogyContext,
} from '../historicalCase';
import { previewTimelineSource } from '../timelineAdapter';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * Historical Case Experience v0.1 测试。
 * 覆盖：Case 视图模型（header / lifecycle / 机制-证据分层 / 证据序列）·
 *       SA 上下文与回流 · Research Candidate 边界 · UNKNOWN 语义 · 无 score/排名。
 */

const source = previewTimelineSource();
const all: TimelineCampaign[] = source.years().flatMap((y) => source.yearData(y).campaigns);
const campaign = all.find((c) => c.campaign_id === 'C-2023-AD')!;
const candidate = all.find((c) => c.kind === 'candidate');

const noop = () => {};

/* ---------------- 1. Case 视图模型 ---------------- */

describe('Historical Case · 视图模型', () => {
  it('header 保留稳定 identity 与层级 metadata', () => {
    const v = historicalCaseOf(campaign);
    expect(v.header.campaignId).toBe('C-2023-AD');
    expect(v.header.title).toContain('汽车');
    expect(v.header.start).toBeTruthy();
    expect(v.header.end).toBeTruthy();
    expect(v.header.objectKind).toBe('campaign');
    expect(v.header.themeCycleId).toBe('auto_intelligence_2023');
    expect(v.header.macroTheme).toBe('汽车');
  });

  it('Research Candidate 的 objectKind 不是 campaign（不得混淆）', () => {
    if (!candidate) return;
    expect(historicalCaseOf(candidate).header.objectKind).toBe('research_candidate');
  });

  it('lifecycle 原样来自 Research phases（不重新推导）', () => {
    const v = historicalCaseOf(campaign);
    expect(v.lifecycle.length).toBe(campaign.phases.length);
    for (let i = 0; i < v.lifecycle.length; i += 1) {
      expect(v.lifecycle[i].stage).toBe(campaign.phases[i].phase);
      expect(v.lifecycle[i].start).toBe(campaign.phases[i].start);
    }
    // 标签表覆盖
    for (const s of v.lifecycle) expect(s.label).toBeTruthy();
  });

  it('evidenceCategories 是「证据类别」而非「驱动机制」（取值域不重叠）', () => {
    const v = historicalCaseOf(campaign);
    for (const c of v.evidenceCategories) {
      expect(Object.keys(EVIDENCE_CATEGORY_LABEL)).toContain(c);
    }
    expect(v.evidenceCategories).not.toContain('POLICY_DRIVEN');
  });

  it('evidenceSequence 按真实日期升序，且带生命周期阶段', () => {
    const v = historicalCaseOf(campaign);
    const dates = v.evidenceSequence.map((e) => e.date);
    expect([...dates].sort()).toEqual(dates);
    for (const e of v.evidenceSequence) {
      if (e.lifecycleStage !== null) {
        expect(e.lifecycleStageLabel).toBe(
          LIFECYCLE_STAGE_LABEL[e.lifecycleStage] ?? e.lifecycleStage,
        );
      }
    }
  });

  it('事件日期不在任何 phases 区间 → lifecycleStage = null（UNKNOWN，不是 MISMATCH）', () => {
    const v = historicalCaseOf(campaign);
    const outside = v.evidenceSequence.filter((e) => e.lifecycleStage === null);
    for (const e of outside) expect(e.lifecycleStageLabel).toBeNull();
  });
});

/* ---------------- 2. 证据类别确定性映射 ---------------- */

describe('Historical Case · 证据类别映射', () => {
  it('policy→POLICY · company→INDUSTRY · market→CAPITAL · macro→EXTERNAL', () => {
    expect(evidenceCategoriesOf([{ event_type: 'policy' }])).toEqual(['POLICY']);
    expect(evidenceCategoriesOf([{ event_type: 'company' }])).toEqual(['INDUSTRY']);
    expect(evidenceCategoriesOf([{ event_type: 'market' }])).toEqual(['CAPITAL']);
    expect(evidenceCategoriesOf([{ event_type: 'macro' }])).toEqual(['EXTERNAL']);
  });

  it('未映射的 event_type 不猜测（industry / news / holiday / other）', () => {
    expect(evidenceCategoriesOf([{ event_type: 'industry' }])).toEqual([]);
    expect(evidenceCategoriesOf([{ event_type: 'news' }])).toEqual([]);
    expect(evidenceCategoriesOf([{ event_type: 'holiday' }])).toEqual([]);
    expect(evidenceCategoriesOf([{ event_type: 'other' }])).toEqual([]);
  });

  it('顺序稳定（POLICY → INDUSTRY → CAPITAL → EXTERNAL）', () => {
    const got = evidenceCategoriesOf([
      { event_type: 'macro' },
      { event_type: 'market' },
      { event_type: 'company' },
      { event_type: 'policy' },
    ]);
    expect(got).toEqual(['POLICY', 'INDUSTRY', 'CAPITAL', 'EXTERNAL']);
  });

  it('无事件 → 空集合（NOT_AVAILABLE，不是「没有」）', () => {
    expect(evidenceCategoriesOf([])).toEqual([]);
  });
});

/* ---------------- 3. 驱动机制按需加载 ---------------- */

describe('Historical Case · 驱动机制按需加载', () => {
  it('loadMechanismDrivers 加载全部 cycle，且只含 canonical 机制', async () => {
    const table = await loadMechanismDrivers();
    const doc = canonicalizationJson as { per_cycle: { cycle_id: string; canonical_drivers: string[] }[] };
    expect(table.size).toBe(doc.per_cycle.length);
    for (const c of doc.per_cycle) {
      const rows = table.get(c.cycle_id) ?? [];
      expect(rows.map((r) => r.driver)).toEqual(c.canonical_drivers);
    }
  });

  it('缓存：重复调用返回同一实例', async () => {
    const a = await loadMechanismDrivers();
    const b = await loadMechanismDrivers();
    expect(a).toBe(b);
  });

  it('withMechanismDrivers 只补机制字段，其余不变', () => {
    const base = historicalCaseOf(campaign);
    const patched = withMechanismDrivers(base, new Map([['C-2023-AD', [
      { driver: 'POLICY_DRIVEN', mappingStatus: 'DIRECT' as const, rawDrivers: [] },
    ]]]));
    expect(patched.mechanismDrivers?.map((d) => d.driver)).toEqual(['POLICY_DRIVEN']);
    expect(patched.header).toEqual(base.header);
    expect(patched.evidenceSequence).toEqual(base.evidenceSequence);
  });

  it('未加载时 mechanismDrivers 为 null（显示加载中，不是「没有机制」）', () => {
    expect(historicalCaseOf(campaign).mechanismDrivers).toBeNull();
  });

  it('无对应 cycle → 空数组（NOT_AVAILABLE 语义）', () => {
    const patched = withMechanismDrivers(historicalCaseOf(campaign), new Map());
    expect(patched.mechanismDrivers).toEqual([]);
  });

  it('映射状态标签覆盖全部取值', () => {
    for (const s of ['DIRECT', 'DERIVED', 'AMBIGUOUS', 'UNKNOWN', 'NOT_AVAILABLE'] as const) {
      expect(MAPPING_STATUS_LABEL[s]).toBeTruthy();
    }
  });
});

/* ---------------- 4. CampaignDetail：SA 上下文与回流 ---------------- */

const CTX: HistoricalCaseAnalogyContext = {
  candidateId: 'CC-2026-BCI-MEDTECH',
  candidateName: '脑机接口医疗器械',
  structuralStatus: '结构支持',
  strictStructuralSupported: true,
  themeRelation: { value: 'CROSS_MACRO_THEME', label: '跨 Macro Theme' },
  dimensions: [
    { key: 'lifecycle', label: '生命周期', status: 'MATCH', statusLabel: '对应' },
    { key: 'mechanism_driver', label: '驱动机制', status: 'MATCH', statusLabel: '对应' },
    { key: 'evidence_sequence', label: '证据顺序', status: 'PARTIAL', statusLabel: '部分对应' },
    { key: 'event_structure', label: '事件结构', status: 'NOT_AVAILABLE', statusLabel: '无可用资料' },
  ],
  whySimilar: ['生命周期阶段对应（MATCH）'],
  whyNotSimilar: ['事件结构 资料不足（UNKNOWN / NOT_AVAILABLE）—— 缺失证据 ≠ 现象不存在'],
  unknownDimensionLabels: ['事件结构'],
  snapshotDate: '2026-09-15',
  ruleSetVersion: 'structural-analogy-ruleset-v0.2',
};

function renderCase(extra: Record<string, unknown> = {}) {
  return renderToStaticMarkup(
    <CampaignDetail campaign={campaign} onOpenRule={noop} onClose={noop} {...extra} />,
  );
}

describe('Historical Case · SA 上下文与回流', () => {
  it('有 SA 上下文时渲染「为什么对应 / 哪里不同」与四维', () => {
    const html = renderCase({ analogyContext: CTX, onBackToAnalogy: noop });
    expect(html).toContain('为什么当前对象与这个历史案例对应');
    expect(html).toContain('结构支持');
    expect(html).toContain('严格口径');
    expect(html).toContain('为什么对应');
    expect(html).toContain('哪里不同');
    for (const label of ['生命周期', '驱动机制', '证据顺序', '事件结构']) {
      expect(html).toContain(label);
    }
  });

  it('提供「返回 Structural Analogy」按钮', () => {
    const html = renderCase({ analogyContext: CTX, onBackToAnalogy: noop });
    expect(html).toContain('返回 Structural Analogy');
  });

  it('无 SA 上下文时不渲染该区块（不编造上下文）', () => {
    const html = renderCase();
    expect(html).not.toContain('为什么当前对象与这个历史案例对应');
    expect(html).not.toContain('返回 Structural Analogy');
  });

  it('UNKNOWN / NOT_AVAILABLE 明示「不等于不存在或不对应」', () => {
    const html = renderCase({ analogyContext: CTX });
    expect(html).toContain('不等于');
    expect(html).toContain('资料不足');
  });

  it('Theme Relation 标注为背景信息（不参与结构判定）', () => {
    const html = renderCase({ analogyContext: CTX });
    expect(html).toContain('背景信息，不参与结构判定');
  });

  it('原样消费 Research 结果（明示不重新计算）', () => {
    const html = renderCase({ analogyContext: CTX });
    expect(html).toContain('产品不重新计算');
    expect(html).toContain('structural-analogy-ruleset-v0.2');
  });
});

/* ---------------- 5. CampaignDetail：层级与分层 ---------------- */

describe('Historical Case · 信息层级与 Driver 分层', () => {
  it('header 显示历史对象类型 / Macro Theme / Theme Cycle', () => {
    const html = renderCase();
    expect(html).toContain('历史对象类型');
    expect(html).toContain('Historical Campaign');
    expect(html).toContain('Macro Theme');
    expect(html).toContain('Theme Cycle');
    expect(html).toContain('auto_intelligence_2023');
  });

  it('「驱动机制」与「证据类别」分开呈现，并说明不是同一维', () => {
    const html = renderCase();
    expect(html).toContain('驱动机制（Mechanism Driver）');
    expect(html).toContain('证据类别（Evidence Category）');
    expect(html).toContain('不是同一维');
  });

  it('旧的「驱动因素（为什么）」已改名为「研究归因（四问）」，不再与机制撞名', () => {
    const html = renderCase();
    expect(html).toContain('研究归因（四问');
    expect(html).not.toContain('驱动因素（为什么）');
  });

  it('证据序列按时间展示，并说明「阶段未知」= UNKNOWN 而非不对应', () => {
    const html = renderCase();
    expect(html).toContain('证据序列（按时间）');
    expect(html).toContain('hcx-seq');
    expect(html).toContain('不是');
  });

  it('生命周期使用既有 phases（不重新推导）', () => {
    const html = renderCase();
    expect(html).toContain('生命周期');
    expect(html).toContain('主题形成');
  });
});

/* ---------------- 6. 边界与禁止项 ---------------- */

describe('Historical Case · 边界', () => {
  it('Research Candidate 明示非 Campaign（不伪装）', () => {
    if (!candidate) return;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={candidate} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('Research Candidate');
    expect(html).toContain('非 Campaign');
  });

  it('渲染结果不含 score / ranking / 概率 / 预测措辞', () => {
    const html = renderCase({ analogyContext: CTX });
    const affirmative = html
      .replace(/<[^>]*>/g, '')
      .replace(/不评分、不排名/g, '')
      .replace(/非预测/g, '')
      .replace(/不构成任何买卖建议/g, '');
    for (const bad of ['最相似', '最强', '评分', '概率', '预测', '推荐']) {
      expect(affirmative).not.toContain(bad);
    }
  });
});
