# Tasks

任务按提交边界组织, 每组对应一条提交. 每组的验证方式统一为运行该 skill 的机械校验, 并确认结果符合该组声明的期望.

通用校验命令 (在仓库根目录运行):

```bash
node skills/skill-creator/scripts/validate_skill.mjs skills/<skill-name>
```

## 1. 补齐 convenient-commit 前提条件

- [x] 1.1 在 `skills/convenient-commit/SKILL.md` 的目的段之后, `## 核心原则` 之前插入 `## 前提条件`, 按运行时 (无), 第三方依赖 (无), 外部程序 (Git, 检查 `git --version`, 不设最低版本, 依据见 design.md D2) 三类列出. 验证: `node skills/skill-creator/scripts/validate_skill.mjs skills/convenient-commit` 输出 `校验通过.`, 无错误无警告.

## 2. 补齐 mentor-profile 前提条件

- [x] 2.1 在 `skills/mentor-profile/SKILL.md` 的 `## 适用与优先级` 之前插入 `## 前提条件`, 三类条目均写 "无", 检查命令写 `true` (依据见 design.md D1). 验证: 校验命令输出 `校验通过.`.

## 3. 补齐 paper-first-pass 前提条件

- [x] 3.1 在 `skills/paper-first-pass/SKILL.md` 的 `## 核心原则` 之前插入 `## 前提条件`, 三类条目均写 "无". 验证: 校验命令输出 `校验通过.`.

## 4. 补齐 paper-second-pass 前提条件

- [x] 4.1 在 `skills/paper-second-pass/SKILL.md` 的 `## 核心原则` 之前插入 `## 前提条件`, 三类条目均写 "无". 验证: 校验命令输出 `校验通过.`.

## 5. 补齐 paper-third-pass 前提条件并修复参考文件互引

- [x] 5.1 在 `skills/paper-third-pass/SKILL.md` 的 `## 核心原则` 之前插入 `## 前提条件`, 三类条目均写 "无". 验证: 校验命令输出 `校验通过.`.
- [x] 5.2 删除 `skills/paper-third-pass/references/report-format.md` 第 3 行中对 `selective-report-format.md` 的互引句子, 保留该文件对完整模式模板的自身说明; 确认 `SKILL.md` 第 35 行与第 66 行仍分别直接引用两个模板 (依据见 design.md D5). 验证: 校验命令输出 `校验通过.`, 且原先的 2 条警告消失.

## 6. 补齐 swiss-grid-design 前提条件

- [x] 6.1 在 `skills/swiss-grid-design/SKILL.md` 的 `## 适用与优先级` 之前插入 `## 前提条件`, 三类条目均写 "无". 验证: 校验命令输出 `校验通过.`.

## 7. 补齐 to-github-issue 前提条件并前移门禁

- [x] 7.1 在 `skills/to-github-issue/SKILL.md` 的 `## 工作流程` 之前插入 `## 前提条件`, 声明 GitHub CLI (检查 `gh --version`) 与目标主机认证 (检查 `gh auth status`), 两条均注明 "仅创建模式需要", 并明确仅整理草稿不受此节阻断 (依据见 design.md D3). 验证: 校验命令输出 `校验通过.`.
- [x] 7.2 调整 `skills/to-github-issue/SKILL.md` 的工作流程, 使创建模式在整理内容之前完成前提检查, 草稿模式跳过该检查; 不改变第 2 步已有的只读检查内容. 验证: 通读 `## 工作流程` 与 `## 操作边界`, 确认创建与草稿两条路径的检查时机不矛盾, 且 `description` 中 "仅整理草稿不需要仓库或 gh 认证" 的承诺仍成立.

## 8. 补齐 weekly-report 前提条件并归位依赖说明

- [x] 8.1 在 `skills/weekly-report/SKILL.md` 的 `## 工作流程` 之前插入 `## 前提条件`, 列出 Python 3.9+ (检查 `python3 -V`), Typst 0.13+ (检查 `typst --version`), 第三方依赖无 (仅标准库), 并写明字体缺失时回退且不阻断 (依据见 design.md D4). 验证: 校验命令输出 `校验通过.`.
- [x] 8.2 把 `skills/weekly-report/SKILL.md` 第 28 行开头的 "需要 Python 3.9+ 和 Typst 0.13+." 改为指向前提条件节; 同句中对字体的说明简化, 不重复前提条件的内容. 验证: 通读第 2 步, 确认不含与 `## 前提条件` 重复的版本号, 且人员按新句能定位到前提条件节.

## 9. 统一 swiss-grid-design 使用文档的小节标题

- [x] 9.1 将 `docs/swiss-grid-design.md` 的 `## 使用方式` 改为 `## 使用前提`, 内容不修改 (依据见 design.md D6). 验证: `grep -m1 '^## ' docs/swiss-grid-design.md` 输出 `## 使用前提`.

## 10. 更新 AGENTS.md 的变更检查项

- [x] 10.1 在 `AGENTS.md` 的 `## 变更检查` 下增加一条, 要求检查 `SKILL.md` 的 `## 前提条件` 存在且条目与使用文档的依赖说明一致 (依据见 design.md D7). 验证: 通读该节, 新条目与既有条目的粒度, 句式一致, 且不与既有条目重复.

## 11. 全仓集成检查

- [x] 11.1 对 9 个 skill 逐个运行校验命令, 确认全部输出 `校验通过.` 且无警告; 其中 `paper-third-pass` 的 2 条警告应已消失. 验证: 命令输出与期望逐项一致.
- [x] 11.2 运行 `node --test tests/skill_creator/`, 确认 158 项全部通过, 无回归. 验证: 输出 `pass 158`, `fail 0`.
- [x] 11.3 复核本次改动的前提条件条目: 对照各 skill 实际执行的命令与 `docs/` 中的既有说明, 逐项确认条目完整且检查命令可执行; 该节不在校验脚本覆盖范围内, 结论标注为人工核对. 验证: 交付说明中列出逐项核对结果, 并区分已验证项与人工判断项.
- [x] 11.4 检查 README 的 `## skills 列表` 与 `docs/` 目录仍与新内容一致, 确认本次改动未使任何既有链接或锚点失效. 验证: 逐个确认新增小节未改变既有标题文本, 唯一改动的小节标题 (`docs/swiss-grid-design.md`) 无入链.

## Workflow follow-up

- 全部任务完成后运行 `/openspec-verify-change` 核对实现与 artifacts 是否一致.
- 验证通过后运行 `/openspec-archive-change` 归档本变更.
