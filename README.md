# Salesforce Security Benchmark — Pilot (10 scenarios)

MSc Research Project: *AI-Augmented Salesforce Security Hardening*.
Pilot of the 150-scenario benchmark: 5 categories × 2 scenarios (1 vulnerable + 1 secure).

## Structure

```
scenarios/<ID>/force-app/main/default/   Apex + metadata (what the tools see)
scenarios/<ID>/ground_truth.json         answer key for that scenario (never sent to tools)
ground_truth.json                        all answer keys in one file
prompts/                                 fixed prompt templates (system, guidance, structured checks)
scripts/run_code_analyzer.sh             baseline: Salesforce Code Analyzer, all Security rules
scripts/bedrock_runner.py                LLM runs on Amazon Bedrock, conditions A–E
scripts/score.py                         compares any tool's output with the answer key
results/code_analyzer/                   raw Code Analyzer output per scenario
results/llm/dry_run/<condition>/         the exact prompts each condition sends (for checking)
results/scores/                          per-scenario CSV + summary JSON
```

Scenario IDs: `C<category>-V<n>` = vulnerable, `C<category>-S<n>` = secure.

| ID | Category | Label | Severity | Difficulty |
|---|---|---|---|---|
| C1-V01 | SOQL injection | vulnerable | High | easy |
| C1-S01 | SOQL injection | secure (dynamic query, but bound + allow-list) | – | medium |
| C2-V01 | CRUD/FLS | vulnerable | Medium | medium |
| C2-S01 | CRUD/FLS | secure (USER_MODE + update as user) | – | medium |
| C3-V01 | Sharing | vulnerable (without sharing; CRUD/FLS done correctly) | High | medium |
| C3-S01 | Sharing | secure (inherited sharing as entry point) | – | hard |
| C4-V01 | Excessive permissions | vulnerable (Modify/View All Data for tier-1 agents) | High | hard |
| C4-S01 | Excessive permissions | secure (Export Reports matches purpose) | – | medium |
| C5-V01 | Guest user | vulnerable (guest can call without-sharing method returning Contacts) | High | hard |
| C5-S01 | Guest user | secure (intended public catalogue) | – | medium |

## Run it

**1. Code Analyzer baseline** (needs Salesforce CLI, Java 11+):
```bash
npm install -g @salesforce/cli
sf plugins install code-analyzer
scripts/run_code_analyzer.sh
python3 scripts/score.py code_analyzer
```

**2. LLM runs on Bedrock** (AWS credentials from Learner Lab; model access enabled in the Bedrock console):
```bash
pip install -r requirements.txt
python3 scripts/bedrock_runner.py --model-id <MODEL_ID> --condition A --dry-run   # check prompts first, no cost
python3 scripts/bedrock_runner.py --model-id <MODEL_ID> --condition A --rep 1 --region eu-west-1
python3 scripts/score.py llm results/llm/<MODEL_ID>__A__rep1.jsonl
python3 scripts/score.py union results/llm/<MODEL_ID>__A__rep1.jsonl              # Code Analyzer ∪ LLM
```
Conditions: A Apex only · B + metadata · C + security guidance · D + structured checks · E + Code Analyzer findings.
Temperature defaults to 0. Each run records latency and input/output tokens for the cost analysis.

## Pilot baseline: Code Analyzer v5.16.0 (all 40 Security rules)

| Scenario | Truth | Code Analyzer | Outcome |
|---|---|---|---|
| C1-V01 | vulnerable | ApexSOQLInjection | TP, category correct |
| C2-V01 | vulnerable | ApexCRUDViolation, ApexFlsViolation | TP, category correct, severity High vs Medium |
| C3-V01 | vulnerable | DatabaseOperationsMustUseWithSharing (+ ApexFlsViolation) | TP, category correct |
| C4-V01 | vulnerable | nothing | **FN** — no rule reads permission-set grants |
| C5-V01 | vulnerable | CRUD/FLS + sharing rules | TP, but **category wrong**: it never sees the guest profile |
| all 5 secure | secure | nothing | TN (no false positives, incl. the tricky cases) |

**TP 4 · FP 0 · FN 1 · TN 5 → precision 1.00, recall 0.80, F1 0.89; category accuracy 0.75.**

Pilot only (n = 10): these numbers show the pipeline works, not a research result.
Note: `ApexFlsViolation` and `DatabaseOperationsMustUseWithSharing` come from the Graph Engine (sfge), tagged DevPreview.

## Rules for adding scenarios

- Every scenario has at least one Apex class, so Condition A always has input.
- Each answer key cites one official Salesforce source and one CWE ID.
- Secure twins should be "tricky": code that looks risky but is safe.
- Never put hints in file names, comments or descriptions that give the answer away beyond what a real org would contain.
# SF-security-benchmark
