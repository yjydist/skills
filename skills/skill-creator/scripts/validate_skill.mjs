#!/usr/bin/env node
// 校验 Agent Skills 目录的标准符合性.
//
// 默认以错误和警告分级输出. 标准违规为错误, 可移植性和冗余问题为警告.
// 使用 --strict 时警告也会导致非零退出状态.

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { parseArgs } from "node:util";
import { createRequire } from "node:module";
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
function usage() {
  return (
    "用法: node validate_skill.mjs <skill 目录> [--strict] [--verbose] [--help]\n" +
    "校验 Agent Skills 目录的 frontmatter, 字段和本地链接."
  );
}

const isMain =
  process.argv[1] !== undefined &&
  isSamePath(process.argv[1], fileURLToPath(import.meta.url));

// `--` 之后是位置参数, 其中的 `--help` 不请求帮助. 其余位置出现 `--help`
// 或 `-h` 才视为帮助请求.
function helpRequested(args) {
  const separator = args.indexOf("--");
  const end = separator === -1 ? args.length : separator;
  for (let index = 0; index < end; index += 1) {
    const argument = args[index];
    if (argument === "--help" || argument === "-h") {
      return true;
    }
  }
  return false;
}

const HELP_REQUESTED = isMain && helpRequested(process.argv.slice(2));

if (NODE_SUPPORTED && HELP_REQUESTED) {
  console.log(usage());
}

// 版本守卫或 --help 提前终止时不再探测依赖, 也不进入 main.
const BOOTSTRAP = NODE_SUPPORTED && !HELP_REQUESTED;

// 依赖清单来自 dependency-list.mjs, 与其他两个脚本共用同一份.
// 逐包导入, 每个包的失败互不影响, 以便报告实际缺失的包.
async function importDependency(name) {
  try {
    return { name, module: await import(name), error: undefined };
  } catch (error) {
    return { name, module: undefined, error };
  }
}

function dependencyErrorMessage(error) {
  return error && error.message ? error.message : String(error);
}

const dependencyResults = [];
if (BOOTSTRAP) {
  for (const name of DEPENDENCY_PACKAGES) {
    dependencyResults.push(await importDependency(name));
  }
}

const availableDependencies = dependencyResults.filter(
  (result) => result.error === undefined
);
const missingDependencies = dependencyResults.filter(
  (result) => result.error !== undefined
);

// 依赖缺失时打印五段报告.
// 只在作为 CLI 运行时调用: 导入本模块以使用导出函数时不打印报告,
// 也不设置 process.exitCode.
function reportMissingDependencies() {
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
    "影响: 依赖缺失时无法执行机械校验, 需要改为人工核对或等待安装."
  );
}

// 依赖缺失时不进入 main, 由调用处只保留失败退出码.
const CAN_RUN = BOOTSTRAP && missingDependencies.length === 0;

const dependencyModule = (name) =>
  dependencyResults.find((result) => result.name === name)?.module;

const yaml = dependencyModule("yaml");
const { fromMarkdown } = dependencyModule("mdast-util-from-markdown") ?? {};
const { decodeNamedCharacterReference } =
  dependencyModule("decode-named-character-reference") ?? {};

const require = createRequire(import.meta.url);
const YAML_VERSION = CAN_RUN ? require("yaml/package.json").version : undefined;

const STANDARD_FIELDS = new Set([
  "name",
  "description",
  "license",
  "compatibility",
  "metadata",
  "allowed-tools",
]);

const MAX_NAME_LENGTH = 64;
const MAX_DESCRIPTION_LENGTH = 1024;
const MAX_COMPATIBILITY_LENGTH = 500;
const MAX_BODY_LINES = 500;

const ESCAPABLE_PUNCTUATION = new Set(
  "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
);

const HTML_LINK_TAG_PATTERN = /<(a|img)(?=[\s/>])/gi;
// 行内 HTML 标签可以跨行 (例如 `<a\nhref="x">`), 但扫描必须有界:
// 从标签名之后到 `>` 的总长度超过该上限就放弃, 避免未闭合的 `<a` 吃掉全文.
const MAX_HTML_TAG_LENGTH = 2048;

const WINDOWS_PATH_PATTERN = /^(?:[A-Za-z]:|\\\\)/;
const WINDOWS_FORWARD_UNC_PATTERN = /^\/\/[^/\s.:]+\/[^/\s]+/;
const SCHEME_PATTERN = /^[A-Za-z][A-Za-z0-9+.-]*:/;
const CONTROL_CHARACTER_PATTERN = /\p{Cc}/u;
const ALNUM_PATTERN = /^[\p{L}\p{N}]$/u;
const ALLOWED_NAME_PATTERN = /^[\p{L}\p{N}-]+$/u;
const PYTHON_SPACE_PATTERN = /[\s\u001c-\u001f]/u;

// 本校验器的约定: 这些路径分量视作依赖目录, 未引用扫描跳过. 不是 Agent Skills 标准要求.
const DEPENDENCY_DIRECTORIES = new Set([
  "node_modules",
  "vendor",
  "third_party",
  "venv",
  "virtualenv",
  "site-packages",
]);

class FrontmatterError extends Error {
  constructor(message, line = null) {
    super(message);
    this.name = "FrontmatterError";
    this.line = line;
  }
}

class Issue {
  constructor(location, message) {
    this.location = location;
    this.message = message;
  }

  render() {
    return this.location ? this.location + ": " + this.message : this.message;
  }
}

function codePointLength(value) {
  return [...value].length;
}

function normalizeName(value) {
  return value.normalize("NFKC").trim();
}

function validateName(name) {
  const normalized = normalizeName(name);
  if (!normalized) {
    return "name 归一化后为空";
  }
  if (codePointLength(normalized) > MAX_NAME_LENGTH) {
    return (
      "name 长度必须在 1-" +
      MAX_NAME_LENGTH +
      " 字符之间, 当前为 " +
      codePointLength(normalized) +
      " 字符"
    );
  }
  if (normalized !== normalized.toLowerCase()) {
    return "name 必须全部为小写字母";
  }
  if (normalized.startsWith("-") || normalized.endsWith("-")) {
    return "name 不能以连字符开头或结尾";
  }
  if (normalized.includes("--")) {
    return "name 不能包含连续连字符";
  }
  if (!ALLOWED_NAME_PATTERN.test(normalized)) {
    return "name 只能包含小写字母, 数字和连字符";
  }
  return null;
}

function splitFrontmatter(text) {
  text = text.replace(/^\uFEFF/u, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = text.split("\n");
  if (lines.length === 0 || lines[0].replace(/[ \t]+$/u, "") !== "---") {
    throw new FrontmatterError(
      "SKILL.md 必须以 YAML frontmatter 开头, 第一行应为 ---",
      1
    );
  }
  for (let index = 1; index < lines.length; index += 1) {
    if (lines[index].replace(/\s+$/u, "") === "---") {
      return {
        frontmatterLines: lines.slice(1, index),
        body: lines.slice(index + 1).join("\n"),
        bodyStart: index + 2,
      };
    }
  }
  throw new FrontmatterError("frontmatter 缺少结束标记 ---", lines.length);
}

function firstErrorLine(error, firstLine) {
  const line = error && error.linePos && error.linePos[0] && error.linePos[0].line;
  return line ? firstLine + line - 1 : firstLine;
}

function firstErrorMessage(error) {
  const message = error && error.message ? error.message : String(error);
  return message.split("\n")[0].replace(/ at line \d+, column \d+:$/u, "");
}

// toJS 遇到未定义锚点会直接抛出 ReferenceError, 不带 linePos. 按错误中的别名
// 名称在 AST 中查找第一个 Alias 节点, 用它的 range 还原 frontmatter 行号.
function unresolvedAliasLine(document, error, firstLine, lineCounter) {
  const match = /Unresolved alias \(the anchor must be set before the alias\): (.+)$/u.exec(
    firstErrorMessage(error)
  );
  if (match === null) {
    return null;
  }
  const name = match[1];
  const pending = [document.contents];
  const seen = new Set();
  while (pending.length > 0) {
    const node = pending.pop();
    if (node === null || typeof node !== "object" || seen.has(node)) {
      continue;
    }
    seen.add(node);
    if (yaml.isAlias(node) && node.source === name && node.range) {
      const position = lineCounter.linePos(node.range[0]);
      return firstLine + position.line - 1;
    }
    if (Array.isArray(node.items)) {
      pending.push(...node.items);
    }
    if (node.key !== undefined) {
      pending.push(node.key);
    }
    if (node.value !== undefined) {
      pending.push(node.value);
    }
    if (node.contents !== undefined) {
      pending.push(node.contents);
    }
  }
  return null;
}

function parseFrontmatter(frontmatterText, firstLine = 2) {
  const normalized = frontmatterText
    .replace(/^\uFEFF/u, "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");
  if (normalized.trim() === "") {
    return { data: new Map(), parser: "yaml " + YAML_VERSION, keyLines: new Map() };
  }

  const lineCounter = new yaml.LineCounter();
  const document = yaml.parseDocument(normalized, {
    lineCounter,
    prettyErrors: true,
    schema: "core",
  });
  if (document.errors.length > 0) {
    const error = document.errors[0];
    throw new FrontmatterError(
      "无法解析 frontmatter: " + firstErrorMessage(error),
      firstErrorLine(error, firstLine)
    );
  }
  if (document.contents === null) {
    return { data: new Map(), parser: "yaml " + YAML_VERSION, keyLines: new Map() };
  }

  let data;
  try {
    data = document.toJS({ mapAsMap: true });
  } catch (error) {
    const aliasLine = unresolvedAliasLine(
      document,
      error,
      firstLine,
      lineCounter
    );
    throw new FrontmatterError(
      "无法解析 frontmatter: " + firstErrorMessage(error),
      aliasLine === null ? firstErrorLine(error, firstLine) : aliasLine
    );
  }
  if (!(data instanceof Map)) {
    throw new FrontmatterError("frontmatter 必须是键值映射", firstLine);
  }

  const keyLines = new Map();
  if (document.contents && Array.isArray(document.contents.items)) {
    for (const pair of document.contents.items) {
      const source = pair.key && pair.key.range ? pair.key.range[0] : pair.range[0];
      const position = lineCounter.linePos(source);
      const key =
        pair.key && "value" in pair.key ? pair.key.value : pair.key;
      keyLines.set(key, firstLine + position.line - 1);
    }
  }

  return { data, parser: "yaml " + YAML_VERSION, keyLines };
}

function pythonString(value) {
  if (value === null) {
    return "None";
  }
  if (value === true) {
    return "True";
  }
  if (value === false) {
    return "False";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return String(value);
    }
    return String(value);
  }
  if (value instanceof Map) {
    return "{...}";
  }
  if (Array.isArray(value)) {
    return "[...]";
  }
  return String(value);
}

