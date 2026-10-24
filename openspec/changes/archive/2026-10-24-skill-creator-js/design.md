# Design

## Context

见 [proposal.md](proposal.md) 的 Why. 当前 `scripts/validate_skill.py` 2594 行中约 630 行是手写 YAML 1.1 解析器, 约 1290 行是手写 CommonMark 扫描器; `tests/test_skill_creator.py` 5387 行, 270 个用例. 换到 Node.js 后, 这两块解析逻辑由 npm 包承载, 校验输出契约在 "已接受的行为变化" 之外保持不变.

## Goals / Non-Goals

**Goals:**

+ 脚本改为 `.mjs`, 在 Node.js 20+ 下运行, CLI 参数名称与退出码保持不变; 长选项须写全, 不接受 argparse 式前缀缩写, 见 "已接受的行为变化".
+ 错误/警告文案与退出状态在 "已接受的行为变化" 与 `references/spec.md` 的解析细则边界之外保持不变; 行内 HTML 标签/注释的识别边界 (未闭合标签, 超过 2048 字符的标签, 行中未闭合注释) 属 CommonMark 解析取舍, 未逐条列入本清单; CLI 用法/参数错误文案是列出的例外之一, 退出码不变.
+ 用库替换手写解析器, 保留逐行诊断能力.
+ 依赖按需安装到 skill 目录内的 `node_modules`, 不提交任何包管理器依赖清单或锁文件; 代码内包名清单由 `scripts/dependency-list.mjs` 维护, 只用于运行时探测, 不参与安装.
+ 给出 `## 前提条件` 的统一格式和阻断流程.

**Non-Goals:**

+ 不迁移 `weekly-report/render.py`, 仓库保持双语言.
+ 不新增独立的校验类别, 只按现行 `references/spec.md` 扩展既有类别覆盖的范围 (片段/查询/纯锚点控制字符, 跨行行内 HTML 标签); 与 Python 基线相比, 错误数与退出状态的差异限于 "已接受的行为变化" 列出的部分与 `references/spec.md` 的解析细则边界. 忽略列表在保留 `__pycache__`/`.pyc` 的基础上增加 `node_modules` 与依赖目录.
+ 不做按执行路径的差异化前提检查.
+ 不在 `AGENTS.md` 或 `validate_skill` 中强制 `## 前提条件`; 由 skill-creator 的流程保证.

## 已接受的行为变化

相对 Python 基线 (`tests/oracle/`), 下列项目会改变输出文案, 错误数或退出状态. 它们由现行 spec, CommonMark 语义或 CLI 文案统一要求决定, 不是实现缺陷; CLI 与脚手架项由契约测试覆盖, 其余每项都有对应 fixture, 复现输出见 [verification.md](verification.md).

