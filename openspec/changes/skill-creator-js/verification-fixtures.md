# 差分 fixture 清单

## 目的

[verification.md](verification.md) 中范围二的 fixture 原先只存在于一个临时目录 (历史记录中写作 `/tmp/s5-fixtures`, 该目录已清理, 仅作历史位置说明), 清理后无法复现. 本文逐条记录每个 fixture 的目录名, 文件内容, 预期退出码与差异类别, 并附生成脚本 [verification-fixtures.sh](verification-fixtures.sh); 仅凭仓库内文件即可在任意目录重建同一组 fixture, 本文统一写作 `/tmp/skill-creator-fixtures`.

## 重建方法

```bash
cd /Users/yjydist/Code/skills
bash openspec/changes/skill-creator-js/verification-fixtures.sh /tmp/skill-creator-fixtures
```

脚本的最后一个参数是 fixture 输出目录, 任意可写目录均可; 本文统一写作 `/tmp/skill-creator-fixtures`.

脚本接受一个目标目录, 在其中创建 32 个 fixture 子目录, 每个子目录是一个独立 skill. 重复执行会覆盖同名目录内容; 不会删除目标目录下其他文件.

本轮用该脚本重建全部 32 个用例; 用例的类别与预期输出以本文的用例一览与 [verification.md](verification.md) 的差异记录为准; 本轮补充的用例清单见 [verification.md](verification.md) 范围二开头的权威清单, 本文不再重复枚举; 当前共 32 个用例, 48 个文件.

行内 HTML 标签的 2048 字符上限与标签/注释识别边界 (超限标签, 未闭合标签, 行内与行首未闭合注释) 由 `tests/skill_creator/links.test.mjs` 的用例覆盖, 不在本文的 32 个 fixture 内.

## 公共 frontmatter

除特别说明外, 每个 `SKILL.md` 的前三行为:

```yaml
---
name: <目录名>
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
```

之后按用例追加 frontmatter 尾部与正文. 下文中的代码块均为文件原文, 未列出的文件不存在.

## 用例一览

退出码与输出由本轮实际运行记录. "一致" 表示标准输出与标准错误逐字节相同, 且退出码相同.

| 目录 | 关键文件 | Python 退出码 | Node 退出码 | 结果 | 差异类别 |
| --- | --- | --- | --- | --- | --- |
| `valid-skill` | `SKILL.md` | 0 | 0 | 一致 | 无 |
| `empty-body` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `long-body` | `SKILL.md` | 0 | 0 | 一致 | 无 |
| `unknown-field` | `SKILL.md` | 0 | 0 | 一致 | 无 |
| `broken-link` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `duplicate-same-line` | `SKILL.md` | 1 | 1 | 错误数不同 | G |
| `mixed-encoded-same-line` | `SKILL.md` | 1 | 1 | 错误数不同 | G |
| `html-unquoted` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `multiline-html-tag` | `SKILL.md`, `ok.md` | 0 | 1 | 退出码与输出均不同 | I |
| `escaped-html` | `SKILL.md` | 1 | 0 | 退出码与输出均不同 | F |
| `invalid-yaml` | `SKILL.md` | 1 | 1 | 文案不同 | B |
| `missing-reference` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `name-mismatch` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `code-block-link` | `SKILL.md` | 0 | 0 | 一致 | 无 |
| `list-item-html-block` | `SKILL.md` | 1 | 0 | 退出码与输出均不同 | E |
| `pycache-files` | `SKILL.md`, `scripts/foo.pyc`, `scripts/__pycache__/x.cpython-311.pyc` | 0 | 0 | 一致 | 无 |
| `unreferenced` | `SKILL.md`, `references/note.md`, `scripts/helper.py` | 0 | 0 | 一致 | 无 |
| `dependency-dirs` | `SKILL.md`, `scripts/site-packages/pkg.py`, `scripts/vendor/lib.py`, `scripts/venv/mod.py` | 0 | 0 | 输出不同 | C |
| `links-portability` | `SKILL.md`, `Real.md` | 1 | 1 | 一致 | 无 |
| `duplicate-keys` | `SKILL.md` | 0 | 1 | 退出码与输出均不同 | A |
| `yaml11-scalars` | `SKILL.md` | 1 | 0 | 退出码与输出均不同 | A |
| `yaml-merge-key` | `SKILL.md` | 0 | 1 | 退出码与输出均不同 | J |
| `control-chars` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `control-chars-definition` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `midline-definition-text` | `SKILL.md` | 0 | 0 | 一致 | 无 |
| `paragraph-continuation-definition` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `multiline-control-chars` | `SKILL.md` | 1 | 1 | 一致 | 无 |
| `multiline-label-control-chars` | `SKILL.md`, `real.md` | 1 | 1 | 一致 | 无 |
| `fragment-control-chars` | `SKILL.md`, `real.md` | 0 | 1 | 退出码与输出均不同 | H |
| `entity-legacy` | `SKILL.md`, `a&b.md`, `aA.md`, `aAb.md`, `a…b.md` | 1 | 1 | 一致 | 无 |
| `double-encoded-entity` | `SKILL.md`, `a&amp;b.md` | 1 | 1 | 一致 | 无 |
| `invalid-utf8` | `SKILL.md` | 1 | 1 | 文案不同 | D |

