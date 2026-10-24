# Proposal

## Why

仓库现有 9 个 skill 中, 8 个缺少 `SKILL.md` 的 `## 前提条件` 一节, 而 `skill-creator` 的规格已经要求该节必须存在, 并规定未改动的既有 skill 在下一次改进时必须补上. 本次就是该触发点: 补齐这 8 个 skill, 让入口文档重新承担执行前的前提检查, 而不是把运行时要求留在使用者文档里.

同时发现两处与仓库自身规范相连的实际缺口: `to-github-issue` 在工作流程中直接调用 `gh`, 但没有前置门禁; `paper-third-pass` 的参考文件互相引用, 违反 `references/writing.md` 的失败清单. 两者都是机械校验无法覆盖, 只能靠本次人工整改发现的.

## What Changes

+ 为 8 个 skill 的 `SKILL.md` 补 `## 前提条件` 一节, 按运行时, 第三方依赖, 外部程序与认证三类列出, 每条给出可执行的检查命令. 无该项时写"无", 不为凑满条目编造检查命令.
+ `to-github-issue`: 在 `## 前提条件` 中声明 GitHub CLI 与目标主机的认证, 并明确仅整理草稿不需要认证; 同时把认证检查前移到工作流程之前, 避免整理完草稿才在流程中途失败.
+ `weekly-report`: 把正文第 28 行的 "需要 Python 3.9+ 和 Typst 0.13+" 移入 `## 前提条件`, 正文改为指向前一节. 字体缺失按现有设计回退, 因此列入前提条件但标注不阻断.
+ `paper-third-pass`: 删除 `references/report-format.md` 中对 `selective-report-format.md` 的互引, 改由 `SKILL.md` 已有的两层直接引用承担可达性; 消除校验脚本的 2 条警告.
+ `docs/swiss-grid-design.md`: 第二节标题由 `## 使用方式` 改为 `## 使用前提`, 与其余 8 份使用文档一致.
+ `AGENTS.md`: 在 `## 变更检查` 中增加一条, 要求检查 `SKILL.md` 的 `## 前提条件` 与使用文档的依赖说明是否一致, 避免该缺口再次积累.

不改动 `skill-creator` 自身, 它已符合全部要求. 不新增或修改任何 spec.

## Capabilities

### New Capabilities

无.

### Modified Capabilities

无.

本次是既有 skill 对已有规格的补齐, 不引入新的可复用能力, 也不改变任何已立规格的要求. `to-github-issue` 目前没有 spec, 其门禁调整属于单个 skill 的工作流程修正, 不构成 spec 级行为变更; 若后续要为该 skill 立规格, 应作为独立变更处理. 因此本 change 的 `.openspec.yaml` 设置 `skip_specs: true`.

## Impact

+ 修改 11 个文件: 8 个 `SKILL.md`, `skills/paper-third-pass/references/report-format.md`, `docs/swiss-grid-design.md`, `AGENTS.md`.
+ 不修改任何脚本, 不新增依赖, 不改变 `skill-creator` 的校验脚本行为.
+ 校验影响: 8 个 skill 的 `validate_skill.mjs` 结果应保持 0 错误; `paper-third-pass` 的 2 条警告应消失.
+ 行为影响: 仅 `to-github-issue` 的前置门禁真正改变执行顺序, 其余改动为文档层面的补充与归位.
+ 不受本次覆盖的范围: 触发语料仍只有 `skill-creator` 一份, 本次不为其余 skill 建立语料, 因此触发质量无法在改动前后做对比验证.
