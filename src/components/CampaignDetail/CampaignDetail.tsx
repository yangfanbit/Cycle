import { useEffect, useMemo, useState } from 'react';
import { allCampaignSecurities, ruleById, themeById, themesOfCampaign } from '../../data';
import type { HistoricalCampaign } from '../../models';
import { campaignDrivers } from '../../data/timeline/timelineAdapter';
import {
  ATTRIBUTION_PHASE_LABEL,
  ATTRIBUTION_QUESTION_LABEL,
  EVIDENCE_CATEGORY_LABEL,
  LIFECYCLE_STAGE_LABEL,
  MAPPING_STATUS_LABEL,
  PHASE_SIGNAL_CLARIFICATION,
  evidenceCategoriesOf,
  historicalCaseOf,
  historicalEvidenceTimelineOf,
  loadMechanismDrivers,
  withMechanismDrivers,
  type HistoricalCaseAnalogyContext,
  type HistoricalCaseView,
  type HistoricalEvidenceTimeline,
  type MechanismDriverView,
} from '../../data/timeline/historicalCase';
import type { ExportConflictV1, ExportDriversV1, TimelineCampaign } from '../../data/timeline/timelineTypes';
import { diffDays } from '../../utils';
import {
  conflictLine,
  DATA_STATUS_LABEL,
  EVENT_TYPE_LABEL,
  LIFECYCLE_LABEL,
  RESULT_LABEL,
  ROLE_LABEL,
  RULE_STATUS_LABEL,
  SIGNAL_CONFIDENCE_LABEL,
  SIGNAL_TYPE_LABEL,
  STRENGTH_LABEL,
} from '../labels';

interface CampaignDetailProps {
  /** 生产 HistoricalCampaign（verified）或 Timeline 预览 Campaign（Research Preview） */
  campaign: HistoricalCampaign | TimelineCampaign;
  onOpenRule: (ruleId: string) => void;
  onClose: () => void;
  /** 从 Structural Analogy 进入时携带的轻量上下文（**原样消费，不重算**）。 */
  analogyContext?: HistoricalCaseAnalogyContext | null;
  /** 返回 Structural Analogy（保持 Current Candidate 上下文）。 */
  onBackToAnalogy?: () => void;
}

interface CampaignDetailModel {
  title: string;
  seasonId: string;
  start: string;
  end: string;
  peak: string | null;
  crossYear: boolean;
  ruleId: string;
  kind: 'campaign' | 'candidate';
  openEnded: boolean;
  themes: { name: string; role?: string }[];
  /** Theme Cycle（research metadata 透传；缺失 null —— 不推断） */
  themeCycleId: string | null;
  /** Macro Theme（由 theme_type ∈ {industry, sector} 的题材透传；缺失 null） */
  macroTheme: string | null;
  securities: { name: string; ticker?: string; role?: string }[];
  events: { name: string; date: string; event_type: string; role?: string | null }[];
  signals: { type: string; date: string; confidence?: string }[];
  /** Research V1.7 驱动因素归因（仅 Research 导出数据源提供；生产 verified 无） */
  drivers?: ExportDriversV1;
  description?: string;
  sourceText: string;
  status: 'verified' | 'provisional' | 'preview' | 'conflict';
  conflicts: ExportConflictV1[] | undefined;
  phases: { phase: keyof typeof LIFECYCLE_LABEL; start: string; end: string }[];
  earlySignal: { start: string; end: string; label?: string } | null;
  strength?: HistoricalCampaign['strength'];
  result?: HistoricalCampaign['result'];
  production: boolean;
  campaignId: string;
}

