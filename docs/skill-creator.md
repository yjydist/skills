# skill-creator 使用文档

`skill-creator` 依据 Agent Skills 标准创建, 改进和校验 skill 目录. 它先判断请求是否值得做成 skill, 再收集真实请求, 设计描述和触发语料, 决定内容去向, 生成脚手架并运行机械校验.

## 使用前提

+ 将 [skill 目录](../skills/skill-creator/SKILL.md) 连同 `references/` 和 `scripts/` 一起提供给执行工具, 保持相对路径.
+ 脚本需要 Python 3.9+. 脚本硬依赖仅标准库; 安装 PyYAML 时优先使用, 未安装时回退到内置解析器, 不要求安装.
+ 校验脚本面向单个 skill 目录, 该目录至少包含 `SKILL.md`.
+ 触发语料和全新上下文试跑依赖所用客户端. 环境不支持时按本文的降级方式人工判断.

下方示例直接写 `skill-creator`. 所用工具支持 `$skill-creator` 这种调用语法时, 也可以改用该写法; 不支持时, 指定本 skill 的 `SKILL.md` 实际路径.

## 调用示例

```text
使用 skill-creator 判断这个需求是否值得做成 skill: 每周把实验记录整理成固定的周报表格, 需要读取模板并检查缺失项.
```

```text
使用 skill-creator 改进 skills/weekly-report: 用户经常把月报说成"这个月的报告", 但 description 只写了周报和月报, 先检查触发语料再修改.
```

```text
使用 skill-creator 校验 skills/skill-creator, 有警告时说明是否需要处理.
```

新建流程会先给出门槛判断. 不适合新建时, 它会说明理由并建议改旧或改用其他形式, 默认不创建目录.

+ 一次性任务: 说明请求不具备重复性, 建议直接完成任务.
+ 职责已被现有 skill 覆盖: 指出覆盖该职责的具体 skill, 建议在原 skill 上修改而不是新增.
+ 用户明确坚持并接受代价时, 说明代价后按用户决定执行, 并在交付说明中记录该决定和已说明的代价.

说明代价时至少覆盖三项: 长期维护成本, 即文档, 脚本和触发语料需要跟随真实请求持续更新; 与同级 skill 的触发冲突, 即新增的 `description` 会挤占已有 skill 的触发空间, 需要重新做竞争测试; 每次激活的上下文占用, 即名称, 描述和正文都会进入上下文, 正文越长常驻开销越大.

## 脚本用法

### 创建骨架

在仓库根目录运行, 例如:

```bash
tmp=$(mktemp -d)
python3 skills/skill-creator/scripts/init_skill.py my-skill --path "$tmp" --scripts --references
```

命令会创建 `$tmp/my-skill/SKILL.md` 以及 `scripts/` 和 `references/`. 参数说明:

+ `<name>` 会归一化为小写连字符形式, 例如 `My_Skill` 变为 `my-skill`. 归一化后为空或超长时返回非零状态, 不创建任何文件.
+ `--path` 指定父目录, 默认为当前目录.
+ `--scripts`, `--references`, `--assets` 按需创建对应目录.
+ 目标目录已存在时返回非零状态, 不覆盖.
+ 生成的 `SKILL.md` 中 `description` 为空, 正文只有一条 TODO 占位注释. 只填写 `description` 会因正文为空而校验失败, 这是刻意设计; 保留该注释本身不是校验失败条件, 写完正文后应删除它作为清理.

### 校验

```bash
python3 skills/skill-creator/scripts/validate_skill.py skills/skill-creator
```

退出状态和选项:

+ 错误为标准违规, 退出状态为 1.
+ 警告为可移植性或冗余问题, 默认退出状态为 0; 加 `--strict` 时退出状态为 1.
+ `--verbose` 输出 frontmatter 解析器名称, 用于确认 PyYAML 或内置解析器路径.
+ 内置解析器支持常见 YAML 写法 (单行普通标量, 引号标量, 块标量, 一层嵌套映射, 注释, CRLF 和 BOM); 不支持的结构会报错并提示人工确认, 需要完整 YAML 语义时可安装 PyYAML.
+ 本地链接检查覆盖 `SKILL.md` 和 `references/` 下的 Markdown 文件 (`*.md`), `references/` 下其他文本文件中的链接不自动检查, 需要人工核对.
+ 本地链接先按 skill 根目录解析, 未找到再按链接所在文件目录解析; 只能按所在文件目录解析的链接给可移植性警告.
+ 解析路径前先对链接目标做 HTML 实体解码和百分号解码: `&amp;` 按 `&` 处理, `%20` 按空格处理, `%25` 按 `%` 处理, 其他百分号转义同理. 因此文件名含空格时链接写 `%20`, 含 `%` 时写 `%25`.
+ 外部链接, 纯锚点, 行内代码, 围栏和缩进代码块, HTML 注释以及原始 HTML 块内的链接不检查; type 7 块不能打断段落. 行内 `<a href>` 与 `<img src>` 的目标按本地链接检查; CommonMark 自动链接, 片段锚点, 折叠引用与快捷引用, 纯文本参考互引需要人工核对.
+ 链接目标不存在, 含 NUL 或 Unicode Cc 类控制字符 (含 C0, DEL 与 C1), 或引用式链接缺少定义时按错误处理; 绝对路径 (目标存在时), Windows 盘符或 UNC 路径, 越出 skill 目录, 路径大小写与磁盘不一致, 仅能按所在文件目录解析的链接按可移植性警告处理.
+ `assets/` 中的文件不检查是否被引用, 因为资源路径可能由脚本在运行时拼接.

