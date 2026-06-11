"""Pure computation core for FP&A.

Kept free of FastAPI/DB types so it can be unit-tested in isolation and reused.
- variance(): aggregate planned vs actual on a chosen dimension.
- apply_levers(): project a scenario by adjusting matching budget lines.
"""
from collections import defaultdict
from typing import Iterable


def _matches(line: dict, field: str, value: str) -> bool:
    return value == "*" or str(line.get(field)) == value


def apply_levers(lines: Iterable[dict], levers: Iterable[dict]) -> list[dict]:
    """Return new lines with each lever applied in order.

    A 'percent' lever scales the matching line's amount; an 'absolute' lever
    adds a flat amount. Levers compound when more than one matches a line.
    """
    projected = [dict(l) for l in lines]
    for lever in levers:
        field, value = lever["target_field"], lever["target_value"]
        kind, amt = lever["adjustment_type"], lever["adjustment_value"]
        for line in projected:
            if not _matches(line, field, value):
                continue
            if kind == "percent":
                line["planned_amount"] *= (1 + amt / 100.0)
            elif kind == "absolute":
                line["planned_amount"] += amt
    return projected


def _group_sum(lines: Iterable[dict], key: str, value_field: str) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for line in lines:
        out[str(line[key])] += float(line[value_field])
    return dict(out)


def variance(planned_lines: Iterable[dict], actual_lines: Iterable[dict], group_by: str) -> list[dict]:
    """Compare planned vs actual totals grouped by a dimension."""
    planned = _group_sum(planned_lines, group_by, "planned_amount")
    actual = _group_sum(actual_lines, group_by, "actual_amount")
    rows = []
    for dim in sorted(set(planned) | set(actual)):
        p = planned.get(dim, 0.0)
        a = actual.get(dim, 0.0)
        v = a - p
        rows.append({
            "dimension": dim,
            "planned": round(p, 2),
            "actual": round(a, 2),
            "variance": round(v, 2),
            "variance_pct": round((v / p * 100) if p else 0.0, 2),
        })
    return rows


def compare_scenario(base_lines: list[dict], projected_lines: list[dict], group_by: str) -> dict:
    """Compare base budget vs a projected scenario grouped by a dimension."""
    base = _group_sum(base_lines, group_by, "planned_amount")
    scen = _group_sum(projected_lines, group_by, "planned_amount")
    rows = []
    for dim in sorted(set(base) | set(scen)):
        b = base.get(dim, 0.0)
        s = scen.get(dim, 0.0)
        rows.append({
            "dimension": dim,
            "base": round(b, 2),
            "scenario": round(s, 2),
            "delta": round(s - b, 2),
        })
    return {
        "group_by": group_by,
        "base_total": round(sum(base.values()), 2),
        "scenario_total": round(sum(scen.values()), 2),
        "rows": rows,
    }
