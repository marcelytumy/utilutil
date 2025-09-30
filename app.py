import keyboard
import pyautogui
import tkinter as tk
import tkinter.ttk as ttk
import pyperclip
import time
import threading
import win32clipboard
import win32con
import win32gui
import subprocess
import os
import re
import json
from dotenv import load_dotenv

# SETTINGS

# concurrency:
video_threads = 2  # Number of concurrent video processing threads
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

# --------------------------------------------
# ACTIONS
# --------------------------------------------

def convert_file(file_paths, progress_callback=None):
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    for file_path in file_paths:
        print(f"[Convert] Placeholder for file conversion: {file_path}")
        # Example: call ffmpeg, pypandoc, PIL, etc.
    if progress_callback:
        progress_callback(100)

def convert_to_mp4(file_paths, progress_callback=None):
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    durations = [get_duration(f) or 1 for f in file_paths]
    total_duration = sum(durations)
    current_offset = 0
    encoder = get_hardware_encoder()
    for i, file_path in enumerate(file_paths):
        duration = durations[i]
        base, _ = os.path.splitext(file_path)
        output = base + '.mp4'
        try:
            proc = subprocess.Popen(['ffmpeg', '-i', file_path, '-c:v', encoder, '-c:a', 'aac', output], 
                                    stderr=subprocess.PIPE, text=True)
            for line in proc.stderr:
                if 'time=' in line:
                    match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if match:
                        h, m, s = map(float, match.groups())
                        current = h * 3600 + m * 60 + s
                        file_progress = current / duration
                        overall_progress = (current_offset + file_progress * duration) / total_duration * 100
                        if progress_callback:
                            progress_callback(min(overall_progress, 100))
            proc.wait()
            current_offset += duration
            if progress_callback:
                progress_callback(min(current_offset / total_duration * 100, 100))
            print(f"[Convert to MP4] Converted {file_path} to {output} using {encoder}")
        except subprocess.CalledProcessError as e:
            print(f"[Convert to MP4] Failed for {file_path}: {e}")
        except FileNotFoundError:
            print("[Convert to MP4] ffmpeg not found. Please install ffmpeg.")

def compress_video(file_paths, progress_callback=None):
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    durations = [get_duration(f) or 1 for f in file_paths]
    total_duration = sum(durations)
    current_offset = 0
    encoder = get_hardware_encoder()
    for i, file_path in enumerate(file_paths):
        duration = durations[i]
        base, _ = os.path.splitext(file_path)
        output = base + '_compressed.mp4'
        try:
            if encoder == 'libx264':
                proc = subprocess.Popen(['ffmpeg', '-i', file_path, '-c:v', encoder, '-crf', '28', '-c:a', 'aac', output], 
                                        stderr=subprocess.PIPE, text=True)
            else:
                # For hardware encoders, use preset and quality settings
                proc = subprocess.Popen(['ffmpeg', '-i', file_path, '-c:v', encoder, '-preset', 'fast', '-c:a', 'aac', output], 
                                        stderr=subprocess.PIPE, text=True)
            for line in proc.stderr:
                if 'time=' in line:
                    match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if match:
                        h, m, s = map(float, match.groups())
                        current = h * 3600 + m * 60 + s
                        file_progress = current / duration
                        overall_progress = (current_offset + file_progress * duration) / total_duration * 100
                        if progress_callback:
                            progress_callback(min(overall_progress, 100))
            proc.wait()
            current_offset += duration
            if progress_callback:
                progress_callback(min(current_offset / total_duration * 100, 100))
            print(f"[Compress Video] Compressed {file_path} to {output} using {encoder}")
        except subprocess.CalledProcessError as e:
            print(f"[Compress Video] Failed for {file_path}: {e}")
        except FileNotFoundError:
            print("[Compress Video] ffmpeg not found. Please install ffmpeg.")

def to_uppercase(text, hwnd):
    result = text.upper()
    pyperclip.copy(result)
    print(f"[Uppercase] {result}")
    replace_selected_text(result, hwnd)

def to_lowercase(text, hwnd):
    result = text.lower()
    pyperclip.copy(result)
    print(f"[Lowercase] {result}")
    replace_selected_text(result, hwnd)

