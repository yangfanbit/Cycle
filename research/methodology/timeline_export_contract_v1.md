# Timeline Export Contract v1.0（Research → Cycle 唯一接口）

> 本文件定义 Cycle-Research → Cycle Timeline 的**唯一**数据交换契约（`timeline_export_v1.json`）。
> 版本：`timeline_export_version = "1.0"`。未来修改走 1.1 / 2.0，保持向后兼容。
> 项目初心：让 Cycle Timeline 直接消费历史 Campaign / Research Signal / Research Candidate / Event / Security / Rule，服务"看历史时间轴 → 找当前相似阶段 → 提前观察"。

---

## 1. Contract

顶层结构（11 个字段，白名单校验，禁止额外字段）：

```json
{
  "contract": "timeline_export",
  "timeline_export_version": "1.0",
  "generated_at": "ISO 时间戳",
  "source_commit": "git commit（数据来源可追溯）",
  "project": "Cycle-Research",
  "rules": [ ... ],
  "signals": [ ... ],
  "campaigns": [ ... ],
  "research_candidates": [ ... ],
  "events": [ ... ],
  "securities": [ ... ]
}
```

- **不出现** `export_version`（版本语义唯一为 `timeline_export_version`）。
- **不出现** `source_project`（统一为 `project`）。

## 2. Version

- 当前：`"1.0"`（canonical）。
- 只允许一个版本字段；禁止新旧版本并存。
- 未来：`1.1`（向后兼容新增可选字段）、`2.0`（破坏性变更，需迁移文档）。

## 3. Rules

```json
{
  "rule_id": "rule_auto_summer",
  "name": "6-8月汽车季节性观察窗口",
  "base_pattern": "汽车",
  "definition": "Historical Observation Window（历史观察窗口），非固定买入窗口",
  "observation_window": "Q2-Q3（4-9月），6-8月为名义窗口；允许漂移"
}
```

## 4. Signals

扁平数组。归属：**campaign_id XOR research_candidate_id**（二选一，必须归属其一）。

```json
{ "type": "EARLY_SIGNAL", "date": "2023-08-29", "confidence": "low", "research_candidate_id": "RC-2023-HUAWEI" }
{ "type": "THEME_FORMING", "date": "2022-05-23", "confidence": "high", "campaign_id": "C-2022-POLICY" }
```

`type ∈ {EARLY_SIGNAL, THEME_FORMING, CONFIRMATION_CANDIDATE}`。Research Signal 是研究层信息，不是交易信号。

## 5. Campaigns

正式 HistoricalCampaign（不包含 research candidates）：

```json
{
  "campaign_id": "C-2022-POLICY",
  "rule_id": "rule_auto_summer",
  "year": 2022,
  "start_date": "2022-04-27",
  "peak_date": "2022-06-10",
  "end_date": "2022-08-31",
  "status": "conflict",
  "confidence": "medium",
  "classification": "theme_campaign",
  "strength": "strong",
  "result": "positive",
  "themes": [{ "name": "...", "theme_type": "concept", "role": "main" }],
  "event_ids": ["EV-2022-01"],
  "security_ids": ["BIDI"],
  "research_status": "CONFLICT",
  "theme_cycle_id": "auto_policy_2022",
  "promotion_status": "READY_FOR_HUMAN_REVIEW",
  "first_signal_date": "2022-04-27",
  "broad_confirmation_date": "2022-06-01",
  "first_decline_date": "2022-07-01",
  "conflicts": [{ "field": "start_date", "candidate_a": {...}, "candidate_b": {...} }],
  "notes": "..."
}
```

- `event_ids` / `security_ids` 引用顶层 `events` / `securities`（**禁止**把整个证券表复制进每个 Campaign）。
- 日期为研究候选日期（candidate date），除非 `status=verified`，否则**不伪装成 Verified**。

## 6. Research Candidates

不进入 `campaigns` 的候选（Cycle Preview 可展示）：

```json
{
  "campaign_id": "RC-2023-HUAWEI",
  "rule_id": "rule_auto_summer",
  "year": 2023,
  "title": "Huawei Auto 2023（华为汽车 / AITO M7 / ADS2.0）",
  "start_date": "2023-09-12",
  "peak_date": null,
  "end_date": null,
  "themes": [...],
  "event_ids": [...],
  "security_ids": [...],
  "early_signal": "2023-08-29",
  "research_status": "PROVISIONAL",
  "theme_cycle_id": "auto_intelligence_2023",
  "conflicts": [],
  "notes": "..."
}
```

当前候选：`RC-2023-HUAWEI`、`RC-2024-SECONDARY`。候选**没有**生产 `status` 字段，只有 `research_status`；**不得伪装 verified**。

