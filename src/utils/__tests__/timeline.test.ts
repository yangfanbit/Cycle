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

describe('V1.5 核验数据完整性', () => {
  it('Evidence 必须引用存在的 Source，且关联对象（rule / campaign / theme）均存在', async () => {
    const { evidences, sourceById, ruleById, campaignById, themeById } = await import('../../data');
    expect(evidences.length).toBeGreaterThan(0);
    for (const ev of evidences) {
      expect(sourceById.has(ev.source_id)).toBe(true);
      if (ev.rule_id) expect(ruleById.has(ev.rule_id)).toBe(true);
      if (ev.campaign_id) expect(campaignById.has(ev.campaign_id)).toBe(true);
      if (ev.theme_id) expect(themeById.has(ev.theme_id)).toBe(true);
      // 材料来源的日期未提供时必须为 null，不得编造
      if (ev.date != null) expect(ev.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('Cross-Year Campaign 日期不能错乱：起止有序、cross_year 与年份一致、V1.5 日期标注齐全', async () => {
    const { campaigns } = await import('../../data');
    for (const c of campaigns) {
      expect(c.start_date <= c.end_date).toBe(true);
      const startYear = Number(c.start_date.slice(0, 4));
      const endYear = Number(c.end_date.slice(0, 4));
      expect(c.cross_year).toBe(endYear > startYear);
      expect(c.campaign_year).toBe(startYear);
      // V1.5：候选行情必须标注日期判定方式与置信度（禁止裸日期冒充已核验）
      expect(c.start_date_basis).toBeDefined();
      expect(c.end_date_basis).toBeDefined();
      expect(c.date_confidence).toBeDefined();
      // 峰值日期若存在，必须落在窗口内
      if (c.peak_date != null) {
        expect(c.start_date <= c.peak_date).toBe(true);
        expect(c.peak_date <= c.end_date).toBe(true);
      }
    }
  });

  it('无法核验的数据可以为 unknown/null（不编造填空）', async () => {
    const { evidences, campaigns } = await import('../../data');
    // 证据：来源未提供日期 → null 是合法状态且实际存在
    expect(evidences.some((e) => e.date === null)).toBe(true);
    // 行情：未核验 → result=unknown、peak_date=null、低置信
    expect(campaigns.some((c) => c.result === 'unknown' && c.peak_date === null)).toBe(true);
    for (const c of campaigns) {
      if (c.result === 'unknown') expect(c.date_confidence).toBe('low');
    }
  });

  it('L2 不自动等于 statistically_supported（证据等级与验证状态独立）', async () => {
    const { validationRecords } = await import('../../data');
    expect(validationRecords.length).toBeGreaterThan(0);
    for (const r of validationRecords) {
      // 不变式：证据等级未达 L3/L4 时，验证状态不得为统计支持 / 交叉验证
      if (r.verification_status === 'statistically_supported' || r.verification_status === 'cross_validated') {
        expect(['L3', 'L4']).toContain(r.evidence_status);
      }
    }
    // 当前骨架：存在 L1 记录（已找到证据但未核验），它们不得被标记为统计支持
    const l1 = validationRecords.filter((r) => r.evidence_status === 'L1');
    expect(l1.length).toBeGreaterThan(0);
    for (const r of l1) {
      expect(r.verification_status).not.toBe('statistically_supported');
      expect(r.verification_status).not.toBe('cross_validated');
    }
  });

  it('失败年份不会被过滤：查询不做 result 过滤，标签体系覆盖 failed', async () => {
    const { campaigns, campaignsOfRule, rules } = await import('../../data');
    for (const rule of rules) {
      const viaHelper = campaignsOfRule(rule.rule_id).length;
      const direct = campaigns.filter((c) => c.rule_id === rule.rule_id).length;
      expect(viaHelper).toBe(direct);
    }
    // 结构必须支持 failed / weak 年份（不得只保存成功案例）
    const { RESULT_LABEL } = await import('../../components/labels');
    for (const r of ['positive', 'neutral', 'weak', 'failed', 'unknown'] as const) {
      expect(RESULT_LABEL[r]).toBeTruthy();
    }
  });

  it('Base Pattern 与 Annual Theme 可以同时存在且不混淆', async () => {
    const { campaignThemes, themeById } = await import('../../data');
    // cmp_auto_2023 同时关联底层行业（汽车，related）与年度题材（减速器，main）
    const links = campaignThemes.filter((ct) => ct.campaign_id === 'cmp_auto_2023');
    const roles = new Map(links.map((l) => [l.theme_id, l.role]));
    expect(roles.get('th_auto')).toBe('related');
    expect(roles.get('th_auto_reducer')).toBe('main');
    // Annual Theme 挂在 Base Pattern 之下（父子层级）
    expect(themeById.get('th_auto_reducer')!.parent_theme_id).toBe('th_auto');
    expect(themeById.get('th_auto')!.theme_type).toBe('sector');
    expect(themeById.get('th_auto_reducer')!.theme_type).toBe('concept');
  });

  it('同一 Base Pattern 可以关联多个 Theme（不同年份不同年度题材）', async () => {
    const { childrenOf, campaignThemes } = await import('../../data');
    // 汽车下挂多个年度题材
    expect(childrenOf('th_auto').length).toBeGreaterThanOrEqual(3);
    // 两条不同年份的汽车 Campaign 使用不同的 main 题材
    const main2023 = campaignThemes.find((ct) => ct.campaign_id === 'cmp_auto_2023' && ct.role === 'main')!;
    const main2024 = campaignThemes.find((ct) => ct.campaign_id === 'cmp_auto_2024' && ct.role === 'main')!;
    expect(main2023.theme_id).not.toBe(main2024.theme_id);
  });

  it('3 条 Pilot 骨架结构完整：计划 / 证据 / 核验记录一一对应', async () => {
    const { pilots, validationRecords, evidencesOfRule, ruleById } = await import('../../data');
    expect(pilots.length).toBe(3);
    for (const p of pilots) {
      expect(ruleById.has(p.rule_id)).toBe(true);
      expect(p.status).toBe('planned');
      const record = validationRecords.find((r) => r.rule_id === p.rule_id);
      expect(record).toBeTruthy();
      expect(evidencesOfRule(p.rule_id).length).toBeGreaterThan(0);
      // 人工核验未开始：reviewer 待分配、未测试
      expect(record!.reviewer).toBe('pending');
      expect(record!.verification_status).toBe('not_tested');
    }
  });

  it('verified 层为空（人工核验未开始，不为填充而编造事实）', async () => {
    const { verifiedCampaigns } = await import('../../data');
    expect(verifiedCampaigns).toEqual([]);
  });

  it('仅有年份提及、无细节的材料不产生 Campaign（广电 2021—2023 待核验）', async () => {
    const { campaigns } = await import('../../data');
    // 材料"提及"2021/2022/2023 年广电行情，但无任何日期/强度/结果细节，
    // 因此不得创建对应 Campaign 记录（防编造的最小事实原则）
    const mediaCampaigns = campaigns.filter((c) => c.rule_id === 'rule_media_year_end');
    expect(mediaCampaigns.length).toBe(1); // 仅跨年结构示例
    expect(mediaCampaigns[0].campaign_id).toBe('cmp_media_2026_2027');
  });
});
