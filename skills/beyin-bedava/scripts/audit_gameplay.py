#!/usr/bin/env python3
"""Audit exported grid, graph, and timing levels against an explicit game design contract."""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path


def unique_strings(value):
    return (isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)
            and len(set(value)) == len(value))


def reachable(grid, start, requires_key):
    queue = deque([(start, False, 0)])
    seen = {(start, False)}
    while queue:
        (x, y), key, steps = queue.popleft()
        if grid[y][x] == "G" and (key or not requires_key):
            return steps
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] != "#":
                state = ((nx, ny), key or grid[ny][nx] == "K")
                if state not in seen:
                    seen.add(state)
                    queue.append((*state, steps + 1))
    return None


def reachable_graph(name, graph, requires_key):
    if not isinstance(graph, dict):
        raise ValueError(f"{name}: graph must be an object")
    nodes = graph.get("nodes")
    if not unique_strings(nodes) or not nodes:
        raise ValueError(f"{name}: graph requires unique nonempty nodes")
    node_set = set(nodes)
    start, goal, key_node = graph.get("start"), graph.get("goal"), graph.get("key_node")
    if start not in node_set or goal not in node_set:
        raise ValueError(f"{name}: graph start and goal must be declared nodes")
    if key_node is not None and key_node not in node_set:
        raise ValueError(f"{name}: graph key_node must be a declared node")
    edges = graph.get("edges")
    if not isinstance(edges, list):
        raise ValueError(f"{name}: graph edges must be a list")
    adjacency = {node: [] for node in nodes}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or edge[0] not in node_set or edge[1] not in node_set:
            raise ValueError(f"{name}: invalid graph edge {edge!r}")
        adjacency[edge[0]].append(edge[1])
    if requires_key and key_node is None:
        return None
    initial_key = start == key_node
    queue = deque([(start, initial_key, 0)])
    seen = {(start, initial_key)}
    while queue:
        node, has_key, steps = queue.popleft()
        if node == goal and (has_key or not requires_key):
            return steps
        for nxt in adjacency[node]:
            state = (nxt, has_key or nxt == key_node)
            if state not in seen:
                seen.add(state)
                queue.append((*state, steps + 1))
    return None


