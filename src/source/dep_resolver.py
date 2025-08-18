"""
Dependency resolver for handling dependencies and topological sorting between sources.
"""

from collections import defaultdict, deque
from loguru import logger

from model import SourceModel


class DependencyResolver:
    """Dependency Resolver"""

    def __init__(self, sources: list[SourceModel]):
        self.sources = {str(source.target_path): source for source in sources}
        self.dependencies = self._build_dependency_graph()

    def _build_dependency_graph(self) -> dict[str, set[str]]:
        """Build dependency graph, return {source_path: {set of dependent source_paths}}"""
        dependencies = defaultdict(set)

        for target_path, source in self.sources.items():
            for resource in source.resources:
                if resource.is_source_reference():
                    referenced_target = resource.get_reference_target()
                    if referenced_target not in self.sources:
                        raise ValueError(
                            f"Source '{target_path}' references unknown source '{referenced_target}'"
                        )
                    dependencies[target_path].add(referenced_target)
                    logger.debug(
                        f"Found dependency: {target_path} -> {referenced_target}"
                    )

        return dict(dependencies)

    def _detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]) -> bool:
            if node in rec_stack:
                # Found a cycle, extract the cycle path
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for dependency in self.dependencies.get(node, []):
                if dfs(dependency, path + [node]):
                    return True

            rec_stack.remove(node)
            return False

        for source_path in self.sources:
            if source_path not in visited:
                dfs(source_path, [])

        return cycles

    def resolve_order(self) -> list[str]:
        """
        Resolve processing order using topological sort.
        Returns a list of target_paths sorted by dependency order.
        """
        # Detect circular dependencies
        cycles = self._detect_cycles()
        if cycles:
            cycle_strs = [" -> ".join(cycle) for cycle in cycles]
            raise ValueError(f"Circular dependencies detected: {'; '.join(cycle_strs)}")

        # Calculate in-degree (how many other sources each source depends on)
        in_degree = {
            source_path: len(deps) for source_path, deps in self.dependencies.items()
        }
        # Set in-degree to 0 for sources with no dependencies
        for source_path in self.sources:
            if source_path not in in_degree:
                in_degree[source_path] = 0

        # Topological sort
        queue = deque(
            [source_path for source_path, degree in in_degree.items() if degree == 0]
        )
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # For each node that depends on the current node, decrease its in-degree
            for source_path in self.sources:
                if current in self.dependencies.get(source_path, set()):
                    in_degree[source_path] -= 1
                    if in_degree[source_path] == 0:
                        queue.append(source_path)

        # Check if all nodes have been processed
        if len(result) != len(self.sources):
            unprocessed = set(self.sources.keys()) - set(result)
            raise ValueError(f"Failed to resolve dependencies for: {unprocessed}")

        logger.info(f"Dependency resolution order: {' -> '.join(result)}")
        return [self.sources[target_path] for target_path in result]

    def get_dependencies(self, target_path: str) -> set[str]:
        """Get direct dependencies of the specified source"""
        return self.dependencies.get(target_path, set())

    def get_all_dependencies(self, target_path: str) -> set[str]:
        """Get all dependencies (including indirect) of the specified source"""
        all_deps = set()
        to_visit = deque([target_path])
        visited = set()

        while to_visit:
            current = to_visit.popleft()
            if current in visited:
                continue
            visited.add(current)

            deps = self.dependencies.get(current, set())
            all_deps.update(deps)
            to_visit.extend(deps)

        return all_deps
