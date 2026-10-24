import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

import { validateSkill } from "../../skills/skill-creator/scripts/validate_skill.mjs";
import {
  withTempDir,
  createSkill,
  VALIDATOR,
  run,
} from "./helpers.mjs";

function render(issues) {
  return issues.map((issue) => issue.render());
}

function filtered(issues, text) {
  return issues.filter((issue) => issue.message.includes(text));
}

test("本地链接目标不存在时报错并给出 SKILL.md 行号", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "正文 [断链](references/missing.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标不存在: references/missing.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("代码块和行内代码中的链接不检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "```markdown",
        "[围栏](references/fenced-missing.md)",
        "```",
        "",
        "~~~",
        "[波浪](references/tilde-missing.md)",
        "~~~",
        "",
        "`[行内](references/inline-missing.md)`",
        "",
        "    [缩进](references/indented-missing.md)",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("原始 HTML 块内的链接不检查, 行内 HTML 属性检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "<div>",
        "[缺失](references/block-missing.md)",
        '<a href="references/block-html-missing.md">x</a>',
        "</div>",
        "",
        '参考 <a href="references/html-missing.md">文档</a>.',
        '插图 <img src="references/img-missing.png"> 结束.',
        "参考 <a href=references/unquoted-html-missing.md>文档</a>.",
        "插图 <img src=references/unquoted-img-missing.png> 结束.",
        "",
        "<!-- [注释](references/comment-missing.md) -->",
        "",
      ].join("\n"),
    });
    assert.deepEqual(
      render(validateSkill(root).errors),
      [
        "SKILL.md:11: 本地链接目标不存在: references/html-missing.md",
        "SKILL.md:12: 本地链接目标不存在: references/img-missing.png",
        "SKILL.md:13: 本地链接目标不存在: references/unquoted-html-missing.md",
        "SKILL.md:14: 本地链接目标不存在: references/unquoted-img-missing.png",
      ]
    );
  }));

test("行内 HTML 属性扫描识别引号内的 >", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        '参考 <a title="a>b" href="references/quoted-missing.md">x</a>.',
        '参考 <a href="references/ok.md" title="x>y">y</a>.',
        "参考 <a href=references/unquoted-after-quote-missing.md>z</a>.",
        "",
      ].join("\n"),
      files: { "references/ok.md": "# ok\n" },
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/quoted-missing.md",
      "SKILL.md:8: 本地链接目标不存在: references/unquoted-after-quote-missing.md",
    ]);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("跨行行内 HTML 标签的属性目标按属性所在行检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "<a",
        'href="references/multiline-missing.md">x</a>',
        "",
        "<a",
        'href="references/ok.md">y</a>',
        "",
        "<img",
        '  title="说明"',
        '  src="references/multiline-img-missing.png">',
        "",
        "<a",
        '  title="跨行说明"',
        '  href="references/titled-missing.md">z</a>',
        "",
      ].join("\n"),
      files: { "references/ok.md": "# ok\n" },
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:7: 本地链接目标不存在: references/multiline-missing.md",
      "SKILL.md:14: 本地链接目标不存在: references/multiline-img-missing.png",
      "SKILL.md:18: 本地链接目标不存在: references/titled-missing.md",
    ]);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("行内 HTML 标签未超过 2048 字符上限时照常检查属性目标", () =>
  withTempDir((directory) => {
    // 标签总长 600 字符, 低于 readHtmlTagEnd 的 2048 字符上限.
    const prefix = '<a href="references/padded-missing.md" data-pad="';
    const tag = prefix + "x".repeat(600 - prefix.length - 2) + '">';
    assert.equal(tag.length, 600);
    const root = createSkill(directory, {
      body: "参考 " + tag + "x</a>.\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标不存在: references/padded-missing.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("行内 HTML 标签超过 2048 字符上限时按普通文本处理", () =>
  withTempDir((directory) => {
    // 标签总长 4119 字符, 超过 readHtmlTagEnd 的 2048 字符上限, 属性不被检查.
    const prefix = '<a href="references/missing.md" data-pad="';
    const tag = prefix + "x".repeat(4119 - prefix.length - 2) + '">';
    assert.equal(tag.length, 4119);
    const root = createSkill(directory, {
      body: "参考 " + tag + "x</a>.\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 0, cli.stdout);
    assert.equal(cli.stdout, "校验通过.\n");
  }));

test("未闭合的行内 HTML 标签按普通文本处理", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: '参考 <a href="references/unclosed-missing.md" 后面还有文字\n',
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 0, cli.stdout);
    assert.equal(cli.stdout, "校验通过.\n");
  }));

test("未闭合 HTML 注释: 行内未闭合按普通文本检查, 行首块注释不检查", () =>
  withTempDir((directory) => {
    // CommonMark 只把带 --> 的行内注释识别为 HTML; 同一行内未闭合的 <!-- 是普通文本,
    // 其中的链接照常解析, 因此会报告目标缺失.
    const inline = createSkill(directory, {
      body: "文字 <!-- [x](references/comment-missing.md)\n",
    });
    assert.deepEqual(render(validateSkill(inline).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/comment-missing.md",
    ]);

    // 行首 <!-- 开启 HTML 块注释并打断段落, 即使到文末都未闭合, 块内链接也不检查.
    const block = createSkill(directory, {
      name: "block-comment",
      directory: "block-comment",
      body: "文字\n<!-- [x](references/block-comment-missing.md)\n",
    });
    const { errors, warnings } = validateSkill(block);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("同一行重复的 HTML 链接目标只报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        '正文 <a href=references/duplicate-missing.md>a</a> 和 ' +
        '<a href="references/duplicate-missing.md">b</a>\n',
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/duplicate-missing.md",
    ]);
  }));

test("同一行同一目标的实体与百分号混写只报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[一](a&b.md) [二](a&amp;b.md) [三](a%26b.md)\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: a&b.md",
    ]);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("同一行解码后不同的目标仍各报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "[一](x&amp;y.md) [二](x%26y.md) [三](other.md)\n\n" +
        "[片段甲](a%26b.md#x) [片段乙](a&amp;b.md#y)\n",
    });
    // 解码后相同的前三个链接只保留一条; 片段不同的两个目标不合并.
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: other.md",
      "SKILL.md:6: 本地链接目标不存在: x&y.md",
      "SKILL.md:8: 本地链接目标不存在: a&b.md",
      "SKILL.md:8: 本地链接目标不存在: a&b.md",
    ]);
  }));

