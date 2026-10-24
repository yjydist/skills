import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

import { ROOT, VALIDATOR, run, withTempDir } from "./helpers.mjs";
import { DEPENDENCY_PACKAGES } from "../../skills/skill-creator/scripts/dependency-list.mjs";

const DOCUMENTATION_FILES = [
  path.join(ROOT, "README.md"),
  path.join(ROOT, "docs/skill-creator.md"),
  path.join(ROOT, "skills/skill-creator/SKILL.md"),
  ...fs
    .readdirSync(path.join(ROOT, "skills/skill-creator/references"))
    .filter((name) => name.endsWith(".md"))
    .sort()
    .map((name) => path.join(ROOT, "skills/skill-creator/references", name)),
];

const REQUIRED_SKILL_SECTIONS = [
  "适用与门槛",
  "意图收集",
  "内容去向",
  "描述与触发",
  "正文与自由度",
  "脚手架与校验",
  "验证",
  "改进现有 skill",
  "交付说明",
  "操作边界",
];

const HARD_CONSTRAINT_NUMBER_PATTERN = /(?<![0-9])(?:64|1024|500|5000)(?![0-9])/g;
const NPM_PACKAGE_NAME_PATTERN =
  /^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/u;
const NPM_INSTALL_VALUE_FLAGS = new Set(["--prefix", "--registry", "-C"]);
const NAME_PATTERN_FORMS = [
  /\bNAME_PATTERN\b/,
  /\ba-z0-9\b/,
  /\[[^\]\n]*a-z[^\]\n]*\]/,
];
const INLINE_LINK_PATTERN =
  /(?<!!)\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^()\s]+)(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?\s*\)/g;
const POWERSHELL_FENCE_PATTERN = /```powershell\n([\s\S]*?)```/gu;

function skillBody(text) {
  const match = text.match(/^---\n[\s\S]*?\n---\n/u);
  return match ? text.slice(match[0].length) : text;
}

