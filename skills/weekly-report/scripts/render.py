#!/usr/bin/env python3
"""将周报或月报 JSON 渲染为独立 Typst 源文件和 A4 PNG 图片."""

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


FONT = "Alimama FangYuanTi"
TEMPLATE = Path(__file__).resolve().parents[1] / "template.typ"
START = "// REPORT_DATA_START"
END = "// REPORT_DATA_END"


KINDS = ("周报", "月报")
EVALUATIONS = ("非常满意", "满意", "不太满意")
REQUIRED = (
    "kind", "year", "month", "name", "student_id", "start", "end",
    "contributions", "research", "service", "exercise", "reflection", "lesson",
    "attendance_hours", "attendance_early", "self_evaluation",
)


class ReportError(Exception):
    """可以直接向用户报告的输入或渲染错误."""


def validate_report(report):
    if not isinstance(report, dict):
        raise ReportError("输入必须是 JSON 对象.")
    missing = [key for key in REQUIRED if key not in report]
    unknown = sorted(set(report) - set(REQUIRED) - {"nth"})
    if missing or unknown:
        problems = []
        if missing:
            problems.append("缺少字段: " + ", ".join(missing))
        if unknown:
            problems.append("未知字段: " + ", ".join(unknown))
        raise ReportError("; ".join(problems) + ".")
    if report["kind"] not in KINDS:
        raise ReportError('kind 必须是 "周报" 或 "月报".')
    if report["kind"] == "周报":
        if type(report.get("nth")) is not int or report["nth"] < 1:
            raise ReportError("周报的 nth 必须是正整数, 表示当月第几次周报.")
    elif "nth" in report:
        raise ReportError("月报不包含 nth 字段.")
    if type(report["year"]) is not int or not 1 <= report["year"] <= 9999:
        raise ReportError("year 必须是 1 至 9999 之间的整数.")
    if type(report["month"]) is not int or not 1 <= report["month"] <= 12:
        raise ReportError("month 必须是 1 至 12 之间的整数.")
    for key in ("name", "student_id", "start", "end",
                "service", "exercise", "reflection", "lesson"):
        if not isinstance(report[key], str) or not report[key].strip():
            raise ReportError(key + " 必须是非空字符串.")
    for key in ("contributions", "research"):
        items = report[key]
        if not isinstance(items, list) or not items or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ReportError(key + " 必须是非空字符串数组, 每条至少包含一个非空白字符.")
    for key in ("attendance_hours", "attendance_early"):
        value = report[key]
        if isinstance(value, str):
            if not value.strip():
                raise ReportError(key + " 不能为空字符串.")
        elif type(value) in (int, float):
            report[key] = format(value, "g")
        else:
            raise ReportError(key + " 必须是非空字符串或数字.")
    if report["self_evaluation"] not in EVALUATIONS:
        raise ReportError('self_evaluation 必须是 "非常满意", "满意" 或 "不太满意".')
    return report


def typst_string(value):
    escapes = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    return '"' + "".join(
        escapes.get(char, "\\u{" + format(ord(char), "x") + "}" if ord(char) < 32 else char)
        for char in value
    ) + '"'


def build_source(report):
    validate_report(report)
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count(START) != 1 or template.count(END) != 1:
        raise ReportError("模板必须包含唯一的数据块起止标记.")
    before, body = template.split(START)
    _, after = body.split(END)

    def array(items):
        return "(\n" + "\n".join(
            "    " + typst_string(item) + "," for item in items
        ) + "\n  )"

    fields = [
        ("kind", typst_string(report["kind"])),
        ("year", str(report["year"])),
        ("month", str(report["month"])),
    ]
    if report["kind"] == "周报":
        fields.append(("nth", str(report["nth"])))
    fields += [
        ("name", typst_string(report["name"])),
        ("student_id", typst_string(report["student_id"])),
        ("start", typst_string(report["start"])),
        ("end", typst_string(report["end"])),
        ("contributions", array(report["contributions"])),
        ("research", array(report["research"])),
        ("service", typst_string(report["service"])),
        ("exercise", typst_string(report["exercise"])),
        ("reflection", typst_string(report["reflection"])),
        ("lesson", typst_string(report["lesson"])),
        ("attendance_hours", typst_string(report["attendance_hours"])),
        ("attendance_early", typst_string(report["attendance_early"])),
        ("self_evaluation", typst_string(report["self_evaluation"])),
    ]
    data = "\n#let report = (\n" + "\n".join(
        "  " + key + ": " + value + "," for key, value in fields
    ) + "\n)\n"
    return before + START + data + END + after


