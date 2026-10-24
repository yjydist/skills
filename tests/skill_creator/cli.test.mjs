import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";

import {
  tempDir,
  removeDir,
  withTempDir,
  createSkill,
  run,
  VALIDATOR,
} from "./helpers.mjs";

// 慢消费者: 首次收到数据后暂停读取, 让管道写满并把剩余输出留在子进程的写队列里.
// 用 process.exit 退出的实现会丢掉这些未刷出的行.
function runSlowConsumer(script, args, pauseMilliseconds = 50) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [script, ...args], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    const chunks = [];
    let stderr = "";
    let paused = false;
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (text) => {
      stderr += text;
    });
    child.stdout.on("data", (chunk) => {
      chunks.push(chunk);
      if (!paused) {
        paused = true;
        child.stdout.pause();
        setTimeout(() => child.stdout.resume(), pauseMilliseconds);
      }
    });
    child.on("error", reject);
    child.on("close", (status) => {
      resolve({
        status,
        stdout: Buffer.concat(chunks).toString("utf8"),
        stderr,
      });
    });
  });
}

test("通过时退出状态为 0", () =>
  withTempDir((directory) => {
    const root = createSkill(directory);
    const result = run(VALIDATOR, [root]);
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.equal(result.stdout, "校验通过.\n");
  }));

test("有错误时退出状态为 1 并输出汇总", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, { description: "" });
    const result = run(VALIDATOR, [root]);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /错误: SKILL\.md:\d+: description 不能为空/u);
    assert.match(result.stdout, /校验失败: 1 个错误, 0 个警告\./u);
  }));

test("只有警告时默认通过, strict 时失败", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      extraFrontmatter: "vendor-field: true\n",
    });
    const normal = run(VALIDATOR, [root]);
    assert.equal(normal.status, 0);
    assert.match(normal.stdout, /警告: SKILL\.md:4: 非标准字段: vendor-field/u);
    assert.match(normal.stdout, /校验通过, 有 1 个警告\./u);

    const strict = run(VALIDATOR, [root, "--strict"]);
    assert.equal(strict.status, 1);
    assert.match(strict.stdout, /严格模式下警告视为错误: 1 个警告\./u);
  }));

test("verbose 输出解析器版本且位于错误和警告之前", () =>
  withTempDir((directory) => {
    const root = createSkill(directory, {
      extraFrontmatter: "vendor-field: true\n",
    });
    const result = run(VALIDATOR, [root, "--verbose"]);
    const lines = result.stdout.trim().split("\n");
    assert.match(lines[0], /^frontmatter 解析器: yaml \d+\.\d+\.\d+$/u);
    assert.match(lines[1], /^警告: /u);
  }));

test("参数错误和缺失路径", () =>
  withTempDir((directory) => {
    const noArgs = run(VALIDATOR, []);
    assert.equal(noArgs.status, 2);
    assert.match(noArgs.stderr, /用法/u);

    const help = run(VALIDATOR, ["--help"]);
    assert.equal(help.status, 0);
    assert.match(help.stdout, /用法/u);
    // 用法行与使用文档一致: 列出实际接受的 --help 选项.
    assert.match(help.stdout, /\[--help\]/u);
    assert.match(noArgs.stderr, /\[--help\]/u);

    const missing = run(VALIDATOR, [path.join(directory, "missing")]);
    assert.equal(missing.status, 1);
    assert.match(missing.stdout, /路径不存在/u);

    const file = path.join(directory, "file.txt");
    fs.writeFileSync(file, "x", "utf8");
    const notDirectory = run(VALIDATOR, [file]);
    assert.equal(notDirectory.status, 1);
    assert.match(notDirectory.stdout, /路径不是目录/u);
  }));

test("参数分隔符之后的 --help 按位置参数处理", () => {
  const result = run(VALIDATOR, ["--", "--help"]);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout + result.stderr, /路径不存在/u);

  const help = run(VALIDATOR, ["--help"]);
  assert.equal(help.status, 0, help.stderr);
  assert.match(help.stdout, /用法/u);
});

