import tkinter as tk
from tkinter import ttk
from maze_visualizer import MazeVisualizer



def main():
    """主函数"""
    root = tk.Tk()
    app = MazeVisualizer(root)

    # 设置窗口图标和主题
    try:
        root.iconbitmap('maze.ico')
    except:
        pass

    # 使用ttk主题
    style = ttk.Style()
    style.theme_use('vista')

    # 自定义样式
    style.configure('.', font=('Segoe UI', 10))

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()