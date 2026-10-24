---
name: paper-third-pass
description: 对用户提供的学术论文执行第三遍深读, 重建方法与证据, 分析数学和可选代码. 完整模式输出 20 节报告; 选择性模式围绕用户指定或第二遍建议的具体问题深入分析, 明确未检查范围. 适用于深度理解, 验证, 复现规划或明确调用本 skill 的场景.
---

# 论文第三遍阅读 (Paper Third Pass)

对一篇学术论文执行第三遍深度阅读: 终极目标不是生成更长的摘要, 而是让用户获得解释, 复现, 批判和扩展这篇论文的能力, 达到 "理解 -> 验证 -> 批判 -> 复现 -> 修改 -> 使用" 的程度. 核心工作是重建论文的完整逻辑链, 深入机制, 数学与实验三个层面, 并在有代码时用代码验证论文描述. 本 skill 可以接续 paper-second-pass, 也可以直接使用. 下列八个目标用于完整模式, 选择性模式只执行解决指定问题所需的部分.

## 前提条件

+ 运行时: 无. 检查: `true`; 以状态 0 退出表示本项没有需要检测的运行时.
+ 第三方依赖: 无. 检查: `true`; 以状态 0 退出表示本项没有需要安装或导入的包.
+ 外部程序与认证: 无. 检查: `true`; 以状态 0 退出表示本项没有需要检测的外部程序或认证. 读取 PDF, 获取链接内容与访问代码仓库的能力由执行工具提供, 不要求特定程序; 代码不可访问时按正文说明如实标注未检查.
+ 检查命令按 POSIX shell (sh/bash) 编写. 以 `true` 作为检查命令的条目表示该项无要求, 在不支持 `true` 的 shell 中直接视为通过.

## 核心原则

+ 重建而非复述: 第三遍的价值在于从零重建论文的 problem, method 与 evidence 链条, 能独立推导和讲解, 而不是复述论文写了什么.
+ 真正的分析而非描述: 在机制层面解释为什么这个设计能工作, 在数学层面弄清每个关键公式的含义与推导, 在实验层面判断证据是否真的支撑结论; 停留在 "论文做了什么" 的描述不算完成.
+ 区分 essential mechanism, implementation choice, optimization trick, engineering convenience, historical convention: 每个设计判断它属于哪一类, 不把工程细节当成核心机制, 也不漏掉伪装成细节的关键设计.
+ 四类信息措辞分离: author claim (作者声称), paper evidence (论文内证据), agent inference (自己的推断), speculation (推测). 重要判断必须标注属于哪一类, 不把推断写成论文内容.
+ 缺信息时写 Unknown 或 Not specified, 不虚构 implementation details, 不为显得完整而填补不存在的细节.
+ 有代码时用代码验证论文描述: 检查实现与论文公式和描述是否一致; 两者冲突时必须显式指出, 不默认任何一方正确.
+ 不因有代码就跳过论文: 代码是验证手段, 不是替代品; 论文的动机, 假设与 claim 仍需从论文本身重建.

## 工作流程

### 1. 获取输入与确认上下文

论文原文是必要输入, 接受 PDF, arXiv 页面或全文文本. 代码仓库是可选的验证材料, 不能单独替代论文. 只有前序报告或代码时, 先获取可明确对应的原文, 无法取得则请求补充. 链接内容获取失败时说明原因并停止; 非论文输入说明不适用并停止.

+ 论文内容解析失败时, 明确向用户指出失败并停止, 不根据标题或常识猜测论文内容继续输出报告.
+ 用户提供第二遍报告 (Second-Pass Reading Report) 时, 以其为起点, 第三遍的优先级问题可直接继承其 Third-Pass Decision 一节; 但关键判断必须回原文验证, 不沿用未经验证的结论.
+ 未提供第二遍报告时不强制先跑前两遍, 直接进入第三遍.

### 2. 选择深读模式

+ 用户明确要求完整深读或限定问题时, 优先遵循该范围.
+ 用户未指定范围, 且第二遍建议为 `SELECTIVE DEEP READ` 并列出具体问题时, 使用选择性模式.
+ 其他情况默认完整模式. 用户明确要求选择性深读但没有可确定的问题时, 先询问关注点, 不擅自扩为完整阅读.
+ 选择性模式读取 [选择性报告模板](references/selective-report-format.md), 按问题读取相关论文内容和必要上下文, 验证前序判断, 按需检查代码. 不要求执行全部八个目标或输出 20 节, 不将未检查的内容视为无问题.

