import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";

import {
  splitFrontmatter,
  parseFrontmatter,
  FrontmatterError,
} from "../../skills/skill-creator/scripts/validate_skill.mjs";
import {
  withTempDir,
  createSkillWithFrontmatter,
  run,
  VALIDATOR,
} from "./helpers.mjs";

// 解析失败时本仓库负责的契约只有错误类型, 行号和统一前缀; 前缀之后的 problem
// 文案由第三方 `yaml` 库给出, 不属于本仓库契约, 断言不锁定其具体文字, 只要求
// 前缀之后仍有内容 (库确实给出了 problem).
const FRONTMATTER_ERROR_PREFIX = "无法解析 frontmatter: ";

function isFrontmatterParseError(error) {
  return (
    error instanceof FrontmatterError &&
    error.message.startsWith(FRONTMATTER_ERROR_PREFIX) &&
    error.message.length > FRONTMATTER_ERROR_PREFIX.length
  );
}

test("splitFrontmatter 处理 BOM, CRLF 和正文起始行", () => {
  const text = "\uFEFF---\r\nname: demo-skill\r\n---\r\n\r\n正文\r\n";
  const result = splitFrontmatter(text);
  assert.deepEqual(result.frontmatterLines, ["name: demo-skill"]);
  assert.equal(result.body, "\n正文\n");
  assert.equal(result.bodyStart, 4);
});

test("splitFrontmatter 拒绝缺失或未闭合的 frontmatter", () => {
  assert.throws(
    () => splitFrontmatter("name: demo-skill\n---\n\n正文\n"),
    (error) =>
      error instanceof FrontmatterError &&
      error.line === 1 &&
      error.message.includes("第一行应为 ---")
  );
  assert.throws(
    () => splitFrontmatter("---\nname: demo-skill\n"),
    (error) =>
      error instanceof FrontmatterError &&
      error.line === 3 &&
      error.message.includes("缺少结束标记")
  );
});

test("parseFrontmatter 解析嵌套映射, 引号键和块标量", () => {
  const { data, parser, keyLines } = parseFrontmatter(
    [
      '"name" : demo-skill',
      "'description': |",
      "  做演示.",
      "  在用户要求演示时使用.",
      "metadata:",
      "  author: example",
      '  version: "1.0"',
    ].join("\n"),
    2
  );
  assert.match(parser, /^yaml \d+\.\d+\.\d+$/u);
  assert.equal(data.get("name"), "demo-skill");
  assert.equal(
    data.get("description"),
    "做演示.\n在用户要求演示时使用.\n"
  );
  assert.ok(data.get("metadata") instanceof Map);
  assert.equal(data.get("metadata").get("version"), "1.0");
  assert.equal(keyLines.get("name"), 2);
  assert.equal(keyLines.get("metadata"), 6);
});

test("parseFrontmatter 使用 YAML 1.2 语义", () => {
  const { data } = parseFrontmatter(
    [
      "name: demo-skill",
      "description: 做演示.",
      "licensed: yes",
      "enabled: on",
      "released: 2024-01-01",
      "version: 1.0",
    ].join("\n"),
    2
  );
  assert.equal(data.get("licensed"), "yes");
  assert.equal(data.get("enabled"), "on");
  assert.equal(data.get("released"), "2024-01-01");
  assert.equal(data.get("version"), 1);
});

test("parseFrontmatter 对解析错误报告 SKILL.md 行号", () => {
  assert.throws(
    () =>
      parseFrontmatter(
        'name: demo-skill\ndescription: hi\nlicense: "unclosed',
        2
      ),
    (error) =>
      error instanceof FrontmatterError &&
      error.line === 4 &&
      error.message.startsWith("无法解析 frontmatter:")
  );
});

test("parseFrontmatter 对重复键报告重复键所在行", () => {
  assert.throws(
    () => parseFrontmatter("name: dup\nname: dup\n", 2),
    (error) => isFrontmatterParseError(error) && error.line === 3
  );
  // 对照: 键不重复的同一形状输入不报错, 用例靠行号与输入构造区分, 不靠库文案.
  assert.doesNotThrow(() => parseFrontmatter("name: dup\nother: dup\n", 2));
});

