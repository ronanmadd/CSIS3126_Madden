from controller import Controller
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
controller = Controller() # Create controller

user_logged_in = False  # PLACEHOLDER VALUE

from login_window import LoginWindow
# from dashboard_window import DashboardWindow

if user_logged_in:
    first_window = DashboardWindow
else: 
    first_window = LoginWindow

controller.show_window(first_window)

sys.exit(app.exec())

