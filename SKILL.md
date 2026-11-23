---
name: bohr-writing-methods-experiments
description: 当需要完成方法与实验章节写作并产出可复核结果时使用。本题范围：写作09｜方法与实验章节写作。题目家族：学术写作（academic-writing）。任务要求：依据研究记录、配置文件、日志与代码说明，把散落的实验材料整理成可执行的方法与实验章节，覆盖方法步骤、实验设置、参数与来源、数据集与划分、对照实验、可复现性与限制条件；参数取值、数据集版本与划分、训练与评测条件必须与材料一致，不补造数值；材料未报告时明确说明，不能联网补写。输出可编辑的目标产物、事实/证据映射、修改或生成记录和人工确认项；不得虚构材料外事实。产出 result.json，其中包含运行时 output_contract 要求的全部字段与 case_id，每条结论附带原文证据（段落定位 + 短引），无法从材料判断的部分如实写入 uncertainty 而非编造。
---

# 写作09｜方法与实验章节写作

## 用途

本题属于 **academic-writing / writing** 赛道，聚焦方法与实验章节写作。目标能力：把零散的实验记录、配置文件、日志与代码说明整理成有序、可执行、可复做的章节成稿，并给出逐条可核验的来源与修改记录。

本题重点关注四个问题：**写得全**（关键步骤、实验设置、参数、数据集与划分、对照与重复次数是否都写到）、**写得准**（参数取值、数据集版本与划分、训练与评测条件是否与配置文件、日志和代码一致，有没有为了段落顺畅而补出的数值）、**做得着**（读者能否按章节中的步骤与参数复做实验，版本、环境、随机种子和命令是否给全）、**说得住**（材料的缺口和不确定处是否被显式标出并交作者确认，限制条件是否指向具体的失效场景而不是套话）。

本 Skill 只做确定性的文本取证与结构化整理：不运行训练、不联网、不推断材料未记录的参数。

## 任务要求（来自题面）

本案例用于“写作 09｜方法与实验章节写作”。依据固定科研材料完成指定的学术写作或结构化写作产物，保持事实和来源一致；对材料不足、冲突和需要人工确认的内容明确标注。

可选择的方向包括：方法步骤（把零散实验记录整理成有序、可执行的步骤序列，写清每步的输入、操作、输出与判断条件）；实验设置（分开描述训练、验证与测试流程，写清硬件、软件版本、运行环境、随机种子与重复次数）；参数与来源（生成带名称、取值、单位、作用对象和来源的参数表，并把正文数值与表格对齐）；数据集与划分（名称、版本、规模、预处理、划分比例与随机方式，以及各子集用途）；对照实验（基线对象及其版本、对照条件是否同预算、评价指标与统计方式）；可复现性与限制条件（代码版本、环境、命令、数据获取方式，以及具体失效场景与适用范围）。

本题可预知的契约键（**实际以运行时 `/input/case.json` 为准**，下表仅供预热）：

- `case_id`
- `deliverable`
- `evidence_map`
- `change_log`
- `preserved_facts`

## 交付物

result.json（契约齐全）、可编辑方法与实验章节稿、evidence_map、change_log、参数与格式核对清单、材料缺口自报。

交付物的**内容契约**由运行时 `output_contract` 决定（见下）；下面「交付物落盘要求」给出的是必须真实存在的**文件**。

## 执行方式

入口脚本：`scripts/sk_entry.py`。它会读取 `/input`，产出 `/app/output/result.json`。

```bash
# 在案例环境中执行（Harbor 会自动调用；手动复现同一条命令）
python /skills/weekly-skill/scripts/sk_entry.py \
  --input /input --work /app/work --out /app/output
```

执行结束后必须存在且可解析：

- `/app/output/result.json` —— 契约字段齐全的最终结果
- `/app/output/run-review.md` —— 人类可读的证据索引与不确定性清单（复核用）

### 单次运行即产出完整交付（判断内置，可选覆盖）

脚本是**确定性**的，但**不是只做取证的半成品**：一次运行就完成
「读材料 → 建证据索引 → 抽出术语定义 / 结论句 / 章节篇幅预算 / 一致性发现
→ 逐字段抽取（当 `/input/target-fields.json` 存在）→ 选取关键事实锚点
→ 给出实质判断（claims / answers）」。正常用法只有一条命令：

```bash
python /skills/weekly-skill/scripts/sk_entry.py \
  --input /input --work /app/work --out /app/output
```

- **判断内置**：哪条是定义、哪句是结论、每个章节该写多少、哪些术语/编号
  不一致、哪些数值/单位/图表/引用不能丢，都由本 Skill 基于材料判定，并逐条
  挂段落定位与逐字短引；实质交付物成形即 `status=answered`。
- **reading 字段表**：若 `/input/target-fields.json` 存在，逐 `field_id` 抽取并
  给出 reported / not_reported / source_conflict / extraction_failed 四态；该清单
  是任务说明而非论文材料，不会被当正文读入证据索引。
- 材料不足时才停在 `partial`，并在 `status_reason` 写明**具体**缺什么
  （而不是"等 Agent 判断"）。

