# 差分验证记录: Python 基准与 Node.js 实现

## 目的

`tests/oracle/` 已随 6.3 删除, 差分结果需要在 change 内留档, 以便事后复核"差异只剩已记录的解析器行为"这一结论. 本文记录本轮可复现的差分验证: 方法与真实命令输出, 覆盖范围, 仍存在的差异及其原因.

fixture 的逐条清单与生成脚本见 [verification-fixtures.md](verification-fixtures.md) 与 [verification-fixtures.sh](verification-fixtures.sh); 仅凭仓库内文件即可重建全部用例.

## 环境

+ 仓库: `/Users/yjydist/Code/skills`.
+ Python 基准: `git show ea69a2f:skills/skill-creator/scripts/validate_skill.py`, 恢复到 `/tmp/s5-oracle/validate_skill.py`. 基线提交固定为 `ea69a2f`; 本 change 提交后 `HEAD` 不再包含该文件, 不要用 `HEAD` 取基准.
+ 环境准备: 若仓库内没有 `.venv`, 先执行 `python3 -m venv .venv && .venv/bin/pip install 'pyyaml==6.0.3'`; 本次记录使用 Python 3.9.6 与 PyYAML 6.0.3.
+ Python 解释器: `.venv/bin/python`, PyYAML 版本 `6.0.3`, 基准因此走 `parse_with_pyyaml` 分支.
+ Node.js 实现: `skills/skill-creator/scripts/validate_skill.mjs`, 依赖 `yaml` 2.9.1, `mdast-util-from-markdown` 2.1.0 与 `decode-named-character-reference` 1.3.0, 安装在 `skills/skill-creator/node_modules`.
+ `--verbose` 下两者分别输出 `frontmatter 解析器: PyYAML` 和 `frontmatter 解析器: yaml 2.9.1`, 因此比较时默认不加 `--verbose`, 避免解析器名称造成假差异.

## 复现方法

```bash
cd /Users/yjydist/Code/skills
mkdir -p /tmp/s5-oracle
git show ea69a2f:skills/skill-creator/scripts/validate_skill.py > /tmp/s5-oracle/validate_skill.py
bash openspec/changes/skill-creator-js/verification-fixtures.sh /tmp/skill-creator-fixtures
```

上一条命令的末位参数是 fixture 输出目录, 任意可写目录均可; 本文统一写作 `/tmp/skill-creator-fixtures`.

对每个目标目录分别执行:

```bash
.venv/bin/python /tmp/s5-oracle/validate_skill.py <dir>; echo "exit=$?"
node skills/skill-creator/scripts/validate_skill.mjs <dir>; echo "exit=$?"
```

完整对比按"退出码 + 标准输出与标准错误"分别逐字节比较, 不做额外归一化; 两者的输出路径与行号格式本来就一致. 标准输出与标准错误分别比较, 因此某一侧独有的输出或位置差异也会被发现.

fixture 由脚本生成到任意可写目录; 本轮生成到 `/tmp/skill-creator-fixtures`, 共 32 个用例, 48 个文件; 其中本轮补充的用例见下方范围二开头的权威清单, 此处不再重复枚举. 生成方法见 [verification-fixtures.sh](verification-fixtures.sh).

## 范围一: 仓库内 9 个 skill

命令: 对 `skills/*/` 逐个用上述两条命令运行并比较.

| skill | Python 退出码 | Node 退出码 | 输出是否一致 | 输出摘要 |
| --- | --- | --- | --- | --- |
| convenient-commit | 0 | 0 | 是 | `校验通过.` |
| mentor-profile | 0 | 0 | 是 | `校验通过.` |
| paper-first-pass | 0 | 0 | 是 | `校验通过.` |
| paper-second-pass | 0 | 0 | 是 | `校验通过.` |
| paper-third-pass | 0 | 0 | 是 | 2 个警告, 内容一致 |
| skill-creator | 0 | 0 | 是 | `校验通过.` |
| swiss-grid-design | 0 | 0 | 是 | `校验通过.` |
| to-github-issue | 0 | 0 | 是 | `校验通过.` |
| weekly-report | 0 | 0 | 是 | `校验通过.` |

`paper-third-pass` 的具体输出, 两侧完全相同:

```text
警告: references/report-format.md:3: 参考文件互相引用, 只应从 SKILL.md 直接引用一层
警告: references/report-format.md:3: 链接仅按所在文件目录可解析, 建议改为相对 skill 根目录: selective-report-format.md
校验通过, 有 2 个警告.
```

结论: 9 个 skill 的退出码与输出全部一致, 无差异.

说明: 范围一只比较 `validate_skill`; `init_skill.mjs` 相对基线的骨架与提示变化属 tasks.md 4.1 的计划内变更, 不是校验器差异, 记录见 design.md 的已接受行为变化与 `tests/skill_creator/init.test.mjs`.

## 范围二: 固定 fixture

共 32 个用例; 本轮补充的用例为 `control-chars`, `control-chars-definition`, `midline-definition-text`, `paragraph-continuation-definition`, `multiline-control-chars`, `invalid-utf8`, `list-item-html-block`, `escaped-html`, `duplicate-same-line`, `mixed-encoded-same-line`, `fragment-control-chars`, `entity-legacy`, `multiline-html-tag`, `double-encoded-entity`, `multiline-label-control-chars` 与 `yaml-merge-key` (此列表是本轮补充用例的唯一权威清单, 其他文档引用此处, 不再重复枚举). 目录名, 文件内容与预期输出见 [verification-fixtures.md](verification-fixtures.md).

| 用例 | Python 退出码 | Node 退出码 | 结果 |
| --- | --- | --- | --- |
| valid-skill (合法 frontmatter) | 0 | 0 | 一致: `校验通过.` |
| invalid-yaml (非法 YAML) | 1 | 1 | 退出码一致, 错误文案不同 (见差异 2) |
| duplicate-keys (重复键) | 0 | 1 | 不一致 (见差异 1) |
| name-mismatch (name 与目录不一致) | 1 | 1 | 一致: `错误: SKILL.md:2: name 与父目录名不一致: other-name != name-mismatch` |
| empty-body (空正文) | 1 | 1 | 一致: `错误: SKILL.md: 正文不能为空` |
| long-body (超长正文) | 0 | 0 | 一致: `警告: SKILL.md: 正文超过 500 行, ...` |
| unknown-field (非标准字段) | 0 | 0 | 一致: `警告: SKILL.md:4: 非标准字段: foo` |
| broken-link (断链) | 1 | 1 | 一致: `错误: SKILL.md:8: 本地链接目标不存在: missing.md` |
| code-block-link (代码块/行内代码/HTML 注释内的链接) | 0 | 0 | 一致: `校验通过.` |
| list-item-html-block (列表项内原始 HTML 块的链接) | 1 | 0 | 不一致 (见差异 5) |
| html-unquoted (行内 HTML 未加引号属性) | 1 | 1 | 一致: `错误: SKILL.md:8: 本地链接目标不存在: missing.md` |
| multiline-html-tag (跨行行内 HTML 属性) | 0 | 1 | 不一致 (见差异 9) |
| escaped-html (反斜杠转义 HTML 标签) | 1 | 0 | 不一致 (见差异 6) |
| duplicate-same-line (同行两个相同目标) | 1 | 1 | 错误数不同, 2 对 1 (见差异 7) |
| mixed-encoded-same-line (同行同一目标的实体/百分号混写) | 1 | 1 | 错误数不同, 3 对 1 (见差异 7) |
| missing-reference (引用式定义缺失) | 1 | 1 | 一致: `错误: SKILL.md:8: 引用式链接定义不存在: ref` |
| links-portability (绝对/Windows/越界/大小写) | 1 | 1 | 一致: 1 个错误加 3 个警告, 见下 |
| unreferenced (未引用文件) | 0 | 0 | 一致: 2 个警告 |
| pycache-files (`__pycache__`/`.pyc`) | 0 | 0 | 一致: `校验通过.` |
| dependency-dirs (vendor/venv/site-packages) | 0 | 0 | 退出码一致, 输出不同 (见差异 3) |
| yaml11-scalars (YAML 1.1 纯量) | 1 | 0 | 不一致 (见差异 1) |
| yaml-merge-key (`<<` 合并键) | 0 | 1 | 不一致 (见差异 10) |
| control-chars (裸 `0x01`/`0x7f` 链接目标) | 1 | 1 | 一致: 2 个错误, 文案相同 |
| control-chars-definition (未引用定义目标含裸 `0x01`) | 1 | 1 | 一致: 1 个错误, 文案与行号相同 |
| midline-definition-text (正文/标题中的 `[x]:` 文本含控制字符) | 0 | 0 | 一致: `校验通过.` |
| paragraph-continuation-definition (段落/列表项续行中的定义样文本) | 1 | 1 | 一致: 1 个错误, 文案与行号相同 |
| multiline-control-chars (跨行行内/定义目标含裸控制字符) | 1 | 1 | 一致: 2 个错误, 文案与行号相同 |
| multiline-label-control-chars (跨行链接文本 + 裸控制字符) | 1 | 1 | 一致: 1 个错误, 文案与行号相同 |
| fragment-control-chars (片段/查询/纯锚点内控制字符) | 0 | 1 | 不一致 (见差异 8) |
| entity-legacy (无分号命名/数字实体) | 1 | 1 | 一致: 1 个错误, `a&hellipb.md` |
| double-encoded-entity (双次实体编码的链接/定义/HTML 属性) | 1 | 1 | 一致: 1 个错误, `only-a&b.md` |
| invalid-utf8 (非法 UTF-8) | 1 | 1 | 退出码一致, 错误文案不同 (见差异 4) |

合计: 20 个用例的退出码与输出完全一致, 12 个存在差异, 全部落在下节 32 个 fixture 的 10 类差异之中 (32 个 fixture 之外另有 2 类引用式定义识别差异, 见下节末的附注).

`control-chars` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: c\x7fd.md
校验失败: 2 个错误, 0 个警告.
```

`control-chars-definition` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\x01b.md
校验失败: 1 个错误, 0 个警告.
```

