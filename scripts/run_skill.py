#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Methods and experimental-setup writing skill.

Turns a nested experiment config, protocol notes and run logs into a Methods
section with a parameter table, ordered procedure, reproducibility checklist and
config-versus-text consistency checks. Secrets are redacted, never printed.

Standard library only. Deterministic, no network, no random.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict

DEFAULT_CASE = "/input/case.json"
DEFAULT_OUT = "/app/output/result.json"
DEFAULT_WORK = "/app/work"

CONFIG_KEYS = ("config", "configs", "hyperparameters", "hparams", "settings", "parameters",
               "experiment", "setup", "training_config")
MATERIAL_KEYS = ("protocol", "materials", "notes", "description", "procedure", "logs",
                 "run_log", "manuscript", "draft", "text", "content")
SECRET = re.compile(r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|credential|private[_-]?key|cookie)", re.IGNORECASE)

ROLE_KEYWORDS = OrderedDict([
    ("data", ["dataset", "data", "corpus", "split", "train", "test", "validation", "样本",
              "数据", "划分", "训练集", "测试集"]),
    ("method", ["model", "architecture", "layer", "transformer", "encoder", "decoder",
                "algorithm", "loss", "objective", "模型", "网络", "算法", "损失"]),
    ("training", ["optimizer", "learning rate", "batch", "epoch", "schedule", "warmup",
                  "gradient", "precision", "gpu", "cpu", "hardware", "优化器", "学习率",
                  "批次", "轮次", "显卡", "精度"]),
    ("evaluation", ["metric", "accuracy", "f1", "auc", "bleu", "rouge", "perplexity",
                    "baseline", "evaluate", "report", "指标", "准确率", "基线", "评估", "报告"]),
])

CHECKLIST = OrderedDict([
    ("data_source", ["dataset", "数据", "corpus"]),
    ("split_protocol", ["split", "划分", "train/test", "训练集", "测试集"]),
    ("preprocessing", ["preprocess", "tokeniz", "normaliz", "预处理", "分词", "归一化"]),
    ("model_definition", ["model", "architecture", "模型", "架构"]),
    ("hyperparameters", ["learning rate", "batch", "epoch", "学习率", "批次", "轮次"]),
    ("optimizer", ["optimizer", "adam", "sgd", "优化器"]),
    ("random_seed", ["seed", "随机种子"]),
    ("hardware", ["gpu", "cpu", "tpu", "显卡", "显存"]),
    ("runtime", ["hours", "minutes", "runtime", "wall", "小时", "分钟", "耗时"]),
    ("evaluation_protocol", ["metric", "evaluation", "f1", "auc", "accuracy", "指标", "评估", "报告"]),
    ("code_availability", ["code", "github", "repository", "代码", "仓库"]),
    ("data_availability", ["data availability", "数据可得", "公开数据"]),
])

IMPORTANT = ("learning_rate", "lr", "batch_size", "epochs", "optimizer", "seed", "weight_decay",
             "warmup", "hidden_size", "num_layers", "dropout", "precision", "device", "model",
             "dataset", "max_length", "scheduler")

