# Proposal

## Why

skill-creator 的校验脚本有约 630 行手写 YAML 与约 1290 行手写 CommonMark 解析逻辑, 长期维护成本高; 同时所有 skill 都没有统一的运行前提声明, 缺少解释器或依赖时只能在执行中途失败. 现在允许脚本引入 npm 依赖, 可以把实现迁到 Node.js, 用现成库替换手写解析器, 并建立一套"前提条件 → 阻断 → 用户授权降级"的统一规则.

## What Changes

+ **BREAKING**: `scripts/init_skill.py` 与 `scripts/validate_skill.py` 改为 `.mjs`, 运行方式从 `python3 ...` 变为 `node ...`; 脚本的重写会用 npm 包承载 YAML 与 Markdown 解析, 删除手写解析器.
+ 依赖清单写入 `SKILL.md` 的 `## 前提条件`, 运行时用 `npm install --no-save --no-package-lock --prefix` 按需创建临时 `node_modules`; 不提交 `package.json` 或锁文件.
+ `SKILL.md` 新增 `## 前提条件` 一节, 列出整个 skill 需要的运行时, 最低版本, 第三方包, 外部程序与认证; 版本低于要求按缺失处理; 路径相对 skill 目录解析.
+ 前提检查失败时阻断, 报告缺少项, 检测结果, 要求, 修复命令和影响, 由用户选择修复后继续, 授权降级或终止; 不自动安装系统程序.
+ skill-creator 的创建流程要求新 skill 带 `## 前提条件`; 改进现有 skill 时补上该节; 交付说明记录前提检查结果和降级项.
+ 测试从 Python 迁移到 Node 测试, `docs/skill-creator.md` 的命令与前提说明同步更新.

## Capabilities

### New Capabilities

无.

### Modified Capabilities

+ `skill-creator`: 新增产出 skill 的运行前提声明, 前提检查与阻断, 运行环境与依赖自建三项要求; 修改机械校验与交付说明两项要求, 明确脚本由 Node.js 运行并记录降级.

## Impact

+ `skills/skill-creator/scripts/`: 两个原脚本 `init_skill.py` 与 `validate_skill.py` 重写为 `init_skill.mjs` 与 `validate_skill.mjs`, 并新增依赖检查脚本 `check_dependencies.mjs` 与依赖清单 `dependency-list.mjs`; 后者是三个脚本共用的依赖清单单一来源; 删除手写 YAML 与 CommonMark 解析器.
+ `skills/skill-creator/SKILL.md`: 新增 `## 前提条件`, 补充创建, 改进和交付规则.
+ `skills/skill-creator/references/spec.md`: 删除 PyYAML 回退与手写解析器的描述, 更新校验项说明.
+ `docs/skill-creator.md`: 更新调用命令, 前提说明和测试方式.
+ `tests/test_skill_creator.py`: 迁移为 Node 测试; 迁移期间用 Python 版作为差分基准.
+ `.gitignore`: 增加 `node_modules/`.
+ 运行环境: Node.js 20+ (按支持窗口建议 22+).
+ 不涉及 `AGENTS.md`, `weekly-report` 及其他 skill.
