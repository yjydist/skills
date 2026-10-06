# 报告模板

每次执行 paper-third-pass 都按本模板结构输出报告. 报告标题固定为 `# Deep Reading Report`. 头部字段之后是 20 个编号小节.

报告正文使用简体中文, 论文原有术语保留英文原文. 关键判断尽可能给出论文内定位, 代码判断给出代码定位, 引用格式见第 20 节.

## 头部字段

```text
# Deep Reading Report

**Title:**
**Authors:**
**Venue / Year:**  (能够可靠确定时填写, 不能确定时如实说明)
**Paper type:** empirical / theoretical / systems / survey / benchmark / dataset / other
**Second-pass verdict:**  (可选, 用户提供第二遍报告时填写)
```

## 20 节结构

### 1. Paper in One Mental Model

用一段话给出论文的完整 mental model: 问题, 核心假设, 方法的关键机制, 证据结构与局限. 读完后应能向别人 5 分钟讲清这篇论文.

+ 重建而非复述: 按逻辑链组织, 不按论文章节顺序摘要.

### 2. Formal Problem Definition

用固定小节块说明论文问题的形式化定义:

```text
Inputs: ...
Outputs: ...
Objective: ...
Constraints: ...
Assumptions: ...
Evaluation: ...
```

+ 论文不是典型 input-output 任务时, 用适合该论文的形式重述问题, 不硬套六项.

### 3. End-to-End Method

沿完整 pipeline 重建方法:

```text
Input -> preprocessing -> representation -> core mechanism -> objective -> optimization -> inference -> output
```

+ 每一步标注: 它做什么 (function), 为什么需要它 (rationale), 是否属于论文的创新点 (novelty).

### 4. Mechanism Decomposition

用 markdown 表格分解方法的每个关键设计:

| Component | Purpose | Mechanism | Necessary? | Evidence | Alternative |

+ Necessary? 区分 `essential` / `helpful` / `unclear`, 并说明判断依据.
+ Alternative 写不用它会怎样, 或已有的替代设计.
+ Evidence 给论文内定位; 属于自己推断时标注 `Inference`.

### 5. Mathematical Core

对每个关键公式给出八要素:

```text
Equation: (编号或定位)
Original role: 它在方法中的原始作用
Formal meaning: 每个符号与项的严格含义
Variables: 各变量的含义, 形状与取值范围
Derivation: 它从哪里来, 关键推导步骤; 标准公式说明来源即可
Intuition: 直觉理解, 各项作用, 去掉某项会怎样
Assumptions: 公式成立依赖的假设
Edge cases: 退化情形, 数值问题, 边界条件
Implementation mapping: 代码中对应的位置; 无代码时写 Unknown
```

+ 无关键公式时明确写: `No essential equation is required to understand the central contribution.`

### 6. Algorithm Walkthrough

用步骤列表或伪代码重述论文的算法 (训练算法或推理算法):

+ 每步标注与第 4 节组件的对应关系.
+ 论文给出伪代码但含糊不清的地方如实指出, 不脑补.

### 7. Training vs Inference

对比训练与推理两个阶段的差异:

+ 训练目标与损失组成, 优化器与超参, 多阶段训练流程.
+ 推理流程与额外开销 (memory, latency, 额外组件).
+ 两者不一致的设计 (如 train-test discrepancy) 显式指出.

### 8. Claim -> Evidence Audit

用 markdown 表格将论文的主要 claim 逐条审计:

| Claim | Evidence | Strength | Alternative explanation | Verdict |

+ Claim 使用 "作者声称" 措辞转述, Evidence 附论文内定位.
+ Strength 评估证据强度 (sample size, baseline 强度, 是否控制 confounders).
+ Alternative explanation 写除论文解释外的其他可能解释.
+ Verdict 五选一: `Strongly supported` / `Supported` / `Partially supported` / `Weakly supported` / `Unsupported or unclear`.

### 9. Experiment Reconstruction

对每个主要实验, 用固定小节块重建:

```text
Experiment: ...
Hypothesis: 该实验想验证什么
Setup: dataset, model, 对比对象, 计算预算
Independent variable: 被改变的因素
Dependent variable: 被观测的指标
Controls: 被控制的变量; 缺失的控制如实指出
Result: 关键数字, 抄自论文对应 Table / Figure 并附定位
Interpretation: 论文的解释
Confounders: 可能的混淆因素
What this actually proves: 该实验实际能支撑的结论
What this does NOT prove: 该实验不能支撑的结论
```

### 10. Ablation & Sensitivity

回答三个问题:

