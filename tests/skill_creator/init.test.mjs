import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

import {
  normalizeName,
  validateName,
} from "../../skills/skill-creator/scripts/init_skill.mjs";
import { validateSkill } from "../../skills/skill-creator/scripts/validate_skill.mjs";
import { withTempDir, run, INIT, VALIDATOR } from "./helpers.mjs";

test("normalizeName 归一化为小写字母, 数字和连字符", () => {
  const cases = {
    "My_Skill  Name": "my-skill-name",
    "--Foo--": "foo",
    "A--B": "a-b",
    "a b_c": "a-b-c",
    "foo.bar": "foo-bar",
    你好: "你好",
    Café: "café",
    ＡＢＣ: "abc",
    "!!!": "",
    "🙂": "",
  };
  for (const [raw, expected] of Object.entries(cases)) {
    assert.equal(normalizeName(raw), expected, raw);
  }
});

test("validateName 拒绝空名称, 大写和连续连字符", () => {
  for (const name of ["", "Demo-Skill", "demo--skill", "-demo", "demo-"]) {
    assert.notEqual(validateName(name), null, name);
  }
  assert.equal(validateName("demo-skill"), null);
  assert.equal(validateName("技能"), null);
  assert.equal(validateName("a".repeat(64)), null);
});

test("import init_skill.mjs 不探测依赖也不产生输出或失败退出码", () => {
  withTempDir((directory) => {
    // 复制脚本与共享依赖清单到没有 node_modules 的临时目录.
    const scripts = path.join(directory, "isolated-skill", "scripts");
    fs.mkdirSync(scripts, { recursive: true });
    fs.copyFileSync(
      path.join(path.dirname(INIT), "dependency-list.mjs"),
      path.join(scripts, "dependency-list.mjs")
    );
    const script = path.join(scripts, "init_skill.mjs");
    fs.copyFileSync(INIT, script);
    const url = pathToFileURL(script).href;
    // 确认纯函数导出仍可用, 同时保持子进程无额外输出.
    const source = `import(${JSON.stringify(url)}).then((module) => {
  if (typeof module.normalizeName !== "function") {
    throw new Error("normalizeName 未导出");
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
    assert.equal(result.stdout, "");
    assert.equal(result.stderr, "");
  });
});

test("--help 输出版本用法并成功退出", () => {
  const result = run(INIT, ["--help"]);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /用法: /u);
  assert.match(result.stdout, /<name>/u);
  // 用法行与使用文档一致: 列出实际接受的 --help 选项.
  assert.match(result.stdout, /\[--help\]/u);
});

test("--help 只在分隔符之前且不是 --path 取值时触发帮助", () =>
  withTempDir((directory) => {
    // --path 缺少取值时按参数错误退出, 不把后面的 --help 当帮助请求.
    const missingPathValue = run(INIT, ["my-skill", "--path", "--help"], {
      cwd: directory,
    });
    assert.equal(
      missingPathValue.status,
      2,
      missingPathValue.stdout + missingPathValue.stderr
    );
    assert.match(missingPathValue.stderr, /--path/u);
    assert.deepEqual(fs.readdirSync(directory), []);

    // -- 之后的 --help 是位置参数, 归一化后创建 ./help.
    const positional = run(INIT, ["--", "--help"], { cwd: directory });
    assert.equal(positional.status, 0, positional.stderr);
    assert.ok(
      fs.statSync(path.join(directory, "help", "SKILL.md")).isFile()
    );

    // --path=--help 是 --path 的取值, 同样不触发帮助.
    const pathValue = run(INIT, ["my-skill", "--path=--help"], {
      cwd: directory,
    });
    assert.equal(pathValue.status, 0, pathValue.stderr);
    assert.ok(
      fs.statSync(
        path.join(directory, "--help", "my-skill", "SKILL.md")
      ).isFile()
    );
  }));

test("缺少位置参数时输出用法并以状态 2 退出", () =>
  withTempDir((directory) => {
    const result = run(INIT, [], { cwd: directory });
    assert.equal(result.status, 2);
    assert.match(result.stderr, /用法: /u);
    assert.match(result.stderr, /<name>/u);
    assert.deepEqual(fs.readdirSync(directory), []);
  }));

test("多余位置参数时输出用法并以状态 2 退出", () =>
  withTempDir((directory) => {
    const result = run(INIT, ["demo-skill", "extra", "--path", directory]);
    assert.equal(result.status, 2);
    assert.match(result.stderr, /用法: /u);
    assert.match(result.stderr, /<name>/u);
    assert.deepEqual(fs.readdirSync(directory), []);
  }));

test("长选项前缀缩写按未知选项处理且不创建目录", () =>
  withTempDir((directory) => {
    for (const args of [
      ["demo-skill", "--pa", directory],
      ["demo-skill", "--scr"],
    ]) {
      const result = run(INIT, args, { cwd: directory });
      assert.equal(
        result.status,
        2,
        args.join(" ") + ": " + result.stdout + result.stderr
      );
      assert.match(result.stderr, /Unknown option/u);
      assert.match(result.stderr, /用法: /u);
      assert.deepEqual(fs.readdirSync(directory), []);
    }
  }));

test("创建请求的目录和骨架", () =>
  withTempDir((directory) => {
    const result = run(INIT, [
      "My_Skill",
      "--path",
      directory,
      "--scripts",
      "--references",
    ]);
    assert.equal(result.status, 0, result.stderr);
    const root = path.join(directory, "my-skill");
    assert.ok(fs.statSync(path.join(root, "SKILL.md")).isFile());
    assert.ok(fs.statSync(path.join(root, "scripts")).isDirectory());
    assert.ok(fs.statSync(path.join(root, "references")).isDirectory());
    assert.ok(!fs.existsSync(path.join(root, "assets")));
    const text = fs.readFileSync(path.join(root, "SKILL.md"), "utf8");
    assert.match(text, /name: "my-skill"/u);
    assert.match(text, /description: ""/u);
    assert.match(text, /^## 前提条件$/mu);
    assert.match(text, /TODO/u);
    assert.match(result.stdout, /名称已归一化: My_Skill -> my-skill/u);
    assert.match(result.stdout, /已创建: /u);
    assert.match(result.stdout, /下一步: /u);
    assert.match(result.stdout, /前提条件/u);
  }));

test("已存在的目标目录不被覆盖", () =>
  withTempDir((directory) => {
    const root = path.join(directory, "demo-skill");
    fs.mkdirSync(root);
    fs.writeFileSync(path.join(root, "SKILL.md"), "original", "utf8");
    const result = run(INIT, ["demo-skill", "--path", directory]);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /不覆盖/u);
    assert.equal(
      fs.readFileSync(path.join(root, "SKILL.md"), "utf8"),
      "original"
    );
  }));

test("非法名称不创建文件", () =>
  withTempDir((directory) => {
    for (const raw of ["!!!", "🙂", "a".repeat(65)]) {
      const result = run(INIT, [raw, "--path", directory]);
      assert.notEqual(result.status, 0, raw);
    }
    assert.deepEqual(fs.readdirSync(directory), []);
  }));

test("生成的骨架先因 description 为空而失败", () =>
  withTempDir((directory) => {
    const result = run(INIT, ["demo-skill", "--path", directory]);
    assert.equal(result.status, 0, result.stderr);
    const root = path.join(directory, "demo-skill");
    const validation = run(VALIDATOR, [root]);
    assert.equal(validation.status, 1);
    assert.match(validation.stdout, /description 不能为空/u);
    assert.doesNotMatch(validation.stdout, /正文不能为空/u);
  }));

test("填写 description 和正文后通过 strict 校验", () =>
  withTempDir((directory) => {
    run(INIT, ["demo-skill", "--path", directory, "--scripts"]);
    const root = path.join(directory, "demo-skill");
    const skillFile = path.join(root, "SKILL.md");
    const text = fs
      .readFileSync(skillFile, "utf8")
      .replace(
        'description: ""',
        "description: 处理演示数据. 在用户要求演示时使用."
      )
      .replace(
        /## 前提条件[\s\S]*$/u,
        "## 前提条件\n\n+ Node.js 20+.\n  检查: `node --version`\n\n## 流程\n\n1. 执行.\n"
      );
    fs.writeFileSync(skillFile, text, "utf8");
    const validation = run(VALIDATOR, [root, "--strict"]);
    assert.equal(validation.status, 0, validation.stdout);
    assert.match(validation.stdout, /校验通过\./u);
  }));

test("assets 目录中的文件不触发未引用警告", () =>
  withTempDir((directory) => {
    run(INIT, ["demo-skill", "--path", directory, "--assets"]);
    const root = path.join(directory, "demo-skill");
    fs.writeFileSync(path.join(root, "assets", "logo.txt"), "logo", "utf8");
    const skillFile = path.join(root, "SKILL.md");
    fs.writeFileSync(
      skillFile,
      fs
        .readFileSync(skillFile, "utf8")
        .replace(
          'description: ""',
          "description: 处理演示数据. 在用户要求演示时使用."
        )
        .replace(
          "<!-- TODO: 填写上方 description, 并在本节之后补充实际流程正文, 同时删除两处 TODO. 占位符不能留在交付物中. -->",
          "## 流程\n\n1. 使用 assets/logo.txt.\n"
        ),
      "utf8"
    );
    const { errors, warnings } = validateSkill(root);
    assert.deepEqual(
      errors.map((issue) => issue.message),
      []
    );
    assert.deepEqual(
      warnings.filter((issue) => issue.location.includes("assets")),
      []
    );
  }));