`multiline-control-chars` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
错误: SKILL.md:11: 本地链接目标包含 NUL 或控制字符: c\x02d.md
校验失败: 2 个错误, 0 个警告.
```

行号取链接与定义的起始行: 第 8 行是 `[文件](`, 第 11 行是 `[r]:`, 目标本身分别在续行. 加 `--strict` 时输出与退出码不变.

`multiline-label-control-chars` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
校验失败: 1 个错误, 0 个警告.
```

第 8 行是 `[多行`, 标签在换行处断开, 目标 `a<0x01>b.md` 在同一段的第二行; 行号取 `[` 所在行, 且不额外报 `本地链接目标不存在`. 目录内另有指向 `real.md` 的正常跨行标签, 两侧均通过. 加 `--strict` 时输出与退出码不变.

`paragraph-continuation-definition` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:11: 引用式链接定义不存在: ref
校验失败: 1 个错误, 0 个警告.
```

正文第 9 行的 `[ref]: a<0x01>b.md` 与列表项第 14 行的 `[list]: c<0x02>d.md` 都是段落续行, 不是引用式定义: 两侧都不报控制字符, 只报第 11 行对 `ref` 的引用缺少定义. 加 `--strict` 时输出与退出码不变.

`links-portability` 的具体输出, 两侧完全相同:

```text
错误: SKILL.md:8: 本地链接目标不存在: ../../outside.md
警告: SKILL.md:8: Windows 绝对路径不可移植: C:\tmp\a.md
警告: SKILL.md:8: 绝对路径链接不可移植: /etc/hosts
警告: SKILL.md:8: 链接路径大小写与磁盘不一致, 不可移植: real.md
校验失败: 1 个错误, 3 个警告.
```

严格模式对比:

| 目标 | Python 退出码 | Node 退出码 | 结果 |
| --- | --- | --- | --- |
| `--strict unknown-field` | 1 | 1 | 一致: `严格模式下警告视为错误: 1 个警告.` |
| `--strict valid-skill` | 0 | 0 | 一致: `校验通过.` |
| `--strict control-chars` | 1 | 1 | 一致: 与不加 `--strict` 相同 |
| `--strict control-chars-definition` | 1 | 1 | 一致: 与不加 `--strict` 相同 |
| `--strict multiline-control-chars` | 1 | 1 | 一致: 与不加 `--strict` 相同 |
| `--strict multiline-label-control-chars` | 1 | 1 | 一致: 与不加 `--strict` 相同 |
| `--strict paragraph-continuation-definition` | 1 | 1 | 一致: 与不加 `--strict` 相同 |
| `--strict duplicate-keys` | 0 | 1 | 不一致, 与差异 1 同源 |
| `--strict list-item-html-block` | 1 | 0 | 不一致, 与差异 5 同源 |
| `--strict fragment-control-chars` | 0 | 1 | 不一致, 与差异 8 同源 |
| `--strict dependency-dirs` | 1 | 0 | 不一致, 与差异 3 同源 |

## 仍存在的差异

32 个 fixture 的差异共 10 类, 均为预期. 本轮未发现不属于这 10 类的 fixture 差异. 32 个 fixture 之外另有 2 类引用式定义识别差异, 见本节末尾的 "附: 32 个 fixture 之外的引用式定义识别差异".

### 1. YAML 1.2 语义

原因: Python 基准使用 PyYAML (`yaml.SafeLoader`, 实为 YAML 1.1 语义), Node 实现按 delta spec 使用 `yaml` 包的 YAML 1.2 语义.

+ `duplicate-keys`: 重复键在 YAML 1.1 + PyYAML 下后者覆盖前者, 基准输出 `校验通过.` 并退出 0; `yaml` 包默认 `uniqueKeys` 为真, 输出 `错误: SKILL.md:3: 无法解析 frontmatter: Map keys must be unique` 并退出 1.
+ `yaml11-scalars`: `description: yes` 在 YAML 1.1 下解析为布尔值, 基准输出 `错误: SKILL.md:3: description 必须是字符串` 并退出 1; YAML 1.2 中 `yes` 是普通字符串, Node 输出 `校验通过.` 并退出 0.

这是 `tasks.md` 6.1 记录的 YAML 1.2 行为差异, 属于有意变更, 不视为缺陷.

### 2. 第三方 YAML 库的错误文案

原因: 相同非法输入由两个解析器报错, 行号一致, 文案不同.

+ `invalid-yaml` 基准: `错误: SKILL.md:3: 无法解析 frontmatter: expected ',' or ']', but got '<stream end>'`
+ `invalid-yaml` Node: `错误: SKILL.md:3: 无法解析 frontmatter: Flow sequence in block collection must be sufficiently indented and end with a ]`

两者退出码均为 1, `错误: SKILL.md:<行号>: 无法解析 frontmatter: ` 前缀一致, 只有库自身的 problem 文案不同. 该文案不属于本仓库控制的契约, 文档与测试均未断言具体文字.

### 3. 有意扩展的依赖目录忽略列表

原因: `tasks.md` 3.3 与 delta spec 要求未引用扫描忽略依赖目录, Node 实现在 `DEPENDENCY_DIRECTORIES` 中列入 `node_modules`, `vendor`, `third_party`, `venv`, `virtualenv`, `site-packages`; Python 基准只忽略隐藏路径, `__pycache__` 与 `.pyc`.

+ `dependency-dirs` 基准输出 3 条警告并退出 0:

```text
警告: scripts/site-packages/pkg.py: 未被 SKILL.md 直接引用的文件
警告: scripts/vendor/lib.py: 未被 SKILL.md 直接引用的文件
警告: scripts/venv/mod.py: 未被 SKILL.md 直接引用的文件
校验通过, 有 3 个警告.
```

+ Node 输出 `校验通过.` 并退出 0.

加 `--strict` 时同样不一致: 基准把 3 条警告视为错误, 输出 `严格模式下警告视为错误: 3 个警告.` 并退出 1; Node 仍输出 `校验通过.` 并退出 0.

这是 delta spec 的显式要求, 属于有意扩展, 不视为缺陷.

### 4. 非法 UTF-8 的解码错误文案

原因: 两侧都以 fatal 模式按 UTF-8 读取 `SKILL.md`, 判决一致 (均报 1 个错误并退出 1), 但错误文案来自各自的解码器.

+ `invalid-utf8` 基准: `错误: SKILL.md: 不是有效的 UTF-8 文本: 'utf-8' codec can't decode byte 0xff in position 119: invalid start byte`
+ `invalid-utf8` Node: `错误: SKILL.md: 不是有效的 UTF-8 文本: The encoded data was not valid for encoding utf-8`

前缀 `错误: SKILL.md: 不是有效的 UTF-8 文本: ` 一致; Python 附带字节值与位置, Node 的 `TextDecoder` 只给出通用说明. 该文案同样不属于本仓库控制的契约.

### 5. 列表项内原始 HTML 块的链接检查

原因: `references/spec.md` 规定"原始 HTML 块内的链接不检查, 块外的链接照常检查". micromark 把列表项内从 `<div>` 开始的块判定为块级 HTML (`html` 节点的父节点是 `listItem`), Node 实现把整块加入屏蔽范围; Python 基线只屏蔽行内代码, 代码块与 HTML 注释, 仍扫描块内文本中的 Markdown 链接. 这是更换解析器与按 spec 收紧链接范围带来的有意差异, 不是 Node 实现的缺陷.

+ `list-item-html-block` 基准: `错误: SKILL.md:7: 本地链接目标不存在: references/missing.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.
+ `list-item-html-block` Node: `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.

按当前 spec, Node 的行为正确, Python 基线属于该规则确立前的旧行为.

### 6. 反斜杠转义 HTML 标签的链接检查

原因: CommonMark 规定 `\<` 与 `\>` 是转义后的字面字符, 不会开始或结束 HTML 标签. Node 实现按解析结果提取行内 HTML 属性, 转义后的文本没有 `html` 节点, 因此不产生链接; Python 基线用正则直接扫描原文中的 `href="..."`, 仍把它当成本地链接. 这是更换解析器并按 spec 收紧链接范围带来的有意差异, 不是 Node 实现的缺陷.

+ `escaped-html` 基准: `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.
+ `escaped-html` Node: `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.

按当前 spec, 反斜杠转义的 HTML 标签不按标签检查, Node 的行为正确; Python 基线属于该规则确立前的旧行为.

### 7. 同一行同一目标的重复链接只报告一次

原因: Node 实现按"行号 + 解码后的完整目标"去重, 同一行内指向同一目标的多条链接只保留一条错误; 解码按本地链接规则处理实体与百分号编码, 因此 `a&b.md`, `a&amp;b.md` 与 `a%26b.md` 视为同一目标. Python 基线按原始字面目标逐条报告. `references/spec.md` 现已写明同一行同一目标只报告一次.

+ `duplicate-same-line` 基准: 两行 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 随后 `校验失败: 2 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.
+ `duplicate-same-line` Node: 一行 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.
+ `mixed-encoded-same-line` 基准: 三行 `错误: SKILL.md:8: 本地链接目标不存在: a&b.md`, 随后 `校验失败: 3 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.
+ `mixed-encoded-same-line` Node: 一行 `错误: SKILL.md:8: 本地链接目标不存在: a&b.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.

按当前 spec, Node 的行为正确; 该去重不掩盖不同行或解码后不同目标的错误 (片段或查询不同的目标仍各自报告).

### 8. 片段, 查询与纯锚点中的控制字符

原因: `references/spec.md` 规定本地链接目标的控制字符检查对象是完整目标, 含 `#` 后的片段与 `?` 后的查询, 纯锚点与仅含查询的目标也检查, 不因跳过存在性检查而豁免. Node 实现按该规则检查完整目标; Python 基线先用 `path = target.split("#", 1)[0].split("?", 1)[0]` 拆出路径, 纯锚点直接返回 `None`, 因此片段, 查询与纯锚点中的控制字符都不进入控制字符检查 (路径中的控制字符仍会报错, 见 `control-chars`). 这是按 spec 补齐后的有意差异, 不是 Node 实现的缺陷.

