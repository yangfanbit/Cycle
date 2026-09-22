import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalJson from '@observation/structural_analogy_explanations_v0_4.json';
import { StructuralAnalogySection, dimensionStatusOf, filterExplanations, macroThemeOf } from '../../../components/CurrentTimeLens/StructuralAnalogySection';
import { CurrentCandidateSection } from '../../../components/CurrentTimeLens/CurrentCandidateSection';
import {
  EMPTY_STRUCTURAL_ANALOGY_DATASET,
  STRUCTURAL_STATUS_LABEL,
  parseStructuralAnalogyDataset,
  loadStructuralAnalogyDataset,
  structuralAnalogyForCandidate,
  type StructuralAnalogyDataset,
  type StructuralStatus,
} from '../structuralAnalogy';
import { buildCurrentCandidateViews } from '../currentCandidateAdapter';
import { parseCurrentCandidateDataset } from '../currentCandidate';
import { verifiedTimelineSource } from '../timelineAdapter';

/**
 * Structural Analogy UI（Product UI Integration v0.1）测试。
 * 覆盖：5 个候选定位 · 五级状态展示 · UNKNOWN/NOT_AVAILABLE 不与 MISMATCH 混淆 ·
 *       CROSS_MACRO_THEME 作 metadata · Research Candidate 无 Campaign 入口 ·
 *       Campaign 可导航 · 默认顺序非排名 · 空态 · 筛选不是排序 · 旧功能不回归。
 */

const dataset = parseStructuralAnalogyDataset(canonicalJson);
const noop = () => {};

function render(candidateId: string, extra: Record<string, unknown> = {}): string {
  // 测试显式注入已解析数据集（避免依赖异步加载；SSR 下 useEffect 不执行）
  return renderToStaticMarkup(
    <StructuralAnalogySection candidateId={candidateId} onSelect={noop} dataset={dataset} {...extra} />,
  );
}

const ALL_CANDIDATE_IDS = [
  'CC-2026-BCI-MEDTECH',
  'CC-2026-COMPUTE-POWER',
  'CC-2026-EMBODIED-AI',
  'CC-2026-OPTICAL-LINK',
  'CC-2026-OFFSHORE-WIND',
];

/* ---------------- 1. 数据可达性 ---------------- */

describe('Structural Analogy UI · 数据可达性', () => {
  it('5 个 Current Candidate 都能找到自己的 Structural Analogy 数据', () => {
    for (const id of ALL_CANDIDATE_IDS) {
      const c = structuralAnalogyForCandidate(dataset, id);
      expect(c, id).not.toBeNull();
      expect(c!.explanations).toHaveLength(79);
      const html = render(id);
      expect(html).toContain('Structural Analogy');
      expect(html).toContain('当前研究对象');
    }
  });

  it('默认渲染前 6 个（渐进披露），并提供「显示全部 79 个」入口', () => {
    for (const id of ALL_CANDIDATE_IDS) {
      const html = render(id);
      const items = html.match(/class="sa-item /g) ?? [];
      expect(items.length, id).toBe(6);
      expect(html, id).toContain('显示全部 79 个历史对象');
      expect(html, id).toContain('不是');
    }
  });

  it('渲染内容包含四维标签（生命周期 / 驱动机制 / 证据顺序 / 事件结构）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    for (const label of ['生命周期', '驱动机制', '证据顺序', '事件结构']) {
      expect(html).toContain(label);
    }
  });
});

/* ---------------- 2. 五级状态展示 ---------------- */