+ **YAML 1.2 语义**: 见决策 2; `duplicate-keys` 与 `yaml11-scalars` 的错误判决与退出状态与基线相反 (verification.md 差异 1).
+ **第三方 YAML 库的错误文案**: 见决策 2; 同一非法 YAML 由 PyYAML 与 `yaml` 包各自报错, 行号与前缀 `错误: SKILL.md:<行号>: 无法解析 frontmatter: ` 一致, 只有库自身的 problem 文案不同. 判决不变, 两侧均报 1 个错误并退出 1. 该文案由第三方库给出, 不属于本仓库控制的契约, 文档与测试不断言具体文字 (verification.md 差异 2).
+ **依赖目录忽略列表**: 见 Non-Goals; 依赖目录内的文件不再产生未引用警告, 退出状态仍为 0 (verification.md 差异 3).
+ **非法 UTF-8 的解码文案**: 两侧都以 fatal 模式按 UTF-8 读取 `SKILL.md`, 判决与退出码一致 (均报 1 个错误并退出 1), 前缀 `错误: SKILL.md: 不是有效的 UTF-8 文本: ` 相同; Python 附带字节值与位置, Node 的 `TextDecoder` 只给出通用说明, 因此尾段文字不同. 该文案由各自的解码器给出, 不属于本仓库控制的契约 (verification.md 差异 4).
+ **`list-item-html-block`**: 列表项内的原始 HTML 块按 `references/spec.md` 整块屏蔽, 块内 Markdown 链接不检查. 基线报 1 个错误并退出 1, Node 输出 `校验通过.` 并退出 0, `--strict` 同理 (verification.md 差异 5).
+ **`escaped-html`**: 反斜杠转义 (`\<`, `\>`) 后的 HTML 标签按 CommonMark 是字面文本, 不产生 `html` 节点, 其中的 `href`/`src` 不按链接检查. 基线报 1 个错误并退出 1, Node 输出 `校验通过.` 并退出 0 (verification.md 差异 6).
+ **`duplicate-same-line` 与 `mixed-encoded-same-line`**: 同一行指向同一目标的多条链接按"行号 + 解码后的完整目标"去重, 只报告一次; 解码按本地链接规则处理实体与百分号编码, 因此 `a&b.md`, `a&amp;b.md` 与 `a%26b.md` 视为同一目标, 片段或查询不同的目标仍各自报告. 前者由 2 个错误变为 1 个, 后者由 3 个错误变为 1 个, 退出码同为 1 (verification.md 差异 7).
+ **片段, 查询与纯锚点中的控制字符**: `references/spec.md` 要求控制字符检查覆盖完整链接目标, 含 `#` 后的片段与 `?` 后的查询, 纯锚点与仅含查询的目标也检查. `fragment-control-chars` 中 Python 基线拆分路径后检查存在性, 纯锚点直接跳过, 输出 `校验通过.` 并退出 0; Node 报 3 个错误并退出 1, `--strict` 同理 (verification.md 差异 8).
+ **跨行行内 HTML 标签**: `references/spec.md` 要求行内 `<a href>`/`<img src>` 目标按本地链接检查且标签可以跨行, 目标缺失按属性值所在行报告. `multiline-html-tag` 中 Python 基线的属性正则遇到换行即放弃, 输出 `校验通过.` 并退出 0; Node 报 `SKILL.md:9` 的缺失目标并退出 1, `--strict` 同理 (verification.md 差异 9).
+ **`<<` 合并键不再展开**: 见决策 2; YAML 1.2 core schema 没有合并键, `metadata: {<<: *defaults}` 中的 `<<` 按普通键处理. PyYAML 展开合并后输出 `校验通过.` 并退出 0; Node 因 `metadata.<<` 的值是映射而报 `错误: SKILL.md:4: metadata.<< 的值必须是字符串` 并退出 1, `--strict` 同理 (verification.md 差异 10). 这是按 YAML 1.2 语义执行的预期结果, 不是实现缺陷.
+ **长选项前缀缩写**: Python 的 argparse 在每个脚本内接受无歧义的长选项前缀 (`validate_skill.py` 的 `--str`, `--verb`; `init_skill.py` 的 `--pa`, `--scr`), Node 的 `parseArgs` 只接受完整长选项 (`--strict`, `--verbose`, `--path`, `--scripts`, `--references`, `--assets`, `--help`). 前缀缩写按未知选项处理: 输出用法并退出 2, 不解码为对应选项; 基线按缩写正常执行, 退出码取决于该次校验结果 (例如 `--verb` 在无警告目录上为 0, `--str` 在仅有警告的目录上为 1, 因为 `--strict` 把警告升级为错误). 完整长选项的行为不变.
+ **CLI 用法/参数错误文案**: 无参数, 未知选项和多余参数时, Python 输出 `usage: validate_skill.py ...` 与 `error: ...`, Node 输出中文用法行 `用法: node validate_skill.mjs <skill 目录> [--strict] [--verbose] [--help]` (未知选项时其前另有 `parseArgs` 的错误描述); `init_skill.mjs` 同样使用 `用法:` 前缀, 用法行列出 `[--help]`. 判定条件和退出码不变, 均为 2.
+ **`init_skill.mjs` 的骨架与提示**: 见 tasks.md 4.1; 骨架的 `description` 留空并新增 `## 前提条件` 占位节, 成功提示改为说明填写占位内容并运行 `node` 校验脚本. 退出码与判定条件不变, 由 `tests/skill_creator/init.test.mjs` 覆盖, 记录见 [verification.md](verification.md) 的 5.2.
+ **引用式定义识别范围**: 迁移到 mdast 后按 CommonMark 识别引用式定义, 识别范围比 Python 基线的手写扫描器大: 块引用定义可以打断段落 (正文行之后直接写 `> [文档]: real.md`), 定义标题可以跨行 (`[文档]: real.md "标` 换行 `题"`). 这两类写法在 Python 基线中报 `错误: SKILL.md:<行号>: 引用式链接定义不存在: 文档` 并退出 1, 当前实现识别出定义, 输出 `校验通过.` 并退出 0, `--strict` 同理. 基线未识别的原因是其手写扫描器的实现限制: 普通段落行之后不带空行的 `> [标签]: 目标` 被当作段落惰性续行, 定义标题被要求在一行内闭合; 这是 mdast 按 CommonMark 识别定义与基线扫描器的对照结果, 与现行 `references/spec.md` 无关 (该条只记录当前实现不登记定义的三类写法). 这两类不在 32 个 fixture 内, 属记录在案的差异, 复现命令与输出见 [verification.md](verification.md) 的 "附: 32 个 fixture 之外的引用式定义识别差异".

