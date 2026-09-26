/**
 * 首页「历史季节性机会地图」—— **Macro Theme 分类配色**（ThreeC 1.1）。
 *
 * ## 为什么需要
 * 地图纵轴 = Macro Theme（一主题一行）。改造前 **12 行共用同一个蓝 `#5a7a9a`**，
 * 逐行浏览时行与行之间缺乏视觉锚点，难以分辨「这根柱子属于哪一行」。
 *
 * ## 设计原则（不得违反）
 * 1. **分类，不是序数** —— 颜色只表示「属于哪个大主题」，**不表示强弱 / 排名 / 涨跌**。
 *    因此 12 色为**等距色相、统一饱和度**，**不得**改造成深浅渐变。
 *    ★ 本系统**不使用涨跌配色语义**（红涨绿跌与本图无关）。
 * 2. **颜色冗余于文字** —— 每行**始终**显示主题名，颜色只是辅助通道；
 *    色觉障碍用户不依赖颜色也能正常使用。
 * 3. **Today 是唯一强调色** —— 全图只有 Today 细红线用高饱和红（`--today`）。
 * 4. **对比度** —— 每个主色对白底对比度 ≥ 3:1（保证 9px 细条可见）。
 * 5. **映射稳定** —— 同一主题在任何年份 / 任何快照都同色；缺项回落中性灰，**不报错**。
 *
 * 方案来源：`docs/HOMEPAGE_THEME_COLOR_PROPOSAL_v0.1.md`
 */

/** 未归属大主题（`ThemeAnnualRow.theme === null`）的中性色 —— 不编造行业名，也不编造主题色 */
export const UNASSIGNED_COLOR = '#7E858C';
export const UNASSIGNED_ONSET_COLOR = '#C9CED3';

/** Macro Theme → 主要炒作窗口色（等距色相 30°，S=45%，L=40%） */
export const THEME_COLOR: Record<string, string> = {
  资源: '#944438',
  消费: '#947238',
  电子: '#889438',
  汽车: '#5A9438',
  金融: '#389444',
  高端装备: '#389472',
  信息通信: '#388894',
  国防军工: '#385A94',
  房地产: '#443894',
  电力设备: '#723894',
  医药健康: '#943888',
};

/** Macro Theme → 长周期起始（onset）的浅色变体（同色相，S=30%，L=80%） */
export const THEME_ONSET_COLOR: Record<string, string> = {
  资源: '#DBC1BD',
  消费: '#DBD0BD',
  电子: '#D7DBBD',
  汽车: '#C8DBBD',
  金融: '#BDDBC1',
  高端装备: '#BDDBD0',
  信息通信: '#BDD7DB',
  国防军工: '#BDC8DB',
  房地产: '#C1BDDB',
  电力设备: '#D0BDDB',
  医药健康: '#DBBDD7',
};

/** 主题主色；未标注 / 未知主题回落中性灰（诚实降级，不报错） */
export function themeColorOf(theme: string | null): string {
  if (!theme) return UNASSIGNED_COLOR;
  return THEME_COLOR[theme] ?? UNASSIGNED_COLOR;
}

/** 主题浅色（onset 用）；未标注 / 未知主题回落中性浅灰 */
export function themeOnsetColorOf(theme: string | null): string {
  if (!theme) return UNASSIGNED_ONSET_COLOR;
  return THEME_ONSET_COLOR[theme] ?? UNASSIGNED_ONSET_COLOR;
}
