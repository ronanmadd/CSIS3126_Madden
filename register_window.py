import sys
import os
import time
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QGridLayout, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

import requests
from validation import run_validators
from auth_requests import send_register_request

from base_window import BaseWindow
from app_globals import APP_PNG_PATH

class RegisterWindow(BaseWindow):
    def __init__(self, controller=None): # Constructor for RegisterWindow class, self is instance being created ===============
                                         # (CONT.) controller=None means optionally pass in controller, if not defaults to None

        super().__init__(controller)        # Refers to parent class of RegisterWindow (BaseWindow)
                                            # (CONT.) BaseWindow.__init__ takes controller as argument
                                            # (CONT 2.) Calls parent constructor so base-window setup is executed (for this instance)

        # Initial but resizeable window size
        self.resize(600,400)

        # Make arrays to store/organize all labels and line edits
        labels = {}
        self.lineEdits = {}

        # Make main vertical layout
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        # Add margins and spacing to make it neater
        # setContentMargins(space from left edge, space from top edge, space from right edge, space from bottom edge)
        mainLayout.setContentsMargins(20, 20, 20, 20) # Adds padding inside layout so widgets don't touch edge of window
        mainLayout.setSpacing(20)                    # Number of pixels between each widget in layout (space between title and gridLayout in this case)

        # Make icon label
        labels['Icon'] = QLabel()
        iconLabel = labels['Icon']
        # the (100, 100) sets the size, the aspect ratio part keeps it from stretching, and the transformation makes scaling look nicer
        iconLabel.setPixmap(QPixmap(APP_PNG_PATH).scaled(125,125, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center it horizontally

        # Make title label
        labels['Title'] = QLabel('Register')
        titleLabel = labels['Title']
        # Customize title label
        titleLabel.setStyleSheet('font-size: 60px; font-weight: bold;')
        titleLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Fixed means it won't grow or shrink
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add icon widget above the title in the main box layout
        mainLayout.addWidget(iconLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add titleLabel widget to box layout mainLayout
        mainLayout.addWidget(titleLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add grid layout into the box layout so it vertically goes under the titleLabel
        gridLayout = QGridLayout()
        gridLayout.setVerticalSpacing(15) # Spacing between rows
        mainLayout.addLayout(gridLayout)

        # If we addStretch at the BOTTOM of our layout, it pushes other widgets away and fills the vertical space
        # (CONT.) so the title and form don't float in the middle vertically when the window is taller
        mainLayout.addStretch()

        # Initialize username and password labels, add them to array
        labels['Username'] = QLabel('Username:')
        labels['Password'] = QLabel('Password:')
        # Streamline variables a bit instead of writing labels['Username'] every time
        usernameLabel = labels['Username']
        passwordLabel = labels['Password']

        # setSizePolicy(horizontal_policy, vertical_policy)
        # We want the labels to be fixed size (not stretch) and the input box to be able to stretch
        usernameLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        passwordLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Initialize line edit variables and add to array
        # We need to do self.lineEdit instead of just lineEdit so they can be instance variables that belong to the 
        # (CONT.) RegisterWindow object and can be accessed elsewhere later
        # (CONT 2.) You don't need to access the labels outside of the __init__ method
        self.lineEdits['Username'] = QLineEdit()
        self.lineEdits['Password'] = QLineEdit()

        # Make it so the input boxes can stretch horizontally if window grows (not vertically)
        self.lineEdits['Username'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lineEdits['Password'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.lineEdits['Password'].setEchoMode(QLineEdit.EchoMode.Password) # Make it so the password is hidden while the user enters it

        # layout.addWidget(widget, row, column, rowSpan, columnSpan)
        # The 0's mean first row and first column and the 1's mean they occupy one row/column respectively
        gridLayout.addWidget(usernameLabel, 0, 0, 1, 1)
        gridLayout.addWidget(self.lineEdits['Username'], 0, 1, 1, 3) # Set column span to 3 to lengthen
        gridLayout.addWidget(passwordLabel, 1, 0, 1, 1)
        gridLayout.addWidget(self.lineEdits['Password'], 1, 1, 1, 3) # Set column span to 3 to lengthen

        # Add a Register button with fixed size policy so it doesn't stretch with the page
        button_register = QPushButton('&Register')
        button_register.setFixedWidth(120)
        button_register.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        gridLayout.addWidget(button_register, 2, 3, 1, 1)

        button_register.clicked.connect(self.run_validation) # When button clicked, run validation

        # QLabel that looks like hyperlink for going to login window
        labels['loginLink'] = QLabel('<a href="#">Already have an account? Click here to login</a>')
        loginLinkLabel = labels['loginLink']                                     # streamline variable
        loginLinkLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)        # make it clickable
        loginLinkLabel.setOpenExternalLinks(False)                               # We want this to be false because we're handling it ourselves just opening another .py file
                                                                                 # (CONT.) Important distinction: send_login_window points to the function, while
                                                                                 # (CONT 2.) send_login_window() will return whatever the function returns
        loginLinkLabel.linkActivated.connect(self.open_login_window)             # on-click call method to open register window
        loginLinkLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)                # Align Center
        loginLinkLabel.setStyleSheet("color: blue; text-decoration: underline;") # Make it look like a hyperlink

        # Add loginLinkLabel to bottom of mainLayout (under the gridLayout which is used for form)
        mainLayout.addWidget(loginLinkLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Styling for potential later error messages and such
        self.status = QLabel('')
        self.status.setWordWrap(True)                                               # If text too long for one line, break into mutliple automatically
        self.status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status.setStyleSheet('font-size: 15px; color: red;')
        mainLayout.addWidget(self.status)


    # Adapter function called by register button to call validation function ==============================================
    def run_validation(self):

        username = self.lineEdits['Username'].text().strip() # Convert to text and strip for later
        password = self.lineEdits['Password'].text().strip()

        errors = run_validators(username, password) # Call function

        if errors:
            self.status.setText("\n".join(errors)) # Join errors if they exist, with line break between
            return
        
        else:

            self.status.setText("Validation passed!")
            error = send_register_request(username, password)  # Send register request to database

            if error:                                               # If there's an error, it will be caught and displayed (code after won't run)
                self.status.setText(error)
                return
            
            self.status.setText("Account created!")                 # If successful, tell user account created and redirect to login window
            self.open_login_window()


    # Function for opening login window ===================================================================================
    def open_login_window(self):
        
        from login_window import LoginWindow

        # Ask controller to open loginWindow
        # Every window should get a controller when it's created, so this "if self.controller" check is kind of bullshit but just to be safe
        if self.controller:
            self.controller.show_window(LoginWindow)