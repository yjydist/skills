# weekly-report 使用文档

`weekly-report` 将用户提供的学期, 周次和本周进展条目填入 Typst 模板, 渲染为一张 PNG 周报图片和对应的 Typst 源文件. 版式固定为标题, 分割线和一个"本周进展"列表, 内容全部来自用户输入, 不代为归纳或编造.

## 使用前提

+ 将 [skill 目录](../skills/weekly-report/SKILL.md) 连同 [Typst 模板](../skills/weekly-report/template.typ) 一起提供给支持 skill 的工具, 保持两者的相对路径.
+ 执行工具能够运行 typst 0.13 或更高版本, 且系统已安装 Alimama FangYuanTi VF 字体.
+ 在请求中直接给出学期, 周次和进展条目; skill 不会替用户归纳内容.

下方示例使用 `$weekly-report` 表示调用该 skill. 如果所用工具不支持这种调用形式, 可以直接指定 `skills/weekly-report/SKILL.md` 的实际路径, 要求按其中的指导处理.

## 调用示例

### 提供完整内容

```text
使用 $weekly-report 生成周报: 2026 年春季学期第 3 周.
本周进展:
- 完成模块 A 的联调, 修复 3 个缺陷
- 输出接口文档初稿
```

预期结果是在当前目录生成 `weekly-report-2026春-第3周.png` 和配套的 `weekly-report-2026春-第3周.typ` 源文件, 图片宽度约 1280px, 内容为标题, 分割线和上述进展条目, 条目原样呈现不做改写.

### 缺少周次时追问

```text
使用 $weekly-report 生成 2026 年春季学期的周报, 进展条目如下:
- 完成数据清洗脚本
```

预期结果是 skill 先追问这是第几周, 补齐周次后才渲染, 不会猜测周次或自行编造进展.

## 异常处理

+ typst 未安装或不在 PATH 中时, 报告缺失并停止, 不会尝试安装.
+ 系统缺少 Alimama FangYuanTi VF 字体时, 报告缺失并停止, 不替换为其他字体.
+ 年份, 学期, 周次或进展条目缺失时, 先追问补齐, 不猜测内容; 年份未提供时默认使用当前年份并明确说明.
+ typst 编译失败时, 展示完整错误输出并说明原因, 不静默重试.

## 进一步阅读

+ [执行流程](../skills/weekly-report/SKILL.md): 环境确认, 内容收集, 模板填充与渲染.
+ [Typst 模板](../skills/weekly-report/template.typ): 页面尺寸, 字体与版式.
+ [返回仓库说明](../README.md).