function proseLines(markdown) {
  const lines = [];
  let fence = null;
  for (const line of markdown.split("\n")) {
    const marker = line.match(/^ {0,3}(`{3,}|~{3,})/u);
    if (fence === null) {
      if (marker) {
        fence = marker[1];
      } else {
        lines.push(line);
      }
    } else if (
      marker &&
      marker[1][0] === fence[0] &&
      marker[1].length >= fence.length
    ) {
      fence = null;
    }
  }
  return lines;
}

function prose(markdown) {
  return proseLines(markdown).join("\n");
}

function levelTwoHeadings(markdown) {
  const headings = [];
  for (const line of proseLines(markdown)) {
    const match = line.match(/^ {0,3}##[ \t]+(.+?)[ \t]*$/u);
    if (match) {
      headings.push(match[1].trim());
    }
  }
  return headings;
}

function levelTwoSection(markdown, heading) {
  const lines = markdown.split("\n");
  const start = lines.findIndex(
    (line) => line.trim() === "## " + heading
  );
  if (start < 0) {
    return null;
  }
  let end = start + 1;
  while (end < lines.length && !/^ {0,3}##[ \t]+/u.test(lines[end])) {
    end += 1;
  }
  return lines.slice(start + 1, end).join("\n");
}

function inlineCodeTokens(text) {
  return [...text.matchAll(/`([^`\n]+)`/gu)].map((match) => match[1].trim());
}

function declaredDependencyFragment(section, label) {
  const match = section.match(/(?:npm 包|第三方依赖)\s+([\s\S]*?)安装在/u);
  assert.ok(match, label + " 缺少声明第三方依赖包名的片段");
  return { fragment: match[0], names: inlineCodeTokens(match[1]) };
}

function npmInstallPackages(command) {
  const tokens = command
    .replace(/<[^>\n]*>/gu, "<placeholder>")
    .trim()
    .split(/\s+/u);
  if (tokens.length < 3 || tokens[0] !== "npm" || tokens[1] !== "install") {
    return null;
  }
  const packages = [];
  let hasFlag = false;
  for (let index = 2; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (NPM_INSTALL_VALUE_FLAGS.has(token)) {
      hasFlag = true;
      index += 1;
      continue;
    }
    if (token.startsWith("-")) {
      hasFlag = true;
      continue;
    }
    if (!NPM_PACKAGE_NAME_PATTERN.test(token)) {
      return null;
    }
    packages.push(token);
  }
  return hasFlag && packages.length > 0 ? packages : null;
}

function npmInstallCommands(section) {
  const commands = [];
  for (const match of section.matchAll(/npm install[^\n`]*/gu)) {
    const packages = npmInstallPackages(match[0]);
    if (packages) {
      commands.push({ text: match[0].trim(), packages });
    }
  }
  return commands;
}

function assertDependencyNames(label, fragment, names) {
  const expected = [...DEPENDENCY_PACKAGES];
  for (const name of expected) {
    assert.ok(fragment.includes(name), label + " 未出现依赖包名: " + name);
  }
  for (const name of names) {
    assert.match(
      name,
      NPM_PACKAGE_NAME_PATTERN,
      label + " 出现不是 npm 包名的 token: " + name
    );
    assert.ok(expected.includes(name), label + " 出现清单外的依赖包名: " + name);
  }
  assert.deepEqual(
    [...new Set(names)].sort(),
    [...expected].sort(),
    label + " 的依赖包名集合与 dependency-list.mjs 不一致"
  );
}

function relativeLinkTargets(markdown) {
  const targets = [];
  for (const match of prose(markdown).matchAll(INLINE_LINK_PATTERN)) {
    let target = match[1];
    if (target.startsWith("<") && target.endsWith(">")) {
      target = target.slice(1, -1);
    }
    target = target.split("#", 1)[0].split("?", 1)[0];
    if (!target || target.startsWith("/") || target.startsWith("//")) {
      continue;
    }
    if (/^[A-Za-z][A-Za-z0-9+.-]*:/u.test(target)) {
      continue;
    }
    targets.push(target);
  }
  return targets;
}

function relativeLinkFragments(markdown) {
  const references = [];
  for (const match of prose(markdown).matchAll(INLINE_LINK_PATTERN)) {
    let target = match[1];
    if (target.startsWith("<") && target.endsWith(">")) {
      target = target.slice(1, -1);
    }
    const hash = target.indexOf("#");
    const location = (hash >= 0 ? target.slice(0, hash) : target).split(
      "?",
      1
    )[0];
    const fragment = hash >= 0 ? target.slice(hash + 1) : "";
    if (!location || location.startsWith("/") || location.startsWith("//")) {
      continue;
    }
    if (/^[A-Za-z][A-Za-z0-9+.-]*:/u.test(location)) {
      continue;
    }
    references.push([location, fragment]);
  }
  return references;
}

function githubHeadingAnchor(heading) {
  let text = heading.trim().toLowerCase();
  text = text.replace(/`([^`\n]*)`/g, "$1");
  text = text.replace(/\[([^\]\n]*)\]\([^)\n]*\)/g, "$1");
  let result = "";
  for (const character of text) {
    if (/^[\p{L}\p{N}]$/u.test(character) || " -_".includes(character)) {
      result += character;
    }
  }
  return result.replace(/ /g, "-");
}

function headingAnchors(markdown) {
  const anchors = new Set();
  const seen = new Map();
  for (const line of proseLines(markdown)) {
    const match = line.match(/^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$/u);
    if (!match) {
      continue;
    }
    const heading = match[1].replace(/[ \t]+#+$/u, "");
    const base = githubHeadingAnchor(heading);
    if (seen.has(base)) {
      seen.set(base, seen.get(base) + 1);
      anchors.add(base + "-" + seen.get(base));
    } else {
      seen.set(base, 0);
      anchors.add(base);
    }
  }
  return anchors;
}

test("SKILL.md 章节保持顺序", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const headings = levelTwoHeadings(skillBody(text));
  for (const section of REQUIRED_SKILL_SECTIONS) {
    assert.ok(headings.includes(section), section);
  }
  const positions = REQUIRED_SKILL_SECTIONS.map((section) =>
    headings.indexOf(section)
  );
  assert.deepEqual(positions, [...positions].sort((left, right) => left - right));
});

test("SKILL.md 声明运行前提和阻断流程", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const body = skillBody(text);
  assert.ok(levelTwoHeadings(body).includes("前提条件"));
  const textOnly = prose(body);
  for (const expected of [
    "Node.js 20",
    "node -v",
    "yaml",
    "mdast-util-from-markdown",
    "decode-named-character-reference",
    "缺少项, 检测结果, 要求, 修复命令, 影响",
    "授权降级",
    "重新执行",
    "重新检查",
  ]) {
    assert.ok(textOnly.includes(expected), expected);
  }
  assert.match(
    textOnly,
    /修复命令执行成功后重新执行本节的全部前提检查/u,
    "缺少修复后重新执行前提检查的步骤"
  );
  assert.match(
    textOnly,
    /\+ npm, 随 Node\.js 一起安装, 用于安装依赖\./u,
    "前提条件缺少 npm 作为安装依赖的外部程序"
  );
  assert.match(
    textOnly,
    /检查: `npm -v`/u,
    "前提条件缺少 npm 的可执行检查命令"
  );
  assert.match(
    textOnly,
    /无其他外部程序与认证要求\. 检查: `true`/u,
    "npm 之外的其余外部程序与认证必须保持为无, 并给出可执行的检查命令"
  );
  assert.match(
    textOnly,
    /仍失败时按安装失败处理/u,
    "复检失败时缺少重新阻断的说明"
  );
  assert.match(
    textOnly,
    /没有降级路径时只提供修复和终止/u,
    "缺少无降级路径时只提供修复和终止的规则"
  );
  assert.match(
    textOnly,
    /用户未选择前不继续, 不默认降级/u,
    "缺少用户未选择前不继续且不默认降级的规则"
  );
  assert.match(
    textOnly,
    /列出所有执行路径需要的/u,
    "缺少把只在部分执行路径使用的依赖一并列入前提条件的规则"
  );
  assert.match(
    textOnly,
    /未运行校验脚本时[\s\S]*?逐项列出实际核对项和结果/u,
    "缺少未运行校验脚本时逐项列出实际核对项和结果的规则"
  );
  assert.match(body, /npm install --no-save --no-package-lock --prefix/u);
  assert.match(body, /scripts\/check_dependencies\.mjs/u);

  const versionCheck = textOnly.match(/node -e "([^"\n]+)"/u);
  assert.ok(versionCheck, "缺少可直接执行的 Node 版本检查命令");
  const versionScript = versionCheck[1];
  assert.match(versionScript, /process\.versions\.node/u);
  assert.doesNotThrow(() =>
    execFileSync(process.execPath, ["-e", versionScript], { stdio: "pipe" })
  );
  const strictScript = versionScript.replace("< 20", "< 99");
  assert.notEqual(strictScript, versionScript, "版本检查命令必须比较主版本号");
  const strictExit = (() => {
    try {
      execFileSync(process.execPath, ["-e", strictScript], { stdio: "pipe" });
      return 0;
    } catch (error) {
      return error.status;
    }
  })();
  assert.equal(strictExit, 1, "版本不足时命令必须以状态 1 退出");
});

test("SKILL.md 每个前提条件条目都有检查命令", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const section = levelTwoSection(skillBody(text), "前提条件");
  assert.ok(section, "缺少前提条件节");
  const entries = section
    .split(/\n(?=\+ )/u)
    .filter((entry) => entry.startsWith("+ "));
  const lastDeclaration = entries.findIndex((entry) =>
    /^\+ 无其他外部程序与认证要求/u.test(entry)
  );
  assert.ok(lastDeclaration >= 0, "缺少外部程序与认证条目");
  const declarations = entries.slice(0, lastDeclaration + 1);
  for (const entry of declarations) {
    const label = entry.split("\n", 1)[0];
    const hasInlineCheck = /检查[^:\n]*: `[^`\n]+`/u.test(entry);
    const hasFencedCheck = /```[^\n]*\n[\s\S]*?\bnode\b[\s\S]*?```/u.test(
      entry
    );
    assert.ok(
      hasInlineCheck || hasFencedCheck,
      "前提条件条目缺少可执行的检查命令: " + label
    );
  }
});

test("SKILL.md 声明前提条件在创建和改进流程中的要求", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const textOnly = prose(skillBody(text));
  assert.match(
    textOnly,
    /新 skill 的 `SKILL\.md` 必须包含 `## 前提条件`[\s\S]*?缺少该节时不交付/u,
    "新 skill 缺少前提条件节时必须阻断交付"
  );
  assert.match(
    textOnly,
    /现有 skill 缺少 `## 前提条件` 时补上[\s\S]*?不按当前请求裁剪/u,
    "改进现有 skill 时必须补齐前提条件节, 且不按请求裁剪"
  );
  assert.match(
    textOnly,
    /用户授权降级时, 记录缺少项, 跳过的步骤, 未验证项和对产物的影响/u,
    "交付说明缺少降级影响的记录要求"
  );
});

test("最小 SKILL.md 示例包含前提条件节", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/references/spec.md"),
    "utf8"
  );
  const match = text.match(/最小 `SKILL\.md`:\n\n```markdown\n([\s\S]*?)\n```/u);
  assert.ok(match, "缺少最小 SKILL.md 示例");
  const headings = levelTwoHeadings(match[1]);
  assert.ok(headings.includes("前提条件"), "最小示例缺少前提条件节");
  assert.ok(headings.includes("流程"), "最小示例缺少流程节");
  assert.ok(
    headings.indexOf("前提条件") < headings.indexOf("流程"),
    "最小示例的前提条件节应位于流程之前"
  );
  assert.match(match[1], /检查: `[^`\n]+`/u, "前提条件条目缺少检查命令");
  assert.match(
    prose(text),
    /`## 前提条件` 是本流程的强制项/u,
    "缺少该节属于流程强制项而非标准要求的说明"
  );
});

