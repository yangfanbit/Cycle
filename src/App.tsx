import { useCallback, useMemo, useState, type ReactNode } from 'react';
import { CampaignDetail } from './components/CampaignDetail/CampaignDetail';
import { CurrentSnapshotSection } from './components/CurrentSnapshot/CurrentSnapshotSection';
import { DirectionLookupSection } from './components/DirectionLookup/DirectionLookupSection';
import { CurrentTimeLens } from './components/CurrentTimeLens/CurrentTimeLens';
import { HistoricalPanorama } from './components/HistoricalPanorama/HistoricalPanorama';
import { HistoricalSimilarPhase } from './components/HistoricalSimilarPhase/HistoricalSimilarPhase';
import { MacroThemeSheet } from './components/MacroThemeSheet/MacroThemeSheet';
import { RuleDetail } from './components/RuleDetail/RuleDetail';
import { SamePeriodView } from './components/SamePeriodView/SamePeriodView';
import { SeasonalMap } from './components/SeasonalMap/SeasonalMap';
import { Timeline, type Selection } from './components/Timeline/Timeline';
import { allCampaigns, campaignById, ruleById } from './data';
import { researchTimelineSource, verifiedTimelineSource } from './data/timeline/timelineAdapter';
import { timelineExportData } from './data/timeline/timelinePreview';
import type { TimelineCampaign } from './data/timeline/timelineTypes';
import {
  seasonalMapRows,
  seasonalMapSummary,
  themeAnnualRowsOf,
  themeKey,
} from './data/timeline/themeAnnualWindow';
import type { HistoricalCaseAnalogyContext } from './data/timeline/historicalCase';
import { parseCurrentCandidateDataset } from './data/timeline/currentCandidate';
import type { CurrentCandidateDataset } from './data/timeline/currentCandidate';
import currentCandidateFixtureJson from '@current/fixtures/example_candidates.json';
import { buildProvenance, PROVENANCE_NOT_AVAILABLE } from './data/buildProvenance';
import { CurrentMarketStrip } from './components/CurrentMarket/CurrentMarketStrip';
import { marketTodayISO } from './utils';

/**
 * ?verified=1 → 旧 verified 生产层（`data/verified`，当前为空，保留为显式回退路径）。
 *
 * Product 1.1 起**首页默认消费 canonical Research export**
 * （`exports/timeline_export_v1.json`），使已 Research 的 Historical Universe
 * 正式进入第一视觉；`?verified=1` 仅用于对照旧生产层。
 * 不做运行时网络访问（静态 PWA 不变）。
 */
function verifiedEnabled(): boolean {
  return new URLSearchParams(window.location.search).get('verified') === '1';
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
  return new URLSearchParams(window.location.search).get('candidates') === 'example';
}

/**
 * ?snapshot=draft 放宽 Market Snapshot 的展示门禁（Phase 1.3）。
 *
 * 默认**只展示已签发（`CANONICAL`）**的快照 —— 防止未经人工审核的研究被当成结论。
 * 本开关仅用于预览未签发内容，页面会**常驻醒目徽标**标明「未签发 · 仅供预览」。
 */