合计 32 个: 20 个完全一致, 12 个存在差异; 差异分别属于 A, B, C, D, E, F, G, H, I, J 十类.

差异类别与 [verification.md](verification.md) 的编号对应:

+ A: YAML 1.2 语义与 PyYAML 的差异.
+ B: 第三方 YAML 库的解析错误文案不同.
+ C: Node 实现有意扩展的依赖目录忽略列表.
+ D: 非法 UTF-8 由不同解码器报错, 文案不同.
+ E: 列表项内原始 HTML 块的判定差异; JS 按当前 spec 跳过块内链接, Python 基线仍检查.
+ F: 反斜杠转义 HTML 标签的判定差异; JS 按 CommonMark 不把 `\<a ...>` 当作标签, Python 基线仍按 HTML 属性提取链接.
+ G: 同一行同一目标的重复链接; Node 按解码后的完整目标 (含片段与查询) 去重, Python 基线逐条报告.
+ H: 片段, 查询与纯锚点中的控制字符; Node 按当前 spec 检查完整链接目标, Python 基线拆分片段与查询后只检查路径, 纯锚点直接跳过.
+ I: 跨行行内 HTML 标签的属性目标; Node 按当前 spec 让标签扫描跨行并按属性所在行报告, Python 基线的属性正则在换行处放弃, 仍漏报.
+ J: `<<` 合并键; PyYAML 按 YAML 1.1 展开合并键后只看到被合并的字符串字段, YAML 1.2 core schema 把 `<<` 当普通键, `metadata.<<` 的值是映射, Node 报值必须是字符串.

## 各用例内容与预期输出

### valid-skill

```markdown
---
name: valid-skill
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

正文内容.
```

预期: 两侧均输出 `校验通过.`, 退出码 0.

### empty-body

```markdown
---
name: empty-body
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---
```

预期: 两侧均输出 `错误: SKILL.md: 正文不能为空`, 退出码 1.

### long-body

frontmatter 与公共模板相同, 正文为 `# 标题`, 空行, 然后 `第 1 行正文.` 到 `第 504 行正文.` 共 504 行, 文件总计 511 行. 脚本用循环生成, 不逐行列出.

预期: 两侧均输出 `警告: SKILL.md: 正文超过 500 行, 建议把细节移入 references/ 或 scripts/` 与 `校验通过, 有 1 个警告.`, 退出码 0.

### unknown-field

```markdown
---
name: unknown-field
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
foo: bar
---

# 标题

正文.
```

预期: 两侧均输出 `警告: SKILL.md:4: 非标准字段: foo` 与 `校验通过, 有 1 个警告.`, 退出码 0; 加 `--strict` 时退出码 1 且输出 `严格模式下警告视为错误: 1 个警告.`.

### broken-link

```markdown
---
name: broken-link
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

[缺失](missing.md)
```

预期: 两侧均输出 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 退出码 1.

### duplicate-same-line

```markdown
---
name: duplicate-same-line
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

[a](missing.md) [b](missing.md)
```

预期: 差异类别 G. 同一行有两个指向同一缺失目标的链接.

