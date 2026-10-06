# paper-first-pass 使用文档

`paper-first-pass` 对用户提供的学术论文执行第一遍 triage 阅读: 按优先级读取标题, 摘要, 引言, 贡献, 主图和主要实验结果, 输出一份 12 节结构的论文快照报告 (Paper Snapshot), 并给出是否值得进入第二遍精读的明确建议. 第一遍以信息增益效率为目标, 不深入公式推导和实现细节.

## 使用前提

+ 将 [skill 目录](../skills/paper-first-pass/SKILL.md) 连同 [报告模板](../skills/paper-first-pass/references/report-format.md) 一起提供给支持 skill 的工具, 保持两者的相对路径.
+ 执行工具能够读取用户提供的论文内容, 例如 PDF 文件, arXiv 页面或论文全文文本.
+ 第一遍报告只基于实际读取的内容; 期望完整实验审计或逐段精读时, 属于第二遍阅读, 不在本 skill 范围内.

下方示例使用 `$paper-first-pass` 表示调用该 skill. 如果所用工具不支持这种调用形式, 可以直接指定 `skills/paper-first-pass/SKILL.md` 的实际路径, 要求按其中的指导处理.

## 调用示例

### 提供 PDF 文件

```text
使用 $paper-first-pass 阅读这篇论文: ~/Downloads/some-paper.pdf
```

预期结果是 skill 解析 PDF 内容, 按优先级阅读关键部分, 输出 `# Paper Snapshot` 报告, 包含一句话总结, Problem, Core Idea, Main Contributions, Evidence at a Glance 等 12 节, 末尾给出 `Recommendation: STRONGLY READ / READ / MAYBE / SKIP` 之一的第二遍阅读建议, 关键判断附带论文内的 Section / Figure / Table 定位.

### 提供 arXiv 链接并附研究方向

```text
使用 $paper-first-pass 阅读这篇论文: https://arxiv.org/abs/XXXX.XXXXX
我目前在做检索增强生成的评测方向, 帮我判断这篇论文是否值得精读.
```

预期结果是 skill 先获取论文实际内容再阅读; 除了标准 12 节报告外, 由于用户提供了研究方向, 报告会额外输出 `## Relevance to Your Goal` 节, 说明论文与该方向的直接关联; 若未提供研究方向, 则不会出现该节.

## 异常处理

+ PDF 内容解析失败时, skill 明确指出失败并停止, 不根据论文标题或常识猜测内容继续输出报告.
+ 提供的不是论文 (例如博客, 新闻或课程笔记) 时, 说明内容不属于论文并停止, 不强行套用报告模板.
+ 论文为 survey, benchmark 或 dataset 等非常规类型时, `Paper type` 字段如实标注, 句式模板可调整但保持简洁, Evidence 节按论文实际类型描述其贡献证据.
+ 关键判断无法在论文中给出定位时, skill 如实说明, 不伪造页码或 figure 编号.

## 进一步阅读

+ [执行流程](../skills/paper-first-pass/SKILL.md): 内容获取, 阅读优先级, 必答问题与操作边界.
+ [报告模板](../skills/paper-first-pass/references/report-format.md): 12 节完整结构与措辞要求.
+ [下游 skill](paper-second-pass.md): 已决定精读后的第二遍理解阅读.
+ [返回仓库说明](../README.md).
