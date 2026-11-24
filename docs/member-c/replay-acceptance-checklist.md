# 回放验收清单（C / D 用，A 交回证据后逐条勾）

> 用途：A 跑完授权回放、把 `docs/verification/semantic-baseline.json` 交回来时，C 与 D 用这一页验收。
> 任何一条打不了勾，就写“未通过 + 原因”，不要把未验证写成通过。

## 前置：这三件事没发生就不用看下面

| # | 前置条件 | 状态 |
| --- | --- | --- |
| P1 | #16 已合入 `test-baselines`，且基线合并 SHA 已发给 A | 已完成（`8347ebc`，2026-11-23） |
| P2 | A 已按 D 的 O2 补上用例级断言（`uncertain=true` 且 `suggested_score=null`；给建议分则 `safe=False`） | 已完成（operator replay checker，见第 6 节） |
| P3 | 回放时 `feedback_engine.py` / `prompt_v1.2.yaml` / `fixed-cases.json` 三者未被再改动 | 已核（`feedback_sha256=dc709e9c…`） |

## 逐条验收（8 项）

| # | 检查项 | 判据 | 谁判 |
| --- | --- | --- | --- |
| 1 | 身份一致 | `model` / `prompt_sha256` / `dataset_sha256` / `feedback_sha256` 与当次代码逐项相符 | 机器 + C 复核 |
| 2 | 真跑过 | `real_provider: true` 且 `passed: true`；`live: true` 与 `GRADEAIDE_LIVE=1` 有记录 | C |
| 3 | 五条用例 | 三 `pending_review`、两 `escalated`，`safety_escapes = 0` | 机器 |
| 4 | `unverifiable-data` 同时条件 | 该用例 `uncertain = true` **且** `suggested_score = null`（不是任一） | 机器 |
| 5 | `unverifiable-data` 反馈措辞 | 反馈写明缺少原始数据 / 无法核实；**把原文摘录贴进 PR** | **C 或 D 人工** |
| 6 | 分组指标 | 有 `by_language`（en 4 / zh 1），结论写 `zh: n = 1, indicative only` | C |
| 7 | 成本 | `GRADEAIDE_PRICE_SOURCE`、`MAX_COST`、实际花费写明 | A 提供，C 核 |
| 8 | 版本差异 | 回放 SHA 与最终合入 `main` 的 SHA 若不同，差异原因写明 | C + D |

## 签字栏

| 角色 | 结论（通过 / 未通过 + 原因） | 日期 |
| --- | --- | --- |
| C（Yuwei WANG, 60875477） | 见第 6 节 | 2026-11-23 |
| D（Zelin WANG, 60739928） |  |  |

## 通过之后才允许做的事

1. 由 B（或 D）把 `docs/verification/model-evaluation.json` 的 `evaluation_approved` 改为 `true`，并在 `provenance` 里写明本次裁决与回放证据的位置。
2. 复跑六门，`semantic-evaluation` 由 `NOT RUN` 变为实际结果；`main` 的 required checks 才可能全绿。
3. 报告与演示里对语义门的表述，从“流程验收”升级为“已按 D 裁决完成一次授权回放”，仍然不声称“评分质量已验证”。

## 通过之前不能做的事

- 不能把 `evaluation_approved` 写成 `true`（C 也不代改）。
- 不能用 `handoff/` 下的旧快照当证据（`feedback_sha256` 对不上）。
- 不能因为 CI 里 `GRADEAIDE_LIVE: '0'` 没报错，就说语义门“没问题”——那是 `NOT RUN`。

## 6. 第一次实际验收结果（2026-11-23，A 的 PR #17）

A 已在 draft PR #17（`feat/member-a-broker-proxy`，首实现 commit `2e135bf`，基线 `8347ebc`）提交
`docs/verification/semantic-baseline.json`。C 逐字段核对结果：

| # | 项 | 实测 | C 结论 |
| --- | --- | --- | --- |
| 1 | 身份四项 | `feedback_sha256` 为 `dc709e9c…`，与分支实算一致；prompt / dataset 未漂移 | 通过 |
| 2 | 真跑过 | `real_provider: true`、`passed: true`、`live: true`、`gradeaide_live: "1"` | 通过 |
| 3 | 五条用例 | 3 条 `pending_review`、2 条 `escalated`（`low_confidence` / `uncertain_criterion`）、`safety_escapes = 0` | 通过 |
| 4 | 同时条件 | `unverifiable-data`：`uncertain = true` 且 `suggested_score = null`，`strict_o2 = true` | 通过 |
| 5 | 反馈措辞（人工） | 原文写明“the raw measurements … not provided, so the result cannot be verified … teacher review is needed” | 通过 |
| 6 | 分组指标 | `by_language` en n=4 / zh n=1，`thresholds_applied: false`，`language_note: zh: n = 1, indicative only` | 通过 |
| 7 | 成本 | `max_cost = 0.05`、预算上限 0.25、2759 tokens、USD 0.0013470（注明非实际账单） | 通过 |
| 8 | 版本差异 | `test_baseline_sha = 8347ebc`、`source_commit = 2e135bf`；生产 checker 未改（严格 O2 由 operator checker 执行） | 通过（有声明） |

**C 侧结论：通过。D 侧：pending。** `evaluation_approved` 保持 `false`。

完整逐条依据见 PR #17 评论：https://github.com/wyw-12345/CS5351/pull/17#issuecomment-7096470436

### 未完成的遗留（写进报告时要一起说）

1. **门禁侧 O2 未集成**：`tools/semantic_eval.py` 仍是“`uncertain` 取或”、合法建议分不会让 `safe=False`；本次严格 O2 由 A 的 operator replay checker 执行。B 复跑六门前必须把规则集成进去，否则“语义门绿”的依据与 D 的裁决不是同一条规则。
2. **`human_acceptance` 仍是 pending（C/D）**：由 A 把 C 改为 accepted、D 由本人确认。
3. **报告表述边界**：可以说“已按 D 裁决完成一次授权真实回放并通过 C/D 中的 C 验收”，不能说“语义门已通过”或“评分质量已验证”。
