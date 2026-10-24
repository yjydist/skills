# 交付与验证记录

本文件是本 change 的交付快照, 归档时随 change 目录移动到 `openspec/changes/archive/`. 其中 `openspec validate add-skill-creator` 只在归档前可用; 归档后该 ID 不再是 active change, 命令会失败. 长期使用方式见 `docs/skill-creator.md`.

## 文件清单

新增:

+ `skills/skill-creator/SKILL.md`
+ `skills/skill-creator/references/spec.md`
+ `skills/skill-creator/references/writing.md`
+ `skills/skill-creator/scripts/init_skill.py`
+ `skills/skill-creator/scripts/validate_skill.py`
+ `docs/skill-creator.md`
+ `tests/test_skill_creator.py`

修改:

+ `README.md`

记录:

+ `openspec/changes/add-skill-creator/verification.md` (本文件), 以及同目录的 `proposal.md`, `design.md`, `tasks.md` 和 `specs/skill-creator/spec.md`. 这些是随本次 change 归档的规划与记录 artifacts, 不属于实现交付物; 归档后本文件中的 `openspec validate add-skill-creator` 不再可用.

## 标准依赖

本 skill 仅使用 `name`/`description` 标准字段与标准目录约定, 未使用客户端特有机制; 如后续使用宿主机制, 需标注适用工具并记录不依赖该机制的替代做法.

## Scenario 覆盖

spec 共 10 个 requirement, 22 个 scenario. 其中 5 个机械 scenario 由 `tests/test_skill_creator.py` 覆盖; 其余 17 个是 `SKILL.md`, `references/` 或 `docs/` 中的指令, 或需要人工执行的场景, 不是自动化验证.

| Requirement | Scenario 数 | 证据类型 |
| --- | --- | --- |
| 创建前的门槛判断 | 2 | `SKILL.md` 指令, 人工场景 |
| 标准符合性 | 2 | 自动化: `tests/test_skill_creator.py` |
| 描述作为触发规则 | 2 | `SKILL.md`/`references/` 指令, 人工判断语料 |
| 内容去向与上下文预算 | 3 | `SKILL.md`/`references/` 指令, 人工场景 |
| 按步骤分配自由度 | 2 | `SKILL.md` 指令, 人工场景 |
| 跨工具可移植 | 2 | `SKILL.md`/`references/` 指令, 人工场景 |
| 机械校验 | 3 | 自动化: `tests/test_skill_creator.py` |
| 交付前验证 | 2 | `docs/` 语料与人工判断, 人工场景 |
| 改进现有 skill | 2 | `SKILL.md` 指令, 人工场景 |
| 交付说明 | 2 | `SKILL.md`/`docs/` 指令, 人工场景 |

## Scenario 证据矩阵

逐条列出 spec 的 22 个 scenario. `自动化测试` 指 `tests/test_skill_creator.py` 中可重复执行的断言; `指令` 指 `SKILL.md`, `references/` 或 `docs/` 中约束执行者行为的章节; `人工` 指需要按场景实际判断或执行, 没有自动化断言.

