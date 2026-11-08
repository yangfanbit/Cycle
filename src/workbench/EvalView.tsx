/**
 * 内部评估视图（v0.74）—— **唯一**允许出现排序/评分的地方。
 *
 * ★★ 隔离要求（有测试锁定）：
 *  · 本组件**不在默认页面渲染**，数据由 Workbench 在用户主动点击后按需 import；
 *  · 默认检索索引产物里零评分字段（`build_workbench_basis_v0_1.py --check` 校验）；
 *  · 打分只用于生成对照实验的材料，**不参与有效性验收**；
 *  · 有效性 = 研究增量（新线索率 / 耗时变化 / 事后可核性），不是行情超额。
 */
import { useMemo, useState } from 'react';
import { RichText } from '../components/RichText';
import type { DeclarationView, EvalDoc } from './types';

const PAGE = 40;

export function EvalView({ doc, declarations }: {
  doc: EvalDoc; declarations?: DeclarationView;
}) {
  const [q, setQ] = useState('');
  const [limit, setLimit] = useState(PAGE);
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const base = needle
      ? doc.rows.filter((r) => (r.board ?? '').toLowerCase().includes(needle)
          || (r.board_series ?? '').toLowerCase().includes(needle))
      : doc.rows;
    return base; // ★ 顺序直接取产物的确定性顺序（priority_score 降序），前端不再二次排序
  }, [doc, q]);

  return (
    <section className="wb-eval" data-eval-view="1">
      <div className="wb-warn" data-eval-warning="1">
        <strong>内部评估视图 · INTERNAL_EVAL_ONLY</strong>
        <p>
          这里的排序<strong>只用于生成对照实验的材料</strong>，不出现在默认页面，
          <strong>不参与有效性验收</strong>，也<strong>不是</strong>推荐、买卖信号或选股清单。
        </p>
        <p>
          <code>priority_score = Wilson 95% 区间下界</code>（输入为历史 <code>hit_rate</code> 与{' '}
          <code>n_years</code>）：小样本与高不确定性自动降权。
          <strong>不是未来概率、不是胜率、未校准</strong>；历史统计不能外推为未来表现。
        </p>
        <p>
          有效性按 <strong>研究增量</strong> 判定（新线索率 / 耗时变化 / 事后可核性），
          见 <code>docs/EVALUATION_FRAMEWORK_v0_1.md</code>。5/10/20 日板块超额已降级为行情附注。
        </p>
      </div>

      <label className="wb-field">
        <span>按板块名或序列 ID 查找</span>
        <input value={q} onChange={(e) => { setQ(e.target.value); setLimit(PAGE); }}
               placeholder="例如 光伏 / BK881280" data-eval-search="" />
      </label>
      <p className="wb-count" data-eval-count={rows.length}>
        命中 <strong>{rows.length}</strong> 行 / 共 {doc.counts.rows} 行 · 展示前 {Math.min(limit, rows.length)} 行
        · 其中 {doc.counts.with_oos_tests} 行有样本外检验
      </p>

      <div className="wb-table-wrap">
        <table className="wb-table">
          <thead>
            <tr>
              <th>板块</th><th>月</th><th>历史命中</th><th>n</th>
              <th>Wilson 95%</th><th>OOS 次数</th><th>层级</th><th>PIT 资格</th>
              <th>priority_score</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, limit).map((r) => (
              <tr key={`${r.board_series}-${r.month}`} data-eval-row={r.board_series}>
                <td>{r.board}<span className="wb-sid">{r.board_series}</span></td>
                <td>{r.month}</td>
                <td>{(r.hit_rate * 100).toFixed(0)}%（{r.k}/{r.n_years}）</td>
                <td>{r.n_years}</td>
                <td>{(r.wilson_low * 100).toFixed(1)}% – {(r.wilson_high * 100).toFixed(1)}%</td>
                <td>{r.oos_tests ?? 0}</td>
                <td>{r.tier}</td>
                <td>{r.pit_basis ?? '—'}</td>
                <td className="wb-score">{r.priority_score.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > limit && (
        <button type="button" className="wb-btn" onClick={() => setLimit(limit + PAGE)}>
          再显示 {PAGE} 行
        </button>
      )}
      {declarations && (
        <section className="wb-decl" data-phase-declarations="1">
          <h2>产业机制阶段声明时间线 · 事后回测留痕</h2>
          <p className="wb-hint">
            阶段声明是<strong>产业机制层的人工判定</strong>，不是行情状态。默认页不展示它
            （行情持续更新时静态旧声明没有信息量）；这里按声明时间排列，每条带
            <strong>当时可知信息的上界</strong>（PIT 锚点 = 声明日）。结算不写进声明，
            事后核对另立一轮；日志<strong>只增不改</strong>，行情推进不改写历史声明。
          </p>
          <p className="wb-hint">
            来源 <code>{declarations.source.file}</code> · sha256 前 16 位{' '}
            <code>{declarations.source.sha256_16}</code> · as_of {declarations.as_of} ·{' '}
            {declarations.counts.declarations} 条声明 /{' '}
            {declarations.counts.review_rounds} 个研究轮次。
            同轮同日的多主题声明不算独立观察，事后核对须先声明窗口与分母。
          </p>
          <ol className="wb-decl-list">
            {declarations.declarations.map((d) => (
              <li key={d.declaration_id} data-declaration-id={d.declaration_id}>
                <div className="wb-decl-head">
                  <strong>{d.display_name}</strong> · <code>{d.declared_phase}</code> · 声明日{' '}
                  <code>{d.declared_at}</code> · {d.review_status ?? '—'}
                </div>
                <div className="wb-decl-anchor">
                  PIT 锚点 <code>{d.market_anchor.as_of}</code>（{d.market_anchor.basis}） ·{' '}
                  {d.supersedes ? `取代 ${d.supersedes}` : '首轮声明'} ·{' '}
                  {d.market_anchor.price_data_available_at_declaration === 'NOT_RECORDED'
                    ? '声明时行情截止日未单独落盘' : '声明时行情截止日已记录'}
                </div>
                <p><RichText text={d.basis} /></p>
                <p className="wb-foot">来源：{d.source_ref}</p>
              </li>
            ))}
          </ol>
          <details className="wb-decl-gaps">
            <summary>已知缺口与边界</summary>
            <ul>
              {declarations.known_gaps.map((g) => (
                <li key={g.id}>
                  <strong>{g.id}</strong>：<RichText text={g.detail} />
                  <span className="wb-foot"> · 限制：{g.blocks}</span>
                </li>
              ))}
            </ul>
          </details>
        </section>
      )}
      <p className="wb-foot">
        数据来源：<code>{doc.source.file}</code> · sha256 前 16 位{' '}
        <code>{doc.source.sha256_16}</code> · 确定性派生产物，可用{' '}
        <code>build_workbench_basis_v0_1.py --check</code> 复算。
      </p>
    </section>
  );
}
