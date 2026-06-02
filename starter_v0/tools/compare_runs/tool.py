import json
from pathlib import Path
from typing import Any


def compare_runs(run1_path: str, run2_path: str) -> dict[str, Any]:
    """
    Compare two eval run JSON files to show progress and differences.
    
    Args:
        run1_path: Path to first run/*.json file
        run2_path: Path to second run/*.json file
    
    Returns:
        Dictionary with summary, case_changes, and failure_type_shifts
    """
    try:
        p1 = Path(run1_path)
        p2 = Path(run2_path)
        
        if not p1.exists():
            return {"error": "run1_path_not_found", "message": f"{run1_path} not found"}
        if not p2.exists():
            return {"error": "run2_path_not_found", "message": f"{run2_path} not found"}
        
        with open(p1) as f:
            data1 = json.load(f)
        with open(p2) as f:
            data2 = json.load(f)
        
        # Extract results
        results1 = {case['id']: case for case in data1.get('results', [])}
        results2 = {case['id']: case for case in data2.get('results', [])}
        
        # Compute summary
        passed1 = sum(1 for c in results1.values() if c.get('result', {}).get('passed', False))
        failed1 = len(results1) - passed1
        pass_rate1 = (passed1 / len(results1) * 100) if results1 else 0
        
        passed2 = sum(1 for c in results2.values() if c.get('result', {}).get('passed', False))
        failed2 = len(results2) - passed2
        pass_rate2 = (passed2 / len(results2) * 100) if results2 else 0
        
        summary = {
            "run1": {
                "pass_rate": round(pass_rate1, 1),
                "passed": passed1,
                "failed": failed1,
                "total": len(results1),
            },
            "run2": {
                "pass_rate": round(pass_rate2, 1),
                "passed": passed2,
                "failed": failed2,
                "total": len(results2),
            },
            "improvement": {
                "pass_rate_delta": round(pass_rate2 - pass_rate1, 1),
                "passed_delta": passed2 - passed1,
                "failed_delta": failed2 - failed1,
            }
        }
        
        # Identify case status changes
        all_cases = set(results1.keys()) | set(results2.keys())
        fixed = []
        regressed = []
        stayed_pass = []
        stayed_fail = []
        
        for case_id in sorted(all_cases):
            case1 = results1.get(case_id)
            case2 = results2.get(case_id)
            
            passed1 = case1.get('result', {}).get('passed', False) if case1 else False
            passed2 = case2.get('result', {}).get('passed', False) if case2 else False
            
            if passed1 and not passed2:
                regressed.append(case_id)
            elif not passed1 and passed2:
                fixed.append(case_id)
            elif passed1 and passed2:
                stayed_pass.append(case_id)
            else:
                stayed_fail.append(case_id)
        
        case_changes = {
            "fixed": fixed,
            "regressed": regressed,
            "stayed_pass": stayed_pass,
            "stayed_fail": stayed_fail,
        }
        
        # Analyze failure type distribution
        def get_failure_types(results_dict):
            from collections import defaultdict
            counts = defaultdict(int)
            for case in results_dict.values():
                if not case.get('result', {}).get('passed', False):
                    ftype = case.get('result', {}).get('case_failure_type', 'unknown')
                    counts[ftype] += 1
            return dict(counts)
        
        failures1 = get_failure_types(results1)
        failures2 = get_failure_types(results2)
        
        all_ftypes = set(failures1.keys()) | set(failures2.keys())
        failure_type_shifts = {}
        for ftype in sorted(all_ftypes):
            count1 = failures1.get(ftype, 0)
            count2 = failures2.get(ftype, 0)
            failure_type_shifts[ftype] = {
                "run1": count1,
                "run2": count2,
                "delta": count2 - count1,
            }
        
        return {
            "summary": summary,
            "case_changes": case_changes,
            "failure_type_shifts": failure_type_shifts,
        }
    
    except json.JSONDecodeError as e:
        return {"error": "json_decode_error", "message": str(e)}
    except Exception as e:
        return {"error": "unexpected_error", "message": str(e)}
