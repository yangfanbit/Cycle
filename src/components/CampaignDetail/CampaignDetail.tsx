import { allCampaignSecurities, ruleById, themeById, themesOfCampaign } from '../../data';
import type { HistoricalCampaign } from '../../models';
import { campaignDrivers } from '../../data/timeline/timelineAdapter';
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

export function CampaignDetail({ campaign, onOpenRule, onClose }: CampaignDetailProps) {
  const m = normalize(campaign);
  const rule = ruleById.get(m.ruleId);
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
    <aside className="detail-panel">
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

      <dl className="kv">
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

        {m.events.length > 0 && (
          <>
            <dt>关联事件</dt>
            <dd>
              {m.events.map((ev) => (
                <div key={`${ev.date}-${ev.name}`} className="event-line">
                  <span className="phase-text">{ev.date}</span> {ev.name}
                  <span className="phase-text">
                    （{EVENT_TYPE_LABEL[ev.event_type] ?? ev.event_type}
                    {ev.role ? ` · ${ROLE_LABEL[ev.role] ?? ev.role}` : ''}）
                  </span>
                </div>
              ))}
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
              <div className="phase-text">（研究层"值得观察"信息，不是交易信号）</div>
            </dd>
          </>
        )}

        <dt>驱动因素（为什么）</dt>
        <dd className="drivers">
          {driverRows.map(({ q, tags }) => (
            <div key={q} className="driver-row">
              <span className="driver-q">{q}</span>
              {tags.length > 0 ? (
                tags.map((t) => (
                  <span className="tag" key={t} title={t}>
                    {t}
                  </span>
                ))
              ) : (
                <span className="phase-text">暂无可靠归因</span>
              )}
            </div>
          ))}
          <div className="phase-text">
            {m.drivers
              ? '（来自 Cycle-Research V1.7 研究归因，原样展示；非因果结论，不构成买卖建议。）'
              : `（基于研究事件的时间归组线索，非因果结论；${m.production ? '生产数据暂无关联事件。' : ''}）`}
          </div>
        </dd>

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
