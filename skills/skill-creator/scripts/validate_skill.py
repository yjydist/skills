#!/usr/bin/env python3
"""校验 Agent Skills 目录的标准符合性.

默认以错误和警告分级输出. 标准违规为错误, 可移植性和冗余问题为警告.
使用 --strict 时警告也会导致非零退出状态.
"""

import argparse
import bisect
from datetime import date, datetime, timedelta, timezone
import html
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote


STANDARD_FIELDS = (
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
)

KEY_PATTERN = re.compile(r"([A-Za-z0-9_.-]+) *:(?: +(.*))?\Z")
# 以下 token 集合与 PyYAML 1.1 布尔/空值 resolver 完全一致: 只接受列出的精确
# 大小写形式, 因此 "oN", "YeS", "NuLl" 等一律按普通字符串处理.
YAML_TRUE_TOKENS = frozenset(
    ("yes", "Yes", "YES", "true", "True", "TRUE", "on", "On", "ON")
)
YAML_FALSE_TOKENS = frozenset(
    ("no", "No", "NO", "false", "False", "FALSE", "off", "Off", "OFF")
)
YAML_NULL_TOKENS = frozenset(("~", "null", "Null", "NULL", ""))
# 以下模式与 PyYAML 1.1 的隐式 resolver 完全一致. 注意: 下划线只允许出现在
# 数字之间; 指数必须带符号; 六十进制首段不能有前导零; nan 不能带符号.
YAML_INT_PATTERN = re.compile(
    r"(?:[-+]?0b[0-1_]+"
    r"|[-+]?0[0-7_]+"
    r"|[-+]?(?:0|[1-9][0-9_]*)"
    r"|[-+]?0x[0-9a-fA-F_]+"
    r"|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)\Z"
)
YAML_FLOAT_PATTERN = re.compile(
    r"(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?"
    r"|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?"
    r"|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*"
    r"|[-+]?\.(?:inf|Inf|INF)"
    r"|\.(?:nan|NaN|NAN))\Z"
)
# 以下两个模式与 PyYAML 1.1 的 timestamp resolver 和构造器完全一致. 小写 z
# 不在 resolver 中, 因此按字符串保留; 单数字月/日/时/分以及 ``+HH`` 偏移会被
# 识别, 而 ``+HHMM`` 不带冒号的形式不匹配, 同样保留为字符串.
YAML_TIMESTAMP_RESOLVER = re.compile(
    r"""^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
        |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
         (?:[Tt]|[ \t]+)[0-9][0-9]?
         :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
         (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$""",
    re.VERBOSE,
)
YAML_TIMESTAMP_CONSTRUCTOR = re.compile(
    r"""^(?P<year>[0-9][0-9][0-9][0-9])
        -(?P<month>[0-9][0-9]?)
        -(?P<day>[0-9][0-9]?)
        (?:(?:[Tt]|[ \t]+)
        (?P<hour>[0-9][0-9]?)
        :(?P<minute>[0-9][0-9])
        :(?P<second>[0-9][0-9])
        (?:\.(?P<fraction>[0-9]*))?
        (?:[ \t]*(?P<tz>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9][0-9]?)
        (?::(?P<tz_minute>[0-9][0-9]))?))?)?$""",
    re.VERBOSE,
)
DOUBLE_QUOTE_ESCAPES = {
    "\\": "\\",
    '"': '"',
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "/": "/",
    " ": " ",
}
BLOCK_HEADER_PATTERN = re.compile(r"([|>])([+-]?[0-9]?[+-]?)(?:[ \t]+#.*)?\Z")
# 标签体允许反斜杠转义 (``[a\]b]``), 未转义的 ``]`` 才是闭合括号.
# 块首缩进按 CommonMark 只认 ASCII 空格 (最多 3 个): U+3000, NBSP 等
# Unicode 空白不是缩进, 带这类前缀的行不是引用定义.
REFERENCE_DEFINITION_PATTERN = re.compile(
    r"^ {0,3}\[(?!\^)(?:\\.|[^\]\\])+\]:\s*(<[^>]*>|\S+)"
)
# 目标写在下一行 (缩进或不缩进): 定义行本身只有标签和冒号.
EMPTY_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"^ {0,3}\[(?!\^)(?:\\.|[^\]\\])+\]:\s*$"
)
# Windows 盘符路径 (绝对路径与 ``C:demo.md`` 这类盘符相对路径) 与反斜杠
# UNC 路径在其它平台上不可移植.
WINDOWS_PATH_PATTERN = re.compile(r"^(?:[A-Za-z]:|\\\\)")
# 正斜杠 UNC: ``//server/share``. 首段带点或端口时更像协议相对 URL, 交给
# 外部链接处理, 避免把 CDN 地址误报为不可移植.
WINDOWS_FORWARD_UNC_PATTERN = re.compile(r"^//[^/\s.:]+/[^/\s]+")
# 行内 HTML 的本地链接属性. 只在脱敏后的文本上匹配, 因此代码块与原始
# HTML 块内的标签不会被扫描.
HTML_LINK_ATTRIBUTE_PATTERN = re.compile(
    r"""<\s*(?:a(?=[\s/>])[^>]*?\shref|img(?=[\s/>])[^>]*?\ssrc)\s*=\s*
        (?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))""",
    re.IGNORECASE | re.VERBOSE,
)
# 只有这些 ASCII 标点前的反斜杠在 Markdown 中算转义.
ESCAPABLE_PUNCTUATION = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
MAX_BODY_LINES = 500


def normalize_name(value):
    """按标准归一化名称: 先去除首尾空白, 再做 NFKC."""
    return unicodedata.normalize("NFKC", value.strip())


def validate_name(name):
    """返回 name 字段的违规说明; 合法时返回 None."""
    normalized = normalize_name(name)
    if not normalized:
        return "name 归一化后为空"
    if len(normalized) > MAX_NAME_LENGTH:
        return "name 长度必须在 1-{} 字符之间, 当前为 {} 字符".format(
            MAX_NAME_LENGTH, len(normalized)
        )
    if normalized != normalized.lower():
        return "name 必须全部为小写字母"
    if normalized.startswith("-") or normalized.endswith("-"):
        return "name 不能以连字符开头或结尾"
    if "--" in normalized:
        return "name 不能包含连续连字符"
    if not all(char == "-" or char.isalnum() for char in normalized):
        return "name 只能包含小写字母, 数字和连字符"
    return None


class FrontmatterError(ValueError):
    """frontmatter 解析失败, 可携带 SKILL.md 中的行号."""

    def __init__(self, message, line=None):
        super().__init__(message)
        self.line = line


class Issue:
    """一条校验结果."""

    def __init__(self, location, message):
        self.location = location
        self.message = message

    def render(self):
        if self.location:
            return "{}: {}".format(self.location, self.message)
        return self.message


# ---------------------------------------------------------------------------
# frontmatter 拆分与解析


def split_frontmatter(text):
    """返回 (frontmatter 行列表, 正文, 正文起始行号)."""
    text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if not lines or lines[0].rstrip(" \t") != "---":
        raise FrontmatterError("SKILL.md 必须以 YAML frontmatter 开头, 第一行应为 ---", 1)
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :]), index + 2
    raise FrontmatterError("frontmatter 缺少结束标记 ---", len(lines))


def _reject_indicator_plain_scalars(node, first_line):
    """拒绝以流指示符开头的普通 (未加引号/非块) 纯量."""
    kind = getattr(node, "id", None)
    if kind == "scalar":
        value = node.value
        if node.style is None and value and value[0] in "[]{},":
            raise FrontmatterError(
                "无法解析, 请人工确认: 不支持以流指示符开头的纯量",
                first_line + node.start_mark.line,
            )
        return
    if kind == "mapping":
        children = [value for _, value in node.value]
    elif kind == "sequence":
        children = node.value
    else:
        return
    for child in children:
        _reject_indicator_plain_scalars(child, first_line)


def parse_with_pyyaml(frontmatter_text, first_line=2):
    """使用 PyYAML 解析. PyYAML 不可用时返回 None."""
    try:
        import yaml
    except ImportError:
        return None
    frontmatter_text = (
        frontmatter_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    )
    try:
        node = yaml.compose(frontmatter_text, Loader=yaml.SafeLoader)
        data = yaml.safe_load(frontmatter_text)
    except (yaml.YAMLError, ValueError) as exc:
        mark = getattr(exc, "problem_mark", None)
        line = first_line + mark.line if mark is not None else first_line
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        raise FrontmatterError("无法解析 frontmatter: {}".format(problem), line)
    if node is not None:
        _reject_indicator_plain_scalars(node, first_line)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter 必须是键值映射", first_line)
    return data


def _indent_of(line, line_no):
    count = 0
    while count < len(line) and line[count] == " ":
        count += 1
    if count < len(line) and line[count] == "\t":
        raise FrontmatterError("缩进不能使用制表符", line_no)
    return count


def _comment_index(value):
    for index, char in enumerate(value):
        if char == "#" and (index == 0 or value[index - 1] in " \t"):
            return index
    return len(value)


def _parse_yaml_int(text):
    """按 PyYAML int 构造器把已匹配的整数 token 转为 int."""
    value = text.replace("_", "")
    sign = -1 if value.startswith("-") else 1
    if value[0] in "+-":
        value = value[1:]
    if value == "0":
        return 0
    if value.startswith("0b"):
        return sign * int(value[2:], 2)
    if value.startswith("0x"):
        return sign * int(value[2:], 16)
    if value[0] == "0":
        return sign * int(value, 8)
    if ":" in value:
        total = 0
        for part in value.split(":"):
            total = total * 60 + int(part)
        return sign * total
    return sign * int(value)


def _parse_yaml_float(text):
    """按 PyYAML float 构造器把已匹配的浮点 token 转为 float."""
    value = text.replace("_", "").lower()
    sign = -1.0 if value.startswith("-") else 1.0
    if value[0] in "+-":
        value = value[1:]
    if value == ".inf":
        return sign * float("inf")
    if value == ".nan":
        return float("nan")
    if ":" in value:
        total = 0.0
        for part in value.split(":"):
            total = total * 60.0 + float(part)
        return sign * total
    return sign * float(value)


def _parse_yaml_timestamp(value):
    """按 PyYAML timestamp 构造器把已识别的 token 转为 date 或 datetime."""
    match = YAML_TIMESTAMP_CONSTRUCTOR.match(value)
    if match is None:  # pragma: no cover - resolver 与构造器模式保持一致
        raise ValueError("无法识别的日期")
    values = match.groupdict()
    year = int(values["year"])
    month = int(values["month"])
    day = int(values["day"])
    if values["hour"] is None:
        return date(year, month, day)
    hour = int(values["hour"])
    minute = int(values["minute"])
    second = int(values["second"])
    fraction = 0
    tzinfo = None
    if values["fraction"]:
        fraction = values["fraction"][:6]
        while len(fraction) < 6:
            fraction += "0"
        fraction = int(fraction)
    if values["tz_sign"]:
        delta = timedelta(
            hours=int(values["tz_hour"]),
            minutes=int(values["tz_minute"] or 0),
        )
        if values["tz_sign"] == "-":
            delta = -delta
        tzinfo = timezone(delta)
    elif values["tz"]:
        tzinfo = timezone.utc
    return datetime(
        year, month, day, hour, minute, second, fraction, tzinfo=tzinfo
    )


