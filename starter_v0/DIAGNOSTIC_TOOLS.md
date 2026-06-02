# Diagnostic and Enhancement Tools

This document describes the new tools added to enhance the eval workflow: `audit_eval`, `compare_runs`, and `batch_eval`.

## Quick Start

### 1. Analyze a Single Eval Run

```bash
python3 scripts/diagnose_eval.py runs/v0_B_base_openai_20260602T142654960548.json
```

Output shows:
- Pass rate summary
- Failure type distribution (missing_info, wrong_tool, wrong_boundary, out_of_scope)
- Routing mismatches (expected vs actual tool choices)
- Argument mismatches (expected vs actual argument values)

Filter by failure types:
```bash
python3 scripts/diagnose_eval.py runs/v0_B_base_openai_20260602T142654960548.json missing_info wrong_tool
```

### 2. Compare Two Eval Runs

Quantify improvements when you change prompts or tool descriptions:

```python
from tools import TOOL_FUNCTIONS

result = TOOL_FUNCTIONS['compare_runs'](
    'runs/v0_B_base_openai_20260602T142654960548.json',      # baseline
    'runs/v0_B_refined_openai_20260603T150201234567.json'   # new version
)

print(f"Pass rate: {result['summary']['run1']['pass_rate']}% → {result['summary']['run2']['pass_rate']}%")
print(f"Fixed: {result['case_changes']['fixed']}")
print(f"Regressed: {result['case_changes']['regressed']}")
```

### 3. Run Multiple Eval Configurations

Test different prompts or models in parallel:

```python
from tools import TOOL_FUNCTIONS

configs = [
    {
        "name": "baseline",
        "system_prompt_path": "artifacts/system_prompt.md",
        "tools_yaml_path": "artifacts/tools.yaml",
        "provider": "openai",
        "eval_data": "data/eval_base.json",
    },
    {
        "name": "refined_v1",
        "system_prompt_path": "artifacts/system_prompt_v2.md",
        "tools_yaml_path": "artifacts/tools_v2.yaml",
        "provider": "openai",
        "eval_data": "data/eval_base.json",
    },
]

result = TOOL_FUNCTIONS['batch_eval'](configs)
print(result['summary_table'])
print(f"Best: {result['best_config']} at {result['best_pass_rate']}%")
```

---

## Tool Details

### audit_eval

**Purpose**: Analyze a single eval run JSON file to identify patterns in failures.

