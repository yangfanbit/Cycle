import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import { parseCurrentCandidateDataset } from '../currentCandidate';
import canonicalJson from '@current/current_candidates.json';
import { lookupDirection } from '../directionLookup';
import {
  DRAFT_CONSTRAINTS,
  EMPTY_DRAFT,
  KNOWN_LIMITATIONS,
  buildLinkedDraft,
  buildResearchRequestPayload,
  isDraftBlank,
  freezeCoverage,
  isDraftEmpty,
  missingDraftFields,
  renderResearchRequestMarkdown,
  toLines,
  type ResearchRequestDraft,
} from '../researchRequestDraft';
import { normalizeDraft } from '../researchRequestDraftStorage';
import { DirectionLookupSection, ResearchRequestDraftBlock } from '../../../components/DirectionLookup/DirectionLookupSection';

/**
 * 研究请求**草稿**的不变量测试（ThreeC 1.3）。
 *
 * ★ 本文件守护的是**红线**与**语义边界**，不是渲染细节：
 *   ① 草稿**没有**正式 ID（不得伪造 URO-* / R<NN>-*）；
 *   ② 状态是 `DRAFT_NOT_REVIEWED`，且明示须人工审查；
 *   ③ 覆盖查询四态结果**随草稿一起导出**（用户与审查者看到同一份事实）；
 *   ④ 「主题名命中 ≠ 结构对应」「未覆盖 ≠ 结构上不存在对应」两条限制**必须在导出里出现**；
 *   ⑤ 不得出现评分 / 排序 / 概率 / 预测 / 买卖信号。
 */

const source = researchTimelineSource();
const dataset = parseCurrentCandidateDataset(canonicalJson).dataset;

const NOW = '2026-10-16T00:00:00.000Z';

const FULL_DRAFT: ResearchRequestDraft = {
  direction: '汽车',
  researchQuestions: 'L3 强制国标落地前后，产业链哪一段先反应？\n历史上类似「合规化驱动」的行情持续多久？',
  whyCare: '所在行业与客户需求',
  knownLeads: '2024-06 某部委征求意见稿\n某券商行业报告',
  timeRange: '2018-2025',
  // ★ v0.7：未关联任何查询的「纯手写草稿」
  linkedQuery: '',
  linkedAt: '',
  linkedCoverage: null,
};

const linked = (q: string, at = NOW): ResearchRequestDraft => ({
  ...FULL_DRAFT,
  direction: q,
  linkedQuery: q,
  linkedAt: at,
  linkedCoverage: freezeCoverage(lookupDirection(q, source, dataset), at),
});

/* ---------------------------------------------- 1. 红线：无 ID / 未审查 */