def _resolve_plain(value):
    if value in YAML_NULL_TOKENS:
        return None
    if value in YAML_TRUE_TOKENS:
        return True
    if value in YAML_FALSE_TOKENS:
        return False
    if YAML_FLOAT_PATTERN.fullmatch(value):
        return _parse_yaml_float(value)
    if YAML_INT_PATTERN.fullmatch(value):
        return _parse_yaml_int(value)
    if YAML_TIMESTAMP_RESOLVER.fullmatch(value):
        # 形如日期但取值非法时直接抛出 ValueError, 与 PyYAML 行为保持一致.
        return _parse_yaml_timestamp(value)
    return value


def _scan_quoted(value, line_no):
    """解析引号标量, 返回 (解码后的文本, 闭合引号之后的下标)."""
    quote = value[0]
    characters = []
    index = 1
    while index < len(value):
        char = value[index]
        if quote == "'":
            if char == "'":
                if index + 1 < len(value) and value[index + 1] == "'":
                    characters.append("'")
                    index += 2
                    continue
                return "".join(characters), index + 1
            characters.append(char)
            index += 1
            continue
        if char == "\\":
            if index + 1 >= len(value):
                raise FrontmatterError("无法解析, 请人工确认: 转义序列不完整", line_no)
            code = value[index + 1]
            if code == "u":
                digits = value[index + 2 : index + 6]
                if len(digits) != 4 or not re.fullmatch(r"[0-9a-fA-F]{4}", digits):
                    raise FrontmatterError("\\u 转义需要 4 位十六进制", line_no)
                characters.append(chr(int(digits, 16)))
                index += 6
                continue
            if code not in DOUBLE_QUOTE_ESCAPES:
                raise FrontmatterError(
                    "不支持的转义序列: \\{}; 内置解析器仅支持 \\\\, \\\", \\n, "
                    "\\t, \\r, \\0, \\/, 空格 和 \\uXXXX; "
                    "可安装 PyYAML 或人工确认".format(code),
                    line_no,
                )
            characters.append(DOUBLE_QUOTE_ESCAPES[code])
            index += 2
            continue
        if char == '"':
            return "".join(characters), index + 1
        characters.append(char)
        index += 1
    raise FrontmatterError(
        "无法解析, 请人工确认: 引号未闭合或属于多行引号标量", line_no
    )


def _parse_quoted(value, line_no):
    decoded, end = _scan_quoted(value, line_no)
    tail = value[end:]
    comment_index = _comment_index(tail)
    if "\t" in tail[:comment_index]:
        raise FrontmatterError("无法解析, 请人工确认: 不支持制表符分隔", line_no)
    tail = tail[:comment_index].strip()
    if tail:
        raise FrontmatterError("引号标量后存在多余内容", line_no)
    return decoded


def _parse_quoted_key(text, line_no):
    """解析引号包裹的键, 返回 (键, 冒号后的值文本); 不是引号键时返回 None."""
    decoded, end = _scan_quoted(text, line_no)
    rest = text[end:]
    stripped_rest = rest.lstrip(" ")
    if not stripped_rest.startswith(":"):
        if "\t" in rest:
            raise FrontmatterError(
                "无法解析, 请人工确认: 不支持制表符分隔", line_no
            )
        return None
    remainder = stripped_rest[1:]
    if remainder and not remainder.startswith((" ", "\t")):
        raise FrontmatterError(
            "无法解析, 请人工确认: 引号键后的冒号需要空格再写值", line_no
        )
    return decoded, remainder.lstrip(" ").rstrip(" ")


def _split_unicode_key(text):
    """在首个未转义且不在引号内的冒号处分割键值, 支持非 ASCII 键.

    返回 (键, 冒号后的值文本); 不是 ``key: value`` 形式时返回 None.
    """
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is None:
            if char in "'\"":
                quote = char
            elif char == "\\":
                index += 2
                continue
            elif char == ":":
                key = text[:index].strip()
                remainder = text[index + 1 :]
                if (
                    not key
                    or key in ("-", "?")
                    or key.startswith(("- ", "? "))
                    or "\t" in text[:index]
                    or _comment_index(text[:index]) < index
                    or (remainder and not remainder.startswith(" "))
                ):
                    return None
                return key, remainder.strip(" ")
        elif quote == "'":
            if char == "'":
                if index + 1 < len(text) and text[index + 1] == "'":
                    index += 2
                    continue
                quote = None
        else:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                quote = None
        index += 1
    return None


def _parse_block_header(value, line_no):
    if "\t" in value[: _comment_index(value)]:
        raise FrontmatterError("无法解析, 请人工确认: 不支持制表符分隔", line_no)
    match = BLOCK_HEADER_PATTERN.match(value.strip())
    if not match:
        raise FrontmatterError("无法解析块标量头部, 请人工确认", line_no)
    style = match.group(1)
    indicators = match.group(2)
    chomping = ""
    indent = None
    for char in indicators:
        if char in "+-":
            if chomping:
                raise FrontmatterError("块标量出现重复的 chomping 指示符", line_no)
            chomping = char
        elif char.isdigit():
            if indent is not None:
                raise FrontmatterError("块标量出现重复的缩进指示符", line_no)
            indent = int(char)
    if indent == 0:
        raise FrontmatterError("块标量缩进指示符必须大于 0", line_no)
    return style, chomping, indent


def _chomp_literal(entries, chomping):
    """字面块标量 (|) 的 chomping: 逐行拼接后按 chomping 处理末尾换行."""
    text = "".join(
        content + ("\n" if has_break else "") for content, has_break in entries
    )
    if chomping == "-":
        return text.rstrip("\n")
    if chomping == "+":
        return text
    if not any(content for content, _ in entries):
        return ""
    return text.rstrip("\n") + ("\n" if text.endswith("\n") else "")


def _chomp_folded(entries, chomping):
    """折叠块标量 (>) 的折叠与 chomping, 语义与 PyYAML 扫描器一致.

    只有两侧都是普通行 (非空行且非更深缩进) 时换行才折叠为空格;
    空行保留为换行, 更深缩进行两侧的换行也保留.
    """
    chunks = []
    pending = []
    index = 0
    total = len(entries)
    line_break = ""
    while index < total:
        content, has_break = entries[index]
        if content == "":
            if has_break:
                pending.append("\n")
            index += 1
            continue
        chunks.extend(pending)
        pending = []
        chunks.append(content)
        line_break = "\n" if has_break else ""
        following = index + 1
        breaks = []
        while following < total and entries[following][0] == "":
            if entries[following][1]:
                breaks.append("\n")
            following += 1
        if following < total:
            next_content = entries[following][0]
            if (
                line_break
                and content[0] not in " \t"
                and next_content[0] not in " \t"
            ):
                if not breaks:
                    chunks.append(" ")
            else:
                chunks.append(line_break)
            pending = breaks
            index = following
            continue
        pending = breaks
        index = following
    if chomping == "-":
        return "".join(chunks)
    value = "".join(chunks) + line_break
    if chomping == "+":
        value += "".join(pending)
    return value


def _parse_block_scalar(
    lines, header_index, parent_indent, header, header_line, text_ended_with_newline
):
    style, chomping, explicit_indent = _parse_block_header(header, header_line)
    last_line = len(lines) - 1
    if text_ended_with_newline and last_line >= 0 and lines[last_line] == "":
        # 文本末尾的换行在 split 后只剩下一个空元素, 它不是内容行.
        last_line -= 1
    content_indent = None
    if explicit_indent is not None:
        content_indent = parent_indent + explicit_indent
    leading_blank_indent = 0
    entries = []
    index = header_index + 1
    while index <= last_line:
        raw = lines[index]
        line_no = header_line + (index - header_index)
        has_break = index < last_line or text_ended_with_newline
        if raw.strip() == "":
            if "\t" in raw:
                # 制表符不能出现在块标量缩进中; PyYAML 在此同样报错.
                raise FrontmatterError("缩进不能使用制表符", line_no)
            if content_indent is not None and len(raw) > content_indent:
                # 缩进超过内容缩进的空白行, 多余空格属于内容且算更深缩进.
                entries.append((raw[content_indent:], has_break))
            else:
                leading_blank_indent = max(leading_blank_indent, len(raw))
                entries.append(("", has_break))
            index += 1
            continue
        indent = _indent_of(raw, line_no)
        if indent <= parent_indent:
            break
        if content_indent is None:
            if indent < leading_blank_indent:
                # YAML 会以更深的前置空行缩进作为内容缩进, 随后整块内容失效.
                raise FrontmatterError(
                    "无法解析, 请人工确认: 块标量首个空行缩进深于内容", line_no
                )
            content_indent = indent
        if indent < content_indent:
            if raw.lstrip().startswith("#"):
                # 缩进不足的注释行按 YAML 语义结束块标量, 交给外层解析器跳过.
                break
            raise FrontmatterError("块标量缩进不一致, 请人工确认", line_no)
        entries.append((raw[content_indent:], has_break))
        index += 1

    if style == "|":
        return _chomp_literal(entries, chomping), index
    return _chomp_folded(entries, chomping), index


def _parse_inline_value(
    lines, index, parent_indent, text, line_no, text_ended_with_newline
):
    if text.startswith(("'", '"')):
        return _parse_quoted(text, line_no), index + 1
    if text.startswith(("|", ">")):
        return _parse_block_scalar(
            lines, index, parent_indent, text, line_no, text_ended_with_newline
        )
    if text[0] in "[]{},":
        raise FrontmatterError(
            "无法解析, 请人工确认: 不支持以流指示符开头的纯量", line_no
        )
    if text[0] in "&*!%@`":
        raise FrontmatterError("无法解析, 请人工确认: 不支持 YAML 高级语法", line_no)
    comment_index = _comment_index(text)
    if "\t" in text[:comment_index]:
        raise FrontmatterError("无法解析, 请人工确认: 不支持制表符分隔", line_no)
    plain = text[:comment_index].rstrip()
    if plain in ("-", "?") or plain.startswith(("- ", "? ")):
        raise FrontmatterError(
            "无法解析, 请人工确认: 不支持序列或映射键形式的纯量", line_no
        )
    if re.search(r":(?:\s|$)", plain):
        raise FrontmatterError("无法解析, 请人工确认: 纯量中包含映射分隔符", line_no)
    try:
        return _resolve_plain(plain), index + 1
    except ValueError as exc:
        raise FrontmatterError(
            "无法解析, 请人工确认: 无效日期 ({})".format(exc), line_no
        ) from exc


def _not_mapping_error(text, line_no):
    if "\t" in text:
        return FrontmatterError("无法解析, 请人工确认: 不支持制表符分隔", line_no)
    return FrontmatterError(
        "无法解析, 请人工确认: 第 {} 行不是 key: value".format(line_no), line_no
    )


