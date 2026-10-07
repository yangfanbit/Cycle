import { useMemo, useState } from 'react';
import {
  coveredTerms,
  lookupDirection,
  type DirectionLookupResult,
} from '../../data/timeline/directionLookup';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import type { CurrentCandidateDataset } from '../../data/timeline/currentCandidate';

/**
 * 方向查询（Direction Lookup）—— ThreeC 1.2 · Usage-Driven。
 *
 * ## 为什么需要它
 * 两次真实使用测试（医药健康 / 汽车）暴露：**全库只有 5 个当前研究对象，历史却有 52 个 Campaign**。
 * 用户真正关心的方向**大概率不在这 5 个里**，而产品此前**只能展示研究侧选定的对象**。
 * 本组件让用户**自己问**，并得到**明确回答**。
 *
 * ## ★★ 语义边界（必须在 UI 上说清楚）
 * 这是**查找**，**不是**结构对应。
 * 命中的是**主题名 / 标题**，与 `Structural Correspondence` **完全无关** ——
 * 冻结 SA 的解释才是唯一的结构对应入口。
 *
 * ## 诚实空态
 * 查不到时**明确说「未覆盖」**，并给出覆盖词表 —— 而不是留一个空白让人以为坏了。
 */

const VERDICT_TEXT: Record<DirectionLookupResult['verdict'], string> = {
  both: '该方向**两侧都有**：既有当前研究对象，也有历史案例 —— 可以走完整工作流。',
  'current-only': '该方向**只有当前研究对象，历史侧没有命中** —— 可看当前对象，但历史结构对应可能为空。',
  'historical-only':
    '该方向**只有历史案例，当前侧没有研究对象** —— 历史可用，但**无法回答「现在处于什么阶段」**（结构对应需要当前对象作为一侧）。',
  none: '本工具**未覆盖**该方向 —— 历史研究与当前研究对象里都没有命中。',
};

export function DirectionLookupSection({
  source,
  dataset,
  onOpenHistoricalCase,
}: {
  source: TimelineDataSource | null;
  dataset: CurrentCandidateDataset | null;
  onOpenHistoricalCase?: (campaignId: string) => void;
}) {
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');

  const result = useMemo(
    () => (query ? lookupDirection(query, source, dataset) : null),
    [query, source, dataset],
  );
  const terms = useMemo(() => coveredTerms(source, dataset), [source, dataset]);

  const submit = (v: string) => {
    const t = v.trim();
    if (t) setQuery(t);
  };

  return (
    <section className="dl" aria-label="方向查询">
      <h3 className="dl-title">查一个方向</h3>
      <p className="dl-lead">
        输入你真正关心的方向（如「汽车」「半导体」「医药」），看本工具<strong>有没有</strong>对应的
        历史案例与当前研究对象。
        <strong>这是查找，不是结构对应</strong> —— 命中的是主题名 / 标题；
        真正的「当前 ↔ 历史 结构对应」只在研究对象的解释里，由冻结规则给出。
      </p>

      <form
        className="dl-form"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <input
          className="dl-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="例如：汽车 / 半导体 / 传媒"
          aria-label="方向关键词"
        />
        <button className="dl-btn" type="submit">
          查询
        </button>
      </form>

      {result && (
        <div className="dl-result" role="status">
          <p className={`dl-verdict dl-v-${result.verdict}`}>
            「{result.query}」：
            {VERDICT_TEXT[result.verdict]
              .split('**')
              .map((seg, i) => (i % 2 === 1 ? <strong key={i}>{seg}</strong> : seg))}
          </p>

          {result.current.length > 0 && (
            <div className="dl-block">
              <h4>当前研究对象（{result.current.length}）</h4>
              <ul className="dl-list">
                {result.current.map((h) => (
                  <li key={h.id}>
                    <span className="dl-id">{h.id}</span>
                    <span className="dl-name">{h.title}</span>
                    {h.macroTheme && <span className="dl-tag">{h.macroTheme}</span>}
                    <span className="dl-why">命中：{h.matchedOn.join(' / ')}</span>
                    {h.researchQuestions && h.researchQuestions.length > 0 && (
                      <details className="dl-qs">
                        <summary>研究问题 {h.researchQuestions.length} 条（继续研究的线索）</summary>
                        <ul>
                          {h.researchQuestions.map((q, i) => (
                            <li key={i}>{q}</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.historical.length > 0 && (
            <div className="dl-block">
              <h4>历史案例（{result.historical.length}）</h4>
              <ul className="dl-list">
                {result.historical.map((h) => (
                  <li key={h.id}>
                    {onOpenHistoricalCase ? (
                      <button
                        type="button"
                        className="dl-id dl-link"
                        onClick={() => onOpenHistoricalCase(h.id)}
                        title="打开该历史案例"
                      >
                        {h.id}
                      </button>
                    ) : (
                      <span className="dl-id">{h.id}</span>
                    )}
                    <span className="dl-name">{h.title}</span>
                    {h.start && (
                      <span className="dl-dates">
                        {h.start} ~ {h.end}
                      </span>
                    )}
                    <span className="dl-why">命中：{h.matchedOn.join(' / ')}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <details className="dl-terms">
        <summary>能查什么？—— 覆盖词表（{terms.length} 个大主题）</summary>
        <p className="dl-dim">
          以下是大主题的<strong>计数事实</strong>（历史案例数 / 当前对象数），<strong>不是排序或评分</strong>。点击即查。
        </p>
        <ul className="dl-term-list">
          {terms.map((t) => (
            <li key={t.term}>
              <button type="button" className="dl-term" onClick={() => { setInput(t.term); submit(t.term); }}>
                {t.term}
                <span className="dl-term-n">
                  历史 {t.historicalCount} · 当前 {t.currentCount}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
