---
name: to-github-issue
description: 收集当前 session 中讨论到的待办, 问题和想法, 归纳为带合适标签的 GitHub issue 草稿, 经确认后用 gh 创建, 必要时拆分 sub-issue. 适用于用户要求把本次讨论的 todo 或想法记成 issue, 或要求整理当前会话中遗留的修复项和改进项时.
---

# 会话待办转 GitHub issue

回顾当前 session 中的讨论, 把其中的待办, 问题和想法归纳成 issue 草稿, 经用户确认后在目标仓库创建, 并打上贴合仓库已有约定的标签.

## 核心原则

+ 一条 issue 服务于一个可执行的目的. issue 必须来自本 session 中真实出现过的讨论, 不虚构需求, 不把推测当成用户的结论.
+ 创建 issue 是对外可见的操作. 必须先展示草稿并得到确认, 确认前不执行任何写操作.
+ 标签优先复用仓库已有的约定, 不强加自己的分类体系.

## 工作流程

### 1. 确认环境与目标仓库

确认当前仓库和 gh 可用性:

```bash
git rev-parse --show-toplevel
git remote get-url origin
gh auth status
gh repo view --json nameWithOwner,viewerPermission
```

+ 从 remote URL 解析 owner/repo. 没有 remote 或当前不在 git 仓库时, 询问用户目标仓库的 slug 并用 `gh repo view` 验证, 不猜测.
+ `viewerPermission` 不足以创建 issue 时, 提前告知用户, 不继续写步骤.
+ 检查 `.github/ISSUE_TEMPLATE/`, 存在模板时按模板结构组织正文.

### 2. 收集 session 信息

这一步主要靠回顾当前对话, 是本 skill 与直接扫描代码的差异所在. 收集以下内容:

+ 用户明确提出的待办和修复要求.
+ 讨论过但被延后处理的 bug 和设计缺陷.
+ 被搁置或被简化的方案, 以及方案中放弃的分支.
+ 用户明确认可的问题或改进方向.

仅在用户要求时才去 grep 代码中的 TODO/FIXME 等注释, 默认不主动扫描.

收集完成后先列出原始清单, 请用户补充或剔除, 再进入归纳. session 中没有可归纳的内容时直接说明, 不虚构 issue.

### 3. 归纳 issue 并匹配标签

+ 去重合并同类讨论, 同一问题被多次提及只保留一条.
+ 按目的分类: 修复缺陷归 fix, 改进现有功能归 enhancement, 对下一步的想法归 idea.
+ 标题具体到能独立理解, 不写 "修复一些问题" 这类概括.
+ 正文包含背景, 问题或目标, 建议方案; 信息不足的条目在正文中标注待确认, 不编造细节.
+ issue 内容复杂或需要拆分时, 读取 [issue 撰写指南](references/issue-drafting.md).
+ 标签匹配和新标签约定, 读取 [标签与 sub-issue 指南](references/labels-and-sub-issues.md).

### 4. 展示草稿并确认

以清单形式逐条展示, 每条包含: 类型, 标题, 正文要点, 标签, 是否拆分 sub-issue 及拆分方式. 计划新建的标签必须在此步明示并获得同意.

草稿得到确认之前不执行任何写操作, 包括创建标签. 用户调整草稿后按调整结果继续.

### 5. 创建 issue

+ 顺序: 先创建确认过的新标签, 再创建无父 issue, 最后按依赖关系创建 sub-issue 并挂到父 issue.
+ 固定使用 `--repo OWNER/REPO`, 不依赖当前工作目录.
+ 正文较长时用 `--body-file -` 配合 heredoc 传入, 避免转义问题.
+ 创建前用 `gh issue list --search <关键词> --repo OWNER/REPO` 查重. 发现高度相似的已有 issue 时暂停, 展示链接, 由用户决定是否继续.
+ sub-issue 优先使用 `gh issue create --parent <父编号>`, 具体命令和备选方案见 [标签与 sub-issue 指南](references/labels-and-sub-issues.md).

### 6. 核对并汇报

对每个创建的 issue 执行:

```bash
gh issue view <number> --json number,title,labels,url
```

汇报编号, URL 和实际标签. 实际结果与草稿不一致时说明差异. 部分失败时不把整体报成完整成功, 明确列出失败项和原因.

## 操作边界

+ 只创建新 issue 和确认过的标签. 不修改, 关闭, 重开或评论已有 issue.
+ 确认范围只涵盖展示过的草稿, 不顺手追加用户没有提到的 issue.
+ 不设置 assignee, milestone 或 project, 除非用户明确要求.
+ 不重命名, 改色或删除已有标签.
+ 不把密钥, 访问令牌或未公开的内部地址写入 issue 正文.
+ 目标仓库不明确时停下来询问, 不猜测.