def _parse_mapping(
    lines, start, indent, first_line, allow_nested, text_ended_with_newline
):
    result = {}
    index = start
    while index < len(lines):
        raw = lines[index]
        line_no = first_line + index
        if raw.strip() == "" or raw.lstrip().startswith("#"):
            index += 1
            continue
        current_indent = _indent_of(raw, line_no)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise FrontmatterError(
                "缩进超出当前层级, 内置解析器只支持一层嵌套映射, 请人工确认", line_no
            )
        stripped = raw[indent:]
        match = KEY_PATTERN.match(stripped)
        if match:
            try:
                key = _resolve_plain(match.group(1))
            except ValueError as exc:
                raise FrontmatterError(
                    "无法解析, 请人工确认: 无效日期 ({})".format(exc), line_no
                ) from exc
            value_text = (match.group(2) or "").rstrip(" ")
        elif stripped.startswith(("'", '"')):
            parsed = _parse_quoted_key(stripped, line_no)
            if parsed is None:
                raise _not_mapping_error(stripped, line_no)
            key, value_text = parsed
        else:
            parsed = _split_unicode_key(stripped)
            if parsed is None:
                raise _not_mapping_error(stripped, line_no)
            unicode_key, value_text = parsed
            try:
                key = _resolve_plain(unicode_key)
            except ValueError as exc:
                raise FrontmatterError(
                    "无法解析, 请人工确认: 无效日期 ({})".format(exc), line_no
                ) from exc

        if value_text == "" or value_text.startswith("#"):
            lookahead = index + 1
            while lookahead < len(lines):
                probe = lines[lookahead]
                if probe.strip() == "" or probe.lstrip().startswith("#"):
                    lookahead += 1
                    continue
                break
            if lookahead < len(lines) and _indent_of(
                lines[lookahead], first_line + lookahead
            ) > indent:
                if not allow_nested:
                    raise FrontmatterError(
                        "内置解析器只支持一层嵌套映射, 请人工确认", first_line + lookahead
                    )
                nested_indent = _indent_of(lines[lookahead], first_line + lookahead)
                value, index = _parse_mapping(
                    lines,
                    index + 1,
                    nested_indent,
                    first_line,
                    False,
                    text_ended_with_newline,
                )
                result[key] = value
                continue
            result[key] = None
            index += 1
            continue

        value, index = _parse_inline_value(
            lines, index, indent, value_text, line_no, text_ended_with_newline
        )
        result[key] = value
    return result, index


def parse_with_builtin(frontmatter_text, first_line=2):
    """不依赖 PyYAML 的受限解析器."""
    frontmatter_text = (
        frontmatter_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    )
    if frontmatter_text.strip() == "":
        return {}
    text_ended_with_newline = frontmatter_text.endswith("\n")
    lines = frontmatter_text.split("\n")
    data, index = _parse_mapping(
        lines, 0, 0, first_line, True, text_ended_with_newline
    )
    for remaining in range(index, len(lines)):
        if lines[remaining].strip() and not lines[remaining].lstrip().startswith("#"):
            raise FrontmatterError(
                "无法解析, 请人工确认", first_line + remaining
            )
    return data


def parse_frontmatter(frontmatter_text, first_line=2):
    """返回 (字段映射, 解析器名称)."""
    data = parse_with_pyyaml(frontmatter_text, first_line)
    if data is not None:
        return data, "PyYAML"
    return parse_with_builtin(frontmatter_text, first_line), "内置解析器"


# ---------------------------------------------------------------------------
# Markdown 链接与引用


FENCE_PATTERN = re.compile(r"^( *)(`{3,}|~{3,})(.*)$")


def _is_fence(line, base_indent=0):
    """解析 CommonMark 围栏标记, 返回 (字符, 长度, 是否可闭合) 或 None.

    围栏行首最多 ``3 + base_indent`` 个空格, 之后是 3 个及以上连续的反引号
    或波浪线; ``base_indent`` 是外围列表项正文的缩进, 使列表内的围栏可以
    随列表缩进. 再深一层的行属于缩进代码块, 不构成围栏. 反引号围栏的 info
    string 不能含反引号, 否则该行不是围栏. 第三个返回值表示标记后只有空白,
    可用于闭合.
    """
    match = FENCE_PATTERN.match(line)
    if not match:
        return None
    if len(match.group(1)) > 3 + max(base_indent, 0):
        return None
    marker = match.group(2)
    rest = match.group(3)
    char = marker[0]
    if char == "`" and "`" in rest:
        return None
    return char, len(marker), not rest.strip()


LIST_MARKER_PATTERN = re.compile(r"^([ \t]*)((?:[+*-]|\d{1,9}[.)]))([ \t]*)")


def _leading_width(text):
    """返回行首空白宽度, Tab 按 4 列计."""
    width = 0
    for char in text:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4
        else:
            break
    return width


def _list_marker_indents(line):
    """返回列表标记的 (标记缩进, 正文缩进); 不是列表标记行时返回 None."""
    match = LIST_MARKER_PATTERN.match(line)
    if not match:
        return None
    prefix, marker, spacing = match.groups()
    if not spacing and line[match.end():].strip():
        return None
    marker_indent = _leading_width(prefix)
    content_indent = marker_indent + len(marker) + max(_leading_width(spacing), 1)
    return marker_indent, content_indent


def _list_content_indent(line):
    """返回列表项正文的起始列; 不是列表标记行时返回 None."""
    indents = _list_marker_indents(line)
    return None if indents is None else indents[1]


ATX_HEADING_PATTERN = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
SETEXT_UNDERLINE_PATTERN = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
THEMATIC_BREAK_PATTERN = re.compile(
    r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$"
)

LIST_REFERENCE_DEFINITION_PREFIX_PATTERN = re.compile(
    r"^ {0,3}(?:[+*-]|\d{1,9}[.)])[ \t]+"
)
ORDERED_REFERENCE_DEFINITION_PREFIX_PATTERN = re.compile(
    r"^ {0,3}(?P<number>\d{1,9})[.)][ \t]+"
)


def _strip_list_reference_prefix(line):
    """去掉列表项定义 ``- [x]: ...`` 的列表标记, 返回 (内容行, 是否列表项)."""
    match = LIST_REFERENCE_DEFINITION_PREFIX_PATTERN.match(line)
    if match is None:
        return line, False
    return line[match.end():], True


def _valid_reference_definition_line(line):
    """判断行内是否给出完整合法的引用定义 (目标后只允许空或可选标题).

    传入的行已去掉列表项标记. 判定与 :func:`_reference_definition_links`
    的登记规则一致: 目标后的额外文本既不是空也不是 CommonMark 可选标题
    时, 该行不是引用定义, 也不能作为相邻定义行的块级边界.
    """
    definition = REFERENCE_DEFINITION_PATTERN.match(line)
    if definition is None:
        return False
    rest = line[definition.end():].strip()
    return not rest or _is_reference_title(rest)


def _is_reference_definition_line(line):
    """判断整行是否为引用定义 (含列表项形式); 脚注定义 ``[^x]`` 不算.

    这里只用于判断相邻行的块级边界: 列表项只识别目标同行的形式, 跨行的
    列表项定义由 :func:`_reference_definition_links` 跳过续行的记录来识别.
    裸定义 ``[标签]:`` 不算边界: 它的下一行能否作为目标由
    :func:`_reference_definition_continuation` 判定, 目标行不成立时两行属于
    同一段落, 随后紧跟的 ``[标签]:`` 只是惰性续行而不是新定义. 跨行定义
    之后相邻的定义由 :func:`_reference_definition_links` 的
    ``last_consumed_index`` 识别, 不依赖本函数.
    """
    content, _ = _strip_list_reference_prefix(line)
    return _valid_reference_definition_line(content)


def _is_setext_underline(lines, index):
    """判断 ``lines[index]`` 是否为 Setext 标题下划线.

    ``===``/``---`` 只有在上一行是段落时才是标题下划线; 独立成行的 ``==``
    (或 ``--``) 前面没有段落文本, 它们本身只是一行普通段落, 不是块边界.
    上一行本身是块级结构 (空行, ATX 标题, 分隔线, 围栏, 列表项, 引用定义
    或另一条 Setext 下划线) 时同样不构成标题. 传入的行已去掉块引用前缀.
    """
    line = lines[index].rstrip("\r")
    if not SETEXT_UNDERLINE_PATTERN.match(line):
        return False
    return _is_setext_heading_text(lines, index - 1)


def _is_setext_heading_text(lines, index):
    """判断 ``lines[index]`` 能否作为 Setext 标题的段落文本行."""
    if index < 0:
        return False
    line = lines[index].rstrip("\r")
    if not line.strip():
        return False
    if ATX_HEADING_PATTERN.match(line):
        return False
    if THEMATIC_BREAK_PATTERN.match(line):
        return False
    if _is_fence(line) is not None:
        return False
    if _list_marker_indents(line) is not None:
        return False
    if _is_reference_definition_line(line):
        return False
    if SETEXT_UNDERLINE_PATTERN.match(line) and _is_setext_underline(lines, index):
        return False
    return True


def _is_block_start_before(lines, index):
    """判断 ``lines[index]`` 是否处于新块的开头, 用于识别引用定义.

    首行, 前一行为空行, 或前一行为标题, 分隔线, 围栏等块级结构时算块首;
    前一行为已识别的引用定义时也算 (连续的引用定义). 紧跟普通正文行或普
    通列表项行之后的 ``[x]: ...`` 不算, 它是惰性续行的一部分.
    前一行的 ``===``/``---`` 只有构成真实 Setext 标题下划线时才是块边界;
    独立成行的 ``==``/``--`` 是普通段落行, 其后的定义属于惰性续行.
    传入的行已去掉块引用前缀.
    """
    if index == 0:
        return True
    previous = lines[index - 1].rstrip("\r")
    if not previous.strip():
        return True
    if ATX_HEADING_PATTERN.match(previous):
        return True
    if SETEXT_UNDERLINE_PATTERN.match(previous) and _is_setext_underline(
        lines, index - 1
    ):
        return True
    if THEMATIC_BREAK_PATTERN.match(previous):
        return True
    if _is_fence(previous) is not None:
        return True
    return _is_reference_definition_line(previous)


def _enclosing_list_item_indents(lines, index):
    """返回 ``lines[index]`` 所属外层列表项的 (标记缩进, 正文缩进).

    只向上回溯同一段落块内的行, 空行即结束回溯; 不维护完整列表栈. 找到的
    是缩进不大于当前行的最近一个列表标记. 当前行不在列表项内 (没有外层
    列表标记) 时返回 None.
    """
    indents = _list_marker_indents(lines[index])
    if indents is None:
        return None
    current_indent = indents[0]
    for number in range(index - 1, -1, -1):
        line = lines[number].rstrip("\r")
        if not line.strip():
            return None
        marker = _list_marker_indents(line)
        if marker is not None and marker[0] <= current_indent:
            return marker
    return None


