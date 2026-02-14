import random


class MazeGenerator:
    def __init__(self, maze, width, height, update_cell):
        self.maze = maze
        self.width = width
        self.height = height
        self.update_cell = update_cell

    def generate_dfs(self):
        """深度优先算法生成迷宫"""
        x_size, y_size = self.width, self.height

        # 生成所有墙壁
        for i in range(2, x_size - 1, 2):
            for j in range(1, y_size - 1):
                self.maze[j][i] = 1
                self.update_cell(i, j, 'wall')

        for i in range(2, y_size - 1, 2):
            for j in range(1, x_size - 1):
                self.maze[i][j] = 1
                self.update_cell(j, i, 'wall')

        start = (random.randrange(1, x_size - 1, 2), random.randrange(1, y_size - 1, 2))

        stack = [start]
        visited = {start}

        direction = [
            lambda x, y: (x - 2, y),
            lambda x, y: (x, y - 2),
            lambda x, y: (x + 2, y),
            lambda x, y: (x, y + 2)
        ]

        while stack:
            cur_point = stack[-1]
            x1, y1 = cur_point
            self.update_cell(*cur_point, 'visited')

            random.shuffle(direction)
            for dir_ in direction:
                next_point = dir_(x1, y1)
                x2, y2 = next_point

                if 0 < x2 < x_size - 1 and 0 < y2 < y_size - 1 and next_point not in visited:
                    # 打通墙壁
                    wall_x = (x1 + x2) // 2
                    wall_y = (y1 + y2) // 2
                    self.maze[wall_y][wall_x] = 0

                    # 可视化
                    self.update_cell(wall_x, wall_y, 'path')
                    self.update_cell(x2, y2, 'current')

                    stack.append(next_point)
                    visited.add(next_point)
                    break
            else:
                stack.pop()
                self.update_cell(*cur_point, 'path')

    def generate_prim(self):
        """Prim算法生成迷宫"""
        x_size, y_size = self.width, self.height

        # 生成所有墙壁
        for i in range(2, x_size - 1, 2):
            for j in range(1, y_size - 1):
                self.maze[j][i] = 1
                self.update_cell(i, j, 'wall')

        for i in range(2, y_size - 1, 2):
            for j in range(1, x_size - 1):
                self.maze[i][j] = 1
                self.update_cell(j, i, 'wall')

        start = (random.randrange(1, x_size - 1, 2), random.randrange(1, y_size - 1, 2))

        sequence = []
        visited = {start}

        direction = [
            lambda x, y: (x - 1, y),
            lambda x, y: (x, y - 1),
            lambda x, y: (x + 1, y),
            lambda x, y: (x, y + 1)
        ]

        # 将起点周围的墙加入候选序列，并记录打通方向
        for dir_ in direction:
            neighbor = dir_(*start)
            x, y = neighbor
            if 0 < x < x_size - 1 and 0 < y < y_size - 1:
                sequence.append((neighbor, dir_))
                self.update_cell(*neighbor, 'frontier')

        while sequence:
            ind = random.randrange(len(sequence))
            wall, dir_ = sequence[ind]
            x, y = wall
            sequence[ind] = sequence[-1]
            sequence.pop()
            self.update_cell(x, y, 'current')
            connect_point = dir_(x, y)
            if connect_point not in visited:
                self.maze[y][x] = 0
                visited.add(connect_point)
                self.update_cell(x, y, 'path')
                for dir_ in direction:
                    neighbor = dir_(*connect_point)
                    x, y = neighbor
                    if 0 < x < x_size - 1 and 0 < y < y_size - 1 and dir_(*neighbor) not in visited:
                        sequence.append((neighbor, dir_))
                        self.update_cell(*neighbor, 'frontier')
            else:
                self.update_cell(x, y, 'wall')

    def generate_recursive(self):
        """递归分割算法生成迷宫"""

        def generate_partition(x1, x2, y1, y2):
            if x2 - x1 < 4 or y2 - y1 < 4:
                return

            # 随机选择分割位置
            partition_x = random.randrange(x1 + 2, x2, 2)
            partition_y = random.randrange(y1 + 2, y2, 2)

            # 生成十字墙壁
            for i in range(y1 + 1, y2):
                self.maze[i][partition_x] = 1
                self.update_cell(partition_x, i, 'wall')

            for j in range(x1 + 1, x2):
                self.maze[partition_y][j] = 1
                self.update_cell(j, partition_y, 'wall')

            # 随机打通三面墙
            walls = [
                (random.randrange(x1 + 1, partition_x, 2), partition_y),
                (partition_x, random.randrange(y1 + 1, partition_y, 2)),
                (random.randrange(partition_x + 1, x2, 2), partition_y),
                (partition_x, random.randrange(partition_y + 1, y2, 2))
            ]

            for wall in random.sample(walls, 3):
                x, y = wall
                self.maze[y][x] = 0
                self.update_cell(x, y, 'current')
                self.update_cell(x, y, 'path')

            # 递归处理子空间
            generate_partition(x1, partition_x, y1, partition_y)
            generate_partition(partition_x, x2, y1, partition_y)
            generate_partition(x1, partition_x, partition_y, y2)
            generate_partition(partition_x, x2, partition_y, y2)

        generate_partition(0, self.width - 1, 0, self.height - 1)
