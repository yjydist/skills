// 测试校验脚本在缺少 Node.js 依赖时给出前提条件提示.

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

import {
  tempDir,
  removeDir,
  withTempDir,
  run,
  createSkill,
  VALIDATOR,
  INIT,
  ROOT,
} from "./helpers.mjs";

const DEPENDENCIES = path.join(
  ROOT,
  "skills/skill-creator/scripts/check_dependencies.mjs"
);

// 三个脚本共用的依赖清单, 必须与脚本一起复制才能加载.
const DEPENDENCY_LIST = path.join(
  ROOT,
  "skills/skill-creator/scripts/dependency-list.mjs"
);

// 仓库内已安装的依赖包, 供单包缺失用例以 symlink 复用, 不复制整目录.
const YAML_PACKAGE = path.join(
  ROOT,
  "skills/skill-creator/node_modules/yaml"
);

const DECODE_PACKAGE = path.join(
  ROOT,
  "skills/skill-creator/node_modules/decode-named-character-reference"
);

// 按相对路径列出目录中的全部文件, 用于确认脚本没有写入.
function listFiles(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      for (const child of listFiles(target)) {
        files.push(path.join(entry.name, child));
      }
    } else {
      files.push(entry.name);
    }
  }
  return files.sort();
}

// 把脚本和共享依赖清单复制到目标目录, 返回脚本路径.
function copyScript(source, targetDirectory) {
  fs.mkdirSync(targetDirectory, { recursive: true });
  fs.copyFileSync(
    DEPENDENCY_LIST,
    path.join(targetDirectory, "dependency-list.mjs")
  );
  const script = path.join(targetDirectory, path.basename(source));
  fs.copyFileSync(source, script);
  return script;
}

// 从五段报告中取出缺少项, 排序后便于跨脚本比较.
function missingPackages(stderr) {
  const line = stderr
    .split("\n")
    .find((text) => text.startsWith("缺少项: "));
  assert.ok(line !== undefined, stderr);
  return line.slice("缺少项: ".length).split(", ").sort();
}

// 通过 --require 预加载改写 process.versions.node, 覆盖三个脚本的 Node.js 版本守卫分支.
function writeNode18Preload(directory) {
  const preload = path.join(directory, "node18-preload.cjs");
  fs.writeFileSync(
    preload,
    'Object.defineProperty(process.versions, "node", { value: "18.0.0" });\n',
    "utf8"
  );
  return preload;
}

function node18Env(preload) {
  const env = { ...process.env };
  delete env.NODE_PATH;
  const quoted = preload.includes(" ") ? '"' + preload + '"' : preload;
  env.NODE_OPTIONS = "--require " + quoted;
  return env;
}

// 版本守卫的五段报告全部写到 stderr, 每段以 `标签: ` 开头.
function assertNodeVersionReport(result) {
  assert.equal(result.status, 1, result.stderr);
  for (const label of ["缺少项", "检测结果", "要求", "修复命令", "影响"]) {
    assert.match(result.stderr, new RegExp("^" + label + ": ", "mu"));
  }
  assert.match(result.stderr, /缺少项: Node\.js 20 或更高版本/u);
  assert.match(result.stderr, /检测结果: 当前为 Node\.js 18\.0\.0\./u);
  assert.match(result.stderr, /要求: 需要 Node\.js 20 或更高版本/u);
  assert.equal(result.stdout, "");
}

test("validate_skill.mjs 在 Node.js 低于 20 时按五段报告退出", () => {
  withTempDir((directory) => {
    const preload = writeNode18Preload(directory);
    const skill = createSkill(directory, { directory: "skill" });
    const result = run(VALIDATOR, [skill], { env: node18Env(preload) });
    assertNodeVersionReport(result);
    assert.doesNotMatch(result.stdout, /校验通过/u);
    assert.doesNotMatch(result.stderr, /Cannot find package/u);
  });
});

