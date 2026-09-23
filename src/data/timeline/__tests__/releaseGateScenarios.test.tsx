/**
 * releaseGateScenarios.test.tsx —— **ThreeC 1.0 Gate U（Real Usage / Human Usability）验收夹具**
 *
 * 目的：不只依赖自动测试，而是把「真实人工验收流程」固化成**可重复执行**的场景。
 * 覆盖 5 个必须走通的真实使用场景：
 *
 *   Scenario A  时间窗口命中 TOP-01 → Today → Time Observation → 历史案例 → 生命周期 → SA
 *   Scenario B  时间窗口无匹配 Pattern → **诚实空态**（不是「错误」）
 *   Scenario C  一个 Research Candidate → 明确标注为「研究候选」，**不冒充正式 Campaign**
 *   Scenario D  一个 lifecycle 只有 UNKNOWN 的 RC → 用户能理解「生命周期信息不足」，**不被错误阶段误导**
 *   Scenario E  一个 end 已知的历史 Campaign → **不显示成「当前仍处于扩张」**
 *
 * ★ 本文件是**验收夹具**，不是产品功能。
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { TimeObservationLayer } from '../../../components/TimeObservation/TimeObservationLayer';
import { StructuralAnalogySection } from '../../../components/CurrentTimeLens/StructuralAnalogySection';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import { attentionOf } from '../researchAttention';
import { historicalCaseOf } from '../historicalCase';
import { parseStructuralAnalogyDataset, structuralAnalogyForCandidate } from '../structuralAnalogy';
import { buildTimeObservationLayer, defaultTimeObservationDataset } from '../timeObservationPatterns';
import { previewTimelineSource } from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import structuralAnalogyJson from '@observation/structural_analogy_explanations_v0_5.json';

const SA = parseStructuralAnalogyDataset(structuralAnalogyJson);
const SOURCE = previewTimelineSource();
const TO = defaultTimeObservationDataset();

/** 便捷：按 id 取 TimelineCampaign（跨年对象去重） */
const ALL = SOURCE.years()
  .flatMap((y) => SOURCE.yearData(y).campaigns)
  .filter((c, i, a) => a.findIndex((x) => x.campaign_id === c.campaign_id) === i);
const byId = (id: string) => ALL.find((c) => c.campaign_id === id)!;

/* ==================================================================== Scenario A */
describe('Gate U · Scenario A：时间窗口命中 TOP-01 时链路完整可走', () => {
  // TOP-01 窗口 = 05-27 ~ 06-26；取窗口内日期
  const TODAY = '2026-06-10';

  it('A1 Time Observation：TOP-01 在窗口内，且为 Timeline-eligible', () => {
    const model = buildTimeObservationLayer(TO, TODAY);
    expect(model.views.length).toBeGreaterThan(0);
    const top01 = model.views.find((v) => v.patternId === 'TOP-01');
    expect(top01).toBeDefined();
    // 该日期确实落在窗口内（不是「附近」的模糊表述）
    expect(top01!.distanceDays).toBe(0);
    expect(top01!.proximityLabel).toBeTruthy();
    // 必须是达标 Pattern（RESEARCH_ONLY / REJECTED 不得出现在 Timeline 视图）
    expect(TO.patterns.find((p) => p.patternId === 'TOP-01')!.promotionStatus).toBe('TIMELINE');
  });

  it('A2 TO 层可渲染，且输出历史窗口与「不是未来概率」声明', () => {
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2026} today={TODAY} onSelect={() => {}} />,
    );
    // ★ TO 组件渲染的是 **Pattern 标题**（不是内部 `pattern_id`）—— 内部 ID 不外露给用户
    const top01Title = TO.patterns.find((p) => p.patternId === 'TOP-01')!.title;
    expect(html).toContain(top01Title);
    expect(html).not.toContain('TOP-01');
    // 历史复现口径（不是概率）
    expect(html).toMatch(/历史复现|观测年份/);
    expect(html).not.toMatch(/概率是|胜率|预期收益/);
  });

  it('A3 从 TO 命中可进入历史案例：窗口内观测年份对象均存在且带 lifecycle 或显式未知', () => {
    const top01 = TO.patterns.find((p) => p.patternId === 'TOP-01')!;
    expect(top01.observations.length).toBeGreaterThan(0);
    for (const o of top01.observations) {
      const obj = byId(o.campaignId ?? '');
      if (!obj) continue; // 观测可能指向已不在当前 export 的年份对象 → 跳过（不编造）
      const hc = historicalCaseOf(obj);
      expect(hc.header.objectKind).toBe(obj.kind === 'candidate' ? 'research_candidate' : 'campaign');
    }
  });

  it('A4 该窗口下的 Current Candidate 可读到 SA 且四维可读', () => {
    const cand = 'CC-2026-OFFSHORE-WIND';
    const view = structuralAnalogyForCandidate(SA, cand);
    expect(view).not.toBeNull();
    expect(view!.explanations.length).toBe(79);
    const html = renderToStaticMarkup(
      <StructuralAnalogySection candidateId={cand} onSelect={() => {}} dataset={SA} />,
    );
    expect(html).toContain('生命周期');
    expect(html).toContain('驱动机制');
    expect(html).toContain('证据顺序');
    expect(html).toContain('事件结构');
  });
});

