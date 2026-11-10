/**
 * 研究工作台（v0.74）回归 —— 只测本轮真正引入的四类不变量，不扩建测试体系。
 *
 *  A. **口径切换**：有效性 = 研究增量；行情超额只作附注；默认页面无优先级排序。
 *  B. **内部排序隔离**：评分/概率字段只在评估视图出现，索引产物与默认渲染里都没有。
 *  C. **T 时刻冻结**：正文与事后核对物理分离，事后核对不改正文。
 *  D. **可核性**：索引 counts / URL 策略 / 评估 priority=Wilson 下界。
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Workbench } from '../Workbench';
import { EvalView } from '../EvalView';
import { ArchiveView } from '../ArchiveView';
import {
  exportBundle, freezeRecord, loadEvals, loadRecords, nextRecordId,
  saveEval, saveRecord, searchItems,
} from '../records';
import indexRaw from '@current/workbench_index_v0_1.json';
import evalRaw from '@current/workbench_eval_basis_v0_1.json';
import frontierRaw from '@current/frontier_board_v0_1.json';
import calendarRaw from '@current/event_calendar_v0_1.json';
import weeklyRaw from '@current/weekly_research_v0_1.json';
import declarationsRaw from '@current/phase_declaration_log_v0_1_view.json';
import themeRaw from '@current/theme_discovery_v0_1.json';
import type { DeclarationView, EvalDoc, IndexDoc } from '../types';
import type { FrontierDoc, EventCalendar, ThemeDiscoveryDoc, WeeklyResearchDoc } from '../FrontierView';

const doc = indexRaw as unknown as IndexDoc;
const evalDoc = evalRaw as unknown as EvalDoc;
const frontier = frontierRaw as unknown as FrontierDoc;
const calendar = calendarRaw as unknown as EventCalendar;
const weekly = weeklyRaw as unknown as WeeklyResearchDoc;
const declarations = declarationsRaw as unknown as DeclarationView;
const td = themeRaw as unknown as ThemeDiscoveryDoc;
/** v0.82：历史研究对象 / 本周研究明细 / 研究轮次都在独立档案视图，不在默认工作台。 */
const archiveHtml = renderToStaticMarkup(
  <ArchiveView doc={frontier} weekly={weekly} onRecord={() => {}} />);

beforeEach(() => {
  const mem = new Map<string, string>();
  (globalThis as unknown as { localStorage: Storage }).localStorage = {
    getItem: (k: string) => mem.get(k) ?? null,
    setItem: (k: string, v: string) => { mem.set(k, v); },
    removeItem: (k: string) => { mem.delete(k); },
    clear: () => mem.clear(),
    key: () => null,
    length: 0,
  } as Storage;
});

describe('A · 口径切换与默认页面隔离', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★ 默认页面写明「有效性 = 研究增量」，并声明行情超额只是附注', () => {
    expect(html).toContain('有效性 = 研究增量');
    expect(html).toContain('行情附注');
    expect(html).toContain('不参与验收');
  });

  it('★★ v0.77：默认页按 G1→G4 研究浏览顺序，但仍不含任何启发式内部打分', () => {
    // 排序分两种：产物已有的分组顺序可以上默认页；Wilson 打分只在评估视图。
    for (const banned of ['data-eval-row', 'INTERNAL_EVAL_ONLY', 'priority_score',
      'wilson_low', 'data-eval-view', 'calibrated']) {
      expect(html, `默认页面不得出现 ${banned}`).not.toContain(banned);
    }
    expect(html).toContain('G1→G4 研究浏览顺序');
    expect(html).toContain('无分数、不是收益排序');
    expect(html).toContain('值得关注');
    expect(html).toContain('不是买卖点');
  });

  it('★ 评估视图是主动入口，默认不渲染评估表格', () => {
    expect(html).toContain('data-open-eval="1"');
    expect(html).not.toContain('<table class="wb-table">');
  });

  it('★ 历史检索仍按日期倒序、空 query 不铺全量（数据不变量）', () => {
    expect(searchItems(doc.items, '')).toEqual([]);
    expect(html).toContain('data-open-history="1"');
    const dated = doc.items.map((x) => x.date).filter(Boolean) as string[];
    expect([...dated]).toEqual([...dated].sort().reverse());
    expect(doc.counts.total).toBe(doc.items.length);
  });
});