test("依赖检查脚本与当前工作目录无关", () => {
  const script = path.join(
    ROOT,
    "skills/skill-creator/scripts/check_dependencies.mjs"
  );
  const fromRoot = run(script, [], { cwd: ROOT });
  assert.equal(fromRoot.status, 0, fromRoot.stderr);
  assert.match(fromRoot.stdout, /yaml/u);
  assert.match(fromRoot.stdout, /mdast-util-from-markdown/u);
  assert.match(fromRoot.stdout, /decode-named-character-reference/u);

  const fromTemp = withTempDir((directory) =>
    run(script, [], { cwd: directory })
  );
  assert.equal(fromTemp.status, 0, fromTemp.stderr);
  assert.match(fromTemp.stdout, /yaml/u);
  assert.match(fromTemp.stdout, /mdast-util-from-markdown/u);
  assert.match(fromTemp.stdout, /decode-named-character-reference/u);
});

test("文档声明的依赖包名与依赖清单一致", () => {
  const skillText = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const skillSection = levelTwoSection(skillBody(skillText), "前提条件");
  assert.ok(skillSection, "缺少前提条件节");
  const skillDeclaration = declaredDependencyFragment(
    skillSection,
    "SKILL.md 的前提条件依赖声明"
  );
  assertDependencyNames(
    "SKILL.md 的前提条件依赖声明",
    skillDeclaration.fragment,
    skillDeclaration.names
  );

  const skillCommands = npmInstallCommands(skillSection);
  assert.ok(skillCommands.length > 0, "前提条件缺少 npm install 修复命令");
  for (const command of skillCommands) {
    assertDependencyNames(
      "SKILL.md 的 npm install 修复命令",
      command.text,
      command.packages
    );
  }
  assert.deepEqual(
    skillCommands[0].packages,
    [...DEPENDENCY_PACKAGES],
    "SKILL.md 的 npm install 修复命令包名顺序与 dependency-list.mjs 不一致"
  );

  const docsText = fs.readFileSync(
    path.join(ROOT, "docs/skill-creator.md"),
    "utf8"
  );
  const docsSection = levelTwoSection(docsText, "使用前提");
  assert.ok(docsSection, "缺少使用前提节");
  const docsDeclaration = declaredDependencyFragment(
    docsSection,
    "docs/skill-creator.md 的使用前提依赖声明"
  );
  assertDependencyNames(
    "docs/skill-creator.md 的使用前提依赖声明",
    docsDeclaration.fragment,
    docsDeclaration.names
  );

  const docsCommands = npmInstallCommands(docsSection);
  assert.ok(docsCommands.length > 0, "使用前提缺少 npm install 安装命令");
  for (const command of docsCommands) {
    assertDependencyNames(
      "docs/skill-creator.md 的 npm install 安装命令",
      command.text,
      command.packages
    );
  }
});