test("同一行的 Markdown 链接与 HTML 属性指向同一目标时只报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: '[一](a%26b.md) <a href="a&amp;b.md">x</a>\n',
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: a&b.md",
    ]);
  }));

test("引用式链接缺少定义时报错, 定义存在时检查目标", () =>
  withTempDir((directory) => {
    const missing = createSkill(directory, {
      body: "正文 [文本][标签].\n",
    });
    assert.deepEqual(
      render(validateSkill(missing).errors),
      ["SKILL.md:6: 引用式链接定义不存在: 标签"]
    );

    const defined = createSkill(directory, {
      name: "defined",
      directory: "defined",
      body: "正文 [文本][标签].\n\n[标签]: references/note.md\n",
      files: { "references/note.md": "# 说明\n" },
    });
    assert.deepEqual(render(validateSkill(defined).errors), []);
    assert.deepEqual(render(validateSkill(defined).warnings), []);
  }));

test("HTML 实体和百分号转义先解码再解析", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "读取 [a](a&amp;b.md) 与 [b](a%20b.md) 与 [c](a%2520b.md).\n",
      files: {
        "a&b.md": "# 1\n",
        "a b.md": "# 2\n",
        "a%20b.md": "# 3\n",
      },
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("命名 HTML 实体按完整实体表解码, 行内 HTML 属性与 Markdown 链接一致", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "读取 [sol](references&sol;a.md) 与 [copy](references/&copy;.md).\n\n" +
        '<a href="references&sol;a.md">a</a>\n\n' +
        '<img src="references/&copy;.md">\n\n' +
        "[missing](references&sol;missing.md)\n\n" +
        '<a href="references&sol;missing.md">missing</a>\n',
      files: {
        "references/a.md": "# a\n",
        "references/©.md": "# copy\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:12: 本地链接目标不存在: references/missing.md",
      "SKILL.md:14: 本地链接目标不存在: references/missing.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("无分号的 legacy 命名实体与数字实体按 HTML 规则解码", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "读取 [实体](a&ampb.md) 与 [数字](a&#65.md) 与 [数字b](a&#65b.md).\n\n" +
        '<a href="a&ampb.md">实体</a>\n\n' +
        '<img src="a&#65.md">\n\n' +
        "对照 [未解码](a&hellipb.md).\n",
      files: {
        "a&b.md": "# 1\n",
        "aA.md": "# 2\n",
        "aAb.md": "# 3\n",
        "a…b.md": "# 4\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:12: 本地链接目标不存在: a&hellipb.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("双次实体编码的 Markdown 链接与定义只解码一次, HTML 属性同样", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "[双实体](a&amp;amp;b.md) 与 [定义][r] 与 [反向](only-a&amp;b.md)\n\n" +
        "[r]: a&amp;amp;b.md\n\n" +
        '<a href="a&amp;amp;b.md">属性</a>\n',
      files: {
        "a&amp;b.md": "# 1\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标不存在: only-a&b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("双次实体编码的目标只有解码后的文件时不通过", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[双实体](a&amp;amp;b.md)\n",
      files: {
        "a&b.md": "# 1\n",
      },
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: a&amp;b.md",
    ]);
  }));

test("Windows 盘符和 UNC 路径给可移植性警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "读取 [盘符](<C:\\work\\demo.md>) 与 [斜杠](C:/work/demo.md), " +
        "以及 [共享](<\\\\server\\share\\demo.md>).\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(
      filtered(warnings, "Windows 绝对路径不可移植").map((issue) => issue.message),
      [
        "Windows 绝对路径不可移植: C:/work/demo.md",
        "Windows 绝对路径不可移植: C:\\work\\demo.md",
        "Windows 绝对路径不可移植: \\server\\share\\demo.md",
      ]
    );
    const strict = run(VALIDATOR, [root, "--strict"]);
    assert.equal(strict.status, 1, strict.stdout);
    assert.match(strict.stdout, /严格模式/u);
  }));

