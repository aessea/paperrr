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


def run(case_file: str, time_limit: float) -> None:
    path = ROOT / "data" / case_file
    inst = load_instance(path, CONFIG)
    cfg = dict(CONFIG)
    cfg["gurobi"] = dict(CONFIG["gurobi"], time_limit=time_limit, mip_gap=0.0)
    t0 = time.perf_counter()
    res = solve_gurobi(inst, cfg)
    dt = time.perf_counter() - t0
    if res.assignment is not None:
        o = evaluate_solution(inst, res.assignment, CONFIG)
        print(f"{inst.name}: obj={o.total:.5f} high={o.high_priority:.5f} cat={o.category_split:.5f} "
              f"sku={o.sku_split:.5f} res={o.residual_capacity:.5f} bound={res.bound:.5f} "
              f"status={res.status} gap={res.extra.get('gap')} time={dt:.1f}s", flush=True)
    else:
        print(f"{inst.name}: NO SOLUTION status={res.status} time={dt:.1f}s", flush=True)


if __name__ == "__main__":
    smalls = [
        "small_01_973_orders_2_cabinets.xlsx",
        "small_02_1017_orders_2_cabinets.xlsx",
        "small_03_1059_orders_2_cabinets.xlsx",
        "small_04_992_orders_2_cabinets.xlsx",
        "small_05_1087_orders_2_cabinets.xlsx",
    ]
    mediums = [
        "medium_01_4827_orders_6_cabinets.xlsx",
        "medium_02_5063_orders_6_cabinets.xlsx",
        "medium_03_5239_orders_6_cabinets.xlsx",
        "medium_04_4911_orders_6_cabinets.xlsx",
        "medium_05_5167_orders_6_cabinets.xlsx",
    ]
    print("=== SMALL (limit 30s, gap 0) ===", flush=True)
    for c in smalls:
        run(c, 30.0)
    print("=== MEDIUM (limit 120s, gap 0) ===", flush=True)
    for c in mediums:
        run(c, 120.0)
