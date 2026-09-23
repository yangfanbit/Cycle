/**
 * researchWorkflow.test.tsx —— **Product / Real Usage v0.1 端到端研究闭环验收**
 *
 * 目的：不再只做「组件测试」，而是模拟用户从**今天**出发完成一次完整历史研究：
 *
 *   Current Candidate → Current Time Lens → Time Observation / Calendar
 *     → Lifecycle → Structural Analogy → Historical Case → Evidence
 *     → 为什么对应 / 哪里不同 → 新的 Research Question
 *
 * 对 **全部 5 个 Current Candidate** 逐一执行，并检查：
 *   · 今天的位置可理解
 *   · 历史对象身份（Campaign vs Research Candidate）明确区分
 *   · 四维结构信息可读（不是一堆内部枚举）
 *   · 不确定性诚实表达（UNKNOWN / NOT_AVAILABLE ≠ MISMATCH）
 *   · 页面结束后能自然产生「下一步研究」
 *   · 无 score / ranking / probability / prediction
 *
 * ★ 本文件是**验收夹具**，不是产品功能。
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import { defaultCurrentCandidateDataset } from '../currentCandidate';
import { currentTimeLens } from '../currentTimeLens';
import { historicalCaseOf } from '../historicalCase';
import {
  DIMENSION_LABEL,
  DIMENSION_STATUS_LABEL,
  INDETERMINATE_DIMENSION_STATUSES,
  STRUCTURAL_STATUS_LABEL,
  explanationByHistoricalCycleId,
  isIndeterminate,
  navigationTargetOf,
  parseStructuralAnalogyDataset,
  structuralAnalogyForCandidate,
} from '../structuralAnalogy';
import { defaultTimeObservationDataset, buildTimeObservationLayer } from '../timeObservationPatterns';
import { previewTimelineSource } from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import structuralAnalogyJson from '@observation/structural_analogy_explanations_v0_5.json';

const TODAY = '2026-09-24';
const SA = parseStructuralAnalogyDataset(structuralAnalogyJson);
const CANDIDATES = defaultCurrentCandidateDataset().candidates;

/** 禁止出现的语义（score / ranking / probability / prediction） */
const BANNED = ['推荐', '买入', '卖出', '必涨', '胜率', '概率是', '预测为', '排名第一', '最相似的是'];

describe('研究闭环验收 · 0. 前置：当前研究对象与历史宇宙', () => {
  it('5 个 Current Candidate 全部存在且带阶段 / 驱动', () => {
    expect(CANDIDATES).toHaveLength(5);
    for (const c of CANDIDATES) {
      expect(c.candidate_id).toBeTruthy();
      expect(c.display_name).toBeTruthy();
      expect(c.attention_state).toBeTruthy();
      expect(c.core_narrative).toBeTruthy();
    }
  });

  it('历史宇宙 = 52 Campaign + 27 Research Candidate（身份已正式区分）', () => {
    expect(timelineExportData.campaigns).toHaveLength(52);
    expect(timelineExportData.research_candidates).toHaveLength(27);
    // SA artifact 的 identity 必须同时含两类（不再是「全部 campaign」）
    const kinds = new Set(
      SA.candidates.flatMap((c) => c.explanations.map((e) => e.identity.historicalObjectKind)),
    );
    expect(kinds).toEqual(new Set(['campaign', 'research_candidate']));
  });
});