上述 14 项中, 前 10 项与 [verification.md](verification.md) 的 32 个 fixture 差异 (共 10 类) 按编号一一对应 (本文件条目前的 (verification.md 差异 N) 即映射关系); 长选项前缀缩写, CLI 用法/参数错误文案, `init_skill.mjs` 骨架/提示与引用式定义识别范围这四项不产生 fixture 差分条目: 前两项由契约测试覆盖, `init_skill.mjs` 骨架/提示由 `init.test.mjs` 覆盖, 引用式定义识别范围由 [verification.md](verification.md) 的附注记录.

因此"文案与退出码不变"只适用于上述项目之外的行为. 链接检查的范围以 `references/spec.md` 与 delta spec 为准, 不要求与 Python 基线逐条一致; 除 `--verbose` 下的解析器名称外, 未列出的 fixture 输出与退出码必须一致.

## Decisions

### 1. ESM + `.mjs`

没有 `package.json` 时 `.js` 按 CJS 解析, 所以脚本统一用 `.mjs` 和 `import`. CLI 解析用 `node:util` 的 `parseArgs`, 不引第三方命令行库.

### 2. YAML 用 `yaml` 包的 1.2 语义

`yaml` 包是纯 JS, 支持位置信息和自定义 tag. 采用默认 1.2 core schema, 不再模拟 PyYAML 1.1 的 `yes/no/on/off` 布尔值, 时间戳, 六十进制整数和 `<<` 合并键展开. 理由: SKILL.md frontmatter 的实际字段很简单, 1.1 的隐式类型转换对 `description` 反而容易产生意外; 官方标准也没有要求 1.1. 这是行为变化, 需要在 `references/spec.md` 和测试中明确记录.

`<<` 合并键的差异最容易被忽略: YAML 1.2 core schema 没有合并键, `<<` 只是普通映射键, 其值不会合并进所在映射. `metadata: {<<: *defaults}` 在 PyYAML 下展开成若干字符串字段并通过校验, 在 `yaml` 包下则因 `metadata.<<` 的值是映射而报 `metadata.<< 的值必须是字符串` 并退出 1. 需要复用字段时显式写出每个键值.

替代方案: `js-yaml` 同样可用, 但 `yaml` 的 AST/位置信息更完整, 且支持后续按需扩展.

### 3. Markdown 用 `mdast-util-from-markdown` + `micromark`

mdast 每个节点带 `position.start.line`, 满足"指出文件与行号"的要求. 代码块, 行内代码, HTML 块/行内 HTML 都由 AST 给出边界, 不再需要手写 CommonMark 扫描器.

`link`, `image`, `definition` 直接映射到现有的链接检查. 三类内容需要额外处理:

+ **缺失的引用式定义**: CommonMark 在定义不存在时把 `[文本][标签]` 解析成普通文本, AST 中不会出现 `linkReference`. 实现为: 用 AST 给出的代码块, 行内代码, HTML 和定义位置构造屏蔽文本, 再对剩余文本做一次带转义处理的引用语法扫描. 该扫描需要自己处理标签查找 (`findLabelEnd`), 行内目标解析 (`parseLinkDestination`, 含尖括号, 反斜杠转义, 括号配对与可选 title), 标签归一化 (`casefold`/`normalizeReferenceLabel`) 和偏移到行号换算. 实现完成后统计, 引用扫描与原始目标/定义扫描合计约 590 行 (仅 `parseLinkDestination` 与 `scanReferenceLabels` 已有 130 余行), 远小于原手写 CommonMark 扫描器的约 1290 行; 结论不变, 仍是"在屏蔽文本上做有界扫描", 没有回退成完整 CommonMark 扫描器.
+ **裸行内目标中的控制字符**: 既有要求规定本地链接目标不得含 NUL 或 Cc 类控制字符 (见 `references/spec.md`). mdast 对裸目标内含控制字符的 `](...)` 不产出 `link`/`image` 节点 (实测只剩 `text`), 只靠 AST 会漏报. 因此实现额外对同一份屏蔽文本做一次有界原始行内目标扫描: 定位未被转义的 `](`, 用 `readInlineTargetAt` 读取紧跟的裸目标或 `<...>` 目标; 读取目标前允许开括号/定义冒号后一个换行与续行缩进, 该空白由 `skipTargetSpace` 跳过, 只有目标内部出现换行才放弃. 目标本身不跨行 (遇换行即放弃), 标签回溯遇到空行或文本开头即停止, 因此扫描由结构自然限制, 不依赖固定长度上限 (本次迁移早期的 Node 草稿 (未入库) 中的 512 与 999 上限已移除, 超长目标或超长标签中的控制字符不再漏检). 扫描结果与 AST 已得到的链接按"行号 + 目标"去重后, 再对目标做控制字符检查. 扫描基于屏蔽文本, 所以代码块, 行内代码, HTML 和已解析的定义天然跳过, 转义由 `isEscapedAt` 与 `readInlineTargetAt` 处理. 该段约 160 行, 与引用扫描共用屏蔽文本和行号索引.
+ **行内 HTML 属性**: `<a href>` 与 `<img src>` 仍从 `html` 节点的内容里提取, 但节点边界由 AST 提供, 不需要判断块类型. 标签可跨行 (以 CommonMark 仍识别为行内 HTML 为前提), `readHtmlTagEnd` 允许换行并有 2048 字符上限; 属性值按 HTML 规则解析 (引号内保留换行与 `>`, 未加引号的在空白处结束), 行号由 `lineAtOffset` 按属性值所在位置计算.