test("正斜杠 UNC 路径给可移植性警告且控制字符仍报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body:
        "读取 [共享](//server/share/demo.md), " +
        "[查询](//server/share/demo.md?raw=1), " +
        "[片段](//server/share/demo.md#section).\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), [
      "SKILL.md:6: Windows 绝对路径不可移植: //server/share/demo.md",
      "SKILL.md:6: Windows 绝对路径不可移植: //server/share/demo.md#section",
      "SKILL.md:6: Windows 绝对路径不可移植: //server/share/demo.md?raw=1",
    ]);

    // 正斜杠 UNC 不是外部链接: 控制字符仍按错误处理, 不报目标缺失.
    const badRoot = createSkill(directory, {
      directory: "unc-control",
      name: "unc-control",
      body: "[坏](//server/share/a\u0001b.md)\n",
    });
    const bad = validateSkill(badRoot);
    assert.deepEqual(render(bad.errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: //server/share/a\\x01b.md",
    ]);
    assert.deepEqual(render(bad.warnings), []);
    const cli = run(VALIDATOR, [badRoot]);
    assert.equal(cli.status, 1, cli.stdout);
    assert.match(cli.stdout, /a\\x01b\.md/u);
    assert.doesNotMatch(cli.stdout, /本地链接目标不存在/u);
  }));

test("绝对路径目标存在时警告并在 skill 内计入引用", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      files: { "references/note.md": "# 笔记\n" },
    });
    const note = path.join(root, "references/note.md");
    fs.writeFileSync(
      path.join(root, "SKILL.md"),
      "---\nname: demo-skill\ndescription: 做演示. 在用户要求演示时使用.\n---\n\n" +
        "读取 [笔记](<" +
        note +
        ">).\n",
      "utf8"
    );
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(
      render(warnings),
      ["SKILL.md:6: 绝对路径链接不可移植: " + note]
    );

    fs.writeFileSync(
      path.join(root, "SKILL.md"),
      "---\nname: demo-skill\ndescription: 做演示. 在用户要求演示时使用.\n---\n\n" +
        "读取 [缺失](</nonexistent/skill-creator-test/missing.md>).\n",
      "utf8"
    );
    assert.deepEqual(
      render(validateSkill(root).errors),
      [
        "SKILL.md:6: 本地链接目标不存在: /nonexistent/skill-creator-test/missing.md",
      ]
    );
  }));

test("越出 skill 目录的链接给警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "参考 [外部](../outside.md).\n",
    });
    fs.writeFileSync(path.join(directory, "outside.md"), "# 外部\n", "utf8");
    assert.deepEqual(
      render(validateSkill(root).warnings),
      ["SKILL.md:6: 链接目标在 skill 目录外, 不可移植: ../outside.md"]
    );
  }));

