import numpy as np

from .models import Instance, ObjectiveBreakdown


def rho_values(n_cabinets: int) -> np.ndarray:
    rho = np.ones(n_cabinets + 1, dtype=np.float64)
    denom = max(1, n_cabinets - 1)
    for j in range(1, n_cabinets + 1):
        rho[j] = (j - 1) / denom
    return rho


def evaluate_solution(instance: Instance, assignment: np.ndarray, config: dict) -> ObjectiveBreakdown:
    assignment = np.asarray(assignment, dtype=np.int32)
    if assignment.shape[0] != instance.n_items:
        raise ValueError("Assignment length does not match number of items")

    weights = config["objective_weights"]
    residual_weights = config["residual_weights"]
    k = instance.n_cabinets
    rho = rho_values(k)

    d_h = max(1.0, float(instance.priority_scores.sum()))
    high = float(np.sum(instance.priority_scores * rho[assignment])) / d_h

    sku_seen = np.zeros((k + 1, instance.n_skus), dtype=bool)
    cat_seen = np.zeros((k + 1, instance.n_categories), dtype=bool)
    load_v = np.zeros(k + 1, dtype=np.float64)
    load_w = np.zeros(k + 1, dtype=np.float64)

    for i, pos in enumerate(assignment):
        if pos < 0 or pos > k:
            raise ValueError(f"Invalid position {pos} for item {i}")
        if pos > 0:
            sku_seen[pos, instance.sku_ids[i]] = True
            cat_seen[pos, instance.category_ids[i]] = True
            load_v[pos] += instance.volumes[i]
            load_w[pos] += instance.weights[i]

    sku_cabinets = sku_seen[1:].sum(axis=0)
    cat_cabinets = cat_seen[1:].sum(axis=0)
    sku_split = float(np.maximum(0, sku_cabinets - 1).sum()) / max(1, instance.n_skus)
    cat_split = float(np.maximum(0, cat_cabinets - 1).sum()) / max(1, instance.n_categories)

    residual = 0.0
    for j in instance.normal_positions:
        residual += residual_weights["volume"] * (instance.volume_caps[j] - load_v[j]) / instance.volume_caps[j]
        residual += residual_weights["weight"] * (instance.weight_caps[j] - load_w[j]) / instance.weight_caps[j]
    residual /= max(1, k)

    total = (
        weights["high_priority"] * high
        + weights["category_split"] * cat_split
        + weights["sku_split"] * sku_split
        + weights["residual_capacity"] * residual
    )
    return ObjectiveBreakdown(
        total=float(total),
        high_priority=float(high),
        category_split=float(cat_split),
        sku_split=float(sku_split),
        residual_capacity=float(residual),
    )
