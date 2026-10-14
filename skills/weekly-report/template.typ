// 学期周报模板. 渲染脚本只替换下方的数据块, 保留版式和页面尺寸.
// 数据块中的条目是字符串, 不作为 Typst 标记或代码执行.
// REPORT_DATA_START
#let report = (
  year: 2026,
  semester: "春季",
  week: 3,
  items: (
    "完成周报 skill 的模板设计与渲染流程验证",
    "整理本周进展条目并确认排版效果",
  ),
)
// REPORT_DATA_END

#set page(paper: "a4", margin: 48pt)
#set text(font: "Alimama FangYuanTi", size: 11pt, lang: "zh", region: "zh")

= #report.year 年#(report.semester)学期 / 第 #report.week 周 周报

#line(length: 100%, stroke: 1pt)

#list(..report.items)
