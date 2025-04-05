# -*- coding: utf-8 -*-
import pyautogui
import time
import random # random 库已导入，可用于选择
import sys
import traceback
from playsound import playsound

# --- 配置常量 ---
CONFIDENCE_LEVEL = 0.5
CHECK_INTERVAL = 10

# +++ 修改 +++ : 使用列表存储多个音频文件名
# !!! 编辑这个列表，放入你所有想要随机播放的音频文件名 !!!
# !!! 确保这些文件都放在脚本所在的文件夹下 !!!
AUDIO_FILES_TO_PLAY = [
    "sound1.wav",
    "voice_line_a.mp3",
    "effect_b.wav",
    # 添加更多文件名...
]

# 图片文件路径
END_GAME_PANEL_IMG = "end_game.png"
PLAY_AGAIN_BTN_IMG = "play_again.png"
HERO_SELECT_SCREEN_IMG = "hero_select_screen.png"
MESSAGE_IMG = "message.png"

# 坐标
RETURN_BTN_ABS_POS = (1245, 39)
# ... (其他坐标保持不变) ...
HERO_MAIN_POS = (113, 468)
HERO_ALT_POS = (241, 462)
HERO_THREE_POS = (379, 457)
HERO_FOUR_POS =(517, 461)
HERO_FIVE_POS =(111, 594)
CONFIRM_BTN_POS = (1266, 1018)
PLAY_AGAIN_ABS_POS = (1226, 1306)
MESSAGE_CLICK_POS = (1279, 900)

# 超时设置
LOBBY_TIMEOUT_SECONDS = 3600
MESSAGE_TIMEOUT_SECONDS = 3600

# 移动参数
INGAME_MOVE_DURATION = 1.5

# 超时设置 (图像查找)
STATE_CHECK_TIMEOUT = 2

# --- 核心函数 ---
def find_image(image_path, confidence=CONFIDENCE_LEVEL, max_wait=STATE_CHECK_TIMEOUT):
    # (此函数保持不变)
    start_time = time.time()
    while True:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location: return location
        except pyautogui.ImageNotFoundException: pass
        except Exception as e: pass
        if time.time() - start_time > max_wait: return None
        time.sleep(0.5)

def wasd_move(duration=INGAME_MOVE_DURATION):
    # (此函数保持不变)
    if duration <= 0: return
    keys = ['w', 'a', 's', 'd', 'x']; end_time = time.time() + duration
    active_key = None
    try:
        while time.time() < end_time:
            remaining_time = end_time - time.time()
            if remaining_time <= 0: break
            if active_key: pyautogui.keyUp(active_key); active_key = None
            key = random.choice(keys)
            press_time = random.uniform(0.2, min(0.8, max(0.1, remaining_time - 1.1)))
            if press_time <= 0: break
            pyautogui.keyDown(key); active_key = key
            time.sleep(press_time)
            if time.time() < end_time: pyautogui.keyUp(active_key); active_key = None
            else:
                if active_key: pyautogui.keyUp(active_key)
                break
            wait_interval = 1.0
            if end_time - time.time() > wait_interval: time.sleep(wait_interval)
            else: break
    except Exception as e: print(f"模拟移动时发生错误: {e}")
    finally:
        if active_key: pyautogui.keyUp(active_key)

def back_to_lobby():
    # (此函数保持不变)
    print(f"尝试直接点击返回房间按钮的绝对坐标: {RETURN_BTN_ABS_POS}")
    if RETURN_BTN_ABS_POS == (1245, 39): print("提示：正在使用坐标 (1245, 39) 点击返回房间。")
    try:
        pyautogui.click(RETURN_BTN_ABS_POS); time.sleep(1)
        pyautogui.click(RETURN_BTN_ABS_POS)
        print(f"已点击返回房间按钮 (绝对坐标)。等待返回...")
        time.sleep(1); return True
    except Exception as e: print(f"点击绝对坐标 {RETURN_BTN_ABS_POS} 时发生错误: {e}"); return False

def attempt_start_new_game():
    # (此函数保持不变)
    print("准备点击 '再来一局' 预设绝对坐标...")
    try:
        print(f"点击 '再来一局' 绝对坐标: {PLAY_AGAIN_ABS_POS}")
        pyautogui.click(PLAY_AGAIN_ABS_POS)
        print("已点击 '再来一局' (绝对坐标)。等待匹配...")
        time.sleep(30); return True
    except Exception as e: print(f"点击绝对坐标 {PLAY_AGAIN_ABS_POS} 时发生错误: {e}"); return False

