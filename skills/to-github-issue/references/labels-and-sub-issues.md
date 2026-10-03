# 标签与 sub-issue 指南

本文说明如何为 issue 匹配或新建标签, 以及如何创建和挂接 sub-issue.

## 标签匹配

先列出仓库已有标签:

```bash
gh label list --repo OWNER/REPO --json name,description,color
```

匹配顺序:

1. 精确同名: 仓库已有 `bug`, `enhancement`, `idea` 等与类型直接对应的标签, 直接使用.
2. 同义标签: 仓库用 `fix` 对应 bug, `feature` 对应 enhancement, `proposal`, `rfc` 对应 idea 等, 使用仓库的叫法.
3. 语义等价: 仓库标签命名自成体系时, 按标签的 description 判断语义是否覆盖本 issue 的类型, 跟随仓库惯例优先.

找不到语义等价的已有标签时才考虑新建. 每条 issue 至多打一个类型标签, 仓库已有其他维度的标签(如优先级, 模块名)仅在语义明确贴合时使用, 不强行凑齐.

## 新建标签约定

+ 名称用小写英文, 跟随仓库已有标签的命名风格(连字符或无空格).
+ 颜色使用 GitHub 默认色板: fix 用红色 `d73a4a`, enhancement 用青色 `a2eeef`, idea 用紫色 `d4c5f9`.
+ 附一句说明用途的 description.

```bash
gh label create <name> --repo OWNER/REPO --color d73a4a --description "<description>"
```

新建标签必须在前面的草稿确认步骤中明示并获得同意. 仓库已有同名标签但语义不符时, 不复用也不改动它, 向用户说明并另行确认.

## sub-issue 创建

首选官方 `--parent` 标志:

```bash
gh issue create --repo OWNER/REPO --title "<title>" --body-file - --parent <父编号>
```

`gh issue create --parent` 要求 gh 版本较新; 版本不支持时改用 API. 把已存在的 issue 挂为 sub-issue 也走 API:

```bash
# 先取 sub-issue 的内部 id, 注意不是 issue number
gh api repos/OWNER/REPO/issues/<子issue编号> --jq .id

# 再挂接到父 issue
gh api -X POST repos/OWNER/REPO/issues/<父issue编号>/sub_issues -F sub_issue_id=<上一步取到的id>
```

注意事项:

+ `sub_issue_id` 是内部 id, 不是 issue number, 两者不要混用.
+ 父 issue 必须是 issue, 不能是 PR.
+ GitHub 限制每个父 issue 最多 100 个 sub-issue, 嵌套最多 8 层.
+ API 也不可用时降级: 在父 issue 正文中直接列出各子 issue 的编号和链接清单, 不强行调用.

## 异常处理

| 情况 | 处理 |
| --- | --- |
| 标签创建失败但 issue 可创建 | 征得用户同意后不带标签创建, 并在汇报中说明 |
| 创建返回 403 或 422 | 报告错误信息和所需权限, 终止, 不降级到其他写操作 |
| gh 未认证 | 展示 `gh auth status` 的报错, 引导用户自行执行 `gh auth login`, 不代做 |
| 发现高度相似的已有 issue | 暂停创建, 展示已有 issue 链接, 由用户决定是新建, 补充到已有 issue 还是用其他方式处理 |
