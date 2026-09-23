import { describe, expect, it } from 'vitest';
import {
  campaignDrivers,
  conflictSeverity,
  derivePhases,
  fromTimelineExportV1,
  getConflictBoundaryCandidates,
  peakWindowOf,
  previewTimelineSource,
  samePeriodCampaigns,
  samePeriodWindow,
  validateTimelineExportV1,
  verifiedTimelineSource,
} from '../timelineAdapter';
import { timelineExportData } from '../timelinePreview';
import { allCampaigns, campaignById, verifiedCampaigns } from '../../index';
import { yearFraction, marketTodayISO } from '../../../utils';
import { fixtureCampaigns, fixtureCrossYearMedia } from '../../../../tests/fixtures/campaignFixtures';
import type { TimelineExportV1 } from '../timelineTypes';

/* ---------------- 真实导出（canonical v1.0）---------------- */

/** 真实导出的深拷贝（测试内可安全篡改） */
function cloneExport(): TimelineExportV1 {
  return JSON.parse(JSON.stringify(timelineExportData)) as TimelineExportV1;
}

/**
 * 数据快照回归：锁定当前消费的 Research 导出版本。
 * 注意：这不是永久业务常量——Research 导出更新后需同步更新此快照值。
 * 本快照 = **Research Core Release**（R01-01~06 全部入库：52 Campaign / 27 Research Candidate /
 * 79 Historical Objects；Driver Canonicalization v0.4 · SA v0.4 · Time Observation v0.2）。
 * JSON 内嵌 source_commit 按 Research 生成约定指向生成时的父 commit。
 */
describe('数据快照回归：timeline_export_v1 版本', () => {
  it('source_commit 为当前同步的 Research 导出（生成时父 commit）', () => {
    expect(timelineExportData.source_commit).toBe('c56e70fc428cc711bff7af27203f70953131425b');
  });

  it('数据量快照：52 Campaign / 27 Candidate / 22 Signal / 138 Event / 258 Security', () => {
    expect(timelineExportData.campaigns).toHaveLength(52);
    expect(timelineExportData.research_candidates).toHaveLength(27);
    expect(timelineExportData.signals).toHaveLength(22);
    expect(timelineExportData.events).toHaveLength(138);
    expect(timelineExportData.securities).toHaveLength(258);
  });
});

describe('V1.7.1：lifecycle / drivers 新字段（Research V1.7 同步）', () => {
  it('全部 52 个 Campaign 均携带非空 lifecycle', () => {
    // ★ 契约（Research Core Release）：
    //   · **Campaign**：全部必须携带非空 lifecycle（52 / 52）。
    //   · **Research Candidate**：**允许为空** —— 但当前 27 个中有 16 个为空，
    //     而它们的 **intake 包内均有 lifecycle**，说明这是 **export 映射表
    //     `CANDIDATE_LIFECYCLE` 覆盖不全（11 / 27）** 造成的 **Research 侧数据缺口**，
    //     **不是**「该对象本就没有生命周期」。
    //     → 这是**已记录的 P0 缺口**，见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`；
    //       本测试**显式锁定当前覆盖数**，使缺口在 CI 中可见，而不是用模糊断言掩盖。
    for (const c of timelineExportData.campaigns) {
      expect(c.lifecycle!.length).toBeGreaterThan(0);
    }
    const rcWithLifecycle = timelineExportData.research_candidates.filter(
      (rc) => (rc.lifecycle ?? []).length > 0,
    );
    expect(rcWithLifecycle).toHaveLength(23);
    expect(timelineExportData.research_candidates).toHaveLength(27);
  });

  it('全部主体均携带 drivers 四问（start / accelerator / turning / ending）', () => {
    const all = [...timelineExportData.campaigns, ...timelineExportData.research_candidates];
    for (const c of all) {
      expect(Array.isArray(c.drivers!.start)).toBe(true);
      expect(Array.isArray(c.drivers!.accelerator)).toBe(true);
      expect(Array.isArray(c.drivers!.turning)).toBe(true);
      expect(Array.isArray(c.drivers!.ending)).toBe(true);
    }
  });

  it('抽查：C-2019-AD / C-2022-POLICY / C-2024-ROBOTAXI 的 lifecycle 与 drivers 均存在', () => {
    for (const id of ['C-2019-AD', 'C-2022-POLICY', 'C-2024-ROBOTAXI']) {
      const c = timelineExportData.campaigns.find((x) => x.campaign_id === id)!;
      expect(c.lifecycle!.length).toBeGreaterThan(0);
      expect(c.drivers!.start.length).toBeGreaterThan(0);
    }
  });

  it('视图层透传：preview 数据源的 Campaign 携带 lifecycle / drivers（生产 verified 无）', () => {
    const source = previewTimelineSource();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        // ★ Campaign 一律必须有 lifecycle；Research Candidate 允许为空（见上条契约说明）
        if (c.kind === 'campaign') {
          expect(c.lifecycle!.length).toBeGreaterThan(0);
        }
        expect(c.drivers).toBeDefined();
      }
    }
    const verifiedCmp = verifiedTimelineSource(fixtureCampaigns).yearData(2023).campaigns[0];
    expect(verifiedCmp.lifecycle).toBeUndefined();
    expect(verifiedCmp.drivers).toBeUndefined();
  });
});