def _is_finite_num(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_timing(name, timing, policy, issues):
    if not isinstance(timing, dict):
        raise ValueError(f"{name}: timing must be an object")
    window = timing.get("reaction_window_ms")
    if not _is_finite_num(window) or window <= 0:
        raise ValueError(f"{name}: reaction_window_ms must be a positive number")
    gap = timing.get("min_gap_ms")
    if gap is not None and (not _is_finite_num(gap) or gap < 0):
        raise ValueError(f"{name}: min_gap_ms must be non-negative")
    concurrent = timing.get("concurrent_max")
    if concurrent is not None and (type(concurrent) is not int or concurrent < 1):
        raise ValueError(f"{name}: concurrent_max must be a positive integer")
    min_window = policy.get("min_reaction_window_ms")
    if min_window is not None and window < min_window:
        issues.append({"check": "unfair_timing", "level": name, "reason": "reaction_window_below_minimum"})
    min_gap = policy.get("min_event_gap_ms")
    if min_gap is not None and gap is not None and gap < min_gap:
        issues.append({"check": "unfair_timing", "level": name, "reason": "event_gap_below_minimum"})
    max_concurrent = policy.get("max_concurrent_events")
    if max_concurrent is not None and concurrent is not None and concurrent > max_concurrent:
        issues.append({"check": "unfair_timing", "level": name, "reason": "concurrent_events_exceed_max"})


def audit(document):
    mechanics, levels, policy = (document[key] for key in ("mechanics", "levels", "policy"))
    if not isinstance(mechanics, dict) or not mechanics:
        raise ValueError("declare at least one mechanic")
    for name, rule in mechanics.items():
        if not name.strip() or not all(isinstance(rule[key], str) and rule[key].strip()
                                      for key in ("verb", "feedback", "failure", "recovery")):
            raise ValueError(f"invalid mechanic contract: {name}")
    if not isinstance(levels, list) or not levels or not unique_strings([level["id"] for level in levels]):
        raise ValueError("declare levels with unique IDs")
    cap = policy["max_difficulty_step"]
    minimum = policy["min_mechanic_sets"]
    has_grid = any("grid" in level for level in levels)
    repeat = policy["max_layout_similarity"] if has_grid else policy.get("max_layout_similarity")
    if type(cap) is not int or cap < 0 or type(minimum) is not int or minimum < 1:
        raise ValueError("invalid difficulty step or mechanic-set minimum")
    if repeat is not None and (type(repeat) not in (int, float) or not 0 < repeat <= 1):
        raise ValueError("layout similarity must be in (0, 1]")
    issues, metrics, layouts, sets, used = [], [], {}, set(), set()
    previous = None
    for level in levels:
        name, tags, difficulty = (level[key] for key in ("id", "mechanics", "difficulty"))
        if not any(kind in level for kind in ("grid", "graph", "timing")):
            raise ValueError(f"{name}: declare grid, graph, or timing level specification")
        if not unique_strings(tags) or not tags or set(tags) - mechanics.keys():
            raise ValueError(f"{name}: invalid or unknown mechanics")
        if type(difficulty) is not int or difficulty < 1:
            raise ValueError(f"{name}: expected positive integer difficulty")
        requires_key = level.get("requires_key", False)
        budget = level.get("move_budget")
        if type(requires_key) is not bool or (budget is not None and (type(budget) is not int or budget < 1)):
            raise ValueError(f"{name}: invalid goal rule or move budget")
        steps = None
        if "grid" in level:
            grid = level["grid"]
            if (not isinstance(grid, list) or not grid or not isinstance(grid[0], str) or not grid[0]
                    or any(not isinstance(row, str) or len(row) != len(grid[0]) or set(row) - set("#.SGK")
                           for row in grid)):
                raise ValueError(f"{name}: expected a rectangular #.SGK grid")
            cells = "".join(grid)
            if cells.count("S") != 1 or cells.count("G") != 1:
                raise ValueError(f"{name}: expected exactly one start and goal")
            start = (cells.index("S") % len(grid[0]), cells.index("S") // len(grid[0]))
            steps = reachable(grid, start, requires_key)
            if steps is None or (budget is not None and steps > budget):
                issues.append({"check": "unwinnable", "level": name})
            for other, other_grid in layouts.items():
                if (len(grid), len(grid[0])) != (len(other_grid), len(other_grid[0])):
                    continue
                # Compare exact orientation and horizontal/vertical reflections.
                variants = (grid, grid[::-1], [row[::-1] for row in grid],
                            [row[::-1] for row in grid[::-1]])
                similarity = max(sum(a == b for a, b in zip("".join(variant), "".join(other_grid)))
                                 for variant in variants) / len(cells)
                if similarity >= repeat:
                    issues.append({"check": "repeated_layout", "level": name, "compared_with": other,
                                   "similarity": round(similarity, 4)})
            layouts[name] = grid
        if "graph" in level:
            graph_steps = reachable_graph(name, level["graph"], requires_key)
            if steps is None:
                steps = graph_steps
            if graph_steps is None or (budget is not None and graph_steps > budget):
                issues.append({"check": "unwinnable", "level": name})
        if "timing" in level:
            validate_timing(name, level["timing"], policy, issues)
        if previous is not None and abs(difficulty - previous) > cap:
            issues.append({"check": "difficulty_jump", "level": name, "step": difficulty - previous})
        previous = difficulty
        used.update(tags)
        sets.add(frozenset(tags))
        metrics.append({"id": name, "shortest_solution_moves": steps, "difficulty": difficulty})
    for name in sorted(mechanics.keys() - used):
        issues.append({"check": "unused_mechanic", "mechanic": name})
    if len(sets) < minimum:
        issues.append({"check": "low_mechanic_variety", "observed": len(sets), "required": minimum})
    return {"evidence_kind": "static_gameplay_analysis", "levels": metrics,
            "distinct_mechanic_sets": len(sets), "issues": issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, KeyError, ValueError, TypeError, AttributeError) as exc:
        parser.exit(2, f"Invalid gameplay document: {exc}\n")
    print(json.dumps(result, indent=2))
    return int(bool(result["issues"]))


if __name__ == "__main__":
    sys.exit(main())
