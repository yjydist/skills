# skill-creator 使用文档

`skill-creator` 依据 Agent Skills 标准创建, 改进和校验 skill 目录. 它先判断请求是否值得做成 skill, 再收集真实请求, 设计描述和触发语料, 决定内容去向, 生成脚手架并运行机械校验.

## 使用前提

+ 将 [skill 目录](../skills/skill-creator/SKILL.md) 连同 `references/` 和 `scripts/` 一起提供给执行工具, 保持相对路径.
+ 分发 skill 时排除 `node_modules` 等依赖目录, 不要把依赖目录打进分发产物; 依赖由使用者在 skill 目录按 [前提条件](../skills/skill-creator/SKILL.md#前提条件) 自行安装, 安装命令见下一条.
+ 脚本需要 Node.js 20+, 建议 22+. 检查: 先 `command -v node`, 再 `node -e "process.exit(Number(process.versions.node.split('.')[0]) < 20 ? 1 : 0)"`; 两条命令任一非零 (命令不存在或版本低于 20) 按缺失处理. 第三方依赖 `yaml`, `mdast-util-from-markdown` 和 `decode-named-character-reference` 安装在 skill 目录的 `node_modules`, 不提交 `package.json` 或锁文件. 首次使用时在 skill 目录运行 `npm install --no-save --no-package-lock --prefix . yaml mdast-util-from-markdown decode-named-character-reference`.
+ npm 是安装上述依赖所需的外部程序, 随 Node.js 一起安装, 与 `SKILL.md` 的前提条件一致. 检查: `npm -v`; 命令不存在或非零状态按缺失处理, 按五段报告缺少项, 检测结果, 要求, 修复命令, 影响. Node.js 或 npm 缺失时, 修复命令由执行者按目标平台给出 (例如用 nvm 或系统包管理器安装 Node.js 20+), 其中 npm 缺失按修复 Node.js 安装处理, 不单独安装系统程序; 第三方依赖缺失时使用上一条给出的 `npm install` 命令.
+ 上述 Node.js, npm 与依赖可导入检查命令按 POSIX shell (sh/bash) 编写. Windows PowerShell 使用以下等价命令, 判定规则和退出状态相同: PowerShell 侧 `Get-Command` 失败时把 `$?` 置为 `False`, 不设置 `$LASTEXITCODE`; 判定依据是 `$?`, 不是进程退出码. `$LASTEXITCODE` 没有更新时会保留上一条本机命令的旧值, 因此不能作为判定依据; `node`/`npm` 这类本机命令的 `$?` 由其退出码派生, 判 `$?` 同样正确.

  ```powershell
  Get-Command node
  node -e "process.exit(Number(process.versions.node.split('.')[0]) < 20 ? 1 : 0)"
  Set-Location <skill 目录>
  node scripts/check_dependencies.mjs
  npm -v
  node -e "process.exit(0)"
  ```

  其中 `Get-Command node` 对应 `command -v node`; `Set-Location <skill 目录>` 后运行 `node scripts/check_dependencies.mjs` 对应依赖可导入检查的 `cd <skill 目录> && node scripts/check_dependencies.mjs`, 两行分开执行, 不使用 Windows PowerShell 5.1 不支持的 `&&`; `npm -v` 对应 npm 条目的存在与可执行检查; 最后一条 `node -e "process.exit(0)"` 代替 "无其他外部程序与认证要求" 条目的 `true`.
+ 脚本使用的依赖包名同时记录在 `skills/skill-creator/scripts/dependency-list.mjs`: 它是代码侧包名清单, 供运行时探测使用, 不参与安装, 不是 `package.json` 或锁文件. 修改依赖时需同时更新 `SKILL.md` 的 `## 前提条件` (依赖条目与修复命令) 与该文件, 保持文档清单与代码清单一致.
+ 依赖可导入检查: 首选写法是 `cd <skill 目录> && node scripts/check_dependencies.mjs`. 脚本按自身位置解析 skill 目录的 `node_modules`, 与当前工作目录无关, 但命令中的脚本路径仍须按当前目录书写. 在 skill 目录运行 `node scripts/check_dependencies.mjs`, 在仓库根目录运行 `node skills/skill-creator/scripts/check_dependencies.mjs`, 其他目录使用绝对路径或可解析到该脚本的路径. 通过时输出三个包的版本, 缺失时输出缺少项, 检测结果, 要求, 修复命令, 影响五段并以非零状态退出, 不自动安装. Windows PowerShell 用 `Set-Location <skill 目录>` 后运行 `node scripts/check_dependencies.mjs` (不用 `&&`).
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

`init_skill.mjs` 与 `validate_skill.mjs` 两个脚本都先检查 Node.js 版本 (需要 20+, 建议 22+), 再响应 `--help`/`-h` 和依赖探测: 版本不足时按五段报告退出 1; 版本满足后 `--help`/`-h` 在依赖探测之前响应, 不要求已安装第三方依赖. `check_dependencies.mjs` 只做同样的版本守卫和依赖探测, 不响应 `--help`/`-h`, 附加参数不会改变其行为.

### 创建骨架

在仓库根目录运行, 例如:

```bash
tmp=$(mktemp -d)
node skills/skill-creator/scripts/init_skill.mjs my-skill --path "$tmp" --scripts --references
```

命令会创建 `$tmp/my-skill/SKILL.md` 以及 `scripts/` 和 `references/`. 参数说明:

+ `<name>` 会归一化为小写连字符形式, 例如 `My_Skill` 变为 `my-skill`. 归一化后为空或超长时返回非零状态, 不创建任何文件.
+ `--help` 或 `-h` 输出用法并以 0 退出, 不创建任何文件, 也不探测第三方依赖.
+ `--path` 指定父目录, 默认为当前目录.
+ `--scripts`, `--references`, `--assets` 按需创建对应目录.
+ 目标目录已存在时返回非零状态, 不覆盖.
+ 生成的 `SKILL.md` 中 `description` 为空, 正文是带 TODO 和占位符的 `## 前提条件` 占位节. `description` 留空时校验失败, 这是刻意设计; 占位节本身已使正文非空, 所以只填 `description` 也能通过机械校验, 但这不算完成: 必须把占位符替换为实际的运行时, 依赖, 外部程序和认证条目, 补充流程正文并删除两处 TODO 后才能交付.

### 校验

```bash
node skills/skill-creator/scripts/validate_skill.mjs skills/skill-creator
```

退出状态和选项:

+ 错误为标准违规, 退出状态为 1.
+ 警告分为内容问题和可移植性问题, 默认退出状态为 0; 加 `--strict` 时退出状态为 1. 内容问题包括非标准 frontmatter 字段, `scripts/` 或 `references/` 中未被 `SKILL.md` 引用的文件, 参考文件互相引用, 正文超过 500 行.
+ `--help` 或 `-h` 输出用法并以 0 退出, 不探测第三方依赖.
+ 依赖可导入时, 缺少必需参数, 未知选项或多余位置参数会输出用法并以 2 退出; 依赖缺失时先按 `## 前提条件` 阻断并以 1 退出.
+ 长选项须写全, 不接受 argparse 式前缀缩写: `--str`, `--verb` 等前缀缩写按未知选项处理, 输出用法并以 2 退出, 与完整长选项 (`--strict`, `--verbose`) 不同.
+ `--verbose` 输出 `frontmatter 解析器: yaml <版本>`, 用于确认依赖版本.
+ frontmatter 由 `yaml` 包按 YAML 1.2 core schema 解析. 与 YAML 1.1 不同, `yes`, `no`, `on`, `off` 和形如日期的纯量按字符串处理. 重复键会被拒绝并报告为解析错误, 不再像 PyYAML 那样静默覆盖. 无法解析时报告行号, 不静默修正; 错误文案来自 `yaml` 库, 与 PyYAML 不同, 例如重复键报 `Map keys must be unique`.
+ 本地链接检查覆盖 `SKILL.md` 和 `references/` 下的 Markdown 文件 (`*.md`), `references/` 下其他文本文件中的链接不自动检查, 需要人工核对.
+ 本地链接先按 skill 根目录解析, 未找到再按链接所在文件目录解析; 只能按所在文件目录解析的链接给可移植性警告.
+ 解析路径前先对链接目标做 HTML 实体解码和百分号解码: 命名 HTML 实体按完整实体表解码 (依赖 `decode-named-character-reference`), 数字实体按码点解码, 未知实体保留原文. 与 Python `html.unescape` 一致, legacy 命名实体 (如 `&amp`, `&lt`, `&gt`, `&quot`, `&nbsp`, `&copy`, `&reg` 等) 与数字实体 (如 `&#65`, `&#x41`) 允许省略结尾分号: 命名实体先按完整名称查找, 未命中时取最长的 legacy 名称前缀, 其余字符原样保留, 因此 `&ampb` 按 `&b` 处理, `&#65b` 按 `Ab` 处理; 非 legacy 名称省略分号时不解码, 保留原文; `%20` 按空格处理, `%25` 按 `%` 处理, 其他百分号转义同理. 因此文件名含空格时链接写 `%20`, 含 `%` 时写 `%25`.
+ 外部链接, 行内代码, 围栏和缩进代码块, HTML 注释以及原始 HTML 块内的链接不检查; 纯锚点跳过目标存在性检查与标题锚点核对, 但完整目标仍做控制字符检查; 行内 `<a href>` 与 `<img src>` 的目标按本地链接检查; CommonMark 自动链接, 片段锚点, 折叠引用与快捷引用, 纯文本参考互引需要人工核对. 行内 HTML 标签从标签名到 `>` 超过 2048 字符时按普通文本处理, 其中的链接不再检查. 块级 HTML 的范围按 CommonMark 判定, 列表项内的块级标签同样整块屏蔽, 其中的链接不检查.
+ 链接目标不存在, 含 NUL 或 Unicode Cc 类控制字符 (含 C0, DEL 与 C1), 或引用式链接缺少定义时按错误处理; 绝对路径 (目标存在时), Windows 盘符或 UNC 路径 (反斜杠形式如 `\\server\share\demo.md` 与正斜杠形式如 `//server/share/demo.md`), 越出 skill 目录, 路径大小写与磁盘不一致, 仅能按所在文件目录解析的链接按可移植性警告处理. 正斜杠 UNC 形式按 Windows UNC 路径处理, 不是外部链接; 带协议的外部链接 (如 `http://`, `https://`) 仍按外部链接跳过.
+ `scripts/` 和 `references/` 中未被 `SKILL.md` 直接引用或正文提到的文件给警告; `assets/`, 顶层文件和依赖目录不检查. 依赖目录是路径中任一分量为 `node_modules`, `vendor`, `third_party`, `venv`, `virtualenv` 或 `site-packages` 的目录, 该集合是本校验器的约定, 不是 Agent Skills 标准要求.
+ `## 前提条件` 一节的存在性与条目内容不在自动检查范围内, 必须人工核对; 该节是本流程的强制项, 不是 Agent Skills 标准的要求, 校验通过不代表该节已满足.

检查项和错误/警告分级见 [规范](../skills/skill-creator/references/spec.md#校验脚本覆盖的检查).

### 运行测试

首次运行前需先按 `## 使用前提` 在 `skills/skill-creator` 安装依赖 (可使用该节的 `npm install --no-save --no-package-lock` 命令), 因为 `node_modules` 不随仓库提交.

在完整仓库根目录运行:

```bash
node --test tests/skill_creator/
```

测试使用 `skills/skill-creator/node_modules` 中已安装的依赖. 测试覆盖 frontmatter 解析, 字段校验, 链接检查, 未引用文件, 错误与警告分级, 三个脚本 (`init_skill.mjs`, `validate_skill.mjs`, `check_dependencies.mjs`) 的退出码和输出, 以及 `SKILL.md` 的章节顺序, 相对链接和标题锚点. 测试文件见 [tests/skill_creator](../tests/skill_creator).

## 未验证项的处理

+ 环境缺少 Node.js 或依赖时, 不运行脚本; 按 [运行前提](../skills/skill-creator/references/spec.md#运行前提) 报告缺少项并等待用户选择. 用户授权降级后, 手工创建目录和最小 frontmatter (见 [规范](../skills/skill-creator/references/spec.md#目录结构)), 再按检查项人工核对, 并在交付说明中列出.
+ 依赖安装失败时, 保留 npm 的原始错误, 按前提缺失处理, 不自动改写依赖清单或静默降级; 安装成功后重新执行前提检查, 通过后才继续.
+ 无法启动独立会话时, 由执行者按 `description` 和同级 skill 的描述人工判断触发语料, 标注"人工判断".
+ 无法对照无 skill 或旧版本结果时, 记录为未做基线对照, 不把人工判断写成自动验证.
+ 脚本未执行或某项检查未完成时, 在交付说明中写原因, 不省略.

## 触发语料自检

以下语料按 [写作方法](../skills/skill-creator/references/writing.md) 的竞争测试方法, 只根据 `description` 判断. 竞争测试的语料范围限于 [README](../README.md#skills-列表) 列出的 9 个用户 skill; `.agents/skills/` 下的 OpenSpec 工具 skill 属于外部工具自带内容, 不作为本仓库用户 skill 的同级竞争者参与归属判断, 也不在本语料和复核记录的范围内. 语料共 12 条: 12 条均已完成独立复核, 复核归属与本表的人工判断逐条一致 (12/12), 没有出现两个 skill 同时匹配的请求. 当前环境没有客户端会话入口, 无法试跑真实触发, 下表结果记录为人工判断. 完整的复核记录见 `openspec/changes/archive/2026-10-24-add-skill-creator/verification.md` 的 `## 独立语料复核记录` 一节 (该记录为 Python 版时期的归档, 命令与脚本名已不适用于当前 Node.js 实现, 12 条语料结论沿用), 不是自动客户端验证.

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
+ [运行前提](../skills/skill-creator/references/spec.md#运行前提): 前提声明, 阻断流程和依赖安装边界.
+ [写作方法](../skills/skill-creator/references/writing.md): 描述公式, 竞争测试, 触发语料构成和常见失败清单.
+ [返回仓库说明](../README.md).
