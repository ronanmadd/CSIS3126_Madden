# SpectraSync

SpectraSync is a desktop application designed to control an ESP32-powered LED lighting system in real time. The app lets users create an account, log in securely, connect to an LED microcontroller, customize lighting behavior, save presets, and run standard, screen-reactive, or audio-reactive lighting modes.

This project was created for CSIS3126 as a final design project and demonstrates desktop GUI development, authentication, password hashing, persistent storage, object-oriented programming, hardware communication, and user-focused documentation.

## Project Status / Demo Notes

SpectraSync was developed as a course project and hardware-based prototype. The application is not intended to be installed and fully tested by every user out of the box, because full functionality requires a compatible ESP32 microcontroller, an addressable LED strip, a proper power setup, and the matching firmware/hardware configuration.

This repository is mainly intended to show the software design, project structure, GUI implementation, authentication system, preset storage, LED control logic, and documentation behind the project.

Users viewing the repository can still review the code, documentation, database structure, and overall architecture without owning the physical LED hardware. However, real LED output can only be tested with the required hardware setup.

## Features

* Python desktop GUI built with PySide6 / PyQt
* ESP32 firmware for LED strip control
* User registration and login
* Password hashing before database storage
* Remember Me / persistent session support
* Saved user settings
* Preset creation, loading, saving, and deleting
* Real-time LED control with compatible hardware
* Solid color mode
* Rainbow mode
* Audio-reactive mode
* Screen-reactive mode
* In-app help page and tooltips

## Project Overview

SpectraSync combines a desktop client with an ESP32 microcontroller. The desktop application handles the user interface, authentication, preset management, saved settings, and lighting configuration. The ESP32 receives lighting commands and updates the connected LED strip in real time.

The final implementation includes a Python GUI, ESP32 firmware, user authentication, password hashing, persistent settings, saved presets, standard lighting modes, visual/audio-reactive modes, and in-app documentation.

## Technologies Used

### Desktop Application

* Python
* PySide6 / PyQt
* SQLite
* JSON
* Object-oriented programming

### Hardware / Microcontroller

* ESP32 microcontroller
* Arduino IDE
* C++ firmware
* Addressable LED strip

## System Architecture

SpectraSync uses two main platforms:

### 1. Desktop Client

The desktop client is implemented in Python using PySide6/PyQt. It manages:

* User interface
* Login and registration
* Authentication
* Preset management
* Saved user settings
* LED mode selection

### 2. ESP32 Microcontroller

The ESP32 firmware is written using the Arduino IDE with C++ code. It receives commands from the desktop application and controls the LED strip based on those commands.

The desktop app sends data such as:

* Mode selection
* Color values
* Brightness settings
* Reactive behavior settings

The ESP32 interprets the data and updates the LED strip output in real time.

## Data Storage

SpectraSync uses both SQLite and JSON.

### SQLite

SQLite is used for user accounts and user settings.

#### Users Table

* `id`
* `username`
* `password_hash`

#### User Settings Table

* `id`
* `user_id`
* `default_mode`
* `default_brightness`
* `remember_session`

Each user has one corresponding settings record.

### JSON

Presets are stored in a JSON file to allow flexibility between different lighting modes. Presets can store values such as:

* Preset name
* Mode
* Zone count
* Brightness
* Speed
* Smoothing
* Primary color
* Secondary color
* Notes

## Authentication and Security

SpectraSync includes a secure login system.

* Passwords are hashed before being stored
* Plaintext passwords are never saved
* Login attempts verify the entered password against the stored hash

This protects user passwords even if the database is opened directly.

## Persistent Sessions

The application supports a Remember Me feature.

When Remember Me is selected:

1. The user logs in successfully
2. `remember_session` is saved
3. On the next startup, the app checks for a remembered user
4. If found, the dashboard opens automatically
5. Otherwise, the login screen is shown

## Preset System

Users can manage lighting presets directly inside the app.

Supported preset actions include:

* Create presets
* Save presets
* Load presets
* Delete presets

This allows users to quickly switch between favorite lighting configurations.

## LED Control Flow

The LED control process follows this flow:

1. User changes settings in the dashboard or presets tab
2. Data is passed to the LED engine
3. The LED engine formats the data
4. The formatted data is sent to the ESP32
5. The ESP32 updates the LED strip

Supported modes:

* Solid
* Rainbow
* Audio Reactive
* Screen Reactive

## Object-Oriented Design

The application is organized using several main classes:

### `BaseWindow`

Provides shared functionality for application windows.

### `LoginWindow`

Handles user login, validation, and authentication.

### `RegisterWindow`

Handles account creation, input validation, password hashing, and database record creation.

### `DashboardWindow`

Acts as the main application interface. Users can manage presets, adjust lighting settings, start or stop the LED engine, and access help documentation.

### `LEDEngine`

Manages communication with the ESP32 by translating user-selected settings into data that can be sent to the microcontroller.

### `Database`

Handles SQLite operations including user creation, lookup, password storage, password verification, and user settings retrieval.

## Running the Project Locally

The desktop application may be run locally for code review or demonstration purposes, but LED output will only work if the required hardware is connected and configured.

1. Clone the repository:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the desktop application:

```bash
python main.py
```

4. For full LED functionality, upload the included ESP32 firmware to a compatible ESP32 board and connect the LED hardware according to the project setup.

Without the ESP32 and LED strip, the application can still be reviewed as a desktop GUI and software design project, but real lighting output cannot be tested.

## Hardware Required for Full Functionality

Full hardware testing requires:

* ESP32 microcontroller
* Addressable LED strip
* Power supply for LED strip
* USB connection for ESP32 programming/communication
* Computer running the desktop application

## Testing

The following features were tested successfully during development:

* User registration
* Duplicate registration prevention
* Login with valid credentials
* Invalid login handling
* Password hashing
* Remember Me functionality
* Saved user settings
* Save preset
* Load preset
* Delete preset
* Help page display
* Tooltips
* Start LED engine
* Stop LED engine
* Mode switching
* ESP32 communication

## Limitations

Because SpectraSync depends on physical LED hardware, users who clone the repository may not be able to fully test the LED output unless they have a compatible ESP32 and LED strip setup.

The repository should be viewed primarily as a demonstration of the application design, GUI structure, authentication system, persistent storage, preset management, and hardware communication logic.

## Future Improvements

Potential future improvements include:

* More advanced screen-reactive effects
* More audio-reactive patterns
* Improved hardware pairing
* Expanded preset customization
* More polished UI styling
* Additional LED animations
* Better device connection handling
* A simulation or preview mode for users without LED hardware

## Author

Ronan Madden

CSIS3126 Final Project
