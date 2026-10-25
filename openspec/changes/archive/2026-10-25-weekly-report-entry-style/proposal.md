# Proposal

## Why

`weekly-report` 的条目由执行模型从对话上下文整理, 但 `SKILL.md` 只规定"原样保留, 不改写", 没有规定条目该写成什么样. 结果是用户口语里的 `我这周跟师兄聊了下大论文的选题` 被原样落进表格, 与"公事公办的汇报口径"不符; 模型一旦自行改写, 又违反该契约, 于是同一输入在不同轮次得到不同口吻.

## What Changes

+ 移除需求 `内容原样保留`, 拆成两条新需求: `事实原样保留` (事实层) 与 `条目表述` (表述层).
+ `事实原样保留`: 人名, 项目名, 文档名, 数字, 条目数量与顺序 MUST 原样保留, 不补写原文没有的事实; 条目字符 MUST 仍作为文本渲染.
+ `条目表述`: 条目 SHALL 写成事项式陈述, 一条一个动作, 动词开头, 省略主语, 不写周期词, 不描述过程与情绪, 不加自我修饰; 风格与事实或可读性冲突时, 以事实准确和可读性优先, 不为改而改.
+ `实验室其他服务性工作`, `运动情况`, `心得体会`, `反思教训` 四项采用同一口吻, 不要求动词开头.
+ 模板数据块示例与 `SKILL.md` 的 JSON 示例统一为动宾风格, 现状一个名词化带句号, 一个动宾无句号.
+ 表述转写 SHALL 由执行模型完成, `scripts/render.py` 继续只做转义与渲染, 不实现表述改写.
+ 输入 JSON 字段与 CLI 参数不变, 无接口破坏性变更.

## Capabilities

### New Capabilities

无. 表述规范属于 `weekly-report` 已有能力的行为, 不另立能力.

### Modified Capabilities

- `weekly-report`: 移除 `内容原样保留`, 新增 `事实原样保留` 与 `条目表述`, 把"不改写"的单层契约改为事实层与表述层两层.

## Impact

+ `skills/weekly-report/SKILL.md`: frontmatter 的 `description`, "收集内容" 与 "操作边界" 的契约措辞, 新增条目表述小节, JSON 示例.
+ `skills/weekly-report/references/weekly-template.typ` 与 `monthly-template.typ`: 数据块中的示例条目.
+ `docs/weekly-report.md`: 调用示例与条目说明.
+ `skills/weekly-report/scripts/render.py`: 不改动.
+ 依赖与环境要求不变, 无需新增运行时或字体.
