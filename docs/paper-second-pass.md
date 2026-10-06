# paper-second-pass 使用文档

`paper-second-pass` 对用户提供的学术论文执行第二遍理解阅读: 建立方法的准确 mental model (数据流, 训练与推理, 关键机制, 与 baseline 的结构差异), 并将每个主要 claim 映射到支撑实验, 审计 baselines, metrics, ablations, generalization 和 cost 是否让逻辑链闭合. 输出一份 16 节结构的精读报告 (Second-Pass Reading Report), 并给出是否值得进入第三遍 (逐式推导, 查证明, 复现) 的明确建议.

## 使用前提

+ 将 [skill 目录](../skills/paper-second-pass/SKILL.md) 连同 [报告模板](../skills/paper-second-pass/references/report-format.md) 一起提供给支持 skill 的工具, 保持两者的相对路径.
+ 执行工具能够读取用户提供的论文内容, 例如 PDF 文件, arXiv 页面或论文全文文本.
+ 第一遍报告 (Paper Snapshot) 可以可选提供, 作为阅读起点; 未提供时不强制先执行 paper-first-pass.
+ 逐个推导公式, 检查证明, 读取全部实现细节或复现代码属于第三遍阅读, 不在本 skill 范围内.

下方示例使用 `$paper-second-pass` 表示调用该 skill. 如果所用工具不支持这种调用形式, 可以直接指定 `skills/paper-second-pass/SKILL.md` 的实际路径, 要求按其中的指导处理.

## 调用示例

### 接续第一遍报告精读

```text
这是我之前的第一遍阅读报告: ~/notes/some-paper-snapshot.md
这是论文原文: ~/Downloads/some-paper.pdf
使用 $paper-second-pass 精读这篇论文.
```

预期结果是 skill 以第一遍报告为起点, 但回原文验证其中的关键判断; 输出 `# Second-Pass Reading Report`, 包含 Executive Understanding, Method Mental Model, Experiment -> Claim Map, Third-Pass Decision 等 16 节, 头部 `First-pass verdict` 字段填写第一遍报告的结论.

### 直接提供 PDF 精读

```text
使用 $paper-second-pass 精读这篇论文: ~/Downloads/another-paper.pdf
```

预期结果是 skill 不要求先跑第一遍, 直接按第二遍范围阅读论文并输出完整 16 节报告, 头部 `First-pass verdict` 字段留空或说明未提供.

### 提供 arXiv 链接并附关注点

```text
使用 $paper-second-pass 精读这篇论文: https://arxiv.org/abs/XXXX.XXXXX
我怀疑提升来自更大的算力而不是方法本身, 帮我确认.
```

预期结果是 skill 在 Experiment -> Claim Map 的 Caveat 列重点检查 compute, data, parameter count 等 confounders 是否被控制, 并在 Most Important Results 和 Third-Pass Decision 中回应这一关注点.

## 异常处理

+ PDF 内容解析失败时, skill 明确指出失败并停止, 不根据论文标题或常识猜测内容继续输出报告.
+ 第一遍报告与论文原文不一致时, 以原文为准, 并在报告中指出差异.
+ 论文为 theory, survey, benchmark 等没有标准实验部分的类型时, 按论文类型调整 Experiment -> Claim Map 等相关节的内容, 但仍输出 16 节结构和第三遍阅读建议.
+ 关键判断无法在论文中给出定位时, skill 如实说明, 不伪造页码, section, figure 或 table 编号.
+ 必答项或固定小节对论文类型不适配时, 注明不适用并按适合该论文的形式处理, 不硬凑内容.

## 进一步阅读

+ [执行流程](../skills/paper-second-pass/SKILL.md): 输入确认, 阅读范围, 方法必答问题与操作边界.
+ [报告模板](../skills/paper-second-pass/references/report-format.md): 16 节完整结构与措辞要求.
+ [上游 skill](paper-first-pass.md): 已决定精读之前的第一遍 triage 阅读.
+ [返回仓库说明](../README.md).
