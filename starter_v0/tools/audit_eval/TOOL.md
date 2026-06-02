---
name: audit_eval
track: bonus
kind: local_knowledge
provider: None
requires_env: []
inputs: [run_json_path, failure_types]
outputs: [summary, failure_details, routing_mismatches, arg_mismatches]
side_effect: false
requires_confirmation: false
---

# Audit Eval — Diagnostic Tool for Eval Runs

Analyzes a run JSON output and summarizes failures by type, routing mismatches, and argument errors.

This is a diagnostic helper to understand which eval cases are failing and why, so teams can iteratively improve the prompt and tool descriptions.

## What it does

- Scans `runs/*.json` for failed cases
- Groups failures by `case_failure_type` (out_of_scope, missing_info, wrong_boundary, wrong_tool)
- Lists tool routing mismatches (expected vs actual tool calls)
- Lists argument mismatches (expected vs actual argument values)
- Returns human-readable summary for prompt/tool tuning

## Output

Returns:
- `summary`: counts of pass/fail, failure distribution
- `failure_details`: list of failed case IDs with query and reason
- `routing_mismatches`: tool name mismatches (timeline vs social_search, etc.)
- `arg_mismatches`: argument value mismatches (limit, timeframe, search_type)
- `expected_mismatch_counts`: how many times expected_tool_calls vs actual_tool_calls differ
