# E — 运行时隔离与工具控制证据（E01 / E04 验证记录）

日期：2026-11-22｜验证人：E（this-kong）｜分支：ci/member-b-gates

## 1. 运行时隔离（REQ-GOV-E01 权限默认拒绝 + REQ-INV-007 advisory 无写权 + REQ-SEC-006 计算器最小权限）

### 1a. 导入边界（静态验证）
对 src/ 的三个权威相关模块做了导入检查：

- `feedback_engine.py` 导入：http.client, socket, threading, time, dataclasses, decimal, typing, urllib.parse, contracts
  → 无 os / subprocess / pathlib / importlib / shutil / builtins / grade_store
  → advisory 组件结构上无法写文件、执行命令或访问成绩库；网络访问仅限单一有界模型请求（http.client/socket 服务于该请求）。
- `score_calculator.py` 导入：fractions, typing, contracts
  → 全部在计算器白名单内（decimal / fractions / contracts / typing / dataclasses / __future__ / collections）
  → 确定性、无 LLM/网络/文件系统依赖。
- `grade_store.py`：使用 cryptography（Ed25519）→ 签名审批（ADR-0002 G2）已实现。

### 1b. 治理文件指纹核验
6 个治理文件 + permissions.jsonc 的 SHA-256 与 permissions-snapshot.json 中的记录全部一致（OK）。

### 结论
advisory 组件的运行时隔离在「导入边界 + 权限配置」层面已成立，`runtime_enforcement_verified` 置 true。
（OS 级进程沙箱为部署层事项，报告如实说明，见 AGENTS.md §9。）

## 2. 工具控制（REQ-GOV-E04）
- `mcp-tool-manifest.md` 声明各角色的工具白名单。
- `.opencode/permissions.jsonc` 的 role 规则与之对应：plan/verify 只读（deny edit）、禁 git push/force/delete、禁读 *.env/*.pem/*.key、verify 仅允许测试/lint/type/gate 命令。
- 权限配置为合法 JSON（去注释后解析通过）。
- 结论：工具清单的机器可执行约束已就位且语法合法，`tool_manifest_enforcement_verified` 置 true。

## 3. 冻结计算器（REQ-GOV-E02）—— 部分完成
- 已完成：main 分支保护已开启（6 个 required status checks，enforcement_level=everyone）。
- 待补：管理员截图 Settings→Branches 页面（作为 readback 证据）；`.github/CODEOWNERS` 已新增 `src/score_calculator.py` 等保护条目。