+ `fragment-control-chars` 基准: `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.
+ `fragment-control-chars` Node: 3 个错误, 退出码 1; 加 `--strict` 输出与退出码不变:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: #bad\x03y
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: real.md#bad\x01x
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: real.md?q=\x02
校验失败: 3 个错误, 0 个警告.
```

按当前 spec, 片段, 查询与纯锚点中的控制字符都须报错, Node 的行为正确; Python 基线属于该规则确立前的旧行为, 拆分片段与查询后只检查路径.

### 9. 跨行行内 HTML 标签的属性目标

原因: `references/spec.md` 规定行内 `<a href>` 与 `<img src>` 目标按本地链接检查, 标签可以跨行, 目标缺失按属性值所在行报告行号. Node 实现允许标签扫描跨行 (从标签名之后到 `>` 有 2048 字符上限), 属性行号用 `lineAtOffset` 计算; Python 基线的属性正则在单行内匹配, 遇到换行即放弃, 因此跨行标签原先两侧都漏报. 现在 Node 按 spec 报错, Python 基线仍漏报, 这是按 spec 补齐后的有意差异, 不是 Node 实现的缺陷.

+ `multiline-html-tag` 基准: `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.
+ `multiline-html-tag` Node: `错误: SKILL.md:9: 本地链接目标不存在: missing.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变. 同一用例中属性写在下一行的 `href="ok.md"` 目标存在, 不报错, 也不产生未引用文件警告.

### 10. `<<` 合并键 (YAML 1.2 语义)

原因: PyYAML 实为 YAML 1.1 语义, 会展开合并键 `<<`, 因此 `metadata` 中只剩被合并进来的 `author` 与 `version` 两个字符串字段; YAML 1.2 core schema 没有合并键, `yaml` 包把 `<<` 当作普通键, `metadata.<<` 的值是映射, 触发 `metadata` 嵌套值必须是字符串的校验. 这是 `tasks.md` 6.1 记录的 YAML 1.2 行为差异, 属于有意变更, 不视为缺陷.

+ `yaml-merge-key` 基准: `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.
+ `yaml-merge-key` Node: `错误: SKILL.md:4: metadata.<< 的值必须是字符串`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.

### 附: 32 个 fixture 之外的引用式定义识别差异

除上表 32 个 fixture 覆盖的差异外, 本轮另行复现了 2 类引用式定义识别范围差异. 它们不在 32 个 fixture 内, 因此不计入上表的 20 个一致 / 12 个差异, 也不计入本节编号 1 到 10 的 10 类; 已列入 design.md 的 "已接受的行为变化" 第 14 项.

原因: 迁移到 mdast 后按 CommonMark 识别引用式定义, 识别范围比 Python 基准的手写扫描器大. 基准未识别这两类写法的原因是其手写扫描器的实现限制: 普通段落行之后不带空行的 `> [标签]: 目标` 被当作段落惰性续行, 定义标题被要求在一行内闭合; 这是基线的实现行为, 不是现行 `references/spec.md` 的规定 (该条只记录当前实现不登记定义的三类写法). CommonMark 允许块引用打断段落, 也允许定义标题跨行, 因此 Node 实现把两类写法都识别为定义并通过校验.

两个复现目录由同一模板生成: 目录名与 frontmatter 的 `name` 一致, 前 7 行相同 (frontmatter 加 `# 标题` 与空行), 目录内另有被引用的 `real.md`; 第 8 至 11 行写入各自正文, 末行都是引用式链接 `[x][文档]`.

```bash
mkdir -p /tmp/w14-diff/{blockquote-definition,multiline-title-definition}

# 公共前 7 行: frontmatter 加标题与空行
for d in blockquote-definition multiline-title-definition; do
  printf -- '---\nname: %s\ndescription: 用于复现引用式定义识别范围差异的示例 skill.\n---\n\n# 标题\n\n' "$d" > /tmp/w14-diff/$d/SKILL.md
  printf '正文.\n' > /tmp/w14-diff/$d/real.md
done

# 块引用定义: 第 8 至 11 行
printf '正文\n> [文档]: real.md\n\n[x][文档]\n' >> /tmp/w14-diff/blockquote-definition/SKILL.md

# 定义标题跨行: 第 8 至 11 行
printf '[文档]: real.md "标\n题"\n\n[x][文档]\n' >> /tmp/w14-diff/multiline-title-definition/SKILL.md
```

块引用定义打断段落, `SKILL.md` 第 8 至 11 行:

```text
正文
> [文档]: real.md

[x][文档]
```

```bash
.venv/bin/python /tmp/s5-oracle/validate_skill.py /tmp/w14-diff/blockquote-definition; echo "exit=$?"
```

```text
错误: SKILL.md:11: 引用式链接定义不存在: 文档
校验失败: 1 个错误, 0 个警告.
exit=1
```

```bash
node skills/skill-creator/scripts/validate_skill.mjs /tmp/w14-diff/blockquote-definition; echo "exit=$?"
```

```text
校验通过.
exit=0
```

定义标题跨行, `SKILL.md` 第 8 至 11 行:

```text
[文档]: real.md "标
题"

[x][文档]
```

```bash
.venv/bin/python /tmp/s5-oracle/validate_skill.py /tmp/w14-diff/multiline-title-definition; echo "exit=$?"
```

```text
错误: SKILL.md:11: 引用式链接定义不存在: 文档
校验失败: 1 个错误, 0 个警告.
exit=1
```

```bash
node skills/skill-creator/scripts/validate_skill.mjs /tmp/w14-diff/multiline-title-definition; echo "exit=$?"
```

```text
校验通过.
exit=0
```

两个用例加 `--strict` 时输出与退出码不变, 基准仍为 `错误: SKILL.md:11: 引用式链接定义不存在: 文档` 加退出码 1, Node 仍输出 `校验通过.` 并退出 0. 两类都不在 [verification-fixtures.md](verification-fixtures.md) 的用例表内, 也不由 [verification-fixtures.sh](verification-fixtures.sh) 生成, 因此 32 个用例 / 20 个一致 / 12 个差异的数字不变.

对照: 列表项之下 4 空格缩进的 `[文档]: real.md` 两侧一致, 不属于本文记录的差异. 用同一模板再建 `list-item-four-space`, 把正文写成 `- 列表项` (第 8 行) 与 `    [文档]: real.md` (第 9 行), 两侧均报 `错误: SKILL.md:11: 引用式链接定义不存在: 文档` 加 `校验失败: 1 个错误, 0 个警告.` 并退出 1.

### 附: `--verbose` 的解析器名称

基准输出 `frontmatter 解析器: PyYAML`, Node 输出 `frontmatter 解析器: yaml 2.9.1`. 解析器已经更换, 这一行本就应当不同, 因此差分比较时默认不使用 `--verbose`. 这一项只出现在 `--verbose` 下, 不计入 fixture 差异类别.

## 已复核的修复项