链接目标的路径解析还需要命名 HTML 实体解码 (`references/spec.md` 要求 `&sol;`, `&amp;` 等按实体解码后再解析路径). 该部分直接使用 `decode-named-character-reference` 的默认导出 `decodeNamedCharacterReference`, 因此它是第三个直接依赖, 与 `yaml`, `mdast-util-from-markdown` 并列写入 `## 前提条件` 和修复命令, 不靠 `micromark` 的传递依赖提供.

替代方案: `markdown-it` 只有块级 `map`, 拿不到段落内元素的精确行号, 会让诊断退化为块级, 不采用. 保留手写扫描器则失去换语言的主要收益, 不采用.

### 4. 依赖安装

`## 前提条件` 是文档侧的清单, `scripts/dependency-list.mjs` 是代码侧的清单; 两者必须同步. 缺失时执行:

```bash
npm install --no-save --no-package-lock --prefix <skill> yaml mdast-util-from-markdown decode-named-character-reference
```

已实测: 该命令只生成 `<skill>/node_modules`, 不生成 `package.json` 或锁文件. 脚本位于 `<skill>/scripts/`, `import` 会向上解析到 `<skill>/node_modules`, 与当前工作目录无关.

三个包都是脚本直接 `import` 的直接依赖, 不是靠其他包传递带入的: `yaml` 用于 frontmatter, `mdast-util-from-markdown` 用于 Markdown AST, `decode-named-character-reference` 用于链接目标的命名 HTML 实体解码 (见决策 3). 后者的默认导出 `decodeNamedCharacterReference` 在 `scripts/validate_skill.mjs` 中直接导入并调用, 所以即使它也是 `mdast-util-from-markdown` 的传递依赖之一, 也必须显式列入 `## 前提条件` 与修复命令, 不能依赖提升后的传递安装.

三个脚本通过 `scripts/dependency-list.mjs` 共用同一份依赖清单: 该文件只导出包名数组, 不导入包本身, 因此缺少 `node_modules` 时仍可被加载; `validate_skill.mjs`, `init_skill.mjs` 与 `check_dependencies.mjs` 都从它导入, 不各自维护副本. 修改依赖时, 需同时更新 `SKILL.md` 的 `## 前提条件` 与该文件, 保持文档清单与代码清单一致.

依赖探测由 `scripts/check_dependencies.mjs` 承担, 可直接从任意工作目录执行. 该脚本按 `import.meta.url` 定位自身, 取上一级得到 skill 目录, 再由 `createRequire(import.meta.url)` 从该位置向上解析 `node_modules`, 因此结果与 cwd 无关. 脚本只探测和报告: 全部可导入时退出 0 并打印包名与版本; 缺失时退出 1, 按固定格式输出缺少项, 检测结果, 要求, 修复命令和影响. 它不执行安装, 也不写任何文件.

依赖安装由执行者按 `## 前提条件` 完成, 脚本自身不自动安装, 只在导入失败时给出指向该节的明确错误.

### 5. 前提检查的执行模型

