/**
 * ★★ v0.70：自动发现的新题材线索 —— 市场状态 vs 事件性质 / 主题粒度 / 覆盖说明（产物 `new_theme_radar_v0_5`）。
 *
 * 本轮回归的三类缺陷：
 *  A. **把「相对表现为正」读成「新催化」**：候选区标题必须只描述**市场条件**，
 *     `CANDIDATE` 文案必须是「待人工复核」；性质=背景/常规重复的事件即使进候选区，
 *     也必须显式标注「只作市场观察，不构成产业催化」。
 *  B. **覆盖说明是旧文案**：`coverage.limits` / `rules.time_rule` 必须与实际来源注册表、
 *     实际出现的时点规则对得上（不得写着「单一发布机构」而实际有 4 个机构）。
 *  C. **主题标签由共享代理序列反推**：`theme_tags` 必须来自实际命中的关键词，
 *     `research_directions` 只是上层分组（同一个方向可能挂多条序列）。
 *
 * 另保留 v0.68/v0.69 的回归：候选可见性、逐板块语义、计数语义、禁用词、裸 Markdown。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { NewThemeRadarSection, relationLabel, natureCaveat } from '../NewThemeRadarSection';
import raw from '@current/new_theme_radar_v0_5.json';

interface D {
  as_of: string; artifact_version?: string;
  coverage: { publishers?: string[]; publisher?: string; sources?: { id: string; name: string }[];
    date_range?: [string, string] | null; events: number; failures?: unknown[];
    limits?: string[]; event_date_sources?: Record<string, number>;
    reaction_bases?: Record<string, number> };
  summary: { events: number; candidates: number; candidates_are?: string;
    by_nature?: Record<string, number>; by_direction?: Record<string, number>;
    by_theme_tag?: Record<string, number>; routine_repeat_groups?: Record<string, number> };
  nature_legend?: Record<string, string>;
  research_directions?: { direction: string; series: string[] }[];
  theme_tags_by_keyword?: Record<string, string>;
  status_legend: Record<string, string>;
  rules?: { count_semantics?: string; time_rule?: string; time_rules?: Record<string, string> };
  events: {
    event_id: string; event_date: string; status: string;
    nature?: { kind: string; basis: string; repeat_count?: number } | null;
    theme_tags?: string[];
    research_directions?: string[];
    source: { id?: string; url: string; name?: string };
    theme_links: { board_series: string; board_name: string; keyword: string; relation: string;
      theme_tag?: string | null }[];
    markets?: { board_series: string; board_name?: string; window?: [string, string] | null;
      excess_pp?: number | null; board_ret_pct?: number | null; observation_trading_days?: number | null;
      assessment?: { relative_positive: boolean; absolute_positive: boolean; note: string } | null;
      status: string }[];
    assessment?: unknown;
    time?: { event_date_source?: string; basis_day?: string | null; reaction_basis?: string };
    review?: { verdict: string } | null;
    gaps: string[];
  }[];
}
const doc = raw as unknown as D;
const html = renderToStaticMarkup(<NewThemeRadarSection />);
const text = html.replace(/<[^>]+>/g, ' ');
/** ★ 不含原文引用（<details> 内是来源正文，可能出现「排名」等词，不是我们的措辞） */
const chromeText = html.replace(/<details[\s\S]*?<\/details>/g, ' ').replace(/<[^>]+>/g, ' ');

