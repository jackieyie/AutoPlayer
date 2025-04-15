import pyautogui
import time
import random
import sys
import traceback # Keep traceback for unexpected errors

# --- 配置常量 ---
CONFIDENCE_LEVEL = 0.5 # 注意：0.5 仍然很低，易误识别
CHECK_INTERVAL = 10

# 图片文件路径 (!!! 必须在 2560x1440 下准确截取 !!!)
END_GAME_PANEL_IMG = "end_game.png"
PLAY_AGAIN_BTN_IMG = "play_again.png"
HERO_SELECT_SCREEN_IMG = "hero_select_screen.png"
MESSAGE_IMG = "message.png"

# 坐标 (!!! 基于你的 2560x1440 分辨率 !!!)
RETURN_BTN_ABS_POS = (1245, 39)
#排位英雄位置
# HERO_MAIN_POS = (536, 868)
# HERO_ALT_POS = (377, 587)
# HERO_THREE_POS = (242, 726)
# HERO_FOUR_POS =(507, 722)
# HERO_FIVE_POS =(122, 596)

#养小号英雄位置
HERO_MAIN_POS = (113, 468)
HERO_ALT_POS = (241, 462)
HERO_THREE_POS = (379, 457)
HERO_FOUR_POS =(517, 461)
HERO_FIVE_POS =(111, 594)

CONFIRM_BTN_POS = (1266, 1018) # 锁定按钮
PLAY_AGAIN_ABS_POS = (1226, 1306) # 再来一局按钮
MESSAGE_CLICK_POS = (1288, 846) # 消息界面的点击坐标

# !!! 超时设置 !!!
LOBBY_TIMEOUT_SECONDS = 3600 # 大厅超时 1 小时
MESSAGE_TIMEOUT_SECONDS = 3600 # <--- 新增：消息界面超时 1 小时

# 移动参数
INGAME_MOVE_DURATION = 1.5

# 超时设置 (图像查找)
STATE_CHECK_TIMEOUT = 2

# --- 核心函数 ---
# find_image, wasd_move, back_to_lobby, attempt_start_new_game, select_hero, handle_message 函数保持不变
# (为简洁起见，省略这些函数的代码，它们与上一个版本相同)
def find_image(image_path, confidence=CONFIDENCE_LEVEL, max_wait=STATE_CHECK_TIMEOUT):
    start_time = time.time()
    while True:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                return location
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            # print(f"查找图片时发生错误 ({image_path}): {e}") # Debug
            pass
        if time.time() - start_time > max_wait:
            return None
        time.sleep(0.5)


def wasd_move(duration=INGAME_MOVE_DURATION):
    if duration <= 0:
        return

    keys = ['w', 'a', 's', 'd']
    end_time = time.time() + duration
    active_key = None

    try:
        while time.time() < end_time:
            remaining_time = end_time - time.time()
            if remaining_time <= 0:
                break

            # 先松开当前按下的键
            if active_key:
                pyautogui.keyUp(active_key)
                active_key = None

            # 随机选择一个键按下
            key = random.choice(keys)
            press_time = random.uniform(0.2, min(0.8, remaining_time))  # 确保不超过剩余时间
            pyautogui.keyDown(key)
            active_key = key

            # 按住一段时间
            time.sleep(press_time)

            # 释放按键
            pyautogui.keyUp(active_key)
            active_key = None

            # 固定 1 秒间隔
            pyautogui.click(RETURN_BTN_ABS_POS)
            time.sleep(1)
            pyautogui.click(PLAY_AGAIN_ABS_POS)
            time.sleep(1)
            pyautogui.click(MESSAGE_CLICK_POS)
            time.sleep(20)

    except Exception as e:
        print(f"模拟移动时发生错误: {e}")
    finally:
        if active_key:
            pyautogui.keyUp(active_key)

def back_to_lobby():
    print(f"尝试直接点击返回房间按钮的绝对坐标: {RETURN_BTN_ABS_POS}")
    if RETURN_BTN_ABS_POS == (1245, 39):
         print("提示：正在使用坐标 (1245, 39) 点击返回房间。")
    try:
        pyautogui.click(RETURN_BTN_ABS_POS)
        print(f"已点击返回房间按钮 (绝对坐标)。等待返回...")
        time.sleep(random.uniform(6, 9))
        return True
    except Exception as e:
        print(f"点击绝对坐标 {RETURN_BTN_ABS_POS} 时发生错误: {e}")
        return False