describe('Structural Analogy UI · 五级状态', () => {
  const cases: [StructuralStatus, string, string][] = [
    ['STRUCTURAL_SUPPORTED', 'CC-2026-BCI-MEDTECH', 'C-2023-AD'],
    ['STRUCTURAL_PARTIAL', 'CC-2026-BCI-MEDTECH', 'C-2019-COMM-5G'],
    ['THEME_ONLY', 'CC-2026-OPTICAL-LINK', 'C-2019-COMM-5G'],
    ['INSUFFICIENT_EVIDENCE', 'CC-2026-BCI-MEDTECH', 'RC-2024-SECONDARY'],
    ['NO_VALID_CORRESPONDENCE', 'CC-2026-EMBODIED-AI', 'C-2024-ROBOTAXI'],
  ];

  for (const [status, candidateId, cycleId] of cases) {
    it(`${status} 在 UI 中以「${STRUCTURAL_STATUS_LABEL[status]}」展示`, () => {
      // 通过深链展开目标项（超出前 6 条时会自动展开全部）
      const html = render(candidateId, { initialOpenCycleId: cycleId });
      expect(html).toContain(STRUCTURAL_STATUS_LABEL[status]);
      expect(html).toContain(`sa-status s-${status.toLowerCase().replace(/_/g, '-')}`);
    });
  }

  it('THEME_ONLY 的文案不与 STRUCTURAL_SUPPORTED 相同（不混淆）', () => {
    expect(STRUCTURAL_STATUS_LABEL.THEME_ONLY).not.toBe(STRUCTURAL_STATUS_LABEL.STRUCTURAL_SUPPORTED);
    const html = render('CC-2026-OPTICAL-LINK');
    expect(html).toContain('仅主题相关');
  });

  it('严格口径标记只出现在唯一 STRICT 案例上', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    const n = (html.match(/sa-strict/g) ?? []).length;
    expect(n).toBe(1);
  });
});

/* ---------------- 3. UNKNOWN / NOT_AVAILABLE 不与 MISMATCH 混淆 ---------------- */

describe('Structural Analogy UI · 不确定状态', () => {
  it('UNKNOWN / NOT_AVAILABLE 使用 is-indeterminate（虚线），MISMATCH 使用 is-mismatch', () => {
    const html = render('CC-2026-EMBODIED-AI');
    expect(html).toContain('is-indeterminate');
    expect(html).toContain('is-mismatch');
    // 两类 class 不同 → 视觉与语义均可区分
    expect('is-indeterminate').not.toBe('is-mismatch');
  });

  it('展开视图区分「哪些维度未知」与「明确不对应」', () => {
    const html = render('CC-2026-EMBODIED-AI', { initialOpenCycleId: 'C-2024-ROBOTAXI' });
    expect(html).toContain('哪些维度未知');
    expect(html).toContain('资料不足，不等于「不存在」或「不对应」');
  });

  it('dimensionStatusOf 正确映射四维（纯映射，不做判定）', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = c.explanations.find((x) => x.identity.historicalCycleId === 'C-2023-AD')!;
    expect(dimensionStatusOf(e, 'lifecycle')).toBe('MATCH');
    expect(dimensionStatusOf(e, 'mechanism_driver')).toBe('MATCH');
    expect(dimensionStatusOf(e, 'evidence_sequence')).toBe('PARTIAL');
    expect(dimensionStatusOf(e, 'event_structure')).toBe('PARTIAL');
  });

  it('PARTIAL 不被显示成 MATCH', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = c.explanations.find((x) => x.identity.historicalCycleId === 'C-2023-AD')!;
    expect(dimensionStatusOf(e, 'evidence_sequence')).not.toBe('MATCH');
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    expect(html).toContain('部分对应');
  });
});

/* ---------------- 4. Theme Relation 仅 metadata ---------------- */

describe('Structural Analogy UI · Theme Relation', () => {
  it('CROSS_MACRO_THEME 以「背景信息」呈现，不进入「哪里不同」', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    expect(html).toContain('跨 Macro Theme（背景信息）');
    // 「哪里不同」区块内不得出现跨主题依据
    const whyNotIdx = html.indexOf('哪里不同');
    expect(whyNotIdx).toBeGreaterThan(-1);
    const tail = html.slice(whyNotIdx, whyNotIdx + 400);
    expect(tail).not.toContain('跨 Macro Theme');
  });

  it('macroThemeOf 从 background_sources 读取（纯展示查找）', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const e = c.explanations.find((x) => x.identity.historicalCycleId === 'C-2023-AD')!;
    expect(macroThemeOf(e)).toBe('汽车');
  });

  it('背景来源全部标记 BACKGROUND_ONLY（UI 明示不作维度依据）', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    expect(html).toContain('仅作背景，不作为维度判定依据');
  });
});