/** 候选区 HTML（切到「二、最近事件」之前）；用区块标记切分，避免 indexOf 找不到时切成 -1 */
function sectionHtml(name: 'candidates' | 'directions' | 'recent'): string {
  const startTag = `data-cand-section="${name}"`;
  const i = html.indexOf(startTag);
  if (i < 0) return '';
  const order = ['data-cand-section="candidates"', 'data-cand-section="directions"',
    'data-cand-section="recent"', 'data-nature-legend'];
  const nextTag = order[order.indexOf(startTag) + 1];
  const nextIdx = nextTag ? html.indexOf(nextTag) : -1;
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
    // ★ 标题由产物计数推导（不写死数字）：只断言前缀与计数一致
    expect(candHtml).toContain('一、市场反应筛选结果（');
    expect(candHtml).toContain(`${candidates.length} 条事件`);
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
    // ★ 只检查本组件的文案：原文引用（<details>）是来源正文，不参与禁用词判定
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分', '排名', '止损']) {
      expect(chromeText, `不得出现「${banned}」`).not.toContain(banned);
    }
    expect(text).toContain('不是买卖建议');
    expect(text).not.toContain('**');
  });

  it('★★ 与当前研究方向相关的事件：全部展示且不与候选/近期区重复', () => {
    const dirEvents = doc.events.filter(
      (e) => e.status !== 'CANDIDATE' && (e.research_directions ?? []).length > 0);
    const dirHtml = sectionHtml('directions');
    if (dirEvents.length > 0) {
      expect(html).toContain(`data-cand-section="directions"`);
      for (const e of dirEvents) {
        expect(dirHtml, `方向事件 ${e.event_id} 必须展示`).toContain(`data-event="${e.event_id}"`);
        expect(dirHtml).toContain(`data-direction-group="${e.research_directions![0]}"`);
      }
      // 不重复：近期区不得再出现这些事件
      const recentHtml = sectionHtml('recent');
      for (const e of dirEvents) expect(recentHtml).not.toContain(`data-event="${e.event_id}"`);
    }
    // 研究方向对应表必须来自产物（序列 → 方向），且只含已存在序列
    expect((doc.research_directions ?? []).length).toBeGreaterThan(0);
    for (const d of doc.research_directions ?? []) expect(d.series.length).toBeGreaterThan(0);
  });

  it('★★ 事件性质：常规重复可识别、新催化与背景可区分（不靠关键词编造）', () => {
    const routine = doc.events.filter((e) => e.nature?.kind === 'ROUTINE_RECURRING');
    expect(routine.length, '产物应有常规重复事件（成品油价格）').toBeGreaterThan(1);
    // 每个常规重复事件都带同组计数，且计数与产物一致
    for (const e of routine) {
      expect(e.nature!.repeat_count).toBe(routine.length);
    }
    expect(html).toContain('data-nature="ROUTINE_RECURRING"');
    expect(text).toContain('常规重复事件');
    expect(text).toContain('同机制第');
    // 性质不等于状态：常规重复里也可能有 CANDIDATE
    const kinds = new Set(doc.events.map((e) => e.nature?.kind).filter(Boolean));
    expect(kinds.size).toBeGreaterThan(1);
    // 性质图例与判据都来自产物
    for (const k of Object.keys(doc.nature_legend ?? {})) expect(text).toContain(k);
    expect(html).toMatch(/data-nature-basis="/);
  });

  it('★ 新来源（医保局 / 能源局 / 工信部）事件可进入产物并带来源与日期来源', () => {
    const ids = new Set(doc.events.map((e) => e.source.id));
    // v0.69 医保局、v0.70 能源局与工信部 —— 至少各有一条事件进入产物
    for (const sid of ['NHSA_NOTICE', 'NEA_XNY', 'MIIT_KJS']) {
      expect(ids, `来源 ${sid} 应至少产生一条事件`).toContain(sid);
    }
    for (const p of ['国家医疗保障局', '国家能源局', '工业和信息化部']) {
      expect(text, `页面必须展示机构「${p}」`).toContain(p);
    }
    // 日期来源必须显式（列表页 / 文章路径）
    expect(text).toMatch(/列表页标注日|文章路径日期/);
  });

  it('★ 状态图例与来源链接仍在', () => {
    for (const k of Object.keys(doc.status_legend)) expect(text).toContain(k);
    expect(html).toContain(`href="${doc.events[0].source.url}"`);
  });
});