describe('B · 内部评估视图（唯一允许排序的地方）', () => {
  const html = renderToStaticMarkup(<EvalView doc={evalDoc} declarations={declarations} />);

  it('★ 表格与评分只在评估视图出现，且带完整边界声明', () => {
    expect(html).toContain('data-eval-view="1"');
    expect(html).toMatch(/data-eval-row="/);
    expect(html).toContain('INTERNAL_EVAL_ONLY');
    expect(html).toContain('不是未来概率');
    expect(html).toContain('不参与有效性验收');
    expect(html).toContain('Wilson 95% 区间下界');
  });

  it('★★ priority_score 恒等于 Wilson 下界，且每行都标未校准/非概率', () => {
    expect(evalDoc.rows.length).toBeGreaterThan(0);
    for (const r of evalDoc.rows) {
      expect(r.priority_score).toBe(r.wilson_low);
      expect(r.usage).toBe('INTERNAL_EVAL_ONLY');
      expect(r.calibrated).toBe(false);
      expect(r.is_probability).toBe(false);
    }
  });

  it('★ 索引产物零评分字段（构建器 --check 也守这条）', () => {
    const blob = JSON.stringify(doc);
    for (const banned of ['priority_score', 'wilson_low', 'hit_rate', 'calibrated']) {
      expect(blob).not.toContain(banned);
    }
  });
});

describe('C · T 时刻冻结与事后核对分离', () => {
  const now = new Date('2026-11-04T21:00:00+08:00');

  it('★ 3 字段正文不含 posthoc，自动字段可核', () => {
    const r = freezeRecord({
      question: '冬季流感的历史对应是否值得继续查？',
      verdict_at_T: '此前没想到 2018 年同期对照，准备核对原始公告',
      type: 'LEAD', cluster_id: 'FLU-2026-WINTER', item_ref: 'X',
    }, doc, now, []);
    expect(r.record_id).toBe('RU-20261104-01');
    expect(r.data_as_of).toBe(doc.as_of);
    expect(r.artifact_ref).toContain('workbench_index_v0_1@');
    expect(Object.keys(r)).not.toContain('posthoc_check');
    expect(Object.keys(r)).not.toContain('posthoc');
  });

  it('★ 同一天序号递增，只增不改', () => {
    const first = freezeRecord({ question: 'q1', verdict_at_T: 'v1', type: 'LEAD', cluster_id: '' }, doc, now, []);
    const rows = saveRecord(first);
    expect(nextRecordId(rows, now)).toBe('RU-20261104-02');
    const second = freezeRecord({ question: 'q2', verdict_at_T: 'v2', type: 'NO_LEAD', cluster_id: '' }, doc, now, rows);
    const all = saveRecord(second);
    expect(all).toHaveLength(2);
    expect(all[0].verdict_at_T).toBe('v1');
  });

  it('★★ 事后核对独立存储，写它不会改动正文', () => {
    const r = freezeRecord({ question: 'q', verdict_at_T: 'v', type: 'LEAD', cluster_id: 'C1' }, doc, now, []);
    saveRecord(r);
    const before = JSON.stringify(loadRecords());
    saveEval({ record_id: r.record_id, checked_at: now.toISOString(),
      is_new_correspondence: 'YES', note: '查到 2018 年原始公告，机制不同' });
    expect(JSON.stringify(loadRecords())).toBe(before);
    expect(loadEvals()).toHaveLength(1);
  });

  it('★ 导出把 records 与 evals 分成两个独立数组', () => {
    const r = freezeRecord({ question: 'q', verdict_at_T: 'v', type: 'LEAD', cluster_id: '' }, doc, now, []);
    saveRecord(r);
    saveEval({ record_id: r.record_id, checked_at: now.toISOString(),
      is_new_correspondence: 'NO', note: '本来就知道' });
    const bundle = JSON.parse(exportBundle());
    expect(bundle.protocol).toBe('REAL_USE_LITE_v0_1');
    expect(Array.isArray(bundle.records)).toBe(true);
    expect(Array.isArray(bundle.evals)).toBe(true);
    expect(bundle.records[0].record_id).toBe(bundle.evals[0].record_id);
  });
});

describe('D · 检索与可核性', () => {
  it('★ 多词 AND、大小写不敏感', () => {
    const hits = searchItems(doc.items, '风电');
    expect(hits.length).toBeGreaterThan(0);
    expect(hits.every((x) => x.title || x.why)).toBe(true);
    expect(searchItems(doc.items, '风电 光伏').length).toBeLessThanOrEqual(hits.length);
    expect(searchItems(doc.items, 'ZZZ_不存在的词_ZZZ')).toEqual([]);
  });

  it('★ 索引里每条都有可核来源说明；外部 URL 必须是 http(s)', () => {
    expect(doc.counts.with_external_url).toBeGreaterThan(0);
    for (const it of doc.items) {
      expect(it.why.length).toBeGreaterThan(0);
      expect(it.uncertainty_reason.length).toBeGreaterThan(0);
      expect(['LOW', 'MEDIUM', 'HIGH']).toContain(it.uncertainty);
      if (it.url) expect(it.url).toMatch(/^https?:\/\//);
    }
  });

  it('★ 三类来源都进入索引，且无编造 URL', () => {
    for (const k of ['HISTORICAL_OBJECT', 'POLICY_EVENT', 'THEME_MAP_EVENT']) {
      expect(doc.counts.by_kind[k]).toBeGreaterThan(0);
    }
    expect(doc.items.filter((x) => x.source.source_kind.startsWith('INTERNAL') && x.url).length).toBe(0);
  });
});

/** ★★ v0.77：默认主入口改成「前瞻排程」（push / 事前），不再是提问式检索。 */
describe('E · 前瞻排程（系统主动推出，双轨并列）', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★★ 默认页是前瞻排程；历史检索 / 记录降级为二级入口', () => {
    expect(html).toContain('data-frontier-view="1"');
    expect(html).toContain('data-open-frontier="1"');
    expect(html).toContain('data-open-history="1"');
    // 提问框不应出现在默认首屏
    expect(html).not.toContain('data-search=""');
  });

  it('★★ 双轨各自 as_of 与更新节奏独立标注，不做因果拼接', () => {
    expect(html).toContain('统计轨 · 季度更新');
    expect(html).toContain('机制轨 · 每周更新');
    expect(html).toContain(frontier.tracks.statistical.as_of);
    expect(html).toContain(frontier.tracks.mechanism.as_of);
    expect(html).toContain('不做因果拼接');
    expect(frontier.tracks.statistical.cadence).toBe('QUARTERLY');
    expect(frontier.tracks.mechanism.cadence).toBe('WEEKLY');
  });

  it('★★ 默认按 G1→G4 研究浏览顺序，且每条带关注标签与双轨理由', () => {
    const groups = [...html.matchAll(/data-group="(G\d)"/g)].map((m) => m[1]);
    expect(groups.length).toBeGreaterThan(0);
    const rank: Record<string, number> = { G1: 1, G2: 2, G3: 3, G4: 4 };
    expect(groups).toEqual([...groups].sort((a, b) => rank[a] - rank[b]));
    expect(html).toContain('data-reason="STATISTICAL"');
    expect(html).toContain('data-reason="MECHANISM"');
    expect(html).toContain('值得关注');
    expect(html).toContain('可斟酌的决策点');
    expect(html).toMatch(/data-record-from="/);
  });

  it('★★ 机制轨作为独立信息流，不给统计卡硬贴理由', () => {
    expect(html).toContain(`data-mechanism-feed="${frontier.mechanism_feed.length}"`);
    // 关键词同时筛选机制轨（否则政策事件里独有的词查不到）
    expect(html).toContain(`data-mechanism-shown="${frontier.mechanism_feed.length}"`);
    expect(html).toContain('上方关键词同时筛选这里');
    expect(frontier.counts.with_mechanism_link).toBeLessThan(frontier.items.length / 10);
    expect(html).toContain('本期机制轨');
    expect(html).toContain('无可核关联');
    for (const e of frontier.mechanism_feed) {
      expect(e.url).toMatch(/^https?:\/\//);
      expect(e.fact_vs_assumption).toBe('FACT_PUBLISHED_DOCUMENT');
    }
  });

  it('★★ 机制理由只在精确序列匹配时出现，URL 可核', () => {
    const linked = frontier.items.filter((x) => x.mechanism_reason);
    expect(linked.length).toBe(frontier.counts.with_mechanism_link);
    for (const x of linked) {
      expect(x.mechanism_reason!.relation).toBe('EXACT_SERIES_MATCH');
      expect(x.mechanism_reason!.url).toMatch(/^https?:\/\//);
    }
  });

  it('★★ 生肖试点：谐音层标 UNVERIFIED、不进统计；PIT 名称缺口如实披露', () => {
    expect(html).toContain('data-calendar-hypothesis="ZODIAC_NAME"');
    expect(html).toContain('data-layer="HOMOPHONE"');
    expect(html).toContain('data-layer-status="UNVERIFIED_ASSUMPTION"');
    expect(html).toContain('九阳股份');
    expect(html).toContain('不进统计、不参与排序、不构成篮子');
    expect(html).toContain('data-gap="PIT_NAME_SNAPSHOT_MISSING"');
    expect(html).toContain('行为假说，不是题材');
    for (const l of calendar.hypotheses[0].mapping_layers) {
      if (l.layer !== 'LITERAL') expect(l.status).toBe('UNVERIFIED_ASSUMPTION');
    }
  });

  it('★★ 日历只含可核事实；产物与默认页均无内部评分字段', () => {
    expect(html).toContain(`data-calendar-entries="${calendar.entries.length}"`);
    for (const e of calendar.entries) expect(e.fact_vs_assumption.length).toBeGreaterThan(0);
    const blob = JSON.stringify(frontier);
    for (const banned of ['priority_score', 'wilson_low', 'INTERNAL_EVAL_ONLY']) {
      expect(blob).not.toContain(banned);
      expect(html).not.toContain(banned);
    }
  });

  it('★★ 措辞放宽但仍无买卖执行类用语', () => {
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '推荐买入']) {
      expect(html, `不应出现「${banned}」`).not.toContain(banned);
    }
    expect(html).toContain('具体的买卖决策由你自行做出');
    expect(html).toContain('不是买卖点');
  });
});

