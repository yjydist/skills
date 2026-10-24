// skill 运行时的第三方依赖清单.
//
// 单一来源: validate_skill.mjs, init_skill.mjs 和 check_dependencies.mjs 都从
// 本文件导入该数组, 不各自维护副本, 避免探测与报告出现漂移.
// 依赖安装在 skill 目录的 node_modules; 本文件只声明包名, 不导入包本身,
// 因此缺少 node_modules 时仍可被三个脚本正常加载.

export const DEPENDENCY_PACKAGES = Object.freeze([
  "yaml",
  "mdast-util-from-markdown",
  "decode-named-character-reference",
]);
