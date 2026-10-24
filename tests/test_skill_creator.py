"""验证 skill-creator 的解析, 校验和脚手架行为."""

import importlib.util
import math
import os
from datetime import date, datetime, timedelta
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills/skill-creator/scripts/validate_skill.py"
INIT_PATH = ROOT / "skills/skill-creator/scripts/init_skill.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module(VALIDATOR_PATH, "skill_validator")
initializer = load_module(INIT_PATH, "skill_initializer")
HAS_PYYAML = validator.parse_with_pyyaml("name: demo-skill", 2) is not None


def run_script(path, *args, python_options=()):
    command = [sys.executable] + list(python_options) + [str(path)] + list(args)
    return subprocess.run(command, capture_output=True, text=True)


def yaml_scalar(value):
    if value == "":
        return '""'
    if (
        any(char in value for char in ':#"\'')
        or value != value.strip()
        or value[:1] in "!&*|>%@`{},[]"
    ):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def create_skill(
    base,
    name="demo-skill",
    directory=None,
    description="做演示. 在用户要求演示时使用.",
    body="## 流程\n\n1. 执行.\n",
    extra_frontmatter="",
    files=None,
):
    directory = directory or name
    root = Path(base) / directory
    root.mkdir(parents=True, exist_ok=True)
    text = "---\nname: {}\ndescription: {}\n{}---\n\n{}\n".format(
        yaml_scalar(name), yaml_scalar(description), extra_frontmatter, body
    )
    (root / "SKILL.md").write_text(text, encoding="utf-8")
    for relative, content in (files or {}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def create_skill_with_frontmatter(
    base,
    frontmatter,
    directory="demo-skill",
    body="## 流程\n\n1. 执行.\n",
):
    """用原样 YAML 片段创建 skill, 用于构造缺字段或类型错误的 frontmatter."""
    root = Path(base) / directory
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text(
        "---\n{}---\n\n{}\n".format(frontmatter, body), encoding="utf-8"
    )
    return root


class FrontmatterParserTests(unittest.TestCase):
    def test_pyyaml_and_builtin_agree_on_common_features(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        text = (
            "\ufeffname: demo-skill\r\n"
            "description: >-\r\n"
            "  做演示.\r\n"
            "  在用户要求演示时使用.\r\n"
            "license: MIT\r\n"
            "metadata:\r\n"
            "  author: example\r\n"
            "  version: '1.0'\r\n"
            "# 注释\r\n"
        )
        self.assertEqual(
            validator.parse_with_pyyaml(text, 2),
            validator.parse_with_builtin(text, 2),
        )

    def test_builtin_parses_crlf_bom_block_scalar_and_nested_mapping(self):
        text = (
            "\ufeffname: demo-skill\r\n"
            "description: >-\r\n"
            "  做演示.\r\n"
            "  在用户要求演示时使用.\r\n"
            "metadata:\r\n"
            "  author: example\r\n"
            "  version: '1.0'\r\n"
        )
        self.assertEqual(
            validator.parse_with_builtin(text, 2),
            {
                "name": "demo-skill",
                "description": "做演示. 在用户要求演示时使用.",
                "metadata": {"author": "example", "version": "1.0"},
            },
        )

    def test_block_scalar_chomping(self):
        cases = {
            "|": {"description": "a\nb\n"},
            "|-": {"description": "a\nb"},
            "|+": {"description": "a\nb\n"},
            ">": {"description": "a b\n"},
            ">-": {"description": "a b"},
            ">+": {"description": "a b\n"},
        }
        for header, expected in cases.items():
            with self.subTest(header=header):
                text = "description: {}\n  a\n  b\n".format(header)
                self.assertEqual(validator.parse_with_builtin(text, 2), expected)

    def test_block_scalar_trailing_blank_lines(self):
        self.assertEqual(
            validator.parse_with_builtin("description: |+\n  a\n\n", 2),
            {"description": "a\n\n"},
        )
        self.assertEqual(
            validator.parse_with_builtin("description: |\n  a\n\n", 2),
            {"description": "a\n"},
        )
        self.assertEqual(
            validator.parse_with_builtin("description: |\n  a", 2),
            {"description": "a"},
        )

    def assert_builtin_matches_pyyaml(self, text, expected):
        """同时断言内置解析器与 PyYAML 的结果 (PyYAML 可用时)."""
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_folded_block_scalar_blank_lines(self):
        cases = {
            "description: >\n  a\n\n  b\n": "a\nb\n",
            "description: >-\n  a\n\n  b\n": "a\nb",
            "description: >+\n  a\n\n  b\n": "a\nb\n",
            "description: >\n  a\n\n\n  b\n": "a\n\nb\n",
            "description: >\n  a\n  \n  b\n": "a\nb\n",
            "description: >\n\n  a\n": "\na\n",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assert_builtin_matches_pyyaml(text, {"description": expected})

    def test_folded_block_scalar_blank_line_before_more_indented_line(self):
        cases = {
            "description: >\n  a\n\n    b\n": "a\n\n  b\n",
            "description: >-\n  a\n\n    b\n": "a\n\n  b",
            "description: >\n  a\n\n\n    b\n": "a\n\n\n  b\n",
            "description: >\n  a\n    b\n  c\n": "a\n  b\nc\n",
            "description: >\n  a\n    b\n\n  c\n": "a\n  b\n\nc\n",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assert_builtin_matches_pyyaml(text, {"description": expected})

    def test_folded_block_scalar_keep_chomping_with_more_indented_tail(self):
        cases = {
            "description: >+\n  a\n    b\n": "a\n  b\n",
            "description: >+\n  a\n    b\n\n\n": "a\n  b\n\n\n",
            "description: >+\n  a\n\n\n": "a\n\n\n",
            "description: >+\n  a\n    \n  b\n\n": "a\n  \nb\n\n",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assert_builtin_matches_pyyaml(text, {"description": expected})

    def test_block_scalar_without_trailing_newline(self):
        cases = {
            "description: >\n  a\n  b": "a b",
            "description: >-\n  a\n  b": "a b",
            "description: >\n  a\n    b": "a\n  b",
            "description: |\n  a\n  b": "a\nb",
            "description: >+\n  a": "a",
            "description: |+\n  a": "a",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assert_builtin_matches_pyyaml(text, {"description": expected})

    def test_literal_block_scalar_whitespace_only_lines_keep_excess_indent(self):
        cases = {
            "description: |\n  a\n    \n": "a\n  \n",
            "description: |+\n  a\n    \n": "a\n  \n",
            "description: |-\n  a\n    \n": "a\n  ",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assert_builtin_matches_pyyaml(text, {"description": expected})

    def test_block_scalar_leading_blank_line_deeper_than_content_is_reported(self):
        # YAML 会把更深的前置空行缩进当成内容缩进, 后续内容行随之失效;
        # 内置解析器不猜测这种写法, 直接明确报错.
        for text in (
            "description: >\n    \n  a\n",
            "description: |\n     \n  a\n",
        ):
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_builtin(text, 2)
                self.assertEqual(
                    str(caught.exception),
                    "无法解析, 请人工确认: 块标量首个空行缩进深于内容",
                )
                if HAS_PYYAML:
                    with self.assertRaises(validator.FrontmatterError):
                        validator.parse_with_pyyaml(text, 2)

    def test_block_scalar_ends_at_less_indented_comment_line(self):
        # 缩进不足的注释行按 YAML 语义结束块标量, 随后作为注释被跳过.
        frontmatter = (
            "name: demo-skill\n"
            "description: |\n"
            "  a\n"
            " # 注释\n"
            "license: MIT\n"
        )
        expected = {"name": "demo-skill", "description": "a\n", "license": "MIT"}
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(frontmatter, 2), expected)
        self.assertEqual(validator.parse_with_builtin(frontmatter, 2), expected)
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill_with_frontmatter(directory, frontmatter)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])

    def test_indented_markers_in_block_scalar_do_not_end_frontmatter(self):
        text = (
            "---\n"
            "name: demo-skill\n"
            "description: |\n"
            "  做演示.\n"
            "  ---\n"
            "  ...\n"
            "  在用户要求演示时使用.\n"
            "---\n"
            "\n## 流程\n"
        )
        frontmatter_lines, body, body_start = validator.split_frontmatter(text)
        self.assertEqual(
            frontmatter_lines,
            [
                "name: demo-skill",
                "description: |",
                "  做演示.",
                "  ---",
                "  ...",
                "  在用户要求演示时使用.",
            ],
        )
        self.assertEqual(body, "\n## 流程\n")
        self.assertEqual(body_start, 9)

    def test_frontmatter_markers_must_start_at_column_zero(self):
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.split_frontmatter("  ---\nname: demo-skill\n---\n正文\n")
        self.assertEqual(caught.exception.line, 1)
        self.assertEqual(
            str(caught.exception),
            "SKILL.md 必须以 YAML frontmatter 开头, 第一行应为 ---",
        )
        frontmatter_lines, body, _ = validator.split_frontmatter(
            "---  \nname: demo-skill\n---\t\n正文\n"
        )
        self.assertEqual(frontmatter_lines, ["name: demo-skill"])
        self.assertEqual(body, "正文\n")
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.split_frontmatter("---  \nname: demo-skill\n...\t\n正文\n")
        self.assertEqual(caught.exception.line, 5)
        self.assertEqual(str(caught.exception), "frontmatter 缺少结束标记 ---")

    def test_quoted_scalars_and_comments(self):
        text = (
            "name: demo-skill\n"
            "description: 'it''s a: value # not comment'  # 注释\n"
            "license: \"line\\nbreak \\u4f60\"\n"
        )
        self.assertEqual(
            validator.parse_with_builtin(text, 2),
            {
                "name": "demo-skill",
                "description": "it's a: value # not comment",
                "license": "line\nbreak 你",
            },
        )

    def test_plain_scalar_types_match_pyyaml(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        values = (
            "0123", "08", "0o123", "0x1f", "0b101", "1_000", "1e3",
            ".5", "5.", "2024-1-1", "2024-01-01", "2024-01-01T12:00:00Z",
            "2024-01-01T00:00:00z", "2024-01-01T00:00:00+08",
            "2024-01-01T00:00:00+0800", "2024-01-01T00:00:00+08:00",
            "2024-01-01T00:00:00.5", "2024-1-1 1:02:03",
            "2024-01-01 00:00:00 +08:00", "12:30",
        )
        for value in values:
            with self.subTest(value=value):
                text = "x: {}\n".format(value)
                self.assertEqual(
                    validator.parse_with_pyyaml(text, 2),
                    validator.parse_with_builtin(text, 2),
                )

    def test_plain_timestamp_offset_forms_use_builtin_parser(self):
        # 内置解析器按 PyYAML 1.1 的 timestamp resolver/构造器处理: 小写 z 与
        # 不带冒号的 +HHMM 偏移不匹配, 保留为字符串; +HH 与 +HH:MM 解析为带
        # 时区的 datetime; 单数字月/日/时/分同样可解析. 这些断言不依赖 PyYAML.
        def resolve(value):
            return validator.parse_with_builtin("description: {}\n".format(value), 2)[
                "description"
            ]

        self.assertEqual(
            resolve("2024-01-01T00:00:00z"), "2024-01-01T00:00:00z"
        )
        self.assertEqual(
            resolve("2024-01-01T00:00:00+0800"), "2024-01-01T00:00:00+0800"
        )
        self.assertEqual(resolve("2024-1-1"), "2024-1-1")
        for value in (
            "2024-01-01T00:00:00+08",
            "2024-01-01T00:00:00+08:00",
        ):
            with self.subTest(value=value):
                timestamp = resolve(value)
                self.assertIs(type(timestamp), datetime)
                self.assertEqual(timestamp.utcoffset(), timedelta(hours=8))
        self.assertEqual(
            resolve("2024-01-01T00:00:00.5"),
            datetime(2024, 1, 1, 0, 0, 0, 500000),
        )
        self.assertEqual(
            resolve("2024-1-1 1:02:03"), datetime(2024, 1, 1, 1, 2, 3)
        )

    def assert_scalar_parity(self, token, expected):
        """断言标量 token 在内置解析器中的类型与值, 并在 PyYAML 可用时比对."""
        text = "x: {}\n".format(token)
        parsers = [("内置解析器", validator.parse_with_builtin)]
        if HAS_PYYAML:
            parsers.append(("PyYAML", validator.parse_with_pyyaml))
        for label, parser in parsers:
            with self.subTest(token=token, parser=label):
                actual = parser(text, 2)["x"]
                self.assertIs(type(actual), type(expected), repr(actual))
                if isinstance(expected, float) and math.isnan(expected):
                    self.assertTrue(math.isnan(actual), repr(actual))
                else:
                    self.assertEqual(actual, expected)

    def test_numeric_tokens_match_pyyaml_resolver(self):
        # PyYAML 1.1 的 resolver 与构造器行为: 下划线可出现在数字之间,
        # 指数必须带符号, 六十进制首段不能带前导零, 大小写十六/二进制前缀
        # 只有小写形式才被构造, .nan 不能带符号, 前导小数点的浮点不带符号
        # (因此 "-.5" 是字符串).
        cases = (
            ("1_000", 1000),
            ("1_", 1),
            ("1__0", 10),
            ("0_", 0),
            ("00", 0),
            ("_1", "_1"),
            ("0x1f", 31),
            ("0x_1f", 31),
            ("-0x1f", -31),
            ("0X1F", "0X1F"),
            ("0b101", 5),
            ("-0b101", -5),
            ("0B101", "0B101"),
            ("0123", 83),
            ("-0123", -83),
            ("019", "019"),
            ("0o123", "0o123"),
            ("1:02", 62),
            ("-1:02", -62),
            ("1:2:3", 3723),
            ("01:02", "01:02"),
            ("1:62", "1:62"),
            ("1:02.5", 62.5),
            ("1:2:3.5", 3723.5),
            (".5", 0.5),
            ("-.5", "-.5"),
            ("+.5", "+.5"),
            ("-0.5", -0.5),
            ("0.", 0.0),
            ("1.5e+3", 1500.0),
            ("1.5E-3", 0.0015),
            (".5e+3", 500.0),
            ("1.5e3", "1.5e3"),
            ("1e3", "1e3"),
            (".5e3", ".5e3"),
            ("1.5e", "1.5e"),
            ("1.5_e3", "1.5_e3"),
            (".inf", float("inf")),
            ("+.inf", float("inf")),
            ("-.inf", float("-inf")),
            (".INF", float("inf")),
            (".nan", float("nan")),
            (".NaN", float("nan")),
            ("-.nan", "-.nan"),
        )
        for token, expected in cases:
            self.assert_scalar_parity(token, expected)

    def test_numeric_conversion_errors_match_pyyaml(self):
        # 这些 token 能通过 resolver, 但 PyYAML 的构造器会抛 ValueError.
        for token in ("0x_", "0x__", "-0x_", "0b_", "0b___"):
            text = "x: {}\n".format(token)
            with self.subTest(token=token):
                with self.assertRaises(validator.FrontmatterError):
                    validator.parse_with_builtin(text, 2)
                if HAS_PYYAML:
                    with self.assertRaises(validator.FrontmatterError):
                        validator.parse_with_pyyaml(text, 2)

    def test_numeric_frontmatter_exit_codes_match_across_parsers(self):
        cases = {
            "typed_values": (
                "metadata:\n"
                "  version: 1_000\n"
                "  ratio: 01:02\n"
                "  scale: 1.5e+3\n"
                "  legacy: 0x1f\n"
                "  note: 1.5e3\n"
            ),
            "conversion_error": "metadata:\n  hex: 0x_\n",
        }
        for label, extra_frontmatter in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = create_skill(directory, extra_frontmatter=extra_frontmatter)
                pyyaml_run = run_script(VALIDATOR_PATH, str(root), "--strict")
                builtin_run = run_script(
                    VALIDATOR_PATH, str(root), "--strict", python_options=("-S",)
                )
                self.assertEqual(
                    pyyaml_run.returncode,
                    builtin_run.returncode,
                    pyyaml_run.stdout + pyyaml_run.stderr,
                )
                if label == "typed_values":
                    self.assertEqual(
                        pyyaml_run.stdout,
                        builtin_run.stdout,
                        "两条解析路径应对数值类型给出相同结论",
                    )

    def test_boolean_and_null_tokens_match_pyyaml_resolver(self):
        # PyYAML 1.1 只把这些 token 的精确大小写形式解析为布尔/空值,
        # 其余大小写混写 (oN, YeS, NuLl 等) 一律保持字符串.
        cases = (
            ("yes", True),
            ("Yes", True),
            ("YES", True),
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("on", True),
            ("On", True),
            ("ON", True),
            ("no", False),
            ("No", False),
            ("NO", False),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("off", False),
            ("Off", False),
            ("OFF", False),
            ("~", None),
            ("null", None),
            ("Null", None),
            ("NULL", None),
            ("", None),
            ("oN", "oN"),
            ("YeS", "YeS"),
            ("tRuE", "tRuE"),
            ("yES", "yES"),
            ("nO", "nO"),
            ("fALSE", "fALSE"),
            ("oFF", "oFF"),
            ("NuLl", "NuLl"),
            ("nULL", "nULL"),
            ("NuLL", "NuLL"),
            ("Nulll", "Nulll"),
            ("~x", "~x"),
        )
        for token, expected in cases:
            self.assert_scalar_parity(token, expected)

    def test_boolean_and_null_frontmatter_exit_codes_match_across_parsers(self):
        cases = {
            "mixed_tokens": (
                "metadata:\n"
                "  exact_true: Yes\n"
                "  exact_false: Off\n"
                "  exact_null: ~\n"
                "  upper_null: NULL\n"
                "  weird_true: oN\n"
                "  weird_false: fALSE\n"
                "  weird_null: NuLl\n"
            ),
            "string_values": (
                "metadata:\n"
                "  weird_true: YeS\n"
                "  weird_null: nULL\n"
            ),
        }
        for label, extra_frontmatter in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = create_skill(directory, extra_frontmatter=extra_frontmatter)
                pyyaml_run = run_script(VALIDATOR_PATH, str(root), "--strict")
                builtin_run = run_script(
                    VALIDATOR_PATH, str(root), "--strict", python_options=("-S",)
                )
                self.assertEqual(
                    pyyaml_run.returncode,
                    builtin_run.returncode,
                    pyyaml_run.stdout + pyyaml_run.stderr,
                )

    def test_plain_scalar_with_mapping_colon_is_rejected(self):
        with self.assertRaises(validator.FrontmatterError):
            validator.parse_with_builtin("description: a: b\n", 2)

    def test_nested_mapping(self):
        text = "metadata:\n  author: example\n  version: \"1.0\"\n"
        self.assertEqual(
            validator.parse_with_builtin(text, 2),
            {"metadata": {"author": "example", "version": "1.0"}},
        )

    def test_unicode_mapping_key(self):
        data = validator.parse_with_builtin("metadata:\n  作者: 易靖远\n", 2)
        self.assertEqual(data, {"metadata": {"作者": "易靖远"}})

    def test_unicode_metadata_key_matches_pyyaml(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        text = "metadata:\n  作者: 易靖远\n"
        self.assertEqual(
            validator.parse_with_builtin(text, 2),
            validator.parse_with_pyyaml(text, 2),
        )

    def test_mapping_keys_use_yaml_types(self):
        data = validator.parse_with_builtin("metadata:\n  true: value\n", 2)
        key = next(iter(data["metadata"]))
        self.assertNotIsInstance(key, str)
        self.assertIs(key, True)
        self.assertEqual(
            validator.parse_with_builtin(
                "name: demo-skill\nallowed-tools: Read\n", 2
            ),
            {"name": "demo-skill", "allowed-tools": "Read"},
        )

    def test_mapping_key_types_match_pyyaml(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        expected_types = {"true": bool, "1": int, "null": type(None), "1.5": float}
        for raw, expected_type in expected_types.items():
            with self.subTest(key=raw):
                text = "metadata:\n  {}: value\n".format(raw)
                builtin = validator.parse_with_builtin(text, 2)
                pyyaml = validator.parse_with_pyyaml(text, 2)
                self.assertEqual(builtin, pyyaml)
                builtin_key = next(iter(builtin["metadata"]))
                pyyaml_key = next(iter(pyyaml["metadata"]))
                self.assertIs(type(builtin_key), type(pyyaml_key))
                self.assertIs(type(builtin_key), expected_type)
                self.assertNotIsInstance(builtin_key, str)

    def test_unsupported_structures_report_errors(self):
        cases = (
            "description:\n  nested:\n    deep: value\n",
            "description: [a, b]\n",
            "description: &anchor value\n",
            "description: \"a\n  b\"\n",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError):
                    validator.parse_with_builtin(text, 2)

    def test_builtin_rejects_multiline_plain_scalar(self):
        text = "description: 第一行\n  第二行\n"
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.parse_with_builtin(text, 2)
        message = str(caught.exception)
        self.assertTrue(
            "无法解析" in message or "人工确认" in message, message
        )

    def test_builtin_rejects_inline_collection(self):
        text = "metadata: {}\n"
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.parse_with_builtin(text, 2)
        message = str(caught.exception)
        self.assertTrue(
            "无法解析" in message or "人工确认" in message, message
        )

    def test_quoted_keys_match_pyyaml(self):
        text = (
            "\"name\": demo-skill\n"
            "'description': 做演示.\n"
            "\"metadata\":\n"
            "  \"author\": example\n"
            "  'version': '1.0'\n"
        )
        expected = {
            "name": "demo-skill",
            "description": "做演示.",
            "metadata": {"author": "example", "version": "1.0"},
        }
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_quoted_key_escapes_match_pyyaml(self):
        text = "\"desc\\u0072iption\": \"a\\tb\"\n"
        expected = {"description": "a\tb"}
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_unicode_escape_is_supported_in_quoted_scalar(self):
        text = 'description: "a\\u0041b"\n'
        expected = {"description": "aAb"}
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_unsupported_escape_reports_actionable_hint(self):
        text = 'description: "a\\x41b"\n'
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.parse_with_builtin(text, 2)
        message = str(caught.exception)
        self.assertIn("不支持的转义序列", message)
        self.assertIn("\\x", message)
        self.assertIn("\\uXXXX", message)
        self.assertTrue("PyYAML" in message or "人工确认" in message, message)
        if HAS_PYYAML:
            self.assertEqual(
                validator.parse_with_pyyaml(text, 2), {"description": "aAb"}
            )

    def test_pyyaml_parses_hex_escape_and_validation_passes(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        with tempfile.TemporaryDirectory() as base:
            root = Path(base) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n"
                "name: demo-skill\n"
                "description: \"a\\x41b. 在用户要求演示时使用.\"\n"
                "---\n\n"
                "## 流程\n\n1. 执行.\n",
                encoding="utf-8",
            )
            errors, _, parser = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(parser, "PyYAML")

    def test_spaces_before_colon_match_pyyaml(self):
        text = (
            "name   : demo-skill\n"
            "description : 做演示.\n"
            "metadata :\n"
            "  author : example\n"
            "\"license\" : MIT\n"
        )
        expected = {
            "name": "demo-skill",
            "description": "做演示.",
            "metadata": {"author": "example"},
            "license": "MIT",
        }
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_marker_prefixed_plain_scalars_are_rejected(self):
        for text in ("description: - a\n", "description: ? a\n", "description: -\n"):
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_builtin(text, 2)
                self.assertIn(
                    "不支持序列或映射键形式的纯量", str(caught.exception)
                )
                if HAS_PYYAML:
                    with self.assertRaises(validator.FrontmatterError):
                        validator.parse_with_pyyaml(text, 2)

    def test_flow_indicator_prefixed_plain_scalars_are_rejected(self):
        for token in ("]foo", "}foo", ",foo"):
            text = "description: {}\n".format(token)
            with self.subTest(token=token):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_builtin(text, 2)
                message = str(caught.exception)
                self.assertIn("不支持以流指示符开头的纯量", message)
                self.assertEqual(caught.exception.line, 2)
                if HAS_PYYAML:
                    with self.assertRaises(validator.FrontmatterError):
                        validator.parse_with_pyyaml(text, 2)

    def test_indicator_prefixed_quoted_and_block_scalars_are_accepted(self):
        cases = (
            ("description: ']foo'\n", "]foo"),
            ('description: "}foo"\n', "}foo"),
            ("description: ',foo'\n", ",foo"),
            ("description: '=foo'\n", "=foo"),
            ("description: |\n  ]foo\n", "]foo\n"),
            ("description: |\n  =foo\n", "=foo\n"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    validator.parse_with_builtin(text, 2), {"description": expected}
                )
                if HAS_PYYAML:
                    self.assertEqual(
                        validator.parse_with_pyyaml(text, 2),
                        {"description": expected},
                    )

    def test_equals_prefixed_plain_scalar_is_accepted(self):
        for text, expected in (
            ("description: =foo\n", "=foo"),
            ("description: =foo bar\n", "=foo bar"),
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    validator.parse_with_builtin(text, 2), {"description": expected}
                )
                if HAS_PYYAML:
                    self.assertEqual(
                        validator.parse_with_pyyaml(text, 2),
                        {"description": expected},
                    )

    def test_flow_indicator_frontmatter_exit_codes_match_across_parsers(self):
        for token in ("]", "}", ","):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "flow-indicator"
                root.mkdir()
                (root / "SKILL.md").write_text(
                    "---\n"
                    "name: flow-indicator\n"
                    "description: {}foo\n"
                    "---\n"
                    "\n"
                    "## 流程\n"
                    "\n"
                    "1. 执行.\n".format(token),
                    encoding="utf-8",
                )
                pyyaml_run = run_script(VALIDATOR_PATH, str(root), "--strict")
                builtin_run = run_script(
                    VALIDATOR_PATH, str(root), "--strict", python_options=("-S",)
                )
                self.assertNotEqual(
                    builtin_run.returncode, 0, builtin_run.stdout + builtin_run.stderr
                )
                self.assertEqual(
                    pyyaml_run.returncode,
                    builtin_run.returncode,
                    pyyaml_run.stdout + pyyaml_run.stderr,
                )
                self.assertIn(
                    "不支持以流指示符开头的纯量", builtin_run.stdout
                )

    def test_equals_frontmatter_exit_codes_match_across_parsers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "equals-scalar"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n"
                "name: equals-scalar\n"
                "description: =foo\n"
                "---\n"
                "\n"
                "## 流程\n"
                "\n"
                "1. 执行.\n",
                encoding="utf-8",
            )
            pyyaml_run = run_script(VALIDATOR_PATH, str(root), "--strict")
            builtin_run = run_script(
                VALIDATOR_PATH, str(root), "--strict", python_options=("-S",)
            )
            self.assertEqual(
                pyyaml_run.returncode, 0, pyyaml_run.stdout + pyyaml_run.stderr
            )
            self.assertEqual(
                builtin_run.returncode, 0, builtin_run.stdout + builtin_run.stderr
            )

    def test_tab_separator_is_rejected(self):
        texts = (
            "description:\thello\n",
            "name:\tdemo\n",
            "name\t: demo\n",
            "name: demo\tvalue\n",
            "name: demo\t# 注释\n",
            "description: \"a\"\t\n",
            "description: |\t\n  a\n",
        )
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_builtin(text, 2)
                self.assertIn("不支持制表符分隔", str(caught.exception))
                if HAS_PYYAML:
                    with self.assertRaises(validator.FrontmatterError):
                        validator.parse_with_pyyaml(text, 2)

    def test_tab_inside_quoted_scalars_is_accepted(self):
        text = "description: \"a\tb\"\nmetadata:\n  author: 'c\td'\n"
        expected = {"description": "a\tb", "metadata": {"author": "c\td"}}
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)

    def test_builtin_and_pyyaml_agree_on_parity_cases(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        cases = (
            "\"name\": demo-skill\n",
            "'name': demo-skill\n",
            "name : demo-skill\n",
            "description: - a\n",
            "description: ? a\n",
            "description:\thello\n",
        )
        for text in cases:
            with self.subTest(text=text):
                outcomes = []
                for parser in (
                    validator.parse_with_pyyaml,
                    validator.parse_with_builtin,
                ):
                    try:
                        outcomes.append(("ok", parser(text, 2)))
                    except validator.FrontmatterError:
                        outcomes.append(("error", None))
                self.assertEqual(outcomes[0], outcomes[1])

    def test_quoted_keys_report_errors_at_their_own_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "quoted-keys"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n"
                '"name": Bad_Name\n'
                "'description': \"\"\n"
                "\n"
                '"license" : MIT\n'
                '"metadata":\n'
                '  "author": example\n'
                '"compatibility": 需要 Python 3.9+.\n'
                '"allowed-tools" : Read\n'
                "---\n"
                "\n"
                "## 流程\n\n1. 执行.\n",
                encoding="utf-8",
            )

            errors, _, _ = validator.validate_skill(root)
            name_locations = {
                issue.location
                for issue in errors
                if issue.message.startswith("name")
            }
            description_locations = {
                issue.location
                for issue in errors
                if issue.message.startswith("description")
            }
            self.assertEqual(name_locations, {"SKILL.md:2"})
            self.assertEqual(description_locations, {"SKILL.md:3"})

    def test_error_reports_line_number(self):
        with self.assertRaises(validator.FrontmatterError) as caught:
            validator.parse_with_builtin("name: demo\ndescription: [a]\n", 2)
        self.assertEqual(caught.exception.line, 3)

    def test_invalid_dates_are_rejected_by_builtin_parser(self):
        cases = (
            "description: 2024-13-99\n",
            "description: 2024-02-31T10:00:00Z\n",
            "2024-13-99: value\n",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_builtin(text, 2)
                self.assertIn("请人工确认: 无效日期", str(caught.exception))
                self.assertEqual(caught.exception.line, 2)

    def test_invalid_dates_are_rejected_by_pyyaml(self):
        if not HAS_PYYAML:
            self.skipTest("PyYAML 不可用")
        cases = (
            "description: 2024-13-99\n",
            "description: 2024-02-31T10:00:00Z\n",
            "2024-13-99: value\n",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(validator.FrontmatterError) as caught:
                    validator.parse_with_pyyaml(text, 2)
                self.assertIn("无法解析 frontmatter", str(caught.exception))
                self.assertEqual(caught.exception.line, 2)

    def test_valid_dates_are_still_parsed(self):
        text = "description: 2024-01-31\n"
        expected = {"description": date(2024, 1, 31)}
        self.assertEqual(validator.parse_with_builtin(text, 2), expected)
        if HAS_PYYAML:
            self.assertEqual(validator.parse_with_pyyaml(text, 2), expected)


class ValidatorTests(unittest.TestCase):
    def test_valid_skill_passes_without_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/note.md": "# 说明\n"},
                body="读取 [说明](references/note.md).\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("校验通过", result.stdout)

    def test_name_check_uses_resolved_symlink_target_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            real_root = create_skill(directory, name="real-name")
            link = Path(directory) / "link-name"
            try:
                link.symlink_to(real_root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("当前平台无法创建符号链接")
            errors, _, _ = validator.validate_skill(link)
            self.assertFalse(
                any("name 与父目录名不一致" in issue.message for issue in errors),
                [issue.message for issue in errors],
            )

    def test_invalid_date_is_reported_without_crashing(self):
        for description in ("2024-13-99", "2024-02-31T10:00:00Z"):
            with self.subTest(description=description):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "demo-skill"
                    root.mkdir()
                    (root / "SKILL.md").write_text(
                        "---\nname: demo-skill\ndescription: {}\n---\n\n"
                        "## 流程\n\n1. 执行.\n".format(description),
                        encoding="utf-8",
                    )
                    errors, _, _ = validator.validate_skill(root)
                    self.assertTrue(
                        any("无法解析" in issue.message for issue in errors)
                    )
                    for python_options in ((), ("-S",)):
                        result = run_script(
                            VALIDATOR_PATH, str(root), python_options=python_options
                        )
                        self.assertEqual(
                            result.returncode,
                            1,
                            result.stdout + result.stderr,
                        )
                        self.assertIn("校验失败", result.stdout)
                        self.assertNotIn("Traceback", result.stderr)

    def test_comment_only_body_is_empty(self):
        bodies = (
            "<!-- 只有注释 -->\n",
            "<!-- 跨行\n注释 -->\n",
            "<!-- 未闭合注释\n仍算注释\n",
        )
        for body in bodies:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as directory:
                root = create_skill(directory, body=body)
                errors, _, _ = validator.validate_skill(root)
                self.assertTrue(
                    any(issue.message == "正文不能为空" for issue in errors)
                )
                result = run_script(VALIDATOR_PATH, str(root))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("正文不能为空", result.stdout)

    def test_comment_alongside_text_is_not_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body="<!-- 说明 -->\n\n## 流程\n\n1. 执行.\n")
            errors, _, _ = validator.validate_skill(root)
            self.assertFalse(
                any(issue.message == "正文不能为空" for issue in errors)
            )

    def test_uppercase_name_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, name="Demo-Skill")
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(any("小写" in issue.message for issue in errors))

    def test_unicode_and_boundary_names_pass(self):
        cases = (
            "技能",
            "café",
            "a-b",
            "a" * 64,
            "技" * 64,
        )
        for name in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = create_skill(directory, name=name, directory=name)
                errors, warnings, _ = validator.validate_skill(root)
                self.assertEqual(
                    [issue.message for issue in errors],
                    [],
                    (name, [issue.message for issue in warnings]),
                )
                result = run_script(VALIDATOR_PATH, str(root))
                self.assertEqual(
                    result.returncode, 0, result.stdout + result.stderr
                )

    def test_name_and_directory_are_compared_after_nfkc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, name="café", directory="cafe\u0301"
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual([issue.message for issue in errors], [])

    def test_name_field_is_stripped_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, name=" demo ", directory="demo")
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual([issue.message for issue in errors], [])

    def test_name_field_is_nfkc_normalized_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, name="ｄｅｍｏ", directory="demo")
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual([issue.message for issue in errors], [])

    # 该用例依赖 POSIX 命名语义: Windows 会去除目录名首尾的 ASCII 空格, 无法构造 " demo"/"demo ".
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 会去除目录名首尾空格, 无法构造该用例",
    )
    def test_directory_name_is_not_stripped_before_comparison(self):
        for directory_name in (" demo", "demo "):
            with self.subTest(directory=directory_name):
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(
                        directory, name="demo", directory=directory_name
                    )
                    errors, _, _ = validator.validate_skill(root)
                    self.assertTrue(
                        any(
                            "name 与父目录名不一致" in issue.message
                            for issue in errors
                        ),
                        [issue.message for issue in errors],
                    )
                    result = run_script(VALIDATOR_PATH, str(root))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("name 与父目录名不一致", result.stdout)

    def test_name_must_match_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, name="other-name", directory="demo-skill")
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(
                any("name 与父目录名不一致" in issue.message for issue in errors)
            )
            result = run_script(VALIDATOR_PATH, str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("name 与父目录名不一致", result.stdout)

    def test_dot_path_uses_resolved_directory_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/note.md": "# 说明\n"},
                body="读取 [说明](references/note.md).\n",
            )
            previous = os.getcwd()
            os.chdir(root)
            try:
                errors, warnings, _ = validator.validate_skill(Path("."))
            finally:
                os.chdir(previous)
            self.assertFalse(
                any("name 与父目录名不一致" in issue.message for issue in errors)
            )
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_name_rules(self):
        cases = (
            "demo--skill",
            "-demo",
            "demo-",
            "demo_skill",
            "a" * 65,
            "a!b",
            "🙂",
        )
        for name in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = create_skill(directory, name=name)
                errors, _, _ = validator.validate_skill(root)
                self.assertTrue(any("name " in issue.message for issue in errors))

    def test_description_empty_and_too_long(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = create_skill(directory, name="empty", description="")
            errors, _, _ = validator.validate_skill(empty)
            self.assertTrue(any("description 不能为空" in issue.message for issue in errors))

            too_long = create_skill(
                directory, name="long", description="a" * 1025
            )
            errors, _, _ = validator.validate_skill(too_long)
            self.assertTrue(
                any("description 不能超过 1024" in issue.message for issue in errors)
            )

    def test_optional_fields_are_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter=(
                    "license: MIT\n"
                    "compatibility: 需要 Python 3.9+.\n"
                    "metadata:\n"
                    "  author: example\n"
                    "  version: \"1.0\"\n"
                    "allowed-tools: Bash(git:*) Read\n"
                ),
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

            bad = create_skill(
                directory,
                directory="bad",
                extra_frontmatter=(
                    "compatibility: " + "a" * 501 + "\n"
                    "metadata:\n"
                    "  version: 1.0\n"
                    "allowed-tools: 123\n"
                ),
            )
            errors, _, _ = validator.validate_skill(bad)
            messages = [issue.message for issue in errors]
            self.assertTrue(any("compatibility 长度" in message for message in messages))
            self.assertTrue(any("metadata.version" in message for message in messages))
            self.assertTrue(any("allowed-tools" in message for message in messages))

            bad_license = create_skill(
                directory,
                directory="bad-license",
                extra_frontmatter="license: 123\n",
            )
            errors, _, _ = validator.validate_skill(bad_license)
            self.assertTrue(
                any("license 必须是字符串" in issue.message for issue in errors)
            )

    def test_allowed_tools_must_be_space_separated(self):
        with tempfile.TemporaryDirectory() as directory:
            comma_separated = create_skill(
                directory,
                name="comma-separated",
                directory="comma-separated",
                extra_frontmatter="allowed-tools: Read, Write\n",
            )
            errors, _, _ = validator.validate_skill(comma_separated)
            self.assertTrue(
                any(
                    "allowed-tools 必须是空格分隔的工具名字符串" in issue.message
                    for issue in errors
                ),
                [issue.render() for issue in errors],
            )
            result = run_script(VALIDATOR_PATH, str(comma_separated))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

            tab_separated = create_skill(
                directory,
                name="tab-separated",
                directory="tab-separated",
                extra_frontmatter='allowed-tools: "Read\\tWrite"\n',
            )
            errors, _, _ = validator.validate_skill(tab_separated)
            self.assertTrue(
                any(
                    "allowed-tools 必须是空格分隔的工具名字符串" in issue.message
                    for issue in errors
                ),
                [issue.render() for issue in errors],
            )
            result = run_script(VALIDATOR_PATH, str(tab_separated))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

            spaced = create_skill(
                directory,
                name="spaced",
                directory="spaced",
                extra_frontmatter="allowed-tools: Bash(git:*) Read\n",
            )
            errors, warnings, _ = validator.validate_skill(spaced)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_local_links_must_exist_and_report_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body="正文 [断链](references/missing.md)\n")
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(
                any("本地链接目标不存在" in issue.message for issue in errors)
            )
            locations = [issue.location for issue in errors]
            self.assertTrue(any(re.fullmatch(r"SKILL\.md:\d+", value) for value in locations))
            self.assertIn("SKILL.md:6", locations)

            with tempfile.TemporaryDirectory() as other:
                reference_root = create_skill(
                    other,
                    files={"references/a.md": "[缺失](missing.md)\n"},
                    body="[a](references/a.md)\n",
                )
                errors, _, _ = validator.validate_skill(reference_root)
                self.assertTrue(
                    any(
                        issue.location == "references/a.md:1"
                        and "本地链接目标不存在" in issue.message
                        for issue in errors
                    ),
                    [issue.render() for issue in errors],
                )
                result = run_script(VALIDATOR_PATH, str(reference_root))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_parenthesized_link_target_is_not_truncated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a(1).md": "# 说明\n"},
                body="读取 [报告](references/a(1).md).\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_escaped_bracket_is_not_a_link(self):
        body = "正文 \\[x](references/nope.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_escaped_parentheses_in_target_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a(b).md": "# 说明\n"},
                body="读取 [x](references/a\\(b\\).md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_multiline_link_target_reports_start_line(self):
        body = "[x](\n references/missing.md\n)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:6", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_footnote_definition_is_not_checked_as_link(self):
        body = "## 说明\n\n[^1]: 参见 references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_definition_after_paragraph_without_blank_line_is_not_a_link(self):
        body = "## 说明\n\n正文继续.\n[x]: references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_non_punctuation_backslash_escape_invalidates_link(self):
        body = "正文 [x](references/a\\ b.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_u2028_does_not_shift_reported_line(self):
        body = "第一行\u2028第二行\n\n[断链](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_nested_brackets_in_link_text_are_reported(self):
        body = "[a [b] c](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:6", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_angle_bracket_reference_definition_with_space_resolves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a b.md": "# 说明\n"},
                body="读取 [报告][a].\n\n[a]: <references/a b.md>\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_multiline_reference_definition_target_is_checked(self):
        body = "读取 [报告][a].\n\n[a]:\n  references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_with_angle_target_resolves(self):
        body = "读取 [报告][a].\n\n[a]:\n  <references/a b.md>\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a b.md": "# 说明\n"},
                body=body,
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_multiline_reference_definition_accepts_unindented_target(self):
        body = "读取 [报告][a].\n\n[a]:\nreferences/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_accepts_title(self):
        body = (
            "[双]:\n"
            'references/present.md "标题"\n'
            "[单]:\n"
            "references/present.md '标题'\n"
            "[括]:\n"
            "references/present.md (标题)\n"
            "[尖]:\n"
            '<a b.md> "标题"\n'
            "\n"
            "引用 [双][双], [单][单], [括][括], [尖][尖].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n", "a b.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_multiline_reference_definition_title_with_missing_target(self):
        body = (
            "[双]:\n"
            'references/missing.md "标题"\n'
            "[单]:\n"
            "references/other.md '标题'\n"
            "[括]:\n"
            "references/third.md (标题)\n"
            "[尖]:\n"
            '<a b.md> "标题"\n'
            "\n"
            "引用 [双][双], [单][单], [括][括], [尖][尖].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    ("SKILL.md:6", "本地链接目标不存在: references/missing.md"),
                    ("SKILL.md:8", "本地链接目标不存在: references/other.md"),
                    ("SKILL.md:10", "本地链接目标不存在: references/third.md"),
                    ("SKILL.md:12", "本地链接目标不存在: a b.md"),
                ],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_accepts_escaped_title(self):
        body = (
            "[双]:\n"
            'references/present.md "标\\"题"\n'
            "[单]:\n"
            "references/present.md '标\\'题'\n"
            "[括]:\n"
            "references/present.md (标\\)题)\n"
            "[原]:\n"
            'references/present.md "标题"\n'
            "\n"
            "引用 [双][双], [单][单], [括][括], [原][原].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_multiline_reference_definition_escaped_title_with_missing_target(self):
        body = (
            "[双]:\n"
            'references/missing.md "标\\"题"\n'
            "\n"
            "引用 [x][双].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:6", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_rejects_unquoted_title(self):
        body = "读取 [x][label].\n\n[label]:\na.md 标题\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:6", "引用式链接定义不存在: label")],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_ignores_plain_paragraph(self):
        body = "读取 [报告][a].\n\n[a]:\nSome text\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:6", "引用式链接定义不存在: a")],
                [issue.render() for issue in errors],
            )

    def test_bare_reference_definition_is_not_block_start(self):
        # 裸定义 `[lab]:` 的下一行是普通段落文本而不是定义目标, 两行同属一个
        # 段落, 紧随的 `[乙]:` 只是惰性续行, 不能登记为引用定义.
        body = "[lab]:\n[乙]: references/present.md\n\n见 [x][乙].\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [("SKILL.md:9", "引用式链接定义不存在: 乙")],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_followed_by_definition(self):
        # 合法跨行定义之后的相邻定义仍由 last_consumed_index 识别.
        body = (
            "[甲]:\n"
            "references/present.md\n"
            "[乙]: references/present.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_multiline_reference_definition_title_on_own_line_is_consumed(self):
        body = (
            "[甲]:\n"
            "references/present.md\n"
            '"标题"\n'
            "[乙]:\n"
            "references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:9", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_inline_reference_definition_title_on_own_line_is_consumed(self):
        body = (
            "[甲]: references/present.md\n"
            '"标题"\n'
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_inline_reference_definition_title_does_not_consume_next_line(self):
        body = (
            '[甲]: references/present.md "标题"\n'
            '"另一标题"\n'
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [("SKILL.md:10", "引用式链接定义不存在: 乙")],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_title_does_not_consume_next_line(self):
        body = (
            "[甲]:\n"
            'references/present.md "标题"\n'
            '"另一标题"\n'
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [("SKILL.md:11", "引用式链接定义不存在: 乙")],
                [issue.render() for issue in errors],
            )

    def test_inline_reference_definition_rejects_unquoted_extra_text(self):
        body = "读取 [x][lab].\n\n[lab]: references/a.md 额外\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:6", "引用式链接定义不存在: lab")],
                [issue.render() for issue in errors],
            )

    def test_invalid_definition_line_does_not_start_a_block(self):
        body = (
            "[lab]: references/a.md extra\n"
            "[lab2]: references/b.md\n"
            "\n"
            "读取 [u][lab2].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:9", "引用式链接定义不存在: lab2")],
                [issue.render() for issue in errors],
            )

    def test_valid_inline_definition_keeps_following_definition(self):
        body = (
            "[甲]: references/present.md\n"
            "[乙]: references/missing.md\n"
            "\n"
            "读取 [u][甲] 和 [v][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:7", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_reference_definition_ignores_unicode_indent(self):
        # CommonMark 的块首缩进只算 ASCII 空格: U+3000 / NBSP 前缀的行只是
        # 普通文本, 不登记定义, 对应的全引用链接按定义缺失报错.
        for prefix in ("\u3000", "\u00a0"):
            body = prefix + "[lab]: references/a.md\n\n读取 [x][lab].\n"
            with tempfile.TemporaryDirectory() as directory:
                root = create_skill(
                    directory, body=body, files={"references/a.md": "# 说明\n"}
                )
                errors, _, _ = validator.validate_skill(root)
                self.assertEqual(
                    [
                        (issue.location, issue.message)
                        for issue in errors
                        if "引用式链接定义不存在" in issue.message
                    ],
                    [("SKILL.md:8", "引用式链接定义不存在: lab")],
                    [prefix] + [issue.render() for issue in errors],
                )
                self.assertEqual(
                    [
                        issue.message
                        for issue in errors
                        if "本地链接目标不存在" in issue.message
                    ],
                    [],
                    [prefix] + [issue.render() for issue in errors],
                )

    def test_reference_definition_ascii_indent_limit(self):
        # 0-3 个 ASCII 空格仍是合法缩进, 4 个空格不再识别为定义.
        for indent in ("", " ", "   "):
            body = indent + "[lab]: references/a.md\n\n读取 [x][lab].\n"
            with tempfile.TemporaryDirectory() as directory:
                root = create_skill(
                    directory, body=body, files={"references/a.md": "# 说明\n"}
                )
                errors, warnings, _ = validator.validate_skill(root)
                detail = [indent] + [issue.render() for issue in errors]
                self.assertEqual(errors, [], detail)
                self.assertEqual(warnings, [], detail)
        body = "    [lab]: references/a.md\n\n读取 [x][lab].\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:8", "引用式链接定义不存在: lab")],
                [issue.render() for issue in errors],
            )

    def test_inline_reference_definition_accepts_title(self):
        body = '读取 [x][lab].\n\n[lab]: references/a.md "标题"\n'
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_inline_reference_definition_title_with_missing_target(self):
        body = '读取 [x][lab].\n\n[lab]: references/a.md "标题"\n'
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/a.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_reference_definition_label_with_escaped_bracket_resolves(self):
        body = "读取 [x][a\\]b].\n\n[a\\]b]: references/a.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_reference_definition_label_with_escaped_bracket_missing_target(self):
        body = "读取 [x][a\\]b].\n\n[a\\]b]: references/a.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/a.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_multiline_reference_definition_with_escaped_bracket_label(self):
        body = "读取 [x][a\\]b].\n\n[a\\]b]:\nreferences/a.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_inline_reference_definition_escaped_title_on_own_line_is_consumed(self):
        body = (
            "[甲]:\n"
            "references/present.md\n"
            '"标\\"题"\n'
            "[乙]:\n"
            "references/present.md\n"
            "(标\\)题)\n"
            "\n"
            "引用 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_inline_reference_definition_accepts_escaped_title(self):
        body = '读取 [x][lab].\n\n[lab]: references/a.md "标\\"题"\n'
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_inline_reference_definition_escaped_title_with_missing_target(self):
        body = '读取 [x][lab].\n\n[lab]: references/a.md "标\\"题"\n'
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/a.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_reference_definition_keeps_plain_line_after_target(self):
        body = (
            "[甲]:\n"
            "references/present.md\n"
            "Some text\n"
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:11", "引用式链接定义不存在: 乙")],
                [issue.render() for issue in errors],
            )

    def test_bare_reference_definition_reports_missing_definition(self):
        body = "读取 [x][label].\n\n[label]:\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [("SKILL.md:6", "引用式链接定义不存在: label")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("引用式链接定义不存在: label", result.stdout)

    def test_bare_reference_definition_after_paragraph_is_not_a_target(self):
        body = "读取 [x][label].\n\n[label]:\nSome text\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:6", "引用式链接定义不存在: label")],
                [issue.render() for issue in errors],
            )

    def test_bare_reference_definition_with_target_is_checked(self):
        body = "读取 [x][label].\n\n[label]:\nreferences/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    # CommonMark 实现在这里存在分歧: markdown-it 把 `===`/`==` 当作有效目标,
    # pandoc 则视为 Setext 标题; 本实现选择 pandoc 语义, 因此该行不是目标,
    # 引用会以 "引用式链接定义不存在" 报错.
    def test_block_marker_after_reference_definition_is_not_a_target(self):
        for marker in ("---", "===", "==", "***", "___", "# 标题"):
            with self.subTest(marker=marker):
                body = "读取 [x][lab].\n\n[lab]:\n{}\n".format(marker)
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(directory, body=body)
                    errors, _, _ = validator.validate_skill(root)
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "本地链接目标不存在" in issue.message
                        ],
                        [],
                        [issue.render() for issue in errors],
                    )
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "引用式链接定义不存在" in issue.message
                        ],
                        [("SKILL.md:6", "引用式链接定义不存在: lab")],
                        [issue.render() for issue in errors],
                    )

    # 独立成行的 `==`/`--` 前面没有段落文本, 它们本身只是普通段落行, 不是
    # Setext 标题下划线, 因此后续的 `[a]: 目标` 是同段的惰性续行, 不登记定义.
    def test_standalone_setext_marker_is_not_a_block_boundary(self):
        for marker in ("==", "--"):
            with self.subTest(marker=marker):
                body = "{}\n[a]: references/present.md\n\n[x][a]\n".format(marker)
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(
                        directory,
                        body=body,
                        files={"references/present.md": "# 说明\n"},
                    )
                    errors, warnings, _ = validator.validate_skill(root)
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "本地链接目标不存在" in issue.message
                        ],
                        [],
                        [issue.render() for issue in errors],
                    )
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "引用式链接定义不存在" in issue.message
                        ],
                        [("SKILL.md:9", "引用式链接定义不存在: a")],
                        [issue.render() for issue in errors],
                    )

    # 对照用例: `===` 紧跟段落 `Title` 时是真实的 Setext 标题下划线, 其后的
    # `[a]: 目标` 处于块首, 是有效定义, 引用不报缺失.
    def test_setext_heading_keeps_following_reference_definition(self):
        body = "Title\n===\n[a]: references/present.md\n\n[x][a]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    # 独立成行的 `---` 仍是分隔线 (thematic break), 其后是新的块, 定义有效.
    def test_standalone_thematic_break_keeps_following_definition(self):
        body = "---\n[a]: references/present.md\n\n[x][a]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    # CommonMark 允许引用定义的标题跨多行书写 (`"ti` 换行 `tle"`), pandoc
    # 也接受; 本验证器只识别单行闭合的标题, 这是已知限制. 跨行标题使定义
    # 不成立, 标签不会登记, 引用会以 "引用式链接定义不存在" 报硬错误.
    def test_multiline_reference_title_is_not_recognized(self):
        for body in (
            '读取 [x][a].\n\n[a]: target.md "ti\ntle"\n',
            '读取 [x][a].\n\n[a]:\ntarget.md "ti\ntle"\n',
        ):
            with self.subTest(body=body):
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(
                        directory,
                        body=body,
                        files={"target.md": "# 说明\n"},
                    )
                    errors, warnings, _ = validator.validate_skill(root)
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "本地链接目标不存在" in issue.message
                        ],
                        [],
                        [issue.render() for issue in errors],
                    )
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "引用式链接定义不存在" in issue.message
                        ],
                        [("SKILL.md:6", "引用式链接定义不存在: a")],
                        [issue.render() for issue in errors],
                    )

    # CommonMark 允许块引用打断段落, 因此紧跟普通段落, 中间没有空行的
    # `> [lab]: 目标` 是块引用内的引用定义; markdown-it 和 pandoc 的
    # commonmark 读取器也接受 (`[x][lab]` 能解析为链接). 本验证器只把块首
    # 位置的块引用定义登记为目标: 该行紧跟段落时属于惰性续行, 定义不成立,
    # `[x][lab]` 会以 "引用式链接定义不存在" 报硬错误. 列表项内的块引用
    # 定义 (`- > [lab]: 目标`) 同样不被识别, 两者都是已知限制: 设计上明确
    # 不追求完整 CommonMark (D3), 不修改解析行为. 空行之后的块引用定义
    # 仍能识别, 因此限制只在块首判定上.
    def test_blockquote_reference_definition_after_paragraph_is_not_recognized(self):
        cases = (
            ("正文段落.\n> [lab]: references/present.md\n\n[x][lab]\n", "SKILL.md:9"),
            ("- > [lab]: references/present.md\n\n[x][lab]\n", "SKILL.md:8"),
        )
        for body, location in cases:
            with self.subTest(body=body):
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(
                        directory,
                        body=body,
                        files={"references/present.md": "# 说明\n"},
                    )
                    errors, warnings, _ = validator.validate_skill(root)
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "本地链接目标不存在" in issue.message
                        ],
                        [],
                        [issue.render() for issue in errors],
                    )
                    self.assertEqual(
                        [
                            (issue.location, issue.message)
                            for issue in errors
                            if "引用式链接定义不存在" in issue.message
                        ],
                        [(location, "引用式链接定义不存在: lab")],
                        [issue.render() for issue in errors],
                    )
                    self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_blockquote_reference_definition_at_block_start_is_recognized(self):
        # 对照用例: 中间有空行时 `> [lab]: ...` 处于块首, 前缀会被去掉后
        # 正常识别为定义, 引用不报缺失.
        body = "正文段落.\n\n> [lab]: references/present.md\n\n[x][lab]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    # CommonMark 允许引用定义出现在列表项内容中: `- item` 之后 4 空格缩进的
    # `[文档]: 目标` 属于该列表项的内容, pandoc 和 markdown-it 都会把它登记
    # 为定义, 随后的 `[x][文档]` 能解析为链接. 本验证器只允许定义行最多 3 个
    # 空格缩进 (实现匹配 `^ {0,3}\[`); 4 个及以上空格 (缩进代码) 或列表项内容
    # 中的缩进定义不会登记, 引用会以 "引用式链接定义不存在" 报硬错误.
    # 这是已知限制: 设计上明确不追求完整 CommonMark (D3), 不修改解析行为,
    # 需要人工改写为顶层定义或列表项同行的 `- [文档]: 目标`.
    def test_nested_list_reference_definition_is_not_recognized(self):
        body = "- item\n    [文档]: references/a.md\n\n[x][文档]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/a.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:9", "引用式链接定义不存在: 文档")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_html_entities_in_link_targets_are_decoded(self):
        body = "读取 [a](a&amp;b.md).\n\n参考 [b][b].\n\n[b]: a&amp;b.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"a&b.md": "# 说明\n"},
                body=body,
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_html_entity_link_target_still_reports_missing(self):
        body = "读取 [a](references/a&amp;b.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    (
                        "SKILL.md:6",
                        "本地链接目标不存在: references/a&b.md",
                    )
                ],
                [issue.render() for issue in errors],
            )

    def test_percent_encoded_space_in_link_target_resolves(self):
        body = "读取 [脚本](a%20b.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, files={"a b.md": "# 说明\n"}, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_percent_encoded_percent_in_link_target_resolves(self):
        body = "读取 [脚本](a%2520b.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, files={"a%20b.md": "# 说明\n"}, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_windows_absolute_paths_warn_and_fail_strict(self):
        body = (
            "读取 [盘符](<C:\\work\\demo.md>) 与 [斜杠](C:/work/demo.md), "
            "以及 [共享](<\\\\server\\share\\demo.md>).\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in warnings
                    if "Windows 绝对路径不可移植" in issue.message
                ],
                [
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: C:/work/demo.md",
                    ),
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: C:\\work\\demo.md",
                    ),
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: \\server\\share\\demo.md",
                    ),
                ],
                [issue.render() for issue in warnings],
            )

            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stdout)
            self.assertEqual(strict.returncode, 1, strict.stdout)

    def test_bare_windows_and_unc_paths_warn(self):
        body = r"读取 [盘符](C:\work\demo.md) 与 [共享](\\server\share\demo.md)." "\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in warnings
                    if "Windows 绝对路径不可移植" in issue.message
                ],
                [
                    ("SKILL.md:6", "Windows 绝对路径不可移植: C:\\work\\demo.md"),
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: \\server\\share\\demo.md",
                    ),
                ],
                [issue.render() for issue in warnings],
            )

            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stdout)
            self.assertEqual(strict.returncode, 1, strict.stdout)

    def test_html_href_and_img_src_missing_targets_report_errors(self):
        body = (
            '参考 <a href="references/html-missing.md">文档</a>.\n'
            '插图 <img src="references/img-missing.png"> 结束.\n'
            "\n"
            "```\n"
            '<a href="references/code-missing.md">代码</a>\n'
            "```\n"
            "\n"
            "<pre>\n"
            '<img src="references/pre-missing.png">\n'
            "</pre>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [
                    (
                        "SKILL.md:6",
                        "本地链接目标不存在: references/html-missing.md",
                    ),
                    (
                        "SKILL.md:7",
                        "本地链接目标不存在: references/img-missing.png",
                    ),
                ],
                [issue.render() for issue in errors],
            )
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("html-missing.md", result.stdout)

    def test_missing_reference_definition_reports_error(self):
        body = (
            "读取 [说明][missing].\n"
            "\n"
            "[定义][present] 见下.\n"
            "\n"
            "[present]: references/present.md\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/present.md": "# 说明\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [("SKILL.md:6", "引用式链接定义不存在: missing")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    # CommonMark 的引用定义标题是纯文本, 其中的 `[x](目标)` 不是链接,
    # `[x][y]` 也不是引用式链接, 因此都不会被扫描.
    def test_definition_title_link_syntax_is_not_scanned(self):
        body = (
            "读取 [文本][lab].\n"
            "\n"
            '[lab]: SKILL.md "[x](references/missing.md)"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])
            self.assertEqual(
                [target for _, target in validator.scan_links(body)], ["SKILL.md"]
            )

    def test_definition_title_reference_syntax_is_not_scanned(self):
        body = (
            "读取 [文本][lab].\n"
            "\n"
            '[lab]: SKILL.md "[x][y]"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])
            self.assertEqual(validator.scan_missing_reference_links(body), [])

    def test_standalone_definition_title_link_syntax_is_not_scanned(self):
        body = (
            "读取 [文本][lab].\n"
            "\n"
            "[lab]: SKILL.md\n"
            '"[x](references/missing.md)"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_definition_title_masking_keeps_target_check(self):
        body = (
            "读取 [文本][lab].\n"
            "\n"
            '[lab]: references/missing.md "[x](references/other.md)"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_definition_title_masking_keeps_missing_definition_check(self):
        body = (
            "读取 [文本][lab].\n"
            "\n"
            '[other]: SKILL.md "[x][y]"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:6", "引用式链接定义不存在: lab")],
                [issue.render() for issue in errors],
            )

    def test_forward_slash_unc_and_drive_relative_paths_warn(self):
        body = "读取 [共享](//server/share/demo.md) 与 [盘符](C:demo.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in warnings
                    if "Windows 绝对路径不可移植" in issue.message
                ],
                [
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: //server/share/demo.md",
                    ),
                    (
                        "SKILL.md:6",
                        "Windows 绝对路径不可移植: C:demo.md",
                    ),
                ],
                [issue.render() for issue in warnings],
            )

            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stdout)
            self.assertEqual(strict.returncode, 1, strict.stdout)

    # Windows 的 Path.resolve() 可能返回磁盘规范大小写, 大小写不一致的链接会被规范成实际路径, 该警告不触发.
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 路径解析可能规范化大小写, 该警告不触发",
    )
    def test_link_path_case_mismatch_warns_and_counts_as_referenced(self):
        body = "读取 [笔记](References/note.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={"references/note.md": "# 笔记\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in warnings
                    if "大小写与磁盘不一致" in issue.message
                ],
                [
                    (
                        "SKILL.md:6",
                        "链接路径大小写与磁盘不一致, 不可移植: References/note.md",
                    )
                ],
                [issue.render() for issue in warnings],
            )
            self.assertEqual(
                [
                    issue.render()
                    for issue in warnings
                    if "未被 SKILL.md 直接引用" in issue.message
                ],
                [],
            )

    def test_nul_in_link_target_reports_error_without_traceback(self):
        body = "读取 [坏](references/bad%00name.md).\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(warnings, [])
            self.assertEqual(
                [(issue.location, issue.message) for issue in errors],
                [
                    (
                        "SKILL.md:6",
                        "本地链接目标包含 NUL 或控制字符: references/bad\\x00name.md",
                    )
                ],
                [issue.render() for issue in errors],
            )

            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("NUL 或控制字符", result.stdout)

    def test_control_characters_in_link_target_report_error_without_traceback(self):
        cases = (
            ("%01", "\\x01"),
            ("%7F", "\\x7f"),
            ("%C2%85", "\\x85"),
            ("%C2%9B", "\\x9b"),
        )
        for encoded, escaped in cases:
            with self.subTest(encoded=encoded):
                with tempfile.TemporaryDirectory() as directory:
                    body = "读取 [坏](references/bad{}name.md).\n".format(encoded)
                    root = create_skill(directory, body=body)
                    errors, warnings, _ = validator.validate_skill(root)
                    self.assertEqual(warnings, [])
                    self.assertEqual(
                        [(issue.location, issue.message) for issue in errors],
                        [
                            (
                                "SKILL.md:6",
                                "本地链接目标包含 NUL 或控制字符: "
                                "references/bad{}name.md".format(escaped),
                            )
                        ],
                        [issue.render() for issue in errors],
                    )

                    result = run_script(VALIDATOR_PATH, str(root))
                    self.assertEqual(
                        result.returncode, 1, result.stdout + result.stderr
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertIn("NUL 或控制字符", result.stdout)

    def test_dot_slash_mention_counts_as_referenced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"scripts/foo.py": "print(1)\n"},
                body="运行 ./scripts/foo.py 生成报告.\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [
                    issue.location
                    for issue in warnings
                    if "未被 SKILL.md 直接引用" in issue.message
                ],
                [],
                [issue.render() for issue in warnings],
            )

    def test_parenthesized_and_angle_bracket_targets_report_full_target(self):
        body = (
            "[括号断链](references/a(1).md)\n\n"
            "[a]: <references/b c.md>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    ("SKILL.md:6", "本地链接目标不存在: references/a(1).md"),
                    ("SKILL.md:8", "本地链接目标不存在: references/b c.md"),
                ],
                [issue.render() for issue in errors],
            )

    def test_external_links_and_code_fences_are_ignored(self):
        body = (
            "[网页](https://example.com) [锚点](#section) [邮件](mailto:a@b.c)\n\n"
            "```markdown\n[缺失](references/missing.md)\n```\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_short_backtick_run_does_not_close_longer_fence(self):
        body = (
            "````markdown\n"
            "[缺失](references/missing.md)\n"
            "```\n"
            "[也缺失](references/other.md)\n"
            "````\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_short_tilde_run_does_not_close_longer_fence(self):
        body = (
            "~~~~markdown\n"
            "[缺失](references/missing.md)\n"
            "~~~\n"
            "[也缺失](references/other.md)\n"
            "~~~~\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_broken_link_after_long_fence_closes_is_reported(self):
        body = (
            "````markdown\n"
            "[围栏内](references/in-fence.md)\n"
            "```\n"
            "````\n"
            "[围栏外](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:10", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_four_space_indented_fence_does_not_open_block(self):
        body = (
            "正文\n\n"
            "    ```markdown\n"
            "    [缩进内](references/indented.md)\n"
            "    ```\n"
            "[缩进后](references/after.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            messages = [
                (issue.location, issue.message)
                for issue in errors
                if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(
                messages,
                [("SKILL.md:11", "本地链接目标不存在: references/after.md")],
                [issue.render() for issue in errors],
            )

    def test_indented_code_block_links_are_ignored(self):
        body = (
            "正文\n\n"
            "    [缺失](references/missing.md)\n"
            "    [也缺失](references/other.md)\n\n"
            "结尾\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_list_continuation_links_are_reported(self):
        body = (
            "- 顶层列表项\n\n"
            "    [续行断链](references/continuation.md)\n\n"
            "    - [嵌套断链](references/nested.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(warnings, [])
            matches = sorted(
                issue.message for issue in errors if "本地链接目标不存在" in issue.message
            )
            self.assertEqual(
                matches,
                [
                    "本地链接目标不存在: references/continuation.md",
                    "本地链接目标不存在: references/nested.md",
                ],
            )

    def test_two_space_nested_list_links_are_reported(self):
        body = "- 顶层列表项\n  - [嵌套断链](references/nested.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(warnings, [])
            matches = [
                issue.message for issue in errors if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(
                matches, ["本地链接目标不存在: references/nested.md"]
            )

    def test_top_level_indented_code_block_links_are_ignored(self):
        body = (
            "- 顶层列表项\n\n"
            "离开列表的正文.\n\n"
            "    [代码块内](references/missing.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_indented_code_block_after_list_and_fence_links_are_ignored(self):
        body = (
            "# 流程\n\n"
            "+ 读取 [参考](references/a.md).\n\n"
            "```text\n"
            "x\n"
            "```\n\n"
            "    [缩进代码](nope2.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/a.md": "# 参考\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])
            self.assertEqual(
                [target for _, target in validator.scan_links(body)],
                ["references/a.md"],
            )

    def test_indented_code_block_inside_list_links_are_ignored(self):
        body = "- 顶层列表项\n\n        [代码块内](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_indented_link_after_heading_is_indented_code(self):
        body = "# 标题\n    [缩进内](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    # 块边界之后的缩进行是缩进代码块, 即使边界行与缩进行之间没有空行.
    # pandoc 与 markdown-it 都这样解析, 因此其中的链接不检查.
    def test_indented_link_directly_after_block_boundary_is_indented_code(self):
        boundaries = {
            "fence": "```text\nx\n```\n",
            "html_comment": "<!-- 注释 -->\n",
            "multiline_html_comment": "<!--\n注释\n-->\n",
            "html_comment_with_blank_line": "<!--\n\n-->\n",
            "raw_html_same_line": "<pre>x</pre>\n",
            "raw_html_close": "<pre>\nx\n</pre>\n",
            "setext_heading": "标题\n===\n",
        }
        for name, boundary in boundaries.items():
            for blank_after in ("", "\n"):
                with self.subTest(boundary=name, blank_after=bool(blank_after)):
                    body = (
                        boundary
                        + blank_after
                        + "    [缩进内](references/missing.md)\n"
                    )
                    with tempfile.TemporaryDirectory() as directory:
                        root = create_skill(directory, body=body)
                        errors, warnings, _ = validator.validate_skill(root)
                        self.assertEqual(
                            errors, [], [issue.render() for issue in errors]
                        )
                        self.assertEqual(warnings, [])
                        self.assertEqual(
                            validator.scan_links(body),
                            [],
                            "块边界后的缩进链接不应被扫描",
                        )

    def test_unindented_link_after_block_boundary_is_still_reported(self):
        boundaries = {
            "fence": "```text\nx\n```\n",
            "html_comment": "<!-- 注释 -->\n",
            "raw_html_same_line": "<pre>x</pre>\n",
            "setext_heading": "标题\n===\n",
        }
        for name, boundary in boundaries.items():
            with self.subTest(boundary=name):
                body = boundary + "[断链](references/missing.md)\n"
                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(directory, body=body)
                    errors, _, _ = validator.validate_skill(root)
                    self.assertEqual(
                        [
                            issue.message
                            for issue in errors
                            if "本地链接目标不存在" in issue.message
                        ],
                        ["本地链接目标不存在: references/missing.md"],
                        [issue.render() for issue in errors],
                    )

    def test_fence_inside_list_follows_list_indent(self):
        body = (
            "1. 步骤\n\n"
            "    ~~~text\n"
            "    [围栏内](references/missing.md)\n"
            "    ~~~\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_definition_after_list_item_is_lazy_continuation(self):
        body = "- item\n[ref]: references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_definition_at_block_start_is_still_checked(self):
        body = "正文\n\n[ref]: references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_consecutive_reference_definitions_are_checked(self):
        body = "[甲]: references/present.md\n[乙]: references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:7", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_adjacent_multiline_reference_definitions_are_checked(self):
        body = (
            "[甲]:\n"
            "references/present.md\n"
            "[乙]:\n"
            "references/missing.md\n"
            "\n"
            "引用 [甲][甲] 和 [乙][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_unreferenced_adjacent_multiline_definition_is_checked(self):
        body = (
            "[甲]:\n"
            "references/present.md\n"
            "[乙]:\n"
            "references/missing.md\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_list_item_multiline_reference_definition_is_checked(self):
        body = "- [lab]:\n  references/present.md\n\n[文本][lab]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_list_item_multiline_reference_definition_with_missing_target(self):
        body = "- [lab]:\n  references/missing.md\n\n[文本][lab]\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:6", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_list_item_reference_definitions_are_checked(self):
        body = "- [甲]: references/missing.md\n1. [乙]: references/other.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    ("SKILL.md:6", "本地链接目标不存在: references/missing.md"),
                    ("SKILL.md:7", "本地链接目标不存在: references/other.md"),
                ],
                [issue.render() for issue in errors],
            )

    def test_non_one_ordered_list_item_after_paragraph_is_lazy_continuation(self):
        body = (
            "para\n"
            "2) [lab]: references/present.md\n"
            "\n"
            "见 [x][lab].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:9", "引用式链接定义不存在: lab")],
                [issue.render() for issue in errors],
            )

    def test_one_starting_ordered_list_item_after_paragraph_is_definition(self):
        body = (
            "para\n"
            "1. [lab]: references/present.md\n"
            "\n"
            "见 [x][lab].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_non_one_ordered_list_item_after_blank_line_is_definition(self):
        body = (
            "para\n"
            "\n"
            "10. [lab]: references/present.md\n"
            "\n"
            "见 [x][lab].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_non_one_ordered_list_item_after_multiline_list_item_is_definition(self):
        body = (
            "1. item\n"
            "   paragraph\n"
            "2. [lab]: references/present.md\n"
            "\n"
            "见 [x][lab].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_non_one_ordered_list_item_inside_list_item_is_lazy_continuation(self):
        body = (
            "- item\n"
            "  2. [lab]: references/present.md\n"
            "\n"
            "见 [x][lab].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:9", "引用式链接定义不存在: lab")],
                [issue.render() for issue in errors],
            )

    def test_list_item_definition_unindented_title_is_consumed(self):
        body = (
            "- [甲]: references/present.md\n"
            '"标题"\n'
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_list_item_definition_indented_title_is_consumed(self):
        body = (
            "- [甲]: references/present.md\n"
            '  "标题"\n'
            "[乙]: references/missing.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    issue.message
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )

    def test_list_item_definition_unindented_title_targets_are_checked(self):
        body = (
            "- [甲]: references/present.md\n"
            '"标题"\n'
            "[乙]: references/other.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={
                    "references/present.md": "# 说明\n",
                    "references/other.md": "# 另一份说明\n",
                },
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])

    def test_list_item_definition_invalid_title_is_not_consumed(self):
        body = (
            "- [甲]: references/present.md\n"
            '"未闭合\n'
            "[乙]: references/other.md\n"
            "\n"
            "见 [x][甲] [y][乙].\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                body=body,
                files={
                    "references/present.md": "# 说明\n",
                    "references/other.md": "# 另一份说明\n",
                },
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [],
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "引用式链接定义不存在" in issue.message
                ],
                [("SKILL.md:10", "引用式链接定义不存在: 乙")],
                [issue.render() for issue in errors],
            )

    def test_list_item_definition_with_paragraph_continuation_is_not_definition(self):
        body = "- [说明]:\n  Some text\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_blockquoted_consecutive_reference_definitions_are_checked(self):
        body = "> [甲]: references/present.md\n> [乙]: references/missing.md\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:7", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_html_comment_links_are_ignored(self):
        body = (
            "正文\n\n"
            "<!-- [单行缺失](references/one.md) -->\n\n"
            "<!--\n"
            "[跨行缺失](references/two.md)\n"
            "-->\n"
            "前缀 <!-- [行内缺失](references/three.md) --> 后缀\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_blockquote_indented_code_links_are_ignored(self):
        body = "正文\n\n>     [块引用代码内](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_blockquote_multiline_indented_code_links_are_ignored(self):
        body = (
            "> 引用正文\n"
            ">\n"
            ">     [块引用代码内](references/missing.md)\n"
            ">     [也代码内](references/other.md)\n"
            ">\n"
            "> [引用断链](references/quote.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:11", "本地链接目标不存在: references/quote.md")],
                [issue.render() for issue in errors],
            )

    def test_blockquoted_fence_links_are_ignored(self):
        body = (
            "> ```markdown\n"
            "> [围栏内](references/in-fence.md)\n"
            "> ```\n"
            "> [围栏外](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:9", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_raw_html_block_links_are_ignored(self):
        body = (
            "<pre>\n"
            "[预格式内](references/pre.md)\n"
            "</pre>\n\n"
            "<script>\n"
            "[脚本内](references/script.md)\n"
            "</script>\n\n"
            "<style>\n"
            "[样式内](references/style.md)\n"
            "</style>\n\n"
            "<textarea>\n"
            "[文本域内](references/textarea.md)\n"
            "</textarea>\n\n"
            '<PRE class="box">\n'
            "[大写内](references/upper.md)\n"
            "</PRE>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_line_start_raw_html_same_line_links_are_ignored(self):
        body = "<pre>[预格式内](references/missing.md)</pre> 后缀\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_inline_raw_html_does_not_hide_links_on_same_line(self):
        body = (
            "前缀 <pre>[预格式内](references/inline.md)</pre> 后缀\n\n"
            "前缀 <textarea>[文本域内](references/other.md)</textarea>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    ("SKILL.md:6", "本地链接目标不存在: references/inline.md"),
                    ("SKILL.md:8", "本地链接目标不存在: references/other.md"),
                ],
                [issue.render() for issue in errors],
            )

    def test_type7_html_block_links_are_ignored(self):
        body = (
            "<custom-tag>\n"
            "[自定义内](references/custom.md)\n"
            "</custom-tag>\n"
            "\n"
            "<br>\n"
            "[换行内](references/br.md)\n"
            "\n"
            "[真实断链](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:13", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_type7_html_block_does_not_interrupt_paragraph(self):
        body = "第一段\n<br>\n[断链](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_type7_html_block_after_blank_line_hides_links(self):
        body = (
            "[现有](references/present.md)\n"
            "\n"
            "<br>\n"
            "[换行内](references/br.md)\n"
            "\n"
            "[真实断链](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:11", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_self_closing_raw_html_start_still_opens_block(self):
        body = '<pre class="x" />\n\n[块内](references/missing.md)\n</pre>\n'
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_inline_pre_does_not_start_html_block(self):
        body = "前缀 <pre>行内标签\n\n[真实断链](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_links_after_raw_html_block_are_reported(self):
        body = (
            "<pre>\n"
            "[预格式内](references/inside.md)\n"
            "</pre>\n\n"
            "[真实断链](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:10", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_type6_html_block_links_are_ignored(self):
        body = (
            "<details>\n"
            "<summary>说明</summary>\n"
            "[详情内](references/details.md)\n"
            "</details>\n"
            "\n"
            '<div class="box">\n'
            "[块内](references/div.md)\n"
            "</div>\n"
            "\n"
            "  <table>\n"
            "<tr><td>[表格内](references/table.md)</td></tr>\n"
            "</table>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_links_after_type6_html_block_are_reported(self):
        body = (
            "<details>\n"
            "[块内](references/inside.md)\n"
            "</details>\n"
            "\n"
            "[真实断链](references/outside.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:10", "本地链接目标不存在: references/outside.md")],
                [issue.render() for issue in errors],
            )

    def test_nested_image_target_is_reported(self):
        body = "[![缺图](references/missing.png)](references/present.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory, body=body, files={"references/present.md": "# 说明\n"}
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:6", "本地链接目标不存在: references/missing.png")],
                [issue.render() for issue in errors],
            )
            self.assertEqual(warnings, [])

    def test_standalone_image_target_is_reported_once(self):
        body = "![缺图](references/missing.png)\n\n[普通断链](references/other.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [
                    ("SKILL.md:6", "本地链接目标不存在: references/missing.png"),
                    ("SKILL.md:8", "本地链接目标不存在: references/other.md"),
                ],
                [issue.render() for issue in errors],
            )

    def test_links_after_comment_and_indented_code_are_still_reported(self):
        body = (
            "    [代码块内](references/missing.md)\n\n"
            "<!-- [注释内](references/missing.md) -->\n\n"
            "[真实断链](references/missing.md)\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            matches = [
                issue for issue in errors if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(len(matches), 1, [issue.render() for issue in errors])
            self.assertTrue(
                re.fullmatch(r"SKILL\.md:\d+", matches[0].location),
                matches[0].location,
            )

    def test_indented_code_block_comment_marker_keeps_later_link_reported(self):
        body = "    <!--\n\n[真实断链](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertFalse(
                any(issue.message == "正文不能为空" for issue in errors),
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:8", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_fenced_comment_marker_keeps_later_link_reported(self):
        body = "~~~\n<!--\n~~~\n\n[真实断链](references/missing.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertFalse(
                any(issue.message == "正文不能为空" for issue in errors),
                [issue.render() for issue in errors],
            )
            self.assertEqual(
                [
                    (issue.location, issue.message)
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                [("SKILL.md:10", "本地链接目标不存在: references/missing.md")],
                [issue.render() for issue in errors],
            )

    def test_blockquote_fence_marker_inside_fence_does_not_close_it(self):
        body = "```markdown\n> ```\n[围栏内](references/in-fence.md)\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_html_comment_only_body_outside_code_blocks_is_empty(self):
        body = "<!-- 只有注释 -->\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(
                any(issue.message == "正文不能为空" for issue in errors),
                [issue.render() for issue in errors],
            )

    def test_single_backtick_code_span_links_are_ignored(self):
        body = "正文 `[单反引号](references/missing.md)` 结束.\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_multi_backtick_code_span_links_are_ignored(self):
        body = (
            "正文 ``[双反引号](references/missing.md)`` 结束.\n\n"
            "正文 ```[三反引号](references/missing.md)``` 结束.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_multiline_code_span_links_are_ignored(self):
        body = (
            "正文 `[跨行代码内](references/missing.md)\n"
            "另一行` 结束.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_links_after_multiline_code_span_are_reported(self):
        body = (
            "正文 `[跨行代码内](references/inside.md)\n"
            "另一行` 之后 [真实断链](references/outside.md) 仍应检查.\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            matches = [
                issue.message for issue in errors if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(
                matches, ["本地链接目标不存在: references/outside.md"]
            )

    def test_unclosed_backtick_keeps_later_links_reported(self):
        body = "正文 `未闭合 [真实断链](references/missing.md) 仍应检查.\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            matches = [
                issue.message for issue in errors if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(matches, ["本地链接目标不存在: references/missing.md"])

    def test_comment_marker_inside_code_span_keeps_later_links_reported(self):
        body = "使用 `<!--` 标记后 [真实断链](references/missing.md) 仍应检查.\n"
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body=body)
            errors, _, _ = validator.validate_skill(root)
            matches = [
                issue.message for issue in errors if "本地链接目标不存在" in issue.message
            ]
            self.assertEqual(matches, ["本地链接目标不存在: references/missing.md"])

    def test_non_standard_field_warns_and_strict_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, extra_frontmatter="vendor-field: true\n")
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(any("非标准字段" in issue.message for issue in warnings))
            self.assertTrue(
                any(
                    "非标准字段" in issue.message and "vendor-field" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )
            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertIn("警告", default.stdout)
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("严格模式", strict.stdout)

    def test_non_ascii_non_standard_field_warns_at_its_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="# 注释\n# 注释\n版本: \"1.0\"\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            matches = [
                issue
                for issue in warnings
                if "非标准字段" in issue.message and "版本" in issue.message
            ]
            self.assertEqual(len(matches), 1, [issue.render() for issue in warnings])
            self.assertEqual(matches[0].location, "SKILL.md:6")

    def test_unreferenced_reference_file_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/used.md": "# 已用\n",
                    "references/unused.md": "# 未用\n",
                },
                body="[已用](references/used.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any(
                    "references/unused.md" in issue.location
                    and "未被 SKILL.md 直接引用" in issue.message
                    for issue in warnings
                )
            )
            self.assertFalse(
                any("references/used.md" in issue.location for issue in warnings)
            )

    def test_reference_link_does_not_exempt_unreferenced_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[b](b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any(
                    issue.location == "references/b.md"
                    and "未被 SKILL.md 直接引用" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )
            self.assertTrue(
                any(
                    issue.location == "references/a.md:1"
                    and "参考文件互相引用" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )
            self.assertFalse(
                any(
                    issue.location == "references/a.md"
                    and "未被 SKILL.md 直接引用" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )

    def test_skill_links_to_every_reference_exempt_from_unreferenced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[b](b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md) [b](references/b.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertFalse(
                any("未被 SKILL.md 直接引用" in issue.message for issue in warnings),
                [issue.render() for issue in warnings],
            )

    def test_adjacent_chinese_and_sentence_period_count_as_mention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"scripts/foo.py": "print(1)\n"},
                body="运行scripts/foo.py. 也可以再次执行\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_mention_does_not_leak_into_longer_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "scripts/foo.py": "print(1)\n",
                    "scripts/foo.py.bak": "backup\n",
                },
                body="运行scripts/foo.py. 旧脚本 myscripts/foo.py 需忽略\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [
                    issue.location
                    for issue in warnings
                    if "未被 SKILL.md 直接引用" in issue.message
                ],
                ["scripts/foo.py.bak"],
                [issue.render() for issue in warnings],
            )

    def test_assets_are_not_checked_for_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, files={"assets/logo.png": "image"})
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_top_level_files_are_not_checked_for_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"LICENSE": "MIT\n", "notes.md": "# 笔记\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)

    def test_top_level_files_named_scripts_or_references_are_not_checked(self):
        # 顶层普通文件即使名叫 scripts/references 也不是目录, 不参与引用扫描.
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "scripts": "not a directory\n",
                    "references": "not a directory\n",
                },
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [
                    issue.render()
                    for issue in warnings
                    if "未被 SKILL.md 直接引用" in issue.message
                ],
                [],
            )

    def test_unreferenced_files_in_scripts_and_references_still_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "scripts/foo.py": "print(1)\n",
                    "references/note.md": "# 笔记\n",
                },
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [
                    issue.location
                    for issue in warnings
                    if "未被 SKILL.md 直接引用" in issue.message
                ],
                ["references/note.md", "scripts/foo.py"],
            )

    def test_license_with_nul_does_not_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter='license: "LICENSE\\0"\n',
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])
            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_unreferenced_scripts_file_still_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, files={"scripts/unused.py": "print(1)\n"})
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any(
                    issue.location == "scripts/unused.py"
                    and "未被 SKILL.md 直接引用" in issue.message
                    for issue in warnings
                )
            )

    def test_license_file_reference_is_not_warned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: references/LICENSE\n",
                files={"references/LICENSE": "MIT\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)

    def test_license_symlink_to_skill_file_is_not_warned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: references/LICENSE\n",
                files={"LICENSE.txt": "MIT\n"},
            )
            link = root / "references" / "LICENSE"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(root / "LICENSE.txt")
            except (OSError, NotImplementedError, AttributeError):
                self.skipTest("当前平台不支持创建符号链接")
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)

    def test_license_case_mismatch_is_not_warned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: references/license.txt\n",
                files={"references/License.txt": "MIT\n"},
            )
            if not (root / "references" / "license.txt").is_file():
                self.skipTest("当前文件系统区分大小写")
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [], [issue.render() for issue in warnings])
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)

    def test_license_symlink_does_not_exempt_other_reference_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: references/LICENSE\n",
                files={
                    "LICENSE.txt": "MIT\n",
                    "references/unused.md": "# 未用\n",
                },
            )
            link = root / "references" / "LICENSE"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(root / "LICENSE.txt")
            except (OSError, NotImplementedError, AttributeError):
                self.skipTest("当前平台不支持创建符号链接")
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [issue.location for issue in warnings], ["references/unused.md"]
            )

    def test_unreferenced_references_file_in_same_skill_still_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: references/LICENSE\n",
                files={
                    "references/LICENSE": "MIT\n",
                    "references/unused.md": "# 未用\n",
                },
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(
                [issue.location for issue in warnings], ["references/unused.md"]
            )

    def test_license_name_is_not_treated_as_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="license: MIT\n",
                files={"references/unused.md": "# 未用\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any(issue.location == "references/unused.md" for issue in warnings)
            )

    def test_reference_cross_link_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[b](b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md) [b](references/b.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any("参考文件互相引用" in issue.message for issue in warnings)
            )

    def test_reference_links_resolve_from_file_or_skill_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[根相对](references/b.md) [文件相对](b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md)\n",
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])

    def test_reference_link_missing_in_both_bases_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a.md": "[缺失](missing.md)\n"},
                body="[a](references/a.md)\n",
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    issue.location
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                ["references/a.md:1"],
            )

    # 平台前提: POSIX 绝对路径 (/tmp/...) 才会进入"绝对路径链接不可移植"警告分支.
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 绝对路径会走单独的警告分支, 不适用 POSIX 绝对路径断言",
    )
    def test_absolute_link_warns_without_failing_default(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "outside.md"
            target.write_text("# 外部\n", encoding="utf-8")
            root = create_skill(
                directory, body="参考 [外部]({}).\n".format(target)
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            matches = [
                issue
                for issue in warnings
                if "绝对路径链接不可移植" in issue.message
            ]
            self.assertEqual(len(matches), 1, [issue.render() for issue in warnings])

            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stdout)
            self.assertEqual(strict.returncode, 1, strict.stdout)

    # 平台前提: 目标不存在报错依赖 POSIX 绝对路径被当作普通链接解析.
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 绝对路径会走单独的警告分支, 不适用 POSIX 绝对路径断言",
    )
    def test_absolute_link_missing_reports_error_and_fails_default(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.md"
            root = create_skill(
                directory, body="参考 [缺失]({}).\n".format(missing)
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [
                    issue.render()
                    for issue in errors
                    if "本地链接目标不存在" in issue.message
                ],
                ["SKILL.md:6: 本地链接目标不存在: {}".format(missing)],
                [issue.render() for issue in errors],
            )
            self.assertFalse(
                any(
                    "绝对路径链接不可移植" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )

            result = run_script(VALIDATOR_PATH, str(root))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    # 平台前提: 绝对路径引用计数仅在 POSIX 绝对路径解析下成立.
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 绝对路径会走单独的警告分支, 不适用 POSIX 绝对路径断言",
    )
    def test_absolute_link_inside_skill_warns_and_counts_as_referenced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/extra.md": "# 说明\n"},
                body="参考 [说明]({}).\n".format(
                    Path(directory) / "demo-skill" / "references" / "extra.md"
                ),
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                len(
                    [
                        issue
                        for issue in warnings
                        if "绝对路径链接不可移植" in issue.message
                    ]
                ),
                1,
                [issue.render() for issue in warnings],
            )
            self.assertFalse(
                any(
                    issue.location == "references/extra.md"
                    and "未被 SKILL.md 直接引用" in issue.message
                    for issue in warnings
                ),
                [issue.render() for issue in warnings],
            )

    # 平台前提: 仅 POSIX 绝对路径的目标才会被判定为 skill 目录外.
    @unittest.skipIf(
        sys.platform == "win32",
        "Windows 绝对路径会走单独的警告分支, 不适用 POSIX 绝对路径断言",
    )
    def test_absolute_link_outside_skill_warns_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "outside.md"
            target.write_text("# 外部\n", encoding="utf-8")
            root = create_skill(directory, body="参考 [外部]({}).\n".format(target))
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [issue.render() for issue in warnings],
                ["SKILL.md:6: 绝对路径链接不可移植: {}".format(target)],
                [issue.render() for issue in warnings],
            )

    def test_link_outside_skill_dir_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "outside.md").write_text("# 外部\n", encoding="utf-8")
            root = create_skill(directory, body="参考 [外部](../outside.md).\n")
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    issue.render()
                    for issue in warnings
                    if "链接目标在 skill 目录外, 不可移植" in issue.message
                ],
                ["SKILL.md:6: 链接目标在 skill 目录外, 不可移植: ../outside.md"],
                [issue.render() for issue in warnings],
            )

    def test_reference_file_relative_only_link_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[b](b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(
                [
                    issue.render()
                    for issue in warnings
                    if "仅按所在文件目录可解析" in issue.message
                ],
                [
                    "references/a.md:1: 链接仅按所在文件目录可解析, "
                    "建议改为相对 skill 根目录: b.md"
                ],
                [issue.render() for issue in warnings],
            )

    def test_reference_root_relative_link_does_not_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/a.md": "[b](references/b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertFalse(
                any("仅按所在文件目录可解析" in issue.message for issue in warnings),
                [issue.render() for issue in warnings],
            )

    def test_skill_md_relative_link_does_not_warn_file_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/a.md": "# a\n"},
                body="[a](references/a.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertFalse(
                any("仅按所在文件目录可解析" in issue.message for issue in warnings),
                [issue.render() for issue in warnings],
            )

    def test_hidden_reference_file_links_are_not_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/.hidden.md": "# 隐藏\n\n[缺失](missing.md)\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_pycache_reference_file_links_are_not_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/__pycache__/cached.md": "[缺失](missing.md)\n"},
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_visible_reference_file_links_are_still_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={"references/visible.md": "# 可见\n\n[缺失](missing.md)\n"},
                body="[可见](references/visible.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(
                [issue.render() for issue in errors],
                ["references/visible.md:3: 本地链接目标不存在: missing.md"],
            )
            self.assertEqual(warnings, [])

    def test_hidden_and_pycache_reference_files_do_not_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "references/used.md": "# 已用\n",
                    "references/.hidden.md": "# 隐藏\n",
                    "references/__pycache__/cached.md": "# 缓存\n",
                },
                body="[已用](references/used.md)\n",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [], [issue.render() for issue in errors])
            self.assertEqual(warnings, [])

    def test_long_body_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body="x\n" * 501)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any("正文超过 500 行" in issue.message for issue in warnings)
            )
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertNotEqual(strict.returncode, 0)

    def test_body_line_limit_ignores_leading_blank_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body="x\n" * 499)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertFalse(
                any("正文超过 500 行" in issue.message for issue in warnings),
                [issue.render() for issue in warnings],
            )
            self.assertEqual(run_script(VALIDATOR_PATH, str(root)).returncode, 0)

        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory, body="x\n" * 500)
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertTrue(
                any("正文超过 500 行" in issue.message for issue in warnings)
            )
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertNotEqual(strict.returncode, 0)

    def test_missing_skill_file_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(any("缺少 SKILL.md" in issue.message for issue in errors))

    def test_unclosed_frontmatter_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: demo-skill\n", encoding="utf-8")
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(any("缺少结束标记" in issue.message for issue in errors))

    def test_block_scalar_with_indented_markers_keeps_full_description(self):
        frontmatter = (
            "name: demo-skill\n"
            "description: |\n"
            "  做演示.\n"
            "  ---\n"
            "  ...\n"
            "  在用户要求演示时使用.\n"
        )
        expected = "做演示.\n---\n...\n在用户要求演示时使用.\n"
        self.assertEqual(
            validator.parse_with_builtin(frontmatter, 2),
            {"name": "demo-skill", "description": expected},
        )
        if HAS_PYYAML:
            self.assertEqual(
                validator.parse_with_pyyaml(frontmatter, 2),
                {"name": "demo-skill", "description": expected},
            )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n" + frontmatter + "---\n\n## 流程\n\n1. 执行.\n",
                encoding="utf-8",
            )
            errors, warnings, parser = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertEqual(parser, "PyYAML" if HAS_PYYAML else "内置解析器")
            frontmatter_lines, _, _ = validator.split_frontmatter(
                (root / "SKILL.md").read_text(encoding="utf-8")
            )
            self.assertEqual(frontmatter_lines[-1], "  在用户要求演示时使用.")

    def test_empty_body_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: 做演示.\n---\n", encoding="utf-8"
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertTrue(any("正文不能为空" in issue.message for issue in errors))

    def test_verbose_reports_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory)
            result = run_script(VALIDATOR_PATH, str(root), "--verbose")
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = "PyYAML" if HAS_PYYAML else "内置解析器"
            self.assertIn("frontmatter 解析器: " + expected, result.stdout)

    def test_builtin_parser_runs_without_site_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(directory)
            result = run_script(
                VALIDATOR_PATH, str(root), "--verbose", python_options=("-S",)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("frontmatter 解析器: 内置解析器", result.stdout)

    def test_builtin_parser_accepts_quoted_keys_and_spaced_colons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n"
                "\"name\" : demo-skill\n"
                "'description': 做演示. 在用户要求演示时使用.\n"
                "\"license\" : MIT\n"
                "---\n\n## 流程\n\n1. 执行.\n",
                encoding="utf-8",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            result = run_script(VALIDATOR_PATH, str(root), python_options=("-S",))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("校验通过", result.stdout)

    def test_builtin_parser_rejects_unsupported_scalars_via_cli(self):
        cases = {
            "description: - a": "不支持序列或映射键形式的纯量",
            "description:\thello": "不支持制表符分隔",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "demo-skill"
                    root.mkdir()
                    (root / "SKILL.md").write_text(
                        "---\nname: demo-skill\n{}\n---\n\n## 流程\n\n1. 执行.\n".format(
                            line
                        ),
                        encoding="utf-8",
                    )
                    result = run_script(
                        VALIDATOR_PATH, str(root), python_options=("-S",)
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stdout + result.stderr)

    def test_builtin_parser_reports_quoted_key_line_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\n"
                "\"name\": demo-skill\n"
                "'description': 做演示. 在用户要求演示时使用.\n"
                "\"license\": 42\n"
                "---\n\n## 流程\n\n1. 执行.\n",
                encoding="utf-8",
            )
            result = run_script(VALIDATOR_PATH, str(root), python_options=("-S",))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SKILL.md:4: license 必须是字符串", result.stdout)

    def test_builtin_parser_rejects_non_string_metadata_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                extra_frontmatter="metadata:\n  true: value\n",
            )
            errors, _, parser = validator.validate_skill(root)
            self.assertEqual(parser, "PyYAML" if HAS_PYYAML else "内置解析器")
            self.assertTrue(
                any("metadata 的键必须是字符串" in issue.message for issue in errors)
            )
            result = run_script(VALIDATOR_PATH, str(root), python_options=("-S",))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "metadata 的键必须是字符串", result.stdout + result.stderr
            )

    def test_missing_name_or_description_is_error(self):
        cases = (
            ("description: 做演示. 在用户要求演示时使用.\n", "缺少 name 字段"),
            ("name: demo-skill\n", "缺少 description 字段"),
        )
        for frontmatter, expected in cases:
            with self.subTest(field=expected), tempfile.TemporaryDirectory() as directory:
                root = create_skill_with_frontmatter(directory, frontmatter)
                errors, warnings, _ = validator.validate_skill(root)
                self.assertEqual(
                    [issue.render() for issue in errors],
                    ["SKILL.md:2: {}".format(expected)],
                    [issue.render() for issue in errors],
                )
                self.assertEqual(warnings, [])
                result = run_script(VALIDATOR_PATH, str(root))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)
                self.assertIn("校验失败", result.stdout)

    def test_non_string_name_or_description_is_error(self):
        cases = (
            (
                "name: 123\ndescription: 做演示. 在用户要求演示时使用.\n",
                "SKILL.md:2: name 必须是字符串",
            ),
            (
                "name: demo-skill\ndescription: 123\n",
                "SKILL.md:3: description 必须是字符串",
            ),
        )
        for frontmatter, expected in cases:
            with self.subTest(issue=expected), tempfile.TemporaryDirectory() as directory:
                root = create_skill_with_frontmatter(directory, frontmatter)
                errors, warnings, _ = validator.validate_skill(root)
                self.assertEqual(
                    [issue.render() for issue in errors],
                    [expected],
                    [issue.render() for issue in errors],
                )
                self.assertEqual(warnings, [])
                result = run_script(VALIDATOR_PATH, str(root))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)
                self.assertIn("校验失败", result.stdout)

    def test_description_and_compatibility_length_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            exact = create_skill(
                directory, name="demo-skill", description="a" * 1024
            )
            errors, warnings, _ = validator.validate_skill(exact)
            self.assertEqual([issue.render() for issue in errors], [])
            self.assertEqual(warnings, [])
            result = run_script(VALIDATOR_PATH, str(exact))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            too_long = create_skill(
                directory,
                name="too-long",
                directory="too-long",
                description="a" * 1025,
            )
            errors, _, _ = validator.validate_skill(too_long)
            self.assertEqual(
                [issue.render() for issue in errors],
                [
                    "SKILL.md:3: description 不能超过 1024 字符, "
                    "当前为 1025 字符"
                ],
                [issue.render() for issue in errors],
            )
            result = run_script(VALIDATOR_PATH, str(too_long))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("description 不能超过 1024", result.stdout)

            compat_exact = create_skill(
                directory,
                name="compat-ok",
                directory="compat-ok",
                extra_frontmatter="compatibility: " + "a" * 500 + "\n",
            )
            errors, warnings, _ = validator.validate_skill(compat_exact)
            self.assertEqual([issue.render() for issue in errors], [])
            self.assertEqual(warnings, [])
            result = run_script(VALIDATOR_PATH, str(compat_exact), "--strict")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            compat_too_long = create_skill(
                directory,
                name="compat-long",
                directory="compat-long",
                extra_frontmatter="compatibility: " + "a" * 501 + "\n",
            )
            errors, _, _ = validator.validate_skill(compat_too_long)
            self.assertEqual(
                [issue.render() for issue in errors],
                [
                    "SKILL.md:4: compatibility 长度必须在 1-500 字符之间, "
                    "当前为 501 字符"
                ],
                [issue.render() for issue in errors],
            )
            result = run_script(VALIDATOR_PATH, str(compat_too_long))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("compatibility 长度", result.stdout)

    def test_pyc_hidden_and_top_level_files_do_not_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = create_skill(
                directory,
                files={
                    "scripts/stray.pyc": "binary\n",
                    "scripts/.hidden": "hidden\n",
                    "LICENSE": "MIT\n",
                },
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual([issue.render() for issue in errors], [])
            self.assertEqual([issue.render() for issue in warnings], [])
            result = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("校验通过", result.stdout)
            self.assertNotIn("警告", result.stdout)

    def test_strict_warning_categories_exit_codes(self):
        def non_standard_field(directory):
            return create_skill(directory, extra_frontmatter="vendor-field: true\n")

        def unreferenced_reference(directory):
            return create_skill(
                directory, files={"references/unused.md": "# 未用\n"}
            )

        def reference_cross_link(directory):
            return create_skill(
                directory,
                files={
                    "references/a.md": "[b](references/b.md)\n",
                    "references/b.md": "# b\n",
                },
                body="[a](references/a.md) [b](references/b.md)\n",
            )

        def link_outside_skill(directory):
            (Path(directory) / "outside.md").write_text("# 外部\n", encoding="utf-8")
            return create_skill(directory, body="参考 [外部](../outside.md).\n")

        cases = (
            ("非标准字段", non_standard_field, "非标准字段"),
            ("未被引用文件", unreferenced_reference, "未被 SKILL.md 直接引用"),
            ("参考互引", reference_cross_link, "参考文件互相引用"),
            ("目录外链接", link_outside_skill, "链接目标在 skill 目录外"),
        )
        for label, build, expected in cases:
            with self.subTest(category=label), tempfile.TemporaryDirectory() as directory:
                root = build(directory)
                errors, warnings, _ = validator.validate_skill(root)
                self.assertEqual([issue.render() for issue in errors], [])
                self.assertEqual(
                    len(warnings), 1, [issue.render() for issue in warnings]
                )
                self.assertIn(expected, warnings[0].message)

                default = run_script(VALIDATOR_PATH, str(root))
                self.assertEqual(
                    default.returncode, 0, default.stdout + default.stderr
                )
                self.assertIn("警告", default.stdout)
                self.assertIn("校验通过", default.stdout)

                strict = run_script(VALIDATOR_PATH, str(root), "--strict")
                self.assertEqual(strict.returncode, 1, strict.stdout + strict.stderr)
                self.assertIn("严格模式", strict.stdout)
                self.assertIn(expected, strict.stdout)


class InitSkillTests(unittest.TestCase):
    def test_normalize_name(self):
        cases = {
            "My_Skill  Name": "my-skill-name",
            "--Foo--": "foo",
            "A--B": "a-b",
            "a b_c": "a-b-c",
            "foo.bar": "foo-bar",
            "你好": "你好",
            "Café": "café",
            "ＡＢＣ": "abc",
            "!!!": "",
            "🙂": "",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(initializer.normalize_name(raw), expected)

    def test_create_skill_with_requested_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(
                INIT_PATH,
                "My_Skill",
                "--path",
                directory,
                "--scripts",
                "--references",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory) / "my-skill"
            self.assertTrue((root / "SKILL.md").is_file())
            self.assertTrue((root / "scripts").is_dir())
            self.assertTrue((root / "references").is_dir())
            self.assertFalse((root / "assets").exists())
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn('name: "my-skill"', text)
            self.assertIn('description: ""', text)

    def test_assets_directory_is_created_and_not_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(
                INIT_PATH,
                "demo-skill",
                "--path",
                directory,
                "--assets",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory) / "demo-skill"
            assets = root / "assets"
            self.assertTrue(assets.is_dir())
            self.assertEqual(list(assets.iterdir()), [])

            (assets / "logo.txt").write_text("logo", encoding="utf-8")
            skill_file = root / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8")
                .replace(
                    'description: ""',
                    "description: 处理演示数据. 在用户要求演示时使用.",
                )
                .replace(
                    "<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. "
                    "只填写 description 仍会因正文为空而校验失败. -->",
                    "## 流程\n\n1. 使用 assets/logo.txt.\n",
                ),
                encoding="utf-8",
            )
            errors, warnings, _ = validator.validate_skill(root)
            self.assertEqual([issue.message for issue in errors], [])
            self.assertEqual(
                [issue.message for issue in warnings if "assets" in issue.location], []
            )

            validation = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(validation.returncode, 0, validation.stdout)
            self.assertIn("校验通过", validation.stdout)
            self.assertNotIn("assets", validation.stdout)

    def test_generated_skill_fails_until_description_and_body_are_filled(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(INIT_PATH, "demo-skill", "--path", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory) / "demo-skill"
            skill_file = root / "SKILL.md"
            original = skill_file.read_text(encoding="utf-8")

            validation = run_script(VALIDATOR_PATH, str(root))
            self.assertNotEqual(validation.returncode, 0)
            self.assertIn("description 不能为空", validation.stdout)

            filled_description = original.replace(
                'description: ""',
                "description: 处理演示数据. 在用户要求演示时使用.",
            )
            skill_file.write_text(filled_description, encoding="utf-8")
            validation = run_script(VALIDATOR_PATH, str(root))
            self.assertNotEqual(validation.returncode, 0)
            self.assertIn("正文不能为空", validation.stdout)

            skill_file.write_text(
                filled_description.replace(
                    "<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. "
                    "只填写 description 仍会因正文为空而校验失败. -->",
                    "## 流程\n\n1. 执行.\n",
                ),
                encoding="utf-8",
            )
            validation = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(validation.returncode, 0, validation.stdout)
            self.assertIn("校验通过", validation.stdout)

    def test_invalid_name_creates_nothing(self):
        for raw in ("!!!", "🙂"):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                result = run_script(INIT_PATH, raw, "--path", directory)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("归一化后为空", result.stderr)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_unicode_name_is_created_and_passes_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(INIT_PATH, "技能", "--path", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory) / "技能"
            skill_file = root / "SKILL.md"
            text = skill_file.read_text(encoding="utf-8")
            self.assertIn('name: "技能"', text)
            skill_file.write_text(
                text.replace(
                    'description: ""',
                    "description: 处理中文任务. 在用户要求时使用.",
                ).replace(
                    "<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. "
                    "只填写 description 仍会因正文为空而校验失败. -->",
                    "## 流程\n\n1. 执行.\n",
                ),
                encoding="utf-8",
            )
            errors, _, _ = validator.validate_skill(root)
            self.assertEqual([issue.message for issue in errors], [])

    def test_yaml_reserved_and_numeric_names_stay_strings(self):
        names = (
            "yes",
            "no",
            "on",
            "off",
            "true",
            "false",
            "null",
            "123",
            "0x1f",
            "0777",
            "0b11",
        )
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                result = run_script(INIT_PATH, name, "--path", directory)
                self.assertEqual(result.returncode, 0, result.stderr)
                root = Path(directory) / name
                skill_file = root / "SKILL.md"
                text = skill_file.read_text(encoding="utf-8")
                self.assertIn('name: "{}"'.format(name), text)

                frontmatter = text.split("---", 2)[1].strip("\n")
                parsed, _ = validator.parse_frontmatter(frontmatter)
                self.assertIsInstance(parsed["name"], str)
                self.assertEqual(parsed["name"], name)
                builtin = validator.parse_with_builtin(frontmatter)
                self.assertIsInstance(builtin["name"], str)
                self.assertEqual(builtin["name"], name)

                skill_file.write_text(
                    text.replace(
                        'description: ""',
                        "description: 处理保留字名称. 在用户要求时使用.",
                    ).replace(
                        "<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. "
                        "只填写 description 仍会因正文为空而校验失败. -->",
                        "## 流程\n\n1. 执行.\n",
                    ),
                    encoding="utf-8",
                )
                errors, _, _ = validator.validate_skill(root)
                messages = [issue.message for issue in errors]
                self.assertNotIn("name 必须是字符串", messages)
                self.assertNotIn("缺少 name 字段", messages)
                self.assertEqual(messages, [])

    def test_existing_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-skill"
            root.mkdir()
            (root / "SKILL.md").write_text("original", encoding="utf-8")
            result = run_script(INIT_PATH, "demo-skill", "--path", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("不覆盖", result.stderr)
            self.assertEqual((root / "SKILL.md").read_text(encoding="utf-8"), "original")

    def test_name_too_long_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(INIT_PATH, "a" * 65, "--path", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_reports_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_script(INIT_PATH, "My_Skill", "--path", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("归一化", result.stdout)
            self.assertIn("My_Skill", result.stdout)
            self.assertIn("my-skill", result.stdout)
            self.assertIn("已创建", result.stdout)
            self.assertIn("下一步", result.stdout)

    def test_name_rules_match_between_init_and_validator(self):
        raw_names = (
            "A--B",
            "a" * 64,
            "a" * 65,
            "-demo",
            "demo-",
            "a_b",
            "demo--skill",
            "你好",
            "Café",
            "ＡＢＣ",
            "技能",
            "!!!",
            "🙂",
        )
        for raw in raw_names:
            with self.subTest(raw=raw):
                normalized = initializer.normalize_name(raw)
                init_accepts = initializer.validate_name(normalized) is None
                if normalized == "":
                    self.assertFalse(init_accepts)
                    continue

                with tempfile.TemporaryDirectory() as directory:
                    root = create_skill(
                        directory, name=normalized, directory=normalized
                    )
                    errors, _, _ = validator.validate_skill(root)
                    name_errors = [
                        issue for issue in errors if issue.message.startswith("name")
                    ]
                    self.assertEqual(
                        init_accepts,
                        not name_errors,
                        "名称规则不一致: {!r} -> {!r}, errors={}".format(
                            raw,
                            normalized,
                            [issue.message for issue in name_errors],
                        ),
                    )


class EndToEndTests(unittest.TestCase):
    def test_init_fill_validate_and_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            init = run_script(
                INIT_PATH,
                "sample-skill",
                "--path",
                directory,
                "--scripts",
                "--references",
                "--assets",
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            root = Path(directory) / "sample-skill"
            skill_file = root / "SKILL.md"
            text = skill_file.read_text(encoding="utf-8").replace(
                'description: ""',
                "description: 处理样例数据. 在用户要求处理样例数据时使用.",
            )
            text = text.replace(
                "<!-- TODO: 先填写上方 description, 再在这里写正文并删除本行. "
                "只填写 description 仍会因正文为空而校验失败. -->",
                "## 流程\n\n1. 读取输入. 参考 [说明](references/note.md).\n",
            )
            self.assertNotIn("TODO", text)
            skill_file.write_text(text, encoding="utf-8")
            (root / "references/note.md").write_text(
                "# 说明\n\n参见 [流程](SKILL.md).\n", encoding="utf-8"
            )

            default = run_script(VALIDATOR_PATH, str(root))
            strict = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(default.returncode, 0, default.stdout)
            self.assertEqual(strict.returncode, 0, strict.stdout)
            self.assertNotIn("警告", default.stdout)

            final_text = skill_file.read_text(encoding="utf-8")
            self.assertNotIn("TODO: 先填写上方 description", final_text)
            self.assertIn("## 流程", final_text)

            builtin = run_script(
                VALIDATOR_PATH, str(root), "--strict", python_options=("-S",)
            )
            self.assertEqual(builtin.returncode, 0, builtin.stdout)
            self.assertNotIn("警告", builtin.stdout)

    def test_filled_skill_passes_with_scaffold_todo_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            init = run_script(INIT_PATH, "demo-skill", "--path", directory)
            self.assertEqual(init.returncode, 0, init.stderr)
            root = Path(directory) / "demo-skill"
            skill_file = root / "SKILL.md"
            text = skill_file.read_text(encoding="utf-8").replace(
                'description: ""',
                "description: 处理演示数据. 在用户要求演示时使用.",
            )
            self.assertIn("TODO: 先填写上方 description", text)
            skill_file.write_text(
                text + "\n## 流程\n\n1. 执行.\n", encoding="utf-8"
            )

            validation = run_script(VALIDATOR_PATH, str(root), "--strict")
            self.assertEqual(validation.returncode, 0, validation.stdout)

            final_text = skill_file.read_text(encoding="utf-8")
            self.assertIn("TODO: 先填写上方 description", final_text)
            self.assertIn("## 流程", final_text)


DOCUMENTATION_FILES = (
    ROOT / "README.md",
    ROOT / "docs/skill-creator.md",
    ROOT / "skills/skill-creator/SKILL.md",
    *sorted((ROOT / "skills/skill-creator/references").glob("*.md")),
)

REQUIRED_SKILL_SECTIONS = (
    "适用与门槛",
    "意图收集",
    "内容去向",
    "描述与触发",
    "正文与自由度",
    "脚手架与校验",
    "验证",
    "改进现有 skill",
    "交付说明",
    "操作边界",
)

HARD_CONSTRAINT_NUMBER_PATTERN = re.compile(r"(?<![0-9])(?:64|1024|500|5000)(?![0-9])")
NAME_PATTERN_FORMS = (
    re.compile(r"\bNAME_PATTERN\b"),
    re.compile(r"\ba-z0-9\b"),
    re.compile(r"\[[^\]\n]*a-z[^\]\n]*\]"),
)
INLINE_LINK_PATTERN = re.compile(
    r"(?<!!)\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^()\s]+)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)


def skill_body(text):
    """去掉 SKILL.md 的 frontmatter, 返回正文."""
    match = re.match(r"\A---\n.*?\n---\n", text, re.DOTALL)
    return text[match.end():] if match else text


def prose_lines(markdown):
    """去掉围栏代码块后逐行返回, 用于检查正文 prose 约束."""
    lines = []
    fence = None
    for line in markdown.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is None:
            if marker:
                fence = marker.group(1)
            else:
                lines.append(line)
        elif (
            marker
            and marker.group(1)[0] == fence[0]
            and len(marker.group(1)) >= len(fence)
        ):
            fence = None
    return lines


def prose(markdown):
    return "\n".join(prose_lines(markdown))


def level_two_headings(markdown):
    return [
        match.group(1).strip()
        for line in prose_lines(markdown)
        if (match := re.match(r"^ {0,3}##[ \t]+(.+?)[ \t]*$", line))
    ]


def relative_link_targets(markdown):
    """返回正文中的相对链接目标 (外部链接, 纯锚点, 绝对路径已排除)."""
    targets = []
    for match in INLINE_LINK_PATTERN.finditer(prose(markdown)):
        target = match.group(1)
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        target = target.split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("/", "//")):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        targets.append(target)
    return targets


def relative_link_fragments(markdown):
    """返回相对链接的 (目标文件, fragment) 对 (外部链接与纯锚点已排除)."""
    references = []
    for match in INLINE_LINK_PATTERN.finditer(prose(markdown)):
        target = match.group(1)
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        location, _, fragment = target.partition("#")
        location = location.split("?", 1)[0]
        if not location or location.startswith(("/", "//")):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", location):
            continue
        references.append((location, fragment))
    return references


def github_heading_anchor(heading):
    """按 GitHub 风格生成标题锚点: 小写, 去标点, 空格转 `-`, 保留 Unicode."""
    text = heading.strip().lower()
    text = re.sub(r"`([^`\n]*)`", r"\1", text)
    text = re.sub(r"\[([^\]\n]*)\]\([^)\n]*\)", r"\1", text)
    characters = [char for char in text if char.isalnum() or char in " -_"]
    return "".join(characters).replace(" ", "-")


def heading_anchors(markdown):
    """返回正文 ATX 标题的锚点集合, 重复标题按 `-1`, `-2` 后缀区分."""
    anchors = set()
    seen = {}
    for line in prose_lines(markdown):
        match = re.match(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", line)
        if not match:
            continue
        heading = re.sub(r"[ \t]+#+$", "", match.group(1))
        base = github_heading_anchor(heading)
        if base in seen:
            seen[base] += 1
            anchor = "{}-{}".format(base, seen[base])
        else:
            seen[base] = 0
            anchor = base
        anchors.add(anchor)
    return anchors


class DocumentationContractTests(unittest.TestCase):
    def test_skill_sections_keep_required_order(self):
        body = skill_body(
            (ROOT / "skills/skill-creator/SKILL.md").read_text(encoding="utf-8")
        )
        headings = level_two_headings(body)
        for section in REQUIRED_SKILL_SECTIONS:
            self.assertIn(section, headings)
        positions = [headings.index(section) for section in REQUIRED_SKILL_SECTIONS]
        self.assertEqual(positions, sorted(positions))

    def test_skill_body_omits_hard_constraint_numbers(self):
        body = skill_body(
            (ROOT / "skills/skill-creator/SKILL.md").read_text(encoding="utf-8")
        )
        matches = HARD_CONSTRAINT_NUMBER_PATTERN.findall(prose(body))
        self.assertEqual(matches, [], "正文不应复制硬约束数字: {}".format(matches))

    def test_skill_body_omits_name_pattern(self):
        body = skill_body(
            (ROOT / "skills/skill-creator/SKILL.md").read_text(encoding="utf-8")
        )
        text = prose(body)
        for pattern in NAME_PATTERN_FORMS:
            match = pattern.search(text)
            self.assertIsNone(match, "正文不应包含名称正则: {}".format(match and match.group(0)))

    def test_document_relative_links_exist(self):
        for document in DOCUMENTATION_FILES:
            text = document.read_text(encoding="utf-8")
            for target in relative_link_targets(text):
                with self.subTest(document=str(document), target=target):
                    resolved = (document.parent / target).resolve()
                    self.assertTrue(
                        resolved.exists(),
                        "{} 中的链接目标不存在: {}".format(document, target),
                    )

    def test_heading_anchor_generation_matches_github_style(self):
        markdown = (
            "# skills\n\n"
            "## skills 列表\n\n"
            "### 校验脚本覆盖的检查\n\n"
            "## 1. 描述公式\n\n"
            "## 重复\n\n"
            "## 重复\n\n"
            "```markdown\n"
            "## 围栏内标题\n"
            "```\n"
        )
        self.assertEqual(
            heading_anchors(markdown),
            {"skills", "skills-列表", "校验脚本覆盖的检查", "1-描述公式", "重复", "重复-1"},
        )

    def test_document_relative_link_anchors_exist(self):
        checked = set()
        for document in DOCUMENTATION_FILES:
            text = document.read_text(encoding="utf-8")
            for target, fragment in relative_link_fragments(text):
                if not fragment:
                    continue
                with self.subTest(
                    document=str(document), target=target, fragment=fragment
                ):
                    resolved = (document.parent / target).resolve()
                    self.assertTrue(
                        resolved.exists(),
                        "{} 中的链接目标不存在: {}#{}".format(
                            document, target, fragment
                        ),
                    )
                    anchors = heading_anchors(resolved.read_text(encoding="utf-8"))
                    self.assertIn(
                        fragment,
                        anchors,
                        "{} 中的链接锚点不存在: {}#{} (可用锚点: {})".format(
                            document, target, fragment, sorted(anchors)
                        ),
                    )
                    checked.add(
                        (resolved.relative_to(ROOT).as_posix(), fragment)
                    )
        expected = {
            ("README.md", "skills-列表"),
            ("skills/skill-creator/references/spec.md", "目录结构"),
            ("skills/skill-creator/references/spec.md", "校验脚本覆盖的检查"),
        }
        self.assertTrue(
            expected <= checked,
            "锚点校验未覆盖: {}".format(sorted(expected - checked)),
        )

    def test_documentation_checks_detect_regressions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "doc.md"
            document.write_text(
                "# 标题\n\n## 操作边界\n\n## 适用与门槛\n\n"
                "长度 64 字符, 匹配 `[a-z0-9]`.\n\n"
                "[外链](https://example.com) [锚点](#标题) "
                "[缺失](missing.md)\n\n"
                "```markdown\n[围栏内](also-missing.md)\n```\n",
                encoding="utf-8",
            )
            body = document.read_text(encoding="utf-8")
            self.assertEqual(level_two_headings(body), ["操作边界", "适用与门槛"])
            self.assertEqual(
                HARD_CONSTRAINT_NUMBER_PATTERN.findall(prose(body)), ["64"]
            )
            self.assertTrue(
                any(p.search(prose(body)) for p in NAME_PATTERN_FORMS)
            )
            self.assertEqual(relative_link_targets(body), ["missing.md"])
            self.assertFalse((document.parent / "missing.md").exists())


if __name__ == "__main__":
    unittest.main()