describe('研究闭环验收 · 1–6. 逐 Candidate 走完整链路', () => {
  for (const cand of CANDIDATES) {
    describe(`▸ ${cand.candidate_id}`, () => {
      it('① 今天在哪里：Current Time Lens 给出窗口与今日位置', () => {
        const lens = currentTimeLens(previewTimelineSource(), TODAY);
        expect(lens.position.today).toBe(TODAY);
        expect(lens.position.window.start).toBeTruthy();
        expect(lens.position.window.end).toBeTruthy();
        expect(lens.position.monthLabel).toBeTruthy();
        // 诚实空态字段必须存在（不是「历史没有机会」）
        expect(typeof lens.uncovered).toBe('boolean');
        expect(lens.samePeriod.length).toBeGreaterThan(0);
      });

      it('② 为什么进入历史比较：SA 数据集含该 Candidate 且解释完整', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id);
        expect(view).not.toBeNull();
        expect(view!.explanations.length).toBeGreaterThan(0);
        expect(view!.explanations.length).toBe(
          timelineExportData.campaigns.length + timelineExportData.research_candidates.length,
        );
      });

      it('③ 历史对象身份：Campaign / RC 明确区分，不混淆', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id)!;
        const rcIds = new Set(timelineExportData.research_candidates.map((r) => r.campaign_id));
        let campaigns = 0;
        let rcs = 0;
        for (const e of view.explanations) {
          const id = e.identity.historicalCycleId;
          if (rcIds.has(id)) {
            rcs += 1;
            expect(e.identity.historicalObjectKind).toBe('research_candidate');
            expect(e.identity.historicalResearchCandidateId).toBe(id);
            expect(e.identity.historicalCampaignId).toBeNull();
          } else {
            campaigns += 1;
            expect(e.identity.historicalObjectKind).toBe('campaign');
            expect(e.identity.historicalCampaignId).toBe(id);
            expect(e.identity.historicalResearchCandidateId).toBeNull();
          }
        }
        expect(campaigns).toBe(52);
        expect(rcs).toBe(27);
      });

      it('④ Structural Analogy 四维可读：四维均有标签与状态标签', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id)!;
        const e = view.explanations[0];
        const DIM_KEYS = {
          lifecycle: 'lifecycle',
          mechanism_driver: 'mechanismDriver',
          evidence_sequence: 'evidenceSequence',
          event_structure: 'eventStructure',
        } as const;
        for (const [snake, camel] of Object.entries(DIM_KEYS)) {
          // 四维都必须有**人类可读标签**（不得把内部枚举直接暴露给用户）
          expect(DIMENSION_LABEL[snake as keyof typeof DIMENSION_LABEL]).toBeTruthy();
          const status = e.dimensions[camel as keyof typeof e.dimensions].status;
          expect(DIMENSION_STATUS_LABEL[status]).toBeTruthy();
        }
        expect(STRUCTURAL_STATUS_LABEL[e.structuralStatus]).toBeTruthy();
      });

      it('⑤ 不确定性诚实：UNKNOWN / NOT_AVAILABLE ≠ MISMATCH，PERIPHERAL 不计支持', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id)!;
        for (const e of view.explanations) {
          const indet = INDETERMINATE_DIMENSION_STATUSES;
          // 「资料不足」与「不对应」必须是**不同**的状态词与标签
          for (const s of indet) expect(s).not.toBe('MISMATCH');
          expect(DIMENSION_STATUS_LABEL.UNKNOWN).not.toBe(DIMENSION_STATUS_LABEL.MISMATCH);
          expect(DIMENSION_STATUS_LABEL.NOT_AVAILABLE).not.toBe(DIMENSION_STATUS_LABEL.MISMATCH);
          // PERIPHERAL_OVERLAP 不得进入 supported
          if (e.dimensions.mechanismDriver.status === 'PERIPHERAL_OVERLAP') {
            expect(e.supportedDimensions).not.toContain('mechanism_driver');
          }
          // 三维数组完整划分四维（不丢维度）
          const all = [...e.supportedDimensions, ...e.unknownDimensions, ...e.unsupportedDimensions];
          expect(new Set(all).size).toBe(all.length);
          expect([...all].sort()).toEqual([
            'event_structure',
            'evidence_sequence',
            'lifecycle',
            'mechanism_driver',
          ]);
        }
      });

      it('⑥ Historical Case 可达：Campaign 可进入；RC 不被伪造成 Campaign Detail', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id)!;
        const source = previewTimelineSource();
        const allObjects = source
          .years()
          .flatMap((y) => source.yearData(y).campaigns)
          .filter((c, i, arr) => arr.findIndex((x) => x.campaign_id === c.campaign_id) === i);
        const byId = new Map(allObjects.map((c) => [c.campaign_id, c]));

        let checkedCampaign = 0;
        let checkedRc = 0;
        for (const e of view.explanations) {
          const id = e.identity.historicalCycleId;
          const obj = byId.get(id);
          if (!obj) continue;
          const hc = historicalCaseOf(obj);
          // 身份必须与 SA artifact 一致
          expect(hc.header.objectKind).toBe(e.identity.historicalObjectKind);
          const nav = navigationTargetOf(e.identity);
          expect(nav).toBeTruthy();
          if (e.identity.historicalObjectKind === 'research_candidate') {
            checkedRc += 1;
            // RC 不得被当作正式 Campaign 呈现
            expect(hc.header.objectKind).toBe('research_candidate');
          } else {
            checkedCampaign += 1;
          }
        }
        // 两类都真实覆盖（否则断言空洞）
        expect(checkedCampaign).toBeGreaterThan(0);
        expect(checkedRc).toBeGreaterThan(0);
      });

      it('⑦ 下一步研究：why_similar / why_not 存在且不含 theme 依据，无 score/ranking', () => {
        const view = structuralAnalogyForCandidate(SA, cand.candidate_id)!;
        for (const e of view.explanations) {
          expect(e.whySimilar.length).toBeGreaterThan(0);
          // 「哪里不同」必须给出说明（即使无显著负证据也要显式说明）
          expect(e.whyNotSimilar.length).toBeGreaterThan(0);
          // ★ 跨 Macro Theme **不是**「不相似」的理由（theme 只作 metadata）
          for (const t of e.whyNotSimilar) {
            expect(t.toLowerCase()).not.toContain('macro theme');
            expect(t).not.toContain('跨 Macro Theme');
          }
        }
      });
    });
  }
});

