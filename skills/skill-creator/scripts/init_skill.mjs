#!/usr/bin/env node
// 创建 skill 目录骨架.
//
// 名称会按 NFKC 归一化为小写字母, 数字和连字符形式. 目录已存在时拒绝覆盖.
// 生成的 description 为空, 正文只有带 TODO 的 `## 前提条件` 占位节,
// 以便校验脚本在填写前必然失败.

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { parseArgs } from "node:util";
import { fileURLToPath } from "node:url";

import { DEPENDENCY_PACKAGES } from "./dependency-list.mjs";

// Node.js 版本守卫: 低于 20 时按五段报告停止, 不做后续处理.
// 提前终止只设置退出码, 让事件循环自然退出, 依赖 stdout/stderr 的排空.
// process.exit 会在管道背压时截断尚未写入的缓冲内容.
const NODE_MAJOR = Number.parseInt(process.versions.node.split(".")[0], 10);
const NODE_SUPPORTED = NODE_MAJOR >= 20;
if (!NODE_SUPPORTED) {
  console.error("缺少项: Node.js 20 或更高版本");
  console.error("检测结果: 当前为 Node.js " + process.versions.node + ".");
  console.error("要求: 需要 Node.js 20 或更高版本, 建议 22+.");
  console.error("修复命令: 由执行者按目标平台用 nvm 或系统包管理器安装 Node.js 20+, 不自动安装.");
  console.error("影响: 脚本无法运行, 安装 Node.js 20+ 后重试.");
  process.exitCode = 1;
}

// 帮助预扫描: 在依赖探测之前响应 --help/-h. 用法不依赖第三方包,
// 因此没有 node_modules 时也能打印用法并以 0 退出.
const isMain =
  process.argv[1] !== undefined &&
  isSamePath(process.argv[1], fileURLToPath(import.meta.url));

// `--` 之后是位置参数, 其中的 `--help` 不请求帮助; `--path` 的取值即使写成
// `--help` 或 `-h` 也不是帮助请求. 其余位置出现 `--help` 或 `-h` 才视为帮助请求.
function helpRequested(args) {
  const separator = args.indexOf("--");
  const end = separator === -1 ? args.length : separator;
  for (let index = 0; index < end; index += 1) {
    const argument = args[index];
    if (argument === "--path") {
      index += 1;
      continue;
    }
    if (argument.startsWith("--path=")) {
      continue;
    }
    if (argument === "--help" || argument === "-h") {
      return true;
    }
  }
  return false;
}

const HELP_REQUESTED = isMain && helpRequested(process.argv.slice(2));

// 依赖探测: 清单来自 dependency-list.mjs, 与 validate_skill.mjs 和
// check_dependencies.mjs 共用同一份. 在创建任何目录或文件之前执行,
// 缺失时按五段报告停止.
// 逐包导入, 每个包的失败互不影响, 以便报告实际缺失的包.
async function probeDependency(name) {
  try {
    await import(name);
    return { name, error: undefined };
  } catch (error) {
    return { name, error };
  }
}

function dependencyErrorMessage(error) {
  return error && error.message ? error.message : String(error);
}

// 探测依赖并在缺失时打印五段报告, 返回是否全部可用.
// 只在作为 CLI 运行时调用: 导入本模块以使用纯函数时不探测依赖,
// 也不产生输出或设置 process.exitCode.
async function checkDependencies() {
  const dependencyResults = [];
  for (const name of DEPENDENCY_PACKAGES) {
    dependencyResults.push(await probeDependency(name));
  }

  const availableDependencies = dependencyResults.filter(
    (result) => result.error === undefined
  );
  const missingDependencies = dependencyResults.filter(
    (result) => result.error !== undefined
  );

  if (missingDependencies.length === 0) {
    return true;
  }

  // 按本脚本所在位置解析依赖: scripts/ 的上一级即 skill 目录.
  const skillDirectory = path.dirname(
    path.dirname(fileURLToPath(import.meta.url))
  );
  const missingNames = missingDependencies.map((result) => result.name);
  console.error(
    "错误: 无法加载 Node.js 依赖 (" + missingNames.join(", ") + ")."
  );
  console.error("缺少项: " + missingNames.join(", "));
  console.error(
    "检测结果: " +
      (availableDependencies.length > 0
        ? availableDependencies
            .map((result) => result.name + " 可导入; ")
            .join("")
        : "未发现可导入的依赖包; ") +
      missingDependencies
        .map(
          (result) =>
            result.name +
            " 导入失败, 原始错误: " +
            dependencyErrorMessage(result.error)
        )
        .join("; ")
  );
  console.error(
    "要求: 需要能从本脚本位置导入 " +
      DEPENDENCY_PACKAGES.join(", ") +
      ", 全部安装在 skill 目录的 node_modules. 请按 SKILL.md 的 前提条件 一节安装依赖后重试."
  );
  console.error(
    "修复命令: npm install --no-save --no-package-lock --prefix " +
      skillDirectory +
      " " +
      DEPENDENCY_PACKAGES.join(" ")
  );
  console.error(
    "影响: 依赖缺失时不创建 skill 骨架, 需要先安装依赖再重试."
  );
  // 依赖缺失时只保留失败退出码, 不再进入 main 覆盖它.
  process.exitCode = 1;
  return false;
}

const MAX_NAME_LENGTH = 64;
const ALNUM_PATTERN = /^[\p{L}\p{N}]$/u;
const ALLOWED_PATTERN = /^[\p{L}\p{N}-]+$/u;