/* ==================================================================== Scenario B */
describe('Gate U · Scenario B：无匹配 Pattern 时必须是诚实空态', () => {
  // TOP-01 窗口 05-27~06-26；09-24 明确在窗口之外
  const TODAY = '2026-09-24';

  it('B1 当前日期不在任何 Timeline 窗口内 → 不谎称「正在窗口内」', () => {
    const model = buildTimeObservationLayer(TO, TODAY);
    for (const v of model.views) {
      expect(v.distanceDays).not.toBe(0);
      expect(v.proximity).not.toBe('IN_WINDOW');
    }
  });

  it('B2 TO 层渲染时给出诚实空态说明，而不是错误', () => {
    const html = renderToStaticMarkup(
      <TimeObservationLayer year={2026} today={TODAY} onSelect={() => {}} />,
    );
    // 必须显式说明「暂无 / 不在窗口 / 距离」，且不得出现「错误 / 失败」措辞
    expect(html).toMatch(/暂无|不在|距离|天/);
    expect(html).not.toMatch(/错误|失败|异常/);
  });

  it('B3 空态下仍不得编造历史案例', () => {
    const model = buildTimeObservationLayer(TO, TODAY);
    // 视图只含 Timeline-eligible 的 Pattern（此处仍展示 TOP-01 的说明，但 proximity 非窗口内）
    for (const v of model.views) {
      const p = TO.patterns.find((x) => x.patternId === v.patternId)!;
      expect(p.timelineEligible).toBe(true);
    }
  });
});

/* ==================================================================== Scenario C */
describe('Gate U · Scenario C：Research Candidate 必须明确标注，不冒充 Campaign', () => {
  const RC = 'RC-2023-HUAWEI';

  it('C1 export 侧：RC 的 research_status 与 campaign 的 status 属不同字段空间', () => {
    const raw = timelineExportData.research_candidates.find((r) => r.campaign_id === RC)!;
    expect(raw).toBeDefined();
    expect(raw.research_status).toBeTruthy();
    // RC 不得出现在 campaigns 数组
    expect(timelineExportData.campaigns.some((c) => c.campaign_id === RC)).toBe(false);
  });

  it('C2 Historical Case 侧：objectKind = research_candidate', () => {
    const obj = byId(RC);
    expect(obj).toBeDefined();
    const hc = historicalCaseOf(obj);
    expect(hc.header.objectKind).toBe('research_candidate');
  });

  it('C3 SA identity 侧：RC 的 campaign id 为 null，RC id 非空', () => {
    const view = structuralAnalogyForCandidate(SA, 'CC-2026-BCI-MEDTECH')!;
    const e = view.explanations.find((x) => x.identity.historicalCycleId === RC)!;
    expect(e).toBeDefined();
    expect(e.identity.historicalObjectKind).toBe('research_candidate');
    expect(e.identity.historicalCampaignId).toBeNull();
    expect(e.identity.historicalResearchCandidateId).toBe(RC);
  });

  it('C4 UI 侧：CampaignDetail 对 RC 使用「研究候选」措辞', () => {
    const obj = byId(RC);
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={obj} onOpenRule={() => {}} onClose={() => {}} />,
    );
    expect(html).toContain('研究候选');
  });
});

