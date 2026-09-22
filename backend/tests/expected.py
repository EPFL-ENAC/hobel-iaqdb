"""Statistics recomputed in plain Python from the fixture series, so every
route answer is checked against an independent implementation."""

import math
from datetime import datetime

from tests.fixtures import Fixture, daily, hourly, mean

BUILDING_OF = {"S1": "B1", "S2": "B1", "S3": "B2", "S9": "B1"}
COUNTRY_OF = {"B1": "CH", "B2": "DE"}
SPACE_TYPE = {"S1": "office", "S2": "meeting room", "S3": "classroom"}


def bucket_values(points, grain: str) -> list[float]:
    """The values a grain exposes: raw readings or bucket means."""
    if grain == "raw":
        return [v for _, v in points]
    groups = hourly(points) if grain == "hour" else daily(points)
    return [mean(v) for v in groups.values()]


def percentile(values: list[float], p: float) -> float:
    """PostgreSQL percentile_cont: linear interpolation."""
    ordered = sorted(values)
    position = p * (len(ordered) - 1)
    lo = math.floor(position)
    hi = math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def stats_of(series: list[list[tuple[datetime, float]]], grain: str) -> dict:
    """Expected `stats` payload of buckets made of these series."""
    values = [v for points in series for v in bucket_values(points, grain)]
    raw = [v for points in series for _, v in points]
    return {
        "mean": mean(raw),
        "sd": stddev(values),
        "min": min(values),
        "p05": percentile(values, 0.05),
        "p25": percentile(values, 0.25),
        "p50": percentile(values, 0.5),
        "p75": percentile(values, 0.75),
        "p95": percentile(values, 0.95),
        "max": max(values),
        "n": len(values),
        "n_records": len(raw),
    }


def series_of(fx: Fixture, slug: str, spaces=None, window=None):
    """Series of a parameter, optionally restricted to spaces and a
    half-open [from, to) window."""
    out = []
    for (s, space), points in fx.series.items():
        if s != slug or (spaces is not None and space not in spaces):
            continue
        if window:
            points = [(t, v) for t, v in points if window[0] <= t < window[1]]
        if points:
            out.append(points)
    return out


def paired_hours(fx: Fixture, x: str, y: str, spaces) -> list[tuple[float, float]]:
    """(x, y) hourly means where both exist in the same space and hour."""
    points = []
    for space in spaces:
        hx = hourly(fx.series.get((x, space), []))
        hy = hourly(fx.series.get((y, space), []))
        for hour in sorted(set(hx) & set(hy)):
            points.append((mean(hx[hour]), mean(hy[hour])))
    return points


def regression(points: list[tuple[float, float]]) -> dict:
    n = len(points)
    mx = mean([p[0] for p in points])
    my = mean([p[1] for p in points])
    sxx = sum((x - mx) ** 2 for x, _ in points)
    syy = sum((y - my) ** 2 for _, y in points)
    sxy = sum((x - mx) * (y - my) for x, y in points)
    slope = sxy / sxx
    r = sxy / math.sqrt(sxx * syy)
    return {"n": n, "slope": slope, "intercept": my - slope * mx, "r": r, "r2": r * r}


def ranks(values: list[float]) -> list[float]:
    """Lowest rank for ties, as PostgreSQL rank()."""
    ordered = sorted(values)
    return [ordered.index(v) + 1 for v in values]


def spearman(points: list[tuple[float, float]]) -> float:
    rx = ranks([p[0] for p in points])
    ry = ranks([p[1] for p in points])
    return regression(list(zip(rx, ry)))["r"]
