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
 *   Scenario F  Gate T8 全局不变量 → Research lifecycle 与阶段推导严格单向对应（P0-1 防回归）
 *
 * ★ 本文件是**验收夹具**，不是产品功能。
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { TimeObservationLayer } from '../../../components/TimeObservation/TimeObservationLayer';
import { StructuralAnalogySection } from '../../../components/CurrentTimeLens/StructuralAnalogySection';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import {
  attentionOf,
  terminalPhaseOf,
  CONTRACT_LIFECYCLE_STAGES,
  STAGE_TO_PHASE_SNAPSHOT,
} from '../researchAttention';
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
   * ★★ **P0-1 已修复（ThreeC 1.0 P0 轮）** —— 由 `it.fails` 正式化为正常断言。
   *
   * 修复前：`historicalCaseOf` 在无 research lifecycle 时**回退到视图分段** `derivePhases()`
   *         → 由 `start/end` 推导出 `main_rise` —— 即**在 Product 层虚构了一个 research 未确立的阶段**。
   * 修复后：`historicalCase.lifecycle` **只消费 Research `lifecycle`**；Research 未记录 → `[]`。
   *
   * Gate T8：`UNKNOWN ≠ 自动推导具体阶段`。
   */
  it('D3 Historical Case 侧：无 research lifecycle 时不得给出具体阶段（不得回退视图分段）', () => {
    const obj = byId(RC);
    expect(obj).toBeDefined();
    // 该对象的视图分段（adapter 派生）确实非空 —— 正是修复前被误当成 Research lifecycle 的来源
    expect(obj.phases.length).toBeGreaterThan(0);
    const hc = historicalCaseOf(obj);
    const stages = hc.lifecycle.map((s) => s.stage);
    expect(stages).toEqual([]);
  });

  it('D3b UI 侧：「生命周期」字段区不得出现具体阶段名（研究原文中的其它「结束」不算）', () => {
    const obj = byId(RC);
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={obj} onOpenRule={() => {}} onClose={() => {}} />,
    );
    // ★ 只截取 <dt>生命周期</dt> 之后到下一个 <dt> 之前的那一段（字段区），
    //   避免误伤研究原文（如备注中的「市场响应层完全空白」）与归因文案中的「结束附近」。
    const m = html.match(/<dt>生命周期<\/dt>([\s\S]*?)<dt>/);
    if (m === null) {
      // 无 Research lifecycle → 该字段区**整体不渲染**，这本身就是正确行为
      expect(html).not.toContain('<dt>生命周期</dt>');
      return;
    }
    const fieldText = m[1].replace(/<[^>]*>/g, '');
    expect(fieldText).not.toMatch(/主升|扩张|峰值|退潮|结束|回撤|衰减|早期信号|主题形成|扩散确认/);
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

/* ==================================================================== Scenario F */
/**
 * Gate T8 全局防回归不变量（★ P0-1）。
 *
 * 对**任何** `TimelineCampaign`（正式 Campaign 与 Research Candidate 一视同仁）：
 *
 *   1. Research lifecycle 为空 ⇒
 *        · `terminalPhaseOf(campaign) === 'UNKNOWN'`
 *        · `historicalCaseOf(campaign).lifecycle.length === 0`
 *   2. Research lifecycle 非空 ⇒
 *        · `terminalPhaseOf(campaign) !== 'UNKNOWN'`
 *        · `historicalCaseOf(campaign).lifecycle.length > 0`
 *
 * 反向（第 2 条）**保证修复不是靠「一律返回空」蒙过去的** —— 有 Research 结论的对象
 * 必须照常给出阶段。这正是本轮修复**只去掉回退、未削弱正常路径**的机械证据。
 *
 * 同时锁死：视图分段 `campaign.phases` **在修复后仍然存在**（Timeline 视觉依赖它），
 * 即「不再被误当作 Research lifecycle」≠「被删除」。
 */
describe('Gate T8 · 全局不变量：Research lifecycle 与阶段推导严格单向对应', () => {
  /** 是否存在「无 lifecycle 却有视图分段」的对象 —— 这正是 P0-1 的触发条件集合 */
  const EMPTY_LIFECYCLE = ALL.filter((c) => (c.lifecycle ?? []).length === 0);
  const NON_EMPTY_LIFECYCLE = ALL.filter((c) => (c.lifecycle ?? []).length > 0);

  it('F1 前件成立：数据集中确实存在「无 Research lifecycle」的对象（不变量不是空断言）', () => {
    expect(EMPTY_LIFECYCLE.length).toBeGreaterThan(0);
    expect(NON_EMPTY_LIFECYCLE.length).toBeGreaterThan(0);
  });

  it('F2 无 Research lifecycle ⇒ terminalPhaseOf = UNKNOWN 且 Historical Case lifecycle = []', () => {
    const violated: string[] = [];
    for (const c of EMPTY_LIFECYCLE) {
      if (terminalPhaseOf(c) !== 'UNKNOWN') violated.push(`${c.campaign_id}: phase=${terminalPhaseOf(c)}`);
      if (historicalCaseOf(c).lifecycle.length !== 0) {
        violated.push(`${c.campaign_id}: hc.lifecycle=${historicalCaseOf(c).lifecycle.length}`);
      }
    }
    expect(violated).toEqual([]);
  });

  it('F3 有 Research lifecycle ⇒ terminalPhaseOf ≠ UNKNOWN 且 Historical Case lifecycle 非空', () => {
    const violated: string[] = [];
    for (const c of NON_EMPTY_LIFECYCLE) {
      if (terminalPhaseOf(c) === 'UNKNOWN') violated.push(`${c.campaign_id}: phase=UNKNOWN`);
      if (historicalCaseOf(c).lifecycle.length === 0) violated.push(`${c.campaign_id}: hc.lifecycle=[]`);
    }
    expect(violated).toEqual([]);
  });

  it('F4 Historical Case lifecycle 原样等于 Research lifecycle（不重新推导、不重排）', () => {
    for (const c of NON_EMPTY_LIFECYCLE) {
      const hc = historicalCaseOf(c);
      expect(hc.lifecycle.map((s) => s.stage)).toEqual((c.lifecycle ?? []).map((s) => s.stage));
      expect(hc.lifecycle.map((s) => s.start)).toEqual((c.lifecycle ?? []).map((s) => s.start));
    }
  });

  it('F5 视图分段仍然保留（Timeline 视觉依赖 phases，修复未删除它）', () => {
    for (const c of EMPTY_LIFECYCLE) {
      if (c.kind === 'campaign') expect(Array.isArray(c.phases)).toBe(true);
    }
    // 至少存在一个「无 lifecycle 但 phases 非空」的对象 —— 即修复前会被虚构阶段的样本
    expect(EMPTY_LIFECYCLE.some((c) => c.phases.length > 0)).toBe(true);
  });

  it('F6 具体复核：4 个 lifecycle 仅 UNKNOWN 的 Research Candidate', () => {
    const KNOWN_UNKNOWN_ONLY = [
      'RC-2019-RE-EASING',
      'RC-2020-FIN-BROKER-VOLUME',
      'RC-2016-RE-SHANTY',
      'RC-2015-FIN-LEVERAGE',
    ];
    for (const id of KNOWN_UNKNOWN_ONLY) {
      const c = byId(id);
      expect(c, id).toBeDefined();
      expect((c.lifecycle ?? []).length, id).toBe(0);
      expect(terminalPhaseOf(c), id).toBe('UNKNOWN');
      expect(historicalCaseOf(c).lifecycle, id).toEqual([]);
    }
  });

  /**
   * ★★ 第二个缺陷（本轮审计发现，同属 Gate T8 家族）：
   *   `STAGE_TO_PHASE` 必须覆盖 Contract 的**全部 11 个** `VALID_LIFECYCLE_STAGE`。
   *   漏项**不报错**，只会让 `phaseOfStage()` 静默返回 `UNKNOWN`
   *   —— 研究记录了大写阶段、Product 却显示「阶段未标注」，是**低估研究结论**的失真。
   *   实测漏项：`ENDED`（当前 export 中出现 2 次）。
   *   `UNKNOWN ≠ 未映射`：前者是「研究未判定」，后者是「Product 没接上」。
   */
  it('F7 覆盖度：STAGE_TO_PHASE 覆盖 Contract 全部 11 个阶段（含 ENDED）', () => {
    const missing = CONTRACT_LIFECYCLE_STAGES.filter(
      (s) => STAGE_TO_PHASE_SNAPSHOT[s] === undefined,
    );
    expect(missing).toEqual([]);
    expect(CONTRACT_LIFECYCLE_STAGES.length).toBe(11);
  });

  it('F8 export 中实际出现的每个 stage 都必须被映射（不得静默退化为 UNKNOWN）', () => {
    const seen = new Set<string>();
    for (const c of ALL) for (const s of c.lifecycle ?? []) seen.add(s.stage);
    expect(seen.size).toBeGreaterThan(0); // 前件成立
    const unmapped = [...seen].filter((s) => STAGE_TO_PHASE_SNAPSHOT[s] === undefined);
    expect(unmapped).toEqual([]);
    // 且每个出现过的 stage 都不得被映射成 UNKNOWN
    const toUnknown = [...seen].filter((s) => STAGE_TO_PHASE_SNAPSHOT[s] === 'UNKNOWN');
    expect(toUnknown).toEqual([]);
  });

  it('F9 具体复核：`ENDED` 必须映射为 END（修复前静默退化为 UNKNOWN）', () => {
    expect(STAGE_TO_PHASE_SNAPSHOT.ENDED).toBe('END');
    for (const c of ALL) {
      const hasEnded = (c.lifecycle ?? []).some((s) => s.stage === 'ENDED');
      if (hasEnded) expect(terminalPhaseOf(c), c.campaign_id).toBe('END');
    }
  });
});
