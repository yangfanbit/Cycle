/**
 * ★★ v0.66：自动发现的新题材线索 —— 首版渲染不变量。
 *
 * 断言的是「不能误读」的五件事：
 *  ① 覆盖范围必须**就地写明**（来源 / 类别 / 日期区间 / 事件数），不能假装是全市场挖掘；
 *  ② 每条事件必须有**可打开的真实来源链接**与状态标签；
 *  ③ 有板块关联的必须显示「命中哪个关键词 + 直接/代理」；无关联的必须明写「未建立关联」；
 *  ④ 行情可核验的必须给**反应窗口 + 板块 + 基准 + 超额 + 交易日数**，缺失走 gaps 而不是补 0；
 *  ⑤ 不得出现打分 / 交易信号式措辞，也不得让 Markdown `**` 原样漏出。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { NewThemeRadarSection } from '../NewThemeRadarSection';
import raw from '@current/new_theme_radar_v0_1.json';

interface D {
  as_of: string; generated_at: string;
  coverage: { sources?: { name: string }[]; date_range?: [string, string] | null; events: number };
  summary: { events: number; candidates: number; by_status: Record<string, number> };
  status_legend: Record<string, string>;
  events: {
    event_id: string; title: string; event_date: string; status: string;
    source: { url: string; name: string };
    theme_links: { board_name: string; board_series: string; keyword: string; relation: string }[];
    market: { status: string; window?: [string, string] | null; excess_pp?: number | null;
      observation_trading_days?: number | null };
    gaps: string[]; evidence_quote?: string | null;
  }[];
}
const doc = raw as unknown as D;
const html = renderToStaticMarkup(<NewThemeRadarSection />);
const text = html.replace(/<[^>]+>/g, ' ');

describe('v0.66 自动发现的新题材线索', () => {
  it('★★ 覆盖范围就地写明：来源 / 日期区间 / 事件数 / as_of', () => {
    expect(html).toContain(`data-radar-as-of="${doc.as_of}"`);
    expect(html).toContain(`data-radar-events="${doc.summary.events}"`);
    expect(html).toContain('第一版 · 覆盖有限');
    for (const s of doc.coverage.sources ?? []) expect(text).toContain(s.name);
    expect(doc.coverage.date_range).toBeTruthy();
    expect(html).toContain(doc.coverage.date_range![0]);
    expect(html).toContain(doc.coverage.date_range![1]);
    // 候选数按产物断言（不写死）
    expect(html).toContain(`data-candidate-count="${doc.summary.candidates}"`);
  });

  it('★★ 每条事件都有真实来源链接与状态标签', () => {
    const shown = doc.events.slice(0, 12);
    for (const e of shown) {
      expect(html).toContain(`data-event="${e.event_id}"`);
      expect(html).toContain(`data-status="${e.status}"`);
      expect(html).toContain(`href="${e.source.url}"`);
      expect(e.source.url.startsWith('https://www.ndrc.gov.cn/')).toBe(true);
    }
    // 状态图例与产物一致
    for (const k of Object.keys(doc.status_legend)) expect(text).toContain(k);
  });

  it('★★ 有板块关联 → 显示命中关键词与「直接/代理」；无关联 → 明写未建立关联', () => {
    const linked = doc.events.find((e) => e.theme_links.length > 0)!;
    expect(linked).toBeTruthy();
    expect(text).toContain(linked.theme_links[0].board_name);
    expect(text).toContain(linked.theme_links[0].keyword);
    expect(html).toMatch(/data-relation="(DIRECT|PROXY)"/);

    const unlinked = doc.events.find((e) => e.theme_links.length === 0)!;
    if (unlinked) expect(text).toContain('未命中显式关键词表');
  });

  it('★★ 行情可核验的显示反应窗口与超额；缺失走 gaps 不补 0', () => {
    const obs = doc.events.find((e) => e.market.status === 'OBSERVED')!;
    expect(obs, '产物里应有 OBSERVED 事件').toBeTruthy();
    expect(html).toContain(obs.market.window![0]);
    expect(html).toContain(obs.market.window![1]);
    expect(text).toContain('反应窗口');
    expect(text).toContain('沪深300');
    expect(text).toContain('超额');
    // 缺数据的必须列出 gaps（广度不可得等），而不是显示 0
    expect(html).toMatch(/data-gaps="\d+"/);
    expect(text).toContain('参与广度无法计算');
  });

  it('★★ 不得出现打分/交易信号式措辞，且 Markdown 星号不得漏出', () => {
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分', '排名', '止损']) {
      expect(text, `不得出现「${banned}」`).not.toContain(banned);
    }
    expect(text).toContain('不是买卖建议');
    expect(text).toContain('不代表');
    expect(text).not.toContain('**');
  });
});