test("init_skill.mjs 在 Node.js 低于 20 时按五段报告退出且不创建目录", () => {
  withTempDir((directory) => {
    const preload = writeNode18Preload(directory);
    const parent = path.join(directory, "parent");
    fs.mkdirSync(parent);
    const result = run(INIT, ["demo-skill", "--path", parent], {
      env: node18Env(preload),
    });
    assertNodeVersionReport(result);
    assert.equal(fs.existsSync(path.join(parent, "demo-skill")), false);
    assert.deepEqual(listFiles(parent), []);
  });
});

test("init_skill.mjs 缺少 Node.js 依赖时按五段报告退出且不创建目录", () => {
  withTempDir((directory) => {
    // 复制脚本到没有 node_modules 的临时 skill 目录, 依赖无法从上层解析.
    const skill = path.join(directory, "isolated-skill");
    const script = copyScript(INIT, path.join(skill, "scripts"));
    const parent = path.join(directory, "parent");
    fs.mkdirSync(parent);
    const before = listFiles(skill);
    const env = { ...process.env };
    delete env.NODE_PATH;
    const result = run(script, ["demo-skill", "--path", parent], { env });
    assert.equal(result.status, 1, result.stderr);
    for (const label of ["缺少项", "检测结果", "要求", "修复命令", "影响"]) {
      assert.match(result.stderr, new RegExp("^" + label + ": ", "mu"));
    }
    assert.match(
      result.stderr,
      /缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference/u
    );
    assert.match(result.stderr, /无法加载 Node\.js 依赖/u);
    assert.match(result.stderr, /Cannot find package/u);
    assert.match(result.stderr, /检测结果: 未发现可导入的依赖包; /u);
    assert.match(
      result.stderr,
      /修复命令: npm install --no-save --no-package-lock --prefix [^\n]*yaml mdast-util-from-markdown decode-named-character-reference/u
    );
    assert.match(result.stderr, /影响: 依赖缺失时不创建 skill 骨架/u);
    assert.equal(result.stdout, "");
    assert.equal(fs.existsSync(path.join(parent, "demo-skill")), false);
    assert.deepEqual(listFiles(parent), []);
    assert.deepEqual(listFiles(skill), before);
  });
});

test("无 Node.js 依赖时 --help 和 -h 输出用法并退出 0", () => {
  withTempDir((directory) => {
    // 复制两个脚本到没有 node_modules 的临时 skill 目录, 依赖无法从上层解析.
    const skill = path.join(directory, "isolated-skill");
    const scripts = path.join(skill, "scripts");
    const env = { ...process.env };
    delete env.NODE_PATH;
    const cases = [
      [VALIDATOR, /用法: node validate_skill\.mjs <skill 目录>/u],
      [INIT, /用法: node init_skill\.mjs <name>/u],
    ];
    for (const [source, usagePattern] of cases) {
      const script = copyScript(source, scripts);
      for (const flag of ["--help", "-h"]) {
        const result = run(script, [flag], { env });
        assert.equal(result.status, 0, result.stderr);
        assert.match(result.stdout, usagePattern);
        // 帮助在依赖探测之前处理, 不输出五段依赖报告.
        assert.equal(result.stderr, "");
      }
    }
  });
});

test("import validate_skill.mjs 不产生输出或失败退出码", () => {
  withTempDir((directory) => {
    // 复制脚本与共享依赖清单到没有 node_modules 的临时目录, 依赖无法从上层解析.
    const scripts = path.join(directory, "isolated-skill", "scripts");
    const script = copyScript(VALIDATOR, scripts);
    const url = pathToFileURL(script).href;
    // 确认导出函数仍可用, 同时保持子进程无额外输出.
    const source = `import(${JSON.stringify(url)}).then((module) => {
  if (typeof module.validateSkill !== "function") {
    throw new Error("validateSkill 未导出");
  }
  if (typeof module.validateName !== "function") {
    throw new Error("validateName 未导出");
  }
});`;
    const env = { ...process.env };
    delete env.NODE_PATH;
    const result = spawnSync(process.execPath, ["-e", source], {
      encoding: "utf8",
      env,
    });
    assert.equal(result.status, 0, result.stderr);
    // 导入不打印五段依赖报告, 也不设置 process.exitCode.
    assert.equal(result.stdout, "");
    assert.equal(result.stderr, "");
  });
});

