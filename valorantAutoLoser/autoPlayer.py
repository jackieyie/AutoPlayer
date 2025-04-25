# -*- coding: utf-8 -*- # <--- 确保Python能正确处理UTF-8字符（中文注释）

import pyautogui
import time
import random
import sys
import traceback      # 用于打印详细的错误信息
import keyboard       # 用于全局热键监听 (需要 pip install keyboard)
import threading      # 用于将悬浮窗放入单独的线程，防止阻塞主程序
import tkinter as tk  # Python内置的GUI库，用于创建悬浮窗
# import ctypes         # 不再需要 ctypes
import platform       # 用于检测操作系统类型

# === 新增导入 ===
import os
from datetime import datetime, timedelta
import pyperclip # <--- 确保导入了 pyperclip

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
HERO_MAIN_POS = (113, 468)
HERO_ALT_POS = (241, 462)
HERO_THREE_POS = (379, 457)
HERO_FOUR_POS =(517, 461)
HERO_FIVE_POS =(111, 594)

# 其他坐标 (需要你自己校准)
CONFIRM_BTN_POS = (1266, 1018)
PLAY_AGAIN_ABS_POS = (1226, 1306)
MESSAGE_CLICK_POS = (1278, 948) # 这个坐标现在主要用于 handle_message 函数，不再用于定时发送消息的激活
CHEAT_HANDLER_POS = (1275, 1222)
ERROR_HANDLER_POS = (1275, 824)

# !!! 超时设置 !!!
LOBBY_TIMEOUT_SECONDS = 3600
MESSAGE_TIMEOUT_SECONDS = 3600

# 移动参数
INGAME_MOVE_DURATION = 1.5

# 超时设置 (图像查找)
STATE_CHECK_TIMEOUT = 2

# === 时间间隔检测相关常量 ===
TIME_CHECK_FILE = "last_wasd_check_time.txt"
# --- 在这里修改时间间隔 ---
# 修改下面这个值来调整发送消息的时间间隔（单位：分钟）
TIME_CHECK_INTERVAL_MINUTES = 10
# -------------------------
# 要发送的消息
MESSAGE_TO_SEND = "哔站关注吕振洪"

# --- 全局状态变量 ---
is_running = False
script_needs_to_exit = False
status_overlay = None # 指向状态悬浮窗对象的全局变量

# --- 简单的置顶状态悬浮窗类 (SimpleStatusOverlay) ---
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
                    pass # 忽略窗口已销毁的错误
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
        else: # 如果窗口不存在了，也停止更新
            self._stop_event.set()


    def start(self):
        """启动悬浮窗线程"""
        if self.thread is None or not self.thread.is_alive():
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._overlay_thread_target, daemon=True)
            self.thread.start()
            print("状态悬浮窗: 正在启动线程...")
            time.sleep(0.5) # 短暂等待线程启动

    def update_status(self, text):
        """线程安全地更新悬浮窗显示的文本"""
        self._text_to_set = text

    def close(self):
        """请求关闭悬浮窗线程"""
        print("状态悬浮窗: 请求关闭。")
        self._stop_event.set()
        if self.thread and self.thread.is_alive():
             print("状态悬浮窗: 等待线程结束...")
             self.thread.join(timeout=2.0) # 等待最多2秒
             if self.thread.is_alive():
                 print("状态悬浮窗: 警告 - 线程未能正常结束。")
        self.thread = None
        print("状态悬浮窗: 已关闭。")


# === 时间处理函数 ===
def get_last_execution_time(filename=TIME_CHECK_FILE):
    """
    获取上次记录的时间。如果文件不存在或格式错误，返回 None。
    """
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding='utf-8') as file: # 指定utf-8编码
                last_execution_time_str = file.read().strip()
                return datetime.strptime(last_execution_time_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, IOError) as e:
            print(f"[时间检查] 读取时间文件 '{filename}' 时出错: {e}")
            return None
    else:
        return None