+ Python 逐条报告, 输出两行 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 随后 `校验失败: 2 个错误, 0 个警告.`, 退出码 1.
+ Node 按解码后的目标去重, 只输出一行 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1.

Node 的去重键是解码后的完整目标 (含片段与查询), Markdown 链接, 行内 HTML 链接与引用定义共用该键; 其他行上的同一目标或解码后不同的目标仍各报一次.

### mixed-encoded-same-line

```markdown
---
name: mixed-encoded-same-line
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

[一](a&b.md) [二](a&amp;b.md) [三](a%26b.md)
```

预期: 差异类别 G. 同一行三个链接分别用裸字符, 实体与百分号编码指向同一目标 `a&b.md`.

+ Python 逐条报告, 输出三行 `错误: SKILL.md:8: 本地链接目标不存在: a&b.md`, 随后 `校验失败: 3 个错误, 0 个警告.`, 退出码 1.
+ Node 按解码后的目标去重, 只输出一行 `错误: SKILL.md:8: 本地链接目标不存在: a&b.md`, 随后 `校验失败: 1 个错误, 0 个警告.`, 退出码 1.

Python 基线按原始字面目标比较, 三种写法互不相等; Node 先按本地链接规则解码实体与百分号编码, 再以解码后的完整目标去重.

### html-unquoted

```markdown
---
name: html-unquoted
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

<a href=missing.md>链接</a>
```

预期: 两侧均输出 `错误: SKILL.md:8: 本地链接目标不存在: missing.md`, 退出码 1.

### multiline-html-tag

跨行的行内 HTML 标签: 标签名与属性分处两行, 第一个标签的目标不存在, 第二个标签的目标存在:

```markdown
---
name: multiline-html-tag
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

<a
href="missing.md">x</a>

<a
href="ok.md">y</a>
```

另有 `ok.md`: `# ok`.

预期: 差异类别 I.

+ Python 基线在单行内匹配属性, 整个用例输出 `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.
+ Node 输出 `错误: SKILL.md:9: 本地链接目标不存在: missing.md` 与 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变. 行号 9 是 `href` 所在的续行, 不是标签起始行 8; 第二个标签的 `href="ok.md"` 目标存在, 不报错, 其文件也被该行内 HTML 链接直接引用, 因此不产生未引用文件警告.

### escaped-html

```markdown
---
name: escaped-html
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

\<a href="missing.md">x\</a>
```

预期: 差异类别 F.

+ Python 输出 `错误: SKILL.md:8: 本地链接目标不存在: missing.md` 与 `校验失败: 1 个错误, 0 个警告.`, 退出码 1.
+ Node 输出 `校验通过.`, 退出码 0; 加 `--strict` 时仍为 `校验通过.` 与退出码 0.

原因: CommonMark 中 `\<` 与 `\>` 是转义后的字面字符, 不会开始或结束 HTML 标签, 因此该行没有 HTML 属性可供提取. JS 按解析结果不检查; Python 基线用正则直接扫原文中的 `href="..."`, 仍会把它当成本地链接. 按当前 spec, Node 的行为正确.

### invalid-yaml

```markdown
---
name: invalid-yaml
description: [未闭合
---

# 标题

正文.
```

预期: 退出码均为 1, 前缀均为 `错误: SKILL.md:3: 无法解析 frontmatter: `, 但库文案不同 (差异类别 B):

+ Python: `expected ',' or ']', but got '<stream end>'`
+ Node: `Flow sequence in block collection must be sufficiently indented and end with a ]`

### missing-reference

```markdown
---
name: missing-reference
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

[文本][ref]
```

预期: 两侧均输出 `错误: SKILL.md:8: 引用式链接定义不存在: ref`, 退出码 1.

### name-mismatch

```markdown
---
name: other-name
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

正文.
```

目录名是 `name-mismatch`, frontmatter 的 `name` 是 `other-name`.

预期: 两侧均输出 `错误: SKILL.md:2: name 与父目录名不一致: other-name != name-mismatch`, 退出码 1.

### code-block-link

````markdown
---
name: code-block-link
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

```
[缺失](missing.md)
```

行内 `[缺失](missing2.md)` 与 HTML `<!-- [x](missing3.md) -->`.
````

预期: 两侧均输出 `校验通过.`, 退出码 0; 代码块, 行内代码与 HTML 注释内的链接都不检查.

### list-item-html-block

```markdown
---
name: list-item-html-block
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