/* ---------------- 5. identity 与导航 ---------------- */

describe('Structural Analogy UI · identity 与导航', () => {
  it('Campaign 提供 Campaign Detail 入口', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    expect(html).toContain('查看完整历史案例');
    expect(html).toContain('历史 Campaign');
  });

  it('Research Candidate 不提供 Campaign Detail 入口，并明示其类型', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'RC-2023-HUAWEI' });
    expect(html).not.toContain('查看完整历史案例');
    expect(html).toContain('历史 Research Candidate');
    expect(html).toContain('不提供不存在的入口');
  });

  it('Campaign 与 Research Candidate 的 kind class 不同', () => {
    const campaignHtml = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'C-2023-AD' });
    const rcHtml = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'RC-2023-HUAWEI' });
    expect(campaignHtml).toContain('k-campaign');
    expect(rcHtml).toContain('k-research_candidate');
  });

  it('显示稳定 identity（historical_cycle_id）', () => {
    const html = render('CC-2026-BCI-MEDTECH', { initialOpenCycleId: 'RC-2023-HUAWEI' });
    expect(html).toContain('C-2023-AD');
    expect(html).toContain('RC-2023-HUAWEI');
  });

  it('historicalLabelOf 提供显示名时优先使用（缺省回退 identity）', () => {
    const withLabel = render('CC-2026-BCI-MEDTECH', {
      initialOpenCycleId: 'C-2023-AD',
      historicalLabelOf: (id: string) => (id === 'C-2023-AD' ? '汽车 · 智能驾驶' : null),
    });
    expect(withLabel).toContain('汽车 · 智能驾驶');
    const without = render('CC-2026-BCI-MEDTECH');
    expect(without).not.toContain('汽车 · 智能驾驶');
  });
});

/* ---------------- 6. 顺序：默认不是排名 ---------------- */

describe('Structural Analogy UI · 顺序', () => {
  it('默认渲染顺序 = artifact 原始顺序（stable identity），不按 status 排序', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const ids = c.explanations.map((e) => e.identity.historicalCycleId);
    expect([...ids].sort()).toEqual(ids); // cycle_id 升序
    // 第一条不是 STRUCTURAL_SUPPORTED（首条为 NO_VALID_CORRESPONDENCE），证明不是「最强在前」
    expect(c.explanations[0].identity.historicalCycleId).toBe('C-2016-CONS-BAIJIU-UPGRADE');
    expect(c.explanations[0].structuralStatus).not.toBe('STRUCTURAL_SUPPORTED');
  });

  it('HTML 中第一个 sa-item 对应 C-2016-CONS-BAIJIU-UPGRADE（identity 顺序）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    const first = html.indexOf('class="sa-item ');
    const head = html.slice(first, first + 600);
    expect(head).toContain('C-2016-CONS-BAIJIU-UPGRADE');
  });

  it('UI 明示列表不是从强到弱', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('不是从强到弱');
  });

  it('渐进披露截断不改变顺序（被隐藏的是「后面的」，不是「较弱的」）', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const html = render('CC-2026-BCI-MEDTECH');
    const shown = (html.match(/class="sa-item /g) ?? []).length;
    expect(shown).toBe(6);
    // 前 6 个与 artifact 前 6 个一致
    for (const e of c.explanations.slice(0, 6)) expect(html).toContain(e.identity.historicalCycleId);
    expect(html).toContain('不是');
    expect(html).toContain(`最强的 6 个`);
  });

  it('filterExplanations 是筛选而非排序（保持传入顺序）', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const all = filterExplanations(c.explanations, 'ALL');
    expect(all.map((e) => e.identity.historicalCycleId)).toEqual(
      c.explanations.map((e) => e.identity.historicalCycleId),
    );
    const partial = filterExplanations(c.explanations, 'STRUCTURAL_PARTIAL');
    expect(partial.length).toBeGreaterThan(0);
    for (const e of partial) expect(e.structuralStatus).toBe('STRUCTURAL_PARTIAL');
    // 子序列顺序与全量一致
    const order = c.explanations.map((e) => e.identity.historicalCycleId);
    const sub = partial.map((e) => e.identity.historicalCycleId);
    let i = -1;
    for (const id of sub) {
      i = order.indexOf(id, i + 1);
      expect(i).toBeGreaterThan(-1);
    }
  });

  it('筛选按钮展示各状态计数（计数，不是分数）', () => {
    const c = structuralAnalogyForCandidate(dataset, 'CC-2026-BCI-MEDTECH')!;
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain(`全部 ${c.explanations.length}`);
    const supported = c.explanations.filter((e) => e.structuralStatus === 'STRUCTURAL_SUPPORTED').length;
    expect(html).toContain(`${STRUCTURAL_STATUS_LABEL.STRUCTURAL_SUPPORTED} ${supported}`);
  });
});