describe('v0.70 市场状态 ≠ 事件性质', () => {
  it('★★ 候选区标题只描述**市场条件**，不得暗示都是新催化', () => {
    const candHtml = sectionHtml('candidates');
    expect(candHtml).toContain('市场反应筛选结果');
    // 旧标题「当前候选事件」会让读者以为这些是「被选中的题材」
    expect(candHtml).not.toContain('当前候选事件');
    // 必须说明筛选条件只有市场条件、且待人工复核
    expect(candHtml).toContain('data-market-filter-note="1"');
    expect(candHtml).toContain('待人工复核');
    expect(candHtml).toContain('不代表');
  });

  it('★★ `CANDIDATE` 文案是「相对基准为正 · 待人工复核」，不是「利好 / 催化」', () => {
    // 直接断言渲染出的状态标签（不依赖哪条事件）
    expect(chromeText).toContain('相对基准为正 · 待人工复核');
    for (const bad of ['利好', '催化确认', '建议关注', '推荐']) {
      expect(chromeText, `状态文案不得出现「${bad}」`).not.toContain(bad);
    }
  });

  it('★★ 性质=背景/常规重复 的事件进候选区时，必须显式说明「只作市场观察」', () => {
    // ① 纯函数：四种性质的交叉说明（这是语义不变量，不依赖产物里恰好有哪种组合）
    expect(natureCaveat('BACKGROUND', 'CANDIDATE')).toContain('不构成产业催化');
    expect(natureCaveat('ROUTINE_RECURRING', 'CANDIDATE')).toContain('不是新催化');
    expect(natureCaveat('UNCLASSIFIED', 'CANDIDATE')).toContain('不推断');
    expect(natureCaveat('NEW_CATALYST', 'CANDIDATE'), '新催化不需要反向说明').toBeNull();
    // 非候选不产生该说明（避免把留档事件也说成催化）
    expect(natureCaveat('BACKGROUND', 'WATCH')).toBeNull();

    // ② 渲染：产物里若存在「背景/常规 + 候选」的组合，必须带 data-nature-caveat
    const candHtml = sectionHtml('candidates');
    const mixed = candidates.filter(
      (e) => e.nature?.kind === 'BACKGROUND' || e.nature?.kind === 'ROUTINE_RECURRING');
    for (const e of mixed) {
      const row = candHtml.slice(candHtml.indexOf(`data-event="${e.event_id}"`));
      const end = row.indexOf('data-event="', 10);
      expect((end > 0 ? row.slice(0, end) : row), `${e.event_id}（${e.nature!.kind}）必须带性质说明`)
        .toContain(`data-nature-caveat="${e.nature!.kind}"`);
    }
    // ③ 正交说明与两套图例都在
    expect(html).toContain('data-orthogonal="1"');
    expect(html).toContain('data-nature-legend="1"');
    expect(html).toContain('data-status-legend="1"');
  });

  it('★★ 性质与状态是两套独立枚举：产物里不得混用键名，且候选区可含非新催化', () => {
    const sk = Object.keys(doc.status_legend);
    const nk = Object.keys(doc.nature_legend ?? {});
    expect(nk.length, '四种性质都必须有图例').toBe(4);
    for (const k of nk) expect(sk, `性质 ${k} 不得同时是状态枚举`).not.toContain(k);
    // 产物层面：CANDIDATE 不全是 NEW_CATALYST（否则说明状态被性质污染了）
    const candKinds = new Set(candidates.map((e) => e.nature?.kind));
    expect(candKinds.size, '候选区应能出现多种性质（证明两者正交）').toBeGreaterThan(1);
  });
});