| # | Requirement | Scenario | 证据类型 | 证据位置 |
| --- | --- | --- | --- | --- |
| 1 | 创建前的门槛判断 | 一次性任务 | 指令 + 人工 | `SKILL.md` "适用与门槛" 小节 ("一次性任务" 条); `SKILL.md` "操作边界" 小节; `docs/skill-creator.md` "调用示例" 小节 |
| 2 | 创建前的门槛判断 | 与已有 skill 重叠 | 指令 + 人工 | `SKILL.md` "适用与门槛" 小节 ("已有 skill 重叠" 条), "意图收集" 小节 |
| 3 | 标准符合性 | 名称含大写 | 自动化测试 | `InitSkillTests.test_normalize_name`, `ValidatorTests.test_uppercase_name_is_error` |
| 4 | 标准符合性 | 描述为空 | 自动化测试 | `ValidatorTests.test_description_empty_and_too_long`, `InitSkillTests.test_generated_skill_fails_until_description_and_body_are_filled` |
| 5 | 描述作为触发规则 | 同级竞争 | 指令 + 人工 | `SKILL.md` "描述与触发" 小节; `references/writing.md` "1 描述公式与同级竞争测试" (小节 "同级竞争测试"); `docs/skill-creator.md` "触发语料自检" 小节 |
| 6 | 描述作为触发规则 | 描述只写主题 | 指令 + 人工 | `references/writing.md` "1 描述公式与同级竞争测试" (含 "只有主题" 对例), "5 常见失败清单" ("描述只写领域") |
| 7 | 内容去向与上下文预算 | 长格式规范 | 指令 + 人工 | `SKILL.md` "内容去向" 小节; `references/spec.md` "渐进披露" 小节, "资源目录职责" 小节 |
| 8 | 内容去向与上下文预算 | 反复出现的脚本逻辑 | 指令 + 人工 | `SKILL.md` "内容去向" 小节, "脚手架与校验" 小节; `references/spec.md` "资源目录职责" 小节 |
| 9 | 内容去向与上下文预算 | 只解释动机的段落 | 指令 + 人工 | `SKILL.md` "内容去向" 小节; `references/writing.md` "3 正文模式", "5 常见失败清单" ("正文解释动机") |
| 10 | 按步骤分配自由度 | 可机械判定的步骤 | 指令 + 人工 | `SKILL.md` "正文与自由度" 小节, "脚手架与校验" 小节; `references/writing.md` "4 按步骤分配自由度" |
| 11 | 按步骤分配自由度 | 依赖上下文的步骤 | 指令 + 人工 | `SKILL.md` "正文与自由度" 小节; `references/writing.md` "4 按步骤分配自由度" (中/高自由度行) |
| 12 | 跨工具可移植 | 需要独立会话的验证 | 指令 + 人工 | `SKILL.md` "验证" 小节; `docs/skill-creator.md` "未验证项的处理" 小节 |
| 13 | 跨工具可移植 | 非标准字段的可移植性风险 | 指令 + 人工 | `references/spec.md` "SKILL.md 格式" (小节 "非标准字段"), "常见厂商扩展" 小节; `SKILL.md` "交付说明" 小节 |
| 14 | 机械校验 | 名称与目录不一致 | 自动化测试 | `ValidatorTests.test_name_must_match_directory`; NFKC 口径见 `ValidatorTests.test_name_and_directory_are_compared_after_nfkc` |
| 15 | 机械校验 | 非标准字段 | 自动化测试 | `ValidatorTests.test_non_standard_field_warns_and_strict_fails` |
| 16 | 机械校验 | 引用不存在 | 自动化测试 | `ValidatorTests.test_local_links_must_exist_and_report_line` |
| 17 | 交付前验证 | 正例无法定位 | 指令 + 人工 | `SKILL.md` "验证" 小节; `references/writing.md` "2 触发语料的构成"; `docs/skill-creator.md` "触发语料自检" 小节 |
| 18 | 交付前验证 | 无独立会话 | 指令 + 人工 | `SKILL.md` "验证" 小节; `docs/skill-creator.md` "未验证项的处理" 小节 |
| 19 | 改进现有 skill | 只修好一个用例 | 指令 + 人工 | `SKILL.md` "改进现有 skill" 小节; `references/writing.md` "5 常见失败清单" ("只修好一个用例") |
| 20 | 改进现有 skill | 用户要求改名 | 指令 + 人工 | `SKILL.md` "改进现有 skill" 小节; `references/spec.md` "name" 小节 |
| 21 | 交付说明 | 仓库要求使用文档 | 指令 + 人工 | `SKILL.md` "交付说明" 小节 |
| 22 | 交付说明 | 脚本未运行 | 指令 + 人工 | `SKILL.md` "验证" 小节, "交付说明" 小节; `references/spec.md` "校验脚本覆盖的检查" 小节; `docs/skill-creator.md` "未验证项的处理" 小节 |

## 测试策略

+ 5 个机械 scenario (第 3, 4, 14, 15, 16 条) 的成功条件可以机械判定, 由 `tests/test_skill_creator.py` 覆盖: 断言退出码, 错误或警告类别和报告行号, 不依赖人工阅读.
+ 17 个行为 scenario 判断的是执行者是否遵守门槛, 描述质量, 内容归位, 自由度分配, 可移植性取舍, 验证流程, 改进流程和交付说明, 没有可判定的输出, 因此只靠 `SKILL.md`, `references/` 和 `docs/` 的指令约束, 或按上表位置人工核对. 给这些场景加单元测试只会测到测试替身, 不能证明行为, 所以不把 "测试数量" 当作 spec 覆盖度.
+ `FrontmatterParserTests` 以及 `ValidatorTests` 中链接, 代码块, HTML 块, 代码跨度, 引用定义等边界测试, 是为自包含实现 (D4: frontmatter 解析优先 PyYAML, 回退到内置受限解析器; 且不引入 Markdown 库) 提供的回归保护, 防止解析和扫描出现退化; 它们不代表 spec 要求把全部检查自动化. spec 对校验的要求是可重复执行并区分错误与警告, 没有规定实现语言或是否依赖第三方库.
+ 因此新增行为要求时, 先更新上表对应的指令章节和人工核对清单; 只有当成功条件能机械判定时, 才补自动化测试并回填证据矩阵.

## 已验证项

