# Spec Delta

## Purpose

依据 Agent Skills 标准创建, 改进和校验 skill 目录, 让产出的 skill 能被任意支持该标准的 agent 工具加载, 并在激活后只消耗必要的上下文.

## ADDED Requirements

### Requirement: 创建前的门槛判断

当请求只是一次性任务, 模型常识, 已有 skill 覆盖或者只是长期保存一段资料或偏好时, skill-creator MUST 说明不适合新建 skill, 并给出改旧或改用其他形式的建议, MUST NOT 在未说明代价的情况下创建 skill 目录. 用户明确坚持创建并接受代价时, 说明代价后可以创建, 并 MUST 在交付说明中记录该决定. 会重复出现, 含非显然步骤或域知识, 且触发语境可辨识的请求默认进入创建流程.

#### Scenario: 一次性任务

- **WHEN** 用户要求为一次性的数据整理新建 skill
- **THEN** 说明该请求不具备重复性, 默认不创建目录, 并建议直接完成任务; 用户明确坚持并接受代价时, 说明后创建, 并在交付说明中记录该决定

#### Scenario: 与已有 skill 重叠

- **WHEN** 请求的主要职责已被现有 skill 覆盖
- **THEN** 指出对应 skill, 建议在原 skill 上修改而不是新增

### Requirement: 标准符合性

产出的 skill MUST 是包含 SKILL.md 的目录. frontmatter MUST 包含 name 和 description; name MUST 在 NFKC 归一化后为 1-64 字符, MUST 只含 Unicode 小写字母和数字以及连字符, MUST NOT 含大写字母, MUST NOT 以连字符开头或结尾, MUST NOT 含连续连字符, 且 MUST 与父目录名在 NFKC 归一化后相同; name 校验 MUST 按官方 `skills-ref` 先去除首尾空白并做 NFKC 归一化, 再执行字符集, 长度与目录一致性检查; description MUST 非空且不超过 1024 字符. 标准字段为 license, compatibility, metadata 和 allowed-tools, 可选字段 MUST 限于这四项, compatibility MUST 为 1-500 字符. 写入标准外字段属于可移植性风险: 默认给警告, 严格模式判失败, 交付说明 MUST 记录该风险和对应客户端.

#### Scenario: 名称含大写

- **WHEN** 用户给出的名称含大写字母或空格
- **THEN** 按 NFKC 归一化为 Unicode 小写字母, 数字和连字符形式 (其他字符转为连字符, 合并连续连字符), 并让目录名与 name 一致

#### Scenario: 描述为空

- **WHEN** 骨架中的 description 尚未填写
- **THEN** 校验失败, 不交付该 skill

### Requirement: 描述作为触发规则

description MUST 同时说明做什么和何时使用, 使用与用户一致的语言, 并包含请求中会出现的具体对象, 动作或格式词. 描述 MUST 能与同级 skill 区分: 仅凭同级 skill 的描述集合, 目标请求只应定位到本 skill. 何时使用的信息 MUST 写入 description, MUST NOT 只出现在正文.

#### Scenario: 同级竞争

- **WHEN** 另一个 skill 的描述同样能匹配目标请求
- **THEN** 调整描述或职责边界, 直到只有一个 skill 匹配

#### Scenario: 描述只写主题

- **WHEN** description 只说明领域, 不含触发语境
- **THEN** 补充用户可能使用的请求措辞和具体对象

### Requirement: 内容去向与上下文预算

每段内容 MUST 按用途归位: 每次激活都要用的决策规则留在 SKILL.md 正文; 确定且可重复执行的操作放进 scripts/; 只在部分分支需要的细节放进 references/, 由正文直接引用并说明何时读取, 引用 MUST NOT 超过一层; 只进入产物而不进入上下文的内容放进 assets/. 背景, 动机和历史 MUST NOT 写入正文. 正文 MUST 保持精简, 每条规则都要能改变执行行为. 脚本以 Markdown 链接形式识别的参考文件互相引用默认给警告, 严格模式判失败; 仅以纯文本提及的参考文件互引无法判定, MUST 人工核对.

#### Scenario: 长格式规范

- **WHEN** 输出格式说明超过正文可承受的篇幅
- **THEN** 移入 references/, 并在正文说明何时读取

#### Scenario: 反复出现的脚本逻辑

- **WHEN** 多次执行都需要相同的脚本逻辑
- **THEN** 收入 scripts/, 由正文说明调用方式

#### Scenario: 只解释动机的段落

- **WHEN** 某段文字只解释来源或动机, 不改变执行行为
- **THEN** 删除或移出正文

### Requirement: 按步骤分配自由度

指令 MUST 按步骤给出恰当自由度: 结果脆弱, 顺序固定或容易出错的步骤 MUST 给出确切命令, 参数或判定条件; 存在多种有效做法且依赖上下文的步骤 SHOULD 给出目标, 约束和理由, 由执行者判断. 整个 skill MUST NOT 只使用一种自由度.