describe('Contract v1.0：canonical 校验', () => {
  it('真实 timeline_export_v1.json 通过校验（无问题项）', () => {
    expect(validateTimelineExportV1(timelineExportData)).toEqual([]);
  });

  it('旧字段 export_version 不再接受（v1.0 白名单外拒绝）', () => {
    const data = cloneExport();
    (data as unknown as Record<string, unknown>).export_version = '1';
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('export_version'))).toBe(true);
  });

  it('旧字段 source_project 不再接受；timeline_export_version 必须为 1.0', () => {
    const data = cloneExport();
    (data as unknown as Record<string, unknown>).source_project = 'Cycle-Research';
    (data as unknown as Record<string, unknown>).timeline_export_version = '0.9';
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('source_project'))).toBe(true);
    expect(issues.some((i) => i.includes('timeline_export_version 必须为'))).toBe(true);
  });

  it('未知顶层字段被拒绝；缺少必填顶层字段报缺失', () => {
    const data = cloneExport();
    (data as unknown as Record<string, unknown>).purpose = 'test';
    delete (data as unknown as Record<string, unknown>).securities;
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('未知顶层字段 "purpose"'))).toBe(true);
    expect(issues.some((i) => i.includes('缺少顶层字段 "securities"'))).toBe(true);
  });

  it('campaign 的 status 与 research_status 不一致时报错；candidate 携带生产 status 报错', () => {
    const data = cloneExport();
    data.campaigns[0].status = 'verified'; // 实际应为 provisional
    (data.research_candidates[0] as unknown as Record<string, unknown>).status = 'preview'; // 候选不得有生产 status
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('status "verified" 与 research_status "PROVISIONAL" 不一致'))).toBe(true);
    expect(issues.some((i) => i.includes('候选不得携带生产 status'))).toBe(true);
  });

  it('signals 归必须为 campaign_id XOR research_candidate_id；引用缺失报错', () => {
    const data = cloneExport();
    data.signals = [
      { type: 'EARLY_SIGNAL', date: '2024-06-01', confidence: 'high', campaign_id: 'C-2024-ROBOTAXI', research_candidate_id: 'RC-2024-SECONDARY' },
      { type: 'EARLY_SIGNAL', date: '2024-06-02', confidence: 'low', campaign_id: 'C-NOPE' },
    ];
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('XOR'))).toBe(true);
    expect(issues.some((i) => i.includes('campaign_id "C-NOPE" 不存在'))).toBe(true);
  });

  it('非法导出（校验失败）抛错并携带问题清单', () => {
    expect(() => fromTimelineExportV1({ wrong: true } as unknown as TimelineExportV1)).toThrow(
      /校验失败/,
    );
  });
});

