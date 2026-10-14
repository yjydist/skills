# skills

我个人自用的 skill 仓库, 用于维护可复用的任务指导和工作流程.

## 使用方式

+ 在下方列表选择 skill, 阅读对应文档中的使用前提和调用示例.
+ 将对应的 `skills/<skill-name>/` 完整目录提供给支持 skill 的工具, 保留其中的参考文件及相对路径. 具体加载方式以所用工具为准.
+ 每个 skill 的 `SKILL.md` 是执行入口, `docs/` 下的同名文档面向使用者. 仓库维护遵循 [AGENTS.md](AGENTS.md).

## skills 列表

+ convenient-commit: 按逻辑完整性规划提交边界, 拟定提交消息, 并在授权范围内创建 Git 提交. [具体文档](docs/convenient-commit.md)
+ to-github-issue: 将会话待办整理为无需认证的 issue 草稿, 创建时核对仓库与权限并集中确认, 支持父子 issue. [具体文档](docs/to-github-issue.md)
+ swiss-grid-design: 用瑞士国际主义的网格, 字体与留白创建, 调整或评审多媒介视觉方案, 明确默认参数和功能例外. [具体文档](docs/swiss-grid-design.md)
+ weekly-report: 原样保留用户进展, 渲染为 A4 尺寸 300 DPI PNG 周报图与独立 Typst 源文件, 超页时自动输出多张图片. [具体文档](docs/weekly-report.md)
+ paper-first-pass: 对学术论文执行第一遍 triage 阅读, 输出论文快照报告与第二遍阅读建议. [具体文档](docs/paper-first-pass.md)
+ paper-second-pass: 对学术论文执行第二遍理解阅读, 建立方法 mental model 与实验到 claim 的证据映射, 输出 16 节精读报告与第三遍阅读建议. [具体文档](docs/paper-second-pass.md)
+ paper-third-pass: 对学术论文执行第三遍深度阅读, 重建逻辑链并深入分析数学, 实验与代码, 支持完整 20 节报告或围绕指定问题的选择性报告. [具体文档](docs/paper-third-pass.md)

## 维护与检查

需要 Python 3.9+. 在仓库根目录建立虚拟环境并运行:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_skills.py
.venv/bin/python -m unittest discover -s tests -v
```

Windows 下将 `.venv/bin/python` 换为 `.venv/Scripts/python.exe`.

+ [规范检查脚本](scripts/check_skills.py) 检查 skill 名称和 YAML frontmatter, 对应使用文档, README 列表, 本地链接及 Markdown 标题锚点.
+ 标点检查覆盖 Markdown 正文和 skill 的 description; 无序列表必须使用 `+`. 围栏代码块, 缩进代码和行内代码不参与正文规范检查. 中文表述质量及指令语义仍需人工审查.
+ 脚本默认检查自身所在仓库, 也可用 `--root /path/to/repo` 指定其他仓库. 错误包含文件, 行号和规则名, 失败时返回非零退出码. 不检查远程链接可用性或原始 HTML 锚点.
+ [GitHub Actions](.github/workflows/check-skills.yml) 在 push 和 PR 时运行相同检查与无字体依赖的测试, 只申请仓库读取权限, 无需配置额外密钥.

周报的真实渲染测试需要本机安装 Typst 0.13+ 和 `Alimama FangYuanTi` 字体, 默认测试与 CI 会明确跳过这两项. 环境就绪时运行:

```bash
RUN_TYPST_TESTS=1 .venv/bin/python -m unittest discover -s tests -p test_weekly_report.py -v
```

真实测试覆盖特殊字符和换行的原文保留, 独立源文件编译, 单页与多页交付. 版式和中文显示还需要查看生成的图片进行验收.
