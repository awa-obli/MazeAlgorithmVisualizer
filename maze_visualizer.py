"""
迷宫算法可视化工具
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import webbrowser
from maze_generator import MazeGenerator
from path_finder import PathFinder
from maze_codec import encode_maze_to_base64, decode_base64_to_maze
from texts import ALGORITHM_INFO, ABOUT_INFO


class MazeVisualizer:
    "迷宫算法可视化"
    def __init__(self, root):
        self.root = root
        self.root.title("迷宫算法可视化工具")
        self.root.geometry("1200x800")

        # 迷宫参数
        self.maze = []
        self.width = 31
        self.height = 31
        self.base_cell_size = 25  # 基础单元格大小
        self.start = (1, 1)
        self.end = (self.width - 2, self.height - 2)
        self.cell_states = {}  # 记录每个单元格的状态

        # 缩放参数
        self.zoom_level = 1.0  # 当前缩放级别
        self.min_zoom = 0.3  # 最小缩放
        self.max_zoom = 2.0  # 最大缩放
        self.zoom_step = 0.1  # 缩放步长

        # 算法状态
        self.is_generating = False
        self.is_finding = False
        self.is_paused = False
        self.is_step_mode = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # 初始为非暂停状态
        self.animation_speed = 100  # ms

        # 颜色配置
        self.colors = {
            'wall': '#2c3e50',
            'path': '#ecf0f1',
            'start': '#2ecc71',
            'end': '#e74c3c',
            'visited': '#3498db',
            'current': '#00ced1',
            'solution': '#9b59b6',
            'frontier': '#e67e22'
        }

        # 设置样式
        self.setup_ui()
        self.setup_bindings()

        # 初始化迷宫
        self.maze = self.init_maze(self.width, self.height)
        self.draw_maze()

    def setup_ui(self):
        """初始化界面"""
        # 主框架布局
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ===== 左侧带滚动条的控制面板 =====
        control_container = ttk.Frame(main_frame)
        control_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 创建画布和滚动条
        self.control_canvas = tk.Canvas(control_container, width=280, highlightthickness=0)
        control_scrollbar = ttk.Scrollbar(control_container, orient=tk.VERTICAL, command=self.control_canvas.yview)

        # 关联滚动条
        self.control_canvas.configure(yscrollcommand=control_scrollbar.set)

        # 布局画布和滚动条
        self.control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        control_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建内容框架（所有控件放在这里）
        control_frame = ttk.Frame(self.control_canvas, padding=5)
        self.control_window = self.control_canvas.create_window((0, 0), window=control_frame, anchor=tk.NW)

        # 滚动功能配置
        def configure_control_scroll(event):
            """内容框架大小变化时更新滚动区域"""
            bbox = self.control_canvas.bbox("all")
            if bbox:
                self.control_canvas.configure(scrollregion=bbox)
            # 设置内容框架宽度与画布宽度一致
            canvas_width = self.control_canvas.winfo_width()
            if canvas_width > 0:
                self.control_canvas.itemconfig(self.control_window, width=canvas_width)

        def configure_control_canvas(event):
            """画布大小变化时更新内容框架宽度"""
            if hasattr(self, 'control_window'):
                self.control_canvas.itemconfig(self.control_window, width=event.width)

        # 绑定事件
        control_frame.bind("<Configure>", configure_control_scroll)
        self.control_canvas.bind("<Configure>", configure_control_canvas)

        # === 鼠标滚轮滚动 ===
        def on_control_mousewheel(event):
            """控制面板鼠标滚轮滚动"""
            # 检查鼠标是否在控制面板区域内
            x, y = self.control_canvas.winfo_pointerxy()
            widget = self.control_canvas.winfo_containing(x, y)
            if widget and str(widget).startswith(str(self.control_canvas)):
                self.control_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # 绑定滚轮事件
        self.control_canvas.bind("<MouseWheel>", on_control_mousewheel)
        self.control_canvas.bind("<Enter>",
                                 lambda e: self.control_canvas.bind_all("<MouseWheel>", on_control_mousewheel))
        self.control_canvas.bind("<Leave>", lambda e: self.control_canvas.unbind_all("<MouseWheel>"))

        # 右侧画布
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建迷宫画布
        self.canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)

        # 添加滚动条
        scroll_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # ===== 以下所有控件都放在 control_frame 中 =====

        # 迷宫尺寸设置
        size_frame = ttk.LabelFrame(control_frame, text="迷宫尺寸", padding=5)
        size_frame.pack(fill=tk.X, pady=(0, 10))

        # 宽度设置
        width_frame = ttk.Frame(size_frame)
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text="宽度 (奇数):").pack(side=tk.LEFT, padx=(0, 5))
        self.width_var = tk.StringVar(value="31")
        width_entry = ttk.Entry(width_frame, textvariable=self.width_var, width=8)
        width_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 高度设置
        height_frame = ttk.Frame(size_frame)
        height_frame.pack(fill=tk.X, pady=2)
        ttk.Label(height_frame, text="高度 (奇数):").pack(side=tk.LEFT, padx=(0, 5))
        self.height_var = tk.StringVar(value="31")
        height_entry = ttk.Entry(height_frame, textvariable=self.height_var, width=8)
        height_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 生成算法选择
        algo_frame = ttk.LabelFrame(control_frame, text="生成算法", padding=5)
        algo_frame.pack(fill=tk.X, pady=(0, 10))

        self.gen_algo_var = tk.StringVar(value="DFS")
        algorithms = [
            ("深度优先 (DFS)", "DFS"),
            ("Prim算法", "Prim"),
            ("Kruskal算法", "Kruskal"),
            ("递归分割", "Recursive")
        ]

        for text, value in algorithms:
            ttk.Radiobutton(algo_frame, text=text, variable=self.gen_algo_var, value=value).pack(anchor=tk.W, pady=2)

        # 生成按钮
        ttk.Button(control_frame, text="生成迷宫", command=self.generate_maze).pack(fill=tk.X, pady=(0, 10))

        # 寻路算法选择
        find_frame = ttk.LabelFrame(control_frame, text="寻路算法", padding=5)
        find_frame.pack(fill=tk.X, pady=(0, 10))

        self.find_algo_var = tk.StringVar(value="DFS")
        find_algorithms = [
            ("深度优先 (DFS)", "DFS"),
            ("广度优先 (BFS)", "BFS"),
            ("Dijkstra算法", "Dijkstra"),
            ("贪心最佳优先 (GBFS)", "GBFS"),
            ("A*算法", "AStar"),
            ("双向深度优先 (D-DFS)", "D-DFS"),
            ("双向广度优先 (D-BFS)", "D-BFS")
        ]

        for text, value in find_algorithms:
            ttk.Radiobutton(find_frame, text=text, variable=self.find_algo_var, value=value).pack(anchor=tk.W, pady=2)

        # 寻路按钮
        ttk.Button(control_frame, text="开始寻路", command=self.find_path).pack(fill=tk.X, pady=(0, 10))

        # 动画速度控制
        speed_frame = ttk.LabelFrame(control_frame, text="动画速度", padding=5)
        speed_frame.pack(fill=tk.X, pady=(0, 10))

        self.speed_var = tk.IntVar(value=100)
        ttk.Scale(speed_frame, from_=0, to=200, variable=self.speed_var, orient=tk.HORIZONTAL,
                  command=self.update_speed).pack(fill=tk.X)

        # 执行控制按钮
        button_frame1 = ttk.Frame(control_frame)
        button_frame1.pack(fill=tk.X, pady=(0, 5))

        # 暂停/继续按钮
        self.pause_btn = ttk.Button(button_frame1, text="⏸️ 暂停", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.pause_btn.state(['disabled'])  # 初始禁用

        # 单步执行按钮
        step_frame = ttk.Frame(button_frame1, width=30, height=30)
        step_frame.pack_propagate(False)  # 禁止子控件撑开 frame
        step_frame.pack(side=tk.LEFT, padx=(5, 0))

        self.step_btn = ttk.Button(step_frame, text="⏯️", command=self.step_execute)
        self.step_btn.pack(fill=tk.BOTH, expand=True)
        self.step_btn.state(['disabled'])  # 初始禁用

        # 操作按钮
        button_frame2 = ttk.Frame(control_frame)
        button_frame2.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame2, text="清空路径", command=self.clear_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(button_frame2, text="重置迷宫", command=self.reset_maze).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        # 状态信息
        info_frame = ttk.LabelFrame(control_frame, text="状态信息", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(info_frame, text="就绪", foreground="green")
        self.status_label.pack(anchor=tk.W, pady=2)

        self.steps_label = ttk.Label(info_frame, text="步数: 0")
        self.steps_label.pack(anchor=tk.W, pady=2)

        self.time_label = ttk.Label(info_frame, text="耗时: 0.0s")
        self.time_label.pack(anchor=tk.W, pady=2)

        # 编码/解码
        codec_frame = ttk.LabelFrame(control_frame, text="迷宫编码", padding=5)
        codec_frame.pack(fill=tk.X, pady=(0, 10))

        self.code_var = tk.StringVar()
        ttk.Entry(codec_frame, textvariable=self.code_var, width=20).pack(fill=tk.X, pady=(0, 5))

        button_container = ttk.Frame(codec_frame)
        button_container.pack(fill=tk.X)

        ttk.Button(button_container, text="编码迷宫", command=self.encode_maze).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(button_container, text="解码迷宫", command=self.decode_maze).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        # 颜色图例
        legend_frame = ttk.LabelFrame(control_frame, text="颜色图例", padding=5)
        legend_frame.pack(fill=tk.X, pady=(0, 10))

        colors_info = [
            ("起点", self.colors['start']),
            ("终点", self.colors['end']),
            ("墙壁", self.colors['wall']),
            ("路径", self.colors['path']),
            ("已访问", self.colors['visited']),
            ("当前", self.colors['current']),
            ("解路径", self.colors['solution']),
            ("边界", self.colors['frontier'])
        ]

        # 使用网格布局
        for i, (text, color) in enumerate(colors_info):
            row = i // 2
            col = i % 2

            frame = ttk.Frame(legend_frame)
            frame.grid(row=row, column=col, sticky="w", padx=5, pady=1)

            color_box = tk.Canvas(frame, width=15, height=15, bg=color, highlightthickness=0)
            color_box.pack(side=tk.LEFT, padx=(0, 3))
            ttk.Label(frame, text=text, font=('Segoe UI', 9)).pack(side=tk.LEFT)

        # 关于链接
        about_frame = ttk.Frame(control_frame)
        about_frame.pack(fill=tk.X, pady=(10, 10))

        about_label = tk.Label(
            about_frame,
            text="关于",
            font=('Segoe UI', 9),
            fg='#0066cc',
            cursor='hand2',
        )
        about_label.pack(anchor=tk.CENTER)
        about_label.bind('<Button-1>', self.show_about)

        # 缩放控制
        zoom_frame = tk.Frame(self.canvas, bg='white', bd=0)
        zoom_frame.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-10, y=10)

        # 添加缩放比例标签
        self.zoom_label = tk.Label(
            zoom_frame,
            text="100%",
            font=('Arial', 10),
            bg='white'
        )
        self.zoom_label.pack(side=tk.TOP, pady=(0, 5))

        # 创建按钮容器
        zoom_btn_container = tk.Frame(zoom_frame, bg='white')
        zoom_btn_container.pack(side=tk.TOP, pady=(0, 2))

        # +号放大按钮
        self.zoom_in_btn = tk.Button(
            zoom_btn_container,
            text="+",
            font=('Arial', 14, 'bold'),
            width=2,
            height=1,
            command=self.zoom_in,
            bg='#f0f0f0',
            relief='flat',
            bd=2,
            padx=0,
            pady=0,
            cursor='hand2'
        )
        self.zoom_in_btn.pack(side=tk.LEFT, padx=(0, 2))

        # -号缩小按钮
        self.zoom_out_btn = tk.Button(
            zoom_btn_container,
            text="-",
            font=('Arial', 14, 'bold'),
            width=2,
            height=1,
            command=self.zoom_out,
            bg='#f0f0f0',
            relief='flat',
            bd=2,
            padx=0,
            pady=0,
            cursor='hand2'
        )
        self.zoom_out_btn.pack(side=tk.LEFT)

        # 重置按钮
        self.zoom_reset_btn = tk.Button(
            zoom_frame,
            text="↺",
            font=('Arial', 12, 'bold'),
            width=5,
            height=1,
            command=self.reset_zoom,
            bg='#f0f0f0',
            relief='flat',
            bd=2,
            cursor='hand2'
        )
        self.zoom_reset_btn.pack(side=tk.TOP)

        # 添加问号按钮
        help_btn = tk.Button(
            canvas_frame,
            text="?",
            font=("Arial", 12, "bold"),
            width=2,
            height=1,
            command=self.show_algorithm_info,
            bg="#f0f0f0",
            relief='flat',
            bd=2,
            cursor='hand2'
        )
        help_btn.place(x=10, y=10)

    def setup_bindings(self):
        """设置事件绑定"""
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        # 鼠标滚轮缩放
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        # Ctrl+滚轮缩放
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        # 鼠标中键拖拽画布
        self.canvas.bind("<Button-2>", self.start_pan)  # 中键按下
        self.canvas.bind("<B2-Motion>", self.pan)  # 中键拖拽
        self.canvas.bind("<ButtonRelease-2>", self.stop_pan)  # 中键释放

    def init_maze(self, width, height):
        """初始化迷宫"""
        maze = []
        for i in range(height):
            maze.append([])
            for j in range(width):
                if i == 0 or i == height - 1:
                    maze[i].append(1)
                elif j == 0 or j == width - 1:
                    maze[i].append(1)
                else:
                    maze[i].append(0)
        return maze

    def draw_maze(self):
        """绘制迷宫"""
        self.canvas.delete("all")

        if not self.maze:
            return

        width = len(self.maze[0])
        height = len(self.maze)

        # 计算缩放后的单元格大小
        cell_size = int(self.base_cell_size * self.zoom_level)

        # 计算总尺寸
        total_width = width * cell_size
        total_height = height * cell_size

        # 居中计算
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 计算居中的偏移量
        if total_width < canvas_width:
            offset_x = (canvas_width - total_width) // 2
        else:
            offset_x = 0

        if total_height < canvas_height:
            offset_y = (canvas_height - total_height) // 2
        else:
            offset_y = 0

        # 绘制每个单元格
        for y in range(height):
            for x in range(width):
                x1 = offset_x + x * cell_size
                y1 = offset_y + y * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                # 确定单元格颜色（优先使用保存的状态）
                cell_type = self.cell_states.get((x, y))

                if cell_type:
                    color = self.colors[cell_type]
                elif self.maze[y][x] == 1:  # 墙壁
                    color = self.colors['wall']
                elif (x, y) == self.start:
                    color = self.colors['start']
                elif (x, y) == self.end:
                    color = self.colors['end']
                else:
                    color = self.colors['path']

                # 绘制单元格
                cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='white', width=1)

                # 存储单元格信息
                self.canvas.itemconfig(cell_id, tags=(f"cell_{x}_{y}", f"x_{x}_y_{y}"))

        # 更新滚动区域
        self.canvas.configure(scrollregion=(0, 0, max(total_width, canvas_width), max(total_height, canvas_height)))

    def update_cell(self, x, y, cell_type):
        """更新单元格显示"""
        if threading.current_thread() is threading.main_thread():
            # 主线程（手动编辑）：直接更新
            self._do_update_cell(x, y, cell_type)
        else:
            # 子线程（算法动画）：调度到主线程更新（确保线程安全），并延迟一段时间
            self.root.after_idle(self._do_update_cell, x, y, cell_type)
            self.check_pause()
            if self.is_step_mode:  # 单步模式下每步结束后重新暂停，不设置延迟
                self.is_step_mode = False
                self.pause_event.clear()
            else:
                time.sleep(self.animation_speed / 1000)

    def _do_update_cell(self, x, y, cell_type):
        """执行GUI更新"""
        # 保存状态
        self.cell_states[(x, y)] = cell_type

        cell_id = self.canvas.find_withtag(f"cell_{x}_{y}")
        if cell_id:
            self.canvas.itemconfig(cell_id[0], fill=self.colors[cell_type])

    def generate_maze(self):
        """生成迷宫"""
        if self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            return

        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())

            if width % 2 == 0 or height % 2 == 0:
                messagebox.showerror("错误", "迷宫尺寸必须为奇数")
                return
            if width < 5 or height < 5:
                messagebox.showerror("错误", "迷宫尺寸至少为5")
                return
            if width > 101 or height > 101:
                messagebox.showerror("错误", "迷宫尺寸最大为101")
                return

            self.width = width
            self.height = height

            self.reset_maze()

            # 在新线程中生成迷宫
            algo = self.gen_algo_var.get()
            thread = threading.Thread(target=self._generate_maze_thread, args=(algo,))
            thread.daemon = True
            thread.start()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def _generate_maze_thread(self, algo):
        """生成迷宫的线程函数"""
        self.is_generating = True
        self.is_paused = False
        self.pause_event.set()
        self.root.after(0, lambda: self.enable_pause_button(True))
        self.root.after(0, lambda: self.status_label.config(text="正在生成迷宫...", foreground="orange"))

        start_time = time.time()

        generator = MazeGenerator(self.maze, self.width, self.height, self.update_cell)
        if algo == "DFS":
            generator.generate_dfs()
        elif algo == "Prim":
            generator.generate_prim()
        elif algo == "Kruskal":
            generator.generate_kruskal()
        elif algo == "Recursive":
            generator.generate_recursive()

        # 设置起点和终点
        self.update_cell(*self.start, 'start')
        self.update_cell(*self.end, 'end')

        elapsed = time.time() - start_time
        self.is_generating = False
        self.root.after(0, lambda: self.status_label.config(text="迷宫生成完成", foreground="green"))
        self.root.after(0, lambda: self.time_label.config(text=f"耗时: {elapsed:.2f}s"))
        self.root.after(0, lambda: self.enable_pause_button(False))

    def find_path(self):
        """寻路"""
        if self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            return

        self.clear_path()

        # 在新线程中寻路
        algo = self.find_algo_var.get()
        thread = threading.Thread(target=self._find_path_thread, args=(algo,))
        thread.daemon = True
        thread.start()

    def _find_path_thread(self, algo):
        """寻路的线程函数"""
        self.is_finding = True
        self.is_paused = False
        self.pause_event.set()
        self.root.after(0, lambda: self.enable_pause_button(True))
        self.root.after(0, lambda: self.status_label.config(text="正在寻路...", foreground="orange"))

        start_time = time.time()

        finder = PathFinder(self.maze, self.width, self.height, self.start, self.end, self.update_cell)
        path = None
        if algo == "DFS":
            path = finder.find_path_dfs()
        elif algo == "BFS":
            path = finder.find_path_bfs()
        elif algo == "Dijkstra":
            path = finder.find_path_dijkstra()
        elif algo == "GBFS":
            path = finder.find_path_gbfs()
        elif algo == "AStar":
            path = finder.find_path_astar()
        elif algo == "D-DFS":
            path = finder.find_path_bidirectional_dfs()
        elif algo == "D-BFS":
            path = finder.find_path_bidirectional_bfs()

        elapsed = time.time() - start_time

        if path:
            # 显示解路径
            for x, y in path:
                if (x, y) != self.start and (x, y) != self.end:
                    self.update_cell(x, y, 'solution')

            self.root.after(0, lambda: self.status_label.config(text=f"寻路成功 ({len(path)}步)", foreground="green"))
            self.root.after(0, lambda: self.steps_label.config(text=f"步数: {len(path)}"))
        else:
            self.root.after(0, lambda: self.status_label.config(text="寻路失败", foreground="red"))

        self.is_finding = False
        self.root.after(0, lambda: self.time_label.config(text=f"耗时: {elapsed:.2f}s"))
        self.root.after(0, lambda: self.enable_pause_button(False))

    def clear_path(self):
        """清除路径标记"""
        if not self.maze or self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            else:
                messagebox.showerror("警告", "请先生成迷宫")
            return

        x_size, y_size = self.width, self.height

        # 清除路径相关的状态
        for x in range(x_size):
            for y in range(y_size):
                if (x, y) in self.cell_states:
                    if self.cell_states[(x, y)] in {'visited', 'current', 'solution', 'frontier'}:
                        del self.cell_states[(x, y)]

        # 重绘迷宫
        self.draw_maze()
        self.status_label.config(text="已清除路径", foreground="green")
        self.steps_label.config(text="步数: 0")

    def reset_maze(self):
        """重置迷宫"""
        if not self.maze or self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            return

        self.start = (1, 1)
        self.end = (self.width - 2, self.height - 2)
        self.maze = []
        self.maze = self.init_maze(self.width, self.height)
        self.cell_states.clear()
        self.draw_maze()

        self.status_label.config(text="就绪", foreground="green")
        self.steps_label.config(text="步数: 0")
        self.time_label.config(text="耗时: 0.0s")

    def encode_maze(self):
        """编码迷宫"""
        if not self.maze or self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            else:
                messagebox.showerror("警告", "请先生成迷宫")
            return

        encoded = encode_maze_to_base64(self.maze)
        self.code_var.set(encoded)

        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(encoded)
        self.status_label.config(text="已复制编码到剪贴板", foreground="green")

    def decode_maze(self):
        """解码迷宫"""
        if self.is_generating or self.is_finding:
            if self.is_generating:
                messagebox.showerror("警告", "正在生成迷宫中...")
            elif self.is_finding:
                messagebox.showerror("警告", "正在寻找路径中...")
            return

        encoded = self.code_var.get().strip()
        if not encoded:
            messagebox.showwarning("警告", "请输入迷宫编码")
            return

        try:
            self.reset_maze()
            self.maze, (self.width, self.height) = decode_base64_to_maze(encoded)
            
            # 设置起点和终点
            self.start = (1, 1)
            self.end = (self.width - 2, self.height - 2)
            
            self.cell_states.clear()
            self.draw_maze()
            self.status_label.config(text="迷宫解码成功", foreground="green")
        except Exception as e:
            messagebox.showerror("解码错误", f"解码失败:\n{str(e)}")

    def update_speed(self, value):
        """更新动画速度"""
        self.animation_speed = 201 - self.speed_var.get()

    def on_canvas_resize(self, event):
        """画布大小改变时重绘迷宫"""
        if self.maze:
            self.draw_maze()

    def _get_cell_at(self, event):
        """根据鼠标事件返回单元格坐标，越界返回 None"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        width = len(self.maze[0])
        height = len(self.maze)
        cell_size = int(self.base_cell_size * self.zoom_level)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        total_width = width * cell_size
        total_height = height * cell_size

        offset_x = (canvas_width - total_width) // 2 if total_width < canvas_width else 0
        offset_y = (canvas_height - total_height) // 2 if total_height < canvas_height else 0

        cell_x = int((x - offset_x) // cell_size)
        cell_y = int((y - offset_y) // cell_size)

        if 0 <= cell_x < width and 0 <= cell_y < height:
            return cell_x, cell_y
        return None

    def on_canvas_click(self, event):
        """画布点击事件"""
        if not self.maze or self.is_generating or self.is_finding:
            return
        cell = self._get_cell_at(event)
        if cell and cell != self.start and cell != self.end:
            cell_x, cell_y = cell
            if self.maze[cell_y][cell_x] == 0:
                self.maze[cell_y][cell_x] = 1
                self.update_cell(cell_x, cell_y, 'wall')
            else:
                self.maze[cell_y][cell_x] = 0
                self.update_cell(cell_x, cell_y, 'path')

    def on_canvas_right_click(self, event):
        """画布右键点击事件"""
        if not self.maze or self.is_generating or self.is_finding:
            return
        cell = self._get_cell_at(event)
        if cell is None:
            return
        cell_x, cell_y = cell
        if self.maze[cell_y][cell_x] == 0 and cell != self.start and cell != self.end:
            choice = simpledialog.askstring("设置点", f"在({cell_x}, {cell_y})设置:\n1. 起点\n2. 终点", parent=self.root)
            if choice == '1':
                self.update_cell(*self.start, 'path')
                self.start = (cell_x, cell_y)
                self.update_cell(cell_x, cell_y, 'start')
            elif choice == '2':
                self.update_cell(*self.end, 'path')
                self.end = (cell_x, cell_y)
                self.update_cell(cell_x, cell_y, 'end')

    def on_canvas_drag(self, event):
        """画布拖拽事件"""
        self.on_canvas_click(event)

    def on_mousewheel(self, event):
        """鼠标滚轮事件 - 滚动画布"""
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def on_ctrl_mousewheel(self, event):
        """Ctrl+鼠标滚轮 - 缩放"""
        if event.delta > 0:
            self.zoom_in(event)
        else:
            self.zoom_out(event)

    def start_pan(self, event):
        """开始拖动画布 - 记录起始位置"""
        self.canvas.scan_mark(event.x, event.y)
        # 改变鼠标样式，提示正在拖拽
        self.canvas.config(cursor="fleur")

    def pan(self, event):
        """拖动画布"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def stop_pan(self, event):
        """停止拖动画布 - 恢复鼠标样式"""
        self.canvas.config(cursor="")

    def zoom_in(self, event=None):
        """放大"""
        if not self.maze:
            return

        if self.zoom_level < self.max_zoom:
            self._do_zoom(self.zoom_step, event)

    def zoom_out(self, event=None):
        """缩小"""
        if not self.maze:
            return

        if self.zoom_level > self.min_zoom:
            self._do_zoom(-self.zoom_step, event)

    def _do_zoom(self, zoom_change, event=None):
        """缩放处理"""
        # 获取当前总尺寸
        old_total_width = len(self.maze[0]) * int(self.base_cell_size * self.zoom_level)
        old_total_height = len(self.maze) * int(self.base_cell_size * self.zoom_level)

        # 获取缩放中心点的比例
        if event:
            # 鼠标触发：将鼠标所在位置移至画面中心
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            ratio_x = x / old_total_width
            ratio_y = y / old_total_height
        else:
            # 按钮触发：向画面中央缩放
            canvas_center_x = self.canvas.winfo_width() // 2
            canvas_center_y = self.canvas.winfo_height() // 2
            x = self.canvas.canvasx(canvas_center_x)
            y = self.canvas.canvasy(canvas_center_y)
            ratio_x = x / old_total_width
            ratio_y = y / old_total_height

        # 执行缩放
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level + zoom_change))
        self.draw_maze()

        # 缩放后的总尺寸
        new_total_width = len(self.maze[0]) * int(self.base_cell_size * self.zoom_level)
        new_total_height = len(self.maze) * int(self.base_cell_size * self.zoom_level)

        # 用比例算新位置
        new_x = ratio_x * new_total_width
        new_y = ratio_y * new_total_height

        # 调整视图
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if new_total_width > canvas_width:
            ratio_x = new_x / new_total_width
            self.canvas.xview_moveto(max(0, min(1, ratio_x - 0.5 * canvas_width / new_total_width)))

        if new_total_height > canvas_height:
            ratio_y = new_y / new_total_height
            self.canvas.yview_moveto(max(0, min(1, ratio_y - 0.5 * canvas_height / new_total_height)))

        self.update_zoom_display()

    def reset_zoom(self):
        """重置缩放"""
        if not self.maze:
            return

        self.zoom_level = 1.0
        self.draw_maze()
        self.update_zoom_display()

        # 重置滚动位置
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def update_zoom_display(self):
        """更新缩放显示"""
        percentage = round(self.zoom_level * 100)
        self.zoom_label.config(text=f"{percentage}%")

    def show_algorithm_info(self):
        """显示迷宫生成算法说明"""
        info_window = tk.Toplevel(self.root)
        info_window.title("迷宫算法介绍")
        info_window.geometry("600x600")
        info_window.resizable(True, True)

        # 设置窗口图标
        try:
            info_window.iconbitmap('maze.ico')
        except:
            pass

        # 居中显示
        info_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - info_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - info_window.winfo_height()) // 2
        info_window.geometry(f"+{x}+{y}")

        # 创建带滚动条的框架
        main_frame = ttk.Frame(info_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建画布和滚动条
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 内容框架
        content_frame = ttk.Frame(canvas, padding=20)
        canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

        # 滚动功能
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=canvas.winfo_width())

        content_frame.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        # 鼠标滚轮滚动
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # === 填充内容 ===
        
        # 标题
        ttk.Label(
            content_frame,
            text=ALGORITHM_INFO["title"],
            font=('Segoe UI', 16, 'bold')
        ).pack()
        ttk.Label(
            content_frame,
            text=ALGORITHM_INFO["subtitle"],
            font=('Segoe UI', 10),
            foreground="gray"
        ).pack(pady=(0, 10))

        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # ========== 迷宫生成算法 ==========
        gen_frame = ttk.LabelFrame(content_frame, text=ALGORITHM_INFO["generation"]["title"], padding=15)
        gen_frame.pack(fill=tk.X, pady=10)

        # 生成算法列表
        gen_algorithms = [
            "dfs",
            "prim",
            "kruskal",
            "recursive"
        ]

        for algo_key in gen_algorithms:
            # 创建算法框架
            algo_frame = ttk.LabelFrame(
                gen_frame, 
                text=ALGORITHM_INFO["generation"][algo_key]["title"], 
                padding=12
            )
            algo_frame.pack(fill=tk.X, pady=5)

            # 创建算法说明标签
            algo_label = ttk.Label(
                algo_frame,
                text=ALGORITHM_INFO["generation"][algo_key]["content"].strip(),
                font=('Segoe UI', 10),
                wraplength=480,
                justify=tk.LEFT
            )
            algo_label.pack(anchor=tk.W, pady=5)

            # GitHub链接
            link_frame = ttk.Frame(algo_frame)
            link_frame.pack(fill=tk.X, pady=(5, 0))

            github_link = tk.Label(
                link_frame,
                text="📦 查看源码",
                font=('Segoe UI', 10, 'underline'),
                fg='#0066cc',
                cursor='hand2',
            )
            github_link.pack(side=tk.LEFT)

            github_urls = {
                'dfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/maze_generator.py#L11-L62',
                'prim': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/maze_generator.py#L64-L118',
                'kruskal': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/maze_generator.py#L120-L192',
                'recursive': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/maze_generator.py#L194-L234'
            }

            def make_link_handler(url):
                return lambda e: webbrowser.open(url)

            github_link.bind('<Button-1>', make_link_handler(github_urls[algo_key]))

        # ========== 迷宫寻路算法 ==========
        find_frame = ttk.LabelFrame(content_frame, text=ALGORITHM_INFO["pathfinding"]["title"], padding=15)
        find_frame.pack(fill=tk.X, pady=10)

        # 寻路算法列表
        find_algorithms = [
            "dfs",
            "bfs",
            "dijkstra",
            "gbfs",
            "astar",
            "d-dfs",
            "d-bfs"
        ]

        for algo_key in find_algorithms:
            # 创建算法框架
            algo_frame = ttk.LabelFrame(
                find_frame, 
                text=ALGORITHM_INFO["pathfinding"][algo_key]["title"], 
                padding=12
            )
            algo_frame.pack(fill=tk.X, pady=5)

            # 创建算法说明标签
            algo_label = ttk.Label(
                algo_frame,
                text=ALGORITHM_INFO["pathfinding"][algo_key]["content"].strip(),
                font=('Segoe UI', 10),
                wraplength=480,
                justify=tk.LEFT
            )
            algo_label.pack(anchor=tk.W, pady=5)

            link_frame = ttk.Frame(algo_frame)
            link_frame.pack(fill=tk.X, pady=(5, 0))

            github_link = tk.Label(
                link_frame,
                text="📦 查看源码",
                font=('Segoe UI', 10, 'underline'),
                fg='#0066cc',
                cursor='hand2',
            )
            github_link.pack(side=tk.LEFT)

            github_urls = {
                'dfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L21-L51',
                'bfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L53-L90',
                'dijkstra': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L92-L132',
                'gbfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L134-L178',
                'astar': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L180-L225',
                'd-dfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L227-L308',
                'd-bfs': 'https://github.com/awa-obli/MazeAlgorithmVisualizer/blob/main/path_finder.py#L310-L387'
            }

            def make_link_handler(url):
                return lambda e: webbrowser.open(url)

            github_link.bind('<Button-1>', make_link_handler(github_urls[algo_key]))

        # ========== 算法对比表格 ==========
        table_frame = ttk.LabelFrame(content_frame, text=ALGORITHM_INFO["comparison"]["title"], padding=15)
        table_frame.pack(fill=tk.X, pady=10)

        # 创建主框架
        main_table_frame = ttk.Frame(table_frame)
        main_table_frame.pack(fill=tk.X, pady=5)

        # ===== 迷宫生成算法对比 =====
        gen_table_title = ttk.Label(main_table_frame, text=ALGORITHM_INFO["comparison"]["generation"]["title"], 
                                    font=('Segoe UI', 11, 'bold'))
        gen_table_title.pack(anchor=tk.W, pady=(0, 5))

        # 生成算法表格框架
        gen_table = ttk.Frame(main_table_frame)
        gen_table.pack(fill=tk.X, pady=(0, 10))

        # 表头
        headers = ALGORITHM_INFO["comparison"]["generation"]["headers"]
        col_widths = [80, 120, 200, 120]  # 列宽保持不变

        for i, header in enumerate(headers):
            label = tk.Label(gen_table, text=header, font=('Segoe UI', 10, 'bold'),
                            bg='#2c3e50', fg='white', padx=8, pady=6, 
                            width=col_widths[i]//6, anchor=tk.W, relief='flat')
            label.grid(row=0, column=i, sticky='ew', padx=1, pady=1)

        # 生成算法数据行
        gen_data = ALGORITHM_INFO["comparison"]["generation"]["data"]
        for row_idx, algo_data in enumerate(gen_data, 1):
            # 交替背景色
            bg_color = '#ecf0f1' if row_idx % 2 == 1 else '#f8f9f9'
            
            row_data = [algo_data["algorithm"], algo_data["idea"], algo_data["features"]]
            for col_idx, data in enumerate(row_data):
                label = tk.Label(gen_table, text=data, font=('Segoe UI', 9),
                                bg=bg_color, padx=8, pady=6, width=col_widths[col_idx]//6,
                                anchor=tk.W, relief='flat', justify=tk.LEFT)
                label.grid(row=row_idx, column=col_idx, sticky='ew', padx=1, pady=1)

        # 添加分隔线
        ttk.Separator(main_table_frame, orient='horizontal').pack(fill=tk.X, pady=15)

        # ===== 迷宫寻路算法对比 =====
        find_table_title = ttk.Label(main_table_frame, text=ALGORITHM_INFO["comparison"]["pathfinding"]["title"], 
                                    font=('Segoe UI', 11, 'bold'))
        find_table_title.pack(anchor=tk.W, pady=(0, 5))

        # 寻路算法表格框架
        find_table = ttk.Frame(main_table_frame)
        find_table.pack(fill=tk.X, pady=(0, 5))

        # 表头
        find_headers = ALGORITHM_INFO["comparison"]["pathfinding"]["headers"]
        find_col_widths = [80, 120, 200, 100]  # 列宽保持不变

        for i, header in enumerate(find_headers):
            label = tk.Label(find_table, text=header, font=('Segoe UI', 10, 'bold'),
                            bg='#2c3e50', fg='white', padx=8, pady=6,
                            width=find_col_widths[i]//6, anchor=tk.W, relief='flat')
            label.grid(row=0, column=i, sticky='ew', padx=1, pady=1)

        # 寻路算法数据行
        find_data = ALGORITHM_INFO["comparison"]["pathfinding"]["data"]
        for row_idx, algo_data in enumerate(find_data, 1):
            # 交替背景色
            bg_color = '#ecf0f1' if row_idx % 2 == 1 else '#f8f9f9'

            row_data = [algo_data["algorithm"], algo_data["idea"], algo_data["features"]]
            for col_idx, data in enumerate(row_data):
                label = tk.Label(find_table, text=data, font=('Segoe UI', 9),
                                bg=bg_color, padx=8, pady=6, width=find_col_widths[col_idx]//6,
                                anchor=tk.W, relief='flat', justify=tk.LEFT)
                label.grid(row=row_idx, column=col_idx, sticky='ew', padx=1, pady=1)

        # ========== 关闭按钮 ==========
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=(20, 10))
        ttk.Button(
            btn_frame,
            text="关闭",
            command=info_window.destroy,
            width=15
        ).pack()

    def show_about(self, event):
        """显示关于对话框"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("500x500")

        # 设置窗口图标
        try:
            about_window.iconbitmap('maze.ico')
        except:
            pass

        # 居中显示
        about_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - about_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - about_window.winfo_height()) // 2
        about_window.geometry(f"+{x}+{y}")

        # 创建带滚动条的框架
        main_frame = ttk.Frame(about_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建画布和滚动条
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 内容框架
        content_frame = ttk.Frame(canvas, padding=20)
        canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

        # 滚动功能
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=canvas.winfo_width())

        content_frame.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        # 鼠标滚轮滚动
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # === 填充内容 ===

        # 标题
        ttk.Label(
            content_frame,
            text=ABOUT_INFO["title"],
            font=('Segoe UI', 16, 'bold')
        ).pack()
        ttk.Label(
            content_frame,
            text=ABOUT_INFO["subtitle"],
            font=('Segoe UI', 10),
            foreground="gray"
        ).pack(pady=(0, 10))

        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # 版本信息
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill=tk.X, pady=5)
        ttk.Label(info_frame, text="版本:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(info_frame, text=ABOUT_INFO["version"], font=('Segoe UI', 10)).pack(side=tk.LEFT)

        # 项目介绍
        intro_frame = ttk.LabelFrame(content_frame, text="📋 项目介绍", padding=15)
        intro_frame.pack(fill=tk.X, pady=10)
        intro_label = ttk.Label(
            intro_frame, 
            text=ABOUT_INFO["introduction"].strip(),
            font=('Segoe UI', 10),
            wraplength=400,
            justify=tk.LEFT
        )
        intro_label.pack(fill=tk.X)

        # 功能介绍
        features_frame = ttk.LabelFrame(content_frame, text="✨ 功能介绍", padding=10)
        features_frame.pack(fill=tk.X, pady=15)
        for feature in ABOUT_INFO["features"]:
            ttk.Label(features_frame, text=feature, font=('Segoe UI', 10)).pack(anchor=tk.W, pady=1)

        # 使用提示
        tips_frame = ttk.LabelFrame(content_frame, text="💡 操作说明", padding=12)
        tips_frame.pack(fill=tk.X, pady=10)
        for tip in ABOUT_INFO["tips"]:
            ttk.Label(tips_frame, text=tip, font=('Segoe UI', 10)).pack(anchor=tk.W, pady=1)

        # 版权信息
        copyright_frame = ttk.Frame(content_frame)
        copyright_frame.pack(pady=(15, 5))
        ttk.Label(
            copyright_frame,
            text=ABOUT_INFO["copyright"],
            font=('Segoe UI', 9),
            foreground="gray",
            justify=tk.CENTER
        ).pack()

        link_frame = ttk.Frame(copyright_frame)
        link_frame.pack()
        ttk.Label(link_frame, text="本软件为", font=('Segoe UI', 9), foreground="gray").pack(side=tk.LEFT)

        link_label = tk.Label(
            link_frame,
            text="开源项目",
            font=('Segoe UI', 9, 'underline'),
            fg='#0066cc',
            cursor='hand2',
        )
        link_label.pack(side=tk.LEFT)
        
        def open_link(event):
            webbrowser.open(ABOUT_INFO["github_url"])
        link_label.bind('<Button-1>', open_link)
        
        ttk.Label(
            link_frame,
            text="，遵循 MIT 许可证",
            font=('Segoe UI', 9),
            foreground="gray"
        ).pack(side=tk.LEFT)

        # 关闭按钮
        ttk.Button(
            content_frame,
            text="关闭",
            command=about_window.destroy,
            width=15
        ).pack(pady=(5, 0))

    def toggle_pause(self):
        """切换暂停/继续状态"""
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.step_btn.state(['disabled'])
            self.pause_btn.config(text="⏸️ 暂停")
            # 恢复原来的状态文本
            if self.is_generating:
                self.status_label.config(text="正在生成迷宫...", foreground="orange")
            elif self.is_finding:
                self.status_label.config(text="正在寻路...", foreground="orange")
        else:
            self.is_paused = True
            self.pause_event.clear()
            self.step_btn.state(['!disabled'])
            self.pause_btn.config(text="▶️ 继续")
            self.status_label.config(text="已暂停", foreground="orange")

    def check_pause(self):
        """检查是否暂停，若暂停则阻塞"""
        self.pause_event.wait()

    def enable_pause_button(self, enable=True):
        """启用/禁用暂停按钮"""
        if enable:
            self.pause_btn.state(['!disabled'])
        else:
            self.pause_btn.state(['disabled'])
            self.step_btn.state(['disabled'])
            # 如果处于暂停状态，自动恢复
            if self.is_paused:
                self.toggle_pause()

    def step_execute(self):
        """单步执行"""
        # 临时恢复执行，一步结束后会在update_cell中重新暂停
        self.is_step_mode = True
        self.pause_event.set()