/* ---------------- 7. 空态 ---------------- */

describe('Structural Analogy UI · 空态', () => {
  it('空数据集 → 诚实空态（不编造、不说「预测失败」）', () => {
    const html = render('CC-2026-BCI-MEDTECH', { dataset: EMPTY_STRUCTURAL_ANALOGY_DATASET });
    expect(html).toContain('暂无 Structural Analogy 研究数据');
    expect(html).toContain('不编造');
    expect(html).not.toContain('预测失败');
  });

  it('未知候选 → 诚实空态', () => {
    const html = render('CC-NOPE');
    expect(html).toContain('暂无 Structural Analogy 研究数据');
  });

  it('候选存在但无记录 → 明确区分「没有记录」与「历史上没有类似结构」', () => {
    const emptyCand: StructuralAnalogyDataset = {
      ...EMPTY_STRUCTURAL_ANALOGY_DATASET,
      artifactVersion: 'test',
      candidates: [
        {
          candidateId: 'CC-TEST',
          displayName: '测试候选',
          macroTheme: null,
          currentStructuralProfile: {
            currentPhase: null,
            phaseStage: null,
            mechanismDrivers: [],
            evidenceCategories: [],
            evidenceSequence: [],
            evidenceSequenceStatus: null,
            eventTypes: [],
            marketStatus: '',
            temporalStatus: '',
            structuralGaps: [],
          },
          summary: {},
          explanations: [],
        },
      ],
    };
    const html = render('CC-TEST', { dataset: emptyCand });
    expect(html).toContain('这不代表「历史上没有类似结构」');
  });
});

/* ---------------- 8. 无 score / 排名 / 概率 ---------------- */

describe('Structural Analogy UI · 无分数与排名', () => {
  it('渲染结果不含 score / 排名 / 概率 / Top-N 措辞', () => {
    const html = ALL_CANDIDATE_IDS.map((id) => render(id)).join('\n');
    // 只允许出现在**否定语境**的措辞：先剔除否定句，再断言其余部分不含这些词
    const affirmative = html
      .replace(/<[^>]*>/g, '')          // 先剥标签，避免 </strong> 把否定句切断
      .replace(/不是「最强的 \d+ 个」/g, '')
      .replace(/不是从强到弱/g, '')
      .replace(/不评分、不排名/g, '')
      .replace(/非预测/g, '')
      .replace(/不是预测失败/g, '');
    for (const bad of ['最相似', '最强', 'Top ', '相似度分', '推荐', '评分']) {
      expect(affirmative).not.toContain(bad);
    }
    // 否定语境是**必须存在**的合规声明
    expect(html).toContain('不评分、不排名');
    expect(html).toContain('不是从强到弱');
    expect(html).toContain('最强的 6 个');
  });

  it('渲染结果不含「预测」「买卖」等越界语义', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    for (const bad of ['买入', '卖出', '目标价', '上涨概率']) {
      expect(html).not.toContain(bad);
    }
    // 「预测」只允许出现在否定语境（研究 · 非预测 / 不是预测失败）
    expect(html).toContain('研究 · 非预测');
    expect(html).toContain('不是预测失败');
  });

  it('明确标注为研究 / 非预测', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('研究 · 非预测');
    expect(html).toContain('不是预测失败');
  });

  it('Driver 分层命名在 UI 中区分（驱动机制 ≠ 证据类别）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('驱动机制');
    expect(html).toContain('证据类别');
    expect(html).toContain('两者不是同一维');
  });
});