/** 归一化详情视图模型：生产 / 预览两种输入共用同一渲染 */
function normalize(c: HistoricalCampaign | TimelineCampaign): CampaignDetailModel {
  if ('start_date' in c) {
    // 生产 verified 层：题材 / 龙头关系从 barrel 查询
    const themes = themesOfCampaign(c.campaign_id)
      .map((ct) => {
        const theme = themeById.get(ct.theme_id);
        return theme ? { name: theme.name, role: ct.role } : null;
      })
      .filter((t): t is NonNullable<typeof t> => t !== null);
    const mainTheme = themes.find((t) => t.role === 'main');
    const securities = allCampaignSecurities
      .filter((cs) => cs.campaign_id === c.campaign_id)
      .map((cs) => ({ name: cs.security_id, role: cs.role as string | undefined }));
    return {
      title: mainTheme ? mainTheme.name : c.season_id,
      seasonId: c.season_id,
      start: c.start_date,
      end: c.end_date,
      peak: c.peak_date ?? null,
      crossYear: c.cross_year,
      ruleId: c.rule_id,
      kind: 'campaign',
      openEnded: false,
      themes,
      themeCycleId: null,
      macroTheme: null,
      securities,
      events: [],
      signals: [],
      description: c.description,
      sourceText: `data/verified（已人工核验 L2）`,
      status: 'verified' as const,
      conflicts: undefined,
      phases: [],
      earlySignal: null,
      strength: c.strength,
      result: c.result,
      production: true,
      campaignId: c.campaign_id,
    };
  }
  // Timeline（预览 / provisional / conflict；含 Research Candidate）
  return {
    title: c.title,
    seasonId: c.season_id,
    start: c.start,
    end: c.end,
    peak: c.peak ?? null,
    crossYear: c.cross_year,
    ruleId: c.rule_id,
    kind: c.kind,
    openEnded: c.openEnded ?? false,
    themes: c.themes,
    themeCycleId: c.theme_cycle_id ?? null,
    macroTheme:
      c.themes.find((t) => t.theme_type === 'industry' || t.theme_type === 'sector')?.name ?? null,
    securities: c.securities,
    events: c.events,
    signals: c.signals,
    drivers: c.drivers,
    description: c.description,
    sourceText: c.sourceNote ?? '—',
    status: c.status,
    conflicts: c.conflicts,
    phases: c.phases,
    earlySignal: c.early_signal ?? null,
    strength: undefined,
    result: undefined,
    production: false,
    campaignId: c.campaign_id,
  };
}