describe('v0.70 覆盖说明与实现一致', () => {
  it('★★ coverage.limits 的机构/来源数必须与真实注册表一致（不是旧文案）', () => {
    const pubs = doc.coverage.publishers ?? [];
    expect(pubs.length, '应有多个发布机构').toBeGreaterThan(1);
    const lim0 = (doc.coverage.limits ?? [])[0] ?? '';
    expect(lim0).toContain(`${pubs.length} 个`);
    expect(lim0).toContain(`${(doc.coverage.sources ?? []).length} 个`);
    for (const p of pubs) expect(lim0, `首条覆盖说明必须列出机构「${p}」`).toContain(p);
    // 旧文案的典型错误表述不得残留
    expect(lim0).not.toContain('单一发布机构');
  });

  it('★★ rules.time_rule 必须覆盖实际出现的每条时点规则（不得只写保守规则）', () => {
    const tr = doc.rules?.time_rules ?? {};
    expect(Object.keys(tr).length, '应有多条时点规则说明').toBeGreaterThanOrEqual(3);
    const used = new Set(doc.events.map((e) => e.time?.reaction_basis).filter(Boolean) as string[]);
    for (const b of used) {
      expect(tr, `产物用了时点规则 ${b}，但 rules.time_rules 没描述它`).toHaveProperty([b]);
    }
    // 总述必须提到「收盘后 / 开盘前 / 盘中退回保守」三种情形
    const total = doc.rules?.time_rule ?? '';
    expect(total).toContain('15:00');
    expect(total).toContain('09:30');
    expect(total).toContain('退回保守');
    // 覆盖说明里的时点统计必须与实际一致（按**事件逐条**计数，不是按规则去重）
    const rb: Record<string, number> = {};
    for (const e of doc.events) {
      const b = e.time?.reaction_basis;
      if (b) rb[b] = (rb[b] ?? 0) + 1;
    }
    expect(doc.coverage.reaction_bases).toEqual(rb);
    expect(Object.keys(rb).length).toBeGreaterThan(1);
  });

  it('★ 覆盖说明必须写明「无法稳定解析而未接入」的栏目（不能只写好话）', () => {
    const all = (doc.coverage.limits ?? []).join(' ');
    expect(all).toContain('未接入');
    expect(all).toContain('工信部');
    expect(all).toContain('能源局');
  });
});

describe('v0.70 主题粒度：具体主题 ≠ 上层方向', () => {
  it('★★ theme_tags 必须由实际命中关键词映射而来，不得由共享序列反推', () => {
    const map = doc.theme_tags_by_keyword ?? {};
    expect(Object.keys(map).length, '应有显式关键词→主题映射表').toBeGreaterThan(0);
    for (const e of doc.events) {
      const want = [...new Set(e.theme_links.map((l) => map[l.keyword]).filter(Boolean))];
      expect(e.theme_tags ?? [], `${e.event_id} 的 theme_tags 必须由关键词映射推出`)
        .toEqual(want);
      for (const l of e.theme_links) {
        if (map[l.keyword]) expect(l.theme_tag).toBe(map[l.keyword]);
      }
    }
  });

  it('★★ 同一上层方向下的不同关键词，必须给出不同的具体主题', () => {
    // 反例回归：医用耗材与脑机接口都挂 BK881144，但主题不同
    const bySid = new Map<string, Set<string>>();
    for (const e of doc.events) {
      for (const l of e.theme_links) {
        if (!bySid.has(l.board_series)) bySid.set(l.board_series, new Set());
        if (l.theme_tag) bySid.get(l.board_series)!.add(l.theme_tag);
      }
    }
    const shared = [...bySid.entries()].filter(([, tags]) => tags.size > 1);
    expect(shared.length, '应存在「同一序列对应多个具体主题」的情形（这正是本轮要修的）')
      .toBeGreaterThan(0);
    // 且这些不同主题在上层方向里被合并成一个 —— 说明为什么需要 theme_tags
    const dirOf = new Map((doc.research_directions ?? []).flatMap(
      (d) => d.series.map((s) => [s, d.direction] as const)));
    const merged = shared.filter(([sid]) => dirOf.has(sid));
    expect(merged.length).toBeGreaterThan(0);
  });

  it('★ 页面上「主题：」与「上层方向：」同时出现且可区分', () => {
    expect(chromeText).toContain('主题：');
    expect(chromeText).toContain('上层方向：');
    expect(html).toMatch(/data-theme-tag="/);
    // 研究方向段必须说明「方向是上层分组、具体主题看主题标签」
    expect(sectionHtml('directions')).toContain('上层分组');
  });
});
