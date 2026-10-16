import { useEffect, useMemo, useState } from 'react';
import {
  coveredTerms,
  lookupDirection,
  type DirectionLookupResult,
} from '../../data/timeline/directionLookup';
import {
  DRAFT_FIELD_MAX,
  EMPTY_DRAFT,
  buildResearchRequestPayload,
  isDraftEmpty,
  missingDraftFields,
  renderResearchRequestMarkdown,
  type ResearchRequestDraft,
  type ResearchRequestPayload,
} from '../../data/timeline/researchRequestDraft';
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

/**
 * ★★ `none` 的**完整**说明（2026-10-07 文化传媒使用测试的产出）。
 *
 * 测试证明：「主题名未覆盖」**不等于**「结构上无对应」——
 * 一个历史宇宙里完全没有的方向，只要有一个「当前研究对象」，**仍能得到结构对应**。
 * 所以必须把这两种「没有」分开说，否则用户会以为工具**根本帮不上**。
 */
const NONE_EXPLAIN = [
  '「未覆盖」指的是**主题名**：历史研究的 44 个主题名里没有它，当前研究对象里也没有它。',
  '★ 但这**不等于**「结构上无对应」。结构对应比的是**机制 / 序列 / 事件结构**，不是名字 ——',
  '实测：一个历史研究里完全没有的方向（文化传媒），在建立当前研究对象后，仍得到了 1 条结构支持。',
  '**要拿到结构层面的答案，需要先为该方向建立一轮研究（当前研究对象）**；在那之前，',
  '本工具只能如实说「还没法比」，而不是「比过了、不成立」。',
];

/**
 * 草稿的本机持久化（★ 只在本机；不上传、不写库）。
 * 键名带版本号：将来改结构时可安全弃用旧键，不会读到半截数据。
 */
const DRAFT_STORAGE_KEY = 'threec.researchRequestDraft.v1';

function loadDraft(): ResearchRequestDraft {
  try {
    const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY);
    if (!raw) return EMPTY_DRAFT;
    const parsed = JSON.parse(raw) as Partial<ResearchRequestDraft>;
    return { ...EMPTY_DRAFT, ...parsed };
  } catch {
    // 隐私模式 / 存储被禁 / 内容损坏 → 静默降级为空草稿（不阻塞使用）
    return EMPTY_DRAFT;
  }
}