def select_hero():
    # (此函数保持不变)
    print("检测到英雄选择界面，执行选择 (拖动到英雄->确认 循环 * 5)...")
    try:
        hero_to_confirm_sleep = 1.2; confirm_to_hero_sleep = 1.2; load_game_sleep = 15
        hero_positions = [ HERO_MAIN_POS, HERO_ALT_POS, HERO_THREE_POS, HERO_FOUR_POS, HERO_FIVE_POS ]
        hero_names = [ "主英雄", "备选英雄", "第三个英雄", "第四个英雄", "第五个英雄" ]
        for i in range(len(hero_positions)):
            start_pos = (100,100); target_pos = hero_positions[i]
            print(f" - 先将鼠标移动到随机起始位置: {start_pos}")
            pyautogui.moveTo(start_pos[0], start_pos[1], duration=random.uniform(0.5, 1.0))
            print(f" - 拖动鼠标到 {hero_names[i]} 位置: {target_pos}")
            pyautogui.moveTo(target_pos[0], target_pos[1], duration=random.uniform(0.5, 1.2))
            print(f" - 点击 {hero_names[i]}")
            pyautogui.click(); print(f"   (暂停 {hero_to_confirm_sleep} 秒)"); time.sleep(hero_to_confirm_sleep)
            print(f" - 拖动鼠标到确认按钮位置: {CONFIRM_BTN_POS}")
            pyautogui.moveTo(CONFIRM_BTN_POS[0], CONFIRM_BTN_POS[1], duration=random.uniform(0.5, 1.2))
            print(f" - 点击确认按钮 (第 {i+1} 次)")
            pyautogui.click()
            if i < len(hero_positions) - 1: print(f"   (暂停 {confirm_to_hero_sleep} 秒)"); time.sleep(confirm_to_hero_sleep)
            else: print("英雄选择流程完成 (英雄->确认 循环 * 5)。")
        print(f"等待游戏加载 ({load_game_sleep} 秒)..."); time.sleep(load_game_sleep)
        return True
    except Exception as e: print(f"选择英雄时发生错误: {e}"); return False

def handle_message():
    # (此函数保持不变)
    print("准备点击消息界面指定坐标...")
    if 'YOUR_MESSAGE_X' in str(MESSAGE_CLICK_POS): print("错误：MESSAGE_CLICK_POS 未配置正确的坐标！无法点击。"); return False
    try:
        print(f"点击消息界面指定坐标: {MESSAGE_CLICK_POS}")
        pyautogui.click(MESSAGE_CLICK_POS)
        print("已点击消息界面坐标。"); time.sleep(random.uniform(1, 2)); return True
    except Exception as e: print(f"点击绝对坐标 {MESSAGE_CLICK_POS} 时发生错误: {e}"); return False


# --- 播放音频并按 V 键的函数 ---
# +++ 修改 +++ : 函数本身逻辑不变，仍然接收一个文件名参数
def play_audio_and_press_v(audio_filename):
    """
    尝试播放指定的音频文件，然后在播放结束后模拟按下 'V' 键。
    """
    print(f"尝试播放音频 '{audio_filename}' 并按下 'V' 键...")
    audio_played_successfully = False
    try:
        print(f"  - 正在播放: {audio_filename}")
        playsound(audio_filename)
        print("  - 音频播放完成。")
        audio_played_successfully = True
    except FileNotFoundError:
         print(f"  [错误] 音频文件未找到: {audio_filename}")
         return False
    except Exception as e:
        print(f"  [错误] 使用 playsound 播放音频时发生错误: {e}")
        return False

    if audio_played_successfully:
        try:
            print("  - 模拟按下 'V' 键...")
            pyautogui.press('v')
            time.sleep(0.1)
            print("  - 'V' 键已按下。")
            return True
        except Exception as e:
            print(f"  [错误] 模拟按下 'V' 键时发生错误: {e}")
            return False
    else:
        print("  - 音频未成功播放，未按下 'V' 键。")
        return False

