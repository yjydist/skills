# Tasks

## 1. 参考文档

+ [x] 1.1 编写 `skills/skill-creator/references/spec.md`, 覆盖标准目录结构, frontmatter 字段表与约束, 命名规则, 资源目录职责, 标准字段与厂商扩展的可移植性对照. 验证: 逐项对照 Agent Skills 规范原文, 确认字段长度, 字符集和必填性一致, 且没有把任一客户端的专有机制写成规则.
+ [x] 1.2 编写 `skills/skill-creator/references/writing.md`, 覆盖描述公式与同级竞争测试, 触发语料的构成, 正文模式, 按步骤分配自由度, 常见失败清单. 验证: 每个方法都能从文档中找到判断依据和反例, 不含与 `spec.md` 重复的硬约束.

## 2. 脚本与测试

+ [x] 2.1 实现 `scripts/validate_skill.py` 的 frontmatter 解析: 优先 PyYAML, 不可用时回退到支持引号标量, 块标量, 一层嵌套映射, 注释, CRLF 和 BOM 的内置解析器. 验证: `tests/test_skill_creator.py` 中解析器的用例全部通过, 两条解析路径对同一输入给出一致字段.
+ [x] 2.2 实现字段校验与资源检查: name 与目录一致, 名称和描述长度及字符集, 可选字段类型与长度, 正文非空, 本地链接目标存在. 验证: 合法样例退出状态为 0; 名称大写, 名称与目录不一致, 描述为空, 描述超长和断链分别被判定为错误.
+ [x] 2.3 实现警告项与 `--strict`: 非标准字段, 未被直接引用的文件, 参考文件互相引用, 正文超过 500 行. 验证: 默认退出状态为 0 且输出警告; 同一输入加 `--strict` 后退出状态非 0.
+ [x] 2.4 实现 `scripts/init_skill.py`: 名称归一化与校验, 拒绝覆盖已存在目录, 按参数创建 `scripts/`, `references/`, `assets/`, 生成的 description 为空. 验证: 新目录中 `validate_skill.py` 因描述为空而失败; 非法名称不产生任何文件; 对已存在目录返回非零状态.
+ [x] 2.5 补齐 `tests/test_skill_creator.py` 的端到端用例, 覆盖两个脚本的退出码与输出. 验证: 在仓库根目录运行 `.venv/bin/python -m pytest tests/test_skill_creator.py` 全部通过.

## 3. 入口与仓库配套

+ [x] 3.1 编写 `skills/skill-creator/SKILL.md`, 按设计中的九段结构组织, 硬约束交由参考文件和脚本承担. 验证: `validate_skill.py skills/skill-creator` 无错误, 正文不含名称正则, 字段长度或厂商专有机制.
+ [x] 3.2 编写 `docs/skill-creator.md`, 说明使用前提, 调用示例, 脚本用法和未验证项的处理方式. 验证: 文档中的命令按原样执行成功, 相对链接指向存在的文件.
+ [x] 3.3 在 `README.md` 的 skills 列表加入 `skill-creator` 条目, 补充简介和文档链接. 验证: 条目格式与其余条目一致, 链接可解析到 `docs/skill-creator.md`.

## 4. 集成验证

+ [x] 4.1 在临时目录用 `init_skill.py` 创建一个样例 skill, 填写最小内容后分别运行默认与 `--strict` 校验. 验证: 两种模式均退出 0, 输出中没有错误和警告.
+ [x] 4.2 在不可用 PyYAML 的条件下运行校验, 确认内置解析器路径可用. 验证: 对同一样例得到与 PyYAML 路径相同的结论, 退出码一致.
+ [x] 4.3 准备触发语料并按 `writing.md` 的方法试跑, 正例覆盖不同措辞, 负例为近似但应交给其他 skill 或工具的请求. 验证: 记录每条语料的判断结果和依据; 无法启动独立会话时标注为人工判断.
+ [x] 4.4 检查交付说明的内容与实际产物一致: 文件清单, 已验证项, 未验证项. 验证: 按说明逐项核对, 不存在的文件或未执行的检查不得写成已验证.

## Workflow follow-up

+ 根据项目审查要求确认后归档本 change.
+ 归档后确认 `openspec/specs/skill-creator/spec.md` 的 Purpose 与需求已同步, README 与文档链接仍可解析.
