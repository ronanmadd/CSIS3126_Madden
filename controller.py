import sys
from PySide6.QtWidgets import QApplication

class Controller:
    def __init__(self):
        self.windows = {} # Array to store references to open windows dynamically

    # Function to show a window of the given class
    def show_window(self, window_class): # window_class is a stand-in for any class of window so it's more dynamic and not as hardcoded

        name = window_class.__name__    # __name__ gives the name of the class as a string

        # Checks if class name is in the reference list already so it knows if an instance has been created yet
        # Checks if the array already had the window added but the window was closed and the reference was set to none
        if name not in self.windows or self.windows[name] is None:

            # If either case is satisfied above, need to create a new instance and pass controller to it
            self.windows[name] = window_class(controller=self) # By passing the controller to it, the window is able to ask the controller to open other windows

        self.windows[name].show()            # Make the window visible to user
        self.windows[name].raise_()          # Bring window to front (raise is a Python keyword so need _ to differentiate)
        self.windows[name].activateWindow()  # Give window focus (without this the window might appear but not be ready to receive input)

    # Function on what to do if/when a window is closed (we'll add separate logic in CloseEvents for each window)
    def window_closed(self, window_class):
        name = window_class.__name__        # Get the class name of the class passed in
        if name in self.windows:            # If that class name is in the controller windows array -->
            self.windows[name] = None       # (CONT.) "Remove" it from the array of active windows