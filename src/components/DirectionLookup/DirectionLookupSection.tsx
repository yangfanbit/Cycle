import { useEffect, useMemo, useState } from 'react';
import {
  coveredTerms,
  lookupDirection,
  type DirectionLookupResult,
} from '../../data/timeline/directionLookup';
import {
  DRAFT_FIELD_MAX,
  EMPTY_DRAFT,
  buildLinkedDraft,
  buildResearchRequestPayload,
  isDraftBlank,
  missingDraftFields,
  renderResearchRequestMarkdown,
  type ResearchRequestDraft,
  type ResearchRequestPayload,
} from '../../data/timeline/researchRequestDraft';
import { copyFailureMessage, copyTextToClipboard } from '../../data/timeline/clipboard';
import {
  browserDraftStorage,
  loadDraft,
  saveDraft,
  shouldAutoFillDirection,
  type DraftStorage,
  type LoadDraftResult,
  type SaveDraftResult,
} from '../../data/timeline/researchRequestDraftStorage';
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
 *
 * ★ v0.7：`themeCount` 由**数据**注入（原先硬编码「44 个主题名」，实测已增至 59）——
 *   数字类声明必须随数据走，否则又会变成过期文案。
 */
export function noneExplain(themeCount: number): string[] {
  return [
    `「未覆盖」指的是**主题名**：库内 ${themeCount} 个主题名里没有它，当前研究对象里也没有它。`,
    '★ 但这**不等于**「结构上无对应」。结构对应比的是**机制 / 序列 / 事件结构**，不是名字 ——',
    '实测：一个历史研究里完全没有的方向（文化传媒），在建立当前研究对象后，仍得到了 1 条结构支持。',
    '**要拿到结构层面的答案，需要先为该方向建立一轮研究（当前研究对象）**；在那之前，',
    '本工具只能如实说「还没法比」，而不是「比过了、不成立」。',
  ];
}

/**
 * ★ v0.7：草稿的读写**全部**走 `researchRequestDraftStorage`（纯函数 + 可注入接口）。
 *   组件只负责：把存储结果翻译成 UI 状态（是否可用 / 是否保存成功 / 是否有坏数据）。
 */