+ `tests/test_skill_creator.py` 全部通过. 数量不在此写明, 避免后续测试增删后失效.
+ 仓库全量 pytest 中, 只有 `tests/test_weekly_report.py` 的两个真实渲染用例被跳过, 原因是未设置 `RUN_TYPST_TESTS=1`; 该跳过与本 change 无关.
+ `python3 skills/skill-creator/scripts/validate_skill.py skills/skill-creator --strict` 退出状态为 0.
+ `openspec validate add-skill-creator --strict` 通过 (归档前有效).
+ `docs/skill-creator.md` 中的 `init_skill.py`, `validate_skill.py`, pytest 和 unittest 命令均按原样执行成功.
+ PyYAML 已安装与 `python3 -S` (仅标准库, 走内置解析器) 两条解析路径均通过, 对同一样例给出相同结论和退出码.
+ `docs/skill-creator.md` 的本地链接全部可解析; 其中带 fragment 的相对链接, 其锚点由 `tests/test_skill_creator.py` 的 `DocumentationContractTests` 校验, 覆盖 `#skills-列表`, `#目录结构` 和 `#校验脚本覆盖的检查` 三个现有锚点.

## 未验证项

+ 真实客户端会话中的自动触发结果: 未在客户端里用触发语料试跑.
+ 无 skill 或旧版本基线对照: 未与关闭 skill 或旧描述的结果比较.
+ 其他客户端特定行为: 不同客户端的调用语法, 加载时机和上下文窗口差异.

## 独立语料复核记录

日期: 2026-10-23.

复核分两轮进行, 方法相同: 复核者只收到 README 的 skills 列表列出的 9 个用户 skill 的 `description` 和待判断的请求, 未读取 `docs/skill-creator.md` 中的语料表和判断依据, 也不知道人工判断的结果. 第一轮覆盖第 1-10 条, 第二轮补充第 11, 12 条. 两轮合计覆盖第 1-12 条. `.agents/skills/` 下的 OpenSpec 工具 skill 是外部工具自带内容, 不在竞争测试语料范围内, 不作为本仓库用户 skill 的同级竞争者参与归属判断.

原始逐条结果:

| 请求 | 复核者归属 |
| --- | --- |
| 1 | skill-creator |
| 2 | skill-creator |
| 3 | skill-creator |
| 4 | skill-creator |
| 5 | skill-creator |
| 6 | 无 |
| 7 | convenient-commit |
| 8 | paper-first-pass |
| 9 | weekly-report |
| 10 | 无 |
| 11 | skill-creator |
| 12 | 无 |

第 1-12 条是独立上下文下的文本评审, 不是客户端会话试跑, 也不等于自动客户端验证. 复核结果与 `docs/skill-creator.md` 的人工判断逐条一致 (12/12), 12 条中没有任何请求同时匹配两个 skill. 第 11 条唯一疑似冲突对象是 weekly-report: 该请求要求新建一个整理实验记录的 skill, 不要求生成或渲染周报, 因此不匹配 weekly-report, 双匹配不成立.

## 最终状态

+ 本文件在最终修复后更新. 上文 `已验证项` 中的机械检查 (pytest, `validate_skill.py --strict`, `openspec validate add-skill-creator --strict`, `docs/skill-creator.md` 中的示例命令, PyYAML 与内置解析器两条解析路径) 均已针对当前工作区重跑, 结论与记录一致.
+ 触发语料涉及的 9 个用户 skill 的 `description` 在独立复核后未修改, 上文 `独立语料复核记录` 对第 1-12 条的结论仍然适用: 12/12 与人工判断一致, 无双匹配. 若后续修改任一 `description` 或语料条目, 需重新运行竞争测试并同步更新本文件.
+ 真实客户端会话中的自动触发结果, 无 skill 或旧版本基线对照, 以及其他客户端的特定行为, 仍是未验证项, 见上文[未验证项](#未验证项).

## 验证 Loop 记录

初次交付后, 按"每轮 3 个独立验证子代理, 去重并核实后每个警告/建议由独立子代理修复"的方式执行了 16 轮 Loop 验证. 第 16 轮的 3 个验证子代理均未发现警告或建议, Loop 结束. 主要修复包括: C1 控制字符检查, 父目录名 NFKC 比较, name 归一化顺序, init 生成的 name 引号, allowed-tools 空格分隔, 时间戳解析与 PyYAML 对齐, 引用定义的相邻/列表项/未缩进/标题/转义/块级标记处理, 以及 Windows 平台测试限制.

每轮修复后运行 `tests/test_skill_creator.py`, `validate_skill.py --strict` 和 `openspec validate add-skill-creator --strict`. 当前 `tests/test_skill_creator.py` 共 270 个测试通过; 系统 Python 未安装 PyYAML 时, 7 个 PyYAML 对照用例按文档跳过. 两个校验命令均通过.

已明确记录并测试的有意限制: 多行标题, 块级标记续行, 紧跟普通段落的块引用定义, 嵌套列表缩进定义, 以及受限 Markdown 子集. 这些是设计 D3 的边界, 不作为缺陷; 若后续需要完整 CommonMark 语义, 应引入成熟解析库并重新评估误报率.
