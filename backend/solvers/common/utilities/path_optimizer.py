from collections import deque


class PathOptimizer:
    def __init__(self, rows, cols, filled=False, unavailable_coords=None):
        self.usage_map = {}  # Tracks how many times each tile has been used
        self.rows = rows
        self.cols = cols
        self.filled = filled
        self.unavailable_coords = unavailable_coords

    def get_usage(self, coord):
        """Get the number of times a coordinate has been used"""
        return self.usage_map.get(coord, 0)

    def update_usage(self, path):
        """Update usage counts for a path"""
        for coord in path:
            self.usage_map[coord] = self.usage_map.get(coord, 0) + 1

    def is_valid(self, coord):
        x, y = coord
        if self.unavailable_coords and [x ,y] in self.unavailable_coords:
            return False
        if self.filled:
            return 0 <= x < self.cols and 0 <= y < self.rows
        return (0 <= x < self.cols and 0 <= y < self.rows and
                (x == 0 or x == self.cols - 1 or y == 0 or y == self.rows - 1))

    def get_neighbors(self, coord):
        x, y = coord
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [n for n in neighbors if self.is_valid(n)]

    def find_balanced_path(self, start, end):
        """Find the shortest path with minimum usage among equally short paths"""
        if start == end:
            return [start]

        # First BFS to find the shortest distance
        queue = deque([(start, 0)])
        distances = {start: 0}
        shortest_distance = None

        while queue:
            current, dist = queue.popleft()

            if current == end:
                shortest_distance = dist
                break

            for neighbor in self.get_neighbors(current):
                if neighbor not in distances:
                    distances[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))

        if shortest_distance is None:
            return []  # No path exists

        # Find all paths of shortest length
        shortest_paths = []
        queue = deque([(start, [start])])

        while queue:
            current, path = queue.popleft()

            if len(path) > shortest_distance + 1:
                break

            if current == end and len(path) == shortest_distance + 1:
                shortest_paths.append(path)
                continue

            for neighbor in self.get_neighbors(current):
                if neighbor not in path and distances.get(neighbor, float('inf')) == len(path):
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))

        if not shortest_paths:
            return []

        # Choose the path with minimum total usage
        best_path = min(shortest_paths,
                        key=lambda p: sum(self.get_usage(coord) for coord in p))

        self.update_usage(best_path)  # Update usage for chosen path
        return best_path

    def find_shortest_path(self, start, end):
        queue = deque([(start, [])])
        visited = set()

        while queue:
            coord, path = queue.popleft()
            if coord == end:
                return path + [end]
            if coord in visited:
                continue
            visited.add(coord)
            for neighbor in self.get_neighbors(coord):
                queue.append((neighbor, path + [coord]))

        return []
if __name__ == "__main__":
    po = PathOptimizer(1,20)
    print( po.find_balanced_path((1,0),(4,0)))