/**
 * 当前前瞻观察 —— 页面级不变量（v0.33）。
 *
 * 只锁「不能误读」的四件事：
 *  ① `as_of` 必须来自产物（观察时点唯一）；
 *  ② 模式状态与候选状态**不得**被页面升格（C 类不能显示成 A 类）；
 *  ③ 「已升温」不得被说成提前发现（页面上必须有该提示）；
 *  ④ 不得出现买卖/评分/目标价类措辞。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  FORWARD_AS_OF,
  FORWARD_OBSERVATION,
  actionableCandidates,
} from '../forwardObservation';
import { ForwardObservationSection } from '../../../components/ForwardObservation/ForwardObservationSection';

const html = renderToStaticMarkup(<ForwardObservationSection />);

describe('当前前瞻观察 · 数据与渲染', () => {
  it('★ as_of 与产物一致，且页面显示观察时点', () => {
    expect(FORWARD_AS_OF).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(html).toContain(`data-forward-as-of="${FORWARD_AS_OF}"`);
    expect(html).toContain('观察时点');
  });

  it('★★ 两个模式都渲染，且状态标签与数据一致（不得升格）', () => {
    for (const p of FORWARD_OBSERVATION.patterns) {
      expect(html).toContain(`data-pattern-id="${p.pattern_id}"`);
      expect(html).toContain(`data-pattern-status="${p.status}"`);
      // C 类不得出现 A 类文案
      if (p.status === 'C_EXPLORATORY') expect(html).not.toContain('A · 重复性较强');
    }
  });

  it('★★ 生肖：可测年份与「不可测年份」必须同时出现（不能只报好看的）', () => {
    const z = FORWARD_OBSERVATION.patterns.find((p) => p.pattern_id === 'ZODIAC_NAME')!;
    expect(z.years!.some((y) => y.testable)).toBe(true);
    expect((z.stats.not_testable_years ?? []).length).toBeGreaterThan(0);
    expect(html).toContain('不可测');
    expect(html).toContain('缺历史名称快照');
  });

  it('★★ 台海：每个事件都渲染「有响应/无响应」，篮子成分偏差必须可见', () => {
    const t = FORWARD_OBSERVATION.patterns.find((p) => p.pattern_id === 'TAIWAN_STRAIT_EVENT')!;
    expect(t.events!.length).toBeGreaterThanOrEqual(5);
    for (const e of t.events!) expect(html).toContain(`data-event="${e.event_id}"`);
    expect(html).toContain('当前成分');
    expect(html).toContain('偏差');
  });

  it('★★ 候选状态可核：只有 PRE_OBSERVATION 算「可执行」', () => {
    expect(html).toContain(`data-actionable-count="${actionableCandidates().length}"`);
    for (const c of FORWARD_OBSERVATION.candidates) {
      expect(html).toContain(`data-candidate-id="${c.candidate_id}"`);
      expect(html).toContain(`data-evidence-status="${c.evidence_status}"`);
    }
    // 「已升温」必须带「不是提前发现」的提示
    if (FORWARD_OBSERVATION.candidates.some((c) => c.evidence_status === 'ALREADY_WARM')) {
      expect(html).toContain('不得');
    }
  });

  it('★ 不得出现买卖信号 / 评分 / 目标价类措辞', () => {
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分']) {
      expect(html, `不应出现「${banned}」`).not.toContain(banned);
    }
  });

  it('★ 正文不得出现裸 Markdown 星号（含 title 属性）', () => {
    expect(html).not.toContain('**');
  });
});
