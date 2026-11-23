# Runtime contract

Bohrium Playground Period 4 submission — challenge `product-arena-05-64faa4a2` (track: `academic-writing`).

This repository holds the complete skill package for the challenge: the skill
definition, its executable entry point and all supporting scripts. No precomputed
answers, private data or credentials are included.

## Skill

- Name: `methods-section-writer`
- Summary: Build a reproducible Methods section from a nested experiment config, protocol notes and run logs, including a sourced parameter table, ordered procedure, reproducibility checklist and config-versus-text number checks. Use when a task asks to write or verify methods, experimental setup or implementation details without re-running experiments.

## Contents

| File |
|------|
| `SKILL.md` |
| `scripts/run_skill.py` |
| `README.md` |

## How to run

```bash
python scripts/run_skill.py --case /input/case.json --output /app/output/result.json
```

The entry point is `SKILL.md`; input/output contracts, error handling and a minimal
usage example are documented there.

## Notes

- Pure Python standard library; no network access required.
- The result JSON keeps the input case id, the main results, per-item evidence,
  a run status and an uncertainty section.