function saveDraft(d: ResearchRequestDraft): void {
  try {
    if (isDraftEmpty(d)) window.localStorage.removeItem(DRAFT_STORAGE_KEY);
    else window.localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(d));
  } catch {
    // 存不下就算了 —— 草稿仍在本页内存里可用
  }
}

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

  /* ------------------------------------------------------------------
   * 研究请求草稿（ThreeC 1.3）
   *
   * ★ 草稿只存在**本机**：localStorage（键名自带版本，便于将来清理）。
   *   不上传、不写库、不生成正式 ID。读取失败（隐私模式 / 禁用存储）静默降级为空草稿。
   * ------------------------------------------------------------------ */
  const [draft, setDraft] = useState<ResearchRequestDraft>(() => loadDraft());
  const [copied, setCopied] = useState<'json' | 'md' | null>(null);

  useEffect(() => {
    saveDraft(draft);
  }, [draft]);

  // 首次查询命中时，把方向回填进草稿（用户不必重打；仍可编辑）
  useEffect(() => {
    if (result && !draft.direction.trim()) {
      setDraft((d) => ({ ...d, direction: result.query }));
    }
  }, [result, draft.direction]);

  const payload = useMemo(
    () => buildResearchRequestPayload(draft, result, new Date().toISOString()),
    [draft, result],
  );
  const payloadJson = useMemo(() => JSON.stringify(payload, null, 2), [payload]);
  const payloadMd = useMemo(() => renderResearchRequestMarkdown(payload), [payload]);

  const copy = async (kind: 'json' | 'md', text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      // ★ 剪贴板不可用（旧浏览器 / 非安全上下文 / 测试环境）→ 不假装成功：
      //   草稿区里的 <textarea> 永远可见可选中，用户可手动复制。
      setCopied(null);
    }
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

          {/* ★★ Contract v1.2：「未覆盖」必须**说清是哪一种** ——
              此前两种情况都只得到笼统的「未覆盖」：
                ② 库内主题、但暂无对象挂靠（如「半导体材料」）
                ③ 根本不是库内主题（如「动力煤」）
              ★ 本块只做**披露**，不改变命中集合（不得把根下的对象算作该查询的命中）。 */}
          {result.verdict === 'none' && result.resolution && (
            <p className="dl-resolution">
              {result.resolution.matchedTheme ? (
                <>
                  该名称是<strong>库内主题</strong>
                  {result.resolution.root && result.resolution.root.name !== result.resolution.matchedTheme.name && (
                    <>（属「{result.resolution.root.name}」）</>
                  )}
                  ：该主题下<strong>暂无历史对象</strong>
                  {result.resolution.rootObjectCount > 0 && result.resolution.root && (
                    <>
                      ；「{result.resolution.root.name}」大主题下有 {result.resolution.rootObjectCount} 个历史对象
                    </>
                  )}
                  。
                </>
              ) : (
                <>
                  该名称<strong>不在库内主题表中</strong>（库内共 {result.resolution.taxonomySize} 个主题）。
                </>
              )}
            </p>
          )}

          {/* ★ 「未覆盖」≠「结构上无对应」—— 必须分开说，否则用户以为工具根本帮不上 */}
          {result.verdict === 'none' && (
            <ul className="dl-none-explain">
              {NONE_EXPLAIN.map((t, i) => (
                <li key={i}>
                  {t.split('**').map((seg, j) => (j % 2 === 1 ? <strong key={j}>{seg}</strong> : seg))}
                </li>
              ))}
            </ul>
          )}

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

      {/* ★ 研究请求草稿：**只在查询之后出现**（先把方向查清楚，再谈把它变成请求）。
          ★ 未查询时不渲染 —— 与既有语义守卫一致：未查询不得出现「未覆盖 ≠ …」类解释。 */}
      {result && (
        <ResearchRequestDraftBlock
          lookup={result}
          draft={draft}
          setDraft={setDraft}
          payload={payload}
          payloadJson={payloadJson}
          payloadMd={payloadMd}
          copied={copied}
          onCopy={copy}
        />
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

/* ================================================================================
 * 研究请求草稿区（ThreeC 1.3 · Usage-Driven）
 *
 * ★★ 定位：用户查到方向之后，**把它变成一次真正的研究请求**。
 * ★ 这是**草稿** —— 无正式 ID、不入库、不上传；须经 Research 审查。
 * ★ 覆盖查询四态结果**随草稿一起导出**（用户与审查者看到同一份事实）。
 * ★ 单独导出以便测试直接渲染（`DirectionLookupSection` 只在查询后渲染它）。
 * ================================================================================ */
export function ResearchRequestDraftBlock({
  lookup,
  draft,
  setDraft,
  payload,
  payloadJson,
  payloadMd,
  copied,
  onCopy,
}: {
  lookup: DirectionLookupResult;
  draft: ResearchRequestDraft;
  setDraft: (updater: (d: ResearchRequestDraft) => ResearchRequestDraft) => void;
  payload: ResearchRequestPayload;
  payloadJson: string;
  payloadMd: string;
  copied: 'json' | 'md' | null;
  onCopy: (kind: 'json' | 'md', text: string) => void;
}) {
  const missing = missingDraftFields(draft);
  const set = (k: keyof ResearchRequestDraft) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => setDraft((d) => ({ ...d, [k]: e.target.value.slice(0, DRAFT_FIELD_MAX) }));

  return (
    <details className="dl-draft" open>
      <summary>把「{lookup.query}」变成研究请求草稿（可导出交接）</summary>
      <p className="dl-draft-lead">
        研究侧当前<strong>只覆盖研究侧选定的方向</strong>。若你关心的方向不在其中，
        可以在这里写下你<strong>真正想回答的问题</strong>，导出成一份
        <strong>草稿</strong>交给研究流程。
        <strong>草稿不会自动进入研究库</strong>，也<strong>不会自动获得正式编号</strong> ——
        它只是你的诉求记录（存在本机，不上传）。
      </p>

      <div className="dl-draft-form">
        <label className="dl-draft-field">
          <span>研究方向</span>
          <input value={draft.direction} onChange={set('direction')}
                 placeholder="例如：汽车 · 智能驾驶合规化" aria-label="研究方向" />
        </label>

        <label className="dl-draft-field">
          <span>希望回答的研究问题（一行一条）</span>
          <textarea value={draft.researchQuestions} onChange={set('researchQuestions')}
                    rows={3} aria-label="研究问题"
                    placeholder={'例如：\nL3 强制国标落地前后，产业链哪一段先反应？\n历史上类似「合规化驱动」的行情持续多久？'} />
        </label>

        <label className="dl-draft-field">
          <span>为什么关注这个方向</span>
          <textarea value={draft.whyCare} onChange={set('whyCare')} rows={2}
                    aria-label="为什么关注" placeholder="例如：所在行业 / 客户需求 / 已观察到现象" />
        </label>

        <label className="dl-draft-field">
          <span>已知线索 / 来源（可选，一行一条）</span>
          <textarea value={draft.knownLeads} onChange={set('knownLeads')} rows={2}
                    aria-label="已知线索" placeholder="例如：2024-06 某部委征求意见稿；某券商报告" />
        </label>

        <label className="dl-draft-field">
          <span>希望调查的历史时间范围</span>
          <input value={draft.timeRange} onChange={set('timeRange')}
                 aria-label="历史时间范围" placeholder="例如：2018-2025" />
        </label>
      </div>

      {missing.length > 0 && (
        <p className="dl-draft-missing">
          ★ 还缺：{missing.join(' / ')}（可以继续补，也可以先导出不完整的草稿 —— 草稿允许不完整）
        </p>
      )}

      <p className="dl-draft-facts">
        <strong>随草稿一起带走的覆盖查询结果</strong>（工具侧事实，供审查者核对）：
        <span className={`dl-verdict dl-v-${payload.coverage_check.verdict}`}>
          {payload.coverage_check.verdict}
        </span>
        —— {payload.coverage_check.verdict_meaning}
        当前研究对象 {payload.coverage_check.current_objects.length} 个 ·
        历史案例 {payload.coverage_check.historical_cases.length} 个。
        <br />
        ★ <strong>主题名命中 ≠ 结构对应</strong>；<strong>未覆盖 ≠ 结构上不存在对应</strong>。
      </p>

      <div className="dl-draft-actions">
        <button type="button" className="dl-btn"
                onClick={() => onCopy('json', payloadJson)}>
          {copied === 'json' ? '已复制 ✓' : '复制 JSON'}
        </button>
        <button type="button" className="dl-btn"
                onClick={() => onCopy('md', payloadMd)}>
          {copied === 'md' ? '已复制 ✓' : '复制 Markdown'}
        </button>
        <button type="button" className="dl-btn dl-btn-ghost"
                onClick={() => setDraft(() => EMPTY_DRAFT)}>
          清空草稿
        </button>
        <span className="dl-draft-note">
          ★ 草稿无正式编号（<code>id: null</code>）· 状态 <code>DRAFT_NOT_REVIEWED</code> ·
          仅存本机、未上传
        </span>
      </div>

      <details className="dl-draft-preview">
        <summary>预览导出内容（可手动选中复制）</summary>
        <h5>JSON</h5>
        <textarea className="dl-draft-out" readOnly value={payloadJson}
                  rows={12} aria-label="草稿 JSON" />
        <h5>Markdown</h5>
        <textarea className="dl-draft-out" readOnly value={payloadMd}
                  rows={12} aria-label="草稿 Markdown" />
      </details>
    </details>
  );
}