def _list_item_can_interrupt_paragraph(lines, index):
    """判断 ``lines[index]`` 的列表项标记能否打断上一行的段落.

    CommonMark 中只有从 1 开始的有序列表能打断段落; ``2)``, ``10.`` 等非 1
    序号属于段落的惰性续行, 其后的 ``[标签]:`` 不会成为引用定义. 上一行若
    不是普通段落 (空行, 标题, 分隔线, 围栏, 列表项, 引用定义等块边界), 该
    列表项本就处于块首, 总能起始, 返回 True. 传入的行已去掉块引用前缀.

    列表项内的段落另有两种边界: 标记缩进退回到外层列表标记的缩进 (或更
    浅) 时, 该项就此结束, 新列表项可以任意起始序号; 标记缩进仍深入外层
    列表项正文 (不小于正文缩进) 时, 它只是该项内段落的惰性续行, 同样要求
    从 1 开始. 标记缩进落在标记缩进与正文缩进之间时, 外层项已结束, 按新
    列表处理.
    """
    ordered = ORDERED_REFERENCE_DEFINITION_PREFIX_PATTERN.match(lines[index])
    if ordered is None or int(ordered.group("number")) == 1:
        return True
    if _is_block_start_before(lines, index):
        return True
    outer = _enclosing_list_item_indents(lines, index)
    if outer is None:
        return False
    marker_indent, content_indent = outer
    current_indent = _leading_width(lines[index][: ordered.start("number")])
    if current_indent <= marker_indent:
        return True
    return current_indent < content_indent


BLOCKQUOTE_PREFIX_PATTERN = re.compile(r" {0,3}> ?")
RAW_HTML_BLOCK_TAGS = ("pre", "script", "style", "textarea")
# CommonMark type 6 块级标签, 这类块从行首起始标签持续到空行.
TYPE6_HTML_BLOCK_TAGS = (
    "address",
    "article",
    "aside",
    "base",
    "basefont",
    "blockquote",
    "body",
    "caption",
    "center",
    "col",
    "colgroup",
    "dd",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "frame",
    "frameset",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hr",
    "html",
    "iframe",
    "legend",
    "li",
    "link",
    "main",
    "menu",
    "menuitem",
    "nav",
    "noframes",
    "ol",
    "optgroup",
    "option",
    "p",
    "param",
    "section",
    "source",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "title",
    "tr",
    "track",
    "ul",
)
# type 1 块只在行首 (最多 3 个空格缩进) 的起始标签处开始; 行内标签按普通
# 行内 HTML 处理, 不开启块.
RAW_HTML_BLOCK_START_PATTERN = re.compile(
    r" {0,3}<(?P<tag>" + "|".join(RAW_HTML_BLOCK_TAGS) + r")(?=[\s/>]|$)",
    re.IGNORECASE,
)
# type 6 块只在行首 (最多 3 个空格缩进) 的起始标签处开始.
TYPE6_HTML_BLOCK_PATTERN = re.compile(
    r" {0,3}<(?P<tag>"
    + "|".join(sorted(TYPE6_HTML_BLOCK_TAGS, key=len, reverse=True))
    + r")(?=[\s/>]|$)",
    re.IGNORECASE,
)
# type 7 块以行首 (最多 3 个空格缩进) 的完整开/闭标签行开始, 该行其余只有
# 空白, 一直持续到空行. 属性语法取自 CommonMark 的 HTML 标签定义, 避免把
# ``<https://example.com>`` 这类自动链接误判为标签行.
HTML_ATTRIBUTE_PATTERN = (
    r"[A-Za-z_:][A-Za-z0-9_.:-]*"
    r'(?:\s*=\s*(?:[^\s"\'=<>`]+|\'[^\']*\'|"[^"]*"))?'
)
TYPE7_HTML_BLOCK_PATTERN = re.compile(
    r" {0,3}(?:<(?P<open>[A-Za-z][A-Za-z0-9-]*)"
    r"(?:\s+" + HTML_ATTRIBUTE_PATTERN + r")*\s*/?>"
    r"|</(?P<close>[A-Za-z][A-Za-z0-9-]*)\s*>)[ \t]*$"
)
RAW_HTML_CLOSE_PATTERNS = {
    name: re.compile(r"</" + name + r"(?=[\s/>])", re.IGNORECASE)
    for name in RAW_HTML_BLOCK_TAGS
}


def _strip_blockquote_prefixes(line, limit=None):
    """去掉行首最多 ``limit`` 个块引用前缀 ``>``, 返回 (内容行, 去掉的个数).

    ``limit`` 为 None 时去掉全部前缀.
    """
    count = 0
    while limit is None or count < limit:
        match = BLOCKQUOTE_PREFIX_PATTERN.match(line)
        if not match:
            break
        line = line[match.end():]
        count += 1
    return line, count


def _strip_blockquote_prefix(line):
    """去掉行首可重复的块引用前缀 ``>``, 返回内容行."""
    return _strip_blockquote_prefixes(line)[0]


def _is_html_block_boundary(previous):
    """判断 ``previous`` 之后是否处于块边界, 供 type 7 块起始判定.

    type 7 块不能打断段落: 只有文档开头, 空行之后, 或标题, 分隔线, 围栏,
    列表项等块级结构之后才允许开启. ``previous`` 是上一行去掉块引用前缀后
    的内容.
    """
    if not previous.strip():
        return True
    if ATX_HEADING_PATTERN.match(previous):
        return True
    if SETEXT_UNDERLINE_PATTERN.match(previous):
        return True
    if THEMATIC_BREAK_PATTERN.match(previous):
        return True
    if _is_fence(previous) is not None:
        return True
    return _list_content_indent(previous) is not None


def _mask_raw_html_blocks(line, block, at_block_start=True):
    """把原始 HTML 块内容替换为空格, 返回 (脱敏后的行, 更新后的块内标签).

    ``block`` 是当前所处的原始文本块标签名 (小写) 或 None. ``pre``,
    ``script``, ``style`` 和 ``textarea`` 的块内内容不检查链接; 这类块
    只在行首 (最多 3 个空格缩进) 开启, 行内标签按普通行内 HTML 处理. 标
    签可同行打开并关闭, 关闭标签之后的行内内容仍会被检查; 写成自闭合形式
    (``<pre ... />``) 的起始标签同样开启块, 直到闭标签或文末. CommonMark
    type 6 块级标签 (``details``, ``div``, ``table`` 等) 从行首起始标签
    处开始, type 7 的完整标签行 (``<custom-tag>``, ``<br>`` 等) 从行首
    开始, 二者都一直持续到下一个空行, 期间同样不检查链接. type 7 块不
    打断段落, 只有 ``at_block_start`` 为真时才允许开启.
    """
    if block is not None and block not in RAW_HTML_BLOCK_TAGS:
        # type 6/7 块没有独立关闭条件, 空行才结束块.
        if not line.strip():
            return line, None
        return " " * len(line), block
    pieces = []
    position = 0
    size = len(line)
    if block is None:
        start = RAW_HTML_BLOCK_START_PATTERN.match(line)
        if start is not None:
            block = start.group("tag").lower()
        else:
            type6 = TYPE6_HTML_BLOCK_PATTERN.match(line)
            if type6 is not None:
                return " " * len(line), type6.group("tag").lower()
            if at_block_start:
                type7 = TYPE7_HTML_BLOCK_PATTERN.match(line)
                if type7 is not None:
                    tag = type7.group("open") or type7.group("close")
                    return " " * len(line), tag.lower()
    while position < size:
        if block is None:
            pieces.append(line[position:])
            break
        close = RAW_HTML_CLOSE_PATTERNS[block].search(line, position)
        if close is None:
            pieces.append(" " * (size - position))
            position = size
            break
        pieces.append(" " * (close.end() - position))
        position = close.end()
        block = None
    return "".join(pieces), block


def _scan_block_comment(line, in_comment):
    """返回 (HTML 注释之外的可见文本, 行末是否仍在注释内).

    用于块级判定: 只有注释的整行是 HTML 块 (CommonMark type 2), 注释结束
    之后即为新的块边界. 行内代码中的 ``<!--`` 不开启注释, 与
    :func:`_scan_inline` 的判定一致; 行首已在注释内时直接从 ``-->`` 继续
    扫描, 注释内部的反引号不再有意义.
    """
    visible = []
    index = 0
    size = len(line)
    while index < size or in_comment:
        if in_comment:
            end = line.find("-->", index)
            if end < 0:
                return "".join(visible), True
            in_comment = False
            index = end + 3
            continue
        masked, comments = _scan_inline(line[index:], mask_code=False)
        visible.append(masked)
        if (
            comments
            and comments[-1][1] == size - index
            and not line.endswith("-->", index, size)
        ):
            # 最后一个注释没有闭合, 屏蔽后的文本延伸到行尾.
            return "".join(visible), True
        break
    return "".join(visible), False


