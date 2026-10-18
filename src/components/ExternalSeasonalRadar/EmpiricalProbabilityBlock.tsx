/**
 * ★★ 历史结果分布 / 经验基准概率（ThreeC 1.3 · v0.9 首个概率层）。
 *
 * ## 位置
 *
 * 挂在**既有**「跨年份比较」区段内部（`CrossYearSection` 的年份表之后），
 * **不另造第二套地图** —— 数据仍来自同一份题材文档。
 *
 * ## 它回答什么
 *
 * 「在**完整可比较**的历史窗口里，源数据定义的 `UP` 结果出现过几次、占多少，
 *   区间有多宽」。这是**历史统计描述 → 经验基准概率**，不是预测模型。
 *
 * ## 它**不**做什么（三条，均有测试）
 *
 * 1. 不把 `partial` 年份算进分母，也不把它算成失败 —— 逐条列出并说明原因；
 * 2. 不硬编码任何结果（`1/7` 这类数字必须由数据算出）；
 * 3. 不把「价格结果」写成「机制成功」—— 事件类型原样列出（流感 2019/20 是
 *    `UNKNOWN_PUBLIC_HEALTH`，**不是**流感驱动）。
 */
import {
  EMPIRICAL_PROBABILITY_DISCLAIMER,
  EMPIRICAL_PROBABILITY_LABEL,
  EVIDENCE_TIER_NOTE,
  assessModelFeasibility,
  computeEmpiricalEstimate,
  empiricalTargetOf,
  timeOrderedBaseline,
  type EmpiricalEstimate,
} from '../../data/timeline/empiricalProbability';
import {
  CROSS_YEAR_OUTCOME_LABEL,
  type CrossYearComparison,
  type CrossYearYear,
  type HistoricalEventsDoc,
} from '../../data/timeline/historicalEventMaps';
import { RichText } from '../RichText';

/** 比例 → 百分比字符串（保留 1 位；`null` → `—`，**不补 0**） */
function pct(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return '—';
  return `${(v * 100).toFixed(1)}%`;
}

function outcomeLabel(code: string): string {
  return CROSS_YEAR_OUTCOME_LABEL[code] ?? code;
}

/** 分母口径：**只**收 `comparable === true` */
const DENOMINATOR_RULE =
  '分母 = comparable === true 的年份（窗口端点可达 **且** 交易日充分）。'
  + 'partial（部分可比）、false、未记录 —— **一律不计入分母**，见下方排除表。';

/** ★ 这一层**不得**与「已验证的预测模型」混称 */
const TIER_BADGE = '未校准 · 探索性';

