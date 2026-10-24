#!/usr/bin/env bash
# 重建差分验证使用的 32 个 fixture, 说明见同目录 verification-fixtures.md.
#
# 用法: verification-fixtures.sh <目标目录>
# 目标目录必须可写; 已存在的同名 fixture 目录会被覆盖.

set -euo pipefail

root="${1:?用法: verification-fixtures.sh <目标目录>}"

# 写入 frontmatter 前 3 行, 之后的用例自行补 frontmatter 尾部与正文.
new_skill() {
  local name="$1"
  mkdir -p "$root/$name"
  printf -- '---\nname: %s\ndescription: 用于差分验证的示例 skill, 说明该 skill 的用途.\n' \
    "$name" > "$root/$name/SKILL.md"
}

new_skill valid-skill
cat >> "$root/valid-skill/SKILL.md" <<'EOF'
---

# 标题

正文内容.
EOF

new_skill empty-body
cat >> "$root/empty-body/SKILL.md" <<'EOF'
---
EOF

new_skill long-body
{
  cat <<'EOF'
---

# 标题

EOF
  for i in $(seq 1 504); do
    printf '第 %d 行正文.\n' "$i"
  done
} >> "$root/long-body/SKILL.md"

new_skill unknown-field
cat >> "$root/unknown-field/SKILL.md" <<'EOF'
foo: bar
---

# 标题

正文.
EOF

new_skill broken-link
cat >> "$root/broken-link/SKILL.md" <<'EOF'
---

# 标题

[缺失](missing.md)
EOF

new_skill html-unquoted
cat >> "$root/html-unquoted/SKILL.md" <<'EOF'
---

# 标题

<a href=missing.md>链接</a>
EOF

# 跨行的行内 HTML 标签: 属性写在标签的下一行. Node 按属性所在行报告缺失目标,
# Python 基线的标签正则不跨行, 因此漏报.
new_skill multiline-html-tag
cat >> "$root/multiline-html-tag/SKILL.md" <<'EOF'
---

# 标题

<a
href="missing.md">x</a>

<a
href="ok.md">y</a>
EOF
printf '# ok\n' > "$root/multiline-html-tag/ok.md"

new_skill invalid-yaml
printf -- '---\nname: invalid-yaml\ndescription: [未闭合\n' > "$root/invalid-yaml/SKILL.md"
cat >> "$root/invalid-yaml/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF

new_skill missing-reference
cat >> "$root/missing-reference/SKILL.md" <<'EOF'
---

# 标题

[文本][ref]
EOF

# name-mismatch 的 name 必须是 other-name, 与目录名不同.
mkdir -p "$root/name-mismatch"
printf -- '---\nname: other-name\ndescription: 用于差分验证的示例 skill, 说明该 skill 的用途.\n' \
  > "$root/name-mismatch/SKILL.md"
cat >> "$root/name-mismatch/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF

new_skill code-block-link
cat >> "$root/code-block-link/SKILL.md" <<'EOF'
---

# 标题

```
[缺失](missing.md)
```

行内 `[缺失](missing2.md)` 与 HTML `<!-- [x](missing3.md) -->`.
EOF

# 列表项内的原始 HTML 块: micromark 把该块判为块级 HTML, Python 基准仍扫描其中的链接.
new_skill list-item-html-block
cat >> "$root/list-item-html-block/SKILL.md" <<'EOF'
---

- <div>
  [缺失](references/missing.md)
  </div>
EOF

new_skill pycache-files
cat >> "$root/pycache-files/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF
mkdir -p "$root/pycache-files/scripts/__pycache__"
printf 'x\n' > "$root/pycache-files/scripts/foo.pyc"
printf 'x\n' > "$root/pycache-files/scripts/__pycache__/x.cpython-311.pyc"

