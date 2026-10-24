import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { validateSkill } from "../../skills/skill-creator/scripts/validate_skill.mjs";
import {
  withTempDir,
  createSkill,
  createSkillWithFrontmatter,
} from "./helpers.mjs";

function render(errors) {
  return errors.map((issue) => issue.render());
}

test("有效 skill 没有错误和警告", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      files: { "references/note.md": "# 说明\n" },
      body: "读取 [说明](references/note.md).\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(render(warnings), []);
  }));

test("缺少 name 或 description 报错并定位到字段行", () =>
  withTempDir((directory) => {
    const missingName = createSkillWithFrontmatter(
      path.join(directory, "name"),
      "description: 做演示. 在用户要求演示时使用.\n"
    );
    assert.deepEqual(
      render(validateSkill(missingName).errors),
      ["SKILL.md:2: 缺少 name 字段"]
    );

    const missingDescription = createSkillWithFrontmatter(
      path.join(directory, "description"),
      "name: demo-skill\n"
    );
    assert.deepEqual(
      render(validateSkill(missingDescription).errors),
      ["SKILL.md:2: 缺少 description 字段"]
    );
  }));

test("name 与 description 的非字符串值报错", () =>
  withTempDir((directory) => {
    const numberName = createSkillWithFrontmatter(
      path.join(directory, "name"),
      "name: 123\ndescription: 做演示. 在用户要求演示时使用.\n"
    );
    assert.deepEqual(
      render(validateSkill(numberName).errors),
      ["SKILL.md:2: name 必须是字符串"]
    );

    const numberDescription = createSkillWithFrontmatter(
      path.join(directory, "description"),
      "name: demo-skill\ndescription: 123\n"
    );
    assert.deepEqual(
      render(validateSkill(numberDescription).errors),
      ["SKILL.md:3: description 必须是字符串"]
    );
  }));

test("name 规则覆盖大小写, 连字符, 字符集和长度", () =>
  withTempDir((directory) => {
    const cases = [
      ["Demo-Skill", "小写"],
      ["-demo", "连字符开头或结尾"],
      ["demo-", "连字符开头或结尾"],
      ["demo--skill", "连续连字符"],
      ["demo_skill", "只能包含"],
      ["a".repeat(65), "长度必须在"],
      ["🙂", "只能包含"],
    ];
    for (const [name, expected] of cases) {
      const root = createSkill(path.join(directory, String(Math.random())), {
        name,
        directory: name,
      });
      const { errors } = validateSkill(root);
      assert.ok(
        errors.some((issue) => issue.message.includes(expected)),
        name + " -> " + JSON.stringify(render(errors))
      );
    }
  }));

test("name 的 Unicode, 去空白和 NFKC 行为", () =>
  withTempDir((directory) => {
    for (const name of ["技能", "café", "a-b", "a".repeat(64)]) {
      const root = createSkill(path.join(directory, "unicode-" + name.length), {
        name,
        directory: name,
      });
      assert.deepEqual(render(validateSkill(root).errors), [], name);
    }

    const nfkc = createSkill(path.join(directory, "nfkc"), {
      name: "café",
      directory: "cafe\u0301",
    });
    assert.deepEqual(render(validateSkill(nfkc).errors), []);

    const stripped = createSkill(path.join(directory, "stripped"), {
      name: " demo ",
      directory: "demo",
    });
    assert.deepEqual(render(validateSkill(stripped).errors), []);
  }));

test("目录名首尾空白不参与 name 归一化", () =>
  withTempDir((directory) => {
    for (const directoryName of [" demo", "demo "]) {
      const root = createSkill(path.join(directory, directoryName.trim() || "x"), {
        name: "demo",
        directory: directoryName,
      });
      assert.ok(
        validateSkill(root).errors.some((issue) =>
          issue.message.includes("name 与父目录名不一致")
        )
      );
    }
  }));

test("通过符号链接调用时按真实目录名校验 name", (t) =>
  withTempDir((directory) => {
    const realRoot = createSkill(directory, { name: "real-name" });
    const aliasRoot = path.join(directory, "alias-name");
    try {
      fs.symlinkSync(realRoot, aliasRoot, "dir");
    } catch (error) {
      // Windows 需要开发者模式或管理员权限才能创建目录符号链接.
      t.skip("当前平台无法创建目录符号链接: " + error.code);
      return;
    }

    assert.deepEqual(render(validateSkill(aliasRoot).errors), []);

    const mismatchRoot = createSkill(directory, {
      name: "ghost-name",
      directory: "actual-dir",
    });
    const mismatchLink = path.join(directory, "ghost-name");
    fs.symlinkSync(mismatchRoot, mismatchLink, "dir");
    assert.deepEqual(render(validateSkill(mismatchLink).errors), [
      "SKILL.md:2: name 与父目录名不一致: ghost-name != actual-dir",
    ]);
  }));