function snapshotPreviewEnabled(): boolean {
  return new URLSearchParams(window.location.search).get('snapshot') === 'draft';
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
  const availableYears = useMemo(() => dataSource.years(), [dataSource]);

  // Current Candidate 数据集（Phase 7）：canonical（默认空集）或示例 fixture（显式开启）
  const candidatesExample = useMemo(() => exampleCandidatesEnabled(), []);
  const currentCandidates = useMemo<CurrentCandidateDataset | null>(
    () =>
      candidatesExample ? parseCurrentCandidateDataset(currentCandidateFixtureJson).dataset : null,
    [candidatesExample],
  );

  // ★ 首页第一视觉（Product 1.1 第二轮）：Macro Theme × 年内时间窗口聚合。
  //   一主题一行，同主题的多次历史出现合并观察；不是一对象一行，也不是一年一行。
  const allThemeRows = useMemo(() => themeAnnualRowsOf(dataSource), [dataSource]);
  const mapRows = useMemo(() => seasonalMapRows(allThemeRows), [allThemeRows]);
  const mapSummary = useMemo(() => seasonalMapSummary(mapRows), [mapRows]);
  const [openTheme, setOpenTheme] = useState<string | null>(null);
  const openThemeRow = useMemo(
    () => allThemeRows.find((r) => themeKey(r) === openTheme) ?? null,
    [allThemeRows, openTheme],
  );

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
          />
        )}

        {/* 一句数据语义说明（首页唯一的数据口径声明） */}
        {!verifiedMode && mapRows.length > 0 && (
          <p className="seasonal-note">
            横轴 1–12 月、每行一个大主题；条形为该主题历史<strong>主要炒作</strong>
            在年内的窗口（长周期仅标起始位置）；「历史 N 次 / 覆盖 N 个年份」是<strong>计数事实</strong>
            ，不是概率、胜率或预测。共 {mapSummary.themeCount} 个大主题 /{' '}
            {mapSummary.objectCount} 个研究对象
            {mapSummary.yearFrom !== null && mapSummary.yearTo !== null
              ? `（${mapSummary.yearFrom}–${mapSummary.yearTo}）`
              : ''}
            ，来自 Cycle-Research canonical export，研究对象含 PROVISIONAL / CONFLICT，
            <strong>非正式历史事实</strong>。
          </p>
        )}

        {/* ★ 覆盖边界（ThreeC 1.2 · Usage-Driven）
            用户拿一个真实方向来问（例如「文化传媒」）时，第一件要知道的是「它在不在覆盖内」。
            实测：历史 52 个 Campaign / 44 个主题名里，**传媒 / 文化 / 娱乐 / 教育 一个都没有** ——
            与其让用户查半天查不到，不如直接说清楚边界。
            ★ 本声明是**人工维护**的（canonical export 已冻结，不得改其 provenance）；
              覆盖范围变化时必须同步更新此处。 */}
        {!verifiedMode && mapRows.length > 0 && (
          <p className="seasonal-scope">
            <strong>覆盖边界</strong>：历史研究集中于<strong>硬科技 · 高端制造 · 消费 · 资源 · 金融</strong>
            等方向（汽车 / 电子 / 半导体 / 电力设备 / 医药 / 资源 / 金融 / 消费 / 军工 / 地产 等）。
            <strong>不包含</strong>传媒 / 文化 / 娱乐 / 教育 等方向 —— 这些方向在历史研究中
            <strong>没有对应对象</strong>，因此本工具<strong>无法</strong>回答关于它们的「历史结构对应」问题。
            <span className="seasonal-scope-note">
              （覆盖范围由 Research 决定；扩边属研究轮次，不在 Product 侧自行推断。）
            </span>
          </p>
        )}

        {/* verified 模式且 verified 层为空：提示回到默认 Research 数据源 */}
        {verifiedMode && allCampaigns.length === 0 && (
          <div className="prod-empty-note">
            旧 verified 层当前为空（人工核验尚未开始）。
            <a className="banner-link" href={window.location.pathname}>
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
            <DirectionLookupSection
              source={dataSource}
              dataset={currentCandidates}
              onOpenHistoricalCase={(id) => setSelection({ kind: 'campaign', id })}
            />
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

          {/* 全部大主题索引：含**未形成年内季节性窗口**的主题（首页地图上不展示，但对象可查） */}
          <DrillSection
            title="全部大主题索引（含无季节性窗口的主题）"
            note={`${allThemeRows.length} 个主题 · 数据库级入口`}
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
                <a className="banner-link" href={`${window.location.pathname}?verified=1`}>
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
                <a className="banner-link" href={window.location.pathname}>
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