def _iter_block_lines(text):
    """按行返回 (行号, 内容, 是否代码块行).

    ``内容`` 不含行尾换行符. 围栏和缩进代码块的判定与块引用, 列表的既有
    处理保持一致, 围栏内的行按开围栏时去掉的块引用前缀个数剥离前缀, 因此
    ``> ``` `` 只在块引用围栏内才闭合围栏. 列表内开启的围栏以列表正文缩进
    为基准, 允许随列表缩进; 标题 (ATX 与 Setext), 分隔线, 闭合的围栏, 结束
    的 HTML 注释与在行内闭合的原始 HTML 块 (``pre`` 等) 之后视为新的块边界,
    紧随的缩进行因此进入缩进代码. 原始 HTML 块 (``pre`` 等, 以及 CommonMark
    type 6 的 ``details``/``div`` 等块级标签) 的内部不判定围栏, 与逐行扫描
    时的既有行为一致.
    """
    fence = None
    fence_prefix = 0
    fence_base = 0
    indented = False
    previous_blank = True
    list_indent = None
    html_block = None
    in_comment = False
    lines = text.split("\n")
    html_boundaries = []
    previous_content = None
    for raw_line in lines:
        content = _strip_blockquote_prefix(raw_line)
        html_boundaries.append(
            previous_content is None or _is_html_block_boundary(previous_content)
        )
        previous_content = content
    for number, raw_line in enumerate(lines, 1):
        if fence is not None:
            line = raw_line
            if fence_prefix:
                line = _strip_blockquote_prefixes(raw_line, fence_prefix)[0]
            parsed = _is_fence(line, fence_base)
            closed_fence = False
            if parsed is not None:
                char, length, closes = parsed
                if char == fence[0] and length >= fence[1] and closes:
                    fence = None
                    fence_prefix = 0
                    fence_base = 0
                    indented = False
                    closed_fence = True
            # 围栏闭合行之后是新的块边界.
            previous_blank = closed_fence or not line.strip()
            yield number, raw_line, True
            continue
        line, prefix_count = _strip_blockquote_prefixes(raw_line)
        blank = not line.strip()
        indent = _leading_width(line)
        if not blank and list_indent is not None and indent < list_indent:
            # 列表结束. 先重置, 使围栏, 标题, HTML 块等提前 return 的分支
            # 也不会沿用旧列表的缩进基准.
            list_indent = None
        if in_comment:
            visible, in_comment = _scan_block_comment(line, True)
            # 注释结束且其后没有可见内容时, 下一行处于块边界.
            previous_blank = not visible.strip() and not in_comment
            yield number, raw_line, False
            continue
        if html_block is not None:
            _, html_block = _mask_raw_html_blocks(
                line, html_block, at_block_start=html_boundaries[number - 1]
            )
            # 原始 HTML 块在本行结束 (type 1 的闭合标签) 时, 下一行处于块边界.
            previous_blank = blank or html_block is None
            yield number, raw_line, False
            continue
        masked_html, next_html_block = _mask_raw_html_blocks(
            line, None, at_block_start=html_boundaries[number - 1]
        )
        if next_html_block is not None or masked_html != line:
            # 本行开启原始 HTML 块 (type 1/6/7); 同行闭合时下一行处于块边界.
            html_block = next_html_block
            previous_blank = blank or next_html_block is None
            yield number, raw_line, False
            continue
        parsed = _is_fence(line, list_indent or 0)
        if parsed is not None:
            char, length, _ = parsed
            fence = (char, length)
            fence_prefix = prefix_count
            fence_base = list_indent or 0
            indented = False
            previous_blank = blank
            yield number, raw_line, True
            continue
        block_boundary = bool(
            not blank
            and (
                ATX_HEADING_PATTERN.match(line)
                or THEMATIC_BREAK_PATTERN.match(line)
                # 空列表项标记 (``-``) 不是 Setext 下划线.
                or (
                    SETEXT_UNDERLINE_PATTERN.match(line)
                    and _list_content_indent(line) is None
                )
            )
        )
        if block_boundary:
            content_indent = None
        else:
            content_indent = None if blank else _list_content_indent(line)
        if indented:
            if blank or indent >= (list_indent or 0) + 4:
                previous_blank = blank
                yield number, raw_line, True
                continue
            indented = False
        if content_indent is not None:
            list_indent = content_indent
        else:
            if not blank and previous_blank and indent >= (list_indent or 0) + 4:
                indented = True
                previous_blank = blank
                yield number, raw_line, True
                continue
        visible, in_comment = _scan_block_comment(line, False)
        if not visible.strip():
            # 本行只有 HTML 注释 (可能开启未闭合注释): 注释结束处是新的块
            # 边界, 紧随的缩进行因此进入缩进代码.
            previous_blank = not in_comment
            yield number, raw_line, False
            continue
        previous_blank = blank or block_boundary
        yield number, raw_line, False


def _mask_code_blocks(text):
    """把围栏与缩进代码块的内容替换为空格, 保留行数和换行符.

    只按 ``\\n`` 分行, 因此 U+2028 等字符不会改变行号或字符偏移.
    """
    masked = []
    for _, line, is_code in _iter_block_lines(text):
        masked.append(" " * len(line) if is_code else line)
    return "\n".join(masked)


def _find_closing_backticks(text, index, length):
    """返回长度恰好为 length 的下一段反引号的起始位置; 没有则返回 -1."""
    size = len(text)
    while index < size:
        if text[index] != "`":
            index += 1
            continue
        start = index
        while index < size and text[index] == "`":
            index += 1
        if index - start == length:
            return start
    return -1


def _mask_into(pieces, segment):
    """把 segment 脱敏为空格写入 pieces, 保留换行符."""
    for char in segment:
        pieces.append(char if char in "\r\n" else " ")


def _mask_inline_and_comments(text):
    """把行内代码与 HTML 注释替换为空格, 保留换行."""
    return _scan_inline(text)[0]


def _scan_inline(text, mask_code=True):
    """扫描行内代码与 HTML 注释, 返回 (屏蔽后的文本, 注释区间列表).

    按字符顺序扫描, 因此代码段内的 ``<!--`` 不会开启注释; 反引号按
    CommonMark 规则成对匹配: 长度为 n 的反引号串只由后面长度恰好为 n 的
    反引号串闭合, 找不到闭合串时该串按普通字符保留. 代码段可以跨行.
    HTML 注释同样可以跨行; 找不到 ``-->`` 时注释延续到文末.

    ``mask_code`` 为 False 时保留行内代码原文, 只屏蔽注释.
    """
    pieces = []
    comments = []
    index = 0
    size = len(text)
    while index < size:
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            stop = size if end < 0 else end + 3
            comments.append((index, stop))
            _mask_into(pieces, text[index:stop])
            index = stop
            continue
        if text[index] == "`":
            run_end = index
            while run_end < size and text[run_end] == "`":
                run_end += 1
            length = run_end - index
            closing = _find_closing_backticks(text, run_end, length)
            if closing < 0:
                pieces.append(text[index:run_end])
                index = run_end
                continue
            stop = closing + length
            if mask_code:
                _mask_into(pieces, text[index:stop])
            else:
                pieces.append(text[index:stop])
            index = stop
            continue
        pieces.append(text[index])
        index += 1
    return "".join(pieces), comments


def _mask_code_and_comments(text):
    """把整篇文本中的代码块, 行内代码与 HTML 注释替换为空格, 保留换行.

    先按 Markdown 块结构屏蔽围栏与缩进代码块, 因此代码块内的 ``<!--``
    不会开启注释; 之后再处理剩余文本中的行内代码与 HTML 注释.
    """
    return _mask_inline_and_comments(_mask_code_blocks(text))


def _has_body_content(text):
    """判断正文去掉 HTML 注释后是否还有内容.

    代码块和行内代码都算作正文内容; 代码块内的 ``<!--`` 不会被当成注释
    开始, 因此不会吞掉后面的正文. ``_mask_code_blocks`` 保持字符偏移,
    所以在屏蔽代码块后的文本上定位到的注释区间可以直接用于原文.
    """
    _, comments = _scan_inline(_mask_code_blocks(text), mask_code=False)
    visible = list(text)
    for start, stop in comments:
        visible[start:stop] = " " * (stop - start)
    return "".join(visible).strip() != ""


def _body_line_count(body):
    """统计正文行数, 忽略开头的空行 (frontmatter 后的惯例空行不计入)."""
    lines = body.splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    return len(lines) - start


def _unescape_markdown(value):
    r"""解码 Markdown 反斜杠转义: ``\(`` -> ``(``, ``\\`` -> ``\``.

    只有 ASCII 标点前的反斜杠算转义, 其它反斜杠 (如路径分隔符) 原样保留.
    """
    pieces = []
    index = 0
    size = len(value)
    while index < size:
        char = value[index]
        if (
            char == "\\"
            and index + 1 < size
            and value[index + 1] in ESCAPABLE_PUNCTUATION
        ):
            pieces.append(value[index + 1])
            index += 2
            continue
        pieces.append(char)
        index += 1
    return "".join(pieces)


def _skip_link_space(text, index):
    """跳过链接语法允许的空白 (含换行), 返回新下标."""
    size = len(text)
    while index < size and text[index] in " \t\r\n":
        index += 1
    return index


def _find_label_end(text, start):
    """返回与 ``text[start]`` 的 ``[`` 配对的 ``]`` 下标, 没有则返回 -1.

    ``start`` 必须指向 ``[``. 允许嵌套方括号, 并跳过反斜杠转义.
    """
    depth = 0
    index = start
    size = len(text)
    while index < size:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _find_title_end(text, start):
    """返回链接标题结束后的下标; 没有闭合则返回 -1."""
    closer = ")" if text[start] == "(" else text[start]
    index = start + 1
    size = len(text)
    while index < size:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == closer:
            return index + 1
        index += 1
    return -1


def _is_reference_title(value):
    """判断整段文本是否为 CommonMark 定义目标后的可选标题.

    双引号, 单引号或圆括号必须包裹整段文本, 且标题内部允许反斜杠转义
    (``"标\\"题"``), 因此闭合符不能简单按正则扫描. 未加引号/括号的额外
    文本不是标题, 不论与目标同行还是写在续行里都留给人工核对.
    """
    if not value or value[0] not in "\"'(":
        return False
    return _find_title_end(value, 0) == len(value)


def _parse_link_destination(text, start):
    """解析 ``(`` 之后的目标与可选标题, 返回 (目标, 右括号之后的下标).

    目标可以是 ``<...>`` (允许空格) 或按平衡括号规则延伸的裸字符串;
    解析出的目标已解码反斜杠转义. 语法不完整时返回 None.
    """
    size = len(text)
    index = _skip_link_space(text, start)
    if index >= size:
        return None
    if text[index] == "<":
        end = index + 1
        while end < size:
            char = text[end]
            if char == "\\":
                if end + 1 < size and text[end + 1] in ESCAPABLE_PUNCTUATION:
                    end += 2
                    continue
                end += 1
                continue
            if char == "<":
                return None
            if char == ">":
                break
            end += 1
        if end >= size:
            return None
        target = text[index + 1:end]
        after = end + 1
    else:
        end = index
        depth = 0
        while end < size:
            char = text[end]
            if char == "\\":
                # 只有 ASCII 标点前的反斜杠是合法转义; 空白前或结尾的反斜杠
                # 在此结束目标 (解析因缺少右括号而失败), 其它字符前按字面量
                # 保留, 以便识别 C:\... 与 \\server\share 这类 Windows 路径.
                following = text[end + 1] if end + 1 < size else ""
                if following in ESCAPABLE_PUNCTUATION:
                    end += 2
                    continue
                if not following or following in " \t\r\n":
                    break
                end += 1
                continue
            if char in " \t\r\n":
                break
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            end += 1
        if end == index or depth:
            return None
        target = text[index:end]
        after = end
    spaced = _skip_link_space(text, after)
    if spaced > after and spaced < size and text[spaced] in "\"'(":
        title_end = _find_title_end(text, spaced)
        if title_end < 0:
            return None
        spaced = _skip_link_space(text, title_end)
    if spaced >= size or text[spaced] != ")":
        return None
    return _unescape_markdown(target), spaced + 1


def _scan_inline_links(text):
    """字符级扫描内联链接, 返回 [(链接起始下标, 目标), ...].

    ``text`` 已由调用方脱敏 (代码块, 行内代码, 注释和原始 HTML), 因此这里只按
    字符顺序解析: 跳过转义字符, 从非转义的 ``[`` (可带前导 ``!``) 开始, 匹配
    允许嵌套的 ``]``, 再要求紧跟 ``(`` 并成功解析目标与闭合 ``)``. 解析失败时
    从 ``[`` 的下一个字符继续扫描, 因此不会产生半个链接.
    """
    links = []
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "!" and text.startswith("[", index + 1):
            start, bracket = index, index + 1
        elif char == "[":
            start, bracket = index, index
        else:
            index += 1
            continue
        label_end = _find_label_end(text, bracket)
        if label_end < 0:
            index += 1
            continue
        if text.startswith("(", label_end + 1):
            parsed = _parse_link_destination(text, label_end + 2)
            if parsed is not None:
                target, index = parsed
                links.append((start, target))
                continue
        index = bracket + 1
    return links


