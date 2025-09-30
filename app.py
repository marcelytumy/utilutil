import keyboard
import pyautogui
import win32gui
import threading
from utils import detect_context
from gui import show_popup

# --------------------------------------------
# HOTKEY LISTENER
# --------------------------------------------

def on_hotkey():
    x, y = pyautogui.position()
    hwnd = win32gui.WindowFromPoint((x, y))
    context, data = detect_context()
    print(f"[Hotkey] Context: {context}, Data: {str(data)[:50]}")

    # Launch popup in a thread to avoid blocking
    threading.Thread(target=show_popup, args=(x, y, context, data, hwnd)).start()

# --------------------------------------------
# MAIN
# --------------------------------------------

def main():
    print("[ContextTool] Running. Press F12 to activate.")
    keyboard.add_hotkey('f12', on_hotkey)
    keyboard.wait()  # Keep script running

if __name__ == "__main__":
    main()
