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
 * 数据快照回归：锁定当前消费的 Research 导出版本（V1.6.2 同步）。
 * 注意：这不是永久业务常量——Research 导出更新后需同步更新此快照值。
 */
describe('数据快照回归：timeline_export_v1 版本', () => {
  it('source_commit 为当前同步的 Research 导出（4bbe257）', () => {
    expect(timelineExportData.source_commit).toBe('4bbe257d37d5991a2c6ce33def205df9a67e2593');
  });

  it('数据量快照：8 Campaign / 2 Candidate / 9 Signal / 26 Event / 39 Security', () => {
    expect(timelineExportData.campaigns).toHaveLength(8);
    expect(timelineExportData.research_candidates).toHaveLength(2);
    expect(timelineExportData.signals).toHaveLength(9);
    expect(timelineExportData.events).toHaveLength(26);
    expect(timelineExportData.securities).toHaveLength(39);
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

describe('Conflict：2022 / 2024 保留 candidate A / B 双方', () => {
  it('C-2022-POLICY：start_date 分歧（04-27 vs 05-23），status=conflict', () => {
    const c = previewTimelineSource()
      .yearData(2022)
      .campaigns.find((x) => x.campaign_id === 'C-2022-POLICY');
    expect(c).toBeDefined();
    expect(c!.status).toBe('conflict');
    const startConflict = c!.conflicts!.find((x) => x.field === 'start_date');
    expect(startConflict).toBeDefined();
    expect(startConflict!.candidate_a.date).toBe('2022-04-27');
    expect(startConflict!.candidate_b.date).toBe('2022-05-23');
    // 冲突数据仍渲染 Campaign 本体，不因分歧消失
    expect(c!.start <= c!.end).toBe(true);
  });

  it('C-2024-ROBOTAXI：peak / end 双分歧，status=conflict', () => {
    const c = previewTimelineSource()
      .yearData(2024)
      .campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI');
    expect(c).toBeDefined();
    expect(c!.status).toBe('conflict');
    expect(c!.conflicts!.some((x) => x.field === 'peak_date')).toBe(true);
    expect(c!.conflicts!.some((x) => x.field === 'end_date')).toBe(true);
  });
});

describe('Conflict 边界候选推导：getConflictBoundaryCandidates', () => {
  const source = previewTimelineSource();
  const c2022 = source.yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
  const c2024 = source.yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
  const normal = source.yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-V2X')!;

  it('conflict start 有 2 个候选（2022：04-27 / 05-23）', () => {
    const { startCandidates } = getConflictBoundaryCandidates(c2022);
    expect(startCandidates).toEqual(['2022-04-27', '2022-05-23']);
  });

  it('conflict peak 有 2 个候选 marker（2024：07-29 / 08-05）', () => {
    const { peakCandidates } = getConflictBoundaryCandidates(c2024);
    expect(peakCandidates).toEqual(['2024-07-29', '2024-08-05']);
  });

  it('conflict end 有 2 个候选（2024：07-31 / 08-23）', () => {
    const { endCandidates } = getConflictBoundaryCandidates(c2024);
    expect(endCandidates).toEqual(['2024-07-31', '2024-08-23']);
  });

  it('非 conflict Campaign 保持原状：三个候选集均为 null', () => {
    expect(getConflictBoundaryCandidates(normal)).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });

  it('2022 start 分歧保留：不自动选择 04-27 或 05-23', () => {
    const { startCandidates } = getConflictBoundaryCandidates(c2022);
    expect(startCandidates).toContain('2022-04-27');
    expect(startCandidates).toContain('2022-05-23');
    expect(startCandidates).toHaveLength(2);
  });

  it('2024 peak 分歧保留：双方日期均在候选集', () => {
    const { peakCandidates } = getConflictBoundaryCandidates(c2024);
    expect(peakCandidates).toContain('2024-07-29');
    expect(peakCandidates).toContain('2024-08-05');
  });

  it('2024 end 分歧保留：双方日期均在候选集', () => {
    const { endCandidates } = getConflictBoundaryCandidates(c2024);
    expect(endCandidates).toContain('2024-07-31');
    expect(endCandidates).toContain('2024-08-23');
  });

  it('不自动选择候选：campaign 正式字段仍为 DB Candidate（A），未被 B 覆盖', () => {
    // C-2024-ROBOTAXI 正式字段 = Candidate A（start 07-08 / peak 07-29 / end 07-31）
    expect(c2024.start).toBe('2024-07-08');
    expect(c2024.peak).toBe('2024-07-29');
    expect(c2024.end).toBe('2024-07-31');
    // C-2022-POLICY 正式起点 = Candidate A（04-27），未采用 B（05-23）
    expect(c2022.start).toBe('2022-04-27');
  });

  it('conflict Campaign 保持 status=conflict（视觉分歧语义的触发条件）', () => {
    expect(c2022.status).toBe('conflict');
    expect(c2024.status).toBe('conflict');
    // helper 仅对 conflict 状态生效（防御性验证）
    expect(getConflictBoundaryCandidates({ status: 'conflict', conflicts: undefined })).toEqual({
      startCandidates: null,
      peakCandidates: null,
      endCandidates: null,
    });
  });

  it('verified / provisional / preview Campaign 不触发 conflict 视觉（状态与候选集）', () => {
    // C-2024-V2X = provisional；RC 候选 = preview
    expect(normal.status).toBe('provisional');
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

  it('轻微峰值分歧：候选 A → B 构成 Peak Window（C-2024-ROBOTAXI：07-29 ~ 08-05）', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const w = peakWindowOf(c);
    expect(w).toEqual({ start: '2024-07-29', end: '2024-08-05', disputed: true });
  });

  it('无 peak（null）→ 无窗口；openEnded 候选同样安全', () => {
    expect(peakWindowOf({ peak: null, status: 'preview', conflicts: undefined })).toBeNull();
  });
});

describe('V1.7：冲突分级阈值（同一窗口 ≤ 10 天 = minor）', () => {
  it('2024 peak 分歧（07-29 vs 08-05，7 天）→ minor：显示窗口，不画大型 Conflict', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const peak = c.conflicts!.find((x) => x.field === 'peak_date')!;
    expect(conflictSeverity(peak)).toBe('minor');
  });

  it('2022 start 分歧（04-27 vs 05-23，26 天）→ major：大型 Conflict 视觉', () => {
    const c = previewTimelineSource().yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
    const start = c.conflicts!.find((x) => x.field === 'start_date')!;
    expect(conflictSeverity(start)).toBe('major');
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
  it('C-2022-POLICY：加速 / 转折有归因标签，启动 / 结束为空（不编造）', () => {
    const c = previewTimelineSource().yearData(2022).campaigns.find((x) => x.campaign_id === 'C-2022-POLICY')!;
    const d = campaignDrivers(c);
    // start 04-27，peak 06-10，end 08-31；events：05-23 国常会 / 05-31 财政部 / 06-10 比亚迪 / 06-22 国常会再促
    expect(d.start).toEqual([]);
    expect(d.accelerate.length).toBe(2);
    expect(d.accelerate.some((t) => t.includes('国常会'))).toBe(true);
    expect(d.accelerate.some((t) => t.includes('财政部'))).toBe(true);
    expect(d.turn.length).toBe(1);
    expect(d.turn[0]).toContain('比亚迪');
    expect(d.end).toEqual([]);
  });

  it('C-2024-ROBOTAXI：启动期事件归入启动组（first-match，不重复归组）', () => {
    const c = previewTimelineSource().yearData(2024).campaigns.find((x) => x.campaign_id === 'C-2024-ROBOTAXI')!;
    const d = campaignDrivers(c);
    expect(d.start.length).toBe(1);
    expect(d.start[0]).toContain('萝卜快跑');
    expect(d.end).toEqual([]); // 07-10 已归启动组，不重复进结束组
  });

  it('无事件的 Campaign：四问全空 → UI 显示"暂无可靠归因"（verified fixture）', () => {
    const cmp = verifiedTimelineSource(fixtureCampaigns).yearData(2023).campaigns[0];
    expect(cmp.events).toEqual([]);
    const d = campaignDrivers(cmp);
    expect(d).toEqual({ start: [], accelerate: [], turn: [], end: [] });
  });

  it('openEnded 候选：无结束归因（end 为年末近似，不归组）', () => {
    const rc = previewTimelineSource().yearData(2023).campaigns.find((x) => x.campaign_id === 'RC-2023-HUAWEI')!;
    const d = campaignDrivers(rc);
    expect(d.end).toEqual([]);
    expect(d.start.length).toBeGreaterThan(0); // 问界 M7 上市归启动
  });
});

describe('V1.7：历史同周期查看（列表，非统计模型）', () => {
  it('窗口口径：9 月 → 08-15 ~ 10-15；1 月跨年 → 前年 12-15 ~ 当年 02-15', () => {
    expect(samePeriodWindow(2026, 9)).toEqual({ start: '2026-08-15', end: '2026-10-15' });
    expect(samePeriodWindow(2026, 1)).toEqual({ start: '2025-12-15', end: '2026-02-15' });
    expect(samePeriodWindow(2026, 12)).toEqual({ start: '2026-11-15', end: '2027-01-15' });
  });

  it('9 月同期：2018 空、2019-2022 与 2025 有正式 Campaign、2023/2024 仅 Research Candidate', () => {
    const rows = samePeriodCampaigns(previewTimelineSource(), 9);
    expect(rows.map((r) => r.year)).toEqual([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
    expect(rows[0].campaigns).toEqual([]); // 2018 反例年
    expect(rows[1].campaigns.map((c) => c.campaign_id)).toEqual(['C-2019-AD']);
    expect(rows[4].campaigns.map((c) => c.campaign_id)).toEqual(['C-2022-POLICY']);
    expect(rows[5].campaigns.map((c) => c.campaign_id)).toEqual(['RC-2023-HUAWEI']);
    // 2024：仅 RC-2024-SECONDARY（Robotaxi end 07-31 < 08-15 不相交）
    expect(rows[6].campaigns.map((c) => c.campaign_id)).toEqual(['RC-2024-SECONDARY']);
    expect(rows[7].campaigns.map((c) => c.campaign_id)).toEqual(['C-2025-ROBOTAXI']);
  });

  it('2 月同期：历史各年均无 Campaign（淡季窗口空态合法）', () => {
    const rows = samePeriodCampaigns(previewTimelineSource(), 2);
    for (const r of rows) {
      expect(r.campaigns).toEqual([]);
    }
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
