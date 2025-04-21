# -*- coding: utf-8 -*- # <--- 确保Python能正确处理UTF-8字符（中文注释）

import pyautogui
import time
import random
import sys
import traceback      # 用于打印详细的错误信息
import keyboard       # 用于全局热键监听 (需要 pip install keyboard)
import threading      # 用于将悬浮窗放入单独的线程，防止阻塞主程序
import tkinter as tk  # Python内置的GUI库，用于创建悬浮窗
# import ctypes         # 不再需要 ctypes，因为我们放弃了点击穿透
import platform       # 用于检测操作系统类型 (虽然现在通用性更强，但保留以备将来扩展)

# --- 配置常量 ---

CONFIDENCE_LEVEL = 0.5      # PyAutoGUI图像识别的置信度（0.0-1.0）
CHECK_INTERVAL = 10         # 脚本运行时，检查游戏状态的时间间隔（秒）

# 图片文件路径 (!!! 必须在 2560x1440 分辨率下准确截取 !!!)
END_GAME_PANEL_IMG = "end_game.png"
PLAY_AGAIN_BTN_IMG = "play_again.png"
HERO_SELECT_SCREEN_IMG = "hero_select_screen.png"
MESSAGE_IMG = "message.png"

# 坐标 (!!! 基于你的 2560x1440 分辨率，需要自行校准 !!!)
RETURN_BTN_ABS_POS = (1245, 39)

# --- 选择一套英雄位置 (取消注释你需要的那一套) ---
# 养小号英雄位置示例 (需要你自己校准)
HERO_MAIN_POS = (113, 468)
HERO_ALT_POS = (241, 462)
HERO_THREE_POS = (379, 457)
HERO_FOUR_POS =(517, 461)
HERO_FIVE_POS =(111, 594)

# 其他坐标 (需要你自己校准)
CONFIRM_BTN_POS = (1266, 1018)
PLAY_AGAIN_ABS_POS = (1226, 1306)
MESSAGE_CLICK_POS = (1278, 948)
CHEAT_HANDLER_POS = (1275, 1222)

# !!! 超时设置 !!!
LOBBY_TIMEOUT_SECONDS = 3600
MESSAGE_TIMEOUT_SECONDS = 3600

# 移动参数
INGAME_MOVE_DURATION = 1.5

# 超时设置 (图像查找)
STATE_CHECK_TIMEOUT = 2

# --- 全局状态变量 ---
is_running = False
script_needs_to_exit = False
status_overlay = None # 指向状态悬浮窗对象的全局变量