function isMapping(value) {
  return value instanceof Map;
}

function validateFields(data, keyLines, skillName, errors, warnings) {
  const location = (field) =>
    "SKILL.md:" + (keyLines.has(field) ? keyLines.get(field) : 2);

  const name = data.get("name");
  if (name === undefined || name === null) {
    errors.push(new Issue(location("name"), "缺少 name 字段"));
  } else if (typeof name !== "string") {
    errors.push(new Issue(location("name"), "name 必须是字符串"));
  } else {
    const problem = validateName(name);
    if (problem) {
      errors.push(new Issue(location("name"), problem));
    }
    if (normalizeName(name) !== skillName.normalize("NFKC")) {
      errors.push(
        new Issue(
          location("name"),
          "name 与父目录名不一致: " + name + " != " + skillName
        )
      );
    }
  }

  const description = data.get("description");
  if (description === undefined || description === null) {
    errors.push(new Issue(location("description"), "缺少 description 字段"));
  } else if (typeof description !== "string") {
    errors.push(new Issue(location("description"), "description 必须是字符串"));
  } else if (description.trim() === "") {
    errors.push(new Issue(location("description"), "description 不能为空"));
  } else if (codePointLength(description) > MAX_DESCRIPTION_LENGTH) {
    errors.push(
      new Issue(
        location("description"),
        "description 不能超过 " +
          MAX_DESCRIPTION_LENGTH +
          " 字符, 当前为 " +
          codePointLength(description) +
          " 字符"
      )
    );
  }

  if (data.has("license")) {
    if (typeof data.get("license") !== "string") {
      errors.push(new Issue(location("license"), "license 必须是字符串"));
    }
  }

  if (data.has("compatibility")) {
    const value = data.get("compatibility");
    if (typeof value !== "string") {
      errors.push(new Issue(location("compatibility"), "compatibility 必须是字符串"));
    } else if (
      codePointLength(value) < 1 ||
      codePointLength(value) > MAX_COMPATIBILITY_LENGTH
    ) {
      errors.push(
        new Issue(
          location("compatibility"),
          "compatibility 长度必须在 1-" +
            MAX_COMPATIBILITY_LENGTH +
            " 字符之间, 当前为 " +
            codePointLength(value) +
            " 字符"
        )
      );
    }
  }

  if (data.has("metadata")) {
    const value = data.get("metadata");
    if (!isMapping(value)) {
      errors.push(new Issue(location("metadata"), "metadata 必须是键值映射"));
    } else {
      for (const [key, item] of value.entries()) {
        if (typeof key !== "string") {
          errors.push(new Issue(location("metadata"), "metadata 的键必须是字符串"));
          continue;
        }
        if (typeof item !== "string") {
          errors.push(
            new Issue(location("metadata"), "metadata." + key + " 的值必须是字符串")
          );
        }
      }
    }
  }

  if (data.has("allowed-tools")) {
    const value = data.get("allowed-tools");
    if (typeof value !== "string") {
      errors.push(new Issue(location("allowed-tools"), "allowed-tools 必须是字符串"));
    } else {
      const invalid = [...value].some(
        (character) =>
          character === "," ||
          character === ";" ||
          (character !== " " && PYTHON_SPACE_PATTERN.test(character))
      );
      if (value.split(/\s+/u).filter(Boolean).length === 0 || invalid) {
        errors.push(
          new Issue(
            location("allowed-tools"),
            "allowed-tools 必须是空格分隔的工具名字符串"
          )
        );
      }
    }
  }

  for (const key of data.keys()) {
    if (typeof key !== "string" || !STANDARD_FIELDS.has(key)) {
      const line = typeof key === "string" && keyLines.has(key) ? keyLines.get(key) : 2;
      warnings.push(
        new Issue("SKILL.md:" + line, "非标准字段: " + pythonString(key))
      );
    }
  }
}

function walk(node, parent, callback) {
  callback(node, parent);
  if (Array.isArray(node.children)) {
    for (const child of node.children) {
      walk(child, node, callback);
    }
  }
}

function stripHtmlComments(value) {
  return value.replace(/<!--[\s\S]*?(?:-->|$)/g, "");
}

// 注释替换为等长空白并保留换行, 使 Node 偏移仍能映射回原文的绝对行号.
function blankHtmlComments(value) {
  return value.replace(/<!--[\s\S]*?(?:-->|$)/g, (comment) =>
    comment.replace(/[^\n\r]/g, " ")
  );
}

function hasVisibleContent(node) {
  if (node.type === "text") {
    return node.value.trim() !== "";
  }
  if (node.type === "html") {
    return stripHtmlComments(node.value).trim() !== "";
  }
  if (node.type === "code" || node.type === "inlineCode") {
    return true;
  }
  if (Array.isArray(node.children)) {
    return node.children.some(hasVisibleContent);
  }
  return true;
}

function hasBodyContent(body) {
  let tree;
  try {
    tree = fromMarkdown(body);
  } catch {
    tree = null;
  }
  if (tree && tree.children.some(hasVisibleContent)) {
    return true;
  }
  // AST 认为没有内容时, 用兜底扫描确认是否只剩注释. 代码块已在 AST 中计为内容.
  return stripHtmlComments(body).trim() !== "";
}

function bodyLineCount(body) {
  const lines = body.split(/\r\n|[\n\r\v\f\u001c-\u001e\u0085\u2028\u2029]/u);
  if (lines.length > 0 && lines[lines.length - 1] === "") {
    lines.pop();
  }
  let start = 0;
  while (start < lines.length && lines[start].trim() === "") {
    start += 1;
  }
  return lines.length - start;
}

function buildLineStarts(text) {
  const starts = [0];
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === "\n") {
      starts.push(index + 1);
    }
  }
  return starts;
}

function lineAtOffset(lineStarts, offset) {
  let low = 0;
  let high = lineStarts.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (lineStarts[middle] <= offset) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return low;
}

function unescapeMarkdown(value) {
  let result = "";
  let index = 0;
  while (index < value.length) {
    const character = value[index];
    if (
      character === "\\" &&
      index + 1 < value.length &&
      ESCAPABLE_PUNCTUATION.has(value[index + 1])
    ) {
      result += value[index + 1];
      index += 2;
      continue;
    }
    result += character;
    index += 1;
  }
  return result;
}

function skipLinkSpace(text, index) {
  while (index < text.length && " \t\r\n".includes(text[index])) {
    index += 1;
  }
  return index;
}

function findLabelEnd(text, start) {
  let depth = 0;
  let index = start;
  while (index < text.length) {
    const character = text[index];
    if (character === "\\") {
      index += 2;
      continue;
    }
    if (character === "[") {
      depth += 1;
    } else if (character === "]") {
      depth -= 1;
      if (depth === 0) {
        return index;
      }
    }
    index += 1;
  }
  return -1;
}

function findTitleEnd(text, start) {
  const closer = text[start] === "(" ? ")" : text[start];
  let index = start + 1;
  while (index < text.length) {
    const character = text[index];
    if (character === "\\") {
      index += 2;
      continue;
    }
    if (character === closer) {
      return index + 1;
    }
    index += 1;
  }
  return -1;
}