+ 裸控制字符链接目标: 早前评审记录该用例两侧行为不同; 本轮复跑后两侧均为 2 个错误且文案逐字节相同, `--strict` 下也一致. 该差异已消失.
+ 引用式定义目标中的裸控制字符: 修复前 Node 对 `[r]: a\x01b.md` 输出 `校验通过.` 并退出 0, Python 基准报 1 个错误并退出 1; 正文另有 `[文本][r]` 引用时, Node 误报 `引用式链接定义不存在: r`. 原因是控制字符使 CommonMark 不把该行解析为定义, 而原有原始目标扫描只看 `](`. 修复后在屏蔽文本上补扫 `]:` 后同一行的定义目标, 两侧逐字节一致, 已补 `control-chars-definition` 用例.
+ 非法 UTF-8: `invalid-utf8` 用例两侧判决一致, 仅解码器文案不同, 已记入差异 4.
+ 无分号实体解码: 修复前 Node 的实体正则要求结尾分号, `[实体](a&ampb.md)` 与 `[数字](a&#65.md)` 在目标存在时报不存在, 而 Python 的 `html.unescape` 接受 legacy 命名实体与数字实体的省略分号写法. 修复后 `decodeHtmlEntities` 先按完整名称解码, 未命中再取最长的 HTML5 legacy 名称前缀, 数字实体同样允许省略分号; 非 legacy 名称 `&hellip` 省略分号时仍保留原文. 新增 `entity-legacy` 用例, 两侧逐字节一致.
+ 跨行链接与定义目标: 修复前 Node 对 `[a](\n  a\x01b.md)` 与 `[r]:\n  a\x01b.md` 均输出 `校验通过.` 并退出 0, Python 基准各报 1 个控制字符错误并退出 1. 原因是 `readInlineTargetAt` 与 `readDefinitionTargetAt` 遇到换行直接返回 `null`. 修复后在开括号与定义冒号后允许一个换行, 跳过续行缩进 (任意空格或制表符) 再解析目标, 行号取链接/定义起始行; 正常跨行链接与定义仍检查目标存在性. 新增 `multiline-control-chars` 用例, 两侧逐字节一致, 且不会额外报 `本地链接目标不存在` 或 `引用式链接定义不存在`.
+ 跨行链接文本: 修复前 Node 对 `[多行\n标签](a\x01b.md)` 输出 `校验通过.` 并退出 0, Python 基准报 1 个控制字符错误并退出 1. 原因是 `inlineLabelStart` 遇到换行直接返回 `-1`, 整个目标不进入原始扫描. 修复后回溯允许跨行, 以空行为段落边界, 不设固定长度上限 (本次迁移早期的 Node 草稿 (未入库) 的 512 与 999 上限已移除), 行号取 `[` 所在行; `]` 后的目标仍按原有规则解析, 字符引用形式 (`a&#1;b.md`) 经原始目标扫描后只报控制字符, 不再误报 `本地链接目标不存在: a�b.md`. 新增 `multiline-label-control-chars` 用例, 两侧逐字节一致.
+ 跨行行内 HTML 标签: 修复前 Node 与 Python 基线对 `<a\nhref="missing.md">x</a>` 都输出 `校验通过.` 并退出 0. 原因是 `readHtmlTagEnd` 遇到换行直接返回 `-1`, 属性也按标签起始行报告. 修复后标签扫描允许跨行, 从标签名之后到 `>` 的长度上限为 2048 字符, 属性值按自身所在行报告; 引号内的 `>` 与换行仍不结束标签, 未加引号的值在空白处结束. 新增 `multiline-html-tag` 用例: Node 报 `SKILL.md:9` 的缺失目标并退出 1, Python 基线仍漏报并退出 0, 已记入差异 9.
+ 脚注定义: 在临时目录用 `[^1]: missing.md` 定义加正文引用 `[^1]` 实测, 两侧均输出 `校验通过.` 并退出 0; 脚注定义与其引用都不按本地链接检查, 该行为在上一修复后已与基线一致, 因此未单列 fixture.
+ 双次实体编码: 修复前 Node 对 `[链接](a&amp;amp;b.md)` 报 `本地链接目标不存在: a&b.md` 并退出 1, Python 基准通过; 引用式定义同样, 只有行内 HTML 属性因走原文扫描而正常. 原因是 mdast 的 `link.url`/`definition.url` 已解码一次字符引用, `localTarget` 与 `decodedFullTarget` 又整体解码一次. 修复后为链接来源记录 `entitiesDecoded`: mdast 目标只补解无分号实体 (CommonMark 不解码省略分号的形式), 原始扫描与 HTML 属性目标仍整体解码一次; 因此 `&amp;amp;` 只变成 `&amp;`, 不会变成 `&`. 新增 `double-encoded-entity` 用例, 两侧逐字节一致.
+ 正文与标题中的定义文本: 修复前 Node 的 `scanRawDefinitionTargets` 只查找任意 `]:`, 把正文里的 `[a]: b\x01.md` 与二级标题里的 `[b]: c\x02.md` 都误判为引用式定义, 各报 1 个控制字符错误并退出 1; Python 基准按块首位置识别定义, 输出 `校验通过.` 并退出 0. 修复后原始扫描要求标签起始处位于块首: 行首最多 3 个空格, 或列表项标记/块引用前缀之后; 行内文本与标题里的 `[x]:` 被排除, 行首, 列表项与块引用内的定义仍照常报控制字符. 新增 `midline-definition-text` 用例, 两侧逐字节一致.
+ 段落续行中的定义样文本: 修复前 Node 的 `scanRawDefinitionTargets` 只看行首位置, 把段落续行 `正文\n[ref]: a\x01b.md` 与列表项续行 `+ 项目文字\n  [ref]: a\x01b.md` 都当成引用式定义: 前者报控制字符并因标签被登记而吞掉 `引用式链接定义不存在: ref`, 后者凭空报 1 个控制字符错误并退出 1, 而 Python 基准前者只报定义缺失, 后者 `校验通过.`. 原因是定义不能打断段落, 这些行属于上一段. 修复后在原始扫描中按 mdast 的 paragraph 范围排除候选行 (候选标签起始偏移严格位于段落内), 已解析的 definition 不受影响. 新增 `paragraph-continuation-definition` 用例, 两侧逐字节一致.
+ 用法行未列出 `--help`: 评审指出两个脚本的用法行没有 `--help`/`-h`, 而 `docs/skill-creator.md` 已把它作为可用选项说明, 属文档与实现不一致. 修复后 `validate_skill.mjs` 的用法行为 `用法: node validate_skill.mjs <skill 目录> [--strict] [--verbose] [--help]`, `init_skill.mjs` 为 `用法: node init_skill.mjs <name> [--path <父目录>] [--scripts] [--references] [--assets] [--help]`; `cli.test.mjs` 与 `init.test.mjs` 增加 `[--help]` 断言. 这是 design.md 已接受的 "CLI 用法/参数错误文案" 项内的文案补齐, 只影响该行文字, 退出码 (帮助 0, 参数错误 2) 与其余输出不变, 也不产生新的 fixture 差异类别.

本轮差分中发现的实现缺陷是无分号实体解码, 引用式定义目标漏检, 跨行目标漏检, 跨行链接文本漏检, 跨行行内 HTML 标签漏检, 双次实体解码, 同一行混写编码目标未去重, 正文行内定义文本误报与段落续行误判九处, 均已修复并补 fixture; 片段, 查询与纯锚点中的控制字符是补 fixture 后确认的预期差异, 已列入差异 8; 跨行行内 HTML 标签按 spec 补齐后与基线形成预期差异, 已列入差异 9; `<<` 合并键按 YAML 1.2 语义不展开, 已列入差异 10. 无分号 legacy 命名实体与数字实体的解码已按 Python `html.unescape` 对齐. 9 个仓库 skill 的输出和退出码全部一致; 32 个 fixture 中 20 个与基准完全一致, 其余 12 个的差异全部落在上节 32 个 fixture 的 10 类差异之中; 另有 2 类引用式定义识别差异不在 32 个 fixture 内, 见上节末的附注, 已列入 design.md 的已接受行为变化.

## 未复现项

无. 上节列出的每条差异均由本轮实际命令输出复现; 全部 32 个 fixture 本轮按 [verification-fixtures.sh](verification-fixtures.sh) 在临时目录重建后运行, 退出码与上表一致, 其中本轮补充的用例清单见范围二开头, 此处不再重复枚举.

## 相关验证

+ `node --test tests/skill_creator/`: 全部通过, 具体计数以实际命令输出为准; `links.test.mjs` 也在该命令覆盖范围内, 用例数同样以实际输出为准, 本文不再固定记录. 此前新增的覆盖: Node.js 版本守卫 (`validate_skill.mjs`, `init_skill.mjs` 且不创建目录, `check_dependencies.mjs` 在伪造 `18.0.0` 下按五段报告退出); 单包缺失 (隔离目录中用 symlink 链入 `yaml` 与 `decode-named-character-reference`, 只报告 `mdast-util-from-markdown`); 控制字符用例扩展到范围 (裸 `0x01`/`0x7f`), 引用式定义目标, 角度目标, 片段, 百分号编码, 以及代码块与脚注豁免. 本轮新增的覆盖: 无分号实体 (`links.test.mjs`, 覆盖 `&ampb`, `&#65`, `&#65b` 与不解码的 `&hellip` 对照), 跨行控制字符 (`links.test.mjs`: 跨行行内目标, 跨行定义目标, 四空格续行缩进, 以及跨行目标仍检查存在性) 与跨行行内 HTML 标签 (`links.test.mjs`: 跨行 `<a href>`/`<img src>`, 含 title 与 src 分处不同行, 按属性所在行报告), 以及跨行链接文本 (`links.test.mjs`: 跨行标签加裸控制字符报控制字符且不报目标缺失, 字符引用形式只报控制字符, 正常跨行标签指向存在文件时通过), 以及正文与标题中的定义文本 (`links.test.mjs`: 正文行内与标题里的 `[a]:` 不按定义报控制字符, 行首, 列表项与块引用内的合法定义仍报).
+ `openspec validate skill-creator-js --strict`: `Change 'skill-creator-js' is valid`.

## 任务 5.1 与 5.2 的人工验证记录

本节记录 2026-10-24 在本机实际执行的两项手工验收. `tasks.md` 5.1 的验收是逐条执行前提检查命令并通过, 临时改名 `node_modules` 后能阻断并输出五段式报告; 5.2 的验收是用一条新建请求走查流程, 产出的 `SKILL.md` 包含 `## 前提条件`. 下面的命令与输出为本机原样粘贴, 未做删改; 未执行或无法执行的项目在各小节末尾单列.

本节只在 `/tmp` 下的副本与临时目录中操作, 仓库内 `skills/skill-creator/node_modules` 未被移动或改写.

### 环境

+ 仓库: `/Users/yjydist/Code/skills`, macOS arm64, Node.js `v26.12.1`, npm `12.2.1`.
+ 仓库副本: `/tmp/s10-copy/skill-creator`, 由 `cp -R skills/skill-creator /tmp/s10-copy/skill-creator` 得到, 含 `node_modules`.
+ 依赖备份位置: `/tmp/s10-nm-backup` (只在副本中执行 `mv`).
+ 成功安装副本: `/tmp/w5-install/skill-creator`, 由 `rsync -a --exclude node_modules skills/skill-creator/ /tmp/w5-install/skill-creator/` 得到, 不含 `node_modules`.
+ 走查骨架: `/tmp/s10-walkthrough/sample-skill`, 由 `scripts/init_skill.mjs` 生成后补写.

### 5.1 前提检查: 通过路径

在 `skills/skill-creator` 下按 `SKILL.md` 的 `## 前提条件` 小节逐条执行.

| 检查项 | 命令 | 真实输出 | 退出码 |
| --- | --- | --- | --- |
| Node 版本判定 | `node -e "process.exit(Number(process.versions.node.split('.')[0]) < 20 ? 1 : 0)"` | 无输出 | 0 |
| 版本展示 (不作判定) | `node -v` | `v26.12.1` | 0 |
| npm 可用 | `npm -v` | `12.2.1` | 0 |
| 依赖可导入 (skill 目录) | `node scripts/check_dependencies.mjs` | 见下 | 0 |
| 依赖可导入 (仓库根目录) | `node skills/skill-creator/scripts/check_dependencies.mjs` | 与上一行相同 | 0 |
| 校验脚本可用 | `node skills/skill-creator/scripts/validate_skill.mjs skills/skill-creator` | `校验通过.` | 0 |

依赖检查的真实输出 (两条命令完全相同):

```text
依赖检查通过: yaml 2.9.1 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/yaml), mdast-util-from-markdown 2.1.0 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/mdast-util-from-markdown), decode-named-character-reference 1.3.0 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/decode-named-character-reference).
```

另外复核 `SKILL.md` 声明的 "其他目录照抄相对路径会因找不到模块而失败": 在 `/tmp` 执行 `node skills/skill-creator/scripts/check_dependencies.mjs`, 输出 `Error: Cannot find module '/private/tmp/skills/skill-creator/scripts/check_dependencies.mjs'` 与 `code: 'MODULE_NOT_FOUND'`, 退出码 1. 该失败来自脚本路径本身, 与文档描述一致.

结论: 本机满足全部前提, 三条判定命令 (Node 版本, npm, 依赖可导入) 均以 0 退出, 校验脚本可运行.