new_skill unreferenced
cat >> "$root/unreferenced/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF
mkdir -p "$root/unreferenced/references" "$root/unreferenced/scripts"
printf '# Note\n' > "$root/unreferenced/references/note.md"
printf 'print(1)\n' > "$root/unreferenced/scripts/helper.py"

new_skill dependency-dirs
cat >> "$root/dependency-dirs/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF
mkdir -p "$root/dependency-dirs/scripts/site-packages" \
  "$root/dependency-dirs/scripts/vendor" \
  "$root/dependency-dirs/scripts/venv"
printf 'v\n' > "$root/dependency-dirs/scripts/site-packages/pkg.py"
printf 'v\n' > "$root/dependency-dirs/scripts/vendor/lib.py"
printf 'v\n' > "$root/dependency-dirs/scripts/venv/mod.py"

new_skill links-portability
cat >> "$root/links-portability/SKILL.md" <<'EOF'
---

# 标题

[绝对](/etc/hosts) [Windows](C:\\tmp\\a.md) [越界](../../outside.md) [大小写](real.md)
EOF
printf '# Real\n' > "$root/links-portability/Real.md"

mkdir -p "$root/duplicate-keys"
printf -- '---\nname: duplicate-keys\nname: duplicate-keys\n' > "$root/duplicate-keys/SKILL.md"
printf -- 'description: 用于差分验证的示例 skill, 说明该 skill 的用途.\n' >> "$root/duplicate-keys/SKILL.md"
cat >> "$root/duplicate-keys/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF

new_skill yaml11-scalars
printf -- '---\nname: yaml11-scalars\ndescription: yes\n' > "$root/yaml11-scalars/SKILL.md"
cat >> "$root/yaml11-scalars/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF

# `<<` 合并键: YAML 1.1 展开成字符串字段, YAML 1.2 core schema 按普通键处理,
# `metadata.<<` 的值是映射, 因此 Node 报值必须是字符串.
new_skill yaml-merge-key
printf -- 'metadata:\n  <<: &defaults\n    author: example-org\n    version: "1.0"\n' \
  >> "$root/yaml-merge-key/SKILL.md"
cat >> "$root/yaml-merge-key/SKILL.md" <<'EOF'
---

# 标题

正文.
EOF

# 裸控制字符: 0x01 (SOH) 与 0x7f (DEL) 直接出现在链接目标中.
new_skill control-chars
printf -- '---\n\n# 标题\n\n[文件](a\001b.md) [删除符](c\177d.md)\n' \
  >> "$root/control-chars/SKILL.md"

# 引用式定义目标含裸控制字符: 控制字符使 CommonMark 不把该行解析为定义.
new_skill control-chars-definition
printf -- '---\n\n[r]: a\001b.md\n' >> "$root/control-chars-definition/SKILL.md"

# 正文与标题里的 `[x]:` 是普通文本, 不是块首定义: 目标中的控制字符不报错.
new_skill midline-definition-text
printf -- '---\n\n# 标题\n\n正文中的 [a]: b\001.md 只是文本.\n\n## 小标题 [b]: c\002.md\n' \
  >> "$root/midline-definition-text/SKILL.md"

# 段落续行不是引用式定义: 定义不能打断段落, `正文` 之后的行首 `[ref]: 目标`
# 与列表项 `+ 项目文字` 之后的 `[list]: 目标` 都只是续行文本, 控制字符不报错;
# 段落之外的 `[文本][ref]` 仍报定义缺失 (行号取引用处).
new_skill paragraph-continuation-definition
printf -- '---\n\n# 标题\n\n正文\n[ref]: a\001b.md\n\n[文本][ref]\n\n+ 项目文字\n  [list]: c\002d.md\n' \
  >> "$root/paragraph-continuation-definition/SKILL.md"

# 跨行目标: 行内链接在开括号后, 引用式定义在冒号后各换行一次再写目标.
# 控制字符按链接/定义的起始行报告, 且不额外报目标或定义缺失.
new_skill multiline-control-chars
printf -- '---\n\n# 标题\n\n[文件](\n  a\001b.md)\n\n[r]:\n  c\002d.md\n\n[r]\n' \
  >> "$root/multiline-control-chars/SKILL.md"