test("文档中的依赖检查命令可从对应目录执行", () => {
  const fromSkillDir = run("scripts/check_dependencies.mjs", [], {
    cwd: path.join(ROOT, "skills/skill-creator"),
  });
  assert.equal(fromSkillDir.status, 0, fromSkillDir.stderr);

  const fromRoot = run(
    "skills/skill-creator/scripts/check_dependencies.mjs",
    [],
    { cwd: ROOT }
  );
  assert.equal(fromRoot.status, 0, fromRoot.stderr);

  const fromTemp = withTempDir((directory) =>
    run(
      path.join(ROOT, "skills/skill-creator/scripts/check_dependencies.mjs"),
      [],
      { cwd: directory }
    )
  );
  assert.equal(fromTemp.status, 0, fromTemp.stderr);
});

test("文档说明脚本路径仍随当前目录书写", () => {
  const documents = [
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    path.join(ROOT, "docs/skill-creator.md"),
  ];
  for (const document of documents) {
    const text = prose(fs.readFileSync(document, "utf8"));
    assert.match(
      text,
      /在 skill 目录运行 `node scripts\/check_dependencies\.mjs`/u,
      document
    );
    assert.match(
      text,
      /在仓库根目录运行 `node skills\/skill-creator\/scripts\/check_dependencies\.mjs`/u,
      document
    );
    assert.match(text, /其他目录使用绝对路径/u, document);
    assert.doesNotMatch(text, /任意目录/u, document);
  }
});