test("import check_dependencies.mjs 不产生输出或失败退出码", () => {
  withTempDir((directory) => {
    // 复制脚本与共享依赖清单到没有 node_modules 的临时目录, 依赖无法从上层解析.
    const scripts = path.join(directory, "isolated-skill", "scripts");
    const script = copyScript(DEPENDENCIES, scripts);
    const url = pathToFileURL(script).href;
    // 脚本不导出任何东西, 只确认导入本身静默完成; then 回调保持进程存活到加载结束.
    const source = `import(${JSON.stringify(url)}).then(() => {});`;
    const env = { ...process.env };
    delete env.NODE_PATH;
    const result = spawnSync(process.execPath, ["-e", source], {
      encoding: "utf8",
      env,
    });
    assert.equal(result.status, 0, result.stderr);
    // 导入不打印五段依赖报告, 也不设置 process.exitCode.
    assert.equal(result.stdout, "");
    assert.equal(result.stderr, "");
  });
});

test("check_dependencies.mjs 在 Node.js 低于 20 时按五段报告退出", () => {
  withTempDir((directory) => {
    const preload = writeNode18Preload(directory);
    const result = run(DEPENDENCIES, [], { env: node18Env(preload) });
    assertNodeVersionReport(result);
    assert.doesNotMatch(result.stdout, /依赖检查通过/u);
  });
});

test("缺少 Node.js 依赖时报告前提条件和原始错误", () => {
  const directory = tempDir();
  try {
    const isolated = path.join(directory, "isolated");
    const script = copyScript(VALIDATOR, isolated);
    const skill = createSkill(directory);
    const result = run(script, [skill]);
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stderr, /无法加载 Node.js 依赖/u);
    assert.match(result.stderr, /前提条件/u);
    for (const label of ["缺少项", "检测结果", "要求", "修复命令", "影响"]) {
      assert.match(result.stderr, new RegExp(label, "u"));
    }
    assert.match(
      result.stderr,
      /缺少项: yaml, mdast-util-from-markdown, decode-named-character-reference/u
    );
    assert.match(
      result.stderr,
      /修复命令: npm install --no-save --no-package-lock --prefix /u
    );
    assert.match(result.stderr, /Cannot find package/u);
    assert.doesNotMatch(result.stdout, /校验通过/u);
  } finally {
    removeDir(directory);
  }
});

test("只缺 mdast-util-from-markdown 时只报告实际缺失项", () => {
  const directory = tempDir();
  try {
    const skill = createSkill(directory, { directory: "isolated" });
    const scripts = path.join(skill, "scripts");
    const script = copyScript(VALIDATOR, scripts);
    const modules = path.join(skill, "node_modules");
    fs.mkdirSync(modules, { recursive: true });
    fs.symlinkSync(YAML_PACKAGE, path.join(modules, "yaml"), "junction");
    fs.symlinkSync(
      DECODE_PACKAGE,
      path.join(modules, "decode-named-character-reference"),
      "junction"
    );
    const env = { ...process.env };
    delete env.NODE_PATH;
    const result = run(script, [skill], { env });
    assert.equal(result.status, 1, result.stderr);
    for (const label of ["缺少项", "检测结果", "要求", "修复命令", "影响"]) {
      assert.match(result.stderr, new RegExp(label, "u"));
    }
    const missingLine = result.stderr
      .split("\n")
      .find((line) => line.startsWith("缺少项: "));
    assert.equal(missingLine, "缺少项: mdast-util-from-markdown");
    assert.match(result.stderr, /检测结果: yaml 可导入/u);
    assert.match(result.stderr, /mdast-util-from-markdown 导入失败/u);
    assert.match(result.stderr, /Cannot find package/u);
    assert.match(
      result.stderr,
      /修复命令: npm install --no-save --no-package-lock --prefix [^\n]*yaml mdast-util-from-markdown decode-named-character-reference/u
    );
    assert.doesNotMatch(result.stdout, /校验通过/u);
  } finally {
    removeDir(directory);
  }
});

