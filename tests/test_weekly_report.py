"""验证周报失败处理与真实渲染结果."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("weekly_report", ROOT / "skills/weekly-report/scripts/render.py")
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def sample(items=None):
    return {"year": 2026, "semester": "春季", "week": 3, "items": items or ["完成开发与验证"]}


class WeeklyReportTests(unittest.TestCase):
    def test_invalid_input_stops_before_running_typst(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(report, "check_environment") as check:
            for change in ({"week": True}, {"year": 0}, {"semester": "暑期"}, {"items": []}):
                with self.subTest(change=change), self.assertRaises(report.ReportError):
                    report.render_report(dict(sample(), **change), directory)
            check.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_existing_multi_page_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(report, "check_environment") as check:
            existing = Path(directory) / "weekly-report-2026春-第3周-第2页.png"
            existing.write_bytes(b"original")
            with self.assertRaises(report.ReportError):
                report.render_report(sample(), directory)
            check.assert_not_called()
            self.assertEqual(existing.read_bytes(), b"original")

    def test_compile_failure_delivers_nothing(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            report, "check_environment", return_value="typst"
        ), patch.object(report, "run_typst", side_effect=report.ReportError("编译失败")):
            with self.assertRaisesRegex(report.ReportError, "编译失败"):
                report.render_report(sample(), directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_publish_conflict_rolls_back_only_new_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.write_bytes(b"new")
            existing = root / "existing"
            existing.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                report.publish_files([(source, "first"), (source, "existing")], root)
            self.assertFalse((root / "first").exists())
            self.assertEqual(existing.read_bytes(), b"original")

    def test_environment_rejects_old_typst_and_missing_font(self):
        with patch.object(report.shutil, "which", return_value="typst"):
            with patch.object(report, "run_typst", return_value="typst 0.12.0"):
                with self.assertRaisesRegex(report.ReportError, "0.13"):
                    report.check_environment()
            with patch.object(report, "run_typst", side_effect=["typst 0.15.1", "Other Font"]):
                with self.assertRaisesRegex(report.ReportError, "缺少字体"):
                    report.check_environment()


@unittest.skipUnless(os.environ.get("RUN_TYPST_TESTS") == "1", "真实渲染需设置 RUN_TYPST_TESTS=1")
class TypstIntegrationTests(unittest.TestCase):
    def test_literals_round_trip_and_standalone_source(self):
        items = ['普通中文 #issue $HOME *星号* _下划线_ [括号] @引用 "引号"',
                 'C:\\data\\file.txt\n第二行\t内容']
        with tempfile.TemporaryDirectory() as directory:
            result = report.render_report(sample(items), directory)
            self.assertEqual(result["pages"], 1)
            self.assertEqual({Path(p).suffix for p in result["files"]}, {".typ", ".png"})
            source = Path(result["files"][0])
            source.write_text(source.read_text() + '\n#metadata(report.items) <items>\n', encoding="utf-8")
            queried = subprocess.check_output(["typst", "query", str(source), "<items>", "--field", "value"], text=True)
            self.assertEqual(json.loads(queried), [items])
            subprocess.run(["typst", "compile", str(source), str(Path(directory) / "independent.png"),
                            "--format", "png", "--ppi", "300"], check=True, capture_output=True)

    def test_all_pages_are_delivered_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            result = report.render_report(sample([f"第 {i} 项: 完成开发与验证." for i in range(100)]), directory)
            self.assertGreater(result["pages"], 1)
            self.assertEqual(len(list(Path(directory).iterdir())), result["pages"] + 1)
            for index, file in enumerate(result["files"][1:], 1):
                self.assertTrue(file.endswith(f"-第{index}页.png"))


if __name__ == "__main__":
    unittest.main()
