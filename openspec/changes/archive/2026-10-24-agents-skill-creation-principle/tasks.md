# Tasks

## 1. 规范文本

- [x] 1.1 在 `AGENTS.md` 的 `## 项目原则` 末尾追加一条, 要求新建 skill 使用 `skills/skill-creator`, 写法与同节的 convenient-commit 条目一致: 一句话说明动作, 用相对链接指向 `skills/skill-creator/SKILL.md`. 完成后确认该节仍是 `+` 开头的无序列表, 链接从 `AGENTS.md` 所在目录解析到实际文件.
- [x] 1.2 检查新增条目与 `skill-creator` 现有职责是否一致: 阅读 `skills/skill-creator/SKILL.md` 的 "适用与门槛", "脚手架与校验", "交付说明" 三节, 确认条目要求的行为都在其中, 不引入 skill-creator 未定义的步骤. 发现不一致时改条目措辞, 不改 skill.

## 2. 一致性检查

- [x] 2.1 按 `AGENTS.md` 的 `## 文档与格式` 核对改动: 简体中文, ASCII 标点, 列表符号为 `+`. 完成后逐条对照该节三条要求, 确认无全角标点.
- [x] 2.2 检索仓库中引用 `AGENTS.md` 维护规范的文档, 确认没有需要同步的副本: 运行 `rg -l "项目原则|AGENTS.md" --glob '!openspec/changes/archive/**'`, 检查命中文件的描述是否与新增条目冲突. 本次预期只有 `README.md` 的 "维护与检查" 小节提及 AGENTS.md 而不复述条目内容, 无需改动; 若出现复述条目内容的文件, 记录并说明处理结论.

## Workflow follow-up

- 变更按仓库约定提交: 使用 `skills/convenient-commit/SKILL.md`, 类型为 `docs`, 作用域为 `agents`.
- 归档前运行 `openspec validate --change agents-skill-creation-principle`, 确认纯文档变更 (skip_specs) 通过校验.
- 归档该变更.
