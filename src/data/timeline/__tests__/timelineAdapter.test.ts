import { describe, expect, it } from 'vitest';
import {
  derivePhases,
  exportCampaignToTimeline,
  previewTimelineSource,
  timelineSourceFromExportV1,
  verifiedTimelineSource,
} from '../timelineAdapter';
import { timelinePreviewExport } from '../timelinePreview';
import { allCampaigns, campaignById, verifiedCampaigns } from '../../index';
import { yearFraction, marketTodayISO } from '../../../utils';
import { fixtureCampaigns, fixtureCrossYearMedia } from '../../../../tests/fixtures/campaignFixtures';

describe('Timeline Adapter：preview 不进入生产数据', () => {
  it('preview 数据不进入 allCampaigns / verifiedCampaigns / campaignById', () => {
    expect(allCampaigns).toEqual([]);
    expect(verifiedCampaigns).toEqual([]);
    const previewIds = new Set(timelinePreviewExport.campaigns.map((c) => c.campaign_id));
    for (const id of previewIds) {
      expect(campaignById.has(id)).toBe(false);
    }
  });
});

describe('Timeline Adapter：verified 生产数据源', () => {
  it('verified 源正常映射（fixture 注入）：字段、年份、题材/龙头查询', () => {
    const source = verifiedTimelineSource(fixtureCampaigns);
    expect(source.kind).toBe('verified');
    const y2023 = source.yearData(2023);
    const cmp = y2023.campaigns.find((c) => c.campaign_id === 'cmp_auto_2023');
    expect(cmp).toBeDefined();
    expect(cmp!.status).toBe('verified');
    expect(cmp!.start).toBe('2023-06-01');
    expect(cmp!.end).toBe('2023-08-31');
    expect(cmp!.season_id).toBe('2023');
    // fixture 行情无题材/龙头关联（生产关系表为空）：视图为空而非报错
    expect(cmp!.themes).toEqual([]);
    expect(cmp!.securities).toEqual([]);
    expect(y2023.campaigns.some((c) => c.campaign_id === 'cmp_auto_2024')).toBe(false);
  });

  it('生产当前为空：years() 为空、yearData 无行情（verified 空态合法）', () => {
    const source = verifiedTimelineSource(); // 不注入 = 生产数据
    expect(source.years()).toEqual([]);
    expect(source.yearData(2026).campaigns).toEqual([]);
    // 事件层仍提供日历事件（含 approximate 标记）
    expect(source.yearData(2026).events.length).toBeGreaterThan(0);
  });
});

describe('Timeline Adapter：跨年与年份切换', () => {
  it('跨年行情在两年各可见：2026-11-01 → 2027-01-15 出现在 2026 与 2027，且是一条记录', () => {
    const source = verifiedTimelineSource([fixtureCrossYearMedia]);
    expect(source.years()).toEqual([2026, 2027]);
    const in2026 = source.yearData(2026).campaigns.find((c) => c.campaign_id === 'cmp_media_2026_2027');
    const in2027 = source.yearData(2027).campaigns.find((c) => c.campaign_id === 'cmp_media_2026_2027');
    expect(in2026).toBeDefined();
    expect(in2027).toBeDefined();
    expect(in2026!.cross_year).toBe(true);
    expect(source.yearData(2025).campaigns).toEqual([]);
  });

  it('preview 年份切换：2022 / 2023 / 2024 可切换，2023 有两条行情', () => {
    const source = previewTimelineSource();
    expect(source.years()).toEqual([2022, 2023, 2024]);
    expect(source.yearData(2022).campaigns).toHaveLength(1);
    expect(source.yearData(2023).campaigns).toHaveLength(2);
    expect(source.yearData(2024).campaigns).toHaveLength(1);
    expect(source.yearData(2021).campaigns).toEqual([]);
  });
});