function parseLinkDestination(text, start) {
  const size = text.length;
  let index = skipLinkSpace(text, start);
  if (index >= size) {
    return null;
  }
  let target;
  let after;
  if (text[index] === "<") {
    let end = index + 1;
    while (end < size) {
      const character = text[end];
      if (character === "\\") {
        if (end + 1 < size && ESCAPABLE_PUNCTUATION.has(text[end + 1])) {
          end += 2;
          continue;
        }
        end += 1;
        continue;
      }
      if (character === "<") {
        return null;
      }
      if (character === ">") {
        break;
      }
      end += 1;
    }
    if (end >= size) {
      return null;
    }
    target = text.slice(index + 1, end);
    after = end + 1;
  } else {
    let end = index;
    let depth = 0;
    while (end < size) {
      const character = text[end];
      if (character === "\\") {
        const following = end + 1 < size ? text[end + 1] : "";
        if (following && ESCAPABLE_PUNCTUATION.has(following)) {
          end += 2;
          continue;
        }
        if (!following || " \t\r\n".includes(following)) {
          break;
        }
        end += 1;
        continue;
      }
      if (" \t\r\n".includes(character)) {
        break;
      }
      if (character === "(") {
        depth += 1;
      } else if (character === ")") {
        if (depth === 0) {
          break;
        }
        depth -= 1;
      }
      end += 1;
    }
    if (end === index || depth !== 0) {
      return null;
    }
    target = text.slice(index, end);
    after = end;
  }

  let spaced = skipLinkSpace(text, after);
  if (spaced > after && spaced < size && "\"'(".includes(text[spaced])) {
    const titleEnd = findTitleEnd(text, spaced);
    if (titleEnd < 0) {
      return null;
    }
    spaced = skipLinkSpace(text, titleEnd);
  }
  if (spaced >= size || text[spaced] !== ")") {
    return null;
  }
  return [unescapeMarkdown(target), spaced + 1];
}

function scanReferenceLabels(text) {
  const labels = [];
  let index = 0;
  const size = text.length;
  while (index < size) {
    const character = text[index];
    if (character === "\\") {
      index += 2;
      continue;
    }
    let bracket;
    if (character === "!" && text[index + 1] === "[") {
      bracket = index + 1;
    } else if (character === "[") {
      bracket = index;
    } else {
      index += 1;
      continue;
    }
    const labelEnd = findLabelEnd(text, bracket);
    if (labelEnd < 0) {
      index = bracket + 1;
      continue;
    }
    if (text[labelEnd + 1] === "(") {
      const parsed = parseLinkDestination(text, labelEnd + 2);
      if (parsed !== null) {
        index = parsed[1];
        continue;
      }
      index = bracket + 1;
      continue;
    }
    if (text[labelEnd + 1] === "[") {
      const referenceEnd = findLabelEnd(text, labelEnd + 1);
      if (referenceEnd >= 0) {
        const identifier = text.slice(labelEnd + 2, referenceEnd).trim();
        if (identifier && !identifier.startsWith("^")) {
          labels.push([bracket, identifier]);
        }
        index = referenceEnd + 1;
        continue;
      }
    }
    index = bracket + 1;
  }
  return labels;
}

function casefold(value) {
  return value.toUpperCase().toLowerCase();
}

function normalizeReferenceLabel(label) {
  return casefold(label.trim().split(/\s+/u).filter(Boolean).join(" "));
}

function maskRanges(text, ranges) {
  const characters = text.split("");
  for (const [start, stop] of ranges) {
    for (let index = Math.max(0, start); index < Math.min(stop, characters.length); index += 1) {
      if (characters[index] !== "\n" && characters[index] !== "\r") {
        characters[index] = " ";
      }
    }
  }
  return characters.join("");
}

function isEscapedAt(value, index) {
  let backslashes = 0;
  let cursor = index - 1;
  while (cursor >= 0 && value[cursor] === "\\") {
    backslashes += 1;
    cursor -= 1;
  }
  return backslashes % 2 === 1;
}

// 属性值可带引号, 引号内的 `>` 与换行都不结束标签; 标签可跨行,
// 但从标签名之后到 `>` 的总长度受 MAX_HTML_TAG_LENGTH 限制.
function readHtmlTagEnd(value, start) {
  let quote = null;
  let index = start;
  while (index < value.length && index - start <= MAX_HTML_TAG_LENGTH) {
    const character = value[index];
    if (quote !== null) {
      if (character === quote) {
        quote = null;
      }
    } else if (character === '"' || character === "'") {
      quote = character;
    } else if (character === ">") {
      return index;
    }
    index += 1;
  }
  return -1;
}

