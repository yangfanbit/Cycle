import { allCampaignSecurities, ruleById, themeById, themesOfCampaign } from '../../data';
import type { HistoricalCampaign } from '../../models';
import type { TimelineCampaign } from '../../data/timeline/timelineTypes';
import { diffDays } from '../../utils';
import {
  DATA_STATUS_LABEL,
  LIFECYCLE_LABEL,
  RESULT_LABEL,
  ROLE_LABEL,
  RULE_STATUS_LABEL,
  STRENGTH_LABEL,
} from '../labels';

interface CampaignDetailProps {
  /** 生产 HistoricalCampaign（verified）或 Timeline 预览 Campaign（Research Preview） */
  campaign: HistoricalCampaign | TimelineCampaign;
  onOpenRule: (ruleId: string) => void;
  onClose: () => void;
}

/** 归一化详情视图模型：生产 / 预览两种输入共用同一渲染 */
function normalize(c: HistoricalCampaign | TimelineCampaign) {
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
      themes,
      securities,
      description: c.description,
      sourceText: `data/verified（已人工核验 L2）`,
      status: 'verified' as const,
      conflicts: undefined as string[] | undefined,
      phases: [] as { phase: keyof typeof LIFECYCLE_LABEL; start: string; end: string }[],
      earlySignal: null,
      strength: c.strength,
      result: c.result,
      production: true,
      campaignId: c.campaign_id,
    };
  }
  // Timeline（预览 / provisional / conflict）
  return {
    title: c.title,
    seasonId: c.season_id,
    start: c.start,
    end: c.end,
    peak: c.peak ?? null,
    crossYear: c.cross_year,
    ruleId: c.rule_id,
    themes: c.themes,
    securities: c.securities,
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

  return (
    <aside className="detail-panel">
      <button className="detail-close" onClick={onClose} aria-label="关闭">
        ×
      </button>
      <h2>历史行情 · {m.seasonId}</h2>
      <div>
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
          <strong>Research Preview</strong>
          <p>
            本条为 Cycle-Research 研究预览数据，非正式 Verified 数据；
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
          <span className="phase-text">（共 {duration} 天）</span>
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
              <span className="tag" key={s.name}>
                {s.name}
                {s.role ? `（${ROLE_LABEL[s.role] ?? s.role}）` : ''}
              </span>
            ))
          )}
        </dd>

        {m.conflicts && m.conflicts.length > 0 && (
          <>
            <dt>研究分歧</dt>
            <dd>
              {m.conflicts.map((c, i) => (
                <div key={i} className="conflict-line">
                  ⚠ {c}
                </div>
              ))}
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