# --- 简单的置顶状态悬浮窗类 (不含点击穿透) ---
class SimpleStatusOverlay:
    """
    创建一个简单的、总在最前的状态显示悬浮窗。
    注意：此窗口会遮挡其下方区域，无法点击穿透。
    """
    def __init__(self):
        self.root = None
        self.label = None
        self.thread = None
        self._stop_event = threading.Event()
        self._text_to_set = "初始化中..."

        # --- 悬浮窗配置 ---
        self.pos_x_offset = -250  # 距离屏幕右边缘的水平偏移量
        self.pos_y_offset = 10    # 距离屏幕上边缘的垂直偏移量
        self.bg_color = 'white'   # 背景色 (白色)
        self.fg_color = 'black'   # 文字颜色 (黑色)
        self.font_size = 14
        self.update_interval_ms = 100

    def _overlay_thread_target(self):
        """悬浮窗线程的执行目标函数"""
        try:
            # --- 创建 Tkinter 窗口 ---
            self.root = tk.Tk()
            self.root.overrideredirect(True) # 创建无边框窗口

            # 计算窗口位置
            screen_width = self.root.winfo_screenwidth()
            pos_x = max(0, screen_width + self.pos_x_offset)
            self.root.geometry(f"+{pos_x}+{self.pos_y_offset}")

            self.root.lift()                 # 提升窗口层级
            # --- 设置总在最前 ---
            self.root.attributes('-topmost', True)

            # --- 设置窗口和标签的颜色 ---
            self.root.config(bg=self.bg_color) # 设置根窗口背景色

            self.label = tk.Label(self.root, text=self._text_to_set,
                                  font=('Consolas', self.font_size, 'bold'),
                                  fg=self.fg_color, bg=self.bg_color, # 标签前景/背景
                                  padx=5, pady=2)
            self.label.pack()

            # --- 无需 ctypes 调用 ---
            # 因为不再尝试点击穿透，所以不需要复杂的 Windows API

            print("状态悬浮窗: 简单置顶窗口创建成功。")
            # --- 启动 Tkinter 事件循环 ---
            self.root.after(self.update_interval_ms, self._check_for_updates)
            self.root.mainloop()

        except Exception as e:
            print(f"状态悬浮窗线程出错: {e}")
            traceback.print_exc()
        finally:
            if self.root:
                try:
                    self.root.destroy()
                except tk.TclError:
                    pass
            print("状态悬浮窗: 线程结束。")
            self._stop_event.set()

    def _check_for_updates(self):
        """在Tkinter事件循环中周期性地检查是否有退出请求或文本更新"""
        if self._stop_event.is_set():
            if self.root:
                self.root.quit()
            return

        if self.label and self.label.winfo_exists():
            current_text = self.label.cget("text")
            if current_text != self._text_to_set:
                 self.label.config(text=self._text_to_set)

        if self.root and self.root.winfo_exists():
            self.root.after(self.update_interval_ms, self._check_for_updates)

    def start(self):
        """启动悬浮窗线程"""
        # 这个简单的版本理论上跨平台性更好，但主要还是在Windows测试
        if self.thread is None or not self.thread.is_alive():
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._overlay_thread_target, daemon=True)
            self.thread.start()
            print("状态悬浮窗: 正在启动线程...")
            time.sleep(0.5)

    def update_status(self, text):
        """线程安全地更新悬浮窗显示的文本"""
        self._text_to_set = text

    def close(self):
        """请求关闭悬浮窗线程"""
        print("状态悬浮窗: 请求关闭。")
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
             print("状态悬浮窗: 等待线程结束...")
             self.thread.join(timeout=2.0)
             if self.thread.is_alive():
                 print("状态悬浮窗: 警告 - 线程未能正常结束。")
        self.thread = None
        print("状态悬浮窗: 已关闭。")


# --- 核心功能函数 (保持不变) ---
# find_image, controlled_sleep, wasd_move, back_to_lobby,
# attempt_start_new_game, select_hero, handle_message 函数的代码与之前相同
# 为简洁起见，这里省略这些函数的代码，它们应保持不变

def find_image(image_path, confidence=CONFIDENCE_LEVEL, max_wait=STATE_CHECK_TIMEOUT):
    start_time = time.time()
    while True:
        if script_needs_to_exit: return None
        if not is_running:
            time.sleep(0.1); start_time = time.time(); continue
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location: return location
        except pyautogui.ImageNotFoundException: pass
        except Exception as e: pass # print(f"查找图片异常: {e}")
        if time.time() - start_time > max_wait: return None
        time.sleep(0.1)

