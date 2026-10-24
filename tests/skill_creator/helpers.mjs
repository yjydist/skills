// 测试辅助: 创建临时 skill 目录, 运行两个 CLI.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../.."
);
export const VALIDATOR = path.join(
  ROOT,
  "skills/skill-creator/scripts/validate_skill.mjs"
);
export const INIT = path.join(
  ROOT,
  "skills/skill-creator/scripts/init_skill.mjs"
);

export function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "skill-creator-test-"));
}

export function removeDir(directory) {
  fs.rmSync(directory, { recursive: true, force: true });
}

export function withTempDir(callback) {
  const directory = tempDir();
  try {
    return callback(directory);
  } finally {
    removeDir(directory);
  }
}

export function run(script, args, options = {}) {
  return spawnSync(process.execPath, [script, ...args], {
    encoding: "utf8",
    ...options,
  });
}

export function yamlScalar(value) {
  if (value === "") {
    return '""';
  }
  if (
    [...value].some((character) => ':#"\''.includes(character)) ||
    value !== value.trim() ||
    "!&*|>%@`{},[]".includes(value[0])
  ) {
    return '"' + value.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
  }
  return value;
}

export function createSkill(base, options = {}) {
  const name = options.name ?? "demo-skill";
  const directory = options.directory ?? name;
  const description = options.description ?? "做演示. 在用户要求演示时使用.";
  const body = options.body ?? "## 流程\n\n1. 执行.\n";
  const extraFrontmatter = options.extraFrontmatter ?? "";
  const files = options.files ?? {};

  const root = path.join(base, directory);
  fs.mkdirSync(root, { recursive: true });
  fs.writeFileSync(
    path.join(root, "SKILL.md"),
    "---\nname: " +
      yamlScalar(name) +
      "\ndescription: " +
      yamlScalar(description) +
      "\n" +
      extraFrontmatter +
      "---\n\n" +
      body +
      "\n",
    "utf8"
  );
  for (const [relative, content] of Object.entries(files)) {
    const target = path.join(root, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, content, "utf8");
  }
  return root;
}

export function createSkillWithFrontmatter(base, frontmatter, options = {}) {
  const directory = options.directory ?? "demo-skill";
  const body = options.body ?? "## 流程\n\n1. 执行.\n";
  const root = path.join(base, directory);
  fs.mkdirSync(root, { recursive: true });
  fs.writeFileSync(
    path.join(root, "SKILL.md"),
    "---\n" + frontmatter + "---\n\n" + body + "\n",
    "utf8"
  );
  return root;
}
