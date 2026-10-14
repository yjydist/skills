# weekly-report 使用文档

`weekly-report` 将用户提供的学期, 周次与进展条目渲染为 A4 尺寸 300 DPI 的 PNG 图片和独立 Typst 源文件. 保留原文和版式, 超页时自动生成多张图片, 不代为归纳或编造进展.

## 使用前提

+ 将 [skill 目录](../skills/weekly-report/SKILL.md) 连同模板和 `scripts/` 一起提供给执行工具, 保持相对路径.
+ 需要 Python 3.9+, Typst 0.13+ 和字体族 `Alimama FangYuanTi`. 渲染脚本只依赖 Python 标准库.
+ 提供学期, 周次及非空进展条目. 年份省略时按用户当前年份补齐, 并在交付时说明.

下方用 `$weekly-report` 表示调用. 工具不支持这种形式时, 指定本 skill 的 `SKILL.md` 实际路径.

## 调用示例

```text
使用 $weekly-report 生成周报: 2026 年春季学期第 3 周.
本周进展:
+ 修复 #issue 并验证 $HOME 环境变量
+ 完成接口文档初稿
```

上述特殊字符作为普通文字呈现. 单页产物为 `weekly-report-2026春-第3周.png` 和同名 `.typ`. 需要多页时, 图片改为 `weekly-report-2026春-第3周-第1页.png`, `...-第2页.png` 等, 源文件仍只有一个.

```text
使用 $weekly-report 生成秋季学期周报, 进展如下:
+ 完成数据清洗脚本
```

此例会追问周次, 年份默认采用当前年份. 长条目和大量条目自动分页, 不自动缩字或改写.

## 直接运行脚本

输入 JSON 包含 `year`, `semester`, `week`, `items` 四个字段. 具体约束和示例见 [执行流程](../skills/weekly-report/SKILL.md). 保存 JSON 后运行:

```bash
python3 skills/weekly-report/scripts/render.py --input input.json --output-dir output
```

也可用 `--input -` 从标准输入读取 JSON. 成功时输出包含 `pages` 和 `files` 的 JSON, 分别表示页数与全部产物的绝对路径. `.typ` 源文件包含完整数据, 可独立编译, 不需要保留输入 JSON.

## 异常处理与检查

+ 缺少 Typst, 版本低于 0.13 或缺少目标字体时停止, 不自动安装或替换.
+ 无效输入或编译失败时返回非零退出码, 显示原因, 不交付部分图片.
+ 同名源文件或同前缀的单页, 多页图片已存在时停止, 不覆盖. 可指定新输出目录后重试.
+ 每张图片均为 2480 x 3508 像素. 交付前检查所有页面的字形, 条目内容与分页, 最终只交付 PNG 和 Typst 文件.

## 可选的手动验证

维护周报脚本时, 可在完整仓库的根目录运行 [周报测试](../tests/test_weekly_report.py). 基础测试只需要 Python 3.9+ 标准库, 覆盖无效输入, 产物冲突, 编译失败及环境检查:

```bash
python3 -m unittest discover -s tests -p test_weekly_report.py -v
```

默认跳过两项真实渲染测试. 安装 Typst 0.13+ 和 `Alimama FangYuanTi` 字体后, 在支持此环境变量语法的 shell 中运行:

```bash
RUN_TYPST_TESTS=1 python3 -m unittest discover -s tests -p test_weekly_report.py -v
```

真实测试覆盖特殊字符和换行的原文保留, 独立源文件编译, 单页与多页交付. 版式和中文显示还需要查看生成的图片进行验收.

## 进一步阅读

+ [执行流程](../skills/weekly-report/SKILL.md).
+ [Typst 模板](../skills/weekly-report/template.typ).
+ [渲染脚本](../skills/weekly-report/scripts/render.py).
+ [返回仓库说明](../README.md).
