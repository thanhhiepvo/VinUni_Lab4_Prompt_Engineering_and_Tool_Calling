from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def audit_eval(run_json_path: str = "", failure_types: list[str] | None = None) -> dict[str, Any]:
    """
    Analyze a run JSON file and summarize failures by type and tool routing.
    
    Args:
        run_json_path: Path to a run/*.json file. If empty, returns guidance.
        failure_types: Filter to specific failure types (e.g., ["missing_info", "wrong_tool"]).
    
    Returns:
        Dictionary with summary, failure_details, routing_mismatches, arg_mismatches.
    """
    if not run_json_path:
        return {
            "tool": "audit_eval",
            "error": "missing_run_json_path",
            "message": "Provide a path to a run JSON file, e.g. runs/v0_B_base_openai_20260602T142654960548.json",
        }
    
    try:
        run_path = Path(run_json_path)
        if not run_path.exists():
            return {
                "tool": "audit_eval",
                "error": "file_not_found",
                "message": f"Run JSON not found: {run_json_path}",
            }
        
        obj = json.loads(run_path.read_text(encoding="utf-8"))
        results = obj.get("results", [])
        
        # Summary counts
        total = len(results)
        passed = sum(1 for r in results if r["result"]["passed"])
        failed = total - passed
        
        # Failure distribution
        failure_type_counts = defaultdict(int)
        failed_cases = []
        routing_mismatches = []
        arg_mismatches = []
        
        for item in results:
            res = item["result"]
            case_id = item["id"]
            
            if not res["passed"]:
                failure_type = res.get("case_failure_type", "unknown")
                failure_type_counts[failure_type] += 1
                
                # Filter by failure_types if specified
                if failure_types and failure_type not in failure_types:
                    continue
                
                inp = item["input"]
                query = inp.get("query") if isinstance(inp, dict) else str(inp)[:80]
                
                failed_cases.append({
                    "case_id": case_id,
                    "failure_type": failure_type,
                    "observed_mismatch": res.get("observed_mismatch"),
                    "query": query,
                    "failures": res.get("failures", []),
                })
                
                # Routing mismatches
                expected_tools = [c["name"] for c in item["expect"].get("tool_calls", [])]
                actual_tools = [c["name"] for c in res.get("actual_tool_calls", [])]
                if expected_tools != actual_tools:
                    routing_mismatches.append({
                        "case_id": case_id,
                        "expected": expected_tools,
                        "actual": actual_tools,
                    })
                
                # Argument mismatches
                for i, expected_call in enumerate(item["expect"].get("tool_calls", [])):
                    actual_call = next((c for c in res.get("actual_tool_calls", []) if c["name"] == expected_call["name"]), None)
                    if actual_call:
                        expected_args = expected_call.get("args", {})
                        actual_args = actual_call.get("args", {})
                        for key, expected_val in expected_args.items():
                            actual_val = actual_args.get(key)
                            if expected_val != actual_val:
                                arg_mismatches.append({
                                    "case_id": case_id,
                                    "tool": expected_call["name"],
                                    "arg": key,
                                    "expected": expected_val,
                                    "actual": actual_val,
                                })
        
        summary = {
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "failure_type_counts": dict(failure_type_counts),
        }
        
        return {
            "tool": "audit_eval",
            "summary": summary,
            "failure_details": failed_cases,
            "routing_mismatches": routing_mismatches,
            "arg_mismatches": arg_mismatches,
        }
    
    except Exception as exc:
        return {
            "tool": "audit_eval",
            "error": type(exc).__name__,
            "message": str(exc),
        }