/* ---------------- 9. 与 canonical JSON 一致性 ---------------- */

describe('Structural Analogy UI · 与 artifact 一致', () => {
  it('UI 展示的历史对象是 artifact 的**前 6 个**（顺序一致，无新增）', () => {
    const raw = canonicalJson as {
      candidates: { candidate_id: string; explanations: { identity: { historical_cycle_id: string } }[] }[];
    };
    for (const rawC of raw.candidates) {
      const html = render(rawC.candidate_id);
      const shown = rawC.explanations.slice(0, 6);
      for (const e of shown) {
        expect(html, `${rawC.candidate_id}/${e.identity.historical_cycle_id}`).toContain(
          e.identity.historical_cycle_id,
        );
      }
      // 第 7 个默认不展示（渐进披露）
      expect(html).not.toContain(rawC.explanations[6].identity.historical_cycle_id);
      // 但明确告知总数为 79（不隐藏总量）
      expect(html).toContain('显示全部 79 个历史对象');
    }
  });
});

/* ---------------- 10. 旧 Current Candidate 功能不回归 ---------------- */

describe('Current Candidate · 旧功能不回归', () => {
  const source = verifiedTimelineSource();
  const parsed = parseCurrentCandidateDataset(undefined);
  const views = buildCurrentCandidateViews(source, parsed.dataset, '2026-09-15', parsed.issues);

  it('CurrentCandidateSection 在无 Structural Analogy 数据时仍可渲染（不抛错）', () => {
    const html = renderToStaticMarkup(
      <CurrentCandidateSection list={views} onSelect={noop} />,
    );
    expect(html).toContain('当前研究候选');
  });

  it('CurrentCandidateSection 接受可选 dataSource（用于历史对象显示名解析）', () => {
    const html = renderToStaticMarkup(
      <CurrentCandidateSection list={views} onSelect={noop} dataSource={source} />,
    );
    expect(html).toContain('当前研究候选');
  });

  it('旧「历史相似阶段」视图仍存在，但被收进兼容保留容器（默认收起）', () => {
    const html = renderToStaticMarkup(
      <CurrentCandidateSection list={views} onSelect={noop} initialOpenId={views.views[0]?.candidate.candidate_id ?? null} />,
    );
    if (views.views.length > 0) {
      expect(html).toContain('旧视图 · 兼容保留');
      expect(html).toContain('ccs-legacy');
    }
  });
});


/* ---------------- 11. 按需加载（Performance Gate v0.1） ---------------- */

describe('Structural Analogy UI · 按需加载', () => {
  it('未注入 dataset 时显示「正在加载」，**不是**空态（避免误判）', () => {
    const html = renderToStaticMarkup(
      <StructuralAnalogySection candidateId="CC-2026-BCI-MEDTECH" onSelect={noop} />,
    );
    expect(html).toContain('正在加载结构对应数据');
    expect(html).not.toContain('暂无 Structural Analogy 研究数据');
    expect(html).toContain('role="status"');
  });

  it('loadStructuralAnalogyDataset 能加载并解析完整数据集（395 条 / 5 候选）', async () => {
    const ds = await loadStructuralAnalogyDataset();
    expect(ds.candidates).toHaveLength(5);
    expect(ds.artifactVersion).toBe('0.4');
    expect(ds.candidates.reduce((n, c) => n + c.explanations.length, 0)).toBe(395);
  });

  it('加载结果被缓存（重复调用返回同一实例，不重复加载）', async () => {
    const a = await loadStructuralAnalogyDataset();
    const b = await loadStructuralAnalogyDataset();
    expect(a).toBe(b);
  });

  it('注入 dataset 时不进入加载态（同步渲染完整内容）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).not.toContain('正在加载结构对应数据');
    expect(html).toContain('sa-list');
  });
});
