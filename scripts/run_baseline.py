"""Run TF-IDF retrieval and scoped SRS evidence assessments."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compliance_copilot.pipeline import run_baseline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--benchmark", type=Path)
    parser.add_argument("--split", help="Explicit benchmark partition, such as test")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    try:
        result = run_baseline(args.root, args.output, args.benchmark, args.split, args.top_k)
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, "Baseline error: {}\n".format(error))
    print(json.dumps(result["metrics"], indent=2))
