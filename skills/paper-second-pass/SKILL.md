---
name: paper-second-pass
description: 在用户已完成论文第一遍阅读并决定精读, 提供论文 (PDF, arXiv 页面或全文) 要求执行第二遍理解阅读, 或明确调用本 skill 时, 建立方法的准确 mental model 与实验到 claim 的证据映射, 审计实验支撑是否闭合逻辑链, 按固定 16 节模板输出精读报告和第三遍阅读建议. 只基于实际读取的内容作答, 不把作者 claim 当作事实, 不伪造证据定位.
---

# 论文第二遍阅读 (Paper Second Pass)

对一篇学术论文执行第二遍理解阅读: 目标不是更长更全的摘要, 而是建立方法的准确 mental model 和实验到 claim 的 evidence map. 核心是检查逻辑链 Problem -> Assumptions -> Method -> Mechanism -> Expected effect -> Experiment -> Observation -> Claim 是否闭合, 每个断点都要指出. 本 skill 是 paper-first-pass 的下游, 服务于已决定精读的场景.

## 核心原则

+ 第二遍的价值在于 mental model 和 evidence map 的准确性, 而不是篇幅. 报告不追求更长更全, 质量看逻辑链审计是否到位.
+ 必须检查逻辑链是否闭合: 方法的机制是否真的指向期望效果, 实验是否真的验证了 claim, 每个断点都要明确指出.
+ 作者 claim 与自己的判断分开措辞, 重要结论绑定论文内的证据定位.
+ 不因 outperform 就认为更好, 必须考虑 compute, data, parameter count 等 confounders.
+ 区分 correlation, empirical evidence 和 causal explanation: 实验显示相关不等于机制得到解释.
+ 数学阅读服务于理解: 只深入支撑核心贡献的公式, 标准公式说明来源和作用即可, 不逐行推导.
+ 第一遍报告可作起点, 但关键判断必须回看原论文验证; 缺信息时不猜测 implementation details, 如实写入未解决缺口.

## 工作流程

### 1. 获取输入与确认上下文

接受用户提供的 PDF, arXiv 页面, 论文全文文本或其他可读取的论文格式.

+ PDF 内容解析失败时, 明确向用户指出失败并停止, 不根据标题或常识猜测论文内容继续输出报告.
+ 用户提供第一遍报告 (Paper Snapshot) 时, 以其为起点并在报告中标注其结论需回原文验证; 未提供时不要求先跑第一遍, 直接进入第二遍.

### 2. 按第二遍范围阅读

按以下范围完整阅读:

1. Title, Abstract
2. Introduction
3. Related Work (与定位贡献相关的部分)
4. Method / Approach
5. Architecture / Algorithm
6. 核心公式
7. Experiments
8. Ablation
9. Analysis / Discussion
10. Limitations
11. Conclusion
12. 必要时: 与主实验直接相关的 appendix 部分

明确不做 (留给第三遍): 逐个推导公式, 检查每个证明, 全部 implementation details, 全部 appendix, 复现代码.

### 3. 建立方法 mental model

阅读完成后, 确认以下问题都能回答; 无法回答时如实说明, 不假装理解:

1. **Inputs / Outputs**: 方法的输入和输出具体是什么?
2. **Components**: 方法由哪些组件构成, 各自做什么?
3. **Data flow**: 数据如何在组件间流动, 形状和依赖关系如何?
4. **Training / Optimization**: 训练目标是什么, loss 由哪些项组成, 优化哪些参数, 是否多阶段?
5. **Inference**: 推理时与训练有何差异, 额外开销是什么?
6. **Key innovation**: 真正改变结果的关键机制是哪个, 为什么它可能有效?
7. **Difference from baseline**: 与 baseline 的结构差异是什么? 适用时使用 `A -> B -> C` vs `A -> X -> B -> C` 的结构对比.
8. **Why it might work**: 机制层面的因果解释是什么, 论文给出的是解释还是只有相关性证据?

### 4. 阅读关键公式

只深入支撑核心贡献的关键公式, 每个公式优先回答:

+ 它想计算什么, 输入和输出是什么?
+ 各项分别起什么作用, 去掉某项会怎样?
+ 它与核心 idea 的关系是什么?

标准公式说明来源和在本方法中的作用即可, 不逐行推导.

### 5. 审计实验与映射 claim

将每个主要 claim 映射到支撑它的实验, 逐项检查:

+ **Baselines**: 是否包含强 baseline, 对比是否公平, 预算 / 数据 / 模型大小等 confounders 是否被控制?
+ **Metrics**: 指标是否真的对应 claim, 是否只报告有利指标?
+ **Ablations**: 哪些模块真正有效, ablation 结果是否支持论文的 mechanism 解释?
+ **Generalization**: 是否覆盖不同 dataset, 模型规模, 任务或分布?
+ **Cost**: 数据量, FLOPs, 参数量, latency, memory, pipeline 复杂度, annotation 成本是否报告?

### 6. 生成报告

严格按照 [报告模板](references/report-format.md) 的 16 节结构输出 `# Second-Pass Reading Report`.

+ 第 15 节 Third-Pass Decision 给出 `DEEP READ / SELECTIVE DEEP READ / STOP` 三选一.
+ Evidence Index 的定位必须来自实际读取的内容, 严禁伪造; 无法定位的判断如实说明.

## 操作边界

+ 不逐段摘要, 不复述第一遍报告的全部内容.
+ 不做第三遍的事: 逐个推导公式, 检查证明, 读取全部 implementation details, 复现代码.
+ 不把作者 claim 当作事实; Limitations 区分作者承认 / 论文可观察 / 自己推测三类.
+ 缺失信息写入 What I Still Don't Understand, 不猜测 implementation details.
+ 不沿用第一遍报告的结论而不回原文验证.
