# 报告模板

每次执行 paper-first-pass 都按本模板结构输出报告. 报告标题固定为 `# Paper Snapshot`. 头部字段之后是 12 个编号小节; 用户提供了研究方向, 项目或问题时, 额外追加 `## Relevance to Your Goal` 节.

报告正文使用简体中文, 论文原有术语保留英文原文. 关键判断尽可能给出论文内的证据定位, 引用格式见第 12 节.

## 头部字段

```text
# Paper Snapshot

**Title:**
**Authors:**
**Venue / Year:**  (能够可靠确定时填写, 不能确定时如实说明)
**Paper type:** empirical / theoretical / systems / survey / benchmark / dataset / other
```

## 12 节结构

### 1. 一句话总结

用一句话说明: 「作者为了 ______, 提出了 ______, 并通过 ______ 证明/展示 ______.」

论文不适合这个句式时可以调整, 但必须保持简洁.

### 2. Problem

说明论文具体解决什么问题.

+ 不只重复论文标题, 用简单而准确的语言说明输入是什么, 输出是什么, 任务是什么, 谁会关心这个问题.
+ 论文不是典型 input-output 任务时, 解释其研究问题.

### 3. Why it matters

说明为什么重要.

+ 区分作者声称的重要性与从论文证据来看的实际重要性, 两者必须分开表述.

### 4. Existing approach -> Gap

先说明以前怎么做, 再说明作者认为哪里有问题. 使用固定小节:

```text
Existing approach:
...

Main limitation:
...
```

+ Existing approach 只介绍理解论文所需的背景, 不展开成 related work survey.
+ Main limitation 写作者认为现有方法最大的不足, 使用「作者认为」等措辞标明这是作者的 claim.

### 5. Core Idea

这是整个报告最重要的部分之一. 用自己的话解释论文的核心思想.

合适时可以使用以下结构:

```text
Before:
...

This paper:
...

Why this might work:
...
```

+ 尽量用非论文原文的语言解释, 不堆术语; 必须使用术语时随后解释.
+ 优先解释 intuition, 而不是 implementation.
+ 目标是让一个具备计算机科学本科背景的人能够理解.

### 6. Main Contributions

列出最多 3-5 个真正重要的贡献.

每项标记类型, 从以下标签中选择: `[Idea]` / `[Method]` / `[System]` / `[Dataset]` / `[Benchmark]` / `[Theory]` / `[Empirical finding]`.

+ 区分真正的新 idea, 工程实现, 新 dataset / benchmark, 新 evaluation, 理论结果和实证发现.
+ 不把作者列出的所有 bullet 无条件视为同等重要的创新.

### 7. Evidence at a Glance

说明作者使用了什么证据支持 claim:

+ datasets / benchmarks
+ baselines
+ evaluation metrics
+ 最关键的实验结果

只保留第一遍真正值得知道的结果. 不做完整实验审计, 完整审计属于第二遍阅读.

### 8. Most Important Figure / Table

选择全篇最值得先看的一个 Figure 或 Table, 说明:

+ Figure / Table 编号
+ 它展示了什么
+ 为什么重要
+ 阅读时应该观察什么

没有明显合适的图表时, 写 `None`.

### 9. Limitations / Red Flags

只记录第一遍就能明显观察到的问题, 例如:

+ 评估范围非常窄
+ baseline 看起来较弱
+ 提升幅度有限
+ claim 大于 evidence
+ 依赖非常特殊的假设
+ 计算成本很高
+ 作者自己明确指出的重要 limitation

不为挑毛病而挑毛病; 没有明显问题时如实说明, 不硬凑条目.

### 10. 三句话带走

严格控制在三条, 每条一句话:

```text
1.
2.
3.
```

### 11. 第二遍阅读建议

给出一个明确判断:

```text
**Recommendation: STRONGLY READ / READ / MAYBE / SKIP**
```

四选一, 并分别回答:

**为什么值得继续:**

...

**什么情况下不值得继续:**

...

**如果进入第二遍, 最应该重点研究的 3 个问题:**

```text
1.
2.
3.
```

### 12. 阅读证据

对于报告中的关键判断, 尽可能给出论文中的定位: Section, Page, Figure, Table, Equation (只在第一遍确实需要时引用).

引用格式示例:

```text
> Evidence: Section 1, p.2
> Evidence: Figure 2
> Evidence: Table 3
```

定位必须来自实际读取的内容, 严禁伪造页码, section, figure 或 table; 无法给出定位的关键判断, 如实说明.

## 可选节: Relevance to Your Goal

仅当用户提供了研究方向, 项目或问题时输出本节, 说明论文与用户目标的直接关联. 用户未提供时不猜测目标, 不输出本节.
