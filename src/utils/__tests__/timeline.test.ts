import { describe, expect, it } from 'vitest';
import type { TimeWindow } from '../../models';
import {
  addDaysISO,
  compareISO,
  compareMD,
  computeWindowStatus,
  dayOfYearISO,
  diffDays,
  isCrossYearMD,
  mdToISO,
  occurrenceForSeason,
  segmentForYear,
  windowSegmentsForYear,
  yearFraction,
} from '..';
import { anchorResolver } from '../../data';

/** 跨年窗口：11-01 → 01-15，预热 20 天（对应年底广电规律） */
const crossYearWindow: TimeWindow = {
  window_id: 'win_test_cross',
  rule_id: 'rule_test',
  window_type: 'empirical',
  start_md: '11-01',
  end_md: '01-15',
  preheat_days: 20,
};

/** 年内窗口：06-01 → 08-31，预热 15 天（对应夏季汽车规律） */
const summerWindow: TimeWindow = {
  window_id: 'win_test_summer',
  rule_id: 'rule_test',
  window_type: 'calendar',
  start_md: '06-01',
  end_md: '08-31',
  preheat_days: 15,
};

describe('dateUtils 基础', () => {
  it('md 与 ISO 互转、MD 比较', () => {
    expect(mdToISO('11-01', 2026)).toBe('2026-11-01');
    expect(compareMD('01-15', '11-01')).toBe(-1);
    expect(isCrossYearMD('11-01', '01-15')).toBe(true);
    expect(isCrossYearMD('06-01', '08-31')).toBe(false);
  });

  it('日期加减与天数差', () => {
    expect(addDaysISO('2026-12-31', 1)).toBe('2027-01-01');
    expect(addDaysISO('2026-11-01', -20)).toBe('2026-10-12');
    expect(diffDays('2026-11-01', '2027-01-15')).toBe(75);
    expect(compareISO('2026-11-01', '2027-01-15')).toBe(-1);
  });

  it('年内第几天与位置比例（闰年 2 月后 +1）', () => {
    expect(dayOfYearISO('2026-01-01')).toBe(1);
    expect(dayOfYearISO('2026-12-31')).toBe(365);
    expect(dayOfYearISO('2024-12-31')).toBe(366);
    expect(yearFraction('2026-01-01')).toBe(0);
  });
});

describe('普通时间窗口', () => {
  it('年内窗口实例化', () => {
    const occ = occurrenceForSeason(summerWindow, 2026)!;
    expect(occ.start).toBe('2026-06-01');
    expect(occ.end).toBe('2026-08-31');
    expect(occ.crossYear).toBe(false);
    expect(occ.preheatStart).toBe('2026-05-17');
  });

  it('窗口内为 ACTIVE，窗口前为 NOT_ACTIVE，窗口后为 ENDED', () => {
    expect(computeWindowStatus(summerWindow, '2026-07-15')!.phase).toBe('ACTIVE');
    expect(computeWindowStatus(summerWindow, '2026-03-01')!.phase).toBe('NOT_ACTIVE');
    expect(computeWindowStatus(summerWindow, '2026-10-01')!.phase).toBe('ENDED');
  });
});

