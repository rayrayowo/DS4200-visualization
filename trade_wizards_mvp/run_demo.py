from __future__ import annotations

import argparse
from pathlib import Path

from tw_mvp.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Trade Wizards MVP (node graph + neural net node + backtesting)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "config" / "default_graph.json",
        help="Path to JSON config for the run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = run_pipeline(args.config)
    print(f"[done] artifacts: {out_dir}")


if __name__ == "__main__":
    main()

