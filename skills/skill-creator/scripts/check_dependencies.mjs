#!/usr/bin/env node
// 检查 skill 目录中的 Node.js 依赖是否可导入.
//
// 依赖按本脚本所在位置解析: scripts/ 的上一级即 skill 目录, Node.js 会从
// 该目录向上查找 node_modules, 因此结果与当前工作目录无关.
// 只探测和报告, 不安装依赖, 不写任何文件.

import process from "node:process";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { DEPENDENCY_PACKAGES } from "./dependency-list.mjs";

// Node.js 版本守卫: 低于 20 时按五段报告停止, 不做后续处理.
// 提前终止只设置退出码, 让事件循环自然退出, 依赖 stderr 的排空.
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

const isMain =
  process.argv[1] !== undefined &&
  isSamePath(process.argv[1], fileURLToPath(import.meta.url));

const SKILL_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(import.meta.url);

// 从清单文件所在目录向上查找包目录.
// 部分包的 exports 不暴露 package.json 子路径, 此时从入口文件所在目录向上查找.
function findPackageDirectory(name, startDirectory) {
  let directory = startDirectory;
  const stop = path.parse(directory).root;
  while (directory !== stop) {
    const manifest = path.join(directory, "package.json");
    if (fs.existsSync(manifest)) {
      let parsed;
      try {
        parsed = JSON.parse(fs.readFileSync(manifest, "utf8"));
      } catch {}
      if (parsed && parsed.name === name) {
        return directory;
      }
    }
    directory = path.dirname(directory);
  }
  return undefined;
}

// 返回包的实际版本和所在目录, 目录一律是真实存在的路径.
function packageInfo(name) {
  try {
    const manifestPath = require.resolve(name + "/package.json");
    const directory = findPackageDirectory(name, path.dirname(manifestPath));
    if (directory !== undefined) {
      const parsed = JSON.parse(
        fs.readFileSync(path.join(directory, "package.json"), "utf8")
      );
      return { version: parsed.version, directory };
    }
  } catch {}
  const directory = findPackageDirectory(
    name,
    path.dirname(require.resolve(name))
  );
  if (directory === undefined) {
    return { version: "版本未知", directory: undefined };
  }
  const parsed = JSON.parse(
    fs.readFileSync(path.join(directory, "package.json"), "utf8")
  );
  return { version: parsed.version, directory };
}

// 报告真实路径, 解析符号链接后避免展示 /private 等别名路径.
function displayPath(directory) {
  try {
    return fs.realpathSync(directory);
  } catch {
    return directory;
  }
}

async function main() {
  const results = [];
  for (const name of DEPENDENCY_PACKAGES) {
    try {
      await import(name);
    } catch (error) {
      results.push({
        name,
        error: error && error.message ? error.message : String(error),
      });
      continue;
    }
    results.push({ name, ...packageInfo(name) });
  }

  const missing = results.filter((result) => result.error !== undefined);

  if (missing.length === 0) {
    console.log(
      "依赖检查通过: " +
        results
          .map(
            (result) =>
              result.name +
              " " +
              result.version +
              (result.directory === undefined
                ? ""
                : " (解析自 " + displayPath(result.directory) + ")")
          )
          .join(", ") +
        "."
    );
    return 0;
  }

  const available = results.filter((result) => result.error === undefined);
  console.error(
    "缺少项: " + missing.map((result) => result.name).join(", ")
  );
  console.error(
    "检测结果: " +
      (available.length > 0
        ? available
            .map((result) => result.name + " " + result.version + " 可导入; ")
            .join("")
        : "未发现可导入的依赖包; ") +
      missing
        .map(
          (result) =>
            result.name + " 导入失败, 原始错误: " + result.error
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
      SKILL_DIR +
      " " +
      DEPENDENCY_PACKAGES.join(" ")
  );
  console.error(
    "影响: 依赖缺失时 validate_skill.mjs 等脚本无法运行, 机械校验需要改为人工核对."
  );
  return 1;
}

function isSamePath(left, right) {
  try {
    return fs.realpathSync(left) === fs.realpathSync(right);
  } catch {
    return path.resolve(left) === path.resolve(right);
  }
}

// 不调用 process.exit: 让事件循环在 stdout/stderr 排空后自然退出, 避免大输出被截断.
// 只在作为 CLI 运行且 Node.js 版本受支持时执行; 导入模块不进入这里,
// 因此导入本身既不产生输出也不设置 process.exitCode.
if (isMain && NODE_SUPPORTED) {
  process.exitCode = await main();
}