test("check_dependencies.mjs 缺少依赖时输出五段报告并退出 1", () => {
  const directory = tempDir();
  try {
    const skill = createSkill(directory, {
      name: "isolated-skill",
      directory: "skill",
    });
    const script = copyScript(DEPENDENCIES, path.join(skill, "scripts"));
    const before = listFiles(skill);
    const env = { ...process.env };
    delete env.NODE_PATH;
    const result = run(script, [], { env });
    assert.equal(result.status, 1, result.stderr);
    for (const label of ["缺少项", "检测结果", "要求", "修复命令", "影响"]) {
      assert.match(result.stderr, new RegExp(label, "u"));
    }
    assert.match(result.stderr, /Cannot find (?:package|module)/u);
    assert.deepEqual(listFiles(skill), before);
  } finally {
    removeDir(directory);
  }
});

// 三个脚本的 "要求" 段必须是同一句文案, 防止副本漂移导致提示不一致.
test("无依赖副本中三个脚本的要求段文案一致", () => {
  const directory = tempDir();
  try {
    const skill = createSkill(directory, { directory: "isolated" });
    const scripts = path.join(skill, "scripts");
    const parent = path.join(directory, "parent");
    fs.mkdirSync(parent);
    const cases = [
      [copyScript(VALIDATOR, scripts), [skill]],
      [copyScript(INIT, scripts), ["demo-skill", "--path", parent]],
      [copyScript(DEPENDENCIES, scripts), []],
    ];
    const env = { ...process.env };
    delete env.NODE_PATH;
    const prefix = "要求: 需要能从本脚本位置导入 ";
    const tail =
      ", 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试.";
    const lines = cases.map(([script, args]) => {
      const result = run(script, args, { env });
      assert.equal(result.status, 1, result.stderr);
      const line = result.stderr
        .split("\n")
        .find((text) => text.startsWith("要求: "));
      assert.ok(line !== undefined, result.stderr);
      assert.ok(line.startsWith(prefix), line);
      assert.ok(line.endsWith(tail), line);
      return line;
    });
    for (const line of lines) {
      assert.equal(line, lines[0]);
    }
  } finally {
    removeDir(directory);
  }
});

// 三个脚本必须报告同一份清单, 防止副本漂移导致检查结果与执行结果不一致.
test("无依赖副本中三个脚本的缺少项集合一致", () => {
  const directory = tempDir();
  try {
    const skill = createSkill(directory, { directory: "isolated" });
    const scripts = path.join(skill, "scripts");
    const parent = path.join(directory, "parent");
    fs.mkdirSync(parent);
    const cases = [
      [copyScript(VALIDATOR, scripts), [skill]],
      [copyScript(INIT, scripts), ["demo-skill", "--path", parent]],
      [copyScript(DEPENDENCIES, scripts), []],
    ];
    const env = { ...process.env };
    delete env.NODE_PATH;
    const reported = cases.map(([script, args]) => {
      const result = run(script, args, { env });
      assert.equal(result.status, 1, result.stderr);
      return missingPackages(result.stderr);
    });
    assert.deepEqual(fs.existsSync(path.join(parent, "demo-skill")), false);
    const expected = [
      "decode-named-character-reference",
      "mdast-util-from-markdown",
      "yaml",
    ];
    for (const packages of reported) {
      assert.deepEqual(packages, expected);
    }
  } finally {
    removeDir(directory);
  }
});
