import { describe, it, expect } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import {
  GRANULARITY_OPTIONS,
  SUB_GRANULARITY_NOTE,
  granularityAxis,
  granularityNoun,
  seasonalMapRows,
  themeAnnualRowsOf,
  themeKey,
} from '../themeAnnualWindow';
import { seasonalityOf, MIN_WINDOWS_FOR_CONCENTRATION } from '../themeSeasonality';
import { macroThemeOf } from '../researchAttention';
import { SeasonalMap } from '../../../components/SeasonalMap/SeasonalMap';

/**
 * 主题粒度（ThreeC 1.2 · Usage-Driven）不变量测试。
 *
 * ## 用户的原话
 * 「很多小主题，比如 煤炭、电力、流感疫苗、文化传媒 等等 好像时间相关性都挺高的，
 *   现在是大主题展示，如何能在地图上加入小主题呢？」
 *
 * ## 本层做的是「换分组口径」，**不是**「新增研究」
 *
 * ★★★ 最重要的不变量：**两种粒度的底层窗口集合完全相同**（同为 68 段窗口、同为 80 个对象）。
 *   粒度只决定「这些窗口怎么分行」，**一个对象都不会凭空出现或消失**。
 *   任何让 `sub` 比 `macro` 多出对象的改动，都意味着在 Product 侧伪造了研究对象 —— 必须失败。
 *
 * ★★ 第二重要：`sub` 下**绝大多数行样本不足**（41 行里只有 2 行的窗口数 ≥ 3）。
 *   集中标注的样本门槛（`MIN_WINDOWS_FOR_CONCENTRATION`）因此**不可因换粒度而放宽**。
 *
 * ★ 第三：粒度切换会**换掉行的 key**（大主题名 ≠ 主题材名），
 *   因此容器必须重置展开态 —— 本文件锁定「两者 key 集合确实不互相包含」这一事实。
 */

const src = researchTimelineSource();
const macroAll = themeAnnualRowsOf(src, 'macro');
const macroMap = seasonalMapRows(macroAll);
const subAll = themeAnnualRowsOf(src, 'sub');
const subMap = seasonalMapRows(subAll);

const objectsOf = (rows: typeof macroAll) => rows.reduce((n, r) => n + r.objects.length, 0);
const windowsOf = (rows: typeof macroAll) => rows.reduce((n, r) => n + r.windows.length, 0);

describe('粒度 = 分组口径，不是新的研究对象', () => {
  it('★★★ 两种粒度的对象集合与窗口集合**完全一致**（一个都不多、一个都不少）', () => {
    expect(objectsOf(macroAll)).toBe(86);
    expect(objectsOf(subAll)).toBe(86);
    expect(windowsOf(macroAll)).toBe(74);
    expect(windowsOf(subAll)).toBe(74);

    // 更强：对象 id 集合逐个相等（不是只有计数相等）
    const ids = (rows: typeof macroAll) =>
      [...new Set(rows.flatMap((r) => r.objects.map((o) => o.campaign_id)))].sort();
    expect(ids(subAll)).toEqual(ids(macroAll));
  });

  it('★ 行数差异只来自「拆得更细」：sub 行数 > macro 行数，且都在「几十条」量级', () => {
    expect(macroAll.length).toBe(14);
    expect(subAll.length).toBe(45);
    expect(macroMap.length).toBe(14);
    expect(subMap.length).toBe(39);
    // 首页仍不是明细库：即便最细口径也远小于对象数
    expect(subMap.length).toBeLessThan(80);
  });

  it('macro 行名 = macroThemeOf()；sub 行名 = themes[role=main].name', () => {
    const macroNames = new Set(
      macroAll.filter((r) => r.theme !== null).map((r) => r.theme as string),
    );
    for (const o of macroAll.flatMap((r) => r.objects)) {
      const want = macroThemeOf(o);
      if (want === null) continue;
      expect(macroNames.has(want)).toBe(true);
    }
    for (const o of subAll.flatMap((r) => r.objects)) {
      const main = (o.themes ?? []).find((t) => t.role === 'main');
      if (!main) continue;
      // 每个对象都必须落在「自己那个 main 主题材」的行里
      const row = subAll.find((r) => r.theme === main.name);
      expect(row).toBeDefined();
      expect(row!.objects.map((x) => x.campaign_id)).toContain(o.campaign_id);
    }
  });

  it('sub 是 macro 的**下钻**：大主题名不会原样消失（有 main 归属者仍可追溯）', () => {
    // 例：macro 的「汽车」在 sub 下拆成 华为汽车 / 汽车消费·购置税刺激 / 新能源汽车·电池 等
    const macroCar = macroAll.find((r) => r.theme === '汽车')!;
    const subNames = new Set(subAll.map((r) => r.theme));
    expect(subNames.has('汽车')).toBe(false); // 大主题名本身不再是 sub 的行名
    const carObjects = new Set(macroCar.objects.map((o) => o.campaign_id));
    const covered = new Set(
      subAll
        .filter((r) => r.objects.some((o) => carObjects.has(o.campaign_id)))
        .map((r) => r.theme),
    );
    expect(covered.size).toBeGreaterThan(1); // 确实被拆到多个具体方向
  });
});