def _scan_inline_images(text):
    """字符级扫描内联图片目标, 返回 [(图片起始下标, 目标), ...].

    与外层链接的扫描彼此独立: 未转义的 ``!`` 后紧跟 ``[...](...)`` 即视为
    图片, 因此 ``[![alt](图.png)](文件.md)`` 中的图片目标也能被发现. 图片
    标签内的文本会继续扫描, 以支持嵌套图片.
    """
    images = []
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "!" and text.startswith("[", index + 1):
            label_end = _find_label_end(text, index + 1)
            if label_end >= 0 and text.startswith("(", label_end + 1):
                parsed = _parse_link_destination(text, label_end + 2)
                if parsed is not None:
                    target, _ = parsed
                    images.append((index, target))
                    # 继续扫描标签内部, 以发现嵌套图片目标.
                    index += 2
                    continue
        index += 1
    return images


def _reference_definition_continuation(line):
    """返回跨行引用定义续行的 (目标, 目标后剩余文本); 续行不成立时返回 None.

    续行可以缩进也可以不缩进 (CommonMark 允许 ``[标签]:`` 的下一行直接写
    目标), 目标之后还可以跟一个可选标题 (``"..."``, ``'...'`` 或 ``(...)``),
    此时剩余文本即该同行标题, 为空则表示没有标题. ``<...>`` 形式的目标允许
    包含空格, 只接受 ``>`` 之后为空或是标题的情况; 裸目标必须是不含空白的
    单一 token, 其后的文本同样只允许为空或标题. 因此 ``Some text`` 和
    ``a.md 标题`` 这类普通段落不会被当成定义目标 (未加引号/括号的额外文本
    不是 CommonMark 标题), 留给人工核对. 已解码反斜杠转义.

    块级标记 (分隔线, Setext 下划线, ATX 标题) 不是定义目标: ``[标签]:``
    之后紧跟 ``---`` 时, 该行是分隔线而非未缩进目标, 这类情况留给人工核对.
    """
    value = line.strip()
    if not value:
        return None
    if (
        THEMATIC_BREAK_PATTERN.match(value)
        or SETEXT_UNDERLINE_PATTERN.match(value)
        or ATX_HEADING_PATTERN.match(value)
    ):
        return None
    if value.startswith("<"):
        end = value.find(">")
        if end < 0:
            return None
        rest = value[end + 1 :].strip()
        if rest and not _is_reference_title(rest):
            return None
        return _unescape_markdown(value[1:end].strip()), rest
    parts = value.split(None, 1)
    rest = parts[1].strip() if len(parts) > 1 else ""
    if rest and not _is_reference_title(rest):
        return None
    return _unescape_markdown(parts[0]), rest


def _masked_link_lines(text):
    """返回 (脱敏后的行, 拼接文本, 每行起始下标).

    围栏代码块, 缩进代码块, 行内代码, HTML 注释与原始 HTML 块都被替换为
    空格, 因此后续扫描不会把其中的 Markdown 或 HTML 链接当作真实链接.
    代码块与块引用前缀的判定由 :func:`_mask_code_and_comments` 完成.
    """
    lines = []
    html_block = None
    previous_content = None
    for raw_line in _mask_code_and_comments(text).split("\n"):
        line = _strip_blockquote_prefix(raw_line)
        at_block_start = (
            previous_content is None or _is_html_block_boundary(previous_content)
        )
        line, html_block = _mask_raw_html_blocks(
            line, html_block, at_block_start=at_block_start
        )
        lines.append(line)
        previous_content = line

    line_starts = []
    position = 0
    for line in lines:
        line_starts.append(position)
        position += len(line) + 1
    return lines, "\n".join(lines), line_starts


def _reference_label(line):
    """返回引用定义行里的标签原文; 没有标签时返回空串."""
    match = re.match(r"^ {0,3}\[(?!\^)((?:\\.|[^\]\\])+)\]", line)
    return match.group(1) if match else ""


def _normalize_reference_label(label):
    """按 CommonMark 规则归一化引用标签: 折叠空白并忽略大小写."""
    return " ".join(label.split()).casefold()


def _consume_reference_definition_title(lines, index):
    """返回引用定义结束行的下标: 紧随其后的独占标题行也计入.

    CommonMark 允许可选标题独占目标之后的一行, 与目标同行等价. 只有引号
    或括号包裹的整行才算标题 (转义感知, 见 :func:`_is_reference_title`),
    普通段落行不消费, 留给后续的行级判定, 避免把正文误当标题. 标题行
    缩进或不缩进都一样: 列表项形式的定义 (``- [标签]: 目标``) 之后未缩进
    的标题行同样属于该定义, 而不是新的块.
    定义行或目标续行本身已带同行标题时, 后续行不再是标题, 调用方不调用
    本函数.
    """
    following = index + 1
    if following >= len(lines):
        return index
    return following if _is_reference_title(lines[following].strip()) else index


def _mask_definition_lines(lines, definition_lines):
    """返回把引用定义相关行整体替换为空格后的行列表.

    CommonMark 的引用定义行, 跨行目标行以及独占标题行都按纯文本解析,
    其中的 ``[...](...)`` 与 ``[文本][标签]`` 不是链接. 行号与字符下标
    保持不变, 因此行内链接扫描报告的位置仍然准确.
    """
    return [
        " " * len(line) if index in definition_lines else line
        for index, line in enumerate(lines)
    ]


def _reference_definition_links(lines):
    """返回 ([(行号, 目标), ...], {归一化标签}, {被消费的 0 基行号}).

    参考定义行按行级正则匹配; 列表项形式的定义 (``- [x]: 目标``) 与连续
    的参考定义同样会被识别. 目标写在下一行的跨行定义也会被识别 (缩进或
    不缩进都可以, 列表项形式也一样, 目标后可跟 CommonMark 可选标题), 并
    跳过该续行; 标题也可以独占紧随目标的一行 (缩进或不缩进都可以), 该行
    同样被消费. 但定义行或目标续行本身已带同行标题时, 其下一行是普通段落
    (CommonMark 惰性续行), 不消费, 因此紧随其后的 ``[标签]:`` 也不会被当
    成块首定义. 紧随被跳过续行之后的定义视为块首, 因此相邻的跨行定义都能
    识别.
    只有成功解析出目标的定义才登记标签, 裸定义 ``[标签]:`` 后没有有效目
    标时既不登记标签也不产生链接, 因此对应的全引用链接会报告定义缺失.
    列表项只在能打断段落时才算块首: 只有从 1 开始的有序列表可以打断段落,
    ``2)``, ``10.`` 等紧跟正文后的列表项属于惰性续行, 其定义不登记.
    """
    links = []
    labels = set()
    definition_lines = set()
    index = 0
    total = len(lines)
    last_consumed_index = -1
    while index < total:
        line, is_list_item = _strip_list_reference_prefix(lines[index])
        at_block_start = (
            (is_list_item and _list_item_can_interrupt_paragraph(lines, index))
            or index == last_consumed_index + 1
            or _is_block_start_before(lines, index)
        )
        if at_block_start:
            definition = REFERENCE_DEFINITION_PATTERN.match(line)
            if definition:
                if not _valid_reference_definition_line(line):
                    # 同行目标后的额外文本既不是可选标题, 该行就不是
                    # CommonMark 引用定义: 不登记标签, 不产生链接.
                    index += 1
                    continue
                rest = line[definition.end() :].strip()
                links.append((index + 1, _unescape_markdown(definition.group(1))))
                labels.add(_normalize_reference_label(_reference_label(line)))
                # 同行已有标题时, 下一行只是普通段落: 不再消费独占标题行,
                # 否则该行之后的定义会被误当块首登记.
                last_consumed_index = (
                    index
                    if rest
                    else _consume_reference_definition_title(lines, index)
                )
                definition_lines.update(range(index, last_consumed_index + 1))
            elif EMPTY_REFERENCE_DEFINITION_PATTERN.match(line):
                continuation = lines[index + 1] if index + 1 < total else ""
                parsed = _reference_definition_continuation(continuation)
                if parsed is not None:
                    target, continuation_rest = parsed
                    labels.add(_normalize_reference_label(_reference_label(line)))
                    links.append((index + 1, target))
                    # 目标续行已带同行标题时, 其下一行同样是普通段落.
                    last_consumed_index = (
                        index + 1
                        if continuation_rest
                        else _consume_reference_definition_title(lines, index + 1)
                    )
                    definition_lines.update(range(index, last_consumed_index + 1))
                    index = last_consumed_index
        index += 1
    return links, labels, definition_lines


def _scan_html_links(lines):
    """返回脱敏行里 ``<a href>`` 与 ``<img src>`` 的 [(行号, 目标), ...]."""
    links = []
    for number, line in enumerate(lines, 1):
        for match in HTML_LINK_ATTRIBUTE_PATTERN.finditer(line):
            target = next(
                (value for value in match.groups() if value is not None), None
            )
            if target is not None:
                links.append((number, target))
    return links


def _scan_reference_labels(text):
    """字符级扫描全引用链接 ``[文本][标签]``, 返回 [(起始下标, 标签), ...].

    空标签的折叠引用 ``[文本][]`` 不在此列, 脚注引用 ``[^x]`` 也不算.
    成功解析的内联链接目标会被整体跳过, 因此 ``[b](目标)`` 不会被误拆成
    引用; ``[a][b](目标)`` 按 CommonMark 仍视为 ``[a][b]`` 全引用链接.
    """
    labels = []
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "!" and text.startswith("[", index + 1):
            bracket = index + 1
        elif char == "[":
            bracket = index
        else:
            index += 1
            continue
        label_end = _find_label_end(text, bracket)
        if label_end < 0:
            index = bracket + 1
            continue
        if text.startswith("(", label_end + 1):
            parsed = _parse_link_destination(text, label_end + 2)
            if parsed is not None:
                _, index = parsed
                continue
            index = bracket + 1
            continue
        if text.startswith("[", label_end + 1):
            reference_end = _find_label_end(text, label_end + 1)
            if reference_end >= 0:
                identifier = text[label_end + 2:reference_end].strip()
                if identifier and not identifier.startswith("^"):
                    labels.append((bracket, identifier))
                index = reference_end + 1
                continue
        index = bracket + 1
    return labels