# --- 主程序 ---
if __name__ == "__main__":
    print("自动化脚本启动...")
    # ... (省略大部分配置打印) ...
    # +++ 修改 +++ : 打印列表内容或列表长度
    if AUDIO_FILES_TO_PLAY:
        print(f"将从以下 {len(AUDIO_FILES_TO_PLAY)} 个音频文件中随机选择:")
        # for f in AUDIO_FILES_TO_PLAY: # 可选：打印所有文件名
        #     print(f"  - {f}")
    else:
        print("[警告] 音频文件列表为空！将无法播放音频。")
    print("="*30)
    print("请在 3 秒内切换到游戏窗口...")
    print("按 Ctrl+C 停止。")
    time.sleep(3)

    need_to_play_audio_flag = False
    print("音频播放标志初始化为 False")

    last_check_time = time.time()
    consecutive_state_check_failures = 0
    in_lobby_since = None
    in_message_since = None
    exit_reason = "未知原因"

    try:
        while True:
            now = time.time()
            is_currently_in_lobby = False
            is_currently_in_message = False

            # --- 状态检测逻辑 ---
            if now >= last_check_time + CHECK_INTERVAL:
                print(f"\n--- {time.strftime('%H:%M:%S')} 达到检查时间点 ---")
                last_check_time = now
                action_taken = False
                is_in_known_state = False

                print("状态检测开始:")

                # 1. 检查是否游戏结束
                # (逻辑不变，但在成功返回大厅后重置 need_to_play_audio_flag = False)
                print(f"  1. 正在检测游戏结束 ({END_GAME_PANEL_IMG})...")
                end_game_loc = find_image(END_GAME_PANEL_IMG)
                if end_game_loc:
                    is_in_known_state = True
                    print(f"     结果: 检测到 [游戏结束] 状态。")
                    if back_to_lobby():
                        action_taken = True
                        need_to_play_audio_flag = False # 重置标志
                        print("        游戏结束返回大厅，音频播放标志重置为 False")
                    in_lobby_since = None; in_message_since = None
                    time.sleep(2); consecutive_state_check_failures = 0
                else: print(f"     结果: 未检测到游戏结束状态。")


                # 2. 检查是否在大厅
                # (逻辑不变，但在成功开始新游戏后设置 need_to_play_audio_flag = True)
                if not action_taken:
                    print(f"  2. 正在检测大厅状态 ({PLAY_AGAIN_BTN_IMG})...")
                    play_again_loc = find_image(PLAY_AGAIN_BTN_IMG, max_wait=2)
                    if play_again_loc:
                        is_in_known_state = True
                        print(f"     结果: 检测到 [大厅] 状态。")
                        is_currently_in_lobby = True; in_message_since = None
                        if in_lobby_since is None: print("        首次检测到大厅状态，启动计时器。"); in_lobby_since = now
                        else:
                            elapsed_lobby_time = now - in_lobby_since
                            print(f"        已在大厅停留 {elapsed_lobby_time:.0f} 秒。")
                            if elapsed_lobby_time > LOBBY_TIMEOUT_SECONDS: exit_reason = "大厅超时"; sys.exit()
                        if attempt_start_new_game():
                             print("        已尝试点击 '再来一局'。")
                             action_taken = True; in_lobby_since = None
                             need_to_play_audio_flag = True # 准备播放
                             print("        新游戏开始，音频播放标志设置为 True")
                        else: print("        点击 '再来一局' 失败。")
                        consecutive_state_check_failures = 0
                    else:
                        print(f"     结果: 未检测到大厅状态。")
                        if in_lobby_since is not None: print("        之前在大厅，现已离开，重置计时器。")
                        in_lobby_since = None; is_currently_in_lobby = False

                # 3. 检查是否在英雄选择
                # (逻辑不变，但在成功选择英雄后设置 need_to_play_audio_flag = True)
                if not action_taken:
                    print(f"  3. 正在检测英雄选择状态 ({HERO_SELECT_SCREEN_IMG})...")
                    hero_select_loc = find_image(HERO_SELECT_SCREEN_IMG)
                    if hero_select_loc:
                        is_in_known_state = True
                        print(f"     结果: 检测到 [英雄选择] 状态。")
                        in_lobby_since = None; in_message_since = None
                        if select_hero():
                            action_taken = True
                            need_to_play_audio_flag = True # 准备播放
                            print("        英雄选择完成，音频播放标志设置为 True")
                        time.sleep(2); consecutive_state_check_failures = 0
                    else: print(f"     结果: 未检测到英雄选择状态。")


                # 4. 检查消息状态
                # (逻辑不变)
                if not action_taken:
                    print(f"  4. 正在检测消息状态 ({MESSAGE_IMG})...")
                    message_loc = find_image(MESSAGE_IMG, max_wait=1)
                    if message_loc:
                        is_in_known_state = True
                        print(f"     结果: 检测到 [消息] 状态。")
                        is_currently_in_message = True; in_lobby_since = None
                        if in_message_since is None: print("        首次检测到消息状态，启动计时器。"); in_message_since = now
                        else:
                            elapsed_message_time = now - in_message_since
                            print(f"        已在消息界面停留 {elapsed_message_time:.0f} 秒。")
                            if elapsed_message_time > MESSAGE_TIMEOUT_SECONDS: exit_reason = "消息界面超时"; sys.exit()
                        if handle_message(): print("        已尝试点击处理消息。"); action_taken = True; in_message_since = None
                        else: print("        点击处理消息失败。")
                        consecutive_state_check_failures = 0
                    else:
                         print(f"     结果: 未检测到消息状态。")
                         if in_message_since is not None: print("        之前在消息界面，现已离开，重置计时器。")
                         in_message_since = None; is_currently_in_message = False


                # 5. 总结检测结果 并 处理“在游戏中”状态
                print("状态检测结束。")
                if not is_in_known_state:
                    # --- 未检测到任何已知状态 => 判断为在游戏中 ---
                    print(f"总结: 未识别到任何明确状态，将假定在游戏中。")
                    consecutive_state_check_failures += 1
                    if consecutive_state_check_failures > (3600 // CHECK_INTERVAL): print(f"警告：已连续 {consecutive_state_check_failures * CHECK_INTERVAL / 60 :.0f} 分钟未能识别明确状态！")
                    in_lobby_since = None; in_message_since = None

                    # --- 在游戏中时，检查是否需要播放音频 ---
                    if need_to_play_audio_flag:
                        print("        检测到在游戏中且需要播放音频...")
                        # +++ 修改 +++ : 随机选择音频文件
                        if not AUDIO_FILES_TO_PLAY: # 检查列表是否为空
                            print("        [警告] 音频文件列表为空，无法播放。")
                        else:
                            chosen_audio_file = random.choice(AUDIO_FILES_TO_PLAY)
                            print(f"        随机选择音频: {chosen_audio_file}")
                            # === 调用播放音频并按 V 的函数 ===
                            if play_audio_and_press_v(chosen_audio_file):
                                print("        音频播放和按键成功。")
                            else:
                                print("        音频播放或按键失败。")
                        # === 播放尝试后（无论成功、失败、列表为空），重置标志 ===
                        need_to_play_audio_flag = False
                        print("        音频播放尝试完成，标志重置为 False")
                        # === 本周期不移动 ===
                        print("        (本周期播放音频，跳过移动)")
                        time.sleep(0.5)
                    else:
                        # --- 不需要播放音频，执行移动 ---
                        print("        执行 WASD 移动...")
                        wasd_move(duration=INGAME_MOVE_DURATION)

                # (处理已知状态的 elif 部分保持不变)
                elif action_taken: print(f"总结: 已识别并处理了一个状态。"); consecutive_state_check_failures = 0
                elif is_in_known_state:
                     current_state = "[大厅]" if is_currently_in_lobby else "[消息界面]" if is_currently_in_message else "[英雄选择]" if find_image(HERO_SELECT_SCREEN_IMG, max_wait=0.1) else "[游戏结束]"
                     print(f"总结: 当前停留在 {current_state} (未执行离开操作或操作失败)。"); consecutive_state_check_failures = 0

                print(f"--- {time.strftime('%H:%M:%S')} 状态检查与处理完毕 ---")


            # --- 非检查时间点的操作 ---
            else:
                time.sleep(0.5) # 保留休眠

    # ... (异常处理和 finally 块保持不变) ...
    except KeyboardInterrupt: exit_reason = "用户中断 (Ctrl+C)"; print(f"\n脚本被{exit_reason}。")
    except SystemExit: print(f"脚本因 {exit_reason} 而正常停止。")
    except Exception as e: exit_reason = "发生未处理的致命错误"; print(f"\n{exit_reason}，脚本将终止: {e}"); traceback.print_exc()
    finally: print("="*30); print(f"自动化脚本已结束。退出原因: {exit_reason}")