test("路径大小写与磁盘不一致时警告并计入引用", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "读取 [笔记](References/note.md).\n",
      files: { "references/note.md": "# 笔记\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), [
      "SKILL.md:6: 链接路径大小写与磁盘不一致, 不可移植: References/note.md",
    ]);
  }));

test("参考文件内只能按文件目录解析的链接给警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[说明](references/a.md)\n",
      files: {
        "references/a.md": "[同目录](b.md)\n",
        "references/b.md": "# b\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(
      filtered(warnings, "仅按所在文件目录可解析").map((issue) =>
        issue.render()
      ),
      [
        "references/a.md:1: 链接仅按所在文件目录可解析, 建议改为相对 skill 根目录: b.md",
      ]
    );
  }));

test("参考文件内的断链报错并给出参考文件与行号", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[说明](references/a.md)\n",
      files: {
        "references/a.md": "# 说明\n\n[断链](missing.md)\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "references/a.md:3: 本地链接目标不存在: missing.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("参考文件内的控制字符目标报错并给出参考文件与行号", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[说明](references/a.md)\n",
      files: {
        "references/a.md": [
          "# 说明",
          "",
          "[坏](bad\u0001name.md)",
          "",
          "[删除](bad\u007fname.md)",
          "",
        ].join("\n"),
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "references/a.md:3: 本地链接目标包含 NUL 或控制字符: bad\\x01name.md",
      "references/a.md:5: 本地链接目标包含 NUL 或控制字符: bad\\x7fname.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("链接目标含控制字符时报错且不进入文件系统", () =>
  withTempDir((directory) => {
    const cases = [
      ["%00", "\\x00"],
      ["%01", "\\x01"],
      ["%7F", "\\x7f"],
      ["%C2%85", "\\x85"],
      ["%C2%9B", "\\x9b"],
    ];
    for (const [encoded, escaped] of cases) {
      const root = createSkill(path.join(directory, encoded), {
        body: "读取 [坏](references/bad" + encoded + "name.md).\n",
      });
      assert.deepEqual(
        render(validateSkill(root).errors),
        [
          "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: references/bad" +
            escaped +
            "name.md",
        ],
        encoded
      );
    }
  }));

test("裸链接目标中的原始控制字符报错且行号准确", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "第一段 [文件](a\u0001b.md).",
        "",
        "第二段 [删除符](c\u007fd.md).",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: c\\x7fd.md",
    ]);
  }));

test("角度链接目标中的原始控制字符只报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "读取 [文件](<a\u0001b.md>) 与 [删除符](<c\u007fd.md>).\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: c\\x7fd.md",
    ]);
  }));

test("普通文本中的括号不按行内链接检查控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "普通文本 foo](a\u0001b) 不是链接.\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
  }));

test("角度链接目标的片段中含控制字符时报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[b](<ok.md#bad\u0001anchor>)\n",
      files: { "ok.md": "# ok\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: ok.md#bad\\x01anchor",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("行内 HTML 属性的片段中含控制字符时报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "参考 <a href=\"ok.md#bad\u0002anchor\">x</a>.\n",
      files: { "ok.md": "# ok\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: ok.md#bad\\x02anchor",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("正常片段锚点不误报", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[ok](ok.md#section)\n",
      files: { "ok.md": "# ok\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("纯锚点内的片段控制字符仍报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "参考 [锚点](#x\u0001y).\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: #x\\x01y",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("纯锚点 HTML 属性内的片段控制字符仍报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: '参考 <a href="#z\u0002">x</a>.\n',
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: #z\\x02",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("正常纯锚点跳过存在性检查且不误报", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: '[ok](#section) 与 <a href="#ok">x</a>\n',
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("百分号编码的控制字符仍按解码结果报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "读取 [编码](a%01b.md) 与 [删除码](c%7Fd.md).\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: c\\x7fd.md",
    ]);
  }));

test("同一行字符引用与百分号编码的同一控制字符目标只报一次", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[引用](a&#1;b.md) [编码](a%01b.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 1, cli.stdout);
  }));

test("字符引用形式的控制字符目标只报控制字符错误", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[x](a&#1;b.md)\n\n![图](img&#1;.png)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: img\\x01.png",
    ]);
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 1, cli.stdout);
    assert.match(cli.stdout, /a\\x01b\.md/u);
    assert.doesNotMatch(cli.stdout, /本地链接目标不存在/u);
  }));

