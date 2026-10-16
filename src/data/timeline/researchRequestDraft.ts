/**
 * 用户研究请求**草稿**（Research Request Draft）—— ThreeC 1.3 · Usage-Driven。
 *
 * ## 这是什么 / 不是什么
 * 用户在「查一个方向」之后，可能想把这个方向**变成一次真正的研究请求**。
 * 本模块把用户的输入 + 覆盖查询结果整理成一份**可交接的草稿**（JSON / Markdown）。
 *
 * ★★ **草稿不是研究请求本身**：
 *   - **不生成**正式 ID（`URO-*` / `R<NN>-*` 均属 Research 侧签发，见
 *     `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` §9 与
 *     `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §5）；
 *   - **不写库**、**不改** `current_candidates.json`、**不新增** Research Candidate / Campaign；
 *   - **不上传**（纯客户端字符串拼接，无网络、无 LLM）；
 *   - 必须经 **Human Review / Research 审查**后才可能成为正式任务。
 *
 * ## 语义边界（沿用 directionLookup，硬约束）
 * 「主题名命中 ≠ 结构对应」；「未覆盖 ≠ 结构上不存在对应」。
 * 本模块**只做字段整理与序列化**，不产生任何评分 / 排序 / 概率 / 推荐。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。localStorage 的读写由 UI 层负责（便于测试与降级）。
 */
import type { DirectionLookupResult } from './directionLookup';

/** 用户可填写的草稿字段（全部是**自然语言**，不做结构化推断） */
export interface ResearchRequestDraft {
  /** 方向（与查询一致；可编辑以细化，如「汽车 → 智能驾驶合规化」） */
  direction: string;
  /** 希望回答的**具体**研究问题（一行一条，允许空行） */
  researchQuestions: string;
  /** 为什么关注这个方向 */
  whyCare: string;
  /** 已知线索 / 来源（可选） */
  knownLeads: string;
  /** 希望调查的历史时间范围（如 2018-2025） */
  timeRange: string;
}

export const EMPTY_DRAFT: ResearchRequestDraft = {
  direction: '',
  researchQuestions: '',
  whyCare: '',
  knownLeads: '',
  timeRange: '',
};

/** ★ 单字段长度上限：草稿是**交接线索**，不是论文；超长应引导用户分次提交 */
export const DRAFT_FIELD_MAX = 2000;

/** 草稿必填项（缺了仍可导出，但会在 `missing` 里如实列出 —— 不阻塞、不伪造） */
export const DRAFT_REQUIRED_FIELDS: (keyof ResearchRequestDraft)[] = [
  'direction',
  'researchQuestions',
];

export function isDraftEmpty(d: ResearchRequestDraft): boolean {
  return DRAFT_REQUIRED_FIELDS.every((k) => !d[k].trim())
    && !d.whyCare.trim() && !d.knownLeads.trim() && !d.timeRange.trim();
}

/** 缺哪些必填项（用于 UI 提示；**不**阻止导出 —— 草稿允许不完整） */
export function missingDraftFields(d: ResearchRequestDraft): string[] {
  return DRAFT_REQUIRED_FIELDS.filter((k) => !d[k].trim()).map((k) =>
    k === 'direction' ? '研究方向' : '希望回答的研究问题',
  );
}

