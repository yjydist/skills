# Proposal

## Why

仓库已有 8 个 skill, 但缺少创建和改进 skill 本身的方法, 新增 skill 只能靠参考现有目录或外部实现. 外部三份实现 (Anthropic, Vercel, OpenAI) 的共同内核是格式, 渐进披露和触发器写法, 但最厚的部分分别是评测基建, 打包格式和宿主工具元数据. 直接照搬会产出只对某一家工具有效的 skill, 与"面向所有支持标准 skill 的 agent 工具"的目标冲突.

## What Changes

+ 新增 `skills/skill-creator/`, 正文覆盖判断门槛, 意图收集, 内容去向, 描述与正文写法, 脚手架与校验, 验证, 迭代与交付说明.
+ 新增 `references/spec.md`: Agent Skills 标准约束, frontmatter 字段表, 命名规则, 资源目录职责, 标准字段与厂商扩展的可移植性对照.
+ 新增 `references/writing.md`: 描述公式与同级竞争测试, 触发语料构成, 正文模式, 按步骤分配自由度, 常见失败清单.
+ 新增 `scripts/init_skill.py`: 校验名称, 创建目录与合法 frontmatter 骨架, 按需创建 `scripts/`, `references/`, `assets/`.
+ 新增 `scripts/validate_skill.py`: 检查标准违规, 本地链接与冗余文件; 错误与警告分级, `--strict` 可选.
+ 新增 `docs/skill-creator.md` 与 README 的 skills 列表条目.
+ 新增 `tests/test_skill_creator.py`, 覆盖名称规则, frontmatter 解析 (含块标量), 链接检查与错误/警告分级.

不修改现有 skill 的入口或行为, 无破坏性变更.

## Capabilities

### New Capabilities

+ `skill-creator`: 依据 Agent Skills 标准创建, 改进与校验 skill 目录, 包括意图提炼, 描述与触发设计, 内容去向判定, 机械校验和可降级的验证方法.

### Modified Capabilities

无.

## Impact

+ 新增 `skills/skill-creator/SKILL.md`, `references/spec.md`, `references/writing.md`, `scripts/init_skill.py`, `scripts/validate_skill.py`.
+ 新增 `docs/skill-creator.md`, 修改 `README.md` 的 skills 列表.
+ 新增 `tests/test_skill_creator.py`.
+ 脚本硬依赖仅 Python 标准库; 存在 PyYAML 时优先使用, 未安装时回退到内置的受限解析器, 不要求安装. 脚本可选用; 缺失 Python 时由执行者手工创建目录和最小 frontmatter, 再按正文的人工检查项核对.
+ 不引入第三方依赖, CI 或统一运行环境.