test("数字实体的无效码点按 U+FFFD 替换并报目标不存在", () =>
  withTempDir((directory) => {
    const cases = [
      ["NUL", "&#0;"],
      ["代理区", "&#xD800;"],
      ["超出上限", "&#x110000;"],
    ];
    for (const [index, [label, entity]] of cases.entries()) {
      const name = "entity-" + index;
      const root = createSkill(directory, {
        name,
        directory: name,
        body: "[x](a" + entity + "b.md)\n",
      });
      const { errors, warnings } = validateSkill(root);
      // 无效码点按 Python html.unescape 的规则解码为 U+FFFD, 不再解成控制字符,
      // 孤立代理或残留原文, 因此报目标不存在而不是控制字符错误.
      assert.deepEqual(
        render(errors),
        ["SKILL.md:6: 本地链接目标不存在: a\uFFFDb.md"],
        label
      );
      assert.ok(errors[0].message.includes("\uFFFD"), label);
      assert.ok(!errors[0].message.includes("控制字符"), label);
      assert.deepEqual(render(warnings), [], label);
      const cli = run(VALIDATOR, [root]);
      assert.equal(cli.status, 1, cli.stdout);
      assert.match(cli.stdout, /a\uFFFDb\.md/u);
      assert.doesNotMatch(cli.stdout, /控制字符/u);
    }
  }));

test("字符引用的控制字符目标不跳过同一行的正常链接", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[x](a&#1;b.md) 与 [正常](references/missing.md)\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/missing.md",
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
  }));

test("转义方括号与代码区域中的控制字符目标不误报", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "正文 [转义\\](a\u0001b.md).",
        "",
        "`[行内](a\u0001b.md)`",
        "",
        "```markdown",
        "[围栏](a\u0001b.md)",
        "```",
        "",
        "<div>",
        "[HTML](a\u0001b.md)",
        "</div>",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
  }));

test("引用式定义目标中的原始控制字符报错, 未被引用的定义也检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "第一段引用[文本][坏标签].",
        "",
        "[坏标签]: a\u0001b.md",
        "",
        "[未引用]: references/c\u007fd.md",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:10: 本地链接目标包含 NUL 或控制字符: references/c\\x7fd.md",
    ]);
  }));

test("引用式定义的角度目标中的控制字符也报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "[角度]: <a\u0001b.md>",
        "",
        "[删除]: <c\u007fd.md>",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: c\\x7fd.md",
    ]);
  }));

test("定义目标后带非标题文本时该行不构成定义, 按定义不存在报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "第一段引用[文本][r].",
        "",
        "[r]: a\u0001b.md  多余文本",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 引用式链接定义不存在: r",
    ]);
    assert.ok(!errors.some((issue) => issue.message.includes("控制字符")));
    assert.deepEqual(render(warnings), []);
  }));

test("定义目标后带合法标题时仍按定义检查控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "第一段引用[文本][r].",
        "",
        '[r]: a\u0001b.md "标题"',
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.ok(!errors.some((issue) => issue.message.includes("定义不存在")));
    assert.deepEqual(render(warnings), []);
  }));

test("定义目标无尾随文本时仍按定义报控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "第一段引用[文本][r].",
        "",
        "[r]: a\u0001b.md",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.ok(!errors.some((issue) => issue.message.includes("定义不存在")));
    assert.deepEqual(render(warnings), []);
  }));

