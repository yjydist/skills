# Proposal

## Why

仓库已有 `skills/skill-creator/`, 覆盖 skill 的门槛判断, 脚手架生成和机械校验, 但 [AGENTS.md](../../../AGENTS.md) 的维护规范没有指向它. 现有规范只要求 skill 目录具备 `SKILL.md`, 使用文档和 README 条目, 属于事后检查; 新建 skill 时缺少统一入口, 容易绕过门槛判断与校验脚本. 提交入口已在 `## 项目原则` 用一条指向 `skills/convenient-commit/SKILL.md` 的规则约束, skill 创建缺少对等的一条.

## What Changes

+ 在 [AGENTS.md](../../../AGENTS.md) 的 `## 项目原则` 追加一条: 新建 skill 使用 [skill-creator](../../../skills/skill-creator/SKILL.md), 由它完成门槛判断, 脚手架生成与机械校验.
+ 该条与既有的 convenient-commit 条目保持同样的写法: 一句话说明动作, 用相对链接指向 skill 入口.

本次只改维护规范文本, 不修改 `skill-creator` 自身, 其他 skill 或任何脚本.

## Capabilities

### New Capabilities

无.

### Modified Capabilities

无. 本变更只是仓库维护规范中的一条约定, 不改变任何 skill 或脚本的可观察行为, 因此 `.openspec.yaml` 设置 `skip_specs: true`, 不新建也不修改 spec.

## Impact

+ `AGENTS.md`: `## 项目原则` 增加一条, 篇幅约一行.
+ 无代码, 脚本, 依赖或运行环境变更.
+ `skill-creator` 的职责边界不变: 新增的只是"新建 skill 时应当经由它"的仓库约定, 不改其 `description`, 正文或触发语料.
