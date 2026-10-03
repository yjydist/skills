# to-github-issue 使用文档

`to-github-issue` 用于回顾当前 session 中的讨论, 把其中的待办, 问题和想法归纳成带标签的 GitHub issue 草稿, 经确认后用 gh 创建. issue 按目的分为 fix, enhancement 和 idea, 标签优先复用仓库已有约定, 过于庞大的 issue 可拆分 sub-issue.

## 使用前提

+ 将 [skill 目录](../skills/to-github-issue/SKILL.md) 连同 `references/` 中的参考文件一起提供给支持 skill 的工具.
+ 执行工具能够运行 `gh` 且已完成认证, 对目标仓库有创建 issue 的权限. 仓库通过当前 git 仓库的 remote 自动检测, 无 remote 时需要提供仓库 slug.
+ 在请求中说明范围: 只要草稿, 还是确认后创建; 是否包含对代码中 TODO/FIXME 的扫描(默认不扫描).

下方示例使用 `$to-github-issue` 表示调用该 skill. 如果所用工具不支持这种调用形式, 可以直接指定 `skills/to-github-issue/SKILL.md` 的实际路径, 要求按其中的指导处理.

## 调用示例

### 仅归纳草稿

```text
使用 $to-github-issue 回顾本次会话, 把遗留的待办和问题整理成 issue 草稿.
本次只输出草稿清单, 不创建任何 issue 或标签.
```

预期结果是一份草稿清单, 每条包含类型, 标题, 正文要点, 拟用标签和是否拆分 sub-issue. 不会执行任何写操作, session 中没有可归纳内容时会直接说明.

### 整理会话待办并创建

```text
使用 $to-github-issue 整理本次会话中的修复项和改进项, 展示草稿后创建到当前仓库.
标签优先复用仓库已有的, 需要新建标签时先告诉我.
```

预期结果是在当前仓库创建确认过的 issue, 并汇报每个 issue 的编号, URL 和实际标签. 创建前会先查重, 发现相似 issue 时暂停等用户决定.

### 拆分 sub-issue

```text
使用 $to-github-issue 把本次讨论中的 X 方向整理成 issue.
这个方向包含多个独立工作项, 拆成父 issue 加 sub-issue 的形式.
```

预期结果是一个描述总体目标的父 issue, 以及逐项挂接到父 issue 的 sub-issue. 拆分依据是工作项能否独立执行和验收, 不满足拆分标准时会保持单条 issue 用任务清单表达.

## 异常处理

+ 草稿未经确认前不会创建任何 issue 或标签, 新建标签必须在草稿展示阶段明示并获得同意.
+ 当前目录不是 git 仓库或没有 remote 时, 会询问目标仓库 slug 并验证; 提供不了则终止, 不猜测仓库.
+ `gh` 未认证时展示报错并引导用户自行登录, 权限不足时提前告知, 不继续写步骤.
+ 创建返回 403 或 422 时报告错误并终止, 不降级到其他写操作; 标签创建失败但 issue 可创建时, 征得同意后才不带标签创建.
+ 查重发现高度相似的已有 issue 时暂停, 展示链接, 由用户决定.
+ 不会修改, 关闭, 重开或评论已有 issue, 也不会设置 assignee, milestone 或 project.

## 进一步阅读

+ [执行流程](../skills/to-github-issue/SKILL.md): 环境确认, 信息收集, 归纳, 确认与创建.
+ [issue 撰写指南](../skills/to-github-issue/references/issue-drafting.md): 信息来源, 类型判定, 标题与正文模板, sub-issue 拆分判定.
+ [标签与 sub-issue 指南](../skills/to-github-issue/references/labels-and-sub-issues.md): 标签匹配与新建, sub-issue 命令与异常处理.
+ [返回仓库说明](../README.md).
