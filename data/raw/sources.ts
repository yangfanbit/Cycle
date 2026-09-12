import type { Source } from '../../src/models';

/**
 * 信息来源（raw 层）。
 * 注意：当前全部规律来自用户提供的个人经验材料，
 * 属于 article / experience source，不能直接当作已验证事实。
 */
export const sources: Source[] = [
  {
    source_id: 'src_exp_001',
    source_type: 'article',
    title: '用户提供的A股季节性经验材料（原始经验描述，未经验证）',
    author: '用户提供',
    url: 'https://www.zhihu.com/question/464198498',
    captured_at: '2026-09-12',
    description:
      '项目启动时用户提供的个人经验判断汇总（原始来源为知乎问题页）。' +
      '内容为候选规律来源，不代表已验证的市场规律；其中缺少精确日期与完整历史案例的部分均按经验窗口处理。',
  },
];

export const sourceById = new Map(sources.map((s) => [s.source_id, s]));
