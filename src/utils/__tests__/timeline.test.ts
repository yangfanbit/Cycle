import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
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
  marketTodayISO,
  mdToISO,
  occurrenceForSeason,
  segmentForYear,
  windowSegmentsForYear,
  yearFraction,
} from '..';
import { anchorResolver } from '../../data';
import {
  fixtureCampaigns,
  fixtureCampaignThemes,
  fixtureCrossYearMedia,
} from '../../../tests/fixtures/campaignFixtures';

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

describe('A股市场日期基准（Asia/Shanghai）', () => {
  it('marketTodayISO 基于 Asia/Shanghai 而非 UTC：北京已跨日、UTC 未跨日时返回北京日期', () => {
    // UTC 2026-06-15T18:30Z = 北京 2026-06-16 02:30 → 市场日期应为 06-16（若误用 UTC 会返回 06-15）
    expect(marketTodayISO(new Date('2026-06-15T18:30:00Z'))).toBe('2026-06-16');
  });

  it('UTC 日期与北京日期相同时返回同一天', () => {
    // UTC 2026-06-15T02:30Z = 北京 2026-06-15 10:30
    expect(marketTodayISO(new Date('2026-06-15T02:30:00Z'))).toBe('2026-06-15');
  });

  it('接近中国午夜的时刻：23:59:59 仍属当日，00:00:00 属次日（不依赖运行机器时区）', () => {
    // 北京 23:59:59 = UTC 15:59:59 → 仍为当日
    expect(marketTodayISO(new Date('2026-06-15T15:59:59Z'))).toBe('2026-06-15');
    // 北京次日 00:00:00 = UTC 16:00:00 → 次日
    expect(marketTodayISO(new Date('2026-06-15T16:00:00Z'))).toBe('2026-06-16');
  });

  it('输出为合法 ISO 日期格式', () => {
    expect(marketTodayISO(new Date('2026-01-01T00:00:00Z'))).toMatch(/^\d{4}-\d{2}-\d{2}$/);
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

  it('所有历史行情都关联到存在的规律与来源（当前生产层仅含 verified）', async () => {
    const { allCampaigns, ruleById, sourceById } = await import('../../data');
    for (const c of allCampaigns) {
      expect(ruleById.has(c.rule_id)).toBe(true);
      expect(sourceById.has(c.source_id)).toBe(true);
      expect(c.start_date <= c.end_date).toBe(true);
    }
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
    // 当前全部规律暂无已核验历史案例（verified 层为空）
    for (const rule of rules) {
      expect(campaignsOfRule(rule.rule_id)).toEqual([]);
    }
    expect(campaignsOfRule('rule_not_exist')).toEqual([]);
  });

  it('缺失关联数据时查询辅助返回空值而非异常', async () => {
    const { themesOfCampaign, campaignById, windowsOfRule, ruleById } = await import('../../data');
    expect(themesOfCampaign('cmp_not_exist')).toEqual([]);
    expect(campaignById.get('cmp_not_exist')).toBeUndefined();
    expect(windowsOfRule('rule_not_exist')).toEqual([]);
    expect(ruleById.get('rule_not_exist')).toBeUndefined();
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
});

describe('V1.5 Preflight：生产层数据语义', () => {
  it('cmp_media_2026_2027（跨年结构示例）不属于生产 data/candidate campaigns', async () => {
    const { campaigns, campaignById } = await import('../../data');
    expect(campaigns.find((c) => c.campaign_id === 'cmp_media_2026_2027')).toBeUndefined();
    expect(campaignById.has('cmp_media_2026_2027')).toBe(false);
  });

  it('候选行情 cmp_auto_2023 / cmp_auto_2024 不再出现在生产层（方案 A：仅存于 Evidence）', async () => {
    const { allCampaigns } = await import('../../data');
    const ids = allCampaigns.map((c) => c.campaign_id);
    expect(ids).not.toContain('cmp_auto_2023');
    expect(ids).not.toContain('cmp_auto_2024');
  });

  it('生产层全部行情 = verified 层（candidate 恒空，不得被 Timeline 当作历史行情）', async () => {
    const { allCampaigns, verifiedCampaigns } = await import('../../data');
    expect(allCampaigns).toEqual(verifiedCampaigns);
  });

  it('仅有年份提及、无细节的材料不产生 Campaign（广电 2021—2023 待核验）', async () => {
    const { allCampaigns } = await import('../../data');
    const mediaCampaigns = allCampaigns.filter((c) => c.rule_id === 'rule_media_year_end');
    // 材料仅"提及"2021/2022/2023 年广电行情，无任何日期/强度/结果细节，不得创建 Campaign
    expect(mediaCampaigns).toEqual([]);
  });

  it('Source URL 已登记且格式合法（来源可追溯）', async () => {
    const { sourceById } = await import('../../data');
    const src = sourceById.get('src_exp_001')!;
    expect(src).toBeTruthy();
    expect(src.url).toBeTruthy();
    expect(src.url).toMatch(/^https?:\/\//);
  });

  it('ValidationRecord：未审核时 reviewer = pending 且 reviewed_at = null（无核验人就不得有核验日期）', async () => {
    const { validationRecords } = await import('../../data');
    for (const r of validationRecords) {
      expect(r.created_at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      if (r.reviewer === 'pending') {
        expect(r.reviewed_at).toBeNull();
        expect(r.verification_status).toBe('not_tested');
      } else {
        // 已有核验人的记录必须有核验完成日期
        expect(r.reviewed_at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      }
    }
  });

  it('Timeline 第三层在 verifiedCampaigns 为空时显示「暂无已核验历史行情」', async () => {
    const { Timeline } = await import('../../components/Timeline/Timeline');
    const html = renderToStaticMarkup(
      createElement(Timeline, { year: 2026, today: '2026-09-12', selection: null, onSelect: () => {} }),
    );
    expect(html).toContain('已核验历史行情');
    expect(html).toContain('暂无已核验历史行情（历史核验尚未开始）');
    // 结构示例不得再被渲染为历史行情
    expect(html).not.toContain('cmp_media_2026_2027');
    expect(html).not.toContain('2026-2027');
  });
});

describe('V1.5 Preflight：测试 fixture 语义（跨年结构示例迁至 tests/fixtures）', () => {
  it('跨年 fixture 仍存在且结构完整（2026-11-01 → 2027-01-15）', () => {
    expect(fixtureCrossYearMedia.campaign_id).toBe('cmp_media_2026_2027');
    expect(fixtureCrossYearMedia.cross_year).toBe(true);
    expect(fixtureCrossYearMedia.season_id).toBe('2026-2027');
    expect(fixtureCrossYearMedia.start_date).toBe('2026-11-01');
    expect(fixtureCrossYearMedia.end_date).toBe('2027-01-15');
  });

  it('跨年 fixture 在两个视图年中渲染为同一 Campaign 的延续分段', () => {
    const segA = segmentForYear(fixtureCrossYearMedia.start_date, fixtureCrossYearMedia.end_date, 2026)!;
    const segB = segmentForYear(fixtureCrossYearMedia.start_date, fixtureCrossYearMedia.end_date, 2027)!;
    expect(segA.continuesIntoNextYear).toBe(true);
    expect(segB.continuesFromPrevYear).toBe(true);
    expect(diffDays(fixtureCrossYearMedia.start_date, fixtureCrossYearMedia.end_date)).toBeGreaterThan(0);
    expect(segA.start).toBe('2026-11-01');
    expect(segB.end).toBe('2027-01-15');
  });

  it('fixture 行情日期约束：起止有序、cross_year 与年份一致、V1.5 日期标注齐全', () => {
    for (const c of fixtureCampaigns) {
      expect(c.start_date <= c.end_date).toBe(true);
      const startYear = Number(c.start_date.slice(0, 4));
      const endYear = Number(c.end_date.slice(0, 4));
      expect(c.cross_year).toBe(endYear > startYear);
      expect(c.campaign_year).toBe(startYear);
      expect(c.start_date_basis).toBeDefined();
      expect(c.end_date_basis).toBeDefined();
      expect(c.date_confidence).toBeDefined();
      if (c.peak_date != null) {
        expect(c.start_date <= c.peak_date).toBe(true);
        expect(c.peak_date <= c.end_date).toBe(true);
      }
    }
  });

  it('无法核验的数据可以为 unknown/null（fixture 保留推断日期的低置信语义）', () => {
    expect(fixtureCampaigns.some((c) => c.result === 'unknown' && c.peak_date === null)).toBe(true);
    for (const c of fixtureCampaigns) {
      if (c.result === 'unknown') expect(c.date_confidence).toBe('low');
    }
  });

  it('fixtureCampaignThemes 引用完整：campaign 端与 theme 端（生产 themes）均存在', async () => {
    const { themeById } = await import('../../data');
    for (const ct of fixtureCampaignThemes) {
      expect(fixtureCampaigns.some((c) => c.campaign_id === ct.campaign_id)).toBe(true);
      expect(themeById.has(ct.theme_id)).toBe(true);
    }
  });

  it('Base Pattern 与 Annual Theme 在 fixture 中同时存在且不混淆', async () => {
    const { themeById } = await import('../../data');
    // cmp_auto_2023 同时关联底层行业（汽车，related）与年度题材（减速器，main）
    const links = fixtureCampaignThemes.filter((ct) => ct.campaign_id === 'cmp_auto_2023');
    const roles = new Map(links.map((l) => [l.theme_id, l.role]));
    expect(roles.get('th_auto')).toBe('related');
    expect(roles.get('th_auto_reducer')).toBe('main');
    expect(themeById.get('th_auto_reducer')!.parent_theme_id).toBe('th_auto');
    expect(themeById.get('th_auto')!.theme_type).toBe('sector');
    expect(themeById.get('th_auto_reducer')!.theme_type).toBe('concept');
  });

  it('同一 Base Pattern 可以关联多个 Theme（不同年份不同年度题材）', async () => {
    const { childrenOf } = await import('../../data');
    // 汽车下挂多个年度题材
    expect(childrenOf('th_auto').length).toBeGreaterThanOrEqual(3);
    // 两条不同年份的汽车 Campaign 使用不同的 main 题材
    const main2023 = fixtureCampaignThemes.find((ct) => ct.campaign_id === 'cmp_auto_2023' && ct.role === 'main')!;
    const main2024 = fixtureCampaignThemes.find((ct) => ct.campaign_id === 'cmp_auto_2024' && ct.role === 'main')!;
    expect(main2023.theme_id).not.toBe(main2024.theme_id);
  });

  it('失败年份不会被过滤：结果标签体系覆盖 failed（结构支持，不得只存成功案例）', async () => {
    const { RESULT_LABEL } = await import('../../components/labels');
    for (const r of ['positive', 'neutral', 'weak', 'failed', 'unknown'] as const) {
      expect(RESULT_LABEL[r]).toBeTruthy();
    }
  });
});
