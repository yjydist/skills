#!/usr/bin/env python3
"""检查 skill 元数据, 文档对应关系, 本地链接和 Markdown 规范."""

import argparse
from collections import Counter
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml


MARKDOWN = MarkdownIt("commonmark").enable("table")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class UniqueLoader(yaml.SafeLoader):
    """拒绝会被普通 YAML 解析器静默覆盖的重复键."""


def unique_mapping(loader, node):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise yaml.constructor.ConstructorError(
                None, None, "字段名称必须是唯一的字符串", key_node.start_mark
            )
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def inline_text(token):
    if token.children:
        return "".join(inline_text(child) for child in token.children)
    return token.content if token.type in ("text", "code_inline") else ""


def heading_ids(tokens):
    used = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        text = inline_text(tokens[index + 1]).lower()
        slug = "".join(char for char in text if char in "_- " or
                       unicodedata.category(char)[0] not in "PSC").replace(" ", "-")
        candidate, suffix = slug, 0
        while candidate in used:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        used.add(candidate)
    return used


class Checker:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.errors = []
        self.documents = {}

    def error(self, path, line, rule, message):
        try:
            location = str(path.relative_to(self.root))
        except ValueError:
            location = str(path)
        self.errors.append(f"{location}:{line}: {rule}: {message}")

    def punctuation(self, path, line, text):
        bad = sorted({char for char in text if ord(char) > 127 and
                      unicodedata.category(char).startswith("P")})
        if bad:
            self.error(path, line, "ascii-punctuation", "使用 ASCII 标点替换: " + "".join(bad))

    def load_document(self, path):
        path = path.resolve()
        if path in self.documents:
            return self.documents[path]
        source = path.read_text(encoding="utf-8")
        body, metadata = source, None
        if path.name == "SKILL.md":
            match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", source, re.S)
            if not match:
                self.error(path, 1, "frontmatter", "缺少完整的 YAML frontmatter.")
            else:
                body = "\n" * source[:match.end()].count("\n") + source[match.end():]
                try:
                    metadata = yaml.load(match.group(1), Loader=UniqueLoader)
                except yaml.YAMLError as error:
                    mark = getattr(error, "problem_mark", None)
                    self.error(path, mark.line + 2 if mark else 1, "frontmatter", str(error))
                if not isinstance(metadata, dict):
                    self.error(path, 1, "frontmatter", "frontmatter 必须是字段映射.")
                    metadata = None
        result = {"source": source, "metadata": metadata, "tokens": MARKDOWN.parse(body)}
        self.documents[path] = result
        return result

    def check_metadata(self, directory):
        path = directory / "SKILL.md"
        if not path.is_file():
            self.error(path, 1, "entrypoint", "skill 缺少 SKILL.md.")
            return
        metadata = self.load_document(path)["metadata"]
        if metadata is None:
            return
        name = metadata.get("name")
        if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
            self.error(path, 1, "skill-name", "name 必须是至多 64 字符的小写字母, 数字和单连字符名称.")
        elif name != directory.name:
            self.error(path, 1, "skill-name", "name 必须与所在目录名称一致.")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            self.error(path, 1, "description", "description 必须是非空字符串, 至多 1024 字符.")
        else:
            self.punctuation(path, 1, description)

    def check_registry(self, names):
        readme = self.root / "README.md"
        if not readme.is_file():
            self.error(readme, 1, "registry", "缺少 README.md.")
            return
        tokens = self.load_document(readme)["tokens"]
        in_section, sections, entries = False, 0, []
        for index, token in enumerate(tokens):
            if token.type == "heading_open" and int(token.tag[1:]) <= 2:
                in_section = token.tag == "h2" and inline_text(tokens[index + 1]) == "skills 列表"
                sections += int(in_section)
            if not in_section or token.type != "list_item_open" or token.level != 1:
                continue
            item = []
            for child in tokens[index + 1:]:
                if child.type == "list_item_close" and child.level == token.level:
                    break
                if child.type == "inline":
                    item.append(child)
            text = " ".join(inline_text(child) for child in item)
            match = re.match(r"([a-z0-9]+(?:-[a-z0-9]+)*):?\s+", text)
            name = match.group(1) if match else ""
            links = [c.attrGet("href") for child in item for c in child.children or []
                     if c.type == "link_open"]
            line = token.map[0] + 1
            if name not in names:
                self.error(readme, line, "registry", "列表项未对应有效的 skill 目录: " + text)
                continue
            entries.append(name)
            if f"docs/{name}.md" not in links:
                self.error(readme, line, "registry", "缺少对应的 docs 使用文档链接: " + name)
        if sections != 1:
            self.error(readme, 1, "registry", "必须存在且仅存在一个二级标题: skills 列表.")
        counts = Counter(entries)
        for name in sorted(names):
            if counts[name] != 1:
                self.error(readme, 1, "registry", f"{name} 必须有且仅有一个列表项, 当前为 {counts[name]}.")

    def check_link(self, source, line, href):
        try:
            url = urlsplit(href)
        except ValueError:
            self.error(source, line, "local-link", "无法解析链接: " + href)
            return
        if url.scheme or url.netloc:
            return
        target = (source.parent / unquote(url.path)).resolve() if url.path else source
        if not target.exists():
            self.error(source, line, "local-link", "目标不存在: " + href)
        elif url.fragment and target.is_file() and target.suffix.lower() == ".md":
            if unquote(url.fragment) not in heading_ids(self.load_document(target)["tokens"]):
                self.error(source, line, "local-anchor", "标题锚点不存在: " + href)

    def check_inline(self, path, line, tokens):
        for token in tokens:
            if token.type == "text":
                self.punctuation(path, line, token.content)
            elif token.type == "link_open":
                self.check_link(path, line, token.attrGet("href"))
            elif token.type == "image":
                self.check_link(path, line, token.attrGet("src"))
                self.check_inline(path, line, token.children or [])

    def check_markdown(self, path):
        for token in self.load_document(path)["tokens"]:
            line = token.map[0] + 1 if token.map else 1
            if token.type == "bullet_list_open" and token.markup != "+":
                self.error(path, line, "list-marker", "Markdown 无序列表必须使用 +.")
            if token.type == "inline":
                self.check_inline(path, line, token.children or [])

    def run(self):
        skills_root = self.root / "skills"
        directories = sorted(path for path in skills_root.glob("*") if path.is_dir() and
                             not path.name.startswith("."))
        if not directories:
            self.error(skills_root, 1, "skills", "未发现 skill 目录.")
        for directory in directories:
            self.check_metadata(directory)
            doc = self.root / "docs" / (directory.name + ".md")
            if not doc.is_file():
                self.error(doc, 1, "usage-doc", "缺少 skill 对应的使用文档.")
        self.check_registry({path.name for path in directories})
        paths = set(self.root.glob("*.md")) | set(skills_root.rglob("*.md")) | set(
            (self.root / "docs").rglob("*.md")
        )
        for path in sorted(paths):
            self.check_markdown(path)
        return sorted(set(self.errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="仓库根目录, 默认脚本所在仓库")
    args = parser.parse_args()
    try:
        errors = Checker(args.root).run()
    except (OSError, UnicodeError) as error:
        print("检查无法完成: " + str(error), file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("skill 与文档规范检查通过.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