+ 哪些组件被 ablation 证明真正有效, 效果多大?
+ 哪些超参与设计选择影响敏感, 哪些不敏感?
+ ablation 结果是否支持论文的 mechanism 解释? 不支持时指出断点.

### 11. Reproduction Blueprint

给出足以复现论文主结果的蓝图, 由 8 个 Step 组成, 每个 Step 用固定小节块:

```text
Step N - <名称>: environment / data / model / training / evaluation / expected outputs / reproduction risks 之一
Content: ...
Source: 论文章节, appendix 或代码定位; 论文未给出时写 Not specified
```

+ 只填可靠且确定的内容; 缺失的配置, 超参, 预处理细节列入下面的 Missing information, 不猜测.
+ 结尾给出三块:

```text
Missing information: ...
Likely reproduction pitfalls: ...
Estimated hardest part to reproduce: ...
```

### 12. Paper -> Code Mapping

有官方代码且已检查时, 用 markdown 表格建立概念到代码的映射:

| Paper Concept | Code Location | Explanation |

+ 只列核心 execution path: model definition, training loop, loss, preprocessing, evaluation, default config.
+ 实现与论文描述一致时说明一致; 冲突时显式指出冲突点与各自内容, 不默认任何一方正确.
+ 无官方代码或未检查时, 本节写明: `Official implementation was not available / not inspected.` 不猜测代码结构.

### 13. Hidden Assumptions

区分两块:

+ **Explicit assumptions**: 论文中明确写出的假设.
+ **Implicit assumptions**: 方法成立所依赖但论文未明说的假设 (数据分布, 规模, 算力, 任务性质等), 逐条标注 `Inference, not explicitly stated by authors`.

### 14. Failure Modes

列出方法可预见的失败模式, 每项用固定结构:

```text
Condition: 什么条件下会失败
Why it may fail: 机制层面的原因
Evidence or reasoning: 论文内证据或自己的推理, 标注属于哪一类
How to test it: 一个可执行的验证方法
```

### 15. Reviewer Perspective

从审稿人视角给出六个固定小节, 每节 2-4 句:

```text
Strengths: ...
Weaknesses: ...
Questions to authors: ...
Missing experiments: ...
Soundness: 方法的正确性论证是否充分
Overall assessment: ...
```

+ 基于论文自身内容评价, 不套用具体 conference 的评分标准, 除非用户要求.

### 16. Reimplementation Checklist

给出从零重新实现本方法所需的任务列表, 使用 `- [ ]` 任务列表语法, 按论文实际内容调整条目:

```text
- [ ] 环境: ...
- [ ] 数据: ...
- [ ] 模型: ...
- [ ] 训练: ...
- [ ] 评估: ...
```

+ 条目具体到可直接执行, 不写 "实现模型" 这类空泛条目.

### 17. Research Extensions

提出 3-7 个研究方向, 必须从论文出发. 每个方向用固定小节块:

```text
Idea: ...
Why it follows from this paper: ...
Hypothesis: ...
Minimal experiment: 最小验证实验
What result would be interesting: 什么结果值得注意
```

+ 覆盖角度可包括: simplification, extension, transfer, combination, failure-driven research.
+ 不做无边界的 brainstorm; 数量不足 3 个或论文确实缺乏延伸空间时如实说明.

### 18. What I Would Do Next

给出自己接下来会做的事, 按优先级排序:

```text
1. (最高优先级)
2.
3.
```

+ 按论文实际情况定制, 不套模板; 可以是读某篇引用, 补某个实验, 验证某个怀疑, 或直接复现某个部分.

### 19. Open Questions

列出读完第三遍后仍未解决的问题: 论文含糊之处, 无法验证的判断, 需要联系作者或实验才能确认的问题.

+ 不硬凑条目, 也不省略真实缺口; 无问题时如实说明.

### 20. Evidence Index

汇总全报告关键判断的论文内与代码内定位: Section, Page, Figure, Table, Equation, Appendix, Code file.

引用格式示例:

```text
> Evidence: Section 3.2, p.4
> Evidence: Table 2
> Evidence: Equation (5)
> Evidence: train.py, line 88
```

+ 定位必须来自实际读取的内容, 严禁伪造页码, section, figure, table 或代码位置.
+ 无法给出定位的关键判断, 如实说明.

## 反作弊条款

+ 严禁伪造证据位置: 每条 Evidence 定位都必须来自本次实际读取的内容.
+ 严禁虚构配置: 复现蓝图与 Reimplementation Checklist 中论文未给出的信息写 Not specified 或 Unknown, 不编造超参与细节.
+ 论文类型不适配的节 (如 survey 没有 experiment, 纯理论论文没有 training) 注明 `Not applicable for this paper type`, 不硬凑内容.
