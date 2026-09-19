# 05_OUTPUT/ — 唯一正式交付位置

> **本目录是 Research Worker 的唯一正式交付位置。**
> 交付结构必须严格对齐 `01_PROTOCOL/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §5.3。

---

## 标准最终交付

```text
05_OUTPUT/
├─ manifest.json               # task_id / research_round_id / generated_at / source_commit /
│                              #   task_scope / macro_theme_proposals / cross_task_notes
├─ coverage.md                 # 人类可读：本任务覆盖了什么、没覆盖什么
├─ candidates.json             # campaign_candidates
├─ evidence.json               # evidence
├─ sources.json                # sources
├─ securities.json             # securities
├─ exclusions.json             # exclusions（★ 强制，不得为空）
├─ conflicts.json              # conflicts
├─ research_questions.json     # research_questions
├─ quality_summary.json        # quality_summary（no_quantity_kpi_acknowledged 必须 true）
└─ checksums.sha256            # 各文件 sha256（交接完整性）
```

> **注意**：`macro_theme_proposals` 与 `cross_task_notes` **没有**独立文件，
> 二者放在 `manifest.json` 中（validator 据此装配）。

---

## 字段定义

以 `01_PROTOCOL/historical_research_intake.schema.json` 为**唯一事实来源**。
不要凭记忆写字段 —— 用 validator 校验。

---

## 交付前必须通过

```bash
python tools/validate_historical_research_intake.py 05_OUTPUT
```

**必须 `RESULT: PASS`（0 FAIL）才能交付。**

---

## 交付之后

```text
05_OUTPUT/
    ↓
ThreeC Agent
    ↓
Review → Dedupe → Merge → Macro Theme Canonicalization（CMTR v1）
       → Campaign Decision → DB Import → Validation → Coverage Audit → Export
```

---

## 提醒

- **不得**在本目录中写入 canonical DB ID
- **不得**宣称 `VERIFIED`
- **不得**写入 score / rank / probability / prediction
- **不得**为了数量制造 Campaign
- 参考模板：`../tools/fixtures/minimal_valid_package/`（**合成夹具，不是研究数据**）