/** ★★ v0.78：默认只显示精选 6 条；命中率改口径；个股参照补回。 */
describe('F · 精选 Top 6 / 命中率口径 / 个股参照', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★★ 默认页恰好 6 条精选，每条带名次与可核排序理由', () => {
    expect(html).toContain('data-top6="6"');
    const top = html.slice(html.indexOf('data-frontier-list="top6"'),
      html.indexOf('data-frontier-count='));
    const rows = [...top.matchAll(/data-frontier-row="([^"]+)"/g)];
    expect(rows.length).toBe(6);
    for (let i = 1; i <= 6; i += 1) expect(top).toContain(`data-rank="${i}"`);
    expect((top.match(/data-rank-reason="1"/g) ?? []).length).toBe(6);
    expect(frontier.top6.length).toBe(6);
    for (const t of frontier.top6) expect(t.rank_reason).toContain('样本外');
  });

  it('★★ v0.82：177 条仍互斥分类，历史固定区下沉档案、不再占默认页', () => {
    expect(frontier.items.length).toBe(177);
    const fixedTotal = frontier.fixed_sections.current_objects.length
      + frontier.fixed_sections.special_hypotheses.length;
    expect(fixedTotal).toBe(9);
    expect(html).toContain(`data-rest-total="${frontier.items.length - frontier.top6.length - fixedTotal}"`);
    // ★ 旧行为快照已撤销：人工设定的固定区行只在档案视图
    expect(html).not.toContain('data-fixed-row=');
    expect(archiveHtml).toContain(`data-fixed-row="${frontier.fixed_sections.current_objects[0]}"`);
    expect(archiveHtml).toContain('存档待复核');
    for (const t of frontier.top6) {
      expect(frontier.fixed_sections.current_objects).not.toContain(t.id);
      expect(frontier.fixed_sections.special_hypotheses).not.toContain(t.id);
    }
  });

  it('★★ Top 6 全部满足 G1 硬门槛，排序规则写进产物', () => {
    const byId = new Map(frontier.items.map((x) => [x.id, x]));
    for (const t of frontier.top6) {
      const x = byId.get(t.id)!;
      expect(x.group).toBe('G1');
      const h = (x.statistical_reason ?? {}) as Record<string, unknown>;
      expect(h.tier).toBe('STRICT');
      expect(h.oos_status).toBe('REPORTED');
      expect(Number(h.oos_hit_rate)).toBeGreaterThanOrEqual(0.5);
      expect(Number(h.pit_eligible_years)).toBeGreaterThanOrEqual(1);
    }
    expect(frontier.selection_rule.month_quota).toBeNull();
    expect(frontier.selection_rule.sort_keys.length).toBeGreaterThan(3);
    expect(html).toContain('data-selection-rule="1"');
  });

  it('★★ 命中率不再是「xx%」，改为「历史跑赢 N/M 年」并附定义', () => {
    expect(html).toMatch(/历史跑赢 \d+\/\d+ 年/);
    expect(html).not.toMatch(/命中率 \d+%/);
    expect(frontier.hit_rate_definition).toContain('年份数 / n');
    expect(html).toContain('查看完整排序规则与命中率定义');
  });

  it('★★ 个股参照补回：概念卡有参照、行业板块如实写无历史成分', () => {
    expect(frontier.counts.with_representative_stocks).toBe(105);
    expect(html).toMatch(/data-stocks="\d+"/);
    expect(html).toContain('data-stock-gap="NO_HISTORICAL_CONSTITUENTS"');
    expect(html).toContain('不是历史成分');
    expect(html).toContain('不列代表股');
  });

  it('★★ 行情校正折叠区默认 IDLE，不内联官方数值', () => {
    expect(html).toContain('data-price-calibration="1"');
    expect(html).toContain('data-price-state="IDLE"');
    expect(html).toContain('六、历史行情校正');
    expect(html).toContain('并列展示、不合并、不替换');
    // 官方逐日点位未落盘，也不内联在默认页面
    expect(html).not.toContain('BACKFILLED_NOT_PIT');
    expect(html).not.toContain('benchmark_parallel_v0_1.json');
  });
});

