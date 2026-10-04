import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
from datetime import datetime, timedelta
import time


class ShutdownTimerTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("⏱️ Windows Shutdown Timer")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.shutdown_scheduled = False
        self.remaining_seconds = 0
        self.countdown_thread = None

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """Setup modern styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        bg_color = "#f5f5f5"
        fg_color = "#333333"
        accent_color = "#2196F3"

        self.root.configure(bg=bg_color)

        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground=accent_color)
        style.configure('Status.TLabel', font=('Arial', 12, 'bold'))
        style.configure('TFrame', background=bg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        
        style.configure('Green.TButton', font=('Arial', 11, 'bold'))
        style.configure('Red.TButton', font=('Arial', 11, 'bold'))

    def create_widgets(self):
        """Create main UI elements"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title
        title_label = ttk.Label(main_frame, text="⏱️ Windows Shutdown Timer Pro", 
                               style='Title.TLabel')
        title_label.pack(pady=10)

        # Subtitle
        subtitle_label = ttk.Label(main_frame, text="🔐 Автоматическое управление выключением",
                                  font=('Arial', 9))
        subtitle_label.pack(pady=5)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Tab 1: Quick Timer
        self.create_quick_timer_tab()

        # Tab 2: Schedule
        self.create_schedule_tab()

        # Tab 3: Weekly
        self.create_weekly_tab()

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        self.status_label = ttk.Label(status_frame, text="⏸️ Таймер не установлен",
                                      style='Status.TLabel')
        self.status_label.pack()

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=10)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(button_frame, text="▶️ Запустить",
                                       command=self.start_shutdown)
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.cancel_button = ttk.Button(button_frame, text="⏹️ Отменить",
                                        command=self.cancel_shutdown, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Timer for updates
        self.update_timer()

    def create_quick_timer_tab(self):
        """Create quick timer tab"""
        timer_frame = ttk.Frame(self.notebook)
        self.notebook.add(timer_frame, text="⏱️ Быстрый таймер")

        # Time selection
        time_group = ttk.LabelFrame(timer_frame, text="Выберите время отсчета", padding=10)
        time_group.pack(fill=tk.X, padx=10, pady=10)

        # Hours
        ttk.Label(time_group, text="Часы:").grid(row=0, column=0, padx=5, pady=5)
        self.hours_var = tk.IntVar(value=0)
        hours_spin = ttk.Spinbox(time_group, from_=0, to=23, textvariable=self.hours_var,
                                 width=10, font=('Arial', 11))
        hours_spin.grid(row=0, column=1, padx=5, pady=5)

        # Minutes
        ttk.Label(time_group, text="Минуты:").grid(row=0, column=2, padx=5, pady=5)
        self.minutes_var = tk.IntVar(value=5)
        minutes_spin = ttk.Spinbox(time_group, from_=0, to=59, textvariable=self.minutes_var,
                                   width=10, font=('Arial', 11))
        minutes_spin.grid(row=0, column=3, padx=5, pady=5)

        # Seconds
        ttk.Label(time_group, text="Секунды:").grid(row=0, column=4, padx=5, pady=5)
        self.seconds_var = tk.IntVar(value=0)
        seconds_spin = ttk.Spinbox(time_group, from_=0, to=59, textvariable=self.seconds_var,
                                   width=10, font=('Arial', 11))
        seconds_spin.grid(row=0, column=5, padx=5, pady=5)

        # Action selection
        action_group = ttk.LabelFrame(timer_frame, text="Действие", padding=10)
        action_group.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(action_group, text="Выполнить:").pack(side=tk.LEFT, padx=5)
        self.quick_action_var = tk.StringVar(value="Выключить ПК")
        action_combo = ttk.Combobox(action_group, textvariable=self.quick_action_var,
                                    values=["Выключить ПК", "Перезагрузить", "Спящий режим",
                                           "Гибернация", "Только оповещение"],
                                    state='readonly', width=30)
        action_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Warning
        warning_label = ttk.Label(timer_frame, 
                                 text="⚠️ ВНИМАНИЕ: Компьютер выключится через указанное время!",
                                 foreground="#856404", background="#fff3cd")
        warning_label.pack(fill=tk.X, padx=10, pady=10)

    def create_schedule_tab(self):
        """Create schedule tab"""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="🕐 По времени")

        # Time selection
        time_group = ttk.LabelFrame(schedule_frame, text="Укажите время выключения", padding=10)
        time_group.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(time_group, text="Выключить в:").pack(side=tk.LEFT, padx=5)

        frame_time = ttk.Frame(time_group)
        frame_time.pack(side=tk.LEFT, padx=5)

        self.schedule_hours_var = tk.IntVar(value=datetime.now().hour)
        ttk.Spinbox(frame_time, from_=0, to=23, textvariable=self.schedule_hours_var,
                   width=3, font=('Arial', 11)).pack(side=tk.LEFT)
        ttk.Label(frame_time, text=":").pack(side=tk.LEFT)
        
        self.schedule_minutes_var = tk.IntVar(value=datetime.now().minute)
        ttk.Spinbox(frame_time, from_=0, to=59, textvariable=self.schedule_minutes_var,
                   width=3, font=('Arial', 11)).pack(side=tk.LEFT)

        # Action
        action_group = ttk.LabelFrame(schedule_frame, text="Действие", padding=10)
        action_group.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(action_group, text="Выполнить:").pack(side=tk.LEFT, padx=5)
        self.schedule_action_var = tk.StringVar(value="Выключить ПК")
        action_combo = ttk.Combobox(action_group, textvariable=self.schedule_action_var,
                                    values=["Выключить ПК", "Перезагрузить", "Спящий режим",
                                           "Гибернация", "Только оповещение"],
                                    state='readonly', width=30)
        action_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Warning
        warning_label = ttk.Label(schedule_frame,
                                 text="⚠️ ВНИМАНИЕ: Компьютер будет выключен в указанное время!",
                                 foreground="#856404", background="#fff3cd")
        warning_label.pack(fill=tk.X, padx=10, pady=10)

    def create_weekly_tab(self):
        """Create weekly tab"""
        weekly_frame = ttk.Frame(self.notebook)
        self.notebook.add(weekly_frame, text="📅 Расписание")

        info_label = ttk.Label(weekly_frame, text="💡 Расписание в разработке...",
                              font=('Arial', 11, 'italic'), foreground="#666")
        info_label.pack(pady=20)

    def start_shutdown(self):
        """Start countdown"""
        if self.shutdown_scheduled:
            messagebox.showwarning("Ошибка", "Таймер уже запущен!")
            return

        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:  # Quick timer
            hours = self.hours_var.get()
            minutes = self.minutes_var.get()
            seconds = self.seconds_var.get()
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds == 0:
                messagebox.showwarning("Ошибка", "Пожалуйста, установите время!")
                return

            self.remaining_seconds = total_seconds
            action = self.quick_action_var.get()

        elif current_tab == 1:  # Schedule
            scheduled_time = datetime.now().replace(
                hour=self.schedule_hours_var.get(),
                minute=self.schedule_minutes_var.get(),
                second=0
            )
            current_time = datetime.now()

            if scheduled_time <= current_time:
                scheduled_time += timedelta(days=1)

            self.remaining_seconds = int((scheduled_time - current_time).total_seconds())
            action = self.schedule_action_var.get()

        else:
            messagebox.showinfo("Информация", "Расписание в разработке!")
            return

        # Confirmation
        hours = self.remaining_seconds // 3600
        mins = (self.remaining_seconds % 3600) // 60
        secs = self.remaining_seconds % 60

        msg = f"Компьютер будет {action.lower()}\nчерез: {hours:02d}:{mins:02d}:{secs:02d}\n\nПродолжить?"
        if messagebox.askyesno("✓ Подтверждение", msg):
            self.shutdown_scheduled = True
            self.shutdown_action = action
            self.start_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
            self.countdown_start_time = datetime.now()

    def cancel_shutdown(self):
        """Cancel shutdown"""
        try:
            subprocess.run(["shutdown", "/a"], check=True, capture_output=True)
        except:
            pass

        self.shutdown_scheduled = False
        self.progress_bar.pack_forget()
        self.status_label.config(text="⏸️ Таймер отменен")
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        messagebox.showinfo("✓ Успешно", "Таймер выключения отменен")

    def update_timer(self):
        """Update timer display"""
        if self.shutdown_scheduled:
            elapsed = (datetime.now() - self.countdown_start_time).total_seconds()
            self.remaining_seconds = max(0, self.remaining_seconds - (elapsed - self.last_update))

            if self.remaining_seconds <= 0:
                self.execute_shutdown()
            else:
                hours = int(self.remaining_seconds // 3600)
                minutes = int((self.remaining_seconds % 3600) // 60)
                seconds = int(self.remaining_seconds % 60)

                self.status_label.config(
                    text=f"⏱️ Осталось: {hours:02d}:{minutes:02d}:{seconds:02d} | {self.shutdown_action}"
                )

                max_seconds = 24 * 3600
                progress = max(0, min(100, 100 * (1 - self.remaining_seconds / max_seconds)))
                self.progress_var.set(progress)

        self.last_update = (datetime.now() - self.countdown_start_time).total_seconds() if self.shutdown_scheduled else 0
        self.root.after(100, self.update_timer)

    def execute_shutdown(self):
        """Execute shutdown"""
        self.shutdown_scheduled = False

        if self.shutdown_action == "Только оповещение":
            messagebox.showinfo("✓ Оповещение", "Время истекло!")
            self.status_label.config(text="⏹️ Таймер завершен")
        else:
            action_map = {
                "Выключить ПК": "/s",
                "Перезагрузить": "/r",
                "Спящий режим": "/h",
                "Гибернация": "/h"
            }

            try:
                subprocess.run(
                    ["shutdown", action_map.get(self.shutdown_action, "/s"), "/t", "60"],
                    check=True, capture_output=True
                )
                self.status_label.config(text="🔴 Компьютер выключается...")
            except Exception as e:
                messagebox.showerror("❌ Ошибка", f"Ошибка при выключении:\n{str(e)}")

        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = ShutdownTimerTkinter(root)
    root.mainloop()
