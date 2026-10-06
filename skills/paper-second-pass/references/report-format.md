# 报告模板

每次执行 paper-second-pass 都按本模板结构输出报告. 报告标题固定为 `# Second-Pass Reading Report`. 头部字段之后是 16 个编号小节.

报告正文使用简体中文, 论文原有术语保留英文原文. 关键判断尽可能给出论文内的证据定位, 引用格式见第 16 节.

## 头部字段

```text
# Second-Pass Reading Report

**Title:**
**Authors:**
**Venue / Year:**  (能够可靠确定时填写, 不能确定时如实说明)
**Paper type:** empirical / theoretical / systems / survey / benchmark / dataset / other
**First-pass verdict:**  (可选, 用户提供第一遍报告时填写)
```

## 16 节结构

### 1. Executive Understanding

用 5-10 句话按逻辑链重建论文, 覆盖以下环节:

```text
Problem -> Gap -> Idea -> Method -> Evidence -> Result
```

+ 每个环节至少一句, 不逐段摘要, 不展开细节.
+ Result 部分只写最重要的结果, 细节留给第 8 节.

### 2. Problem Formulation

用固定小节块说明论文如何形式化问题:

```text
Given: ...
Goal: ...
Constraints: ...
Evaluation criterion: ...
```

+ 论文不是典型 input-output 任务时, 用适合该论文的形式重述问题, 不硬套四项.
+ 区分论文显式给出的设定与自己补充的理解.

### 3. Method Mental Model

先给一个 30 秒能读完的解释, 再给详细流程:

```text
30-second explanation:
...

Detailed flow:
...
```

+ Detailed flow 的每一步说明它做什么, 为什么需要它, 是否属于论文的创新点.
+ 沿用 skill 第 3 步的必答问题覆盖: Inputs / Outputs, Components, Data flow, Training / Optimization, Inference, Key innovation.
+ 与 baseline 对比时使用结构对比, 例如 `A -> B -> C` vs `A -> X -> B -> C`, 并指出差异步骤.

### 4. Core Components

用 markdown 表格列出真正重要的组件, 只保留理解方法必需的行, 不罗列全部模块:

| Component | Function | Why needed | Novel? | Evidence |

+ Novel? 一列区分 `new` / `existing` / `adapted`, 不确定时如实标注.
+ Evidence 一列给出论文内定位, 见第 16 节的引用格式.

### 5. Key Equations

只列支撑核心贡献的关键公式, 每个公式回答五要素:

```text
Equation: (编号或定位)
Purpose: 它想计算什么
Variables: 各变量的含义
Intuition: 直觉理解, 各项作用, 去掉某项会怎样
Connection to core idea: 与核心 idea 的关系
```

+ 标准公式说明来源和在本方法中的作用即可, 不逐行推导.
+ 无关键公式时明确写: `No essential equation is required to understand the central contribution.`

### 6. What Is Actually New?

用固定三块区分组合与创新:

```text
Known ingredients:
...

New combination:
...

Potentially novel contribution:
...
```

+ 方法只是组合已有技术时直接说明, 不拔高.
+ Potentially novel contribution 使用"作者声称"等措辞标明这是作者的 claim.

### 7. Experiment -> Claim Map

用 markdown 表格将主要 claim 映射到支撑实验, 不遗漏论文的主要 claim:

| Author Claim | Supporting Experiment | Result | Does it support the claim? | Caveat |

+ Author Claim 使用"作者声称"措辞, 转述不添加.
+ Result 抄自论文对应 Table 或 Figure, 并附定位.
+ Does it support the claim? 区分 `fully supported` / `partially supported` / `not supported`, 并说明理由.
+ Caveat 写 confounders (compute, data, parameter count), 指标选择等保留意见.

### 8. Most Important Results

列出 3-5 个最重要的结果, 每项包含:

+ Figure / Table 定位
+ 对比对象 (与哪个 baseline 或设置比较)
+ 具体数字, 必须抄自论文对应 Table 并附定位, 不凭记忆或概括改写
+ 该结果是否实际重要, 为什么
+ caveat

### 9. Ablation Analysis

回答三个问题:

+ 哪些组件被 ablation 证明真正有效, 效果如何?
+ 哪些设计选择影响有限或未被充分验证?
+ ablation 结果是否支持论文的 mechanism 解释? 不支持时指出断点.

### 10. Assumptions

区分显式假设与推断假设:

+ 显式假设: 论文中明确写出的假设.
+ 推断假设: 方法成立所依赖但论文未明说的假设, 逐条标记 `Inference, not explicitly stated by authors`.

### 11. Limitations and Failure Modes

用固定三块, 三块性质不同不得混写:

```text
Authors acknowledge:
...

Observed from the paper:
...

Potential failure modes:
...
```

+ 第一块是作者自己承认的 limitation.
+ 第二块是从论文实验和文本中可观察到的问题, 附证据定位.
+ 第三块是自己的推测, 不得写成事实.

### 12. Cost / Trade-offs

说明方法在以下维度上的代价与权衡:

+ quality vs compute, data, latency, memory
+ 复杂度, engineering effort
+ interpretability 或其他被牺牲的维度

+ 论文未报告的项如实标注 `not reported`, 不替作者补全.

### 13. Strongest and Weakest Part

各一段:

+ **Strongest part:** 说明论文最有力之处并给出理由.
+ **Weakest part:** 说明论文最薄弱之处并给出理由.

+ 理由绑定证据定位, 不写空泛评价.

### 14. What I Still Don't Understand

列出未解决的理解缺口, 可包括: unclear detail, unexplained result, missing baseline, ambiguous formula, insufficient ablation.

+ 不硬凑条目, 也不省略真实缺口; 无缺口时如实说明.

### 15. Third-Pass Decision

给出一个明确判断:

```text
**Recommendation: DEEP READ / SELECTIVE DEEP READ / STOP**
```

三选一, 然后分别回答:

**为什么值得 (或不值得) 第三遍:**

...

**第三遍优先级 (3-7 项):**

```text
1.
2.
3.
```

**第三遍要解决的具体问题:**

+ 列出具体问题, 例如某公式某项的推导, 某个实验设置的公平性, 某个实现细节; 不写宽泛目标.

### 16. Evidence Index

汇总全报告关键判断的论文内定位: Section, Page, Figure, Table, Equation, Appendix.

引用格式示例:

```text
> Evidence: Section 3.2, p.4
> Evidence: Table 2
> Evidence: Equation (5)
```

+ 定位必须来自实际读取的内容, 严禁伪造页码, section, figure 或 table.
+ 无法给出定位的关键判断, 如实说明.