function readHtmlAttributeValue(body, start) {
  let index = start;
  while (index < body.length && /\s/u.test(body[index])) {
    index += 1;
  }
  const quote = body[index];
  if (quote === '"' || quote === "'") {
    const end = body.indexOf(quote, index + 1);
    if (end === -1) {
      return null;
    }
    return {
      value: body.slice(index + 1, end),
      start: index + 1,
      end: end + 1,
    };
  }
  let end = index;
  while (end < body.length && !/[\s"'=<>`]/u.test(body[end])) {
    end += 1;
  }
  if (end === index) {
    return null;
  }
  return { value: body.slice(index, end), start: index, end };
}

function collectHtmlAttributeTargets(body, attributeName) {
  const targets = [];
  let index = 0;
  while (index < body.length) {
    while (index < body.length && /\s/u.test(body[index])) {
      index += 1;
    }
    if (index >= body.length) {
      break;
    }
    if (body[index] === "/") {
      index += 1;
      continue;
    }
    const nameStart = index;
    while (index < body.length && !/[\s=/>]/u.test(body[index])) {
      index += 1;
    }
    const name = body.slice(nameStart, index).toLowerCase();
    while (index < body.length && /\s/u.test(body[index])) {
      index += 1;
    }
    if (body[index] !== "=") {
      continue;
    }
    const parsed = readHtmlAttributeValue(body, index + 1);
    if (parsed === null) {
      break;
    }
    index = parsed.end;
    if (name === attributeName) {
      targets.push({ value: parsed.value, start: parsed.start });
    }
  }
  return targets;
}

function scanHtmlAttributeLinks(value, startOffset, lineStarts) {
  const pattern = new RegExp(HTML_LINK_TAG_PATTERN.source, "gi");
  const found = [];
  let match;
  while ((match = pattern.exec(value)) !== null) {
    const tagStart = match.index;
    if (isEscapedAt(value, tagStart)) {
      continue;
    }
    const tagEnd = readHtmlTagEnd(value, pattern.lastIndex);
    if (tagEnd === -1) {
      continue;
    }
    const attributeName = match[1].toLowerCase() === "a" ? "href" : "src";
    const targets = collectHtmlAttributeTargets(
      value.slice(pattern.lastIndex, tagEnd),
      attributeName
    );
    for (const target of targets) {
      // 属性可写在标签内的任意一行, 行号取属性值自身所在行.
      const targetOffset = startOffset + pattern.lastIndex + target.start;
      found.push({
        line: lineAtOffset(lineStarts, targetOffset),
        url: target.value,
        offset: startOffset + tagStart,
      });
    }
    pattern.lastIndex = tagEnd + 1;
  }
  return found;
}

function isAsciiPunctuation(character) {
  return character !== undefined && /^[!-/:-@[-`{-~]$/u.test(character);
}

// 目标前的空白: 空格与制表符, 以及最多一个换行及其续行缩进. 续行缩进不限
// 空格或制表符 (段落与定义的续行位置不会成为缩进代码块), 但只允许一个换行;
// 目标自身仍不能跨行, 解析循环照旧拒绝目标内部的换行.
function skipTargetSpace(value, start) {
  let index = start;
  while (index < value.length && (value[index] === " " || value[index] === "\t")) {
    index += 1;
  }
  if (index >= value.length) {
    return index;
  }
  if (value[index] === "\r" && value[index + 1] === "\n") {
    index += 2;
  } else if (value[index] === "\n" || value[index] === "\r") {
    index += 1;
  } else {
    return index;
  }
  while (index < value.length && (value[index] === " " || value[index] === "\t")) {
    index += 1;
  }
  return index;
}

function readInlineTargetAt(value, start) {
  const index = skipTargetSpace(value, start);
  if (index >= value.length) {
    return null;
  }
  if (value[index] === "<") {
    const bodyStart = index + 1;
    let cursor = bodyStart;
    // 目标不跨行 (遇换行即放弃), 因此扫描由行边界自然限制, 无需长度上限.
    while (cursor < value.length) {
      const character = value[cursor];
      if (character === "\n" || character === "\r") {
        return null;
      }
      if (character === "\\" && isAsciiPunctuation(value[cursor + 1])) {
        cursor += 2;
        continue;
      }
      if (character === ">") {
        return { target: value.slice(bodyStart, cursor) };
      }
      cursor += 1;
    }
    return null;
  }
  const bodyStart = index;
  let depth = 0;
  let cursor = bodyStart;
  while (cursor < value.length) {
    const character = value[cursor];
    if (character === "\n" || character === "\r") {
      return null;
    }
    if (character === "\\" && isAsciiPunctuation(value[cursor + 1])) {
      cursor += 2;
      continue;
    }
    if (character === "(") {
      depth += 1;
    } else if (character === ")") {
      if (depth === 0) {
        return { target: value.slice(bodyStart, cursor) };
      }
      depth -= 1;
    } else if ((character === " " || character === "\t") && depth === 0) {
      return { target: value.slice(bodyStart, cursor) };
    }
    cursor += 1;
  }
  return null;
}

// 换行处向前看上一行是否为空行 (只有空格与制表符). 空行结束段落, 链接文本
// 不能跨过它. 到达文本开头时同样视为段落起始.
function isBlankLineBefore(value, newlineIndex) {
  let cursor = newlineIndex - 1;
  while (cursor >= 0 && (value[cursor] === " " || value[cursor] === "\t")) {
    cursor -= 1;
  }
  if (cursor < 0) {
    return true;
  }
  return value[cursor] === "\n" || value[cursor] === "\r";
}

// 只有 `]` 前存在未转义的 `[` (含 `![`) 才是行内链接的标签结尾;
// 普通文本中的 `foo](目标)` 不按链接处理. 方括号按嵌套深度配对.
// 链接文本可以跨行 (CommonMark 允许), 因此回溯跨过换行; 但不能跨空行,
// 回溯会在空行或文本开头处停止, 因此不会吃掉全文, 无需长度上限.
function inlineLabelStart(value, close) {
  let depth = 0;
  let index = close - 1;
  while (index >= 0) {
    const character = value[index];
    if (character === "\n" || character === "\r") {
      const pair = character === "\n" && value[index - 1] === "\r";
      if (isBlankLineBefore(value, pair ? index - 1 : index)) {
        return -1;
      }
      index -= pair ? 2 : 1;
      continue;
    }
    if (character === "]" && !isEscapedAt(value, index)) {
      depth += 1;
    } else if (character === "[" && !isEscapedAt(value, index)) {
      if (depth === 0) {
        return index;
      }
      depth -= 1;
    }
    index -= 1;
  }
  return -1;
}

function scanRawInlineTargets(masked, lineStarts) {
  const found = [];
  const keys = new Set();
  let index = 0;
  while (index < masked.length) {
    const close = masked.indexOf("]", index);
    if (close < 0) {
      break;
    }
    // 只有 `](` 才可能是行内链接; 先做这项廉价判断, 再回溯查找标签起始,
    // 避免为文档里的每个 `]` 都向前扫描.
    if (masked[close + 1] !== "(" || isEscapedAt(masked, close)) {
      index = close + 1;
      continue;
    }
    const labelStart = inlineLabelStart(masked, close);
    if (labelStart < 0) {
      index = close + 1;
      continue;
    }
    const parsed = readInlineTargetAt(masked, close + 2);
    if (parsed === null) {
      index = close + 1;
      continue;
    }
    const target = decodedFullTarget(parsed.target);
    if (CONTROL_CHARACTER_PATTERN.test(target)) {
      // 目标可以另起一行; 行号仍取链接起始行, 与 mdast 节点的 start.line 和
      // Python 基准一致.
      const line = lineAtOffset(lineStarts, labelStart);
      const key = line + "\u0000" + target;
      if (!keys.has(key)) {
        keys.add(key);
        found.push({ line, target, raw: parsed.target });
      }
    }
    index = close + 1;
  }
  return found;
}

// 定义目标没有闭合括号, 到行尾或空白结束: `[标签]: 目标 "标题"`. 冒号后的
// 目标也可以另起一行 (CommonMark 允许), 缩进按上面的续行规则跳过. 返回值带上
// 目标的结束偏移 `end`, 供调用方检查目标行剩余部分是否只有可选标题.
function readDefinitionTargetAt(value, start) {
  const index = skipTargetSpace(value, start);
  if (index >= value.length) {
    return null;
  }
  if (value[index] === "<") {
    const bodyStart = index + 1;
    let cursor = bodyStart;
    // 目标不跨行 (遇换行即放弃), 因此扫描由行边界自然限制, 无需长度上限.
    while (cursor < value.length) {
      const character = value[cursor];
      if (character === "\n" || character === "\r") {
        return null;
      }
      if (character === "\\" && isAsciiPunctuation(value[cursor + 1])) {
        cursor += 2;
        continue;
      }
      if (character === "<") {
        return null;
      }
      if (character === ">") {
        return { target: value.slice(bodyStart, cursor), end: cursor + 1 };
      }
      cursor += 1;
    }
    return null;
  }
  const bodyStart = index;
  let depth = 0;
  let cursor = bodyStart;
  while (cursor < value.length) {
    const character = value[cursor];
    if (
      character === "\n" ||
      character === "\r" ||
      character === " " ||
      character === "\t"
    ) {
      break;
    }
    if (character === "\\" && isAsciiPunctuation(value[cursor + 1])) {
      cursor += 2;
      continue;
    }
    if (character === "(") {
      depth += 1;
    } else if (character === ")") {
      if (depth === 0) {
        break;
      }
      depth -= 1;
    }
    cursor += 1;
  }
  if (cursor === bodyStart) {
    return null;
  }
  return { target: value.slice(bodyStart, cursor), end: cursor };
}

// 目标之后到行尾只允许空白, 或一个合法标题 (`"..."`, `'...'`, `(...)`) 再加
// 空白. 其他尾随文本 (例如 `多余文本`) 会让整行不构成定义. 标题必须与目标同
// 行, 因此先按行切片再用 findTitleEnd 配对, 不跨行误判.
function definitionTargetTailIsValid(value, end) {
  let lineEnd = end;
  while (
    lineEnd < value.length &&
    value[lineEnd] !== "\n" &&
    value[lineEnd] !== "\r"
  ) {
    lineEnd += 1;
  }
  const line = value.slice(end, lineEnd);
  let cursor = 0;
  while (cursor < line.length && (line[cursor] === " " || line[cursor] === "\t")) {
    cursor += 1;
  }
  if (cursor >= line.length) {
    return true;
  }
  if (!"\"'(".includes(line[cursor])) {
    return false;
  }
  const titleEnd = findTitleEnd(line, cursor);
  if (titleEnd < 0) {
    return false;
  }
  cursor = titleEnd;
  while (cursor < line.length && (line[cursor] === " " || line[cursor] === "\t")) {
    cursor += 1;
  }
  return cursor >= line.length;
}

// 已被 mdast 解析的定义范围会随标签遮蔽, 原始目标需按节点范围回读, 才能看到
// 被解码成 U+FFFD 之前的控制字符.
function parsedDefinitionTarget(value, start, end) {
  let cursor = value.indexOf("]", start + 1);
  while (cursor >= 0 && cursor < end) {
    if (!isEscapedAt(value, cursor) && value[cursor + 1] === ":") {
      return readDefinitionTargetAt(value, cursor + 2);
    }
    cursor = value.indexOf("]", cursor + 1);
  }
  return null;
}

// 从定义行的 `]` 向前找标签起始的 `[`. 标签内不允许未转义的 `]`, 也不能跨行.
function definitionLabelStart(value, close) {
  let index = close - 1;
  while (index >= 0) {
    const character = value[index];
    if (character === "\n" || character === "\r") {
      return -1;
    }
    if (character === "]" && !isEscapedAt(value, index)) {
      return -1;
    }
    if (character === "[" && !isEscapedAt(value, index)) {
      return index;
    }
    index -= 1;
  }
  return -1;
}

// 引用式定义只能出现在块首: 行首最多 3 个空格, 或列表项标记/块引用前缀之后.
// 前缀可以交替嵌套 (`> - [标签]: 目标`). 行内文本与标题里的 `[x]:` 不是定义,
// 标题前缀 (`# `) 不属于这些前缀, 因此保留在剩余文本中而被排除.
const DEFINITION_BLOCKQUOTE_PREFIX_PATTERN = /^ {0,3}>[ \t]?/;
const DEFINITION_LIST_ITEM_PREFIX_PATTERN =
  /^ {0,3}(?:[+*-]|\d{1,9}[.)])[ \t]+/;

function isInsideListRange(listItemRanges, offset) {
  for (const [start, stop] of listItemRanges) {
    if (offset > start && offset < stop) {
      return true;
    }
  }
  return false;
}

function isDefinitionBlockStart(value, labelStart, listItemRanges) {
  let lineStart = labelStart;
  while (lineStart > 0) {
    const previous = value[lineStart - 1];
    if (previous === "\n" || previous === "\r") {
      break;
    }
    lineStart -= 1;
  }
  // 列表项内容的续行按 CommonMark 规则缩进到标记宽度之后 (通常 2-4 个空格),
  // 这类缩进不出现在首行前缀模式里. 所在行属于列表项时按内容缩进剥离, 再识别
  // 同一行的块引用/嵌套列表前缀; 缩进代码块已被遮蔽, 不会进入原始扫描.
  const inListItem = isInsideListRange(listItemRanges, labelStart);
  let prefix = value.slice(lineStart, labelStart);
  for (;;) {
    const blockquote = DEFINITION_BLOCKQUOTE_PREFIX_PATTERN.exec(prefix);
    if (blockquote !== null) {
      prefix = prefix.slice(blockquote[0].length);
      continue;
    }
    const listItem = DEFINITION_LIST_ITEM_PREFIX_PATTERN.exec(prefix);
    if (listItem !== null) {
      prefix = prefix.slice(listItem[0].length);
      continue;
    }
    if (inListItem) {
      const indentation = /^[ \t]+/.exec(prefix);
      if (indentation !== null) {
        prefix = prefix.slice(indentation[0].length);
        continue;
      }
    }
    break;
  }
  return /^ {0,3}$/.test(prefix);
}

// 定义不能打断段落: `正文\n[ref]: 目标` 里的 `[ref]: 目标` 只是上一段的续行.
// 段落范围来自 mdast, 只用于排除原始扫描的候选行; 已解析的定义不在段落内.
// 段落首行本身不是续行: 列表项里的排印缩进会让标签起始偏移大于段落起始偏移,
// 因此按行比较, 同一行上的标签仍可能是定义.
function isParagraphContinuation(paragraphRanges, lineStarts, offset) {
  const line = lineAtOffset(lineStarts, offset);
  for (const [start, stop] of paragraphRanges) {
    if (
      offset > start &&
      offset < stop &&
      lineAtOffset(lineStarts, start) !== line
    ) {
      return true;
    }
  }
  return false;
}

// 控制字符会让 CommonMark 放弃整条定义, 因此对 `]:` 后的目标另做原始文本扫描.
// 只收集含控制字符的目标; 脚注定义 (`[^1]: 目标`) 不是引用式链接, 直接跳过.
function scanRawDefinitionTargets(
  masked,
  lineStarts,
  paragraphRanges,
  listItemRanges
) {
  const found = [];
  const keys = new Set();
  let index = 0;
  while (index < masked.length) {
    const close = masked.indexOf("]", index);
    if (close < 0) {
      break;
    }
    index = close + 1;
    if (masked[close + 1] !== ":" || isEscapedAt(masked, close)) {
      continue;
    }
    const start = definitionLabelStart(masked, close);
    if (
      start < 0 ||
      !isDefinitionBlockStart(masked, start, listItemRanges) ||
      isParagraphContinuation(paragraphRanges, lineStarts, start)
    ) {
      continue;
    }
    const label = masked.slice(start + 1, close);
    if (label.startsWith("^")) {
      continue;
    }
    const parsed = readDefinitionTargetAt(masked, close + 2);
    if (
      parsed === null ||
      !definitionTargetTailIsValid(masked, parsed.end)
    ) {
      continue;
    }
    const target = decodedFullTarget(parsed.target);
    if (!CONTROL_CHARACTER_PATTERN.test(target)) {
      continue;
    }
    // 目标可以另起一行; 行号仍取定义起始行, 与 Python 基准一致.
    const line = lineAtOffset(lineStarts, start);
    const key = line + "\u0000" + target;
    if (keys.has(key)) {
      continue;
    }
    keys.add(key);
    found.push({ line, target, raw: parsed.target, label });
  }
  return found;
}

function collectMarkdown(text) {
  const tree = fromMarkdown(text);
  const lineStarts = buildLineStarts(text);
  const inline = [];
  const definitions = [];
  const htmlLinks = [];
  const maskedRanges = [];
  const paragraphRanges = [];
  const listItemRanges = [];
  const blockParents = new Set(["root", "listItem", "blockquote"]);

  walk(tree, null, (node, parent) => {
    if (node.type === "paragraph") {
      paragraphRanges.push([
        node.position.start.offset,
        node.position.end.offset,
      ]);
    }
    if (node.type === "listItem") {
      listItemRanges.push([
        node.position.start.offset,
        node.position.end.offset,
      ]);
    }
    if (node.type === "code" || node.type === "inlineCode") {
      maskedRanges.push([node.position.start.offset, node.position.end.offset]);
      return;
    }
    if (node.type === "html" || node.type === "text") {
      if (node.type === "html") {
        maskedRanges.push([node.position.start.offset, node.position.end.offset]);
      }
      const inlineNode = parent !== null && !blockParents.has(parent.type);
      if (inlineNode) {
        const value =
          node.type === "html"
            ? blankHtmlComments(node.value)
            : text.slice(node.position.start.offset, node.position.end.offset);
        htmlLinks.push(
          ...scanHtmlAttributeLinks(
            value,
            node.position.start.offset,
            lineStarts
          )
        );
      }
      return;
    }
    if (node.type === "definition") {
      // 脚注定义 (`[^1]: 目标`) 不是引用式链接定义, 不参与链接检查和互引检查;
      // 仍遮蔽其文本范围, 避免目标被后续扫描当作行内目标.
      if (typeof node.identifier === "string" && node.identifier.startsWith("^")) {
        maskedRanges.push([node.position.start.offset, node.position.end.offset]);
        return;
      }
      definitions.push({
        line: node.position.start.line,
        offset: node.position.start.offset,
        end: node.position.end.offset,
        url: decodeMarkdownUrl(node.url),
        identifier: node.identifier,
      });
      maskedRanges.push([node.position.start.offset, node.position.end.offset]);
      return;
    }
    if (node.type === "link" || node.type === "image") {
      inline.push({
        line: node.position.start.line,
        offset: node.position.start.offset,
        url: decodeMarkdownUrl(node.url),
      });
    }
  });

  inline.sort((left, right) => left.offset - right.offset);

  const seen = new Set();
  const links = [];
  // mdast 的 link/definition 目标已由 decodeMarkdownUrl 处理 (CommonMark 的带
  // 分号解码加无分号补解); 原始扫描得到的 HTML 属性目标仍是原文, 还要整体
  // 解码一次. entitiesDecoded 记录这一区别, 避免 mdast 目标被二次解码
  // (`&amp;amp;` 变成 `&` 而不是 `&amp;`).
  const addLink = (line, url, entitiesDecoded) => {
    // 去重键用解码后的完整目标, 同一行内实体与百分号混写的同一目标
    // (`a&b.md`, `a&amp;b.md`, `a%26b.md`) 只报告一次; 片段与查询保留在键中,
    // 编码不同但解码后不同的目标不会误合并.
    const key = line + "\u0000" + decodedFullTarget(url, entitiesDecoded);
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    links.push({ line, url, entitiesDecoded });
  };
  for (const item of inline) {
    addLink(item.line, item.url, true);
  }
  for (const item of definitions) {
    addLink(item.line, item.url, true);
  }
  for (const item of htmlLinks) {
    addLink(item.line, item.url, false);
  }
  links.sort((left, right) => left.line - right.line);

  const masked = maskRanges(text, maskedRanges);
  const rawDefinitions = scanRawDefinitionTargets(
    masked,
    lineStarts,
    paragraphRanges,
    listItemRanges
  );
  const labels = new Set(
    definitions.map((item) => normalizeReferenceLabel(item.identifier))
  );
  // 目标含控制字符的定义无法被 CommonMark 解析, 但标签确实存在: 引用它时只报
  // 控制字符错误, 不再报定义缺失.
  for (const item of rawDefinitions) {
    labels.add(normalizeReferenceLabel(item.label));
  }
  const missing = [];
  for (const [position, identifier] of scanReferenceLabels(masked)) {
    if (labels.has(normalizeReferenceLabel(identifier))) {
      continue;
    }
    missing.push([lineAtOffset(lineStarts, position), identifier]);
  }

  const seenControlTargets = new Set();
  const controlTargets = [];
  const rawTargets = [
    ...scanRawInlineTargets(masked, lineStarts),
    ...rawDefinitions,
  ];
  for (const item of definitions) {
    const parsed = parsedDefinitionTarget(text, item.offset, item.end);
    if (parsed === null) {
      continue;
    }
    const target = decodedFullTarget(parsed.target);
    if (!CONTROL_CHARACTER_PATTERN.test(target)) {
      continue;
    }
    rawTargets.push({
      // 定义目标可能另起一行, 行号仍取定义节点起始行.
      line: item.line,
      target,
      raw: parsed.target,
    });
  }
  // 同一行同一解码目标只保留一条. 不用 AST 链接抑制原始扫描结果: mdast 会把
  // `&#1;` 解码成 U+FFFD, 抑制后对应的 AST 链接会额外报目标缺失; AST 链接统一
  // 由 astLinkSkipKeys 跳过.
  for (const item of rawTargets) {
    const key = item.line + "\u0000" + item.target;
    if (seenControlTargets.has(key)) {
      continue;
    }
    seenControlTargets.add(key);
    if (isExternalTarget(item.raw)) {
      continue;
    }
    controlTargets.push({ line: item.line, target: item.target });
  }

  return { links, missing, controlTargets };
}

function decodePercent(value) {
  let result = "";
  let bytes = [];
  const flush = () => {
    if (bytes.length > 0) {
      result += Buffer.from(bytes).toString("utf8");
      bytes = [];
    }
  };
  for (let index = 0; index < value.length; index += 1) {
    if (
      value[index] === "%" &&
      /^[0-9A-Fa-f]{2}$/u.test(value.slice(index + 1, index + 3))
    ) {
      bytes.push(Number.parseInt(value.slice(index + 1, index + 3), 16));
      index += 2;
      continue;
    }
    flush();
    result += value[index];
  }
  flush();
  return result;
}

// HTML5 legacy 命名实体允许省略分号; 与 Python html.unescape 的规则一致:
// 先按完整名称查找 (分号存在时), 未命中再取最长的 legacy 名称前缀, 前缀之后
// 的字符原样保留. 非 legacy 名称省略分号时不解码 (`&hellip` 保持原文).
const LEGACY_NAMED_ENTITIES = new Set(
  (
    "AElig AMP Aacute Acirc Agrave Aring Atilde Auml COPY Ccedil ETH " +
    "Eacute Ecirc Egrave Euml GT Iacute Icirc Igrave Iuml LT Ntilde " +
    "Oacute Ocirc Ograve Oslash Otilde Ouml QUOT REG THORN Uacute Ucirc " +
    "Ugrave Uuml Yacute aacute acirc acute aelig agrave amp aring atilde " +
    "auml brvbar ccedil cedil cent copy curren deg divide eacute ecirc " +
    "egrave eth euml frac12 frac14 frac34 gt iacute icirc iexcl igrave " +
    "iquest iuml laquo lt macr micro middot nbsp not ntilde oacute ocirc " +
    "ograve ordf ordm oslash otilde ouml para plusmn pound quot raquo reg " +
    "sect shy sup1 sup2 sup3 szlig thorn times uacute ucirc ugrave uml " +
    "uuml yacute yen yuml"
  ).split(" ")
);

// 数字字符引用按码点解码, 与 Python html.unescape 的规则一致: 解析失败时保留
// 原文; 无效码点 (NUL, 代理区 U+D800-U+DFFF, 超出 U+10FFFF) 替换为 U+FFFD,
// 而不是解出一个控制字符, 孤立代理或残留原文; 其余合法码点解出对应字符.
function decodeEntityNumber(digits, radix, fallback) {
  const code = Number.parseInt(digits, radix);
  if (!Number.isFinite(code)) {
    return fallback;
  }
  if (code === 0 || (code >= 0xd800 && code <= 0xdfff) || code > 0x10ffff) {
    return "\uFFFD";
  }
  return String.fromCodePoint(code);
}

// 返回解码结果加未匹配的后缀; 没有 legacy 前缀时返回 null.
function decodeLegacyNamedEntity(name) {
  for (let length = name.length; length >= 2; length -= 1) {
    const prefix = name.slice(0, length);
    if (!LEGACY_NAMED_ENTITIES.has(prefix)) {
      continue;
    }
    const replacement = decodeNamedCharacterReference(prefix);
    if (replacement !== false) {
      return replacement + name.slice(length);
    }
  }
  return null;
}

// 命名实体交给 HTML 命名实体解析器, 覆盖完整的实体表; 数字实体按码点处理.
// 数字实体与 legacy 命名实体允许省略分号. 未知实体或解码失败时保留原文.
// semicolonlessOnly 只解码无分号的形式: mdast 已按 CommonMark 解码带分号的
// 字符引用, 再解一次会把 `&amp;amp;` 变成 `&`.
function decodeHtmlEntities(value, semicolonlessOnly = false) {
  return value.replace(
    /&(?:#([0-9]+)|#[xX]([0-9A-Fa-f]+)|([A-Za-z][A-Za-z0-9]+))(;?)/g,
    (match, decimal, hexadecimal, name, semicolon) => {
      if (semicolon && semicolonlessOnly) {
        return match;
      }
      if (decimal !== undefined) {
        return decodeEntityNumber(decimal, 10, match);
      }
      if (hexadecimal !== undefined) {
        return decodeEntityNumber(hexadecimal, 16, match);
      }
      if (semicolon) {
        const replacement = decodeNamedCharacterReference(name);
        if (replacement !== false) {
          return replacement;
        }
      }
      const legacy = decodeLegacyNamedEntity(name);
      return legacy === null ? match : legacy + semicolon;
    }
  );
}

// mdast 已按 CommonMark 解码带分号的字符引用, 但保留无分号的 legacy/数字实体.
// 后者仍需按 Python html.unescape 的规则解码; 带分号的形式不能再解一次.
function decodeMarkdownUrl(url) {
  return decodeHtmlEntities(url, true);
}

function isWindowsAbsolutePath(value) {
  if (WINDOWS_PATH_PATTERN.test(value)) {
    return true;
  }
  if (WINDOWS_FORWARD_UNC_PATTERN.test(value)) {
    return true;
  }
  return value.startsWith("\\") && value.slice(1).includes("\\");
}

// 控制字符检查的对象是完整链接目标: 保留 `#fragment` 与 `?query`, 不与路径解析
// 一样截断; 实体与百分号编码按与路径解析相同的顺序解码后再判断. mdast 目标
// 已解码过实体 (entitiesDecoded), 只做百分号解码.
function decodedFullTarget(target, entitiesDecoded = false) {
  target = target.trim();
  if (target.startsWith("<") && target.endsWith(">")) {
    target = target.slice(1, -1).trim();
  }
  return decodePercent(
    entitiesDecoded ? target : decodeHtmlEntities(target)
  );
}

// mdast 把字符引用中的控制字符 (`&#1;`) 解码为 U+FFFD, 原始扫描与错误信息仍使用
// 真实字符. 存在性检查据此把同一行同一目标与控制字符扫描结果对齐.
function astLinkSkipKeys(controlTargets) {
  const keys = new Set();
  for (const { line, target } of controlTargets) {
    // mdast 解析百分号编码时保留原文, 解析字符引用时把控制字符替换为 U+FFFD.
    // 两种 AST 目标都要与控制字符扫描结果对齐, 避免同一行同一目标重复报告或
    // 把字符引用目标误报为缺失.
    keys.add(line + "\u0000" + target);
    keys.add(line + "\u0000" + target.replace(/\p{Cc}/gu, "\uFFFD"));
  }
  return keys;
}

// 外部链接不做控制字符检查, 与 localTarget 返回 null 时的语义一致; 纯锚点和
// 查询目标仍按本地目标检查.
function isExternalTarget(target, entitiesDecoded = false) {
  target = target.trim();
  if (target.startsWith("<") && target.endsWith(">")) {
    target = target.slice(1, -1).trim();
  }
  if (!entitiesDecoded) {
    target = decodeHtmlEntities(target);
  }
  if (!target) {
    return false;
  }
  if (isWindowsAbsolutePath(target)) {
    return false;
  }
  if (SCHEME_PATTERN.test(target)) {
    return true;
  }
  return target.startsWith("//");
}

function localTarget(target, entitiesDecoded = false) {
  target = target.trim();
  if (target.startsWith("<") && target.endsWith(">")) {
    target = target.slice(1, -1).trim();
  }
  if (!entitiesDecoded) {
    target = decodeHtmlEntities(target);
  }
  if (!target || target.startsWith("#")) {
    return null;
  }
  if (isWindowsAbsolutePath(target)) {
    return target;
  }
  if (SCHEME_PATTERN.test(target)) {
    return null;
  }
  if (target.startsWith("//")) {
    return null;
  }
  const local = target.split("#", 1)[0].split("?", 1)[0];
  if (!local) {
    return null;
  }
  return decodePercent(local);
}

function unicodeEscape(value) {
  let result = "";
  for (const character of value) {
    const code = character.codePointAt(0);
    if (character === "\\") {
      result += "\\\\";
    } else if (character === "\n") {
      result += "\\n";
    } else if (character === "\r") {
      result += "\\r";
    } else if (character === "\t") {
      result += "\\t";
    } else if (code >= 32 && code < 127) {
      result += character;
    } else if (code < 256) {
      result += "\\x" + code.toString(16).padStart(2, "0");
    } else if (code < 65536) {
      result += "\\u" + code.toString(16).padStart(4, "0");
    } else {
      result += "\\U" + code.toString(16).padStart(8, "0");
    }
  }
  return result;
}

function realpathLoose(target) {
  let absolute = path.resolve(target);
  const remainder = [];
  while (!fs.existsSync(absolute)) {
    const parent = path.dirname(absolute);
    if (parent === absolute) {
      break;
    }
    remainder.unshift(path.basename(absolute));
    absolute = parent;
  }
  let resolved;
  try {
    resolved = fs.realpathSync(absolute);
  } catch {
    resolved = absolute;
  }
  return path.resolve(resolved, ...remainder);
}

function isWithin(target, root) {
  const relative = path.relative(root, target);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function matchDiskCase(root, candidate) {
  let relative;
  try {
    relative = path.relative(root, candidate);
  } catch {
    return null;
  }
  if (relative === "" || relative.startsWith("..") || path.isAbsolute(relative)) {
    return null;
  }
  const parts = relative.split(path.sep);
  if (parts.length === 0 || parts.some((part) => part === "" || part === "." || part === "..")) {
    return null;
  }
  let current = root;
  const actualParts = [];
  let mismatched = false;
  for (const part of parts) {
    let entries;
    try {
      entries = fs.readdirSync(current);
    } catch {
      return null;
    }
    let actual;
    if (entries.includes(part)) {
      actual = part;
    } else {
      const folded = casefold(part);
      const matches = entries
        .filter((entry) => casefold(entry) === folded)
        .sort();
      if (matches.length === 0) {
        return null;
      }
      actual = matches[0];
      mismatched = true;
    }
    actualParts.push(actual);
    current = path.join(current, actual);
  }
  if (!fs.existsSync(current)) {
    return null;
  }
  return [path.join(root, ...actualParts), mismatched];
}

function resolveLocalLink(skillDir, baseDir, local) {
  const root = realpathLoose(skillDir);
  const base = realpathLoose(baseDir);
  const byRoot = realpathLoose(path.resolve(root, local));
  if (fs.existsSync(byRoot)) {
    return [byRoot, false];
  }
  const byBase = realpathLoose(path.resolve(base, local));
  if (fs.existsSync(byBase)) {
    return [byBase, base !== root];
  }
  return [null, false];
}

function resolveCaseInsensitiveLink(skillDir, baseDir, local) {
  const root = realpathLoose(skillDir);
  const base = realpathLoose(baseDir);
  for (const candidateBase of [root, base]) {
    const matched = matchDiskCase(root, path.resolve(candidateBase, local));
    if (matched === null) {
      continue;
    }
    return [matched[0], candidateBase !== root, true];
  }
  return [null, false, false];
}

function validateLocalLink(skillDir, baseDir, local, location, errors, warnings) {
  if (isWindowsAbsolutePath(local)) {
    warnings.push(new Issue(location, "Windows 绝对路径不可移植: " + local));
    return null;
  }

  const root = realpathLoose(skillDir);
  if (local.startsWith("/")) {
    const absolutePath = realpathLoose(local);
    if (!fs.existsSync(absolutePath)) {
      errors.push(new Issue(location, "本地链接目标不存在: " + local));
      return null;
    }
    warnings.push(new Issue(location, "绝对路径链接不可移植: " + local));
    if (isWithin(absolutePath, root)) {
      const matched = matchDiskCase(root, absolutePath);
      if (matched === null) {
        return absolutePath;
      }
      if (matched[1]) {
        warnings.push(
          new Issue(location, "链接路径大小写与磁盘不一致, 不可移植: " + local)
        );
      }
      return matched[0];
    }
    return null;
  }

  let [targetPath, fileRelativeOnly] = resolveLocalLink(skillDir, baseDir, local);
  let caseMismatch = false;
  if (targetPath === null) {
    [targetPath, fileRelativeOnly, caseMismatch] = resolveCaseInsensitiveLink(
      skillDir,
      baseDir,
      local
    );
  } else {
    const matched = matchDiskCase(root, targetPath);
    if (matched !== null) {
      targetPath = matched[0];
      caseMismatch = matched[1];
    }
  }
  if (targetPath === null) {
    errors.push(new Issue(location, "本地链接目标不存在: " + local));
    return null;
  }
  if (fileRelativeOnly) {
    warnings.push(
      new Issue(
        location,
        "链接仅按所在文件目录可解析, 建议改为相对 skill 根目录: " + local
      )
    );
  }
  if (!isWithin(targetPath, root)) {
    warnings.push(
      new Issue(location, "链接目标在 skill 目录外, 不可移植: " + local)
    );
    return null;
  }
  if (caseMismatch) {
    warnings.push(
      new Issue(location, "链接路径大小写与磁盘不一致, 不可移植: " + local)
    );
  }
  return targetPath;
}

function relativePosix(root, target) {
  return path.relative(root, target).split(path.sep).join("/");
}

function checkLinks(skillDir, body, bodyStart, errors, warnings) {
  const root = realpathLoose(skillDir);
  const referenced = new Set();
  const bodyLinks = collectMarkdown(body);
  // 控制字符目标已由原始扫描报告, 对应的 AST 链接不再做存在性检查, 避免 `&#1;`
  // 被 mdast 解码为 U+FFFD 后额外报缺失.
  const bodySkipKeys = astLinkSkipKeys(bodyLinks.controlTargets);

  for (const [line, identifier] of bodyLinks.missing) {
    errors.push(
      new Issue(
        "SKILL.md:" + (bodyStart + line - 1),
        "引用式链接定义不存在: " + identifier
      )
    );
  }
  for (const { line, target } of bodyLinks.controlTargets) {
    errors.push(
      new Issue(
        "SKILL.md:" + (bodyStart + line - 1),
        "本地链接目标包含 NUL 或控制字符: " + unicodeEscape(target)
      )
    );
  }
  for (const { line, url, entitiesDecoded } of bodyLinks.links) {
    if (
      bodySkipKeys.has(
        line + "\u0000" + decodedFullTarget(url, entitiesDecoded)
      )
    ) {
      continue;
    }
    const location = "SKILL.md:" + (bodyStart + line - 1);
    const full = decodedFullTarget(url, entitiesDecoded);
    // 纯锚点在 localTarget 中返回 null, 但其片段仍要检查控制字符.
    if (
      !isExternalTarget(url, entitiesDecoded) &&
      CONTROL_CHARACTER_PATTERN.test(full)
    ) {
      errors.push(
        new Issue(
          location,
          "本地链接目标包含 NUL 或控制字符: " + unicodeEscape(full)
        )
      );
      continue;
    }
    const local = localTarget(url, entitiesDecoded);
    if (local === null) {
      continue;
    }
    const targetPath = validateLocalLink(
      skillDir,
      skillDir,
      local,
      location,
      errors,
      warnings
    );
    if (targetPath === null) {
      continue;
    }
    referenced.add(relativePosix(root, targetPath));
  }

  const referencesDir = path.join(skillDir, "references");
  let referencesStat = null;
  try {
    referencesStat = fs.statSync(referencesDir);
  } catch {
    referencesStat = null;
  }
  if (referencesStat === null || !referencesStat.isDirectory()) {
    return referenced;
  }

  const markdownFiles = [];
  const collect = (directory) => {
    let entries;
    try {
      entries = fs.readdirSync(directory, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        collect(absolute);
        continue;
      }
      let stat;
      try {
        stat = fs.statSync(absolute);
      } catch {
        continue;
      }
      if (stat.isFile() && entry.name.endsWith(".md")) {
        markdownFiles.push(absolute);
      }
    }
  };
  collect(referencesDir);
  markdownFiles.sort();

  for (const reference of markdownFiles) {
    if (isIgnoredPath(path.relative(skillDir, reference))) {
      continue;
    }
    const relative = relativePosix(skillDir, reference);
    // 与 SKILL.md 一致: 读取失败与解码失败分开报告.
    let raw;
    try {
      raw = fs.readFileSync(reference);
    } catch (error) {
      errors.push(new Issue(relative, "无法读取: " + error.message));
      continue;
    }
    let text;
    try {
      text = new TextDecoder("utf-8", { fatal: true }).decode(raw);
    } catch (error) {
      errors.push(
        new Issue(relative, "不是有效的 UTF-8 文本: " + error.message)
      );
      continue;
    }
    const referenceLinks = collectMarkdown(text);
    const referenceSkipKeys = astLinkSkipKeys(referenceLinks.controlTargets);
    for (const [line, identifier] of referenceLinks.missing) {
      errors.push(
        new Issue(relative + ":" + line, "引用式链接定义不存在: " + identifier)
      );
    }
    for (const { line, target } of referenceLinks.controlTargets) {
      errors.push(
        new Issue(
          relative + ":" + line,
          "本地链接目标包含 NUL 或控制字符: " + unicodeEscape(target)
        )
      );
    }
    for (const { line, url, entitiesDecoded } of referenceLinks.links) {
      if (
        referenceSkipKeys.has(
          line + "\u0000" + decodedFullTarget(url, entitiesDecoded)
        )
      ) {
        continue;
      }
      const location = relative + ":" + line;
      const full = decodedFullTarget(url, entitiesDecoded);
      // 纯锚点在 localTarget 中返回 null, 但其片段仍要检查控制字符.
      if (
        !isExternalTarget(url, entitiesDecoded) &&
        CONTROL_CHARACTER_PATTERN.test(full)
      ) {
        errors.push(
          new Issue(
            location,
            "本地链接目标包含 NUL 或控制字符: " + unicodeEscape(full)
          )
        );
        continue;
      }
      const local = localTarget(url, entitiesDecoded);
      if (local === null) {
        continue;
      }
      const targetPath = validateLocalLink(
        skillDir,
        path.dirname(reference),
        local,
        location,
        errors,
        warnings
      );
      if (targetPath === null) {
        continue;
      }
      const targetRelative = relativePosix(root, targetPath);
      if (targetRelative.startsWith("references/") && targetRelative !== relative) {
        warnings.push(
          new Issue(location, "参考文件互相引用, 只应从 SKILL.md 直接引用一层")
        );
      }
    }
  }

  return referenced;
}

function isIgnoredPath(relative) {
  if (relative.endsWith(".pyc")) {
    return true;
  }
  return relative
    .split(path.sep)
    .some(
      (part) =>
        part.startsWith(".") ||
        DEPENDENCY_DIRECTORIES.has(part) ||
        part === "__pycache__"
    );
}

function mentionsPath(text, relativePath) {
  const escaped = relativePath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    "(?<![A-Za-z0-9_./-])(?:\\./)?" +
      escaped +
      "(?!(?:[A-Za-z0-9_/-]|\\.(?=[A-Za-z0-9_./-])))"
  );
  return pattern.test(text);
}

function licenseFile(skillDir, data) {
  if (!data.has("license")) {
    return null;
  }
  const value = data.get("license");
  if (typeof value !== "string") {
    return null;
  }
  const target = value.trim();
  if (!target) {
    return null;
  }
  const root = realpathLoose(skillDir);
  let candidate;
  try {
    candidate = realpathLoose(path.resolve(root, target));
  } catch {
    return null;
  }
  if (!isWithin(candidate, root)) {
    return null;
  }
  try {
    if (!fs.statSync(candidate).isFile()) {
      return null;
    }
  } catch {
    return null;
  }
  return candidate;
}

function isSameFile(left, right) {
  try {
    const leftStat = fs.statSync(left);
    const rightStat = fs.statSync(right);
    return leftStat.dev === rightStat.dev && leftStat.ino === rightStat.ino;
  } catch {
    return false;
  }
}

function collectFiles(directory, result = []) {
  let entries;
  try {
    entries = fs.readdirSync(directory, { withFileTypes: true });
  } catch {
    return result;
  }
  for (const entry of entries) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      collectFiles(absolute, result);
      continue;
    }
    let stat;
    try {
      stat = fs.statSync(absolute);
    } catch {
      continue;
    }
    if (stat.isFile()) {
      result.push(absolute);
    }
  }
  return result;
}