每个 skill 维护一份全局清单, 不按路径裁剪. 检查顺序: `command -v <runtime>` → 版本比较 → 依赖目录存在 → 包可导入 → 外部程序/认证. 运行时不满足时无法用自身检查自身, 所以第一步必须是 shell 级 `command -v`. 版本比较由 `NODE_MAJOR < 20` 判定, 不满足时打印五段报告并设置 `process.exitCode = 1`, 让事件循环自然退出. 不用 `process.exit` 有两个原因: 避免 Node 26 起 `process.exit(false)` 抛 `TypeError`, 也避免 `process.exit` 在管道背压时截断尚未排空的 stdout/stderr.

阻断后的报告固定包含五段: 缺少项, 检测结果, 要求, 修复命令, 影响. 用户选择修复, 授权降级或终止; 没有降级路径时只有修复和终止.

`validate_skill.mjs`, `init_skill.mjs` 与 `check_dependencies.mjs` 三个脚本各自保留一份版本守卫与五段报告 (只有依赖清单是共享来源), 由 `tests/skill_creator/prerequisites.test.mjs` 保证缺少项集合与 `要求` 段文案一致; 这是有意的显式重复, 便于脚本独立运行, 不是遗漏.

### 6. 测试迁移

分两段:

1. **差分阶段**: 保留 Python 版到 `tests/oracle/` (skill 目录之外, 不触发未引用扫描), 用仓库内全部 skill 和一组固定 fixture 同时跑两个实现, 比较归一化后的输出和退出码. 已知差异 (YAML 1.1 → 1.2) 单独记录并人工确认.
2. **契约阶段**: 用 `node --test` 重写测试, 覆盖 CLI 参数, 退出码, 错误/警告分级, 链接检查, 前提条件阻断流程. 现有 270 个用例中大量是解析器边界, 由库行为替代, 不再逐条搬运.

### 7. 文档与参考文件

+ `SKILL.md`: 新增 `## 前提条件`; 脚手架和校验命令改为 `node`; 增加对产出 skill 的前提声明要求, 改进流程和交付说明规则.
+ `references/spec.md`: 删除 PyYAML 回退和内置解析器的整段说明, 更新未引用扫描的忽略列表.
+ `docs/skill-creator.md`: 更新命令, 前提, 测试方式.
+ `.gitignore`: 增加 `node_modules/`.

`--verbose` 保留, 输出改为 `frontmatter 解析器: yaml <版本>`; `--strict` 语义不变.

## Risks / Trade-offs

+ [库的 CommonMark 行为与手写实现有差异] → 差分测试覆盖仓库内 skill, 差异见 "已接受的行为变化" 与 [verification.md](verification.md) 的 32 个 fixture 差异 (10 类) 及 fixture 之外的引用式定义识别差异; 契约测试只断言对外可见的错误/警告.
+ [缺失引用定义无法直接从 AST 得到] → 保留一段有界的目标扫描, 只处理 AST 未屏蔽的文本.
+ [YAML 1.1 → 1.2 是行为变化] → 在 `references/spec.md` 明确写出, 相关用例按新语义重写.
+ [`node_modules` 可能被手动复制进分发目录] → 文档提示分发时排除; `node_modules` 在 skill 根目录, 不在 `scripts/` 下, 不会被未引用扫描误报.
+ [测试重写工作量大于脚本本身] → 先差分后重写, 只保留契约级用例; 不追求与 Python 用例一一对应.
+ [依赖安装需要网络] → 安装失败按前提缺失阻断, 报告 npm 原始错误, 不静默降级.
+ [Node 版本下限] → 声明 20+, 按支持窗口在文档中建议 22+.

## Migration Plan

1. `.gitignore` 增加 `node_modules/`.
2. 实现 `scripts/validate_skill.mjs` 与 `scripts/init_skill.mjs`, 与 Python 版并存; 同时新增 `scripts/check_dependencies.mjs` 用于依赖探测, 并新增 `scripts/dependency-list.mjs` 作为三个脚本共用的依赖清单单一来源, 与 `SKILL.md` 的 `## 前提条件` 保持同步.
3. 用仓库内 skill 和 fixture 做差分, 逐项确认差异.
4. 更新 `SKILL.md`, `references/spec.md`, `docs/skill-creator.md`.
5. 用 `node` 测试替换 `tests/test_skill_creator.py`, 删除 `tests/oracle/` 下的 Python 版.
6. 删除 `scripts/*.py`, 运行 `node scripts/validate_skill.mjs skills/skill-creator` 和仓库全部 skill.

回滚: 还原提交即可恢复 Python 版; 新旧实现并存期间可随时切回.
