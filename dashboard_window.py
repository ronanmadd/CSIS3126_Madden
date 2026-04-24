# This is to let me work with files/folders like json file path
import os

# Can save and load preset data using json format
import json

from PySide6.QtCore import Qt

# This is used for the color picker
from PySide6.QtGui import QColor

# Widgets / Layouts we use
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QComboBox, QSlider, QTextEdit,
    QColorDialog, QSpinBox, QStackedWidget
)

from base_window import BaseWindow

from led_engine import LEDEngine

from database import get_user_id, get_user_settings, save_user_settings

class DashboardWindow(BaseWindow):
    def __init__(self, controller=None):
        super().__init__(controller)

        self.controller = controller    # save controller reference
        self.setWindowTitle("SpectraSync Dashboard")

        # Window starting size
        self.resize(1000, 700)

        # Path to JSON file where presets are saved
        self.presets_file = os.path.join(os.path.dirname(__file__), "user_presets.json")

        # List to hold all presets
        self.presets = []

        # Use to keep track of which preset is currently selected
        self.current_index = None

        # Create new engine instance to control LEDs
        self.engine = LEDEngine()

        # Load saved presets from JSON file
        self.load_presets()

        # Build all widgets / layouts
        self.setup_ui()

    def setup_ui(self):

        # Horizontal layout for whole window
        main_layout = QHBoxLayout()

        # Window's main layout
        self.setLayout(main_layout)

        # Left side menu layout
        left_panel = QVBoxLayout()

        # Navigation buttons
        self.overview_button = QPushButton("Overview")
        self.presets_button = QPushButton("Presets")
        self.help_button = QPushButton("Help")
        self.logout_button = QPushButton("Log Out")

        # When "overview" is clicked, show page 0 in the stacked widget
        self.overview_button.clicked.connect(lambda: self.pages.setCurrentIndex(0))

        # When "presets" is clicked, show page 1 in the stacked widget
        self.presets_button.clicked.connect(lambda: self.pages.setCurrentIndex(1))

        # When "help" is clicked, show page 2 in the stacked widget
        self.help_button.clicked.connect(lambda: self.pages.setCurrentIndex(2))

        # When logout is clicked, call logout function
        self.logout_button.clicked.connect(self.logout_clicked)

        # Add the page buttons to the left menu
        left_panel.addWidget(self.overview_button)
        left_panel.addWidget(self.presets_button)
        left_panel.addWidget(self.help_button)
        left_panel.addStretch()                        # Pushes logout button to the bottom
        left_panel.addWidget(self.logout_button)

        # Widget to hold the left menu layout
        # (CONT.) Layouts organize widgets
        # (CONT 2.) # Widgets are what actually get displayed
        # (CONT 3.) Can't add layouts to layouts directly
        left_widget = QWidget()

        # Attach layout to widget
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(180)

        # A QStackedWidget is basically a container that holds multiple pages but only shows one at a time, like tabs but you control with buttons
        self.pages = QStackedWidget()

        # ---------------------------- Overview Page -------------------------------

        # Create overview page widget
        self.overview_page = QWidget()

        # Vertical layout for overview page
        overview_layout = QVBoxLayout()

        # Attach layout to overview page
        self.overview_page.setLayout(overview_layout)

        # Default username in case controller/user is missing
        username = "User"

        # If controller exists and has current user, use their name
        if self.controller and self.controller.current_user:
            username = self.controller.current_user

        # Overview page welcome label
        self.welcome_label = QLabel(f"Welcome, {username}")

        # Make welcome label big and bold
        self.welcome_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        # Add welcome label to overview page
        overview_layout.addWidget(self.welcome_label)

        # Small placeholder description label
        self.info_label = QLabel("This is the SpectraSync dashboard.")

        # Add description label to overview page
        overview_layout.addWidget(self.info_label)

        # Push everything upward
        overview_layout.addStretch()

        # --------------------------- Presets Page --------------------------------

        # Create presets page widget
        self.presets_page = QWidget()

        # Horizontal layout so the preset list on the left and the editor on the right can sit side by side
        presets_layout = QHBoxLayout()

        # Attach presets layout to preset page
        self.presets_page.setLayout(presets_layout)

        # Left side of presets page
        left_presets = QVBoxLayout()

        # List widget to list the preset names
        self.preset_list = QListWidget()

        # When the row selected changes, load that preset into the editor
        self.preset_list.currentRowChanged.connect(self.load_selected_preset)

        # Buttons for preset actions
        self.new_button = QPushButton("New Preset")
        self.save_button = QPushButton("Save Preset")
        self.delete_button = QPushButton("Delete Preset")

        # Connect the buttons above to their actions
        self.new_button.clicked.connect(self.new_preset)
        self.save_button.clicked.connect(self.save_preset)
        self.delete_button.clicked.connect(self.delete_preset)

        # Add label/list/buttons to left preset panel
        left_presets.addWidget(QLabel("Presets"))
        left_presets.addWidget(self.preset_list)
        left_presets.addWidget(self.new_button)
        left_presets.addWidget(self.save_button)
        left_presets.addWidget(self.delete_button)

        # Create widget to hold left preset panel
        left_presets_widget = QWidget()

        # Set the QVBoxLayuout for left preset panel widget
        left_presets_widget.setLayout(left_presets)
        left_presets_widget.setFixedWidth(250)

        # Right side of presets page for editing selected preset
        right_presets = QVBoxLayout()

        # Preset name and label and text box
        right_presets.addWidget(QLabel("Preset Name"))
        self.name_edit = QLineEdit()
        right_presets.addWidget(self.name_edit)

        # Mode label and dropdown
        right_presets.addWidget(QLabel("Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Solid", "Rainbow", "Audio Reactive", "Screen Reactive"])    # Options for effect mode
        self.mode_combo.setToolTip("Select the lighting mode for the LEDs")                    # Hover tooltip when user hovers over, small box appears explaining what it does
        right_presets.addWidget(self.mode_combo)

        # Zone count label and dropdown (zone count is how many sections you divide the LED strip into)
        # (CONT 1.) If you have a strip of 100 leds, a zone count of 10 splits the LED's into 10 leds each
        self.zone_count_label = QLabel("Zone Count")
        right_presets.addWidget(self.zone_count_label)
        self.zone_spin = QSpinBox()
        self.zone_spin.setRange(1, 20)                                                         # Min/Max zone values
        self.zone_spin.setToolTip("Number of LED zones around the display")                    # Hover tooltip when user hovers over, small box appears explaining what it does
        right_presets.addWidget(self.zone_spin)

        # Brightness label and slider
        self.brightness_label = QLabel("Brightness")
        right_presets.addWidget(self.brightness_label)
        self.brightness_row_widget = QWidget()
        brightness_row = QHBoxLayout()
        self.brightness_row_widget.setLayout(brightness_row)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 255)                                                 # brightness range
        self.brightness_slider.setToolTip("Adjust overall LED brightness")                      # Hover tooltip when user hovers over, small box appears explaining what it does
        self.brightness_value_label = QLabel("128")                                             # Default middle value
        brightness_row.addWidget(self.brightness_slider)
        brightness_row.addWidget(self.brightness_value_label)
        right_presets.addWidget(self.brightness_row_widget)

        # Speed label and slider
        self.speed_label = QLabel("Speed")
        right_presets.addWidget(self.speed_label)
        self.speed_row_widget = QWidget()
        speed_row = QHBoxLayout()
        self.speed_row_widget.setLayout(speed_row)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 100)                                                      # Speed range
        self.speed_slider.setToolTip("Controls animation speed")                                # Hover tooltip when user hovers over, small box appears explaining what it does
        self.speed_value_label = QLabel("50")                                                   # Default middle value
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_value_label)
        right_presets.addWidget(self.speed_row_widget)

        # Smoothing label and slider (how smooth or gradual effect changes are)
        self.smoothing_label = QLabel("Smoothing")
        right_presets.addWidget(self.smoothing_label)
        self.smoothing_row_widget = QWidget()
        smoothing_row = QHBoxLayout()
        self.smoothing_row_widget.setLayout(smoothing_row)
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setRange(0, 100)                                                  # Smoothing range
        self.smoothing_slider.setToolTip("Smooths transitions between frames")                  # Hover tooltip when user hovers over, small box appears explaining what it does
        self.smoothing_value_label = QLabel("50")                                               # Default middle value
        smoothing_row.addWidget(self.smoothing_slider)
        smoothing_row.addWidget(self.smoothing_value_label)
        right_presets.addWidget(self.smoothing_row_widget)

        # For handling the updated values on slider labels
        self.brightness_slider.valueChanged.connect(self.update_slider_labels)
        self.speed_slider.valueChanged.connect(self.update_slider_labels)
        self.smoothing_slider.valueChanged.connect(self.update_slider_labels)

        # Labels and Buttons for picking color
        self.primary_color_label = QLabel("Primary Color")
        right_presets.addWidget(self.primary_color_label)
        self.primary_color_button = QPushButton("Pick Color")
        self.primary_color_button.setToolTip("Choose primary color")                            # Hover tooltip when user hovers over, small box appears explaining what it does
        right_presets.addWidget(self.primary_color_button)
        self.secondary_color_label = QLabel("Secondary Color")
        right_presets.addWidget(self.secondary_color_label)
        self.secondary_color_button = QPushButton("Pick Color")
        self.secondary_color_button.setToolTip("Choose secondary color")                        # Hover tooltip when user hovers over, small box appears explaining what it does
        right_presets.addWidget(self.secondary_color_button)

        # Connect color buttons to functions
        self.primary_color_button.clicked.connect(self.pick_primary_color)
        self.secondary_color_button.clicked.connect(self.pick_secondary_color)

        # Default starting colors
        self.primary_color = "#ffffff"
        self.secondary_color = "#ffffff"

        # Make it so buttons show default colors
        self.primary_color_button.setText(self.primary_color)
        self.primary_color_button.setStyleSheet(f"background-color: {self.primary_color}; color: black;")
        self.secondary_color_button.setText(self.secondary_color)
        self.secondary_color_button.setStyleSheet(f"background-color: {self.secondary_color}; color: black;")

        # Notes label and text box
        right_presets.addWidget(QLabel("Notes"))
        self.notes_edit = QTextEdit()
        right_presets.addWidget(self.notes_edit)

        # Start and stop buttons for engine
        self.start_button = QPushButton("Start Engine")
        self.stop_button = QPushButton("Stop Engine")
        self.start_button.clicked.connect(self.start_engine)
        self.stop_button.clicked.connect(self.stop_engine)
        right_presets.addWidget(self.start_button)
        right_presets.addWidget(self.stop_button)

        # Status label for messages like saved / loaded/ deleted
        self.status_label = QLabel("")
        right_presets.addWidget(self.status_label)

        # Push everything upward
        right_presets.addStretch()

        # Create widget to hold right preset editor
        right_presets_widget = QWidget()

        # Attach layout to right preset editor widget
        right_presets_widget.setLayout(right_presets)

        # Add left and right preset sections to presets page
        presets_layout.addWidget(left_presets_widget)
        presets_layout.addWidget(right_presets_widget)

        
        self.help_page = QWidget()                                                            # Creates help page widget
        help_layout = QVBoxLayout()                                                           # Gives page vertical layout so everything stacks top to bottom
        self.help_page.setLayout(help_layout)                                                 # Set/apply layout

        self.help_title = QLabel("SpectraSync Help")                                          # Creates title text at top
        self.help_title.setStyleSheet("font-size: 22px; font-weight: bold;")                  # Makes title bigger and bold
        help_layout.addWidget(self.help_title)                                                # Add title to page

        # Help page content
        help_text = QLabel(
            "<b>Getting Started</b><br>"
            "1. Create an account or log in.<br>"
            "2. Go to the Presets page.<br>"
            "3. Choose a mode and adjust the settings.<br>"
            "4. Click Start Engine to send the effect to the ESP32.<br><br>"
            "<b>Modes</b><br>"
            "Solid: Displays a single color.<br>"
            "Rainbow: Cycles through colors across the LEDs.<br>"
            "Audio Reactive: Responds to sound input.<br>"
            "Screen Reactive: Samples colors from your screen.<br><br>"
            "<b>Controls</b><br>"
            "Zone Count: Splits the LED layout into sections.<br>"
            "Brightness: Controls LED intensity.<br>"
            "Speed: Controls animation speed.<br>"
            "Smoothing: Makes transitions less abrupt.<br>"
            "Primary / Secondary Color: Used by supported modes.<br><br>"
            "<b>Presets</b><br>"
            "New Preset clears the editor.<br>"
            "Save Preset stores the current settings.<br>"
            "Delete Preset removes the selected preset.<br><br>"
            "<b>Troubleshooting</b><br>"
            "Make sure the ESP32 is connected before starting the engine.<br>"
            "If LEDs do not respond, stop and restart the engine.<br>"
            "Check that the correct serial port is being used in the LED engine."
        )

        help_text.setWordWrap(True)                                                             # Allows text to wrap instead of going off the screen
        help_layout.addWidget(help_text)                                                        # Add help content to page
        help_layout.addStretch()                                                                # Pushes everything upward for proper spacing

        # Add all pages to the stacked widget
        self.pages.addWidget(self.overview_page)
        self.pages.addWidget(self.presets_page)
        self.pages.addWidget(self.help_page)

        # add sidebhar and page area to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.pages)

        # Update engine when UI changes
        self.brightness_slider.valueChanged.connect(self.send_to_engine)
        self.speed_slider.valueChanged.connect(self.send_to_engine)
        self.smoothing_slider.valueChanged.connect(self.send_to_engine)
        self.mode_combo.currentTextChanged.connect(self.send_to_engine)
        self.mode_combo.currentTextChanged.connect(self.update_mode_ui)
        self.zone_spin.valueChanged.connect(self.send_to_engine)
        self.name_edit.textChanged.connect(self.send_to_engine)
        self.notes_edit.textChanged.connect(self.send_to_engine)

        self.new_preset()

        self.update_mode_ui()

        # Load preset names into the list widget
        self.refresh_preset_list()

        # Restore the logged-in user's saved mode and brightness when the dashboard opens
        self.load_user_settings()

        self.mode_combo.currentTextChanged.connect(self.save_current_user_settings)  # Changing the mode immediately updates the user's saved default mode
        self.brightness_slider.valueChanged.connect(self.save_current_user_settings)  # Changing brightness immediately updates the user's saved default brightness