export function DirectionLookupSection({
  source,
  dataset,
  onOpenHistoricalCase,
  draftStorage,
}: {
  source: TimelineDataSource | null;
  dataset: CurrentCandidateDataset | null;
  onOpenHistoricalCase?: (campaignId: string) => void;
  /** ★ 测试可注入内存实现；默认走浏览器 localStorage（不可用 → null） */
  draftStorage?: DraftStorage | null;
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
   * 研究请求草稿（ThreeC 1.3 · v0.7 生命周期修复）
   *
   * ★ 草稿只存在**本机**；不上传、不写库、不生成正式 ID。
   * ★ v0.7 修复（缺陷 #1）：清空必须**真的清空** —— 用 `userClearedFor` 记住
   *   「用户为哪个查询显式清空过」，自动回填**不得**把它填回来。
   * ------------------------------------------------------------------ */
  const storage = useMemo<DraftStorage | null>(
    () => (draftStorage !== undefined ? draftStorage : browserDraftStorage()),
    [draftStorage],
  );
  /** 首屏读取（只在挂载时一次）—— 保留完整结果以便诚实披露「坏数据 / 不可用」 */
  const [initialLoad] = useState<LoadDraftResult>(() => loadDraft(storage));
  const [draft, setDraft] = useState<ResearchRequestDraft>(() =>
    initialLoad.status === 'loaded' ? initialLoad.draft : { ...EMPTY_DRAFT });
  /** ★ 保存结果（诚实披露：失败绝不假装成功） */
  const [saveState, setSaveState] = useState<SaveDraftResult | null>(null);
  /** ★ 用户显式清空时对应的查询词（防回填） */
  const [userClearedFor, setUserClearedFor] = useState('');
  const [copied, setCopied] = useState<'json' | 'md' | null>(null);
  /** ★ v0.8：复制失败原因（null = 未失败）—— 失败**必须**告知用户并给下一步 */
  const [copyError, setCopyError] = useState<string | null>(null);
  /** ★ v0.8：导出预览是否展开（复制失败时自动展开，用户不必猜下一步） */
  const [previewOpen, setPreviewOpen] = useState(false);

  // 持久化：每次草稿变化写一次（空草稿 → 删除记录）
  useEffect(() => {
    setSaveState(saveDraft(storage, draft));
  }, [storage, draft]);

  // ★★ 自动回填（v0.7 修复）：**只对空草稿**、且用户**没有**为当前查询清空过。
  //    v0.6 的判定是「方向字段为空就填」→ 清空后立刻被填回、手删方向也被填回。
  useEffect(() => {
    if (!result) return;
    if (!shouldAutoFillDirection({
      query: result.query,
      direction: draft.direction,
      draftEmpty: isDraftBlank(draft),
      userClearedFor,
    })) return;
    // ★ v0.8：与「以当前查询新建草稿」**共用同一个纯函数** —— 一次性写全
    //   direction + linkedQuery + linkedAt + linkedCoverage，不依赖后续 effect。
    setDraft((d) => buildLinkedDraft(result.query, result, new Date().toISOString()));
  }, [result, draft, userClearedFor]);

  const payload = useMemo(
    () => buildResearchRequestPayload(draft, result, new Date().toISOString()),
    [draft, result],
  );
  const payloadJson = useMemo(() => JSON.stringify(payload, null, 2), [payload]);
  const payloadMd = useMemo(() => renderResearchRequestMarkdown(payload), [payload]);

  const copy = async (kind: 'json' | 'md', text: string) => {
    const outcome = await copyTextToClipboard(text);
    if (outcome.ok) {
      // ★ 只有**真的成功**才显示「已复制」
      setCopyError(null);
      setCopied(kind);
      window.setTimeout(() => setCopied((c) => (c === kind ? null : c)), 2000);
      return;
    }
    // ★ v0.8：失败 → 明确告知 + **自动展开导出预览**，用户能立刻手动选中复制
    setCopied(null);
    setCopyError(copyFailureMessage(outcome));
    setPreviewOpen(true);
  };

  /** ★ 清空草稿：表单 + 关联状态 + 持久化 + 复制态**一起**清，并记住「为哪个查询清空过」 */
  const clearDraft = () => {
    setDraft({ ...EMPTY_DRAFT });
    setCopied(null);
    setCopyError(null);
    setUserClearedFor(query);
  };

  /**
   * ★ 以当前查询**新建**草稿（v0.8 修复：**一次性建立完整关联**）。
   *
   * v0.7 只设 `direction`，指望随后的自动回填 effect 补关联 —— 而 effect 的守卫是
   * `isDraftBlank(draft)`：`direction` 非空 ⇒ **不 blank** ⇒ effect **不跑**
   * ⇒ 关联**永远不建立**（导出仍显示「未关联任何查询」）。
   * → 现在直接调 `buildLinkedDraft()` 写全四个字段。
   */
  const relinkToCurrentQuery = () => {
    if (!result) return;
    setDraft(buildLinkedDraft(result.query, result, new Date().toISOString()));
    setCopied(null);
    setCopyError(null);
    setUserClearedFor('');
  };

  /** 当前查询是否与草稿关联的查询不同（★ 只比字符串；用于决定是否提示/提供「新建」按钮） */
  const queryChanged = Boolean(result)
    && Boolean(draft.linkedQuery)
    && result!.query !== draft.linkedQuery;

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
              {noneExplain(result.resolution?.taxonomySize ?? 0).map((t, i) => (
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

      {/* ★ 研究请求草稿（v0.7）：
          · **有查询结果**时出现（把方向变成请求）
          · **草稿非空**时也出现 —— 这样**刷新/重进页面后恢复的草稿可见可编辑**
            （v0.6 只在有 `result` 时渲染 → 恢复的草稿在用户再查一次之前**看不见**，
             再查一次时新查询结果又会冒充原证据） */}
      {(result || !isDraftBlank(draft)) && (
        <ResearchRequestDraftBlock
          lookup={result}
          draft={draft}
          setDraft={setDraft}
          payload={payload}
          payloadJson={payloadJson}
          payloadMd={payloadMd}
          copied={copied}
          onCopy={copy}
          onClear={clearDraft}
          onRelink={relinkToCurrentQuery}
          queryChanged={queryChanged}
          saveState={saveState}
          loadState={initialLoad}
          copyError={copyError}
          previewOpen={previewOpen}
          onPreviewOpenChange={setPreviewOpen}
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
  onClear,
  onRelink,
  queryChanged,
  saveState,
  loadState,
  copyError,
  previewOpen,
  onPreviewOpenChange,
}: {
  /** 当前查询结果（未查询 → null）。★ **不是**证据来源，证据在 `draft.linkedCoverage` */
  lookup: DirectionLookupResult | null;
  draft: ResearchRequestDraft;
  setDraft: (updater: (d: ResearchRequestDraft) => ResearchRequestDraft) => void;
  payload: ResearchRequestPayload;
  payloadJson: string;
  payloadMd: string;
  copied: 'json' | 'md' | null;
  onCopy: (kind: 'json' | 'md', text: string) => void;
  /** ★ 清空：表单 + 关联 + 持久化 + 复制态一起清，且不得被自动回填 */
  onClear: () => void;
  /** ★ 以当前查询**新建**草稿（显式改绑，一次性建立完整关联） */
  onRelink: () => void;
  /** 当前查询与草稿关联查询是否不同（只比字符串） */
  queryChanged: boolean;
  /** 保存结果（null = 尚未写）—— ★ 失败必须显示「未保存」 */
  saveState: SaveDraftResult | null;
  /** 首屏读取结果 —— ★ 坏数据 / 存储不可用必须披露 */
  loadState: LoadDraftResult;
  /** ★ 复制失败的一句话（null = 未失败）—— 失败必须告知，不得假装成功 */
  copyError: string | null;
  /** ★ 导出预览是否展开（复制失败时自动展开） */
  previewOpen: boolean;
  /** 用户手动开合预览 */
  onPreviewOpenChange: (open: boolean) => void;
}) {
  const missing = missingDraftFields(draft);
  const set = (k: keyof ResearchRequestDraft) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => setDraft((d) => ({ ...d, [k]: e.target.value.slice(0, DRAFT_FIELD_MAX) }));

  const storageUnavailable = saveState?.ok === false && saveState.reason === 'unavailable';
  const saveFailed = saveState?.ok === false && saveState.reason !== 'unavailable';
  const cc = payload.coverage_check;

  return (
    <details className="dl-draft" open>
      <summary>
        把「{lookup?.query || draft.linkedQuery || '这个方向'}」变成研究请求草稿（可导出交接）
      </summary>
      <p className="dl-draft-lead">
        研究侧当前<strong>只覆盖研究侧选定的方向</strong>。若你关心的方向不在其中，
        可以在这里写下你<strong>真正想回答的问题</strong>，导出成一份
        <strong>草稿</strong>交给研究流程。
        <strong>草稿不会自动进入研究库</strong>，也<strong>不会自动获得正式编号</strong> ——
        它只是你的诉求记录（存在本机，不上传）。
      </p>

      {/* ★★ 存储状态必须**诚实**：不可用 / 保存失败 / 读到坏数据，都要说，不得假装成功 */}
      {(storageUnavailable || saveFailed || loadState.status === 'corrupt'
        || (loadState.status === 'loaded' && loadState.issues.length > 0)) && (
        <p className="dl-draft-storage" role="status">
          {storageUnavailable && <>★ <strong>本机存储不可用</strong>（浏览器隐私模式或被禁用）——
            草稿仍可填写与导出，但<strong>刷新后会丢失</strong>，请先复制内容。</>}
          {saveFailed && <>★ <strong>草稿未能保存到本机</strong>（{saveState!.reason === 'write_failed'
            ? '存储写入失败（可能已满）' : '存储删除失败'}）—— 当前内容仍在本页可用，
            <strong>刷新后可能丢失</strong>，请先复制内容。</>}
          {loadState.status === 'corrupt' && <>★ 检测到<strong>无法使用的旧草稿记录</strong>
            （{loadState.reason === 'json' ? 'JSON 语法损坏'
              : loadState.reason === 'shape' ? '结构不合法' : '内容过大'}）→
            已<strong>忽略</strong>该记录，未覆盖你的新输入。</>}
          {loadState.status === 'loaded' && loadState.issues.length > 0 && (
            <>★ 恢复草稿时发现<strong>不合法的字段</strong>，已安全降级（
              {loadState.issues.slice(0, 3).join('；')}
              {loadState.issues.length > 3 ? ` 等 ${loadState.issues.length} 项` : ''}）。</>
          )}
        </p>
      )}

      <div className="dl-draft-form">
        <label className="dl-draft-field">
          <span>研究方向（可细化，不必与查询词相同）</span>
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

      {/* ★★ 关联披露：请求原文 ↔ 查询证据**分开说**（不做相似度判断，只陈述事实） */}
      <p className="dl-draft-facts">
        <strong>本草稿的覆盖查询证据</strong>：
        {cc.executed ? (
          <>
            属于查询 <code>{payload.linkage.linked_query}</code>
            （{payload.linkage.linked_at ? payload.linkage.linked_at.slice(0, 19).replace('T', ' ') : '时间未记录'}）：
            <span className={`dl-verdict dl-v-${cc.verdict}`}>{cc.verdict}</span>
            —— {cc.verdict_meaning}
            当前研究对象 {cc.current_objects.length} 个 ·
            历史案例 {cc.historical_cases.length} 个。
          </>
        ) : (
          <>★ <strong>未关联任何查询</strong> —— 导出内容里<strong>没有</strong>查询证据。
            这不代表「未覆盖」，只代表「没查过」。</>
        )}
        {queryChanged && (
          <>
            <br />
            ★ 当前界面的查询是 <code>{payload.linkage.current_query}</code>，
            <strong>与本草稿的证据不同</strong> —— 新查询结果<strong>未</strong>附加到本草稿。
          </>
        )}
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
        {lookup && (
          <button type="button" className="dl-btn"
                  onClick={onRelink}
                  title="以当前查询重新建立草稿与关联（会清空当前草稿内容）">
            以当前查询新建草稿
          </button>
        )}
        <button type="button" className="dl-btn dl-btn-ghost" onClick={onClear}>
          清空草稿
        </button>
      </div>

      {/* ★★ v0.8：复制失败必须**明确告知 + 给下一步**（不显示「已复制」假成功） */}
      {copyError && (
        <p className="dl-draft-copy-error" role="alert">
          {copyError}
          <br />
          下方导出预览<strong>已自动展开</strong> —— 请**手动选中复制**（内容与你刚才点的那份完全相同）。
        </p>
      )}

      <p className="dl-draft-note">
        ★ 草稿无正式编号（<code>id: null</code>）· 状态 <code>DRAFT_NOT_REVIEWED</code> ·
        {storageUnavailable
          ? <strong>本机存储不可用 —— 刷新后会丢失</strong>
          : saveFailed
            ? <strong>未保存到本机 —— 刷新后可能丢失</strong>
            : <>仅存本机、未上传{saveState?.ok ? '（已保存）' : ''}</>}
      </p>

      <details
        className="dl-draft-preview"
        open={previewOpen}
        onToggle={(e) => onPreviewOpenChange(e.currentTarget.open)}
      >
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
