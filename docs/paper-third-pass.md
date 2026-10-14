# paper-third-pass 使用文档

`paper-third-pass` 对用户提供的学术论文执行第三遍深度阅读: 重建论文的完整逻辑链, 深入分析核心数学与关键机制, 逐条审计实验证据, 生成可执行的复现蓝图, 并从审稿人视角给出批判性评估与研究延伸方向. 完整模式输出 20 节结构的 Deep Reading Report; 选择性模式只围绕指定问题给出分析与证据, 目标是让用户达到 "理解 -> 验证 -> 批判 -> 复现 -> 修改 -> 使用" 这篇论文的程度, 而不是生成更长的摘要.

## 使用前提

+ 将 [skill 目录](../skills/paper-third-pass/SKILL.md) 连同 `references/` 中的完整和选择性报告模板一起提供给支持 skill 的工具, 保持两者的相对路径.
+ 执行工具能够读取用户提供的论文内容, 例如 PDF 文件, arXiv 页面或论文全文文本.
+ 论文原文必需, 只有代码或前序报告时需先获取明确对应的原文. 代码仓库是可选输入: 提供官方代码时按阅读范围检查相关实现; 未提供或未检查时在完整报告的 Paper -> Code Mapping 或选择性报告的阅读范围中说明, 不猜测代码结构.
+ 第二遍报告 (Second-Pass Reading Report) 可以可选提供, 作为阅读起点并继承第三遍优先级; 未提供时不强制先执行 paper-second-pass.

下方示例使用 `$paper-third-pass` 表示调用该 skill. 如果所用工具不支持这种调用形式, 可以直接指定 `skills/paper-third-pass/SKILL.md` 的实际路径, 要求按其中的指导处理.

## 调用示例

### 接续第二遍报告深读

```text
这是我之前的第二遍精读报告: ~/notes/some-paper-second-pass.md
这是论文原文: ~/Downloads/some-paper.pdf
使用 $paper-third-pass 深度阅读这篇论文.
```

预期结果是 skill 以第二遍报告为起点并继承其 Third-Pass Decision 中的优先级, 但关键判断回原文验证. 建议为 `SELECTIVE DEEP READ` 且提供具体问题时输出选择性报告; 其他情况默认完整报告, 头部 `Second-pass verdict` 填写第二遍结论.

### 直接提供 PDF 深读

```text
使用 $paper-third-pass 深度阅读这篇论文: ~/Downloads/another-paper.pdf
```

预期结果是 skill 不要求先跑前两遍, 直接完整阅读论文 (含 appendix 的 implementation details 与 hyperparameters) 并输出完整 20 节报告; Paper -> Code Mapping 一节写明未提供或未检查代码, 复现蓝图中缺失的配置如实列入 Missing information.

### 提供论文与官方代码仓库

```text
论文: ~/Downloads/some-paper.pdf
官方代码仓库: ~/code/some-paper-official
使用 $paper-third-pass 深度阅读这篇论文, 并用代码验证论文描述.
```

预期结果是 skill 同时阅读论文与代码核心实现 (model definition, training loop, loss, evaluation, default config), 在 Paper -> Code Mapping 中给出概念到代码位置的映射; 若实现与论文公式或描述冲突, 在报告中显式指出冲突点.

### 围绕指定问题深读

```text
使用 $paper-third-pass 阅读这篇论文: ~/Downloads/some-paper.pdf
仅深入公式 (5) 的推导, 以及表 3 是否控制了训练预算, 不做全篇深读.
```

预期结果是按阅读范围, 逐问题分析, 未解决问题和证据索引组织的报告. 每个问题包含结论, 推理, 原文证据和限制, 不输出完整 20 节, 不把未检查范围写成已验证.

用户未指定范围, 且第二遍建议为 `SELECTIVE DEEP READ` 并给出具体问题时, 自动采用此模式. 用户要求完整深读时优先完整模式, 无其他明确范围时也默认完整模式. 明确要求选择性深读但没有问题时先询问关注点.

## 异常处理

+ PDF 内容解析失败时, skill 明确指出失败并停止, 不根据论文标题或常识猜测内容继续输出报告.
+ 未提供代码仓库或代码无法访问时, 在相应模式的报告中说明未提供, 无法访问或未检查, 不猜测代码结构.
+ 代码实现与论文描述冲突时, skill 在报告中显式指出冲突点与双方内容, 不默认任何一方正确.
+ 论文为 theory, survey, benchmark 等类型时, 不适配的节 (如没有 experiment 或 training) 注明 `Not applicable for this paper type`, 不硬凑内容, 完整模式的其余节仍按 20 节结构输出, 选择性模式则说明该类型下相关问题的证据边界.
+ 关键判断无法在论文或代码中给出定位时, skill 如实说明, 不伪造页码, section, figure, table 或代码位置.
+ 论文未给出的实现细节与超参, skill 写 Unknown 或 Not specified, 不虚构 implementation details.

## 进一步阅读

+ [执行流程](../skills/paper-third-pass/SKILL.md): 输入确认, 完整阅读范围, 八个目标与操作边界.
+ [报告模板](../skills/paper-third-pass/references/report-format.md): 20 节完整结构, 固定小节块与反作弊条款.
+ [选择性报告模板](../skills/paper-third-pass/references/selective-report-format.md): 限定问题的分析和未检查范围.
+ [上游 skill](paper-second-pass.md): 第二遍理解阅读, 其 Third-Pass Decision 是本 skill 的入口.
+ [返回仓库说明](../README.md).
