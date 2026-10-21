# Tasks

## 1. 模板版式

- [x] 1.1 将两个模板的页面设置改为 `paper: "a4", height: auto`, 边距 `(x: 1.9cm, y: 2.54cm)`, 分别编译 `weekly-template.typ` 和 `monthly-template.typ`, 确认各输出一张 PNG 且宽度为 2480 像素, 高度随模板示例内容收缩.
- [x] 1.2 将信息行改为 `columns: (auto, 1fr, auto)`, 主表改为 `columns: (14.3%, 75.7%, 10%)`, 渲染确认 `姓名：易靖远` 单行显示且内容列每行约 30 个汉字.
- [x] 1.3 将自我评价改为复选框映射 (`sym.ballot` / `sym.ballot.cross`, 全角空格分隔), 渲染确认只出现 ☐ 和 ☒ 且选中项与 `self_evaluation` 一致.
- [x] 1.4 字体改为单一 `Alimama FangYuanTi`, 渲染确认中文正常; 另用不存在的字体族名做一次临时对照, 确认 Typst 仅告警并回退.
- [x] 1.5 两个模板的数据块默认值改为 `name: "易靖远"`, `student_id: "26031210039G"`, 编译确认独立源文件可直接出图.

## 2. 渲染脚本

- [x] 2.1 `FONTS` 收敛为 `("Alimama FangYuanTi",)`, 更新 `check_environment` 的缺失提示文案, 运行脚本单测确认字体用例通过且不再查询 VF 变体.
- [x] 2.2 让 `name` 与 `student_id` 可省略: 移出 `REQUIRED`, 校验前以默认值填充, 显式空字符串仍报错; 补充默认值与覆盖值的单测并运行通过.
- [x] 2.3 移除分页逻辑: 命名去掉 `-第N页`, 冲突正则去掉分页分支, 删除结果中的 `pages`, 尺寸校验改为宽度 2480 且高度大于 0; 更新受影响单测 (含 2480x1456 通过、宽度不符失败) 并运行通过.
- [x] 2.4 用真实 JSON 运行 `render.py` 输出到临时目录, 确认产物只有一张 PNG 和同名 `.typ`, 且 `.typ` 可直接 `typst compile` 出同尺寸图片.

## 3. 文档与说明

- [x] 3.1 更新 `skills/weekly-report/SKILL.md`: 删除分页, 多页命名, 3508 像素, VF 优先和 `pages` 描述, 改为单图可变高度, 默认身份可覆盖, 单一字体回退; 按文档中的命令实际渲染一次确认可执行.
- [x] 3.2 更新 `docs/weekly-report.md` 与 `README.md` 的条目简介: 同步单图产物, 命名, 默认姓名学号与测试说明; 检查文档内链接与路径仍有效.
- [x] 3.3 运行 `python3 -m unittest discover -s tests -p test_weekly_report.py -v` 确认常规用例全通过, 再以 `RUN_TYPST_TESTS=1` 运行真实渲染用例, 确认单图交付与独立源文件编译.

## 4. 集成验收

- [x] 4.1 分别生成一份周报和一份月报 (含长条目), 查看图片确认标题, 信息行, 表格边框, 中文与复选框无缺失, 且超长内容只产生一张图; 核对产物命名为 `weekly-report-<年>年<月>月第<次>次.png` 和 `monthly-report-<年>年<月>月.png`.
