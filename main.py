import tkinter as tk
import time
from tkinter import ttk
import threading
from ui_items.karbon_ui import KarbonUI
import sys
import os

from user_manager import UserManager
from utils.user_utils import get_active_user

# Initialize UserManager and get active user
user_manager = UserManager()
active_user = user_manager.get_active_user()
print("Active User:", active_user)

# Function to get the correct path for bundled data files
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Step 1: Create autosave directory
autosave_dir = "autosave"
os.makedirs(autosave_dir, exist_ok=True)

if __name__ == "__main__":
    def start_ui():
        root = tk.Tk()

        # Create UserManager instance and get active user again (if needed)
        user_manager = UserManager()
        active_user = user_manager.get_active_user()
        print("Active user:", active_user)

        app = KarbonUI(root, active_user=active_user)

        # ✅ Define and set close protocol BEFORE mainloop
        def on_closing():
            app.save_settings()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()

    start_ui()
