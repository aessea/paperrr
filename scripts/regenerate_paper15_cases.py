from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

HEADERS = [
    "index",
    "MRP SKU",
    "排单数量",
    "材积",
    "重量",
    "品类",
    "separate_cabinet_group",
    "weight_min",
    "weight_max",
    "weight_lower_rate",
    "volume_min",
    "volume_max",
    "volume_lower_rate",
    "sku_style_min",
    "sku_style_max",
    "per_sku_quantity_min",
    "per_sku_quantity_max",
    "类别",
    "cno",
]

VOLUME_CAP = 60.0
WEIGHT_CAP = 19000.0
UNLIMITED_CAP = 999999


@dataclass(frozen=True)
class CaseSpec:
    scale: str
    case_no: int
    orders: int
    cabinets: int
    file_name: str

    @property
    def name(self) -> str:
        return f"{self.scale}_{self.case_no:02d}"


CASES = [
    CaseSpec("small", 1, 973, 2, "small_01_973_orders_2_cabinets.xlsx"),
    CaseSpec("small", 2, 1017, 2, "small_02_1017_orders_2_cabinets.xlsx"),
    CaseSpec("small", 3, 1059, 2, "small_03_1059_orders_2_cabinets.xlsx"),
    CaseSpec("small", 4, 992, 2, "small_04_992_orders_2_cabinets.xlsx"),
    CaseSpec("small", 5, 1087, 2, "small_05_1087_orders_2_cabinets.xlsx"),
    CaseSpec("medium", 1, 4827, 6, "medium_01_4827_orders_6_cabinets.xlsx"),
    CaseSpec("medium", 2, 5063, 6, "medium_02_5063_orders_6_cabinets.xlsx"),
    CaseSpec("medium", 3, 5239, 6, "medium_03_5239_orders_6_cabinets.xlsx"),
    CaseSpec("medium", 4, 4911, 6, "medium_04_4911_orders_6_cabinets.xlsx"),
    CaseSpec("medium", 5, 5167, 6, "medium_05_5167_orders_6_cabinets.xlsx"),
    CaseSpec("large", 1, 11000, 15, "large_01_11000_orders_15_cabinets.xlsx"),
    CaseSpec("large", 2, 11000, 15, "large_02_11000_orders_15_cabinets.xlsx"),
    CaseSpec("large", 3, 11000, 15, "large_03_11000_orders_15_cabinets.xlsx"),
    CaseSpec("large", 4, 11000, 15, "large_04_11000_orders_15_cabinets.xlsx"),
    CaseSpec("large", 5, 11000, 15, "large_05_11000_orders_15_cabinets.xlsx"),
]


def _shuffled_labels(prefix: str, case_name: str, unique_count: int, total_count: int, rng: random.Random) -> list[str]:
    labels = [f"{prefix}-{case_name}-{idx:05d}" for idx in range(unique_count)]
    values = labels + [rng.choice(labels) for _ in range(total_count - unique_count)]
    rng.shuffle(values)
    return values


def _positive_scaled_values(
    total_count: int,
    target_total: float,
    rng: random.Random,
    minimum: float,
    digits: int,
) -> list[float]:
    raw = [minimum + rng.gammavariate(2.0, 1.0) for _ in range(total_count)]
    factor = target_total / sum(raw)
    values = [round(value * factor, digits) for value in raw]
    values[-1] = round(target_total - sum(values[:-1]), digits)
    if values[-1] <= 0:
        raise ValueError("Generated a non-positive final scaled value")
    return values


def _build_case_rows(spec: CaseSpec) -> tuple[list[list[object]], dict[str, float]]:
    rng = random.Random(20260608 + spec.case_no + spec.cabinets * 100 + len(spec.scale) * 1000)
    sku_ratio = 0.882 + rng.random() * 0.012
    category_ratio = 0.145 + rng.random() * 0.010
    high_priority_ratio = 0.190 + rng.random() * 0.020
    volume_ratio = spec.cabinets + 0.35 + rng.random() * 0.35
    weight_capacity_ratio = 0.655 + rng.random() * 0.035

    sku_count = round(spec.orders * sku_ratio)
    category_count = round(spec.orders * category_ratio)
    high_priority_count = round(spec.orders * high_priority_ratio)
    target_volume = round(volume_ratio * VOLUME_CAP, 5)
    target_weight = round(weight_capacity_ratio * spec.cabinets * WEIGHT_CAP, 5)

    sku_labels = [f"SKU-{spec.name}-{idx:05d}" for idx in range(sku_count)]
    category_labels = [f"CATE-{spec.name}-{idx:05d}" for idx in range(category_count)]
    sku_to_category = {
        sku: category_labels[idx % category_count]
        for idx, sku in enumerate(sku_labels)
    }
    rng.shuffle(sku_labels)
    skus = sku_labels + [rng.choice(sku_labels) for _ in range(spec.orders - sku_count)]
    rng.shuffle(skus)
    categories = [sku_to_category[sku] for sku in skus]
    volumes = _positive_scaled_values(spec.orders, target_volume, rng, minimum=0.005, digits=5)
    weights = _positive_scaled_values(spec.orders, target_weight, rng, minimum=0.01, digits=6)
    high_priority_items = set(rng.sample(range(spec.orders), high_priority_count))

    rows = []
    for idx in range(spec.orders):
        rows.append(
            [
                idx,
                skus[idx],
                rng.randint(1, 30),
                volumes[idx],
                weights[idx],
                categories[idx],
                "NINE_CASE_BENCHMARK",
                0,
                WEIGHT_CAP,
                0,
                0,
                VOLUME_CAP,
                0,
                0,
                UNLIMITED_CAP,
                0,
                UNLIMITED_CAP,
                1 if idx in high_priority_items else 0,
                0,
            ]
        )

    summary = {
        "orders": spec.orders,
        "cabinets": spec.cabinets,
        "sku_count": sku_count,
        "category_count": category_count,
        "high_priority_count": high_priority_count,
        "volume_ratio": sum(volumes) / VOLUME_CAP,
        "weight_capacity_ratio": sum(weights) / (spec.cabinets * WEIGHT_CAP),
    }
    return rows, summary


def _write_case(spec: CaseSpec) -> dict[str, float]:
    rows, summary = _build_case_rows(spec)
    wb = Workbook()
    ws = wb.active
    ws.title = "data"
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(DATA_DIR / spec.file_name)
    return summary


def main() -> None:
    print("case,orders,cabinets,sku,sku_ratio,categories,category_ratio,high,high_ratio,volume_ratio,weight_capacity_ratio")
    for spec in CASES:
        summary = _write_case(spec)
        print(
            f"{spec.file_name},"
            f"{summary['orders']},"
            f"{summary['cabinets']},"
            f"{summary['sku_count']},"
            f"{summary['sku_count'] / summary['orders']:.4f},"
            f"{summary['category_count']},"
            f"{summary['category_count'] / summary['orders']:.4f},"
            f"{summary['high_priority_count']},"
            f"{summary['high_priority_count'] / summary['orders']:.4f},"
            f"{summary['volume_ratio']:.4f},"
            f"{summary['weight_capacity_ratio']:.4f}"
        )


if __name__ == "__main__":
    main()
