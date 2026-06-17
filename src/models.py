from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np


@dataclass(frozen=True)
class Instance:
    name: str
    scale: str
    path: str
    n_cabinets: int
    item_ids: np.ndarray
    sku_ids: np.ndarray
    category_ids: np.ndarray
    sku_labels: list[str]
    category_labels: list[str]
    volumes: np.ndarray
    weights: np.ndarray
    quantities: np.ndarray
    high_priority: np.ndarray
    priority_scores: np.ndarray
    volume_caps: np.ndarray
    weight_caps: np.ndarray
    sku_style_caps: np.ndarray
    per_sku_qty_caps: np.ndarray

    @property
    def n_items(self) -> int:
        return int(self.volumes.shape[0])

    @property
    def n_skus(self) -> int:
        return len(self.sku_labels)

    @property
    def n_categories(self) -> int:
        return len(self.category_labels)

    @property
    def positions(self) -> range:
        return range(self.n_cabinets + 1)

    @property
    def normal_positions(self) -> range:
        return range(1, self.n_cabinets + 1)


@dataclass(frozen=True)
class ObjectiveBreakdown:
    total: float
    high_priority: float
    category_split: float
    sku_split: float
    residual_capacity: float


@dataclass
class SolveResult:
    solver: str
    objective: Optional[float]
    runtime: float
    status: str
    assignment: Optional[np.ndarray] = None
    bound: Optional[float] = None
    backend: str = ""
    extra: Dict[str, object] = field(default_factory=dict)
