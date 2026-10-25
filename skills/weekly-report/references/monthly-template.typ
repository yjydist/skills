// 月报模板. 渲染脚本只替换下方的数据块, 保留版式和页面尺寸.
// 数据块中的内容是字符串或数字, 不作为 Typst 标记或代码执行.
// REPORT_DATA_START
#let report = (
  kind: "月报",
  year: 2026,
  month: 3,
  name: "易靖远",
  student_id: "26031210039G",
  start: "2026.3.1",
  end: "2026.3.31",
  contributions: (
    "查看和对比实验室主机的硬件设备",
  ),
  research: (
    "阅读师兄师姐的大论文, 积累综述的素材",
  ),
  service: "无",
  exercise: "日常锻炼",
  reflection: "无",
  lesson: "无",
  attendance_hours: "5.5",
  attendance_early: "20",
  self_evaluation: "满意",
)
// REPORT_DATA_END

#set page(paper: "a4", height: auto, margin: (x: 1.9cm, y: 2.54cm))
#set text(font: "Alimama FangYuanTi", size: 12pt, lang: "zh", region: "zh")

#let period = "本月"
#let lines(items) = items.map(item => [#item]).join(linebreak())
#let check-box(selected) = box(
  width: 0.85em,
  height: 0.85em,
  baseline: 0.11em,
  inset: 0pt,
  stroke: 0.5pt,
  if selected {
    curve(
      stroke: (paint: black, thickness: 0.10em, cap: "round", join: "round"),
      curve.move((22%, 52%)),
      curve.line((41%, 73%)),
      curve.line((80%, 25%)),
    )
  },
)
#let evaluations = ("非常满意", "满意", "不太满意").map(option => {
  [#check-box(option == report.self_evaluation)#h(0.4em)#option]
})
#let head-cell(body) = table.cell(align: center + horizon, text(weight: "bold", body))
#let cat-cell(body) = table.cell(align: center + horizon, body)
#let body-cell(body) = table.cell(align: left + horizon, body)

#align(center, text(size: 20pt, weight: "bold", [#(report.year)年#(report.month)月月报]))

#v(8pt)

#table(
  columns: (auto, 1fr, auto, 1fr, auto),
  stroke: none,
  [姓名：#(report.name)],
  [],
  [学号：#(report.student_id)],
  [],
  [日期：#(report.start)-#(report.end)],
)

#table(
  columns: (14.3%, 75.7%, 10%),
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
    #(period)进度或学习状态#h(1em)#(evaluations.join(h(1.2em)))
  ],
  [],
)