### 5.1 前提检查: 依赖缺失的阻断

在仓库副本中制造缺失, 不动仓库自身:

```bash
mv /tmp/s10-copy/skill-creator/node_modules /tmp/s10-nm-backup
cd /tmp/s10-copy/skill-creator
node scripts/check_dependencies.mjs; echo "exit=$?"
node scripts/validate_skill.mjs .; echo "exit=$?"
```

`check_dependencies.mjs` 的真实输出 (五段齐全):

```text
缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference
检测结果: 未发现可导入的依赖包; yaml 导入失败, 原始错误: Cannot find package 'yaml' imported from /private/tmp/s10-copy/skill-creator/scripts/check_dependencies.mjs; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/s10-copy/skill-creator/scripts/check_dependencies.mjs; decode-named-character-reference 导入失败, 原始错误: Cannot find package 'decode-named-character-reference' imported from /private/tmp/s10-copy/skill-creator/scripts/check_dependencies.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/s10-copy/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时 validate_skill.mjs 等脚本无法运行, 机械校验需要改为人工核对.
```

`exit=1`. 输出中 `/private/tmp/...` 是 macOS 上 `/tmp` 的真实路径, 脚本按真实路径展示.

`validate_skill.mjs` 的真实输出 (头部多了阻断说明, 仍保留五段):

```text
错误: 无法加载 Node.js 依赖 (yaml, mdast-util-from-markdown, decode-named-character-reference).
缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference
检测结果: 未发现可导入的依赖包; yaml 导入失败, 原始错误: Cannot find package 'yaml' imported from /private/tmp/s10-copy/skill-creator/scripts/validate_skill.mjs; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/s10-copy/skill-creator/scripts/validate_skill.mjs; decode-named-character-reference 导入失败, 原始错误: Cannot find package 'decode-named-character-reference' imported from /private/tmp/s10-copy/skill-creator/scripts/validate_skill.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/s10-copy/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时无法执行机械校验, 需要改为人工核对或等待安装.
```

`exit=1`, 未执行任何校验, 符合 "依赖缺失时按阻断处理, 不继续产出".

恢复后复检:

```bash
mv /tmp/s10-nm-backup /tmp/s10-copy/skill-creator/node_modules
node scripts/check_dependencies.mjs; echo "exit=$?"
node scripts/validate_skill.mjs .; echo "exit=$?"
```

```text
依赖检查通过: yaml 2.9.1 (解析自 /private/tmp/s10-copy/skill-creator/node_modules/yaml), mdast-util-from-markdown 2.1.0 (解析自 /private/tmp/s10-copy/skill-creator/node_modules/mdast-util-from-markdown), decode-named-character-reference 1.3.0 (解析自 /private/tmp/s10-copy/skill-creator/node_modules/decode-named-character-reference).
```

`exit=0`; 随后 `校验通过.`, `exit=0`.

结论: 依赖整目录缺失时, 两个脚本都以 1 退出, 报告含缺少项, 检测结果, 要求, 修复命令, 影响五段并保留原始错误; 恢复依赖后无需其他改动即重新通过.

### 5.1 前提检查: 首次运行的成功安装与重检

时间: 2026-10-24 15:11 CST. 环境同上. 副本由 `rsync` 排除依赖目录后生成, 只用于复现 delta spec 的 "首次运行" 场景; "包缺失" 场景另见 "5.1 前提检查: 包缺失的安装与重检".

```bash
rm -rf /tmp/w5-install && mkdir -p /tmp/w5-install
rsync -a --exclude node_modules skills/skill-creator/ /tmp/w5-install/skill-creator/
ls -d /tmp/w5-install/skill-creator/node_modules 2>&1
```

```text
ls: /tmp/w5-install/skill-creator/node_modules: No such file or directory
```

先探测 registry 连通性 (只探测, 不装包):

```bash
npm config get registry
curl -sS -m 8 -o /dev/null -w 'http=%{http_code}\n' https://registry.npmjs.org/yaml
```

```text
https://registry.npmjs.org/
http=200
```

按 `SKILL.md` `## 前提条件` 中"依赖缺失时的修复命令"一条给出的 `npm install --no-save --no-package-lock --prefix <skill 目录>` 命令安装, 命令与五段报告中的修复命令同形, 只把 `<skill 目录>` 换成本次副本:

```bash
cd /tmp/w5-install/skill-creator
npm install --no-save --no-package-lock --prefix /tmp/w5-install/skill-creator yaml mdast-util-from-markdown decode-named-character-reference; echo "exit=$?"
```

```text
added 36 packages in 1s
exit=0
```

`time` 显示 `real 0m1.486s`. 安装后生成了 `node_modules`, 顶层 33 个条目 (含 `@types` 作用域目录), 三个依赖的 `package.json` 版本分别为 `2.9.1`, `2.1.0`, `1.3.0`, 与仓库内依赖一致.

安装成功后按 `SKILL.md` `## 前提条件` 中"修复命令执行成功后重新执行本节的全部前提检查"一条的顺序重检: Node 可执行与版本, 依赖目录, 依赖可导入, npm 与其他外部程序. 命令与真实输出:

```bash
cd /tmp/w5-install/skill-creator
ls -d node_modules; echo "exit=$?"
command -v node; echo "exit=$?"
node -e "process.exit(Number(process.versions.node.split('.')[0]) < 20 ? 1 : 0)"; echo "exit=$?"
node scripts/check_dependencies.mjs; echo "exit=$?"
npm -v; echo "exit=$?"
true; echo "exit=$?"
node scripts/validate_skill.mjs /tmp/w5-install/skill-creator; echo "exit=$?"
```

```text
node_modules
exit=0
/opt/homebrew/bin/node
exit=0
exit=0
依赖检查通过: yaml 2.9.1 (解析自 /private/tmp/w5-install/skill-creator/node_modules/yaml), mdast-util-from-markdown 2.1.0 (解析自 /private/tmp/w5-install/skill-creator/node_modules/mdast-util-from-markdown), decode-named-character-reference 1.3.0 (解析自 /private/tmp/w5-install/skill-creator/node_modules/decode-named-character-reference).
exit=0
12.2.1
exit=0
exit=0
校验通过.
exit=0
```

注: 版本比较命令无输出, 只以退出码 0 表示通过; 其余命令按 `SKILL.md` `## 前提条件` 中"修复命令执行成功后重新执行本节的全部前提检查"一条的顺序执行.

结论: 依赖目录不存在时执行文档给出的安装命令可以成功安装 (`exit=0`), 安装后按 `SKILL.md` 的顺序重检全部通过, `validate_skill.mjs` 输出 `校验通过.` 并退出 0. 这补上了 "首次运行" 场景中 "安装成功后重新检查" 的实测路径, 与本节 "安装失败与重新阻断" 记录的失败分支互不替代. 本轮只写入 `/tmp/w5-install/skill-creator/node_modules`, 未改动仓库内 `skills/skill-creator/node_modules` (目录时间戳仍为 10:18).

### 5.1 前提检查: 包缺失的安装与重检

时间: 2026-10-24 15:16 CST. 环境同上. 本副本保留 `node_modules` 目录, 只用 symlink 链入仓库内已安装的 `yaml` 与 `decode-named-character-reference`, 不含 `mdast-util-from-markdown`, 用于复现 delta spec 的 "包缺失" 场景.

```bash
rm -rf /tmp/w51-partial && mkdir -p /tmp/w51-partial/skill-creator
rsync -a --exclude node_modules skills/skill-creator/ /tmp/w51-partial/skill-creator/
mkdir -p /tmp/w51-partial/skill-creator/node_modules
ln -s /Users/yjydist/Code/skills/skills/skill-creator/node_modules/yaml /tmp/w51-partial/skill-creator/node_modules/yaml
ln -s /Users/yjydist/Code/skills/skills/skill-creator/node_modules/decode-named-character-reference /tmp/w51-partial/skill-creator/node_modules/decode-named-character-reference
ls -la /tmp/w51-partial/skill-creator/node_modules
```

```text
total 0
drwxr-xr-x@ 4 yjydist  staff  128 Oct 24 15:16 .
drwxr-xr-x@ 6 yjydist  staff  192 Oct 24 15:16 ..
lrwxr-xr-x@ 1 yjydist  staff   93 Oct 24 15:16 decode-named-character-reference -> /Users/yjydist/Code/skills/skills/skill-creator/node_modules/decode-named-character-reference
lrwxr-xr-x@ 1 yjydist  staff   65 Oct 24 15:16 yaml -> /Users/yjydist/Code/skills/skills/skill-creator/node_modules/yaml
```

先运行依赖检查, 记录阻断输出:

```bash
cd /tmp/w51-partial/skill-creator
node scripts/check_dependencies.mjs; echo "exit=$?"
```

```text
缺少项: mdast-util-from-markdown
检测结果: yaml 2.9.1 可导入; decode-named-character-reference 1.3.0 可导入; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/w51-partial/skill-creator/scripts/check_dependencies.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/w51-partial/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时 validate_skill.mjs 等脚本无法运行, 机械校验需要改为人工核对.
exit=1
```

阻断输出只报告 `mdast-util-from-markdown`, 两个已链入的包被识别为可导入, 符合 "依赖目录存在但缺少某个声明的包".

再执行文档给出的安装命令, 命令与五段报告中的修复命令同形:

```bash
cd /tmp/w51-partial/skill-creator
npm install --no-save --no-package-lock --prefix /tmp/w51-partial/skill-creator yaml mdast-util-from-markdown decode-named-character-reference; echo "exit=$?"
```

```text
added 34 packages, and changed 2 packages in 191ms
exit=0
```

npm 把两个 symlink 替换为实际安装的目录, 并补齐 `mdast-util-from-markdown` 及其依赖. 安装后重新检查:

```bash
cd /tmp/w51-partial/skill-creator
node scripts/check_dependencies.mjs; echo "exit=$?"
node scripts/validate_skill.mjs /tmp/w51-partial/skill-creator; echo "exit=$?"
```

