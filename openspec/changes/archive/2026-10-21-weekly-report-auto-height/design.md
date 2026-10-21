# Design

## Context

见 `proposal.md` 的 Why. 相关约束:

+ 现有实现由两个模板 (`references/*-template.typ`) 与一个 Python 脚本 (`scripts/render.py`) 组成. 脚本把 JSON 转成 Typst 字符串, 替换模板中 `REPORT_DATA_START` / `REPORT_DATA_END` 之间的数据块, 再调用 Typst 0.13+ 编译为 PNG.
+ 模板现状: `#set page(paper: "a4", margin: (top/bottom 2.54cm, left/right 3.17cm))`, 字体列表 `("Alimama FangYuanTi VF", "Alimama FangYuanTi")`, 信息行列宽 17.6/39.7/42.7%, 主表列宽 14.3/73/12.7%.
+ 脚本现状: 编译 `page-{p}.png`, 按 2480x3508 校验每张图, 多页时按 `-第N页` 命名, 返回 `pages`/`files`/`font_note`; `name` 与 `student_id` 为必填; 冲突检查正则含 `-第\d+页\.png`.
+ 使用环境为 macOS, 已安装 Typst 0.15.1 与 `Alimama FangYuanTi`.
+ 无既有 OpenSpec 规格, 本变更建立 `weekly-report` 能力.

实测依据 (Typst 0.15.1):

| 验证项 | 结果 |
|---|---|
| `#set page(paper: "a4", height: auto)` | 可用, 单页输出 |
| 同内容固定 A4 vs 自动高度 | 2480x3508 → 2480x1456 |
| 6000 词极端内容 | 2480x36954, 单张, 编译 1.4s 无报错 |
| 内容列 75.7% (版心 17.2cm) 中文 | 每行约 30 个全角字符 (现状约 25) |
| `sym.ballot` / `sym.ballot.cross` | 渲染为 ☐ / ☒, 中文字体下字形正常 |
| 不存在的字体族 | stderr 打 `warning: unknown font family`, 退出码 0, 按默认字体出图 |

## Goals / Non-Goals

**Goals:**

+ 单次渲染只产出一张 PNG, 宽度固定 2480 像素, 高度等于内容高度加页边距.
+ 版心从 14.66cm 增至 17.2cm, 内容列保持 75.7% 并保留 10% 备注列.
+ 身份信息有默认值且可覆盖, 模板数据块与默认值一致.
+ 自我评价使用 Typst 原生复选框字符.
+ 字体解析规则收敛为单一字体族, 缺失时静默回退.

**Non-Goals:**

+ 不改变字体大小, 行高, 标题字号, 表格结构与类别名称.
+ 不引入知识库, 自动归纳或内容改写.
+ 不改变输入 JSON 中除 `name`/`student_id` 可省略以外的字段约束.
+ 不处理 A4 高度上限保护, 不压缩超大图片.

## Decisions

### D1: 用页面 `height: auto` 代替固定纸张

采用 `#set page(paper: "a4", height: auto, margin: (x: 1.9cm, y: 2.54cm))`. 宽度仍由 `paper: "a4"` 提供, 高度交给布局.

备选: 在固定 A4 页面里把内容包进 `block(height: auto)` 再裁剪页面——Typst 无法根据内容裁剪页面尺寸, 且表格无法跨页, 复杂且不可靠. 备选: 用 `#set page(height: auto)` 同时去掉 `paper` 并显式写 `width: 21cm`——等价, 但 `paper` 让页宽意图更明显, 与现有模板差异更小.

### D2: 边距取 1.9cm / 2.54cm

左右从 3.17cm 收到 1.9cm, 版心 17.2cm; 上下保持 2.54cm, 维持正式文档的上下留白. 1.9cm 是明显加宽又不至于让表格顶到纸边的折中; 1.5cm 会再宽 0.8cm, 但打印边距过窄.

### D3: 主表列宽 14.3 / 75.7 / 10

类别列保持 14.3% 以容纳 `实验室、项目贡献` 的既有折行; 省出的 2.7% 全部给内容列; 备注列保留 10% (约 1.7cm). 备选是删除备注列以获得 40 字/行, 但备注是实验室表格的固定表头, 删除会改变表格结构, 用户已确认保留.

### D4: 信息行改用内容自适应列宽

