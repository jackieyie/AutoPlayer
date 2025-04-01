import pyautogui
import time
import atexit
import sys

def print_mouse_position_on_exit():
    """
    在脚本退出时获取并打印鼠标指针的最终坐标。
    """
    try:
        # 获取当前鼠标坐标
        x, y = pyautogui.position()
        print(f"\n-------------------------------------")
        print(f"脚本结束。鼠标最后位置: (x={x}, y={y})")
        print(f"-------------------------------------")
    except Exception as e:
        # pyautogui 在某些环境 (如无头服务器或权限不足) 可能失败
        print(f"\n无法获取鼠标位置: {e}", file=sys.stderr)

# 注册一个函数，使其在 Python 解释器正常终止时执行
# 这包括脚本自然结束、调用 sys.exit() 或发生未捕获的异常 (如 KeyboardInterrupt)
atexit.register(print_mouse_position_on_exit)

# --- 你的主脚本代码放在这里 ---
print("脚本开始运行...")
print("你可以移动鼠标。")
print("脚本将在 10 秒后自动结束，或者你可以按 Ctrl+C 提前结束。")
print("(无论如何结束，都会尝试打印最后的鼠标位置)")

try:
    # 这里放一些模拟脚本工作的代码
    for i in range(10, 0, -1):
        print(f"脚本剩余时间: {i} 秒...", end='\r')
        time.sleep(1)
    print("\n脚本正常完成。")

except KeyboardInterrupt:
    print("\n检测到 Ctrl+C，脚本正在退出...")
    # atexit 注册的函数仍然会被调用

# --- 脚本结束 ---
# 不需要在这里显式调用 print_mouse_position_on_exit，atexit 会处理