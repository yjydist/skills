# Proposal

## Why

自我评价复选框当前用 `sym.ballot` 和 `sym.ballot.cross` 字符渲染, 而模板唯一使用的 `Alimama FangYuanTi` 不包含 `U+2610` 和 `U+2612`. Typst 会按字形回退到其他字体, 不同平台与字体环境得到的方框和叉粗细不一致, 同一行里观感割裂. 模板中的全角空格 `U+3000` 同样不在该字体中, 自我评价行的间距也在走回退. 报告以 PNG 交付并要求跨机器一致, 这些依赖应当消除.

## What Changes

+ 两个模板的自我评价标记改为 Typst 矢量绘制: 未选中为空心方框, 选中为方框加勾. 方框尺寸与基线偏移用 `em`, 勾的端点用相对方框的百分比, 跟随字号和方框尺寸等比缩放.
+ 自我评价行的两处 `U+3000` 全角空格改为显式 `h()` 间距, 去掉该行剩余的字体回退.
+ 规格中的"选中项使用带叉方框"改为"带勾方框", 并增加"方框与勾 MUST 由矢量图形绘制, 不使用符号字符, 不依赖字体字形"的约束; 现有场景里的 `☒`/`☐` 字面量改为形状描述.
+ 验收增加字体缺失场景: 回退到默认字体时, 方框与勾形状不变.

## Capabilities

### New Capabilities

无.

### Modified Capabilities

- `weekly-report`: "自我评价复选框"要求改变标记形状 (叉改为勾), 新增矢量绘制与字体独立性约束, 并补充字体回退场景.

## Impact

+ `skills/weekly-report/references/weekly-template.typ` 和 `monthly-template.typ`: 自我评价标记与行内间距.
+ `openspec/specs/weekly-report/spec.md`: 通过本 change 的 delta 在归档时同步.
+ `docs/weekly-report.md`: 交付前检查项补充字体缺失时复选框形状的确认.
+ 不涉及 `scripts/render.py`, 输入 JSON 格式, 产物命名, 字体回退逻辑或测试接口.