export function CampaignDetail({
  campaign,
  onOpenRule,
  onClose,
  analogyContext = null,
  onBackToAnalogy,
}: CampaignDetailProps) {
  const m = normalize(campaign);
  const rule = ruleById.get(m.ruleId);

  // Historical Case 基础视图（**同步纯映射**，SSR 与首帧即可用）
  const caseBase = useMemo<HistoricalCaseView | null>(
    () => (m.production || !('phases' in campaign) ? null : historicalCaseOf(campaign as TimelineCampaign)),
    [campaign, m.production],
  );

  // 驱动机制：**按需加载**（独立 chunk）；加载中为 null → 显示「正在加载…」
  const [mechanismDrivers, setMechanismDrivers] = useState<MechanismDriverView[] | null>(null);
  useEffect(() => {
    if (!caseBase) return;
    let alive = true;
    loadMechanismDrivers()
      .then((table) => {
        if (alive) setMechanismDrivers(withMechanismDrivers(caseBase, table).mechanismDrivers ?? []);
      })
      .catch(() => {
        if (alive) setMechanismDrivers([]);
      });
    return () => {
      alive = false;
    };
  }, [caseBase]);

  const evidenceCategories = caseBase?.evidenceCategories ?? evidenceCategoriesOf(m.events);

  // ★ Rework v0.1：统一的「历史演化证据」时间线（**每个事件只出现一次**）
  const evidenceTimeline: HistoricalEvidenceTimeline | null = useMemo(
    () => (m.production || !('phases' in campaign) ? null : historicalEvidenceTimelineOf(campaign as TimelineCampaign)),
    [campaign, m.production],
  );
  const duration = diffDays(m.start, m.end) + 1;
  // 驱动因素四问（Research V1.7 人工归因优先；缺失时基于研究事件时间归组；
  // 无数据组 → "暂无可靠归因"，不编造）
  const drivers = campaignDrivers({
    start: m.start,
    peak: m.peak,
    end: m.end,
    openEnded: m.openEnded,
    events: m.events,
    drivers: m.drivers,
  });
  const driverRows: { q: string; tags: string[] }[] = [
    { q: '为什么启动？', tags: drivers.start },
    { q: '为什么加速？', tags: drivers.accelerate },
    { q: '为什么转折？', tags: drivers.turn },
    { q: '为什么结束？', tags: drivers.end },
  ];

  return (
    <aside className="detail-panel" role="dialog" aria-label="完整历史案例">
      <button className="detail-close" onClick={onClose} aria-label="关闭">
        ×
      </button>
      <h2>
        {m.kind === 'candidate' ? '研究候选 · ' : '历史行情 · '}
        {m.seasonId}
      </h2>
      <div>
        {m.kind === 'candidate' && !m.production && (
          <span className="rc-badge" title="Research Candidate：研究候选，非正式 Historical Campaign">
            Research Candidate
          </span>
        )}
        {m.crossYear && <span className="badge badge-cross">跨年行情</span>}
        {m.production ? (
          <>
            <span className="badge badge-plain">强度 {STRENGTH_LABEL[m.strength!]}</span>
            <span className="badge badge-plain">结果 {RESULT_LABEL[m.result!]}</span>
          </>
        ) : (
          <span className={`st-badge st-${m.status}`}>{DATA_STATUS_LABEL[m.status]}</span>
        )}
      </div>

      {!m.production && (
        <div className="preview-note">
          <strong>{m.kind === 'candidate' ? 'Research Candidate（研究候选）' : 'Research Preview'}</strong>
          <p>
            {m.kind === 'candidate'
              ? '本条为 Cycle-Research 研究候选（未达正式 Campaign 门槛），与 Historical Campaign 并列展示；'
              : '本条为 Cycle-Research 研究预览数据，非正式 Verified 数据；'}
            {m.status === 'conflict'
              ? '且研究结论存在分歧，仅供模式探索，不得视为历史事实。'
              : '尚未完成人工最终核验，仅供界面与历史模式探索。'}
          </p>
        </div>
      )}

      {/* ---------- Structural Analogy 上下文（从 SA 进入时；**不重算**） ---------- */}
      {analogyContext && (
        <div className="hcx-sa" role="note">
          <div className="hcx-sa-head">
            <strong>为什么当前对象与这个历史案例对应</strong>
            <span className="hcx-sa-status">{analogyContext.structuralStatus}</span>
            {analogyContext.strictStructuralSupported && (
              <span className="hcx-sa-strict">严格口径</span>
            )}
          </div>
          <p className="hcx-sa-from">
            当前对象：{analogyContext.candidateName ?? analogyContext.candidateId}
            <span className="phase-text">
              （{analogyContext.themeRelation.label} · 背景信息，不参与结构判定）
            </span>
          </p>
          <ul className="hcx-sa-dims">
            {analogyContext.dimensions.map((d) => (
              <li key={d.key}>
                <span className="hcx-sa-dim-label">{d.label}</span>
                <span className="hcx-sa-dim-status">{d.statusLabel}</span>
              </li>
            ))}
          </ul>
          {analogyContext.whySimilar.length > 0 && (
            <div className="hcx-sa-block">
              <span className="phase-text">为什么对应</span>
              <ul>
                {analogyContext.whySimilar.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
          )}
          {analogyContext.whyNotSimilar.length > 0 && (
            <div className="hcx-sa-block">
              <span className="phase-text">哪里不同</span>
              <ul>
                {analogyContext.whyNotSimilar.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
          )}
          {analogyContext.unknownDimensionLabels.length > 0 && (
            <p className="phase-text">
              未知维度：{analogyContext.unknownDimensionLabels.join('、')}
              —— 资料不足，**不等于**「不存在」或「不对应」。
            </p>
          )}
          <p className="phase-text">
            快照 {analogyContext.snapshotDate} · 规则版本 {analogyContext.ruleSetVersion}
            （本区块原样消费 Research 结果，产品不重新计算）
          </p>
          {onBackToAnalogy && (
            <button className="hcx-back" type="button" onClick={onBackToAnalogy}>
              ← 返回 Structural Analogy（保持当前候选上下文）
            </button>
          )}
        </div>
      )}

      <dl className="kv">
        <dt>历史对象类型</dt>
        <dd>
          {m.kind === 'candidate' ? 'Research Candidate（研究候选，非 Campaign）' : 'Historical Campaign'}
        </dd>

        <dt>Macro Theme</dt>
        <dd>{m.macroTheme ?? <span className="empty-note">未标注（不推断）</span>}</dd>

        <dt>Theme Cycle</dt>
        <dd>{m.themeCycleId ?? <span className="empty-note">未标注（不推断）</span>}</dd>

        <dt>行情</dt>
        <dd>{m.title}</dd>

        <dt>完整日期</dt>
        <dd>
          {m.start} → {m.end}
          {m.conflicts && m.conflicts.length > 0 ? (
            <span className="phase-text">
              （日期存在研究分歧，A / B 候选见下方；本区间为 DB Candidate 口径）
            </span>
          ) : m.openEnded ? (
            <span className="phase-text">（候选观察中，结束日期未记录，end 为年末近似）</span>
          ) : (
            <span className="phase-text">（共 {duration} 天）</span>
          )}
        </dd>

        <dt>峰值</dt>
        <dd>{m.peak ?? '未核验（合法空状态）'}</dd>

        <dt>所属规律</dt>
        <dd>
          {rule ? (
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                onOpenRule(rule.rule_id);
              }}
            >
              {rule.name}
            </a>
          ) : (
            m.ruleId
          )}
          {rule && <span className="phase-text">（{RULE_STATUS_LABEL[rule.status]}）</span>}
        </dd>

        {m.earlySignal && (
          <>
            <dt>早期信号</dt>
            <dd>
              {m.earlySignal.start} → {m.earlySignal.end}
              {m.earlySignal.label ? `（${m.earlySignal.label}）` : ''}
              <span className="phase-text">（前置观察，非正式行情起点）</span>
            </dd>
          </>
        )}

        {m.phases.length > 0 && (
          <>
            <dt>生命周期</dt>
            <dd>
              {m.phases
                .map((p) => `${LIFECYCLE_LABEL[p.phase]} ${p.start.slice(5)}→${p.end.slice(5)}`)
                .join('；')}
            </dd>
          </>
        )}

        <dt>题材</dt>
        <dd>
          {m.themes.length === 0 && <span className="empty-note">题材信息待补充</span>}
          {m.themes.map((t) => (
            <span className="tag" key={t.name}>
              {t.name}
              {t.role ? `（${ROLE_LABEL[t.role] ?? t.role}）` : ''}
            </span>
          ))}
        </dd>

        <dt>代表股票</dt>
        <dd>
          {m.securities.length === 0 ? (
            <span className="empty-note">
              {m.production ? '暂无代表股票记录（待历史数据核实后补充）' : '研究候选龙头（非正式）'}
            </span>
          ) : (
            m.securities.map((s) => (
              <span className="tag" key={`${s.ticker ?? ''}-${s.name}`}>
                {s.name}
                {s.ticker ? `（${s.ticker}）` : ''}
                {s.role ? ` · ${ROLE_LABEL[s.role] ?? s.role}` : ''}
              </span>
            ))
          )}
        </dd>

        {m.conflicts && m.conflicts.length > 0 && (
          <>
            <dt>研究分歧</dt>
            <dd>
              {[...m.conflicts]
                .sort((a, b) => a.field.localeCompare(b.field))
                .map((c) => (
                  <div key={`${c.field}-${c.candidate_a.date}`} className="conflict-line">
                    {conflictLine(c)}
                  </div>
                ))}
              <div className="phase-text">（保留 candidate A / B 双方口径，未自行取舍；非历史事实）</div>
            </dd>
          </>
        )}

        {caseBase && (
          <>
            <dt>驱动机制（Mechanism Driver）</dt>
            <dd>
              {mechanismDrivers === null ? (
                <span className="empty-note">正在加载…</span>
              ) : mechanismDrivers.length === 0 ? (
                <span className="empty-note">
                  未标注可用驱动机制（NOT_AVAILABLE）—— 不代表「没有驱动」，只代表当前研究资料不足以编码。
                </span>
              ) : (
                mechanismDrivers.map((d) => (
                  <span className="tag" key={d.driver} title={MAPPING_STATUS_LABEL[d.mappingStatus]}>
                    {d.driver}
                    <span className="phase-text">（{MAPPING_STATUS_LABEL[d.mappingStatus]}）</span>
                  </span>
                ))
              )}
              <div className="phase-text">
                机制判断（如「政策驱动」），来自 Historical Driver Canonicalization（Research 层），产品不重新推导。
              </div>
            </dd>

            <dt>证据类别（Evidence Category）</dt>
            <dd>
              {evidenceCategories.length === 0 ? (
                <span className="empty-note">无可用事件 → 无法映射证据类别（NOT_AVAILABLE）</span>
              ) : (
                evidenceCategories.map((c) => (
                  <span className="tag" key={c}>
                    {EVIDENCE_CATEGORY_LABEL[c]}
                    <span className="phase-text">（{c}）</span>
                  </span>
                ))
              )}
              <div className="phase-text">
                证据**来源**类别（由事件的 event_type 确定性映射）。
                「证据类别」与「驱动机制」**不是同一维**，不可混用。
              </div>
            </dd>

          </>
        )}

        {/* ---------- ★ 历史演化证据（统一证据视图 · Rework v0.1） ---------- */}
        {evidenceTimeline && (
          <>
            <dt>历史演化证据</dt>
            <dd>
              {!evidenceTimeline.hasEvents ? (
                <span className="empty-note">
                  无关联事件记录（NOT_AVAILABLE）—— 这不代表「当时没有事件」，只代表当前资料未记录。
                </span>
              ) : (
                <>
                  <p className="phase-text hcx-ev-intro">
                    按时间排序，<strong>每个事件只展示一次</strong>；
                    同一行承载 日期 · 生命周期阶段 · 事件类型 · 角色 · 事件名 · 归组阶段。
                    归组阶段表示该事件在案例时间轴上的<strong>位置</strong>，<strong>不代表</strong>因果证明。
                  </p>
                  <ol className="hcx-ev">
                    {evidenceTimeline.rows.map((r) => (
                      <li key={r.key} className="hcx-ev-row">
                        <div className="hcx-ev-line1">
                          <span className="hcx-ev-date">{r.date}</span>
                          <span className={`hcx-ev-stage${r.lifecycleStage === null ? ' is-unknown' : ''}`}>
                            {r.lifecycleStageLabel}
                          </span>
                          <span className="hcx-ev-type">
                            {r.eventType}
                            {r.role ? ` · ${r.role}` : ''}
                          </span>
                          <span className="hcx-ev-attr" title="时间归组位置，非因果证明">
                            {ATTRIBUTION_PHASE_LABEL[r.attributionPhase]}
                          </span>
                        </div>
                        <div className="hcx-ev-name">{r.name}</div>
                      </li>
                    ))}
                  </ol>
                  {evidenceTimeline.hasUnknownStage && (
                    <p className="phase-text hcx-ev-note">
                      「阶段未知」= 该事件日期不落在任何已记录生命周期区间内（UNKNOWN）——
                      <strong>不代表</strong>事件不存在或不重要。
                    </p>
                  )}
                </>
              )}
            </dd>

            {/* ---------- 阶段级研究归因（**不是**重复事件列表） ---------- */}
            <dt>阶段级研究归因</dt>
            <dd>
              <p className="phase-text hcx-ev-intro">
                {evidenceTimeline.attributionSource === 'RESEARCH'
                  ? '来自 Research V1.7 研究归因（原样展示，按阶段归组）。'
                  : 'Research 未提供归因 → 以下为按事件时间窗口的**归组线索**。'}
                <strong>归因是研究归组 / 研究判断，不是单条事件的因果证明。</strong>
              </p>
              <div className="hcx-attr">
                {evidenceTimeline.attribution.map((g) => (
                  <div key={g.phase} className="hcx-attr-row">
                    <span className="hcx-attr-q">{g.question}</span>
                    <span className="hcx-attr-phase">{g.phaseLabel}</span>
                    {g.items.length > 0 ? (
                      <ul className="hcx-attr-items">
                        {g.items.map((t) => (
                          <li key={t} title={t}>
                            {t}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="phase-text">暂无可靠归因</span>
                    )}
                  </div>
                ))}
              </div>
              <p className="phase-text">
                {evidenceTimeline.attributionSource === 'RESEARCH'
                  ? '（来自 Cycle-Research V1.7 研究归因，原样展示；非因果结论，不构成买卖建议。）'
                  : '（基于研究事件的时间归组线索，非因果结论。）'}
              </p>
            </dd>
          </>
        )}

        {m.signals.length > 0 && (
          <>
            <dt>研究信号</dt>
            <dd>
              {m.signals.map((s, i) => (
                <div key={i} className="event-line">
                  <span className="phase-text">{s.date}</span>{' '}
                  {SIGNAL_TYPE_LABEL[s.type] ?? s.type}
                  <span className="phase-text">
                    （置信度 {SIGNAL_CONFIDENCE_LABEL[s.confidence ?? ''] ?? s.confidence ?? '—'}）
                  </span>
                </div>
              ))}
              <div className="phase-text">（研究层「值得观察」信息，不是交易信号）</div>
              <div className="phase-text hcx-phase-signal">{PHASE_SIGNAL_CLARIFICATION}</div>
            </dd>
          </>
        )}

        <dt>备注</dt>
        <dd>{m.description ?? '—'}</dd>

        <dt>信息来源</dt>
        <dd>{m.sourceText || `${m.seasonId} 行情（data/verified）`}</dd>
      </dl>

      <p className="disclaimer">
        历史行情记录用于规律研究，不构成任何买卖建议；strength / result 未经量化验证时记为
        unknown；预览数据（Research Preview）非正式历史事实。
      </p>
    </aside>
  );
}