def set_last_execution_time(filename=TIME_CHECK_FILE):
    """
    设置当前时间为上次记录时间。
    """
    current_time = datetime.now()
    try:
        with open(filename, "w", encoding='utf-8') as file: # 指定utf-8编码
            file.write(current_time.strftime("%Y-%m-%d %H:%M:%S"))
        print(f"[时间检查] 已更新时间记录文件 '{filename}' 为: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except IOError as e:
        print(f"[时间检查] 写入时间文件 '{filename}' 时出错: {e}")


# === 修改后的发送消息函数 (使用回车激活) ===
def send_text_via_clipboard(text: str, enter_press_delay: float = 1.0, pre_paste_delay: float = 0.5, enter_after_paste: bool = True):
    """
    通过按回车键激活聊天输入框，然后将文本复制到剪贴板并通过 Ctrl+V 粘贴发送。
    Args:
        text: 要发送的文本.
        enter_press_delay: 按下回车后等待聊天框响应的时间（秒）.
        pre_paste_delay: 粘贴前额外等待的时间（秒）.
        enter_after_paste: 是否在粘贴后按下 Enter 键发送消息.
    Returns:
        bool: 发送成功返回 True，失败返回 False.
    """
    original_clipboard = "Error: Clipboard not saved" # 设定一个默认值
    try:
        print(f"[消息发送] 准备发送: '{text}'")

        # 1. 按回车激活输入框
        print(f"[消息发送] 按下 Enter 键以激活聊天输入框...")
        pyautogui.press('enter')
        # 使用 controlled_sleep 以便响应暂停/退出
        print(f"[消息发送] 等待 {enter_press_delay} 秒让聊天框响应...")
        if not controlled_sleep(enter_press_delay):
            print("[消息发送] 在等待聊天框响应时脚本暂停或退出，取消发送。")
            return False # 返回失败

        # (可选) 粘贴前额外等待
        if pre_paste_delay > 0:
            print(f"[消息发送] 额外等待 {pre_paste_delay} 秒，准备粘贴...")
            if not controlled_sleep(pre_paste_delay):
                 print("[消息发送] 在粘贴前等待时脚本暂停或退出，取消发送。")
                 return False # 返回失败

        # 2. 复制和粘贴
        original_clipboard = pyperclip.paste() # 保存原始剪贴板内容
        pyperclip.copy(text)
        time.sleep(0.1) # 短暂等待确保复制操作完成

        print("[消息发送] 执行粘贴 (Ctrl+V)...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2) # 稍长一点的等待，确保粘贴完成

        # 3. (可选) 按下 Enter 发送
        if enter_after_paste:
            print("[消息发送] 按下 Enter 发送...")
            pyautogui.press('enter')
            print("[消息发送] 已发送 (带回车)")
        else:
             print("[消息发送] 已粘贴 (无回车)")

        # 4. 恢复剪贴板
        # 延时一下再恢复，防止干扰下一次输入（如果游戏反应慢）
        time.sleep(0.1)
        pyperclip.copy(original_clipboard)
        print("[消息发送] 原始剪贴板内容已恢复。")
        return True # 返回成功

    except Exception as e:
        print(f"[消息发送] 发送时出错: {e}")
        traceback.print_exc()
        # 尝试恢复剪贴板
        try:
            if original_clipboard != "Error: Clipboard not saved":
                 pyperclip.copy(original_clipboard)
                 print("[消息发送] 尝试恢复剪贴板内容。")
        except Exception as clip_err:
             print(f"[消息发送] 恢复剪贴板时也发生错误: {clip_err}")
        return False # 返回失败


# === 修改后的检查时间间隔并发送消息的函数 ===
def check_time_interval_and_send_message():
    """
    检查距离上次记录的时间是否超过指定间隔。
    如果超过间隔或首次执行，则更新记录时间，并尝试通过按回车激活聊天框来发送指定消息。
    """
    print("-" * 10 + "[时间间隔检查开始]" + "-" * 10)
    last_execution_time = get_last_execution_time()
    interval_seconds = TIME_CHECK_INTERVAL_MINUTES * 60
    should_send_message = False # 标记是否满足发送条件

    # --- 时间检查逻辑 ---
    if last_execution_time:
        time_since_last = datetime.now() - last_execution_time
        print(f"[时间检查] 上次记录时间: {last_execution_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[时间检查] 当前时间:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[时间检查] 已过时间:     {time_since_last}")
        print(f"[时间检查] 间隔阈值:     {timedelta(seconds=interval_seconds)} ({TIME_CHECK_INTERVAL_MINUTES} 分钟)")
        if time_since_last >= timedelta(seconds=interval_seconds):
            print(f"[时间检查] >> 条件满足: 已超过 {TIME_CHECK_INTERVAL_MINUTES} 分钟。")
            should_send_message = True
        else:
            remaining_time = timedelta(seconds=interval_seconds) - time_since_last
            minutes, seconds = divmod(remaining_time.total_seconds(), 60)
            print(f"[时间检查] >> 条件不满足: 距离上次记录时间不足 {TIME_CHECK_INTERVAL_MINUTES} 分钟。")
            print(f"[时间检查]    还需要等待大约 {int(minutes)} 分钟 {int(seconds)} 秒。")
    else:
        print("[时间检查] 未找到上次执行时间记录 (可能是首次运行或文件丢失)。")
        should_send_message = True # 首次运行时也满足发送条件

    # --- 如果满足条件，尝试发送消息 ---
    if should_send_message:
        print(f"[时间检查] 条件满足，尝试发送消息: '{MESSAGE_TO_SEND}' (通过按 Enter 激活)")
        # 调用修改后的发送函数
        if send_text_via_clipboard(MESSAGE_TO_SEND):
             print("[时间检查] 消息发送成功。")
             print("[时间检查] 正在更新时间记录...")
             set_last_execution_time() # 发送成功后才更新时间记录
        else:
             print("[时间检查] 消息发送失败。本次将不会更新时间记录。")
             # 如果发送失败，不更新时间，下次还会尝试发送

    print("-" * 10 + "[时间间隔检查结束]" + "-" * 10)


# --- 核心功能函数 ---
def find_image(image_path, confidence=CONFIDENCE_LEVEL, max_wait=STATE_CHECK_TIMEOUT):
    """查找屏幕上的图片，支持超时和脚本状态检查"""
    start_time = time.time()
    while True:
        if script_needs_to_exit: return None
        if not is_running:
            # 如果暂停，短暂休眠并重置开始时间，避免暂停时间计入超时
            time.sleep(0.1)
            start_time = time.time()
            continue
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                # print(f"找到图片 '{image_path}' at {location}")
                return location
        except pyautogui.ImageNotFoundException:
            pass # 图片未找到是正常情况
        except Exception as e:
            # 打印其他可能的异常，如权限问题或图像库错误
            # print(f"查找图片 '{image_path}' 时发生异常: {e}")
            pass # 暂时忽略查找过程中的其他错误
        # 检查是否超时
        if time.time() - start_time > max_wait:
            # print(f"查找图片 '{image_path}' 超时 ({max_wait}s)")
            return None
        # 短暂休眠，避免CPU占用过高
        time.sleep(0.1)

def controlled_sleep(duration):
    """
    可控的休眠函数，响应暂停(is_running)和退出(script_needs_to_exit)信号。
    Args:
        duration: 要休眠的总秒数.
    Returns:
        bool: 如果休眠正常完成返回 True，如果因暂停或退出信号中断返回 False.
    """
    end_time = time.time() + duration
    while time.time() < end_time:
        if script_needs_to_exit: return False # 检测到退出信号，立即返回 False
        if not is_running:
            # 如果脚本暂停，进入内部循环等待恢复
            print("[暂停中] controlled_sleep 检测到暂停，等待恢复...")
            while not is_running:
                 if script_needs_to_exit: return False # 暂停期间也检查退出信号
                 time.sleep(0.1) # 短暂休眠
            # 恢复运行后，需要重新计算剩余时间，可能已经超时
            print("[恢复运行] controlled_sleep 检测到恢复。")
            # 因为暂停可能持续很久，重新检查是否已超时
            if time.time() >= end_time:
                 break # 如果恢复时已经超时，则结束外部循环
            else:
                 # 更新 end_time 是错误的，应该保持原始的结束时间
                 # 只需要继续外部循环即可
                 pass
        # 计算下一次检查的时间间隔，最多0.1秒，但不超过剩余时间
        check_interval = min(0.1, end_time - time.time())
        if check_interval <= 0:
            break # 剩余时间不足，结束循环
        time.sleep(check_interval) # 休眠一小段时间
    # 循环结束后，再次检查是否是因为退出信号导致的（虽然理论上内部循环会处理）
    return not script_needs_to_exit


# --- WASD 移动函数 (已修复语法错误) ---
def wasd_move(duration=INGAME_MOVE_DURATION):
    """
    执行 WASD 移动和固定点击逻辑，
    然后在函数结束前执行时间间隔检查并尝试发送消息。
    """
    if duration <= 0:
        print("[WASD移动] 持续时间为 0 或负数，跳过移动。")
        # 如果不移动，根据需要决定是否仍要检查时间
        # if is_running and not script_needs_to_exit:
        #     check_time_interval_and_send_message()
        return

    keys = ['w', 'a', 's', 'd']
    end_time = time.time() + duration
    active_key = None
    original_move_completed = False # 标记移动循环是否自然结束

    print(f"[WASD移动] 开始模拟 WASD 移动，持续 {duration:.1f} 秒...")
    try:
        # --- 移动循环 ---
        while time.time() < end_time:
            if not is_running or script_needs_to_exit:
                print("[WASD移动] 脚本暂停或退出，中断移动循环。")
                break # 退出移动循环

            remaining_time = end_time - time.time()
            if remaining_time <= 0:
                break # 剩余时间不足，理论上不应发生，但作为保险

            # 先松开当前按下的键 (如果上一次循环有按下)
            if active_key:
                pyautogui.keyUp(active_key)
                # print(f"[WASD移动] 松开 {active_key}")
                active_key = None
                # 松开后短暂间隔，避免立即重新按下相同按键（虽然随机选择）
                if not controlled_sleep(0.05): break # 响应暂停/退出

            # 随机选择一个键按下
            key = random.choice(keys)
            # 计算按键时间
            press_time = random.uniform(0.2, min(0.8, remaining_time - 0.1 if remaining_time > 0.1 else 0.05))
            if press_time <= 0:
                 # 如果计算出的时间无效，短暂休眠后继续
                 if not controlled_sleep(0.1): break
                 continue

            # 按下按键
            pyautogui.keyDown(key)
            active_key = key
            # print(f"[WASD移动] 按下 {key} 持续 {press_time:.2f} 秒")

            # 按住一段时间
            if not controlled_sleep(press_time):
                print("[WASD移动] 在按键期间脚本暂停或退出。")
                break # controlled_sleep 返回 False 表示被中断

            # 按键时间结束后，松开按键
            # 检查是否是最后一次按键时间结束时超时了
            if time.time() < end_time:
                 # 时间未到，正常松开键，准备下一次循环或空闲等待
                 # print(f"[WASD移动] 松开 {key}")
                 pyautogui.keyUp(active_key)
                 active_key = None
            else:
                 # 时间到了或超过了，结束循环
                 if active_key: # 如果有键还按着，先松开
                     # print(f"[WASD移动] 时间到，松开 {key}")
                     pyautogui.keyUp(active_key)
                     active_key = None # 设为 None
                 # 跳出 while 循环，不再执行后续的空闲等待
                 break

            # 在两次按键之间添加一个小的随机间隔
            idle_time = random.uniform(0.1, 0.3)
            if time.time() + idle_time < end_time:
                # print(f"[WASD移动] 空闲等待 {idle_time:.2f} 秒")
                if not controlled_sleep(idle_time):
                    print("[WASD移动] 在空闲期间脚本暂停或退出。")
                    break # controlled_sleep 返回 False 表示被中断
            # else:
                # 剩余时间不足以进行完整的空闲等待，直接进入下一次循环（或结束）
                # pass

        # 检查循环是否是正常完成 (而不是 break 跳出)
        # 额外检查 active_key 是否为 None，确保最后一次按键已释放
        if time.time() >= end_time and active_key is None and is_running and not script_needs_to_exit:
             original_move_completed = True

        # --- 固定点击逻辑 ---
        # 只有在移动部分正常完成且脚本在运行时才执行
        if original_move_completed:
            print("[WASD移动] 移动完成，执行固定的点击序列...")
            try:
                # 每次点击前都检查状态
                if not is_running or script_needs_to_exit: raise Exception("Script stopped before RETURN click")
                pyautogui.click(RETURN_BTN_ABS_POS);
                if not controlled_sleep(1): raise Exception("Script stopped after RETURN click")

                if not is_running or script_needs_to_exit: raise Exception("Script stopped before PLAY_AGAIN click")
                pyautogui.click(PLAY_AGAIN_ABS_POS);
                if not controlled_sleep(1): raise Exception("Script stopped after PLAY_AGAIN click")

                if not is_running or script_needs_to_exit: raise Exception("Script stopped before MESSAGE click")
                pyautogui.click(MESSAGE_CLICK_POS);
                if not controlled_sleep(1): raise Exception("Script stopped after MESSAGE click")

                if not is_running or script_needs_to_exit: raise Exception("Script stopped before ERROR click")
                pyautogui.click(ERROR_HANDLER_POS);
                if not controlled_sleep(1): raise Exception("Script stopped after ERROR click")

                if not is_running or script_needs_to_exit: raise Exception("Script stopped before CHEAT click")
                pyautogui.click(CHEAT_HANDLER_POS);
                if not controlled_sleep(20): raise Exception("Script stopped during CHEAT wait") # 长延时
                print("[WASD移动] 固定点击序列结束。")

            except Exception as click_e:
                 # 如果在点击序列中脚本被停止或发生错误
                 print(f"[WASD移动] 固定点击序列被中断或出错: {click_e}")
                 # 无需额外操作，finally会处理按键释放

        elif not is_running or script_needs_to_exit :
             # 如果是因为脚本暂停或退出导致没完成移动，也跳过点击
             print("[WASD移动] 脚本已暂停或退出，跳过固定点击序列。")
        else: # 移动循环因为 break 跳出，但脚本仍在运行
            print("[WASD移动] 移动循环未正常完成(可能被中断)，跳过固定点击序列。")


    except Exception as e:
        print(f"[WASD移动] 模拟移动或点击时发生未预料的错误: {e}")
        traceback.print_exc() # 需要调试时取消注释
    finally:
        # --- 清理按键 ---
        # 确保无论如何，最终都尝试松开可能按下的键
        if active_key:
            try:
                pyautogui.keyUp(active_key)
                print(f"[WASD移动] Finally: 确保松开按键 {active_key}")
            except Exception as keyup_err:
                 print(f"[WASD移动] Finally: 尝试松开按键 {active_key} 时出错: {keyup_err}")
            active_key = None # 重置状态

        # 作为额外的保险，可以尝试松开所有WASD键 (通常不需要，但无害)
        # for k in keys:
        #     try: pyautogui.keyUp(k)
        #     except: pass

        print("[WASD移动] WASD 移动及点击部分执行完毕 (或被中断)。")

        # === 调用检查和发送函数 ===
        # 条件：函数执行到 finally，且脚本仍在运行状态
        if is_running and not script_needs_to_exit:
             check_time_interval_and_send_message() # 调用检查和发送函数
        else:
             print("[时间检查] 脚本已暂停或退出，跳过本次时间间隔检查和消息发送。")
        # =========================================


def back_to_lobby():
    """尝试点击返回房间按钮并等待"""
    print(f"尝试点击返回房间按钮: {RETURN_BTN_ABS_POS}")
    try:
        pyautogui.click(RETURN_BTN_ABS_POS)
        print("已点击。等待返回...")
        # 使用 controlled_sleep 等待随机时间
        if not controlled_sleep(random.uniform(6, 9)):
            print("[返回大厅] 等待期间脚本被暂停或退出。")
            return False
        print("[返回大厅] 等待完成。")
        return True
    except Exception as e:
        print(f"点击 {RETURN_BTN_ABS_POS} 错误: {e}")
        return False

def attempt_start_new_game():
    """尝试点击再来一局按钮并等待"""
    print("准备点击 '再来一局'...")
    try:
        print(f"点击 '再来一局' 坐标: {PLAY_AGAIN_ABS_POS}")
        pyautogui.click(PLAY_AGAIN_ABS_POS)
        print("已点击。等待匹配...")
        # 使用 controlled_sleep 等待随机时间
        if not controlled_sleep(random.uniform(12, 18)):
            print("[开始新局] 等待期间脚本被暂停或退出。")
            return False
        print("[开始新局] 等待完成（可能已进入选人）。")
        return True
    except Exception as e:
        print(f"点击 {PLAY_AGAIN_ABS_POS} 错误: {e}")
        return False

def select_hero():
    """执行选英雄流程，包含多次点击和等待"""
    print("执行选英雄流程...")
    try:
        hero_to_confirm_sleep = 1.2
        confirm_to_hero_sleep = 1.2
        load_game_sleep = 15 # 加载游戏等待时间
        hero_positions = [HERO_MAIN_POS, HERO_ALT_POS, HERO_THREE_POS, HERO_FOUR_POS, HERO_FIVE_POS]
        hero_names = ["主英雄", "备选1", "备选2", "备选3", "备选4"]

        for i in range(len(hero_positions)):
            # 每次循环开始前检查状态
            if script_needs_to_exit or not is_running:
                print("[选英雄] 流程中脚本被暂停或退出。")
                return False

            target_pos = hero_positions[i]
            print(f" - [{i+1}/5] 尝试选择 {hero_names[i]} @ {target_pos}")
            pyautogui.moveTo(target_pos[0], target_pos[1], duration=random.uniform(0.4, 0.8))
            pyautogui.click()

            print(f"   (等待 {hero_to_confirm_sleep:.1f}s)")
            if not controlled_sleep(hero_to_confirm_sleep): return False # 响应暂停/退出

            # 再次检查状态
            if script_needs_to_exit or not is_running: return False

            print(f" - [{i+1}/5] 尝试点击确认 @ {CONFIRM_BTN_POS}")
            pyautogui.moveTo(CONFIRM_BTN_POS[0], CONFIRM_BTN_POS[1], duration=random.uniform(0.4, 0.8))
            pyautogui.click()
            print(f"   (已点击确认)")

            # 如果不是最后一个英雄，等待下次选择
            if i < len(hero_positions) - 1:
                print(f"   (等待 {confirm_to_hero_sleep:.1f}s)")
                if not controlled_sleep(confirm_to_hero_sleep): return False # 响应暂停/退出
            else:
                # 最后一个英雄选完，认为选人阶段结束
                print("[选英雄] 选人流程完成。")

        print(f"等待游戏加载 ({load_game_sleep} 秒)...")
        if not controlled_sleep(load_game_sleep): return False # 响应暂停/退出

        print("[选英雄] 假定游戏已加载完成。")
        return True

    except Exception as e:
        print(f"选英雄流程错误: {e}")
        traceback.print_exc()
        return False

def handle_message():
    """处理消息界面点击（可能只是关闭弹窗）"""
    print("准备点击消息界面（可能用于关闭弹窗）...")
    try:
        print(f"点击坐标: {MESSAGE_CLICK_POS}")
        pyautogui.click(MESSAGE_CLICK_POS)
        print("已点击。")
        # 点击后短暂等待
        if not controlled_sleep(random.uniform(1, 2)):
             print("[处理消息] 等待期间脚本被暂停或退出。")
             return False
        return True
    except Exception as e:
        print(f"点击 {MESSAGE_CLICK_POS} 错误: {e}")
        return False

# --- 热键切换功能 ---
def toggle_script_state():
    """切换脚本的运行/暂停状态，并更新悬浮窗文本"""
    global is_running
    is_running = not is_running
    status_text = "运行中" if is_running else "已暂停"
    print(f"\n--- 脚本状态被 'k' 键切换为: {status_text} ---")
    # 更新悬浮窗显示的文本 (如果悬浮窗存在)
    if status_overlay:
        status_overlay.update_status(f"状态: {status_text} ") # 加空格确保文本变化

# --- 键盘监听器设置 ---
try:
    # 使用 suppress=True 避免热键本身被输入到游戏中
    keyboard.add_hotkey('k', toggle_script_state, suppress=True)
    print("已设置 'k' 键来切换脚本运行/暂停状态。")
except ImportError:
     print("错误：未找到 'keyboard' 库。请运行 'pip install keyboard' 安装。")
     print("脚本将无法使用 'k' 键切换状态，将直接开始运行。")
     is_running = True
except Exception as e:
    print(f"警告：无法设置 'k' 键热键。错误: {e}")
    print("可能原因：\n  - 在 Linux/macOS 上没有使用 root/sudo 权限运行脚本。\n  - 键盘监听库与其他程序冲突。")
    print("脚本将无法通过 'k' 键暂停/启动，将直接开始运行。")
    is_running = True # 如果热键设置失败，默认设为运行状态

# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 创建并启动状态悬浮窗 ---
    print("正在创建状态悬浮窗 (简单置顶版)...")
    status_overlay = SimpleStatusOverlay()
    status_overlay.start()
    # 在启动后稍微等待一下，确保窗口已创建并可以接收更新
    time.sleep(0.8)
    initial_status_text = "运行中" if is_running else "已暂停"
    if status_overlay:
         status_overlay.update_status(f"状态: {initial_status_text} ")

    # --- 打印初始配置信息 ---
    print("\n自动化脚本启动 (带消息和大厅超时检测, 'k'键切换, 简单置顶悬浮窗)...")
    print(f"目标分辨率: 2560x1440 (请确保游戏在此分辨率下运行)")
    print(f"图像识别置信度: {CONFIDENCE_LEVEL}")
    print(f"状态检测间隔: {CHECK_INTERVAL} 秒")
    print(f"大厅超时时间: {LOBBY_TIMEOUT_SECONDS / 60:.0f} 分钟")
    print(f"消息界面超时时间: {MESSAGE_TIMEOUT_SECONDS / 60:.0f} 分钟")
    print(f"[配置] WASD后时间检测间隔: {TIME_CHECK_INTERVAL_MINUTES} 分钟 (使用文件: {TIME_CHECK_FILE})") # 强调是可修改的
    print(f"[配置] 定时发送消息: '{MESSAGE_TO_SEND}' (通过按 Enter 激活聊天框)") # 强调激活方式
    print("="*10 + " 使用的坐标 " + "="*10)
    print(f"  返回房间: {RETURN_BTN_ABS_POS}")
    print(f"  再来一局: {PLAY_AGAIN_ABS_POS}")
    print(f"  选人确认: {CONFIRM_BTN_POS}")
    print(f"  消息点击(处理用): {MESSAGE_CLICK_POS}") # 区分用途
    print(f"  英雄1: {HERO_MAIN_POS}")
    # ... 其他英雄坐标 ...
    print("="*10 + " 需要的图片文件 " + "="*10)
    print(f"  - {END_GAME_PANEL_IMG} (游戏结束)")
    print(f"  - {PLAY_AGAIN_BTN_IMG} (大厅)")
    print(f"  - {HERO_SELECT_SCREEN_IMG} (选人)")
    print(f"  - {MESSAGE_IMG} (消息弹窗)")
    print("!!! 请确保图片准确截取并与脚本同目录 !!!")
    print("="*30)
    if not is_running: print("脚本默认启动时处于 [暂停] 状态。按 'k' 键启动。")
    else: print("脚本已启动运行。按 'k' 键暂停。")
    print("请在 3 秒内切换到游戏窗口...")
    print("在终端窗口按 Ctrl+C 可以强制停止脚本。")

    # 确保悬浮窗初始状态文本设置成功
    if status_overlay:
         overlay_text = "状态: 运行中 " if is_running else "状态: 已暂停 "
         status_overlay.update_status(overlay_text)
    time.sleep(3)

    # --- 初始化主循环变量 ---
    last_check_time = time.time()
    consecutive_state_check_failures = 0
    in_lobby_since = None
    in_message_since = None
    exit_reason = "正常退出（或未知）" # 初始退出原因

    # --- 主循环 ---
    try:
        while not script_needs_to_exit:
            # --- 暂停处理 ---
            if not is_running:
                # 在暂停状态下，重置计时器和状态检测失败计数器，避免暂停期间累积
                time.sleep(0.1) # 降低暂停时的CPU占用
                # 更新检查时间，避免暂停后立刻因时间差过大而检查
                last_check_time = time.time()
                # 重置可能正在进行的超时计时
                in_lobby_since, in_message_since = None, None
                consecutive_state_check_failures = 0
                continue # 跳过当前循环的剩余部分

            # --- 运行状态下的逻辑 ---
            now = time.time()
            action_taken_this_cycle = False # 标记本轮检查是否已执行了主要状态处理动作
            current_state_detected = False # 标记本轮是否检测到了任何已知状态

            # --- 状态检测逻辑 (基于 CHECK_INTERVAL) ---
            if now >= last_check_time + CHECK_INTERVAL:
                print(f"\n--- {time.strftime('%H:%M:%S')} 检查点 ({CHECK_INTERVAL}s 间隔) ---")
                last_check_time = now # 更新检查时间戳
                print("状态检测:")
                status_overlay.update_status("状态: 检测中 ") if status_overlay else None # 更新悬浮窗

                # 1. 游戏结束?
                print(f"  1. 检测游戏结束 ({END_GAME_PANEL_IMG})...", end="")
                if find_image(END_GAME_PANEL_IMG):
                    print("是"); current_state_detected = True; status_overlay.update_status("状态: 游戏结束 ") if status_overlay else None
                    if back_to_lobby():
                        print("    已尝试返回大厅。")
                        action_taken_this_cycle = True
                        # 重置所有计时器和失败计数
                        in_lobby_since, in_message_since = None, None
                        consecutive_state_check_failures = 0
                    else:
                        print("    返回大厅失败/中断。")
                else: print("否")

                # 2. 大厅? (仅在未执行其他动作时检查)
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  2. 检测大厅 ({PLAY_AGAIN_BTN_IMG})...", end="")
                    if find_image(PLAY_AGAIN_BTN_IMG, max_wait=1): # 快速检测大厅
                        print("是"); current_state_detected = True; status_overlay.update_status("状态: 在大厅 ") if status_overlay else None
                        # 重置消息计时和失败计数
                        in_message_since = None; consecutive_state_check_failures = 0
                        # 处理大厅超时
                        if in_lobby_since is None: print("    首次检测到大厅, 启动大厅计时."); in_lobby_since = now
                        else:
                            elapsed = now - in_lobby_since; print(f"    停留大厅 {elapsed:.0f}s / {LOBBY_TIMEOUT_SECONDS}s.")
                            if elapsed > LOBBY_TIMEOUT_SECONDS: exit_reason = f"大厅超时({LOBBY_TIMEOUT_SECONDS}s)"; print(f"!!!!!! {exit_reason} !!!!!!"); script_needs_to_exit = True; continue # 超时则直接退出循环
                        # 尝试开始新游戏
                        if not script_needs_to_exit:
                             if attempt_start_new_game():
                                 print("    尝试开局成功。"); action_taken_this_cycle = True; in_lobby_since = None # 开局成功，重置大厅计时
                             else:
                                 print("    开局失败/中断。")
                    else:
                        print("否")
                        # 如果之前在大厅，现在不在了，重置计时
                        if in_lobby_since is not None: print("    离开大厅, 重置大厅计时."); in_lobby_since = None

                # 3. 选人? (仅在未执行其他动作时检查)
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  3. 检测选人 ({HERO_SELECT_SCREEN_IMG})...", end="")
                    if find_image(HERO_SELECT_SCREEN_IMG):
                        print("是"); current_state_detected = True; status_overlay.update_status("状态: 选英雄 ") if status_overlay else None
                        # 重置所有计时器和失败计数
                        in_lobby_since, in_message_since = None, None; consecutive_state_check_failures = 0
                        if select_hero():
                            print("    选人流程执行完毕。"); action_taken_this_cycle = True
                        else:
                            print("    选人失败/中断。")
                    else: print("否")

                # 4. 消息弹窗? (仅在未执行其他动作时检查)
                if not action_taken_this_cycle and is_running and not script_needs_to_exit:
                    print(f"  4. 检测消息弹窗 ({MESSAGE_IMG})...", end="")
                    if find_image(MESSAGE_IMG, max_wait=1): # 快速检测消息
                        print("是"); current_state_detected = True; status_overlay.update_status("状态: 有消息 ") if status_overlay else None
                        # 重置大厅计时和失败计数
                        in_lobby_since = None; consecutive_state_check_failures = 0
                        # 处理消息超时
                        if in_message_since is None: print("    首次检测到消息, 启动消息计时."); in_message_since = now
                        else:
                            elapsed = now - in_message_since; print(f"    停留消息界面 {elapsed:.0f}s / {MESSAGE_TIMEOUT_SECONDS}s.")
                            if elapsed > MESSAGE_TIMEOUT_SECONDS: exit_reason = f"消息界面超时({MESSAGE_TIMEOUT_SECONDS}s)"; print(f"!!!!!! {exit_reason} !!!!!!"); script_needs_to_exit = True; continue # 超时则直接退出循环
                        # 尝试处理消息（点击）
                        if not script_needs_to_exit:
                            if handle_message():
                                print("    尝试处理消息点击成功。"); action_taken_this_cycle = True; in_message_since = None # 处理成功，重置消息计时
                            else:
                                print("    处理消息点击失败/中断。")
                    else:
                        print("否")
                        # 如果之前在消息界面，现在不在了，重置计时
                        if in_message_since is not None: print("    离开消息界面, 重置消息计时."); in_message_since = None

                # --- 状态检测总结 ---
                print("状态检测结束.")
                if not current_state_detected:
                    # 只有在确实没有检测到任何已知状态时，才认为是“未知状态”（可能在游戏中）
                    print("总结: 未检测到明确状态 (可能在游戏中)。")
                    status_overlay.update_status("状态: 游戏中? ") if status_overlay else None
                    consecutive_state_check_failures += 1
                    print(f"    连续未识别状态次数: {consecutive_state_check_failures}")
                    # 连续多次未识别，增加警告，或设置退出逻辑
                    if consecutive_state_check_failures > (LOBBY_TIMEOUT_SECONDS // CHECK_INTERVAL): # 例如用大厅超时作为阈值
                        exit_reason = f"连续 {consecutive_state_check_failures * CHECK_INTERVAL / 60 :.0f} 分钟未识别明确状态"
                        print(f"!!!!!! {exit_reason}, 脚本将退出 !!!!!!"); script_needs_to_exit = True; continue
                    # 只要是未知状态，就重置大厅和消息的计时器，因为我们假定在游戏中
                    in_lobby_since, in_message_since = None, None
                elif action_taken_this_cycle:
                    print("总结: 已识别并处理状态。")
                    consecutive_state_check_failures = 0 # 成功处理，重置失败计数
                else:
                    # 检测到了状态，但处理失败或无需处理（例如超时判断中）
                    print("总结: 已识别状态但未成功处理或无需处理。")
                    # 这里不重置 consecutive_state_check_failures，因为虽然识别了，但可能卡在某个状态的处理流程中
                print(f"--- 检查完毕 ({time.strftime('%H:%M:%S')}) ---")
                # 更新悬浮窗为运行中（如果之前是检测中）
                if status_overlay and status_overlay._text_to_set == "状态: 检测中 ":
                    status_overlay.update_status("状态: 运行中 ")


            # --- 游戏内移动逻辑 ---
            # 条件：脚本在运行 & 本轮状态检查没有执行主要动作 & 不在大厅计时 & 不在消息计时
            # 增加一个小的延迟判断(0.5s)，避免在状态切换（如刚退出大厅）的瞬间错误地执行移动
            elif not action_taken_this_cycle and time.time() > last_check_time + 0.5:
                 # 确认不在任何需要特殊处理的状态（由计时器标记）
                 if in_lobby_since is None and in_message_since is None:
                     # 并且确认最近的状态检测没有识别出任何已知界面 (避免刚退出大厅/消息就移动)
                     if not current_state_detected:
                         # 满足所有条件，执行游戏内移动
                         # print(f"[{time.strftime('%H:%M:%S')}] 执行游戏内移动...") # 可以取消注释以观察
                         wasd_move(duration=INGAME_MOVE_DURATION) # 调用包含时间检查和消息发送的 wasd_move
                         # wasd_move 函数结束后会自行处理时间检查和可能的发送，无需在此处额外操作
                 # else:
                 #     # 正处于大厅或消息计时状态，不执行移动
                 #     # print(f"[{time.strftime('%H:%M:%S')}] 处于大厅或消息计时状态，跳过移动。")
                 #     pass # 短暂休眠避免空转？或者不需要
                 #     time.sleep(0.1)


            # --- 主循环的小延时 ---
            # 减少CPU占用，不需要太快
            time.sleep(0.05) # 50ms

    # --- 异常处理 ---
    except KeyboardInterrupt:
        exit_reason = "用户中断 (Ctrl+C)"
        print(f"\n脚本被 {exit_reason}。")
        script_needs_to_exit = True # 标记需要退出
    except SystemExit:
        # 这个通常是由 script_needs_to_exit = True 间接触发的，或者是代码中显式调用 sys.exit()
        print(f"脚本因 '{exit_reason}' 而系统性停止。")
        # script_needs_to_exit 应该已经是 True 了
    except ImportError as e:
         exit_reason = f"缺少必要的库: {e}"
         print(f"\n错误：{exit_reason}")
         print("请确保已安装所有依赖库 (pyautogui, keyboard, pyperclip)。")
         script_needs_to_exit = True
    except Exception as e:
        exit_reason = "发生未处理的致命错误"
        print(f"\n{exit_reason}，脚本将终止:")
        traceback.print_exc() # 打印详细错误信息
        script_needs_to_exit = True # 标记需要退出

    # --- 清理工作 ---
    finally:
        print("="*30)
        print("开始清理资源...")
        script_needs_to_exit = True # 确保标记为退出状态

        # 关闭状态悬浮窗
        if status_overlay:
            print("正在关闭状态悬浮窗...")
            status_overlay.close()

        # 移除键盘监听
        try:
            # 检查 keyboard 是否成功导入
            if 'keyboard' in sys.modules:
                 keyboard.unhook_all_hotkeys()
                 print("已移除键盘热键监听。")
        except Exception as e:
            print(f"移除热键监听时出错: {e}")

        # 尝试松开常用按键，以防卡住
        print("尝试松开常用按键 (w, a, s, d, ctrl, shift, alt)...")
        for key in ['w', 'a', 's', 'd', 'shift', 'ctrl', 'alt']:
             try:
                 # 检查 pyautogui 是否成功导入
                 if 'pyautogui' in sys.modules:
                     pyautogui.keyUp(key)
             except Exception:
                 pass # 忽略松开按键时的错误

        print(f"自动化脚本已结束。最终退出原因: {exit_reason}")
        print("="*30)
