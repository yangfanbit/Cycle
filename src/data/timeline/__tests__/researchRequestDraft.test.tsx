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
  buildResearchRequestPayload,
  isDraftEmpty,
  missingDraftFields,
  renderResearchRequestMarkdown,
  toLines,
  type ResearchRequestDraft,
} from '../researchRequestDraft';
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
};

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
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    const s = JSON.stringify(p) + renderResearchRequestMarkdown(p);

    // ① 硬禁：任何语境下都不许出现（与 timeObservationPatterns 的 hard 列表同源）
    for (const hard of ['推荐', '目标价', '胜率', '大概率', '买入区', '布局窗口', '荐股', '排名第一']) {
      expect(s, `导出内容不得含「${hard}」`).not.toContain(hard);
    }

    // ② 只允许出现在**否定语境**里（如免责声明「不含评分 / 排序 / 概率 / 预测 / 买卖信号」）
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
    expect(joined).toContain('不等于**结构对应**'.replace(/\*\*/g, '') === '' ? '' : '结构对应');
    expect(joined).toContain('未覆盖');
    expect(joined).toContain('不等于');
    expect(p.known_limitations).toEqual(KNOWN_LIMITATIONS);
    // Markdown 也要带（用户粘出去的才是这一份）
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('主题名命中');
    expect(md).toContain('结构对应');
    expect(md).toContain('未覆盖');
    expect(md).toContain('未经审查');
  });
});

/* ---------------------------------------------- 3. 覆盖查询四态衔接 */

describe('研究请求草稿 · 覆盖查询衔接', () => {
  const cases: [string, string][] = [
    ['汽车', 'both'],
    ['军工', 'historical-only'],
    ['文化传媒', 'historical-only'],
    ['动力煤', 'none'],
  ];

  it('★ 四态结论与命中明细随草稿导出（用户与审查者看到同一份事实）', () => {
    for (const [q, expected] of cases) {
      const lookup = lookupDirection(q, source, dataset);
      expect(lookup.verdict, q).toBe(expected);
      const p = buildResearchRequestPayload({ ...FULL_DRAFT, direction: q }, lookup, NOW);
      expect(p.coverage_check.query).toBe(q);
      expect(p.coverage_check.verdict).toBe(expected);
      expect(p.coverage_check.verdict_meaning.length).toBeGreaterThan(0);
      // 命中集合与查询结果**逐条一致**（草稿不得改写命中）
      expect(p.coverage_check.current_objects.map((o) => o.id))
        .toEqual(lookup.current.map((h) => h.id));
      expect(p.coverage_check.historical_cases.map((o) => o.id))
        .toEqual(lookup.historical.map((h) => h.id));
    }
  });

  it('★ 未执行查询时如实标注，而不是伪造一个 none 结论', () => {
    const p = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    expect(p.coverage_check.query).toBe('');
    expect(p.coverage_check.verdict_meaning).toContain('未执行覆盖查询');
  });

  it('★ 查询方向自动成为草稿方向（用户不必重打）', () => {
    const p = buildResearchRequestPayload(
      { ...EMPTY_DRAFT, researchQuestions: 'q' },
      lookupDirection('医药', source, dataset),
      NOW,
    );
    expect(p.request.direction).toBe('医药');
  });
});

/* ---------------------------------------------- 4. 草稿字段处理 */

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

  it('★ 同输入 → 同输出（确定性，便于用户核对与 diff）', () => {
    const a = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    const b = buildResearchRequestPayload(FULL_DRAFT, null, NOW);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });
});

/* ---------------------------------------------- 5. UI：入口存在且不误导 */

describe('研究请求草稿 · UI 入口', () => {
  const sectionHtml = renderToStaticMarkup(
    <DirectionLookupSection source={source} dataset={dataset} />,
  );

  /** 草稿区（只在查询后出现）—— 直接渲染以便断言（SSR 无法模拟输入） */
  // ★ 用「娱乐」：实测 verdict = none（两侧都没命中）。
  //   注意「教育」**不是** none —— 它被当前候选命中 → current-only（实测）。
  const lookup = lookupDirection('娱乐', source, dataset);
  const payload = buildResearchRequestPayload(FULL_DRAFT, lookup, NOW);
  const blockHtml = renderToStaticMarkup(
    <ResearchRequestDraftBlock
      lookup={lookup}
      draft={FULL_DRAFT}
      setDraft={() => {}}
      payload={payload}
      payloadJson={JSON.stringify(payload, null, 2)}
      payloadMd={renderResearchRequestMarkdown(payload)}
      copied={null}
      onCopy={() => {}}
    />,
  );

  it('★ 方向查询仍在（不因加草稿而破坏既有能力）', () => {
    expect(sectionHtml).toContain('查一个方向');
    expect(sectionHtml).toContain('这是查找，不是结构对应');
  });

  it('★★ 未查询时**不**渲染草稿区（语义守卫：未查询不得出现「未覆盖 ≠ …」解释）', () => {
    expect(sectionHtml).not.toContain('研究请求草稿');
    expect(sectionHtml).not.toContain('不等于');
  });

  it('★★ 草稿区明示「不自动进入研究库 / 不自动获得正式编号 / 不上传」', () => {
    expect(blockHtml).toContain('研究请求草稿');
    expect(blockHtml).toContain('草稿不会自动进入研究库');
    expect(blockHtml).toContain('不会自动获得正式编号');
    expect(blockHtml).toContain('存在本机，不上传');
  });

  it('★ 五个草稿字段都在（方向 / 问题 / 为什么 / 线索 / 时间范围）', () => {
    for (const label of ['研究方向', '希望回答的研究问题（一行一条）', '为什么关注这个方向',
      '已知线索 / 来源（可选，一行一条）', '希望调查的历史时间范围']) {
      expect(blockHtml, label).toContain(label);
    }
  });

  it('★ 导出区含 JSON 与 Markdown 预览（剪贴板不可用时仍可手动复制）', () => {
    expect(blockHtml).toContain('复制 JSON');
    expect(blockHtml).toContain('复制 Markdown');
    expect(blockHtml).toContain('草稿 JSON');
    expect(blockHtml).toContain('草稿 Markdown');
    expect(blockHtml).toContain('threec_research_request_draft');
  });

  it('★ 草稿区把覆盖查询结论一起显示（用户看到与导出相同的事实）', () => {
    expect(blockHtml).toContain('随草稿一起带走的覆盖查询结果');
    expect(blockHtml).toContain('娱乐');
    expect(blockHtml).toContain('none');
  });
});
