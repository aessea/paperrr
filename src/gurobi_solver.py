import time
from collections import defaultdict

import numpy as np

from .evaluator import rho_values
from .models import Instance, SolveResult


def solve_gurobi(instance: Instance, config: dict) -> SolveResult:
    start = time.perf_counter()
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except Exception as exc:
        return SolveResult(
            solver="Gurobi",
            objective=None,
            runtime=time.perf_counter() - start,
            status=f"IMPORT_FAILED: {exc}",
            backend="gurobi",
        )

    gcfg = config["gurobi"]
    try:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", int(gcfg["output_flag"]))
        env.start()
        model = gp.Model(f"container_assignment_{instance.name}", env=env)
    except Exception as exc:
        return SolveResult(
            solver="Gurobi",
            objective=None,
            runtime=time.perf_counter() - start,
            status=f"MODEL_INIT_FAILED: {exc}",
            backend="gurobi",
        )
    model.Params.OutputFlag = int(gcfg["output_flag"])
    model.Params.TimeLimit = float(gcfg["time_limit"])
    model.Params.MIPGap = float(gcfg["mip_gap"])
    if int(gcfg["threads"]) > 0:
        model.Params.Threads = int(gcfg["threads"])

    n = instance.n_items
    k = instance.n_cabinets
    weights = config["objective_weights"]
    residual_weights = config["residual_weights"]

    items_by_sku = defaultdict(list)
    items_by_cat = defaultdict(list)
    for i in range(n):
        items_by_sku[int(instance.sku_ids[i])].append(i)
        items_by_cat[int(instance.category_ids[i])].append(i)

    x = model.addVars(n, k + 1, vtype=GRB.BINARY, name="x")
    y = model.addVars(range(1, k + 1), vtype=GRB.BINARY, name="y")
    u = model.addVars(range(1, k + 1), instance.n_skus, vtype=GRB.BINARY, name="u")
    z = model.addVars(range(1, k + 1), instance.n_categories, vtype=GRB.BINARY, name="z")
    eta = model.addVars(instance.n_skus, vtype=GRB.BINARY, name="eta")
    gamma = model.addVars(instance.n_categories, vtype=GRB.BINARY, name="gamma")
    rv = model.addVars(range(1, k + 1), lb=0.0, vtype=GRB.CONTINUOUS, name="rv")
    rw = model.addVars(range(1, k + 1), lb=0.0, vtype=GRB.CONTINUOUS, name="rw")

    model.addConstrs((gp.quicksum(x[i, l] for l in range(k + 1)) == 1 for i in range(n)), name="assign_one")
    model.addConstrs((y[j] == 1 for j in range(1, k + 1)), name="use_prescribed_cabinets")
    model.addConstrs((x[i, j] <= y[j] for i in range(n) for j in range(1, k + 1)), name="open_upper")
    model.addConstrs((y[j] <= gp.quicksum(x[i, j] for i in range(n)) for j in range(1, k + 1)), name="open_lower")
    model.addConstrs(
        (gp.quicksum(float(instance.volumes[i]) * x[i, j] for i in range(n)) <= float(instance.volume_caps[j]) * y[j] for j in range(1, k + 1)),
        name="volume",
    )
    model.addConstrs(
        (gp.quicksum(float(instance.weights[i]) * x[i, j] for i in range(n)) <= float(instance.weight_caps[j]) * y[j] for j in range(1, k + 1)),
        name="weight",
    )

    for j in range(1, k + 1):
        model.addConstr(gp.quicksum(u[j, s] for s in range(instance.n_skus)) <= int(instance.sku_style_caps[j]), name=f"sku_type_{j}")
        for s, indices in items_by_sku.items():
            model.addConstr(
                gp.quicksum(float(instance.quantities[i]) * x[i, j] for i in indices) <= float(instance.per_sku_qty_caps[j]) * u[j, s],
                name=f"sku_qty_{j}_{s}",
            )
            model.addConstr(u[j, s] <= gp.quicksum(x[i, j] for i in indices), name=f"sku_upper_{j}_{s}")
            for i in indices:
                model.addConstr(x[i, j] <= u[j, s], name=f"sku_lower_{i}_{j}")
        for c, indices in items_by_cat.items():
            model.addConstr(z[j, c] <= gp.quicksum(x[i, j] for i in indices), name=f"cat_upper_{j}_{c}")
            for i in indices:
                model.addConstr(x[i, j] <= z[j, c], name=f"cat_lower_{i}_{j}")
        model.addConstr(rv[j] == float(instance.volume_caps[j]) * y[j] - gp.quicksum(float(instance.volumes[i]) * x[i, j] for i in range(n)), name=f"rv_{j}")
        model.addConstr(rw[j] == float(instance.weight_caps[j]) * y[j] - gp.quicksum(float(instance.weights[i]) * x[i, j] for i in range(n)), name=f"rw_{j}")

    for s in range(instance.n_skus):
        model.addConstrs((u[j, s] <= eta[s] for j in range(1, k + 1)), name=f"eta_lower_{s}")
        model.addConstr(eta[s] <= gp.quicksum(u[j, s] for j in range(1, k + 1)), name=f"eta_upper_{s}")
    for c in range(instance.n_categories):
        model.addConstrs((z[j, c] <= gamma[c] for j in range(1, k + 1)), name=f"gamma_lower_{c}")
        model.addConstr(gamma[c] <= gp.quicksum(z[j, c] for j in range(1, k + 1)), name=f"gamma_upper_{c}")

    rho = rho_values(k)
    d_h = max(1.0, float(instance.priority_scores.sum()))
    d_c = max(1, instance.n_categories)
    d_s = max(1, instance.n_skus)
    d_r = max(1, k)

    high_obj = gp.quicksum(float(instance.priority_scores[i]) * float(rho[l]) * x[i, l] for i in range(n) for l in range(k + 1)) / d_h
    cat_obj = gp.quicksum(gp.quicksum(z[j, c] for j in range(1, k + 1)) - gamma[c] for c in range(instance.n_categories)) / d_c
    sku_obj = gp.quicksum(gp.quicksum(u[j, s] for j in range(1, k + 1)) - eta[s] for s in range(instance.n_skus)) / d_s
    res_obj = gp.quicksum(
        residual_weights["volume"] * rv[j] / float(instance.volume_caps[j])
        + residual_weights["weight"] * rw[j] / float(instance.weight_caps[j])
        for j in range(1, k + 1)
    ) / d_r
    model.setObjective(
        weights["high_priority"] * high_obj
        + weights["category_split"] * cat_obj
        + weights["sku_split"] * sku_obj
        + weights["residual_capacity"] * res_obj,
        GRB.MINIMIZE,
    )

    model.optimize()
    runtime = time.perf_counter() - start
    assignment = None
    objective = None
    bound = None
    if model.SolCount > 0:
        objective = float(model.ObjVal)
        assignment = np.zeros(n, dtype=np.int32)
        for i in range(n):
            assignment[i] = max(range(k + 1), key=lambda l: x[i, l].X)
    try:
        bound = float(model.ObjBound)
    except Exception:
        bound = None
    return SolveResult(
        solver="Gurobi",
        objective=objective,
        runtime=runtime,
        status=str(model.Status),
        assignment=assignment,
        bound=bound,
        backend="gurobi",
        extra={"gap": getattr(model, "MIPGap", None), "sol_count": model.SolCount},
    )
