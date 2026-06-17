from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

CONFIG = {
    "objective_weights": {
        "high_priority": 30,
        "category_split": 15,
        "sku_split": 5,
        "residual_capacity": 30.0,
    },
    "residual_weights": {
        "volume": 1.0,
        "weight": 0.0,
    },
    "gurobi": {
        "time_limit": 200.0,
        "mip_gap": 0.05,
        "threads": 0,
        "output_flag": 0,
    },
    "data_scope": {
        "paper15": [
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
            "large_01_11000_orders_15_cabinets.xlsx",
            "large_02_11000_orders_15_cabinets.xlsx",
            "large_03_11000_orders_15_cabinets.xlsx",
            "large_04_11000_orders_15_cabinets.xlsx",
            "large_05_11000_orders_15_cabinets.xlsx",
        ],
        "data_dir": str(ROOT_DIR / "data"),
    },
    "output": {
        "results_dir": str(ROOT_DIR / "outputs"),
        "comparison_csv": "comparison_results.csv",
    },
}