test("SKILL.md 正文不复制硬约束数字和名称正则", () => {
  const text = fs.readFileSync(
    path.join(ROOT, "skills/skill-creator/SKILL.md"),
    "utf8"
  );
  const textOnly = prose(skillBody(text));
  assert.deepEqual(textOnly.match(HARD_CONSTRAINT_NUMBER_PATTERN) ?? [], []);
  for (const pattern of NAME_PATTERN_FORMS) {
    assert.doesNotMatch(textOnly, pattern);
  }
});

test("文档中的相对链接目标存在", () => {
  for (const document of DOCUMENTATION_FILES) {
    const text = fs.readFileSync(document, "utf8");
    for (const target of relativeLinkTargets(text)) {
      const resolved = path.resolve(path.dirname(document), target);
      assert.ok(fs.existsSync(resolved), document + " -> " + target);
    }
  }
});

test("skill-creator 自身在严格模式下校验通过", () => {
  // --strict 把警告升级为错误, 覆盖 "链接目标不得越出 skill 目录" 等可移植性检查:
  // 校验通过且输出不带警告, 说明 skill-creator 自身没有触发这些警告.
  const result = run(VALIDATOR, [
    path.join(ROOT, "skills/skill-creator"),
    "--strict",
  ]);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stdout, /校验通过\./u);
});

