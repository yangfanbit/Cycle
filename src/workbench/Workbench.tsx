/**
 * ThreeC 研究工作台（v0.77）—— 任务导向的**独立入口**，旧站 `/Cycle/` 退为只读档案。
 *
 * ★★ 方向纠正：默认主入口是「前瞻排程」（push / 事前）—— 系统主动推出
 * 接下来值得关注的板块 / 概念窗口 + 双轨理由；原来的「我提问 → 历史对照」
 * 降级为**历史检索**标签，只在用户想深挖某个已筛出的方向时使用。
 * T 时刻冻结记录保留（改称对照记录），用于「研究增量」验收。
 *
 * ★★ 口径（`docs/EVALUATION_FRAMEWORK_v0_1.md` + `docs/FRONTIER_CADENCE_v0_1.md`）：
 *  · 有效性 = **研究增量**，不是 5/10/20 日板块超额；
 *  · 默认页按 **G1→G4 研究浏览顺序**（产物已有分组，无分数、不是收益排序）；
 *  · 启发式内部打分**只在**主动打开的评估视图，且按需加载，不进入默认页；
 *  · 「值得关注」= 前置观察窗口 / 研究起点，**不是买卖点**。
 */
import { useMemo, useState } from 'react';
import raw from '@current/workbench_index_v0_1.json';
import frontierRaw from '@current/frontier_board_v0_1.json';
import calendarRaw from '@current/event_calendar_v0_1.json';
import type { EvalDoc, IndexDoc, PosthocEval, RecordType, UseRecord, WorkbenchItem } from './types';
import { FrontierView } from './FrontierView';
import type { FrontierDoc, EventCalendar } from './FrontierView';
import { EvalView } from './EvalView';
import {
  downloadText, exportBundle, freezeRecord, loadEvals, loadRecords,
  saveEval, saveRecord, searchItems,
} from './records';

const doc = raw as unknown as IndexDoc;
const frontierDoc = frontierRaw as unknown as FrontierDoc;
const eventCalendar = calendarRaw as unknown as EventCalendar;
const TYPES: RecordType[] = ['LEAD', 'CONFIRM', 'REJECT', 'NO_LEAD', 'BLOCKED', 'UI_FRICTION'];
const TYPE_LABEL: Record<RecordType, string> = {
  LEAD: '新线索', CONFIRM: '强化已有判断', REJECT: '放弃某方向',
  NO_LEAD: '带问题来但没得到线索', BLOCKED: '数据/口径受阻', UI_FRICTION: '页面没帮上忙',
};
const KIND_LABEL: Record<string, string> = {
  HISTORICAL_OBJECT: '历史研究对象', POLICY_EVENT: '公开政策事件', THEME_MAP_EVENT: '历史题材地图事件',
};

type Step = 'ask' | 'evidence' | 'record';
type View = 'frontier' | 'workbench' | 'eval';

