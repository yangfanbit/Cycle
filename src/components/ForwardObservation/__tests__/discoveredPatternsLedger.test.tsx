/**
 * 候选账本 → 前端渲染（v0.50）。
 *
 * 断言的是**不能误读**的四件事：
 *  ① 账本元信息必须出现（候选数 / 已结算 / 待结算），不能只存在于 JSON；
 *  ② 「本月已实现部分」必须带**锚点**与三档结果，且 20 日必须是「待结算」而不是 0；
 *  ③ 未开始的候选必须写「窗口未开始」，**不得**用 0.00% 冒充「没有表现」；
 *  ④ 必须显式标注「已实现部分不是样本外前瞻」——否则会被读成前瞻验证。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { DiscoveredPatterns } from '../DiscoveredPatterns';
import summary from '@current/pattern_discovery_summary_v0_1.json';
import digest from '@current/candidate_digest_v0_12.json';

const html = renderToStaticMarkup(<DiscoveredPatterns />);
/** 首页「季节性统计窗口」预览的 6 条 id（用于核对两处列表的关系） */
const digestPreview = ((digest as unknown as {
  sections?: { seasonal_preview?: { ids: string[] } };
}).sections?.seasonal_preview?.ids ?? []);

describe('季节性发现 · 候选账本渲染', () => {
  it('★ 账本元信息出现：候选数 / 5·10 日已结算 / 20 日待结算', () => {
    const d = summary as unknown as {
      ledger: { as_of: string; summary: { candidates: number;
        by_outcome_type: Record<string, number>;
        horizon_status: Record<string, Record<string, number>> } };
    };
    expect(d.ledger, '摘要必须带 ledger 段').toBeTruthy();
    expect(html).toContain(`data-ledger="${d.ledger.as_of}"`);
    expect(html).toContain('候选账本');
    // 计数与产物一致（不写死数字，按产物断言）
    expect(d.ledger.summary.candidates).toBeGreaterThan(0);
    expect(html).toContain(String(d.ledger.summary.candidates));
    // ★★ 键是 "5d"/"10d"/"20d"：写错成 "5" 会静默显示 0 —— 必须按产物断言真实数字
    const hs = d.ledger.summary.horizon_status;
    expect(hs['5d']?.AVAILABLE ?? 0).toBeGreaterThan(0);
    expect(html).toContain(`5 日已结算 <strong>${hs['5d'].AVAILABLE}</strong>`);
    expect(html).toContain(`10 日已结算 <strong>${hs['10d'].AVAILABLE}</strong>`);
    expect(html).toContain(`20 日待结算 <strong>${hs['20d'].PENDING}</strong>`);
  });

  it('★★ 本月已实现部分：带锚点、5/10 日有数字、20 日待结算', () => {
    const d = summary as unknown as {
      realized_windows: {
        pattern_id: string; outcome: { anchor: string | null;
          horizons: Record<'5' | '10' | '20', { status: string; excess_pp?: number | null }> };
      }[];
    };
    expect(d.realized_windows.length).toBeGreaterThan(0);
    expect(html).toContain(`data-realized-windows="${d.realized_windows.length}"`);
    for (const w of d.realized_windows) {
      expect(html).toContain(`data-realized="${w.pattern_id}"`);
      expect(w.outcome.anchor).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      // 5/10 已结算 → 必须有超额数字；20 日必须 PENDING（不补 0）
      expect(w.outcome.horizons['5'].status).toBe('AVAILABLE');
      expect(w.outcome.horizons['5'].excess_pp).not.toBeNull();
      expect(w.outcome.horizons['20'].status).toBe('PENDING');
      expect(w.outcome.horizons['20'].excess_pp).toBeNull();
    }
    expect(html).toContain('待结算');
  });

  it('★★ 未开始的候选写「窗口未开始」，不得用 0.00% 冒充', () => {
    expect(html).toContain('窗口未开始');
    // 账本里 NOT_STARTED 的候选其 excess 必为 null（结构断言）
    const d = summary as unknown as {
      top_windows: { outcome?: { horizons: Record<string, { status: string; excess_pp?: number | null }> } | null }[];
    };
    const notStarted = d.top_windows.filter((w) => w.outcome?.horizons['5']?.status === 'NOT_STARTED');
    expect(notStarted.length).toBeGreaterThan(0);
    for (const w of notStarted) {
      expect(w.outcome!.horizons['5'].excess_pp).toBeNull();
    }
  });

  it('★★ 必须显式说明「已实现部分不是样本外前瞻」', () => {
    expect(html).toContain('data-realized-caveat="1"');
    expect(html).toContain('不是');
    expect(html).toContain('样本外前瞻');
    // 也不得出现评分/排名式措辞
    expect(html).not.toMatch(/胜率|推荐|买入|目标价/);
  });

  /**
   * ★★ v0.66 更正：v0.65 曾写「与首页季节性预览是**同一批**模式」——
   * 实测两处六条**没有交集**（选取规则不同：首页综合排序 + 同月 ≤3；本区按历史中位超额取前六）。
   * 本用例同时钉住「文案不再说同一批」与「两组列表本来就可能不一致」这个事实。
   */
  it('★★ 与首页季节预览：同源但**筛选规则不同**，不得声称「同一批」', () => {
    const d = summary as unknown as { top_windows: { pattern_id: string }[] };
    const top6 = (d.top_windows ?? []).slice(0, 6).map((w) => w.pattern_id);
    expect(top6.length).toBe(6);

    // 产物层面的事实：两组列表不重合（若将来真的重合，应重新评估这条文案，而不是断言恒等）
    expect(digestPreview).not.toEqual(top6);

    // 文案层面：必须写清「同一份数据 + 规则不同 + 可能不一致」，且不得再说「同一批」
    expect(html).toContain('data-source-note="same-artifact-different-selection"');
    expect(html).toContain('来自同一份历史模式数据');
    expect(html).toContain('筛选与排序规则不同');
    expect(html).toContain('可能不一致');
    expect(html).not.toContain('同一批');
  });
});
