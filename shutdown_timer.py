import sys
import subprocess
import threading
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QComboBox, QPushButton, QTimeEdit, QMessageBox,
    QProgressBar, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette


class ShutdownWorker(QObject):
    """Worker for countdown operations"""
    update_signal = pyqtSignal(int, str)  # remaining seconds, formatted time
    finished_signal = pyqtSignal()

    def __init__(self, shutdown_time_seconds):
        super().__init__()
        self.shutdown_time = shutdown_time_seconds
        self.is_running = True

    def run(self):
        """Run the countdown"""
        start_time = datetime.now()
        while self.is_running:
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = max(0, self.shutdown_time - elapsed)

            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)

            formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.update_signal.emit(int(remaining), formatted_time)

            if remaining <= 0:
                self.finished_signal.emit()
                break

            threading.Event().wait(0.1)

    def stop(self):
        """Stop the countdown"""
        self.is_running = False


class ShutdownTimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.worker_thread = None
        self.shutdown_scheduled = False
        self.remaining_seconds = 0
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Windows Shutdown Timer")
        self.setGeometry(100, 100, 600, 400)

        # Set application style
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Таймер выключения Windows")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Create tab widget
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Tab 1: Timer by Duration
        timer_tab = self.create_timer_tab()
        tabs.addTab(timer_tab, "По времени")

        # Tab 2: Schedule by Time
        schedule_tab = self.create_schedule_tab()
        tabs.addTab(schedule_tab, "По времени суток")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Таймер не установлен")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        main_layout.addWidget(self.status_label)

        # Control buttons layout
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Запустить")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.start_button.clicked.connect(self.start_shutdown)
        button_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.cancel_button.clicked.connect(self.cancel_shutdown)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)
        main_widget.setLayout(main_layout)

        # Timer for updating display
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)

    def create_timer_tab(self):
        """Create tab for setting timer by duration"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Time selection layout
        time_layout = QHBoxLayout()
        
        # Hours
        time_layout.addWidget(QLabel("Часы:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setMaximum(23)
        self.hours_spin.setMinimum(0)
        self.hours_spin.setValue(0)
        self.hours_spin.setStyleSheet("padding: 5px;")
        time_layout.addWidget(self.hours_spin)

        # Minutes
        time_layout.addWidget(QLabel("Минуты:"))
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setMaximum(59)
        self.minutes_spin.setMinimum(0)
        self.minutes_spin.setValue(5)
        self.minutes_spin.setStyleSheet("padding: 5px;")
        time_layout.addWidget(self.minutes_spin)

        # Seconds
        time_layout.addWidget(QLabel("Секунды:"))
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setMaximum(59)
        self.seconds_spin.setMinimum(0)
        self.seconds_spin.setValue(0)
        self.seconds_spin.setStyleSheet("padding: 5px;")
        time_layout.addWidget(self.seconds_spin)

        time_layout.addStretch()
        layout.addLayout(time_layout)

        # Warning label
        warning = QLabel("⚠️ Компьютер выключится через указанное время")
        warning.setStyleSheet("color: #ff9800; padding: 10px;")
        layout.addWidget(warning)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_schedule_tab(self):
        """Create tab for scheduling shutdown at specific time"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Time selection
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Выключить в:"))
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime().addSecs(300))  # 5 minutes from now
        self.time_edit.setStyleSheet("padding: 5px;")
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)

        # Action before shutdown
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Действие перед выключением:"))
        
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Выключить", "Перезагрузить", "Спящий режим", "Гибернация"])
        self.action_combo.setStyleSheet("padding: 5px;")
        action_layout.addWidget(self.action_combo)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Warning label
        warning = QLabel("⚠️ Компьютер выполнит выбранное действие в указанное время")
        warning.setStyleSheet("color: #ff9800; padding: 10px;")
        layout.addWidget(warning)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def start_shutdown(self):
        """Start the shutdown timer"""
        if self.shutdown_scheduled:
            QMessageBox.warning(self, "Ошибка", "Таймер уже запущен!")
            return

        # Determine which tab is active
        current_tab = self.findChild(QTabWidget).currentIndex()

        if current_tab == 0:  # Timer tab
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds == 0:
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, установите время!")
                return

            self.remaining_seconds = total_seconds
            action = "Выключить"
        else:  # Schedule tab
            scheduled_time = self.time_edit.time().toPython()
            current_time = datetime.now().time()

            scheduled_datetime = datetime.combine(datetime.now().date(), scheduled_time)
            current_datetime = datetime.now()

            if scheduled_datetime <= current_datetime:
                scheduled_datetime += timedelta(days=1)

            self.remaining_seconds = int((scheduled_datetime - current_datetime).total_seconds())
            action = self.action_combo.currentText()

        if self.remaining_seconds < 0:
            QMessageBox.warning(self, "Ошибка", "Время уже прошло!")
            return

        # Show confirmation
        hours = self.remaining_seconds // 3600
        mins = (self.remaining_seconds % 3600) // 60
        secs = self.remaining_seconds % 60

        msg = f"Компьютер будет {action.lower()} через:\n{hours:02d}:{mins:02d}:{secs:02d}\n\nПродолжить?"
        reply = QMessageBox.question(self, "Подтверждение", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.shutdown_scheduled = True
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.display_timer.start(100)

        # Store action for later use
        self.shutdown_action = action

    def cancel_shutdown(self):
        """Cancel the scheduled shutdown"""
        if not self.shutdown_scheduled:
            return

        # Cancel Windows shutdown command
        try:
            subprocess.run(["shutdown", "/a"], check=True, capture_output=True)
        except:
            pass

        self.shutdown_scheduled = False
        self.display_timer.stop()
        self.progress_bar.setVisible(False)
        self.status_label.setText("Таймер отменен")
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        QMessageBox.information(self, "Успешно", "Таймер выключения отменен")

    def update_display(self):
        """Update the display"""
        if not self.shutdown_scheduled:
            return

        self.remaining_seconds -= 0.1
        
        if self.remaining_seconds <= 0:
            self.execute_shutdown()
            return

        # Update progress bar
        max_seconds = 24 * 3600  # Max 24 hours
        progress = max(0, min(100, 100 * (1 - self.remaining_seconds / max_seconds)))
        self.progress_bar.setValue(int(progress))

        # Update status
        hours = int(self.remaining_seconds // 3600)
        minutes = int((self.remaining_seconds % 3600) // 60)
        seconds = int(self.remaining_seconds % 60)

        self.status_label.setText(
            f"Осталось: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def execute_shutdown(self):
        """Execute the shutdown command"""
        self.shutdown_scheduled = False
        self.display_timer.stop()

        action_map = {
            "Выключить": "/s",
            "Перезагрузить": "/r",
            "Спящий режим": "/h",
            "Гибернация": "/h"
        }

        command = ["shutdown", action_map.get(self.shutdown_action, "/s"), "/t", "60", "/c", "Windows выключается по таймеру..."]

        try:
            subprocess.run(command, check=True, capture_output=True)
            self.status_label.setText("Компьютер выключается...")
            self.progress_bar.setVisible(False)
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выключении:\n{str(e)}")
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = ShutdownTimerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
