from PySide6.QtWidgets import QApplication
from controller import Controller
from app_init import init_app
from login_window import LoginWindow
import sys

def main():
    app = QApplication([])
    init_app()

    controller = Controller()

    user_logged_in = False  # PLACEHOLDER VALUE, if false send to LoginWindow, if true send to DashboardWindow

    if user_logged_in:
        first_window = DashboardWindow
    else: 
        first_window = LoginWindow

    controller.show_window(first_window)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()