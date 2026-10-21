# Proposal

## Why

信息行当前使用 `table(columns: (auto, 1fr, auto))`, 中间的 `1fr` 列吃掉全部剩余宽度, 学号在该列内左对齐, 于是紧贴姓名, 日期被推到版心右边缘. 默认数据下实测姓名与学号之间只有 10pt 空白, 学号与日期之间 149.56pt, 相差 15 倍: 前两项挤成一段, 日期孤零零贴在右边.

## What Changes

+ 周报和月报模板的信息行由三列 `(auto, 1fr, auto)` 改为五列 `(auto, 1fr, auto, 1fr, auto)`, 用两个空列均分剩余宽度, 使姓名与学号之间和学号与日期之间的空白相等.
+ 默认数据下两处空白均为 74.78pt (约 2.6cm). 日期右端仍内缩 5pt, 与下方表格的单元格内缩一致, 不再贴到版心右边缘.
+ 规格中"信息行 MUST 使用按内容自适应的列宽"是一条实现形状的约束, 只保证不折行, 没有约束空白分布; 改为直接约束两处空白相等, 并新增等距场景.
+ 内容变长时两处空白同步收窄, 不会退化为固定间距加右侧留白.
+ 非破坏性: 输入 JSON, 产物命名和结果字段都不变.

## Capabilities

### New Capabilities

无.

### Modified Capabilities

+ `weekly-report`: "版式参数" 中信息行的列宽规则由按内容自适应改为两处空白均分, 并新增信息行等距场景.

## Impact

+ `skills/weekly-report/references/weekly-template.typ` 和 `monthly-template.typ`: 信息行的表格列定义.
+ `openspec/specs/weekly-report/spec.md`: 通过本 change 的 delta 在归档时同步.
+ 不涉及渲染脚本, 输入格式, 产物命名, 依赖或测试用例.
