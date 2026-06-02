from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from tools import TOOL_FUNCTIONS

load_lab_env(ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the Tavily lookup tool with .env loaded.")
    parser.add_argument("--query", default="AI", help="Search query to send to Tavily.")
    parser.add_argument("--max-results", type=int, default=1, help="Maximum number of results to return.")
    args = parser.parse_args()

    result = TOOL_FUNCTIONS["lookup"](args.query, max_results=args.max_results)
    print(result)

    if result.get("error"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