def scan_links(text):
    """返回 [(行号, 目标), ...].

    跳过围栏代码块, 缩进代码块, HTML 注释, 行内代码和原始 HTML 块
    (``pre``, ``script``, ``style``, ``textarea`` 以及 ``details``/``div``
    等 CommonMark type 6 块级标签) 中的链接. 代码块与块引用前缀的判定由
    :func:`_mask_code_and_comments` 完成.

    内联链接由 :func:`_scan_inline_links` 按字符级语法解析, 因此支持转义,
    嵌套方括号文本, 跨行目标与平衡括号; 起始行号取 ``[`` 所在行.
    内联图片目标由 :func:`_scan_inline_images` 单独扫描后合并去重, 因此
    ``[![alt](图.png)](文件.md)`` 里的图片目标也会被检查.
    HTML ``<a href>`` 与 ``<img src>`` 的属性值由
    :func:`_scan_html_links` 在同一份脱敏文本上扫描.
    参考定义行按行级正则匹配; 列表项形式的定义 (``- [x]: 目标``) 与连续
    的参考定义同样会被识别, 目标写在下一行 (缩进或不缩进, 含列表项形式与
    相邻的跨行定义) 的跨行定义也会被识别, 并跳过该续行.
    引用定义行及其目标/标题在行内扫描前被整体屏蔽, 因此标题里的
    ``[x](缺失.md)`` 或 ``[x][y]`` 不会被误报; 定义目标仍由
    :func:`_reference_definition_links` 检查.
    """
    lines, _, line_starts = _masked_link_lines(text)
    definition_links, _, definition_lines = _reference_definition_links(lines)
    # 引用定义行 (含跨行目标与独占标题) 在 CommonMark 里是纯文本, 其中的
    # 方括号与圆括号不是链接; 定义目标本身由 _reference_definition_links
    # 检查, 因此行内扫描与 HTML 属性扫描都使用屏蔽掉这些行的文本.
    scanning_lines = _mask_definition_lines(lines, definition_lines)
    scanning = "\n".join(scanning_lines)
    # 图片既可能单独出现, 也可能嵌在链接文本里; 两种扫描合并去重, 避免
    # 独立图片被当作普通链接重复处理.
    findings = _scan_inline_links(scanning) + _scan_inline_images(scanning)
    findings.sort(key=lambda finding: finding[0])
    links = []
    seen = set()
    for position, target in findings:
        key = (position, target)
        if key in seen:
            continue
        seen.add(key)
        links.append((bisect.bisect_right(line_starts, position), target))
    links.extend(definition_links)
    links.extend(_scan_html_links(scanning_lines))
    links.sort(key=lambda link: link[0])
    return links


def scan_missing_reference_links(text):
    """返回 [(行号, 标签), ...], 标签非空且没有对应定义的引用式链接.

    定义存在时其目标已由 :func:`scan_links` 检查, 这里只报告缺失的定义.
    与 :func:`scan_links` 使用同一套脱敏文本, 因此代码块与原始 HTML 块内
    的 ``[文本][标签]`` 不会被误报.
    """
    lines, _, line_starts = _masked_link_lines(text)
    _, labels, definition_lines = _reference_definition_links(lines)
    # 定义行及其目标/标题在 CommonMark 里是纯文本, 其中的 [文本][标签]
    # 不是引用式链接, 因此同样用屏蔽掉这些行的文本扫描.
    scanning = "\n".join(_mask_definition_lines(lines, definition_lines))
    missing = []
    for position, identifier in _scan_reference_labels(scanning):
        if _normalize_reference_label(identifier) in labels:
            continue
        missing.append(
            (bisect.bisect_right(line_starts, position), identifier)
        )
    return missing


def _is_windows_absolute_path(value):
    """判断是否为 Windows 盘符路径 (含盘符相对) 或 UNC 路径."""
    if WINDOWS_PATH_PATTERN.match(value):
        return True
    if WINDOWS_FORWARD_UNC_PATTERN.match(value):
        return True
    # Markdown 反斜杠转义可能把 UNC 开头的 ``\\server`` 变成 ``\server``.
    return value.startswith("\\") and "\\" in value[1:]


def local_target(target):
    """把链接目标转为本地路径; 外部链接和纯锚点返回 None.

    目标先解码 HTML 实体 (``&amp;`` 等), 再做存在性检查.
    以 `/` 开头的绝对路径和 Windows 盘符/UNC 路径会原样返回, 交给调用方
    给出可移植性警告.
    """
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = html.unescape(target)
    if not target or target.startswith("#"):
        return None
    if _is_windows_absolute_path(target):
        return target
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    if target.startswith("//"):
        return None
    path = target.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    return unquote(path)


def _mentions_path(text, relative_path):
    """判断正文是否以纯文本提到路径.

    路径边界只由 ASCII 路径字符决定, 因此中文紧邻 (如 "运行scripts/foo.py") 算命中.
    允许 ``./`` 前缀 (如 "运行 ./scripts/foo.py"), 前缀之前同样受路径边界约束.
    结尾允许一个句末句点, 但后面不能再接路径字符, 所以 "scripts/foo.py." 算命中,
    "scripts/foo.py.bak" 不算.
    """
    pattern = (
        r"(?<![A-Za-z0-9_./-])(?:\./)?"
        + re.escape(relative_path)
        + r"(?!(?:[A-Za-z0-9_/-]|\.(?=[A-Za-z0-9_./-])))"
    )
    return re.search(pattern, text) is not None


def _license_file(skill_dir, data):
    """返回 license 字段整体指向的 skill 目录内现有文件的绝对路径; 否则返回 None."""
    value = data.get("license")
    if not isinstance(value, str):
        return None
    target = value.strip()
    if not target:
        return None
    root = skill_dir.resolve()
    try:
        candidate = (root / target).resolve()
    except (OSError, ValueError):
        return None
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    try:
        is_file = candidate.is_file()
    except (OSError, ValueError):
        return None
    if not is_file:
        return None
    return candidate


def _is_same_file(path, other):
    """比较两个路径是否指向同一文件, 兼容符号链接和大小写不敏感的文件系统."""
    try:
        return os.path.samefile(path, other)
    except (OSError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 校验


def _top_level_key_lines(frontmatter_lines, first_line):
    lines = {}
    for index, line in enumerate(frontmatter_lines):
        if not line or line[0] in " \t#":
            continue
        line_no = first_line + index
        if line[0] in "'\"":
            try:
                parsed = _parse_quoted_key(line, line_no)
            except FrontmatterError:
                continue
            if parsed is not None:
                lines[parsed[0]] = line_no
            continue
        match = re.match(r"([A-Za-z0-9_.-]+) *:", line)
        if match:
            lines[match.group(1)] = line_no
            continue
        # 非 ASCII 的非标准键不匹配上面的 ASCII 模式, 改用通用分割兜底.
        parsed = _split_unicode_key(line)
        if parsed is not None:
            lines[parsed[0]] = line_no
    return lines


def _issue_key(issue):
    file_name, separator, line = issue.location.rpartition(":")
    if separator and line.isdigit():
        return (file_name, int(line), issue.message)
    return (issue.location, 0, issue.message)


def _validate_fields(data, key_lines, skill_name, errors, warnings):
    def location(field):
        return "SKILL.md:{}".format(key_lines.get(field, 2))

    name = data.get("name")
    if name is None:
        errors.append(Issue(location("name"), "缺少 name 字段"))
    elif not isinstance(name, str):
        errors.append(Issue(location("name"), "name 必须是字符串"))
    else:
        problem = validate_name(name)
        if problem:
            errors.append(Issue(location("name"), problem))
        # name 字段先去除首尾空白再做 NFKC; 父目录名只做 NFKC, 因此目录名
        # 带首尾空白时会被视为与 name 不一致.
        if normalize_name(name) != unicodedata.normalize("NFKC", skill_name):
            errors.append(
                Issue(
                    location("name"),
                    "name 与父目录名不一致: {} != {}".format(name, skill_name),
                )
            )

    description = data.get("description")
    if description is None:
        errors.append(Issue(location("description"), "缺少 description 字段"))
    elif not isinstance(description, str):
        errors.append(Issue(location("description"), "description 必须是字符串"))
    elif description.strip() == "":
        errors.append(Issue(location("description"), "description 不能为空"))
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            Issue(
                location("description"),
                "description 不能超过 {} 字符, 当前为 {} 字符".format(
                    MAX_DESCRIPTION_LENGTH, len(description)
                ),
            )
        )

    if "license" in data:
        value = data["license"]
        if not isinstance(value, str):
            errors.append(Issue(location("license"), "license 必须是字符串"))

    if "compatibility" in data:
        value = data["compatibility"]
        if not isinstance(value, str):
            errors.append(Issue(location("compatibility"), "compatibility 必须是字符串"))
        elif not 1 <= len(value) <= MAX_COMPATIBILITY_LENGTH:
            errors.append(
                Issue(
                    location("compatibility"),
                    "compatibility 长度必须在 1-{} 字符之间, 当前为 {} 字符".format(
                        MAX_COMPATIBILITY_LENGTH, len(value)
                    ),
                )
            )

    if "metadata" in data:
        value = data["metadata"]
        if not isinstance(value, dict):
            errors.append(Issue(location("metadata"), "metadata 必须是键值映射"))
        else:
            for key, item in value.items():
                if not isinstance(key, str):
                    errors.append(
                        Issue(location("metadata"), "metadata 的键必须是字符串")
                    )
                    continue
                if not isinstance(item, str):
                    errors.append(
                        Issue(
                            location("metadata"),
                            "metadata.{} 的值必须是字符串".format(key),
                        )
                    )

    if "allowed-tools" in data:
        value = data["allowed-tools"]
        if not isinstance(value, str):
            errors.append(
                Issue(location("allowed-tools"), "allowed-tools 必须是字符串")
            )
        elif not value.split() or any(
            char in ",;" or (char.isspace() and char != " ") for char in value
        ):
            errors.append(
                Issue(
                    location("allowed-tools"),
                    "allowed-tools 必须是空格分隔的工具名字符串",
                )
            )

    for key in data:
        if not isinstance(key, str) or key not in STANDARD_FIELDS:
            line = key_lines.get(key, 2) if isinstance(key, str) else 2
            warnings.append(
                Issue("SKILL.md:{}".format(line), "非标准字段: {}".format(key))
            )


def _resolve_local_link(skill_dir, base_dir, local):
    """解析本地链接, 返回 (存在的目标路径, 是否只能按所在文件目录解析).

    先按 skill 根目录解析, 再按链接所在文件目录解析. 仅当根目录解析不到而
    所在文件目录能解析到时, 第二个返回值才为 True. 两者都存在或所在文件
    目录就是 skill 根目录时, 该值为 False.
    """
    root = skill_dir.resolve()
    try:
        base = base_dir.resolve()
    except (OSError, ValueError):
        base = base_dir
    try:
        by_root = (root / local).resolve()
    except (OSError, ValueError):
        by_root = None
    try:
        root_exists = by_root is not None and by_root.exists()
    except (OSError, ValueError):
        root_exists = False
    if root_exists:
        return by_root, False
    try:
        by_base = (base / local).resolve()
    except (OSError, ValueError):
        by_base = None
    try:
        base_exists = by_base is not None and by_base.exists()
    except (OSError, ValueError):
        base_exists = False
    if base_exists:
        return by_base, base != root
    return None, False


