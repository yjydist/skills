---
name: paper-first-pass
description: 在用户提供论文 (PDF, arXiv 页面或全文) 并希望快速判断其内容与价值, 或明确调用本 skill 时, 执行第一遍 triage 阅读, 按固定模板输出论文快照报告和第二遍阅读建议. 只基于实际读取的内容作答, 不深入推导细节, 不伪造证据定位.
---

# 论文第一遍阅读 (Paper First Pass)

对一篇学术论文执行第一遍 triage 阅读: 以较低成本快速建立论文全局认知 (研究什么, 为什么值得研究, 核心方法, 实验结果概况), 并判断是否值得进入第二遍精读. 本 skill 针对快速决策优化, 不产出普通论文摘要.

## 核心原则

+ 第一遍的价值在于 information gain per minute, 而不是 completeness. 目标不是全部看懂, 而是找出论文的 narrative: Problem -> Existing approaches -> Limitation / Gap -> Proposed idea -> Claimed contribution -> Evidence -> Conclusion.
+ 最终报告必须让用户无需先阅读全文, 也能决定是否投入时间进入第二遍.
+ 作者 claim 与 agent 自己的判断必须分开: 作者声称的内容使用「作者认为 / 作者报告 / 作者声称」等措辞, 自己的评价单独给出.
+ 只基于实际读取的内容作答, 不假装理解没有读取到的部分, 不根据论文标题或常识猜测论文内容.

## 工作流程

### 1. 获取论文内容

接受用户提供的 PDF, arXiv 页面, 论文全文文本或其他可读取的论文格式.

+ PDF 内容解析失败时, 明确向用户指出失败并停止, 不根据标题或常识猜测论文内容继续输出报告.
+ 用户提供的是链接时, 先获取实际内容再进入阅读; 获取失败时如实报告, 不凭记忆补全.

### 2. 按优先级阅读

按以下顺序优先阅读:

1. Title
2. Abstract
3. Introduction
4. Contributions
5. 论文中的主要 overview / architecture / pipeline 图
6. 主要实验表格和结果图
7. Conclusion / Discussion
8. 必要时快速浏览 section headings

除非理解主线所必需, 否则第一遍不深入: 数学推导, 证明, 算法细节, implementation details, appendix, 大量实验细节, 超参数, 每个 baseline 的具体配置.

### 3. 自检必答问题

阅读完成后, 确认以下问题都能回答; 无法回答时如实说明, 不假装理解:

1. **Problem**: 论文具体解决什么问题? 不只重复论文标题, 用简单而准确的语言说明输入是什么, 输出是什么, 任务是什么, 谁会关心; 非典型 input-output 任务时解释其研究问题.
2. **Motivation**: 为什么这个问题重要? 区分作者声称的重要性与论文证据支持的实际重要性.
3. **Existing approaches**: 以前通常如何解决? 只介绍理解论文所需的背景, 不展开成 related work survey.
4. **Gap**: 作者认为现有方法最大的不足是什么? 这是理解整篇论文最重要的问题之一.
5. **Core idea**: 作者提出的核心 idea 是什么? 用自己的话解释, 不堆术语, 必须使用术语时随后解释, 优先解释 intuition 而非 implementation, 目标是让具备计算机科学本科背景的人能理解.
6. **Contributions**: 作者声称的主要贡献是什么? 区分真正的新 idea, 工程实现, 新 dataset / benchmark, 新 evaluation, 理论结果, 实证发现, 不把作者列出的所有 bullet 无条件视为同等重要.
7. **Evidence**: 作者使用了什么证据支持 claim? 快速检查 dataset / benchmark, baseline, 主要指标, 最重要结果, 以及明显的失败, trade-off 或限制; 不做完整实验审计, 这属于第二遍.
8. **Bottom line**: 只用三句话告诉别人这篇论文讲了什么.

### 4. 生成报告

严格按照 [报告模板](references/report-format.md) 的 12 节结构输出 `# Paper Snapshot` 报告.

+ 关键判断尽可能附论文内的定位 (Section / Page / Figure / Table / Equation), 定位必须来自实际读取的内容, 严禁伪造页码, section, figure 或 table.
+ 用户提供了研究方向, 项目或问题时, 额外输出 Relevance to Your Goal 节; 未提供时不猜测, 不输出该节.

## 操作边界

+ 不逐段摘要, 不解释所有术语.
+ 不在第一遍陷入公式推导.
+ 不为挑毛病而挑毛病, Limitations / Red Flags 只记录第一遍就能明显观察到的问题.
+ 不猜测用户未提供的研究目标.