**Parameters**:
- `run_json_path` (required): Path to run/*.json file
- `failure_types` (optional): List of failure types to focus on

**Returns**:
```json
{
  "summary": {
    "total_cases": 20,
    "passed": 14,
    "failed": 6,
    "pass_rate": 70.0,
    "failure_type_counts": {
      "out_of_scope": 2,
      "missing_info": 2,
      "wrong_tool": 1,
      "wrong_boundary": 1
    }
  },
  "failure_details": [
    {
      "case_id": "R10_missing_handle",
      "failure_type": "missing_info",
      "observed_mismatch": "...",
      "query": "What are the latest posts from user@handle?",
      "failures": ["..."]
    }
  ],
  "routing_mismatches": [
    {
      "case_id": "R10_missing_handle",
      "expected": ["clarify"],
      "actual": ["timeline"]
    }
  ],
  "arg_mismatches": [
    {
      "case_id": "R01_example",
      "tool": "send",
      "arg": "confirmed",
      "expected": true,
      "actual": false
    }
  ]
}
```

**When to use**:
- After running eval, quickly see which cases failed and why
- Identify patterns (e.g., "missing_info appears 5 times for timeline tool")
- Guide next refinement efforts

---

### compare_runs

**Purpose**: Compare two eval runs side-by-side to quantify improvements.

**Parameters**:
- `run1_path` (required): Path to first run/*.json (baseline)
- `run2_path` (required): Path to second run/*.json (to compare)

**Returns**:
```json
{
  "summary": {
    "run1": {"pass_rate": 70.0, "passed": 14, "failed": 6, "total": 20},
    "run2": {"pass_rate": 80.0, "passed": 16, "failed": 4, "total": 20},
    "improvement": {
      "pass_rate_delta": 10.0,
      "passed_delta": 2,
      "failed_delta": -2
    }
  },
  "case_changes": {
    "fixed": ["R08_out_of_scope", "R14_send_confirm"],
    "regressed": [],
    "stayed_pass": [...],
    "stayed_fail": [...]
  },
  "failure_type_shifts": {
    "out_of_scope": {"run1": 2, "run2": 1, "delta": -1},
    "missing_info": {"run1": 2, "run2": 2, "delta": 0},
    "wrong_tool": {"run1": 1, "run2": 0, "delta": -1},
    "wrong_boundary": {"run1": 1, "run2": 1, "delta": 0}
  }
}
```

**When to use**:
- After making prompt changes, confirm they actually improved metrics
- Track improvement trajectory: baseline → v1 → v2 → ...
- Debug: "Did this change help or hurt?"

---

### batch_eval

**Purpose**: Run eval with multiple configurations in sequence and compare results.

**Parameters**:
- `configs` (required): List of config dicts, each with:
  - `name`: Configuration identifier
  - `system_prompt_path`: Path to system_prompt file
  - `tools_yaml_path`: Path to tools.yaml file
  - `provider`: Model provider (openai, anthropic, gemini, openrouter)
  - `eval_data`: Path to eval data (data/eval_base.json, data/eval_group.json, etc.)

**Returns**:
```json
{
  "runs": [
    {
      "config_name": "baseline",
      "run_json_path": "runs/v0_B_base_openai_20260602T142654960548.json",
      "pass_rate": 70.0,
      "passed": 14,
      "failed": 6,
      "total": 20
    },
    {
      "config_name": "refined_v1",
      "run_json_path": "runs/v0_B_refined_v1_openai_20260603T150201234567.json",
      "pass_rate": 80.0,
      "passed": 16,
      "failed": 4,
      "total": 20
    }
  ],
  "best_config": "refined_v1",
  "best_pass_rate": 80.0,
  "summary_table": "| Config | Pass Rate | Passed | Failed | Total | Run JSON |..."
}
```

**When to use**:
- Test 3+ prompt variations with quantified metrics
- Compare performance across different LLM providers
- Validate improvements hold across different eval datasets

---

## Workflow Example: Improving from 70% to 80%

### Step 1: Baseline Analysis
```bash
$ python3 scripts/diagnose_eval.py runs/v0_B_base_openai_20260602T142654960548.json

=== Eval Summary ===
Total: 20, Passed: 14 (70.0%), Failed: 6

Failure distribution:
  out_of_scope: 2
  missing_info: 2
  wrong_boundary: 1
  wrong_tool: 1

=== Routing Mismatches (6) ===
  R10_missing_handle: expected ['clarify'] got ['timeline']
  R11_missing_url: expected ['clarify'] got ['fetch']
  R12_confirm_before_send: expected ['clarify'] got ['send']
  R13_parallel_web_and_tweets: expected ['lookup', 'social_search'] got ['lookup', 'timeline']
```

**Hypothesis**: Tool descriptions need clearer boundaries. Timeline should not be used without a handle, clarify should be triggered earlier.

### Step 2: Refine Prompt & Tools
Edit `artifacts/system_prompt.md`:
- Add: "Only ask for clarification when tool calls require missing info (handles, URLs, confirmations)"
- Add explicit routing: "Use timeline only with @handle, not for keywords"

Edit `artifacts/tools.yaml`:
- Clarify tool: "Use when user hasn't provided required arguments like Twitter handles, URLs, or confirmation"
- Timeline tool: "Requires screenname; do NOT use for keyword search"
- Social_search: "Use this for tweets about a subject, not a specific account"

### Step 3: Compare Results
```python
from tools import TOOL_FUNCTIONS

result = TOOL_FUNCTIONS['compare_runs'](
    'runs/v0_B_base_openai_20260602T142654960548.json',      # 70%
    'runs/v0_B_refined_openai_20260603T150201234567.json'   # after changes
)

print(f"Improvement: {result['summary']['improvement']['pass_rate_delta']}%")
print(f"Fixed: {result['case_changes']['fixed']}")
```

Output: ✅ 80% (16/20 passed)
- Fixed: ['R08_out_of_scope', 'R09_tweet_content_boundary', 'R14_send_confirm']
- Still failing: R10 (missing_info on handle), R11 (missing_info on URL), R12, R13

### Step 4: Iterate
Continue refining based on which cases remain failing. Use `audit_eval` to drill into specific failure types.

---

## Integration with Chat

These tools can be called from the agent chat to help analyze and improve eval results:

```
User: "Why did we only get 70% on eval?"

Agent uses: audit_eval
Response: "We have 6 failures:
  - 2 cases need better 'missing_info' handling (R10, R11)
  - 2 are out-of-scope (expected no tools, agent used send)
  - 1 routing error: timeline used instead of clarify
  
Recommendation: Refine tool descriptions to clarify when clarify should be used vs timeline."
```

---

## File Structure

```
starter_v0/
├── tools/
│   ├── audit_eval/
│   │   ├── TOOL.md        # Tool documentation
│   │   └── tool.py        # Implementation
│   ├── compare_runs/
│   │   ├── TOOL.md
│   │   └── tool.py
│   ├── batch_eval/
│   │   ├── TOOL.md
│   │   └── tool.py
│   └── __init__.py        # Registers all tools
├── artifacts/
│   └── tools.yaml         # Tool descriptions for model
└── scripts/
    └── diagnose_eval.py   # Quick CLI for audit_eval
```