test("description 和 compatibility 的长度边界", () =>
  withTempDir((directory) => {
    const exact = createSkill(directory, {
      name: "demo-skill",
      description: "a".repeat(1024),
    });
    assert.deepEqual(render(validateSkill(exact).errors), []);

    const tooLong = createSkill(directory, {
      name: "too-long",
      directory: "too-long",
      description: "a".repeat(1025),
    });
    assert.deepEqual(
      render(validateSkill(tooLong).errors),
      ["SKILL.md:3: description 不能超过 1024 字符, 当前为 1025 字符"]
    );

    const compatibility = createSkill(directory, {
      name: "compat",
      directory: "compat",
      extraFrontmatter: "compatibility: " + "a".repeat(500) + "\n",
    });
    assert.deepEqual(render(validateSkill(compatibility).errors), []);

    const compatibilityTooLong = createSkill(directory, {
      name: "compat-long",
      directory: "compat-long",
      extraFrontmatter: "compatibility: " + "a".repeat(501) + "\n",
    });
    assert.deepEqual(
      render(validateSkill(compatibilityTooLong).errors),
      [
        "SKILL.md:4: compatibility 长度必须在 1-500 字符之间, 当前为 501 字符",
      ]
    );
  }));

test("可选字段的类型和格式", () =>
  withTempDir((directory) => {
    const valid = createSkill(directory, {
      extraFrontmatter:
        "license: MIT\n" +
        "compatibility: 需要 Node.js 20+.\n" +
        "metadata:\n" +
        "  author: example\n" +
        '  version: "1.0"\n' +
        "allowed-tools: Bash(git:*) Read\n",
    });
    assert.deepEqual(render(validateSkill(valid).errors), []);

    const invalid = createSkill(directory, {
      name: "invalid",
      directory: "invalid",
      extraFrontmatter:
        "license: 123\n" +
        'compatibility: ""\n' +
        "metadata:\n" +
        "  version: 1.0\n" +
        "  true: value\n" +
        "allowed-tools: Read, Write\n",
    });
    const messages = render(validateSkill(invalid).errors);
    for (const expected of [
      "license 必须是字符串",
      "compatibility 长度必须在 1-500 字符之间",
      "metadata.version 的值必须是字符串",
      "metadata 的键必须是字符串",
      "allowed-tools 必须是空格分隔的工具名字符串",
    ]) {
      assert.ok(
        messages.some((message) => message.includes(expected)),
        expected + " -> " + JSON.stringify(messages)
      );
    }

    const tab = createSkill(directory, {
      name: "tab",
      directory: "tab",
      extraFrontmatter: 'allowed-tools: "Read\\tWrite"\n',
    });
    assert.ok(
      render(validateSkill(tab).errors).some((message) =>
        message.includes("allowed-tools 必须是空格分隔的工具名字符串")
      )
    );
  }));

test("非标准字段报警告并定位到字段行", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      extraFrontmatter: "# 注释\n# 注释\n版本: \"1.0\"\n",
    });
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(render(errors), []);
    assert.deepEqual(
      warnings.map((issue) => issue.render()),
      ["SKILL.md:6: 非标准字段: 版本"]
    );
  }));

test("正文为空, 只有注释和超长正文", () =>
  withTempDir((directory) => {
    for (const body of [
      "",
      "<!-- 只有注释 -->\n",
      "<!-- 跨行\n注释 -->\n",
      "<!-- 未闭合注释\n仍算注释\n",
    ]) {
      const root = createSkill(path.join(directory, String(Math.random())), {
        body,
      });
      assert.ok(
        validateSkill(root).errors.some(
          (issue) => issue.message === "正文不能为空"
        ),
        body
      );
    }

    const commentWithText = createSkill(path.join(directory, "text"), {
      body: "<!-- 说明 -->\n\n## 流程\n\n1. 执行.\n",
    });
    assert.ok(
      !validateSkill(commentWithText).errors.some(
        (issue) => issue.message === "正文不能为空"
      )
    );

    const long = createSkill(path.join(directory, "long"), {
      body: "x\n".repeat(501),
    });
    assert.ok(
      validateSkill(long).warnings.some((issue) =>
        issue.message.includes("正文超过 500 行")
      )
    );

    const boundary = createSkill(path.join(directory, "boundary"), {
      body: "x\n".repeat(499),
    });
    assert.ok(
      !validateSkill(boundary).warnings.some((issue) =>
        issue.message.includes("正文超过 500 行")
      )
    );
  }));

test("缺失 SKILL.md 和未闭合 frontmatter 报错", () =>
  withTempDir((directory) => {
    const missing = path.join(directory, "demo-skill");
    fs.mkdirSync(missing);
    assert.deepEqual(render(validateSkill(missing).errors), [
      "SKILL.md: 缺少 SKILL.md",
    ]);

    const unclosed = path.join(directory, "unclosed");
    fs.mkdirSync(unclosed);
    fs.writeFileSync(
      path.join(unclosed, "SKILL.md"),
      "---\nname: unclosed\n",
      "utf8"
    );
    assert.ok(
      validateSkill(unclosed).errors.some((issue) =>
        issue.message.includes("缺少结束标记")
      )
    );
  }));