**可选覆盖**（只有执行 Agent 想给出更强判断时才需要）：把判断写到
`/app/work/agent_judgement.json`，或直接改 `/app/output/result.json`，再跑一次；
脚本会逐条校验引文后合并，未通过校验的条目退回并记录原因。判断文件结构：

```json
{
  "case_id": "必须与 case.json 一致",
  "claims": [
    {"text": "你判断为结论的陈述",
     "evidence": [{"paragraph_id": "P002", "quote": "原文里逐字出现的片段"}]}
  ],
  "answers": [
    {"question": "被问的问题", "answer": "你的回答",
     "evidence": [{"paragraph_id": "P002", "quote": "原文里逐字出现的片段"}]}
  ],
  "deliverable": "本题最终交付物的正文",
  "contract_fields": {"契约键名": "该键的内容（可选，直接填契约键）"},
  "uncertainties": [
    {"kind": "machine_readable_category", "item": "具体对象",
     "detail": "客观描述", "resolution": "你做了什么或为何无法继续"}
  ]
}
```

**覆盖时的校验闸门（脚本强制执行）**：

- 每条 `quote` 必须能在材料原文里**逐字找回**（允许空白差异）—— 找不到就**退回**，
  并把退回理由写进 `uncertainty`；
- 每条 claim / answer 必须至少有一个证据锚点 —— 没有锚点的条目被退回；
- `contract_fields` 的值不能是 `null` 或空容器 —— 空值被退回；
- 被退回的条目**不会**进入最终结果，脚本保留自己的确定性抽取作为兜底。

> 判断可以自由，**证据不可以自由**。这条闸门是本 Skill 的可信度基础。
> 跳过覆盖不会降级 —— 脚本自己的判断就是最终判断。

### 脚本职责

| 脚本 | 职责 |
|---|---|
| `scripts/sk_entry.py` | 入口：定位输入、发现材料、执行 `topic.run()`、装配 `result.json`、自检并写复核产物 |
| `scripts/sk_base.py` | 公共库：契约解析、材料发现、证据构造、结果装配、自检工具 |
| `scripts/topic.py` | 题目逻辑：读材料 → 建证据索引 → 按契约键名语义产出字段 → 校验并合并你的判断 |
| `scripts/specialize.py` | reading / writing 引擎：逐 `field_id` 抽取（四态状态）；可编辑稿件 + 改动记录 + 来源映射 |
| `scripts/artifacts.py` | graphics 引擎：实体—连接—步骤 IR → 分层 SVG → 渲染 PNG + 来源记录 |
| `scripts/pptxgen.py` | slides 引擎：stdlib-only 真实 PPTX + 逐页 SVG/PNG + 独立讲稿备注 |

**这些引擎会真的写文件。** 每条赛道具体落盘哪些文件、每个文件里有什么、
如何回挂到契约键，见 `references/artifact-pipeline.md`。

### 运行时契约是唯一权威

`output_contract` **只在运行时可见**（`/input/case.json`）。
不要硬编码任何字段名，也不要凭题面示例臆造字段：

1. 读取 `/input/case.json` 的 `output_contract`；
2. 对每个契约键，按**键名语义**判断它应该承载什么（证据 / 结论 / 不确定性 /
   交付物 / 覆盖度 / 变更记录 …）；
3. 产出对应内容，**不允许**留下 `null` 或"未产出"占位；
4. 若该键确实无法从材料得出，填入结构化的"无法判断"条目（带 `kind`、`item`、
   `detail`、`resolution`），而不是留空。

## 交付物落盘要求

除 `result.json` 外，**可编辑的交付物源文件与其渲染预览必须真实存在**：

| 赛道 | 必须落到 `/app/output` 的文件 |
|---|---|
| writing | `result.json`（契约齐全的结构化结果） |
| writing | `manuscript.md` —— 真实可编辑稿件，章节结构取自材料自身标题 |
| writing | `change-log.md` —— 逐条 before/after 改动记录 + 锚点守恒检查 |
| writing | `evidence-map.json` —— 章节 → 段落 / 锚点的来源映射，含**逐条锚点定位**（文件 + 行号 + 段落 id + 原文短引）与关键论断清单 |
| writing | `edit-targets.json` —— 逐条编辑目标回执（若提供 workorder） |
| writing | `qa-report.json` —— 逐节锚点守恒统计 + edit-target 状态 + 人工待核清单 |
| writing | `format-spec-checklist.json` —— 格式规格逐项核对清单：栏数 / 字号 / 行距 / 页边距 / 标题层级 / 图表题注 / 参考文献样式 / 导出格式等，附出处文件、行号与原文短引；材料未写明的记为缺失 |
| writing | `anomaly-report.json` —— 材料缺口与异常自报：格式规格缺失 / 冲突、锚点守恒异常、待人工确认项 |

平台提供的 `office-renderer` / `pdf-render-tool` / `latex-compiler` 可用来渲染预览。
**只有规格描述、没有真实文件，等于没交付** —— 评审要打开文件看。

