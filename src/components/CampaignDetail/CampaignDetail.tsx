import { campaignSecurities, ruleById, sourceById, themeById, themesOfCampaign } from '../../data';
import type { HistoricalCampaign } from '../../models';
import { diffDays } from '../../utils';
import { RESULT_LABEL, ROLE_LABEL, RULE_STATUS_LABEL, STRENGTH_LABEL } from '../labels';

interface CampaignDetailProps {
  campaign: HistoricalCampaign;
  onOpenRule: (ruleId: string) => void;
  onClose: () => void;
}

export function CampaignDetail({ campaign, onOpenRule, onClose }: CampaignDetailProps) {
  const rule = ruleById.get(campaign.rule_id);
  const themes = themesOfCampaign(campaign.campaign_id);
  const securities = campaignSecurities.filter((cs) => cs.campaign_id === campaign.campaign_id);
  const source = sourceById.get(campaign.source_id);
  const duration = diffDays(campaign.start_date, campaign.end_date) + 1;

  return (
    <aside className="detail-panel">
      <button className="detail-close" onClick={onClose} aria-label="关闭">
        ×
      </button>
      <h2>历史行情 · {campaign.season_id}</h2>
      <div>
        {campaign.cross_year && <span className="badge badge-cross">跨年行情</span>}
        <span className="badge badge-plain">强度 {STRENGTH_LABEL[campaign.strength]}</span>
        <span className="badge badge-plain">结果 {RESULT_LABEL[campaign.result]}</span>
      </div>

      <dl className="kv">
        <dt>完整日期</dt>
        <dd>
          {campaign.start_date} → {campaign.end_date}
          <span className="phase-text">（共 {duration} 天）</span>
        </dd>

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
            campaign.rule_id
          )}
          {rule && <span className="phase-text">（{RULE_STATUS_LABEL[rule.status]}）</span>}
        </dd>

        <dt>具体题材</dt>
        <dd>
          {themes.length === 0 && <span className="empty-note">题材信息待补充</span>}
          {themes.map((ct) => {
            const t = themeById.get(ct.theme_id);
            return (
              <span className="tag" key={ct.theme_id}>
                {t?.name ?? ct.theme_id}（{ROLE_LABEL[ct.role] ?? ct.role}）
              </span>
            );
          })}
        </dd>

        <dt>代表股票</dt>
        <dd>
          {securities.length === 0 ? (
            <span className="empty-note">暂无代表股票记录（待历史数据核实后补充）</span>
          ) : (
            securities.map((s) => s.security_id).join('、')
          )}
        </dd>

        <dt>备注</dt>
        <dd>{campaign.description ?? '—'}</dd>

        <dt>信息来源</dt>
        <dd>{source ? `${source.title}（${source.source_type}）` : campaign.source_id}</dd>
      </dl>

      <p className="disclaimer">
        历史行情记录用于规律研究，不构成任何买卖建议；strength / result 未经量化验证时记为 unknown。
      </p>
    </aside>
  );
}
