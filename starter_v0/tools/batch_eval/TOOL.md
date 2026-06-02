---
name: batch_eval
track: bonus
kind: local_knowledge
---

# batch_eval

Run eval.py with multiple configurations and generate a summary report.

## Purpose
Execute multiple eval runs in sequence with different:
- System prompts (baseline vs refined versions)
- Tool descriptions (different clarity/specificity levels)
- Model providers (OpenAI, Anthropic, Gemini, OpenRouter)
- Eval datasets (base, group, research_extension)

Then produce a comparison matrix showing which config performs best.

## When to use
- Testing multiple prompt variations to find the best one
- Evaluating whether different LLM providers produce consistent results
- Validating that improvements hold across different eval datasets
- Creating a performance baseline before major changes
- Documenting config choices with quantified evidence

## Input structure
```python
batch_configs = [
    {
        "name": "baseline",
        "system_prompt_path": "artifacts/system_prompt.md",
        "tools_yaml_path": "artifacts/tools.yaml",
        "provider": "openai",
        "eval_data": "data/eval_base.json",
    },
    {
        "name": "refined_routing",
        "system_prompt_path": "artifacts/system_prompt_v2.md",
        "tools_yaml_path": "artifacts/tools_v2.yaml",
        "provider": "openai",
        "eval_data": "data/eval_base.json",
    },
]
```

## Output structure
```json
{
  "runs": [
    {
      "config_name": "baseline",
      "run_json_path": "runs/v0_B_base_openai_20260602T142654960548.json",
      "pass_rate": 70.0,
      "passed": 14,
      "failed": 6
    },
    {
      "config_name": "refined_routing",
      "run_json_path": "runs/v0_B_refined_routing_openai_20260603T150201234567.json",
      "pass_rate": 80.0,
      "passed": 16,
      "failed": 4
    }
  ],
  "best_config": "refined_routing",
  "best_pass_rate": 80.0,
  "summary_table": "| Config | Pass Rate | Passed | Failed | Run JSON |...",
}
```

## Example
Run eval with 3 different prompt versions and 2 datasets to find the optimal configuration:
```
batch_eval([
  {"name": "v1_baseline", "system_prompt_path": "system_prompt.md", "provider": "openai", "eval_data": "eval_base.json"},
  {"name": "v2_routing_rules", "system_prompt_path": "system_prompt_v2.md", "provider": "openai", "eval_data": "eval_base.json"},
  {"name": "v3_explicit_boundaries", "system_prompt_path": "system_prompt_v3.md", "provider": "openai", "eval_data": "eval_base.json"},
])
```

Result: Show that v3 achieves 80%, demonstrating clear improvement trajectory.