- <div>
  [缺失](references/missing.md)
  </div>
```

预期: 差异类别 E, 属 JS 符合当前 spec 的行为.

+ Python 输出 `错误: SKILL.md:7: 本地链接目标不存在: references/missing.md` 与 `校验失败: 1 个错误, 0 个警告.`, 退出码 1.
+ Node 输出 `校验通过.`, 退出码 0.

原因: [references/spec.md](../../../skills/skill-creator/references/spec.md) 规定原始 HTML 块内的链接不检查. micromark 把列表项内从 `<div>` 开始的块判为块级 HTML, 该 `html` 节点的父节点是 `listItem`, Node 实现据此把整块加入屏蔽范围, 块内文本里的 Markdown 链接不再扫描. Python 基线只屏蔽行内代码, 代码块与 HTML 注释, 仍会检查块内文本中的链接, 属于该规则确立前的旧行为.

### pycache-files

`SKILL.md` 的正文为 `# 标题` 与 `正文.`. 另有:

+ `scripts/foo.pyc`: `x`
+ `scripts/__pycache__/x.cpython-311.pyc`: `x`

预期: 两侧均输出 `校验通过.`, 退出码 0; `.pyc` 与 `__pycache__` 被忽略.

### unreferenced

`SKILL.md` 的正文为 `# 标题` 与 `正文.`. 另有:

+ `references/note.md`: `# Note`
+ `scripts/helper.py`: `print(1)`

预期: 两侧均输出两条 `未被 SKILL.md 直接引用的文件` 警告与 `校验通过, 有 2 个警告.`, 退出码 0.

### dependency-dirs

`SKILL.md` 的正文为 `# 标题` 与 `正文.`. 另有内容均为 `v` 的三个文件:

+ `scripts/site-packages/pkg.py`
+ `scripts/vendor/lib.py`
+ `scripts/venv/mod.py`

预期: 退出码均为 0, 输出不同 (差异类别 C):

+ Python 只忽略隐藏路径与 `__pycache__`, 输出 3 条 `未被 SKILL.md 直接引用的文件` 警告与 `校验通过, 有 3 个警告.`
+ Node 忽略依赖目录, 输出 `校验通过.`

### links-portability

`SKILL.md` 正文第 8 行 (文件内是两条反斜杠):

```markdown
[绝对](/etc/hosts) [Windows](C:\\tmp\\a.md) [越界](../../outside.md) [大小写](real.md)
```

另有 `Real.md`: `# Real` (文件名首字母大写, 链接写作 `real.md`).

预期: 两侧均输出 1 个错误与 3 个警告, 退出码 1:

```text
错误: SKILL.md:8: 本地链接目标不存在: ../../outside.md
警告: SKILL.md:8: Windows 绝对路径不可移植: C:\tmp\a.md
警告: SKILL.md:8: 绝对路径链接不可移植: /etc/hosts
警告: SKILL.md:8: 链接路径大小写与磁盘不一致, 不可移植: real.md
校验失败: 1 个错误, 3 个警告.
```

### duplicate-keys

```markdown
---
name: duplicate-keys
name: duplicate-keys
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
---

# 标题

正文.
```

预期: 差异类别 A.

+ Python (YAML 1.1 语义, 后者覆盖前者) 输出 `校验通过.`, 退出码 0.
+ Node (`yaml` 包 `uniqueKeys` 默认开启) 输出 `错误: SKILL.md:3: 无法解析 frontmatter: Map keys must be unique`, 退出码 1.

### yaml11-scalars

```markdown
---
name: yaml11-scalars
description: yes
---

# 标题

正文.
```

预期: 差异类别 A.

+ Python 把 `yes` 解析为布尔值, 输出 `错误: SKILL.md:3: description 必须是字符串`, 退出码 1.
+ Node 按 YAML 1.2 把 `yes` 视为字符串, 输出 `校验通过.`, 退出码 0.

### yaml-merge-key

YAML 1.1 的合并键 `<<`:

