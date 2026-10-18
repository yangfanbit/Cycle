import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react';
import { CampaignDetail } from './components/CampaignDetail/CampaignDetail';
import { CurrentSnapshotSection } from './components/CurrentSnapshot/CurrentSnapshotSection';
import { DirectionLookupSection } from './components/DirectionLookup/DirectionLookupSection';
import { ExternalSeasonalRadar } from './components/ExternalSeasonalRadar/ExternalSeasonalRadar';
import { CurrentTimeLens } from './components/CurrentTimeLens/CurrentTimeLens';
import { HistoricalPanorama } from './components/HistoricalPanorama/HistoricalPanorama';
import {
  HistoricalThemeMaps,
  HISTORICAL_THEME_MAPS_ID,
} from './components/HistoricalThemeMaps/HistoricalThemeMaps';
import { HistoricalSimilarPhase } from './components/HistoricalSimilarPhase/HistoricalSimilarPhase';
import { MacroThemeSheet } from './components/MacroThemeSheet/MacroThemeSheet';
import { RuleDetail } from './components/RuleDetail/RuleDetail';
import { SamePeriodView } from './components/SamePeriodView/SamePeriodView';
import { SeasonalMap } from './components/SeasonalMap/SeasonalMap';
import { Timeline, type Selection } from './components/Timeline/Timeline';
import { allCampaigns, campaignById, ruleById } from './data';
import { researchTimelineSource, verifiedTimelineSource } from './data/timeline/timelineAdapter';
import {
  externalCalendarDoc,
  type ExternalCalendarEntry,
} from './data/timeline/externalSeasonalCalendar';
import { makeDraftSeed, type DraftSeed } from './data/timeline/externalLeadDraft';
import type { ResearchRequestDraft } from './data/timeline/researchRequestDraft';
import { timelineExportData } from './data/timeline/timelinePreview';
import type { TimelineCampaign } from './data/timeline/timelineTypes';
import {
  granularityNoun,
  seasonalMapRows,
  seasonalMapSummary,
  themeAnnualRowsOf,
  themeKey,
} from './data/timeline/themeAnnualWindow';
import type { ThemeGranularity } from './data/timeline/themeAnnualWindow';
import type { HistoricalCaseAnalogyContext } from './data/timeline/historicalCase';
import type { CurrentCandidateDataset } from './data/timeline/currentCandidate';
import { selectCurrentCandidateDataset } from './data/timeline/appDatasets';
import { buildProvenance, PROVENANCE_NOT_AVAILABLE } from './data/buildProvenance';
import { CurrentMarketStrip } from './components/CurrentMarket/CurrentMarketStrip';
import { CurrentWatchboardSection } from './components/CurrentWatchboard/CurrentWatchboardSection';
import { marketTodayISO } from './utils';

/**
 * ?verified=1 → 旧 verified 生产层（`data/verified`，当前为空，保留为显式回退路径）。
 *
 * Product 1.1 起**首页默认消费 canonical Research export**
 * （`exports/timeline_export_v1.json`），使已 Research 的 Historical Universe
 * 正式进入第一视觉；`?verified=1` 仅用于对照旧生产层。
 * 不做运行时网络访问（静态 PWA 不变）。
 */
/**
 * ★ v0.7：SSR / 预渲染 / node 测试环境下安全读取 URL 查询参数。
 *
 * 原来这三处 flag 直接访问 `window.location` —— 于是 **`<App />` 在 node 下渲染即崩**
 * （`window is not defined`），这也正是「App 层零测试」的原因之一。
 * 无 `window` 时返回空串 = **默认模式**（与生产环境不带参数时行为一致）。
 */

/** 方向查询区的 id（供外部线索「带入研究请求」滚动定位） */
const DIRECTION_LOOKUP_ID = 'direction-lookup';
function urlParam(name: string): string {
  if (typeof window === 'undefined') return '';
  try {
    return new URLSearchParams(window.location.search).get(name) ?? '';
  } catch {
    return '';
  }
}

/** ★ v0.7：SSR 安全的当前路径（无 window → '/'） */
function currentPath(): string {
  if (typeof window === 'undefined') return '/';
  try {
    return window.location.pathname;
  } catch {
    return '/';
  }
}

function verifiedEnabled(): boolean {
  return urlParam('verified') === '1';
}

