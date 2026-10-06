# skills

我个人自用的 skill 仓库, 用于维护可复用的任务指导和工作流程.

## 使用方式

+ 在下方列表选择 skill, 阅读对应文档中的使用前提和调用示例.
+ 将对应的 `skills/<skill-name>/` 完整目录提供给支持 skill 的工具, 保留其中的参考文件及相对路径. 具体加载方式以所用工具为准.
+ 每个 skill 的 `SKILL.md` 是执行入口, `docs/` 下的同名文档面向使用者. 仓库维护遵循 [AGENTS.md](AGENTS.md).

## skills 列表

+ convenient-commit: 按逻辑完整性规划提交边界, 拟定提交消息, 并在授权范围内创建 Git 提交. [具体文档](docs/convenient-commit.md)
+ to-github-issue: 收集 session 中的待办和想法, 归纳为带标签的 GitHub issue 草稿, 确认后创建, 必要时拆分 sub-issue. [具体文档](docs/to-github-issue.md)
+ swiss-grid-design: 用瑞士国际主义的网格, 字体与留白创建, 调整或评审多媒介视觉方案, 明确默认参数和功能例外. [具体文档](docs/swiss-grid-design.md)
+ weekly-report: 将用户提供的学期, 周次与本周进展条目填入 Typst 模板, 渲染为 SVG 周报矢量图与 Typst 源文件. [具体文档](docs/weekly-report.md)
+ paper-first-pass: 对学术论文执行第一遍 triage 阅读, 输出论文快照报告与第二遍阅读建议. [具体文档](docs/paper-first-pass.md)
+ paper-second-pass: 对学术论文执行第二遍理解阅读, 建立方法 mental model 与实验到 claim 的证据映射, 输出 16 节精读报告与第三遍阅读建议. [具体文档](docs/paper-second-pass.md)
+ paper-third-pass: 对学术论文执行第三遍深度阅读, 重建逻辑链并深入分析数学, 实验与代码, 输出 20 节 Deep Reading Report 与研究延伸方向. [具体文档](docs/paper-third-pass.md)