### 3. 完整范围阅读

完整模式按以下范围阅读, 范围大于第二遍:

1. Title, Abstract, Introduction
2. Related Work (用于判断 novelty 与定位)
3. Method / Approach 全部细节
4. 全部关键 equations, 逐个弄清
5. 全部 Algorithms
6. Experiments, Ablations, Analysis
7. Limitations, Conclusion
8. Relevant Appendix: implementation details, hyperparameters, dataset details
9. 有代码仓库且可访问时, 检查核心实现: model definition, training loop, loss, preprocessing, evaluation, default config

### 4. 完整模式的八个目标

阅读完成后依次完成以下八个目标, 每个目标的产出写入报告对应小节:

+ **(a) 重建论文**: 沿链条重建完整逻辑链: problem -> formulation -> assumptions -> design requirements -> method -> justification -> implementation -> experiment design -> evidence -> limitations. 每个环节问: 论文为什么这样设计, 换一种设计会怎样.
+ **(b) 机制理解**: 对每个关键设计回答六个问题: 它解决什么问题, 不用它会怎样, 为什么这样设计而不是别的方式, 与哪些已有设计相关, 它的代价是什么, 它是核心机制还是实现选择. 每个设计标注五分类: essential mechanism / implementation choice / optimization trick / engineering convenience / historical convention.
+ **(c) 数学理解**: 对每个关键公式回答模板中的要素 (见报告模板第 5 节): formal meaning, intuition, derivation, assumptions, edge cases, 与核心 idea 的 connection. 标准公式说明来源和作用即可, 不逐行推导.
+ **(d) 实验重建**: 对每个主要实验沿链条重建: claim -> hypothesis -> experimental design -> control -> metric -> result -> interpretation -> alternative explanation. 主动检查 confounders 与 cherry-picking: baseline 强度, 超参搜索是否对等, 指标是否只报有利项, seed 与方差是否报告.
+ **(e) 复现蓝图**: 生成足以复现的蓝图: environment, data, model, training, evaluation, expected outputs, reproduction risks. 只填论文 (或代码) 中可靠且确定的内容, 缺失项明确列入 Missing information, 不猜测.
+ **(f) 代码级理解**: 有代码时建立 paper concept -> code location 的映射, 只追核心 execution path (model definition, training loop, loss, evaluation), 不逐文件罗列. 无代码时如实说明, 不猜测代码结构.
+ **(g) 批判性分析**: 从 novelty, correctness, evidence quality, generality, efficiency, reproducibility, hidden assumptions, missing experiments 八个维度批判; 每条批判绑定证据或推理, 不写空泛评价.
+ **(h) 研究延伸**: 提出 3-7 个研究方向: simplification (能否更简单达到同样效果), extension, transfer (迁移到别的领域), combination (与哪些方法结合), failure-driven research (针对论文的失败模式设计研究). 每个方向给出 hypothesis 与最小验证实验; 必须从论文出发, 不做无边界的 brainstorm.

### 5. 生成报告

完整模式按照 [完整报告模板](references/report-format.md) 的 20 节结构输出 `# Deep Reading Report`. 选择性模式按照 [选择性报告模板](references/selective-report-format.md) 输出围绕问题的报告, 不补齐未研究的章节.

+ Evidence Index 的定位必须来自实际读取的内容, 严禁伪造; 无法定位的判断如实说明.
+ 完整模式的代码不可用或未检查时, 在 Paper -> Code Mapping 一节写明: `Official implementation was not available / not inspected.`, 不猜测代码结构.

## 操作边界

+ 不把第三遍写成更长的摘要, 不复述前两遍报告的全部内容.
+ 不逐段翻译论文.
+ 不为显得完整而填补不存在的细节; 缺失的 implementation details 如实写 Unknown / Not specified.
+ 不模拟具体 conference 的评分标准给出打分, 除非用户明确要求.
+ 研究延伸必须从论文的具体内容出发, 每个方向给出可检验的 hypothesis.
