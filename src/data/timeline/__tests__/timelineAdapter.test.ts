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
 * 本快照 = Wave 1A 电力设备历史 Cycle 同步（新增 rule_power_equipment +
 * C-2020-POWER-NE / C-2022-POWER-GRID + Macro Theme TH-POWER）。
 * JSON 内嵌 source_commit 按 Research 生成约定指向生成时的父 commit。
 */
describe('数据快照回归：timeline_export_v1 版本', () => {
  it('source_commit 为当前同步的 Research 导出（生成时父 commit）', () => {
    expect(timelineExportData.source_commit).toBe('f446cb8a02128f63835f3fd29c432f1e96a82fd0');
  });

  it('数据量快照：11 Campaign / 4 Candidate / 18 Signal / 42 Event / 54 Security', () => {
    expect(timelineExportData.campaigns).toHaveLength(11);
    expect(timelineExportData.research_candidates).toHaveLength(4);
    expect(timelineExportData.signals).toHaveLength(18);
    expect(timelineExportData.events).toHaveLength(42);
    expect(timelineExportData.securities).toHaveLength(54);
  });
});

describe('V1.7.1：lifecycle / drivers 新字段（Research V1.7 同步）', () => {
  it('全部 9 Campaign 与 4 Research Candidate 均携带非空 lifecycle', () => {
    for (const c of timelineExportData.campaigns) {
      expect(c.lifecycle!.length).toBeGreaterThan(0);
    }
    for (const rc of timelineExportData.research_candidates) {
      expect(rc.lifecycle!.length).toBeGreaterThan(0);
    }
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

  it('视图层透传：preview 数据源的 TimelineCampaign 携带 lifecycle / drivers（生产 verified 无）', () => {
    const source = previewTimelineSource();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        expect(c.lifecycle!.length).toBeGreaterThan(0);
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

describe('年份推导与 2018 反例年份', () => {
  it('2018–2025 全部可见（含无 Campaign 的 2018）', () => {
    expect(previewTimelineSource().years()).toEqual([
      2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025,
    ]);
  });

  it('2018 无 Campaign：空态合法，不编造行情', () => {
    const y2018 = previewTimelineSource().yearData(2018);
    expect(y2018.campaigns).toEqual([]);
    // 2018 通过研究事件出现在时间轴（反例年份也有历史事件可看）
    expect(y2018.researchEvents!.length).toBeGreaterThan(0);
  });

  it('2019–2025 有真实 Research 数据', () => {
    const source = previewTimelineSource();
    for (const y of [2019, 2020, 2021, 2022, 2023, 2024, 2025]) {
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

  it('9 月同期：2018 空、2019-2025 有行情（医药 / 电力设备为跨年 Campaign）、2023/2024 另有 Research Candidate', () => {
    const rows = samePeriodCampaigns(previewTimelineSource(), 9);
    expect(rows.map((r) => r.year)).toEqual([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
    expect(rows[0].campaigns).toEqual([]); // 2018 反例年
    // 2019-2022：医药跨年 Campaign（C-2019-PHARMA-INNOV, 2019-01-02~2022-10-31）每年都命中窗口
    expect(rows[1].campaigns.map((c) => c.campaign_id)).toEqual(['C-2019-PHARMA-INNOV', 'C-2019-AD']);
    expect(rows[2].campaigns.map((c) => c.campaign_id)).toEqual([
      'C-2019-PHARMA-INNOV', 'RC-2020-PANDEMIC', 'C-2020-NEV', 'C-2020-POWER-NE',
    ]);
    expect(rows[3].campaigns.map((c) => c.campaign_id)).toEqual([
      'C-2019-PHARMA-INNOV', 'RC-2020-PANDEMIC', 'C-2020-POWER-NE', 'C-2021-NEV',
    ]);
    // 2022：电力设备发电 Cycle（C-2020-POWER-NE）+ 电网 Cycle（C-2022-POWER-GRID）同时命中
    expect(rows[4].campaigns.map((c) => c.campaign_id)).toEqual([
      'C-2019-PHARMA-INNOV', 'C-2020-POWER-NE', 'RC-2021-TCM', 'C-2022-POWER-GRID', 'C-2022-POLICY',
    ]);
    // 2023-2025：电网 Cycle（C-2022-POWER-GRID, 2022-01-10~2025-12-31）为跨年命中
    expect(rows[5].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID', 'RC-2023-HUAWEI']);
    // 2024：另有 RC-2024-SECONDARY（Robotaxi end 07-31 < 08-15 不相交，故 C-2024-ROBOTAXI 不入）
    expect(rows[6].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID', 'RC-2024-SECONDARY']);
    expect(rows[7].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID', 'C-2025-ROBOTAXI']);
  });

  it('2 月同期：2019-2022 由医药跨年 Campaign 覆盖，2023-2025 由电网跨年 Campaign 覆盖', () => {
    const rows = samePeriodCampaigns(previewTimelineSource(), 2);
    // 医药跨年 Campaign（2019-01-02~2022-10-31）使 2 月窗口不再为空态；
    // 这是「跨年结构性 Campaign」相对「季节性 Campaign」的语义差异（见审计报告 F-MED-2）。
    // 电力设备两个 Cycle 同为跨年结构：发电 2020-09-22~2022-12-30、电网 2022-01-10~2025-12-31。
    expect(rows.map((r) => r.year)).toEqual([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
    expect(rows[0].campaigns).toEqual([]); // 2018
    expect(rows[1].campaigns.map((c) => c.campaign_id)).toEqual(['C-2019-PHARMA-INNOV']);
    expect(rows[2].campaigns.map((c) => c.campaign_id)).toEqual(['C-2019-PHARMA-INNOV', 'RC-2020-PANDEMIC']);
    expect(rows[3].campaigns.map((c) => c.campaign_id)).toEqual([
      'C-2019-PHARMA-INNOV', 'RC-2020-PANDEMIC', 'C-2020-POWER-NE',
    ]);
    expect(rows[4].campaigns.map((c) => c.campaign_id)).toEqual([
      'C-2019-PHARMA-INNOV', 'C-2020-POWER-NE', 'RC-2021-TCM', 'C-2022-POWER-GRID',
    ]);
    expect(rows[5].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID']); // 2023
    expect(rows[6].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID']); // 2024
    expect(rows[7].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POWER-GRID']); // 2025
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

  it('conflict 徽章：状态为 conflict 的行情携带分歧数据', () => {
    const source = previewTimelineSource();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        if (c.status === 'conflict') {
          expect((c.conflicts ?? []).length).toBeGreaterThan(0);
        }
      }
    }
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