检查项和错误/警告分级见 [规范](../skills/skill-creator/references/spec.md#校验脚本覆盖的检查).

### 运行测试

在完整仓库根目录运行:

```bash
.venv/bin/python -m pytest tests/test_skill_creator.py
```

未安装 pytest 时使用标准库测试运行器:

```bash
python3 -m unittest discover -s tests -p test_skill_creator.py -v
```

系统 Python 未安装 PyYAML 时, 依赖 PyYAML 的解析器对照用例会跳过, 输出中记为 `skipped`. 需要完整覆盖时改用 `.venv/bin/python -m unittest discover -s tests -p test_skill_creator.py -v` 或先安装 PyYAML.

测试覆盖 frontmatter 解析, 字段校验, 链接检查, 错误与警告分级, 两个脚本的退出码和输出. 测试文件见 [test_skill_creator.py](../tests/test_skill_creator.py).

## 未验证项的处理

+ 环境缺少 Python 时, 不运行脚本; 手工创建目录和最小 frontmatter (见 [规范](../skills/skill-creator/references/spec.md#目录结构)), 再按检查项人工核对, 并在交付说明中列出.
+ 未安装 PyYAML 时使用内置解析器, 不自动安装依赖. 对无法识别的 YAML 结构, 人工确认后再继续.
+ 无法启动独立会话时, 由执行者按 `description` 和同级 skill 的描述人工判断触发语料, 标注"人工判断".
+ 无法对照无 skill 或旧版本结果时, 记录为未做基线对照, 不把人工判断写成自动验证.
+ 脚本未执行或某项检查未完成时, 在交付说明中写原因, 不省略.

## 触发语料自检

以下语料按 [写作方法](../skills/skill-creator/references/writing.md) 的竞争测试方法, 只根据 `description` 判断. 竞争测试的语料范围限于 [README](../README.md#skills-列表) 列出的 9 个用户 skill; `.agents/skills/` 下的 OpenSpec 工具 skill 属于外部工具自带内容, 不作为本仓库用户 skill 的同级竞争者参与归属判断, 也不在本语料和复核记录的范围内. 语料共 12 条: 12 条均已完成独立复核, 复核归属与本表的人工判断逐条一致 (12/12), 没有出现两个 skill 同时匹配的请求. 当前环境没有客户端会话入口, 无法试跑真实触发, 下表结果记录为人工判断. 完整的复核记录随本次 change 归档, 不是自动客户端验证.

| 请求 | 期望 | 判断依据 | 本 skill 是否命中 |
| --- | --- | --- | --- |
| 帮我新建一个 skill, 用来把会议纪要整理成行动项. | 本 skill | 新建 skill, 对象和动作明确. | 命中 |
| 这个流程每次都要重复做, 能不能做成一个可复用的技能? | 本 skill | 重复流程, 做成 skill. | 命中 |
| 检查一下 `skills/foo/SKILL.md` 的 description 和链接有没有问题. | 本 skill | 校验 SKILL.md, 描述和链接. | 命中 |
| 我们仓库的 skill 描述总是互相抢触发, 帮我改一下. | 本 skill | 改进触发描述和职责边界. | 命中 |
| 给这个 skill 加一个 references 目录, 把长规范拆出去. | 本 skill | 内容去向, references 目录. | 命中 |
| 解释一下 YAML frontmatter 的语法. | 无 | 通用 YAML/Hugo/Jekyll frontmatter 语法问题, 不涉及 skill 目录或 SKILL.md 的结构与写法. | 未命中 |
| 按 conventional commits 帮我写这次改动的提交消息. | convenient-commit | 提交消息, 该 skill 的描述覆盖此请求. | 未命中 |
| 把这篇论文做成第一遍阅读报告. | paper-first-pass | 论文 triage, 该 skill 的描述覆盖此请求. | 未命中 |
| 帮我把这份周报渲染成 PNG. | weekly-report | 周报渲染, 该 skill 的描述覆盖此请求. | 未命中 |
| 给这个函数加一个单元测试. | 无 | 普通编码任务, 不需要 skill. | 未命中 |
| 用 skill-creator 帮我创建一个每周整理实验记录的 skill. | 本 skill | 明确点名本 skill 并新建 skill. | 命中 |
| 帮我把这次会议记录整理成行动项. | 无 | 一次性任务, 直接完成, 不激活 skill. | 未命中 |

结论: 12 条语料按预期归属, 没有出现两个 skill 同时匹配. 这些归属是人工判断, 不是自动客户端验证; 12 条已完成独立复核, 复核者归属与本表逐条一致 (12/12), 且同样没有出现双匹配. 第 11 条 "用 skill-creator 帮我创建一个每周整理实验记录的 skill" 虽含"每周", 但请求是新建一个整理实验记录的 skill, 不要求生成或渲染周报, 因此归本 skill 而非 weekly-report.

## 进一步阅读

+ [执行流程](../skills/skill-creator/SKILL.md): 门槛判断, 请求收集, 描述设计, 内容分配, 脚手架与校验.
+ [规范](../skills/skill-creator/references/spec.md): 目录结构, frontmatter 字段约束, 命名规则和校验项分级.
+ [写作方法](../skills/skill-creator/references/writing.md): 描述公式, 竞争测试, 触发语料构成和常见失败清单.
+ [返回仓库说明](../README.md).