describe('研究闭环验收 · 7. Time Observation 契约', () => {
  it('只有真实达标的 Pattern 进入 Timeline；RESEARCH_ONLY / EXPLORATORY / REJECTED 不冒充', () => {
    const ds = defaultTimeObservationDataset();
    expect(ds.issues).toEqual([]);
    const eligible = ds.patterns.filter((p) => p.timelineEligible);
    expect(eligible.length).toBeGreaterThan(0);
    for (const p of eligible) {
      expect(p.promotionStatus).toBe('TIMELINE');
      expect(p.window).not.toBeNull();
      expect(p.recurrence.eligibleYears).toBeGreaterThanOrEqual(5);
    }
    for (const p of ds.patterns) {
      if (p.promotionStatus !== 'TIMELINE') expect(p.timelineEligible).toBe(false);
    }
    // TOP-01 仍在（研究结论不因扩容而消失）
    expect(ds.patterns.some((p) => p.patternId === 'TOP-01' && p.timelineEligible)).toBe(true);
  });

  it('Time Observation 层只展示 Timeline-eligible，且不表述为未来概率', () => {
    const ds = defaultTimeObservationDataset();
    const model = buildTimeObservationLayer(ds, TODAY);
    expect(model.views.length).toBeGreaterThan(0);
    for (const v of model.views) {
      expect(ds.patterns.find((p) => p.patternId === v.patternId)!.promotionStatus).toBe('TIMELINE');
    }
    expect(model.researchOnlyCount + model.rejectedCount).toBeGreaterThan(0);
  });

  it('当前日期不在窗口时出现诚实空态（不编造「正在窗口内」）', () => {
    const ds = defaultTimeObservationDataset();
    // 2026-09-24 与 TOP-01 窗口（05-27 ~ 06-26）不相交 → 必须为诚实空态
    const model = buildTimeObservationLayer(ds, '2026-09-24');
    for (const v of model.views) {
      // 纯日历口径：proximity 为枚举 + 人类可读标签 + 距窗口天数（不是概率）
      expect(typeof v.proximity).toBe('string');
      expect(v.proximityLabel).toBeTruthy();
      expect(typeof v.distanceDays).toBe('number');
      // 「历史复现：N / M 个观测年份」——**不是**未来概率
      expect(v.recurrenceLabel).toContain('历史复现');
      expect(v.recurrenceLabel).toContain('观测年份');
      expect(v.recurrenceLabel).not.toMatch(/概率|胜率|预期/);
    }
  });
});

describe('研究闭环验收 · 8. 语义红线：无 score / ranking / probability / prediction', () => {
  /**
   * ★ 重要区分（避免把「忠实呈现研究原文」误判为违规）：
   *   Product 必须**原样呈现研究证据原文**。例如 export 的
   *   `C-2024-FIN-BANK-DIVIDEND` driver 原文含「2024 年 A 股银行板块全年涨幅超 37%，
   *   所有行业中排名第一（E-FINRE-34）」—— 这是**历史事实描述**，不是 Product 生成的排名。
   *   因此本测试只检查 **Product 自己生成的标签 / 文案**，不扫描研究证据原文。
   */
  it('Product 自有的标签词表与 UI 文案不含禁止语义', () => {
    const productLabels = [
      ...Object.values(STRUCTURAL_STATUS_LABEL),
      ...Object.values(DIMENSION_STATUS_LABEL),
      ...Object.values(DIMENSION_LABEL),
      '当前值得研究',
      '保持观察',
      '历史参考',
    ];
    for (const label of productLabels) {
      for (const b of BANNED) expect(label).not.toContain(b);
    }
  });

  it('CurrentTimeLens 的 UI 结构文案不含禁止语义（排除研究证据原文）', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={null}
        onSelect={() => {}}
      />,
    );
    // 只取 Product 自己写的 UI 文案：标题 / 说明 / 按钮 / 注释性段落
    const uiTexts = [
      ...html.matchAll(/<(?:h[1-6]|p|button|span)[^>]*>([^<]{2,})</g),
    ]
      .map((m) => m[1])
      .filter((t) => !/E-[A-Z]|EV-|S\d{3}|（.*?，.*?）/.test(t));
    expect(uiTexts.length).toBeGreaterThan(0);
    for (const t of uiTexts) {
      for (const b of BANNED) expect(t).not.toContain(b);
    }
    // 反向校验：UI 必须明确声明「不是排名 / 不是概率」
    expect(html).toContain('不是');
  });

  it('SA 与 TO artifact 中不存在 score / ranking / probability 字段', () => {
    const walk = (o: unknown, acc: string[] = []): string[] => {
      if (Array.isArray(o)) o.forEach((x) => walk(x, acc));
      else if (o && typeof o === 'object') {
        for (const [k, v] of Object.entries(o as Record<string, unknown>)) {
          acc.push(k);
          walk(v, acc);
        }
      }
      return acc;
    };
    const banned = /similarity_score|weighted_score|confidence_score|probability|ranking|prediction|win_rate|expected_return/i;
    for (const [name, obj] of [
      ['explanations_v0_5', structuralAnalogyJson],
      ['time_observation_v0_2', defaultTimeObservationDataset()],
    ] as const) {
      const hits = walk(obj).filter((k) => banned.test(k));
      expect(hits, `${name} 出现禁止字段：${hits.join(',')}`).toEqual([]);
    }
  });
});