function issueKey(issue) {
  const location = issue.location || "";
  const separator = location.lastIndexOf(":");
  if (separator >= 0 && /^\d+$/u.test(location.slice(separator + 1))) {
    return [location.slice(0, separator), Number(location.slice(separator + 1)), issue.message];
  }
  return [location, 0, issue.message];
}

function compareIssues(left, right) {
  const leftKey = issueKey(left);
  const rightKey = issueKey(right);
  if (leftKey[0] !== rightKey[0]) {
    return leftKey[0] < rightKey[0] ? -1 : 1;
  }
  if (leftKey[1] !== rightKey[1]) {
    return leftKey[1] - rightKey[1];
  }
  if (leftKey[2] === rightKey[2]) {
    return 0;
  }
  return leftKey[2] < rightKey[2] ? -1 : 1;
}

function displayDirectory(value) {
  const normalized = path.normalize(String(value));
  const root = path.parse(normalized).root;
  let result = normalized;
  while (result.length > root.length && result.endsWith(path.sep)) {
    result = result.slice(0, -1);
  }
  return result;
}

function validateSkill(skillDirectory) {
  const errors = [];
  const warnings = [];
  const displayDir = displayDirectory(skillDirectory);
  const skillDir = path.resolve(skillDirectory);

  let skillStat;
  try {
    skillStat = fs.statSync(skillDir);
  } catch {
    errors.push(new Issue(displayDir, "路径不存在"));
    return { errors, warnings, parser: null };
  }
  if (!skillStat.isDirectory()) {
    errors.push(new Issue(displayDir, "路径不是目录"));
    return { errors, warnings, parser: null };
  }

  const skillFile = path.join(skillDir, "SKILL.md");
  let fileStat;
  try {
    fileStat = fs.statSync(skillFile);
  } catch {
    fileStat = null;
  }
  if (fileStat === null || !fileStat.isFile()) {
    errors.push(new Issue("SKILL.md", "缺少 SKILL.md"));
    return { errors, warnings, parser: null };
  }

  // 读取与解码分开捕获: 权限或 I/O 失败不是编码问题, 不能误报成非法 UTF-8.
  let raw;
  try {
    raw = fs.readFileSync(skillFile);
  } catch (error) {
    errors.push(new Issue("SKILL.md", "无法读取: " + error.message));
    return { errors, warnings, parser: null };
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(raw);
  } catch (error) {
    errors.push(new Issue("SKILL.md", "不是有效的 UTF-8 文本: " + error.message));
    return { errors, warnings, parser: null };
  }

  let frontmatterLines;
  let body;
  let bodyStart;
  try {
    ({ frontmatterLines, body, bodyStart } = splitFrontmatter(text));
  } catch (error) {
    if (error instanceof FrontmatterError) {
      errors.push(new Issue("SKILL.md:" + (error.line || 1), error.message));
      return { errors, warnings, parser: null };
    }
    throw error;
  }

  let data;
  let parser;
  let keyLines;
  try {
    ({ data, parser, keyLines } = parseFrontmatter(
      frontmatterLines.join("\n"),
      2
    ));
  } catch (error) {
    if (error instanceof FrontmatterError) {
      errors.push(new Issue("SKILL.md:" + (error.line || 2), error.message));
      return { errors, warnings, parser: null };
    }
    throw error;
  }

  const resolvedDir = realpathLoose(skillDir);
  const skillName = path.basename(resolvedDir);
  validateFields(data, keyLines, skillName, errors, warnings);

  if (!hasBodyContent(body)) {
    errors.push(new Issue("SKILL.md", "正文不能为空"));
  } else if (bodyLineCount(body) > MAX_BODY_LINES) {
    warnings.push(
      new Issue(
        "SKILL.md",
        "正文超过 " + MAX_BODY_LINES + " 行, 建议把细节移入 references/ 或 scripts/"
      )
    );
  }

  const referenced = checkLinks(skillDir, body, bodyStart, errors, warnings);
  const license = licenseFile(skillDir, data);

  const files = collectFiles(skillDir);
  files.sort((left, right) => {
    const leftRelative = relativePosix(skillDir, left);
    const rightRelative = relativePosix(skillDir, right);
    return leftRelative < rightRelative ? -1 : leftRelative > rightRelative ? 1 : 0;
  });
  for (const file of files) {
    const relative = relativePosix(skillDir, file);
    const parts = relative.split("/");
    if (parts.length < 2 || (parts[0] !== "scripts" && parts[0] !== "references")) {
      continue;
    }
    let directoryStat;
    try {
      directoryStat = fs.statSync(path.join(skillDir, parts[0]));
    } catch {
      continue;
    }
    if (!directoryStat.isDirectory()) {
      continue;
    }
    if (isIgnoredPath(path.relative(skillDir, file))) {
      continue;
    }
    if (license !== null && isSameFile(file, license)) {
      continue;
    }
    if (referenced.has(relative) || mentionsPath(body, relative)) {
      continue;
    }
    warnings.push(new Issue(relative, "未被 SKILL.md 直接引用的文件"));
  }

  errors.sort(compareIssues);
  warnings.sort(compareIssues);
  return { errors, warnings, parser };
}

