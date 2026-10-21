# Tasks

## 1. 周报模板

+ [x] 1.1 把 `skills/weekly-report/references/weekly-template.typ` 信息行的列定义改为 `(auto, 1fr, auto, 1fr, auto)`, 在姓名/学号之间和学号/日期之间各插入一个空 cell. 验证: `typst compile skills/weekly-report/references/weekly-template.typ /tmp/wr-weekly.png --format png --ppi 300` 编译成功, 输出宽度为 2480 像素.
+ [x] 1.2 测量默认数据下信息行三段的墨迹起止位置, 确认姓名与学号之间, 学号与日期之间的空白相等且均大于 60pt, 日期右端距版心右边缘约 5pt. 验证: 两处空白差值不超过 1pt.

## 2. 月报模板

+ [x] 2.1 同步修改 `skills/weekly-report/references/monthly-template.typ` 的同一行. 验证: 编译成功, 输出宽度为 2480 像素.
+ [x] 2.2 测量月报默认数据的信息行空白. 验证: 两处空白相等且差值不超过 1pt, 姓名, 学号和日期均不折行.

## 3. 集成验证

+ [x] 3.1 在仓库根目录运行 `RUN_TYPST_TESTS=1 python3 -m unittest discover -s tests -p test_weekly_report.py -v`. 验证: 全部用例通过, 含真实渲染用例.
+ [x] 3.2 用 `skills/weekly-report/scripts/render.py` 按默认数据各生成一份周报和月报, 查看 PNG 的信息行. 验证: 三项等距, 左右与下方表格的文字边线对齐, 无折行.
