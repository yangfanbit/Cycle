/**
 * ★★ v0.68：自动发现的新题材线索 —— 候选可见性与逐板块语义（产物 `new_theme_radar_v0_3`）。
 *
 * 两个真实缺陷的回归：
 *  A. 原实现只渲染 `events.slice(0, 12)` → **较早的候选事件在页面上根本找不到**
 *     （实测 2026-09-24 成品油候选不在最近 12 条内）。现在候选区**全部展示**，近期区排除已展示的候选。
 *  B. 多板块事件不得只凭第一条已观察板块给整体说明 —— 绝对/相对说明已下沉到**每个板块**。
 *
 * 另断言：计数语义（候选**事件**数 ≠ 独立题材数）、禁用词、裸 Markdown。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { NewThemeRadarSection, relationLabel } from '../NewThemeRadarSection';
import raw from '@current/new_theme_radar_v0_3.json';

interface D {
  as_of: string; artifact_version?: string;
  coverage: { sources?: { name: string }[]; date_range?: [string, string] | null; events: number;
    failures?: unknown[] };
  summary: { events: number; candidates: number; candidates_are?: string };
  status_legend: Record<string, string>;
  rules?: { count_semantics?: string };
  events: {
    event_id: string; event_date: string; status: string;
    source: { url: string };
    theme_links: { board_series: string; board_name: string; keyword: string; relation: string }[];
    markets?: { board_series: string; board_name?: string; window?: [string, string] | null;
      excess_pp?: number | null; board_ret_pct?: number | null; observation_trading_days?: number | null;
      assessment?: { relative_positive: boolean; absolute_positive: boolean; note: string } | null;
      status: string }[];
    assessment?: unknown;
    review?: { verdict: string } | null;
    gaps: string[];
  }[];
}
const doc = raw as unknown as D;
const html = renderToStaticMarkup(<NewThemeRadarSection />);
const text = html.replace(/<[^>]+>/g, ' ');

/** 候选区 HTML（切到「二、最近事件」之前）；用区块标记切分，避免 indexOf 找不到时切成 -1 */
function sectionHtml(name: 'candidates' | 'recent'): string {
  const startTag = `data-cand-section="${name}"`;
  const i = html.indexOf(startTag);
  if (i < 0) return '';
  const nextIdx = name === 'candidates' ? html.indexOf('data-cand-section="recent"') : html.indexOf('data-status-legend');
  return html.slice(i, nextIdx > i ? nextIdx : html.length);
}

const candidates = doc.events.filter((e) => e.status === 'CANDIDATE');

describe('v0.68 候选可见性', () => {
  it('★★ 较早的候选事件即使不在最近 12 条内，也必须出现在候选区', () => {
    expect(candidates.length, '产物应有候选事件').toBeGreaterThan(0);
    const top12 = new Set(doc.events.slice(0, 12).map((e) => e.event_id));
    // 前提：至少有一条候选**不在**最近 12 条（否则这条回归没有意义）
    const outside = candidates.filter((e) => !top12.has(e.event_id));
    expect(outside.length, '应存在「不在最近 12 条」的候选事件').toBeGreaterThan(0);

    const candHtml = sectionHtml('candidates');
    for (const e of candidates) {
      expect(candHtml, `候选 ${e.event_id} 必须在候选区出现`).toContain(`data-event="${e.event_id}"`);
    }
    // 候选区数量 = 产物候选数
    expect(candHtml).toContain(`一、当前候选事件（${candidates.length}）`);
  });

  it('★★ 近期区不重复展示已在上方出现的候选事件', () => {
    const recentHtml = sectionHtml('recent');
    for (const e of candidates) {
      expect(recentHtml, `候选 ${e.event_id} 不应在近期区重复`).not.toContain(`data-event="${e.event_id}"`);
    }
    // 近期区确实还有其它事件（不是把整段清空）
    const rest = doc.events.filter((e) => e.status !== 'CANDIDATE');
    expect(rest.length).toBeGreaterThan(0);
    expect(recentHtml).toContain(`data-event="${rest[0].event_id}"`);
  });

  it('★★ 计数语义：候选是**事件条数**，不是独立题材数', () => {
    expect(html).toContain(`data-candidate-count="${doc.summary.candidates}"`);
    expect(html).toContain('data-count-semantics="EVENTS_NOT_THEMES"');
    expect(text).toContain('事件条数');
    expect(text).toContain('不输出题材数');
    expect(doc.summary.candidates_are).toBe('EVENTS_NOT_THEMES');
    // 不得出现「N 个新题材」式表述
    expect(text).not.toMatch(/\d+\s*个(独立)?新题材/);
  });
});

describe('v0.68 逐板块语义', () => {
  it('★★ 绝对/相对说明挂在每个板块上，不再有事件级整体结论', () => {
    const withMk = candidates.find((e) => (e.markets ?? []).length > 0)!;
    expect(withMk).toBeTruthy();
    expect(withMk.assessment, '事件级 assessment 应已废弃').toBeUndefined();

    const candHtml = sectionHtml('candidates');
    for (const m of withMk.markets!) {
      expect(candHtml).toContain(`data-market-board="${m.board_series}"`);
      if (m.status === 'OBSERVED') {
        expect(m.assessment, `${m.board_series} 应有逐板块 assessment`).toBeTruthy();
        expect(candHtml).toMatch(/data-assess="REL_(POS|NEG)"/);
      }
    }
    expect(text).toContain('沪深300');
    expect(text).toContain('超额');
  });

  it('★ 代理板块必须标注「代理板块，非主题本身」', () => {
    // ① 标签逻辑本身（确定性断言，不依赖哪条事件被渲染）
    expect(relationLabel('PROXY')).toBe('代理板块，非主题本身');
    expect(relationLabel('DIRECT')).toBe('直接');
    // ② 已渲染的 PROXY 事件必须带上该标注（本轮 PROXY 事件较早，未必落在展示区）
    const rendered = new Set(
      [...sectionHtml('candidates'), ...sectionHtml('recent')].flatMap((h) =>
        [...h.matchAll(/data-event="([^"]+)"/g)].map((m) => m[1])),
    );
    const proxyRendered = doc.events
      .filter((e) => rendered.has(e.event_id))
      .flatMap((e) => e.theme_links)
      .filter((l) => l.relation === 'PROXY');
    if (proxyRendered.length > 0) expect(text).toContain('代理板块，非主题本身');
    // ③ 产物里确实存在 PROXY 关联（若没有，说明代理映射被误删）
    const proxyAll = doc.events.flatMap((e) => e.theme_links).filter((l) => l.relation === 'PROXY');
    expect(proxyAll.length, '产物应保留 PROXY 代理关联').toBeGreaterThan(0);
  });

  it('★ 保留原文、时点口径与缺口说明；无禁用词、无裸 Markdown', () => {
    expect(text).toContain('基准日');
    expect(text).toContain('观察起点');
    expect(html).toMatch(/data-gaps="\d+"/);
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分', '排名', '止损']) {
      expect(text, `不得出现「${banned}」`).not.toContain(banned);
    }
    expect(text).toContain('不是买卖建议');
    expect(text).not.toContain('**');
  });

  it('★ 状态图例与来源链接仍在', () => {
    for (const k of Object.keys(doc.status_legend)) expect(text).toContain(k);
    expect(html).toContain(`href="${doc.events[0].source.url}"`);
  });
});