```markdown
---
name: yaml-merge-key
description: 用于差分验证的示例 skill, 说明该 skill 的用途.
metadata:
  <<: &defaults
    author: example-org
    version: "1.0"
---

# 标题

正文.
```

预期: 差异类别 J.

+ Python 基准 (PyYAML, YAML 1.1 语义) 展开合并键, `metadata` 中只有 `author` 与 `version` 两个字符串字段, 输出 `校验通过.`, 退出码 0; 加 `--strict` 输出与退出码不变.
+ Node (`yaml`, YAML 1.2 core schema) 把 `<<` 当作普通键, `metadata.<<` 的值是映射, 输出 `错误: SKILL.md:4: metadata.<< 的值必须是字符串` 与 `校验失败: 1 个错误, 0 个警告.`, 退出码 1; 加 `--strict` 输出与退出码不变.

按 YAML 1.2 语义, Node 的行为正确, 该差异属于预期变更.

### control-chars

`SKILL.md` 的正文第 8 行在链接目标中直接写入裸控制字符: `a` 与 `b` 之间是 `0x01`, `c` 与 `d` 之间是 `0x7f`. 目录内没有对应目标文件.

预期: 两侧行为一致, 均为 2 个错误, 退出码 1:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: c\x7fd.md
校验失败: 2 个错误, 0 个警告.
```

加 `--strict` 时输出不变. 此前该用例两侧行为不同, 已在裸控制字符处理修复后消失; 见 [verification.md](verification.md) 的 "已复核的修复项".

### control-chars-definition

`SKILL.md` 的正文第 6 行是未引用的引用式定义, 目标中 `a` 与 `b` 之间直接写入裸控制字符 `0x01`:

```markdown
[r]: a<0x01>b.md
```

控制字符使 CommonMark 不把该行解析为定义, 因此需要在原始文本上单独扫描 `]:` 后的目标. 目录内没有对应目标文件.

预期: 两侧行为一致, 均为 1 个错误, 退出码 1:

```text
错误: SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\x01b.md
校验失败: 1 个错误, 0 个警告.
```

加 `--strict` 时输出不变. 本轮修复前 Node 输出 `校验通过.` 并退出 0; 正文若另有 `[文本][r]` 引用, 修复前 Node 误报 `引用式链接定义不存在: r`, 修复后只报这条控制字符错误.

### midline-definition-text

正文与标题中的 `[a]:` 是普通文本, 不是块首的引用式定义. `SKILL.md` 第 6 行的正文含 `[a]: b<0x01>.md`, 第 8 行的二级标题含 `[b]: c<0x02>.md`; 两处都不是定义, 目标中的裸控制字符不应报错. 目录内没有对应目标文件.

```markdown
# 标题

正文中的 [a]: b<0x01>.md 只是文本.

## 小标题 [b]: c<0x02>.md
```

预期: 两侧均输出 `校验通过.`, 退出码 0.

加 `--strict` 时输出与退出码不变. 本轮修复前 Node 的原始定义扫描只查找任意 `]:`, 把这两处行内文本误判为定义并各报一条控制字符错误; Python 基准按块首位置识别定义, 输出 `校验通过.` 并退出 0.

### paragraph-continuation-definition

引用式定义不能打断段落: 段落第一行之后的 `[标签]: 目标` 只是续行文本. 本用例同时覆盖两种续行: 正文段落第 8 行的 `正文` 之后, 第 9 行首是定义样文本; 列表项第 13 行的 `+ 项目文字` 之后, 第 14 行缩进两格是定义样文本. 两处目标各含裸控制字符 (`0x01`, `0x02`), 段落后另有对 `ref` 的引用, 目录内没有对应目标文件.

```markdown
# 标题

正文
[ref]: a<0x01>b.md

[文本][ref]

+ 项目文字
  [list]: c<0x02>d.md