const SKILL_TEMPLATE = `---
name: "{name}"
description: ""
---

## 前提条件

<!-- TODO: 按实际运行时, 第三方依赖, 外部程序和认证填写下列条目, 缺失的项写 无, 然后删除本行. 检查命令必须可直接执行. -->

+ <运行时名称与最低版本>.
  检查: \`<可执行的版本检查命令>\`
+ <第三方依赖包; 无依赖时写 无>.
  检查: \`<可执行的依赖检查命令>\`
+ <外部程序与认证; 没有时写 无>.
  检查: \`<可执行的检查命令>\`

<!-- TODO: 填写上方 description, 并在本节之后补充实际流程正文, 同时删除两处 TODO. 占位符不能留在交付物中. -->
`;

function normalizeName(raw) {
  const name = raw.normalize("NFKC").trim().toLowerCase();
  const characters = [];
  for (const character of name) {
    characters.push(ALNUM_PATTERN.test(character) || character === "-" ? character : "-");
  }
  return characters.join("").replace(/-{2,}/g, "-").replace(/^-+|-+$/g, "");
}

function validateName(name) {
  const normalized = name.normalize("NFKC").trim();
  if (!normalized) {
    return "名称归一化后为空, 只允许小写字母, 数字和连字符";
  }
  if ([...normalized].length > MAX_NAME_LENGTH) {
    return "名称不能超过 " + MAX_NAME_LENGTH + " 字符";
  }
  if (normalized !== normalized.toLowerCase()) {
    return "名称必须全部为小写字母";
  }
  if (normalized.startsWith("-") || normalized.endsWith("-")) {
    return "名称不能以连字符开头或结尾";
  }
  if (normalized.includes("--")) {
    return "名称不能包含连续连字符";
  }
  if (!ALLOWED_PATTERN.test(normalized)) {
    return "名称只能包含小写字母, 数字和连字符";
  }
  return null;
}

function createSkill(name, parent, options = {}) {
  const target = path.join(parent, name);
  if (fs.existsSync(target)) {
    throw new Error("exists:" + target);
  }
  fs.mkdirSync(target, { recursive: true });
  fs.writeFileSync(target + path.sep + "SKILL.md", SKILL_TEMPLATE.replace("{name}", name), "utf8");
  for (const [enabled, directory] of [
    [options.scripts, "scripts"],
    [options.references, "references"],
    [options.assets, "assets"],
  ]) {
    if (enabled) {
      fs.mkdirSync(path.join(target, directory), { recursive: true });
    }
  }
  return target;
}

function usage() {
  return [
    "用法: node init_skill.mjs <name> [--path <父目录>] [--scripts] [--references] [--assets] [--help]",
    "创建 Agent Skills 目录骨架.",
  ].join("\n");
}

function main(argv = process.argv.slice(2)) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      allowPositionals: true,
      options: {
        path: { type: "string", default: "." },
        scripts: { type: "boolean", default: false },
        references: { type: "boolean", default: false },
        assets: { type: "boolean", default: false },
        help: { type: "boolean", short: "h", default: false },
      },
    });
  } catch (error) {
    console.error(error.message);
    console.error(usage());
    return 2;
  }

  if (parsed.values.help) {
    console.log(usage());
    return 0;
  }
  if (parsed.positionals.length !== 1) {
    console.error(usage());
    return 2;
  }

  const rawName = parsed.positionals[0];
  const name = normalizeName(rawName);
  const problem = validateName(name);
  if (problem) {
    console.error("错误: " + problem);
    return 1;
  }

  if (name !== rawName.trim()) {
    console.log("名称已归一化: " + rawName.trim() + " -> " + name);
  }

  let target;
  try {
    target = createSkill(name, parsed.values.path, {
      scripts: parsed.values.scripts,
      references: parsed.values.references,
      assets: parsed.values.assets,
    });
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("exists:")) {
      console.error(
        "错误: 目标路径已存在, 不覆盖: " +
          path.join(parsed.values.path, name)
      );
      return 1;
    }
    console.error("错误: 创建失败: " + (error && error.message ? error.message : error));
    return 1;
  }

  let resolved;
  try {
    resolved = fs.realpathSync(target);
  } catch {
    resolved = path.resolve(target);
  }
  const validatorPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "validate_skill.mjs");
  console.log("已创建: " + resolved);
  console.log(
    "下一步: 填写 \"## 前提条件\" 的占位内容, description 和流程正文, 再运行 node " +
      validatorPath +
      " " +
      resolved
  );
  return 0;
}

function isSamePath(left, right) {
  try {
    return fs.realpathSync(left) === fs.realpathSync(right);
  } catch {
    return path.resolve(left) === path.resolve(right);
  }
}

// 不调用 process.exit: 让事件循环在 stdout 排空后自然退出, 避免大输出被截断.
async function runCli() {
  // 帮助在依赖探测之前响应, 没有 node_modules 时也能打印用法并以 0 退出.
  if (HELP_REQUESTED) {
    console.log(usage());
    return;
  }
  // 依赖探测在创建任何目录或文件之前完成, 缺失时只保留失败退出码.
  if (await checkDependencies()) {
    process.exitCode = main();
  }
}

// 只在作为 CLI 运行且 Node.js 版本受支持时执行; 导入模块不进入这里.
if (isMain && NODE_SUPPORTED) {
  await runCli();
}

export { normalizeName, validateName };
