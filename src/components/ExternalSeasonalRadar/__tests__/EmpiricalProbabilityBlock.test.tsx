/**
 * ★★ 经验基准概率区块的**渲染事实**（v0.9）。
 *
 * 本文件只断言「给定真实数据时渲染出什么」：
 * 分母、排除项、区间、探索性标记、机制区分、可行性结论。
 * 计算正确性由 `empiricalProbability.test.ts` 覆盖。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { crossYearComparisonOf, eventMapByTheme } from '../../../data/timeline/historicalEventMaps';
import { EmpiricalProbabilityBlock } from '../EmpiricalProbabilityBlock';

const power = eventMapByTheme('POWER_SUMMER')!;
const flu = eventMapByTheme('FLU')!;
const renderPower = () => renderToStaticMarkup(
  <EmpiricalProbabilityBlock doc={power.doc} cmp={crossYearComparisonOf(power.doc)!} />,
);
const renderFlu = () => renderToStaticMarkup(
  <EmpiricalProbabilityBlock doc={flu.doc} cmp={crossYearComparisonOf(flu.doc)!} />,
);

const textOf = (html: string) => html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

describe('经验基准概率 · 渲染事实', () => {
  it('★★ 标题用「探索性经验基准概率」并带「未校准」徽标', () => {
    const html = renderPower();
    expect(html).toContain('历史结果分布');
    expect(html).toContain('探索性经验基准概率');
    expect(html).toContain('未校准');
  });

  it('★★ 分母与点估计**来自数据**：电力 1 / 7', () => {
    const t = textOf(renderPower());
    expect(t).toContain('1 / 7');
    expect(t).toContain('14.3%');
  });

  it('★★ 显示 95% Wilson 区间（小样本 → 宽区间）', () => {
    const t = textOf(renderPower());
    expect(t).toContain('95% Wilson');
    expect(t).toContain('2.6%');
    expect(t).toContain('51.3%');
  });

  it('★★ 排除项逐条可见，且带源数据原因', () => {
    const html = renderPower();
    expect(html).toContain('data-ep-excluded="2016"');
    expect(html).toContain('data-ep-excluded="2019"');
    expect(html).toContain('data-ep-excluded="2024"');
    const t = textOf(html);
    expect(t).toContain('部分可比');
    expect(t).toContain('交易日');
  });

  it('★★ 明确写出「排除 ≠ 失败」（不得让读者以为排除=没涨）', () => {
    expect(textOf(renderPower())).toContain('排除 ≠ 失败');
  });

  it('★★ 目标定义与判定规则原样展示（读者能核对 1/7 在数什么）', () => {
    const t = textOf(renderPower());
    expect(t).toContain('目标事件');
    expect(t).toContain('观察窗口');
    expect(t).toContain('每年 5/1 – 7/31');
    expect(t).toContain('标的池');
    expect(t).toContain('华电国际');
    expect(t).toContain('全部跑赢基准');
  });

  it('★★ 声明「不是对未来窗口的预测」+「三层口径」', () => {
    const t = textOf(renderPower());
    expect(t).toContain('不是对未来窗口的预测');
    expect(t).toContain('尚未');
    expect(t).toContain('三层口径');
    expect(t).toContain('历史统计描述');
    expect(t).toContain('经验基准概率');
    expect(t).toContain('经验证的预测模型');
  });

  it('★★ 流感：唯一成功年 2019 标注 UNKNOWN_PUBLIC_HEALTH（不是流感驱动）', () => {
    const html = renderFlu();
    expect(html).toContain('data-ep-success="2019"');
    const t = textOf(html);
    expect(t).toContain('UNKNOWN_PUBLIC_HEALTH');
    // 机制表里 SEASONAL_FLU 行的 UP 计数为 0
    const mechRow = html.slice(html.indexOf('data-ep-mechanism="SEASONAL_FLU"'));
    const rowText = mechRow.slice(0, mechRow.indexOf('</tr>')).replace(/<[^>]+>/g, '|');
    expect(rowText).toContain('|0|');
  });

  it('★★ 流感分母 1 / 9（不是 11 个窗口）', () => {
    const html = renderFlu();
    expect(textOf(html)).toContain('1 / 9');
    expect(html).toContain('data-ep-excluded="2015"');
    expect(html).toContain('data-ep-excluded="2016"');
    expect(html).toContain('分母内 9 个完整可比较年份');
  });

  it('★★ 模型可行性：显示「不训练」，并列出门槛与缺口', () => {
    const t = textOf(renderPower());
    expect(t).toContain('可行性');
    expect(t).toContain('门槛 30');
    expect(t).toContain('不训练');
    expect(t).toContain('事前');
  });

  it('★★ 评估方式是时间前推（禁止随机拆分），且逐步列出训练年份', () => {
    const html = renderPower();
    expect(html).toContain('data-ep-step="2021"');
    expect(html).toContain('data-ep-step="2025"');
    const t = textOf(html);
    expect(t).toContain('严格按年份升序');
    expect(t).toContain('不做');
    expect(t).toContain('随机拆分');
    expect(t).toContain('Brier');
    expect(t).toContain('LogLoss');
  });

  it('★★ 校准分箱照实显示：空箱写「无样本」，不合并、不省略', () => {
    const html = renderPower();
    expect(html).toContain('data-ep-calibration=');
    expect(html).toContain('校准偏差');
    expect(html).toContain('无样本');
    // 分箱步数总和 = 样本外步数（不重不漏）
    const steps = Number(html.match(/样本外 (\d+) 步/)?.[1] ?? '0');
    expect(steps).toBeGreaterThan(0);
  });

  it('★★ 评估基准写明 Jeffreys 平滑，且声明「只用于评估、k/n 未平滑」', () => {
    const html = renderPower();
    expect(html).toContain('data-ep-baseline-kind="JEFFREYS_SMOOTHED_FREQUENCY"');
    const t = textOf(html);
    expect(t).toContain('Jeffreys');
    expect(t).toContain('(k + 0.5) / (n + 1)');
    expect(t).toContain('只用于评估');
    expect(t).toContain('未做平滑');
  });

  it('★★ 逐步表同时给出「原始 k/n」与「平滑基准预测」（可核对）', () => {
    const html = renderPower();
    expect(html).toContain('原始 k/n');
    expect(html).toContain('基准预测（平滑）');
    expect(html).toContain('fem-ep-raw');
  });

  it('★★ 可行性分成**两道门槛**显示：步数 / 事前特征 / 训练条件', () => {
    const html = renderPower();
    expect(html).toContain('data-ep-gates="1"');
    const t = textOf(html);
    expect(t).toContain('样本外步数');
    expect(t).toContain('事前特征');
    expect(t).toContain('训练条件');
    expect(t).toContain('不具备');
    // 现有数据 0 个事前特征 → 特征那一道必须是「不足」
    expect(t).toContain('事前特征：0 / 3');
  });

  it('★★ 渲染里**没有** Markdown 星号（JSX 不解析 `**`）', () => {
    for (const html of [renderPower(), renderFlu()]) {
      expect(html).not.toContain('**');
      expect(html).toContain('<strong>');
    }
  });

  it('★★ 不出现买卖 / 推荐 / 评分 / 排名类措辞（真实语义守卫仍保留）', () => {
    for (const html of [renderPower(), renderFlu()]) {
      for (const hard of ['买入', '卖出', '建仓', '加仓', '减仓', '止盈', '止损', '仓位',
        '推荐', '评分', '排名', '胜率', '目标价', '必涨']) {
        expect(html, hard).not.toContain(hard);
      }
    }
  });

  it('★ 不把本区块写成「结构对应」结论（结构对应唯一入口是冻结 SA）', () => {
    const t = textOf(renderPower());
    expect(t).not.toContain('结构对应成立');
    expect(t).not.toContain('对应结论');
  });
});
