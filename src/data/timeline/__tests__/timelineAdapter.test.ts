import { describe, expect, it } from 'vitest';
import {
  derivePhases,
  fromTimelineExportV1,
  previewTimelineSource,
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
