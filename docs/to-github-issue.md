# to-github-issue 使用文档

`to-github-issue` 将当前会话讨论过的待办, 问题和想法归纳为 GitHub issue 草稿. 用户要求创建时, 检查目标仓库, 标签和重复记录, 集中确认完整草稿后创建, 必要时建立父子关系.

## 使用前提

+ 将 [skill 目录](../skills/to-github-issue/SKILL.md) 连同 `references/` 一起提供给执行工具.
+ 仅整理草稿不需要 Git 仓库, gh 或认证. 没有仓库信息时, 标签和目标仓库标为待确定.
+ 实际创建需要 gh, 对目标主机完成认证, 并具备计划操作的权限. 创建 issue, 应用标签, 新建标签和挂接子 issue 分别检查权限.
+ 用户指定的目标仓库优先, 否则从当前仓库的 origin 获取. 没有可确定目标时才询问. 仅给 `OWNER/REPO` 时默认主机为 `github.com`.

下方用 `$to-github-issue` 表示调用; 不支持该形式时, 直接指定其 `SKILL.md` 实际路径.

## 调用示例

### 仅整理草稿

```text
使用 $to-github-issue 回顾本次会话, 把遗留的待办整理成 issue 草稿.
只输出草稿, 不创建任何 issue 或标签.
```

直接得到标题, 正文, 拟用标签, 拆分关系和待确认信息. 不要求先登录或确认原始清单; 没有真实待办时如实说明.

### 创建到指定仓库

```text
使用 $to-github-issue 整理本次讨论的修复项, 准备创建到 OWNER/REPO.
展示完整草稿后创建, 标签优先使用仓库已有的.
```

先读取目标仓库的模板和全部标签, 检索开放和关闭的相似 issue, 将新标签, 权限限制与重复条目一起展示. 用户批准具体草稿后创建, 同一版本不重复确认. 所有操作及最终核对固定使用该目标仓库.

### 拆分子 issue

```text
使用 $to-github-issue 把本次讨论中的 X 方向整理成父 issue 和子 issue.
子项需要能够独立执行和验收, 先展示完整草稿.
```

先检查 gh 是否支持 `--parent`; 支持时直接创建关联, 否则使用普通创建加 API 挂接. 创建前仍需确认具体父子关系, 完成后核对实际关联.

## 异常处理

+ 仓库归档, 未启用 Issues, 认证或访问失败时停止创建并保留草稿.
+ 标签或关联权限不足时, 在确认前提出实际可行方案, 不静默省略标签或关系.
+ 草稿确认前不写入 GitHub, 已确认内容发生实质变化时只重新确认变化部分.
+ 创建或挂接失败时报告已完成的 issue 和失败项. 已创建但未挂接的子 issue 保留原状, 不改写父正文或自动删除.
+ 网络中断或非零退出码不代表一定没有创建成功. 先只读核对, 不盲目重复创建.
+ 不自动修改, 关闭或评论已有 issue, 不设置 assignee, milestone 或 project, 不改动已有标签.

## 进一步阅读

+ [执行流程](../skills/to-github-issue/SKILL.md).
+ [issue 撰写指南](../skills/to-github-issue/references/issue-drafting.md).
+ [标签, 权限与子 issue 指南](../skills/to-github-issue/references/labels-and-sub-issues.md).
+ [返回仓库说明](../README.md).