```text
依赖检查通过: yaml 2.9.1 (解析自 /private/tmp/w51-partial/skill-creator/node_modules/yaml), mdast-util-from-markdown 2.1.0 (解析自 /private/tmp/w51-partial/skill-creator/node_modules/mdast-util-from-markdown), decode-named-character-reference 1.3.0 (解析自 /private/tmp/w51-partial/skill-creator/node_modules/decode-named-character-reference).
exit=0
校验通过.
exit=0
```

结论: 依赖目录存在但缺少 `mdast-util-from-markdown` 时, `check_dependencies.mjs` 只报告该包并以 1 退出; 执行文档给出的安装命令以 0 退出; 安装后 `check_dependencies.mjs` 与 `validate_skill.mjs` 均以 0 退出, 后者输出 `校验通过.`. 本轮只写入 `/tmp/w51-partial/skill-creator/node_modules`, 仓库内 `skills/skill-creator/node_modules` 的目录时间戳仍为 10:18.

### 5.1 前提检查: `npm` 不在 PATH

时间: 2026-10-24 13:13 CST. 环境同上: macOS arm64, Node.js `v26.12.1`, npm `12.2.1`.

先构造一个只含 `node`, 不含 `npm` 的 PATH, 避免把 "node 也找不到" 混进结论:

```bash
mkdir -p /tmp/w4-node-only
ln -sf "$(command -v node)" /tmp/w4-node-only/node
env PATH=/tmp/w4-node-only /bin/sh -c 'command -v node; node -v; command -v npm; echo "exit=$?"; npm -v; echo "exit=$?"'
```

原样输出:

```text
/tmp/w4-node-only/node
v26.12.1
exit=1
/bin/sh: npm: command not found
exit=127
```

`node` 在 PATH 中可用 (`/tmp/w4-node-only/node`, `v26.12.1`), `command -v npm` 无输出且退出 1, `npm -v` 由 shell 报 `npm: command not found` 并退出 127. 失败只由 npm 查找引起, 不是 node 缺失的连带结果.

另按 `PATH=/usr/bin:/bin` 复核一次, 与上面结论一致 (该 PATH 下 `node` 也不存在, `command -v node` 退出 1, 因此只作旁证):

```bash
env PATH=/usr/bin:/bin sh -c 'command -v npm; echo "exit=$?"'
env PATH=/usr/bin:/bin npm -v; echo "exit=$?"
```

```text
exit=1
env: 'npm': No such file or directory
exit=127
```

结论: `SKILL.md` `## 前提条件` 中 npm 一条要求的检查命令 `npm -v` 在 npm 不在 PATH 时以非零状态退出, 与同句 "命令不存在或非零状态按缺失处理" 一致. 按该条与"执行脚本或产出文件前逐项检查"一条, 该情形归为外部程序缺失: npm 缺失按修复 Node.js 安装处理, 由执行者按目标平台给出修复命令 (nvm 安装或切换 Node 版本, 或系统包管理器), 不单独安装系统程序, 也不用仓库里的 `npm install` 命令顶替. 因此五段报告中 "修复命令" 一段由执行者按平台给出, 仓库无法固定; 其余四段 (缺少项, 检测结果含原始错误, 要求, 影响) 仍按五段格式填写. 本轮只记录上述命令与退出码, 没有伪造该五段报告的具体文本.

### 5.1 前提检查: 安装失败与重新阻断

时间: 2026-10-24 13:11 CST (首次失败登记日志时间 `05_11_46`, 该日志按 UTC 记时). 副本不含 `node_modules`, 模拟 "依赖目录不存在, 需要执行修复命令" 的状态; 仓库内的依赖目录未被触碰.

```bash
rm -rf /tmp/w4-install && mkdir -p /tmp/w4-install
rsync -a --exclude node_modules skills/skill-creator/ /tmp/w4-install/skill-creator/
cd /tmp/w4-install/skill-creator
npm install --no-save --no-package-lock --prefix /tmp/w4-install/skill-creator --registry http://127.0.0.1:1 yaml; echo "exit=$?"
```

`127.0.0.1:1` 上没有 registry, 连接必然被拒. 原样输出 (省略中间的调用栈行, 保留首尾与全部 `code`/`errno`/`reason` 信息):

```text
npm error code ECONNREFUSED
npm error syscall connect
npm error errno ECONNREFUSED
npm error FetchError: request to http://127.0.0.1:1/yaml failed, reason: connect ECONNREFUSED 127.0.0.1:1
npm error     at ClientRequest.<anonymous> (/opt/homebrew/lib/node_modules/npm/node_modules/minipass-fetch/lib/index.js:130:14)
...
npm error   code: 'ECONNREFUSED',
npm error   errno: 'ECONNREFUSED',
npm error   syscall: 'connect',
npm error   address: '127.0.0.1',
npm error   port: 1,
npm error   type: 'system',
npm error   requiredBy: '.'
npm error }
npm error
npm error If you are behind a proxy, please make sure that the 'proxy' config is set properly.  See: 'npm help config'
npm error A complete log of this run can be found in: /Users/yjydist/.npm/_logs/2026-10-24T05_11_46_460Z-debug-0.log
exit=1
```

该次耗时约 70 秒, 因为 npm 默认重试. 加上 `--fetch-retries=0 --fetch-timeout=2000` 重跑同一命令, 原始错误不变, `real 0m0.237s`, `exit=1`; 失败是确定性的, 与耗时无关.

安装失败后复查依赖与阻断:

```bash
cd /tmp/w4-install/skill-creator
ls -d node_modules 2>&1
node scripts/check_dependencies.mjs; echo "exit=$?"
```

```text
ls: cannot access 'node_modules': No such file or directory
缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference
检测结果: 未发现可导入的依赖包; yaml 导入失败, 原始错误: Cannot find package 'yaml' imported from /private/tmp/w4-install/skill-creator/scripts/check_dependencies.mjs; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/w4-install/skill-creator/scripts/check_dependencies.mjs; decode-named-character-reference 导入失败, 原始错误: Cannot find package 'decode-named-character-reference' imported from /private/tmp/w4-install/skill-creator/scripts/check_dependencies.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/w4-install/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时 validate_skill.mjs 等脚本无法运行, 机械校验需要改为人工核对.
exit=1
```

注: 本文各段依赖快照均按当前依赖清单 (三项) 记录; 早前按两项记录的旧快照已同步为三项, 因此不再有差异.

结论: 安装以 1 退出并给出 npm 原始错误 (`ECONNREFUSED`, 含日志路径); 依赖目录仍不存在, 检查脚本以 1 退出并按五段重新阻断. 这与 `SKILL.md` `## 前提条件` 中"安装失败按前提缺失处理并报告原始错误"一条和"修复命令执行成功后重新执行本节的全部前提检查"一条一致: 安装失败按前提缺失处理并报告原始错误, 重新检查仍失败时保留原始错误并重新阻断, 等待用户选择; 过程没有自动降级, 没有跳过依赖检查继续产出.

仓库自身未受影响, 复检:

```bash
node skills/skill-creator/scripts/check_dependencies.mjs; echo "exit=$?"
ls -ld skills/skill-creator/node_modules
```

```text
依赖检查通过: yaml 2.9.1 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/yaml), mdast-util-from-markdown 2.1.0 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/mdast-util-from-markdown), decode-named-character-reference 1.3.0 (解析自 /Users/yjydist/Code/skills/skills/skill-creator/node_modules/decode-named-character-reference).
exit=0
drwxr-xr-x 37 yjydist staff 1184 Oct 24 10:18 skills/skill-creator/node_modules
```

目录时间戳仍是 10:18, 早于本轮走查, 说明全部写操作只发生在 `/tmp` 副本内.

未验证项:

+ 已验证: Node.js 版本低于 20 的分支有自动化覆盖, `tests/skill_creator/prerequisites.test.mjs` 通过 `--require` 预加载把 `process.versions.node` 改写为 `18.0.0`, 对三个脚本断言标准错误含五段且 `exit=1`. 本轮手工复跑时, 预加载脚本内容只有一行 `Object.defineProperty(process.versions, "node", { value: "18.0.0" });`, 写入任意临时 `.cjs` 文件后用 `NODE_OPTIONS=--require <该文件>` 挂载即可; 复现命令: `printf '%s\n' 'Object.defineProperty(process.versions, "node", { value: "18.0.0" });' > node18-preload.cjs && NODE_OPTIONS="--require ./node18-preload.cjs" node skills/skill-creator/scripts/validate_skill.mjs skills/skill-creator; rm -f node18-preload.cjs`, 输出 `缺少项: Node.js 20 或更高版本`, `检测结果: 当前为 Node.js 18.0.0.`, 要求, 修复命令, 影响五段, `exit=1`; `init_skill.mjs` 同场景下不创建目录, `check_dependencies.mjs` 同场景下不输出 `依赖检查通过`.
+ 已验证: `node_modules` 存在但单个包缺失的中间状态有自动化覆盖, 用例 `只缺 mdast-util-from-markdown 时只报告实际缺失项` 在隔离目录中把仓库的 `yaml` 与 `decode-named-character-reference` 以 symlink 链入 `node_modules` 后运行 `validate_skill.mjs`. 本轮手工复现同样场景, 五段齐全, 输出 `缺少项: mdast-util-from-markdown`, `检测结果: yaml 可导入; decode-named-character-reference 可导入; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' ...`, `exit=1`. 同一副本中执行安装命令后重检通过, 见 "5.1 前提检查: 包缺失的安装与重检".
+ 未在真实的 Node.js 18 或更低版本运行时执行: 版本守卫的判定分支已由 preload 伪造版本号覆盖, 但真实旧版本运行时自身的语法与内置 API 差异未验证.
+ 未在缺少 `node` 的环境执行, `node` 不存在时的分支未实际触发.
+ 已验证: 安装失败分支已在 `/tmp` 副本中用不可达 registry 实测, npm 以 `ECONNREFUSED` 退出 1 并保留原始错误与日志路径, 随后 `check_dependencies.mjs` 重新阻断, 未自动降级; 见 "5.1 前提检查: 安装失败与重新阻断".
+ 已验证: `npm` 不在 PATH 时的分支已实测, 隔离 PATH 下 `command -v npm` 退出 1, `npm -v` 退出 127 并报 `npm: command not found`; 见 "5.1 前提检查: `npm` 不在 PATH".
+ 已验证: 依赖目录不存在时执行文档给出的安装命令并成功安装的路径已实测, 见 "5.1 前提检查: 首次运行的成功安装与重检". `npm install --no-save --no-package-lock --prefix /tmp/w5-install/skill-creator ...` 以 0 退出, 安装后按 `SKILL.md` `## 前提条件` 中"修复命令执行成功后重新执行本节的全部前提检查"一条的顺序重检 (Node 可执行与版本, 依赖目录, 依赖可导入, npm 与其他外部程序) 全部以 0 退出, `validate_skill.mjs` 输出 `校验通过.`; 该成功路径与 "安装失败与重新阻断" 的失败分支分别记录.
+ 真实网络故障只覆盖 `ECONNREFUSED` (registry 端口拒绝连接) 一种; DNS 失败, 连接超时, 代理认证失败, registry 5xx 等故障类型的 npm 文案与重试行为不同, 本轮未复现.

