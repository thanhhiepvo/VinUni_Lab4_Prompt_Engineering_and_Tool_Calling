#!/usr/bin/env python3
"""
Quick diagnostic script to analyze eval failures using the audit_eval tool.

Usage:
    python scripts/diagnose_eval.py runs/v0_B_base_openai_TIMESTAMP.json
    python scripts/diagnose_eval.py runs/v0_B_base_openai_TIMESTAMP.json missing_info wrong_tool
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import TOOL_FUNCTIONS


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    run_json = sys.argv[1]
    failure_types = sys.argv[2:] if len(sys.argv) > 2 else None
    
    result = TOOL_FUNCTIONS['audit_eval'](run_json, failure_types)
    
    if result.get('error'):
        print(f"Error: {result['error']}")
        print(f"Message: {result['message']}")
        sys.exit(1)
    
    summary = result['summary']
    print(f"\n=== Eval Summary ===")
    print(f"Total: {summary['total_cases']}")
    print(f"Passed: {summary['passed']} ({summary['pass_rate']}%)")
    print(f"Failed: {summary['failed']}")
    print(f"\nFailure distribution:")
    for ftype, count in summary['failure_type_counts'].items():
        print(f"  {ftype}: {count}")
    
    routing = result['routing_mismatches']
    if routing:
        print(f"\n=== Routing Mismatches ({len(routing)}) ===")
        for m in routing[:5]:
            print(f"  {m['case_id']}: expected {m['expected']} got {m['actual']}")
        if len(routing) > 5:
            print(f"  ... and {len(routing) - 5} more")
    
    args = result['arg_mismatches']
    if args:
        print(f"\n=== Argument Mismatches ({len(args)}) ===")
        for m in args[:5]:
            print(f"  {m['case_id']} {m['tool']}.{m['arg']}: expected {m['expected']} got {m['actual']}")
        if len(args) > 5:
            print(f"  ... and {len(args) - 5} more")
    
    print()


if __name__ == '__main__':
    main()
