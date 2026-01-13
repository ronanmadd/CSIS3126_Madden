import ctypes
import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon

from app_globals import APP_USER_MODEL_ID, APP_NAME, APP_ICO_PATH, APP_PNG_PATH

# I found an interesting workaround for setting the taskbar icon in PySide6 on Stack Overflow here, using ctypes
# https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
# Set AppUserModelID (Windows only), runs once when module first imported
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
except Exception:
    pass  # ignore on non-Windows systems

class BaseWindow(QWidget):
    def __init__(self, controller):
        super().__init__()

        # Store reference to controller if passed
        self.controller = controller

        # Set full window title automatically'
        class_name = self.__class__.__name__                # Since __class__ refers to the class type itself (not the instance), we get that
                                                            # (CONT.) Then we use __name__ to get the name of that class as a string
                                                            # (CONT 2.) Since all class names are streamlined as SomethingWindow
        window_title = class_name.replace("Window", "")     # (CONT 3.) We can trim the "Window" part for the "window_title"

        self.setWindowTitle(f"{APP_NAME}: {window_title}")  # Pass in global APP_NAME and window_title to set it automatically

        # Set streamlined window icon
        self.setWindowIcon(QIcon(APP_ICO_PATH))

    # Streamlined close event that informs the controller this window was closed
    def closeEvent(self, event):

        if self.controller is not None: # Probably would genuinely like NEVER be None, but just to be safe I guess lol

            # Tell controller that this window is closed so it can clear its reference
            self.controller.window_closed(self.__class__) # Pass in class type to controller where the window_closed function can do the rest

        # Always call the original QWidget closeEvent to actually close the window (we wrote our own logic so have to override and include the close itself)
        super().closeEvent(event)