# ---------------------------------------------------------------------------

    def get_current_preset_data(self):

        # Get all current UI values
        return {
            "name": self.name_edit.text(),
            "mode": self.mode_combo.currentText(),
            "zone_count": self.zone_spin.value(),
            "brightness": self.brightness_slider.value(),
            "speed": self.speed_slider.value(),
            "smoothing": self.smoothing_slider.value(),
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "notes": self.notes_edit.toPlainText()
        }

    def send_to_engine(self):

        # Get the current values
        preset = self.get_current_preset_data()

        # Send data to engine
        self.engine.update_preset(preset)

    def start_engine(self):

        self.engine.start()
        self.send_to_engine()
        self.status_label.setText("Engine started")

    def stop_engine(self):

        self.engine.stop()
        self.status_label.setText("Engine stopped")

    # Load presets from json file
    def load_presets(self):

        # Check if json file exists
        if os.path.exists(self.presets_file):
            try:

                # Open file in read mode ("r")
                with open(self.presets_file, "r") as f:

                    # Load json into the presets list
                    self.presets = json.load(f)

            # If it doesn't work just use an empty list
            except:
                self.presets = []
        # If file doesn't exist use empty list with no presets
        else:
            self.presets = []

    # Saves current presets list back into json file
    def write_presets(self):

        # open file in write mode ("w")
        with open(self.presets_file, "w") as f:

            # Write presets list as formatted json
            json.dump(self.presets, f, indent=4)        # indent 4 is pretty normal because it's a lot more readable

    # refreshes preset names shown in list widget
    def refresh_preset_list(self):

        # Clear old items
        self.preset_list.clear()

        # add each preset name to list
        for preset in self.presets:
            self.preset_list.addItem(preset["name"])

    # Clear editor to start making new preset
    def new_preset(self):

        # No preset currently selected
        self.current_index = None

        # Reset fields to default
        self.name_edit.setText("")
        self.mode_combo.setCurrentIndex(0)
        self.update_mode_ui()
        self.zone_spin.setValue(8)
        self.brightness_slider.setValue(128)
        self.speed_slider.setValue(50)
        self.smoothing_slider.setValue(50)
        
        # Update slider labels so value shows
        self.update_slider_labels()

        # Reset default colors
        self.primary_color = "#ffffff"
        self.secondary_color = "#ffffff"

        # Make it so buttons show default colors
        self.primary_color_button.setText(self.primary_color)
        self.primary_color_button.setStyleSheet(f"background-color: {self.primary_color}; color: black;")
        self.secondary_color_button.setText(self.secondary_color)
        self.secondary_color_button.setStyleSheet(f"background-color: {self.secondary_color}; color: black;")

        # Clear notes box
        self.notes_edit.clear()

        # Update engine
        self.send_to_engine()  # NEW: update engine

        # Status message when making new preset
        self.status_label.setText("New preset started")

    # Saves current editor values as a preset
    def save_preset(self):

        # Create dictionary from all editor fields (key value pairs)
        preset = {
            "name": self.name_edit.text(),
            "mode": self.mode_combo.currentText(),
            "zone_count": self.zone_spin.value(),
            "brightness": self.brightness_slider.value(),
            "speed": self.speed_slider.value(),
            "smoothing": self.smoothing_slider.value(),
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "notes": self.notes_edit.toPlainText()
        }

        # If no preset selected, add as new one
        if self.current_index is None:
            self.presets.append(preset)

        # otherwise replace selected preset (if you're editing one)
        else:
            self.presets[self.current_index] = preset

        # Save changes to json
        self.write_presets()

        # Refresh list to show changes
        self.refresh_preset_list()

        # Status message after saving preset
        self.status_label.setText("Preset saved")

    # Load selected preset into the editor
    def load_selected_preset(self, row):  # QT passes in the row as an argument automatically

        # Ignore invalid rows (less than 0 or greater than length of list)
        if row < 0 or row >= len(self.presets):
            return

        # Store which preset is selected
        self.current_index = row

        # Get selected preset dictionary
        preset = self.presets[row]

        # Put preset values into the editor fields
        self.name_edit.setText(preset["name"])
        self.mode_combo.setCurrentText(preset["mode"])
        self.update_mode_ui()                               # Important to include
        self.zone_spin.setValue(preset["zone_count"])
        self.brightness_slider.setValue(preset["brightness"])
        self.speed_slider.setValue(preset["speed"])
        self.smoothing_slider.setValue(preset["smoothing"])
        self.primary_color = preset["primary_color"]
        self.secondary_color = preset["secondary_color"]
        self.notes_edit.setPlainText(preset["notes"])

        # Update it so slider labels show value
        self.update_slider_labels()

        # Make it so buttons show default colors
        self.primary_color_button.setText(self.primary_color)
        self.primary_color_button.setStyleSheet(f"background-color: {self.primary_color}; color: black;")
        self.secondary_color_button.setText(self.secondary_color)
        self.secondary_color_button.setStyleSheet(f"background-color: {self.secondary_color}; color: black;")

        self.send_to_engine() # Send to engine

        # Status message when preset is loaded
        self.status_label.setText("Preset loaded")

    # Deletes selected preset
    def delete_preset(self):

        # Get selected row from list widget
        row = self.preset_list.currentRow()

        # Ignore invalid rows
        if row < 0 or row >= len(self.presets):
            return

        # Remove selected preset from list
        del self.presets[row]

        # Save updated list
        self.write_presets()

        # Refresh list to show changes
        self.refresh_preset_list()

        # Clear editor to default new preset
        self.new_preset()

        # Status message when preset has been deleted
        self.status_label.setText("Preset deleted")

    # Opens color picker for primary color
    def pick_primary_color(self):

        # Open color picker
        color = QColorDialog.getColor()

        # if user picked valid color (user actually picked a color and didn't just hit cancel)
        if color.isValid():

            # Save selected hex color
            self.primary_color = color.name()

            # Show selected hex on button text
            self.primary_color_button.setText(self.primary_color)
            self.primary_color_button.setStyleSheet(f"background-color: {self.primary_color}; color: black;")

            self.send_to_engine() # Send to engine

    # Opens color picker for secondary color
    def pick_secondary_color(self):

        # Open color picker
        color = QColorDialog.getColor()

        # if user picked valid color (user actually picked a color and didn't just hit cancel)
        if color.isValid():

            # Save selected hex color
            self.secondary_color = color.name()

            # Show selected hex on button text
            self.secondary_color_button.setText(self.secondary_color)
            self.secondary_color_button.setStyleSheet(f"background-color: {self.secondary_color}; color: black;")

            self.send_to_engine() # Send to engine

    # Function for updating slider labels numeric value
    def update_slider_labels(self):

        self.brightness_value_label.setText(str(self.brightness_slider.value()))
        self.speed_value_label.setText(str(self.speed_slider.value()))
        self.smoothing_value_label.setText(str(self.smoothing_slider.value()))

    # Function for updating labels based on which mode is selected
    def update_mode_ui(self):

        mode = self.mode_combo.currentText()

        if mode == "Solid":
            self.zone_count_label.hide()
            self.zone_spin.hide()
            self.primary_color_label.show()
            self.primary_color_button.show()
            self.secondary_color_label.hide()
            self.secondary_color_button.hide()
            self.speed_label.hide()
            self.speed_row_widget.hide()
            self.smoothing_label.hide()
            self.smoothing_row_widget.hide()

        elif mode == "Rainbow":
            self.zone_count_label.show()
            self.zone_spin.show()
            self.primary_color_label.show()
            self.primary_color_button.show()
            self.secondary_color_label.show()
            self.secondary_color_button.show()
            self.speed_label.show()
            self.speed_row_widget.show()
            self.smoothing_label.show()
            self.smoothing_row_widget.show()

        elif mode == "Audio Reactive":
            self.zone_count_label.show()
            self.zone_spin.show()
            self.primary_color_label.show()
            self.primary_color_button.show()
            self.secondary_color_label.show()
            self.secondary_color_button.show()
            self.speed_label.show()
            self.speed_row_widget.show()
            self.smoothing_label.show()
            self.smoothing_row_widget.show()

        elif mode == "Screen Reactive":
            self.zone_count_label.show()
            self.zone_spin.show()
            self.primary_color_label.hide()
            self.primary_color_button.hide()
            self.secondary_color_label.hide()
            self.secondary_color_button.hide()
            self.speed_label.hide()
            self.speed_row_widget.hide()
            self.smoothing_label.show()
            self.smoothing_row_widget.show()

    # Function to load saved dashboard settings for the current user
    def load_user_settings(self):
        if not self.controller or not self.controller.current_user:     # only runs when a user is actually logged in
            return

        user_id = get_user_id(self.controller.current_user)             # look up the logged-in user's numeric id
        if user_id is None:                                             # check in case the username is missing from database
            return

        settings = get_user_settings(user_id)                           # get the saved mode and brightness from the user_settings table

        mode = settings["default_mode"]                                 # read the user's saved default mode
        brightness = settings["default_brightness"]                     # read the user's saved default brightness

        index = self.mode_combo.findText(mode)                          # find where that saved mode appears in the dropdown
        if index != -1:                                                 # app only sets the dropdown if the mode name exists
            self.mode_combo.setCurrentIndex(index)                      # restore the saved mode in the combo box

        self.brightness_slider.setValue(brightness)                     # restore the saved brightness in the slider

    # Function to save the current user's selected mode and brightness
    def save_current_user_settings(self):
        if not self.controller or not self.controller.current_user:     # only saves for a logged-in user
            return
        
        user_id = get_user_id(self.controller.current_user)             # get the current user's id for saving settings
        if user_id is None:                                             # check in case the username is not found
            return
        
        existing_settings = get_user_settings(user_id)                  # remember_session is preserved when dashboard settings are saved

        # Write the current mode and brightness back into the database
        save_user_settings(
            user_id,
            self.mode_combo.currentText(),
            self.brightness_slider.value(),
            existing_settings["remember_session"]
        )
        
    # Logout button function
    def logout_clicked(self):

        self.save_current_user_settings()  #  Latest mode and brightness are saved before the user logs out

        # If controller exists, call logout
        if self.controller:
            self.controller.logout()

    # Function to handle what happens if user closes with X button instead of logging out
    def closeEvent(self, event):
        self.save_current_user_settings()   # Settings are saved when the user closes the window with X button
        event.accept()