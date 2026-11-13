"""Score tool predictions against the benchmark ground truth.

Usage:
  python scripts/score.py code_analyzer                 # Salesforce Code Analyzer baseline
  python scripts/score.py llm results/llm/<run>.jsonl   # an LLM run from bedrock_runner.py
  python scripts/score.py union results/llm/<run>.jsonl # Code Analyzer OR LLM (post-hoc union)

Writes results/scores/<name>_per_scenario.csv and results/scores/<name>_summary.json.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRUTH = {t["scenario_id"]: t for t in json.loads((ROOT / "ground_truth.json").read_text())}

# Code Analyzer rule -> benchmark category (rules with no mapping count as detection only)
CA_RULE_CATEGORY = {
    "ApexSOQLInjection": "C1",
    "ApexCRUDViolation": "C2",
    "ApexFlsViolation": "C2",
    "ApexSharingViolations": "C3",
    "DatabaseOperationsMustUseWithSharing": "C3",
}
CA_SEVERITY = {1: "High", 2: "High", 3: "Medium", 4: "Low", 5: "Low"}


def code_analyzer_predictions():
    preds = {}
    for sid in TRUTH:
        f = ROOT / "results" / "code_analyzer" / f"{sid}.json"
        violations = json.loads(f.read_text()).get("violations", []) if f.exists() else []
        sec = [v for v in violations if "Security" in v.get("tags", [])]
        preds[sid] = {
            "vulnerable": bool(sec),
            "categories": sorted({CA_RULE_CATEGORY.get(v["rule"], "other") for v in sec}),
            "severity": max((CA_SEVERITY[v["severity"]] for v in sec), key=["Low", "Medium", "High"].index, default="None"),
            "detail": "; ".join(f'{v["rule"]}@L{v["locations"][v.get("primaryLocationIndex", 0)].get("startLine")}' for v in sec),
        }
    return preds


def repair_json(raw):
    """Second-chance parse of a model's raw answer.
    Fixes formatting slips only (e.g. \\' which is not a valid JSON escape); never changes content."""
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    text = m.group(0)
    for candidate in (text, re.sub(r'\\(?!["\\/bfnrtu])', "", text)):
        try:
            out = json.loads(candidate)
            return out if isinstance(out, dict) else None
        except json.JSONDecodeError:
            continue
    return None


OUTPUT_STATUS = {}  # scenario_id -> "ok" | "repaired" | "invalid", filled by llm_predictions


def llm_predictions(path):
    preds = {}
    OUTPUT_STATUS.clear()
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out, status = rec.get("output"), "ok"
        if not isinstance(out, dict):
            out = repair_json(rec.get("raw", ""))
            status = "repaired" if out is not None else "invalid"
            out = out or {}
        OUTPUT_STATUS[rec["scenario_id"]] = status
        findings = out.get("findings", []) or []
        sev_rank = ["None", "Low", "Medium", "High"]
        detail = "; ".join(f.get("title", "") for f in findings)
        if status != "ok":
            detail = f"[{status.upper()}] {detail}"
        preds[rec["scenario_id"]] = {
            # an invalid (unparseable / truncated) answer is scored as "not vulnerable", and reported separately
            "vulnerable": bool(out.get("vulnerable")),
            "categories": sorted({f.get("category", "other") for f in findings}),
            "severity": max((f.get("severity", "None") for f in findings), key=lambda s: sev_rank.index(s) if s in sev_rank else 0, default="None"),
            "detail": detail,
        }
    return preds


def union(a, b):
    out = {}
    rank = ["None", "Low", "Medium", "High"]
    for sid in TRUTH:
        x, y = a.get(sid, {}), b.get(sid, {})
        out[sid] = {
            "vulnerable": x.get("vulnerable", False) or y.get("vulnerable", False),
            "categories": sorted(set(x.get("categories", [])) | set(y.get("categories", []))),
            "severity": max(x.get("severity", "None"), y.get("severity", "None"), key=rank.index),
            "detail": f'CA: {x.get("detail", "")} | LLM: {y.get("detail", "")}',
        }
    return out


def score(name, preds):
    rows, c = [], defaultdict(int)
    per_cat = defaultdict(lambda: defaultdict(int))
    cat_ok = sev_ok = 0
    for sid, t in TRUTH.items():
        p = preds.get(sid, {"vulnerable": False, "categories": [], "severity": "None", "detail": "no output"})
        actual = t["label"] == "vulnerable"
        outcome = {(True, True): "TP", (False, True): "FP", (True, False): "FN", (False, False): "TN"}[(actual, p["vulnerable"])]
        c[outcome] += 1
        per_cat[t["category"]][outcome] += 1
        right_cat = outcome == "TP" and t["category"] in p["categories"]
        right_sev = outcome == "TP" and p["severity"] == t["severity"]
        cat_ok += right_cat
        sev_ok += right_sev
        rows.append({"scenario_id": sid, "truth_label": t["label"], "truth_category": t["category"],
                     "truth_severity": t["severity"], "predicted_vulnerable": p["vulnerable"],
                     "predicted_categories": " ".join(p["categories"]), "predicted_severity": p["severity"],
                     "outcome": outcome, "category_correct": right_cat if outcome == "TP" else "",
                     "severity_correct": right_sev if outcome == "TP" else "", "detail": p["detail"]})

    tp, fp, fn, tn = c["TP"], c["FP"], c["FN"], c["TN"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    summary = {
        "name": name, "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
        "accuracy": round((tp + tn) / len(TRUTH), 3),
        "category_accuracy_on_TP": round(cat_ok / tp, 3) if tp else None,
        "severity_accuracy_on_TP": round(sev_ok / tp, 3) if tp else None,
        "per_category": {k: dict(v) for k, v in sorted(per_cat.items())},
        "outputs_repaired": sum(v == "repaired" for v in OUTPUT_STATUS.values()) if OUTPUT_STATUS else None,
        "outputs_invalid": sum(v == "invalid" for v in OUTPUT_STATUS.values()) if OUTPUT_STATUS else None,
    }
    out = ROOT / "results" / "scores"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{name}_per_scenario.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out / f"{name}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"\n=== {name} ===")
    print(f"{'Scenario':<9} {'Truth':<11} {'Pred':<6} {'Outcome':<8} {'Cat ok':<7} {'Sev ok':<7} Detail")
    for r in rows:
        print(f"{r['scenario_id']:<9} {r['truth_label']:<11} {str(r['predicted_vulnerable']):<6} {r['outcome']:<8} "
              f"{str(r['category_correct']):<7} {str(r['severity_correct']):<7} {r['detail'][:70]}")
    print(f"\nTP={tp} FP={fp} FN={fn} TN={tn}  precision={summary['precision']} recall={summary['recall']} "
          f"F1={summary['f1']}  category acc={summary['category_accuracy_on_TP']}  severity acc={summary['severity_accuracy_on_TP']}")
    if OUTPUT_STATUS:
        print(f"outputs: repaired={summary['outputs_repaired']} invalid={summary['outputs_invalid']} (invalid = truncated/unparseable, scored as not vulnerable)")
    return summary


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "code_analyzer"
    if mode == "code_analyzer":
        score("code_analyzer", code_analyzer_predictions())
    elif mode == "llm":
        score(Path(sys.argv[2]).stem, llm_predictions(sys.argv[2]))
    elif mode == "union":
        score("union_" + Path(sys.argv[2]).stem, union(code_analyzer_predictions(), llm_predictions(sys.argv[2])))
    else:
        sys.exit(__doc__)