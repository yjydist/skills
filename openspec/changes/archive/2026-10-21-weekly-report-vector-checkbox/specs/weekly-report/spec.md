# Spec Delta

## MODIFIED Requirements

### Requirement: 自我评价复选框

自我评价 SHALL 以三个复选框呈现 `非常满意`, `满意`, `不太满意`, 选中项使用带勾方框, 其余项使用空方框. 输入 MUST 仍限制为这三个选项之一.

#### Scenario: 选中满意
- **WHEN** `self_evaluation` 为 `满意`
- **THEN** `满意` 前的方框内含勾, `非常满意` 和 `不太满意` 前为空方框

#### Scenario: 非法选项
- **WHEN** `self_evaluation` 不是三个选项之一
- **THEN** 渲染停止并返回说明取值范围的错误

## ADDED Requirements

### Requirement: 自我评价标记的字体独立性

自我评价的方框与勾 MUST 由矢量图形绘制, 不使用符号字符. 其外观 MUST 只由模板中的矢量图形和字号决定, 不得随当前可用字体变化. 方框尺寸, 基线偏移和勾的线宽 MUST 以相对字号的单位表达, 使标记随字号等比缩放.

#### Scenario: 报告字体缺失
- **WHEN** 环境没有 `Alimama FangYuanTi`, 渲染回退到 Typst 默认字体
- **THEN** 渲染成功, 自我评价的方框与勾形状与字体齐全时一致

#### Scenario: 调整字号
- **WHEN** 模板正文字号改变
- **THEN** 方框尺寸, 基线偏移和勾的线宽随字号等比变化, 标记与文字的相对位置保持稳定
