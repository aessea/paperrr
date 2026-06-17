import argparse
import csv
from pathlib import Path

from .config import CONFIG
from .data_loader import load_instance
from .gurobi_solver import solve_gurobi


def _case_files(config: dict, scope: str, case: str | None) -> list[Path]:
    data_dir = Path(config["data_scope"]["data_dir"])
    files = [data_dir / name for name in config["data_scope"]["paper15"]]
    if scope in {"small", "medium", "large"}:
        files = [p for p in files if p.name.startswith(scope + "_")]
    elif scope != "paper15":
        raise ValueError(f"Unsupported scope: {scope}")
    if case:
        files = [p for p in files if p.name.startswith(case + "_")]
    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing data files: {missing}")
    return files


def run(config: dict, scope: str, solver: str, case: str | None) -> list[dict]:
    if solver != "gurobi":
        raise ValueError(f"Unsupported solver: {solver}")

    rows = []
    for path in _case_files(config, scope, case):
        inst = load_instance(path, config)
        print(f"\nCase {inst.name} ({inst.n_items} orders, {inst.n_cabinets} cabinets)")

        milp = solve_gurobi(inst, config)
        print(f"  Gurobi status={milp.status} obj={milp.objective} time={milp.runtime:.2f}s")

        rows.append(
            {
                "case": inst.name,
                "scale": inst.scale,
                "orders": inst.n_items,
                "milp_obj": milp.objective,
                "milp_bound": milp.bound,
                "milp_status": milp.status,
                "milp_time": milp.runtime,
            }
        )
    return rows


def write_csv(rows: list[dict], config: dict) -> Path:
    out_dir = Path(config["output"]["results_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / config["output"]["comparison_csv"]
    if not rows:
        return out_path
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def print_summary(rows: list[dict]) -> None:
    print("\ncase,scale,orders,milp_obj,milp_bound,milp_status")
    for row in rows:
        print(
            f"{row['case']},{row['scale']},{row['orders']},"
            f"{row['milp_obj']},{row['milp_bound']},{row['milp_status']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run container assignment Gurobi baseline.")
    parser.add_argument("--scope", default="paper15", choices=["paper15", "small", "medium", "large"])
    parser.add_argument("--solver", default="gurobi", choices=["gurobi"])
    parser.add_argument("--case", default=None)
    args = parser.parse_args()

    rows = run(CONFIG, args.scope, args.solver, args.case)
    print_summary(rows)
    out_path = write_csv(rows, CONFIG)
    print(f"\nSaved CSV: {out_path}")


if __name__ == "__main__":
    main()