describe('年份推导与空态年份', () => {
  it('years() 升序、连续，且恰好覆盖导出对象的年份区间（数据驱动）', () => {
    const source = previewTimelineSource();
    const years = source.years();
    // 升序且无重复
    expect(years).toEqual([...years].sort((a, b) => a - b));
    expect(new Set(years).size).toBe(years.length);
    // 连续（步长 1）
    for (let i = 1; i < years.length; i += 1) expect(years[i] - years[i - 1]).toBe(1);
    // 区间 = 导出中全部对象的 min/max year（不写死具体年份，避免与 universe 耦合）
    const allYears = [
      ...timelineExportData.campaigns.map((c) => c.year),
      ...timelineExportData.research_candidates.map((rc) => rc.year),
    ];
    expect(years[0]).toBe(Math.min(...allYears));
    expect(years[years.length - 1]).toBe(Math.max(...allYears));
  });

  it('范围外年份：campaigns 为空数组（空态合法，不编造行情）', () => {
    // ★ 当前 universe（79 objects）覆盖 2015–2025，**每个年份都有对象** ——
    //   因此「空态」不能用覆盖范围内的年份验证，必须用**范围外**年份。
    const source = previewTimelineSource();
    const years = source.years();
    const outside = [Math.min(...years) - 1, Math.max(...years) + 1];
    for (const y of outside) {
      const d = source.yearData(y);
      expect(d.campaigns).toEqual([]);
      expect(d.researchEvents ?? []).toEqual([]);
    }
  });

  it('有 Campaign 的年份：campaigns 非空（无凭空丢失）', () => {
    const source = previewTimelineSource();
    const campaignYears = new Set(timelineExportData.campaigns.map((c) => c.year));
    for (const y of campaignYears) {
      expect(source.yearData(y).campaigns.length).toBeGreaterThan(0);
    }
  });
});

describe('Conflict：保留 candidate A / B 双方（V1.7.1 数据现状）', () => {
  it('C-2022-POLICY：研究已解决 start 分歧 → provisional，无 conflicts', () => {
    const c = previewTimelineSource()
      .yearData(2022)
      .campaigns.find((x) => x.campaign_id === 'C-2022-POLICY');
    expect(c).toBeDefined();
    // 旧导出（4bbe257）为 CONFLICT（start 04-27 vs 05-23）；V1.7 导出（eadf06a）
    // 研究结论已定：起点 04-27，05-23 为 THEME_FORMING 信号（不再渲染分歧）
    expect(c!.status).toBe('provisional');
    expect(c!.conflicts ?? []).toEqual([]);
    expect(c!.start).toBe('2022-04-27');
    expect(c!.start <= c!.end).toBe(true);
  });

  it('C-2024-ROBOTAXI：end 单分歧（peak 分歧已解决），status=conflict', () => {
    const c = previewTimelineSource()
      .yearData(2024)
      .campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI');
    expect(c).toBeDefined();
    expect(c!.status).toBe('conflict');
    // 旧导出为 peak + end 双分歧；V1.7 研究将 peak 定为 07-29（lifecycle PEAK 窗口 07-29 ~ 08-05）
    expect(c!.conflicts!.some((x) => x.field === 'peak_date')).toBe(false);
    expect(c!.conflicts!.some((x) => x.field === 'end_date')).toBe(true);
    // 冲突数据仍渲染 Campaign 本体，不因分歧消失
    expect(c!.start <= c!.end).toBe(true);
  });
});

