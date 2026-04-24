from PySide6.QtWidgets import QApplication
from controller import Controller
from app_init import init_app
from login_window import LoginWindow
from dashboard_window import DashboardWindow
from database import get_remembered_user
import sys

def main():
    app = QApplication([])
    init_app()

    controller = Controller()

    remembered_user = get_remembered_user()  # look in the database for a user with remember_session = 1

    # If remember_session for user is 1
    if remembered_user:
        controller.current_user = remembered_user  # so the controller knows which user is being autologged in
        first_window = DashboardWindow  # app skips login and opens the dashboard
    else:
        first_window = LoginWindow  # login opens normally when no user is remembered

    controller.show_window(first_window) # open whichever window is chosen above

    sys.exit(app.exec())

if __name__ == "__main__":
    main()