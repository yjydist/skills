# weekly-report Specification

## Purpose

从结构化输入渲染周报或月报, 输出一张宽度为 A4 的 PNG 图片和可独立编译的 Typst 源文件, 原样保留用户条目, 并按固定版式与身份信息呈现.

## Requirements

### Requirement: 单张可变高度图片

一次渲染 SHALL 输出一张图片, 宽度保持 A4 (21cm), 高度随内容自动增长, 不得因内容长度产生分页或多张图片. 无论内容多少, 页面 SHALL 保持单一横向连续的版式, 不插入分页符.

#### Scenario: 内容不足一页
- **WHEN** 条目总长度远小于 A4 版面
- **THEN** 输出单张图片, 宽度 2480 像素, 高度按实际内容收缩

#### Scenario: 内容超过一页
- **WHEN** 条目总长度超过一页 A4
- **THEN** 输出单张图片, 宽度 2480 像素, 高度按实际内容扩展, 不生成 `-第1页`, `-第2页` 等额外文件

### Requirement: 版式参数

模板 MUST 使用 A4 纸张宽度 21cm, 左右边距 1.9cm, 上下边距 2.54cm. 主表格列宽 MUST 为类别 14.3%, 内容 75.7%, 备注 10%. 信息行 MUST 使用按内容自适应的列宽, 使姓名, 学号和日期各占一行内显示.

#### Scenario: 中文条目换行位置
- **WHEN** 以 12pt 字号渲染中文内容条目
- **THEN** 内容列每行容纳约 30 个全角字符, 备注列保留且不占用超过 10% 宽度

#### Scenario: 姓名不折行
- **WHEN** 姓名为默认值 `易靖远`
- **THEN** 姓名与学号, 日期在同一信息行内完整显示, 不发生折行

### Requirement: 默认身份信息

输入未提供姓名或学号时, MUST 使用默认值 `易靖远` 和 `26031210039G`. 输入提供时 MUST 使用提供的值覆盖默认值. 两个模板的数据块 MUST 以同样的默认值作为示例.

#### Scenario: 省略身份信息
- **WHEN** 输入 JSON 不含 `name` 和 `student_id`
- **THEN** 图片和源文件显示 `易靖远` 与 `26031210039G`

#### Scenario: 覆盖身份信息
- **WHEN** 输入 JSON 的 `name` 为其他非空字符串
- **THEN** 图片和源文件显示该字符串, 不使用默认值

### Requirement: 自我评价复选框

自我评价 SHALL 以三个复选框呈现 `非常满意`, `满意`, `不太满意`, 选中项使用带叉方框, 其余项使用空方框. 输入 MUST 仍限制为这三个选项之一.

#### Scenario: 选中满意
- **WHEN** `self_evaluation` 为 `满意`
- **THEN** `满意` 前显示 `☒`, `非常满意` 和 `不太满意` 前显示 `☐`

#### Scenario: 非法选项
- **WHEN** `self_evaluation` 不是三个选项之一
- **THEN** 渲染停止并返回说明取值范围的错误

### Requirement: 字体选择与回退

渲染 MUST 只使用 `Alimama FangYuanTi` 字体, 不得优先尝试 `Alimama FangYuanTi VF`. 该字体缺失时 MUST 使用 Typst 默认字体继续渲染, 不得失败, 并通过结果中的 `font_note` 返回提示. 字体齐全时 `font_note` 为空.

#### Scenario: 字体缺失
- **WHEN** 环境中没有 `Alimama FangYuanTi`
- **THEN** 渲染成功, 图片使用默认字体, `font_note` 说明已回退

#### Scenario: 仅有 VF 变体
- **WHEN** 环境只安装 `Alimama FangYuanTi VF`
- **THEN** 不将其作为 `Alimama FangYuanTi` 使用, 按字体缺失回退并给出提示

### Requirement: 产物命名与结果输出

周报产物 MUST 命名为 `weekly-report-<年>年<月>月第<次>次.png` 与同名 `.typ`, 月报为 `monthly-report-<年>年<月>月.png` 与同名 `.typ`, 不存在页码后缀. 脚本成功时 MUST 返回 `files` 和 `font_note` 字段, 不得返回 `pages` 字段.

#### Scenario: 周报产物
- **WHEN** 渲染 2026 年 3 月第 2 次周报
- **THEN** 输出 `weekly-report-2026年3月第2次.png` 和 `weekly-report-2026年3月第2次.typ`

#### Scenario: 结果字段
- **WHEN** 脚本渲染成功
- **THEN** 标准输出 JSON 包含 `files` 与 `font_note`, 不含 `pages`

### Requirement: 尺寸校验与失败处理

脚本 MUST 校验输出图片宽度为 2480 像素且高度大于 0, 不得要求高度为 3508 像素. 编译失败或校验失败时 MUST 返回非零退出码且不留下任何产物. 目标目录已有同名前缀产物时 MUST 停止且不覆盖.

#### Scenario: 自动高度被接受
- **WHEN** 输出图片为 2480 x 1456 像素
- **THEN** 校验通过并交付

#### Scenario: 宽度不符合
- **WHEN** 输出图片宽度不是 2480 像素
- **THEN** 渲染判定失败, 返回非零退出码且不留下产物

#### Scenario: 同名产物存在
- **WHEN** 目标目录已有同名 `.png` 或 `.typ`
- **THEN** 停止并报告冲突路径, 不覆盖原文件

### Requirement: 内容原样保留

类别条目 MUST 按用户提供的原文, 顺序和条目内换行渲染, 不归纳, 改写或补写. 条目中的字符 MUST 作为文本渲染, 不作为 Typst 标记或代码执行.

#### Scenario: 特殊字符
- **WHEN** 条目包含 `#`, `$`, `"` 或反斜杠
- **THEN** 图片中按字面显示这些字符, 渲染不发生错误