/** ★★ v0.82：不可解释板块排除但可见 / 历史研究档案整体退出默认页。 */
describe('G · 可解释性门槛与默认页/档案分离', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★★ Top 6 不再出现「其他社会服务」，且每条都可解释', () => {
    const top = html.slice(html.indexOf('data-frontier-list="top6"'),
      html.indexOf('data-frontier-count='));
    expect(top).not.toContain('其他社会服务');
    for (const t of frontier.top6) {
      const x = frontier.items.find((i) => i.id === t.id)!;
      expect(x.interpretable).toBe(true);
      expect(x.board_note ?? '').toBe('');
    }
  });

  it('★★ 被排除的板块在下方单独显示，带排除理由与外部 research', () => {
    expect(frontier.excluded_from_top6.length).toBeGreaterThan(0);
    expect(html).toContain('data-excluded-row="SEAS-BK881179-M11"');
    expect(html).toContain('三、待解释板块');
    expect(html).toContain('data-board-research="BK881179"');
    expect(html).toContain('检验检测认证');
    expect(html).toContain('实朴检测');
    expect(html).toContain('不是成分名单');
    expect(html).toContain('CURRENT_CONSTITUENTS_UNAVAILABLE');
  });

  it('★★ 27 个模糊板块全部登记且仍可查，不删除', () => {
    expect(frontier.board_semantics.entries.length).toBe(27);
    for (const e of frontier.board_semantics.entries) {
      expect(e.interpretable).toBe(false);
      expect(e.classification_note.length).toBeGreaterThan(10);
    }
    expect(frontier.items.length).toBe(177);
    expect(html).toContain('data-fuzzy-list="1"');
    // 27 条都有「不模糊层」：从名称确定性派生的父级类目（零编造）
    expect(frontier.board_semantics.entries.every((e) => e.inferred_parent_sector)).toBe(true);
    const withParent = frontier.board_semantics.entries.filter(
      (e) => e.inferred_parent_sector?.parent);
    expect(withParent.length).toBeGreaterThanOrEqual(25);
    expect(html).toContain('data-parent-sector=');
  });

  it('★★ v0.82：默认页只给数据挖出的主题，历史研究对象整块退出', () => {
    expect(html).toContain('data-frontier-section="discovery"');
    expect(html).toContain('data-theme-discovery="1"');
    expect(html).toContain('档案（待复核）');
    // ★ 旧行为快照已撤销：默认页不得再出现历史研究档案的任何痕迹
    for (const s of ['data-weekly-research="1"', 'data-research-round="1"',
      'data-declaration-policy="1"', 'data-fixed-row=', 'data-archived-themes="1"',
      '产业机制阶段：', '研究侧声明 2026-10-23', '行情附注 as_of',
      'data-industry-phase=', 'data-phase-governance=']) {
      expect(html, `默认页不得出现 ${s}`).not.toContain(s);
    }
    // 归档内容整体可在独立档案视图查到，不丢失、不删除
    expect(archiveHtml).toContain('data-archive-view="1"');
    expect(archiveHtml).toContain('data-archived-themes="1"');
    expect(archiveHtml).toContain('data-weekly-archive="1"');
    expect(archiveHtml).toContain('data-declaration-policy="1"');
    expect(archiveHtml).toContain('本周研究明细 · 存档待复核');
    const gov = frontier.theme_market.phase_governance as {
      update_policy: { auto_change_phase: boolean };
    };
    expect(gov.update_policy.auto_change_phase).toBe(false);
    const themes = frontier.theme_market.themes;
    expect(themes.length).toBe(6);
    for (const t of themes) {
      expect(t.market_as_of).toBeTruthy();
      expect(t.equal_weight['20']).toBeTruthy();
      expect(archiveHtml).toContain(`data-fixed-row="${t.candidate_id}"`);
    }
  });

  it('★★ 光互联：阶段/背离信号留在档案，默认页不拿历史对象占位置', () => {
    const t = frontier.theme_market.themes.find(
      (x) => x.candidate_id === 'CC-2026-OPTICAL-LINK')!;
    expect(t.phase_label).toBe('扩散');
    expect(t.equal_weight['20'].equal_weight_excess_pp).toBeLessThan(-10);
    expect(t.signals.some((s) => s.id === 'DIVERGENCE_INDUSTRY_VS_MARKET')).toBe(true);
    expect(t.signals.some((s) => s.id === 'REVIEW_STALE')).toBe(true);
    expect(archiveHtml).toContain('data-signal="DIVERGENCE_INDUSTRY_VS_MARKET"');
    expect(archiveHtml).toContain('data-signal="REVIEW_STALE"');
    expect(html).not.toContain('data-signal=');
  });

  it('★★ 阶段声明 SOP 在档案视图可查，默认页不再重复', () => {
    expect(archiveHtml).toContain('阶段声明去哪了 / 口径与后续更新 SOP');
    expect(archiveHtml).toContain('R0_INSUFFICIENT_EVIDENCE');
    expect(archiveHtml).toContain('REVIEWED_MAINTAINED');
    expect(archiveHtml).toContain('不参与定档、不自动改阶段');
    expect(archiveHtml).toContain('不作反向证据');
    expect(archiveHtml).toContain('phase_declaration_log_v0_1.json');
    expect(html).not.toContain('阶段声明去哪了');
  });
});