def attempt_start_new_game():
    print("准备点击 '再来一局' 预设绝对坐标...")
    try:
        print(f"点击 '再来一局' 绝对坐标: {PLAY_AGAIN_ABS_POS}")
        pyautogui.click(PLAY_AGAIN_ABS_POS)
        print("已点击 '再来一局' (绝对坐标)。等待匹配...")
        time.sleep(random.uniform(12, 18))
        return True
    except Exception as e:
        print(f"点击绝对坐标 {PLAY_AGAIN_ABS_POS} 时发生错误: {e}")
        return False

def select_hero():
    """按顺序：(英雄->确认) * 5次，使用拖动方式移动鼠标"""
    print("检测到英雄选择界面，执行选择 (拖动到英雄->确认 循环 * 5)...")

    try:
        hero_to_confirm_sleep = 1.2
        confirm_to_hero_sleep = 1.2
        load_game_sleep = 15

        # 预定义英雄位置
        hero_positions = [
            HERO_MAIN_POS, HERO_ALT_POS, HERO_THREE_POS, HERO_FOUR_POS, HERO_FIVE_POS
        ]
        hero_names = [
            "主英雄", "备选英雄", "第三个英雄", "第四个英雄", "第五个英雄"
        ]

        # 随机起始位置，避免过于机械的鼠标行为
        screen_width, screen_height = pyautogui.size()
        random_start_positions = [
            (random.randint(0, screen_width), random.randint(0, screen_height)) for _ in range(len(hero_positions))
        ]

        for i in range(len(hero_positions)):
            # 随机起始位置
            start_pos = (100,100)
            target_pos = hero_positions[i]

            print(f" - 先将鼠标移动到随机起始位置: {start_pos}")
            pyautogui.moveTo(start_pos[0], start_pos[1], duration=random.uniform(0.5, 1.0))

            print(f" - 拖动鼠标到 {hero_names[i]} 位置: {target_pos}")
            pyautogui.moveTo(target_pos[0], target_pos[1], duration=random.uniform(0.5, 1.2))

            print(f" - 点击 {hero_names[i]}")
            pyautogui.click()
            print(f"   (暂停 {hero_to_confirm_sleep} 秒)")
            time.sleep(hero_to_confirm_sleep)

            print(f" - 拖动鼠标到确认按钮位置: {CONFIRM_BTN_POS}")
            pyautogui.moveTo(CONFIRM_BTN_POS[0], CONFIRM_BTN_POS[1], duration=random.uniform(0.5, 1.2))

            print(f" - 点击确认按钮 (第 {i+1} 次)")
            pyautogui.click()
            if i < len(hero_positions) - 1:
                print(f"   (暂停 {confirm_to_hero_sleep} 秒)")
                time.sleep(confirm_to_hero_sleep)
            else:
                print("英雄选择流程完成 (英雄->确认 循环 * 5)。")

        print(f"等待游戏加载 ({load_game_sleep} 秒)...")
        time.sleep(load_game_sleep)
        return True
    except Exception as e:
        print(f"选择英雄时发生错误: {e}")
        return False

def handle_message():
    """检测到消息界面后，点击指定坐标"""
    print("准备点击消息界面指定坐标...")
    if 'YOUR_MESSAGE_X' in str(MESSAGE_CLICK_POS):
         print("错误：MESSAGE_CLICK_POS 未配置正确的坐标！无法点击。")
         return False
    try:
        print(f"点击消息界面指定坐标: {MESSAGE_CLICK_POS}")
        pyautogui.click(MESSAGE_CLICK_POS)
        print("已点击消息界面坐标。")
        time.sleep(random.uniform(1, 2))
        return True
    except Exception as e:
        print(f"点击绝对坐标 {MESSAGE_CLICK_POS} 时发生错误: {e}")
        return False