function main(argv = process.argv.slice(2)) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      allowPositionals: true,
      options: {
        strict: { type: "boolean", default: false },
        verbose: { type: "boolean", default: false },
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

  const { errors, warnings, parser } = validateSkill(parsed.positionals[0]);
  if (parsed.values.verbose && parser) {
    console.log("frontmatter 解析器: " + parser);
  }
  for (const issue of errors) {
    console.log("错误: " + issue.render());
  }
  for (const issue of warnings) {
    console.log("警告: " + issue.render());
  }

  if (errors.length > 0) {
    console.log(
      "校验失败: " + errors.length + " 个错误, " + warnings.length + " 个警告."
    );
    return 1;
  }
  if (warnings.length > 0 && parsed.values.strict) {
    console.log("严格模式下警告视为错误: " + warnings.length + " 个警告.");
    return 1;
  }
  if (warnings.length > 0) {
    console.log("校验通过, 有 " + warnings.length + " 个警告.");
    return 0;
  }
  console.log("校验通过.");
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
// 只在作为 CLI 运行且未被版本守卫或 --help 提前终止时执行; 导入模块不进入这里,
// 因此导入本身既不产生输出也不设置 process.exitCode.
if (isMain && NODE_SUPPORTED && !HELP_REQUESTED) {
  if (CAN_RUN) {
    process.exitCode = main();
  } else {
    // 依赖缺失时打印五段报告, 只保留失败退出码, 不进入 main 覆盖它.
    reportMissingDependencies();
    process.exitCode = 1;
  }
}

export {
  FrontmatterError,
  splitFrontmatter,
  parseFrontmatter,
  validateName,
  normalizeName,
  validateSkill,
};