test("正文与标题中的 [a]: 文本不按引用式定义检查控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "正文中的 [a]: b\u0001.md 只是文本.",
        "",
        "# 标题中的 [b]: c\u0002.md 也只是文本",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("行首, 列表项与块引用中的合法定义仍报控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "[行首]: a\u0001b.md",
        "",
        "- [列表]: c\u0002d.md",
        "",
        "> [引用]: e\u0003f.md",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: c\\x02d.md",
      "SKILL.md:10: 本地链接目标包含 NUL 或控制字符: e\\x03f.md",
    ]);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("列表项续行缩进 4 空格的含控制字符定义仍被识别", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "- 项目",
        "",
        "    [文档]: a\u0001b.md",
        "",
        "[文本][文档]",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("块引用内列表项续行缩进的定义仍被识别", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "> - 项目",
        ">",
        ">     [文档]: a\u0001b.md",
        "",
        "[文本][文档]",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("段落续行中的定义样文本不报控制字符, 引用仍报定义缺失", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: ["正文", "[ref]: a\u0001b.md", "", "[文本][ref]", ""].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:9: 引用式链接定义不存在: ref",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("列表项与块引用续行中的定义样文本不报控制字符", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "+ 项目文字",
        "  [ref]: a\u0001b.md",
        "",
        "> 引用文字",
        "> [ref2]: c\u0002d.md",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("跨行行内链接目标中的控制字符报错且不报目标缺失", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[行内](\n  a\u0001b.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("跨行引用式定义目标中的控制字符报错且不报定义缺失", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[标签]:\n  a\u0001b.md\n\n见 [文本][标签].\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("跨行目标允许四空格续行缩进", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "[行内](",
        "    a\u0001b.md)",
        "",
        "[标签]:",
        "    c\u0002d.md",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:9: 本地链接目标包含 NUL 或控制字符: c\\x02d.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("跨行链接与定义仍检查目标是否存在", () =>
  withTempDir((directory) => {
    const inlineRoot = createSkill(directory, {
      name: "multiline-inline",
      directory: "multiline-inline",
      body: "[行内](\n  references/missing.md)\n",
    });
    assert.deepEqual(render(validateSkill(inlineRoot).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/missing.md",
    ]);
    const definitionRoot = createSkill(directory, {
      name: "multiline-definition",
      directory: "multiline-definition",
      body: "[标签]:\n  references/missing.md\n\n见 [文本][标签].\n",
    });
    assert.deepEqual(render(validateSkill(definitionRoot).errors), [
      "SKILL.md:6: 本地链接目标不存在: references/missing.md",
    ]);
  }));

test("跨行标签的裸控制字符目标报控制字符且不报目标缺失", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[多行\n标签](a\u0001b.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("跨行标签的字符引用控制字符只报控制字符错误", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[多行\n标签](a&#1;b.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("正常跨行标签指向存在文件时通过", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[多行\n标签](references/real.md)\n",
      files: { "references/real.md": "# Real\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("引用式定义目标中的字符引用控制字符只报控制字符错误", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[未引用]: a&#1;b.md\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
    ]);
  }));

test("被引用定义的字符引用控制字符不报定义缺失, 正常定义仍检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "见 [x][l] 与 [y][正常].",
        "",
        "[l]: a&#1;b.md",
        "[正常]: references/missing.md",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:8: 本地链接目标包含 NUL 或控制字符: a\\x01b.md",
      "SKILL.md:9: 本地链接目标不存在: references/missing.md",
    ]);
  }));

test("脚注定义目标中的控制字符不按链接报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: ["脚注[^1].", "", "[^1]: a\u0001b.md", ""].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
  }));

test("代码块和行内代码中的定义目标控制字符不报错", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "```markdown",
        "[围栏]: a\u0001b.md",
        "```",
        "",
        "`[行内]: a\u0001b.md`",
        "",
      ].join("\n"),
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
  }));

test("正常链接和普通括号文本不误报", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "调用 f(x) 与 g(a(b)c), 见 [文件](references/ok.md).\n",
      files: { "references/ok.md": "# 说明\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("未引用参考文件和脚本文件给警告, 依赖目录和顶层文件不检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      files: {
        "references/used.md": "# 已用\n",
        "references/unused.md": "# 未用\n",
        "references/.hidden.md": "# 隐藏\n",
        "references/node_modules/pkg/index.md": "# 依赖\n",
        "references/third_party/pkg/index.md": "# 依赖\n",
        "references/custom/note.md": "# 自定义\n",
        "scripts/vendor/lib/a.py": "print()\n",
        "scripts/venv/lib/a.py": "print()\n",
        "scripts/__pycache__/cache.pyc": "bytecode\n",
        "scripts/stray.pyc": "bytecode\n",
        "scripts/stray.mjs": "export {};\n",
        "scripts/foo.py": "print()\n",
        "scripts/.hidden": "hidden\n",
        "assets/logo.txt": "logo\n",
        "LICENSE": "MIT\n",
      },
      body: "[已用](references/used.md)\n",
    });
    assert.deepEqual(render(validateSkill(root).warnings), [
      "references/custom/note.md: 未被 SKILL.md 直接引用的文件",
      "references/unused.md: 未被 SKILL.md 直接引用的文件",
      "scripts/foo.py: 未被 SKILL.md 直接引用的文件",
      "scripts/stray.mjs: 未被 SKILL.md 直接引用的文件",
    ]);
  }));

