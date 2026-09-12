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
    captured_at: '2026-09-12',
    description:
      '项目启动时用户提供的个人经验判断汇总。内容为候选规律来源，' +
      '不代表已验证的市场规律；其中缺少精确日期与完整历史案例的部分均按经验窗口处理。',
  },
  {
    source_id: 'src_spec_001',
    source_type: 'personal',
    title: '项目需求文档中的数据结构示例',
    captured_at: '2026-09-12',
    description:
      '需求文档中为说明跨年行情数据结构而给出的示例（如 2026-11-01 → 2027-01-15）。' +
      '仅用于验证跨年渲染与数据结构，不是真实历史行情记录。',
  },
];

export const sourceById = new Map(sources.map((s) => [s.source_id, s]));
