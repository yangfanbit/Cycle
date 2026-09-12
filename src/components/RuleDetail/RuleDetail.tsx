import { anchorResolver, campaignsOfRule, eventById, sourceById, windowsOfRule } from '../../data';
import type { Rule } from '../../models';
import { computeWindowStatus } from '../../utils';
import { PHASE_LABEL, RESULT_LABEL, RULE_STATUS_LABEL, RULE_TYPE_LABEL, STRENGTH_LABEL, windowRangeLabel } from '../labels';

interface RuleDetailProps {
  rule: Rule;
  today: string;
  onOpenCampaign: (campaignId: string) => void;
  onClose: () => void;
}

export function RuleDetail({ rule, today, onOpenCampaign, onClose }: RuleDetailProps) {
  const windows = windowsOfRule(rule.rule_id);
  const cases = campaignsOfRule(rule.rule_id);
  const source = sourceById.get(rule.source_id);

  return (
    <aside className="detail-panel">
      <button className="detail-close" onClick={onClose} aria-label="关闭">
        ×
      </button>
      <h2>{rule.name}</h2>
      <div>
        <span className="badge badge-candidate">{RULE_STATUS_LABEL[rule.status]}</span>
        <span className="badge badge-plain">{RULE_TYPE_LABEL[rule.rule_type]}</span>
      </div>

      <dl className="kv">
        <dt>底层方向</dt>
        <dd>{rule.base_sector}</dd>

        <dt>经验时间窗</dt>
        <dd>
          {windows.length === 0 && <span className="empty-note">暂无可计算窗口</span>}
          {windows.map((w) => {
            const status = computeWindowStatus(w, today, anchorResolver);
            return (
              <div key={w.window_id}>
                <div>
                  {w.window_type === 'relative_event'
                    ? `相对「${eventById.get(w.anchor_event ?? '')?.name ?? w.anchor_event ?? '未知事件'}」：${
                        w.start_offset_days
                      } 天 → +${w.end_offset_days} 天`
                    : windowRangeLabel(w.start_md ?? '未定', w.end_md ?? '未定', w.approximate)}
                  {status
                    ? `（本季${w.approximate ? '近似' : ''}实例：${status.occurrence.start} → ${status.occurrence.end}）`
                    : ''}
                </div>
                {w.note && <div className="phase-text">{w.note}</div>}
                <div className="phase-text">
                  提前观察：约 {w.preheat_days} 天
                  {status ? ` ｜ 当前状态：${PHASE_LABEL[status.phase]}` : ''}
                </div>
              </div>
            );
          })}
        </dd>

        <dt>规律描述</dt>
        <dd>{rule.description}</dd>

        {rule.mechanism && (
          <>
            <dt>可能机理</dt>
            <dd>{rule.mechanism}</dd>
          </>
        )}

        <dt>标签</dt>
        <dd>
          {rule.tags.map((t) => (
            <span className="tag" key={t}>
              {t}
            </span>
          ))}
        </dd>

        <dt>统计状态</dt>
        <dd>{rule.statistics?.status === 'not_verified' ? '未验证（V1 不提供量化评分）' : '已计算'}</dd>

        <dt>信息来源</dt>
        <dd>{source ? `${source.title}（${source.source_type}）` : rule.source_id}</dd>
      </dl>

      <div className="section-title">历史案例</div>
      {cases.length === 0 ? (
        <div className="empty-note">历史案例待补充</div>
      ) : (
        <ul className="case-list">
          {cases.map((c) => (
            <li key={c.campaign_id} onClick={() => onOpenCampaign(c.campaign_id)}>
              <div>
                <strong>{c.season_id}</strong>
                {c.cross_year && <span className="badge badge-cross">跨年</span>}
                <span className="badge badge-plain">
                  强度 {STRENGTH_LABEL[c.strength]} ｜ 结果 {RESULT_LABEL[c.result]}
                </span>
              </div>
              <div className="case-dates">
                {c.start_date} → {c.end_date}
              </div>
            </li>
          ))}
        </ul>
      )}

      <p className="disclaimer">
        本规律为候选经验假设，不构成任何买卖建议；统计结论需等待历史数据验证（V1.5+）。
      </p>
    </aside>
  );
}
