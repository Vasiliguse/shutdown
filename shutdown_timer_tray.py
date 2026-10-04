import sys
import subprocess
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton, QTimeEdit, QMessageBox, QProgressBar, QTabWidget, QCheckBox, QGroupBox, QGridLayout, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QTime, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtCore import QUrl
import winsound


class ShutdownTimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.worker_thread = None
        self.shutdown_scheduled = False
        self.remaining_seconds = 0
        self.shutdown_action = ""
        self.is_minimized = False
        
        self.init_ui()
        self.setup_tray()
        self.apply_modern_style()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("⏱️ Windows Shutdown Timer Pro")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Create tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { 
                background-color: #f0f0f0; 
                padding: 10px 20px; 
                margin-right: 2px;
                border-radius: 5px 5px 0px 0px;
            }
            QTabBar::tab:selected { 
                background-color: #2196F3; 
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #42a5f5;
                color: white;
            }
        """)
        main_layout.addWidget(tabs, 1)

        # Tab 1: Quick Timer
        timer_tab = self.create_timer_tab()
        tabs.addTab(timer_tab, "⏱️ Быстрый таймер")

        # Tab 2: Schedule at Time
        schedule_tab = self.create_schedule_tab()
        tabs.addTab(schedule_tab, "🕐 По времени")

        # Tab 3: Presets
        presets_tab = self.create_presets_tab()
        tabs.addTab(presets_tab, "⭐ Быстрые старты")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("⏸️ Таймер не установлен")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #333; padding: 10px;")
        main_layout.addWidget(self.status_label)

        # Control buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("▶️ Запустить")
        self.start_button.setMinimumHeight(50)
        self.start_button.setFont(self.get_button_font())
        self.start_button.setStyleSheet(self.get_green_button_style())
        self.start_button.clicked.connect(self.start_shutdown)
        button_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("⏹️ Отменить")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setFont(self.get_button_font())
        self.cancel_button.setStyleSheet(self.get_red_button_style())
        self.cancel_button.clicked.connect(self.cancel_shutdown)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)
        main_widget.setLayout(main_layout)

        # Timer for updating display
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)

    def setup_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("📂 Показать")
        show_action.triggered.connect(self.show_window)
        
        hide_action = tray_menu.addAction("🔽 Скрыть")
        hide_action.triggered.connect(self.hide_to_tray)
        
        tray_menu.addSeparator()
        
        timer_5min = tray_menu.addAction("⏱️ Выключить через 5 минут")
        timer_5min.triggered.connect(lambda: self.quick_shutdown(5, 0))
        
        timer_10min = tray_menu.addAction("⏱️ Выключить через 10 минут")
        timer_10min.triggered.connect(lambda: self.quick_shutdown(10, 0))
        
        timer_30min = tray_menu.addAction("⏱️ Выключить через 30 минут")
        timer_30min.triggered.connect(lambda: self.quick_shutdown(30, 0))
        
        timer_1hour = tray_menu.addAction("⏱️ Выключить через 1 час")
        timer_1hour.triggered.connect(lambda: self.quick_shutdown(0, 1))
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("❌ Выход")
        exit_action.triggered.connect(self.exit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def create_header(self):
        """Create header with title and info"""
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        
        title = QLabel("Windows Shutdown Timer Pro")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        header_layout.addWidget(title)

        subtitle = QLabel("🔐 Автоматическое управление выключением компьютера | Часть в трее Windows")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; padding: 5px;")
        header_layout.addWidget(subtitle)

        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background-color: #f5f5f5; border-radius: 10px;")
        return header_widget

    def create_timer_tab(self):
        """Create tab for setting timer by duration"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Time selection group
        time_group = QGroupBox("Выберите время отсчета")
        time_group.setStyleSheet(self.get_group_style())
        time_layout = QGridLayout()

        # Hours
        time_layout.addWidget(QLabel("Часы:"), 0, 0)
        self.hours_spin = QSpinBox()
        self.hours_spin.setMaximum(23)
        self.hours_spin.setMinimum(0)
        self.hours_spin.setValue(0)
        self.hours_spin.setStyleSheet(self.get_spinbox_style())
        self.hours_spin.setMinimumHeight(35)
        time_layout.addWidget(self.hours_spin, 0, 1)

        # Minutes
        time_layout.addWidget(QLabel("Минуты:"), 0, 2)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setMaximum(59)
        self.minutes_spin.setMinimum(0)
        self.minutes_spin.setValue(5)
        self.minutes_spin.setStyleSheet(self.get_spinbox_style())
        self.minutes_spin.setMinimumHeight(35)
        time_layout.addWidget(self.minutes_spin, 0, 3)

        # Seconds
        time_layout.addWidget(QLabel("Секунды:"), 0, 4)
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setMaximum(59)
        self.seconds_spin.setMinimum(0)
        self.seconds_spin.setValue(0)
        self.seconds_spin.setStyleSheet(self.get_spinbox_style())
        self.seconds_spin.setMinimumHeight(35)
        time_layout.addWidget(self.seconds_spin, 0, 5)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Action selection
        action_group = QGroupBox("Действие при запуске таймера")
        action_group.setStyleSheet(self.get_group_style())
        action_layout = QHBoxLayout()

        action_layout.addWidget(QLabel("Выполнить:"))
        self.quick_action_combo = QComboBox()
        self.quick_action_combo.addItems(["Выключить ПК", "Перезагрузить", "Спящий режим", "Гибернация", "Только оповещение"])
        self.quick_action_combo.setStyleSheet(self.get_combo_style())
        self.quick_action_combo.setMinimumHeight(35)
        action_layout.addWidget(self.quick_action_combo)
        action_layout.addStretch()

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # Notification option
        options_group = QGroupBox("Параметры")
        options_group.setStyleSheet(self.get_group_style())
        options_layout = QVBoxLayout()

        self.enable_sound = QCheckBox("🔔 Включить звуковое оповещение")
        self.enable_sound.setChecked(True)
        self.enable_sound.setMinimumHeight(30)
        options_layout.addWidget(self.enable_sound)

        self.enable_popup = QCheckBox("📢 Показывать всплывающие уведомления")
        self.enable_popup.setChecked(True)
        self.enable_popup.setMinimumHeight(30)
        options_layout.addWidget(self.enable_popup)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Warning label
        warning = QLabel("⚠️ ВНИМАНИЕ: Компьютер выключится через указанное время!")
        warning.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; font-weight: bold;")
        warning.setMinimumHeight(40)
        layout.addWidget(warning)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_schedule_tab(self):
        """Create tab for scheduling shutdown at specific time"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Time selection group
        time_group = QGroupBox("Укажите время выключения")
        time_group.setStyleSheet(self.get_group_style())
        time_layout = QGridLayout()

        time_layout.addWidget(QLabel("Выключить в:"), 0, 0)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime().addSecs(300))
        self.time_edit.setStyleSheet(self.get_time_edit_style())
        self.time_edit.setMinimumHeight(35)
        time_layout.addWidget(self.time_edit, 0, 1)
        time_layout.addStretch(0, 2)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Action group
        action_group = QGroupBox("Действие при достижении времени")
        action_group.setStyleSheet(self.get_group_style())
        action_layout = QHBoxLayout()

        action_layout.addWidget(QLabel("Выполнить:"))
        self.schedule_action_combo = QComboBox()
        self.schedule_action_combo.addItems(["Выключить ПК", "Перезагрузить", "Спящий режим", "Гибернация", "Только оповещение"])
        self.schedule_action_combo.setStyleSheet(self.get_combo_style())
        self.schedule_action_combo.setMinimumHeight(35)
        action_layout.addWidget(self.schedule_action_combo)
        action_layout.addStretch()

        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        # Warning
        warning = QLabel("⚠️ ВНИМАНИЕ: Компьютер будет выключен в указанное время!")
        warning.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; font-weight: bold;")
        warning.setMinimumHeight(40)
        layout.addWidget(warning)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_presets_tab(self):
        """Create tab with quick preset buttons"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        info_label = QLabel("⚡ Быстрые кнопки для быстрого запуска таймера")
        info_label.setStyleSheet("color: #666; font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)

        # Create preset buttons
        presets_group = QGroupBox("Выключить через...")
        presets_group.setStyleSheet(self.get_group_style())
        presets_layout = QGridLayout()

        presets = [
            ("5 минут", 5, 0),
            ("10 минут", 10, 0),
            ("15 минут", 15, 0),
            ("30 минут", 30, 0),
            ("1 час", 60, 0),
            ("2 часа", 120, 0),
        ]

        for i, (label, minutes, hours) in enumerate(presets):
            btn = QPushButton(f"⏱️ {label}")
            btn.setMinimumHeight(50)
            btn.setFont(self.get_button_font())
            btn.setStyleSheet(self.get_green_button_style())
            btn.clicked.connect(lambda checked, m=minutes, h=hours: self.quick_shutdown(m, h))
            presets_layout.addWidget(btn, i // 3, i % 3)

        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def quick_shutdown(self, minutes, hours):
        """Start quick shutdown"""
        total_seconds = hours * 3600 + minutes * 60
        
        self.remaining_seconds = total_seconds
        self.shutdown_action = "Выключить ПК"
        
        reply = QMessageBox.question(
            self, "✓ Подтверждение",
            f"Компьютер будет вы��лючен через {minutes + hours * 60} минут?\n\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.shutdown_scheduled = True
            self.start_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.display_timer.start(100)
            self.status_label.setStyleSheet("color: #4CAF50; padding: 10px;")
            
            # Show notification
            self.tray_icon.showMessage(
                "⏱️ Таймер запущен",
                f"Компьютер выключится через {minutes + hours * 60} минут",
                QSystemTrayIcon.MessageIcon.Information
            )

    def start_shutdown(self):
        """Start the shutdown timer"""
        if self.shutdown_scheduled:
            QMessageBox.warning(self, "Ошибка", "Таймер уже запущен!")
            return

        tabs = self.findChild(QTabWidget)
        current_tab = tabs.currentIndex()

        if current_tab == 0:  # Quick timer tab
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds == 0:
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, установите время!")
                return

            self.remaining_seconds = total_seconds
            action = self.quick_action_combo.currentText()
        elif current_tab == 1:  # Schedule tab
            scheduled_time = self.time_edit.time().toPython()
            current_time = datetime.now().time()

            scheduled_datetime = datetime.combine(datetime.now().date(), scheduled_time)
            current_datetime = datetime.now()

            if scheduled_datetime <= current_datetime:
                scheduled_datetime += timedelta(days=1)

            self.remaining_seconds = int((scheduled_datetime - current_datetime).total_seconds())
            action = self.schedule_action_combo.currentText()

            if self.remaining_seconds < 0:
                QMessageBox.warning(self, "Ошибка", "Время уже прошло!")
                return
        else:
            return

        # Show confirmation
        hours = self.remaining_seconds // 3600
        mins = (self.remaining_seconds % 3600) // 60
        secs = self.remaining_seconds % 60

        msg = f"Компьютер будет {action.lower()}\nчерез: {hours:02d}:{mins:02d}:{secs:02d}\n\nПродолжить?"
        reply = QMessageBox.question(self, "✓ Подтверждение", msg, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.shutdown_scheduled = True
        self.shutdown_action = action
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.display_timer.start(100)
        self.status_label.setStyleSheet("color: #4CAF50; padding: 10px;")

    def cancel_shutdown(self):
        """Cancel the scheduled shutdown"""
        if not self.shutdown_scheduled:
            return

        try:
            subprocess.run(["shutdown", "/a"], check=True, capture_output=True)
        except:
            pass

        self.shutdown_scheduled = False
        self.display_timer.stop()
        self.progress_bar.setVisible(False)
        self.status_label.setText("⏸️ Таймер отменен")
        self.status_label.setStyleSheet("color: #f44336; padding: 10px;")
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        QMessageBox.information(self, "✓ Успешно", "Таймер выключения отменен")

    def update_display(self):
        """Update the display"""
        if not self.shutdown_scheduled:
            return

        self.remaining_seconds -= 0.1
        
        if self.remaining_seconds <= 0:
            self.execute_shutdown()
            return

        # Update progress bar
        max_seconds = 24 * 3600
        progress = max(0, min(100, 100 * (1 - self.remaining_seconds / max_seconds)))
        self.progress_bar.setValue(int(progress))

        # Update status
        hours = int(self.remaining_seconds // 3600)
        minutes = int((self.remaining_seconds % 3600) // 60)
        seconds = int(self.remaining_seconds % 60)

        self.status_label.setText(
            f"⏱️ Осталось: {hours:02d}:{minutes:02d}:{seconds:02d} | Действие: {self.shutdown_action}"
        )

        # Update tray tooltip
        self.tray_icon.setToolTip(
            f"Windows Shutdown Timer\nОсталось: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def execute_shutdown(self):
        """Execute the shutdown command"""
        self.shutdown_scheduled = False
        self.display_timer.stop()

        # Play notification sound
        if self.enable_sound.isChecked():
            self.play_notification_sound()

        if self.shutdown_action == "Только оповещение":
            if self.enable_popup.isChecked():
                QMessageBox.information(self, "✓ Оповещение", "Время истекло!")
            self.status_label.setText("⏹️ Таймер завершен (только оповещение)")
        else:
            action_map = {
                "Выключить ПК": "/s",
                "Перезагрузить": "/r",
                "Спящий режим": "/h",
                "Гибернация": "/h"
            }

            command = ["shutdown", action_map.get(self.shutdown_action, "/s"), "/t", "60", 
                      "/c", "Windows выключается по таймеру..."]

            try:
                subprocess.run(command, check=True, capture_output=True)
                self.status_label.setText("🔴 Компьютер выключается...")
                self.tray_icon.showMessage(
                    "⏹️ Выключение",
                    f"Компьютер выключается...",
                    QSystemTrayIcon.MessageIcon.Information
                )
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Ошибка при выключении:\n{str(e)}")

        self.progress_bar.setVisible(False)
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def play_notification_sound(self):
        """Play notification sound"""
        try:
            winsound.Beep(1000, 500)
            winsound.Beep(1000, 500)
        except:
            pass

    def hide_to_tray(self):
        """Hide window to tray"""
        self.hide()
        self.is_minimized = True

    def show_window(self):
        """Show window from tray"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.is_minimized = False

    def changeEvent(self, event):
        """Handle window minimize event"""
        if event.type() == 99:  # WindowStateChange
            if self.isMinimized():
                self.hide_to_tray()
        return super().changeEvent(event)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.shutdown_scheduled:
            reply = QMessageBox.question(
                self, "⚠️ Внимание",
                "Таймер все еще активен. Скрыть в трей или выйти?",
                QMessageBox.StandardButton.Hide | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Hide:
                self.hide_to_tray()
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()

    def exit_app(self):
        """Exit application"""
        if self.shutdown_scheduled:
            try:
                subprocess.run(["shutdown", "/a"], check=True, capture_output=True)
            except:
                pass
        self.tray_icon.hide()
        sys.exit(0)

    # Style methods
    def apply_modern_style(self):
        """Apply modern styling"""
        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QLabel { color: #333; }
            QGroupBox {
                color: #333;
                border: 2px solid #2196F3;
                border-radius: 5px;
                padding-top: 10px;
                padding-left: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QComboBox, QSpinBox, QTimeEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox:hover, QSpinBox:hover, QTimeEdit:hover {
                border: 2px solid #2196F3;
            }
            QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {
                border: 2px solid #1976D2;
            }
            QCheckBox {
                color: #333;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def get_green_button_style(self):
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

    def get_red_button_style(self):
        return """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #ba0000;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

    def get_button_font(self):
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font

    def get_spinbox_style(self):
        return """
            QSpinBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QSpinBox:hover {
                border: 2px solid #2196F3;
            }
        """

    def get_combo_style(self):
        return """
            QComboBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border: 2px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
        """

    def get_time_edit_style(self):
        return """
            QTimeEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QTimeEdit:hover {
                border: 2px solid #2196F3;
            }
        """

    def get_group_style(self):
        return """
            QGroupBox {
                color: #333;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """


def main():
    app = QApplication(sys.argv)
    window = ShutdownTimerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
