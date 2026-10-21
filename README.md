# skills

我个人自用的 skill 仓库, 用于维护可复用的任务指导和工作流程.

## 使用方式

+ 在下方列表选择 skill, 阅读对应文档中的使用前提和调用示例.
+ 将对应的 `skills/<skill-name>/` 完整目录提供给支持 skill 的工具, 保留其中的参考文件及相对路径. 具体加载方式以所用工具为准.
+ 每个 skill 的 `SKILL.md` 是执行入口, `docs/` 下的同名文档面向使用者. 仓库维护遵循 [AGENTS.md](AGENTS.md).

## skills 列表

+ convenient-commit: 按逻辑完整性规划提交边界, 拟定提交消息, 并在授权范围内创建 Git 提交. [具体文档](docs/convenient-commit.md)
+ to-github-issue: 将会话待办整理为无需认证的 issue 草稿, 创建时核对仓库与权限并集中确认, 支持父子 issue. [具体文档](docs/to-github-issue.md)
+ swiss-grid-design: 用瑞士国际主义的网格, 字体与留白创建, 调整或评审多媒介视觉方案, 明确默认参数和功能例外. [具体文档](docs/swiss-grid-design.md)
+ weekly-report: 按固定表格版式渲染周报或月报, 原样保留用户内容, 输出 A4 宽度 300 DPI 的单张可变高度 PNG 与独立 Typst 源文件. [具体文档](docs/weekly-report.md)
+ paper-first-pass: 对学术论文执行第一遍 triage 阅读, 输出论文快照报告与第二遍阅读建议. [具体文档](docs/paper-first-pass.md)
+ paper-second-pass: 对学术论文执行第二遍理解阅读, 建立方法 mental model 与实验到 claim 的证据映射, 输出 16 节精读报告与第三遍阅读建议. [具体文档](docs/paper-second-pass.md)
+ paper-third-pass: 对学术论文执行第三遍深度阅读, 重建逻辑链并深入分析数学, 实验与代码, 支持完整 20 节报告或围绕指定问题的选择性报告. [具体文档](docs/paper-third-pass.md)
+ mentor-profile: 汇总导师对图形交付物的主观偏好 (实心填充图标, 配色最多 5 种, 板块颜色统一), 用于绘制或调整面向导师的图形. [具体文档](docs/mentor-profile.md)

## 维护与检查

维护要求统一见 [AGENTS.md](AGENTS.md), 修改后按其中的规范审查文档和相关实现.

各个 skill 自带的脚本, 运行依赖和可选验证方式见对应使用文档, 使用者按需准备环境.
