# Tasks

## 1. 契约与表述规则 (SKILL.md)

- [x] 1.1 重写 `skills/weekly-report/SKILL.md` frontmatter 的 `description`, 让"事实沿用用户提供的内容"与"条目按事项式汇报口吻呈现"并存, 删除 `原样保留内容` 这一整体保留的说法. 验证: 查看该文件前 5 行, 确认 YAML 有效, `name` 仍为 `weekly-report`, `description` 不含 `原样保留`
- [x] 1.2 在 `## 工作流程` 的 "收集内容" 一节新增条目表述说明: 事项式陈述, 一条一个动作, 动词开头, 省略主语, 不写周期词, 不描述过程与情绪, 不加自我修饰, 冲突时以事实准确与可读性优先; 并给出 4 组口语叙述到条目的正反对照. 验证: 逐条比对 `specs/weekly-report/spec.md` 的 `条目表述` 与 `事实原样保留` 场景, 7 个场景在该节及 "操作边界" 中都能找到对应说明
- [x] 1.3 改写 "收集内容" 与 "操作边界" 中与新契约冲突的措辞 (`保留原文`, `不增删或改写`, `不虚构, 补写或润色`), 明确事实层是硬约束, 表述层允许按汇报口吻规范化. 验证: `grep -n "不改写\|润色\|原样保留" skills/weekly-report/SKILL.md` 无与两条新需求矛盾的行
- [x] 1.4 更新 `SKILL.md` 中 JSON 示例的条目为动宾风格, 条目末尾不加句号, 条目内标点改为 ASCII 逗号. 验证: 将示例 JSON 存为临时文件后调用 `scripts/render.py` 的 `validate_report` 校验通过
- [x] 1.5 在 "核对并交付" 一节增加表述核对项: 条目不含第一人称与周期词, 人名, 项目名与数字与用户提供的一致. 验证: 该节含这三项检查, 且用 `grep -n "第一人称" skills/weekly-report/SKILL.md` 能定位

## 2. 示例与对外文档对齐

- [x] 2.1 将 `references/weekly-template.typ` 与 `references/monthly-template.typ` 数据块中的示例条目改为动宾风格, 去掉名词化与句号, 全角标点改为 ASCII. 验证: `grep -n "查看和对比\|阅读师兄" skills/weekly-report/references/*.typ` 命中新示例, 且 `grep -n "的查看和对比。" skills/weekly-report/references/*.typ` 无命中; 运行 `python3 -m unittest discover -s tests -p test_weekly_report.py -v` 通过
- [x] 2.2 同步 `docs/weekly-report.md`: 首段的 "保留原文和版式, 不代为归纳或编造进展" 改为两层口径, 调用示例中的条目与 `SKILL.md` 示例保持同一风格. 验证: 文档内无与新需求矛盾的句子, 且文档中的相对链接仍可解析
- [x] 2.3 同步 `README.md` 的 `skills 列表` 中 `weekly-report` 条目简介, 去掉 `原样保留用户内容` 的旧说法. 验证: `grep -n "weekly-report:" README.md` 的简介与 `SKILL.md` 的 `description` 口径一致, 其链接 `docs/weekly-report.md` 存在

## 3. 集成验证

- [x] 3.1 用一份含口语叙述的输入分别渲染周报与月报, 用图像查看工具确认条目为事项式陈述, 无第一人称与周期词, 条目数量与事实同输入一致. 验证: 实际渲染并查看生成的 PNG
- [x] 3.2 运行基础测试与真实渲染测试, 确认示例改动未破坏现有断言. 验证: `python3 -m unittest discover -s tests -p test_weekly_report.py -v` 与 `RUN_TYPST_TESTS=1 python3 -m unittest discover -s tests -p test_weekly_report.py -v` 均通过
- [x] 3.3 按 `AGENTS.md` 的变更检查逐项自查: frontmatter, 使用文档, README 条目, 相对链接与标题锚点, `## 前提条件` 与实际依赖一致. 验证: 逐项给出核对结论与未验证原因

## Workflow follow-up

- 评审通过后归档该 change, 归档时把 delta 同步进 `openspec/specs/weekly-report/spec.md`.
