import tkinter.messagebox as messagebox
import pyperclip
import time
import win32gui
import keyboard
import os
import re
import json
import subprocess
from langdetect import detect
import deepl
from utils import get_duration, get_hardware_encoder

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
    for i, file_path in enumerate(file_paths):
        duration = durations[i]
        base, _ = os.path.splitext(file_path)
        output = base + '.mp4'
        if os.path.exists(output):
            filename = os.path.basename(output)
            if not messagebox.askyesno("Overwrite File", f"File '{filename}' already exists. Overwrite?"):
                continue
        encoder = get_hardware_encoder()
        try:
            proc = subprocess.Popen(['ffmpeg', '-y', '-i', file_path, '-c:v', encoder, '-c:a', 'aac', output],
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
        if os.path.exists(output):
            filename = os.path.basename(output)
            if not messagebox.askyesno("Overwrite File", f"File '{filename}' already exists. Overwrite?"):
                continue
        try:
            if encoder == 'libx264':
                proc = subprocess.Popen(['ffmpeg', '-y', '-i', file_path, '-c:v', encoder, '-crf', '28', '-c:a', 'aac', output],
                                        stderr=subprocess.PIPE, text=True)
            else:
                # For hardware encoders, use preset and quality settings
                proc = subprocess.Popen(['ffmpeg', '-y', '-i', file_path, '-c:v', encoder, '-preset', 'fast', '-c:a', 'aac', output],
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
        lang = detect(text)
        if lang == 'en':
            result = text  # Already in English
            print("[Translated] Already in English")
        else:
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