# AGENTS.md

提供给 Agent 阅读的仓库维护规范. 修改后由 Agent 按下列要求审查改动.

## 项目原则

+ 仓库用于维护 skill 指令, 参考文档, 模板及各个 skill 自带的脚本. 仓库级维护不设置 CI 或统一的运行环境, 通过阅读规范和审查改动完成检查.
+ 每个 skill 的运行依赖由使用者按对应使用文档准备. 修改该 skill 的脚本时, 按其需要进行验证并说明结果或未验证原因.
+ 进行 Git 提交时, 使用仓库内的 [convenient-commit](skills/convenient-commit/SKILL.md).

## 文档与格式

+ skill 及配套文档的自然语言使用简体中文和 ASCII 标点, 只有必要的地方使用英语. 此要求也适用于 frontmatter 的 `description`.
+ Markdown 无序列表统一使用 `+`, 任务列表使用 `+ [ ]` 或 `+ [x]`.
+ 围栏代码块, 缩进代码和行内代码按其自身语法保留, 不机械套用自然语言标点或 Markdown 列表规则.

## 变更检查

+ 每个 `skills/<skill-name>/` 目录包含 `SKILL.md`. 文件开头的 YAML frontmatter 必须有效, `name` 与目录名称一致, `description` 为非空的用途说明.
+ 每个 skill 都有对应的 `docs/<skill-name>.md` 使用文档, 并在 README 的 `## skills 列表` 下有一个对应条目. 条目包含名称, 简短简介及文档链接, 格式示例: `+ <skill-name>: <skill 的简短简介> [具体文档](docs/<skill-name>.md)`.
+ 检查新增或修改的本地链接, 按所在文档的位置解析相对路径, 确认目标文件和标题锚点存在. 移动或删除文件时, 同步清理仓库中指向它的引用.
+ 核对 skill 入口, 参考文件, 模板或脚本, 使用文档及 README 的说明是否一致. 根据实际改动检查输入要求, 执行步骤, 依赖和交付结果, 不用机械规则判断中文表达质量或指令是否合理.
