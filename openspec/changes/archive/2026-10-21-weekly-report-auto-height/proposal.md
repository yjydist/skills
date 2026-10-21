# Proposal

## Why

周报和月报当前固定 A4 纸张高度, 内容一超页就拆成多张 PNG 并加页码后缀, 而实际使用中报告多为单张图片转发, 分页只增加阅读与归档成本. 同时内容列为空的备注列让出 12.7% 宽度, 中文条目约 25 字就换行, 且姓名在信息行内会被折行.

## What Changes

+ 页面改为宽 A4 (21cm), 高度 `auto`, 内容多长图片就有多高, 单次渲染只输出一张 PNG.
+ 版式调整: 左右边距 3.17cm 收窄为 1.9cm, 上下边距保持 2.54cm; 类别/内容/备注列宽由 14.3/73/12.7 改为 14.3/75.7/10, 内容列中文容量约 25 字/行提升到约 30 字/行.
+ 信息行改用内容自适应列宽, 姓名和日期不再折行.
+ 自我评价由 `√ 选项` 文本改为复选框: 未选中 `sym.ballot` (☐), 选中 `sym.ballot.cross` (☒).
+ 姓名和学号提供默认值 `易靖远` / `26031210039G`, 输入仍可覆盖; 两个模板的数据块同步为默认值.
+ 字体只用 `Alimama FangYuanTi`, 不再优先 `Alimama FangYuanTi VF`; 该字体缺失时回退 Typst 默认字体并给出提示.
+ **BREAKING** 产物命名去掉 `-第N页` 后缀, 结果 JSON 移除 `pages` 字段, 尺寸校验从 `2480 x 3508` 改为宽度 2480 且高度随内容.
+ 文档与测试同步: `SKILL.md`, `docs/weekly-report.md`, `README.md` 中分页和多页命名描述删除, 测试用例补单图与默认身份覆盖.

## Capabilities

### New Capabilities

+ `weekly-report`: 从结构化输入渲染周报或月报的单个 A4 宽度图片与可独立编译的 Typst 源文件, 包括版式参数, 固定默认身份信息, 字体回退与产物命名规则.

### Modified Capabilities

无. 仓库此前没有 OpenSpec 规格, 本变更建立该能力的首份规格.

## Impact

+ `skills/weekly-report/references/weekly-template.typ` 和 `monthly-template.typ`: 页面尺寸, 列宽, 信息行, 自我评价, 字体, 默认数据块.
+ `skills/weekly-report/scripts/render.py`: 字体常量与提示, 默认姓名和学号, 单图命名, 尺寸校验, 结果 JSON.
+ `skills/weekly-report/SKILL.md`, `docs/weekly-report.md`, `README.md`: 分页, 多页命名, 像素尺寸, 字体优先级描述.
+ `tests/test_weekly_report.py`: 多页交付用例, 3508 像素断言, `pages` 字段断言, 字体缺省用例.
+ 交付产物由 "多页 PNG + 源文件" 变为 "单张 PNG + 源文件", 已有脚本调用方依赖 `pages` 或 `-第N页` 命名时需同步调整.