describe('Conflict 边界候选推导：getConflictBoundaryCandidates', () => {
  const source = previewTimelineSource();
  const c2022 = source.yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
  const c2024 = source.yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
  const normal = source.yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-V2X')!;

  it('conflict end 有 2 个候选（2024：07-31 / 08-23）', () => {
    const { endCandidates } = getConflictBoundaryCandidates(c2024);
    expect(endCandidates).toEqual(['2024-07-31', '2024-08-23']);
  });

  it('V1.7.1 数据现状：2022 start 分歧已解决 → 三个候选集均为 null（不再渲染分歧）', () => {
    expect(c2022.status).toBe('provisional');
    expect(getConflictBoundaryCandidates(c2022)).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });

  it('V1.7.1 数据现状：2024 peak 分歧已解决 → peak 候选集为 null（Peak 由 lifecycle 窗口表达）', () => {
    const { peakCandidates, startCandidates } = getConflictBoundaryCandidates(c2024);
    expect(peakCandidates).toBeNull();
    expect(startCandidates).toBeNull();
  });

  it('非 conflict Campaign 保持原状：三个候选集均为 null', () => {
    expect(getConflictBoundaryCandidates(normal)).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });

  it('2024 end 分歧保留：双方日期均在候选集（不自动选择）', () => {
    const { endCandidates } = getConflictBoundaryCandidates(c2024);
    expect(endCandidates).toContain('2024-07-31');
    expect(endCandidates).toContain('2024-08-23');
  });

  it('不自动选择候选：campaign 正式字段仍为 DB Candidate（A），未被 B 覆盖', () => {
    // C-2024-ROBOTAXI 正式字段 = Candidate A（start 07-08 / peak 07-29 / end 07-31）
    expect(c2024.start).toBe('2024-07-08');
    expect(c2024.peak).toBe('2024-07-29');
    expect(c2024.end).toBe('2024-07-31');
    // C-2022-POLICY 正式起点 = 研究确定值 04-27（旧 start 分歧已解决）
    expect(c2022.start).toBe('2022-04-27');
  });

  it('conflict Campaign 保持 status=conflict（视觉分歧语义的触发条件）', () => {
    expect(c2024.status).toBe('conflict');
    // 2022 已不再 conflict（研究解决）——conflict 是数据属性，不是历史包袱
    expect(c2022.status).not.toBe('conflict');
    // helper 仅对 conflict 状态生效（防御性验证）
    expect(getConflictBoundaryCandidates({ status: 'conflict', conflicts: undefined })).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });

  it('verified / provisional / preview Campaign 不触发 conflict 视觉（状态与候选集）', () => {
    // C-2024-V2X / C-2022-POLICY（V1.7.1 起）= provisional；RC 候选 = preview
    expect(normal.status).toBe('provisional');
    expect(c2022.status).toBe('provisional');
    const rc = source.yearData(2023).campaigns.find((x) => x.campaign_id === 'RC-2023-HUAWEI')!;
    expect(rc.status).toBe('preview');
    expect(getConflictBoundaryCandidates(rc).startCandidates).toBeNull();
    // verified fixture 同样无候选集
    const verifiedCmp = verifiedTimelineSource(fixtureCampaigns).yearData(2023).campaigns[0];
    expect(verifiedCmp.status).toBe('verified');
    expect(getConflictBoundaryCandidates(verifiedCmp)).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });
});

/* ---------------- V1.7：Phase Window / 冲突分级 / 驱动因素 / 同周期 ---------------- */

describe('V1.7：Peak Window（窗口优先于精确日期）', () => {
  it('正常峰值：peak ± 7 天窗口（C-2020-NEV：07-06 ~ 07-20，非分歧）', () => {
    const c = previewTimelineSource().yearData(2020).campaigns.find((x) => x.campaign_id === 'C-2020-NEV')!;
    const w = peakWindowOf(c);
    expect(w).toEqual({ start: '2020-07-06', end: '2020-07-20', disputed: false });
  });

  it('lifecycle PEAK 窗口（V1.7.1）：C-2024-ROBOTAXI 07-29 ~ 08-05（DATE_WINDOW，peak 分歧已解决）', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const w = peakWindowOf(c);
    expect(w).toEqual({ start: '2024-07-29', end: '2024-08-05', disputed: false });
  });

  it('无 peak（null）→ 无窗口；openEnded 候选同样安全', () => {
    expect(peakWindowOf({ peak: null, status: 'preview', conflicts: undefined })).toBeNull();
  });
});

describe('V1.7：冲突分级阈值（同一窗口 ≤ 10 天 = minor）', () => {
  it('2024 peak 分歧已解决（V1.7.1 数据现状）：无 peak_date conflict，窗口改由 lifecycle 提供', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    expect(c.conflicts!.find((x) => x.field === 'peak_date')).toBeUndefined();
  });

  it('2022 start 分歧已解决（V1.7.1 数据现状）：provisional，无 conflict 视觉', () => {
    const c = previewTimelineSource().yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
    expect(c.status).toBe('provisional');
    expect(c.conflicts ?? []).toEqual([]);
  });

  it('2024 end 分歧（07-31 vs 08-23，23 天）→ major：End 候选区间保留', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const end = c.conflicts!.find((x) => x.field === 'end_date')!;
    expect(conflictSeverity(end)).toBe('major');
  });

  it('边界：恰好 10 天 → minor；11 天 → major', () => {
    const mk = (a: string, b: string) => ({
      field: 'peak_date',
      candidate_a: { date: a, label: 'A' },
      candidate_b: { date: b, label: 'B' },
    });
    expect(conflictSeverity(mk('2024-07-01', '2024-07-11'))).toBe('minor');
    expect(conflictSeverity(mk('2024-07-01', '2024-07-12'))).toBe('major');
  });
});

