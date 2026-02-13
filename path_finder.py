from collections import deque


class PathFinder:
    def __init__(self, maze, width, height, start, end, update_cell):
        self.maze = maze
        self.width = width
        self.height = height
        self.start = start
        self.end = end
        self.update_cell = update_cell

    def find_path_dfs(self):
        """深度优先寻路"""
        x_size, y_size = self.width, self.height
        stack = [self.start]
        visited = {self.start}

        direction = [
            lambda x, y: (x - 1, y),
            lambda x, y: (x, y - 1),
            lambda x, y: (x + 1, y),
            lambda x, y: (x, y + 1)
        ]

        while stack:
            cur_point = stack[-1]
            if cur_point != self.start and cur_point != self.end:
                self.update_cell(*cur_point, 'visited')

            for dir_ in direction:
                next_point = dir_(*cur_point)
                x, y = next_point

                if (0 <= x < x_size and 0 <= y < y_size and
                        self.maze[y][x] == 0):

                    if next_point not in visited:
                        stack.append(next_point)
                        visited.add(next_point)

                        if next_point != self.start and next_point != self.end:
                            self.update_cell(x, y, 'current')

                        if next_point == self.end:
                            return stack
                        break
            else:
                stack.pop()
                if cur_point != self.start and cur_point != self.end:
                    self.update_cell(*cur_point, 'path')

        return None

    def find_path_bfs(self):
        """广度优先寻路"""
        x_size, y_size = self.width, self.height
        queue = deque([self.start])
        previous = {self.start: None}
        visited = {self.start}

        direction = [
            lambda x, y: (x - 1, y),
            lambda x, y: (x, y - 1),
            lambda x, y: (x + 1, y),
            lambda x, y: (x, y + 1)
        ]

        while queue:
            cur_point = queue.popleft()

            if cur_point != self.start and cur_point != self.end:
                self.update_cell(*cur_point, 'visited')

            for dir_ in direction:
                next_point = dir_(*cur_point)
                x, y = next_point

                if 0 <= x < x_size and 0 <= y < y_size and self.maze[y][x] == 0 and next_point not in visited:

                    queue.append(next_point)
                    previous[next_point] = cur_point
                    visited.add(next_point)

                    if next_point != self.start and next_point != self.end:
                        self.update_cell(x, y, 'frontier')

                    if next_point == self.end:
                        # 回溯路径
                        path = []
                        cur = self.end
                        while cur is not None:
                            path.append(cur)
                            cur = previous[cur]
                        path.reverse()
                        return path

        return None

    def find_path_astar(self):
        """A*算法寻路"""
        import heapq

        def heuristic(a, b):
            """曼哈顿距离"""
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        x_size, y_size = self.width, self.height

        open_set = []
        heapq.heappush(open_set, (0, self.start))

        came_from = {self.start: None}
        g_score = {self.start: 0}

        direction = [
            lambda x, y: (x - 1, y),
            lambda x, y: (x, y - 1),
            lambda x, y: (x + 1, y),
            lambda x, y: (x, y + 1)
        ]

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == self.end:
                # 回溯路径
                path = []
                cur = self.end
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path

            if current != self.start and current != self.end:
                self.update_cell(*current, 'visited')

            for dir_ in direction:
                neighbor = dir_(*current)
                x, y = neighbor

                if 0 <= x < x_size and 0 <= y < y_size and self.maze[y][x] == 0:
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        priority = tentative_g + heuristic(neighbor, self.end)
                        heapq.heappush(open_set, (priority, neighbor))

                        if neighbor != self.start and neighbor != self.end:
                            self.update_cell(x, y, 'frontier')

        return None