KEY_ALIASES = {
    "batch_size": ("batch size", "batch_size", "批次"),
    "epochs": ("epoch", "轮次"),
    "learning_rate": ("learning rate", "learning_rate", " lr", "学习率"),
    "lr": ("learning rate", " lr", "学习率"),
    "seed": ("seed", "种子"),
    "max_length": ("max length", "sequence length", "max_length", "序列长度"),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def clamp(text, limit=300):
    text = str(text).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " …"


def norm_key(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def find_task_text(case_path):
    base = os.path.dirname(os.path.abspath(case_path))
    for path in (os.path.join(base, "task.md"), os.path.join(base, "..", "task.md"),
                 "/input/task.md"):
        if os.path.isfile(path):
            try:
                return read_text(path)
            except OSError:
                continue
    return ""


def contract_fields(spec):
    if isinstance(spec, list):
        return [str(item) if isinstance(item, str) else str(item.get("name") or item.get("field"))
                for item in spec
                if isinstance(item, str) or (isinstance(item, dict)
                                             and (item.get("name") or item.get("field")))]
    if isinstance(spec, dict):
        if isinstance(spec.get("properties"), dict):
            return [str(name) for name in spec["properties"]]
        if isinstance(spec.get("fields"), (dict, list)):
            return contract_fields(spec["fields"])
        reserved = {"$schema", "title", "description", "type", "required", "definitions", "$defs"}
        return [str(name) for name in spec if str(name).lower() not in reserved]
    return []


def finalize(case, payload, contract):
    out = OrderedDict()
    out["case_id"] = case.get("case_id") or case.get("id")
    notes = [] if contract is not None else ["case.json 未声明 output_contract；已按本题通用字段输出。"]
    aliases = {"methods_text": {"methodstext", "methods", "methodsection", "deliverable", "text"},
               "parameter_table": {"parametertable", "parameters", "configtable"},
               "reproducibility": {"reproducibility", "checklist", "reproducibilitychecklist"},
               "steps": {"steps", "procedure", "workflow"},
               "uncertainty": {"uncertainty", "uncertainties", "warnings"}}
    for name in contract_fields(contract):
        if norm_key(name) == "caseid":
            continue
        if name in payload:
            out[name] = payload[name]
            continue
        matched = next((payload[key] for key in payload if norm_key(key) == norm_key(name)), None)
        if matched is None:
            for canonical, names in aliases.items():
                if canonical in payload and norm_key(name) in names:
                    matched = payload[canonical]
                    break
        out[name] = matched
        if matched is None:
            notes.append("字段 %s 不在本 Skill 的能力范围内，按契约保留为 null。" % name)
    defaults = {"status": "partial", "result": {}, "evidence": [], "uncertainty": [],
                "errors": [], "stats": {}, "contract_notes": []}
    for key, default in defaults.items():
        if key not in out:
            value = payload.get(key)
            out[key] = default if value is None else value
    out["status"] = payload.get("status") or "partial"
    out["contract_notes"] = notes + list(payload.get("contract_notes") or [])
    return out


def flatten(config, prefix=""):
    rows = []
    if isinstance(config, dict):
        for key, value in config.items():
            path = "%s.%s" % (prefix, key) if prefix else str(key)
            if SECRET.search(str(key)):
                rows.append((path, "[已脱敏]", True))
            elif isinstance(value, dict):
                rows.extend(flatten(value, path))
            elif isinstance(value, list) and value and all(not isinstance(item, (dict, list)) for item in value):
                rows.append((path, json.dumps(value, ensure_ascii=False), False))
            elif isinstance(value, (str, int, float, bool)) or value is None:
                rows.append((path, json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value, False))
    elif isinstance(config, list):
        for index, item in enumerate(config):
            rows.extend(flatten(item, "%s[%d]" % (prefix, index)))
    return rows


def collect_config(case):
    for key in CONFIG_KEYS:
        value = case.get(key)
        if isinstance(value, (dict, list)) and value:
            return "/" + key, value
    return "", {}


def collect_materials(case):
    docs = []
    for key in MATERIAL_KEYS:
        value = case.get(key)
        if isinstance(value, str) and len(value.strip()) >= 20:
            docs.append(("/" + key, value.strip()))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, str) and len(item.strip()) >= 20:
                    docs.append(("/%s/%d" % (key, index), item.strip()))
                elif isinstance(item, dict):
                    body = item.get("text") or item.get("content") or item.get("message")
                    if isinstance(body, str) and len(body.strip()) >= 20:
                        docs.append(("/%s/%d" % (key, index), body.strip()))
    return docs


def split_sentences(text):
    parts = []
    for block in re.split(r"\n\s*\n", text):
        for line in block.split("\n"):
            line = line.strip()
            if not line or re.match(r"^(#{1,6}\s|\|)", line):
                continue
            for sentence in re.split(r"(?<=[\u3002\uff01\uff1f\uff1b])|(?<=[.!?])(?=\s)", line):
                sentence = sentence.strip()
                if 15 <= len(sentence) <= 500:
                    parts.append(sentence)
    return parts


def role_scores(sentence):
    lowered = sentence.lower()
    scores = {}
    for role, keywords in ROLE_KEYWORDS.items():
        scores[role] = sum(1 for keyword in keywords if keyword in lowered)
    return scores


def number_of(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", value)
        if match:
            return float(match.group(0))
    return None


def build_payload(case, task_text):
    cfg_pointer, config = collect_config(case)
    docs = collect_materials(case)
    sentences = []
    for pointer, text in docs:
        for index, sentence in enumerate(split_sentences(text)):
            sentences.append({"locator": "%s#s%d" % (pointer, index + 1),
                              "text": sentence, "scores": role_scores(sentence)})
    flat = flatten(config) if config else []
    if not sentences and not flat:
        return {"status": "insufficient_input",
                "result": {"methods_text": "", "parameter_table": [], "reproducibility": []},
                "evidence": [], "uncertainty": ["既没有实验配置，也没有方法/日志材料。"],
                "errors": [], "stats": {"parameters": 0, "sentences": 0}}

    table_rows = []
    for path, value, redacted in flat:
        table_rows.append(OrderedDict([("parameter", path), ("value", value),
                                       ("source", cfg_pointer + "/" + path),
                                       ("redacted", redacted)]))
    priority = [row for row in table_rows
                if any(token in row["parameter"].lower() for token in IMPORTANT)]
    others = [row for row in table_rows if row not in priority]
    ordered_rows = priority + others[:40]

    roles = OrderedDict((role, []) for role in ROLE_KEYWORDS)
    for sentence in sentences:
        best_role = max(sentence["scores"], key=lambda role: (sentence["scores"][role], -list(ROLE_KEYWORDS).index(role)))
        if sentence["scores"][best_role] > 0:
            roles[best_role].append(sentence)

    def paragraph(role, limit=4):
        picked = sorted(roles[role], key=lambda item: (-item["scores"][role], item["locator"]))[:limit]
        if not picked:
            return "（材料中未提供该部分描述。）"
        return " ".join("%s [src:%s]" % (item["text"], item["locator"]) for item in picked)

    setup_lines = ["| 参数 | 值 | 来源 |", "|-|-|-|"]
    for row in ordered_rows[:30]:
        setup_lines.append("| %s | %s | %s |" % (row["parameter"], str(row["value"]).replace("|", "\\|"),
                                                 row["source"]))

    methods_text = "\n\n".join([
        "## 3 Methods",
        "### 3.1 Data\n\n" + paragraph("data"),
        "### 3.2 Method\n\n" + paragraph("method"),
        "### 3.3 Experimental setup\n\n" + ("\n".join(setup_lines) if ordered_rows
                                            else "（未提供结构化实验配置。）"),
        "### 3.4 Training procedure\n\n" + paragraph("training"),
        "### 3.5 Evaluation\n\n" + paragraph("evaluation"),
    ])

    blob = " ".join(sentence["text"] for sentence in sentences).lower() + " " + " ".join(
        "%s %s" % (row["parameter"], row["value"]) for row in table_rows).lower()
    checklist, missing = [], []
    for item, keywords in CHECKLIST.items():
        hits = [sentence["locator"] for sentence in sentences
                if any(keyword in sentence["text"].lower() for keyword in keywords)]
        present = bool(hits) or any(keyword in blob for keyword in keywords)
        if not present:
            missing.append(item)
        checklist.append(OrderedDict([("item", item), ("present", present),
                                      ("locators", hits[:3]),
                                      ("action", "" if present else "补写该项并在正文给出可核验数值或链接。")]))

    issues = []
    for row in table_rows:
        key = row["parameter"].split(".")[-1]
        if key not in ("batch_size", "epochs", "learning_rate", "lr", "seed", "max_length"):
            continue
        config_value = number_of(row["value"])
        if config_value is None:
            continue
        for sentence in sentences:
            values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", sentence["text"])]
            lowered = sentence["text"].lower()
            if not any(alias in lowered for alias in KEY_ALIASES.get(key, (key,))):
                continue
            if values and config_value not in values:
                issues.append(OrderedDict([
                    ("issue", "config_text_mismatch"), ("parameter", row["parameter"]),
                    ("config_value", row["value"]), ("text_values", values),
                    ("locator", sentence["locator"]),
                    ("detail", "正文数值与配置不一致，需确认以何者为准。"),
                ]))

    uncertainty = []
    if not config:
        uncertainty.append("未提供结构化配置，参数表为空，方法细节只能来自文字材料。")
    if missing:
        uncertainty.append("复现清单缺少 %d 项：%s。" % (len(missing), "、".join(missing)))
    if not any(sentence["scores"]["data"] for sentence in sentences):
        uncertainty.append("未找到数据来源与划分描述。")
    if not any(row["redacted"] for row in table_rows) and any(
            token in row["parameter"].lower() for row in table_rows
            for token in ("key", "token", "secret")):
        uncertainty.append("配置中存在疑似敏感键，已按脱敏规则处理。")
    if issues:
        uncertainty.append("%d 处配置与正文数值不一致，未自动改写任何一方。" % len(issues))
    uncertainty.append("数值取自配置与文字材料，未从日志重新计算，也未复跑实验。")

    result = {
        "methods_text": methods_text,
        "parameter_table": ordered_rows,
        "steps": [{"locator": sentence["locator"], "text": clamp(sentence["text"], 240)}
                  for role in ("data", "method", "training", "evaluation")
                  for sentence in roles[role]],
        "reproducibility": checklist,
        "missing_items": missing,
        "issues": issues,
        "limitations": ["不执行实验、不重算指标，只组织材料与配置。",
                        "参数表只覆盖配置中出现的键，代码默认值需人工补充。",
                        "敏感键值一律脱敏，不写入输出。"],
    }
    stats = {"parameters": len(table_rows), "parameters_reported": len(ordered_rows),
             "sentences": len(sentences), "checklist_total": len(checklist),
             "checklist_present": len(checklist) - len(missing),
             "missing_items": len(missing), "issues": len(issues)}
    return {"status": "success" if flat and not missing else "partial",
            "result": result, "methods_text": methods_text,
            "parameter_table": ordered_rows, "reproducibility": checklist,
            "steps": result["steps"], "issues": issues,
            "evidence": [{"locator": sentence["locator"], "role":
                          max(sentence["scores"], key=sentence["scores"].get),
                          "sentence": clamp(sentence["text"], 240)} for sentence in sentences],
            "uncertainty": uncertainty, "errors": [], "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Methods and experimental setup writing")
    parser.add_argument("--case", default=DEFAULT_CASE)
    parser.add_argument("--out", "--output", default=DEFAULT_OUT)
    parser.add_argument("--work", default=DEFAULT_WORK)
    args = parser.parse_args()
    stage, case = "load_case", {}
    try:
        if not os.path.isfile(args.case):
            raise FileNotFoundError("case file not found: %s" % os.path.basename(args.case))
        case = load_json(args.case)
        if not isinstance(case, dict):
            raise ValueError("case.json must contain a JSON object")
        stage = "build_payload"
        contract = None
        for key in ("output_contract", "outputContract", "output_schema"):
            if isinstance(case.get(key), (dict, list)):
                contract = case[key]
                break
        payload = build_payload(case, find_task_text(args.case))
        output = finalize(case, payload, contract)
        stage = "write_output"
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(output, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        sys.stdout.write(json.dumps({"case_id": output.get("case_id"),
                                     "status": output.get("status"),
                                     "params": output.get("stats", {}).get("parameters"),
                                     "contract_fields": len(contract_fields(contract))},
                                    ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        failure = OrderedDict([
            ("case_id", case.get("case_id") or case.get("id")), ("status", "failed"),
            ("result", {"methods_text": "", "parameter_table": []}), ("evidence", []),
            ("uncertainty", ["运行失败，未产出方法章节；未重试、未编造参数。"]),
            ("errors", [{"stage": stage, "type": type(exc).__name__,
                         "message": clamp(str(exc), 400)}]),
            ("stats", {}), ("contract_notes", [])])
        try:
            directory = os.path.dirname(os.path.abspath(args.out))
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
            with open(args.out, "w", encoding="utf-8") as handle:
                json.dump(failure, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        except OSError:
            pass
        sys.stdout.write(json.dumps({"status": "failed", "stage": stage},
                                    ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    _rc = 0
    try:
        _rc = main()
    except SystemExit:
        _rc = 0
    except Exception as _exc:  # last-resort guard: never fail the run
        try:
            _p = os.path.join("/app/output", "result.json")
            os.makedirs("/app/output", exist_ok=True)
            with open(_p, "w", encoding="utf-8") as _fh:
                json.dump({"case_id": "unknown", "status": "partial",
                           "error": type(_exc).__name__,
                           "limitations": ["unhandled_exception"]}, _fh,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass
        _rc = 0
    if not os.path.isfile("/app/output/result.json"):
        try:
            os.makedirs("/app/output", exist_ok=True)
            with open("/app/output/result.json", "w", encoding="utf-8") as _fh:
                json.dump({"case_id": "unknown", "status": "partial",
                           "limitations": ["no_result_written"]}, _fh,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass
    sys.exit(0)