describe('V1.7：驱动因素四问（研究事件时间归组）', () => {
  it('C-2022-POLICY（V1.7.1）：研究归因优先，四问均有标签且每组封顶 3 条', () => {
    const c = previewTimelineSource().yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
    const d = campaignDrivers(c);
    // Research drivers：start 3 条 / accelerator 原始 4 条 → 封顶 3 / turning 3 / ending 2
    expect(d.start.some((t) => t.includes('国常会'))).toBe(true);
    expect(d.accelerate).toHaveLength(3);
    expect(d.accelerate.some((t) => t.includes('财政部'))).toBe(true);
    expect(d.turn.some((t) => t.includes('比亚迪'))).toBe(true);
    expect(d.end.length).toBeGreaterThan(0);
  });

  it('C-2024-ROBOTAXI（V1.7.1）：研究归因——启动含萝卜快跑、转折含 8/6 回撤、结束含 08-23', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const d = campaignDrivers(c);
    expect(d.start.some((t) => t.includes('萝卜快跑'))).toBe(true);
    expect(d.turn.some((t) => t.includes('8/6'))).toBe(true);
    expect(d.end.some((t) => t.includes('08-23'))).toBe(true);
  });

  it('无事件的 Campaign：四问全空 → UI 显示"暂无可靠归因"（verified fixture）', () => {
    const cmp = verifiedTimelineSource(fixtureCampaigns).yearData(2023).campaigns[0];
    expect(cmp.events).toEqual([]);
    const d = campaignDrivers(cmp);
    expect(d).toEqual({ start: [], accelerate: [], turn: [], end: [] });
  });

  it('openEnded 候选（V1.7.1）：研究归因 ending = unknown 原样展示（未确认结束，不编造）', () => {
    const rc = previewTimelineSource().yearData(2023).campaigns.find((x) => x.campaign_id === 'RC-2023-HUAWEI')!;
    const d = campaignDrivers(rc);
    expect(d.end).toEqual(['unknown（至2023-10-31仍升，未确认结束）']);
    expect(d.start.some((t) => t.includes('问界新M7'))).toBe(true);
  });

  it('无 drivers 回退路径（生产 verified / 旧导出）：事件按时间归组（first-match，不重复归组）', () => {
    const d = campaignDrivers({
      start: '2024-07-01',
      peak: '2024-08-01',
      end: '2024-08-31',
      openEnded: false,
      events: [
        { name: '事件甲（07-10 启动期）', date: '2024-07-10', event_type: 'policy', role: 'trigger' },
        { name: '事件乙（07-20 加速期）', date: '2024-07-20', event_type: 'market', role: 'catalyst' },
        { name: '事件丙（07-28 峰值附近）', date: '2024-07-28', event_type: 'market', role: null },
        { name: '事件丁（08-20 尾声）', date: '2024-08-20', event_type: 'market', role: null },
      ],
    });
    expect(d.start).toEqual(['事件甲（07-10 启动期）']);
    expect(d.accelerate).toEqual(['事件乙（07-20 加速期）']);
    expect(d.turn).toEqual(['事件丙（07-28 峰值附近）']);
    expect(d.end).toEqual(['事件丁（08-20 尾声）']);
  });
});

