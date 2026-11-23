# 本棒交接记录 — C 拍板启动基线（bootstrap baseline）

- 日期/时区：2026-11-23，Asia/Shanghai
- 成员角色、真实姓名/学号：C（需求工程 + 治理基线负责人）；Yuwei WANG，60875477
- 实际使用的 AI/模型与原始会话路径：Vibe（Mistral，桌面 agent）+ 人工决策；原始会话由 C 本地保存导出，仓库内不放 transcript
- 接收的上游版本/commit：`main` @ `cdd6ce7`（policy.json 转 active，reviewers 为 this-kong / unohhh1）；PR #8 分支 `ci/member-b-gates` head `6323cbc`；E→B 交接说明 2026-11-22
- 本次完成的范围：ADR-B0006（bootstrap 边界）+ `docs/review-memo.md` 条目 C-BOOT-001 + 需求如何定/如何验收的书面定义 + 语义验收清单（交 D 确认）
- 当前状态：`decided_pending_independent_review`。依据：决策与边界已成文并签给 C；D 的独立 exact-head 评审、B 的合并后六门复跑尚未发生

## 实际变更

| 文件 | 改了什么 | 对应 REQ/ADR/INV | 草案或已评审 |
|---|---|---|---|
| `docs/architecture/adr/ADR-B0006-bootstrap-baseline.md` | 新建：划定 bootstrap 窗口（≤ `cdd6ce7`）、严格窗口（>`cdd6ce7`）、不豁免的检查、失效条件、回滚方式 | REQ-GOV-C01、REQ-GOV-B03 | C 已决策；待 D 独立评审 |
| `docs/review-memo.md` | 追加 C-BOOT-001：按模板逐项记录 PR/base-head/SHA/安全/门禁/变异/债务，verdict 写 CHANGES REQUIRED | REQ-GOV-B06 | 已记录，非批准 |
| `docs/member-c/C-requirements-and-acceptance.md` | 新建：需求怎么定（7 步）+ 四层验收（L1–L4）+ 谁验谁签 + 不得声称的四件事 | REQ-GOV-C01/C02、REQ-GOV-B03 | 草案，供报告与 10 分钟演示使用 |
| `docs/member-c/semantic-acceptance-checklist.md` | 新建：语义门的前置条件、5 个固定用例、5 个硬门限、待 D 裁决的两个开放项 | REQ-GOV-B03、REQ-PERF-003 | 提案，待 D 确认 |
| `docs/ai-use-log.yaml` | 追加 AI-C-BOOT-20261123-001 | REQ-GOV-B06 | 实际记录 |

## 实际检查

| 命令/人工检查 | 日期 | 实际结果 | 证据路径 | 未完成原因 |
|---|---|---|---|---|
| 读取 `docs/verification/policy.json`（main） | 2026-11-23 | `status: active`，reviewers 两人 | `docs/verification/policy.json` | — |
| 读取 `docs/verification/implementation-approvals.json` | 2026-11-23 | `{"approvals": []}`：历史无先测后写批准 | 同路径 | 不能补造 |
| 读取 `docs/verification/model-evaluation.json` | 2026-11-23 | `evaluation_approved: false`、`live: false`、5 个用例、sha256 已固定 | 同路径 | P2/P3 未满足，语义门只能 NOT RUN |
| 读取 `docs/verification/test-map.yaml` | 2026-11-23 | 47 条中 10 条仍无 locator | 同路径 | B 的活，未动 |
| 六门复跑 | — | NOT RUN（本棒不跑 CI） | — | 等 PR #8 合并后由 B 复跑 |
| 独立评审 | — | NOT OBTAINED | — | 需 D 用非作者账号评审 |

## 真实人类评审与批准

未取得。C 是决策作者，不能代替 D 的独立评审；`review-memo.md` 的 verdict 保持 `CHANGES REQUIRED`，直到：

1. D 在 PR #8 上以非作者身份对 exact head 给出评审意见（并确认或驳回 ADR-B0006 的边界）；
2. PR #8 合并时保留 main 的 active `policy.json`，不被分支上的 pending 版覆盖；
3. B 在合并后的 head 复跑六门并贴出 run 链接。

## 决策和待解决事项

- bootstrap 窗口的边界写死为 `cdd6ce7`，不允许再开第二个窗口；这条是本次唯一需要"拍板"的内容。
- 未豁免：`schema`、`static-analysis`、`semantic-evaluation` 与 `regression` 的变异子项。特别是 `INV-003-signing`、`INV-007-advisory-authority` 仍是 NOT RUN。
- 语义门的两个开放项（中文是否单独计、`unverifiable-data` 的 expected_reason 是否收紧）留给 D 一句话裁决，C 不单方面改阈值。
- 报告中必须原样写出偏差：实现与测试同期提交、无先测后写批准、无人工逐题评审。

## 下一棒

- 下一角色：D（独立评审 + 语义验收裁决），随后 B（合并 PR #8 并复跑）。
- 先读哪些文件：
  1. `docs/architecture/adr/ADR-B0006-bootstrap-baseline.md`
  2. `docs/review-memo.md`（C-BOOT-001）
  3. `docs/member-c/semantic-acceptance-checklist.md`
  4. `docs/verification/model-evaluation.json`、`policy.json`
- 第一件具体工作：在 PR #8 上以 `unohhh1` 账号对当前 head 做 exact-head 评审，明确写下"接受/驳回 bootstrap 边界"与"是否批准 evaluation dataset（P2）"。
- 仍需真人提供什么：D 的评审记录；A 的授权 live 回放；B 的合并后六门 run 链接；E 的分支保护 readback 截图/JSON。
- 本次 commit 与实际远端：见 `git-操作步骤.md`；C 需按该步骤在本机 clone 中提交并 push 分支后开 PR。
