/**
 * 外部季节性线索 —— **证据核验**摘要（v0.37）。
 * ★ 只显示：名称 / 外部声称窗口 / 处理状态 / 原因。默认折叠，不再渲染 12 个月轴与详细卡片。
 * ★ 任何条目都**不是**「外部报告已验证」：原始报告不在库内（external_report_verified 恒 false）。
 */
import raw from '@current/external_claim_verification_v0_1.json';

interface Claim {
  claim_id: string; name: string; claimed_window: string | null; status: string; reason: string;
  internal_pattern?: { board: string; month: number; median_excess_pct: number; oos_status?: string } | null;
}
interface Doc { as_of: string; counts: Record<string, number>; rule: string; claims: Claim[] }
const doc = raw as unknown as Doc;

const LABEL: Record<string, string> = {
  INTERNAL_SUPPORTED: '内部同月结构支持（≠外部已验证）',
  INTERNAL_WEAK: '内部结构偏弱',
  NOT_SUPPORTED: '内部数据不支持',
  UNTESTABLE_NO_SERIES: '无可对照序列',
  NOT_CALENDAR: '事件驱动（无固定窗口）',
};

export function ExternalClaimsSummary() {
  return (
    <details className="fwd-ext" data-external-claims="1" data-as-of={doc.as_of}>
      <summary>
        外部季节性线索（{doc.counts.total} 条 · 内部支持 {doc.counts.internal_supported} · 不可测 {doc.counts.untestable}）
        —— 仅作参考资料，<strong>未</strong>经外部原始报告验证
      </summary>
      <p className="fwd-note">{doc.rule}</p>
      <ul className="fwd-ext-list">
        {doc.claims.map((c) => (
          <li key={c.claim_id} data-claim={c.claim_id} data-status={c.status}>
            <strong>{c.name}</strong>
            <span className="fwd-role-asof">{c.claimed_window ?? '—'}</span>
            <span className={`fwd-ev st-${c.status === 'INTERNAL_SUPPORTED' ? 'pre_observation' : 'insufficient'}`}>
              {LABEL[c.status] ?? c.status}
            </span>
            <span className="fwd-note">
              {c.reason}
              {c.internal_pattern && (
                <> · 对照：{c.internal_pattern.board} {c.internal_pattern.month} 月
                  （中位 {c.internal_pattern.median_excess_pct > 0 ? '+' : ''}{c.internal_pattern.median_excess_pct}%，
                  样本外 {c.internal_pattern.oos_status ?? '—'}）</>
              )}
            </span>
          </li>
        ))}
      </ul>
    </details>
  );
}