describe('V1.7：历史同周期查看（列表，非统计模型）', () => {
  it('窗口口径：9 月 → 08-15 ~ 10-15；1 月跨年 → 前年 12-15 ~ 当年 02-15', () => {
    expect(samePeriodWindow(2026, 9)).toEqual({ start: '2026-08-15', end: '2026-10-15' });
    expect(samePeriodWindow(2026, 1)).toEqual({ start: '2025-12-15', end: '2026-02-15' });
    expect(samePeriodWindow(2026, 12)).toEqual({ start: '2026-11-15', end: '2027-01-15' });
  });

  it('9 月同期：行 = 全部覆盖年份；每行只含与该年 9 月窗口真实相交的对象（不写死 ID 清单）', () => {
    const source = previewTimelineSource();
    const rows = samePeriodCampaigns(source, 9);

    // 行 = source.years()（升序、无重复、不多不少）
    expect(rows.map((r) => r.year)).toEqual(source.years());

    const allIds = new Set<string>();
    for (const row of rows) {
      const win = samePeriodWindow(row.year, 9);
      const ids = row.campaigns.map((c) => c.campaign_id);
      // 行内无重复
      expect(new Set(ids).size).toBe(ids.length);
      for (const c of row.campaigns) {
        allIds.add(c.campaign_id);
        // ★ 核心不变量：命中窗口的对象必须**真的**与该年窗口相交（不是靠名字或年份猜的）
        const s = c.start;
        const e = c.end ?? c.start;
        expect(e >= win.start && s <= win.end).toBe(true);
        // ★ 注意：`c.year` 是**对象自身的研究年份**，而 row.year 是**窗口年份** ——
        //   跨年对象会出现在多个年份行（这是「跨年结构性 Campaign」的既有语义），
        //   因此 **不得** 断言二者相等；真正的不变量是上面的窗口相交。
        //   但对象必须在窗口年份「可见」（其区间覆盖该年）。
        expect(c.start.slice(0, 4) <= String(row.year) && String(row.year) <= e.slice(0, 4)).toBe(true);
      }
    }

    // 至少有一个年份命中（否则断言会空洞通过）
    expect(rows.some((r) => r.campaigns.length > 0)).toBe(true);
    // 反向不变量：未被任何年份行收录的对象，必须确实与该月窗口不相交
    const allObjects = [
      ...timelineExportData.campaigns.map((c) => ({ id: c.campaign_id, year: c.year, start: c.start_date, end: c.end_date })),
      ...timelineExportData.research_candidates.map((c) => ({ id: c.campaign_id, year: c.year, start: c.start_date, end: c.end_date })),
    ];
    for (const o of allObjects) {
      if (allIds.has(o.id)) continue;
      const win = samePeriodWindow(o.year, 9);
      const e = o.end ?? o.start;
      expect(e === null || o.start === null || !(e >= win.start && o.start <= win.end)).toBe(true);
    }
  });

  it('2 月同期：跨年结构性 Campaign 使 2 月窗口多年命中（不写死 ID 清单）', () => {
    const source = previewTimelineSource();
    const rows = samePeriodCampaigns(source, 2);

    expect(rows.map((r) => r.year)).toEqual(source.years());

    for (const row of rows) {
      const win = samePeriodWindow(row.year, 2);
      for (const c of row.campaigns) {
        const e = c.end ?? c.start;
        // ★ 核心不变量：命中 2 月窗口的对象必须真的与该年 2 月窗口相交
        expect(e >= win.start && c.start <= win.end).toBe(true);
        // `c.year` 为对象自身研究年份，窗口年份为 row.year —— 跨年对象二者可不同
        expect(c.start.slice(0, 4) <= String(row.year) && String(row.year) <= e.slice(0, 4)).toBe(true);
      }
    }

    // ★ 跨年语义（本测试的真实意图）：
    //   存在**跨年结构性**对象在 2 月窗口命中 **≥2 个不同年份** ——
    //   这与「季节性 Campaign」只命中单年形成语义差异（见审计报告 F-MED-2）。
    const hitYears = new Map<string, number>();
    for (const row of rows) {
      for (const c of row.campaigns) {
        hitYears.set(c.campaign_id, (hitYears.get(c.campaign_id) ?? 0) + 1);
      }
    }
    expect([...hitYears.values()].some((n) => n >= 2)).toBe(true);
    // 注：**不**断言「必须存在空态年份行」—— 2 月窗口在当前 universe 下可能每年都有
    //     跨年对象命中，那是合法状态（空态另由「范围外年份」用例覆盖）。
  });

  it('preview / production 隔离：生产 verified 空 → 同周期无结果，不消费 preview 数据', () => {
    expect(samePeriodCampaigns(verifiedTimelineSource(), 9)).toEqual([]);
    // fixture 注入的 verified 源可用（同一接口），但不混入 preview 行情
    const fixtureRows = samePeriodCampaigns(verifiedTimelineSource(fixtureCampaigns), 6);
    expect(fixtureRows.length).toBeGreaterThan(0);
    expect(fixtureRows.some((r) => r.campaigns.some((c) => c.campaign_id.startsWith('C-20')))).toBe(false);
  });
});