describe('Timeline Adapter：preview / conflict 徽章', () => {
  it('preview 徽章：预览行情 status=preview，来源标注非正式历史事实', () => {
    const source = previewTimelineSource();
    for (const c of source.yearData(2022).campaigns) {
      expect(c.status).toBe('preview');
      expect(c.sourceNote).toContain('非正式历史事实');
    }
  });

  it('conflict 徽章：华为汽车链为研究分歧，携带分歧说明', () => {
    const source = previewTimelineSource();
    const huawei = source
      .yearData(2023)
      .campaigns.find((c) => c.campaign_id === 'cmp_prev_2023_huawei_auto');
    expect(huawei).toBeDefined();
    expect(huawei!.status).toBe('conflict');
    expect(huawei!.conflicts!.length).toBeGreaterThan(0);
  });

  it('provisional：research_status 映射为 TimelineDataStatus', () => {
    const provisional = exportCampaignToTimeline({
      campaign_id: 'x',
      rule_id: 'rule_auto_summer',
      year: 2025,
      season_id: '2025',
      title: 't',
      themes: [],
      start_date: '2025-06-01',
      end_date: '2025-08-01',
      research_status: 'provisional',
    });
    expect(provisional.status).toBe('provisional');
  });
});

describe('Timeline Adapter：生命周期与日期位置', () => {
  it('生命周期分段按序覆盖 start→end，peak 在区间内', () => {
    for (const c of previewTimelineSource().yearData(2023).campaigns) {
      expect(c.phases[0].start).toBe(c.start);
      expect(c.phases[c.phases.length - 1].end).toBe(c.end);
      for (let i = 1; i < c.phases.length; i += 1) {
        expect(c.phases[i].start).toBe(c.phases[i - 1].end);
      }
      if (c.peak) {
        expect(c.peak >= c.start && c.peak <= c.end).toBe(true);
      }
      if (c.early_signal) {
        expect(c.early_signal.end < c.start).toBe(true); // 早期信号在正式起点之前
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
    expect(
      derivePhases({ start: '2024-01-01', end: '2024-03-01', peak: null }),
    ).toEqual([{ phase: 'main_rise', start: '2024-01-01', end: '2024-03-01' }]);
  });

  it('日期位置按真实日期比例（非 12 等分）：7 月 2 日约在年中', () => {
    const f = yearFraction('2023-07-02'); // 2023 年第 183 天 / 365
    expect(f).toBeGreaterThan(0.49);
    expect(f).toBeLessThan(0.51);
    // 5 月底（2022 行情起点）位于第 151/365 天 ≈ 41%
    expect(yearFraction('2022-05-31')).toBeGreaterThan(0.4);
    expect(yearFraction('2022-05-31')).toBeLessThan(0.42);
  });

  it('TODAY 基准：北京已跨日、UTC 未跨日时返回北京日期（Asia/Shanghai）', () => {
    expect(marketTodayISO(new Date('2026-09-12T18:30:00Z'))).toBe('2026-09-13');
  });
});

describe('Timeline Adapter：timeline_export_v1 导入接口', () => {
  it('本地导出对象可直接生成 preview 数据源（不做运行时网络访问）', () => {
    const source = timelineSourceFromExportV1({
      export_version: '1',
      generated_at: '2026-09-13',
      source_project: 'Cycle-Research',
      campaigns: [
        {
          campaign_id: 'cmp_import_test',
          rule_id: 'rule_auto_summer',
          year: 2025,
          season_id: '2025',
          title: '导入测试行情',
          themes: [{ name: '导入题材', role: 'main' }],
          start_date: '2025-06-01',
          peak_date: '2025-07-15',
          end_date: '2025-08-31',
          early_signal: { start_date: '2025-05-01', end_date: '2025-05-31', label: '导入早信号' },
          securities: [{ name: '示例股份', role: 'leader' }],
          research_status: 'preview',
        },
      ],
    });
    expect(source.kind).toBe('preview');
    expect(source.years()).toEqual([2025]);
    const c = source.yearData(2025).campaigns[0];
    expect(c.title).toBe('导入测试行情');
    expect(c.early_signal!.label).toBe('导入早信号');
    expect(c.phases.map((p) => p.phase)).toEqual(['main_rise', 'retracement', 'declining']);
    expect(c.securities[0].name).toBe('示例股份');
  });
});
