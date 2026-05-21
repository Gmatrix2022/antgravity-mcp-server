import threading
import queue
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger("ag_mcp.ui")

class MessagePopupManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MessagePopupManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.msg_queue = queue.Queue()
        self.messages = []
        self.current_index = -1
        self.thread = None
        self.root = None

    def start_ui_thread(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_ui, daemon=True)
            self.thread.start()

    def add_message(self, message: str):
        self.msg_queue.put(message)
        self.start_ui_thread()

    def _run_ui(self):
        try:
            self.root = tk.Tk()
            self.root.title("Anti Gravity 桌面消息")
            self.root.geometry("500x300")
            self.root.attributes("-topmost", True)  # 保持窗口在最前
            
            # 窗口置中
            window_width = 500
            window_height = 300
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
            
            # 配置样式
            style = ttk.Style()
            style.theme_use('clam')
            
            # 主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 顶部信息栏
            top_frame = ttk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.lbl_counter = ttk.Label(top_frame, text="暂无消息", font=("微软雅黑", 10, "bold"))
            self.lbl_counter.pack(side=tk.LEFT)
            
            # 文本显示区
            self.text_area = tk.Text(main_frame, wrap=tk.WORD, font=("微软雅黑", 10), bg="#f8f9fa", relief=tk.FLAT)
            self.text_area.pack(fill=tk.BOTH, expand=True)
            self.text_area.insert(tk.END, "等待消息输入...")
            self.text_area.config(state=tk.DISABLED)
            
            # 底部按钮区
            bottom_frame = ttk.Frame(main_frame)
            bottom_frame.pack(fill=tk.X, pady=(10, 0))
            
            self.btn_prev = ttk.Button(bottom_frame, text="◀ 上一条", command=self._show_prev, state=tk.DISABLED)
            self.btn_prev.pack(side=tk.LEFT, padx=5)
            
            self.btn_next = ttk.Button(bottom_frame, text="下一条 ▶", command=self._show_next, state=tk.DISABLED)
            self.btn_next.pack(side=tk.RIGHT, padx=5)
            
            # 启动定期检查队列的定时器
            self.root.after(100, self._check_queue)
            
            self.root.mainloop()
        except Exception as e:
            logger.error(f"UI Thread Exception: {e}")
            
    def _check_queue(self):
        new_msgs = False
        while not self.msg_queue.empty():
            try:
                msg = self.msg_queue.get_nowait()
                self.messages.append(msg)
                new_msgs = True
            except queue.Empty:
                break
                
        if new_msgs:
            # 自动跳到最新一条消息
            self.current_index = len(self.messages) - 1
            self._update_display()
            # 唤醒窗口到前台
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after_idle(self.root.attributes, "-topmost", False)
            
        # 继续循环检查
        self.root.after(100, self._check_queue)
        
    def _update_display(self):
        if not self.messages:
            return
            
        # 更新文本
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.messages[self.current_index])
        self.text_area.config(state=tk.DISABLED)
        
        # 更新计数器
        self.lbl_counter.config(text=f"消息 {self.current_index + 1} / {len(self.messages)}")
        
        # 更新按钮状态
        if self.current_index > 0:
            self.btn_prev.config(state=tk.NORMAL)
        else:
            self.btn_prev.config(state=tk.DISABLED)
            
        if self.current_index < len(self.messages) - 1:
            self.btn_next.config(state=tk.NORMAL)
        else:
            self.btn_next.config(state=tk.DISABLED)

    def _show_prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
            
    def _show_next(self):
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            self._update_display()


# 暴露给 MCP 的工具函数
async def ag_popup_message(message: str) -> str:
    import json
    try:
        manager = MessagePopupManager()
        manager.add_message(message)
        return json.dumps({
            "ok": True, 
            "status": "Message pushed to UI queue successfully"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "ok": False, 
            "error": str(e)
        }, ensure_ascii=False)
