# test-baselines 分支保护记录（C 执行，2026-11-23）

## 1. 为什么做

B（Shuzhao SHEN）在 2026-11-23 群里要求："**#16 已切到 test-baselines，D 的正式审批有效。麻烦管理员给这个分支开保护。保护生效后我合入 #16，再把基线合并 SHA 发给 A 开始实现。**"
E（Hanyu WANG）在群里 @王雨薇 指派执行。C 是该仓库 owner，有 admin 权限，由 C 执行并留下本记录。

## 2. 实际设置（readback，非意图）

执行：`PUT /repos/wyw-12345/CS5351/branches/test-baselines/protection` → HTTP 200，随后 `GET` 回读确认。

| 项 | 值 | 理由 |
| --- | --- | --- |
| `required_status_checks` | **未设置（none）** | 该分支当前 CI 状态是 `unstable`（有 check 未通过）。若照抄 `main` 的六个 context，B 立刻会被卡死。六门仍在 `main` 与 PR 层面生效，这里不重复施加 |
| `required_pull_request_reviews.required_approving_review_count` | **1** | D 已在 #16 提交 APPROVE（SHA `833140d`），满足条件即可合入 |
| `dismiss_stale_reviews` | **false** | 若设为 true，B 在合并前补一个小 commit 就会把 D 的批准作废、流程退回。这里选择不自动作废；若要与 `main` 完全一致，改成 true 即可 |
| `enforce_admins` | **true** | 管理员同样受约束，避免"owner 手推绕过保护"这种不可审计的情况 |
| `allow_force_pushes` | **false** | 基线分支不允许改写历史 |
| `allow_deletions` | **false** | 基线分支不可删除 |
| `required_linear_history` | false | 不强制线性历史，`main` 也没有 |
| `required_conversation_resolution` | **false** | 未解决评论不作为阻塞条件，避免与"只差一个批准"的现状冲突 |
| `restrictions` | 未设置 | 不对推送者做白名单限制，组员仍可推分支 |

## 3. 当时的 PR #16 状态（同一时刻回读）

| 项 | 值 |
| --- | --- |
| state | `open` |
| base / head | `test-baselines` ← `test/member-a-explicit-broker-proxy` |
| head SHA | `833140d`（与 D 评审的 SHA 一致） |
| 评审 | `unohhh1`（D）：先 `COMMENTED`（08:44Z），后 `APPROVED`（08:47Z），均针对 `833140d` |
| mergeable | `true`（`mergeable_state: unstable` —— 仍有 check 未通过，但因未设 required checks 不阻塞） |

## 4. 如果要收紧（B 或 E 可要求）

1. 加六门 required contexts：把 `test-approval`、`static-analysis`、`schema`、`regression`、`ai-use-log`、`semantic-evaluation` 设为 required status checks，并把 `strict` 设为 true。
2. 与 `main` 对齐 `dismiss_stale_reviews: true`。
3. 注意代价：一旦加上，`unstable` 状态的 PR 将无法合入，必须先跑绿。

## 5. 边界说明（不夸大）

- 本记录只证明"保护已开启、内容如上"，**不证明**六门通过、不证明语义门结果、不证明任何测试先于实现。
- `test-baselines` 目前不是 `main`；保护这条分支不等于保护 `main`，两者的 required checks 不同（`main` 有 6 个 context，这里没有）。
