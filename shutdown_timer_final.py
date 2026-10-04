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
    QTabWidget,
    QTimeEdit,
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont
import winsound


class ShutdownTimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shutdown_scheduled = False
        self.wakeup_scheduled = False
        self.remaining_seconds = 0
        self.wakeup_remaining_seconds = 0
        self.shutdown_action = "Выключить ПК"
        self.start_time = None
        self.wakeup_start_time = None
        self.build_ui()
        self.build_tray()

    def build_ui(self):
        self.setWindowTitle("Shutdown & Wake-up Timer")
        self.resize(620, 520)
        self.setMinimumWidth(580)

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Windows Shutdown & Wake-up Timer")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        tabs = QTabWidget()

        shutdown_tab = QWidget()
        shutdown_layout = QVBoxLayout(shutdown_tab)
        shutdown_layout.setSpacing(12)

        settings = QGroupBox("⏹️ Таймер выключения")
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

        shutdown_layout.addWidget(settings)

        self.status_label = QLabel("⏸️ Таймер не запущен")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(11)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #333333; padding: 8px;")
        shutdown_layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("▶️ Запустить выключение")
        self.start_button.setMinimumHeight(42)
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #256b28; }"
        )
        self.start_button.clicked.connect(self.start_timer)
        buttons.addWidget(self.start_button)

        self.cancel_button = QPushButton("⏹️ Отменить")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet(
            "QPushButton { background-color: #d32f2f; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #b71c1c; }"
        )
        self.cancel_button.clicked.connect(self.cancel_timer)
        buttons.addWidget(self.cancel_button)

        shutdown_layout.addLayout(buttons)
        shutdown_layout.addStretch()
        tabs.addTab(shutdown_tab, "⏱️ Выключение")

        wakeup_tab = QWidget()
        wakeup_layout = QVBoxLayout(wakeup_tab)
        wakeup_layout.setSpacing(12)

        wakeup_settings = QGroupBox("⏰ Включить компьютер")
        wakeup_settings_layout = QGridLayout(wakeup_settings)

        wakeup_settings_layout.addWidget(QLabel("Включить в:"), 0, 0)
        self.wakeup_time_edit = QTimeEdit()
        self.wakeup_time_edit.setTime(QTime(8, 0))
        self.wakeup_time_edit.setMinimumHeight(35)
        wakeup_settings_layout.addWidget(self.wakeup_time_edit, 0, 1)

        wakeup_settings_layout.addWidget(QLabel("Дата:"), 1, 0)
        self.wakeup_date_combo = QComboBox()
        self.wakeup_date_combo.addItems(["Сегодня", "Завтра", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"])
        wakeup_settings_layout.addWidget(self.wakeup_date_combo, 1, 1)

        wakeup_layout.addWidget(wakeup_settings)

        self.wakeup_status_label = QLabel("⏸️ Включение не запланировано")
        self.wakeup_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wakeup_status_label.setFont(status_font)
        self.wakeup_status_label.setStyleSheet("color: #333333; padding: 8px;")
        wakeup_layout.addWidget(self.wakeup_status_label)

        wakeup_buttons = QHBoxLayout()
        self.wakeup_start_button = QPushButton("⏰ Запланировать включение")
        self.wakeup_start_button.setMinimumHeight(42)
        self.wakeup_start_button.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1565c0; }"
        )
        self.wakeup_start_button.clicked.connect(self.start_wakeup)
        wakeup_buttons.addWidget(self.wakeup_start_button)

        self.wakeup_cancel_button = QPushButton("❌ Отменить включение")
        self.wakeup_cancel_button.setMinimumHeight(42)
        self.wakeup_cancel_button.setEnabled(False)
        self.wakeup_cancel_button.setStyleSheet(
            "QPushButton { background-color: #d32f2f; color: white; border: none; border-radius: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #b71c1c; }"
        )
        self.wakeup_cancel_button.clicked.connect(self.cancel_wakeup)
        wakeup_buttons.addWidget(self.wakeup_cancel_button)

        wakeup_layout.addLayout(wakeup_buttons)

        info_label = QLabel("ℹ️ Для включения по расписанию компьютер должен быть в спящем режиме или выключен")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 8px;")
        wakeup_layout.addWidget(info_label)
        wakeup_layout.addStretch()

        tabs.addTab(wakeup_tab, "⏰ Включение")

        layout.addWidget(tabs)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_timer)

    def build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Shutdown & Wake-up Timer")

        menu = QMenu(self)
        show_action = menu.addAction("📂 Показать")
        show_action.triggered.connect(self.show_window)

        hide_action = menu.addAction("🔽 Скрыть")
        hide_action.triggered.connect(self.hide_window)

        menu.addSeparator()

        exit_action = menu.addAction("❌ Выход")
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
        if self.shutdown_scheduled or self.wakeup_scheduled:
            self.hide()
            event.ignore()
        else:
            self.tray.hide()
            event.accept()

    def start_timer(self):
        if self.shutdown_scheduled:
            QMessageBox.warning(self, "Ошибка", "Таймер выключения уже запущен.")
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

        self.status_label.setText(f"⏱️ Осталось: {self.format_time(self.remaining_seconds)}")
        self.status_label.setStyleSheet("color: #1b5e20; padding: 8px;")

        self.tray.showMessage("Timer", f"Таймер выключения запущен. Действие: {self.shutdown_action}", 1000)

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
        self.status_label.setText("⏸️ Выключение отменено")
        self.status_label.setStyleSheet("color: #b71c1c; padding: 8px;")
        self.tray.showMessage("Shutdown Timer", "Таймер выключения отменён.", 1000)

    def start_wakeup(self):
        if self.wakeup_scheduled:
            QMessageBox.warning(self, "Ошибка", "Включение уже запланировано.")
            return

        wakeup_time = self.wakeup_time_edit.time().toPython()
        date_option = self.wakeup_date_combo.currentText()

        today = datetime.now().date()
        if date_option == "Сегодня":
            target_date = today
        elif date_option == "Завтра":
            target_date = today + timedelta(days=1)
        else:
            day_map = {
                "Понедельник": 0,
                "Вторник": 1,
                "Среда": 2,
                "Четверг": 3,
                "Пятница": 4,
                "Суббота": 5,
                "Воскресенье": 6,
            }
            target_weekday = day_map.get(date_option, 0)
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)

        target_datetime = datetime.combine(target_date, wakeup_time)
        now = datetime.now()

        if target_datetime <= now:
            QMessageBox.warning(self, "Ошибка", "Время уже прошло. Выберите будущее время.")
            return

        self.wakeup_scheduled = True
        self.wakeup_start_time = now
        self.wakeup_remaining_seconds = int((target_datetime - now).total_seconds())
        self.wakeup_start_button.setEnabled(False)
        self.wakeup_cancel_button.setEnabled(True)

        if not self.timer.isActive():
            self.timer.start()

        self.wakeup_status_label.setText(f"⏰ Включение запланировано на {target_datetime.strftime('%d.%m.%Y %H:%M:%S')}")
        self.wakeup_status_label.setStyleSheet("color: #1565c0; padding: 8px;")
        self.tray.showMessage("Timer", f"Компьютер включится в {target_datetime.strftime('%H:%M:%S')}", 1000)

    def cancel_wakeup(self):
        self.wakeup_scheduled = False
        self.wakeup_remaining_seconds = 0
        self.wakeup_start_button.setEnabled(True)
        self.wakeup_cancel_button.setEnabled(False)
        self.wakeup_status_label.setText("⏸️ Включение отменено")
        self.wakeup_status_label.setStyleSheet("color: #b71c1c; padding: 8px;")
        self.tray.showMessage("Timer", "Включение отменено.", 1000)

    def update_timer(self):
        if self.shutdown_scheduled and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            remaining = self.remaining_seconds - elapsed

            if remaining <= 0:
                self.execute_shutdown()
            else:
                self.status_label.setText(f"⏱️ Осталось: {self.format_time(int(remaining))}")
                self.status_label.setStyleSheet("color: #1b5e20; padding: 8px;")
                self.tray.setToolTip(f"Timer\nВыключение: {self.format_time(int(remaining))}")

        if self.wakeup_scheduled and self.wakeup_start_time:
            elapsed = (datetime.now() - self.wakeup_start_time).total_seconds()
            remaining = self.wakeup_remaining_seconds - elapsed

            if remaining <= 0:
                self.wakeup_scheduled = False
                self.wakeup_start_button.setEnabled(True)
                self.wakeup_cancel_button.setEnabled(False)
                self.wakeup_status_label.setText("✅ Время включения достигнуто")
                self.wakeup_status_label.setStyleSheet("color: #1b5e20; padding: 8px;")
                self.play_sound()
                self.tray.showMessage("Timer", "Время включения. Пожалуйста, включите компьютер вручную или используйте Wake-on-LAN.", 3000)
                QMessageBox.information(self, "⏰ Включение", "Компьютер должен быть включен сейчас. Используйте кнопку питания или Wake-on-LAN.")
            else:
                self.wakeup_status_label.setText(f"⏰ Осталось: {self.format_time(int(remaining))}")
                self.wakeup_status_label.setStyleSheet("color: #1565c0; padding: 8px;")

    def execute_shutdown(self):
        self.shutdown_scheduled = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.play_sound()

        if self.shutdown_action == "Только уведомление":
            self.status_label.setText("⏹️ Время прошло. Уведомление.")
            self.status_label.setStyleSheet("color: #f9a825; padding: 8px;")
            self.tray.showMessage("Timer", "Время прошло. Уведомление.", 2000)
            QMessageBox.information(self, "Время прошло", "Таймер завершён.")
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
            self.status_label.setText("🔴 Компьютер выключается...")
            self.status_label.setStyleSheet("color: #d32f2f; padding: 8px;")
            self.tray.showMessage("Timer", "Компьютер выключается...", 2000)
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
