import pyautogui
import pyperclip
import time
import win32clipboard
import win32con
import subprocess
import os
import json
import re
from dotenv import load_dotenv

# SETTINGS

# concurrency:
image_threads = 4  # Number of concurrent image processing threads

# Load environment variables
load_dotenv()


# --------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------

def get_selected_text():
    """Simulate Ctrl+C to get currently selected text"""
    # Clear all clipboard contents
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    return pyperclip.paste()

def get_clipboard_files():
    """Check clipboard for file paths"""
    win32clipboard.OpenClipboard()
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            return list(files)
    except Exception:
        return []
    finally:
        win32clipboard.CloseClipboard()
    return []

def detect_context():
    """Determine if user has selected text or files"""
    text = get_selected_text()
    files = get_clipboard_files()
    if files:
        return 'file', files
    if text.strip():
        return 'text', text.strip()
    return 'none', None

def is_image_file(file_path):
    """Check if file is an image"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}
    return any(file_path.lower().endswith(ext) for ext in image_extensions)

def is_video_file(file_path):
    """Check if file is a video"""
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
    return any(file_path.lower().endswith(ext) for ext in video_extensions)

def get_duration(file_path):
    """Get video duration in seconds"""
    try:
        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path],
                                capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return None

def get_hardware_encoder():
    """Detect available hardware encoder for H.264"""
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, check=True)
        encoders = result.stdout
        if 'h264_nvenc' in encoders:
            return 'h264_nvenc'
        elif 'h264_amf' in encoders:
            return 'h264_amf'
        elif 'h264_qsv' in encoders:
            return 'h264_qsv'
        else:
            return 'libx264'  # Fallback to software
    except:
        return 'libx264'  # Fallback if ffmpeg not found or fails