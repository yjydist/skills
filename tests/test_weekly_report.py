"""验证周报失败处理与真实渲染结果."""

import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("weekly_report", ROOT / "skills/weekly-report/scripts/render.py")
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def sample(**change):
    base = {
        "kind": "周报", "year": 2026, "month": 3, "nth": 2,
        "name": "常瑞", "student_id": "25031212280",
        "start": "2026.3.2", "end": "2026.3.8",
        "contributions": ["查看和对比实验室主机的硬件设备"],
        "research": ["读师兄师姐的大论文，积累综述的素材"],
        "service": "无", "exercise": "日常锻炼", "reflection": "无", "lesson": "无",
        "attendance_hours": "5.5", "attendance_early": "5",
        "self_evaluation": "满意",
    }
    base.update(change)
    return base


class WeeklyReportTests(unittest.TestCase):
    def test_invalid_input_stops_before_running_typst(self):
        monthly = sample(kind="月报")
        del monthly["nth"]
        cases = (
            sample(nth=True), sample(year=0), sample(month=13), sample(kind="季报"),
            sample(contributions=[]), sample(research=[""]), sample(self_evaluation="一般"),
            sample(attendance_hours=" "), sample(extra=1), dict(monthly, nth=1),
            {key: value for key, value in sample().items() if key != "name"},
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(report, "check_environment") as check:
            for case in cases:
                with self.subTest(case=case), self.assertRaises(report.ReportError):
                    report.render_report(case, directory)
            check.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_existing_multi_page_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(report, "check_environment") as check:
            existing = Path(directory) / "weekly-report-2026年3月第2次-第2页.png"
            existing.write_bytes(b"original")
            with self.assertRaises(report.ReportError):
                report.render_report(sample(), directory)
            check.assert_not_called()
            self.assertEqual(existing.read_bytes(), b"original")

    def test_compile_failure_delivers_nothing(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            report, "check_environment", return_value=("typst", None)
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
            with self.assertRaisesRegex(report.ReportError, "existing"):
                report.publish_files([(source, "first"), (source, "existing")], root)
            self.assertFalse((root / "first").exists())
            self.assertEqual(existing.read_bytes(), b"original")

    def test_environment_rejects_old_typst(self):
        with patch.object(report.shutil, "which", return_value="typst"):
            with patch.object(report, "run_typst", return_value="typst 0.12.0"):
                with self.assertRaisesRegex(report.ReportError, "0.13"):
                    report.check_environment()

    def test_environment_allows_missing_fonts(self):
        with patch.object(report.shutil, "which", return_value="typst"), patch.object(
            report, "run_typst", side_effect=["typst 0.15.1", "Other Font"]
        ), patch("sys.stderr", new_callable=io.StringIO) as stderr:
            path, note = report.check_environment()
            self.assertEqual(path, "typst")
            self.assertIsNotNone(note)
            self.assertIn("Alimama", note)
            self.assertTrue(stderr.getvalue().startswith("提示: "))

    def test_environment_reports_no_note_when_fonts_present(self):
        with patch.object(report.shutil, "which", return_value="typst"), patch.object(
            report, "run_typst", side_effect=["typst 0.15.1", "Alimama FangYuanTi"]
        ):
            self.assertEqual(report.check_environment(), ("typst", None))

    def test_build_source_selects_template_by_kind(self):
        weekly = report.build_source(sample())
        self.assertIn("  nth:", weekly)
        self.assertIn("次周报", weekly)
        monthly = sample(kind="月报")
        del monthly["nth"]
        source = report.build_source(monthly)
        self.assertNotIn("  nth:", source)
        self.assertNotIn("report.nth", source)
        self.assertIn("月月报", source)

    def test_output_path_must_be_directory(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(report, "check_environment") as check:
            target = Path(directory) / "output"
            target.write_text("not a directory", encoding="utf-8")
            with self.assertRaisesRegex(report.ReportError, "不是目录"):
                report.render_report(sample(), target)
            check.assert_not_called()

    def test_stdin_input_is_rendered_once(self):
        with patch.object(report.sys, "argv", ["render.py", "--input", "-"]), patch(
            "sys.stdin", io.StringIO(json.dumps(sample(), ensure_ascii=False))
        ), patch.object(report, "render_report", return_value={"pages": 1}) as render:
            self.assertEqual(report.main(), 0)
            render.assert_called_once()
            self.assertEqual(render.call_args.args[0], sample())

    def test_stdin_invalid_input_reports_failure(self):
        with patch.object(report.sys, "argv", ["render.py", "--input", "-"]), patch(
            "sys.stdin", io.StringIO('{"kind": "周报"}')
        ), patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(report.main(), 1)
            self.assertTrue(stderr.getvalue().startswith("周报生成失败: "))

    def test_font_note_is_passed_through(self):
        def fake_run(command):
            work = Path(command[2]).parent
            payload = (
                b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
                + struct.pack(">II", 2480, 3508) + b"\x08\x06\x00\x00\x00"
            )
            (work / "page-1.png").write_bytes(payload)
            return ""

        with tempfile.TemporaryDirectory() as directory, patch.object(
            report, "check_environment", return_value=("typst", "字体缺失提示")
        ), patch.object(report, "run_typst", side_effect=fake_run):
            result = report.render_report(sample(), directory)
            self.assertEqual(result["font_note"], "字体缺失提示")
            self.assertEqual(result["pages"], 1)

    def test_typst_string_rejects_non_string(self):
        for value in (1, 5.5, None):
            with self.subTest(value=value), self.assertRaisesRegex(report.ReportError, "字符串"):
                report.typst_string(value)


@unittest.skipUnless(os.environ.get("RUN_TYPST_TESTS") == "1", "真实渲染需设置 RUN_TYPST_TESTS=1")
class TypstIntegrationTests(unittest.TestCase):
    def test_literals_round_trip_and_standalone_source(self):
        items = ['普通中文 #issue $HOME *星号* _下划线_ [括号] @引用 "引号"',
                 'C:\\data\\file.txt\n第二行\t内容']
        with tempfile.TemporaryDirectory() as directory:
            result = report.render_report(sample(research=items), directory)
            self.assertEqual(result["pages"], 1)
            self.assertIsNone(result["font_note"])
            self.assertEqual({Path(p).suffix for p in result["files"]}, {".typ", ".png"})
            source = Path(result["files"][0])
            source.write_text(source.read_text() + '\n#metadata(report.research) <items>\n', encoding="utf-8")
            queried = subprocess.check_output(["typst", "query", str(source), "<items>", "--field", "value"], text=True)
            self.assertEqual(json.loads(queried), [items])
            subprocess.run(["typst", "compile", str(source), str(Path(directory) / "independent.png"),
                            "--format", "png", "--ppi", "300"], check=True, capture_output=True)

    def test_all_pages_are_delivered_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            result = report.render_report(sample(research=[f"第 {i} 项: 完成开发与验证." for i in range(100)]), directory)
            self.assertGreater(result["pages"], 1)
            self.assertEqual(len(list(Path(directory).iterdir())), result["pages"] + 1)
            for index, file in enumerate(result["files"][1:], 1):
                self.assertTrue(file.endswith(f"-第{index}页.png"))


if __name__ == "__main__":
    unittest.main()