test("标题锚点生成与 GitHub 风格一致", () => {
  const markdown = [
    "# skills",
    "",
    "## skills 列表",
    "",
    "### 校验脚本覆盖的检查",
    "",
    "## 1. 描述公式",
    "",
    "## 重复",
    "",
    "## 重复",
    "",
    "```markdown",
    "## 围栏内标题",
    "```",
  ].join("\n");
  assert.deepEqual(
    [...headingAnchors(markdown)].sort(),
    ["1-描述公式", "skills", "skills-列表", "校验脚本覆盖的检查", "重复", "重复-1"].sort()
  );
});

test("文档中的相对链接锚点存在", () => {
  const checked = new Set();
  for (const document of DOCUMENTATION_FILES) {
    const text = fs.readFileSync(document, "utf8");
    for (const [target, fragment] of relativeLinkFragments(text)) {
      if (!fragment) {
        continue;
      }
      const resolved = path.resolve(path.dirname(document), target);
      assert.ok(fs.existsSync(resolved), document + " -> " + target);
      assert.ok(
        headingAnchors(fs.readFileSync(resolved, "utf8")).has(fragment),
        document + " -> " + target + "#" + fragment
      );
      checked.add(
        path.relative(ROOT, resolved).split(path.sep).join("/") + "#" + fragment
      );
    }
  }
  for (const expected of [
    "README.md#skills-列表",
    "skills/skill-creator/references/spec.md#目录结构",
    "skills/skill-creator/references/spec.md#校验脚本覆盖的检查",
    "skills/skill-creator/references/spec.md#运行前提",
  ]) {
    assert.ok(checked.has(expected), expected);
  }
});

function powershellFenceLineArrays(markdown) {
  return [...markdown.matchAll(POWERSHELL_FENCE_PATTERN)].map((match) =>
    match[1].replace(/\n$/u, "").split("\n")
  );
}

function describePowerShellDrift(skillLines, docsLines) {
  const boundary = Math.max(skillLines.length, docsLines.length);
  for (let index = 0; index < boundary; index += 1) {
    if (skillLines[index] !== docsLines[index]) {
      return (
        "第 " +
        (index + 1) +
        " 行不一致: skills/skill-creator/SKILL.md = " +
        JSON.stringify(skillLines[index] ?? null) +
        ", docs/skill-creator.md = " +
        JSON.stringify(docsLines[index] ?? null)
      );
    }
  }
  return "两份文档的 powershell 代码块行数不同";
}

test("SKILL.md 与使用文档的 PowerShell 等价命令一致", () => {
  const documents = [
    {
      label: "skills/skill-creator/SKILL.md",
      path: path.join(ROOT, "skills/skill-creator/SKILL.md"),
    },
    {
      label: "docs/skill-creator.md",
      path: path.join(ROOT, "docs/skill-creator.md"),
    },
  ];
  const blocks = documents.map((document) => ({
    label: document.label,
    lines: powershellFenceLineArrays(fs.readFileSync(document.path, "utf8")),
  }));
  for (const block of blocks) {
    assert.equal(
      block.lines.length,
      1,
      block.label +
        " 应恰好有 1 个 powershell 代码块, 实际 " +
        block.lines.length +
        " 个"
    );
  }
  const skillLines = blocks[0].lines[0];
  const docsLines = blocks[1].lines[0];
  assert.deepEqual(
    skillLines,
    docsLines,
    "PowerShell 等价命令不一致: " +
      describePowerShellDrift(skillLines, docsLines)
  );
});

test("文档不再描述 Python 回退解析器", () => {
  for (const document of DOCUMENTATION_FILES) {
    const text = fs.readFileSync(document, "utf8");
    for (const obsolete of [
      "内置解析器",
      "未安装 PyYAML",
      "validate_skill.py",
      "init_skill.py",
      "test_skill_creator.py",
    ]) {
      assert.ok(!text.includes(obsolete), document + " -> " + obsolete);
    }
  }
});
