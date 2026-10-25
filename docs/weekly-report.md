# weekly-report 使用文档

`weekly-report` 将用户提供的学生信息, 报告周期与各类别内容渲染为 A4 宽度 300 DPI 的 PNG 图片和独立 Typst 源文件, 图片高度随内容自动增长. 支持周报和月报, 保留模板版式. 人名, 项目名, 文档名, 数字与条目数量等事实沿用用户提供的内容, 不代为归纳, 编造或补写; 条目按事项式汇报口吻呈现, 动词开头, 省略主语与周期词.

## 使用前提

+ 将 [skill 目录](../skills/weekly-report/SKILL.md) 连同模板和 `scripts/` 一起提供给执行工具, 保持相对路径.
+ 需要 Python 3.9+ 和 Typst 0.13+. 模板只使用 `Alimama FangYuanTi` 字体, 该字体缺失时回退 Typst 默认字体, 并在结果的 `font_note` 中给出提示. 渲染脚本只依赖 Python 标准库.
+ 提供类型(周报或月报), 年月, 姓名, 学号, 日期范围, 各类别内容, 考勤和自我评价. 周报还需提供当月第几次. 年月省略时按用户当前日期补齐, 并在交付时说明. 姓名和学号可省略, 省略时分别使用默认值 `易靖远` 和 `26031210039G`.

下方用 `$weekly-report` 表示调用. 工具不支持这种形式时, 指定本 skill 的 `SKILL.md` 实际路径.

## 调用示例

```text
使用 $weekly-report 生成 2026 年 3 月第 2 次周报, 姓名常瑞, 学号 25031212280, 日期 2026.3.2-2026.3.8.
实验室、项目贡献:
+ 查看和对比实验室主机的硬件设备
科研进展:
+ 阅读师兄师姐的大论文, 积累综述的素材
其他: 服务性工作无, 日常锻炼, 心得体会无, 反思教训无.
考勤: 平均每天 5.5 小时, 9:30 前打卡 5 次. 自我评价: 满意.
```

产物为 `weekly-report-2026年3月第2次.png` 和同名 `.typ`, 只有这一张图片. 月报命名如 `monthly-report-2026年3月.png`.

```text
使用 $weekly-report 生成本月月报, 各项内容如下: ...
```

此例会追问月份和日期范围. 长条目和大量条目使图片高度增加, 不自动缩字, 截断或分页.

## 直接运行脚本

输入 JSON 的字段和约束见 [执行流程](../skills/weekly-report/SKILL.md). 保存 JSON 后运行:

```bash
python3 skills/weekly-report/scripts/render.py --input input.json --output-dir output
```

也可用 `--input -` 从标准输入读取 JSON. 成功时输出包含 `files` 和 `font_note` 两个字段的 JSON: `files` 为 PNG 与 `.typ` 的绝对路径, `font_note` 为字体回退提示, 字体齐全时为 `null`. 不再返回 `pages`, 需要时读取 `files` 长度. `.typ` 源文件包含完整数据, 可独立编译, 不需要保留输入 JSON.

## 异常处理与检查

+ 缺少 Typst 或版本低于 0.13 时停止, 不自动安装. `Alimama FangYuanTi` 缺失时提示并回退到 Typst 默认字体, 不停止, 需在交付说明中告知用户中文字形可能与预期不同.
+ 无效输入或编译失败时返回非零退出码, 显示原因, 不交付部分图片.
+ 同名源文件或图片已存在时停止, 不覆盖. 可指定新输出目录后重试. 发布阶段再次撞名时同样以中文错误停止.
+ 图片宽度固定为 2480 像素, 高度随内容变化. 交付前检查图片的字形, 表格内容与复选框, 最终只交付 PNG 和 Typst 文件.
+ 字体缺失而回退字体时, 自我评价的方框与勾形状不变, 三个选项的标记粗细一致.

## 可选的手动验证

维护周报脚本时, 可在完整仓库的根目录运行 [周报测试](../tests/test_weekly_report.py). 基础测试只需要 Python 3.9+ 标准库, 覆盖无效输入, 产物冲突, 编译失败及环境检查:

```bash
python3 -m unittest discover -s tests -p test_weekly_report.py -v
```

默认跳过两项真实渲染测试. 安装 Typst 0.13+ 后, 在支持此环境变量语法的 shell 中运行:

```bash
RUN_TYPST_TESTS=1 python3 -m unittest discover -s tests -p test_weekly_report.py -v
```

真实测试覆盖特殊字符和换行的字面渲染, 独立源文件编译, 单图交付与超长内容. 建议安装 `Alimama FangYuanTi` 以核对正式字形, 缺失时测试仍运行但使用回退字体. 版式和中文显示还需要查看生成的图片进行验收.

## 进一步阅读

+ [执行流程](../skills/weekly-report/SKILL.md).
+ [周报模板](../skills/weekly-report/references/weekly-template.typ) 和 [月报模板](../skills/weekly-report/references/monthly-template.typ).
+ [渲染脚本](../skills/weekly-report/scripts/render.py).
+ [返回仓库说明](../README.md).