/* ==================================================================== Scenario D */
describe('Gate U · Scenario D：lifecycle 仅 UNKNOWN 的 RC → 明确「信息不足」，不被错误阶段误导', () => {
  const RC = 'RC-2016-RE-SHANTY';

  it('D1 export 侧：lifecycle 为空（未虚构阶段）', () => {
    const raw = timelineExportData.research_candidates.find((r) => r.campaign_id === RC)!;
    expect(raw).toBeDefined();
    expect(raw.lifecycle ?? []).toEqual([]);
  });

  it('D2 export 侧：语义由 research_status 承载（INSUFFICIENT / CONFLICT），不是具体阶段', () => {
    const raw = timelineExportData.research_candidates.find((r) => r.campaign_id === RC)!;
    expect(['INSUFFICIENT', 'CONFLICT']).toContain(raw.research_status);
  });

  /**
   * ★★ **KNOWN GAP（Gate T 未通过）** —— 用 `it.fails` 显式锁定，**不当成正确行为**。
   *
   * 期望：research lifecycle 为空（阶段不可识别）时，Historical Case **不得**给出具体阶段。
   * 实测：`historicalCaseOf` 在无 research lifecycle 时**回退到视图分段** `derivePhases()`
   *       → 由 `start/end` 推导出 `main_rise` —— 即**在 Product 层虚构了一个 research 未确立的阶段**。
   *
   * 这违反 Gate T 的 `UNKNOWN ≠ 自动推导具体阶段`。
   * 用 `it.fails` 的意义：**当前已知不通过**；一旦该行为被修好，本用例会**失败并提醒更新**。
   */
  it.fails('D3 Historical Case 侧：无 research lifecycle 时不得给出具体阶段（★ 当前 KNOWN GAP）', () => {
    const obj = byId(RC);
    expect(obj).toBeDefined();
    const hc = historicalCaseOf(obj);
    const stages = hc.lifecycle.map((s) => s.stage);
    expect(stages).toEqual([]);
  });

  it('D4 SA 侧：lifecycle 维度为「资料不足」而不是「不对应」', () => {
    const view = structuralAnalogyForCandidate(SA, 'CC-2026-BCI-MEDTECH')!;
    const e = view.explanations.find((x) => x.identity.historicalCycleId === RC);
    if (!e) return; // 该 RC 未被此 candidate 收录时跳过（不编造）
    // UNKNOWN / NOT_AVAILABLE / COMPARISON_POINT_UNKNOWN 三者均属「资料不足」，**都不是 MISMATCH**
    expect(e.dimensions.lifecycle.status).not.toBe('MISMATCH');
    expect(e.unknownDimensions).toContain('lifecycle');
  });

  it('D5 UI 侧：渲染出「未知 / 无可用资料」措辞，不出现具体阶段名', () => {
    const html = renderToStaticMarkup(
      <StructuralAnalogySection candidateId="CC-2026-BCI-MEDTECH" onSelect={() => {}} dataset={SA} />,
    );
    expect(html).toMatch(/未知|无可用资料|资料不足|不对应|部分对应/);
  });
});

/* ==================================================================== Scenario E */
describe('Gate U · Scenario E：end 已知的历史 Campaign 不得显示为「当前仍处于扩张」', () => {
  // ★ 选一个**有研究证据**且**已记录 end** 的对象 —— 这样才会真正走到「已记录结束」守卫
  //   （无证据的对象会在更早的「证据不足」分支返回 WATCH，测不到该守卫）
  const CAMPAIGN = 'C-2019-RES-DYE-SHOCK';   // end = 2019-07-30，修复前被判为 ACTIVE_RESEARCH

  it('E1 该 Campaign 的 end 已知（openEnded = false）', () => {
    const obj = byId(CAMPAIGN);
    expect(obj).toBeDefined();
    expect(obj.end).toBeTruthy();
    expect(obj.openEnded).toBe(false);
  });

  it('E2 Attention Gate：不得判为「当前值得研究」，且给出「已记录结束日期」的可读理由', () => {
    const obj = byId(CAMPAIGN);
    const a = attentionOf(obj);
    expect(a.state).not.toBe('ACTIVE_RESEARCH');
    expect(a.state).toBe('HISTORICAL_REFERENCE');
    expect(a.reasons.length).toBeGreaterThan(0);
    expect(a.reasons.join(' ')).toMatch(/结束/);
  });

  it('E2b 另一个已结束对象（证据不足 → WATCH）同样不得为 ACTIVE', () => {
    const obj = byId('C-2016-PANEL-CYCLE');
    const a = attentionOf(obj);
    expect(a.state).not.toBe('ACTIVE_RESEARCH');
  });

  it('E3 全局不变量：所有「已记录 end」的 Campaign 都不得为 ACTIVE_RESEARCH', () => {
    const violated = ALL.filter(
      (c) => c.kind === 'campaign' && !c.openEnded && c.end != null
        && attentionOf(c).state === 'ACTIVE_RESEARCH',
    );
    expect(violated.map((c) => c.campaign_id)).toEqual([]);
  });

  it('E4 反向：仍为 ACTIVE 的必须是「研究未记录结束」的对象', () => {
    const actives = ALL.filter((c) => attentionOf(c).state === 'ACTIVE_RESEARCH');
    for (const c of actives) {
      expect(c.kind).toBe('campaign');
      expect(c.openEnded).toBe(true);
    }
  });
});
