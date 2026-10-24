#!/usr/bin/env python3
"""创建 skill 目录骨架.

名称会按 NFKC 归一化为小写字母, 数字和连字符形式. 目录已存在时拒绝覆盖. 生成的
description 为空, 正文只有占位注释, 以便校验脚本在填写前必然失败.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path


MAX_NAME_LENGTH = 64

SKILL_TEMPLATE = """---
name: "{name}"
description: ""
---

<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. 只填写 description 仍会因正文为空而校验失败. -->
"""


def normalize_name(raw):
    """归一化为 Unicode 小写字母, 数字和连字符形式."""
    name = unicodedata.normalize("NFKC", raw).strip().lower()
    characters = [
        char if char.isalnum() or char == "-" else "-" for char in name
    ]
    return re.sub(r"-{2,}", "-", "".join(characters)).strip("-")


def validate_name(name):
    """返回错误说明; 名称合法时返回 None."""
    normalized = unicodedata.normalize("NFKC", name).strip()
    if not normalized:
        return "名称归一化后为空, 只允许小写字母, 数字和连字符"
    if len(normalized) > MAX_NAME_LENGTH:
        return "名称不能超过 {} 字符".format(MAX_NAME_LENGTH)
    if normalized != normalized.lower():
        return "名称必须全部为小写字母"
    if normalized.startswith("-") or normalized.endswith("-"):
        return "名称不能以连字符开头或结尾"
    if "--" in normalized:
        return "名称不能包含连续连字符"
    if not all(char == "-" or char.isalnum() for char in normalized):
        return "名称只能包含小写字母, 数字和连字符"
    return None


def create_skill(
    name,
    parent,
    include_scripts=False,
    include_references=False,
    include_assets=False,
):
    """创建目录并返回路径; 目录已存在时抛出 FileExistsError."""
    target = Path(parent) / name
    if target.exists():
        raise FileExistsError(str(target))
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name), encoding="utf-8"
    )
    for flag, directory in (
        (include_scripts, "scripts"),
        (include_references, "references"),
        (include_assets, "assets"),
    ):
        if flag:
            (target / directory).mkdir()
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="创建 Agent Skills 目录骨架.")
    parser.add_argument("name", help="skill 名称, 会按 NFKC 归一化为小写字母, 数字和连字符形式")
    parser.add_argument("--path", default=".", help="父目录, 默认为当前目录")
    parser.add_argument("--scripts", action="store_true", help="创建 scripts/")
    parser.add_argument("--references", action="store_true", help="创建 references/")
    parser.add_argument("--assets", action="store_true", help="创建 assets/")
    args = parser.parse_args(argv)

    name = normalize_name(args.name)
    problem = validate_name(name)
    if problem:
        print("错误: {}".format(problem), file=sys.stderr)
        return 1

    if name != args.name.strip():
        print("名称已归一化: {} -> {}".format(args.name.strip(), name))

    try:
        target = create_skill(
            name,
            args.path,
            include_scripts=args.scripts,
            include_references=args.references,
            include_assets=args.assets,
        )
    except FileExistsError:
        print(
            "错误: 目标路径已存在, 不覆盖: {}".format(Path(args.path) / name),
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print("错误: 创建失败: {}".format(exc), file=sys.stderr)
        return 1

    print("已创建: {}".format(target.resolve()))
    print(
        "下一步: 填写 description, 然后运行 validate_skill.py {}".format(
            target.resolve()
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