/** ★★ v0.82：历史研究周报下沉档案 / 追加式阶段声明日志只在评估视图。 */
describe('H · 历史研究周报（档案）与阶段声明日志（评估视图）', () => {
  const html = renderToStaticMarkup(<Workbench />);
  const evalHtml = renderToStaticMarkup(<EvalView doc={evalDoc} declarations={declarations} />);

  it('★ 档案里每个方向都有本周结论，缺命中必须写原因', () => {
    expect(weekly.artifact).toBe('weekly_research');
    expect(weekly.cadence).toBe('WEEKLY');
    expect(weekly.feed_window[0] <= weekly.feed_window[1]).toBe(true);
    expect(weekly.counts.directions).toBe(weekly.directions.length);
    expect(weekly.counts.events_in_window).toBe(
      weekly.counts.linked_to_direction + weekly.counts.other_verifiable_documents);
    for (const d of weekly.directions) {
      expect(archiveHtml).toContain(`data-weekly-direction="${d.direction}"`);
      if (d.matched_events.length === 0) {
        expect(d.no_match_reason).toBeTruthy();
        expect(archiveHtml).toContain(`data-weekly-gap="${d.direction}"`);
      } else {
        for (const e of d.matched_events) {
          expect(e.url).toMatch(/^https?:\/\//);
          expect(archiveHtml).toContain(`data-weekly-event="${e.event_id}"`);
          expect(e.boards.length).toBeGreaterThan(0);
        }
      }
    }
  });

  it('★ 主题索引由产物给出（前端不重算），6 个历史主题在档案全覆盖', () => {
    const ids = frontier.theme_market.themes.map((t) => t.candidate_id);
    for (const id of ids) {
      expect(weekly.theme_index[id]).toBeTruthy();
      expect(archiveHtml).toContain(`data-weekly-theme-count="${weekly.theme_index[id].matched_count}"`);
    }
    expect(Object.keys(weekly.theme_index).length).toBe(ids.length);
    expect(archiveHtml).toContain('前置观察窗口（库内可核）');
    for (const w of weekly.observation_windows) {
      expect(archiveHtml).toContain(`data-observation-window="${w.date}"`);
    }
  });

  it('★★ 阶段声明只在评估视图，且带 PIT 锚点、不含结算字段', () => {
    expect(html).not.toContain('data-phase-declarations="1"');
    expect(evalHtml).toContain('data-phase-declarations="1"');
    expect(declarations.append_only).toBe(true);
    expect(declarations.counts.with_settlement_fields).toBe(0);
    // ★ 由产物推导，不写死条数：新一轮研究追加后声明会变多
    expect(declarations.counts.declarations).toBe(declarations.declarations.length);
    expect(declarations.counts.review_rounds).toBeGreaterThanOrEqual(2);
    const newer = declarations.declarations.filter((d) => d.declared_at > '2026-10-23');
    expect(newer.length).toBeGreaterThan(0);
    for (const d of newer) {
      expect(d.supersedes, `${d.declaration_id} 应指向上一轮声明`).toBeTruthy();
    }
    const ids = new Set(declarations.declarations.map((d) => d.declaration_id));
    expect(ids.size).toBe(declarations.declarations.length);
    for (const d of declarations.declarations) {
      expect(d.market_anchor.as_of).toBe(d.declared_at);
      expect(d.market_anchor.basis).toBe('DECLARATION_DATE_AS_PIT_UPPER_BOUND');
      expect(d.basis.length).toBeGreaterThan(10);
      expect((d as unknown as Record<string, unknown>).superseded_by).toBeUndefined();
      expect(evalHtml).toContain(`data-declaration-id="${d.declaration_id}"`);
    }
  });

  it('★ 历史研究轮次与观察方向在档案可查，不占默认页', () => {
    expect(archiveHtml).toContain('data-research-round="1"');
    expect(html).not.toContain('data-research-round="1"');
    const r = weekly.research_round!;
    expect(r.theme_reviews.length).toBe(frontier.theme_market.themes.length);
    for (const w of r.new_watch_directions) {
      expect(archiveHtml).toContain(`data-watch-direction="${w.direction_id}"`);
      expect(w.event.url).toMatch(/^https?:\/\//);
      // 未映射的板块必须写原因，不能补造
      if (!w.board_series) expect(w.board_mapping_reason.length).toBeGreaterThan(5);
    }
    for (const t of r.theme_reviews) {
      expect(archiveHtml).toContain(`data-theme-review="${t.candidate_id}"`);
      expect(t.next_research_question.length).toBeGreaterThan(5);
    }
  });

  it('★★ v0.81 单人工具：口径说明集中一处、默认收起、默认可见区不重复', () => {
    expect(html).toContain('data-caliber-details="1"');
    expect(html).not.toContain('data-frontier-caliber="1"');
    const outside = html.split('data-caliber-details="1"')[0];
    for (const s of ['有效性 = 研究增量', 'G1→G4 研究浏览顺序', '不是买卖点',
      '不做因果拼接', '无分数、不是收益排序']) {
      expect(outside, `默认可见区不得重复「${s}」`).not.toContain(s);
      expect(html, `口径仍须可查「${s}」`).toContain(s);
    }
    // 每张卡重复挂的 caveat 已移除（177 张卡 × 2 条 → 0）
    expect(html).not.toContain('历史统计，未校准，不预测未来涨跌；只作行情附注');
    expect(html).not.toContain('关联是序列匹配，不证明因果；机制轨整体见下方独立信息流');
    // 评估视图的免责也收进折叠，但必要声明仍在
    expect(evalHtml).toContain('wb-eval-caliber');
    expect(evalHtml).toContain('不是未来概率');
    expect(evalHtml).toContain('不参与有效性验收');
  });

  it('★★ 三个视图都无裸 Markdown 星号（研究侧字符串一律过 RichText）', () => {
    expect(html).not.toContain('**');
    expect(evalHtml).not.toContain('**');
    expect(archiveHtml).not.toContain('**');
  });

  it('★★ 主题挖掘区与档案区不出现禁用措辞', () => {
    const discoveryBlock = html.slice(html.indexOf('data-frontier-section="discovery"'),
      html.indexOf('data-frontier-section="fuzzy"'));
    const weeklyBlock = archiveHtml.slice(archiveHtml.indexOf('data-weekly-archive="1"'),
      archiveHtml.indexOf('data-archived-themes="1"'));
    const declBlock = evalHtml.slice(evalHtml.indexOf('data-phase-declarations="1"'));
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '评分', '龙头', '弹性']) {
      expect(discoveryBlock, `主题挖掘区不得出现 ${banned}`).not.toContain(banned);
      expect(weeklyBlock, `档案周报区不得出现 ${banned}`).not.toContain(banned);
      expect(declBlock, `声明时间线不得出现 ${banned}`).not.toContain(banned);
    }
    expect(discoveryBlock.length).toBeGreaterThan(100);
    expect(weeklyBlock.length).toBeGreaterThan(100);
  });
});