## 7. Events

扁平数组，必须知道属于谁：

```json
{ "event_id": "EV-2022-01", "name": "...", "date": "2022-05-23", "event_type": "policy", "role": "trigger", "campaign_id": "C-2022-POLICY", "research_candidate_id": null }
```

- 全局事件（如 2018 反例、2024-10-10 特斯拉发布会）：`campaign_id = null`，不强行绑定。
- research candidate 事件：`research_candidate_id = "RC-..."`。

## 8. Securities

扁平数组，**必须知道属于谁**（campaign_id 或 research_candidate_id，禁止无归属）：

```json
{ "security_id": "SAILISI", "name": "赛力斯", "ticker": "601127", "exchange": "SH", "role": "leader", "campaign_id": null, "research_candidate_id": "RC-2023-HUAWEI" }
```

同一证券可属于多个 owner（如 比亚迪 → C-2020-NEV / C-2021-NEV / C-2022-POLICY），每 (security_id, owner) 一条。

## 9. Status（生产兼容）

生产兼容状态（Cycle 消费）——小写枚举：

| status | 含义 |
|---|---|
| `verified` | 人工最终复核确认，日期为 Verified Date |
| `provisional` | 研究预览可用（PROVISIONAL），非最终事实 |
| `conflict` | 存在日期口径冲突，保留候选双方 |
| `preview` | Research Candidate 预览（只出现在 research_candidates） |

## 10. Research Status（研究层）

大写枚举（research metadata，非 HistoricalCampaign schema 字段）：

| research_status | 含义 |
|---|---|
| `PROVISIONAL` | 主题可识别 + 证据/来源齐 + 日期有依据，未人工复核 |
| `CONFLICT` | 日期口径冲突，必须带 `conflicts`（candidate_a/candidate_b） |
| `INSUFFICIENT` | 来源不足/无法判断，不编造 |

**不混淆**：`status`（生产小写）≠ `research_status`（研究大写）。promotion 词汇（如 `READY_FOR_HUMAN_REVIEW`）单独命名为 `promotion_status`（research metadata），不再占用 `status`。

## 11. Compatibility

- **Cycle-compatible fields**：`campaign_id / rule_id / year / start_date / peak_date / end_date / status / confidence / classification / strength / result / themes / events / securities`（经 `event_ids`/`security_ids` 引用）。
- **Research-only metadata**（明确不是 HistoricalCampaign schema 字段，可进入 Export 但标注来源）：`research_status / theme_cycle_id / promotion_status / first_signal_date / broad_confirmation_date / first_decline_date / conflicts / notes / early_signal / title / event_ids / security_ids`。
- 禁止把 research-only 字段伪装成 Cycle 正式字段。

## 12. Example（最小可消费片段）

```json
{
  "contract": "timeline_export",
  "timeline_export_version": "1.0",
  "generated_at": "2026-09-13T11:49:39",
  "source_commit": "49797cc...",
  "project": "Cycle-Research",
  "rules": [{ "rule_id": "rule_auto_summer", "base_pattern": "汽车", "definition": "Historical Observation Window" }],
  "signals": [{ "type": "EARLY_SIGNAL", "date": "2022-04-27", "confidence": "medium", "campaign_id": "C-2022-POLICY" }],
  "campaigns": [{ "campaign_id": "C-2022-POLICY", "rule_id": "rule_auto_summer", "year": 2022, "status": "conflict", "research_status": "CONFLICT", "conflicts": [{"field": "start_date", "candidate_a": {...}, "candidate_b": {...}}] }],
  "research_candidates": [{ "campaign_id": "RC-2023-HUAWEI", "research_status": "PROVISIONAL" }],
  "events": [{ "event_id": "EV-2022-01", "campaign_id": "C-2022-POLICY" }],
  "securities": [{ "security_id": "BIDI", "campaign_id": "C-2022-POLICY" }]
}
```

## 13. Backward Compatibility

- v1.0 为 canonical；v1.0 中任何字段不允许被 v1.1 删除或改变语义（只允许新增可选字段）。
- 破坏性变更必须升主版本（2.0）并提供迁移说明。
- 校验器 `scripts/validate_timeline_export.py` 是接口守门人：任何字段漂移都会 FAIL。
- Cycle Adapter 应只读取 `timeline_export_version` 判定兼容版本，不读取其他版本字段。

---

**生成**：`python scripts/batch_auto_research.py`（只读数据库，不写 DB；不改 SQLite schema）。
**校验**：`python scripts/validate_timeline_export.py`（14 项 + RC-2023-HUAWEI 关键测试）。
