from collections import deque
import heapq


class PathFinder:
    DIRECTIONS = [
            lambda x, y: (x - 1, y),
            lambda x, y: (x, y - 1),
            lambda x, y: (x + 1, y),
            lambda x, y: (x, y + 1)
        ]

    def __init__(self, maze, width, height, start, end, update_cell):
        self.maze = maze
        self.width = width
        self.height = height
        self.start = start
        self.end = end
        self.update_cell = update_cell

    def find_path_dfs(self):
        """深度优先寻路"""
        stack = [self.start]
        visited = {self.start}

        while stack:
            cur_point = stack[-1]
            if cur_point != self.start and cur_point != self.end:
                self.update_cell(*cur_point, 'visited')

            for dir_ in self.DIRECTIONS:
                next_point = dir_(*cur_point)
                x, y = next_point

                if 0 <= x < self.width and 0 <= y < self.height and self.maze[y][x] == 0:
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
        queue = deque([self.start])
        came_from = {self.start: None}
        visited = {self.start}

        while queue:
            cur_point = queue.popleft()

            if cur_point == self.end:
                # 回溯路径
                path = []
                cur = self.end
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                return path

            if cur_point != self.start and cur_point != self.end:
                self.update_cell(*cur_point, 'current')

            for dir_ in self.DIRECTIONS:
                next_point = dir_(*cur_point)
                x, y = next_point

                if 0 <= x < self.width and 0 <= y < self.height and self.maze[y][x] == 0 and next_point not in visited:
                    queue.append(next_point)
                    came_from[next_point] = cur_point
                    visited.add(next_point)

                    if next_point != self.start and next_point != self.end:
                        self.update_cell(x, y, 'frontier')

            if cur_point != self.start and cur_point != self.end:
                self.update_cell(*cur_point, 'visited')

        return None

    def find_path_dijkstra(self):
        """Dijkstra算法寻路"""
        open_set = []
        heapq.heappush(open_set, (0, self.start))

        came_from = {self.start: None}
        g_score = {self.start: 0}

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
                self.update_cell(*current, 'current')

            for dir_ in self.DIRECTIONS:
                neighbor = dir_(*current)
                x, y = neighbor

                if 0 <= x < self.width and 0 <= y < self.height and self.maze[y][x] == 0:
                    new_cost = g_score[current] + 1
                    if neighbor not in g_score or new_cost < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = new_cost
                        heapq.heappush(open_set, (new_cost, neighbor))

                        if neighbor != self.start and neighbor != self.end:
                            self.update_cell(x, y, 'frontier')
            if current != self.start and current != self.end:
                self.update_cell(*current, 'visited')

        return None

    def find_path_gbfs(self):
        """GBFS算法寻路"""
        def heuristic(a, b):
            """曼哈顿距离"""
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (heuristic(self.start, self.end), self.start))

        came_from = {self.start: None}
        visited = {self.start}

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
                self.update_cell(*current, 'current')

            for dir_ in self.DIRECTIONS:
                neighbor = dir_(*current)
                x, y = neighbor

                if 0 <= x < self.width and 0 <= y < self.height and self.maze[y][x] == 0:
                    if neighbor not in visited:
                        came_from[neighbor] = current
                        visited.add(neighbor)
                        priority = heuristic(neighbor, self.end)
                        heapq.heappush(open_set, (priority, neighbor))

                        if neighbor != self.start and neighbor != self.end:
                            self.update_cell(x, y, 'frontier')
            if current != self.start and current != self.end:
                self.update_cell(*current, 'visited')

        return None

    def find_path_astar(self):
        """A*算法寻路"""
        def heuristic(a, b):
            """曼哈顿距离"""
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, self.start))

        came_from = {self.start: None}
        g_score = {self.start: 0}

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
                self.update_cell(*current, 'current')

            for dir_ in self.DIRECTIONS:
                neighbor = dir_(*current)
                x, y = neighbor

                if 0 <= x < self.width and 0 <= y < self.height and self.maze[y][x] == 0:
                    new_cost = g_score[current] + 1
                    if neighbor not in g_score or new_cost < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = new_cost
                        priority = new_cost + heuristic(neighbor, self.end)
                        heapq.heappush(open_set, (priority, neighbor))

                        if neighbor != self.start and neighbor != self.end:
                            self.update_cell(x, y, 'frontier')
            if current != self.start and current != self.end:
                self.update_cell(*current, 'visited')

        return None

    def find_path_bidirectional_dfs(self):
        """双向DFS寻路"""
        # 初始化两个方向的栈和访问记录
        # 前向搜索(从起点开始)
        stack_forward = [self.start]
        visited_forward = {self.start}
        parent_forward = {self.start: None}  # 记录前驱节点

        # 后向搜索(从终点开始)
        stack_backward = [self.end]
        visited_backward = {self.end}
        parent_backward = {self.end: None}  # 记录后继节点

        # 相遇点
        meeting_point = None

        # 开始双向搜索
        while stack_forward and stack_backward and not meeting_point:
            # 交替扩展，每次扩展一个节点
            meeting_point = self._dfs_step(stack_forward, visited_forward, visited_backward, 
                                        parent_forward, self.DIRECTIONS, is_forward=True)

            if not meeting_point:
                meeting_point = self._dfs_step(stack_backward, visited_backward, visited_forward,
                                            parent_backward, self.DIRECTIONS, is_forward=False)

        # 构建完整路径
        if meeting_point:
            return self._construct_bidirectional_path(meeting_point, parent_forward, parent_backward)

        return None

    def _dfs_step(self, stack, visited_self, visited_other, parent, directions, is_forward):
        """
        DFS单步扩展
        
        参数:
            stack: 当前方向的栈
            visited_self: 当前方向的访问集合
            visited_other: 相反方向的访问集合
            parent: 父节点映射
            directions: 方向向量
            is_forward: 是否为前向搜索
        """
        if not stack:
            return None

        current = stack[-1]  # 查看栈顶元素

        # 可视化当前节点
        if current != self.start and current != self.end:
            self.update_cell(*current, 'visited')

        # 尝试找到未访问的邻居
        for dir_ in directions:
            nx, ny = dir_(*current)
            neighbor = (nx, ny)

            # 检查边界和墙壁
            if (0 <= nx < self.width and 0 <= ny < self.height and 
                self.maze[ny][nx] == 0 and neighbor not in visited_self):

                # 标记为已访问
                visited_self.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)

                if neighbor != self.start and neighbor != self.end:
                    self.update_cell(nx, ny, 'current')

                # 检查是否与另一方向相遇
                if neighbor in visited_other:
                    return neighbor

                break
        else:
            # 如果没有未访问的邻居，回溯
            stack.pop()
            if current != self.start and current != self.end:
                self.update_cell(*current, 'path')

        return None

    def find_path_bidirectional_bfs(self):
        """双向BFS寻路"""
        # 初始化两个方向的队列和访问记录
        # 前向搜索(从起点开始)
        queue_forward = deque([self.start])
        visited_forward = {self.start}
        parent_forward = {self.start: None}  # 记录前驱节点

        # 后向搜索(从终点开始)
        queue_backward = deque([self.end])
        visited_backward = {self.end}
        parent_backward = {self.end: None}  # 记录后继节点

        # 相遇点
        meeting_point = None

        # 开始双向搜索
        while queue_forward and queue_backward and not meeting_point:
            # 交替扩展,每次扩展一层
            meeting_point = self._bfs_layer(queue_forward, visited_forward, visited_backward, 
                                        parent_forward, self.DIRECTIONS, is_forward=True)

            if not meeting_point:
                meeting_point = self._bfs_layer(queue_backward, visited_backward, visited_forward,
                                            parent_backward, self.DIRECTIONS, is_forward=False)

        # 构建完整路径
        if meeting_point:
            return self._construct_bidirectional_path(meeting_point, parent_forward, parent_backward)

        return None

    def _bfs_layer(self, queue, visited_self, visited_other, parent, directions, is_forward):
        """
        扩展一层BFS

        参数:
            queue: 当前方向的队列
            visited_self: 当前方向的访问集合
            visited_other: 相反方向的访问集合
            parent: 父节点映射
            directions: 方向向量
            is_forward: 是否为前向搜索
        """
        # 记录当前层的节点数
        layer_size = len(queue)

        for _ in range(layer_size):
            current = queue.popleft()

            if current != self.start and current != self.end:
                self.update_cell(*current, 'current')

            # 探索四个方向
            for dir_ in directions:
                nx, ny = dir_(*current)
                neighbor = (nx, ny)

                # 检查边界和墙壁
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    self.maze[ny][nx] == 0 and neighbor not in visited_self):

                    # 标记为已访问
                    visited_self.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

                    if neighbor != self.start and neighbor != self.end:
                        self.update_cell(nx, ny, 'frontier')

                    # 检查是否与另一方向相遇
                    if neighbor in visited_other:
                        return neighbor

            if current != self.start and current != self.end:
                self.update_cell(*current, 'visited')

        return None

    def _construct_bidirectional_path(self, meeting_point, parent_forward, parent_backward):
        """
        构建双向搜索的完整路径
        """
        # 从起点到相遇点的路径(正向)
        path_forward = []
        current = meeting_point
        while current is not None:
            path_forward.append(current)
            current = parent_forward.get(current)
        path_forward.reverse()  # 反转得到从起点到相遇点
        
        # 从相遇点到终点的路径(反向,不包括相遇点)
        path_backward = []
        current = parent_backward.get(meeting_point)
        while current is not None:
            path_backward.append(current)
            current = parent_backward.get(current)
        
        # 合并路径
        full_path = path_forward + path_backward
        
        # 验证路径(可选)
        # print(f"双向BFS找到路径长度: {len(full_path)}")
        
        return full_path