describe('跨年窗口', () => {
  it('2026-11-01 → 2027-01-15 实例化为一条完整窗口，不拆成两条', () => {
    const occ = occurrenceForSeason(crossYearWindow, 2026)!;
    expect(occ.start).toBe('2026-11-01');
    expect(occ.end).toBe('2027-01-15');
    expect(occ.crossYear).toBe(true);
    expect(diffDays(occ.start, occ.end)).toBe(75);
  });

  it('跨年窗口在 2026 年与 2027 年各渲染对应分段，且标注延续关系', () => {
    const segs2026 = windowSegmentsForYear(crossYearWindow, 2026);
    const segs2027 = windowSegmentsForYear(crossYearWindow, 2027);

    // 2026：1 月有 2025 季的尾段（左端开口），11 月有 2026 季新段（右端开口）
    const tail2026 = segs2026.find((s) => s.continuesFromPrevYear);
    const head2026 = segs2026.find((s) => s.continuesIntoNextYear);
    expect(tail2026).toBeDefined();
    expect(tail2026!.start).toBe('2026-01-01');
    expect(tail2026!.end).toBe('2026-01-15');
    expect(head2026).toBeDefined();
    expect(head2026!.start).toBe('2026-11-01');
    expect(head2026!.end).toBe('2026-12-31');

    // 2027：上一季尾段（年初 → 01-15），左端开口来自上一年；本季新段从 11-01 开始
    const tail = segs2027.find((s) => s.continuesFromPrevYear);
    expect(tail).toBeDefined();
    expect(tail!.start).toBe('2027-01-01');
    expect(tail!.end).toBe('2027-01-15');
  });

  it('跨年 Campaign 分段：完整日期范围不被裁剪丢失', () => {
    const start = '2026-11-01';
    const end = '2027-01-15';
    const segA = segmentForYear(start, end, 2026)!;
    const segB = segmentForYear(start, end, 2027)!;
    expect(segA.continuesIntoNextYear).toBe(true);
    expect(segB.continuesFromPrevYear).toBe(true);
    // 两段拼起来覆盖完整生命周期
    expect(segA.start).toBe(start);
    expect(segB.end).toBe(end);
    // 不相干的年份没有分段
    expect(segmentForYear(start, end, 2028)).toBeNull();
  });

  it('1 月仍处于去年 11 月开启的窗口中 → ACTIVE', () => {
    const status = computeWindowStatus(crossYearWindow, '2027-01-05')!;
    expect(status.phase).toBe('ACTIVE');
    expect(status.occurrence.seasonYear).toBe(2026);
    expect(status.occurrence.start).toBe('2026-11-01');
    expect(status.occurrence.end).toBe('2027-01-15');
  });
});

describe('Pre-heat 提前观察', () => {
  it('预热区开始日 = 窗口开始日 - preheat_days', () => {
    const occ = occurrenceForSeason(crossYearWindow, 2026)!;
    expect(occ.preheatStart).toBe('2026-10-12');
  });

  it('预热区内为 PRE_HEAT，进入窗口后转 ACTIVE，结束后转 ENDED', () => {
    expect(computeWindowStatus(crossYearWindow, '2026-10-20')!.phase).toBe('PRE_HEAT');
    expect(computeWindowStatus(crossYearWindow, '2026-11-01')!.phase).toBe('ACTIVE');
    expect(computeWindowStatus(crossYearWindow, '2027-02-01')!.phase).toBe('ENDED');
  });

  it('PRE_HEAT 的 daysToStart 为正且等于距窗口天数', () => {
    const status = computeWindowStatus(crossYearWindow, '2026-10-20')!;
    expect(status.daysToStart).toBe(12); // 10-20 → 11-01
  });
});

describe('相对事件窗口（春节锚点）', () => {
  const springWindow: TimeWindow = {
    window_id: 'win_test_spring',
    rule_id: 'rule_test',
    window_type: 'relative_event',
    anchor_event: 'evt_spring_festival',
    start_offset_days: -20,
    end_offset_days: 30,
    preheat_days: 15,
  };

  it('按逐年春节日期解析（2026 春节 = 02-17）', () => {
    const occ = occurrenceForSeason(springWindow, 2026, anchorResolver)!;
    expect(occ.start).toBe('2026-01-28');
    expect(occ.end).toBe('2026-03-19');
  });

  it('春节前→春节后天然跨年时 crossYear 自动成立', () => {
    // 2025 春节 01-29：节前 20 天 = 01-09，同年；构造一个偏移更大的窗口验证跨年
    const wide: TimeWindow = { ...springWindow, start_offset_days: -40 };
    const occ = occurrenceForSeason(wide, 2025, anchorResolver)!;
    expect(occ.start).toBe('2024-12-20');
    expect(occ.crossYear).toBe(true);
  });
});

describe('TODAY 定位与年份切换', () => {
  it('yearFraction 在不同年份独立计算，切换年份不产生错位', () => {
    // 同一个窗口在 2026 / 2027 视图中分段位置各自独立且都在 [0,1]
    for (const year of [2025, 2026, 2027]) {
      for (const seg of windowSegmentsForYear(crossYearWindow, year)) {
        expect(seg.startFraction).toBeGreaterThanOrEqual(0);
        expect(seg.endFraction).toBeLessThanOrEqual(1);
        expect(seg.endFraction).toBeGreaterThan(seg.startFraction);
      }
    }
  });
});