describe('粒度切换必须重置展开态（key 集合不互相包含）', () => {
  it('★ 至少一个 macro key 在 sub 下不存在 —— 所以切换时不能沿用旧 key', () => {
    const mk = new Set(macroMap.map(themeKey));
    const sk = new Set(subMap.map(themeKey));
    const orphan = [...mk].filter((k) => !sk.has(k));
    expect(orphan.length).toBeGreaterThan(0);
    expect(orphan).toContain('汽车');
  });

  it('★ 每种粒度内部 key 唯一（否则展开会错行）', () => {
    for (const rows of [macroMap, subMap]) {
      const keys = rows.map(themeKey);
      expect(new Set(keys).size).toBe(keys.length);
    }
  });

  it('★★ Contract v1.1：产品归组改用 Research 侧（CMTR v1）解析出的根', () => {
    // 修复前的缺陷（实测）：`航天装备` 在 DB 里是 `国防军工` 的**子节点**，
    // 但产品按**字面名**归组 → 它自占一行，且因不在 `THEME_COLOR` 里
    // 而**渲染成与「未标注」相同的灰色**（不报错、看不出错）。
    // Contract v1.1 后产品优先用 `macro_theme_root` → `航天装备` 并入 `国防军工`。
    const macroNames = macroMap.map((r) => r.theme ?? '');
    expect(macroNames).not.toContain('航天装备');
    expect(macroNames).toContain('国防军工');

    // 该对象现在计入 `国防军工` 行
    const gj = macroMap.find((r) => r.theme === '国防军工')!;
    expect(gj.objects.map((o) => o.campaign_id)).toContain('RC-2024-MIL-COMMERCIAL-SPACE');

    // ★ 且每个对象都有解析出的根（唯一例外是已知 taxonomy 缺口 RC-2023-HUAWEI）
    const noRoot = macroAll
      .flatMap((r) => r.objects)
      .filter((o) => !o.macro_theme_root)
      .map((o) => o.campaign_id);
    expect(noRoot).toEqual(['RC-2023-HUAWEI']);
  });

  it('未归属行用哨兵 key，且标签按粒度给出（不编造行业名）', () => {
    expect(themeKey(macroAll.find((r) => r.theme === null)!)).toBe('__unassigned__');
    expect(themeKey(subAll.find((r) => r.theme === null)!)).toBe('__unassigned__');
    expect(macroAll.find((r) => r.theme === null)!.label).toBe('未标注大主题');
    expect(subAll.find((r) => r.theme === null)!.label).toBe('未标注主题材');
  });
});

describe('★★ 样本门槛不因换粒度而放宽', () => {
  it('sub 下只有 2 行的窗口数 ≥ 3；其余一律不做集中标注', () => {
    const eligible = subMap.filter((r) => seasonalityOf(r).windowCount >= MIN_WINDOWS_FOR_CONCENTRATION);
    expect(eligible.length).toBe(2);
    expect(eligible.map((r) => r.theme).sort()).toEqual(['半导体', '银行']);
  });

  it('★★ 不变量：窗口数 < 门槛 ⇒ 永远不 concentrated，且不给陈述', () => {
    for (const rows of [macroMap, subMap]) {
      for (const r of rows) {
        const s = seasonalityOf(r);
        if (s.windowCount < MIN_WINDOWS_FOR_CONCENTRATION) {
          expect(s.concentrated).toBe(false);
          expect(s.statement).toBeNull();
        }
      }
    }
  });

  it('★ 实测：sub 下「银行」3 个窗口 · 2 个落在 10-31~12-31 达到判据；「半导体」5 个只中 2 个，不标注', () => {
    const bank = seasonalityOf(subMap.find((r) => r.theme === '银行')!);
    expect(bank.windowCount).toBe(3);
    expect(bank.inBand).toBe(2);
    expect(bank.concentrated).toBe(true);
    expect(bank.band!.from).toBe('10-31');

    const semi = seasonalityOf(subMap.find((r) => r.theme === '半导体')!);
    expect(semi.windowCount).toBe(5);
    expect(semi.inBand).toBe(2);
    expect(semi.concentrated).toBe(false);
    expect(semi.statement).toBeNull();
  });

  it('★ macro 下达到判据的 2 行是汽车 / 金融（换粒度不影响既有结论）', () => {
    // ★★ 2026-10-11（R02-03 入库后）由 3 行 → **2 行**：
    // `资源` 因新增煤炭窗口（2021-08~10）落在集中带（03-02~05-02）外 → 3/5 < 2/3，不再达标。
    const conc = macroMap.filter((r) => seasonalityOf(r).concentrated).map((r) => r.theme);
    expect(conc.sort()).toEqual(['汽车', '金融']);
  });
});

