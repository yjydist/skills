# Design

## Context

动机见 [proposal.md](proposal.md). 本文件只记录实现方式上的选择.

约束来自三处:

+ `openspec/specs/skill-creator/spec.md` 的 `运行前提声明` 要求完整列出运行时, 最低版本, 第三方依赖, 外部程序和认证, 且不能只列当前请求用到的项. 该要求规定未改动的既有 skill 不回溯强制, 但下次改进时必须补上.
+ `skills/skill-creator/references/spec.md` 的 `运行前提` 规定检查命令要按目标平台书写, 且检查顺序为 运行时 -> 版本比较 -> 依赖目录 -> 包可导入 -> 外部程序与认证.
+ `skills/skill-creator/references/writing.md` 的失败清单禁止参考文件之间互相链接, 所有引用必须由 `SKILL.md` 直接指向一层.

现状: 9 个 skill 中仅 `skill-creator` 有 `## 前提条件`. 8 个缺该节, 其中 6 个实际没有可机械检查的外部依赖.

## Goals / Non-Goals

**Goals:**

+ 让每个 skill 的 `SKILL.md` 在执行前能独立回答 "本 skill 需要什么, 怎么检查".
+ 把已有文档中的依赖信息归位到执行入口, 保持文档与入口一致.
+ 让 `validate_skill.mjs` 对全部 9 个 skill 输出 0 错误 0 警告.

**Non-Goals:**

+ 不为其余 8 个 skill 建立触发语料. 该决策会改变仓库文件构成, 属于独立议题.
+ 不改动 `validate_skill.mjs`, 不让它检查 `## 前提条件`. 该检查需要解析自然语言条目, 无法机械判定.
+ 不改写任何 skill 的执行逻辑, 唯一例外是 `to-github-issue` 的检查时机前移.
+ 不为 `to-github-issue` 新建 spec.

## Decisions

### D1: 无依赖的 skill 写 "无", 不编造检查命令

`spec.md` 要求每个条目给出可执行的检查命令, 但 `mentor-profile`, `swiss-grid-design`, `paper-first-pass`, `paper-second-pass`, `paper-third-pass` 的真实前提是 "执行工具能读取图形或论文", 这是工具能力而非可检查的程序依赖.

替选方案: 写 `command -v <某工具>` 之类形式化的检查命令. 否决理由: 这些命令不检查任何真实前提, 通过与否与 skill 能否执行无关, 属于 spec.md 明确反对的 `true` 之外的伪检查. 采用方案: 三类条目全部写 "无", 检查命令写 `true`, 与 `skill-creator` 现有写法一致.

### D2: `convenient-commit` 不声明 Git 最低版本

它使用的 `git diff --cached --check`, `git add -p`, `git show` 都是长期稳定接口, 没有可依据的版本门槛.

替选方案: 写一个保守的版本号 (如 2.0). 否决理由: 无证据支撑, 会让检查在正常环境误报, 且 spec.md 要求版本低于声明时按缺失处理, 错误声明会制造假阻断. 采用方案: 声明外部程序为 Git, 检查命令 `git --version`, 不设最低版本.

### D3: `to-github-issue` 的门禁区分模式

该 skill 有明确承诺 "仅整理草稿不需要仓库或 gh 认证" (`SKILL.md` 的 `description` 与使用文档均如此表述). 若把 gh 与认证写成无条件前提, 会破坏已有的草稿模式.

采用方案: `## 前提条件` 中列出 GitHub CLI 与认证, 并逐条注明适用模式; 认证条目写明 "仅创建模式, 且必须是目标主机的认证". 检查时机上, 草稿模式跳过该节, 创建模式在整理内容之前先完成检查.

替选方案: 保持现状, 让流程第 2 步自然失败. 否决理由: 用户会先收到一份完整草稿, 再被告知无法创建, 违背 `前提检查与阻断` 要求的 "产出文件前检查".

### D4: `weekly-report` 的字体不列为阻断项

字体缺失时脚本按现有设计回退到 Typst 默认字体, 继续渲染并通过 `font_note` 提示.

采用方案: 在 `## 前提条件` 中写明字体要求, 并明确 "缺失不阻断, 回退后提示". 这样既满足 "列出所有执行路径需要的外部资源", 又不改变现有的降级行为.

### D5: `paper-third-pass` 删除参考文件互引

`references/report-format.md:3` 链向 `selective-report-format.md`. `SKILL.md` 第 35 行和第 66 行已经分别直接引用两个模板, 因此删掉这条互引不损失可达性.

替选方案: 把互引改成相对 skill 根目录的写法 (`references/selective-report-format.md`), 消除其中一条警告. 否决理由: 只解决路径基准问题, 仍违反 "参考文件之间不互相链接" 这条更强的规则. 采用方案: 删句.

### D6: 文档标题统一为 `使用前提`

`docs/swiss-grid-design.md` 现用 `## 使用方式`, 其余 8 份为 `## 使用前提`.

采用方案: 改为 `使用前提`, 内容不改. 该标题下的内容本就是环境与输入前提, 与其余 8 份同构, 一致后读者不必按文档记忆不同的小节名. 已确认仓库内没有指向该锚点的链接.

### D7: `AGENTS.md` 增加检查项而非新增脚本

替选方案: 扩展 `validate_skill.mjs` 让它在仓库根目录批量扫描. 否决理由: 该脚本面向单个 skill 目录, 且 `## 前提条件` 是否存在可检查, 但 "条目是否完整正确" 无法机械判定; 部分机械化会给人已全面检查的错觉. 采用方案: 在 `AGENTS.md` 的 `## 变更检查` 增加一条人工检查项, 与现有条目同粒度.

## Risks / Trade-offs

+ [前提条件的内容可能写错] -> 逐项对照各 skill 实际执行的命令和 `docs/` 中的既有说明; 交付说明中把该节的正确性标注为人工核对, 不声称已机械验证.
+ [`to-github-issue` 门禁前移后, 草稿模式可能被误阻断] -> 在前提条件和流程中双向写明模式区分; 交付时用一个"仅整理草稿且无 gh"的场景人工核对路径.
+ [`AGENTS.md` 增加条目后, 其他 skill 的下次改动会多一道检查] -> 这是预期效果, 与既有 "每个 skill 都有对应文档和 README 条目" 同性质.
+ [改动分散在 10 个提交, 中途 review 成本] -> 按一个 skill 一条提交组织, 每条自包含且可独立验证; `AGENTS.md` 与 `docs/` 各一条.

## Open Questions

无.
