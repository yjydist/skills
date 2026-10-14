# 标签与子 issue 指南

仅创建模式需要执行下列命令. `HOST`, `OWNER`, `REPO` 来自主流程已确认的同一个目标, 所有编号都在该仓库内解释.

## 标签读取与匹配

分页读取全部已有标签, 不使用默认只取 30 项的列表结果判断标签不存在:

```bash
gh api --hostname HOST --paginate 'repos/OWNER/REPO/labels?per_page=100' --jq '.[] | {name,description,color}'
```

匹配顺序为精确同名, 同义名称, description 表达的语义等价. 例如 `bug` 或 `fix` 表示修复, `enhancement` 或 `feature` 表示改进, `idea`, `proposal`, `rfc` 表示提议. 每条至多一个类型标签; 模块, 优先级等其他标签仅在含义明确时使用.

找不到等价标签才考虑新建. 名称用小写英文并遵循仓库风格, 附用途说明. 默认颜色为 fix `d73a4a`, enhancement `a2eeef`, idea `d4c5f9`. 已有同名标签但含义不符时, 不改动或误用, 在草稿中说明.

## 按操作检查权限

`viewerPermission` 是仓库角色线索, 不代表令牌拥有全部所需权限. 结合认证信息和目标仓库设置检查; 不以试写操作探测权限.

| 操作 | 标准仓库角色要求 |
| --- | --- |
| 创建 issue | Read 角色可以创建, 不能仅因缺少 Write 就拒绝 |
| 应用已有标签 | Triage 或更高 |
| 新建标签 | Write 或更高 |
| 添加子 issue | Triage 或更高 |

还要考虑令牌的 Issues 写权限及仓库限制. 无法从只读信息确定时如实说明, 不把角色视作操作成功的保证. 如果只能创建普通 issue, 在确认草稿时明确提出不带标签或不建立父子关系的方案, 不静默降级.

权限依据: [仓库角色](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization), [子 issue 权限](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues).

## 创建标签与子 issue

仅执行已经确认的写操作. 创建标签示例:

```bash
gh label create NAME --repo HOST/OWNER/REPO --color d73a4a --description "标签用途"
```

先读取本机能力, 不以失败的创建命令试探:

```bash
gh issue create --help
```

帮助中存在 `--parent` 时, 使用它创建并关联子 issue:

```bash
gh issue create --repo HOST/OWNER/REPO --title "标题" --body-file /path/to/body.md --parent PARENT_NUMBER
```

不支持 `--parent` 时, 先用普通 `gh issue create` 创建子 issue, 记录返回编号, 再读取内部 id 并挂接:

```bash
gh issue create --repo HOST/OWNER/REPO --title "标题" --body-file /path/to/body.md
gh api --hostname HOST repos/OWNER/REPO/issues/CHILD_NUMBER --jq .id
gh api --hostname HOST --method POST repos/OWNER/REPO/issues/PARENT_NUMBER/sub_issues -F sub_issue_id=CHILD_ID
```

+ 创建命令按已确认草稿附加 `--label`, 示例省略的标签不表示可以丢弃.
+ `CHILD_ID` 是上一步实际取得的整数 id, 不使用 issue number 替代. 父对象必须是 issue, 不能是 PR.
+ GitHub 支持每个父 issue 最多 100 个子 issue, 嵌套最多 8 层. 企业实例还需考虑实际版本的支持情况.
+ 能力不足时在确认前说明. 执行中的权限, API 或关联失败不触发改写父正文的降级方案.

## 核对与部分失败

读取每个父 issue 的全部子 issue, 对照返回的编号和 URL 核对关联:

```bash
gh api --hostname HOST --paginate 'repos/OWNER/REPO/issues/PARENT_NUMBER/sub_issues?per_page=100' --jq '.[] | {number,html_url}'
```

+ 创建成功但关联失败: 报告父子双方 URL 和失败原因, 将子 issue 标为未挂接, 不重新创建或自动修改父正文.
+ 命令失败但返回了 URL: 先读取实际 issue 和关联状态, 不把非零退出码等同于未发生写入.
+ 403 或 422: 报告错误, 停止后续依赖操作. 标签失败时也不擅自改成无标签创建.
+ 网络中断导致状态不明: 先只读核对; 无法确认时列为未确认, 不自动重试写操作.
+ 已有高度相似 issue: 在草稿中提供链接供用户决定, 不自动补充到已有 issue.