/** 把多行文本拆成非空条目（保留原文顺序，去首尾空白） */
export function toLines(s: string): string[] {
  return s
    .split('\n')
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

/** 草稿 → 可交接载荷（**确定性**：同输入同输出，便于用户核对与 diff） */
export interface ResearchRequestPayload {
  kind: 'threec_research_request_draft';
  draft_version: '0.1';
  /** ★ 明确：草稿**没有**正式 ID —— 不伪造 URO / R 编号 */
  id: null;
  status: 'DRAFT_NOT_REVIEWED';
  review_required: true;
  generated_at: string;
  request: {
    direction: string;
    research_questions: string[];
    why_care: string;
    known_leads: string[];
    time_range: string;
  };
  /** 与覆盖查询的衔接（四态之一 + 命中明细） */
  coverage_check: {
    query: string;
    verdict: DirectionLookupResult['verdict'];
    verdict_meaning: string;
    current_objects: { id: string; title: string; matched_on: string[] }[];
    historical_cases: { id: string; title: string; matched_on: string[] }[];
    resolution: DirectionLookupResult['resolution'];
  };
  /** 拟交接范围（对齐 intake 协议的 `task_scope`；**不含** `task_id` —— 由 Research 侧签发） */
  handoff: {
    intended_protocol: string;
    task_scope_sketch: {
      task_id: null;
      family_directions: string[];
      years: string;
      included_scope: string;
      excluded_scope: string;
    };
    drop_location: string;
    note: string;
  };
  /** 已知限制（必须在导出里出现，避免被当成结论） */
  known_limitations: string[];
  /** 本草稿做了什么 / 没做什么 */
  constraints: string[];
}

const VERDICT_MEANING: Record<DirectionLookupResult['verdict'], string> = {
  both: '当前与历史两侧都有覆盖 —— 可走完整工作流。',
  'current-only': '只有当前研究对象，历史侧没有命中 —— 历史结构对应可能为空。',
  'historical-only': '只有历史案例，当前侧没有研究对象 —— 无法回答「现在处于什么阶段」。',
  none: '两侧都未覆盖 —— 历史研究与当前研究对象里都没有命中。',
};

export const KNOWN_LIMITATIONS: string[] = [
  '★ 「主题名命中」**不等于**「结构对应」：命中的是主题名 / 标题，'
    + '真正的结构对应只由冻结 SA 解释给出。',
  '★ 「未覆盖」**不等于**「结构上不存在对应」：结构对应比的是机制 / 序列 / 事件结构，'
    + '一个历史里没有的方向，在建立当前研究对象后仍可能得到结构支持。',
  '★ 覆盖查询是**字符串匹配**，不做同义词 / 上位词推断，可能漏掉表述不同的同一方向。',
  '★ 本草稿由用户填写，**未经任何审查**；其中的「为什么关注」「已知线索」是用户主张，'
    + '不是已核实事实。',
  '★ 时间范围是**用户的期望**，与库内实际覆盖范围可能不一致（以覆盖查询结果为准）。',
];

export const DRAFT_CONSTRAINTS: string[] = [
  '本文件是**草稿**：未生成正式任务 ID，未写入数据库，未新增 Research Candidate / Campaign。',
  '必须经 Research 审查（Human Review）后才可能成为正式研究任务。',
  '纯客户端生成：未上传、无网络请求、无 LLM 参与。',
  // ★ 逐项否定：每项都紧邻否定词，便于人工与自动化检查（沿用项目既有约定）
  '不含评分；不做排序；不给概率；不做预测；不构成任何买卖信号。',
];

/**
 * 构造交接载荷。
 *
 * @param draft   用户填写的草稿
 * @param lookup  覆盖查询结果（可为 null —— 用户没查就直接写草稿时）
 * @param now     生成时间（ISO 字符串；由调用方注入，便于测试确定性）
 */
export function buildResearchRequestPayload(
  draft: ResearchRequestDraft,
  lookup: DirectionLookupResult | null,
  now: string,
): ResearchRequestPayload {
  const direction = draft.direction.trim() || lookup?.query || '';
  return {
    kind: 'threec_research_request_draft',
    draft_version: '0.1',
    id: null,
    status: 'DRAFT_NOT_REVIEWED',
    review_required: true,
    generated_at: now,
    request: {
      direction,
      research_questions: toLines(draft.researchQuestions),
      why_care: draft.whyCare.trim(),
      known_leads: toLines(draft.knownLeads),
      time_range: draft.timeRange.trim(),
    },
    coverage_check: {
      query: lookup?.query ?? '',
      verdict: lookup?.verdict ?? 'none',
      verdict_meaning: lookup ? VERDICT_MEANING[lookup.verdict] : '未执行覆盖查询（用户直接填写草稿）。',
      current_objects: (lookup?.current ?? []).map((h) => ({
        id: h.id, title: h.title, matched_on: h.matchedOn,
      })),
      historical_cases: (lookup?.historical ?? []).map((h) => ({
        id: h.id, title: h.title, matched_on: h.matchedOn,
      })),
      resolution: lookup?.resolution ?? null,
    },
    handoff: {
      intended_protocol: 'research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md',
      task_scope_sketch: {
        task_id: null, // ★ 由 Research 侧签发，草稿不得伪造
        family_directions: direction ? [direction] : [],
        years: draft.timeRange.trim(),
        included_scope: direction ? `与「${direction}」相关的历史周期与当前研究对象` : '',
        excluded_scope: '待 Research 界定（草稿不得自行缩小或扩大研究边界）',
      },
      drop_location: 'research/intake/packages/<task_id>/（task_id 由 Research 侧签发后确定）',
      note: '★ 本 sketch 仅供研究侧起草参考，**不构成**任务边界；'
        + '正式边界由 Research 依据 intake 协议与 CMTR 口径确定。',
    },
    known_limitations: KNOWN_LIMITATIONS,
    constraints: DRAFT_CONSTRAINTS,
  };
}

/** 渲染人类可读 Markdown（便于直接粘贴进 issue / 邮件 / 研究交接单） */
export function renderResearchRequestMarkdown(p: ResearchRequestPayload): string {
  const L: string[] = [];
  L.push('# ThreeC 研究请求草稿（**未经审查**）');
  L.push('');
  L.push('> ★ 这是**草稿**，不是正式研究任务：没有正式 ID、未入库、未新增研究对象。');
  L.push('> 需经 Research 审查后才可能成为正式任务。');
  L.push('');
  L.push(`- 生成时间：\`${p.generated_at}\``);
  L.push(`- 草稿版本：\`${p.draft_version}\` · 状态：\`${p.status}\``);
  L.push(`- 正式 ID：**未分配**（\`id: null\`）`);
  L.push('');
  L.push('## 1. 研究方向');
  L.push('');
  L.push(p.request.direction ? `**${p.request.direction}**` : '（未填写）');
  L.push('');
  L.push('## 2. 希望回答的研究问题');
  L.push('');
  if (p.request.research_questions.length === 0) L.push('（未填写）');
  for (const q of p.request.research_questions) L.push(`- ${q}`);
  L.push('');
  L.push('## 3. 为什么关注这个方向');
  L.push('');
  L.push(p.request.why_care || '（未填写）');
  L.push('');
  L.push('## 4. 已知线索 / 来源');
  L.push('');
  if (p.request.known_leads.length === 0) L.push('（未填写）');
  for (const k of p.request.known_leads) L.push(`- ${k}`);
  L.push('');
  L.push('## 5. 希望调查的历史时间范围');
  L.push('');
  L.push(p.request.time_range || '（未填写）');
  L.push('');
  L.push('## 6. 覆盖查询结果（工具侧事实）');
  L.push('');
  L.push(`- 查询词：\`${p.coverage_check.query || '（未查询）'}\``);
  L.push(`- 结论：**${p.coverage_check.verdict}** —— ${p.coverage_check.verdict_meaning}`);
  L.push(`- 当前研究对象命中 ${p.coverage_check.current_objects.length} 个`
    + (p.coverage_check.current_objects.length
      ? `：${p.coverage_check.current_objects.map((o) => `${o.id}（${o.title}）`).join('；')}`
      : ''));
  L.push(`- 历史案例命中 ${p.coverage_check.historical_cases.length} 个`
    + (p.coverage_check.historical_cases.length
      ? `：${p.coverage_check.historical_cases.map((o) => `${o.id}（${o.title}）`).join('；')}`
      : ''));
  if (p.coverage_check.resolution) {
    const r = p.coverage_check.resolution;
    L.push(`- 名称解析：${r.matchedTheme
      ? `库内主题「${r.matchedTheme.name}」${r.root && r.root.name !== r.matchedTheme.name ? `（属「${r.root.name}」）` : ''}，`
        + `该主题下直接挂靠对象 ${r.directObjectCount} 个；根下共 ${r.rootObjectCount} 个`
      : `不在库内主题表中（库内共 ${r.taxonomySize} 个主题）`}`);
  }
  L.push('');
  L.push('## 7. 已知限制（**请勿把本草稿当作结论**）');
  L.push('');
  for (const t of p.known_limitations) L.push(`- ${t}`);
  L.push('');
  L.push('## 8. 本草稿的边界');
  L.push('');
  for (const t of p.constraints) L.push(`- ${t}`);
  L.push('');
  L.push('## 9. 拟交接（仅供 Research 起草参考）');
  L.push('');
  L.push(`- 目标协议：\`${p.handoff.intended_protocol}\``);
  L.push(`- 拟放置位置：\`${p.handoff.drop_location}\``);
  L.push(`- \`task_id\`：**未分配**（由 Research 侧签发）`);
  L.push(`- 拟 family_directions：${p.handoff.task_scope_sketch.family_directions.join(' / ') || '（未填写）'}`);
  L.push(`- 拟 years：${p.handoff.task_scope_sketch.years || '（未填写）'}`);
  L.push(`- 说明：${p.handoff.note}`);
  L.push('');
  return L.join('\n');
}
