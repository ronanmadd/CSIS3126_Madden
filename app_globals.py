import os
import ctypes
from PySide6.QtGui import QIcon

# APP-WIDE CONSTANTS ==========================================================================
APP_NAME = "SpectraSync"

# __file__ is special Python variable which holds the path of the current Python file
# os.path.dirname(__file__) gets the directory of the current file but strips the file name from it
# os.path.join(..., "SpectraSyncIco.ico") joins the directory path with filename in platform independent way (works w Mac, Windows, etc.)
APP_ICO_PATH = os.path.join(os.path.dirname(__file__), "SpectraSyncICOnoBG.ico")
APP_PNG_PATH = os.path.join(os.path.dirname(__file__), "SpectraSyncPNGnoBG.png")

# Unique Windows AppUserModelID for taskbar icon
APP_USER_MODEL_ID = "spectrasync.app"
# =============================================================================================