export function EmpiricalProbabilityBlock({
  doc,
  cmp,
}: {
  doc: HistoricalEventsDoc;
  cmp: CrossYearComparison;
}) {
  const years: CrossYearYear[] = cmp.years ?? [];
  const target = empiricalTargetOf(doc, cmp);
  if (!target) return null;                       // ★ 无判定规则 → 不展示（不自己编规则）

  const est: EmpiricalEstimate = computeEmpiricalEstimate(years, target);
  const ev = timeOrderedBaseline(years, target);
  const feas = assessModelFeasibility(ev, { comparableYears: est.denominator });

  return (
    <section className="fem-ep" data-empirical-probability="1" aria-label="历史结果分布与经验基准概率">
      <h5 className="fem-ep-title">
        历史结果分布 / {EMPIRICAL_PROBABILITY_LABEL}
        <span className="fem-ep-badge">{TIER_BADGE}</span>
      </h5>

      <p className="fem-ep-disc"><RichText text={EMPIRICAL_PROBABILITY_DISCLAIMER} /></p>

      {/* ---------- 目标定义（缺一个字段，比例就没有意义） ---------- */}
      <dl className="fem-ep-def">
        <dt>目标事件</dt>
        <dd>{target.label}</dd>
        <dt>观察窗口</dt>
        <dd>{target.windowLabel}</dd>
        <dt>标的池</dt>
        <dd>{target.poolLabel}</dd>
        <dt>判定规则（源数据原文）</dt>
        <dd className="fem-ep-rule"><RichText text={target.outcomeRule} /></dd>
        <dt>分母口径</dt>
        <dd><RichText text={DENOMINATOR_RULE} /></dd>
      </dl>

      {/* ---------- 结果分布（分母内） ---------- */}
      <h6 className="fem-ep-h6">结果分布（分母内 {est.denominator} 个完整可比较年份）</h6>
      {est.denominator === 0 ? (
        <p className="fem-empty">
          没有任何<strong>完整可比较</strong>的年份 —— 无法计算比例（<strong>不补 0</strong>，
          也不假设「从未发生」）。
        </p>
      ) : (
        <div className="fem-table-wrap">
          <table className="fem-table fem-ep-table">
            <thead>
              <tr>
                <th>结果（源数据码）</th><th>年数</th><th>占分母</th><th>说明</th>
              </tr>
            </thead>
            <tbody>
              {est.distribution.map((b) => (
                <tr key={b.outcome} data-ep-outcome={b.outcome}>
                  <td><code>{b.outcome}</code> {outcomeLabel(b.outcome)}</td>
                  <td>{b.count}</td>
                  <td>{pct(b.rate)}</td>
                  <td>
                    {target.successOutcomes.includes(b.outcome)
                      ? '★ 本目标定义的「成功」类'
                      : <>非「成功」类（<strong>不等于</strong>「失败」—— 只是不满足该目标定义）</>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- 二元目标：k/n + Wilson ---------- */}
      <h6 className="fem-ep-h6">二元目标：{target.successOutcomes.join(' / ')} 的历史经验比例</h6>
      {est.denominator === 0 ? (
        <p className="fem-empty">分母为 0 —— 不给出比例与区间。</p>
      ) : (
        <>
          <p className="fem-ep-est" data-ep-estimate="1">
            <strong>{est.successes} / {est.denominator}</strong>
            <span className="fem-ep-rate">= {pct(est.rate)}</span>
            {est.wilson && (
              <span className="fem-ep-ci">
                · 95% Wilson 区间 {pct(est.wilson.low)} ~ {pct(est.wilson.high)}
              </span>
            )}
            <span className="fem-ep-ci-note">
              （样本 {est.denominator} 个窗口；区间宽 = 不确定性大，<strong>不是</strong>精度声明）
            </span>
          </p>
          <p className="fem-ep-samples">
            计入分母的年份：{est.sampleYears.join(' · ')}
            {est.successYears.length > 0 && (
              <>
                <br />
                判定为 {target.successOutcomes.join(' / ')} 的年份：
                {est.successYears.map((s) => (
                  <span key={s.year} className="fem-ep-hit" data-ep-success={s.year}>
                    {s.year}
                    {s.seasonLabel ? ` ${s.seasonLabel}` : ''}
                    {s.eventType ? ` · 事件类型 ${s.eventType}` : ''}
                    {s.inWindowEvent === false ? ' · 窗口内事件：否' : ''}
                  </span>
                ))}
              </>
            )}
          </p>
        </>
      )}

      {/* ---------- 排除项（逐条，带原因） ---------- */}
      {est.excluded.length > 0 && (
        <>
          <h6 className="fem-ep-h6">未计入分母的年份（{est.excluded.length} 个）</h6>
          <div className="fem-table-wrap">
            <table className="fem-table fem-ep-table">
              <thead>
                <tr><th>年份</th><th>可比性</th><th>覆盖</th><th>排除原因（源数据原文）</th></tr>
              </thead>
              <tbody>
                {est.excluded.map((x) => (
                  <tr key={x.year} data-ep-excluded={x.year}>
                    <td>{x.year}{x.seasonLabel ? ` ${x.seasonLabel}` : ''}</td>
                    <td><code>{x.comparable}</code></td>
                    <td>{x.coverage ?? '—'}</td>
                    <td className="fem-ep-reason">
                      {x.reason ? <RichText text={x.reason} /> : '源数据未给出原因'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="fem-ep-note">
            ★ 排除 ≠ 失败。这些年份<strong>既不计入分子也不计入分母</strong> ——
            把它们算成「没涨」会系统性压低比例。
          </p>
        </>
      )}

      {/* ---------- 机制分布：价格结果 ≠ 机制成功 ---------- */}
      <h6 className="fem-ep-h6">机制分布（区分「价格结果」与「事件机制」）</h6>
      <div className="fem-table-wrap">
        <table className="fem-table fem-ep-table">
          <thead>
            <tr><th>窗口内事件类型（源数据）</th><th>年数</th><th>其中 {target.successOutcomes.join('/')}</th></tr>
          </thead>
          <tbody>
            {est.mechanismSplit.map((m) => (
              <tr key={m.eventType} data-ep-mechanism={m.eventType}>
                <td><code>{m.eventType}</code></td>
                <td>{m.count}</td>
                <td>{m.successCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="fem-ep-note">
        ★ <strong>价格结果 ≠ 机制成功</strong>：若某年判定为 {target.successOutcomes.join('/')}，
        但该年的窗口内事件类型<strong>不是本题材机制</strong>，那么它只是「价格结果」，
        <strong>不得</strong>记作本题材的机制成功。本表原样列出事件类型，不做合并、不做推断 ——
        判定为 {target.successOutcomes.join('/')} 的年份及其事件类型见上方明细。
      </p>

      {/* ---------- 三层口径 ---------- */}
      <p className="fem-ep-tier"><RichText text={EVIDENCE_TIER_NOTE} /></p>

      {/* ---------- 模型可行性（D）：只陈述事实 ---------- */}
      <details className="fem-ep-model">
        <summary>
          下一步：预测模型可行性（样本外 {ev.n} 步 / 门槛 {feas.requiredSteps} 步 ·
          事前特征 {feas.exAnteFeatureCount} / 需 {feas.requiredFeatures}）
        </summary>
        <p className="fem-ep-note">
          ★ 评估方式：<strong>严格按年份升序</strong>做 expanding-window 预测 ——
          第 i 年只用<strong>严格早于</strong>它的年份估计历史频率，再看该年实际结果。
          <strong>不做</strong>随机拆分（会打乱时间顺序、造成未来信息泄漏）。
        </p>
        <p className="fem-ep-note" data-ep-baseline-kind={ev.baseline.kind}>
          ★ <strong>评估基准</strong>：{ev.baseline.label}。
          用平滑频率是为了避免「训练集成功数为 0 → 预测 0 → 一次意外成功让 LogLoss 爆到 20+」，
          从而<strong>被单个样本主导</strong>。★ 平滑<strong>只用于评估</strong> ——
          上方展示的 <code>k/n</code> 与 Wilson 区间<strong>未做平滑</strong>。
        </p>
        {ev.n > 0 ? (
          <div className="fem-table-wrap">
            <table className="fem-table fem-ep-table">
              <thead>
                <tr>
                  <th>被预测年</th><th>训练年份</th><th>训练集成功/样本</th>
                  <th>原始 k/n</th><th>基准预测（平滑）</th><th>实际</th>
                  <th>Brier</th><th>LogLoss</th>
                </tr>
              </thead>
              <tbody>
                {ev.steps.map((s) => (
                  <tr key={s.year} data-ep-step={s.year}>
                    <td>{s.year}</td>
                    <td>{s.trainYears.join(' · ')}</td>
                    <td>{s.trainSuccesses}/{s.trainN}</td>
                    <td className="fem-ep-raw">{pct(s.rawFrequency)}</td>
                    <td>{pct(s.predicted)}</td>
                    <td>{s.observed}</td>
                    <td>{s.brier.toFixed(3)}</td>
                    <td>{s.logLoss.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="fem-empty">{ev.note}</p>
        )}
        <p className="fem-ep-est" data-ep-baseline="1">
          汇总：Brier <strong>{ev.pooledBrier == null ? '—' : ev.pooledBrier.toFixed(3)}</strong>
          {' · '}LogLoss <strong>{ev.pooledLogLoss == null ? '—' : ev.pooledLogLoss.toFixed(3)}</strong>
          {' · '}样本外 {ev.n} 步
        </p>
        <p className="fem-ep-note"><RichText text={ev.calibrationNote} /></p>
        {/* ★ 校准分箱：样本少时大多为空箱 —— **照实显示**，不合并、不省略 */}
        <div className="fem-table-wrap">
          <table className="fem-table fem-ep-table">
            <thead>
              <tr>
                <th>预测区间</th><th>步数</th><th>平均预测</th><th>实际成功率</th><th>校准偏差</th>
              </tr>
            </thead>
            <tbody>
              {ev.calibration.map((b) => (
                <tr key={`${b.low}-${b.high}`} data-ep-calibration={b.low}>
                  <td>
                    {pct(b.low)} – {b.high > 1 ? '100%' : pct(b.high)}
                  </td>
                  <td>{b.n}</td>
                  <td>{pct(b.meanPredicted)}</td>
                  <td>{pct(b.observedRate)}</td>
                  <td>
                    {b.n === 0 || b.observedRate == null || b.meanPredicted == null
                      ? '—（无样本）'
                      : `${((b.observedRate - b.meanPredicted) * 100).toFixed(1)} pp`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="fem-ep-gates" data-ep-gates="1">
          <span className={feas.stepsSufficient ? 'gate-ok' : 'gate-no'}>
            样本外步数：{feas.outOfSampleSteps} / {feas.requiredSteps}
            （{feas.stepsSufficient ? '达标' : '不足'}）
          </span>
          {' · '}
          <span className={feas.featuresSufficient ? 'gate-ok' : 'gate-no'}>
            事前特征：{feas.exAnteFeatureCount} / {feas.requiredFeatures}
            （{feas.featuresSufficient ? '够用' : '不足'}）
          </span>
          {' · '}
          <span className={feas.sufficient ? 'gate-ok' : 'gate-no'}>
            训练条件：{feas.sufficient ? '具备' : '不具备'}
          </span>
        </p>
        <p className="fem-ep-verdict" data-ep-feasibility={feas.sufficient ? 'sufficient' : 'insufficient'}>
          <strong>可行性结论</strong>：<RichText text={feas.verdict} />
        </p>
        <ul className="fem-gaps">
          {feas.missing.map((m) => <li key={m}><RichText text={m} /></li>)}
        </ul>
      </details>
    </section>
  );
}
