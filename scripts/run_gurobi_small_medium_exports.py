from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import CONFIG
from src.data_loader import load_instance
from src.evaluator import evaluate_solution
from src.gurobi_solver import solve_gurobi
from src.solution_exporter import write_solution_workbook


CASES = [
    "small_01_973_orders_2_cabinets.xlsx",
    "small_02_1017_orders_2_cabinets.xlsx",
    "small_03_1059_orders_2_cabinets.xlsx",
    "small_04_992_orders_2_cabinets.xlsx",
    "small_05_1087_orders_2_cabinets.xlsx",
    "medium_01_4827_orders_6_cabinets.xlsx",
    "medium_02_5063_orders_6_cabinets.xlsx",
    "medium_03_5239_orders_6_cabinets.xlsx",
    "medium_04_4911_orders_6_cabinets.xlsx",
    "medium_05_5167_orders_6_cabinets.xlsx",
]


def main() -> int:
    output_dir = ROOT / "outputs" / "gurobi_small_medium_unlimited_excel"
    cfg = dict(CONFIG)
    cfg["gurobi"] = dict(
        CONFIG["gurobi"],
        time_limit=1.0e100,
        mip_gap=0.05,
        output_flag=0,
    )

    for case_file in CASES:
        case_path = ROOT / "data" / case_file
        inst = load_instance(case_path, cfg)
        print(f"=== {inst.name} start ===", flush=True)
        started = time.perf_counter()
        result = solve_gurobi(inst, cfg)
        elapsed = time.perf_counter() - started
        if result.assignment is None:
            print(f"{inst.name}: no solution status={result.status} time={elapsed:.1f}s", flush=True)
            continue

        objective = evaluate_solution(inst, result.assignment, cfg)
        output_path = output_dir / f"{inst.name}_gurobi.xlsx"
        write_solution_workbook(inst, result, output_path)
        print(
            f"{inst.name}: status={result.status} obj={objective.total:.6f} "
            f"bound={result.bound} gap={result.extra.get('gap')} time={elapsed:.1f}s "
            f"file={output_path}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