describe('Research Candidate：并列来源，非 Historical Confirmed Campaign', () => {
  it('RC-2023-HUAWEI / RC-2024-SECONDARY 在 preview 年份可见且 kind=candidate', () => {
    const source = previewTimelineSource();
    const huawei = source
      .yearData(2023)
      .campaigns.find((x) => x.campaign_id === 'RC-2023-HUAWEI');
    const secondary = source
      .yearData(2024)
      .campaigns.find((x) => x.campaign_id === 'RC-2024-SECONDARY');
    expect(huawei).toBeDefined();
    expect(secondary).toBeDefined();
    expect(huawei!.kind).toBe('candidate');
    expect(secondary!.kind).toBe('candidate');
    // 候选永不映射 verified
    expect(['preview', 'conflict']).toContain(huawei!.status);
    expect(['preview', 'conflict']).toContain(secondary!.status);
  });

  it('candidate 不进入生产 allCampaigns / verifiedCampaigns / campaignById', () => {
    expect(allCampaigns).toEqual([]);
    expect(verifiedCampaigns).toEqual([]);
    const candidateIds = ['RC-2023-HUAWEI', 'RC-2024-SECONDARY'];
    for (const id of candidateIds) {
      expect(campaignById.has(id)).toBe(false);
    }
  });

  it('正式 Campaign（kind=campaign）与 candidate 在同一 years 数据中共存但可区分', () => {
    const y2023 = previewTimelineSource().yearData(2023);
    const kinds = new Set(y2023.campaigns.map((c) => c.kind));
    expect(kinds.has('campaign')).toBe(true);
    expect(kinds.has('candidate')).toBe(true);
  });
});

describe('Preview / 冲突徽章与来源标注', () => {
  it('preview 徽章：所有预览行情 sourceNote 标注非正式历史事实 + Research 来源', () => {
    const source = previewTimelineSource();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        expect(c.sourceNote).toContain('非正式历史事实');
        expect(c.sourceNote).toContain('Cycle-Research');
      }
    }
  });

  it('conflict 徽章：Campaign 的 conflict 必须携带分歧数据；RC 的分类级 CONFLICT 不得被伪造成日期分歧', () => {
    // ★ 契约（Research Core Release）：
    //   · **Campaign** `status = conflict` ⇒ 必须携带 `conflicts`（日期级分歧记录）。
    //   · **Research Candidate** `research_status = CONFLICT` 可能是**分类级**判断
    //     （例：`RC-2020-FIN-BROKER-VOLUME` intake 原文为「是否将券商行情整体降级」的归属分歧，
    //      **intake 包内并无 `conflicts` 字段**）→ 此时**不得**伪造日期级 conflicts。
    //     UI 文案为「研究结论存在分歧」而非「日期存在分歧」，语义正确。
    const source = previewTimelineSource();
    let campaignConflict = 0;
    let rcClassificationConflict = 0;
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        if (c.status !== 'conflict') continue;
        if (c.kind === 'campaign') {
          campaignConflict += 1;
          expect((c.conflicts ?? []).length).toBeGreaterThan(0);
        } else {
          rcClassificationConflict += 1;
          // 允许为空，但若为空则必须**确实**在 export 侧没有 conflicts 记录（不伪造）
          const raw = [
            ...timelineExportData.campaigns,
            ...timelineExportData.research_candidates,
          ].find((x) => x.campaign_id === c.campaign_id);
          expect(raw).toBeDefined();
          expect((c.conflicts ?? []).length).toBe((raw!.conflicts ?? []).length);
        }
      }
    }
    // 两类都必须真实存在，否则断言空洞
    expect(campaignConflict).toBeGreaterThan(0);
    expect(rcClassificationConflict).toBeGreaterThan(0);
  });
});