```

预期: 两侧行为一致, 均为 1 个错误, 退出码 1. 两处续行都不报控制字符, 也不把 `ref` 登记为已定义, 因此第 11 行的引用报定义缺失:

```text
错误: SKILL.md:11: 引用式链接定义不存在: ref
校验失败: 1 个错误, 0 个警告.
```

加 `--strict` 时输出与退出码不变. 本轮修复前 Node 把这两处续行都当作定义, 输出 2 个控制字符错误 (第 9 行与第 14 行) 并吞掉定义缺失; Python 基准只报第 11 行的定义缺失, 列表项续行部分输出 `校验通过.`.

### multiline-control-chars

`SKILL.md` 的正文把目标写在下一行: 行内链接在 `(` 后换行, 引用式定义在 `:` 后换行, 续行缩进 2 个空格. 行内目标中 `a` 与 `b` 之间是裸控制字符 `0x01`, 定义目标中 `c` 与 `d` 之间是 `0x02`; 末尾用 `[r]` 引用该定义. 目录内没有对应目标文件.

```markdown
[文件](
  a<0x01>b.md)

[r]:
  c<0x02>d.md

[r]
```

预期: 两侧行为一致, 均为 2 个错误, 退出码 1:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
错误: SKILL.md:11: 本地链接目标包含 NUL 或控制字符: c\x02d.md
校验失败: 2 个错误, 0 个警告.
```

加 `--strict` 时输出不变. 行号是链接与定义的起始行, 不是目标所在的续行. 修复前两侧行为不同: Python 报上述两个错误并退出 1, Node 输出 `校验通过.` 并退出 0; 修复后 Node 与基准逐字节一致, 且不会额外报 `本地链接目标不存在` 或 `引用式链接定义不存在`.

### multiline-label-control-chars

`SKILL.md` 的正文让链接文本跨行: 第 8 行是 `[多行`, 第 9 行是 `标签](a<0x01>b.md)`, 控制字符 `0x01` 位于 `a` 与 `b` 之间; 空行之后是正常的跨行标签 `[正常` / `标签](real.md)`. 另有 `real.md`: `# Real`. 目录内没有 `a<0x01>b.md`.

```markdown
[多行
标签](a<0x01>b.md)

[正常
标签](real.md)
```

预期: 两侧行为一致, 均为 1 个错误, 退出码 1:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\x01b.md
校验失败: 1 个错误, 0 个警告.
```

加 `--strict` 时输出不变. 行号取 `[` 所在行, 不是目标所在的续行; 正常的跨行标签指向存在的文件, 两侧都通过. 修复前 Node 输出 `校验通过.` 并退出 0, 整个目标因标签跨行而未进入原始扫描; 修复后回溯跨行, 以空行为段落边界, 不设固定长度上限 (本次迁移早期的 Node 草稿 (未入库) 的 512 与 999 上限已移除), `]` 后目标仍按原有规则解析.

### fragment-control-chars

`SKILL.md` 的正文第 8 行在同一行放入三个链接, 控制字符分别位于片段, 查询与纯锚点中: `#` 后是 `0x01`, `?q=` 后是 `0x02`, 纯锚点的 `#` 后是 `0x03`:

```markdown
[片段](real.md#bad<0x01>x) [查询](real.md?q=<0x02>) [锚点](#bad<0x03>y)
```

另有 `real.md`: `# Real`.

预期: 差异类别 H, 属 Node 符合当前 spec 的行为. 当前 spec 要求控制字符检查覆盖完整链接目标, 含 `#` 后的片段与 `?` 后的查询, 纯锚点与仅含查询的目标也检查, 不因跳过存在性检查而豁免.

+ Python 基线拆分片段与查询后只检查路径存在性, 纯锚点直接跳过, 输出 `校验通过.`, 退出码 0; 加 `--strict` 时输出与退出码不变.
+ Node 输出 3 个错误, 退出码 1; 加 `--strict` 时输出与退出码不变:

```text
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: #bad\x03y
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: real.md#bad\x01x
错误: SKILL.md:8: 本地链接目标包含 NUL 或控制字符: real.md?q=\x02
校验失败: 3 个错误, 0 个警告.
```

三个错误按目标字符串排序输出, 与链接在行内的先后顺序不同.

### invalid-utf8

`SKILL.md` 的正文含一个 `0xff` 字节 (`正文` 与 `内容.` 之间), 文件不是合法 UTF-8.

预期: 退出码均为 1, 前缀均为 `错误: SKILL.md: 不是有效的 UTF-8 文本: `, 但解码器文案不同 (差异类别 D):

+ Python: `'utf-8' codec can't decode byte 0xff in position 119: invalid start byte`
+ Node: `The encoded data was not valid for encoding utf-8`

### entity-legacy

无分号实体: `SKILL.md` 的正文第 8 行同时出现 legacy 命名实体 `&amp` 与数字实体 `&#65` 的省略分号写法, 第 10 行与第 12 行分别用行内 HTML 属性重复同一写法, 第 14 行是不应被无分号解码的对照:

```markdown
读取 [实体](a&ampb.md) 与 [数字](a&#65.md) 与 [数字b](a&#65b.md).

<a href="a&ampb.md">实体</a>

<img src="a&#65.md">

对照 [未解码](a&hellipb.md).
```

目录内 `a&b.md`, `aA.md`, `aAb.md` 存在; 另有 `a…b.md`, 用来证明 `&hellip` 省略分号时不会被解码成 `…`.

预期: 两侧行为一致, 均为 1 个错误, 退出码 1:

```text
错误: SKILL.md:14: 本地链接目标不存在: a&hellipb.md
校验失败: 1 个错误, 0 个警告.
```

`a&ampb.md` 解码为 `a&b.md`, `a&#65.md` 解码为 `aA.md`, `a&#65b.md` 解码为 `aAb.md`; `a&hellipb.md` 中的 `&hellip` 是非 legacy 名称, 省略分号时保持原文, 因此报缺失. 行内 HTML 属性与 Markdown 链接走同一解码函数, 两侧结果相同.

### double-encoded-entity

双次实体: `SKILL.md` 的正文第 8 行是 Markdown 链接, 第 10 行是引用式定义, 第 12 行是行内 HTML 属性, 三者目标都是 `a&amp;amp;b.md`; 第 14 行是只应解码一次的反向用例:

```markdown
[双实体](a&amp;amp;b.md) 与 [定义][r]

[r]: a&amp;amp;b.md

<a href="a&amp;amp;b.md">属性</a>

[反向](only-a&amp;b.md)
```

目录内只有 `a&amp;b.md`.

预期: 两侧行为一致, 均为 1 个错误, 退出码 1:

```text
错误: SKILL.md:14: 本地链接目标不存在: only-a&b.md
校验失败: 1 个错误, 0 个警告.
```

`&amp;amp;` 只解码一次得到 `a&amp;b.md`, 三个来源都通过; `only-a&amp;b.md` 解码为 `only-a&b.md`, 目录中不存在, 因此报缺失. mdast 已按 CommonMark 解码带分号的字符引用, Node 对 mdast 目标只补解无分号实体, 不再整体解码一次; 行内 HTML 属性仍是原文, 只解码一次. 修复前 Node 会把第 8 与第 10 行错误地再解一次为 `a&b.md` 并报缺失.

## 复现命令

前提: Python 基准固定取基线提交 `ea69a2f`, 该提交之后 `HEAD` 不再包含 `validate_skill.py`. 首次复现需在仓库根目录准备解释器与 PyYAML: `python3 -m venv .venv && .venv/bin/pip install 'pyyaml==6.0.3'` (PyYAML 需为 6.x, 否则基准可能走内置解析器分支).

```bash
cd /Users/yjydist/Code/skills
mkdir -p /tmp/s5-oracle
git show ea69a2f:skills/skill-creator/scripts/validate_skill.py > /tmp/s5-oracle/validate_skill.py
bash openspec/changes/skill-creator-js/verification-fixtures.sh /tmp/skill-creator-fixtures
for dir in /tmp/skill-creator-fixtures/*/; do
  .venv/bin/python /tmp/s5-oracle/validate_skill.py "$dir"; echo "exit=$?"
  node skills/skill-creator/scripts/validate_skill.mjs "$dir"; echo "exit=$?"
done
```

代码块里生成命令的最后一个参数是 fixture 输出目录, 任意可写目录均可; 上面的 `/tmp/skill-creator-fixtures` 与 [verification.md](verification.md) 保持一致, 循环里的路径需随之同步.

本轮用上述脚本在临时目录重建全部 32 个用例并逐一运行两侧: 既有用例的类别不变; 本轮补充的用例清单见 [verification.md](verification.md) 范围二开头的权威清单, 各用例的结果与差异类别仍见上文用例一览与下文各用例小节, 合计 20 个一致, 12 个差异.
