# Tasks

## 1. 环境与依赖

+ [x] 1.1 在 `.gitignore` 增加 `node_modules/`; 验证: `git check-ignore -v skills/skill-creator/node_modules/x` 能匹配到该规则.
+ [x] 1.2 在 `skills/skill-creator` 执行 `npm install --no-save --no-package-lock --prefix . yaml mdast-util-from-markdown decode-named-character-reference`; 验证: 目录下只多出 `node_modules`, 没有 `package.json` 或锁文件.
+ [x] 1.3 把现有 Python 脚本复制到 `tests/oracle/` 作为差分基准, 暂不删除; 验证: `python3 tests/oracle/validate_skill.py skills/skill-creator` 仍以 0 退出; 注: `tests/oracle/` 已由 6.3 删除, 上述命令无法原样复现, 复现方式见 `verification.md` (例如用 `git show ea69a2f:skills/skill-creator/scripts/validate_skill.py` 取回基准脚本).

## 2. 校验脚本: frontmatter 与字段

+ [x] 2.1 建立 `tests/skill_creator/` 下的 Node 测试骨架和运行 CLI 的辅助函数; 验证: `node --test tests/skill_creator/` 能执行并报告通过.
+ [x] 2.2 实现 `scripts/validate_skill.mjs` 的 frontmatter 拆分与 YAML 1.2 解析; 验证: 合法与非法 frontmatter 用例通过, 解析错误带行号.
+ [x] 2.3 实现 name, description, 可选字段和非标准字段警告; 验证: 各字段的边界与类型用例通过.
+ [x] 2.4 实现正文空检查与 500 行警告; 验证: 空正文报错, 超长正文报警告.
+ [x] 2.5 实现 CLI, 保留 `--strict` 和 `--verbose`, 除 design 已接受的 CLI 用法/参数错误文案变化外输出文案与退出码不变; 验证: 端到端用例断言 stdout 和退出码.

## 3. 校验脚本: 链接与未引用文件

+ [x] 3.1 用 `mdast-util-from-markdown` 建立 AST 与屏蔽文本, 实现 Markdown 链接, 图片和引用定义的检查与行号; 验证: 代码块, 行内代码和 HTML 内的链接不被检查, 段落内链接行号准确.
+ [x] 3.2 实现行内 HTML 属性提取和缺失引用定义扫描; 验证: `&amp;` 与百分号解码, 反斜杠转义标签, 无定义引用用例通过.
+ [x] 3.3 实现本地链接的可移植性警告与未引用文件扫描, 忽略列表保留 `__pycache__` 和 `.pyc`, 并新增 `node_modules` 与依赖目录; 验证: 绝对路径, Windows 路径, 越界, 大小写不一致, 仅相对文件目录五类用例通过.

## 4. 脚手架脚本

+ [x] 4.1 实现 `scripts/init_skill.mjs`, 保持 NFKC 归一化, 非法名称, 拒绝覆盖和三个目录参数的行为; 验证: 用例通过, 生成的骨架因 `description` 为空而校验失败; 占位节使正文非空; 填写 `description` 后仍需替换占位内容并删除 TODO.
+ [x] 4.2 在 `SKILL.md` 中把脚手架和校验命令改为 `node`; 校验命令见 `SKILL.md` 的 `## 脚手架与校验` (含 skill-creator 目录与仓库根目录两种写法); 验证: 两条命令按文档原样执行成功.

## 5. 运行前提

+ [x] 5.1 在 `skills/skill-creator/SKILL.md` 增加 `## 前提条件`, 含 node 版本检查, 依赖检查和阻断流程; 验证: 逐条执行检查命令通过; 临时改名 `node_modules` 后能阻断并输出五段式报告.
+ [x] 5.2 在创建, 改进现有 skill, 交付说明三处补规则, 要求产出 skill 带 `## 前提条件` 且降级留痕; 验证: 用一条新建请求走查流程, 产出的 `SKILL.md` 包含该节.
+ [x] 5.3 更新 `references/spec.md` 和 `docs/skill-creator.md`, 删除 PyYAML 回退说明, 同步命令与测试方式; 验证: 文档中的命令可执行, 相对链接和锚点存在.

## 6. 差分与清理

+ [x] 6.1 对仓库内全部 skill 和固定 fixture 分别运行 Python 基准与 JS 实现, 比较归一化后的输出和退出码; 验证: 9 个 skill 全部一致, 32 个 fixture 中 20 个一致, 12 个差异, 其余差异仅为已记录的 YAML 1.2 语义 (含重复键, 1.1 纯量与 `<<` 合并键), 第三方 YAML 库错误文案, 非法 UTF-8 解码文案, 有意扩展的依赖目录忽略列表, 以及链接检查范围的五项差异 (列表项内原始 HTML 块, 反斜杠转义的 HTML 标签, 同一行同一目标只报告一次, 片段/查询/纯锚点中的控制字符, 跨行行内 HTML 标签的属性目标; JS 均按当前 spec 处理); 验证记录见 [verification.md](verification.md), fixture 清单见 [verification-fixtures.md](verification-fixtures.md).
+ [x] 6.2 把文档契约测试迁移到 Node, 覆盖章节顺序, 链接目标和锚点; 验证: `node --test tests/skill_creator/` 全部通过.
+ [x] 6.3 删除 `scripts/*.py`, `tests/oracle/` 和 `tests/test_skill_creator.py`; 验证: `node --test tests/skill_creator/` 通过, `python3 -m unittest discover -s tests -p test_weekly_report.py` 不受影响.
+ [x] 6.4 用新脚本校验仓库内全部 skill; 验证: `node skills/skill-creator/scripts/validate_skill.mjs <skill>` 对每个 skill 退出码为 0, 无错误.

## Workflow follow-up

+ 评审通过后归档该 change.
+ 归档后确认 `openspec/specs/skill-creator/spec.md` 已包含新增和修改的要求.
