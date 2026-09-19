# packages/ — R01 任务交付投放目录

> 本目录是 **Research Agent 提交 Intake Package 的唯一投放位置**。
> **不是** canonical 数据目录。**不允许**任何脚本从这里写入数据库。

---

## 约定

```text
research/intake/packages/
├── README.md            # 本文件
├── R01-01/              # 每个 task 一个独立目录
├── R01-02/
├── R01-03/
├── R01-04/
├── R01-05/
└── R01-06/
```

每个 task 目录的结构见协议 §5.3：

```text
R01-0X/
├── manifest.json
├── coverage.md
├── candidates.json
├── evidence.json
├── sources.json
├── securities.json
├── exclusions.json
├── conflicts.json
├── research_questions.json
├── quality_summary.json
└── checksums.sha256
```

---

## 硬约束

| 规则 | 说明 |
|---|---|
| **一个 task 一个目录** | 不得把多个 task 塞进同一个 package |
| **不覆盖** | 不得覆盖已有 package；**同一 round 不覆盖旧 task package** |
| **不写 DB** | 不得从此目录直接写入 `research/database/cycle_research.db` |
| **不改 existing campaigns** | 不得修改任何既有历史研究结论 |
| **LF only** | 所有文件必须 LF 换行 |

---

## 校验

```bash
# 校验单个 package（目录）
python research/scripts/validate_historical_research_intake.py research/intake/packages/R01-01

# 校验单个 package（单文件形式）
python research/scripts/validate_historical_research_intake.py path/to/package.json

# 基础设施自检（含本目录下所有 package）
python research/scripts/validate_historical_research_intake.py --check
```

**退出码**：`0` = 无 FAIL；`1` = 存在 FAIL。

---

## 当前状态

**`R01-01` ~ `R01-06` 均未启动。**
R00 只建立基础设施；启动任一 task 需**单独授权**。

见：

- `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`
- `research/intake/HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md`
- `research/intake/HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json`