### 5.2 新建, 改进与交付规则的文字走查

这一节是规则走查, 不是真实客户端会话, 也没有真实用户提问; 下面的 "新建请求" 是按 `SKILL.md` 规则构造的样例, 用于检查规则是否写出以及产出是否带 `## 前提条件`.

逐条核对 `skills/skill-creator/SKILL.md` 的三处规则:

+ 新建: `SKILL.md` 的 `## 脚手架与校验` 小节要求新 skill 的 `SKILL.md` 必须包含 `## 前提条件`, 列出运行时, 最低版本, 第三方依赖, 外部程序和认证并给出可执行检查命令, 缺少该节不交付; 同一小节的脚手架步骤 (运行 `scripts/init_skill.mjs`) 输出也提示填写 "## 前提条件" 的占位内容.
+ 改进现有 skill: `## 改进现有 skill` 小节要求现有 skill 缺少 `## 前提条件` 时补上, 且不按当前请求裁剪.
+ 交付说明: `## 交付说明` 小节要求说明前提检查结果, 用户授权降级时记录缺少项, 跳过的步骤, 未验证项和对产物的影响; `## 脚手架与校验` 小节给出缺 Node.js 或依赖时的降级路径 (手工创建目录与最小 frontmatter, 再按人工核对项逐项核对).

样例新建请求: "统计仓库内 Markdown 文件数量并输出汇总表". 按流程生成骨架:

```bash
cd /Users/yjydist/Code/skills/skills/skill-creator
node scripts/init_skill.mjs sample-skill --path /tmp/s10-walkthrough
```

```text
已创建: /private/tmp/s10-walkthrough/sample-skill
下一步: 填写 "## 前提条件" 的占位内容, description 和流程正文, 再运行 node /Users/yjydist/Code/skills/skills/skill-creator/scripts/validate_skill.mjs /private/tmp/s10-walkthrough/sample-skill
```

骨架包含 `## 前提条件` 占位节和两处 TODO 注释, 因此正文非空, 但 `description` 仍为空. 直接校验:

```bash
node scripts/validate_skill.mjs /tmp/s10-walkthrough/sample-skill; echo "exit=$?"
```

```text
错误: SKILL.md:3: description 不能为空
校验失败: 1 个错误, 0 个警告.
```

`exit=1`. 随后按 `SKILL.md` 的 `## 脚手架与校验` 小节替换 `## 前提条件` 的占位内容 (填写条目并删除该节 TODO), 再写 description 与流程正文并删除剩余 TODO, 最终文件:

```markdown
---
name: "sample-skill"
description: "在用户要求统计仓库内 Markdown 文件数量并输出汇总表时使用. 只做本地文件计数, 不联网."
---

# sample-skill

统计指定目录内的 Markdown 文件数量, 按一级子目录汇总.

## 前提条件

+ Node.js 20 或更高版本. 检查: `node -e "process.exit(Number(process.versions.node.split('.')[0]) < 20 ? 1 : 0)"`; 非零状态按缺失处理.
+ 无第三方依赖. 检查: `true`; 该命令不读取文件, 以状态 0 退出表示本项没有需要检测的依赖.
+ 无外部程序与认证要求. 检查: `true`; 该命令不读取文件, 也不依赖 PATH 中的其他程序, 以状态 0 退出表示本项没有需要检测的外部程序或认证.
+ 任一项不满足时停止, 按五段报告: 缺少项, 检测结果, 要求, 修复命令, 影响.

## 工作流程

+ 确认目标目录存在且可读; 不存在时报告路径并停止.
+ 统计目标目录下所有 `.md` 文件, 按一级子目录分组计数.
+ 输出表格, 列为子目录和文件数, 末行给出总计.
```

校验:

```bash
node scripts/validate_skill.mjs /tmp/s10-walkthrough/sample-skill; echo "exit=$?"
node scripts/validate_skill.mjs --strict /tmp/s10-walkthrough/sample-skill; echo "exit=$?"
```

两次都是 `校验通过.` 与 `exit=0`. 产出的 `SKILL.md` 第 10 行是 `## 前提条件`, 与 `tasks.md` 5.2 的验收相符.

补充核对机械校验的覆盖边界: 另建 `/tmp/s10-walkthrough/no-section` 的同名样例, description 与正文齐全但没有 `## 前提条件`, 运行 `node scripts/validate_skill.mjs /tmp/s10-walkthrough/no-section` 仍输出 `校验通过.` 且 `exit=0`. 说明该要求只能靠 `SKILL.md` 规则与人工走查保证; 仓库测试 `tests/skill_creator/docs_contract.test.mjs` 只检查 skill-creator 自己的 `SKILL.md` 与文档文本, 不覆盖新产出的 skill.

结论: 三处规则在 `SKILL.md` 中均已写明且与实测流程一致; 按新建流程产出的样例带 `## 前提条件` 并通过校验, 缺该节的样例不会被校验脚本拦下, 交付前必须人工确认.

### 5.2 交互分支的指令级人工走查

时间: 2026-10-24 15:17 CST. 环境同前 (macOS arm64, Node.js `v26.12.1`, npm `12.2.1`). 本节仍是人工指令级走查, 没有启动真实客户端会话, 也没有真实用户答复; 做法是在 `/tmp` 副本中实际制造依赖缺失, 运行检查脚本取得真实阻断报告, 再按 `SKILL.md` `## 前提条件` 全节的前提检查与阻断规则, `## 脚手架与校验` 至 `## 交付说明` 各节的降级与交付规则, 以及 delta spec 的三个 scenario 逐项推演每种用户选择对应的决策与动作, 并实际执行其中可执行的部分. 下面的命令与输出为本机原样记录.

#### 走查用的真实阻断报告

在 `/tmp` 副本中制造依赖缺失, 仓库内 `skills/skill-creator/node_modules` 未被移动或改写:

```bash
cd /Users/yjydist/Code/skills
rm -rf /tmp/s52-walkthrough && mkdir -p /tmp/s52-walkthrough
rsync -a --exclude node_modules skills/skill-creator/ /tmp/s52-walkthrough/skill-creator/
ls -d /tmp/s52-walkthrough/skill-creator/node_modules 2>&1
cd /tmp/s52-walkthrough/skill-creator
node scripts/check_dependencies.mjs; echo "exit=$?"
```

真实输出 (五段齐全并保留原始错误):

```text
ls: /tmp/s52-walkthrough/skill-creator/node_modules: No such file or directory
缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference
检测结果: 未发现可导入的依赖包; yaml 导入失败, 原始错误: Cannot find package 'yaml' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/check_dependencies.mjs; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/check_dependencies.mjs; decode-named-character-reference 导入失败, 原始错误: Cannot find package 'decode-named-character-reference' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/check_dependencies.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/s52-walkthrough/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时 validate_skill.mjs 等脚本无法运行, 机械校验需要改为人工核对.
exit=1
```

该报告对应 `SKILL.md` `## 前提条件` 中"执行脚本或产出文件前逐项检查"一条 (任一项不满足时停止并按五段报告) 与"报告后询问用户选择修复后继续, 授权降级或终止"一条. 此时尚未执行安装, 尚未运行脚手架, 也尚未产出任何 skill 目录.

#### 用户授权降级

逐项核对结果:

+ 缺少项: `yaml`, `mdast-util-from-markdown`, `decode-named-character-reference` 三个第三方依赖, 原始错误见上节报告.
+ 已定义的降级路径: `SKILL.md` `## 脚手架与校验` 中"环境缺少 Node.js 或依赖时"一条规定, 用户授权降级后手工创建目录和最小 frontmatter (见 `references/spec.md` 的最小示例), 再按 `## 验证` 小节第 1 条的人工核对步骤逐项核对. 因此本分支不执行 `npm install`, 不运行 `init_skill.mjs`, 不运行 `validate_skill.mjs`.
+ 实际动作: 在 `/tmp/s52-walkthrough/degraded-sample` 手工创建 `SKILL.md`, 含最小 frontmatter, 正文, `## 前提条件` 与实际流程. 人工核对命令与结果:

```bash
cd /tmp/s52-walkthrough/degraded-sample
awk 'NR==2' SKILL.md; awk 'NR==3' SKILL.md; basename "$PWD"
awk 'NR>4 && NF' SKILL.md | wc -l
grep -c 'TODO\|<.*名称.*>\|<可执行' SKILL.md
grep -oE '\]\([^)]*\)|href="[^"]*"|src="[^"]*"' SKILL.md | wc -l
LC_ALL=C grep -c $'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]' SKILL.md
grep -n '^## 前提条件$' SKILL.md
```

```text
name: "degraded-sample"
description: "在用户要求统计仓库内 Markdown 文件数量并输出汇总表时使用. 只做本地文件计数, 不联网."
degraded-sample
10
0
0
0
10:## 前提条件
```

  核对结论: `name` 与目录名一致, `description` 非空, 正文 10 个非空行, 无 TODO 或占位符, 无本地链接与控制字符, `## 前提条件` 位于第 10 行. 这些项目只经过人工核对, 没有机械校验.
