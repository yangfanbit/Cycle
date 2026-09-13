import type { TimelineExportV1 } from './timelineTypes';

/**
 * Cycle-Research 预览数据（timeline_export_v1 兼容）。
 *
 * 边界（重要）：
 * - 全部为研究预览数据（status = preview / conflict），**非正式历史事实**，
 *   禁止写入 data/verified/，禁止混入生产 allCampaigns。
 * - 正式生产数据仍然只来自 data/verified/（人工核验 L2）。
 * - 日期为 Research 当前研究结论，随 exports/timeline_export_v1.json 的
 *   批量产出由导入接口替换（Adapter 支持，UI 不感知数据来源细节）。
 *
 * 已研究的三个案例年份：
 * - 2022：购置税减半政策行情（Auto Policy）
 * - 2023：智能驾驶行情（Smart Driving）+ 华为汽车链（Research Candidate，存在分歧）
 * - 2024：Robotaxi（萝卜快跑）
 */
export const timelinePreviewExport: TimelineExportV1 = {
  export_version: '1',
  generated_at: '2026-09-13',
  source_project: 'Cycle-Research',
  campaigns: [
    {
      campaign_id: 'cmp_prev_2022_auto_policy',
      rule_id: 'rule_auto_summer',
      year: 2022,
      season_id: '2022',
      title: '汽车 · 购置税减半政策行情',
      themes: [
        { name: '汽车整车', role: 'main' },
        { name: '汽车零部件', role: 'secondary' },
      ],
      start_date: '2022-05-31',
      peak_date: '2022-07-14',
      end_date: '2022-08-31',
      early_signal: {
        start_date: '2022-04-26',
        end_date: '2022-05-30',
        label: '疫后复产 + 稳增长政策预期',
      },
      retracement_start: '2022-07-29',
      securities: [
        { name: '长安汽车', role: 'leader' },
        { name: '比亚迪', role: 'representative' },
        { name: '广汽集团', role: 'follow' },
      ],
      description:
        '2022-05-31 财政部公告 600 亿元乘用车购置税减半落地，叠加疫后复产，整车与零部件共振上行；7 月中旬见顶后高位回落，8 月末结束。（研究预览口径，非正式历史事实）',
      research_status: 'preview',
      notes: 'Cycle-Research 2022 年度研究：政策驱动型行情，早信号为稳增长预期发酵。',
    },
    {
      campaign_id: 'cmp_prev_2023_smart_driving',
      rule_id: 'rule_auto_summer',
      year: 2023,
      season_id: '2023',
      title: '汽车 · 智能驾驶',
      themes: [
        { name: '智能驾驶', role: 'main' },
        { name: '线控底盘', role: 'secondary' },
      ],
      start_date: '2023-06-08',
      peak_date: '2023-07-14',
      end_date: '2023-09-08',
      early_signal: {
        start_date: '2023-04-18',
        end_date: '2023-06-07',
        label: '上海车展智能化定调',
      },
      retracement_start: '2023-07-28',
      securities: [
        { name: '伯特利', role: 'leader' },
        { name: '德赛西威', role: 'second_leader' },
        { name: '科博达', role: 'follow' },
      ],
      description:
        '2023 年 6—9 月智能驾驶主线行情：上海车展确立智能化产业趋势，6 月起城市 NOA 落地预期升温，7 月中旬见顶，9 月上旬退潮。（研究预览口径，非正式历史事实）',
      research_status: 'preview',
      notes: 'Cycle-Research 2023 年度研究：主题材为智能驾驶而非汽车整体。',
    },
    {
      campaign_id: 'cmp_prev_2023_huawei_auto',
      rule_id: 'rule_auto_summer',
      year: 2023,
      season_id: '2023',
      title: '汽车 · 华为汽车链（研究候选）',
      themes: [{ name: '华为汽车产业链', role: 'main' }],
      start_date: '2023-09-11',
      peak_date: '2023-11-15',
      end_date: '2023-12-08',
      securities: [
        { name: '赛力斯', role: 'leader' },
        { name: '江淮汽车', role: 'follow' },
      ],
      description:
        '2023 年 9 月问界新 M7 上市大定超预期引发的华为汽车链行情（研究候选）。（非正式历史事实）',
      research_status: 'conflict',
      conflicts: [
        'Research 内部存在分歧：独立行情，还是智能驾驶行情的延续组成部分',
        '起止日期两个研究版本不一致（2023-09-05 起步 / 2023-09-11 起步），待人工复核',
      ],
      notes: 'CONFLICT 仅为研究分歧标注，不得被描述成历史事实。',
    },
    {
      campaign_id: 'cmp_prev_2024_robotaxi',
      rule_id: 'rule_auto_summer',
      year: 2024,
      season_id: '2024',
      title: '汽车 · Robotaxi（萝卜快跑）',
      themes: [
        { name: 'Robotaxi', role: 'main' },
        { name: '自动驾驶', role: 'secondary' },
      ],
      start_date: '2024-07-10',
      peak_date: '2024-07-16',
      end_date: '2024-08-30',
      early_signal: {
        start_date: '2024-05-08',
        end_date: '2024-07-09',
        label: 'FSD 入华预期 + 萝卜快跑放量预期',
      },
      retracement_start: '2024-07-26',
      securities: [
        { name: '大众交通', role: 'leader' },
        { name: '锦江在线', role: 'second_leader' },
        { name: '金龙汽车', role: 'follow' },
      ],
      description:
        '2024 年 7 月武汉萝卜快跑爆单舆情引爆的 Robotaxi 主题行情：爆发快、见顶快（约一周），随后一个月退潮。（研究预览口径，非正式历史事实）',
      research_status: 'preview',
      notes: 'Cycle-Research 2024 年度研究：舆情脉冲型主题行情的代表案例。',
    },
  ],
};
