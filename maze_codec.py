import base64

def encode_maze_to_base64(maze):
    """
    将迷宫编码为Base64字符串
    
    参数:
        maze: 二维列表，0（地面），1（墙壁）
    
    返回:
        Base64编码字符串（包含尺寸信息）
    
    编码格式：width,height,base64_data
    """
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    
    # 将迷宫展平为一维比特数组
    bits = []
    for row in maze:
        for cell in row:
            bits.append(cell)
    
    # 转换为字节数组
    byte_array = bytearray()
    
    # 每8个比特打包成一个字节
    for i in range(0, len(bits), 8):
        byte_val = 0
        # 处理当前字节的8个比特
        for j in range(8):
            if i + j < len(bits):
                if bits[i + j] == 1:
                    byte_val |= (1 << (7 - j))  # 设置对应位
        byte_array.append(byte_val)
    
    # Base64编码
    base64_data = base64.b64encode(byte_array).decode('ascii')
    
    # 返回包含尺寸信息的字符串
    return f"{width},{height},{base64_data}"


def decode_base64_to_maze(encoded_str):
    """
    将Base64字符串解码为迷宫
    
    参数:
        encoded_str: 编码字符串，格式为 width,height,base64_data
    
    返回:
        (maze, (width, height)) 元组
    """
    # 解析尺寸信息
    parts = encoded_str.split(',', 2)
    
    width = int(parts[0])
    height = int(parts[1])
    base64_data = parts[2]
    
    # Base64解码
    byte_array = base64.b64decode(base64_data)
    
    # 将字节转换回比特
    total_bits = width * height
    bits = []
    
    for byte in byte_array:
        # 提取一个字节的8个比特
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    
    # 只取需要的比特数（去掉填充）
    bits = bits[:total_bits]
    
    # 重建迷宫二维数组
    maze = []
    for i in range(height):
        start_idx = i * width
        end_idx = start_idx + width
        row = bits[start_idx:end_idx]
        maze.append(row)
    
    return maze, (width, height)
