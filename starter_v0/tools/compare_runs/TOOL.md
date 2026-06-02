---
name: compare_runs
track: bonus
kind: local_knowledge
---

# compare_runs

Compare two eval run JSON files to show progress and differences.

## Purpose
Analyze improvements between two eval runs by comparing:
- Pass rates and failure counts
- Which cases changed status (fixed, regressed, stayed same)
- Failure type distribution shifts
- Routing vs argument mismatch trends

## When to use
- After making prompt/tool changes, compare old vs new run to quantify impact
- Identify which specific cases were fixed by recent changes
- Track improvement trajectory across multiple iterations
- Debug whether a code change helped or hurt overall accuracy

## Output structure
```json
{
  "summary": {
    "run1": {"pass_rate": 70.0, "passed": 14, "failed": 6},
    "run2": {"pass_rate": 80.0, "passed": 16, "failed": 4},
    "improvement": {
      "pass_rate_delta": 10.0,
      "passed_delta": 2,
      "failed_delta": -2
    }
  },
  "case_changes": {
    "fixed": ["R08_trend_twitter", "R14_send_confirm"],  // Cases that went from FAIL to PASS
    "regressed": [],  // Cases that went from PASS to FAIL
    "stayed_pass": [...],  // Cases that passed in both
    "stayed_fail": [...]  // Cases that failed in both
  },
  "failure_type_shifts": {
    "out_of_scope": {"run1": 2, "run2": 2, "delta": 0},
    "missing_info": {"run1": 2, "run2": 1, "delta": -1},
    "wrong_tool": {"run1": 1, "run2": 0, "delta": -1},
    "wrong_boundary": {"run1": 1, "run2": 1, "delta": 0}
  }
}
```

## Example
Given two run files from eval iterations:
- `runs/v0_B_base_openai_20260602T142654960548.json` (70%, baseline)
- `runs/v0_B_refined_openai_20260603T150201234567.json` (80%, after prompt tuning)

The tool returns which cases improved and why, helping prioritize next tuning efforts.