`columns: (auto, 1fr, auto)`. 现状 17.6% 只够 2.58cm, `姓名：易靖远` 需要约 3.0cm, 会折成 `易靖`/`远`. 自适应列宽对任意姓名长度都不折行, 且日期靠右.

### D5: 复选框使用 `sym.ballot` / `sym.ballot.cross`

Typst 没有 `sym.ballot.checked` 修饰符 (实测 unknown symbol modifier). 选中项输出 `sym.ballot.cross` (☒), 未选中输出 `sym.ballot` (☐), 三者用全角空格分隔, 替换原 `√ 选项、选项` 的拼接. 备选 `sym.checkmark` (√) 放在文本外, 但与方框布局不一致, 视觉效果不如叉号方框.

模板内实现为对 `("非常满意", "满意", "不太满意")` 映射, 每项生成 `[#if selected { sym.ballot.cross } else { sym.ballot } #label]`, 保持现有 `evaluations` 变量的位置语义.

### D6: 字体收敛为 `Alimama FangYuanTi`

`FONTS = ("Alimama FangYuanTi",)`, 模板 `#set text(font: "Alimama FangYuanTi", ...)`. 缺失时 Typst 自身回退默认字体并仅打 warning, 脚本现有 `run_typst` 只把 stderr 转印, 不视为失败, 因此无需改动控制流; 仅需改 `check_environment` 的提示文案与存在性判断. 备选保留 VF 作为第二顺位被用户明确否决: VF 是可变字体, 字形与静态版不完全一致.

### D7: 默认身份信息放在脚本校验层

`validate_report` 在字段缺失时填充默认值, 而不是把 `name`/`student_id` 从 `REQUIRED` 中删除后交给模板: 这样模板数据块始终有值, 源文件可独立编译, 且未知字段检查不受影响. 实现上把两者移出 `REQUIRED`, 在校验循环前用 `setdefault` 填充并照常做非空字符串校验 (显式传空字符串仍报错).

模板数据块同步改为 `name: "易靖远"`, `student_id: "26031210039G"`, 文件名示例同步.

### D8: 产物命名与结果字段清理

`stem` 不再拼接页码, `files` 固定为 `.typ` 加一个 `.png`; 删除 `pages` 字段与 `-第N页` 冲突分支. 尺寸校验改为 `width == 2480 and height > 0`. 备选保留 `pages: 1` 以兼容调用方, 但该字段在单图模型下恒为 1, 保留只会误导; 需要兼容时读取 `files` 长度即可.

重新编译建议命令更新为不带 `{p}` 的 `typst compile "<stem>.typ" "<stem>.png" --format png --ppi 300`.

### D9: 测试调整

+ 删除多页交付用例 (`test_all_pages_are_delivered_in_order` 及 `-第N页` 断言), 改为单图断言: 产物恰为 2 个文件, 图片宽度 2480.
+ 尺寸校验单测的 PNG 头构造从 2480x3508 改为 2480x1456, 并补一条宽度不符的失败用例.
+ `pages` 断言改为 `files` 断言.
+ 新增默认身份用例: 省略 `name`/`student_id` 时 `build_source` 输出含 `易靖远` 与 `26031210039G`; 显式覆盖时输出覆盖值.
+ 字体用例改为只断言 `Alimama FangYuanTi`, 断言 VF 不再被查询.

## Risks / Trade-offs

+ 超长报告生成极高的 PNG (实测 36954px), 某些看图工具会缩放到不可读 → 不设上限, 交付时说明高度; 用户可改用 `.typ` 自行输出 PDF.
+ 去掉分页后, 单图高度可能超出部分平台图片上传上限 → 同上, 属于用户已接受的取舍.
+ `height: auto` 下表格不会跨页, 因此极长条目不会被切断, 但也无法利用固定 A4 的排版约束 → 这正是目标.
+ 不存在的字体族会让 Typst 每次编译打 warning, 含临时路径 → 与现状回退行为一致, 已在 `font_note` 中说明; 若日后噪音明显再考虑过滤 stderr.
+ 移除 `pages` 是外部可见变更, 依赖该字段的调用方会读到缺失键 → 在 proposal 中标记为 BREAKING, 文档明确以 `files` 为准.
+ 备注列固定 10% 在极窄内容下可能显得空 → 保持表头完整优先.

## Migration Plan

无数据迁移. 部署即替换模板与脚本; 已交付的源文件仍可独立编译 (其页面设置为旧值, 属历史产物). 回滚方式是还原这四个文件的改动, 无持久状态.