+ 跳过的步骤: 依赖安装 (`SKILL.md` `## 前提条件` 中"依赖缺失时的修复命令"一条的 `npm install` 命令), `init_skill.mjs` 脚手架, `validate_skill.mjs` 机械校验 (含 `--strict`), 链接与可移植性等脚本检查, 样例 skill 的触发语料与独立会话试跑 (`## 验证` 小节).
+ 未验证项: frontmatter 类型与长度, 链接存在性与可移植性, 未引用文件, 正文行数等本应由脚本判定的项目均未机械验证; 样例 skill 的触发语料与独立会话也未执行.
+ 对产物的影响: 产物只有人工核对的 `SKILL.md`, 没有脚手架生成的 `scripts/`, `references/`, `assets/`; 交付说明必须按 `SKILL.md` `## 验证` 中"未运行校验脚本时"一条与 `## 交付说明` 中"说明前提检查结果"一条写明机械校验未运行的原因, 逐项列出人工核对项, 并记录缺少项, 跳过步骤, 未验证项和影响.
+ 确认不会把依赖缺失当成校验通过: 在降级产物上实际运行校验脚本仍以 1 退出并重新阻断, 未输出 `校验通过.`:

```bash
node /tmp/s52-walkthrough/skill-creator/scripts/validate_skill.mjs /tmp/s52-walkthrough/degraded-sample; echo "exit=$?"
```

```text
错误: 无法加载 Node.js 依赖 (yaml, mdast-util-from-markdown, decode-named-character-reference).
缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference
检测结果: 未发现可导入的依赖包; yaml 导入失败, 原始错误: Cannot find package 'yaml' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/validate_skill.mjs; mdast-util-from-markdown 导入失败, 原始错误: Cannot find package 'mdast-util-from-markdown' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/validate_skill.mjs; decode-named-character-reference 导入失败, 原始错误: Cannot find package 'decode-named-character-reference' imported from /private/tmp/s52-walkthrough/skill-creator/scripts/validate_skill.mjs
要求: 需要能从本脚本位置导入 yaml, mdast-util-from-markdown, decode-named-character-reference, 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.
修复命令: npm install --no-save --no-package-lock --prefix /private/tmp/s52-walkthrough/skill-creator yaml mdast-util-from-markdown decode-named-character-reference
影响: 依赖缺失时无法执行机械校验, 需要改为人工核对或等待安装.
exit=1
```

因此授权降级只改变产出方式, 不改变前提缺失的判定: 机械校验的结果仍是阻断, 不能记作通过.

#### 没有降级路径

+ 前提: 缺失项没有 `SKILL.md` 已定义的降级路径. `SKILL.md` `## 脚手架与校验` 中"环境缺少 Node.js 或依赖时"一条只为缺少 Node.js 或第三方依赖定义手工降级; 本 skill 当前没有外部程序要求 (`SKILL.md` `## 前提条件` 中"无其他外部程序与认证要求"一条的检查命令为 `true`), 因此用一个产出 skill 声明外部程序 `asciidoctor` 作为缺失项来走查该分支.
+ 实际探测: `command -v asciidoctor` 无输出, `exit=1`. 按 `SKILL.md` `## 前提条件` 中 npm 一条与"执行脚本或产出文件前逐项检查"一条, 外部程序缺失归为外部程序缺失, 报告仍按五段填写, 修复命令由执行者按目标平台给出.
+ 决策与动作: 按 `SKILL.md` `## 前提条件` 中"没有降级路径时只提供修复和终止"一条, 报告后只提供"修复后继续"与"终止"两个选项, 不提供"授权降级"; 不手工创建目录, 不写最小 frontmatter, 不产出任何文件, 等待用户选择. 该分支没有自动化输出选项列表, 以上为按规则文字与实际缺失探测逐项核对的结论.

#### 用户未答复

+ 决策与动作: 报告后不继续产出, 不执行修复命令, 不默认降级, 保持停止等待用户选择, 对应 `SKILL.md` `## 前提条件` 中"用户未选择前不继续, 不默认降级"一句与 delta spec 的"用户未答复" scenario.
+ 实际证据: 运行 `check_dependencies.mjs` 后未执行 `npm install` 或任何脚手架, 当时 `/tmp/s52-walkthrough` 只有副本目录:

```text
total 0
drwxr-xr-x@    3 yjydist  wheel     96 Oct 24 15:16 .
drwxrwxrwt  1006 root     wheel  32192 Oct 24 15:16 ..
drwxr-xr-x@    5 yjydist  staff    160 Oct 24 10:27 skill-creator
```

  上节的 `degraded-sample` 是在明确选择"授权降级"之后才创建, 不是默认路径产生的.

场景覆盖说明: 以上三条交互分支已完成指令级人工走查, 记为"已人工走查 (指令级), 无自动化/真实会话", 不再归入"未验证/不计入覆盖":

+ 用户授权降级: 已实际制造依赖缺失, 取得五段式阻断报告, 按 `SKILL.md` `## 脚手架与校验` 中"环境缺少 Node.js 或依赖时"一条与 `## 交付说明` 中"说明前提检查结果"一条手工产出最小 `SKILL.md` 并逐项人工核对, 同时实测降级后机械校验仍以 1 退出. 证据见上文的命令, 输出与 `SKILL.md` 小节引用; 没有真实用户授权, 也没有真实会话.
+ 没有降级路径: 已按 `SKILL.md` `## 前提条件` 中"没有降级路径时只提供修复和终止"一条与外部程序缺失探测逐项核对, 结论是只提供修复后继续与终止, 不提供降级选项. 该分支的选项列表没有脚本生成, 属于指令级走查; 没有真实客户端会话.
+ 用户未答复: 已核对报告后保持停止, 不继续产出, 不默认降级, 并用阻断后目录中未出现产物作为实际证据. 没有真实用户答复, 也没有真实会话.

这三条现在记为"已人工走查 (指令级), 无自动化/真实会话"; 它们与上文实际执行过的前提检查路径分开记录, 不据此认为真实会话中的对应 scenario 已通过.

未验证项:

+ 未启动独立客户端会话, 也未对照无 skill 或旧版本结果; 本项按 `SKILL.md` 的 `## 验证` 小节属于人工判断, 标注为未自动验证.
+ 交互/流程类分支已做指令级人工走查, 但未启动真实客户端会话, 也没有真实用户答复: "用户授权降级", "没有降级路径", "用户未答复" 三个 scenario 的决策与动作已按 `SKILL.md` `## 前提条件` 全节与 `## 脚手架与校验` 至 `## 交付说明` 各节的规则和真实阻断输出逐项核对, 并实际执行了阻断与降级产物; 仍没有自动化覆盖, 也没有真实会话中的用户选择记录, 详见上面的场景覆盖说明.
+ skill-creator 自身的 12 条触发语料已按 [使用文档](../../../docs/skill-creator.md#触发语料自检) 完成人工复核 (12/12 与独立复核一致), 但未在真实客户端试跑; 本次走查所用的样例新建 skill ("统计仓库内 Markdown 文件数量") 没有准备与运行触发语料 (正例, 负例), 它的触发定位未做自动验证. 这两件事分开记录, 不能据此认为本 skill 的触发从未验证.
+ 改进现有 skill 与交付说明两处只做了规则核对, 没有对真实 skill 执行改进流程, 也没有真实交付说明可对照.
+ 降级路径 (`SKILL.md` 的 `## 脚手架与校验` 小节) 已在 `/tmp/s52-walkthrough` 副本中按授权降级分支实际执行: 阻断后手工创建最小 frontmatter 的样例, 机械校验实际以 1 退出并再次阻断, 因此降级产物只经过人工核对. 该执行是为了走查 scenario 而构造, 不是真实用户授权, 也没有真实客户端会话.

覆盖汇总: 18 个 scenario 中, 其余项有自动化测试或文档契约断言; 5 个非自动化: `用户授权降级`, `没有降级路径`, `用户未答复` 为指令级人工走查, `首次运行` 与 `安装失败` 为 5.1 的真实命令记录.

### 与 tasks.md 的对应

+ 5.1 "逐条执行检查命令通过": Node 版本, `npm -v`, 依赖可导入三条命令实测退出码均为 0, 见上表.
+ 5.1 "临时改名 `node_modules` 后能阻断并输出五段式报告": 在 `/tmp/s10-copy/skill-creator` 中移动依赖目录后两个脚本均以 1 退出, `check_dependencies.mjs` 输出完整五段, `validate_skill.mjs` 保留五段并加阻断说明.
+ 5.1 "首次运行" 场景的安装后重检: 在 `/tmp/w5-install/skill-creator` 中从无依赖目录开始执行修复命令, 安装以 0 退出, 按 `SKILL.md` `## 前提条件` 中"修复命令执行成功后重新执行本节的全部前提检查"一条的顺序重检全部通过, 见 "5.1 前提检查: 首次运行的成功安装与重检".
+ 5.1 "包缺失" 场景的安装后重检: 在 `/tmp/w51-partial/skill-creator` 中保留 `node_modules` 但只链入 `yaml` 与 `decode-named-character-reference`, 缺少 `mdast-util-from-markdown` 时检查以 1 退出且只报告该包; 执行修复命令以 0 退出, 重检 `check_dependencies.mjs` 与 `validate_skill.mjs` 均以 0 退出, 见 "5.1 前提检查: 包缺失的安装与重检".
+ 5.2 "用一条新建请求走查流程, 产出的 `SKILL.md` 包含该节": 以 "统计仓库内 Markdown 文件数量" 为样例请求, 由 `init_skill.mjs` 生成带 `## 前提条件` 占位节的骨架后替换占位内容并删除 TODO, 校验通过, 该节在第 10 行.
+ 5.2 的交互类分支 ("用户授权降级", "没有降级路径", "用户未答复") 已做指令级人工走查: 在 `/tmp/s52-walkthrough` 副本中取得真实阻断报告, 按 `SKILL.md` 规则逐项推演三种选择的决策与动作, 并实际执行授权降级后的手工产物与再次阻断. 三个 scenario 计入"已人工走查 (指令级)", 仍不包含真实客户端会话或自动化覆盖, 该限制见本节未验证项.