test("长选项前缀缩写按未知选项处理", () =>
  withTempDir((directory) => {
    const root = createSkill(directory);
    for (const prefix of ["--str", "--verb"]) {
      const result = run(VALIDATOR, [root, prefix]);
      assert.equal(
        result.status,
        2,
        prefix + ": " + result.stdout + result.stderr
      );
      assert.match(result.stderr, /Unknown option/u);
      assert.match(result.stderr, /用法: /u);
    }
  }));

test("尾随路径分隔符不出现在错误前缀中", () =>
  withTempDir((directory) => {
    const file = path.join(directory, "outside.md");
    fs.writeFileSync(file, "x", "utf8");
    const result = run(VALIDATOR, [file + path.sep]);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /路径不是目录/u);
    assert.ok(
      result.stdout.includes("错误: " + file + ": 路径不是目录"),
      result.stdout
    );
    assert.ok(!result.stdout.includes("outside.md" + path.sep), result.stdout);
  }));

test("大量警告经慢消费者输出完整, 与重定向文件一致", async () => {
  const directory = tempDir();
  try {
    let extraFrontmatter = "";
    for (let index = 0; index < 6000; index += 1) {
      extraFrontmatter += "vendor-field-" + index + ": true\n";
    }
    const root = createSkill(directory, { extraFrontmatter });

    // 重定向到文件作为基准: 输出不经过管道, 不受管道容量限制.
    const outFile = path.join(directory, "stdout.txt");
    const descriptor = fs.openSync(outFile, "w");
    const redirected = run(VALIDATOR, [root], {
      stdio: ["ignore", descriptor, "ignore"],
    });
    fs.closeSync(descriptor);
    const expected = fs.readFileSync(outFile, "utf8");
    assert.equal(redirected.status, 0);
    assert.equal(
      expected.split("\n").length - 1,
      6001,
      "基准应为 6000 条警告加 1 行汇总"
    );

    // 管道背压: 6000 条警告约 270KB, 超过管道缓冲区. 旧实现用 process.exit
    // 退出时会丢掉尚未写入管道的行.
    const slow = await runSlowConsumer(VALIDATOR, [root]);
    assert.equal(slow.status, 0, slow.stderr);
    assert.equal(slow.stderr, "");
    assert.equal(slow.stdout, expected);
  } finally {
    removeDir(directory);
  }
});

// 非 root 的 POSIX 平台才拿得到 EACCES; root 与 Windows 跳过.
const CAN_DENY_READ = process.platform !== "win32" && process.getuid?.() !== 0;

test(
  "SKILL.md 不可读时输出无法读取, 不输出非法 UTF-8",
  { skip: !CAN_DENY_READ && "需要非 root 的 POSIX 平台才能制造 EACCES" },
  () =>
    withTempDir((directory) => {
      const root = createSkill(directory);
      const skillFile = path.join(root, "SKILL.md");
      fs.chmodSync(skillFile, 0o000);
      try {
        const result = run(VALIDATOR, [root]);
        assert.equal(result.status, 1, result.stdout + result.stderr);
        assert.match(result.stdout, /错误: SKILL\.md: 无法读取: /u);
        assert.ok(
          !result.stdout.includes("不是有效的 UTF-8"),
          result.stdout
        );
      } finally {
        fs.chmodSync(skillFile, 0o600);
      }
    })
);

test("SKILL.md 含非法字节时输出非法 UTF-8, 不输出无法读取", () =>
  withTempDir((directory) => {
    const root = createSkill(directory);
    fs.writeFileSync(
      path.join(root, "SKILL.md"),
      Buffer.concat([
        Buffer.from(
          "---\nname: demo-skill\ndescription: 做演示. 在用户要求演示时使用.\n---\n\n## 流程\n\n",
          "utf8"
        ),
        Buffer.from([0xff, 0xfe]),
        Buffer.from("\n", "utf8"),
      ])
    );
    const result = run(VALIDATOR, [root]);
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout, /错误: SKILL\.md: 不是有效的 UTF-8 文本: /u);
    assert.ok(!result.stdout.includes("无法读取"), result.stdout);
  }));