/**
 * ?candidates=example 展示**示例 fixture**（Phase 7）。
 *
 * 缺省时产品消费 canonical 数据集 `research/current/current_candidates.json`
 * （Phase 7.1 起承载第一轮真实候选 5 条；数据集为空时 Current Lens 显示诚实空态）。
 * fixture 仅用于验证 Temporal Firewall / 阶段推断 / 相似度链路，UI 会显式标注
 * 「示例 fixture（非真实研究数据）」。
 */
function exampleCandidatesEnabled(): boolean {
  return urlParam('candidates') === 'example';
}

/**
 * ?snapshot=draft 放宽 Market Snapshot 的展示门禁（Phase 1.3）。
 *
 * 默认**只展示已签发（`CANONICAL`）**的快照 —— 防止未经人工审核的研究被当成结论。
 * 本开关仅用于预览未签发内容，页面会**常驻醒目徽标**标明「未签发 · 仅供预览」。
 */
function snapshotPreviewEnabled(): boolean {
  return urlParam('snapshot') === 'draft';
}

export default function App() {
  // A股市场日期基准：Asia/Shanghai（不随用户机器时区漂移）
  const today = useMemo(() => marketTodayISO(), []);
  const verifiedMode = useMemo(() => verifiedEnabled(), []);

  // Timeline 数据源（Product 1.1）：
  //   默认 = canonical Research export（52 Campaign + 27 Research Candidate，2015–2025）；
  //   ?verified=1 = 旧 verified 生产层（当前为空，显式回退）。
  const dataSource = useMemo(
    () => (verifiedMode ? verifiedTimelineSource() : researchTimelineSource()),
    [verifiedMode],
  );

  /**
   * ★ v0.13：历史窗口对照用的**宏观主题行**。
   * 显式使用 `granularity='macro'` —— 不随用户在首页切换 `macro`/`sub` 而变化。
   */
  const macroThemeRows = useMemo(
    () => (dataSource ? themeAnnualRowsOf(dataSource, 'macro') : []),
    [dataSource],
  );

  /**
   * ★ v0.13：未映射外部线索 → 研究请求草稿的「种子」。
   * `token` 每次自增，让同一条线索再次点击也能重新触发（组件据此决定带入）。
   */
  const [draftSeed, setDraftSeed] = useState<DraftSeed | null>(null);
  const draftSeedToken = useRef(0);

  const bringExternalLead = useCallback((entry: ExternalCalendarEntry) => {
    draftSeedToken.current += 1;
    setDraftSeed(makeDraftSeed(
      entry,
      externalCalendarDoc().source_reports,
      draftSeedToken.current,
    ));
    // 滚到方向查询区（SSR / 无 DOM 时不假装滚动了）
    if (typeof document === 'undefined') return;
    const el = document.getElementById(DIRECTION_LOOKUP_ID);
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);
  const availableYears = useMemo(() => dataSource.years(), [dataSource]);

  // Current Candidate 数据集（Phase 7）：
  //   · `?candidates=example` → 示例 fixture（显式开启）
  //   · 默认 → **canonical 数据集**（与 CurrentTimeLens 的 `defaultCurrentCandidateParse()`
  //     同一份静态数据，单一数据源）
  // ★★ 2026-10-16 修复（v0.6 D 工作流发现的 P0 接线 bug）：默认曾是 `null`，
  //   于是「查一个方向」在默认页面上**看不到任何当前研究对象** —— 同页 Watchboard
  //   明明展示着 6 个候选，方向查询却对「汽车」回答「只有历史案例」。
  //   根因：选取规则只存在于本文件的接线约定里，而组件测试都直接注入 dataset
  //   → 接线错误永远逃过测试。现抽到 `selectCurrentCandidateDataset()`（纯函数，可断言）。
  const candidatesExample = useMemo(() => exampleCandidatesEnabled(), []);
  const currentCandidates = useMemo<CurrentCandidateDataset>(
    () => selectCurrentCandidateDataset({ exampleFixture: candidatesExample }),
    [candidatesExample],
  );

  // ★ 首页第一视觉（Product 1.1 第二轮）：主题 × 年内时间窗口聚合。
  //   一主题一行，同主题的多次历史出现合并观察；不是一对象一行，也不是一年一行。
  //   ★ 粒度（ThreeC 1.2）：`macro` 大主题（默认） / `sub` 主题材（具体方向）。
  //     粒度只改**分组口径**，不新增对象、不新增研究结论。
  const [granularity, setGranularity] = useState<ThemeGranularity>('macro');
  const allThemeRows = useMemo(
    () => themeAnnualRowsOf(dataSource, granularity),
    [dataSource, granularity],
  );
  const mapRows = useMemo(() => seasonalMapRows(allThemeRows), [allThemeRows]);

  // ★★ 覆盖边界横幅的**数据驱动**来源（2026-10-16）：Contract v1.2 `taxonomy` 段的根大主题。
  //   取代原人工维护的硬编码「不包含传媒/煤炭/电力/流感疫苗」—— 那四个方向此后都已入库，
  //   硬编码声明与同页季节地图、themeGranularity 测试三方矛盾。根节点 = `parent_theme_id` 为 null。
  //   legacy verified 源无 taxonomy 段 → 空数组 → 横幅走「无法列出」的诚实分支。
  const taxonomyRoots = useMemo(
    () =>
      (dataSource.taxonomy?.() ?? [])
        .filter((n) => n.parent_theme_id === null)
        .map((n) => n.name),
    [dataSource],
  );
  const mapSummary = useMemo(() => seasonalMapSummary(mapRows), [mapRows]);
  /**
   * ★ v0.10：首页「历史题材地图」当前题材。
   * 由外部雷达的「在历史题材地图中查看」联动 —— 点一下即选中并滚到该区块。
   */
  const [mapTheme, setMapTheme] = useState<string | null>(null);
  const openMapTheme = useCallback((themeId: string) => {
    setMapTheme(themeId);
    // SSR / 无 DOM 环境 → 只改状态，不滚动（不得假装滚动了）
    if (typeof document === 'undefined') return;
    const el = document.getElementById(HISTORICAL_THEME_MAPS_ID);
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  const [openTheme, setOpenTheme] = useState<string | null>(null);
  const openThemeRow = useMemo(
    () => allThemeRows.find((r) => themeKey(r) === openTheme) ?? null,
    [allThemeRows, openTheme],
  );
  /**
   * ★ 切换粒度时**必须重置展开态**：换口径后原来的 key 未必存在
   *   （大主题名 ≠ 主题材名），否则附页会悬空或错行。
   */
  const changeGranularity = useCallback((g: ThemeGranularity) => {
    setGranularity(g);
    setOpenTheme(null);
  }, []);

  // 初始年份：当前年不在数据源年份内时回退到最近的可用年份
  // （如 Research 源 2015–2025、当前 2026 → 打开即显示 2025，而不是空白年）
  const [year, setYear] = useState(() => {
    const current = Number(today.slice(0, 4));
    if (availableYears.length === 0 || availableYears.includes(current)) return current;
    const earlier = availableYears.filter((y) => y < current);
    return earlier.length > 0 ? Math.max(...earlier) : Math.min(...availableYears);
  });
  const [selection, setSelection] = useState<Selection>(null);
  // 从 Structural Analogy 进入 Historical Case 时携带的轻量上下文（原样消费，不重算）
  const [analogyContext, setAnalogyContext] = useState<HistoricalCaseAnalogyContext | null>(null);

  /**
   * ★ 接通（ThreeC 1.2 · P0 最后一块）：从「本期研究快照」的研究对象
   * 跳到它的**结构对应详情**（Current Time Lens 里的冻结 SA 区块）。
   *
   * 做法：设置 focusCandidateId（由 CurrentTimeLens 透传给候选区块就地展开），
   * 并展开承载它的原生 `<details>` 后滚过去。
   * 只做导航，**不做任何判定**。
   */
  const [focusCandidateId, setFocusCandidateId] = useState<string | null>(null);
  const focusObject = useCallback((objectId: string) => {
    setFocusCandidateId(objectId);
    const el = document.getElementById('drill-current-time-lens') as HTMLDetailsElement | null;
    if (el) {
      el.open = true;
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  const yearData = useMemo(() => dataSource.yearData(year), [dataSource, year]);

  // Campaign 索引（供详情面板解析；Research 数据不进入生产 allCampaigns）
  const researchCampaignsById = useMemo(() => {
    const map = new Map<string, TimelineCampaign>();
    for (const y of dataSource.years()) {
      for (const c of dataSource.yearData(y).campaigns) map.set(c.campaign_id, c);
    }
    return map;
  }, [dataSource]);

  /**
   * ★ v0.14：外部×历史窗口对照 → 进入**具体对象**详情。
   * 复用同一套 selection / CampaignDetail 流程（不建第二个详情弹窗）；
   * Research Candidate 与 Campaign 都走这里，**保持原身份**（详情内部自己呈现 kind）。
   */
  const openHistoricalObject = useCallback((id: string, _year: number) => {
    setSelection({ kind: 'campaign', id });
  }, []);
  /**
   * 该历史对象能否通过现有详情流程解析。
   * 解析不了 → 对照面板不渲染「查看对象详情」按钮（不放无效按钮）。
   */
  const canOpenHistoricalObject = useCallback((id: string) =>
    campaignById.has(id) || (!verifiedMode && researchCampaignsById.has(id)),
  [campaignById, verifiedMode, researchCampaignsById]);

  const selectedRule = selection?.kind === 'rule' ? ruleById.get(selection.id) : undefined;
  // 生产 verified 优先；Research Campaign 在非 verified 模式下解析
  const selectedCampaign =
    selection?.kind === 'campaign'
      ? campaignById.get(selection.id) ?? (!verifiedMode ? researchCampaignsById.get(selection.id) : undefined)
      : undefined;

  return (
    <>
      <header className="app-header">
        <h1 className="app-title">A股机会时间轴</h1>
        <p className="app-subtitle">一年中历史上哪些时间窗口反复出现过什么类型的题材炒作</p>
        <div className="app-today">
          <span className="today-chip">Today {today}</span>
        </div>
        {/* ★ 当前市场状态（ThreeC 1.2 · 只读描述性产物）
            ★★ 放在**全局位置**、**不与任何历史行情并列** ——
               把「某段历史的启动前」与「现在」摆在同一张卡片里，等于替使用者摆好「像不像」的题面。 */}
        <CurrentMarketStrip />
      </header>

      <main className="app-main">
        {/* ★ 第一视觉（Product 1.1 第二轮）：历史季节性机会地图。
            纵轴 = 大主题（一主题一行），横轴 = 1–12 月，条形 = 历史主要炒作在年内的窗口。
            首页是「地图」，不是「历史数据库」——逐条对象明细一律走下面的钻取入口。 */}
        {!verifiedMode && mapRows.length > 0 && (
          <SeasonalMap
            rows={mapRows}
            today={today}
            openTheme={openTheme}
            onOpenTheme={setOpenTheme}
            granularity={granularity}
            onGranularity={changeGranularity}
          />
        )}

        {/* 一句数据语义说明（首页唯一的数据口径声明） */}
        {!verifiedMode && mapRows.length > 0 && (
          <p className="seasonal-note">
            横轴 1–12 月、每行一个{granularityNoun(granularity)}；条形为该主题历史<strong>主要炒作</strong>
            在年内的窗口（长周期仅标起始位置）；「历史 N 次 / 覆盖 N 个年份」是<strong>计数事实</strong>
            ，不是概率、胜率或预测。共 {mapSummary.themeCount} 个{granularityNoun(granularity)} /{' '}
            {mapSummary.objectCount} 个研究对象
            {mapSummary.yearFrom !== null && mapSummary.yearTo !== null
              ? `（${mapSummary.yearFrom}–${mapSummary.yearTo}）`
              : ''}
            ，来自 Cycle-Research canonical export，研究对象含 PROVISIONAL / CONFLICT，
            <strong>非正式历史事实</strong>。
          </p>
        )}

        {/* ★★ 历史题材地图（v0.10 新增 · **直接入口**）——
            4 个题材的历史事后重建，首屏可切换，**不需要**先展开外部线索。
            ★ 复用 `HistoricalEventMap`（事件卡 / 跨年份比较 / 经验基准概率原样），
              题材清单由 `historical_event_maps_index.json` 驱动。
            ★ 与下方外部雷达**职责分离**：本区 = ThreeC 从历史数据得到；雷达 = 外部资料声称。 */}
        {!verifiedMode && (
          <HistoricalThemeMaps activeThemeId={mapTheme ?? undefined} onSelectTheme={setMapTheme} />
        )}

        {/* ★ 外部季节性观察雷达（2026-10-13 新增）——
            ★★ 与上方地图**并列但来源分离**：上方是 ThreeC **从历史数据得到的**窗口（研究结果），
               本视图是**外部资料声称的**季节性线索（未经 ThreeC 验证）。
               两者**不得**混为一个没有来源区分的指标体系。 */}
        {!verifiedMode && (
          <ExternalSeasonalRadar
            today={today}
            onOpenMap={openMapTheme}
            onRequestDraft={bringExternalLead}
            onOpenObject={openHistoricalObject}
            canOpenObject={canOpenHistoricalObject}
            macroRows={macroThemeRows}
          />
        )}

        {/* ★ 覆盖边界（ThreeC 1.2 · Usage-Driven）
            用户拿一个真实方向来问（例如「文化传媒」）时，第一件要知道的是「它在不在覆盖内」。
            ★★ 2026-10-16 改为**数据驱动**（此前是人工维护的硬编码文本，已两次落后于数据：
               原文仍称「煤炭 / 电力 / 流感疫苗 / 文化传媒 一个都没有命中」，而这四个方向
               **此后都已被研究轮次入库** —— 与同页季节地图、themeGranularity 测试三方矛盾）。
            ★ 现在由 Contract v1.2 的 `taxonomy` 段**实时推导**：列出当前**根大主题**，
              「不在其中」即未覆盖。覆盖范围由 Research 决定；扩边属研究轮次，
              Product 侧不自行推断、不编造父主题。 */}
        {!verifiedMode && mapRows.length > 0 && (
          <p className="seasonal-scope">
            <strong>分类体系</strong>：
            {taxonomyRoots.length > 0 ? (
              <>
                当前研究分类体系有 <strong>{taxonomyRoots.length}</strong> 个<strong>根主题</strong>：
                <strong>{taxonomyRoots.join(' · ')}</strong>
                （数据来源：Contract v1.2 `taxonomy` 段，由 DB `themes` 表推导 ——
                **不是人工列举**，研究轮次新增主题后此处自动跟上）。
              </>
            ) : (
              <>当前数据源未提供 taxonomy 段（legacy verified 源）→ 无法列出根主题，</>
            )}
            <span className="seasonal-scope-note">
              ★★ <strong>这是分类体系事实，不是覆盖承诺</strong>：根主题下可能<strong>只有 1–2 个</strong>
              历史对象，也可能某个<strong>具体方向名</strong>根本不在根清单里却仍有命中
              （例如「半导体」属「电子」、「电力」是运营端口径、子主题名与概念名通常与根名不同）。
              因此<strong>「不在上面的根清单里」并不等于「未覆盖」</strong> ——
              <strong>具体结论以方向查询的实际命中为准</strong>，本清单只描述分类结构。
              <br />
              ★ 四件事互不相同，不要合并成一个标签：
              <strong>① 分类体系里有没有对应根主题</strong> ·
              <strong>② 查询有没有命中对象</strong>（当前侧 / 历史侧分别看）·
              <strong>③ 有没有冻结 SA 给出的结构对应</strong> ·
              <strong>④ 是「资料不足」还是「确实没有对应」</strong>。
              <br />
              ★ 语义边界：<strong>名字没命中 ≠ 结构上无对应</strong>（结构对应比的是机制 / 序列 /
              事件结构，不是名字）；反过来，<strong>名字命中 ≠ 结构对应</strong> ——
              冻结 SA 的解释才是唯一的结构对应入口。
              （覆盖范围由 Research 决定；扩边属研究轮次，不在 Product 侧自行推断，
              也不为把清单凑齐而推断缺失对象。）
            </span>
          </p>
        )}

        {/* ★★ 当前观察台（ThreeC 1.2 · Usage-Driven）
            用户要的是「**在当下这个时间点，一屏看到该看什么**」，而不是逐条点开对照。
            ★★★ 但它**不是**「可能性排序」：项目禁止概率 / 评分 / 预测，且**一旦排序就会被当作推荐**。
            因此按**阶段**分组（封闭枚举）、组内按**阶段起点时间序**，核心列是「**还缺什么**」。
            点击对象 → 复用既有 focusObject（展开当前时间透镜并滚动过去），只做导航、不做判定。 */}
        {!verifiedMode && (
          <CurrentWatchboardSection onOpenCandidate={focusObject} />
        )}

        {/* verified 模式且 verified 层为空：提示回到默认 Research 数据源 */}
        {verifiedMode && allCampaigns.length === 0 && (
          <div className="prod-empty-note">
            旧 verified 层当前为空（人工核验尚未开始）。
            <a className="banner-link" href={currentPath()}>
              返回默认 Research 数据源
            </a>
          </div>
        )}

        {/* ───────── 钻取区：首页不铺开数据库级内容，但能力全部保留 ─────────
            逐年 Panorama / 单年 Timeline / Current Time Lens / Historical Similar Phase /
            Calendar Lens / 数据来源 一律改为**默认收起的钻取入口**，不删除、不弱化。 */}
        <section className="drill-block" aria-label="研究明细与导航（钻取入口）">
          <p className="drill-hint">
            以下为研究明细与导航入口，默认收起 —— 首页只保留上面的季节性地图；点开即用，能力不变。
          </p>

          {/* ★★ 方向查询（ThreeC 1.2 · Usage-Driven）：**唯一的用户驱动入口**。
              两次真实使用测试暴露：全库只有 5 个当前对象、历史有 52 个 Campaign，
              用户关心的方向大概率不在这 5 个里 —— 因此必须先让用户能自己问。
              语义边界：这是**查找**，不是结构对应（命中主题名 ≠ Structural Correspondence）。 */}
          {!verifiedMode && (
            <div id={DIRECTION_LOOKUP_ID}>
              <DirectionLookupSection
                source={dataSource}
                dataset={currentCandidates}
                onOpenHistoricalCase={(id) => setSelection({ kind: 'campaign', id })}
                seed={draftSeed}
              />
            </div>
          )}

          {/* ⓪ 本期研究快照（Phase 1.3）：月度节奏下用户最关心「跟上期比变了什么」，
              因此放在钻取区第一位。默认只展示 CANONICAL；?snapshot=draft 可预览未签发内容。 */}
          {!verifiedMode && (
            <DrillSection
              title="本期研究快照（Current Snapshot）"
              note="跟上期比变了什么 · 市场环境 / 研究对象 / 历史结构候选"
            >
              <CurrentSnapshotSection
                previewMode={snapshotPreviewEnabled()}
                onOpenHistoricalCase={(id) => setSelection({ kind: 'campaign', id })}
                onOpenObject={focusObject}
              />
            </DrillSection>
          )}

          {!verifiedMode && (
            <DrillSection
              title="逐年历史全景（Historical Panorama）"
              note="一年一行 · 2015–2025 · 完整生命周期分段"
            >
              <div className="drill-yearbar">
                <YearSwitch
                  year={year}
                  setYear={setYear}
                  availableYears={availableYears}
                />
              </div>
              <HistoricalPanorama
                dataSource={dataSource}
                today={today}
                year={year}
                selection={selection}
                onSelect={setSelection}
              />
            </DrillSection>
          )}

          <DrillSection title="单年明细 Timeline" note={`${year} 年 · 规律窗口 / 冲突 / Peak Window`}>
            <div className="drill-yearbar">
              <YearSwitch year={year} setYear={setYear} availableYears={availableYears} />
            </div>
            <Timeline
              year={year}
              today={today}
              selection={selection}
              onSelect={setSelection}
              campaigns={yearData.campaigns}
              researchEvents={yearData.researchEvents}
              sourceKind={dataSource.kind}
            />
          </DrillSection>

          {/* ② 当前时间研究导航：A. A股整体环境 / B. 当前 Theme · Theme Cycle / C. Research Attention。
              与 Timeline 共用 selection（entryId 定位展示实例，campaign_id 打开完整案例）。 */}
          <DrillSection
            title="当前时间研究导航（Current Time Lens）"
            note="A股整体环境 / Theme Cycle / Research Attention"
            id="drill-current-time-lens"
          >
            <CurrentTimeLens
              dataSource={dataSource}
              today={today}
              selection={selection}
              onSelect={setSelection}
              onOpenHistoricalCase={(sel, ctx) => {
                setAnalogyContext(ctx);
                setSelection(sel);
              }}
              currentCandidates={currentCandidates}
              focusCandidateId={focusCandidateId}
            />
          </DrillSection>

          {/* ③ 历史相似阶段（生命周期相似检索）：参照 = 当前选中对象 / 研究覆盖内最新案例。
              与 ④ 历史同期（日历同期）并存，两者不可互相替代。 */}
          <DrillSection title="历史相似阶段（Lifecycle Lens）" note="生命周期相似检索">
            <HistoricalSimilarPhase
              dataSource={dataSource}
              selection={selection}
              onSelect={setSelection}
            />
          </DrillSection>

          {/* ④ 历史同期（日历同期）：主题级；一行 = 一个主主题。保留既有能力，重新定位为 Calendar Lens。 */}
          <DrillSection title="历史同期（Calendar Lens）" note="日历同期 · 主题级">
            <SamePeriodView
              dataSource={dataSource}
              today={today}
              selection={selection}
              onSelect={setSelection}
            />
          </DrillSection>

          {/* 全部主题索引：含**未形成年内季节性窗口**的主题（首页地图上不展示，但对象可查）
              ★ 随当前粒度走 —— 口径与上面的地图保持一致，避免「地图按主题材、索引按大主题」的错位 */}
          <DrillSection
            title={`全部${granularityNoun(granularity)}索引（含无季节性窗口的主题）`}
            note={`${allThemeRows.length} 个${granularityNoun(granularity)} · 数据库级入口`}
          >
            <ul className="theme-index">
              {allThemeRows.map((r) => (
                <li key={themeKey(r)}>
                  <button className="theme-index-btn" onClick={() => setOpenTheme(themeKey(r))}>
                    <span className="ti-name">{r.label}</span>
                    <span className="ti-meta">
                      {r.objects.length} 个对象 · {r.campaignCount} Campaign /{' '}
                      {r.candidateCount} RC
                      {r.windows.length === 0 ? ' · 无年内季节性窗口' : ''}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </DrillSection>

          {/* 数据来源说明（原首页横幅，改为钻取项）：默认消费 canonical Research export，非运行时生成 */}
          <DrillSection title="数据来源" note="Research canonical export · 构建溯源">
            {!verifiedMode && (
              <div className="preview-banner research-banner" role="status">
                <strong>Research 数据源</strong>
                <span>
                  默认消费 Cycle-Research canonical export（52 Campaign +{' '}
                  27 Research Candidate），commit{' '}
                  {timelineExportData.source_commit.slice(0, 7)}；研究对象含 PROVISIONAL /
                  CONFLICT，<strong>非正式历史事实</strong>，仅供研究浏览。
                </span>
                <a className="banner-link" href={`${currentPath()}?verified=1`}>
                  查看旧 verified 层（当前为空）
                </a>
              </div>
            )}
            {/* 示例候选 fixture 横幅：绝不冒充真实研究数据 */}
            {candidatesExample && (
              <div className="preview-banner fixture-banner" role="status">
                <strong>示例 Current Candidate fixture</strong>
                <span>
                  当前展示的是<strong>协议示例数据</strong>（
                  <code>research/current/fixtures/example_candidates.json</code>
                  ），用于验证 Temporal Firewall / 阶段推断 / 相似度链路；不是任何真实研究对象，
                  不构成投资依据。
                </span>
                <a className="banner-link" href={currentPath()}>
                  返回真实数据集
                </a>
              </div>
            )}
          </DrillSection>
        </section>
      </main>

      {/* Macro Theme 附页（drill-down）：按年份列出该主题下的历史对象 → 可进入 CampaignDetail */}
      {openThemeRow && (
        <MacroThemeSheet
          row={openThemeRow}
          onClose={() => setOpenTheme(null)}
          onOpenCampaign={(id, y) => {
            setYear(y);
            setSelection({ kind: 'campaign', id });
          }}
        />
      )}

      {selectedRule && (
        <RuleDetail
          rule={selectedRule}
          today={today}
          onOpenCampaign={(id) => setSelection({ kind: 'campaign', id })}
          onClose={() => setSelection(null)}
        />
      )}
      {selectedCampaign && (
        <CampaignDetail
          campaign={selectedCampaign}
          onOpenRule={(id) => setSelection({ kind: 'rule', id })}
          onClose={() => {
            // 关闭 Case 后回到原上下文（Current Candidate / Structural Analogy 状态由组件自身保持）
            setAnalogyContext(null);
            setSelection(null);
          }}
          analogyContext={analogyContext}
          onBackToAnalogy={() => {
            // 返回 Structural Analogy：关闭 Case，保留 Current Candidate 展开态
            setAnalogyContext(null);
            setSelection(null);
          }}
        />
      )}

      {/* Build Provenance（Gate D7）：线上 build ↔ Research artifact 版本对应关系。
          溯源信息，**不是**质量 / 可信度指标；字段缺失显示「未标注」，不猜测。 */}
      <BuildProvenanceFooter />
    </>
  );
}

/** 钻取项：默认收起；能力保留，只是不在首页铺开。 */
function DrillSection({
  title,
  note,
  children,
  id,
}: {
  title: string;
  note?: string;
  children: ReactNode;
  /** 供「从别处跳到本区块」使用（原生 `<details>`，用 id 定位后展开） */
  id?: string;
}) {
  return (
    <details className="drill-item" id={id}>
      <summary className="drill-summary">
        <span className="drill-title">{title}</span>
        {note ? <span className="drill-note">{note}</span> : null}
      </summary>
      <div className="drill-body">{children}</div>
    </details>
  );
}

/** 年份切换（原首页顶部控件，随逐年视图一并下移到钻取区） */
function YearSwitch({
  year,
  setYear,
  availableYears,
}: {
  year: number;
  setYear: (fn: (y: number) => number) => void;
  availableYears: number[];
}) {
  return (
    <>
      <span className="year-switch">
        <button onClick={() => setYear((y) => y - 1)} aria-label="上一年">
          ‹
        </button>
        <span className="year-label">{year}</span>
        <button onClick={() => setYear((y) => y + 1)} aria-label="下一年">
          ›
        </button>
      </span>
      {/* 数据源可展示年份（不硬编码：来自 TimelineDataSource.years()） */}
      {availableYears.length > 0 && (
        <span className="year-chips">
          {availableYears.map((y) => (
            <button
              key={y}
              className={`year-chip${y === year ? ' on' : ''}`}
              onClick={() => setYear(() => y)}
            >
              {y}
            </button>
          ))}
        </span>
      )}
    </>
  );
}

/** 页脚构建溯源：回答「这个 build 消费了哪一版 Research 结论」。 */
function BuildProvenanceFooter() {
  const p = useMemo(() => buildProvenance(), []);
  const na = PROVENANCE_NOT_AVAILABLE;
  const counts = p.exportObjectCounts;
  return (
    <footer className="build-provenance" role="contentinfo">
      <details>
        <summary>
          Build Provenance · v{p.productVersion ?? na} · Research export{' '}
          {p.exportVersion ?? na}
        </summary>
        <dl>
          <dt>Product version</dt>
          <dd>{p.productVersion ?? na}</dd>
          <dt>构建 commit</dt>
          <dd>
            {p.gitCommitShort ?? na}
            {p.gitCommit ? <span className="phase-text">（{p.gitCommit}）</span> : null}
          </dd>
          <dt>构建时间</dt>
          <dd>{p.buildTime ?? na}</dd>
          <dt>Research export 版本</dt>
          <dd>{p.exportVersion ?? na}</dd>
          <dt>Research export source commit</dt>
          <dd>
            {p.exportSourceCommitShort ?? na}
            {p.exportSourceCommit ? (
              <span className="phase-text">（{p.exportSourceCommit}）</span>
            ) : null}
          </dd>
          <dt>Research export 生成时间</dt>
          <dd>{p.exportGeneratedAt ?? na}</dd>
          <dt>研究对象数</dt>
          <dd>
            {counts
              ? `${counts.campaigns} Campaign + ${counts.researchCandidates} Research Candidate = ${
                  counts.campaigns + counts.researchCandidates
                }`
              : na}
          </dd>
          <dt>Structural Analogy</dt>
          <dd>
            artifact {p.saArtifactVersion ?? na}
            {p.saRuleSetVersion ? <span className="phase-text">（{p.saRuleSetVersion}）</span> : null}
          </dd>
          <dt>Time Observation</dt>
          <dd>
            artifact {p.toArtifactVersion ?? na}
            <span className="phase-text">（文件名 v0_2 / 内部版本见左）</span>
          </dd>
        </dl>
        <p className="build-provenance-note">
          本区块是**溯源信息**，用于确认线上 build 与 Research artifact 的对应关系；
          它不是可信度、完整度或质量评分，也不影响任何研究结论的语义。
        </p>
      </details>
    </footer>
  );
}