def run_typst(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise ReportError(result.stderr.strip() or result.stdout.strip() or "Typst 执行失败.")
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.stdout


def check_environment():
    executable = shutil.which("typst")
    if not executable:
        raise ReportError("未找到 typst, 需要 Typst 0.13 或更高版本.")
    version = run_typst([executable, "--version"])
    match = re.search(r"typst (\d+)\.(\d+)\.(\d+)", version)
    if not match or tuple(map(int, match.groups())) < (0, 13, 0):
        raise ReportError("需要 Typst 0.13 或更高版本, 当前为: " + version.strip())
    if FONT not in run_typst([executable, "fonts"]).splitlines():
        raise ReportError("缺少字体: " + FONT + ". 请安装后重新运行, 不自动替换字体.")
    return executable


def check_conflicts(output_dir, stem):
    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise ReportError("输出路径不是目录: " + str(output_dir))
    pattern = re.compile(re.escape(stem) + r"(?:\.typ|\.png|-第\d+页\.png)$")
    conflicts = sorted(path.name for path in output_dir.iterdir() if pattern.fullmatch(path.name))
    if conflicts:
        raise ReportError("已有同名周报产物, 请选择其他目录或先处理原文件: " + ", ".join(conflicts))


def publish_files(files, output_dir):
    """独占创建目标文件; 发布失败时只移除本次新建的文件."""
    created = []
    try:
        for source, name in files:
            destination = output_dir / name
            with destination.open("xb") as target:
                created.append(destination)
                with source.open("rb") as data:
                    shutil.copyfileobj(data, target)
    except OSError:
        for path in created:
            path.unlink()
        raise
    return created


def render_report(report, output_dir):
    source = build_source(report)
    period = f'{report["year"]}年{report["month"]}月'
    if report["kind"] == "周报":
        stem = f"weekly-report-{period}第{report['nth']}次"
    else:
        stem = f"monthly-report-{period}"
    output_dir = Path(output_dir).resolve()
    check_conflicts(output_dir, stem)
    executable = check_environment()
    with tempfile.TemporaryDirectory(prefix="weekly-report-") as temporary:
        work = Path(temporary)
        typ_path = work / (stem + ".typ")
        typ_path.write_text(source, encoding="utf-8")
        run_typst([
            executable, "compile", str(typ_path), str(work / "page-{p}.png"),
            "--format", "png", "--ppi", "300",
        ])
        pages = sorted(work.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[1]))
        if not pages:
            raise ReportError("Typst 未生成任何 PNG 图片.")
        for page in pages:
            with page.open("rb") as image:
                header = image.read(24)
            if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(
                ">II", header[16:24]
            ) != (2480, 3508):
                raise ReportError("图片不是预期的 A4 300 DPI 尺寸: " + page.name)
        files = [(typ_path, typ_path.name)] + [
            (page, stem + (".png" if len(pages) == 1 else f"-第{index}页.png"))
            for index, page in enumerate(pages, 1)
        ]
        output_dir.mkdir(parents=True, exist_ok=True)
        check_conflicts(output_dir, stem)
        delivered = publish_files(files, output_dir)
    return {"pages": len(pages), "files": [str(path) for path in delivered]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="输入 JSON 路径, 使用 - 从标准输入读取")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(), help="输出目录, 默认当前目录")
    args = parser.parse_args()
    try:
        content = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        result = render_report(json.loads(content), args.output_dir)
    except (ReportError, OSError, ValueError) as error:
        print("周报生成失败: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