/** ★★ v0.82：默认工作台换成「从行情 + 信息挖出来的主题」，不是历史研究记录。 */
describe('I · 数据驱动的主题挖掘（不预设主题集合）', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★★ 主题由两轨输入聚出，sections 由产物给出（前端不重算）', () => {
    expect(td.artifact).toBe('theme_discovery');
    expect(td.as_of).toBe(td.market_as_of);
    expect(td.feed_window[0] <= td.feed_window[1]).toBe(true);
    const ruleSections = td.rules.sections as unknown as Record<string, string>;
    const bySection = td.counts.by_section as unknown as Record<string, number>;
    for (const k of ['G1', 'G2', 'G3', 'G4'] as const) {
      expect(ruleSections[k]).toBeTruthy();
      expect(bySection[k]).toBe(k === 'G4' ? td.sections.G4.total : td.sections[k].items.length);
    }
    expect(html).toContain(`data-theme-discovery="1"`);
    expect(html).toContain(`as_of <code>${td.as_of}</code>`);
    // G3 是「信息已到、行情未动」的提前观察重点，必须在默认页可见
    for (const c of td.sections.G3.items) {
      expect(html).toContain(`data-theme-candidate="${c.theme_id}"`);
      expect(html).toContain(`data-theme-section="G3"`);
      expect(html).toContain(`data-theme-board="${c.board_series}"`);
    }
    for (const c of td.sections.G1.items) {
      expect(html).toContain(`data-theme-candidate="${c.theme_id}"`);
    }
  });

  it('★★ 每个主题候选都有可核信息侧 URL + 客观行情量 + 成分/角色缺口原因', () => {
    const all = [...td.sections.G1.items, ...td.sections.G3.items];
    expect(all.length).toBe(td.counts.theme_candidates);
    for (const c of all) {
      expect(c.information_side.events.length).toBeGreaterThan(0);
      expect(c.why_now.length).toBeGreaterThan(10);
      expect(c.caveat.length).toBeGreaterThan(10);
      expect(c.constituent_availability.reason.length).toBeGreaterThan(5);
      expect(c.historical_roles.status.length).toBeGreaterThan(0);
      for (const e of c.information_side.events) {
        expect(e.url).toMatch(/^https?:\/\//);
        expect(e.rationale.length).toBeGreaterThan(0);
        expect(html).toContain(`data-theme-event="${e.event_id}"`);
      }
      // 行情量是历史描述统计；缺数据必须写原因而不是显示 0
      expect(['number', 'object']).toContain(typeof c.market_side.excess_20_pp);
    }
  });

  it('★★ 零打分零排序零推荐：宪法字段与措辞都不进产物和页面', () => {
    // ★ 只查真实键名：产物里的「不产出 score / ranking…」是否定式声明文字，不是字段
    const keys = new Set<string>();
    const walk = (v: unknown) => {
      if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v === 'object') {
        for (const [k, x] of Object.entries(v as Record<string, unknown>)) { keys.add(k); walk(x); }
      }
    };
    walk(td);
    for (const banned of ['priority_score', 'wilson_low', 'calibrated', 'is_probability',
      'ranking', 'score', 'recommendation', 'prediction']) {
      expect(keys.has(banned), `产物不得有字段 ${banned}`).toBe(false);
    }
    for (const banned of ['龙头', '弹性', '荐股', '选股清单', '买入', '卖出', '评分']) {
      expect(html, `默认页不得含 ${banned}`).not.toContain(banned);
    }
    expect(String(td.rules.not_a_ranking)).toContain('不是优先级排序');
    expect(String(td.rules.not_a_recommendation)).toContain('不是预测');
    // 分组内按 board_series 字典序，确定性（不是按涨幅排序）
    const ids = td.sections.G3.items.map((c) => c.theme_id);
    expect(ids).toEqual([...ids].sort());
  });

  it('★★ 词表显式映射，构建时双向校验；未命中逐条写原因', () => {
    const noLink = td.counts.no_link_reasons as unknown as Record<string, number>;
    const bySection = td.counts.by_section as unknown as Record<string, number>;
    expect(td.counts.dropped_mappings).toBe(0);
    expect(td.counts.events_with_board_link).toBeGreaterThan(0);
    expect(noLink).toBeTruthy();
    expect(Object.values(noLink).every((n) => Number(n) > 0)).toBe(true);
    // ★★ 单位守恒：命中「事件数」+ 未命中「事件数」== 窗口事件数；关联条目数另算
    expect(Number(td.counts.events_with_board_link) + Object.values(noLink)
      .reduce((a, b) => a + Number(b), 0)).toBe(td.counts.events_in_window);
    expect(Number(td.counts.board_link_entries))
      .toBeGreaterThanOrEqual(Number(td.counts.events_with_board_link));
    // ★★ 互斥全覆盖：G1–G4 + 显式排除的杂项桶 == 扫描序列数
    expect(['G1', 'G2', 'G3', 'G4'].reduce((a, k) => a + bySection[k], 0)
      + Number(td.counts.excluded_fuzzy_gate_hit)).toBe(td.counts.scanned_series);
    expect(td.sections.G4.excluded_interpretable_false.count)
      .toBe(td.counts.excluded_fuzzy_gate_hit);
    expect(html).toContain(`data-excluded-fuzzy="${td.counts.excluded_fuzzy_gate_hit}"`);
    expect(html).toContain('不可解释杂项桶');
    expect(td.sections.G4.reason.length).toBeGreaterThan(10);
    expect(html).toContain('data-insufficient="1"');
    expect(html).toContain('证据不足');
    expect(html).toContain(`data-market-only="1"`);
    expect(html).toContain(`data-market-only-row=`);
  });

  it('★★ 个股层只给历史 PIT 角色记录（带来源），不给当前标的判断', () => {
    const a = td.historical_role_archive;
    expect(a.theme_families.length).toBe(td.counts.historical_role_families);
    expect(a.total_pit_safe_roles).toBeGreaterThan(0);
    expect(html).toContain('data-role-archive="1"');
    for (const f of a.theme_families) {
      expect(html).toContain(`data-role-family="${f.theme_id}"`);
      expect(f.roles.length).toBeGreaterThan(0);
      for (const r of f.roles) {
        // 产物只保留 pit_safe 记录（由 --check 保证），每条带识别日与来源
        expect(r.identified_date).toBeTruthy();
        expect(r.role.length).toBeGreaterThan(0);
        expect(r.source_record || r.evidence_url).toBeTruthy();
        expect(html).toContain(`data-role-row="${r.security_id ?? ''}"`);
      }
    }
    expect(a.note).toContain('历史');
    expect(html).toContain(data_role_note(a.note));
  });

  it('★★ as_of / 计数由产物派生，页面与产物对得上', () => {
    expect(html).toContain(`<strong>${td.counts.scanned_series}</strong>`);
    expect(html).toContain(`<strong>${td.counts.theme_candidates}</strong>`);
    expect(html).toContain(`主题候选`);
    expect(td.source_sha256_16).toBeTruthy();
    expect(Object.keys(td.source_sha256_16).length).toBeGreaterThanOrEqual(4);
  });
});

/** 产物里的 note 含 ** 强调，页面过 RichText；这里只取纯文字片段做对账。 */
function data_role_note(note: string): string {
  return note.replace(/\*\*/g, '').split('；')[0].slice(0, 12);
}
