/**
 * 候选追踪（跨月滚动）→ 前端渲染（v0.51）。
 *
 * 断言的是**不能误读**的六件事：
 *  ① 形成元信息必须出现（批次数 / 累计实例 / 最早形成日 / 结算日），不能只存在于 JSON；
 *  ② 5/10/20 三档「已结算 / 待结算」必须按**产物真实数字**渲染（写错键名会静默显示 0）；
 *  ③ 每一行必须能区分「前瞻」与「窗口内」——否则窗口内观察会被读成样本外验证；
 *  ④ 未结算的档位必须给明确状态，**不得**用 0.00% 冒充；
 *  ⑤ 行序必须与产物一致（**不按结果重排**），否则会变成隐性业绩榜；
 *  ⑥ 形成记录不可变 / 不排名 / 无信号 —— 必须在页面文字里说清。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { CandidateTracking } from '../CandidateTracking';
import summary from '@current/pattern_discovery_summary_v0_1.json';

interface TH { status: string; board_ret: number | null; excess_pp: number | null; settle_date: string | null }
interface TI {
  instance_id: string; board: string; month: number; batch_id: string | null;
  formed_at: string; anchor: string | null; outcome_type: string;
  horizons: Record<'5' | '10' | '20', TH>;
}
interface T {
  market_as_of: string;
  formation_log: { batches: number; instances: number; earliest_formed_at: string };
  formation_run: { new_instances: number; reappeared: number } | null;
  batches: { batch_id: string; formed_at: string; new_instances: number }[];
  settled: Record<string, number>; pending: Record<string, number>;
  instances: TI[];
}

const d = (summary as unknown as { tracking?: T | null }).tracking as T;
const html = renderToStaticMarkup(<CandidateTracking />);

describe('候选追踪 · 跨月滚动', () => {
  it('① 形成元信息出现，且与产物一致', () => {
    expect(d, '摘要必须带 tracking 段').toBeTruthy();
    expect(html).toContain(`data-tracking="${d.market_as_of}"`);
    expect(html).toContain(`data-track-meta="${d.formation_log.batches}/${d.instances.length}"`);
    expect(html).toContain(`最早形成 <strong>${d.formation_log.earliest_formed_at}</strong>`);
    expect(html).toContain('形成批次');
    expect(d.instances.length).toBe(d.formation_log.instances);
  });

  it('② 5/10/20 已结算·待结算按产物真实数字渲染', () => {
    for (const h of ['5d', '10d', '20d'] as const) {
      const s = d.settled[h];
      const p = d.pending[h];
      // ★ 已结算 + 待结算 必须等于实例总数（口径自洽，防漏算）
      expect(s + p).toBe(d.instances.length);
      expect(html).toContain(`已结算 ${s} / 待 ${p}`);
    }
    // 至少有一档真的结算了 —— 否则上面的断言会「全 0 也通过」
    expect(d.settled['5d']).toBeGreaterThan(0);
  });

  it('③ 每行都能区分「前瞻」与「窗口内」', () => {
    const otypes = new Set(d.instances.map((i) => i.outcome_type));
    expect(otypes.size).toBeGreaterThan(1);
    for (const o of otypes) {
      expect(html).toContain(`data-otype="${o}"`);
    }
    expect(html).toContain('（窗口开始前形成）');
    expect(html).toContain('（形成时窗口已开始）');
    // 「窗口内」必须与锚点自洽：形成日不早于锚点
    for (const i of d.instances.filter((x) => x.outcome_type === 'IN_WINDOW_PARTIAL')) {
      expect(i.anchor).not.toBeNull();
      expect(i.formed_at >= i.anchor!).toBe(true);
    }
    for (const i of d.instances.filter((x) => x.outcome_type === 'FORWARD_PENDING')) {
      if (i.anchor) expect(i.formed_at < i.anchor).toBe(true);
    }
  });

  it('④ 未结算给明确状态，已结算给真实数字（不补 0）', () => {
    const pendingRow = d.instances.find((i) => i.horizons['20'].status === 'PENDING');
    expect(pendingRow, '应存在 20 日待结算实例').toBeTruthy();
    expect(pendingRow!.horizons['20'].excess_pp).toBeNull();
    expect(html).toContain('待结算');

    const settledRow = d.instances.find((i) => i.horizons['5'].status === 'AVAILABLE');
    expect(settledRow, '应存在 5 日已结算实例').toBeTruthy();
    const v = settledRow!.horizons['5'].excess_pp!;
    expect(v).not.toBeNull();
    // 按产物数字断言（不写死），且必须带正负号
    expect(html).toContain(`${v > 0 ? '+' : ''}${v.toFixed(2)}pp`);
  });

  it('⑤ 行序与产物一致（不按结果重排）', () => {
    const ids = [...html.matchAll(/data-track-row="([^"]+)"/g)].map((m) => m[1]);
    expect(ids.length).toBe(d.instances.length);
    expect(ids).toEqual(d.instances.map((i) => i.instance_id));
  });

  it('⑥ 说明形成记录不可变 / 不排名 / 无信号', () => {
    expect(html).toContain('data-track-caveat="1"');
    expect(html).toContain('追加式日志');
    expect(html).toContain('不按结果排名');
    expect(html).toContain('不是');
    expect(html).toContain('样本外前瞻');
    // ★ 渲染后不得残留裸 Markdown 星号（RichText 必须真的生效）
    expect(html).not.toMatch(/\*\*/);
    // ★ 与页面级不变量（`forwardObservation.test.tsx`）用**同一组**禁用词，
    //   不要自造一套：本组件文案里用的是「打分」，页面级禁的是「评分」——两者不要混。
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分']) {
      expect(html, `不应出现「${banned}」`).not.toContain(banned);
    }
  });
});