def controlled_sleep(duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        if script_needs_to_exit: return False
        if not is_running:
            while not is_running:
                 if script_needs_to_exit: return False
                 time.sleep(0.1)
            if time.time() >= end_time: break
        time.sleep(0.1)
    return True

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
            time.sleep(1)
            pyautogui.click(CHEAT_HANDLER_POS)
            time.sleep(20)

    except Exception as e:
        print(f"模拟移动时发生错误: {e}")
    finally:
        if active_key:
            pyautogui.keyUp(active_key)

def back_to_lobby():
    print(f"尝试点击返回房间按钮: {RETURN_BTN_ABS_POS}")
    try:
        pyautogui.click(RETURN_BTN_ABS_POS); print("已点击。等待返回...")
        if not controlled_sleep(random.uniform(6, 9)): return False
        return True
    except Exception as e: print(f"点击 {RETURN_BTN_ABS_POS} 错误: {e}"); return False

def attempt_start_new_game():
    print("准备点击 '再来一局'...")
    try:
        print(f"点击 '再来一局' 坐标: {PLAY_AGAIN_ABS_POS}")
        pyautogui.click(PLAY_AGAIN_ABS_POS); print("已点击。等待匹配...")
        if not controlled_sleep(random.uniform(12, 18)): return False
        return True
    except Exception as e: print(f"点击 {PLAY_AGAIN_ABS_POS} 错误: {e}"); return False

def select_hero():
    print("执行选英雄流程...")
    try:
        hero_to_confirm_sleep = 1.2; confirm_to_hero_sleep = 1.2; load_game_sleep = 15
        hero_positions = [HERO_MAIN_POS, HERO_ALT_POS, HERO_THREE_POS, HERO_FOUR_POS, HERO_FIVE_POS]
        hero_names = ["主英雄", "备选1", "备选2", "备选3", "备选4"]
        for i in range(len(hero_positions)):
            if script_needs_to_exit or not is_running: return False
            target_pos = hero_positions[i]; print(f" - [{i+1}/5] 选 {hero_names[i]} @ {target_pos}")
            pyautogui.moveTo(target_pos[0], target_pos[1], duration=random.uniform(0.4, 0.8)); pyautogui.click()
            if not controlled_sleep(hero_to_confirm_sleep): return False; print(f"   (等 {hero_to_confirm_sleep:.1f}s)")
            if script_needs_to_exit or not is_running: return False
            print(f" - [{i+1}/5] 点确认 @ {CONFIRM_BTN_POS}")
            pyautogui.moveTo(CONFIRM_BTN_POS[0], CONFIRM_BTN_POS[1], duration=random.uniform(0.4, 0.8)); pyautogui.click(); print(f"   (已确认)")
            if i < len(hero_positions) - 1:
                if not controlled_sleep(confirm_to_hero_sleep): return False; print(f"   (等 {confirm_to_hero_sleep:.1f}s)")
            else: print("选人完成.")
        print(f"等待加载 ({load_game_sleep} 秒)...")
        if not controlled_sleep(load_game_sleep): return False
        return True
    except Exception as e: print(f"选英雄错误: {e}"); return False

def handle_message():
    print("准备点消息界面...")
    try:
        print(f"点击消息坐标: {MESSAGE_CLICK_POS}"); pyautogui.click(MESSAGE_CLICK_POS); print("已点击.")
        if not controlled_sleep(random.uniform(1, 2)): return False
        return True
    except Exception as e: print(f"点击 {MESSAGE_CLICK_POS} 错误: {e}"); return False

# --- 热键切换功能 (保持不变) ---
def toggle_script_state():
    """切换脚本的运行/暂停状态，并更新悬浮窗文本"""
    global is_running
    is_running = not is_running
    status_text = "上分中" if is_running else "已暂停"
    print(f"\n--- 脚本状态被 'k' 键切换为: {status_text} ---")
    # 更新悬浮窗显示的文本 (如果悬浮窗存在)
    if status_overlay:
        status_overlay.update_status(f"状态: {status_text} ") # 加空格确保文本变化

# --- 键盘监听器设置 (保持不变) ---
try:
    keyboard.add_hotkey('k', toggle_script_state)
    print("已设置 'k' 键来切换脚本运行/暂停状态。")
except Exception as e:
    print(f"警告：无法设置 'k' 键热键。错误: {e}")
    print("可能原因：\n  - 在 Linux/macOS 上没有使用 root/sudo 权限运行脚本。\n  - 键盘监听库与其他程序冲突。")
    print("脚本将无法通过 'k' 键暂停/启动，将直接开始运行。")
    is_running = True

# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 创建并启动状态悬浮窗 ---
    print("正在创建状态悬浮窗 (简单置顶版)...")
    # 使用新的、简单的悬浮窗类
    status_overlay = SimpleStatusOverlay()
    status_overlay.start()
    initial_status_text = "运行中" if is_running else "已暂停"
    # 延迟一点确保窗口创建后再更新文本
    time.sleep(0.6)
    status_overlay.update_status(f"状态: {initial_status_text} ")

    # --- 打印初始配置信息 (保持不变) ---
    print("\n自动化脚本启动 (带消息和大厅超时检测, 'k'键切换, 简单置顶悬浮窗)...")
    print(f"目标分辨率: 2560x1440 (请确保游戏在此分辨率下运行)")
    print(f"图像识别置信度: {CONFIDENCE_LEVEL}")
    print(f"状态检测间隔: {CHECK_INTERVAL} 秒")
    print(f"大厅超时时间: {LOBBY_TIMEOUT_SECONDS / 60:.0f} 分钟")
    print(f"消息界面超时时间: {MESSAGE_TIMEOUT_SECONDS / 60:.0f} 分钟")
    print("="*10 + " 使用的坐标 " + "="*10)
    print(f"  返回房间: {RETURN_BTN_ABS_POS}")
    print(f"  再来一局: {PLAY_AGAIN_ABS_POS}")
    print(f"  选人确认: {CONFIRM_BTN_POS}")
    print(f"  消息点击: {MESSAGE_CLICK_POS}")
    print(f"  英雄1: {HERO_MAIN_POS}")
    print("="*10 + " 需要的图片文件 " + "="*10)
    print(f"  - {END_GAME_PANEL_IMG} (游戏结束)")
    print(f"  - {PLAY_AGAIN_BTN_IMG} (大厅)")
    print(f"  - {HERO_SELECT_SCREEN_IMG} (选人)")
    print(f"  - {MESSAGE_IMG} (消息)")
    print("!!! 请确保图片准确截取并与脚本同目录 !!!")
    print("="*30)
    if not is_running: print("脚本默认启动时处于 [暂停] 状态。")
    print("请在 3 秒内切换到游戏窗口...")
    print("按 'k' 键 [开始/暂停] 脚本。")
    print("在终端窗口按 Ctrl+C 可以强制停止脚本。")
    print("注意：状态悬浮窗会遮挡其下方区域。")

    # 确保悬浮窗初始状态文本设置成功
    if status_overlay:
         overlay_text = "状态: 运行中 " if is_running else "状态: 已暂停 "
         status_overlay.update_status(overlay_text)
    time.sleep(3)

    # --- 初始化主循环变量 (保持不变) ---
    last_check_time = time.time()
    consecutive_state_check_failures = 0
    in_lobby_since = None
    in_message_since = None
    exit_reason = "未知原因"

    # --- 主循环 (保持不变) ---
    try:
        while not script_needs_to_exit:
            if not is_running:
                time.sleep(0.1); last_check_time = time.time()
                in_lobby_since, in_message_since = None, None; continue

            now = time.time(); action_taken_this_cycle = False; current_state_detected = False

            if now >= last_check_time + CHECK_INTERVAL:
                print(f"\n--- {time.strftime('%H:%M:%S')} 检查点 ---"); last_check_time = now
                print("状态检测:")

                # 1. 游戏结束?
                print(f"  1. 检测结束 ({END_GAME_PANEL_IMG})...", end="")
                if find_image(END_GAME_PANEL_IMG):
                    print("是"); current_state_detected = True
                    if back_to_lobby(): action_taken_this_cycle = True
                    in_lobby_since, in_message_since, consecutive_state_check_failures = None, None, 0
                else: print("否")

                # 2. 大厅?
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  2. 检测大厅 ({PLAY_AGAIN_BTN_IMG})...", end="")
                    if find_image(PLAY_AGAIN_BTN_IMG, max_wait=1):
                        print("是"); current_state_detected = True; in_message_since = None; consecutive_state_check_failures = 0
                        if in_lobby_since is None: print("    首次检测到, 启动计时."); in_lobby_since = now
                        else:
                            elapsed = now - in_lobby_since; print(f"    停留 {elapsed:.0f}s.")
                            if elapsed > LOBBY_TIMEOUT_SECONDS: exit_reason = f"大厅超时"; print(f"!!!!!! {exit_reason} !!!!!!"); script_needs_to_exit = True
                        if not script_needs_to_exit and attempt_start_new_game(): print("    尝试开局."); action_taken_this_cycle = True; in_lobby_since = None
                        elif not script_needs_to_exit: print("    开局失败/中断.")
                    else:
                        print("否");
                        if in_lobby_since is not None: print("    离开大厅, 重置计时."); in_lobby_since = None

                # 3. 选人?
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  3. 检测选人 ({HERO_SELECT_SCREEN_IMG})...", end="")
                    if find_image(HERO_SELECT_SCREEN_IMG):
                        print("是"); current_state_detected = True; in_lobby_since, in_message_since, consecutive_state_check_failures = None, None, 0
                        if select_hero(): action_taken_this_cycle = True
                    else: print("否")

                # 4. 消息?
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  4. 检测消息 ({MESSAGE_IMG})...", end="")
                    if find_image(MESSAGE_IMG, max_wait=1):
                        print("是"); current_state_detected = True; in_lobby_since = None; consecutive_state_check_failures = 0
                        if in_message_since is None: print("    首次检测到, 启动计时."); in_message_since = now
                        else:
                            elapsed = now - in_message_since; print(f"    停留 {elapsed:.0f}s.")
                            if elapsed > MESSAGE_TIMEOUT_SECONDS: exit_reason = f"消息超时"; print(f"!!!!!! {exit_reason} !!!!!!"); script_needs_to_exit = True
                        if not script_needs_to_exit and handle_message(): print("    尝试处理."); action_taken_this_cycle = True; in_message_since = None
                        elif not script_needs_to_exit: print("    处理失败/中断.")
                    else:
                         print("否");
                         if in_message_since is not None: print("    离开消息, 重置计时."); in_message_since = None

                # 总结
                print("检测结束.")
                if not current_state_detected:
                    print("总结: 未知状态(游戏中?)."); consecutive_state_check_failures += 1
                    if consecutive_state_check_failures > (3600 // CHECK_INTERVAL): print(f"警告: 连续{consecutive_state_check_failures * CHECK_INTERVAL / 60 :.0f}分钟未知状态!")
                    in_lobby_since, in_message_since = None, None
                elif action_taken_this_cycle: print("总结: 已处理状态."); consecutive_state_check_failures = 0
                else: print("总结: 识别状态但未处理."); consecutive_state_check_failures = 0
                print(f"--- 检查完毕 ---")

            # 游戏内移动逻辑
            elif not action_taken_this_cycle and time.time() > last_check_time + 1.0:
                 if in_lobby_since is None and in_message_since is None:
                     wasd_move(duration=INGAME_MOVE_DURATION)
                     controlled_sleep(random.uniform(0.2, 0.5))

            if is_running: time.sleep(0.05)

    # --- 异常处理 (保持不变) ---
    except KeyboardInterrupt: exit_reason = "用户中断 (Ctrl+C)"; print(f"\n脚本被{exit_reason}。"); script_needs_to_exit = True
    except SystemExit: print(f"脚本因 {exit_reason} 而系统性停止。"); script_needs_to_exit = True
    except Exception as e: exit_reason = "发生未处理的致命错误"; print(f"\n{exit_reason}，脚本将终止: {e}"); traceback.print_exc(); script_needs_to_exit = True
    # --- 清理工作 (保持不变) ---
    finally:
        print("="*30); print("开始清理资源..."); script_needs_to_exit = True
        if status_overlay: print("正在关闭状态悬浮窗..."); status_overlay.close()
        try: keyboard.unhook_all_hotkeys(); print("已移除键盘热键监听。")
        except Exception as e: print(f"移除热键监听时出错: {e}")
        print("尝试松开常用按键...");
        for key in ['w', 'a', 's', 'd', 'shift', 'ctrl', 'alt']:
             try: pyautogui.keyUp(key)
             except Exception: pass
        print(f"自动化脚本已结束。退出原因: {exit_reason}"); print("="*30)