describe('引用解析：events / securities / signals 挂到正确主体', () => {
  it('Campaign 经 event_ids 引用顶层 events（不要求嵌套）', () => {
    const c = previewTimelineSource()
      .yearData(2020)
      .campaigns.find((x) => x.campaign_id === 'C-2020-NEV');
    expect(c).toBeDefined();
    expect(c!.events.length).toBeGreaterThan(0);
    for (const ev of c!.events) {
      expect(ev.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('securities 经 (security_id, owner) 归属解析：龙头带 ticker', () => {
    const c = previewTimelineSource()
      .yearData(2020)
      .campaigns.find((x) => x.campaign_id === 'C-2020-NEV');
    expect(c!.securities.length).toBeGreaterThan(0);
    for (const s of c!.securities) {
      expect(s.name.length).toBeGreaterThan(0);
    }
  });

  it('signals 归属 campaign：研究信号进入 Timeline（非交易信号语义）', () => {
    const c = previewTimelineSource()
      .yearData(2024)
      .campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI');
    expect(c!.signals.length).toBeGreaterThan(0);
    for (const s of c!.signals) {
      expect(['EARLY_SIGNAL', 'THEME_FORMING', 'CONFIRMATION_CANDIDATE']).toContain(s.type);
    }
  });

  it('校验器：campaign 引用不存在的 event_id / security_id 报错', () => {
    const data = cloneExport();
    data.campaigns[0].event_ids = ['E-NOPE'];
    const issues = validateTimelineExportV1(data);
    expect(issues.some((i) => i.includes('E-NOPE'))).toBe(true);
  });
});

describe('Timeline Adapter：verified 生产数据源（隔离不变）', () => {
  it('verified 源正常映射（fixture 注入）：字段、年份、题材/龙头查询', () => {
    const source = verifiedTimelineSource(fixtureCampaigns);
    expect(source.kind).toBe('verified');
    const y2023 = source.yearData(2023);
    const cmp = y2023.campaigns.find((c) => c.campaign_id === 'cmp_auto_2023');
    expect(cmp).toBeDefined();
    expect(cmp!.status).toBe('verified');
    expect(cmp!.kind).toBe('campaign');
    expect(cmp!.start).toBe('2023-06-01');
    expect(cmp!.end).toBe('2023-08-31');
    expect(y2023.campaigns.some((c) => c.campaign_id === 'cmp_auto_2024')).toBe(false);
  });

  it('生产当前为空：years() 为空、yearData 无行情（verified 空态合法）', () => {
    const source = verifiedTimelineSource();
    expect(source.years()).toEqual([]);
    expect(source.yearData(2026).campaigns).toEqual([]);
    expect(source.yearData(2026).researchEvents).toBeUndefined();
  });

  it('跨年行情在两年各可见：2026-11-01 → 2027-01-15 出现在 2026 与 2027', () => {
    const source = verifiedTimelineSource([fixtureCrossYearMedia]);
    expect(source.years()).toEqual([2026, 2027]);
    expect(source.yearData(2026).campaigns.some((c) => c.campaign_id === 'cmp_media_2026_2027')).toBe(true);
    expect(source.yearData(2027).campaigns.some((c) => c.campaign_id === 'cmp_media_2026_2027')).toBe(true);
  });
});

describe('生命周期与日期位置（Adapter 渲染规则）', () => {
  it('真实导出：分段按序覆盖 start→end，早期信号早于正式起点', () => {
    const source = previewTimelineSource();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        expect(c.phases[0].start).toBe(c.start);
        expect(c.phases[c.phases.length - 1].end).toBe(c.end);
        for (let i = 1; i < c.phases.length; i += 1) {
          expect(c.phases[i].start).toBe(c.phases[i - 1].end);
        }
        if (c.early_signal) {
          expect(c.early_signal.end <= c.start).toBe(true);
        }
      }
    }
  });

  it('retracement_start 缺省时以 peak→end 中点近似（Adapter 层近似）', () => {
    const phases = derivePhases({
      start: '2023-06-08',
      end: '2023-09-08',
      peak: '2023-07-14',
      retracement_start: null,
    });
    expect(phases).toEqual([
      { phase: 'main_rise', start: '2023-06-08', end: '2023-07-14' },
      { phase: 'retracement', start: '2023-07-14', end: '2023-08-11' },
      { phase: 'declining', start: '2023-08-11', end: '2023-09-08' },
    ]);
  });

  it('无 peak 时退化为单一 main_rise 段（合法状态，不编造峰值）', () => {
    expect(derivePhases({ start: '2024-01-01', end: '2024-03-01', peak: null })).toEqual([
      { phase: 'main_rise', start: '2024-01-01', end: '2024-03-01' },
    ]);
  });

  it('日期位置按真实日期比例（非 12 等分）：7 月 2 日约在年中', () => {
    const f = yearFraction('2023-07-02');
    expect(f).toBeGreaterThan(0.49);
    expect(f).toBeLessThan(0.51);
  });

  it('TODAY 基准：北京已跨日、UTC 未跨日时返回北京日期（Asia/Shanghai）', () => {
    expect(marketTodayISO(new Date('2026-09-12T18:30:00Z'))).toBe('2026-09-13');
  });
});