describe('数据完整性', () => {
  it('所有规律都有来源且状态为 candidate / under_review（V1 不允许 verified）', async () => {
    const { rules, sourceById } = await import('../../data');
    for (const rule of rules) {
      expect(sourceById.has(rule.source_id)).toBe(true);
      expect(['candidate', 'under_review']).toContain(rule.status);
      expect(rule.statistics?.status).toBe('not_verified');
    }
  });

  it('所有历史行情都关联到存在的规律与来源', async () => {
    const { campaigns, ruleById, sourceById } = await import('../../data');
    for (const c of campaigns) {
      expect(ruleById.has(c.rule_id)).toBe(true);
      expect(sourceById.has(c.source_id)).toBe(true);
      expect(c.start_date <= c.end_date).toBe(true);
    }
  });

  it('跨年示例行情 2026-11-01 → 2027-01-15 是一条完整记录', async () => {
    const { campaigns } = await import('../../data');
    const c = campaigns.find((x) => x.campaign_id === 'cmp_media_2026_2027')!;
    expect(c.cross_year).toBe(true);
    expect(c.season_id).toBe('2026-2027');
    expect(c.start_date).toBe('2026-11-01');
    expect(c.end_date).toBe('2027-01-15');
  });
});

describe('数据治理规范', () => {
  it('Rule 不会因数据"看起来合理"而变成 verified（种子数据零 verified）', async () => {
    const { rules } = await import('../../data');
    expect(rules.length).toBeGreaterThan(0);
    for (const rule of rules) {
      expect(rule.status).not.toBe('verified');
      // verified 只能由 quant_verification 来源支撑；当前不存在该类型来源
      expect(rule.statistics?.status).toBe('not_verified');
    }
  });

  it('缺失 HistoricalCampaign 是合法状态：查询返回空数组而非报错', async () => {
    const { campaignsOfRule, rules } = await import('../../data');
    // 大部分候选规律暂无历史案例
    const noCaseRules = rules.filter((r) => campaignsOfRule(r.rule_id).length === 0);
    expect(noCaseRules.length).toBeGreaterThan(0);
    expect(campaignsOfRule('rule_not_exist')).toEqual([]);
  });

  it('CampaignTheme 关联完整：两端引用必须存在', async () => {
    const { campaignThemes, campaignById, themeById } = await import('../../data');
    for (const ct of campaignThemes) {
      expect(campaignById.has(ct.campaign_id)).toBe(true);
      expect(themeById.has(ct.theme_id)).toBe(true);
    }
  });

  it('缺失关联数据时查询辅助返回空值而非异常', async () => {
    const { themesOfCampaign, campaignById, windowsOfRule, ruleById } = await import('../../data');
    expect(themesOfCampaign('cmp_not_exist')).toEqual([]);
    expect(campaignById.get('cmp_not_exist')).toBeUndefined();
    expect(windowsOfRule('rule_not_exist')).toEqual([]);
    expect(ruleById.get('rule_not_exist')).toBeUndefined();
  });

  it('跨年种子行情在两个视图年中渲染为同一 Campaign 的延续分段', async () => {
    const { campaigns } = await import('../../data');
    const c = campaigns.find((x) => x.campaign_id === 'cmp_media_2026_2027')!;
    const segA = segmentForYear(c.start_date, c.end_date, 2026)!;
    const segB = segmentForYear(c.start_date, c.end_date, 2027)!;
    // 同一条 Campaign：两段都标注延续，且持续时间为正
    expect(segA.continuesIntoNextYear).toBe(true);
    expect(segB.continuesFromPrevYear).toBe(true);
    expect(diffDays(c.start_date, c.end_date)).toBeGreaterThan(0);
    // 完整生命周期不被年份裁剪丢失
    expect(segA.start).toBe('2026-11-01');
    expect(segB.end).toBe('2027-01-15');
  });
});