def _is_within(path, root):
    """判断 path 是否位于 root 目录内."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_ignored_path(path):
    """判断相对路径是否位于隐藏文件/目录或 __pycache__ 中."""
    return any(part.startswith(".") or part == "__pycache__" for part in path.parts)


def _has_control_characters(value):
    """判断字符串是否含 NUL 或 Unicode Cc 类控制字符 (C0, DEL 与 C1)."""
    return any(unicodedata.category(char) == "Cc" for char in value)


def _match_disk_case(root, candidate):
    """按磁盘实际名称逐段匹配 candidate, 返回 (实际路径, 是否大小写不一致).

    candidate 必须词法上位于 root 内且不含 ``..``; 每段优先精确匹配, 否则
    按大小写折叠匹配. 任一段缺失, 目录不可读或路径越界时返回 None. 最终
    路径必须存在, 因此调用方可以安全地把它当作链接目标.
    """
    try:
        root = root.resolve()
        relative = candidate.relative_to(root)
    except (OSError, ValueError):
        return None
    parts = relative.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return None
    current = root
    actual_parts = []
    mismatched = False
    for part in parts:
        try:
            entries = os.listdir(current)
        except OSError:
            return None
        if part in entries:
            actual = part
        else:
            folded = part.casefold()
            matches = [entry for entry in entries if entry.casefold() == folded]
            if not matches:
                return None
            actual = sorted(matches)[0]
            mismatched = True
        actual_parts.append(actual)
        current = current / actual
    try:
        if not current.exists():
            return None
    except (OSError, ValueError):
        return None
    return root / Path(*actual_parts), mismatched


def _resolve_case_insensitive_link(skill_dir, base_dir, local):
    """按大小写折叠回退解析本地链接, 返回 (路径, 是否仅按文件目录解析, 是否大小写不一致).

    仅在精确解析失败时使用, 让同一份文档在大小写敏感与不敏感文件系统上
    得到一致的大小写警告, 而不是在敏感平台上退化为 "目标不存在".
    """
    root = skill_dir.resolve()
    try:
        base = base_dir.resolve()
    except (OSError, ValueError):
        base = base_dir
    for candidate_base in (root, base):
        matched = _match_disk_case(root, candidate_base / local)
        if matched is None:
            continue
        path, _ = matched
        return path, candidate_base != root, True
    return None, False, False


def _validate_local_link(skill_dir, base_dir, local, location, errors, warnings):
    """检查一条本地链接, 返回 skill 目录内存在的目标路径或 None.

    目标不存在是错误. 含 NUL 或 Unicode Cc 类控制字符 (C0, DEL 与 C1) 的目标
    一律报错, 不进入文件系统调用.
    绝对路径和落在 skill 目录外的目标存在时只给可移植性警告; Windows 盘符/
    UNC 路径一律只给警告. 绝对路径目标若位于 skill 目录内则仍返回, 以便计入
    被引用文件. 参考文件内只能按所在文件目录解析的链接也给出警告. 链接能
    解析到文件但路径分量大小写与磁盘实际名称不一致时给出不可移植警告, 并
    返回磁盘上的实际路径, 避免产生额外的未引用警告.
    """
    if _has_control_characters(local):
        errors.append(
            Issue(
                location,
                "本地链接目标包含 NUL 或控制字符: {}".format(
                    local.encode("unicode_escape").decode("ascii")
                ),
            )
        )
        return None
    if _is_windows_absolute_path(local):
        warnings.append(
            Issue(location, "Windows 绝对路径不可移植: {}".format(local))
        )
        return None
    if local.startswith("/"):
        try:
            absolute_path = Path(local).resolve()
        except (OSError, ValueError):
            absolute_path = None
        try:
            absolute_exists = (
                absolute_path is not None and absolute_path.exists()
            )
        except (OSError, ValueError):
            absolute_exists = False
        if not absolute_exists:
            errors.append(
                Issue(location, "本地链接目标不存在: {}".format(local))
            )
            return None
        warnings.append(
            Issue(location, "绝对路径链接不可移植: {}".format(local))
        )
        if _is_within(absolute_path, skill_dir.resolve()):
            matched = _match_disk_case(skill_dir, absolute_path)
            if matched is None:
                return absolute_path
            actual_path, case_mismatch = matched
            if case_mismatch:
                warnings.append(
                    Issue(
                        location,
                        "链接路径大小写与磁盘不一致, 不可移植: {}".format(local),
                    )
                )
            return actual_path
        return None
    target_path, file_relative_only = _resolve_local_link(skill_dir, base_dir, local)
    case_mismatch = False
    if target_path is None:
        target_path, file_relative_only, case_mismatch = (
            _resolve_case_insensitive_link(skill_dir, base_dir, local)
        )
    else:
        matched = _match_disk_case(skill_dir, target_path)
        if matched is not None:
            target_path, case_mismatch = matched
    if target_path is None:
        errors.append(
            Issue(location, "本地链接目标不存在: {}".format(local))
        )
        return None
    if file_relative_only:
        warnings.append(
            Issue(
                location,
                "链接仅按所在文件目录可解析, 建议改为相对 skill 根目录: {}".format(
                    local
                ),
            )
        )
    if not _is_within(target_path, skill_dir.resolve()):
        warnings.append(
            Issue(location, "链接目标在 skill 目录外, 不可移植: {}".format(local))
        )
        return None
    if case_mismatch:
        warnings.append(
            Issue(
                location,
                "链接路径大小写与磁盘不一致, 不可移植: {}".format(local),
            )
        )
    return target_path


def _check_links(skill_dir, body, body_start, errors, warnings):
    """检查本地链接, 返回仅由 SKILL.md 直接链接的文件集合.

    参考文件里的链接目标只用于链接存在性和互引检查, 不计入返回值, 因此不能借此
    豁免 "未被 SKILL.md 直接引用" 的警告.
    """
    referenced = set()
    for line, identifier in scan_missing_reference_links(body):
        errors.append(
            Issue(
                "SKILL.md:{}".format(body_start + line - 1),
                "引用式链接定义不存在: {}".format(identifier),
            )
        )
    skill_links = scan_links(body)
    for line, target in skill_links:
        local = local_target(target)
        if local is None:
            continue
        location = "SKILL.md:{}".format(body_start + line - 1)
        target_path = _validate_local_link(
            skill_dir, skill_dir, local, location, errors, warnings
        )
        if target_path is None:
            continue
        referenced.add(target_path.relative_to(skill_dir.resolve()).as_posix())

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for reference in sorted(references_dir.rglob("*.md")):
            if not reference.is_file():
                continue
            if _is_ignored_path(reference.relative_to(skill_dir)):
                continue
            relative = reference.relative_to(skill_dir).as_posix()
            try:
                text = reference.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(Issue(relative, "无法读取: {}".format(exc)))
                continue
            for line, identifier in scan_missing_reference_links(text):
                errors.append(
                    Issue(
                        "{}:{}".format(relative, line),
                        "引用式链接定义不存在: {}".format(identifier),
                    )
                )
            for line, target in scan_links(text):
                local = local_target(target)
                if local is None:
                    continue
                location = "{}:{}".format(relative, line)
                target_path = _validate_local_link(
                    skill_dir, reference.parent, local, location, errors, warnings
                )
                if target_path is None:
                    continue
                target_relative = target_path.relative_to(
                    skill_dir.resolve()
                ).as_posix()
                if target_relative.startswith("references/") and (
                    target_relative != relative
                ):
                    warnings.append(
                        Issue(
                            location,
                            "参考文件互相引用, 只应从 SKILL.md 直接引用一层",
                        )
                    )

    return referenced


def validate_skill(skill_directory):
    """返回 (错误列表, 警告列表, 解析器名称)."""
    errors = []
    warnings = []
    skill_dir = Path(skill_directory)

    if not skill_dir.exists():
        errors.append(Issue(str(skill_dir), "路径不存在"))
        return errors, warnings, None
    if not skill_dir.is_dir():
        errors.append(Issue(str(skill_dir), "路径不是目录"))
        return errors, warnings, None

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append(Issue("SKILL.md", "缺少 SKILL.md"))
        return errors, warnings, None

    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(Issue("SKILL.md", "不是有效的 UTF-8 文本: {}".format(exc)))
        return errors, warnings, None
    except OSError as exc:
        errors.append(Issue("SKILL.md", "无法读取: {}".format(exc)))
        return errors, warnings, None

    try:
        frontmatter_lines, body, body_start = split_frontmatter(text)
    except FrontmatterError as exc:
        errors.append(Issue("SKILL.md:{}".format(exc.line or 1), str(exc)))
        return errors, warnings, None

    try:
        data, parser = parse_frontmatter("\n".join(frontmatter_lines), 2)
    except FrontmatterError as exc:
        errors.append(Issue("SKILL.md:{}".format(exc.line or 2), str(exc)))
        return errors, warnings, None

    key_lines = _top_level_key_lines(frontmatter_lines, 2)
    _validate_fields(data, key_lines, skill_dir.resolve().name, errors, warnings)

    if not _has_body_content(body):
        errors.append(Issue("SKILL.md", "正文不能为空"))
    elif _body_line_count(body) > MAX_BODY_LINES:
        warnings.append(
            Issue(
                "SKILL.md",
                "正文超过 {} 行, 建议把细节移入 references/ 或 scripts/".format(
                    MAX_BODY_LINES
                ),
            )
        )

    referenced = _check_links(skill_dir, body, body_start, errors, warnings)
    license_file = _license_file(skill_dir, data)

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir).as_posix()
        parts = relative.split("/")
        # 顶层普通文件即使名为 scripts/references 也不属于这两个目录,
        # 只有目录内的文件才检查引用.
        if len(parts) < 2 or parts[0] not in ("scripts", "references"):
            continue
        if not (skill_dir / parts[0]).is_dir():
            continue
        if _is_ignored_path(path.relative_to(skill_dir)):
            continue
        if relative.endswith(".pyc"):
            continue
        if license_file is not None and _is_same_file(path, license_file):
            continue
        if relative in referenced or _mentions_path(body, relative):
            continue
        warnings.append(Issue(relative, "未被 SKILL.md 直接引用的文件"))

    errors.sort(key=_issue_key)
    warnings.sort(key=_issue_key)
    return errors, warnings, parser


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="校验 Agent Skills 目录的 frontmatter, 字段和本地链接."
    )
    parser.add_argument("skill_dir", type=Path, help="skill 目录路径")
    parser.add_argument(
        "--strict", action="store_true", help="把警告视为错误并以非零状态退出"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="输出 frontmatter 解析器名称"
    )
    args = parser.parse_args(argv)

    errors, warnings, parser_name = validate_skill(args.skill_dir)
    if args.verbose and parser_name:
        print("frontmatter 解析器: {}".format(parser_name))
    for issue in errors:
        print("错误: {}".format(issue.render()))
    for issue in warnings:
        print("警告: {}".format(issue.render()))

    if errors:
        print("校验失败: {} 个错误, {} 个警告.".format(len(errors), len(warnings)))
        return 1
    if warnings and args.strict:
        print("严格模式下警告视为错误: {} 个警告.".format(len(warnings)))
        return 1
    if warnings:
        print("校验通过, 有 {} 个警告.".format(len(warnings)))
        return 0
    print("校验通过.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