export function Workbench() {
  const [view, setView] = useState<View>('frontier');
  const [step, setStep] = useState<Step>('ask');
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState('');
  const [limit, setLimit] = useState(30);
  const [selected, setSelected] = useState<WorkbenchItem | null>(null);
  const [frontierRef, setFrontierRef] = useState<string | null>(null);

  const [question, setQuestion] = useState('');
  const [verdict, setVerdict] = useState('');
  const [type, setType] = useState<RecordType>('LEAD');
  const [cluster, setCluster] = useState('');
  const [records, setRecords] = useState<UseRecord[]>(() => loadRecords());
  const [evals, setEvals] = useState<PosthocEval[]>(() => loadEvals());
  const [evalRecordId, setEvalRecordId] = useState('');
  const [evalVerdict, setEvalVerdict] = useState<PosthocEval['is_new_correspondence']>('UNVERIFIABLE');
  const [evalNote, setEvalNote] = useState('');

  const [evalDoc, setEvalDoc] = useState<EvalDoc | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  const results = useMemo(() => searchItems(doc.items, submitted), [submitted]);
  const related = useMemo(() => {
    if (!selected) return [];
    const ts = new Set(selected.themes ?? []);
    return doc.items.filter((x) => x.id !== selected.id
      && (x.themes ?? []).some((t) => ts.has(t))).slice(0, 6);
  }, [selected]);

  async function openEval() {
    setView('eval');
    if (evalDoc || evalLoading) return;
    setEvalLoading(true);
    setEvalError(null);
    try {
      const m = await import('@current/workbench_eval_basis_v0_1.json');
      setEvalDoc((m as { default?: EvalDoc }).default ?? (m as unknown as EvalDoc));
    } catch (e) {
      setEvalError(String(e));
    } finally {
      setEvalLoading(false);
    }
  }

  /** 从「值得关注」清单直接进入 T 时刻冻结：预填研究问题，不要求先检索 */
  function recordFromFrontier(title: string, id: string) {
    setQuestion(`「${title}」是否提示了一个值得继续研究的方向？我此前是否已考虑过？`);
    setFrontierRef(id);
    setSelected(null);
    setView('workbench');
    setStep('record');
  }

  function openEvidence(it: WorkbenchItem) {
    setSelected(it);
    setStep('evidence');
    if (!question) setQuestion(`「${it.title}」是否提示了一个值得继续研究的方向？`);
  }

  function freeze() {
    if (!question.trim() || !verdict.trim()) return;
    const r = freezeRecord({
      question, verdict_at_T: verdict, type, cluster_id: cluster,
      item_ref: selected?.id ?? frontierRef,
    }, doc, new Date(), records);
    setRecords(saveRecord(r));
    setVerdict('');
    setEvalRecordId(r.record_id);
    setStep('record');
  }

  function addEval() {
    if (!evalRecordId || !evalNote.trim()) return;
    setEvals(saveEval({
      record_id: evalRecordId, checked_at: new Date().toISOString(),
      is_new_correspondence: evalVerdict, note: evalNote.trim(),
    }));
    setEvalNote('');
  }

  return (
    <div className="wb">
      <header className="wb-head">
        <div>
          <h1>ThreeC 研究工作台</h1>
          <p className="wb-sub">
            系统先推出「接下来值得关注」的前置观察窗口 + 双轨理由；点进去才是证据与来源。
            用来检验「工具是否改善了研究」，不是看板块后来涨没涨。
          </p>
        </div>
        <nav className="wb-nav">
          <button type="button" className={view === 'frontier' ? 'is-active' : ''}
                  onClick={() => setView('frontier')} data-open-frontier="1">前瞻排程</button>
          <button type="button" className={view === 'workbench' ? 'is-active' : ''}
                  onClick={() => setView('workbench')} data-open-history="1">历史检索 / 记录</button>
          <button type="button" className={view === 'eval' ? 'is-active' : ''}
                  onClick={openEval} data-open-eval="1">内部评估视图</button>
          <a href="./index.html" className="wb-archive-link">历史档案视图（旧站）↗</a>
        </nav>
      </header>

      <p className="wb-caliber" data-caliber="1">
        <strong>有效性 = 研究增量</strong>（新线索率 / 耗时变化 / 事后可核性）。
        5/10/20 日板块超额只是<strong>行情附注</strong>，不参与验收。
        默认页按 <strong>G1→G4 研究浏览顺序</strong>（产物已有分组，无分数、不是收益排序）；
        启发式内部打分只在评估视图。<strong>「值得关注」= 前置观察窗口 / 研究起点，不是买卖点</strong>，
        具体的买卖决策由你自行做出。
        统计轨 as_of <code>{frontierDoc.tracks.statistical.as_of}</code>（季度） ·
        机制轨 as_of <code>{frontierDoc.tracks.mechanism.as_of}</code>（周更） ·
        检索索引 {doc.counts.total} 条。
      </p>

      {view === 'eval' ? (
        evalLoading ? <p className="wb-loading">内部评估数据按需加载中…</p>
          : evalError ? <p className="wb-error">加载失败：{evalError}（可切回「研究」重试）</p>
            : evalDoc ? <EvalView doc={evalDoc} />
              : <p className="wb-error">未加载到评估数据。</p>
      ) : view === 'frontier' ? (
        <FrontierView doc={frontierDoc} cal={eventCalendar} onRecord={recordFromFrontier} />
      ) : (
        <main className="wb-main">
          <ol className="wb-steps" data-steps="1">
            {([['ask', '① 我提问'], ['evidence', '② 看证据'], ['record', '③ 冻结判断']] as [Step, string][])
              .map(([s, label]) => (
                <li key={s}>
                  <button type="button" className={step === s ? 'is-active' : ''}
                          onClick={() => setStep(s)}>{label}</button>
                </li>
              ))}
          </ol>

          {step === 'ask' && (
            <section className="wb-panel" data-step="ask">
              <label className="wb-field">
                <span>你正在研究什么方向 / 问题？</span>
                <input value={query} onChange={(e) => setQuery(e.target.value)}
                       onKeyDown={(e) => { if (e.key === 'Enter') { setSubmitted(query); setLimit(30); } }}
                       placeholder="例如：流感、海上风电、医用耗材、算电协同" data-search="" />
              </label>
              <button type="button" className="wb-btn primary"
                      onClick={() => { setSubmitted(query); setLimit(30); }}>
                检索历史对照
              </button>
              <p className="wb-hint">
                只按<strong>标题 / 主题 / 关联理由</strong>做字面匹配，不是语义理解；
                结果<strong>按日期倒序</strong>（产物顺序），<strong>这里不引入优先级排序</strong>；
                默认页「前瞻排程」的 G1→G4 分组顺序是另一件事，两者不混读。
              </p>
              {submitted && (
                <>
                  <p className="wb-count" data-result-count={results.length}>
                    「{submitted}」命中 <strong>{results.length}</strong> 条 · 展示 {Math.min(limit, results.length)} 条
                  </p>
                  {results.length === 0 && (
                    <p className="wb-empty" data-empty="1">
                      <strong>当前采集范围未发现</strong>与该词相关的记录 —— 这是覆盖缺口，
                      <strong>不代表</strong>现实中没发生；可换词或直接记一条 <code>NO_LEAD</code>。
                    </p>
                  )}
                  <ul className="wb-results">
                    {results.slice(0, limit).map((it) => (
                      <li key={it.id} data-item={it.id} data-uncertainty={it.uncertainty}>
                        <div className="wb-r1">
                          <span className="wb-kind">{KIND_LABEL[it.kind] ?? it.kind}</span>
                          <span className="wb-date">{it.date ?? '—'}</span>
                          <span className={`wb-unc u-${it.uncertainty.toLowerCase()}`}>
                            不确定性 {it.uncertainty}
                          </span>
                        </div>
                        <button type="button" className="wb-linkbtn" onClick={() => openEvidence(it)}>
                          {it.title}
                        </button>
                        <p className="wb-why">{it.why}</p>
                        <p className="wb-src">{it.source.name ?? '内部对象'}
                          {it.url ? ' · 有原始 URL 可核' : ' · 内部结构化对象，无外部 URL'}</p>
                      </li>
                    ))}
                  </ul>
                  {results.length > limit && (
                    <button type="button" className="wb-btn" onClick={() => setLimit(limit + 30)}>
                      再显示 30 条
                    </button>
                  )}
                </>
              )}
            </section>
          )}

          {step === 'evidence' && (
            <section className="wb-panel" data-step="evidence">
              {!selected ? (
                <p className="wb-empty">请先在第 ① 步选择一条线索。</p>
              ) : (
                <>
                  <h2>{selected.title}</h2>
                  <p className="wb-meta">
                    {KIND_LABEL[selected.kind]} · {selected.date ?? '—'} · 来源 {selected.source.name}
                    {selected.source.publisher ? `（${selected.source.publisher}）` : ''}
                  </p>
                  <div className="wb-evidence">
                    <p><strong>为什么算相关</strong>：{selected.why}</p>
                    <p><strong>不确定性 {selected.uncertainty}</strong>：{selected.uncertainty_reason}</p>
                    <p><strong>原始来源</strong>：{selected.url ? (
                      <a href={selected.url} target="_blank" rel="noreferrer noopener">{selected.url}</a>
                    ) : '内部结构化对象，无外部报道 URL；可在旧站「历史题材 / 事件」中查看对象详情。'}</p>
                    {selected.themes.length > 0 && (
                      <p><strong>主题标签</strong>：{selected.themes.join(' · ')}</p>
                    )}
                    {selected.status && <p><strong>市场状态</strong>：{selected.status}（只作留档，不构成结论）</p>}
                  </div>
                  <p className="wb-hint">
                    这一屏只给<strong>可核证据与缺口</strong>，不给结论、不给优先级、不推断因果。
                  </p>
                  {related.length > 0 && (
                    <div className="wb-related">
                      <h3>同主题的其它线索（{related.length}）</h3>
                      <ul>
                        {related.map((x) => (
                          <li key={x.id}>
                            <button type="button" className="wb-linkbtn" onClick={() => openEvidence(x)}>
                              {x.title}
                            </button>
                            <span className="wb-date"> · {x.date ?? '—'}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <button type="button" className="wb-btn primary" onClick={() => setStep('record')}>
                    记录我的判断 →
                  </button>
                </>
              )}
            </section>
          )}

          {step === 'record' && (
            <section className="wb-panel" data-step="record">
              <h2>T 时刻冻结</h2>
              <p className="wb-hint">
                在<strong>看到后续行情或结果之前</strong>写下判断。正文写后不改；
                事后核对存在<strong>独立区域</strong>，不会修改这里。
              </p>
              <label className="wb-field"><span>研究问题</span>
                <input value={question} onChange={(e) => setQuestion(e.target.value)} data-field="question" />
              </label>
              <label className="wb-field"><span>T 时刻的判断（线索是什么 / 我此前是否考虑过 / 准备做什么）</span>
                <textarea value={verdict} onChange={(e) => setVerdict(e.target.value)}
                          rows={4} data-field="verdict" />
              </label>
              <div className="wb-formrow">
                <label className="wb-field"><span>类型（负向同等重要）</span>
                  <select value={type} onChange={(e) => setType(e.target.value as RecordType)}
                          data-field="type">
                    {TYPES.map((t) => <option key={t} value={t}>{TYPE_LABEL[t]}</option>)}
                  </select>
                </label>
                <label className="wb-field"><span>cluster_id（同一题材/周填同一个）</span>
                  <input value={cluster} onChange={(e) => setCluster(e.target.value)}
                         placeholder="可空" data-field="cluster" />
                </label>
              </div>
              <button type="button" className="wb-btn primary" disabled={!question.trim() || !verdict.trim()}
                      onClick={freeze} data-freeze="1">冻结这条记录</button>
              {(selected || frontierRef) && (
                <p className="wb-hint" data-record-ref="1">
                  关联线索：<code>{selected?.id ?? frontierRef}</code>
                  {frontierRef ? '（来自前瞻排程）' : ''}
                </p>
              )}

              <h3>已冻结正文（{records.length}）</h3>
              {records.length === 0 ? <p className="wb-empty">还没有记录。</p> : (
                <ul className="wb-records" data-records={records.length}>
                  {records.map((r) => (
                    <li key={r.record_id}>
                      <strong>{r.record_id}</strong> · {TYPE_LABEL[r.type]} · {r.frozen_at.slice(0, 16).replace('T', ' ')}
                      {r.cluster_id ? ` · cluster ${r.cluster_id}` : ''}
                      <p>{r.question}</p><p>{r.verdict_at_T}</p>
                    </li>
                  ))}
                </ul>
              )}

              <div className="wb-posthoc" data-posthoc="1">
                <h3>事后核对（独立存储，不改正文）</h3>
                <label className="wb-field"><span>对应记录</span>
                  <select value={evalRecordId} onChange={(e) => setEvalRecordId(e.target.value)}>
                    <option value="">选择…</option>
                    {records.map((r) => <option key={r.record_id} value={r.record_id}>{r.record_id}</option>)}
                  </select>
                </label>
                <label className="wb-field"><span>是否为新的历史对应</span>
                  <select value={evalVerdict} onChange={(e) =>
                    setEvalVerdict(e.target.value as PosthocEval['is_new_correspondence'])}>
                    <option value="YES">是（可核）</option>
                    <option value="NO">否（本来就知道 / 不成立）</option>
                    <option value="UNVERIFIABLE">无法核实</option>
                  </select>
                </label>
                <label className="wb-field"><span>核对说明</span>
                  <textarea value={evalNote} onChange={(e) => setEvalNote(e.target.value)} rows={3} />
                </label>
                <button type="button" className="wb-btn" disabled={!evalRecordId || !evalNote.trim()}
                        onClick={addEval}>保存核对</button>
                <p className="wb-hint">已有核对 {evals.length} 条；正文 {records.length} 条、核对 {evals.length} 条分别计数。</p>
              </div>

              <button type="button" className="wb-btn" data-export="1"
                      onClick={() => downloadText('threec-real-use.json', exportBundle())}>
                导出 JSON（放到 .tmp/real_use/records/，不入库）
              </button>
            </section>
          )}
        </main>
      )}

      <footer className="wb-foot">
        前瞻排程 <code>frontier_board_v0_1.json</code>（{frontierDoc.items.length} 条）+
        日历 <code>event_calendar_v0_1.json</code>（{eventCalendar.entries.length} 条）
        · 由既有产物确定性派生，<code>build_frontier_board_v0_1.py --check</code> 逐字段复算 ·
        检索索引 <code>workbench_index_v0_1.json</code>（{doc.counts.total} 条，
        其中 {doc.counts.with_external_url} 条带原始 URL）·
        url 为 null 表示内部结构化对象，<strong>不编造外部来源</strong>。
      </footer>
    </div>
  );
}
