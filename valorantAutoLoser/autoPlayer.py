import pyautogui
import time
import random

# --- 坐标定义 ---
HERO_POSITIONS = [
    (113, 468), (241, 462), (379, 457), (517, 461), (111, 594)
]
CONFIRM_BTN_POS = (1266, 1018)
PLAY_AGAIN_ABS_POS = (1226, 1306)
MESSAGE_CLICK_POS = (1288, 846)

# --- 参数配置 ---
MOVE_SPEED = 0.5  # 鼠标移动速度
CLICK_INTERVAL = 1.0  # 点击后的等待时间
WALK_STEPS = 5  # 随机走动的次数
ROUND_INTERVAL = 3.0  # 每一轮大循环之间的停顿时间


def smooth_click(target_pos):
    """平滑移动并点击"""
    x, y = target_pos
    pyautogui.moveTo(x, y, duration=MOVE_SPEED)
    pyautogui.click()
    time.sleep(CLICK_INTERVAL)


def random_move():
    """随机按下 WASD 键让人物移动"""
    keys = ['w', 'a', 's', 'd']
    print(f"--- 开始随机移动 (共 {WALK_STEPS} 步) ---")

    for i in range(WALK_STEPS):
        key = random.choice(keys)
        duration = random.uniform(0.2, 1.0)
        print(f"步数 {i + 1}: 按下 [{key.upper()}] 持续 {duration:.2f} 秒")

        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)
        time.sleep(0.1)

        print("--- 移动结束，准备执行键盘发送序列 ---")

        # 1. 按下回车 (打开输入框)
        pyautogui.press('enter')
        time.sleep(0.5)  # 稍微停顿，等待输入框弹出

        # 2. 按下 Control + V (粘贴内容)
        # hotkey 会按顺序按下这些键，然后按相反顺序释放
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        # 3. 再次按下回车 (发送消息)
        pyautogui.press('enter')
        print("--- 键盘序列执行完毕 ---")


def run_script():
    # 彻底禁用安全保护（请谨慎使用，因为脚本会一直循环）
    pyautogui.FAILSAFE = False

    print("脚本已启动，3秒后进入无限循环模式...")
    time.sleep(3)

    count = 1
    while True:
        print(f"\n======== 开始执行第 {count} 轮循环 ========")

        # 1. 英雄选择循环（点英雄 -> 点确认）
        for i, hero_pos in enumerate(HERO_POSITIONS, 1):
            print(f"步骤 {i}: 选择英雄位置 {hero_pos}")
            smooth_click(hero_pos)
            print(f"步骤 {i}: 点击确认按钮")
            smooth_click(CONFIRM_BTN_POS)

        # 2. 点击后续功能按钮
        print("点击：再来一局")
        smooth_click(PLAY_AGAIN_ABS_POS)
        print("点击：消息界面")
        smooth_click(MESSAGE_CLICK_POS)

        # 3. 随机移动
        random_move()

        print(f"✅ 第 {count} 轮任务执行完毕。")
        print(f"休息 {ROUND_INTERVAL} 秒后开始下一轮...")

        time.sleep(ROUND_INTERVAL)
        count += 1


if __name__ == "__main__":
    try:
        run_script()
    except KeyboardInterrupt:
        # 在终端按下 Ctrl+C 即可安全停止
        print("\n[检测到停止信号] 脚本已结束运行。")
