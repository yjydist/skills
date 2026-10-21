# Tasks

## 1. 周报模板

- [x] 1.1 在 `skills/weekly-report/references/weekly-template.typ` 中加入 `check-box(selected)` helper (方框 `0.85em`, 边框 `0.5pt`, `baseline: 0.11em`, 勾线宽 `0.10em`), 并把 `evaluations` 改为调用该 helper; 验证: `typst compile skills/weekly-report/references/weekly-template.typ /tmp/wr-weekly.png --format png --ppi 300` 成功, 图片宽度 2480 像素, 查看自我评价行确认 `满意` 为方框加勾, 其余两项为空方框.
- [x] 1.2 把同一模板自我评价行的两处全角空格改为 `h()`: 引导文字后 `1em`, 选项之间 `1.2em`, 方框与标签之间 `0.4em`; 验证: `grep -n "　" skills/weekly-report/references/weekly-template.typ` 无输出, 重新编译后自评行仍为单行且各选项间距均匀.

## 2. 月报模板

- [x] 2.1 对 `skills/weekly-report/references/monthly-template.typ` 做与 1.1, 1.2 相同的修改; 验证: `typst compile skills/weekly-report/references/monthly-template.typ /tmp/wr-monthly.png --format png --ppi 300` 成功, 图片宽度 2480 像素, 自评行显示正确, `grep -n "　"` 无输出.

## 3. 文档

- [x] 3.1 在 `docs/weekly-report.md` 的交付检查项补充"字体缺失时自我评价方框与勾形状不变", 并在 `skills/weekly-report/SKILL.md` 的核对清单同步该检查; 验证: 两处表述一致, 文档内相对链接仍可解析.

## 4. 集成验证

- [x] 4.1 在仓库根目录运行 `RUN_TYPST_TESTS=1 python3 -m unittest discover -s tests -p test_weekly_report.py -v`; 验证: 全部用例通过, 含真实渲染与独立源文件编译.
- [x] 4.2 用 `skills/weekly-report/scripts/render.py` 分别生成一份周报和一份月报, 查看 PNG 的自我评价行; 验证: 三个方框粗细一致, 仅选中项带勾, 行高与改动前基本一致.
- [x] 4.3 把两个模板复制到 `/tmp`, 将字体族名改为不存在的名称后编译, 对照自评行; 验证: 文字字形回退, 但方框与勾形状与真实字体渲染一致.
- [x] 4.4 检查模板不再使用符号字符; 验证: `grep -n "sym.ballot\|sym.checkmark\|　" skills/weekly-report/references/*.typ` 无输出.

## Workflow follow-up

- 评审与验证通过后归档本 change, 确认 delta 同步到 `openspec/specs/weekly-report/spec.md`.