describe('研究请求草稿 · 红线', () => {
  it('★★ 草稿**没有**正式 ID（不得伪造 URO-* / R<NN>-*）', () => {
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    expect(p.id).toBeNull();
    expect(p.status).toBe('DRAFT_NOT_REVIEWED');
    expect(p.review_required).toBe(true);
    // task_scope.task_id 也必须为 null —— 编号由 Research 侧签发
    expect(p.handoff.task_scope_sketch.task_id).toBeNull();
    const s = JSON.stringify(p);
    expect(s).not.toMatch(/URO-/);
    expect(s).not.toMatch(/"task_id":\s*"R\d/);
  });

  it('★★ 导出内容不得含评价性 / 交易性用语（沿用项目既有约定：硬禁 + 否定语境）', () => {
    const p = buildResearchRequestPayload(linked('汽车'), null, NOW);
    const s = JSON.stringify(p) + renderResearchRequestMarkdown(p);

    // ① 硬禁：任何语境下都不许出现（与 timeObservationPatterns 的 hard 列表同源）
    for (const hard of ['推荐', '目标价', '胜率', '大概率', '买入区', '布局窗口', '荐股', '排名第一']) {
      expect(s, `导出内容不得含「${hard}」`).not.toContain(hard);
    }

    // ② 只允许出现在**否定语境**里（如免责声明「不含评分；不做排序；…」）
    for (const phrase of ['评分', '排序', '概率', '预测', '买入', '卖出', '信号', '仓位']) {
      let i = s.indexOf(phrase);
      while (i >= 0) {
        const before = s.slice(Math.max(0, i - 12), i);
        expect(
          ['不', '非', '无', '未', '禁止'].some((n) => before.includes(n)),
          `「${phrase}」只能出现在否定语境（实际上下文：…${s.slice(Math.max(0, i - 20), i + phrase.length)}…）`,
        ).toBe(true);
        i = s.indexOf(phrase, i + 1);
      }
    }
  });

  it('★ 明示「草稿不落库 / 未上传 / 无 LLM」', () => {
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    const s = p.constraints.join('\n');
    expect(s).toContain('草稿');
    expect(s).toContain('未上传');
    expect(s).toContain('数据库');
    expect(p.constraints).toEqual(DRAFT_CONSTRAINTS);
  });
});

/* ---------------------------------------------- 2. 语义边界必须随草稿带走 */

describe('研究请求草稿 · 语义边界', () => {
  it('★★ 「主题名命中 ≠ 结构对应」「未覆盖 ≠ 结构上不存在对应」都在导出里', () => {
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    const joined = p.known_limitations.join('\n');
    expect(joined).toContain('结构对应');
    expect(joined).toContain('未覆盖');
    expect(joined).toContain('不等于');
    expect(p.known_limitations).toEqual(KNOWN_LIMITATIONS);
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('主题名命中');
    expect(md).toContain('结构对应');
    expect(md).toContain('未覆盖');
    expect(md).toContain('未经审查');
  });
});

/* ---------------------------------------------- 3. ★★ 关联：请求原文 ↔ 查询证据 */

describe('研究请求草稿 · 查询关联（v0.7）', () => {
  const cases: [string, string][] = [
    ['汽车', 'both'],
    ['军工', 'historical-only'],
    ['文化传媒', 'historical-only'],
    ['动力煤', 'none'],
  ];

  it('★ 四态结论与命中明细随草稿导出（证据取自**冻结快照**）', () => {
    for (const [q, expected] of cases) {
      const r = lookupDirection(q, source, dataset);
      expect(r.verdict, q).toBe(expected);
      const p = buildResearchRequestPayload(linked(q), null, NOW);
      expect(p.coverage_check.executed).toBe(true);
      expect(p.coverage_check.query).toBe(q);
      expect(p.coverage_check.verdict).toBe(expected);
      expect(p.linkage.linked_query).toBe(q);
      expect(p.linkage.evidence_source).toBe('frozen_snapshot');
      // 命中集合与查询结果**逐条一致**（草稿不得改写命中）
      expect(p.coverage_check.current_objects.map((o) => o.id))
        .toEqual(r.current.map((h) => h.id));
      expect(p.coverage_check.historical_cases.map((o) => o.id))
        .toEqual(r.historical.map((h) => h.id));
    }
  });

  it('★★ 未关联查询时：`verdict` 为 **null**（不得用默认 none 冒充「两侧都没覆盖」）', () => {
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    expect(p.coverage_check.executed).toBe(false);
    expect(p.coverage_check.verdict).toBeNull();
    expect(p.coverage_check.query).toBe('');
    expect(p.coverage_check.verdict_meaning).toContain('未执行覆盖查询');
    expect(p.coverage_check.verdict_meaning).toContain('不是「未覆盖」');
    expect(p.linkage.evidence_unavailable).toBe(true);
    // Markdown 也必须诚实（不得出现 `结论：**none**`）
    const md = renderResearchRequestMarkdown(p);
    expect(md).not.toContain('结论：**none**');
    expect(md).toContain('未关联任何覆盖查询');
  });

  it('★★ 换了查询词：新证据**不得**静默附加到旧草稿（只披露 changed）', () => {
    // 草稿关联「汽车」，但界面当前查询是「医药」
    const draft = linked('汽车');
    const live = lookupDirection('医药', source, dataset);
    const p = buildResearchRequestPayload(draft, live, NOW);

    // 证据仍是汽车那次（冻结），不是医药
    expect(p.coverage_check.query).toBe('汽车');
    expect(p.coverage_check.verdict).toBe('both');
    expect(p.coverage_check.current_objects.map((o) => o.id))
      .toEqual(lookupDirection('汽车', source, dataset).current.map((h) => h.id));
    // 但**披露**了「当前查询与证据不同」
    expect(p.linkage.current_query).toBe('医药');
    expect(p.linkage.changed).toBe(true);
    expect(p.linkage.note).toContain('两者不同');
    expect(p.linkage.note).toContain('未**附加**到本草稿'.replace(/\*\*/g, '') === '' ? '' : '未');
    // Markdown 同样披露
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('医药');
    expect(md).toContain('与关联查询不同');
  });

  it('★★ 用户细化方向（≠ 查询词）时：两个字符串**都保留**，不做相似度归并', () => {
    const draft: ResearchRequestDraft = { ...linked('汽车'), direction: '智能驾驶合规化' };
    const p = buildResearchRequestPayload(draft, lookupDirection('汽车', source, dataset), NOW);
    expect(p.request.direction).toBe('智能驾驶合规化'); // 用户原文不被覆盖
    expect(p.linkage.linked_query).toBe('汽车');          // 证据归属不被改写
    expect(p.linkage.changed).toBe(false);                // 查询词没变 → 不谎报变更
  });

  it('★ `changed` 只做字符串比较（不做语义 / 相似度判断）', () => {
    const draft = linked('汽车');
    // 「汽车零部件」不是「汽车」—— 事实是「不同」，不得被归并
    const p = buildResearchRequestPayload(draft, lookupDirection('汽车零部件', source, dataset), NOW);
    expect(p.linkage.changed).toBe(true);
    expect(p.linkage.current_query).toBe('汽车零部件');
    expect(p.coverage_check.query).toBe('汽车'); // 证据不被替换
  });

  it('★ 恢复草稿（无 live 查询）时：证据来自冻结快照，不标 changed', () => {
    const p = buildResearchRequestPayload(linked('文化传媒'), null, NOW);
    expect(p.coverage_check.executed).toBe(true);
    expect(p.coverage_check.verdict).toBe('historical-only');
    expect(p.linkage.current_query).toBe('');
    expect(p.linkage.changed).toBe(false);
  });

  it('★★ JSON 与 Markdown 的关联关系**一致**（同一套事实）', () => {
    const draft = { ...linked('汽车'), direction: '智能驾驶合规化' };
    const p = buildResearchRequestPayload(draft, lookupDirection('医药', source, dataset), NOW);
    const md = renderResearchRequestMarkdown(p);
    // 请求原文
    expect(md).toContain('智能驾驶合规化');
    // 证据归属查询词（Markdown 里保留强调标记）
    expect(md).toContain('本草稿**关联的查询词**');
    expect(md).toContain('`汽车`');
    // 当前查询 + 变更披露
    expect(md).toContain('`医药`');
    expect(md).toContain('与关联查询不同');
    // 命中集合
    expect(md).toContain('C-2019-AD');
    // 限制
    expect(md).toContain('主题名命中');
  });
});

/* ---------------------------------------------- 4. 字段处理 */

describe('研究请求草稿 · 字段处理', () => {
  it('多行文本按行拆分、去空白、保留顺序', () => {
    expect(toLines('a\n\n  b  \n c')).toEqual(['a', 'b', 'c']);
    expect(toLines('')).toEqual([]);
  });

  it('缺必填项时如实列出，但**不**阻止导出（草稿允许不完整）', () => {
    expect(missingDraftFields(EMPTY_DRAFT)).toEqual(['研究方向', '希望回答的研究问题']);
    expect(isDraftEmpty(EMPTY_DRAFT)).toBe(true);
    const p = buildResearchRequestPayload(EMPTY_DRAFT, null, NOW);
    expect(p.request.research_questions).toEqual([]);
    expect(p.status).toBe('DRAFT_NOT_REVIEWED'); // 仍可导出，仍是草稿
    expect(missingDraftFields(FULL_DRAFT)).toEqual([]);
    expect(isDraftEmpty(FULL_DRAFT)).toBe(false);
  });

  it('★ 空方向**不再**由查询词兜底（v0.7：请求原文与证据分离，不混角色）', () => {
    const p = buildResearchRequestPayload(EMPTY_DRAFT, lookupDirection('医药', source, dataset), NOW);
    expect(p.request.direction).toBe('');            // 用户没填就是没填
    expect(p.linkage.current_query).toBe('医药');     // 查询词只出现在关联事实里
    expect(p.handoff.task_scope_sketch.family_directions).toEqual([]);
  });

  it('★ 同输入 → 同输出（确定性，便于用户核对与 diff）', () => {
    const a = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    const b = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it('★ `draft_version` 已升到 0.3（新增 matched_on 与关联语义）', () => {
    expect(buildResearchRequestPayload(FULL_DRAFT, null, NOW).draft_version).toBe('0.3');
  });
});

/* ---------------------------------------------- 5. UI（只断言 props 驱动的渲染事实） */

/**
 * ★★ 关于本段的**能力边界**（v0.7 诚实声明，见 docs/PROJECT_STATE.md）：
 *   测试环境是 `environment: 'node'`（无 jsdom）→ **`useEffect` 不执行、点击不可模拟**。
 *   因此本段只验证「**给定 props 时的渲染输出**」：
 *     · 文案 / 字段 / 按钮是否存在
 *     · **存储状态、关联披露**是否正确渲染（这些完全由 props 决定，可静态验证）
 *   而**不**声称验证了任何交互后的状态（保存 / 恢复 / 清空 / 回填）。
 *   那些行为由 `researchRequestDraftStorage.test.ts` 以**纯函数 + 注入存储**覆盖。
 */
describe('研究请求草稿 · UI 渲染（props 驱动）', () => {
  const sectionHtml = renderToStaticMarkup(
    <DirectionLookupSection source={source} dataset={dataset} draftStorage={null} />,
  );

  const block = (over: Partial<React.ComponentProps<typeof ResearchRequestDraftBlock>> = {}) => {
    const draft = over.draft ?? linked('汽车');
    const lookup = over.lookup !== undefined ? over.lookup : lookupDirection('汽车', source, dataset);
    const payload = buildResearchRequestPayload(draft, lookup, NOW);
    return renderToStaticMarkup(
      <ResearchRequestDraftBlock
        lookup={lookup}
        draft={draft}
        setDraft={() => {}}
        payload={payload}
        payloadJson={JSON.stringify(payload, null, 2)}
        payloadMd={renderResearchRequestMarkdown(payload)}
        copied={null}
        onCopy={() => {}}
        onClear={() => {}}
        onRelink={() => {}}
        queryChanged={false}
        saveState={{ ok: true, action: 'written' }}
        loadState={{ status: 'empty' }}
        copyError={null}
        previewOpen={false}
        onPreviewOpenChange={() => {}}
        {...over}
      />,
    );
  };

  it('★ 方向查询仍在（不因加草稿而破坏既有能力）', () => {
    expect(sectionHtml).toContain('查一个方向');
    expect(sectionHtml).toContain('这是查找，不是结构对应');
  });

  it('★★ 无查询且草稿为空 → **不**渲染草稿区（语义守卫：未查询不得出现「未覆盖 ≠ …」）', () => {
    expect(sectionHtml).not.toContain('研究请求草稿');
    expect(sectionHtml).not.toContain('不等于');
  });

  it('★★ 草稿区明示「不自动进入研究库 / 不自动获得正式编号 / 不上传」', () => {
    const html = block();
    expect(html).toContain('研究请求草稿');
    expect(html).toContain('草稿不会自动进入研究库');
    expect(html).toContain('不会自动获得正式编号');
    expect(html).toContain('存在本机，不上传');
  });

  it('★ 五个草稿字段都在（方向 / 问题 / 为什么 / 线索 / 时间范围）', () => {
    const html = block();
    for (const label of ['研究方向', '希望回答的研究问题（一行一条）', '为什么关注这个方向',
      '已知线索 / 来源（可选，一行一条）', '希望调查的历史时间范围']) {
      expect(html, label).toContain(label);
    }
  });

  it('★ 导出区提供 JSON 与 Markdown **只读预览**（不依赖剪贴板）', () => {
    // ★ 不声称「剪贴板失败时可用」—— 那需要 DOM；这里只验证只读框本身存在
    const html = block();
    expect(html).toContain('复制 JSON');
    expect(html).toContain('复制 Markdown');
    expect(html).toContain('草稿 JSON');
    expect(html).toContain('草稿 Markdown');
    expect(html).toContain('threec_research_request_draft');
    expect(html.toLowerCase()).toContain('readonly'); // SSR 输出小写属性名
  });

  it('★★ 存储**不可用**时必须显示「刷新后会丢失」，不得声称已保存', () => {
    const html = block({ saveState: { ok: false, reason: 'unavailable', detail: 'no window' } });
    expect(html).toContain('本机存储不可用');
    expect(html).toContain('刷新后会丢失');
    expect(html).not.toContain('（已保存）');
  });

  it('★★ 保存**失败**时必须显示「未保存」，不得假装成功', () => {
    const html = block({ saveState: { ok: false, reason: 'write_failed', detail: 'QuotaExceededError' } });
    expect(html).toContain('草稿未能保存到本机');
    expect(html).toContain('未保存到本机');
    expect(html).not.toContain('（已保存）');
  });

  it('★★ 读到**损坏**记录时必须披露，而不是装作没发生过', () => {
    const html = block({ loadState: { status: 'corrupt', reason: 'json', rawLength: 12 } });
    expect(html).toContain('无法使用的旧草稿记录');
    expect(html).toContain('JSON 语法损坏');
  });

  it('★ 恢复时字段被规范化 → 披露「已安全降级」', () => {
    const html = block({
      loadState: { status: 'loaded', draft: linked('汽车'), issues: ['direction 类型错误（number）→ 已置空'] },
    });
    expect(html).toContain('不合法的字段');
    expect(html).toContain('direction 类型错误');
  });

  it('★★ 证据归属与当前查询不同时 → 必须披露（不得静默）', () => {
    const html = block({
      draft: linked('汽车'),
      lookup: lookupDirection('医药', source, dataset),
      queryChanged: true,
    });
    expect(html).toContain('本草稿的覆盖查询证据');
    expect(html).toContain('汽车');
    expect(html).toContain('与本草稿的证据不同');
    expect(html).toContain('未');
  });

  it('★★ 未关联查询的草稿 → 明说「没有查询证据」，不冒充「未覆盖」', () => {
    const html = block({ draft: { ...FULL_DRAFT }, lookup: null });
    expect(html).toContain('未关联任何查询');
    expect(html).toContain('没有');
    expect(html).toContain('不代表「未覆盖」');
  });

  it('★ 清空与「以当前查询新建草稿」是两个**不同**按钮（清空 ≠ 重新建立关联）', () => {
    const html = block({ lookup: lookupDirection('汽车', source, dataset) });
    expect(html).toContain('清空草稿');
    expect(html).toContain('以当前查询新建草稿');
  });
});

/* ---------------------------------------------- 6. v0.8：一次性关联 + 命中依据 + 旧数据兼容 */

describe('v0.8 · buildLinkedDraft（一次性建立完整关联）', () => {
  it('★★ 新草稿四件套齐全：direction + linkedQuery + linkedAt + linkedCoverage', () => {
    const r = lookupDirection('汽车', source, dataset);
    const d = buildLinkedDraft('汽车', r, NOW);
    expect(d.direction).toBe('汽车');
    expect(d.linkedQuery).toBe('汽车');
    expect(d.linkedAt).toBe(NOW);
    expect(d.linkedCoverage).not.toBeNull();
    expect(d.linkedCoverage!.query).toBe('汽车');
    expect(d.linkedCoverage!.verdict).toBe('both');
    expect(d.linkedCoverage!.current.length).toBeGreaterThan(0);
    // 用户文本字段是空的（新建草稿不预填用户内容）
    expect(d.researchQuestions).toBe('');
    expect(isDraftBlank(d)).toBe(false);
  });

  it('★★ 用 buildLinkedDraft 建的草稿导出后**不等于**「未关联」', () => {
    const r = lookupDirection('医药', source, dataset);
    const p = buildResearchRequestPayload(buildLinkedDraft('医药', r, NOW), r, NOW);
    expect(p.linkage.evidence_source).toBe('frozen_snapshot');
    expect(p.coverage_check.executed).toBe(true);
    expect(p.coverage_check.verdict).toBe('both');
    expect(p.request.direction).toBe('医药');
    const md = renderResearchRequestMarkdown(p);
    expect(md).not.toContain('未关联任何覆盖查询');
    expect(md).toContain('医药');
  });
});

describe('v0.8 · 命中依据（matched_on）全程不丢', () => {
  it('★★ 当前草稿：matched_on 是**真实依据**（与查询结果的 matchedOn 逐条一致）', () => {
    const r = lookupDirection('汽车', source, dataset);
    const p = buildResearchRequestPayload(buildLinkedDraft('汽车', r, NOW), null, NOW);
    expect(p.coverage_check.current_objects[0].matched_on)
      .toEqual(r.current[0].matchedOn);
    expect(p.coverage_check.historical_cases[0].matched_on)
      .toEqual(r.historical[0].matchedOn);
    // Markdown 也把依据写出来
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('命中');
    for (const m of r.current[0].matchedOn) expect(md, m).toContain(m);
  });

  it('★★ **旧草稿**（linkedCoverage 无 matchedOn）→ matched_on = null + 明说「未保存该信息」', () => {
    // 模拟 v0.7 留下来的本机记录：只有 id/title，没有 matchedOn
    const oldStyle = {
      query: '汽车',
      verdict: 'both',
      current: [{ id: 'CC-2026-AUTO-SMARTDRIVE', title: '智能驾驶合规化（L3/L4 强制国标—责任划分—量产准入）' }],
      historical: [{ id: 'C-2019-AD', title: '自动驾驶' }],
      resolution: null,
      captured_at: NOW,
    } as unknown as ResearchRequestDraft['linkedCoverage'];
    const draft = { ...FULL_DRAFT, linkedQuery: '汽车', linkedAt: NOW, linkedCoverage: oldStyle };
    const p = buildResearchRequestPayload(draft, null, NOW);
    expect(p.coverage_check.executed).toBe(true);
    expect(p.coverage_check.current_objects[0].matched_on).toBeNull();   // ★ 不是 []
    expect(p.coverage_check.historical_cases[0].matched_on).toBeNull();
    // Markdown 明说，而不是留空让人以为「没有依据」
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('命中依据：未保存该信息（旧草稿）');
  });

  it('★ normalizeDraft 保留 matchedOn（三态：数组 / null / 缺键）', () => {
    const withArr = normalizeDraft({ direction: 'x', linkedQuery: '汽车', linkedCoverage: {
      query: '汽车', verdict: 'both',
      current: [{ id: 'A', title: 'a', matchedOn: ['汽车'] }],
      historical: [], resolution: null, captured_at: NOW,
    } });
    expect(withArr.draft.linkedCoverage?.current[0].matchedOn).toEqual(['汽车']);
    expect(withArr.issues).toEqual([]);

    const withoutKey = normalizeDraft({ direction: 'x', linkedQuery: '汽车', linkedCoverage: {
      query: '汽车', verdict: 'both',
      current: [{ id: 'A', title: 'a' }],
      historical: [], resolution: null, captured_at: NOW,
    } });
    expect(withoutKey.draft.linkedCoverage?.current[0].matchedOn).toBeNull();

    const badType = normalizeDraft({ direction: 'x', linkedQuery: '汽车', linkedCoverage: {
      query: '汽车', verdict: 'both',
      current: [{ id: 'A', title: 'a', matchedOn: '汽车' }],
      historical: [], resolution: null, captured_at: NOW,
    } });
    expect(badType.draft.linkedCoverage?.current[0].matchedOn).toBeNull(); // 不得强转成 ["汽","车"]
  });
});
