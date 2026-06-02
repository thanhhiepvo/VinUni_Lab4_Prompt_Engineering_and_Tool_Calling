import json
import subprocess
from pathlib import Path
from typing import Any
from datetime import datetime


def batch_eval(configs: list[dict[str, str]]) -> dict[str, Any]:
    """
    Run eval.py with multiple configurations and generate a summary report.
    
    Args:
        configs: List of config dicts with keys:
            - name: Configuration name
            - system_prompt_path: Path to system_prompt file
            - tools_yaml_path: Path to tools.yaml file
            - provider: Model provider (openai, anthropic, gemini, openrouter)
            - eval_data: Path to eval data JSON (data/eval_base.json, etc.)
    
    Returns:
        Dictionary with runs list, best_config, and summary_table
    """
    try:
        if not configs:
            return {"error": "empty_configs", "message": "configs list is empty"}
        
        runs = []
        cwd = Path(__file__).resolve().parents[2]  # starter_v0 root
        
        for config in configs:
            # Validate config
            required_keys = ["name", "system_prompt_path", "tools_yaml_path", "provider", "eval_data"]
            missing = [k for k in required_keys if k not in config]
            if missing:
                return {"error": "missing_config_keys", "message": f"Missing keys: {missing}"}
            
            name = config["name"]
            prompt_path = config["system_prompt_path"]
            tools_path = config["tools_yaml_path"]
            provider = config["provider"]
            eval_data = config["eval_data"]
            
            # Verify files exist
            for path in [prompt_path, tools_path, eval_data]:
                full_path = cwd / path
                if not full_path.exists():
                    return {"error": "file_not_found", "message": f"{path} not found"}
            
            # Run eval
            cmd = [
                "python3", "run_eval.py",
                f"--system_prompt_path={prompt_path}",
                f"--tools_yaml_path={tools_path}",
                f"--provider={provider}",
                f"--eval_data={eval_data}",
            ]
            
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                return {
                    "error": "eval_execution_failed",
                    "config": name,
                    "message": result.stderr,
                }
            
            # Parse output to find run JSON path
            # Typical output: "Run complete: runs/v0_B_base_openai_TIMESTAMP.json"
            output_lines = result.stdout.split('\n')
            run_json_path = None
            for line in output_lines:
                if 'runs/' in line and line.strip().endswith('.json'):
                    run_json_path = line.split()[-1]
                    break
            
            if not run_json_path:
                return {
                    "error": "run_json_not_found",
                    "config": name,
                    "message": "Could not determine output run JSON from eval output",
                }
            
            # Extract summary from run JSON
            run_path = cwd / run_json_path
            if not run_path.exists():
                return {"error": "run_json_missing", "message": f"{run_json_path} not found"}
            
            with open(run_path) as f:
                run_data = json.load(f)
            
            evals = run_data.get('evals', [])
            passed = sum(1 for c in evals if c.get('passed', False))
            failed = len(evals) - passed
            pass_rate = (passed / len(evals) * 100) if evals else 0
            
            runs.append({
                "config_name": name,
                "run_json_path": str(run_json_path),
                "pass_rate": round(pass_rate, 1),
                "passed": passed,
                "failed": failed,
                "total": len(evals),
            })
        
        # Find best config
        best = max(runs, key=lambda r: r['pass_rate'])
        best_config = best['config_name']
        best_pass_rate = best['pass_rate']
        
        # Build summary table
        table_lines = ["| Config | Pass Rate | Passed | Failed | Total | Run JSON |"]
        table_lines.append("|--------|-----------|--------|--------|-------|----------|")
        for r in runs:
            marker = " ⭐" if r['config_name'] == best_config else ""
            row = f"| {r['config_name']}{marker} | {r['pass_rate']}% | {r['passed']} | {r['failed']} | {r['total']} | {r['run_json_path']} |"
            table_lines.append(row)
        
        return {
            "runs": runs,
            "best_config": best_config,
            "best_pass_rate": best_pass_rate,
            "summary_table": "\n".join(table_lines),
        }
    
    except subprocess.TimeoutExpired:
        return {"error": "eval_timeout", "message": "Eval run exceeded 10 minute timeout"}
    except Exception as e:
        return {"error": "unexpected_error", "message": str(e)}
