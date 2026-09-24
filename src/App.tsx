import { useMemo, useState } from 'react';
import { CampaignDetail } from './components/CampaignDetail/CampaignDetail';
import { CurrentTimeLens } from './components/CurrentTimeLens/CurrentTimeLens';
import { HistoricalPanorama } from './components/HistoricalPanorama/HistoricalPanorama';
import { HistoricalSimilarPhase } from './components/HistoricalSimilarPhase/HistoricalSimilarPhase';
import { RuleDetail } from './components/RuleDetail/RuleDetail';
import { SamePeriodView } from './components/SamePeriodView/SamePeriodView';
import { Timeline, type Selection } from './components/Timeline/Timeline';
import { allCampaigns, campaignById, ruleById } from './data';
import { researchTimelineSource, verifiedTimelineSource } from './data/timeline/timelineAdapter';
import { timelineExportData } from './data/timeline/timelinePreview';
import type { TimelineCampaign } from './data/timeline/timelineTypes';
import type { HistoricalCaseAnalogyContext } from './data/timeline/historicalCase';
import { parseCurrentCandidateDataset } from './data/timeline/currentCandidate';
import type { CurrentCandidateDataset } from './data/timeline/currentCandidate';
import currentCandidateFixtureJson from '@current/fixtures/example_candidates.json';
import { buildProvenance, PROVENANCE_NOT_AVAILABLE } from './data/buildProvenance';
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
        <p className="app-subtitle">历史规律 × 题材轮动 × 事件节奏 × 提前观察</p>
        <div className="app-today">
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
                  onClick={() => setYear(y)}
                >
                  {y}
                </button>
              ))}
            </span>
          )}
        </div>
      </header>

      {/* 数据来源说明（Product 1.1）：默认消费 canonical Research export，非运行时生成 */}
      {!verifiedMode && (
        <div className="preview-banner research-banner" role="status">
          <strong>Research 数据源</strong>
          <span>
            默认消费 Cycle-Research canonical export（52 Campaign +{' '}
            27 Research Candidate），commit {timelineExportData.source_commit.slice(0, 7)}；
            研究对象含 PROVISIONAL / CONFLICT，<strong>非正式历史事实</strong>，仅供研究浏览。
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
            当前展示的是<strong>协议示例数据</strong>（<code>research/current/fixtures/example_candidates.json</code>），
            用于验证 Temporal Firewall / 阶段推断 / 相似度链路；不是任何真实研究对象，不构成投资依据。
          </span>
          <a className="banner-link" href={window.location.pathname}>
            返回真实数据集
          </a>
        </div>
      )}

      <main className="app-main">
        {/* IA（V2.0）：① Timeline（第一视觉）→ ② 当前时间研究导航（Current Time Lens v2）
            → ③ 历史相似阶段（Lifecycle Lens）→ ④ 历史同期（Calendar Lens）。
            视觉优先级：Timeline > Current Lens > Similar Phase；Lens 是研究导航层，但不压过 Timeline。 */}
        {/* ★ 第一视觉（Product 1.1）：Historical Opportunity Panorama ——
            一眼看到历史上全年时间维度（Jan–Dec）的题材 / Campaign 炒作分布。
            数据与单年 Timeline 同源（同一 Adapter / 同一 lifecycle），不做第二套研究逻辑。
            verified 回退模式下不渲染（该层当前为空，全景无意义）。 */}
        {!verifiedMode && (
          <HistoricalPanorama
            dataSource={dataSource}
            today={today}
            year={year}
            selection={selection}
            onSelect={setSelection}
          />
        )}
        {/* 单年明细 Timeline（原第一视觉，现降为钻取层）：规律窗口 / 冲突标记 / Peak Window 等
            细粒度交互仍在此层，放大某一年的结构。 */}
        <Timeline
          year={year}
          today={today}
          selection={selection}
          onSelect={setSelection}
          campaigns={yearData.campaigns}
          researchEvents={yearData.researchEvents}
          sourceKind={dataSource.kind}
        />
        {/* ② 当前时间研究导航：A. A股整体环境 / B. 当前 Theme · Theme Cycle / C. Research Attention。
            与 Timeline 共用 selection（entryId 定位展示实例，campaign_id 打开完整案例）。 */}
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
        />
        {/* ③ 历史相似阶段（生命周期相似检索）：参照 = 当前选中对象 / 研究覆盖内最新案例。
            与 ④ 历史同期（日历同期）并存，两者不可互相替代。 */}
        <HistoricalSimilarPhase
          dataSource={dataSource}
          selection={selection}
          onSelect={setSelection}
        />
        {/* ④ 历史同期（日历同期）：主题级；一行 = 一个主主题。保留既有能力，重新定位为 Calendar Lens。 */}
        <SamePeriodView
          dataSource={dataSource}
          today={today}
          selection={selection}
          onSelect={setSelection}
        />
        {/* verified 模式且 verified 层为空：提示回到默认 Research 数据源 */}
        {verifiedMode && allCampaigns.length === 0 && (
          <div className="prod-empty-note">
            旧 verified 层当前为空（人工核验尚未开始）。
            <a className="banner-link" href={window.location.pathname}>
              返回默认 Research 数据源
            </a>
          </div>
        )}
      </main>

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
