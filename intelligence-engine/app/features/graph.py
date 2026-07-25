"""Feature dependency graph — topo order, cycle detection, invalidation."""

from __future__ import annotations

from collections import defaultdict, deque


class DependencyCycleError(Exception):
    pass


class FeatureDependencyGraph:
    def __init__(self) -> None:
        self._deps: dict[str, set[str]] = defaultdict(set)  # feature -> dependencies
        self._dependents: dict[str, set[str]] = defaultdict(set)  # feature -> dependents

    def set_dependencies(self, feature_id: str, dependencies: list[str]) -> None:
        # clear old reverse edges
        for old in list(self._deps.get(feature_id, ())):
            self._dependents[old].discard(feature_id)
        self._deps[feature_id] = set(dependencies)
        for dep in dependencies:
            self._dependents[dep].add(feature_id)
        self.topological_order([feature_id])  # validates no cycle involving this node

    def dependencies_of(self, feature_id: str) -> set[str]:
        return set(self._deps.get(feature_id, ()))

    def dependents_of(self, feature_id: str) -> set[str]:
        return set(self._dependents.get(feature_id, ()))

    def transitive_dependents(self, feature_id: str) -> set[str]:
        seen: set[str] = set()
        stack = list(self._dependents.get(feature_id, ()))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self._dependents.get(node, ()))
        return seen

    def topological_order(self, feature_ids: list[str] | None = None) -> list[str]:
        """Kahn topo sort over full graph or induced subgraph of feature_ids + deps."""
        if feature_ids is None:
            nodes = set(self._deps.keys()) | {d for deps in self._deps.values() for d in deps}
            nodes |= set(self._dependents.keys())
        else:
            nodes = set()
            stack = list(feature_ids)
            while stack:
                node = stack.pop()
                if node in nodes:
                    continue
                nodes.add(node)
                stack.extend(self._deps.get(node, ()))

        indegree = {n: 0 for n in nodes}
        for n in nodes:
            for dep in self._deps.get(n, ()):
                if dep in nodes:
                    indegree[n] += 1

        queue = deque(sorted(n for n, deg in indegree.items() if deg == 0))
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for child in sorted(self._dependents.get(node, ())):
                if child not in indegree:
                    continue
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(order) != len(nodes):
            raise DependencyCycleError("feature dependency cycle detected")
        return order