#### Scenario: 可机械判定的步骤

- **WHEN** 某步骤的成功条件可以机械判定
- **THEN** 给出可执行的命令和失败后的处理方式

#### Scenario: 依赖上下文的步骤

- **WHEN** 某步骤的合理做法随输入或环境变化
- **THEN** 说明取舍标准和边界, 不枚举固定的唯一做法

### Requirement: 跨工具可移植

skill 的指令 MUST 只依赖 Agent Skills 标准定义的结构和字段, MUST NOT 依赖某一 agent 工具专有的工具名, 元数据文件或调用方式. 确实需要宿主机制时 MUST 单独标注适用工具, 并给出不依赖该机制时的替代做法. 正文 MUST NOT 假设存在子 agent, 浏览器或特定命令.

#### Scenario: 需要独立会话的验证

- **WHEN** 当前环境无法启动独立会话
- **THEN** 降级为人工对照, 并在交付说明中标注降级

#### Scenario: 非标准字段的可移植性风险

- **WHEN** 用户要求在 frontmatter 中加入标准外的字段
- **THEN** 说明只有对应客户端识别该字段; 部分客户端会忽略, 部分上传或打包路径会拒绝并报错

### Requirement: 机械校验

skill-creator MUST 提供可重复执行的校验, 覆盖 frontmatter 可解析, name 与目录一致, 名称与描述约束, 可选字段, 正文非空, 本地链接目标存在且不含控制字符, 引用式链接定义存在. 校验 MUST 区分错误与警告: 标准违规为错误并以非零状态退出; 内容警告覆盖非标准字段, 未被 `SKILL.md` 直接引用或正文提到的 `scripts/` 与 `references/` 文件, 参考互引和正文过长; 可移植性警告覆盖目标存在的绝对路径, Windows 盘符或 UNC 路径, 越出 skill 目录, 路径大小写与磁盘不一致, 仅能按所在目录解析的链接. 未引用扫描 MUST NOT 检查顶层文件, `assets/`, 隐藏文件, `__pycache__` 和 `.pyc`; `license` 指向目录内现有文件时 MUST 视为已引用. 警告默认只报告, 严格模式升级为错误. 无法运行校验时 MUST 按等价清单人工检查并说明.

#### Scenario: 名称与目录不一致

- **WHEN** SKILL.md 的 name 与父目录名不同
- **THEN** 报错误并以非零状态退出

#### Scenario: 非标准字段

- **WHEN** frontmatter 含标准外的字段
- **THEN** 报警告并列出字段名, 默认不影响退出状态, 严格模式下失败

#### Scenario: 引用不存在

- **WHEN** 正文或参考文件中的本地链接指向不存在的文件
- **THEN** 报错误并指出文件与行号

### Requirement: 交付前验证

交付前 MUST 完成机械校验, 触发语料判断和一次全新上下文试跑. 触发语料 MUST 同时包含不同措辞的正例和负例; 负例 MUST 覆盖两类请求: 近似但应交给其他 skill 或工具的请求, 以及只需模型常识或一次推理, 或属于一次性任务的请求. 太简单以致不需要 skill 的请求 MUST NOT 作为正例, 但可作为负例, 用来排除过宽的 description. 环境能启动独立会话时 SHOULD 对照无 skill 或旧版本的结果; 不能时 MUST 用人工对照替代. 验证结果 MUST 区分已验证项与未验证项.

#### Scenario: 正例无法定位

- **WHEN** 正例请求无法由 description 定位到本 skill
- **THEN** 修改描述或职责边界后重跑同一语料

#### Scenario: 无独立会话

- **WHEN** 环境不能启动新会话
- **THEN** 人工按语料判断, 并记录为未自动验证

### Requirement: 改进现有 skill

改进现有 skill 时 MUST 先读取现有入口和引用, 保持 name 与目录不变, MUST 优先删除不改变行为的指令, 再从使用反馈中泛化修改. 修改后 MUST 用与之前相同的语料和任务重跑, MUST NOT 只针对单个示例调整.

#### Scenario: 只修好一个用例

- **WHEN** 修改只解决一个测试请求
- **THEN** 用其余语料重跑, 确认没有退化

#### Scenario: 用户要求改名

- **WHEN** 用户要求重命名现有 skill
- **THEN** 说明改名会改变触发标识, 需同时调整目录名与 name

### Requirement: 交付说明

交付时 MUST 说明创建或修改的文件, 机械校验与验证结果, 以及未验证项. 所在仓库对 skill 目录有额外规范时 MUST 按该规范补充, 未执行时 MUST 说明.

#### Scenario: 仓库要求使用文档

- **WHEN** 仓库规范要求每个 skill 提供使用文档和索引条目
- **THEN** 一并补齐, 并在交付说明中列出

#### Scenario: 脚本未运行

- **WHEN** 环境缺少运行校验脚本所需的条件
- **THEN** 说明原因, 并列出已人工核对的检查项