test("正文纯文本提及和 license 文件豁免未引用警告", () =>
  withTempDir((directory) => {
    const mentioned = createSkill(directory, {
      files: { "scripts/foo.mjs": "export {};\n" },
      body: "运行 ./scripts/foo.mjs 生成报告.\n",
    });
    assert.deepEqual(render(validateSkill(mentioned).warnings), []);

    const licensed = createSkill(directory, {
      name: "licensed",
      directory: "licensed",
      extraFrontmatter: "license: references/license.txt\n",
      files: { "references/license.txt": "MIT\n" },
    });
    assert.deepEqual(render(validateSkill(licensed).warnings), []);
  }));

test("参考文件互相引用给警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[a](references/a.md) [b](references/b.md)\n",
      files: {
        "references/a.md": "[b](references/b.md)\n",
        "references/b.md": "# b\n",
      },
    });
    assert.deepEqual(render(validateSkill(root).warnings), [
      "references/a.md:1: 参考文件互相引用, 只应从 SKILL.md 直接引用一层",
    ]);
  }));

test("反斜杠转义的标签和引用标签不误报", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        '正文 \\<a href="references/escaped-missing.md">x</a>',
        "",
        "正文 \\<a href=references/escaped-unquoted-missing.md>x</a>",
        "",
        "正文 \\[x](references/escaped-link-missing.md)",
        "",
        "[x][a\\]b]",
        "",
        "[a\\]b]: references/note.md",
        "",
      ].join("\n"),
      files: { "references/note.md": "# 说明\n" },
    });
    assert.deepEqual(render(validateSkill(root).errors), []);
    assert.deepEqual(render(validateSkill(root).warnings), []);
  }));

test("脚注定义不按引用式链接定义检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "正文引用脚注[^1] 与[^2].",
        "",
        "[^1]: references/missing.md",
        "[^2]: references/note.md",
        "",
      ].join("\n"),
      files: { "references/note.md": "# 说明\n" },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("参考文件内的脚注定义不报错也不触发互引警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[a](references/a.md) [b](references/b.md)\n",
      files: {
        "references/a.md": [
          "# a",
          "",
          "脚注[^1] 与[^2].",
          "",
          "[^1]: references/b.md",
          "[^2]: references/missing.md",
          "",
        ].join("\n"),
        "references/b.md": "# b\n",
      },
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("脚注定义存在时普通引用式定义仍按原规则检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: [
        "脚注[^1] 与引用[文本][标签].",
        "",
        "[^1]: references/footnote-missing.md",
        "[标签]: references/definition-missing.md",
        "",
      ].join("\n"),
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:9: 本地链接目标不存在: references/definition-missing.md",
    ]);
    assert.deepEqual(render(warnings), []);
  }));

test("嵌套图片目标也检查", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[![alt](images/missing.png)](references/missing.md)\n",
    });
    assert.deepEqual(render(validateSkill(root).errors), [
      "SKILL.md:6: 本地链接目标不存在: images/missing.png",
      "SKILL.md:6: 本地链接目标不存在: references/missing.md",
    ]);
  }));

// 非 root 的 POSIX 平台才拿得到 EACCES; root 与 Windows 跳过.
const CAN_DENY_READ = process.platform !== "win32" && process.getuid?.() !== 0;

function invalidUtf8Skill() {
  return Buffer.concat([
    Buffer.from(
      "---\nname: demo-skill\ndescription: 做演示. 在用户要求演示时使用.\n---\n\n## 流程\n\n",
      "utf8"
    ),
    Buffer.from([0xff, 0xfe]),
    Buffer.from("\n", "utf8"),
  ]);
}

test(
  "SKILL.md 不可读时报无法读取, 不误报非法 UTF-8",
  { skip: !CAN_DENY_READ && "需要非 root 的 POSIX 平台才能制造 EACCES" },
  () =>
    withTempDir((directory) => {
      const root = createSkill(directory);
      const skillFile = path.join(root, "SKILL.md");
      fs.chmodSync(skillFile, 0o000);
      try {
        const rendered = render(validateSkill(root).errors);
        assert.equal(rendered.length, 1, rendered.join("\n"));
        assert.match(rendered[0], /^SKILL\.md: 无法读取: /u);
        assert.ok(!rendered[0].includes("不是有效的 UTF-8"), rendered[0]);
      } finally {
        fs.chmodSync(skillFile, 0o600);
      }
    })
);