# 非法 UTF-8: 正文含单个 0xff 字节.
new_skill invalid-utf8
printf -- '---\n\n# 标题\n\n正文\377内容.\n' >> "$root/invalid-utf8/SKILL.md"

# 反斜杠转义的 HTML 标签: CommonMark 中 \< 与 \> 是字面字符, 不构成 HTML 标签.
new_skill escaped-html
cat >> "$root/escaped-html/SKILL.md" <<'EOF'
---

# 标题

\<a href="missing.md">x\</a>
EOF

# 同一行两个指向同一缺失目标的链接.
new_skill duplicate-same-line
cat >> "$root/duplicate-same-line/SKILL.md" <<'EOF'
---

# 标题

[a](missing.md) [b](missing.md)
EOF

# 同一行指向同一文件的实体/百分号混写目标: 解码后都是 a&b.md.
new_skill mixed-encoded-same-line
cat >> "$root/mixed-encoded-same-line/SKILL.md" <<'EOF'
---

# 标题

[一](a&b.md) [二](a&amp;b.md) [三](a%26b.md)
EOF

# 片段, 查询与纯锚点中的裸控制字符: 0x01, 0x02, 0x03.
new_skill fragment-control-chars
printf -- '---\n\n# 标题\n\n[片段](real.md#bad\001x) [查询](real.md?q=\002) [锚点](#bad\003y)\n' \
  >> "$root/fragment-control-chars/SKILL.md"
printf '# Real\n' > "$root/fragment-control-chars/real.md"

# 无分号实体: legacy 命名实体 `&amp` 与数字实体 `&#65` 按 HTML 规则解码,
# 非 legacy 名称 `&hellip` 省略分号时保留原文.
new_skill entity-legacy
cat >> "$root/entity-legacy/SKILL.md" <<'EOF'
---

# 标题

读取 [实体](a&ampb.md) 与 [数字](a&#65.md) 与 [数字b](a&#65b.md).

<a href="a&ampb.md">实体</a>

<img src="a&#65.md">

对照 [未解码](a&hellipb.md).
EOF
printf '# 1\n' > "$root/entity-legacy/a&b.md"
printf '# 2\n' > "$root/entity-legacy/aA.md"
printf '# 3\n' > "$root/entity-legacy/aAb.md"
printf '# 4\n' > "$root/entity-legacy/a…b.md"

# 双次实体: `&amp;amp;` 在 Markdown 链接, 引用式定义与 HTML 属性中均只解码
# 一次, 得到文件名 `a&amp;b.md`; 反向用例 `only-a&amp;b.md` 只解码成
# `only-a&b.md`, 用于确认没有过度解码.
new_skill double-encoded-entity
cat >> "$root/double-encoded-entity/SKILL.md" <<'EOF'
---

# 标题

[双实体](a&amp;amp;b.md) 与 [定义][r]

[r]: a&amp;amp;b.md

<a href="a&amp;amp;b.md">属性</a>

[反向](only-a&amp;b.md)
EOF
printf '# x\n' > "$root/double-encoded-entity/a&amp;b.md"

# 跨行链接文本: 标签在换行处断开, 目标仍在同一段落内按原有规则扫描.
# 裸控制字符按 `[` 所在行报告, 不额外报目标不存在; 第二个跨行标签指向存在的文件.
new_skill multiline-label-control-chars
printf -- '---\n\n# 标题\n\n[多行\n标签](a\001b.md)\n\n[正常\n标签](real.md)\n' \
  >> "$root/multiline-label-control-chars/SKILL.md"
printf '# Real\n' > "$root/multiline-label-control-chars/real.md"

printf '已生成 32 个 fixture 到 %s\n' "$root"