test("parseFrontmatter 要求顶层是键值映射", () => {
  assert.throws(
    () => parseFrontmatter("- name: demo-skill", 2),
    (error) =>
      error instanceof FrontmatterError &&
      error.line === 2 &&
      error.message === "frontmatter 必须是键值映射"
  );
});

test("parseFrontmatter 接受空 frontmatter", () => {
  const { data } = parseFrontmatter("", 2);
  assert.ok(data instanceof Map);
  assert.equal(data.size, 0);
});

test("parseFrontmatter 把未定义别名转为带行号的 FrontmatterError", () => {
  assert.throws(
    () =>
      parseFrontmatter(
        "name: undefined-alias\ndescription: *missing\n",
        2
      ),
    (error) => isFrontmatterParseError(error) && error.line === 3
  );
  // 对照: 去掉别名后同一形状输入不报错, 用例靠行号与输入构造区分, 不靠库文案.
  assert.doesNotThrow(() =>
    parseFrontmatter("name: undefined-alias\ndescription: 做演示.\n", 2)
  );
});

test("parseFrontmatter 把未定义锚点的合并键转为带行号的 FrontmatterError", () => {
  assert.throws(
    () =>
      parseFrontmatter(
        "name: demo-skill\ndescription: 做演示.\nmetadata: {<<: *nodefaults}\n",
        2
      ),
    (error) => isFrontmatterParseError(error) && error.line === 4
  );
  // 对照: 同一形状但没有别名时不报错, 用例靠行号与输入构造区分, 不靠库文案.
  assert.doesNotThrow(() =>
    parseFrontmatter(
      "name: demo-skill\ndescription: 做演示.\nmetadata: {author: example}\n",
      2
    )
  );
});

test("CLI 对未定义别名和合并键输出诊断而不是堆栈", () =>
  withTempDir((directory) => {
    const cases = [
      [
        "name: undefined-alias\ndescription: *missing\n",
        3,
      ],
      [
        "name: demo-skill\ndescription: 做演示.\nmetadata: {<<: *nodefaults}\n",
        4,
      ],
    ];
    for (const [index, [frontmatter, line]] of cases.entries()) {
      const root = createSkillWithFrontmatter(
        path.join(directory, String(index)),
        frontmatter
      );
      const result = run(VALIDATOR, [root]);
      assert.equal(result.status, 1, result.stdout + result.stderr);
      // 只断言本仓库生成的位置与统一前缀; `\\S` 表示前缀之后仍有库给出的
      // problem 文案, 但不断言该文案的具体文字.
      assert.match(
        result.stdout,
        new RegExp(
          "错误: SKILL\\.md:" + line + ": 无法解析 frontmatter: \\S",
          "u"
        ),
        result.stdout
      );
      assert.doesNotMatch(
        result.stdout + result.stderr,
        /ReferenceError|\n\s+at /u
      );
    }
  }));

test("YAML 1.2 下已定义锚点的合并键按普通键报错", () =>
  withTempDir((directory) => {
    const frontmatter = [
      "name: demo-skill",
      "description: 做演示.",
      "defaults: &defaults {author: example}",
      "metadata: {<<: *defaults}",
    ].join("\n") + "\n";
    const { data } = parseFrontmatter(frontmatter, 2);
    const metadata = data.get("metadata");
    assert.ok(metadata instanceof Map);
    assert.ok(metadata.has("<<"));
    assert.equal(metadata.get("<<").get("author"), "example");
    assert.equal(metadata.has("author"), false);

    const root = createSkillWithFrontmatter(directory, frontmatter);
    const result = run(VALIDATOR, [root]);
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(
      result.stdout,
      /错误: SKILL\.md:5: metadata\.<< 的值必须是字符串/u
    );
  }));
