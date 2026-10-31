/**
 * ★★ v0.67：自动发现的新题材线索 —— 渲染不变量（产物 `new_theme_radar_v0_2`）。
 *
 * 断言的是「不能误读」的六件事：
 *  ① 覆盖范围与抓取失败必须**就地写明**；
 *  ② 每条事件有可打开的真实来源、状态、以及「本次列表仍可见 / 历史保留」；
 *  ③ 关联必须显示命中关键词 + 直接/代理；未关联的必须给**复核结论**；
 *  ④ 逐板块展示窗口与超额（不是只算第一个板块）；
 *  ⑤ **相对 vs 绝对**：绝对收益为负、超额为正时必须写「不证明因果」；
 *  ⑥ 时间口径（基准日 / 观察起点）与证据类型（正文 / 仅附件）可见；不得出现打分式措辞。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { NewThemeRadarSection } from '../NewThemeRadarSection';
import raw from '@current/new_theme_radar_v0_2.json';

interface D {
  as_of: string; generated_at: string; artifact_version?: string;
  coverage: { sources?: { name: string }[]; date_range?: [string, string] | null; events: number;
    failures?: unknown[]; historical_only?: number };
  summary: { events: number; candidates: number; by_status: Record<string, number> };
  status_legend: Record<string, string>;
  events: {
    event_id: string; title: string; event_date: string; status: string;
    presence?: string; first_seen?: string; last_seen?: string;
    source: { url: string };
    time?: { basis_day?: string | null; observe_from?: string | null };
    evidence?: { kind: string; quote?: string | null; quote_sha256_16?: string | null;
      attachments?: { name: string; url: string }[] };
    theme_links: { board_name: string; board_series: string; keyword: string; relation: string }[];
    markets?: { board_series: string; board_name?: string; window?: [string, string] | null;
      excess_pp?: number | null; board_ret_pct?: number | null; observation_trading_days?: number | null }[];
    assessment?: { relative_positive: boolean; absolute_positive: boolean; note: string } | null;
    review?: { verdict: string; note: string } | null;
    gaps: string[];
  }[];
}
const doc = raw as unknown as D;
const html = renderToStaticMarkup(<NewThemeRadarSection />);
const text = html.replace(/<[^>]+>/g, ' ');

describe('v0.67 自动发现的新题材线索', () => {
  it('★★ 覆盖范围写明（来源 / 日期区间 / 事件数 / 候选数），并暴露抓取失败', () => {
    expect(html).toContain(`data-radar-as-of="${doc.as_of}"`);
    expect(html).toContain(`data-radar-version="0.2"`);
    expect(html).toContain(`data-radar-events="${doc.summary.events}"`);
    for (const s of doc.coverage.sources ?? []) expect(text).toContain(s.name);
    expect(doc.coverage.date_range).toBeTruthy();
    expect(html).toContain(doc.coverage.date_range![0]);
    expect(html).toContain(doc.coverage.date_range![1]);
    expect(html).toContain(`data-candidate-count="${doc.summary.candidates}"`);
    // 有失败就必须出现失败块（本轮无失败 → 不出现）
    if ((doc.coverage.failures ?? []).length > 0) {
      expect(html).toContain('data-failures=');
      expect(text).toContain('不完整');
    }
  });

  it('★★ 每条事件：真实来源链接 + 状态 + 采集时间字段', () => {
    const shown = doc.events.slice(0, 12);
    for (const e of shown) {
      expect(html).toContain(`data-event="${e.event_id}"`);
      expect(html).toContain(`data-status="${e.status}"`);
      expect(html).toContain(`href="${e.source.url}"`);
      expect(e.source.url.startsWith('https://www.ndrc.gov.cn/')).toBe(true);
      expect(e.first_seen, `${e.event_id} 必须有首次采集时间`).toBeTruthy();
    }
    for (const k of Object.keys(doc.status_legend)) expect(text).toContain(k);
  });

  it('★★ 关联显示命中关键词与直接/代理；未关联的给复核结论', () => {
    const linked = doc.events.find((e) => e.theme_links.length > 0)!;
    expect(text).toContain(linked.theme_links[0].board_name);
    expect(text).toContain(linked.theme_links[0].keyword);
    expect(html).toMatch(/data-relation="(DIRECT|PROXY)"/);

    const unlinked = doc.events.find((e) => e.theme_links.length === 0 && e.review)!;
    expect(unlinked, '应存在带复核结论的未关联事件').toBeTruthy();
    expect(text).toContain('未命中显式关键词表');
    expect(html).toContain(`data-review="${unlinked.review!.verdict}"`);
  });

  it('★★ 逐板块：每个板块各自的窗口与超额（不是只算第一个）', () => {
    const withMk = doc.events.find((e) => (e.markets ?? []).length > 0)!;
    expect(withMk).toBeTruthy();
    expect(html).toContain(`data-markets="${withMk.markets!.length}"`);
    for (const m of withMk.markets!) {
      expect(html).toContain(`data-market-board="${m.board_series}"`);
    }
    const m0 = withMk.markets![0];
    expect(html).toContain(m0.window![0]);
    expect(html).toContain(m0.window![1]);
    expect(text).toContain('沪深300');
    expect(text).toContain('超额');
  });

  it('★★ 相对 vs 绝对：绝对为负 + 超额为正时必须写「不证明因果」', () => {
    const rel = doc.events.find((e) => e.assessment?.relative_positive && !e.assessment.absolute_positive);
    expect(rel, '本轮应存在「绝对负 / 相对正」的事件').toBeTruthy();
    expect(html).toContain('data-assess="REL_POS"');
    expect(text).toContain('绝对收益为负');
    expect(text).toContain('不证明');
  });

  it('★★ 时间口径与证据类型可见；不得出现打分式措辞或裸 Markdown', () => {
    const e = doc.events.find((x) => x.time?.basis_day)!;
    expect(html).toContain(e.time!.basis_day!);
    expect(text).toContain('基准日');
    expect(text).toContain('观察起点');
    expect(text).toMatch(/正文片段|正文在附件内|无正文/);
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分', '排名', '止损']) {
      expect(text, `不得出现「${banned}」`).not.toContain(banned);
    }
    expect(text).toContain('不是买卖建议');
    expect(text).not.toContain('**');
  });
});