# --- 主程序 ---
if __name__ == "__main__":
    print("自动化脚本启动 (带消息和大厅超时)...")
    print(f"目标分辨率: 2560x1440")
    print(f"状态检测间隔: {CHECK_INTERVAL} 秒")
    print(f"大厅超时时间: {LOBBY_TIMEOUT_SECONDS / 60:.0f} 分钟")
    print(f"消息界面超时时间: {MESSAGE_TIMEOUT_SECONDS / 60:.0f} 分钟") # 新增打印
    # ...(其他打印配置)...
    print("="*10 + " 使用的坐标 " + "="*10)
    print(f"返回房间按钮 (绝对): {RETURN_BTN_ABS_POS}")
    print(f"再来一局按钮 (绝对): {PLAY_AGAIN_ABS_POS}")
    print(f"主英雄 (绝对): {HERO_MAIN_POS}")
    print(f"备选英雄 (绝对): {HERO_ALT_POS}")
    print(f"第三个英雄 (绝对): {HERO_THREE_POS}")
    print(f"第四个英雄 (绝对): {HERO_FOUR_POS}")
    print(f"第五个英雄 (绝对): {HERO_FIVE_POS}")
    print(f"锁定按钮 (绝对): {CONFIRM_BTN_POS}")
    print(f"消息界面点击坐标: {MESSAGE_CLICK_POS}")
    print("="*10 + " 需要的文件 " + "="*10)
    print(f"- {END_GAME_PANEL_IMG} (检测结束)")
    print(f"- {PLAY_AGAIN_BTN_IMG} (检测大厅)")
    print(f"- {HERO_SELECT_SCREEN_IMG} (检测选人)")
    print(f"- {MESSAGE_IMG} (检测消息状态)")
    print("!!! 请确保以上图片已在 2560x1440 下正确截取 !!!")
    print(f"!!! 注意：置信度 CONFIDENCE_LEVEL 设置为 {CONFIDENCE_LEVEL} !!!")
    print("="*30)
    print("请在 3 秒内切换到游戏窗口...")
    print("按 Ctrl+C 停止。")
    time.sleep(3)

    last_check_time = time.time()
    consecutive_state_check_failures = 0
    in_lobby_since = None
    in_message_since = None # <--- 初始化消息计时器

    exit_reason = "未知原因" # 用于记录退出原因

    try:
        while True:
            now = time.time()
            is_currently_in_lobby = False
            is_currently_in_message = False # <--- 新增：本轮是否在消息界面

            # --- 状态检测逻辑 ---
            if now >= last_check_time + CHECK_INTERVAL:
                print(f"\n--- {time.strftime('%H:%M:%S')} 达到检查时间点 ---")
                last_check_time = now
                action_taken = False

                print("状态检测开始:")

                # 1. 检查是否游戏结束
                print(f"  1. 正在检测游戏结束 ({END_GAME_PANEL_IMG})...")
                end_game_loc = find_image(END_GAME_PANEL_IMG)
                if end_game_loc:
                    print(f"     结果: 检测到 [游戏结束] 状态 (位置: {end_game_loc})。")
                    if back_to_lobby():
                        action_taken = True
                    in_lobby_since = None # 重置大厅计时器
                    in_message_since = None # <--- 重置消息计时器
                    time.sleep(2)
                    consecutive_state_check_failures = 0
                else:
                    print(f"     结果: 未检测到游戏结束状态。")

                # 2. 检查是否在大厅 (带超时)
                if not action_taken:
                    print(f"  2. 正在检测大厅状态 ({PLAY_AGAIN_BTN_IMG})...")
                    play_again_loc = find_image(PLAY_AGAIN_BTN_IMG, max_wait=2)
                    if play_again_loc:
                        print(f"     结果: 检测到 [大厅] 状态 (位置: {play_again_loc})。")
                        is_currently_in_lobby = True
                        in_message_since = None # <--- 在大厅，重置消息计时器
                        if in_lobby_since is None:
                            print("        首次检测到大厅状态，启动计时器。")
                            in_lobby_since = now
                        else:
                            elapsed_lobby_time = now - in_lobby_since
                            print(f"        已在大厅停留 {elapsed_lobby_time:.0f} 秒。")
                            if elapsed_lobby_time > LOBBY_TIMEOUT_SECONDS:
                                exit_reason = "大厅超时"
                                print(f"!!!!!! 在大厅停留超过 {LOBBY_TIMEOUT_SECONDS / 60:.0f} 分钟，脚本将停止运行。 !!!!!!")
                                sys.exit()
                        if attempt_start_new_game():
                             print("        已尝试点击 '再来一局'。")
                             action_taken = True
                             in_lobby_since = None # 假设点击成功离开大厅
                        else:
                             print("        点击 '再来一局' 失败。")
                        consecutive_state_check_failures = 0
                    else:
                        print(f"     结果: 未检测到大厅状态。")
                        if in_lobby_since is not None:
                             print("        之前在大厅，现已离开，重置计时器。")
                        in_lobby_since = None

                # 3. 检查是否在英雄选择
                if not action_taken:
                    print(f"  3. 正在检测英雄选择状态 ({HERO_SELECT_SCREEN_IMG})...")
                    hero_select_loc = find_image(HERO_SELECT_SCREEN_IMG)
                    if hero_select_loc:
                        print(f"     结果: 检测到 [英雄选择] 状态 (位置: {hero_select_loc})。")
                        in_lobby_since = None # 重置大厅计时器
                        in_message_since = None # <--- 重置消息计时器
                        if select_hero():
                            action_taken = True
                        time.sleep(2)
                        consecutive_state_check_failures = 0
                    else:
                        print(f"     结果: 未检测到英雄选择状态。")

                # 4. 检查消息状态 (带超时)
                if not action_taken:
                    print(f"  4. 正在检测消息状态 ({MESSAGE_IMG})...")
                    message_loc = find_image(MESSAGE_IMG, max_wait=1)
                    if message_loc:
                        print(f"     结果: 检测到 [消息] 状态 (位置: {message_loc})。")
                        is_currently_in_message = True # <--- 标记在消息界面
                        in_lobby_since = None # 在消息界面，重置大厅计时器
                        if in_message_since is None:
                            print("        首次检测到消息状态，启动计时器。")
                            in_message_since = now
                        else:
                            # 仍然在消息状态，检查超时
                            elapsed_message_time = now - in_message_since
                            print(f"        已在消息界面停留 {elapsed_message_time:.0f} 秒。")
                            if elapsed_message_time > MESSAGE_TIMEOUT_SECONDS:
                                exit_reason = "消息界面超时"
                                print(f"!!!!!! 在消息界面停留超过 {MESSAGE_TIMEOUT_SECONDS / 60:.0f} 分钟，脚本将停止运行。 !!!!!!")
                                sys.exit() # 因消息超时退出
                        # 如果没超时，尝试处理消息
                        if handle_message():
                             print("        已尝试点击处理消息。")
                             action_taken = True
                             # 假设点击成功会离开消息界面，重置计时器
                             in_message_since = None
                        else:
                            print("        点击处理消息失败。")
                            # 点击失败，计时器不重置
                        consecutive_state_check_failures = 0
                    else:
                         print(f"     结果: 未检测到消息状态。")
                         # 不在消息状态，重置计时器
                         if in_message_since is not None:
                              print("        之前在消息界面，现已离开，重置计时器。")
                         in_message_since = None

                # 5. 总结检测结果
                print("状态检测结束。")
                current_state = "[未知/游戏中]"
                if is_currently_in_lobby: current_state = "[大厅]"
                if is_currently_in_message: current_state = "[消息界面]"
                if action_taken: current_state += " (已处理)"

                if not action_taken and not is_currently_in_lobby and not is_currently_in_message:
                    print(f"总结: 未识别到任何明确状态，将假定在游戏中。")
                    consecutive_state_check_failures += 1
                    if consecutive_state_check_failures > (3600 // CHECK_INTERVAL): # 约1小时
                         print(f"警告：已连续 {consecutive_state_check_failures * CHECK_INTERVAL / 60 :.0f} 分钟未能识别明确状态！请检查游戏或脚本。")
                    # 确保所有计时器都已重置
                    in_lobby_since = None
                    in_message_since = None
                elif action_taken:
                    print(f"总结: 已识别并处理了一个状态: {current_state}")
                    consecutive_state_check_failures = 0
                elif is_currently_in_lobby or is_currently_in_message:
                    print(f"总结: 当前停留在 {current_state}，但未执行离开操作 (可能超时检查通过或点击失败)。")
                    consecutive_state_check_failures = 0

                print(f"--- {time.strftime('%H:%M:%S')} 状态检查与处理完毕 ---")


            # --- 游戏进行中逻辑 ---
            else:
                wasd_move(duration=INGAME_MOVE_DURATION)
                time.sleep(random.uniform(0.5, 1.0))

    except KeyboardInterrupt:
        exit_reason = "用户中断 (Ctrl+C)"
        print(f"\n脚本被{exit_reason}。")
    except SystemExit:
        # exit_reason 应该在超时逻辑中被设置
        print(f"脚本因 {exit_reason} 而正常停止。")
    except Exception as e:
        exit_reason = "发生未处理的致命错误"
        print(f"\n{exit_reason}，脚本将终止: {e}")
        traceback.print_exc()
    finally:
        print("="*30)
        print(f"自动化脚本已结束。退出原因: {exit_reason}")
