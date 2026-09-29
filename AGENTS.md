# AGENTS.md

提供给 Agent 阅读的文档

## 项目原则

+ 所有创建的 skill, 自然语言必须使用简体中文, 标点符号必须使用 ASCII 标点, 只有必要的地方使用英语
+ 进行 git 提交的时候, 请使用 `skills/convenient-commit` 目录下的技能
+ `skills` 目录下面的每个 skill, 在 `docs` 目录下面都要创建个对应的使用文档. 比如: `skills/<skill-name>` 那创建 `docs/<skill-name>.md`
+ `skills` 目录下面的每个 skill, 在 `README.md` 的 `## skills 列表` 下面都要创建一个列表项. 使用 `+` 列表语法. 格式是: `<skill-name>: <skill 的简短简介> [具体文档](docs/<skill-name>.md)
+ markdown 的无序列表语法统一使用 `+` 符号