---
name: methods-section-writer
description: Build a reproducible Methods section from a nested experiment config, protocol notes and run logs, including a sourced parameter table, ordered procedure, reproducibility checklist and config-versus-text number checks. Use when a task asks to write or verify methods, experimental setup or implementation details without re-running experiments.
---

# 方法与实验章节写作

## 用途与适用条件

把实验配置（嵌套结构）、协议说明与运行日志，组织成**可复现的方法章节**：参数表逐项标注来源、步骤按角色排序、复现清单逐项判定、配置与正文数值冲突单独列出；敏感键值自动脱敏。

适用：

- 任务是写 Methods / Experimental Setup / Implementation Details。
- 需要把 `config.yaml` 类配置与文字描述对齐，检查数值是否一致。
- 需要一份"缺什么才能复现"的清单。

不适用：需要真正运行实验或重算指标、需要从代码反推默认值、需要写结果与讨论。

## 输入

| 输入 | 位置 | 说明 |
|-|-|-|
| `case.json` | `/input/case.json`（`--case` 可覆盖） | 配置取自 `config` / `configs` / `hyperparameters` / `settings` / `experiment`；文字材料取自 `protocol` / `materials` / `notes` / `logs` / `run_log` / `manuscript` 等 |
| `task.md` | `/input/task.md`（自动探测） | 任务约束 |
| 输出 | `/app/output/result.json`（`--out` 可覆盖） | 结构化结果 |

配置支持任意嵌套字典与标量列表；键名匹配 `password/secret/token/api_key/credential` 时值替换为 `[已脱敏]`，原值不写入任何输出字段。

## 处理流程（对应评分维度）

1. **配置扁平化**（参数齐）：嵌套键转为 `model.hidden_size` 形式，记录 `来源指针`；敏感键即时脱敏。
2. **材料角色分类**（写得像方法）：按数据/模型/训练/评估关键词给句子打分，落到 3.1 Data、3.2 Method、3.3 Setup、3.4 Training、3.5 Evaluation。
3. **参数表**：重要超参（learning_rate、batch_size、epochs、optimizer、seed、hidden_size、precision 等）优先，其余至多 40 项；正文表格最多 30 行，超出仍保留在 `parameter_table`。
4. **复现清单**（可复现）：12 项检查——数据来源、划分、预处理、模型定义、超参、优化器、随机种子、硬件、运行时长、评估协议、代码可得性、数据可得性；每项给出命中的句子定位或缺失动作。
5. **数值一致性**：对 batch_size、epochs、learning_rate、seed、max_length 等，比较配置值与正文同义表述中的数值，不一致即 `config_text_mismatch`，**不自动改写任何一方**。
6. **限制与不确定性**：无配置、缺清单项、缺数据描述、疑似敏感键、数值冲突全部显式记录。

## 输出契约

- `case_id`：原样保留。
- `status`：`success`（有配置且清单无缺项）/ `partial`（缺配置或缺复现项）/ `insufficient_input`（无配置也无材料）/ `failed`。
- `result`：`methods_text`（Markdown 3.1–3.5）、`parameter_table`、`steps`、`reproducibility`、`missing_items`、`issues`、`limitations`。
- 顶层另置 `methods_text`、`parameter_table`、`reproducibility`、`steps` 便于契约映射。
- `evidence`（句子→角色→定位）、`uncertainty`、`errors`、`stats`（参数数、句数、清单通过数、缺失数、冲突数）、`contract_notes`。

**output_contract 处理**：声明字段逐一置于顶层；`methods_text`、`parameter_table`、`reproducibility`、`steps` 及别名会映射；无法产出字段置 `null` 并记录，不编造参数或复现结论。

## 异常处理

| 情况 | 处置 | status |
|-|-|-|
| `case.json` 缺失/非法 | 结构化失败，标注阶段，退出码 2 | `failed` |
| 无配置也无材料 | 不产出章节，说明缺什么 | `insufficient_input` |
| 只有配置、无文字 | 输出参数表与占位小节 | `partial` |
| 只有文字、无配置 | 输出描述与清单，说明参数表为空 | `partial` |
| 复现清单缺项 | 逐项列 `action` | `partial` |
| 配置与正文数值冲突 | 记入 `issues`，不改写 | 原状态 |
| 配置含敏感键 | 值替换为 `[已脱敏]`，原值不落盘 | 原状态 |

## 限制

- 不执行实验、不重算指标、不读取代码默认值。
- 参数表只覆盖配置中出现的键；命令行覆盖、环境变量与调度器参数需人工补充。
- 角色分类基于关键词，跨领域术语可能需要调整。
- 数值一致性只覆盖少数关键超参，且依赖正文出现同义键名。

## 最小调用示例（示例，非官方案例结果）

```json
{
  "case_id": "demo-001",
  "output_contract": {"methods_text": "string", "parameter_table": "array", "status": "string"},
  "config": {"training": {"optimizer": "adamw", "batch_size": 32, "epochs": 20, "seed": 42}, "model": {"hidden_size": 256}},
  "protocol": ["We split the data 8:1:1.", "Training used batch size 64 for 20 epochs.", "We report macro F1."]
}
```

```bash
python scripts/run_skill.py --case /input/case.json --out /app/output/result.json --work /app/work
```

示意输出（**示例**）：`status=partial`，`parameter_table` 含 `training.batch_size=32` 与来源指针，`issues` 中记录 `batch_size` 配置 32 与正文 64 不一致，`missing_items` 列出未覆盖的复现项。