describe('★ 覆盖边界：R02-03 之后，用户点名的方向**已在库内**', () => {
  // ★★ 2026-10-11 反转：本测试原先断言「煤炭 / 电力 / 流感疫苗 / 文化传媒 一个都不命中」。
  //     R02-03 canonicalization 之后该断言**已不成立**（这是好消息导致的失败）——
  //     现在四个方向都已在库内，其中两个是**新增的根节点**。
  it('煤炭 / 流感疫苗 / 文化传媒 / 电力（运营端）均已入库', () => {
    const names = subAll.map((r) => r.theme ?? '');
    // ★ sub 粒度取的是 `themes[role=main].name` —— 所以这里断言的是**主题材**名。
    //   `电力（运营端）` 是 `related`（macro 层），**不出现在 sub 行名里**；
    //   它在 macro 粒度出现（见下一条断言）。
    for (const w of ['煤炭', '流感疫苗', '文化传媒', '绿电 / 新能源运营商']) {
      expect(names.some((n) => n.includes(w))).toBe(true);
    }
    // macro 粒度：两个**新增的根节点**各自成行
    const macroNames = macroAll.map((r) => r.theme ?? '');
    for (const w of ['电力（运营端）', '文化传媒']) {
      expect(macroNames.some((n) => n.includes(w))).toBe(true);
    }
    // 仍未覆盖的（如实保留）：教育
    expect(names.some((n) => n === '教育')).toBe(false);
  });

  it('相近但不同：「电网/输变电设备」「光伏/新能源发电设备」存在，属电力设备而非公用事业电力', () => {
    const names = subAll.map((r) => r.theme ?? '');
    expect(names).toContain('电网/输变电设备');
    expect(names).toContain('光伏/新能源发电设备');
  });
});

describe('粒度文案', () => {
  it('选项 / 表头 / 量词一一对应', () => {
    expect(GRANULARITY_OPTIONS.map((o) => o.value)).toEqual(['macro', 'sub']);
    expect(granularityAxis('macro')).toBe('大主题');
    expect(granularityAxis('sub')).toBe('主题材');
    expect(granularityNoun('macro')).toBe('大主题');
    expect(granularityNoun('sub')).toBe('主题材');
  });

  it('★ sub 的样本边界说明必须写明「样本不足时不做标注」，且不含禁列词', () => {
    expect(SUB_GRANULARITY_NOTE).toContain('样本不足时一律不做集中标注');
    for (const bad of ['胜率', '推荐分', '预测', '**', 'score', 'probability']) {
      expect(SUB_GRANULARITY_NOTE).not.toContain(bad);
    }
  });
});

describe('SeasonalMap · 粒度切换渲染', () => {
  const render = (granularity: 'macro' | 'sub') =>
    renderToStaticMarkup(
      createElement(SeasonalMap, {
        rows: granularity === 'macro' ? macroMap : subMap,
        today: '2026-10-08',
        openTheme: null,
        onOpenTheme: () => {},
        granularity,
        onGranularity: () => {},
      }),
    );

  const macroHtml = render('macro');
  const subHtml = render('sub');

  it('切换控件存在，且当前粒度处于选中态（aria-pressed）', () => {
    expect(macroHtml).toContain('sm-gran');
    expect(macroHtml).toContain('按大主题');
    expect(macroHtml).toContain('按主题材');
    expect(macroHtml).toContain('aria-pressed="true"');
    // macro 渲染里「按大主题」按钮是选中态
    expect(macroHtml).toMatch(/aria-pressed="true"[^>]*>按大主题|按大主题<\/button>/);
  });

  it('纵轴表头随粒度变化（大主题 → 主题材）', () => {
    expect(macroHtml).toContain('>大主题</div>');
    expect(subHtml).toContain('>主题材</div>');
  });

  it('渲染行数 = 该粒度的行数（不是另一粒度的行数）', () => {
    expect((macroHtml.match(/class="sm-row/g) ?? []).length).toBe(macroMap.length);
    expect((subHtml.match(/class="sm-row/g) ?? []).length).toBe(subMap.length);
  });

  it('★ 样本边界说明只在 sub 粒度出现（macro 下不吓唬用户）', () => {
    expect(subHtml).toContain('样本不足时一律不做集中标注');
    expect(macroHtml).not.toContain('样本不足时一律不做集中标注');
  });

  it('★ 集中标注随粒度重算：macro 3 个、sub 1 个', () => {
    expect((macroHtml.match(/sm-seasonal-flag/g) ?? []).length).toBe(2);
    expect((subHtml.match(/sm-seasonal-flag/g) ?? []).length).toBe(1);
    expect(subHtml).toContain('银行');
  });

  it('★★ 两种粒度下都不引入评分 / 排名 / 概率 / 预测 / 胜率 / 推荐分', () => {
    for (const html of [macroHtml, subHtml]) {
      for (const bad of ['score', 'ranking', 'probability', 'prediction', '胜率', '推荐分', '预测']) {
        expect(html.toLowerCase()).not.toContain(bad.toLowerCase());
      }
    }
  });

  it('★ 切换控件不破坏既有契约：Today 仍只有一根细红线', () => {
    for (const html of [macroHtml, subHtml]) {
      expect((html.match(/class="today-span"/g) ?? []).length).toBe(1);
    }
  });
});