### 导出前合规检查（pre-export compliance）

导出件落盘后，本 Skill 会**自动核对**并在 `*-export-checks.json` 里留档，
让评审不必逐个打开文件猜：

| 检查维度 | 记什么 |
|---|---|
| 目标格式 | 期望的 SVG / PNG / PDF 是否齐全、各自字节数、是否是**真矢量** |
| 画布与分辨率 | 像素尺寸 → pt → mm 换算，实测 dpi，目标 dpi |
| 字体 | 字体清单、嵌入情况、中文回退策略、是否存在方框/缺字风险 |
| 色彩空间 | 色彩空间标注（sRGB 等）与是否有嵌入配置 |
| 线宽 / 分层 | 线宽是否过细、图层是否可拆、图层清单 |
| 数据一致性 | 图上出现的数值与源数据表的比对结果 |
| 讲稿隔离 | 备注文字是否混进页面文字（逐页最大重叠片段） |
| 人工确认 | 需人眼确认的项一律标 `pending_human_review`，**不代签** |

失败的检查项会**原样保留为 fail**，不会被改写成通过；不可用的工具（如运行时
没有矢量转换器或 LibreOffice）也如实记为 `unavailable`，不做假成功。

## 质量红线

- 参数取值、数据集版本与划分、随机种子、重复次数、单位与硬件配置在整理后**逐字保持**
- 每个参数都要能指回**配置文件、日志、代码或作者说明**中的具体位置，而不是只给一个数值
- 材料未记录的参数与步骤不补写；缺失、冲突与待确认项逐条进入 `change_log` / `uncertainty`
- 限制条件必须落到具体失效场景与适用范围，不用“存在一定局限”一类套话替代
- 正文数值与参数表必须对齐；发现不一致时列出两处出处，由人工裁决

通用红线（违反即失分）：

- **不编造**：材料没有的数字、引用、图表、方法、结论，一律不写。写不出来就进
  `uncertainty`，并在 `status_reason` 里说明。
- **可回溯**：每条结论必须能指回原文的段落 id 与短引；引文必须是原文片段，
  不做改写、不做拼接。
- **不提前交卷**：材料可能读不全。若只读到部分文件，`status` 应为 `partial`，
  并在 `coverage.not_read` 写明未读的部分。
- **不自评**：不要在结果里写"质量良好""得分很高"这类自评语句。

## 失败与边界

| 情况 | 正确处理 |
|---|---|
| 材料是扫描件、无文本层 | 用 `scripts/sk_base.py` 的 PDF 解析；仍无文本则 `status=unsupported` 并在 `uncertainty` 写明"无文本层" |
| 材料是图片/图表 | 用平台提供的 `pdf-render-tool` / `ocr-tool`；OCR 结果标注为推断 |
| 材料格式未知 | 记录文件路径与可读性，不猜测内容 |
| 契约键无法解读 | 产出该键的结构化说明而非空值，并记录在 `uncertainty` |

详见 `references/failure-modes.md` 与 `references/evidence-discipline.md`。

## 一致性清单产出（v15）

引擎在同一次运行里从已加载材料确定性地产出下列清单，条目均为逐字引文 +
段落/来源定位，不做语义改写、不编造：

| 产物 | `result.json` 键 | 依据 |
|---|---|---|
| 术语表 | `glossary` | 显式定义句式、缩写全称展开、高频缩写兜底（标注 `first_use_context`） |
| 符号与单位 | `symbols`、`units` | 希腊字母、下标变量与常见单位串 |
| 结论清单 | `conclusions` | 因此/综上/结果表明/we conclude 等提示句 |
| 章节预算 | `section_plan` | 大纲或 Markdown 标题；无大纲时 `derived: true` |
| 跨章一致性 | `consistency_audit` | 术语写法变体、图表编号重复或跳号、重复定义 |
| 术语-章节图 | `graph` | 术语为节点，出现章节为边 |

材料中确实没有定义句或结论句时，对应列表为空，并在 `uncertainty` 写
`no_explicit_definitions` 说明原因；不要为了填满字段而杜撰条目。

## 自检

`result.json` 写完后由 `scripts/sk_entry.py` 自动自检（结构、契约覆盖、
证据完整性）。自检失败时以 `partial` 提交并在 `status_reason` 写明原因，
不要伪造 `answered`。

```bash
python /skills/weekly-skill/scripts/sk_selftest.py --input /input
```

## 参考

- `references/evidence-discipline.md` —— 证据与不确定性纪律
- `references/contract-handling.md` —— 运行时契约的读法与字段语义表
- `references/two-phase-workflow.md` —— 两阶段工作流协议与校验闸门
- `references/failure-modes.md` —— 常见失败模式与正确退路
- `references/artifact-pipeline.md` —— 每条赛道真实落盘哪些文件、怎么回挂契约键
- `assets/result-schema.md` —— `result.json` 的字段说明
- `assets/policy.json` —— 不编造承诺与来源声明
- `examples/demo-case/` —— 一个可离线复现的最小案例
