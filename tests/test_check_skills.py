"""使用临时仓库验证规范检查, 不依赖真实仓库中的错误."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_skills.py"
SPEC = importlib.util.spec_from_file_location("check_skills", SCRIPT)
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class CheckSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write("skills/example/SKILL.md", "---\nname: example\ndescription: 示例技能.\n---\n\n# 示例\n\n+ 正文.\n")
        self.write("docs/example.md", "# 使用说明\n\n[入口](../skills/example/SKILL.md)\n")
        self.registry = "# 项目\n\n## skills 列表\n\n+ example: 示例 [具体文档](docs/example.md)\n"
        self.write("README.md", self.registry)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def errors(self):
        return checks.Checker(self.root).run()

    def assert_rule(self, rule):
        errors = self.errors()
        self.assertTrue(any(f": {rule}:" in error for error in errors), errors)

    def test_valid_repository(self):
        self.assertEqual(self.errors(), [])

    def test_missing_usage_doc(self):
        (self.root / "docs/example.md").unlink()
        self.assert_rule("usage-doc")

    def test_missing_entrypoint(self):
        (self.root / "skills/example/SKILL.md").unlink()
        self.assert_rule("entrypoint")

    def test_missing_registry_entry(self):
        self.write("README.md", "## skills 列表\n")
        self.assert_rule("registry")

    def test_registry_entry_outside_section_does_not_count(self):
        self.write("README.md", "## skills 列表\n\n## 其他\n\n+ example: 示例 [具体文档](docs/example.md)\n")
        self.assert_rule("registry")

    def test_duplicate_registry_entry(self):
        self.write("README.md", self.registry + "+ example: 重复 [具体文档](docs/example.md)\n")
        self.assert_rule("registry")

    def test_wrong_document_mapping(self):
        self.write("docs/another.md", "# 其他文档\n")
        self.write("README.md", self.registry.replace("docs/example.md", "docs/another.md"))
        self.assert_rule("registry")

    def test_malformed_and_duplicate_frontmatter(self):
        for text in ["# 无元数据\n", "---\nname: [\n---\n", "---\nname: example\nname: example\ndescription: 示例\n---\n"]:
            with self.subTest(text=text):
                self.write("skills/example/SKILL.md", text)
                self.assert_rule("frontmatter")

    def test_empty_description_and_name_mismatch(self):
        self.write("skills/example/SKILL.md", '---\nname: different\ndescription: ""\n---\n')
        self.assert_rule("skill-name")
        self.assert_rule("description")

    def test_unicode_punctuation_in_prose_and_description(self):
        self.write("docs/example.md", "# 使用说明\n\n这里有中文逗号\uff0c以及句号\u3002\n")
        self.assert_rule("ascii-punctuation")
        self.write("docs/example.md", "# 使用说明\n")
        self.write("skills/example/SKILL.md", "---\nname: example\ndescription: 示例\u3002\n---\n")
        self.assert_rule("ascii-punctuation")

    def test_wrong_list_markers_in_nested_lists_and_quotes(self):
        for text in ["- 错误列表\n", "+ 外层\n  * 错误内层\n", "> - 引用中的列表\n"]:
            with self.subTest(text=text):
                self.write("docs/example.md", text)
                self.assert_rule("list-marker")

    def test_missing_local_link_and_image(self):
        for text in ["[缺失](missing.md)", "![图片](missing.png)", "[引用][target]\n\n[target]: missing.md"]:
            with self.subTest(text=text):
                self.write("docs/example.md", text)
                self.assert_rule("local-link")

    def test_heading_anchors_and_encoded_paths(self):
        self.write("docs/space name.md", "# 中文标题\n\n## 重复\n\n## 重复\n")
        self.write("docs/example.md", "[标题](space%20name.md#中文标题)\n\n[重复](space%20name.md#重复-1)\n")
        self.assertEqual(self.errors(), [])
        self.write("docs/example.md", "[标题](space%20name.md#不存在)\n")
        self.assert_rule("local-anchor")

    def test_fenced_indented_and_inline_code_are_excluded(self):
        self.write("docs/example.md", """# 示例

`[示例](missing.md)` 和 `\u300c原文\u300d`.

```markdown
- 示例\uff0c [文件](missing.md)
```

~~~typst
- 示例\u3002
~~~

    - 缩进代码\uff0c [文件](missing.md)

+ 正常列表.

[外部链接](https://example.com/路径?text=\uff0c)
""")
        self.assertEqual(self.errors(), [])

    def test_cli_reports_errors_and_exit_status(self):
        (self.root / "docs/example.md").unlink()
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/example.md:1: usage-doc:", result.stderr)


if __name__ == "__main__":
    unittest.main()
