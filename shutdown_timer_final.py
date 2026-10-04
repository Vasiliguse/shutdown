import sys
import subprocess
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import winsound


class ShutdownTimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shutdown_scheduled = False
        self.remaining_seconds = 0
        self.shutdown_action = "Выключить ПК"
        self.start_time = None
        self.build_ui()
        self.build_tray()

    def build_ui(self):
        self.setWindowTitle("Shutdown Timer")
        self.resize(520, 420)
        self.setMinimumWidth(480)

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Windows Shutdown Timer")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Timer settings
        settings = QGroupBox("Таймер")
        settings_layout = QGridLayout(settings)

        settings_layout.addWidget(QLabel("Часы:"), 0, 0)
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(0)
        settings_layout.addWidget(self.hours_spin, 0, 1)

        settings_layout.addWidget(QLabel("Минуты:"), 0, 2)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(10)
        settings_layout.addWidget(self.minutes_spin, 0, 3)

        settings_layout.addWidget(QLabel("Секунды:"), 1, 0)
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setValue(0)
        settings_layout.addWidget(self.seconds_spin, 1, 1)

        settings_layout.addWidget(QLabel("Действие:"), 1, 2)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Выключить ПК", "Перезагрузить", "Спящий режим", "Гибернация", "Только уведомление"])
        settings_layout.addWidget(self.action_combo, 1, 3)

        layout.addWidget(settings)

        self.status_label = QLabel("Таймер не запущен")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #333333; padding: 8px;")
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Запустить")
        self.start_button.setMinimumHeight(42)
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #256b28; }"
        )
        self.start_button.clicked.connect(self.start_timer)
        buttons.addWidget(self.start_button)

        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet(
            "QPushButton { background-color: #d32f2f; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #b71c1c; }"
        )
        self.cancel_button.clicked.connect(self.cancel_timer)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_timer)

    def build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Shutdown Timer")

        menu = QMenu(self)
        show_action = menu.addAction("Показать")
        show_action.triggered.connect(self.show_window)

        hide_action = menu.addAction("Скрыть")
        hide_action.triggered.connect(self.hide_window)

        menu.addSeparator()

        exit_action = menu.addAction("Выход")
        exit_action.triggered.connect(self.exit_app)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        self.hide()

    def exit_app(self):
        if self.shutdown_scheduled:
            try:
                subprocess.run(["shutdown", "/a"], check=False, capture_output=True)
            except Exception:
                pass
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if self.shutdown_scheduled:
            self.hide()
            event.ignore()
        else:
            self.tray.hide()
            event.accept()

    def start_timer(self):
        if self.shutdown_scheduled:
            QMessageBox.warning(self, "Ошибка", "Таймер уже запущен.")
            return

        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        seconds = self.seconds_spin.value()
        total = hours * 3600 + minutes * 60 + seconds

        if total <= 0:
            QMessageBox.warning(self, "Ошибка", "Установите время больше нуля.")
            return

        self.shutdown_action = self.action_combo.currentText()
        self.remaining_seconds = total
        self.start_time = datetime.now()
        self.shutdown_scheduled = True
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.timer.start()

        self.status_label.setText(f"Осталось: {self.format_time(self.remaining_seconds)}")
        self.status_label.setStyleSheet("color: #1b5e20; padding: 8px;")

        if self.shutdown_action == "Только уведомление":
            self.tray.showMessage("Shutdown Timer", "Таймер запущен. Уведомление будет показано по истечении времени.", 1000)
        else:
            self.tray.showMessage("Shutdown Timer", f"Таймер запущен. Действие: {self.shutdown_action}", 1000)

    def cancel_timer(self):
        try:
            subprocess.run(["shutdown", "/a"], check=False, capture_output=True)
        except Exception:
            pass

        self.shutdown_scheduled = False
        self.timer.stop()
        self.remaining_seconds = 0
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Таймер отменён")
        self.status_label.setStyleSheet("color: #b71c1c; padding: 8px;")
        self.tray.showMessage("Shutdown Timer", "Таймер отменён.", 1000)

    def update_timer(self):
        if not self.shutdown_scheduled:
            return

        if self.start_time is None:
            return

        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = self.remaining_seconds - elapsed

        if remaining <= 0:
            self.execute_shutdown()
            return

        self.status_label.setText(f"Осталось: {self.format_time(int(remaining))}")
        self.status_label.setStyleSheet("color: #1b5e20; padding: 8px;")
        self.tray.setToolTip(f"Shutdown Timer\nОсталось: {self.format_time(int(remaining))}")

    def execute_shutdown(self):
        self.shutdown_scheduled = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.play_sound()

        if self.shutdown_action == "Только уведомление":
            self.status_label.setText("Время прошло. Уведомление.")
            self.status_label.setStyleSheet("color: #f9a825; padding: 8px;")
            self.tray.showMessage("Shutdown Timer", "Время прошло. Уведомление.", 2000)
            QMessageBox.information(self, "Время прошло", "Таймер завершён. Никаких системных действий не выполнено.")
            return

        action_map = {
            "Выключить ПК": "/s",
            "Перезагрузить": "/r",
            "Спящий режим": "/h",
            "Гибернация": "/h",
        }

        cmd = ["shutdown", action_map.get(self.shutdown_action, "/s"), "/t", "60"]
        try:
            subprocess.run(cmd, check=False, capture_output=True)
            self.status_label.setText("Компьютер выключается...")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 8px;")
            self.tray.showMessage("Shutdown Timer", "Компьютер выключается...", 2000)
        except Exception:
            QMessageBox.critical(self, "Ошибка", "Не удалось запустить команду выключения.")

    def play_sound(self):
        try:
            winsound.Beep(1000, 250)
            winsound.Beep(1200, 250)
            winsound.Beep(1400, 300)
        except Exception:
            pass

    @staticmethod
    def format_time(total_seconds):
        total = int(total_seconds)
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main():
    app = QApplication(sys.argv)
    window = ShutdownTimerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
