"""Run benchmark scenarios through an Amazon Bedrock model and save the outputs.

Conditions (RQ4):
  A  Apex only
  B  Apex + metadata
  C  Apex + metadata + Salesforce security guidance
  D  C + structured security checks
  E  D + Salesforce Code Analyzer findings (fed-in; run scripts/run_code_analyzer.sh first)

The answer key (ground_truth.json) is never read or sent to the model.

Examples:
  python scripts/bedrock_runner.py --model-id <bedrock model id> --condition B --dry-run
  python scripts/bedrock_runner.py --model-id <bedrock model id> --condition B --rep 1 --region eu-west-1

Output: results/llm/<model>__<condition>__rep<n>.jsonl (one line per scenario)
"""
import argparse
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"


def scenario_files(sid, include_metadata):
    base = ROOT / "scenarios" / sid / "force-app" / "main" / "default"
    files = sorted((base / "classes").glob("*.cls"))
    if include_metadata:
        files += sorted(p for p in base.rglob("*.xml") if not p.name.endswith(".cls-meta.xml"))
    return files


def code_analyzer_findings(sid):
    f = ROOT / "results" / "code_analyzer" / f"{sid}.json"
    if not f.exists():
        raise SystemExit(f"Condition E needs Code Analyzer results; missing {f}")
    v = json.loads(f.read_text()).get("violations", [])
    if not v:
        return "Salesforce Code Analyzer reported no security violations."
    lines = []
    for x in v:
        loc = x["locations"][x.get("primaryLocationIndex", 0)]
        lines.append(f'- {x["rule"]} (severity {x["severity"]}) in {Path(loc["file"]).name} line {loc.get("startLine")}: {x["message"]}')
    return "Salesforce Code Analyzer reported:\n" + "\n".join(lines)


def build_prompt(sid, condition):
    with_meta = condition in "BCDE"
    parts = []
    if condition in "CDE":
        parts.append((PROMPTS / "guidance.txt").read_text())
    parts.append("Analyse the following Salesforce files:")
    for f in scenario_files(sid, with_meta):
        parts.append(f"--- FILE: {f.name} ---\n{f.read_text()}")
    if condition == "E":
        parts.append(code_analyzer_findings(sid))
    if condition in "DE":
        parts.append((PROMPTS / "structured_checks.txt").read_text())
    else:
        parts.append("Output only the JSON object.")
    return "\n\n".join(parts)


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def call_ollama(args, system, prompt):
    """Call a local Ollama model with the same system prompt, user prompt and settings as Bedrock."""
    import urllib.request
    body = {
        "model": args.model_id,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": args.temperature, "num_predict": args.max_tokens, "num_ctx": 8192},
    }
    req = urllib.request.Request(
        args.ollama_url.rstrip("/") + "/api/chat",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read())
    return resp["message"].get("content", ""), resp.get("prompt_eval_count"), resp.get("eval_count")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", required=True, help="Bedrock model or inference profile id")
    ap.add_argument("--condition", choices=list("ABCDE"), required=True)
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--region", default="eu-west-1")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--scenarios", nargs="*", help="default: all")
    ap.add_argument("--dry-run", action="store_true", help="write prompts only, no Bedrock calls")
    ap.add_argument("--backend", choices=["bedrock", "ollama"], default="bedrock",
                    help="bedrock (AWS, default) or ollama (local model, code never leaves the machine)")
    ap.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server address")
    args = ap.parse_args()

    system = (PROMPTS / "system.txt").read_text()
    sids = args.scenarios or sorted(p.name for p in (ROOT / "scenarios").iterdir() if p.is_dir())
    safe_model = re.sub(r"[^A-Za-z0-9._-]", "_", args.model_id)
    out_dir = ROOT / "results" / "llm"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        d = out_dir / "dry_run" / args.condition
        d.mkdir(parents=True, exist_ok=True)
        for sid in sids:
            (d / f"{sid}.txt").write_text("SYSTEM:\n" + system + "\n\nUSER:\n" + build_prompt(sid, args.condition))
        print(f"Wrote {len(sids)} prompts to {d}")
        return

    if args.backend == "bedrock":
        import boto3  # imported here so --dry-run and ollama work without AWS
        client = boto3.client("bedrock-runtime", region_name=args.region)
    else:
        safe_model = "ollama_" + safe_model

    out = out_dir / f"{safe_model}__{args.condition}__rep{args.rep}.jsonl"
    with open(out, "w") as fh:
        for sid in sids:
            prompt = build_prompt(sid, args.condition)
            t0 = time.time()
            if args.backend == "bedrock":
                resp = client.converse(
                    modelId=args.model_id,
                    system=[{"text": system}],
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"temperature": args.temperature, "maxTokens": args.max_tokens},
                )
                text = "".join(c.get("text", "") for c in resp["output"]["message"]["content"])
                usage = resp.get("usage", {})
                in_tok, out_tok = usage.get("inputTokens"), usage.get("outputTokens")
            else:
                text, in_tok, out_tok = call_ollama(args, system, prompt)
            latency = round(time.time() - t0, 2)
            rec = {
                "scenario_id": sid, "model": args.model_id, "backend": args.backend,
                "condition": args.condition, "rep": args.rep,
                "temperature": args.temperature, "latency_s": latency,
                "input_tokens": in_tok, "output_tokens": out_tok,
                "output": parse_json(text), "raw": text,
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"{sid}: vulnerable={rec['output'] and rec['output'].get('vulnerable')} "
                  f"tokens={rec['input_tokens']}/{rec['output_tokens']} {latency}s")
    print(f"Saved {out}\nScore it: python scripts/score.py llm {out}")


if __name__ == "__main__":
    main()