test(
  "参考文件不可读时报无法读取, 不误报非法 UTF-8",
  { skip: !CAN_DENY_READ && "需要非 root 的 POSIX 平台才能制造 EACCES" },
  () =>
    withTempDir((directory) => {
      const root = createSkill(directory, {
        body: "[说明](references/note.md)\n",
        files: { "references/note.md": "# 说明\n" },
      });
      const reference = path.join(root, "references/note.md");
      fs.chmodSync(reference, 0o000);
      try {
        const rendered = render(validateSkill(root).errors);
        assert.equal(rendered.length, 1, rendered.join("\n"));
        assert.match(rendered[0], /^references\/note\.md: 无法读取: /u);
        assert.ok(!rendered[0].includes("不是有效的 UTF-8"), rendered[0]);
      } finally {
        fs.chmodSync(reference, 0o600);
      }
    })
);

test("非法 UTF-8 的 SKILL.md 报不是有效的 UTF-8 文本", () =>
  withTempDir((directory) => {
    const root = createSkill(directory);
    fs.writeFileSync(path.join(root, "SKILL.md"), invalidUtf8Skill());
    const rendered = render(validateSkill(root).errors);
    assert.equal(rendered.length, 1, rendered.join("\n"));
    assert.match(rendered[0], /^SKILL\.md: 不是有效的 UTF-8 文本: /u);
    assert.ok(!rendered[0].includes("无法读取"), rendered[0]);
  }));

test("非法 UTF-8 的参考文件报不是有效的 UTF-8 文本", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      body: "[说明](references/note.md)\n",
      files: { "references/note.md": "# 说明\n" },
    });
    fs.writeFileSync(
      path.join(root, "references/note.md"),
      Buffer.from([0xff, 0xfe, 0x0a])
    );
    const rendered = render(validateSkill(root).errors);
    assert.equal(rendered.length, 1, rendered.join("\n"));
    assert.match(rendered[0], /^references\/note\.md: 不是有效的 UTF-8 文本: /u);
    assert.ok(!rendered[0].includes("无法读取"), rendered[0]);
  }));

test("超长行内目标中的控制字符仍报错且消息包含完整目标", () =>
  withTempDir((directory) => {
    // 约 600 字符的裸行内目标, 远超本次迁移早期的 Node 草稿 (未入库) 的 512 字符扫描上限.
    const target = "a".repeat(300) + "\u0001" + "b".repeat(300) + ".md";
    const escaped = target.replace("\u0001", "\\x01");
    const root = createSkill(directory, {
      body: "[文件](" + target + ")\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: " + escaped,
    ]);
    assert.ok(errors[0].message.includes(escaped), "消息应包含完整目标");
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 1, cli.stdout);
    assert.ok(cli.stdout.includes(escaped), cli.stdout);
  }));

test("超长引用式定义目标中的控制字符仍报错且消息包含完整目标", () =>
  withTempDir((directory) => {
    const target = "a".repeat(300) + "\u0001" + "b".repeat(300) + ".md";
    const escaped = target.replace("\u0001", "\\x01");
    const root = createSkill(directory, {
      body: "[标签]: " + target + "\n\n见 [文本][标签].\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: " + escaped,
    ]);
    assert.ok(errors[0].message.includes(escaped), "消息应包含完整目标");
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 1, cli.stdout);
    assert.ok(cli.stdout.includes(escaped), cli.stdout);
  }));

test("超长链接文本中的控制字符目标仍报错", () =>
  withTempDir((directory) => {
    // 约 1200 字符的链接文本, 远超本次迁移早期的 Node 草稿 (未入库) 的 999 字符标签回溯上限.
    const label = "文".repeat(1200);
    const root = createSkill(directory, {
      body: "[" + label + "](x\u0001y.md)\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), [
      "SKILL.md:6: 本地链接目标包含 NUL 或控制字符: x\\x01y.md",
    ]);
    assert.deepEqual(render(warnings), []);
    const cli = run(VALIDATOR, [root]);
    assert.equal(cli.status, 1, cli.stdout);
    assert.ok(cli.stdout.includes("x\\x01y.md"), cli.stdout);
  }));