def reverse_text(text, hwnd):
    result = text[::-1]
    pyperclip.copy(result)
    print(f"[Reversed] {result}")
    replace_selected_text(result, hwnd)

def translate_text(text, hwnd):
    try:
        from langdetect import detect
        lang = detect(text)
        if lang == 'en':
            result = text  # Already in English
            print("[Translated] Already in English")
        else:
            import deepl
            auth_key = os.getenv("deepl_auth_key")
            translator = deepl.Translator(auth_key)
            result = translator.translate_text(text, target_lang="EN-GB").text
            print(f"[Translated] {result}")
        pyperclip.copy(result)
        replace_selected_text(result, hwnd)
    except Exception as e:
        print("Translation failed:", e)

def replace_selected_text(result, hwnd):
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.01)  # Small delay to ensure window is active
        keyboard.press_and_release('ctrl+v')
    except Exception as e:
        print(f"Failed to replace text: {e}")

def start_conversion(file_list, func, root, progress, frame):
    if isinstance(file_list, str):
        file_list = [file_list]
    # Disable all buttons
    for child in frame.winfo_children():
        if isinstance(child, tk.Button):
            child.config(state='disabled')
    progress.pack()  # Show progress
    progress.config(mode='determinate', maximum=100, value=0)
    
    def progress_callback(p):
        root.after(0, lambda: progress.config(value=p))
    
    def run():
        func(file_list, progress_callback)
        root.after(0, lambda: [progress.pack_forget(), root.destroy()])
    
    threading.Thread(target=run).start()

# --------------------------------------------
# GUI POPUP
# --------------------------------------------

def show_popup(x, y, context, data, hwnd):
    root = tk.Tk()
    root.overrideredirect(True)  # Removes window decorations
    root.attributes("-topmost", True)
    root.geometry(f"+{x}+{y}")
    root.configure(bg='white')

    frame = tk.Frame(root, bg='white', padx=10, pady=10)
    frame.pack()

    progress = ttk.Progressbar(frame, mode='indeterminate')
    progress.pack(pady=5)
    progress.pack_forget()  # Hide initially

    if context == 'text':
        label = tk.Label(frame, text=f"Text: {data[:40]}...", bg='white')
        label.pack()
        buttons = [
            ("To Uppercase", lambda: [to_uppercase(data, hwnd), root.destroy()]),
            ("To Lowercase", lambda: [to_lowercase(data, hwnd), root.destroy()]),
            ("Reverse", lambda: [reverse_text(data, hwnd), root.destroy()]),
            ("Translate", lambda: [translate_text(data, hwnd), root.destroy()]),
        ]
        for text_btn, cmd in buttons:
            btn = tk.Button(frame, text=text_btn, command=cmd)
            btn.pack(pady=5)

    elif context == 'file':
        image_files = [f for f in data if is_image_file(f)]
        video_files = [f for f in data if is_video_file(f)]
        
        if image_files:
            btn = tk.Button(frame, text=f"Convert {len(image_files)} Image(s)", 
                            command=lambda: start_conversion(image_files, convert_file, root, progress, frame))
            btn.pack(pady=5)
        
        if video_files:
            non_mp4 = [f for f in video_files if not f.lower().endswith('.mp4')]
            if non_mp4:
                btn = tk.Button(frame, text=f"Convert {len(non_mp4)} to MP4", 
                                command=lambda: start_conversion(non_mp4, convert_to_mp4, root, progress, frame))
                btn.pack(pady=5)
            btn = tk.Button(frame, text=f"Compress {len(video_files)} Video(s)", 
                            command=lambda: start_conversion(video_files, compress_video, root, progress, frame))
            btn.pack(pady=5)
        
        # Skip other file types

    else:
        label = tk.Label(frame, text="No valid context detected.", bg='white')
        label.pack()

    # Bind ESC to close
    root.bind('<Escape>', lambda e: root.destroy())
    # Bind focus out to close (click away)
    root.bind('<FocusOut>', lambda e: root.destroy())

    root.focus_force()  # Ensure the popup is focused
    root.mainloop()

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
