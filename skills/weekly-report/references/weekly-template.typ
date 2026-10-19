// 周报模板. 渲染脚本只替换下方的数据块, 保留版式和页面尺寸.
// 数据块中的内容是字符串或数字, 不作为 Typst 标记或代码执行.
// REPORT_DATA_START
#let report = (
  kind: "周报",
  year: 2026,
  month: 3,
  nth: 2,
  name: "常瑞",
  student_id: "25031212280",
  start: "2026.3.2",
  end: "2026.3.8",
  contributions: (
    "实验室主机的硬件设备的查看和对比。",
  ),
  research: (
    "读师兄师姐的大论文，积累综述的素材。",
  ),
  service: "无",
  exercise: "日常锻炼",
  reflection: "无",
  lesson: "无",
  attendance_hours: "5.5",
  attendance_early: "5",
  self_evaluation: "满意",
)
// REPORT_DATA_END

#set page(paper: "a4", margin: (top: 2.54cm, bottom: 2.54cm, left: 3.17cm, right: 3.17cm))
#set text(font: ("Alimama FangYuanTi VF", "Alimama FangYuanTi"), size: 12pt, lang: "zh", region: "zh")

#let period = "本周"
#let lines(items) = items.map(item => [#item]).join(linebreak())
#let evaluations = ("非常满意", "满意", "不太满意").map(
  option => if option == report.self_evaluation { "√ " + option } else { option },
)
#let head-cell(body) = table.cell(align: center + horizon, text(weight: "bold", body))
#let cat-cell(body) = table.cell(align: center + horizon, body)
#let body-cell(body) = table.cell(align: left + horizon, body)

#align(center, text(size: 20pt, weight: "bold", [#(report.year)年#(report.month)月第#(report.nth)次周报]))

#v(8pt)

#table(
  columns: (17.6%, 39.7%, 42.7%),
  stroke: none,
  [姓名：#(report.name)],
  [学号：#(report.student_id)],
  [日期：#(report.start)-#(report.end)],
)

#table(
  columns: (14.3%, 73%, 12.7%),
  stroke: 0.5pt,
  table.header(
    head-cell[类别],
    head-cell[内容],
    head-cell[备注],
  ),
  cat-cell[实验室、项目贡献],
  body-cell(lines(report.contributions)),
  [],
  cat-cell[科研进展],
  body-cell(lines(report.research)),
  [],
  cat-cell[其他],
  body-cell[
    实验室其他服务性工作：#(report.service) \
    运动情况：#(report.exercise) \
    心得体会：#(report.reflection) \
    反思教训：#(report.lesson)
  ],
  [],
  cat-cell[考勤],
  body-cell[
    #(period)平均每天打卡时长： #(report.attendance_hours) 小时 \
    #(period)上午9:30前打卡次数：#(report.attendance_early)次
  ],
  [],
  cat-cell[自我评价],
  body-cell[
    #(period)进度或学习状态　#(evaluations.join("、"))
  ],
  [],
)
